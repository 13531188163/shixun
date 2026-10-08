<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { getHealth } from '../api/health'
import { getProvinces, getCities, getDistricts } from '../api/location'
import { getDashboardOverview, getProvinceDashboardOverview } from '../api/dashboard'
import {
  getWeatherDates,
  getProvinceWeatherDates,
  getWeatherTrend,
  getProvinceWeatherTrend,
  getCityWeatherComparison,
} from '../api/weather'
import { getAirQualityRanking, getAirQualityDistribution } from '../api/airQuality'
import DashboardHeader from '../components/dashboard/DashboardHeader.vue'
import DashboardPanel from '../components/dashboard/DashboardPanel.vue'
import WeatherOverview from '../components/dashboard/WeatherOverview.vue'
import WeatherMetrics from '../components/dashboard/WeatherMetrics.vue'
import WeatherTrendChart from '../components/dashboard/WeatherTrendChart.vue'
import CityComparisonChart from '../components/dashboard/CityComparisonChart.vue'
import CenterOverview from '../components/dashboard/CenterOverview.vue'
import AirQualityOverview from '../components/dashboard/AirQualityOverview.vue'
import AirQualityRankingChart from '../components/dashboard/AirQualityRankingChart.vue'
import AirQualityDistributionChart from '../components/dashboard/AirQualityDistributionChart.vue'

const provinces = ref([])
const cities = ref([])
const districts = ref([])
const availableDates = ref([])
const selection = reactive({ province: '', city: '', district: '', scope: 'province' })
const selectedDate = ref('')
const mapDetailProvince = ref('')
const health = ref(null)
const healthError = ref('')

const dashboard = ref(null)
const latestWeather = ref(null)
const latestAirQuality = ref(null)
const weatherTrend = ref([])
const cityComparison = ref([])
const airQualityRanking = ref([])
const airQualityDistribution = ref([])

const pageError = ref('')
const locationLoading = ref(false)
const payloadLoading = ref(true)
const errors = reactive({
  overview: '',
  weather: '',
  trend: '',
  comparison: '',
  airQuality: '',
  ranking: '',
  distribution: '',
})

let requestVersion = 0
let comparisonPoolPromise
let sharedAirQualityPromise

const loading = computed(() => locationLoading.value || payloadLoading.value)
const basicStatistics = computed(() => dashboard.value?.basicStatistics || null)
const cityComparisonDisplay = computed(() => cityComparison.value.slice(0, 6))
const locationReady = computed(() => Boolean(selection.province))
const isProvinceScope = computed(() => selection.scope === 'province' || !selection.city)
const dataDate = computed(() => selectedDate.value || latestWeather.value?.date || basicStatistics.value?.weatherLatestDate || '')
const apiStatus = computed(() => {
  if (pageError.value) return '需要检查 API'
  if (healthError.value) return '健康检查失败'
  if (health.value?.application === 'ok' && health.value?.database === 'ok') return 'API / DB 已连接'
  return '正在检查服务'
})

function statusOf(error) {
  return error?.response?.status || error?.apiResponse?.code || 0
}

function isNotFound(error) {
  return statusOf(error) === 404
}

function errorText(error, fallback) {
  if (isNotFound(error)) return ''
  return `${fallback}${error?.message ? `：${error.message}` : ''}`
}

function buildLocationParams() {
  const params = { province: selection.province, city: selection.city }
  if (!selection.city) return { province: selection.province }
  if (selection.district) params.district = selection.district
  return params
}

function clearData() {
  dashboard.value = null
  latestWeather.value = null
  latestAirQuality.value = null
  weatherTrend.value = []
  cityComparison.value = []
  errors.overview = ''
  errors.weather = ''
  errors.trend = ''
  errors.comparison = ''
  errors.airQuality = ''
}

async function comparisonCitiesFor(selectedCity) {
  if (!comparisonPoolPromise) {
    const sampleProvinces = provinces.value.slice(0, 8).filter((province) => province !== selection.province)
    comparisonPoolPromise = Promise.allSettled(
      sampleProvinces.map((province) => getCities({ province })),
    ).then((results) => results.flatMap((result) => (
      result.status === 'fulfilled' && Array.isArray(result.value.data) ? result.value.data : []
    )))
  }
  const pool = await comparisonPoolPromise
  return [...new Set([selectedCity, ...pool].filter(Boolean))].slice(0, 10)
}

async function ensureSharedAirQuality() {
  if (!sharedAirQualityPromise) {
    sharedAirQualityPromise = Promise.allSettled([
      getAirQualityRanking({ limit: 10, order: 'asc' }),
      getAirQualityDistribution(),
    ]).then(([rankingResult, distributionResult]) => {
      airQualityRanking.value = rankingResult.status === 'fulfilled' && Array.isArray(rankingResult.value.data)
        ? rankingResult.value.data
        : []
      airQualityDistribution.value = distributionResult.status === 'fulfilled' && Array.isArray(distributionResult.value.data)
        ? distributionResult.value.data
        : []
      errors.ranking = rankingResult.status === 'rejected'
        ? errorText(rankingResult.reason, '空气质量排名读取失败')
        : ''
      errors.distribution = distributionResult.status === 'rejected'
        ? errorText(distributionResult.reason, '空气质量分布读取失败')
        : ''
    })
  }
  await sharedAirQualityPromise
}

async function loadSelectedData(version) {
  if (!selection.province || version !== requestVersion) return

  payloadLoading.value = true
  const params = buildLocationParams()
  const overviewParams = selectedDate.value ? { ...params, date: selectedDate.value } : params
  const dateParams = selectedDate.value ? { date: selectedDate.value } : {}
  const provinceScope = isProvinceScope.value
  let comparisonCities = []
  if (provinceScope) {
    comparisonCities = cities.value.slice(0, 10)
  } else {
    try {
      comparisonCities = await comparisonCitiesFor(selection.city)
    } catch {
      comparisonCities = [selection.city]
    }
  }
  if (version !== requestVersion) return

  const requestsToMake = provinceScope
    ? [
        getProvinceDashboardOverview(overviewParams),
        getProvinceWeatherTrend({ province: selection.province, ...dateParams, days: 7 }),
        comparisonCities.length
          ? getCityWeatherComparison({ cities: comparisonCities.join(','), ...dateParams })
          : Promise.resolve({ data: [] }),
      ]
    : [
        getDashboardOverview(overviewParams),
        getWeatherTrend({ ...params, ...dateParams, days: 7 }),
        getCityWeatherComparison({ cities: comparisonCities.join(','), ...dateParams }),
      ]
  const [requests] = await Promise.all([
    Promise.allSettled([
      ...requestsToMake,
    ]),
    ensureSharedAirQuality(),
  ])
  if (version !== requestVersion) return

  const [overviewResult, trendResult, comparisonResult] = requests
  dashboard.value = overviewResult.status === 'fulfilled' ? (overviewResult.value.data || null) : null

  const overviewWeather = dashboard.value?.latestWeather || null
  const overviewAirQuality = dashboard.value?.latestAirQuality || null
  latestWeather.value = overviewWeather
  latestAirQuality.value = overviewAirQuality
  weatherTrend.value = trendResult.status === 'fulfilled' && Array.isArray(trendResult.value.data) ? trendResult.value.data : []
  cityComparison.value = comparisonResult.status === 'fulfilled' && Array.isArray(comparisonResult.value.data) ? comparisonResult.value.data : []

  errors.overview = overviewResult.status === 'rejected' && !dashboard.value ? errorText(overviewResult.reason, '概览接口暂时不可用') : ''
  errors.weather = !latestWeather.value && errors.overview ? '天气数据暂无' : ''
  errors.trend = trendResult.status === 'rejected' ? errorText(trendResult.reason, '天气历史趋势读取失败') : ''
  errors.comparison = comparisonResult.status === 'rejected' ? errorText(comparisonResult.reason, '城市比较读取失败') : ''
  errors.airQuality = !latestAirQuality.value && errors.overview ? '空气质量数据暂无' : ''
  payloadLoading.value = false
}

async function loadAvailableDates(version) {
  if (!selection.province || version !== requestVersion) return
  try {
    const response = isProvinceScope.value
      ? await getProvinceWeatherDates({ province: selection.province })
      : await getWeatherDates(buildLocationParams())
    if (version !== requestVersion) return
    availableDates.value = Array.isArray(response.data) ? response.data : []
    if (!availableDates.value.includes(selectedDate.value)) {
      selectedDate.value = availableDates.value[0] || ''
    }
  } catch (error) {
    if (version !== requestVersion) return
    availableDates.value = []
    selectedDate.value = ''
    if (!isNotFound(error)) pageError.value = errorText(error, '可用日期读取失败')
  }
}

async function loadDistrictsAndData(version) {
  if (!selection.province || !selection.city || version !== requestVersion) return
  try {
    const response = await getDistricts({ province: selection.province, city: selection.city })
    if (version !== requestVersion) return
    districts.value = Array.isArray(response.data) ? response.data : []
    if (!districts.value.includes(selection.district)) selection.district = ''
  } catch (error) {
    if (version !== requestVersion) return
    districts.value = []
    selection.district = ''
    // A missing district list is a valid empty state; a server error remains visible.
    if (!isNotFound(error)) pageError.value = errorText(error, '区县列表读取失败')
  }
  await loadAvailableDates(version)
  await loadSelectedData(version)
}

async function handleProvinceChange(province) {
  const version = ++requestVersion
  selection.province = province
  selection.city = ''
  selection.district = ''
  selection.scope = 'province'
  selectedDate.value = ''
  cities.value = []
  districts.value = []
  availableDates.value = []
  comparisonPoolPromise = undefined
  clearData()
  pageError.value = ''
  if (!province) {
    locationLoading.value = false
    payloadLoading.value = false
    return
  }

  locationLoading.value = true
  payloadLoading.value = true
  try {
    const response = await getCities({ province })
    if (version !== requestVersion) return
    cities.value = Array.isArray(response.data) ? response.data : []
    if (!cities.value.length) {
      pageError.value = '该省份暂无城市数据'
    }
    await loadAvailableDates(version)
    await loadSelectedData(version)
  } catch (error) {
    if (version === requestVersion) pageError.value = errorText(error, '城市列表读取失败')
  } finally {
    if (version === requestVersion) {
      locationLoading.value = false
      payloadLoading.value = false
    }
  }
}

function mapProvinceToApiName(mapProvince) {
  const value = String(mapProvince || '').trim()
  if (!value) return ''
  const direct = provinces.value.find((province) => province === value)
  if (direct) return direct
  const trimSuffix = (name) => String(name || '').replace(/省|市|自治区|特别行政区$/u, '')
  const normalized = trimSuffix(value)
  return provinces.value.find((province) => {
    const candidate = trimSuffix(province)
    return value.startsWith(province)
      || province.startsWith(value)
      || normalized === candidate
      || normalized.startsWith(candidate)
      || candidate.startsWith(normalized)
  }) || value
}

async function handleMapProvinceSelect(mapProvince) {
  const province = mapProvinceToApiName(mapProvince)
  if (!provinces.value.includes(province)) {
    pageError.value = `地图省份“${mapProvince}”暂无可查询记录`
    return
  }
  mapDetailProvince.value = province
  await handleProvinceChange(province)
}

function handleMapReset() {
  mapDetailProvince.value = ''
}

async function handleCityChange(city) {
  const version = ++requestVersion
  selection.city = city
  selection.district = ''
  selection.scope = city ? 'city' : 'province'
  selectedDate.value = ''
  districts.value = []
  availableDates.value = []
  clearData()
  pageError.value = ''
  if (!city) {
    locationLoading.value = true
    payloadLoading.value = true
    try {
      await loadAvailableDates(version)
      await loadSelectedData(version)
    } finally {
      if (version === requestVersion) {
        locationLoading.value = false
        payloadLoading.value = false
      }
    }
    return
  }
  locationLoading.value = true
  payloadLoading.value = true
  try {
    await loadDistrictsAndData(version)
  } catch (error) {
    if (version === requestVersion) pageError.value = errorText(error, '地区数据读取失败')
  } finally {
    if (version === requestVersion) {
      locationLoading.value = false
      payloadLoading.value = false
    }
  }
}

async function handleDistrictChange(district) {
  const version = ++requestVersion
  selection.district = district
  selectedDate.value = ''
  availableDates.value = []
  clearData()
  pageError.value = ''
  locationLoading.value = true
  try {
    await loadAvailableDates(version)
    await loadSelectedData(version)
  } finally {
    if (version === requestVersion) {
      locationLoading.value = false
      payloadLoading.value = false
    }
  }
}

async function handleDateChange(date) {
  const version = ++requestVersion
  selectedDate.value = date
  clearData()
  pageError.value = ''
  await loadSelectedData(version)
}

async function loadInitial() {
  pageError.value = ''
  const [healthResult, provincesResult] = await Promise.allSettled([getHealth(), getProvinces()])
  if (healthResult.status === 'fulfilled') health.value = healthResult.value.data || null
  else healthError.value = healthResult.reason?.message || '健康检查失败'
  if (provincesResult.status !== 'fulfilled') {
    pageError.value = errorText(provincesResult.reason, '省份列表读取失败') || '省份列表读取失败'
    payloadLoading.value = false
    return
  }
  provinces.value = Array.isArray(provincesResult.value.data) ? provincesResult.value.data : []
  if (!provinces.value.length) {
    pageError.value = '后端已连接，但暂无省份数据'
    payloadLoading.value = false
    return
  }
  await handleProvinceChange(provinces.value[0])
}

onMounted(loadInitial)
</script>

<template>
  <main class="dashboard-shell">
    <DashboardHeader :location="dashboard?.location || selection" :data-date="dataDate" :status="apiStatus" />

    <div class="dashboard-content">
      <div class="dashboard-toolbar">
        <div class="map-interaction-hint">
          <span class="selector-label">全国地图</span>
          <span>点击省份查看省级汇总，再按需选择城市、区县和固定日期</span>
          <span v-if="dataDate" class="fixed-date">固定数据日期：{{ dataDate }}</span>
        </div>
        <div class="toolbar-summary">
          <span :class="['api-status', { offline: pageError || healthError }]" aria-live="polite"><i />{{ apiStatus }}</span>
          <span v-if="locationReady">{{ selection.province }}<template v-if="selection.city"> / {{ selection.city }}</template><template v-else> / 省级汇总</template><template v-if="selection.district"> / {{ selection.district }}</template></span>
        </div>
      </div>

      <div v-if="locationReady" class="selection-controls" aria-label="地图选中地区的详细条件">
        <span class="selection-controls-title">地图选中后细化</span>
        <label>
          <span>城市</span>
          <select :value="selection.city" :disabled="loading" @change="handleCityChange($event.target.value)">
            <option value="">省级汇总（选择城市后下钻）</option>
            <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
          </select>
        </label>
        <label>
          <span>区县</span>
          <select :value="selection.district" :disabled="loading || !selection.city || !districts.length" @change="handleDistrictChange($event.target.value)">
            <option value="">全市代表记录</option>
            <option v-for="district in districts" :key="district" :value="district">{{ district }}</option>
          </select>
        </label>
        <label>
          <span>数据日期</span>
          <select :value="selectedDate" :disabled="loading || !availableDates.length" @change="handleDateChange($event.target.value)">
            <option v-for="date in availableDates" :key="date" :value="date">{{ date }}</option>
          </select>
        </label>
        <span class="selection-caption">共 {{ availableDates.length }} 个可用观测日期</span>
      </div>

      <p v-if="pageError" class="dashboard-alert" role="alert">{{ pageError }}</p>

      <div class="dashboard-grid">
        <section class="dashboard-column left-column" aria-label="天气数据">
          <DashboardPanel title="当前天气概况" subtitle="weather/latest · 所选固定日期记录">
            <WeatherOverview :weather="latestWeather" :loading="loading" :error="errors.weather" />
          </DashboardPanel>
          <DashboardPanel title="天气指标" subtitle="仅展示数据库支持的天气字段">
            <WeatherMetrics
              :weather="latestWeather"
              :air-quality="latestAirQuality"
              :air-quality-summary="dashboard?.airQualitySummary"
              :loading="loading"
              :error="errors.weather"
            />
          </DashboardPanel>
          <DashboardPanel title="主要城市温度比较" subtitle="city-comparison · 所选日期实际返回城市">
            <CityComparisonChart :data="cityComparisonDisplay" :loading="loading" :error="errors.comparison" />
          </DashboardPanel>
          <DashboardPanel title="历史天气趋势" subtitle="trend · 所选日期向前 7 个观测日，不代表预报">
            <WeatherTrendChart :data="weatherTrend" :loading="loading" :error="errors.trend" />
          </DashboardPanel>
        </section>

        <section class="dashboard-column center-column" aria-label="区域数据概览">
          <DashboardPanel title="区域数据概览" subtitle="dashboard/overview · 省级或城市真实 API 聚合">
            <CenterOverview
              :location="dashboard?.location"
              :weather="latestWeather"
              :air-quality="latestAirQuality"
              :air-quality-summary="dashboard?.airQualitySummary"
              :statistics="basicStatistics"
              :detail-province="mapDetailProvince"
              :loading="loading"
              :error="errors.overview"
              @province-select="handleMapProvinceSelect"
              @map-reset="handleMapReset"
            />
          </DashboardPanel>
        </section>

        <section class="dashboard-column right-column" aria-label="空气质量数据">
          <DashboardPanel title="空气质量概况" subtitle="air-quality/latest · 固定快照，不随天气日期变化">
            <AirQualityOverview
              :air-quality="latestAirQuality"
              :air-quality-summary="dashboard?.airQualitySummary"
              :location="selection"
              :loading="loading"
              :error="errors.airQuality"
            />
          </DashboardPanel>
          <DashboardPanel title="AQI 低值城市 TOP10" subtitle="ranking · 固定快照，从低到高（越低越好）">
            <AirQualityRankingChart :data="airQualityRanking" :loading="loading" :error="errors.ranking" />
          </DashboardPanel>
          <DashboardPanel title="空气质量等级分布" subtitle="distribution · 固定快照实际返回等级">
            <AirQualityDistributionChart :data="airQualityDistribution" :loading="loading" :error="errors.distribution" />
          </DashboardPanel>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
.dashboard-alert {
  margin: 0 0 18px;
  padding: 10px 14px;
  color: var(--danger);
  font-size: 13px;
  background: rgb(100 24 48 / 32%);
  border: 1px solid rgb(255 125 134 / 40%);
  border-radius: 7px;
}

.toolbar-summary {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 11px;
  color: var(--text-muted);
  font-size: 11px;
  text-align: right;
}

.map-interaction-hint {
  display: flex;
  min-width: 0;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: var(--text-muted);
  font-size: 12px;
}

.map-interaction-hint .selector-label {
  color: var(--accent-cyan);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.selection-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 9px 12px;
  margin: 0 0 16px;
  padding: 10px 13px;
  background: rgb(11 37 76 / 58%);
  border: 1px solid var(--color-panel-line);
  border-radius: 8px;
}

.selection-controls-title {
  color: var(--accent-cyan);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.selection-controls label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
}

.selection-controls select {
  min-width: 112px;
  max-width: 190px;
  padding: 6px 25px 6px 9px;
  color: var(--text-primary);
  font: inherit;
  background: #0a2852;
  border: 1px solid rgb(45 151 216 / 55%);
  border-radius: 5px;
  outline: none;
}

.selection-controls select:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 2px rgb(52 210 255 / 16%);
}

.selection-controls select:disabled {
  cursor: wait;
  opacity: 0.65;
}

.selection-caption {
  color: var(--text-muted);
  font-size: 10px;
}

.fixed-date {
  padding-left: 10px;
  color: var(--text-secondary);
  border-left: 1px solid var(--color-panel-line);
}

.api-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--accent-green);
}

.api-status i {
  width: 7px;
  height: 7px;
  background: currentcolor;
  border-radius: 50%;
  box-shadow: 0 0 8px currentcolor;
}

.api-status.offline {
  color: var(--danger);
}

@media (max-width: 680px) {
  .map-interaction-hint {
    align-items: flex-start;
    flex-direction: column;
    gap: 5px;
  }

  .fixed-date {
    padding-top: 5px;
    padding-left: 0;
    border-top: 1px solid var(--color-panel-line);
    border-left: 0;
  }

  .toolbar-summary {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
  }

  .selection-controls {
    align-items: flex-start;
    flex-direction: column;
  }

  .selection-controls label {
    justify-content: space-between;
    width: 100%;
  }

  .selection-controls select {
    flex: 1;
    max-width: none;
  }
}
</style>
