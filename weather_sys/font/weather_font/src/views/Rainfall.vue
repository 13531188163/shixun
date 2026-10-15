<script setup>
import { computed, onMounted, ref } from 'vue'

import { getCities, getDistricts, getProvinces } from '../api/location'
import {
  getRainfallCore,
  getRainfallDates,
  getRainfallDistribution,
  getRainfallTrend,
  getRecentRainfall,
} from '../api/rainfall'
import BigScreenLayout from '../components/layout/BigScreenLayout.vue'
import ChartState from '../components/dashboard/ChartState.vue'
import DashboardPanel from '../components/dashboard/DashboardPanel.vue'
import RainfallDistributionChart from '../components/rainfall/RainfallDistributionChart.vue'
import RainfallTrendChart from '../components/rainfall/RainfallTrendChart.vue'
import { formatNumber, formatPrecipitation, weatherSymbol, weatherTypeClass } from '../utils/formatters'

const provinces = ref([])
const cities = ref([])
const districts = ref([])
const availableDates = ref([])

const province = ref('')
const city = ref('')
const district = ref('')
const startDate = ref('')
const endDate = ref('')

const core = ref(null)
const recent = ref([])
const trend = ref([])
const distribution = ref([])
const loading = ref(true)
const locationLoading = ref(false)
const error = ref('')
const requestVersion = ref(0)

const rainfallStandards = Object.freeze([
  { level: '无降水', range: '0 mm', tone: 'none' },
  { level: '小雨', range: '0.1 – 9.9 mm', tone: 'light' },
  { level: '中雨', range: '10.0 – 24.9 mm', tone: 'moderate' },
  { level: '大雨', range: '25.0 – 49.9 mm', tone: 'heavy' },
  { level: '暴雨', range: '50.0 – 99.9 mm', tone: 'storm' },
  { level: '大暴雨', range: '100.0 – 249.9 mm', tone: 'downpour' },
  { level: '特大暴雨', range: '≥ 250 mm', tone: 'extreme' },
])

const locationLabel = computed(() => {
  if (district.value) return `${province.value} / ${city.value} / ${district.value}`
  if (city.value) return `${province.value} / ${city.value}`
  if (province.value) return `${province.value} / 省级汇总`
  return '全国汇总'
})

const dateLabel = computed(() => {
  if (startDate.value && endDate.value) return `${startDate.value} 至 ${endDate.value}`
  if (startDate.value) return `${startDate.value} 起`
  if (endDate.value) return `截至 ${endDate.value}`
  return '全部历史观测日期'
})

const startDateOptions = computed(() => availableDates.value.filter(
  (date) => !endDate.value || date <= endDate.value,
))
const endDateOptions = computed(() => availableDates.value.filter(
  (date) => !startDate.value || date >= startDate.value,
))

const totalPrecipText = computed(() => formatPrecipitation(core.value?.totalPrecip))
const avgPrecipText = computed(() => formatPrecipitation(core.value?.avgPrecip))
const maxPrecipText = computed(() => formatPrecipitation(core.value?.maxPrecip))
const rainyDaysText = computed(() => formatNumber(core.value?.rainyDays))

const peakTrend = computed(() => {
  const rows = trend.value.filter((row) => Number.isFinite(Number(row.precip)))
  return rows.reduce((peak, row) => (
    peak === null || Number(row.precip) > Number(peak.precip) ? row : peak
  ), null)
})

const dominantLevel = computed(() => {
  const rows = distribution.value.filter((row) => Number(row.count) > 0)
  return rows.reduce((dominant, row) => (
    dominant === null || Number(row.count) > Number(dominant.count) ? row : dominant
  ), null)
})

const conclusionItems = computed(() => {
  const items = []
  if (core.value?.totalPrecip !== null && core.value?.totalPrecip !== undefined) {
    items.push({
      tone: 'rain',
      label: '累计降水',
      text: `${locationLabel.value}在${dateLabel.value}累计降水 ${totalPrecipText.value}。`,
    })
  }
  if (peakTrend.value) {
    items.push({
      tone: 'peak',
      label: '降水集中日',
      text: `近30个观测日中，${peakTrend.value.date}降水最多，为 ${formatPrecipitation(peakTrend.value.precip)}。`,
    })
  }
  if (dominantLevel.value) {
    items.push({
      tone: 'level',
      label: '等级特点',
      text: `降水等级分布中，${dominantLevel.value.level}占 ${dominantLevel.value.count} 个观测日，按真实观测日期统计。`,
    })
  }
  return items
})

function statusCode(reason) {
  return reason?.response?.status || reason?.apiResponse?.code || 0
}

function errorMessage(reason, fallback) {
  if (statusCode(reason) === 404) return ''
  return reason?.message ? `${fallback}：${reason.message}` : fallback
}

function buildParams() {
  const params = {}
  if (province.value) params.province = province.value
  if (city.value) params.city = city.value
  if (district.value) params.district = district.value
  if (startDate.value) params.startDate = startDate.value
  if (endDate.value) params.endDate = endDate.value
  return params
}

function clearResults() {
  core.value = null
  recent.value = []
  trend.value = []
  distribution.value = []
}

function selectDefaultRange(dates) {
  const sortedDates = [...new Set(dates)].sort((left, right) => right.localeCompare(left))
  availableDates.value = sortedDates
  if (!sortedDates.length) {
    startDate.value = ''
    endDate.value = ''
    return
  }
  endDate.value = sortedDates[0]
  startDate.value = sortedDates[Math.min(sortedDates.length - 1, 29)]
}

function dateOptionLabel(value) {
  return String(value || '').replace(/-/g, '/')
}

function handleStartDateChange(value) {
  startDate.value = value
  if (startDate.value && endDate.value && startDate.value > endDate.value) {
    endDate.value = startDate.value
  }
}

function handleEndDateChange(value) {
  endDate.value = value
  if (startDate.value && endDate.value && startDate.value > endDate.value) {
    startDate.value = endDate.value
  }
}

async function loadAvailableDates(version) {
  if (version !== requestVersion.value) return false
  loading.value = true
  try {
    const response = await getRainfallDates({
      ...(province.value ? { province: province.value } : {}),
      ...(city.value ? { city: city.value } : {}),
      ...(district.value ? { district: district.value } : {}),
    })
    if (version !== requestVersion.value) return false
    selectDefaultRange(Array.isArray(response.data) ? response.data : [])
    return true
  } catch (reason) {
    if (version !== requestVersion.value) return false
    availableDates.value = []
    startDate.value = ''
    endDate.value = ''
    if (statusCode(reason) !== 404) error.value = errorMessage(reason, '可用降水日期读取失败')
    loading.value = false
    return false
  }
}

async function loadScopedData(version) {
  const datesLoaded = await loadAvailableDates(version)
  if (version !== requestVersion.value) return
  if (!datesLoaded || !availableDates.value.length) {
    loading.value = false
    return
  }
  await loadData(version)
}

const requestLabels = Object.freeze({
  core: '降水核心指标',
  recent: '近7日降水详情',
  trend: '近30天降水趋势',
  distribution: '降水等级分布',
})

async function settleRequest(key, request) {
  try {
    return { key, status: 'fulfilled', value: await request() }
  } catch (reason) {
    return { key, status: 'rejected', reason }
  }
}

async function loadData(version = ++requestVersion.value) {
  loading.value = true
  error.value = ''
  const params = buildParams()
  const firstBatch = await Promise.all([
    settleRequest('core', () => getRainfallCore(params)),
    settleRequest('recent', () => getRecentRainfall(params)),
  ])
  if (version !== requestVersion.value) return
  const secondBatch = await Promise.all([
    settleRequest('trend', () => getRainfallTrend(params)),
    settleRequest('distribution', () => getRainfallDistribution(params)),
  ])
  const results = [...firstBatch, ...secondBatch]
  if (version !== requestVersion.value) return

  const resultByKey = Object.fromEntries(results.map((result) => [result.key, result]))
  const coreResult = resultByKey.core
  const recentResult = resultByKey.recent
  const trendResult = resultByKey.trend
  const distributionResult = resultByKey.distribution
  core.value = coreResult.status === 'fulfilled' ? coreResult.value.data : null
  recent.value = recentResult.status === 'fulfilled' && Array.isArray(recentResult.value.data)
    ? recentResult.value.data
    : []
  trend.value = trendResult.status === 'fulfilled' && Array.isArray(trendResult.value.data)
    ? trendResult.value.data
    : []
  distribution.value = distributionResult.status === 'fulfilled' && Array.isArray(distributionResult.value.data)
    ? distributionResult.value.data
    : []

  const failed = results.find((result) => result.status === 'rejected' && statusCode(result.reason) !== 404)
  if (failed) {
    const label = requestLabels[failed.key] || '降水分析'
    error.value = `${label}数据读取失败：${failed.reason?.message || '请求失败'}`
  }
  loading.value = false
}

async function handleProvinceChange(value) {
  const version = ++requestVersion.value
  province.value = value
  city.value = ''
  district.value = ''
  cities.value = []
  districts.value = []
  clearResults()
  locationLoading.value = true
  try {
    if (value) {
      const response = await getCities({ province: value })
      if (version !== requestVersion.value) return
      cities.value = Array.isArray(response.data) ? response.data : []
    }
    await loadScopedData(version)
  } catch (reason) {
    if (version === requestVersion.value) error.value = errorMessage(reason, '城市列表读取失败')
  } finally {
    if (version === requestVersion.value) locationLoading.value = false
  }
}

async function handleCityChange(value) {
  const version = ++requestVersion.value
  city.value = value
  district.value = ''
  districts.value = []
  clearResults()
  locationLoading.value = true
  try {
    if (value) {
      try {
        const response = await getDistricts({ province: province.value, city: value })
        if (version !== requestVersion.value) return
        districts.value = Array.isArray(response.data) ? response.data : []
      } catch (reason) {
        if (statusCode(reason) !== 404) throw reason
      }
    }
    await loadScopedData(version)
  } catch (reason) {
    if (version === requestVersion.value) error.value = errorMessage(reason, '区县列表读取失败')
  } finally {
    if (version === requestVersion.value) locationLoading.value = false
  }
}

async function handleDistrictChange(value) {
  const version = ++requestVersion.value
  district.value = value
  clearResults()
  locationLoading.value = true
  try {
    await loadScopedData(version)
  } finally {
    if (version === requestVersion.value) locationLoading.value = false
  }
}

async function loadInitial() {
  loading.value = true
  const version = ++requestVersion.value
  try {
    const response = await getProvinces()
    if (version !== requestVersion.value) return
    provinces.value = Array.isArray(response.data) ? response.data : []
    await loadScopedData(version)
  } catch (reason) {
    if (version === requestVersion.value) error.value = errorMessage(reason, '省份列表读取失败')
    loading.value = false
  }
}

onMounted(loadInitial)
</script>

<template>
  <BigScreenLayout
    page-number="3"
    title="降水分析"
    description="基于历史天气数据分析区域降水情况。"
    header-status="降水历史数据"
    toolbar-status="历史观测分析 · 不代表天气预报"
    :data-date="endDate"
  >
    <template #filters>
      <div class="rainfall-filter-layout" aria-label="降水分析区域筛选">
        <div class="rainfall-filters">
          <span class="rainfall-filter-title">区域筛选</span>
          <label>
            <span>省级行政区</span>
            <select :value="province" :disabled="locationLoading" @change="handleProvinceChange($event.target.value)">
              <option value="">全国</option>
              <option v-for="item in provinces" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>城市</span>
            <select :value="city" :disabled="locationLoading || !province" @change="handleCityChange($event.target.value)">
              <option value="">全部城市</option>
              <option v-for="item in cities" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>
          <label>
            <span>区县</span>
            <select :value="district" :disabled="locationLoading || !city" @change="handleDistrictChange($event.target.value)">
              <option value="">全部区县</option>
              <option v-for="item in districts" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>
          <label class="rainfall-date-range">
            <span>时间范围</span>
            <select
              :value="startDate"
              :disabled="loading || locationLoading || !availableDates.length"
              aria-label="开始日期"
              @change="handleStartDateChange($event.target.value)"
            >
              <option v-if="!startDate" value="" disabled>开始日期</option>
              <option v-for="date in startDateOptions" :key="`start-${date}`" :value="date">{{ dateOptionLabel(date) }}</option>
            </select>
            <b>~</b>
            <select
              :value="endDate"
              :disabled="loading || locationLoading || !availableDates.length"
              aria-label="结束日期"
              @change="handleEndDateChange($event.target.value)"
            >
              <option v-if="!endDate" value="" disabled>结束日期</option>
              <option v-for="date in endDateOptions" :key="`end-${date}`" :value="date">{{ dateOptionLabel(date) }}</option>
            </select>
          </label>
          <button class="rainfall-query-button" type="button" :disabled="loading || locationLoading || !availableDates.length" @click="loadData()">
            查询
          </button>
        </div>
        <span class="rainfall-filter-caption">{{ locationLabel }} · {{ dateLabel }}</span>
      </div>
    </template>

    <p v-if="error" class="rainfall-alert" role="alert">{{ error }}</p>

    <div class="rainfall-page">
      <DashboardPanel title="降水核心指标" :subtitle="`${locationLabel} · ${dateLabel}`">
        <ChartState :loading="loading" :error="''" :empty="!core" empty-message="当前筛选范围暂无降水数据">
          <div class="rainfall-metric-grid">
            <article class="rainfall-metric-card total-card">
              <span class="metric-icon">∑</span>
              <div>
                <span class="metric-label">累计降水量</span>
                <strong>{{ totalPrecipText }}</strong>
                <small>按区域日均降水量累计</small>
              </div>
            </article>
            <article class="rainfall-metric-card average-card">
              <span class="metric-icon">≈</span>
              <div>
                <span class="metric-label">平均降水量</span>
                <strong>{{ avgPrecipText }}</strong>
                <small>来源字段：total_precip</small>
              </div>
            </article>
            <article class="rainfall-metric-card max-card">
              <span class="metric-icon">↑</span>
              <div>
                <span class="metric-label">最大单日降水</span>
                <strong>{{ maxPrecipText }}</strong>
                <small>出现日期：{{ core?.maxPrecipDate || '--' }}</small>
              </div>
            </article>
            <article class="rainfall-metric-card days-card">
              <span class="metric-icon">☔</span>
              <div>
                <span class="metric-label">降水天数</span>
                <strong>{{ rainyDaysText }} 天</strong>
                <small>区域日均降水量大于 0 的观测日</small>
              </div>
            </article>
          </div>
        </ChartState>
      </DashboardPanel>

      <div class="rainfall-analysis-grid">
        <DashboardPanel class="rainfall-recent-panel" title="近7日降水情况" subtitle="weather_data · 实际观测日记录">
          <ChartState :loading="loading" :error="''" :empty="!recent.length" empty-message="当前筛选范围暂无观测数据">
            <div class="recent-rainfall-grid">
              <article v-for="row in recent" :key="row.date" class="recent-rainfall-card">
                <div class="recent-date">{{ row.date }}</div>
                <div :class="['recent-weather-icon', weatherTypeClass(row.weather)]">{{ weatherSymbol(row.weather) }}</div>
                <div class="recent-weather-name">{{ row.weather || '天气未记录' }}</div>
                <strong class="recent-precip">{{ formatPrecipitation(row.precip) }}</strong>
                <small>区域日平均降水量</small>
              </article>
            </div>
          </ChartState>
        </DashboardPanel>

        <DashboardPanel class="rainfall-distribution-panel" title="降水分布" subtitle="近30天降水日数统计">
          <RainfallDistributionChart :data="distribution" :loading="loading" :error="''" />
        </DashboardPanel>

        <DashboardPanel class="rainfall-trend-panel" title="降水量变化趋势" subtitle="近30天区域日均降水">
          <RainfallTrendChart :data="trend" :loading="loading" :error="''" />
        </DashboardPanel>

        <div class="rainfall-side-stack">
          <DashboardPanel class="rainfall-standard-panel" title="降水等级标准" subtitle="依据《降水量等级划分标准》">
            <div class="rainfall-standard-grid">
              <div
                v-for="item in rainfallStandards"
                :key="item.level"
                :class="['rainfall-standard-item', item.tone]"
              >
                <strong>{{ item.level }}</strong>
                <span>{{ item.range }}</span>
              </div>
            </div>
          </DashboardPanel>

          <DashboardPanel class="rainfall-conclusion-panel" title="降水分析结论" subtitle="根据真实观测数据计算">
            <ChartState :loading="loading" :error="''" :empty="!conclusionItems.length" empty-message="暂无足够真实数据生成结论">
              <div class="rainfall-conclusions">
                <div v-for="item in conclusionItems" :key="item.label" :class="['conclusion-item', item.tone]">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.text }}</span>
                </div>
              </div>
            </ChartState>
          </DashboardPanel>
        </div>
      </div>
    </div>
  </BigScreenLayout>
</template>

<style scoped>
.rainfall-filter-layout { display: flex; width: 100%; align-items: center; gap: 10px; padding: 7px 13px; background: linear-gradient(90deg, rgb(6 42 81 / 92%), rgb(4 28 61 / 84%)); border: 1px solid rgb(35 143 211 / 58%); border-radius: 6px; box-shadow: inset 0 0 16px rgb(30 132 204 / 10%), 0 5px 16px rgb(0 8 26 / 18%); }
.rainfall-filters { display: flex; min-width: 0; flex: 1; align-items: center; flex-wrap: wrap; gap: 7px 13px; }
.rainfall-filter-title { color: var(--accent-cyan); font-size: 13px; font-weight: 700; white-space: nowrap; }
.rainfall-filters label { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); font-size: 11px; white-space: nowrap; }
.rainfall-filters select { height: 32px; min-width: 116px; padding: 5px 24px 5px 9px; color: var(--text-primary); font: inherit; background: linear-gradient(180deg, #0b315f, #08254b); border: 1px solid rgb(45 151 216 / 68%); border-radius: 4px; outline: none; }
.rainfall-filters select:focus { border-color: var(--accent-cyan); box-shadow: 0 0 0 2px rgb(52 210 255 / 16%); }
.rainfall-date-range { gap: 5px !important; }
.rainfall-date-range select { width: 136px; min-width: 136px; }
.rainfall-date-range b { color: var(--text-muted); font-weight: 400; }
.rainfall-query-button { min-width: 62px; height: 32px; padding: 0 13px; color: #eafaff; font: inherit; font-weight: 700; background: linear-gradient(180deg, #1579c1, #0b4f96); border: 1px solid #34d2ff; border-radius: 4px; cursor: pointer; }
.rainfall-query-button:disabled { cursor: not-allowed; opacity: 0.55; }
.rainfall-filter-caption { color: var(--text-muted); font-size: 10px; white-space: nowrap; }
.rainfall-alert { margin: 0; padding: 8px 12px; color: var(--danger); font-size: 12px; background: rgb(100 24 48 / 32%); border: 1px solid rgb(255 125 134 / 40%); border-radius: 6px; }
.rainfall-page { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: 12px; }
.rainfall-metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.rainfall-metric-card { display: flex; min-height: 104px; align-items: center; gap: 13px; padding: 14px 15px; background: linear-gradient(145deg, rgb(7 49 94 / 80%), rgb(3 26 58 / 78%)); border: 1px solid rgb(36 145 211 / 52%); border-radius: 7px; box-shadow: inset 0 0 22px rgb(42 163 223 / 8%); }
.metric-icon { display: grid; width: 48px; height: 48px; flex: 0 0 48px; place-items: center; color: var(--accent-cyan); font-size: 24px; font-weight: 700; background: rgb(12 94 157 / 38%); border: 1px solid rgb(73 205 255 / 45%); border-radius: 50%; }
.metric-label { display: block; color: var(--text-secondary); font-size: 12px; }
.rainfall-metric-card strong { display: block; margin-top: 4px; color: var(--text-primary); font-size: 25px; line-height: 1.1; }
.rainfall-metric-card small { display: block; margin-top: 6px; color: var(--text-muted); font-size: 10px; }
.average-card .metric-icon, .average-card strong { color: #70c5ff; }
.max-card .metric-icon, .max-card strong { color: #ff9c75; }
.days-card .metric-icon, .days-card strong { color: #54e0b2; }
.recent-rainfall-grid { display: grid; flex: 1 1 auto; grid-template-columns: repeat(7, minmax(0, 1fr)); align-items: stretch; gap: 9px; }
.recent-rainfall-card { height: 100%; min-height: 157px; padding: 10px 8px; text-align: center; background: rgb(4 36 74 / 72%); border: 1px solid rgb(37 143 210 / 45%); border-radius: 6px; }
.recent-rainfall-card:last-child { border-color: var(--accent-cyan); box-shadow: 0 0 14px rgb(35 205 255 / 13%); }
.recent-date { color: var(--text-primary); font-size: 12px; font-weight: 700; }
.recent-weather-icon { height: 36px; margin-top: 7px; color: var(--accent-cyan); font-size: 29px; line-height: 36px; }
.recent-weather-icon.weather-icon-sun { color: #ffc45e; }
.recent-weather-icon.weather-icon-rain, .recent-weather-icon.weather-icon-snow { color: #7abaff; }
.recent-weather-icon.weather-icon-cloud, .recent-weather-icon.weather-icon-partly { color: #b8d8f4; }
.recent-weather-name { min-height: 18px; margin-top: 3px; color: var(--text-secondary); font-size: 11px; }
.recent-precip { display: block; margin-top: 7px; color: #8fd4ff; font-size: 15px; }
.recent-rainfall-card small { color: var(--text-muted); font-size: 9px; }
.rainfall-analysis-grid { display: grid; min-height: 0; grid-template-columns: minmax(0, 1.72fr) minmax(360px, 1fr); grid-template-areas: 'recent distribution' 'trend side'; gap: 12px; }
.rainfall-recent-panel { grid-area: recent; min-height: 285px; }
.rainfall-distribution-panel { grid-area: distribution; min-height: 285px; }
.rainfall-trend-panel { grid-area: trend; min-height: 285px; }
.rainfall-recent-panel :deep(.panel-body), .rainfall-distribution-panel :deep(.panel-body), .rainfall-trend-panel :deep(.panel-body) { min-height: 220px; }
.rainfall-side-stack { display: grid; min-width: 0; min-height: 285px; grid-area: side; grid-template-rows: auto minmax(0, 1fr); gap: 12px; }
.rainfall-standard-panel, .rainfall-conclusion-panel { min-height: 0; }
.rainfall-standard-panel :deep(.panel-body) { padding: 9px 10px; }
.rainfall-standard-grid { display: grid; min-height: 0; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; }
.rainfall-standard-item { display: flex; min-width: 0; min-height: 71px; align-items: center; justify-content: space-between; flex-direction: column; padding: 6px 3px 5px; color: var(--text-primary); text-align: center; background: rgb(9 45 85 / 78%); border: 1px solid rgb(45 151 216 / 56%); border-radius: 5px; }
.rainfall-standard-item strong { display: block; width: 100%; padding: 4px 1px; font-size: 10px; font-weight: 700; white-space: nowrap; background: rgb(62 137 190 / 35%); border-radius: 3px; }
.rainfall-standard-item span { color: var(--text-secondary); font-size: 9px; line-height: 1.3; }
.rainfall-standard-item.light strong { background: #1596cd; }
.rainfall-standard-item.moderate strong { background: #286bd7; }
.rainfall-standard-item.heavy strong { color: #15243c; background: #f2b629; }
.rainfall-standard-item.storm strong { color: #561a2a; background: #f15968; }
.rainfall-standard-item.downpour strong { background: #7d28bf; }
.rainfall-standard-item.extreme strong { background: #7623ce; }
.rainfall-conclusion-panel :deep(.panel-body) { padding: 9px 10px; }
.rainfall-conclusions { display: grid; gap: 8px; }
.conclusion-item { display: grid; grid-template-columns: 88px 1fr; gap: 10px; align-items: center; min-height: 40px; padding: 8px 12px; color: var(--text-secondary); font-size: 12px; background: rgb(5 37 76 / 68%); border: 1px solid rgb(42 148 211 / 42%); border-radius: 6px; }
.conclusion-item strong { color: var(--accent-cyan); }
.conclusion-item.peak strong { color: #ffb16d; }
.conclusion-item.level strong { color: #54e0b2; }
@media (max-width: 1040px) { .rainfall-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .recent-rainfall-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } .rainfall-analysis-grid { grid-template-columns: 1fr; grid-template-areas: 'recent' 'distribution' 'trend' 'side'; } .rainfall-side-stack { min-height: auto; grid-template-rows: auto auto; } .rainfall-filter-layout { align-items: flex-start; flex-direction: column; } .rainfall-filter-caption { white-space: normal; } }
@media (max-width: 680px) { .rainfall-filters { align-items: flex-start; flex-direction: column; } .rainfall-filters label { justify-content: space-between; width: 100%; } .rainfall-filters select { flex: 1; max-width: none; } .rainfall-date-range { flex-wrap: wrap; } .rainfall-date-range select { width: auto; } .rainfall-metric-grid, .recent-rainfall-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .conclusion-item { grid-template-columns: 1fr; gap: 4px; } }
</style>
