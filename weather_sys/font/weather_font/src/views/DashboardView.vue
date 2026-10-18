<script setup>
import { computed, onMounted, reactive, ref } from 'vue'

import { getHealth } from '../api/health'
import { getProvinces, getCities, getDistricts } from '../api/location'
import { getDashboardOverview, getNationalDashboardOverview, getProvinceDashboardOverview } from '../api/dashboard'
import {
  getWeatherDates,
  getNationalWeatherDates,
  getNationalWeatherTrend,
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
  regionScope,
  resolveRegionOption,
} from '../utils/dashboardRegion'
import {
  currentDate,
  dataRegion,
  setCurrentDate,
  setDataRegion,
  setMapRegion,
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
const airQualityPromises = new Map()

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
const isProvinceScope = computed(() => dataRegion.scope === 'province' && Boolean(dataRegion.province))
const dataDate = computed(() => currentDate.value || latestWeather.value?.date || basicStatistics.value?.weatherLatestDate || '')
const leftRailOpen = ref(true)
const rightRailOpen = ref(true)
const apiStatus = computed(() => {
  if (pageError.value) return '需要检查 API'
  if (healthError.value) return '健康检查失败'
  if (health.value?.application === 'ok' && health.value?.database === 'ok') return 'API / DB 已连接'
  return '正在检查服务'
})

function toggleLeftRail() {
  leftRailOpen.value = !leftRailOpen.value
}

function toggleRightRail() {
  rightRailOpen.value = !rightRailOpen.value
}

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

function resolveProvince(value) {
  return resolveRegionOption(provinces.value, value)
}

function resolveCity(value, options = cities.value) {
  return resolveRegionOption(options, value)
}

function resolveDistrict(value) {
  return resolveRegionOption(districts.value, value)
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
  airQualityRanking.value = []
  airQualityDistribution.value = []
  errors.overview = ''
  errors.weather = ''
  errors.trend = ''
  errors.comparison = ''
  errors.airQuality = ''
  errors.ranking = ''
  errors.distribution = ''
}

function resetDataSelection() {
  ++requestVersion
  setDataRegion({ province: '', city: '', district: '', scope: 'country' })
  setMapRegion({ province: '', city: '', district: '', scope: 'country', path: [] })
  setCurrentDate('')
  cities.value = []
  districts.value = []
  availableDates.value = []
  comparisonPoolPromise = undefined
  airQualityPromises.clear()
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

function airQualityParams() {
  if (dataRegion.district) return null
  if (!dataRegion.province) return {}
  const params = { province: dataRegion.province }
  if (dataRegion.city) params.city = dataRegion.city
  return params
}

async function ensureSharedAirQuality(version) {
  const params = airQualityParams()
  if (!params) return { ranking: [], distribution: [], rankingError: '', distributionError: '' }
  const key = `${params.province || 'country'}::${params.city || ''}`
  if (!airQualityPromises.has(key)) {
    const requestParams = { ...params, limit: 10, order: 'asc' }
    const distributionParams = { ...params }
    airQualityPromises.set(key, Promise.allSettled([
      getAirQualityRanking(requestParams),
      getAirQualityDistribution(distributionParams),
    ]).then(([rankingResult, distributionResult]) => ({
      ranking: rankingResult.status === 'fulfilled' && Array.isArray(rankingResult.value.data)
        ? rankingResult.value.data : [],
      distribution: distributionResult.status === 'fulfilled' && Array.isArray(distributionResult.value.data)
        ? distributionResult.value.data : [],
      rankingError: rankingResult.status === 'rejected'
        ? errorText(rankingResult.reason, '空气质量排名读取失败') : '',
      distributionError: distributionResult.status === 'rejected'
        ? errorText(distributionResult.reason, '空气质量分布读取失败') : '',
    })))
  }
  const result = await airQualityPromises.get(key)
  if (version !== requestVersion) return null
  airQualityRanking.value = result.ranking
  airQualityDistribution.value = result.distribution
  errors.ranking = result.rankingError
  errors.distribution = result.distributionError
  return result
}

async function loadSelectedData(version) {
  if (version !== requestVersion) return

  payloadLoading.value = true
  const params = buildLocationParams()
  const overviewParams = currentDate.value ? { ...params, date: currentDate.value } : params
  const dateParams = currentDate.value ? { date: currentDate.value } : {}
  const nationalScope = dataRegion.scope === 'country' || !dataRegion.province
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

  const comparisonParams = {
    cities: comparisonCities.join(','),
    ...dateParams,
    ...(!nationalScope && dataRegion.province ? { province: dataRegion.province } : {}),
  }
  const requestsToMake = nationalScope
    ? [
        getNationalDashboardOverview(overviewParams),
        getNationalWeatherTrend({ ...dateParams, days: 7 }),
        comparisonCities.length
          ? getCityWeatherComparison(comparisonParams)
          : Promise.resolve({ data: [] }),
      ]
    : provinceScope
    ? [
        getProvinceDashboardOverview(overviewParams),
        getProvinceWeatherTrend({ province: dataRegion.province, ...dateParams, days: 7 }),
        comparisonCities.length
            ? getCityWeatherComparison(comparisonParams)
          : Promise.resolve({ data: [] }),
      ]
    : [
        getDashboardOverview(overviewParams),
        getWeatherTrend({ ...params, ...dateParams, days: 7 }),
          getCityWeatherComparison(comparisonParams),
      ]
  const [requests] = await Promise.all([
    Promise.allSettled([
      ...requestsToMake,
    ]),
    ensureSharedAirQuality(version),
  ])
  if (version !== requestVersion) return

  const [overviewResult, trendResult, comparisonResult] = requests
  dashboard.value = overviewResult.status === 'fulfilled' ? (overviewResult.value.data || null) : null

  const overviewWeather = dashboard.value?.latestWeather || null
  const overviewAirQuality = dataRegion.district ? null : (dashboard.value?.latestAirQuality || null)
  latestWeather.value = overviewWeather
  latestAirQuality.value = overviewAirQuality
  weatherTrend.value = trendResult.status === 'fulfilled' && Array.isArray(trendResult.value.data) ? trendResult.value.data : []
  cityComparison.value = comparisonResult.status === 'fulfilled' && Array.isArray(comparisonResult.value.data) ? comparisonResult.value.data : []

  const noWeatherMessage = dataRegion.district
    ? `${dataRegion.district}所选日期暂无天气观测`
    : dataRegion.city
      ? `${dataRegion.city}所选日期暂无天气观测`
      : dataRegion.province
        ? `${dataRegion.province}所选日期暂无天气观测`
        : '全国暂无天气观测'
  errors.overview = overviewResult.status === 'rejected' && !dashboard.value
    ? (isNotFound(overviewResult.reason) ? noWeatherMessage : errorText(overviewResult.reason, '概览接口暂时不可用'))
    : ''
  errors.weather = !latestWeather.value ? (errors.overview || noWeatherMessage) : ''
  errors.trend = trendResult.status === 'rejected' ? errorText(trendResult.reason, '天气历史趋势读取失败') : ''
  errors.comparison = comparisonResult.status === 'rejected' ? errorText(comparisonResult.reason, '城市比较读取失败') : ''
  errors.airQuality = !latestAirQuality.value && errors.overview ? '空气质量数据暂无' : ''
  if (dataRegion.district) errors.airQuality = '当前区县暂无对应 AQI 快照'
  payloadLoading.value = false
}

async function loadAvailableDates(version) {
  if (version !== requestVersion) return
  try {
    const response = dataRegion.scope === 'country' || !dataRegion.province
      ? await getNationalWeatherDates()
      : isProvinceScope.value
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

async function selectRegion({ province = '', city = '', district = '', syncMap = true } = {}) {
  const nextProvince = resolveProvince(province)
  const nextCity = resolveCity(city, nextProvince === dataRegion.province ? cities.value : [])
  const nextDistrict = resolveDistrict(district)
  const nextScope = regionScope(nextProvince, nextCity, nextDistrict)
  const sameRegion = dataRegion.province === nextProvince
    && dataRegion.city === nextCity
    && dataRegion.district === nextDistrict
    && dataRegion.scope === nextScope
  if (sameRegion && availableDates.value.length) {
    if (syncMap) {
      setMapRegion({ province: nextProvince, city: nextCity, district: nextDistrict, scope: nextScope, path: [] })
    }
    return
  }

  const version = ++requestVersion
  setDataRegion({ province: nextProvince, city: nextCity, district: nextDistrict, scope: nextScope })
  if (syncMap) {
    setMapRegion({
      province: nextProvince,
      city: nextCity,
      district: nextDistrict,
      scope: nextScope,
      path: [],
    })
  }
  setCurrentDate('')
  cities.value = []
  districts.value = []
  availableDates.value = []
  comparisonPoolPromise = undefined
  clearData()
  pageError.value = ''
  locationLoading.value = true
  payloadLoading.value = true

  try {
    if (nextProvince) {
      try {
        const cityResponse = await getCities({ province: nextProvince })
        if (version !== requestVersion) return
        cities.value = Array.isArray(cityResponse.data) ? cityResponse.data : []
      } catch (error) {
        if (version !== requestVersion) return
        cities.value = []
        if (!isNotFound(error)) pageError.value = errorText(error, '城市列表读取失败')
      }
      if (nextCity && !cities.value.includes(nextCity)) cities.value = [...cities.value, nextCity]

      if (nextCity) {
        try {
          const districtResponse = await getDistricts({ province: nextProvince, city: nextCity })
          if (version !== requestVersion) return
          districts.value = Array.isArray(districtResponse.data) ? districtResponse.data : []
        } catch (error) {
          if (version !== requestVersion) return
          districts.value = []
          if (!isNotFound(error)) pageError.value = errorText(error, '区县列表读取失败')
        }
        if (nextDistrict && !districts.value.includes(nextDistrict)) {
          districts.value = [...districts.value, nextDistrict]
        }
      }
    }
    await loadAvailableDates(version)
    await loadSelectedData(version)
  } catch (error) {
    if (version === requestVersion) pageError.value = errorText(error, '地区数据读取失败')
  } finally {
    if (version === requestVersion) {
      locationLoading.value = false
      payloadLoading.value = false
    }
  }
}

async function handleProvinceChange(province) {
  await selectRegion({ province })
}

async function handleCityChange(city) {
  await selectRegion({ province: dataRegion.province, city })
}

async function handleDistrictChange(district) {
  await selectRegion({ province: dataRegion.province, city: dataRegion.city, district })
}

async function handleMapAreaSelect(payload = {}) {
  await selectRegion({
    province: payload.province,
    city: payload.city,
    district: payload.district,
    syncMap: false,
  })
}

async function handleMapReset() {
  await selectRegion({ syncMap: false })
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
  await loadAvailableDates(version)
  await loadSelectedData(version)
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

      <div :class="['dashboard-stage', { 'left-rail-collapsed': !leftRailOpen, 'right-rail-collapsed': !rightRailOpen }]">
        <aside :class="['dashboard-rail dashboard-weather-rail', { 'is-collapsed': !leftRailOpen }]" aria-label="天气数据侧栏">
          <button
            type="button"
            class="dashboard-rail-toggle"
            :aria-expanded="leftRailOpen"
            aria-controls="dashboard-weather-rail-content"
            :aria-label="leftRailOpen ? '收起天气数据侧栏' : '展开天气数据侧栏'"
            @click="toggleLeftRail"
          >
            <span aria-hidden="true">{{ leftRailOpen ? '‹' : '›' }}</span>
          </button>
          <div id="dashboard-weather-rail-content" class="dashboard-rail-content">
            <div class="dashboard-rail-heading">
              <span class="dashboard-rail-kicker">WEATHER DATA</span>
              <strong>天气数据</strong>
            </div>
            <DashboardPanel class="dashboard-focus-panel dashboard-weather-focus" title="核心天气指标" subtitle="所选区域 · 固定日期">
              <div class="weather-focus-content">
                <WeatherOverview :weather="latestWeather" :loading="loading" :error="errors.weather" />
                <WeatherMetrics
                  :weather="latestWeather"
                  :air-quality="latestAirQuality"
                  :air-quality-summary="dashboard?.airQualitySummary"
                  :loading="loading"
                  :error="errors.weather"
                />
              </div>
            </DashboardPanel>
            <DashboardPanel class="dashboard-focus-panel dashboard-chart-panel" title="近7日天气趋势" subtitle="历史观测">
              <WeatherTrendChart :data="weatherTrend" :loading="loading" :error="errors.trend" />
            </DashboardPanel>
            <DashboardPanel class="dashboard-focus-panel dashboard-chart-panel" title="重点城市天气对比" subtitle="实际返回城市">
              <CityComparisonChart :data="cityComparisonDisplay" :loading="loading" :error="errors.comparison" />
            </DashboardPanel>
          </div>
        </aside>

        <section class="dashboard-map-stage" aria-label="全国天气与空气质量地图主舞台">
          <div class="dashboard-map-glow" aria-hidden="true" />
          <CenterOverview
            :location="dataRegion"
            :weather="latestWeather"
            :air-quality="latestAirQuality"
            :air-quality-summary="dashboard?.airQualitySummary"
            :statistics="basicStatistics"
            :loading="loading"
            :error="errors.overview"
            @area-select="handleMapAreaSelect"
            @map-reset="handleMapReset"
          />
        </section>

        <aside :class="['dashboard-rail dashboard-air-rail', { 'is-collapsed': !rightRailOpen }]" aria-label="空气质量数据侧栏">
          <button
            type="button"
            class="dashboard-rail-toggle"
            :aria-expanded="rightRailOpen"
            aria-controls="dashboard-air-rail-content"
            :aria-label="rightRailOpen ? '收起空气质量侧栏' : '展开空气质量侧栏'"
            @click="toggleRightRail"
          >
            <span aria-hidden="true">{{ rightRailOpen ? '›' : '‹' }}</span>
          </button>
          <div id="dashboard-air-rail-content" class="dashboard-rail-content">
            <div class="dashboard-rail-heading">
              <span class="dashboard-rail-kicker">AIR QUALITY</span>
              <strong>空气质量数据</strong>
            </div>
            <DashboardPanel class="dashboard-focus-panel" title="空气质量概况" subtitle="固定 AQI 快照">
              <AirQualityOverview
                :air-quality="latestAirQuality"
                :air-quality-summary="dashboard?.airQualitySummary"
                :location="dataRegion"
                :loading="loading"
                :error="errors.airQuality"
              />
            </DashboardPanel>
            <DashboardPanel class="dashboard-focus-panel dashboard-chart-panel" title="AQI 低值城市 TOP10" subtitle="固定快照 · 从低到高">
              <AirQualityRankingChart :data="airQualityRanking" :loading="loading" :error="errors.ranking" />
            </DashboardPanel>
            <DashboardPanel class="dashboard-focus-panel dashboard-chart-panel" title="空气质量等级分布" subtitle="固定快照 · 实际等级">
              <AirQualityDistributionChart :data="airQualityDistribution" :loading="loading" :error="errors.distribution" />
            </DashboardPanel>
          </div>
        </aside>
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
