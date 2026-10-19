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
  ['database', '数据库管理'],
  ['monitor', '系统监控'],
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
  createdAt: '入库时间', table: '数据表', status: '状态', records: '记录/样本', coverage: '覆盖信息', metric: '监控指标', value: '当前值',
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
    api('/health'),
    api('/weather/national-dates'),
    api('/air-quality/overview'),
    api('/dashboard/national-overview'),
    api('/weather/national-trend', { days: 30 }),
  ])
  if (serial !== requestSerial) return
  const [health, dates, aqi, overview, trend] = results
  consoleData.value = {
    health: health.status === 'fulfilled' ? health.value.data : null,
    dates: dates.status === 'fulfilled' ? dates.value.data : [],
    aqi: aqi.status === 'fulfilled' ? aqi.value.data : null,
    overview: overview.status === 'fulfilled' ? overview.value.data : null,
    trend: trend.status === 'fulfilled' ? trend.value.data : [],
  }
  page.cards = [
    { label: '天气有效观测日', value: consoleData.value.dates.length, unit: '天' },
    { label: '天气记录数', value: consoleData.value.overview?.basicStatistics?.weatherRecordCount, unit: '条' },
    { label: 'AQI城市样本', value: consoleData.value.aqi?.cityCount, unit: '个' },
    { label: '数据库连接', value: consoleData.value.health?.database || '未连接', unit: '' },
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
      keyword: filters.keyword,
      page: pagination.page,
      pageSize: pagination.pageSize,
    })
    const result = response.data || {}
    rows = result.rows || []
    chartRows = rows.map((row) => ({ date: row.date, maxTemp: row.maxTemp, minTemp: row.minTemp }))
    pagination.total = result.total || 0
    pagination.pages = result.pages || 0
    note = '天气记录表使用后台受保护的服务端分页接口；筛选条件和日期均来自真实 weather_data。'
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
    note = '温度指标沿用温度分析服务的真实聚合口径。'
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
    note = '降水使用区域日均聚合结果，不把站点或区县降水量直接相加。'
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
    note = '风速来自现有 weather_data 风速字段；wind_data 不是当前正式数据源。'
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
    note = 'AQI 是固定城市快照，createdAt 表示入库时间，不代表天气历史观测日。'
  } else if (active.value === 'database') {
    const [health, dates, aqi, overview] = await Promise.all([
      api('/health'),
      api('/weather/national-dates'),
      api('/air-quality/overview'),
      api('/dashboard/national-overview'),
    ])
    rows = [
      { table: 'weather_data', status: health.data?.database === 'ok' ? '可查询' : '数据库异常', records: overview.data?.basicStatistics?.weatherRecordCount ?? '--', coverage: `${dates.data?.[dates.data.length - 1] || '--'}（最新可用日）` },
      { table: 'air_quality_data', status: aqi.data ? '可查询' : '暂无快照', records: aqi.data?.cityCount === undefined ? '--' : `${aqi.data.cityCount} 个有效城市快照`, coverage: aqi.data?.createdAt || '暂无入库时间' },
      { table: 'wind_data', status: '非正式数据源', records: '--', coverage: '仅使用 weather_data 风速字段' },
    ]
    note = '数据库管理仅展示受控只读统计，不开放任意 SQL；字段结构和原始表仍以项目数据字典为准。'
  } else if (active.value === 'monitor') {
    const health = await api('/health')
    rows = [
      { metric: 'Flask服务', value: '运行中' },
      { metric: 'MySQL连接', value: health.data?.database || '异常' },
      { metric: '请求总量', value: '暂无监控数据' },
      { metric: '成功率', value: '暂无监控数据' },
      { metric: '平均响应时间', value: '暂无监控数据' },
    ]
    note = '当前项目未采集请求级监控指标，页面明确显示暂无监控数据。'
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
  chart.setOption({
    color: ['#52d8ff', '#ffc466', '#56e39f', '#f47d9b'],
    tooltip: { trigger: 'axis' },
    legend: { data: keys, textStyle: { color: '#a7c3d9' } },
    grid: { left: 42, right: 24, top: 38, bottom: 34 },
    xAxis: { type: 'category', data: category, axisLabel: { color: '#a7c3d9' } },
    yAxis: { type: 'value', axisLabel: { color: '#a7c3d9' }, splitLine: { lineStyle: { color: '#193b5c' } } },
    series: keys.map((key) => ({ name: key, type: 'line', smooth: true, connectNulls: false, data: data.map((row) => row[key]) })),
  })
}

function resizeChart() { chart?.resize() }

onMounted(async () => {
  try {
    await loadLocations()
    await refresh()
  } catch (reason) {
    error.value = reason?.message || '后台数据读取失败，请检查 Flask 与数据库连接'
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
          <section class="admin-panel"><h2>{{ title }} <small v-if="loading">加载中…</small></h2><el-table class="admin-el-table" :data="page.rows" border stripe height="540" empty-text="暂无真实数据"><el-table-column v-for="key in Object.keys(page.rows[0] || {})" :key="key" :prop="key" :label="columnLabel(key)" min-width="120"><template #default="scope">{{ displayValue(scope.row[key]) }}</template></el-table-column><el-table-column v-if="active === 'weather'" label="操作" width="100" fixed="right"><template #default="scope"><el-button link type="primary" @click="openDetail(scope.row)">查看详情</el-button></template></el-table-column></el-table></section>
          <div v-if="active === 'weather' && pagination.total" class="admin-pagination"><span>共 {{ pagination.total }} 条</span><el-pagination background layout="prev, pager, next" :current-page="pagination.page" :page-size="pagination.pageSize" :total="pagination.total" @current-change="changeWeatherPage" /></div>
          <section v-if="page.chart.length" class="admin-panel"><h2>真实数据趋势或分布</h2><div ref="chartElement" class="admin-chart"></div></section>
        </template>
        <el-drawer v-model="detailOpen" title="天气记录详情" size="360px"><dl class="detail-list"><template v-for="(value, key) in selectedRow || {}" :key="key"><dt>{{ columnLabel(key) }}</dt><dd>{{ displayValue(value) }}</dd></template></dl></el-drawer>
      </section>
    </main>
  </div>
</template>

<style scoped>
.admin-app :deep(.el-select),.admin-app :deep(.el-date-editor),.admin-app :deep(.el-input){width:100%;min-width:150px}.admin-app :deep(.el-select__wrapper),.admin-app :deep(.el-input__wrapper){min-height:36px;background:#071a34;box-shadow:0 0 0 1px #285679 inset}.admin-app :deep(.el-select__selected-item),.admin-app :deep(.el-input__inner){color:#eaf6ff}.admin-app :deep(.el-date-editor .el-input__inner){color:#eaf6ff}.admin-app :deep(.el-button){border-radius:4px}.admin-app :deep(.el-button--primary){--el-button-bg-color:#178bc2;--el-button-border-color:#45c9f2;--el-button-hover-bg-color:#2aa4dc}.admin-app :deep(.el-table){--el-table-bg-color:transparent;--el-table-tr-bg-color:transparent;--el-table-header-bg-color:#12375d;--el-table-row-hover-bg-color:#12365f;--el-table-border-color:#1a4166;--el-table-text-color:#b7d4e7;--el-table-header-text-color:#c5e8f7}.admin-app :deep(.el-table th.el-table__cell){background:#12375d}.admin-app :deep(.el-table__inner-wrapper::before){background:#1a4166}.admin-app :deep(.el-drawer){background:#0a1f3c;color:#eaf6ff}.admin-app :deep(.el-drawer__header){margin-bottom:10px;color:#eaf6ff}.admin-app :deep(.el-pagination){--el-pagination-bg-color:#123c67;--el-pagination-button-bg-color:#123c67;--el-pagination-text-color:#b7d4e9;--el-pagination-button-color:#b7d4e9;--el-pagination-hover-color:#65ddff}.admin-app :deep(.el-pagination button:disabled){background:#0d2745}.admin-app :deep(.el-alert){margin-bottom:15px}\n.admin-app{display:flex;min-height:100vh;color:#eaf6ff;background:radial-gradient(circle at 75% -15%,#173c69 0,#071329 52%,#040b18 100%);font-family:system-ui,"Microsoft YaHei",sans-serif}.admin-sidebar{display:flex;width:236px;flex:none;flex-direction:column;padding:22px 14px;background:rgba(8,29,58,.95);border-right:1px solid #245681}.admin-brand{padding:0 12px 22px;color:#65ddff;font-size:21px;font-weight:700;letter-spacing:.03em}.admin-brand small{display:block;margin-top:4px;color:#91abc5;font-size:11px;font-weight:400}.admin-menu,.admin-swagger{padding:11px 12px;color:#b7d4e9;text-align:left;text-decoration:none;background:transparent;border:1px solid transparent;border-radius:6px;cursor:pointer}.admin-menu:hover,.admin-menu.active{color:#fff;background:linear-gradient(90deg,#123b69,#10305a);border-color:#2c83b5;box-shadow:0 0 18px #1daee833}.admin-swagger{margin-top:auto;color:#65ddff}.admin-main{min-width:0;flex:1}.admin-top{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:18px 28px;background:#081a35cc;border-bottom:1px solid #245681}.admin-top h1{margin:4px 0 0;font-size:24px}.admin-top span{color:#91abc5;font-size:12px}.admin-top-actions{display:flex;align-items:center;gap:20px}.admin-top-actions a{color:#65ddff}.admin-status{color:#42d99b!important}.admin-content{max-width:1600px;margin:0 auto;padding:22px;overflow:auto}.admin-toolbar{display:flex;align-items:end;flex-wrap:wrap;gap:12px;margin-bottom:16px;padding:14px;background:#0d2242cc;border:1px solid #245681;border-radius:8px}.admin-toolbar label{display:flex;min-width:150px;flex-direction:column;gap:5px;color:#b7d4e9;font-size:12px}.admin-toolbar select,.admin-toolbar input{min-width:150px;padding:8px;color:#eaf6ff;background:#071a34;border:1px solid #285679;border-radius:4px}.admin-toolbar button{padding:9px 16px;color:#03182b;font-weight:700;background:#65ddff;border:0;border-radius:4px;cursor:pointer}.admin-toolbar button:disabled{cursor:wait;opacity:.6}.admin-toolbar .reset{color:#dff8ff;background:#123c67}.admin-error{margin-bottom:15px;padding:11px 14px;color:#ffd1d5;background:#572b3b;border:1px solid #b64e62;border-radius:6px}.admin-error button{margin-left:12px;padding:5px 11px;color:#fff;background:#8c354c;border:0;border-radius:3px}.admin-note{margin:0 0 16px;padding:10px 13px;color:#a7c4d8;background:#0b203b;border-left:3px solid #52d8ff;border-radius:4px}.admin-cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:18px}.admin-cards article,.admin-panel{padding:16px;background:linear-gradient(145deg,#102c50e8,#0a1d38e8);border:1px solid #245681;border-radius:8px;box-shadow:0 10px 28px #0003}.admin-cards span{color:#91abc5;font-size:13px}.admin-cards strong{display:block;margin-top:8px;color:#65ddff;font-size:25px;line-height:1.25;word-break:break-word}.admin-cards small{margin-left:4px;color:#a7c4d8;font-size:12px;font-weight:400}.admin-panel{margin-bottom:18px;min-width:0}.admin-panel h2{margin:0 0 14px;font-size:17px}.admin-panel h2 small{margin-left:8px;color:#ffbc6b;font-size:11px}.admin-chart{width:100%;height:360px;min-height:220px}.admin-table-wrap{max-height:540px;overflow:auto}table{width:100%;border-collapse:collapse;font-size:12px;white-space:nowrap}th,td{padding:10px;text-align:left;border-bottom:1px solid #1a4166}th{position:sticky;top:0;color:#c5e8f7;background:#12375d}td{color:#b7d4e7}.admin-pagination{display:flex;align-items:center;justify-content:flex-end;gap:10px;margin:-8px 0 18px;color:#91abc5;font-size:12px}.admin-pagination button{padding:6px 12px;color:#dff8ff;background:#123c67;border:1px solid #2c83b5;border-radius:4px;cursor:pointer}.admin-pagination button:disabled{cursor:not-allowed;opacity:.45}.detail-button{padding:4px 8px;color:#bfefff;background:#123c67;border:1px solid #2c83b5;border-radius:3px;cursor:pointer}.detail-drawer{position:fixed;top:0;right:0;z-index:5;width:min(360px,90vw);height:100vh;padding:22px;background:#0a1f3ceF;border-left:1px solid #3a91bd;box-shadow:-12px 0 32px #0008}.detail-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:18px;font-size:17px}.detail-head button{padding:5px 10px;color:#dff8ff;background:#123c67;border:1px solid #2c83b5;border-radius:3px;cursor:pointer}.detail-list{display:grid;grid-template-columns:100px 1fr;gap:0;margin:0}.detail-list dt,.detail-list dd{margin:0;padding:9px 0;border-bottom:1px solid #1a4166}.detail-list dt{color:#91abc5}.detail-list dd{color:#eaf6ff;word-break:break-word}.admin-empty{padding:70px;text-align:center;color:#91abc5}@media(max-width:900px){.admin-sidebar{width:190px}.admin-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.admin-top{align-items:flex-start;flex-direction:column}}@media(max-width:620px){.admin-app{display:block}.admin-sidebar{width:auto}.admin-menu{display:inline-block;margin:2px}.admin-swagger{display:inline-block;margin-top:10px}.admin-cards{grid-template-columns:1fr}.admin-content{padding:12px}.admin-top{padding:15px}.admin-toolbar label{min-width:calc(50% - 8px)}.admin-chart{height:280px}}
</style>



