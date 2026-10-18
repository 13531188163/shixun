<script setup>
import { computed, onMounted, ref } from 'vue'
import BigScreenLayout from '../components/layout/BigScreenLayout.vue'
import ChartState from '../components/dashboard/ChartState.vue'
import DashboardPanel from '../components/dashboard/DashboardPanel.vue'
import { getComparison, getComparisonLocations } from '../api/comparison'
import { useEChart } from '../utils/chart'
import {
  RADAR_FIELDS,
  buildRadarValues,
  finiteNumber,
  metricValue,
  selectRadarDimensions,
} from '../utils/comparisonRadar'

const locations = ref([])
const selectedKeys = ref([])
const startDate = ref('')
const endDate = ref('')
const result = ref(null)
const loading = ref(false)
const error = ref('')
const requestVersion = ref(0)

const radarElement = ref(null)
const barElement = ref(null)
const monthElement = ref(null)

const cities = computed(() => result.value?.cities || [])
const hasCommonDates = computed(() => Number(result.value?.dataCoverage?.commonDays) > 0)
const radarBaseline = computed(() => result.value?.radarBaseline || {})
const aqiSnapshotTimeText = computed(() => cities.value.length
  ? cities.value.map((city) => `${cityLabel(city)}：${city?.aqiSnapshot?.createdAt || '暂无快照'}`).join('；')
  : '暂无快照')
const metrics = (city) => city?.weatherMetrics || {}
const metricNumber = metricValue

function formatValue(value, suffix = '', digits = 2) {
  const number = finiteNumber(value)
  return number === null ? '暂无数据' : `${number.toFixed(digits)}${suffix}`
}

function formatAqi(value) {
  const number = finiteNumber(value)
  return number === null ? '暂无AQI快照' : String(Math.round(number))
}

function formatDays(value) {
  const number = finiteNumber(value)
  return number === null ? '暂无数据' : String(Math.round(number))
}

function cityValidDays(city) {
  const coverage = result.value?.dataCoverage?.cities?.find((item) => item.key === city?.key)
  return formatDays(coverage?.validDays)
}

const colors = ['#ff6b7a', '#38bdf8', '#ffc04d', '#34e0a1']
const color = (index) => colors[index % colors.length]
const cityLabel = (city) => (city ? `${city.province} · ${city.city}` : '暂无地区')

const metricGroups = [
  { key: 'avgTempEstimate', title: '平均温度对比', subtitle: '共同日期估算平均值', unit: ' ℃', digits: 2 },
  { key: 'totalPrecip', title: '降水量对比', subtitle: '区域日均降水累计估计', unit: ' mm', digits: 2 },
  { key: 'avgWind', title: '平均风速对比', subtitle: '共同日期区域日均值', unit: ' m/s', digits: 2 },
  { key: 'aqiSnapshot', title: 'AQI快照对比', subtitle: '独立固定快照，不属于天气日期范围', unit: '', digits: 0 },
]

function groupValue(city, group) {
  const value = metricNumber(city, group.key)
  return group.key === 'aqiSnapshot' ? formatAqi(value) : formatValue(value, group.unit, group.digits)
}

function addCity() {
  const next = locations.value.find((item) => !selectedKeys.value.includes(item.key))
  if (next && selectedKeys.value.length < 4) selectedKeys.value.push(next.key)
}

function removeCity(index) {
  if (selectedKeys.value.length > 2) selectedKeys.value.splice(index, 1)
}

function buildParams() {
  return {
    cities: selectedKeys.value.join(','),
    ...(startDate.value ? { startDate: startDate.value } : {}),
    ...(endDate.value ? { endDate: endDate.value } : {}),
  }
}

async function query() {
  if (selectedKeys.value.length < 2) {
    error.value = '请至少选择两个真实天气城市进行对比'
    return
  }
  const token = ++requestVersion.value
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const response = await getComparison(buildParams())
    if (token !== requestVersion.value) return
    result.value = response.data || null
    if (!startDate.value) startDate.value = result.value?.weatherPeriod?.startDate || ''
    if (!endDate.value) endDate.value = result.value?.weatherPeriod?.endDate || ''
  } catch (reason) {
    if (token === requestVersion.value) error.value = reason?.message || '区域对比数据读取失败'
  } finally {
    if (token === requestVersion.value) loading.value = false
  }
}

// 雷达图只保留所有所选城市都有有效值的维度，避免将缺失值当作0参与比较。
const radarFields = RADAR_FIELDS
const radarDimensions = computed(() => selectRadarDimensions(cities.value, radarBaseline.value, radarFields))
const radarValues = computed(() => buildRadarValues(cities.value, radarDimensions.value, radarBaseline.value))
const radarReady = computed(() => radarDimensions.value.length >= 3
  && radarValues.value.length === cities.value.length
  && radarValues.value.every((values) => values.length === radarDimensions.value.length && values.every((value) => Number.isFinite(value))))
const radarExcluded = computed(() =>
  radarFields.filter((field) => !radarDimensions.value.some((item) => item.key === field.key)).map((field) => field.name),
)

function rawMetricText(city, field) {
  const value = metricNumber(city, field.key)
  return field.key === 'aqiSnapshot' ? formatAqi(value) : formatValue(value, field.unit, field.digits)
}

function radarOption() {
  const dimensions = radarDimensions.value
  const values = radarValues.value
  return {
    animation: false,
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const city = cities.value.find((item) => cityLabel(item) === params.name)
        if (!city) return params.name || ''
        return [cityLabel(city), ...radarFields.map((field) => `${field.name}：${rawMetricText(city, field)}`)].join('<br/>')
      },
    },
    legend: { bottom: 0, type: 'scroll', textStyle: { color: '#b8d9ef' }, data: cities.value.map(cityLabel) },
    radar: {
      indicator: dimensions.map((field) => ({ name: field.name, max: 1 })),
      center: ['50%', '44%'],
      radius: '61%',
      axisName: { color: '#cfeeff', fontSize: 11 },
      splitNumber: 4,
      splitArea: { areaStyle: { color: ['rgba(18,75,125,.22)', 'rgba(5,36,75,.16)'] } },
      splitLine: { lineStyle: { color: 'rgba(67,171,224,.42)' } },
      axisLine: { lineStyle: { color: 'rgba(67,171,224,.42)' } },
    },
    series: [{
      type: 'radar',
      data: cities.value.map((city, index) => ({
        name: cityLabel(city),
        value: values[index],
        lineStyle: { color: color(index), width: 2 },
        itemStyle: { color: color(index) },
        areaStyle: { color: color(index), opacity: 0.12 },
      })),
    }],
  }
}

function barOption() {
  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const name = params?.[0]?.axisValue || ''
        const city = cities.value.find((item) => cityLabel(item) === name)
        if (!city) return name
        return [
          name,
          `估算平均温度：${formatValue(metricNumber(city, 'avgTempEstimate'), ' ℃')}`,
          `AQI固定快照：${formatAqi(metricNumber(city, 'aqiSnapshot'))}`,
        ].join('<br/>')
      },
    },
    legend: { top: 0, textStyle: { color: '#b8d9ef' } },
    grid: { left: 45, right: 48, top: 40, bottom: 58, containLabel: true },
    xAxis: {
      type: 'category',
      data: cities.value.map(cityLabel),
      axisLabel: { color: '#b8d9ef', interval: 0, rotate: cities.value.some((city) => cityLabel(city).length > 8) ? 22 : 0 },
      axisLine: { lineStyle: { color: 'rgba(91,180,232,.6)' } },
    },
    yAxis: [
      { type: 'value', name: '温度 ℃', axisLabel: { color: '#b8d9ef' }, nameTextStyle: { color: '#8cb9d5' } },
      { type: 'value', name: 'AQI', axisLabel: { color: '#b8d9ef' }, nameTextStyle: { color: '#8cb9d5' } },
    ],
    series: [
      { name: '估算平均温度', type: 'bar', barMaxWidth: 28, data: cities.value.map((city) => metricNumber(city, 'avgTempEstimate')), itemStyle: { color: '#38bdf8' } },
      { name: 'AQI固定快照', type: 'bar', yAxisIndex: 1, barMaxWidth: 28, data: cities.value.map((city) => metricNumber(city, 'aqiSnapshot')), itemStyle: { color: '#ffc04d' } },
    ],
  }
}

function monthLabel(value) {
  return /^\d{4}-\d{2}$/.test(value) ? `${value.slice(0, 4)}年${value.slice(5)}月` : value
}

function monthOption() {
  const months = [...new Set(cities.value.flatMap((city) => (city.monthlyPrecip || []).map((item) => item.month)))].sort()
  const hasZoom = months.length > 8
  return {
    animation: false,
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const lines = [monthLabel(params?.[0]?.axisValue || '')]
        params.forEach((item) => lines.push(`${item.seriesName}：${formatValue(item.value, ' mm')}`))
        return lines.join('<br/>')
      },
    },
    legend: { top: 0, type: 'scroll', textStyle: { color: '#b8d9ef' } },
    grid: { left: 48, right: 20, top: 40, bottom: hasZoom ? 66 : 42, containLabel: true },
    xAxis: { type: 'category', data: months, axisLabel: { color: '#b8d9ef', formatter: monthLabel }, axisLine: { lineStyle: { color: 'rgba(91,180,232,.6)' } } },
    yAxis: { type: 'value', name: 'mm', axisLabel: { color: '#b8d9ef' }, nameTextStyle: { color: '#8cb9d5' } },
    dataZoom: hasZoom ? [{ type: 'inside' }, { type: 'slider', height: 12, bottom: 8, borderColor: 'rgba(57,205,251,.55)', textStyle: { color: '#a9d7ee' } }] : [],
    series: cities.value.map((city, index) => ({
      name: cityLabel(city),
      type: 'line',
      connectNulls: false,
      showSymbol: months.length <= 12,
      data: months.map((month) => {
        const item = city.monthlyPrecip?.find((entry) => entry.month === month)
        return item ? finiteNumber(item.precip) : null
      }),
      lineStyle: { color: color(index), width: 2 },
      itemStyle: { color: color(index) },
    })),
  }
}

useEChart(radarElement, radarOption, [cities, radarDimensions, radarValues], {})
useEChart(barElement, barOption, [cities], {})
useEChart(monthElement, monthOption, [cities], {})

function bestCity(field, direction = 'max') {
  const valid = cities.value.filter((city) => metricNumber(city, field) !== null)
  if (!valid.length) return null
  return [...valid].sort((left, right) => {
    const difference = metricNumber(right, field) - metricNumber(left, field)
    return direction === 'max' ? difference : -difference
  })[0]
}

const conclusion = computed(() => {
  if (!cities.value.length) return []
  const temp = bestCity('avgTempEstimate')
  const rain = bestCity('totalPrecip')
  const wind = bestCity('avgWind')
  const validAqi = cities.value.filter((city) => metricNumber(city, 'aqiSnapshot') !== null)
  const aqi = validAqi.length >= 2 ? bestCity('aqiSnapshot', 'min') : null
  return [
    { icon: '℃', label: '温度最高', city: temp, text: temp ? `估算平均温度 ${formatValue(metricNumber(temp, 'avgTempEstimate'), ' ℃')}` : '暂无可比数据' },
    { icon: '雨', label: '降水量最多', city: rain, text: rain ? `区域日均降水累计 ${formatValue(metricNumber(rain, 'totalPrecip'), ' mm')}` : '暂无可比数据' },
    { icon: '风', label: '平均风速最大', city: wind, text: wind ? `平均风速 ${formatValue(metricNumber(wind, 'avgWind'), ' m/s')}` : '暂无可比数据' },
    { icon: 'AQI', label: 'AQI最低', city: aqi, text: aqi ? `固定快照 AQI ${formatAqi(metricNumber(aqi, 'aqiSnapshot'))}` : validAqi.length === 1 ? '仅一个城市有有效快照，无法进行城市间排名' : '暂无足够有效AQI快照进行比较' },
  ]
})

onMounted(async () => {
  try {
    const response = await getComparisonLocations()
    locations.value = Array.isArray(response.data) ? response.data : []
    // 默认值来自真实天气地点接口，不硬编码业务城市。
    selectedKeys.value = locations.value.slice(0, 2).map((item) => item.key)
    await query()
  } catch (reason) {
    error.value = reason?.message || '区域选项读取失败'
  }
})
</script>

<template>
  <BigScreenLayout page-number="6" title="区域对比分析" description="基于真实天气历史数据与独立 AQI 快照进行区域对比。">
    <template #filters>
      <div class="compare-filter">
        <strong>对比区域</strong>
        <label v-for="(key, index) in selectedKeys" :key="index">
          <span>城市{{ String.fromCharCode(65 + index) }}</span>
          <select v-model="selectedKeys[index]">
            <option v-for="item in locations" :key="item.key" :value="item.key" :disabled="selectedKeys.includes(item.key) && selectedKeys[index] !== item.key">
              {{ item.province }} · {{ item.city }}
            </option>
          </select>
          <button v-if="selectedKeys.length > 2" type="button" @click="removeCity(index)">移除</button>
        </label>
        <button v-if="selectedKeys.length < 4" type="button" @click="addCity">+ 添加城市</button>
        <label><span>起始日期</span><input v-model="startDate" type="date"></label>
        <label><span>结束日期</span><input v-model="endDate" type="date"></label>
        <button class="query-button" type="button" :disabled="loading" @click="query">查询</button>
      </div>
    </template>

    <p v-if="error" class="compare-alert">{{ error }}</p>

    <div class="comparison-page">
      <div v-if="loading || !result" class="comparison-state">
        <ChartState :loading="loading" :error="error" :empty="!loading && !error" empty-message="暂无对比数据" />
      </div>

      <template v-else>
        <div class="metric-groups">
          <DashboardPanel v-for="group in metricGroups" :key="group.key" :title="group.title" :subtitle="group.subtitle">
            <div class="metric-group-list">
              <div v-for="(city, index) in cities" :key="city.key" class="metric-row" :style="{ '--city-color': color(index) }">
                <span class="city-dot" aria-hidden="true" />
                <span class="metric-city" :title="cityLabel(city)">{{ cityLabel(city) }}</span>
                <strong>{{ groupValue(city, group) }}</strong>
              </div>
            </div>
          </DashboardPanel>
        </div>

        <div class="comparison-period">
          <span>天气日期：{{ result.weatherPeriod.startDate }} 至 {{ result.weatherPeriod.endDate }}</span>
          <span>共同可比观测日：{{ formatDays(result.dataCoverage.commonDays) }} 天</span>
          <span>AQI：数据库固定快照，入库时间按真实 created_at 展示（非观测时间）</span>
          <span>AQI快照入库：{{ aqiSnapshotTimeText }}</span>
        </div>
        <p v-if="!hasCommonDates" class="compare-alert comparison-no-common">当前城市没有共同有效天气观测日期，无法进行严格同期比较；请调整日期范围或更换城市。</p>

        <div class="compare-grid">
          <DashboardPanel title="多维指标对比" :subtitle="radarReady ? '基于共同日期真实城市样本的相对量级，越外不代表越好' : '有效指标不足，无法进行雷达比较'">
            <div v-if="hasCommonDates && radarReady" ref="radarElement" class="chart radar-chart" />
            <div v-else class="radar-empty">
              <div class="chart-empty">{{ hasCommonDates ? `至少需要三个对所有城市均有效的指标维度；缺失维度：${radarExcluded.join('、') || '暂无'}` : '没有共同有效天气观测日期，暂不绘制雷达图' }}</div>
              <table v-if="hasCommonDates" class="radar-fallback-table">
                <thead><tr><th>原始指标</th><th v-for="city in cities" :key="city.key">{{ cityLabel(city) }}</th></tr></thead>
                <tbody><tr v-for="field in radarFields" :key="field.key"><td>{{ field.name }}</td><td v-for="city in cities" :key="city.key">{{ rawMetricText(city, field) }}</td></tr></tbody>
              </table>
            </div>
          </DashboardPanel>
          <DashboardPanel title="城市温度与 AQI 对比" subtitle="温度来自历史天气日期范围，AQI来自独立固定快照">
            <div v-if="hasCommonDates" ref="barElement" class="chart" />
            <div v-else class="chart-empty">暂无共同可比天气数据</div>
          </DashboardPanel>
          <DashboardPanel title="月度降水量对比" subtitle="按共同可比日期统计，仅展示实际存在月份">
            <div v-if="hasCommonDates" ref="monthElement" class="chart" />
            <div v-else class="chart-empty">暂无共同可比降水数据</div>
          </DashboardPanel>
        </div>

        <div class="bottom-grid">
          <DashboardPanel title="城市指标对比" :subtitle="`有效天气观测日：${result.dataCoverage.cities.map((item) => formatDays(item.validDays)).join(' / ')} 天；共同可比：${formatDays(result.dataCoverage.commonDays)} 天`">
            <div class="compare-table-wrap">
              <table>
                <thead><tr><th>城市</th><th>平均温度</th><th>平均最高温</th><th>平均最低温</th><th>区域日均降水累计</th><th>平均风速</th><th>最大风速</th><th>AQI快照</th><th>有效天数</th></tr></thead>
                <tbody>
                  <tr v-for="(city, index) in cities" :key="city.key">
                    <td><span class="table-city-mark" :style="{ backgroundColor: color(index) }" />{{ cityLabel(city) }}</td>
                    <td>{{ formatValue(metricNumber(city, 'avgTempEstimate'), ' ℃') }}</td>
                    <td>{{ formatValue(metricNumber(city, 'avgMaxTemp'), ' ℃') }}</td>
                    <td>{{ formatValue(metricNumber(city, 'avgMinTemp'), ' ℃') }}</td>
                    <td>{{ formatValue(metricNumber(city, 'totalPrecip'), ' mm') }}</td>
                    <td>{{ formatValue(metricNumber(city, 'avgWind'), ' m/s') }}</td>
                    <td>{{ formatValue(metricNumber(city, 'maxWind'), ' m/s') }}</td>
                    <td>{{ formatAqi(metricNumber(city, 'aqiSnapshot')) }}</td>
                    <td>{{ formatDays(metrics(city).validDays) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="comparison-coverage" aria-label="数据覆盖说明">
              <div class="coverage-row">
                <strong>有效观测日</strong>
                <span v-for="city in cities" :key="city.key">{{ cityLabel(city) }}：{{ cityValidDays(city) }} 天</span>
              </div>
              <div class="coverage-row">
                <strong>可比范围</strong>
                <span>共同可比：{{ formatDays(result.dataCoverage.commonDays) }} 天</span>
                <span>天气日期：{{ result.weatherPeriod.startDate }} 至 {{ result.weatherPeriod.endDate }}</span>
              </div>
              <div class="coverage-row coverage-note">
                <strong>AQI来源</strong>
                <span>air_quality_data 固定快照；created_at 为入库时间，不代表天气观测时间。</span>
              </div>
            </div>
          </DashboardPanel>

          <DashboardPanel title="区域对比分析结论" subtitle="依据共同可比天气日期与独立 AQI 快照动态生成">
            <div class="conclusions">
              <div v-for="item in conclusion" :key="item.label" class="conclusion-item">
                <span class="conclusion-icon" :style="{ color: item.city ? color(cities.indexOf(item.city)) : '#8bb9d4' }">{{ item.icon }}</span>
                <div><strong>{{ item.label }}</strong><span v-if="item.city" class="conclusion-city">{{ cityLabel(item.city) }}</span><p>{{ item.text }}</p></div>
              </div>
            </div>
          </DashboardPanel>
        </div>
      </template>
    </div>
  </BigScreenLayout>
</template>

<style scoped>
.compare-filter { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px; padding: 7px 12px; color: var(--text-muted); font-size: 11px; background: linear-gradient(90deg, rgb(6 42 81 / 92%), rgb(4 28 61 / 84%)); border: 1px solid rgb(35 143 211 / 58%); border-radius: 6px; }
.compare-filter strong { color: var(--accent-cyan); font-size: 13px; }
.compare-filter label { display: inline-flex; align-items: center; gap: 5px; }
.compare-filter select, .compare-filter input { height: 31px; min-width: 118px; padding: 4px 7px; color: var(--text-primary); background: #0b315f; border: 1px solid rgb(45 151 216 / 68%); border-radius: 4px; }
.compare-filter button { height: 30px; padding: 0 8px; color: #cdeeff; background: #0b477a; border: 1px solid #287fb6; border-radius: 4px; cursor: pointer; }
.compare-filter .query-button { padding: 0 16px; color: #fff; background: #0877bd; border-color: #39cdfb; }
.compare-filter button:disabled { opacity: 0.55; cursor: wait; }
.compare-alert { margin: 0; padding: 8px 12px; color: #ff9fae; background: rgb(100 24 48 / 32%); border: 1px solid rgb(255 125 134 / 40%); border-radius: 6px; }
.comparison-page { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: 10px; }
.comparison-state { display: flex; min-height: 280px; align-items: center; justify-content: center; border: 1px solid rgb(43 157 216 / 34%); border-radius: var(--panel-radius); }
.metric-groups { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.metric-groups :deep(.dashboard-panel) { min-height: 148px; }
.metric-group-list { display: grid; gap: 7px; }
.metric-row { display: grid; min-width: 0; grid-template-columns: 8px minmax(0, 1fr) auto; align-items: center; gap: 7px; padding: 7px 8px; background: rgb(5 42 82 / 56%); border: 1px solid rgb(36 145 211 / 38%); border-radius: 5px; }
.city-dot { width: 7px; height: 7px; background: var(--city-color); border-radius: 50%; box-shadow: 0 0 7px var(--city-color); }
.metric-city { overflow: hidden; color: var(--text-secondary); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.metric-row strong { color: var(--text-primary); font-size: 16px; white-space: nowrap; }
.comparison-period { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px 18px; padding: 6px 10px; color: var(--text-muted); font-size: 10px; background: rgb(4 33 68 / 66%); border: 1px solid rgb(36 145 211 / 28%); border-radius: 5px; }
.compare-grid { display: grid; min-width: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.compare-grid :deep(.dashboard-panel) { min-height: 350px; }
.chart { width: 100%; height: 285px; min-height: 0; }
.radar-chart { height: 295px; }
.chart-empty { display: flex; height: 285px; align-items: center; justify-content: center; padding: 16px; color: var(--text-muted); font-size: 11px; line-height: 1.7; text-align: center; }
.radar-empty { display: grid; min-height: 285px; align-content: center; gap: 8px; }
.radar-empty .chart-empty { height: auto; min-height: 112px; }
.radar-fallback-table { width: 100%; border-collapse: collapse; color: var(--text-secondary); font-size: 10px; }
.radar-fallback-table th, .radar-fallback-table td { padding: 5px 6px; text-align: center; border: 1px solid rgb(45 126 177 / 34%); }
.radar-fallback-table th { color: #cdeeff; background: rgb(8 58 106 / 70%); }
.bottom-grid { display: grid; min-width: 0; align-items: stretch; grid-template-columns: minmax(0, 1.45fr) minmax(330px, 0.9fr); gap: 10px; }
.bottom-grid :deep(.dashboard-panel) { min-height: 0; }
.compare-table-wrap { overflow-x: auto; }
.compare-table-wrap table { width: 100%; min-width: 720px; border-collapse: collapse; color: var(--text-secondary); font-size: 10px; }
.compare-table-wrap th, .compare-table-wrap td { padding: 6px 6px; text-align: center; border: 1px solid rgb(45 126 177 / 40%); white-space: nowrap; }
.compare-table-wrap th { color: #cdeeff; background: rgb(8 58 106 / 80%); }
.compare-table-wrap td:first-child { color: var(--text-primary); text-align: left; }
.table-city-mark { display: inline-block; width: 7px; height: 7px; margin-right: 6px; border-radius: 50%; }
.comparison-coverage { display: grid; gap: 5px; margin-top: 8px; padding: 7px 8px; color: var(--text-muted); font-size: 10px; line-height: 1.45; background: rgb(4 36 73 / 52%); border: 1px solid rgb(36 145 211 / 30%); border-radius: 5px; }
.coverage-row { display: flex; flex-wrap: wrap; align-items: baseline; gap: 3px 12px; }
.coverage-row strong { color: var(--accent-cyan); font-weight: 600; }
.coverage-note { color: var(--text-muted); }
.conclusions { display: grid; gap: 6px; }
.conclusion-item { display: grid; grid-template-columns: 34px minmax(0, 1fr); gap: 9px; align-items: start; padding: 7px 8px; color: var(--text-secondary); background: rgb(7 49 94 / 55%); border: 1px solid rgb(36 145 211 / 42%); border-radius: 6px; }
.conclusion-icon { display: grid; min-height: 28px; place-items: center; font-size: 15px; font-weight: 700; background: rgb(12 94 157 / 35%); border-radius: 50%; }
.conclusion-item strong { display: inline-block; margin-right: 8px; color: var(--accent-cyan); font-size: 12px; }
.conclusion-city { color: var(--text-primary); font-size: 12px; }
.conclusion-item p { margin: 3px 0 0; color: var(--text-secondary); font-size: 11px; line-height: 1.5; }
@media (max-width: 1250px) { .metric-groups { grid-template-columns: repeat(2, minmax(0, 1fr)); } .compare-grid { grid-template-columns: 1fr 1fr; } .compare-grid :deep(.dashboard-panel:last-child) { grid-column: 1 / -1; } }
@media (max-width: 900px) { .compare-grid, .bottom-grid { grid-template-columns: 1fr; } .compare-grid :deep(.dashboard-panel:last-child) { grid-column: auto; } }
@media (max-width: 680px) { .metric-groups { grid-template-columns: 1fr; } .compare-filter { align-items: flex-start; flex-direction: column; } .compare-filter label { justify-content: space-between; width: 100%; } .compare-filter select, .compare-filter input { flex: 1; max-width: none; } .comparison-period { flex-direction: column; } }
</style>
