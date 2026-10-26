<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import {
  ElButton,
  ElDatePicker,
  ElDrawer,
  ElInput,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
} from 'element-plus'
import 'element-plus/dist/index.css'
import request from '../api/request'

const menu = [
  ['console', '控制台'],
  ['weather', '天气数据管理'],
  ['temperature', '温度管理'],
  ['rainfall', '降水管理'],
  ['wind', '风力管理'],
  ['air', '空气质量管理'],
]

const active = ref('console')
const loading = ref(false)
const error = ref('')
const provinces = ref([])
const cities = ref([])
const districts = ref([])
const filters = reactive({ province: '', city: '', district: '', date: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 50, total: 0, pages: 0 })
const page = reactive({ cards: [], rows: [], chart: [], note: '' })
const consoleData = ref(null)
const selectedRow = ref(null)
const detailOpen = ref(false)
const chartElement = ref(null)
let chart
let requestSerial = 0

const title = computed(() => menu.find(([key]) => key === active.value)?.[1] || '控制台')
const columnLabels = {
  id: '记录ID', province: '省份', city: '城市', district: '区县', date: '观测日期', weather: '天气',
  maxTemp: '最高温度', minTemp: '最低温度', avgWind: '平均风速', maxWind: '最大风速', precipitation: '降水量',
  createdAt: '入库时间', aqi: 'AQI', rank: '排名', status: '状态',
}
const api = (path, params = {}) => request.get(path, { params })
const cleanParams = (params) => Object.fromEntries(
  Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ''),
)
const locationParams = () => cleanParams({
  province: filters.province,
  city: filters.city,
  district: filters.district,
})
const analysisParams = () => cleanParams({
  ...locationParams(),
  startDate: filters.date,
  endDate: filters.date,
})

function clearPage() {
  page.cards = []
  page.rows = []
  page.chart = []
  page.note = ''
  selectedRow.value = null
  detailOpen.value = false
  pagination.total = 0
  pagination.pages = 0
  chart?.dispose()
  chart = null
}

async function loadLocations() {
  const response = await api('/locations/provinces')
  provinces.value = Array.isArray(response.data) ? response.data : []
  if (!filters.province && provinces.value.length) filters.province = provinces.value[0]
  await loadCities(false)
  if (!filters.city && cities.value.length) filters.city = cities.value[0]
  await loadDistricts(false)
  if (!filters.date && filters.province && filters.city) {
    const dates = (await api('/weather/dates', locationParams())).data || []
    filters.date = dates[0] || ''
  }
}

async function loadCities(reset = true) {
  if (!filters.province) {
    cities.value = []
    districts.value = []
    if (reset) {
      filters.city = ''
      filters.district = ''
    }
    return
  }
  const response = await api('/locations/cities', { province: filters.province })
  cities.value = Array.isArray(response.data) ? response.data : []
  if (reset) {
    filters.city = ''
    filters.district = ''
  }
}

async function loadDistricts(reset = true) {
  if (!filters.province || !filters.city) {
    districts.value = []
    if (reset) filters.district = ''
    return
  }
  const response = await api('/locations/districts', {
    province: filters.province,
    city: filters.city,
  })
  districts.value = Array.isArray(response.data) ? response.data : []
  if (reset) filters.district = ''
}

async function chooseProvince() {
  filters.city = ''
  filters.district = ''
  filters.date = ''
  filters.keyword = ''
  await loadCities()
  if (cities.value.length) filters.city = cities.value[0]
  await loadDistricts(false)
  await refresh()
}

async function chooseCity() {
  filters.district = ''
  filters.date = ''
  filters.keyword = ''
  await loadDistricts()
  await refresh()
}

function dateParams() {
  return filters.date ? { date: filters.date } : {}
}

async function loadConsole(serial) {
  const results = await Promise.allSettled([
    api('/weather/national-dates'),
    api('/air-quality/overview'),
    api('/dashboard/national-overview'),
    api('/weather/national-trend', { days: 30 }),
  ])
  if (serial !== requestSerial) return
  const [dates, aqi, overview, trend] = results
  consoleData.value = {
    dates: dates.status === 'fulfilled' ? dates.value.data : [],
    aqi: aqi.status === 'fulfilled' ? aqi.value.data : null,
    overview: overview.status === 'fulfilled' ? overview.value.data : null,
    trend: trend.status === 'fulfilled' ? trend.value.data : [],
  }
  page.cards = [
    { label: '天气有效观测日', value: consoleData.value.dates.length, unit: '天' },
    { label: '天气记录数', value: consoleData.value.overview?.basicStatistics?.weatherRecordCount, unit: '条' },
    { label: 'AQI城市样本', value: consoleData.value.aqi?.cityCount, unit: '个' },
    { label: '最新观测日', value: consoleData.value.dates[0] || '--', unit: '' },
  ]
  page.chart = Array.isArray(consoleData.value.trend) ? consoleData.value.trend : []
  page.note = '控制台只展示数据库真实统计；未采集的运行指标不会被补造。'
  await renderChart()
}

async function loadBusiness(serial) {
  if (active.value === 'console') return loadConsole(serial)
  const params = active.value === 'weather' ? { ...locationParams(), ...dateParams() } : analysisParams()
  let cards = []
  let rows = []
  let chartRows = []
  let note = ''

  if (active.value === 'weather') {
    const response = await api('/admin/weather-records', {
      ...params,
      ...cleanParams({ keyword: filters.keyword }),
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    const result = response.data || {}
    rows = result.rows || []
    chartRows = rows.map((row) => ({ date: row.date, maxTemp: row.maxTemp, minTemp: row.minTemp }))
    pagination.total = result.total || 0
    pagination.pages = result.pages || 0
    note = '天气记录来自真实 weather_data，可按地区、观测日期和关键词筛选。'
  } else if (active.value === 'temperature') {
    const [average, extremes, trend] = await Promise.all([
      api('/temperature/average', params),
      api('/temperature/extremes', params),
      api('/temperature/trend', params),
    ])
    cards = [
      { label: '平均最高温', value: average.data?.avgMaxTemp, unit: '°C' },
      { label: '平均最低温', value: average.data?.avgMinTemp, unit: '°C' },
      { label: '估算平均温度', value: average.data?.avgTemp, unit: '°C' },
      { label: '最高温记录', value: extremes.data?.maxTemperature, unit: '°C' },
    ]
    rows = trend.data || []
    chartRows = rows
    note = '温度指标来自真实天气记录的聚合结果。'
  } else if (active.value === 'rainfall') {
    const [core, trend] = await Promise.all([
      api('/rainfall/core', params),
      api('/rainfall/trend', params),
    ])
    cards = [
      { label: '累计降水', value: core.data?.totalPrecip, unit: 'mm' },
      { label: '平均日降水', value: core.data?.avgPrecip, unit: 'mm' },
      { label: '最大日降水', value: core.data?.maxPrecip, unit: 'mm' },
      { label: '有效观测日', value: core.data?.observationDays, unit: '天' },
    ]
    rows = trend.data || []
    chartRows = rows
    note = '降水量按区域观测记录计算，展示累计、日均和最大值。'
  } else if (active.value === 'wind') {
    const [core, trend] = await Promise.all([
      api('/wind/core', params),
      api('/wind/trend', params),
    ])
    cards = [
      { label: '平均风速', value: core.data?.avgWind, unit: 'm/s' },
      { label: '最大风速', value: core.data?.maxWind, unit: 'm/s' },
      { label: '有效观测日', value: core.data?.observationDays, unit: '天' },
    ]
    rows = trend.data || []
    chartRows = rows
    note = '风速来自真实 weather_data 风速字段。'
  } else if (active.value === 'air') {
    const [overview, ranking, levels] = await Promise.all([
      api('/air-quality/overview', { province: filters.province || undefined }),
      api('/air-quality/ranking', { ...locationParams(), limit: 100, order: 'asc' }),
      api('/air-quality/levels', { province: filters.province || undefined }),
    ])
    cards = [
      { label: '城市样本数', value: overview.data?.cityCount, unit: '个' },
      { label: '样本平均AQI', value: overview.data?.averageAqi, unit: '' },
      { label: '优良城市数', value: overview.data?.goodCityCount, unit: '个' },
      { label: '快照入库时间', value: overview.data?.createdAt || '暂无快照', unit: '' },
    ]
    rows = ranking.data || []
    chartRows = levels.data || []
    note = 'AQI 来自城市空气质量快照，入库时间不代表天气历史观测日。'
  }

  if (serial !== requestSerial) return
  page.cards = cards
  page.rows = Array.isArray(rows) ? rows : []
  page.chart = Array.isArray(chartRows) ? chartRows : []
  page.note = note
  await renderChart()
}

async function refresh(targetPage = null) {
  if (active.value === 'weather') pagination.page = targetPage || 1
  const serial = ++requestSerial
  loading.value = true
  error.value = ''
  clearPage()
  try {
    await loadBusiness(serial)
    if (serial === requestSerial && !page.rows.length && !page.chart.length && active.value !== 'console') {
      page.note = page.note || '当前筛选条件没有真实数据。'
    }
  } catch (reason) {
    if (serial === requestSerial) error.value = reason?.message || '数据读取失败，请重试'
  } finally {
    if (serial === requestSerial) loading.value = false
  }
}

async function retry() {
  try {
    if (!provinces.value.length) await loadLocations()
    await refresh()
  } catch (reason) {
    error.value = reason?.message || '数据读取失败，请重试'
  }
}

async function selectMenu(key) {
  active.value = key
  await refresh()
}

async function resetFilters() {
  filters.province = provinces.value[0] || ''
  filters.city = ''
  filters.district = ''
  filters.date = ''
  filters.keyword = ''
  await loadCities(false)
  filters.city = cities.value[0] || ''
  await loadDistricts(false)
  await refresh()
}

async function changeWeatherPage(targetPage) {
  if (targetPage < 1 || (pagination.pages && targetPage > pagination.pages)) return
  await refresh(targetPage)
}

function displayValue(value) {
  if (value === null || value === undefined || value === '') return '--'
  if (typeof value === 'number' && !Number.isFinite(value)) return '--'
  if (typeof value === 'number') return Number(value.toFixed(2))
  return typeof value === 'object' ? JSON.stringify(value) : value
}

function columnLabel(key) { return columnLabels[key] || key }
function openDetail(row) { selectedRow.value = row; detailOpen.value = true }

async function renderChart() {
  await nextTick()
  if (!chartElement.value || !page.chart.length) return
  chart?.dispose()
  chart = echarts.init(chartElement.value)
  const data = page.chart
  const keys = Object.keys(data[0] || {}).filter((key) => key !== 'date' && key !== 'month' && data.some((row) => Number.isFinite(Number(row[key]))))
  const category = data.map((row) => row.date || row.month || row.status || '')
  const labelInterval = category.length > 16 ? Math.ceil(category.length / 12) - 1 : 0
  chart.setOption({
    color: ['#52d8ff', '#ffc466', '#56e39f', '#f47d9b'],
    tooltip: {
      trigger: 'axis',
      confine: true,
      backgroundColor: 'rgba(7, 20, 40, 0.96)',
      borderColor: '#3d83ad',
      textStyle: { color: '#eaf6ff' },
      valueFormatter: (value) => {
        const number = Number(value)
        return Number.isFinite(number) ? number.toFixed(2) : value
      },
    },
    legend: {
      data: keys.map(columnLabel),
      top: 4,
      left: 16,
      right: 16,
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 16,
      textStyle: { color: '#a7c3d9' },
    },
    grid: { left: 48, right: 24, top: 42, bottom: category.length > 12 ? 84 : 42, containLabel: true },
    xAxis: {
      type: 'category',
      data: category,
      axisLabel: {
        color: '#a7c3d9',
        hideOverlap: true,
        interval: labelInterval,
        margin: 14,
        rotate: category.length > 12 ? 30 : 0,
      },
      axisLine: { lineStyle: { color: '#42627b' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#a7c3d9' },
      splitLine: { lineStyle: { color: '#193b5c' } },
    },
    series: keys.map((key) => ({ name: columnLabel(key), type: 'line', smooth: true, showSymbol: true, symbolSize: 7, lineStyle: { width: 2 }, connectNulls: false, data: data.map((row) => row[key]) })),
  })
}

function resizeChart() { chart?.resize() }

onMounted(async () => {
  try {
    await loadLocations()
    await refresh()
  } catch (reason) {
    error.value = reason?.message || '后台数据读取失败，请检查服务是否正常'
  }
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  chart?.dispose()
})
</script>

<template>
  <div class="admin-app">
    <aside class="admin-sidebar">
      <div class="admin-brand">WeatherDemo<small>可视化管理系统</small></div>
      <div class="admin-nav-label">数据分析</div>
      <button v-for="item in menu" :key="item[0]" :class="['admin-menu', { active: active === item[0] }]" @click="selectMenu(item[0])">{{ item[1] }}</button>
      <a class="admin-swagger" href="/api/docs" target="_blank" rel="noreferrer">Swagger 开发文档</a>
    </aside>

    <main class="admin-main">
      <header class="admin-top">
        <div><span>WeatherDemo / 后台管理</span><h1>{{ title }}</h1></div>
        <div class="admin-top-actions"><span class="admin-status">● 只读真实数据</span><a href="/" target="_blank" rel="noreferrer">返回天气大屏</a></div>
      </header>

      <section class="admin-content">
        <div v-if="error" class="admin-error">{{ error }}<el-button type="danger" plain size="small" @click="retry">重试</el-button></div>
        <div v-if="active !== 'console'" class="admin-toolbar">
          <label>省份<el-select v-model="filters.province" filterable clearable placeholder="全部省份" @change="chooseProvince"><el-option v-for="item in provinces" :key="item" :label="item" :value="item" /></el-select></label>
          <label>城市<el-select v-model="filters.city" filterable clearable :disabled="!filters.province" placeholder="全部城市" @change="chooseCity"><el-option v-for="item in cities" :key="item" :label="item" :value="item" /></el-select></label>
          <label>区县<el-select v-model="filters.district" filterable clearable :disabled="!filters.city" placeholder="全部区县" @change="refresh"><el-option v-for="item in districts" :key="item" :label="item" :value="item" /></el-select></label>
          <label>观测日<el-date-picker v-model="filters.date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期" @change="refresh" /></label>
          <label v-if="active === 'weather'">关键词<el-input v-model.trim="filters.keyword" placeholder="省市区县或天气" clearable @keyup.enter="refresh" /></label>
          <el-button class="query" type="primary" :loading="loading" @click="refresh">刷新数据</el-button>
          <el-button class="reset" @click="resetFilters">重置筛选</el-button>
        </div>
        <div v-if="active !== 'console' && page.note" class="admin-note">{{ page.note }}</div>

        <template v-if="active === 'console'">
          <div class="admin-cards"><article v-for="card in page.cards" :key="card.label"><span>{{ card.label }}</span><strong>{{ displayValue(card.value) }}<small>{{ card.unit }}</small></strong></article></div>
          <section class="admin-panel"><h2>全国历史天气趋势 <small v-if="loading">加载中…</small></h2><div ref="chartElement" class="admin-chart"></div><div v-if="!loading && !page.chart.length" class="admin-empty">暂无真实趋势数据</div></section>
          <div class="admin-note">{{ page.note }}</div>
        </template>

        <template v-else>
          <div v-if="page.cards.length" class="admin-cards"><article v-for="card in page.cards" :key="card.label"><span>{{ card.label }}</span><strong>{{ displayValue(card.value) }}<small>{{ card.unit }}</small></strong></article></div>
          <section class="admin-panel"><h2>{{ title }} <small v-if="loading">加载中…</small></h2><el-table class="admin-el-table" :data="page.rows" border stripe :max-height="active === 'weather' ? 540 : undefined" empty-text="暂无真实数据"><el-table-column v-for="key in Object.keys(page.rows[0] || {})" :key="key" :prop="key" :label="columnLabel(key)" min-width="120"><template #default="scope">{{ displayValue(scope.row[key]) }}</template></el-table-column><el-table-column v-if="active === 'weather'" label="操作" width="100" fixed="right"><template #default="scope"><el-button link type="primary" @click="openDetail(scope.row)">查看详情</el-button></template></el-table-column></el-table></section>
          <div v-if="active === 'weather' && pagination.total" class="admin-pagination"><span>共 {{ pagination.total }} 条</span><el-pagination background layout="prev, pager, next" :current-page="pagination.page" :page-size="pagination.pageSize" :total="pagination.total" @current-change="changeWeatherPage" /></div>
          <section v-if="page.chart.length" class="admin-panel"><h2>真实数据趋势或分布</h2><div ref="chartElement" class="admin-chart"></div></section>
        </template>
        <el-drawer v-model="detailOpen" title="天气记录详情" size="360px"><dl class="detail-list"><template v-for="(value, key) in selectedRow || {}" :key="key"><dt>{{ columnLabel(key) }}</dt><dd>{{ displayValue(value) }}</dd></template></dl></el-drawer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-app {
  --admin-bg: #071329;
  --admin-surface: rgba(14, 35, 67, 0.88);
  --admin-surface-strong: #102b50;
  --admin-line: rgba(83, 170, 224, 0.28);
  --admin-text: #eaf6ff;
  --admin-muted: #91abc5;
  --admin-cyan: #65ddff;
  --admin-sidebar-width: 248px;
  position: relative;
  display: grid;
  grid-template-columns: var(--admin-sidebar-width) minmax(0, 1fr);
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  color: var(--admin-text);
  background:
    radial-gradient(circle at 88% -18%, rgba(31, 104, 159, 0.42), transparent 36%),
    linear-gradient(135deg, #071329 0%, #061022 55%, #040b18 100%);
  font-family: system-ui, "Microsoft YaHei", sans-serif;
}

.admin-sidebar {
  display: flex;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  flex-direction: column;
  gap: 6px;
  padding: 24px 16px 18px;
  background: linear-gradient(180deg, rgba(10, 36, 70, 0.98), rgba(6, 22, 45, 0.98));
  border-right: 1px solid var(--admin-line);
}

.admin-brand {
  position: relative;
  padding: 2px 12px 24px 16px;
  margin-bottom: 8px;
  color: var(--admin-cyan);
  font-size: 22px;
  font-weight: 750;
  letter-spacing: 0.02em;
}

.admin-brand::after {
  position: absolute;
  right: 12px;
  bottom: 0;
  left: 12px;
  height: 1px;
  content: "";
  background: linear-gradient(90deg, var(--admin-cyan), transparent);
  opacity: 0.45;
}

.admin-brand small {
  display: block;
  margin-top: 6px;
  color: var(--admin-muted);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.08em;
}

.admin-nav-label {
  width: 100%;
  padding: 8px 14px 4px;
  color: #5f8caf;
  font-size: 11px;
  letter-spacing: 0.14em;
}

.admin-menu,
.admin-swagger {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  color: #b7d4e9;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: color 160ms ease, background 160ms ease, border-color 160ms ease, transform 160ms ease;
}

.admin-menu::before {
  width: 6px;
  height: 6px;
  flex: 0 0 6px;
  content: "";
  background: #4f7896;
  border-radius: 50%;
  transition: background 160ms ease, box-shadow 160ms ease;
}

.admin-menu:hover,
.admin-menu:focus-visible,
.admin-menu.active {
  color: #fff;
  background: linear-gradient(100deg, rgba(31, 112, 178, 0.5), rgba(17, 62, 111, 0.48));
  border-color: rgba(74, 182, 232, 0.52);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
  outline: none;
  transform: translateX(2px);
}

.admin-menu:hover::before,
.admin-menu:focus-visible::before,
.admin-menu.active::before {
  background: var(--admin-cyan);
  box-shadow: 0 0 10px rgba(101, 221, 255, 0.8);
}

.admin-swagger {
  margin-top: auto;
  color: var(--admin-cyan);
  text-decoration: none;
}

.admin-swagger:hover,
.admin-swagger:focus-visible {
  background: rgba(28, 124, 176, 0.2);
  outline: none;
}

.admin-main {
  display: flex;
  min-width: 0;
  min-height: 0;
  height: 100%;
  flex-direction: column;
  overflow: hidden;
}

.admin-top {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 88px;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 18px clamp(22px, 3vw, 42px);
  background: rgba(7, 24, 49, 0.84);
  border-bottom: 1px solid var(--admin-line);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
}

.admin-top > div:first-child > span {
  color: var(--admin-muted);
  font-size: 12px;
  letter-spacing: 0.04em;
}

.admin-top h1 {
  margin: 4px 0 0;
  color: #f5fbff;
  font-size: clamp(22px, 2vw, 28px);
  line-height: 1.2;
}

.admin-top-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  flex-wrap: wrap;
  font-size: 13px;
}

.admin-top-actions a {
  color: var(--admin-cyan);
  font-weight: 600;
}

.admin-status {
  color: #42d99b !important;
  white-space: nowrap;
}

.admin-content {
  display: block;
  width: 100%;
  max-width: none;
  min-width: 0;
  min-height: 0;
  flex: 1 1 auto;
  margin: 0;
  padding: 26px clamp(18px, 3vw, 42px) 38px;
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.admin-toolbar {
  display: flex;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
  padding: 16px;
  background: var(--admin-surface);
  border: 1px solid var(--admin-line);
  border-radius: 12px;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.12);
}

.admin-toolbar label {
  display: flex;
  min-width: 170px;
  flex: 1 1 170px;
  flex-direction: column;
  gap: 6px;
  color: #b7d4e9;
  font-size: 12px;
}

.admin-toolbar label:has(.el-date-editor) {
  flex-basis: 190px;
}

.admin-toolbar label:has(.el-input) {
  flex-basis: 210px;
}

.admin-toolbar button {
  min-height: 36px;
  padding: 0 16px;
  color: #03182b;
  font-weight: 700;
  background: var(--admin-cyan);
  border: 0;
  border-radius: 7px;
}

.admin-toolbar button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.admin-toolbar .reset {
  color: #dff8ff;
  background: #123c67;
}

.admin-error {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 14px;
  color: #ffd1d5;
  background: rgba(87, 43, 59, 0.82);
  border: 1px solid #b64e62;
  border-radius: 8px;
}

.admin-note {
  margin: 0 0 18px;
  padding: 11px 14px;
  color: #a7c4d8;
  background: rgba(11, 32, 59, 0.72);
  border: 1px solid rgba(82, 216, 255, 0.18);
  border-left: 3px solid #52d8ff;
  border-radius: 8px;
}

.admin-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.admin-cards article {
  position: relative;
  min-width: 0;
  min-height: 106px;
  padding: 18px;
  background: linear-gradient(145deg, rgba(20, 55, 95, 0.9), rgba(9, 28, 56, 0.92));
  border: 1px solid var(--admin-line);
  border-radius: 12px;
  box-shadow: 0 12px 26px rgba(0, 0, 0, 0.14);
}

.admin-cards article::before {
  position: absolute;
  top: 0;
  right: 18px;
  left: 18px;
  height: 2px;
  content: "";
  background: linear-gradient(90deg, var(--admin-cyan), transparent);
  opacity: 0.7;
}

.admin-cards span {
  color: var(--admin-muted);
  font-size: 13px;
}

.admin-cards strong {
  display: block;
  margin-top: 9px;
  overflow: hidden;
  color: var(--admin-cyan);
  font-size: clamp(24px, 2.2vw, 34px);
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-cards small {
  margin-left: 5px;
  color: #a7c4d8;
  font-size: 12px;
  font-weight: 400;
}

.admin-panel {
  min-width: 0;
  margin-bottom: 20px;
  padding: 20px;
  overflow: hidden;
  background: linear-gradient(145deg, rgba(18, 45, 81, 0.9), rgba(8, 25, 51, 0.9));
  border: 1px solid var(--admin-line);
  border-radius: 12px;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.14);
}

.admin-panel h2 {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0 0 16px;
  color: #f1f9ff;
  font-size: 18px;
}

.admin-panel h2 small {
  color: #ffbc6b;
  font-size: 11px;
  font-weight: 500;
}

.admin-chart {
  width: 100%;
  height: clamp(300px, 38vh, 430px);
  min-height: 260px;
}

.admin-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin: -4px 0 20px;
  color: var(--admin-muted);
  font-size: 12px;
}

.detail-list {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr);
  gap: 0;
  margin: 0;
}

.detail-list dt,
.detail-list dd {
  min-width: 0;
  margin: 0;
  padding: 9px 0;
  border-bottom: 1px solid #1a4166;
}

.detail-list dt {
  color: var(--admin-muted);
}

.detail-list dd {
  overflow-wrap: anywhere;
  color: var(--admin-text);
}

.admin-empty {
  padding: 70px;
  color: var(--admin-muted);
  text-align: center;
}

.admin-app :deep(.el-select),
.admin-app :deep(.el-date-editor),
.admin-app :deep(.el-input) {
  width: 100%;
  min-width: 0;
}

.admin-app :deep(.el-select__wrapper),
.admin-app :deep(.el-input__wrapper) {
  min-height: 36px;
  background: #071a34;
  box-shadow: 0 0 0 1px #285679 inset;
}

.admin-app :deep(.el-select__selected-item),
.admin-app :deep(.el-input__inner),
.admin-app :deep(.el-date-editor .el-input__inner) {
  color: var(--admin-text);
}

.admin-app :deep(.el-button) {
  border-radius: 7px;
}

.admin-app :deep(.el-button--primary) {
  --el-button-bg-color: #178bc2;
  --el-button-border-color: #45c9f2;
  --el-button-hover-bg-color: #2aa4dc;
}

.admin-app :deep(.el-table) {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: #12375d;
  --el-table-row-hover-bg-color: #12365f;
  --el-table-border-color: #1a4166;
  --el-table-text-color: #b7d4e7;
  --el-table-header-text-color: #c5e8f7;
  width: 100%;
}

.admin-app :deep(.el-table td.el-table__cell) {
  background: transparent;
  color: #c0d8e9;
}

.admin-app :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: rgba(39, 91, 139, 0.24);
}

.admin-app :deep(.el-table__body tr:hover > td.el-table__cell) {
  background: rgba(65, 145, 195, 0.22) !important;
}

.admin-app :deep(.el-table .cell) {
  line-height: 1.45;
}

.admin-app :deep(.el-table__fixed),
.admin-app :deep(.el-table__fixed-right) {
  background: #102b50;
}

.admin-app :deep(.el-table__fixed td.el-table__cell),
.admin-app :deep(.el-table__fixed-right td.el-table__cell) {
  background: #102b50;
}

.admin-app :deep(.el-table__fixed .el-table__row--striped td.el-table__cell),
.admin-app :deep(.el-table__fixed-right .el-table__row--striped td.el-table__cell) {
  background: #15385f;
}

.admin-app :deep(.el-table th.el-table__cell) {
  background: #12375d;
}

.admin-app :deep(.el-table__inner-wrapper::before) {
  background: #1a4166;
}

.admin-app :deep(.el-drawer) {
  background: #0a1f3c;
  color: var(--admin-text);
}

.admin-app :deep(.el-drawer__header) {
  margin-bottom: 10px;
  color: var(--admin-text);
}

.admin-app :deep(.el-pagination) {
  --el-pagination-bg-color: #123c67;
  --el-pagination-button-bg-color: #123c67;
  --el-pagination-text-color: #b7d4e9;
  --el-pagination-button-color: #b7d4e9;
  --el-pagination-hover-color: var(--admin-cyan);
}

.admin-app :deep(.el-pagination button:disabled) {
  background: #0d2745;
}

@media (max-width: 1180px) {
  .admin-app {
    --admin-sidebar-width: 220px;
  }

  .admin-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .admin-app {
    display: block;
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .admin-sidebar {
    height: auto;
    max-height: none;
    padding: 16px 12px 14px;
    border-right: 0;
    border-bottom: 1px solid var(--admin-line);
  }

  .admin-brand {
    padding-bottom: 16px;
  }

  .admin-menu {
    width: auto;
    flex: 1 1 150px;
  }

  .admin-sidebar {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .admin-brand {
    width: 100%;
  }

  .admin-swagger {
    width: auto;
    margin-top: 0;
  }

  .admin-main {
    height: auto;
    min-height: calc(100vh - 180px);
    overflow: visible;
  }

  .admin-top {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
    padding: 18px 16px;
  }

  .admin-top-actions {
    justify-content: flex-start;
  }

  .admin-content {
    padding: 18px 12px 28px;
    overflow: visible;
  }

  .admin-cards {
    grid-template-columns: 1fr;
  }

  .admin-chart {
    height: 300px;
  }
}

@media (max-width: 460px) {
  .admin-toolbar label {
    min-width: 100%;
    flex-basis: 100%;
  }

  .admin-toolbar button {
    flex: 1 1 calc(50% - 6px);
  }

  .admin-panel {
    padding: 14px;
  }

  .admin-chart {
    min-height: 220px;
    height: 270px;
  }
}
</style>

