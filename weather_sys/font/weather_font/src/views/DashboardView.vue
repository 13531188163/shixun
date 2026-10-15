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
import {
  currentDate,
  dataRegion,
  setCurrentDate,
  setDataRegion,
} from '../stores/regionStore'

const provinces = ref([])
const cities = ref([])
const districts = ref([])
const availableDates = ref([])
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

const DIRECT_MUNICIPALITIES = new Set(['北京', '北京市', '上海', '上海市', '天津', '天津市', '重庆', '重庆市'])

function provinceLabel(province) {
  const name = String(province || '')
  if (!DIRECT_MUNICIPALITIES.has(name)) return name
  return name.endsWith('市') ? name : `${name}市`
}

const loading = computed(() => locationLoading.value || payloadLoading.value)
const basicStatistics = computed(() => dashboard.value?.basicStatistics || null)
const cityComparisonDisplay = computed(() => cityComparison.value.slice(0, 6))
const locationReady = computed(() => Boolean(dataRegion.province))
const isProvinceScope = computed(() => dataRegion.scope === 'province' || !dataRegion.city)
const dataDate = computed(() => currentDate.value || latestWeather.value?.date || basicStatistics.value?.weatherLatestDate || '')
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
  if (!dataRegion.province) return {}
  const params = { province: dataRegion.province, city: dataRegion.city }
  if (!dataRegion.city) return { province: dataRegion.province }
  if (dataRegion.district) params.district = dataRegion.district
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

function resetDataSelection() {
  ++requestVersion
  setDataRegion({ province: '', city: '', district: '', scope: 'country' })
  setCurrentDate('')
  cities.value = []
  districts.value = []
  availableDates.value = []
  comparisonPoolPromise = undefined
  clearData()
  pageError.value = ''
  locationLoading.value = false
  payloadLoading.value = false
}

async function comparisonCitiesFor(selectedCity) {
  if (!comparisonPoolPromise) {
    const sampleProvinces = provinces.value.slice(0, 8).filter((province) => province !== dataRegion.province)
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
  if (!dataRegion.province || version !== requestVersion) return

  payloadLoading.value = true
  const params = buildLocationParams()
  const overviewParams = currentDate.value ? { ...params, date: currentDate.value } : params
  const dateParams = currentDate.value ? { date: currentDate.value } : {}
  const provinceScope = isProvinceScope.value
  let comparisonCities = []
  if (provinceScope) {
    comparisonCities = cities.value.slice(0, 10)
  } else {
    try {
      comparisonCities = await comparisonCitiesFor(dataRegion.city)
    } catch {
      comparisonCities = [dataRegion.city]
    }
  }
  if (version !== requestVersion) return

  const requestsToMake = provinceScope
    ? [
        getProvinceDashboardOverview(overviewParams),
        getProvinceWeatherTrend({ province: dataRegion.province, ...dateParams, days: 7 }),
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
  if (!dataRegion.province || version !== requestVersion) return
  try {
    const response = isProvinceScope.value
      ? await getProvinceWeatherDates({ province: dataRegion.province })
      : await getWeatherDates(buildLocationParams())
    if (version !== requestVersion) return
    availableDates.value = Array.isArray(response.data) ? response.data : []
    if (!availableDates.value.includes(currentDate.value)) {
      setCurrentDate(availableDates.value[0] || '')
    }
  } catch (error) {
    if (version !== requestVersion) return
    availableDates.value = []
    setCurrentDate('')
    if (!isNotFound(error)) pageError.value = errorText(error, '可用日期读取失败')
  }
}

async function loadDistrictsAndData(version) {
  if (!dataRegion.province || !dataRegion.city || version !== requestVersion) return
  try {
    const response = await getDistricts({ province: dataRegion.province, city: dataRegion.city })
    if (version !== requestVersion) return
    districts.value = Array.isArray(response.data) ? response.data : []
    if (!districts.value.includes(dataRegion.district)) {
      setDataRegion({ ...dataRegion, district: '' })
    }
  } catch (error) {
    if (version !== requestVersion) return
    districts.value = []
    setDataRegion({ ...dataRegion, district: '' })
    // A missing district list is a valid empty state; a server error remains visible.
    if (!isNotFound(error)) pageError.value = errorText(error, '区县列表读取失败')
  }
  await loadAvailableDates(version)
  await loadSelectedData(version)
}

async function handleProvinceChange(province) {
  const version = ++requestVersion
  setDataRegion({ province, city: '', district: '', scope: province ? 'province' : 'country' })
  setCurrentDate('')
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

async function handleCityChange(city) {
  const version = ++requestVersion
  setDataRegion({ ...dataRegion, city, district: '', scope: city ? 'city' : 'province' })
  setCurrentDate('')
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
  setDataRegion({ ...dataRegion, district })
  setCurrentDate('')
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
  setCurrentDate(date)
  clearData()
  pageError.value = ''
  await loadSelectedData(version)
}

async function loadInitial() {
  pageError.value = ''
  healthError.value = ''
  provinces.value = []
  resetDataSelection()
  const version = requestVersion
  payloadLoading.value = true
  const [healthResult, provincesResult] = await Promise.allSettled([getHealth(), getProvinces()])
  if (version !== requestVersion) return
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
  await ensureSharedAirQuality()
  if (version === requestVersion) {
    locationLoading.value = false
    payloadLoading.value = false
  }
}

onMounted(loadInitial)
</script>

<template>
  <main class="dashboard-shell">
    <DashboardHeader :location="dataRegion" :data-date="dataDate" :status="apiStatus">
      <template #filters>
        <div class="header-selection-layout">
          <div class="selection-controls" aria-label="区域筛选条件">
            <span class="selection-controls-title">区域筛选</span>
            <label class="selection-level-field">
              <span>区域级</span>
              <select disabled>
                <option v-if="!dataRegion.province">全国汇总</option>
                <option v-else-if="!dataRegion.city">省级汇总（选择城市后下钻）</option>
                <option v-else>城市级</option>
              </select>
            </label>
            <label>
              <span>省级行政区</span>
              <select :value="dataRegion.province" :disabled="loading || !provinces.length" @change="handleProvinceChange($event.target.value)">
                <option value="">全国</option>
                <option v-for="province in provinces" :key="province" :value="province">{{ provinceLabel(province) }}</option>
              </select>
            </label>
            <label>
              <span>城市</span>
              <select :value="dataRegion.city" :disabled="loading || !dataRegion.province || !cities.length" @change="handleCityChange($event.target.value)">
                <option value="">全部城市</option>
                <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
              </select>
            </label>
            <label>
              <span>区县</span>
              <select :value="dataRegion.district" :disabled="loading || !dataRegion.city || !districts.length" @change="handleDistrictChange($event.target.value)">
                <option value="">全部区县</option>
                <option v-for="district in districts" :key="district" :value="district">{{ district }}</option>
              </select>
            </label>
            <label>
              <span>数据日期</span>
              <select :value="currentDate" :disabled="loading || !availableDates.length" @change="handleDateChange($event.target.value)">
                <option v-if="!availableDates.length" value="">选择区域后可用</option>
                <option v-for="date in availableDates" :key="date" :value="date">{{ date }}</option>
              </select>
            </label>
            <span class="selection-caption">共 {{ availableDates.length }} 个可用观测日期</span>
          </div>
          <div class="toolbar-summary">
            <span :class="['api-status', { offline: pageError || healthError }]" aria-live="polite"><i />{{ apiStatus }}</span>
            <span v-if="locationReady">{{ dataRegion.province }}<template v-if="dataRegion.city"> / {{ dataRegion.city }}</template><template v-else> / 省级汇总</template><template v-if="dataRegion.district"> / {{ dataRegion.district }}</template></span>
            <span v-else>全国汇总</span>
          </div>
        </div>
      </template>
    </DashboardHeader>

    <div class="dashboard-content">
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
              :location="dataRegion"
              :weather="latestWeather"
              :air-quality="latestAirQuality"
              :air-quality-summary="dashboard?.airQualitySummary"
              :statistics="basicStatistics"
              :loading="loading"
              :error="errors.overview"
            />
          </DashboardPanel>
        </section>

        <section class="dashboard-column right-column" aria-label="空气质量数据">
          <DashboardPanel title="空气质量概况" subtitle="air-quality/latest · 固定快照，不随天气日期变化">
            <AirQualityOverview
              :air-quality="latestAirQuality"
              :air-quality-summary="dashboard?.airQualitySummary"
              :location="dataRegion"
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

.header-selection-layout {
  display: flex;
  min-width: 0;
  width: 100%;
  align-items: center;
  gap: 14px;
  padding: 7px 13px;
  background: linear-gradient(90deg, rgb(6 42 81 / 92%), rgb(4 28 61 / 84%));
  border: 1px solid rgb(35 143 211 / 58%);
  border-radius: 6px;
  box-shadow: inset 0 0 16px rgb(30 132 204 / 10%), 0 5px 16px rgb(0 8 26 / 18%);
}

.toolbar-summary {
  display: flex;
  min-width: 142px;
  align-items: flex-end;
  flex-direction: column;
  flex-wrap: wrap;
  justify-content: center;
  gap: 3px;
  color: var(--text-muted);
  font-size: 10px;
  text-align: right;
  white-space: nowrap;
}

.selection-controls {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px 13px;
  margin: 0;
  padding: 0;
  background: transparent;
  border: 0;
  border-radius: 0;
}

.selection-controls-title {
  color: var(--accent-cyan);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.selection-controls label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
}

.selection-controls select {
  min-width: 118px;
  max-width: 205px;
  height: 32px;
  padding: 5px 26px 5px 9px;
  color: var(--text-primary);
  font: inherit;
  background: linear-gradient(180deg, #0b315f, #08254b);
  border: 1px solid rgb(45 151 216 / 68%);
  border-radius: 4px;
  outline: none;
}

.selection-level-field select { min-width: 188px; }

.selection-controls select:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 2px rgb(52 210 255 / 16%);
}

.selection-controls select:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.selection-caption {
  color: var(--text-muted);
  font-size: 10px;
  white-space: nowrap;
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
  .header-selection-layout {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }

  .toolbar-summary {
    width: 100%;
    min-width: 0;
    align-items: flex-start;
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
