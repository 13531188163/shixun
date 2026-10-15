<script setup>
import { computed, onMounted, ref } from 'vue'

import { getCities, getDistricts, getProvinces } from '../api/location'
import {
  getRecentTemperature,
  getTemperatureAverage,
  getTemperatureDates,
  getTemperatureExtremes,
  getTemperatureMonthly,
  getTemperatureTrend,
} from '../api/temperature'
import BigScreenLayout from '../components/layout/BigScreenLayout.vue'
import DashboardPanel from '../components/dashboard/DashboardPanel.vue'
import ChartState from '../components/dashboard/ChartState.vue'
import WeatherTrendChart from '../components/dashboard/WeatherTrendChart.vue'
import TemperatureMonthlyChart from '../components/temperature/TemperatureMonthlyChart.vue'
import { formatTemperature, weatherSymbol, weatherTypeClass } from '../utils/formatters'

const provinces = ref([])
const cities = ref([])
const districts = ref([])
const availableDates = ref([])

const province = ref('')
const city = ref('')
const district = ref('')
const startDate = ref('')
const endDate = ref('')

const average = ref(null)
const extremes = ref(null)
const trend = ref([])
const monthly = ref([])
const recent = ref([])
const loading = ref(true)
const locationLoading = ref(false)
const error = ref('')
const requestVersion = ref(0)

const monthLabels = Array.from({ length: 12 }, (_, index) => `${index + 1}月`)
const DIRECT_MUNICIPALITIES = new Set(['北京', '北京市', '上海', '上海市', '天津', '天津市', '重庆', '重庆市'])

function provinceLabel(value) {
  const name = String(value || '')
  if (!DIRECT_MUNICIPALITIES.has(name)) return name
  return name.endsWith('市') ? name : `${name}市`
}

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

const averageText = computed(() => formatTemperature(average.value?.avgTemp))
const maxText = computed(() => formatTemperature(extremes.value?.maxTemperature))
const minText = computed(() => formatTemperature(extremes.value?.minTemperature))
const rangeValue = computed(() => {
  const max = Number(extremes.value?.maxTemperature)
  const min = Number(extremes.value?.minTemperature)
  if (!Number.isFinite(max) || !Number.isFinite(min)) return null
  return Number((max - min).toFixed(2))
})
const rangeText = computed(() => formatTemperature(rangeValue.value))

const monthlyChartData = computed(() => {
  if (!monthly.value.length) return []
  const rows = new Map(monthly.value.map((row) => [row.month, row]))
  return monthLabels.map((month) => ({
    month,
    avgTemp: rows.get(month)?.avgTemp ?? null,
  }))
})

const conclusionItems = computed(() => {
  const items = []
  if (average.value?.avgTemp !== null && average.value?.avgTemp !== undefined) {
    items.push({
      tone: 'warm',
      label: '平均温度',
      text: `${locationLabel.value}在${dateLabel.value}的平均温度为 ${formatTemperature(average.value.avgTemp)}。`,
    })
  }
  if (rangeValue.value !== null) {
    items.push({
      tone: 'cool',
      label: '温差范围',
      text: `筛选范围内最高温与最低温相差 ${rangeText.value}（最高 ${maxText.value}，最低 ${minText.value}）。`,
    })
  }
  const validTrend = trend.value.filter((row) => Number.isFinite(Number(row.maxTemp)) && Number.isFinite(Number(row.minTemp)))
  if (validTrend.length >= 2) {
    const first = (Number(validTrend[0].maxTemp) + Number(validTrend[0].minTemp)) / 2
    const lastRow = validTrend[validTrend.length - 1]
    const last = (Number(lastRow.maxTemp) + Number(lastRow.minTemp)) / 2
    const change = Number((last - first).toFixed(2))
    const direction = change > 0 ? '上升' : change < 0 ? '下降' : '基本稳定'
    items.push({
      tone: 'green',
      label: '趋势情况',
      text: `近${validTrend.length}个观测日的日均温度由 ${formatTemperature(first)} 变为 ${formatTemperature(last)}，整体${direction}。`,
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
  average.value = null
  extremes.value = null
  trend.value = []
  monthly.value = []
  recent.value = []
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
  return String(value || '').replaceAll('-', '/')
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
  if (version !== requestVersion.value) return
  loading.value = true
  try {
    const response = await getTemperatureDates({
      ...(province.value ? { province: province.value } : {}),
      ...(city.value ? { city: city.value } : {}),
      ...(district.value ? { district: district.value } : {}),
    })
    if (version !== requestVersion.value) return
    selectDefaultRange(Array.isArray(response.data) ? response.data : [])
    return true
  } catch (reason) {
    if (version !== requestVersion.value) return
    availableDates.value = []
    startDate.value = ''
    endDate.value = ''
    if (statusCode(reason) !== 404) error.value = errorMessage(reason, '可用日期读取失败')
    loading.value = false
    return false
  }
}

async function loadScopedData(version) {
  const datesLoaded = await loadAvailableDates(version)
  if (version !== requestVersion.value) return
  // 日期列表为空或读取失败时不发起无日期边界的全表统计，避免退化为慢查询。
  if (!datesLoaded || !availableDates.value.length) {
    loading.value = false
    return
  }
  await loadData(version)
}

const temperatureRequestLabels = Object.freeze({
  average: '平均温度',
  extremes: '历史极值',
  trend: '近30天温度趋势',
  monthly: '月度平均温度趋势',
  recent: '近7天天气温度',
})

async function settleTemperatureRequest(key, request) {
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
  // 数据库连接由后端按请求创建。分两批请求，避免一次页面加载同时
  // 建立五条连接；单个接口失败仍保留其它成功结果。
  const firstBatch = await Promise.all([
    settleTemperatureRequest('average', () => getTemperatureAverage(params)),
    settleTemperatureRequest('extremes', () => getTemperatureExtremes(params)),
  ])
  if (version !== requestVersion.value) return
  const secondBatch = await Promise.all([
    settleTemperatureRequest('trend', () => getTemperatureTrend(params)),
    settleTemperatureRequest('monthly', () => getTemperatureMonthly(params)),
  ])
  if (version !== requestVersion.value) return
  const recentResult = await settleTemperatureRequest('recent', () => getRecentTemperature(params))
  const results = [...firstBatch, ...secondBatch, recentResult]
  if (version !== requestVersion.value) return

  const resultByKey = Object.fromEntries(results.map((result) => [result.key, result]))
  const averageResult = resultByKey.average
  const extremesResult = resultByKey.extremes
  const trendResult = resultByKey.trend
  const monthlyResult = resultByKey.monthly
  const recentTemperatureResult = resultByKey.recent
  average.value = averageResult.status === 'fulfilled' ? averageResult.value.data : null
  extremes.value = extremesResult.status === 'fulfilled' ? extremesResult.value.data : null
  trend.value = trendResult.status === 'fulfilled' && Array.isArray(trendResult.value.data) ? trendResult.value.data : []
  monthly.value = monthlyResult.status === 'fulfilled' && Array.isArray(monthlyResult.value.data) ? monthlyResult.value.data : []
  recent.value = recentTemperatureResult.status === 'fulfilled' && Array.isArray(recentTemperatureResult.value.data)
    ? recentTemperatureResult.value.data
    : []

  const failed = results.find((result) => result.status === 'rejected' && statusCode(result.reason) !== 404)
  if (failed) {
    const label = temperatureRequestLabels[failed.key] || '温度分析'
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
        districts.value = []
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
    page-number="2"
    title="温度分析"
    description="基于历史天气数据分析区域温度变化趋势。"
    header-status="温度历史数据"
    toolbar-status="历史观测分析 · 不代表天气预报"
    :data-date="endDate"
  >
    <template #filters>
      <div class="temperature-filter-layout" aria-label="温度分析区域筛选">
        <div class="temperature-filters">
          <span class="temperature-filter-title">区域筛选</span>
          <label>
            <span>省级行政区</span>
            <select :value="province" :disabled="locationLoading" @change="handleProvinceChange($event.target.value)">
              <option value="">全国</option>
              <option v-for="item in provinces" :key="item" :value="item">{{ provinceLabel(item) }}</option>
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
          <label class="temperature-date-range">
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
          <button class="temperature-query-button" type="button" :disabled="loading || locationLoading" @click="loadData()">
            查询
          </button>
        </div>
        <span class="temperature-filter-caption">{{ locationLabel }} · {{ dateLabel }}</span>
      </div>
    </template>

    <p v-if="error" class="temperature-alert" role="alert">{{ error }}</p>

    <div class="temperature-page">
      <DashboardPanel title="温度核心指标" :subtitle="`${locationLabel} · ${dateLabel}`">
        <ChartState :loading="loading" :error="''" :empty="!average && !extremes">
          <div class="temperature-metric-grid">
            <article class="temperature-metric-card average-card">
              <span class="metric-icon">℃</span>
              <div>
                <span class="metric-label">平均温度</span>
                <strong>{{ averageText }}</strong>
                <small>最高/最低平均：{{ formatTemperature(average?.avgMaxTemp) }} / {{ formatTemperature(average?.avgMinTemp) }}</small>
              </div>
            </article>
            <article class="temperature-metric-card max-card">
              <span class="metric-icon">↑</span>
              <div>
                <span class="metric-label">历史最高温</span>
                <strong>{{ maxText }}</strong>
                <small>出现日期：{{ extremes?.maxDate || '--' }}</small>
              </div>
            </article>
            <article class="temperature-metric-card min-card">
              <span class="metric-icon">↓</span>
              <div>
                <span class="metric-label">历史最低温</span>
                <strong>{{ minText }}</strong>
                <small>出现日期：{{ extremes?.minDate || '--' }}</small>
              </div>
            </article>
            <article class="temperature-metric-card range-card">
              <span class="metric-icon">↕</span>
              <div>
                <span class="metric-label">最大温差</span>
                <strong>{{ rangeText }}</strong>
                <small>最高 {{ maxText }} / 最低 {{ minText }}</small>
              </div>
            </article>
          </div>
        </ChartState>
      </DashboardPanel>

      <DashboardPanel title="近 7 天天气温度详情" subtitle="weather_data · 实际观测日记录">
        <ChartState :loading="loading" :error="''" :empty="!recent.length" empty-message="当前筛选范围暂无观测数据">
          <div class="recent-temperature-grid">
            <article v-for="row in recent" :key="row.date" class="recent-temperature-card">
              <div class="recent-date">{{ row.date }}</div>
              <div :class="['recent-weather-icon', weatherTypeClass(row.weather)]">{{ weatherSymbol(row.weather) }}</div>
              <div class="recent-weather-name">{{ row.weather || '天气未记录' }}</div>
              <div class="recent-temperature-values">
                <span class="recent-max">{{ formatTemperature(row.maxTemp) }}</span>
                <span class="recent-min">{{ formatTemperature(row.minTemp) }}</span>
              </div>
              <small>最高温&nbsp;&nbsp;&nbsp;最低温</small>
            </article>
          </div>
        </ChartState>
      </DashboardPanel>

      <div class="temperature-chart-grid">
        <DashboardPanel title="近 30 天最高温 / 最低温趋势" subtitle="按观测日期聚合，不代表天气预报">
          <WeatherTrendChart :data="trend" :loading="loading" :error="''" />
        </DashboardPanel>
        <DashboardPanel title="月度平均温度趋势" subtitle="按实际观测日期月份分组">
          <TemperatureMonthlyChart :data="monthlyChartData" :loading="loading" :error="''" />
        </DashboardPanel>
      </div>

      <DashboardPanel title="温度分析结论" subtitle="根据当前筛选范围内的真实观测数据计算">
        <ChartState :loading="loading" :error="''" :empty="!conclusionItems.length" empty-message="暂无足够真实数据生成结论">
          <div class="temperature-conclusions">
            <div v-for="item in conclusionItems" :key="item.label" :class="['conclusion-item', item.tone]">
              <strong>{{ item.label }}</strong>
              <span>{{ item.text }}</span>
            </div>
          </div>
        </ChartState>
      </DashboardPanel>
    </div>
  </BigScreenLayout>
</template>

<style scoped>
.temperature-filter-layout { display: flex; width: 100%; align-items: center; gap: 10px; padding: 7px 13px; background: linear-gradient(90deg, rgb(6 42 81 / 92%), rgb(4 28 61 / 84%)); border: 1px solid rgb(35 143 211 / 58%); border-radius: 6px; box-shadow: inset 0 0 16px rgb(30 132 204 / 10%), 0 5px 16px rgb(0 8 26 / 18%); }
.temperature-filters { display: flex; min-width: 0; flex: 1; align-items: center; flex-wrap: wrap; gap: 7px 13px; }
.temperature-filter-title { color: var(--accent-cyan); font-size: 13px; font-weight: 700; white-space: nowrap; }
.temperature-filters label { display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); font-size: 11px; white-space: nowrap; }
.temperature-filters select, .temperature-filters input { height: 32px; padding: 5px 9px; color: var(--text-primary); font: inherit; background: linear-gradient(180deg, #0b315f, #08254b); border: 1px solid rgb(45 151 216 / 68%); border-radius: 4px; outline: none; }
.temperature-filters select { min-width: 116px; padding-right: 24px; }
.temperature-filters input { color-scheme: dark; }
.temperature-filters select:focus, .temperature-filters input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 0 2px rgb(52 210 255 / 16%); }
.temperature-date-range { gap: 5px !important; }
.temperature-date-range select { width: 136px; min-width: 136px; }
.temperature-date-range b { color: var(--text-muted); font-weight: 400; }
.temperature-query-button { min-width: 62px; height: 32px; padding: 0 13px; color: #eafaff; font: inherit; font-weight: 700; background: linear-gradient(180deg, #1579c1, #0b4f96); border: 1px solid #34d2ff; border-radius: 4px; cursor: pointer; }
.temperature-query-button:disabled { cursor: not-allowed; opacity: 0.55; }
.temperature-filter-caption { color: var(--text-muted); font-size: 10px; white-space: nowrap; }
.temperature-alert { margin: 0; padding: 8px 12px; color: var(--danger); font-size: 12px; background: rgb(100 24 48 / 32%); border: 1px solid rgb(255 125 134 / 40%); border-radius: 6px; }
.temperature-page { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: 12px; }
.temperature-metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.temperature-metric-card { display: flex; min-height: 104px; align-items: center; gap: 13px; padding: 14px 15px; background: linear-gradient(145deg, rgb(7 49 94 / 80%), rgb(3 26 58 / 78%)); border: 1px solid rgb(36 145 211 / 52%); border-radius: 7px; box-shadow: inset 0 0 22px rgb(42 163 223 / 8%); }
.metric-icon { display: grid; width: 48px; height: 48px; flex: 0 0 48px; place-items: center; color: var(--accent-cyan); font-size: 24px; font-weight: 700; background: rgb(12 94 157 / 38%); border: 1px solid rgb(73 205 255 / 45%); border-radius: 50%; }
.metric-label { display: block; color: var(--text-secondary); font-size: 12px; }
.temperature-metric-card strong { display: block; margin-top: 4px; color: var(--text-primary); font-size: 25px; line-height: 1.1; }
.temperature-metric-card small { display: block; margin-top: 6px; color: var(--text-muted); font-size: 10px; }
.max-card .metric-icon, .max-card strong { color: #ff9c75; }
.min-card .metric-icon, .min-card strong { color: #70c5ff; }
.range-card .metric-icon, .range-card strong { color: #bd9bff; }
.recent-temperature-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 9px; }
.recent-temperature-card { min-height: 157px; padding: 10px 8px; text-align: center; background: rgb(4 36 74 / 72%); border: 1px solid rgb(37 143 210 / 45%); border-radius: 6px; }
.recent-temperature-card:last-child { border-color: var(--accent-cyan); box-shadow: 0 0 14px rgb(35 205 255 / 13%); }
.recent-date { color: var(--text-primary); font-size: 12px; font-weight: 700; }
.recent-weather-icon { height: 36px; margin-top: 7px; color: var(--accent-cyan); font-size: 29px; line-height: 36px; }
.recent-weather-icon.weather-icon-sun { color: #ffc45e; }
.recent-weather-icon.weather-icon-rain, .recent-weather-icon.weather-icon-snow { color: #7abaff; }
.recent-weather-icon.weather-icon-cloud, .recent-weather-icon.weather-icon-partly { color: #b8d8f4; }
.recent-weather-name { min-height: 18px; margin-top: 3px; color: var(--text-secondary); font-size: 11px; }
.recent-temperature-values { display: flex; justify-content: center; gap: 12px; margin-top: 7px; font-size: 15px; font-weight: 700; }
.recent-max { color: #ff8e71; }
.recent-min { color: #5bc7ff; }
.recent-temperature-card small { color: var(--text-muted); font-size: 9px; }
.temperature-chart-grid { display: grid; min-height: 285px; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.temperature-chart-grid :deep(.dashboard-panel) { min-height: 285px; }
.temperature-chart-grid :deep(.panel-body) { min-height: 220px; }
.temperature-conclusions { display: grid; gap: 8px; }
.conclusion-item { display: grid; grid-template-columns: 88px 1fr; gap: 10px; align-items: center; min-height: 40px; padding: 8px 12px; color: var(--text-secondary); font-size: 12px; background: rgb(5 37 76 / 68%); border: 1px solid rgb(42 148 211 / 42%); border-radius: 6px; }
.conclusion-item strong { color: var(--accent-cyan); }
.conclusion-item.warm strong { color: #ffb16d; }
.conclusion-item.cool strong { color: #7bc9ff; }
.conclusion-item.green strong { color: #54e0b2; }
@media (max-width: 1040px) { .temperature-metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .recent-temperature-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); } .temperature-chart-grid { grid-template-columns: 1fr; } .temperature-filter-layout { align-items: flex-start; flex-direction: column; } .temperature-filter-caption { white-space: normal; } }
@media (max-width: 680px) { .temperature-filters { align-items: flex-start; flex-direction: column; } .temperature-filters label { justify-content: space-between; width: 100%; } .temperature-filters select, .temperature-filters input { flex: 1; max-width: none; } .temperature-date-range { flex-wrap: wrap; } .temperature-date-range select { width: auto; } .temperature-metric-grid, .recent-temperature-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .conclusion-item { grid-template-columns: 1fr; gap: 4px; } }
</style>
