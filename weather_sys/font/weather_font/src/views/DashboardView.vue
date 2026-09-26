<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { getHealth } from '../api/health'
import { getProvinces, getCities, getDistricts } from '../api/location'
import { getDashboardOverview } from '../api/dashboard'
import { getLatestWeather, getWeatherTrend, getCityWeatherComparison } from '../api/weather'
import { getLatestAirQuality, getAirQualityRanking, getAirQualityDistribution } from '../api/airQuality'
import DashboardHeader from '../components/dashboard/DashboardHeader.vue'
import DashboardPanel from '../components/dashboard/DashboardPanel.vue'
import LocationSelector from '../components/dashboard/LocationSelector.vue'
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
const selection = reactive({ province: '', city: '', district: '' })
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

const loading = computed(() => locationLoading.value || payloadLoading.value)
const basicStatistics = computed(() => dashboard.value?.basicStatistics || null)
const locationReady = computed(() => Boolean(selection.province && selection.city))
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
  if (selection.district) params.district = selection.district
  return params
}

function clearData() {
  dashboard.value = null
  latestWeather.value = null
  latestAirQuality.value = null
  weatherTrend.value = []
  cityComparison.value = []
  airQualityRanking.value = []
  airQualityDistribution.value = []
  Object.keys(errors).forEach((key) => { errors[key] = '' })
}

async function comparisonCitiesFor(selectedCity) {
  if (!comparisonPoolPromise) {
    const sampleProvinces = provinces.value.slice(0, 8)
    comparisonPoolPromise = Promise.allSettled(
      sampleProvinces.map((province) => getCities({ province })),
    ).then((results) => results.flatMap((result) => (
      result.status === 'fulfilled' && Array.isArray(result.value.data) ? result.value.data : []
    )))
  }
  const pool = await comparisonPoolPromise
  return [...new Set([selectedCity, ...pool].filter(Boolean))].slice(0, 10)
}

async function loadSelectedData(version) {
  if (!selection.city || version !== requestVersion) return

  payloadLoading.value = true
  const params = buildLocationParams()
  let comparisonCities
  try {
    comparisonCities = await comparisonCitiesFor(selection.city)
  } catch {
    comparisonCities = [selection.city]
  }
  if (version !== requestVersion) return

  const requests = await Promise.allSettled([
    getDashboardOverview(params),
    getLatestWeather(params),
    getWeatherTrend({ ...params, days: 7 }),
    getCityWeatherComparison({ cities: comparisonCities.join(',') }),
    getLatestAirQuality({ city: selection.city }),
    getAirQualityRanking({ limit: 10, order: 'asc' }),
    getAirQualityDistribution(),
  ])
  if (version !== requestVersion) return

  const [overviewResult, weatherResult, trendResult, comparisonResult, airResult, rankingResult, distributionResult] = requests
  dashboard.value = overviewResult.status === 'fulfilled' ? (overviewResult.value.data || null) : null

  const overviewWeather = dashboard.value?.latestWeather || null
  const overviewAirQuality = dashboard.value?.latestAirQuality || null
  latestWeather.value = weatherResult.status === 'fulfilled' ? (weatherResult.value.data || null) : overviewWeather
  latestAirQuality.value = airResult.status === 'fulfilled' ? (airResult.value.data || null) : overviewAirQuality
  weatherTrend.value = trendResult.status === 'fulfilled' && Array.isArray(trendResult.value.data) ? trendResult.value.data : []
  cityComparison.value = comparisonResult.status === 'fulfilled' && Array.isArray(comparisonResult.value.data) ? comparisonResult.value.data : []
  airQualityRanking.value = rankingResult.status === 'fulfilled' && Array.isArray(rankingResult.value.data) ? rankingResult.value.data : []
  airQualityDistribution.value = distributionResult.status === 'fulfilled' && Array.isArray(distributionResult.value.data) ? distributionResult.value.data : []

  errors.overview = overviewResult.status === 'rejected' && !dashboard.value ? errorText(overviewResult.reason, '概览接口暂时不可用') : ''
  errors.weather = weatherResult.status === 'rejected' && !latestWeather.value ? errorText(weatherResult.reason, '天气接口暂时不可用') : ''
  errors.trend = trendResult.status === 'rejected' ? errorText(trendResult.reason, '天气历史趋势读取失败') : ''
  errors.comparison = comparisonResult.status === 'rejected' ? errorText(comparisonResult.reason, '城市比较读取失败') : ''
  errors.airQuality = airResult.status === 'rejected' && !latestAirQuality.value ? errorText(airResult.reason, '空气质量接口暂时不可用') : ''
  errors.ranking = rankingResult.status === 'rejected' ? errorText(rankingResult.reason, '空气质量排名读取失败') : ''
  errors.distribution = distributionResult.status === 'rejected' ? errorText(distributionResult.reason, '空气质量分布读取失败') : ''
  payloadLoading.value = false
}

async function loadDistrictsAndData(version) {
  if (!selection.province || !selection.city || version !== requestVersion) return
  try {
    const response = await getDistricts({ province: selection.province, city: selection.city })
    if (version !== requestVersion) return
    districts.value = Array.isArray(response.data) ? response.data : []
    if (!districts.value.includes(selection.district)) selection.district = districts.value[0] || ''
  } catch (error) {
    if (version !== requestVersion) return
    districts.value = []
    selection.district = ''
    // A missing district list is a valid empty state; a server error remains visible.
    if (!isNotFound(error)) pageError.value = errorText(error, '区县列表读取失败')
  }
  await loadSelectedData(version)
}

async function handleProvinceChange(province) {
  const version = ++requestVersion
  selection.province = province
  selection.city = ''
  selection.district = ''
  cities.value = []
  districts.value = []
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
      payloadLoading.value = false
      return
    }
    selection.city = cities.value[0]
    await loadDistrictsAndData(version)
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
  selection.city = city
  selection.district = ''
  districts.value = []
  clearData()
  pageError.value = ''
  if (!city) {
    locationLoading.value = false
    payloadLoading.value = false
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
  clearData()
  pageError.value = ''
  locationLoading.value = true
  try {
    await loadSelectedData(version)
  } finally {
    if (version === requestVersion) {
      locationLoading.value = false
      payloadLoading.value = false
    }
  }
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
    <DashboardHeader />

    <div class="dashboard-content">
      <div class="dashboard-toolbar">
        <LocationSelector
          :provinces="provinces"
          :cities="cities"
          :districts="districts"
          :selection="selection"
          :loading="loading"
          @province-change="handleProvinceChange"
          @city-change="handleCityChange"
          @district-change="handleDistrictChange"
        />
        <div class="toolbar-summary">
          <span :class="['api-status', { offline: pageError || healthError }]" aria-live="polite"><i />{{ apiStatus }}</span>
          <span v-if="locationReady">{{ selection.province }} / {{ selection.city }}</span>
        </div>
      </div>

      <p v-if="pageError" class="dashboard-alert" role="alert">{{ pageError }}</p>

      <div class="dashboard-grid">
        <section class="dashboard-column left-column" aria-label="天气数据">
          <DashboardPanel title="当前天气概况" subtitle="weather/latest · 历史可获得最新记录">
            <WeatherOverview :weather="latestWeather" :loading="loading" :error="errors.weather" />
          </DashboardPanel>
          <DashboardPanel title="天气指标" subtitle="仅展示数据库支持的天气字段">
            <WeatherMetrics :weather="latestWeather" :air-quality="latestAirQuality" :loading="loading" :error="errors.weather" />
          </DashboardPanel>
          <DashboardPanel title="主要城市温度比较" subtitle="city-comparison · 实际返回城市">
            <CityComparisonChart :data="cityComparison" :loading="loading" :error="errors.comparison" />
          </DashboardPanel>
          <DashboardPanel title="历史天气趋势" subtitle="trend · 最高 / 最低温度，不代表预报">
            <WeatherTrendChart :data="weatherTrend" :loading="loading" :error="errors.trend" />
          </DashboardPanel>
        </section>

        <section class="dashboard-column center-column" aria-label="区域数据概览">
          <DashboardPanel title="区域数据概览" subtitle="dashboard/overview · 真实 API 聚合">
            <CenterOverview
              :location="dashboard?.location"
              :weather="latestWeather"
              :air-quality="latestAirQuality"
              :statistics="basicStatistics"
              :loading="loading"
              :error="errors.overview"
            />
          </DashboardPanel>
        </section>

        <section class="dashboard-column right-column" aria-label="空气质量数据">
          <DashboardPanel title="空气质量概况" subtitle="air-quality/latest · 快照数据">
            <AirQualityOverview :air-quality="latestAirQuality" :loading="loading" :error="errors.airQuality" />
          </DashboardPanel>
          <DashboardPanel title="AQI 低值城市 TOP10" subtitle="ranking · AQI 从低到高（越低越好）">
            <AirQualityRankingChart :data="airQualityRanking" :loading="loading" :error="errors.ranking" />
          </DashboardPanel>
          <DashboardPanel title="空气质量等级分布" subtitle="distribution · 仅统计实际返回等级">
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
  .toolbar-summary {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
  }
}
</style>
