<script setup>
import { computed, onMounted, ref } from 'vue'

import { getHealth } from '../api/health'
import { getProvinces, getCities, getDistricts } from '../api/location'
import { getDashboardOverview } from '../api/dashboard'

const loading = ref(true)
const errorMessage = ref('')
const health = ref(null)
const provinces = ref([])
const selectedLocation = ref({ province: '', city: '', district: '' })
const dashboard = ref(null)

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
const latestWeather = computed(() => dashboard.value?.latestWeather || null)
const latestAirQuality = computed(() => dashboard.value?.latestAirQuality || null)
const basicStatistics = computed(() => dashboard.value?.basicStatistics || null)

function displayValue(value, fallback = '暂无数据') {
  return value === null || value === undefined || value === '' ? fallback : value
}

function buildLocationParams() {
  const params = {
    province: selectedLocation.value.province,
    city: selectedLocation.value.city,
  }
  if (selectedLocation.value.district) {
    params.district = selectedLocation.value.district
  }
  return params
}

async function loadDashboard() {
  loading.value = true
  errorMessage.value = ''
  try {
    const healthResponse = await getHealth()
    health.value = healthResponse.data

    const provincesResponse = await getProvinces()
    provinces.value = Array.isArray(provincesResponse.data) ? provincesResponse.data : []
    if (!provinces.value.length) {
      errorMessage.value = '后端已连接，但暂无省份数据'
      return
    }

    const province = provinces.value[0]
    const citiesResponse = await getCities({ province })
    const cities = Array.isArray(citiesResponse.data) ? citiesResponse.data : []
    if (!cities.length) {
      errorMessage.value = '后端已连接，但暂无城市数据'
      return
    }

    const city = cities[0]
    let district = ''
    try {
      const districtsResponse = await getDistricts({ province, city })
      const districts = Array.isArray(districtsResponse.data) ? districtsResponse.data : []
      district = districts[0] || ''
    } catch {
      // 区县没有数据时仍可用省份和城市调用 Dashboard。
      district = ''
    }

    selectedLocation.value = { province, city, district }
    const dashboardResponse = await getDashboardOverview(buildLocationParams())
    dashboard.value = dashboardResponse.data
  } catch (error) {
    console.error('WeatherDemo API request failed:', error)
    errorMessage.value = error.message || '后端服务连接失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <main class="dashboard-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">WeatherDemo</p>
        <h1>后端 API 联调页</h1>
        <p class="subtitle">当前页面只展示真实 Flask API 返回的数据。</p>
      </div>
      <button class="refresh-button" type="button" :disabled="loading" @click="loadDashboard">
        {{ loading ? '加载中…' : '重新加载' }}
      </button>
    </header>

    <p v-if="loading" class="notice">正在连接后端并读取真实地区数据…</p>
    <p v-else-if="errorMessage" class="notice notice-error">{{ errorMessage }}</p>

    <section class="status-grid" aria-label="服务状态">
      <article class="status-card">
        <span class="label">后端状态</span>
        <strong :class="health?.application === 'ok' ? 'success' : 'muted'">
          {{ health?.application === 'ok' ? '正常' : '暂无数据' }}
        </strong>
      </article>
      <article class="status-card">
        <span class="label">数据库状态</span>
        <strong :class="health?.database === 'ok' ? 'success' : 'muted'">
          {{ health?.database === 'ok' ? '正常' : '暂无数据' }}
        </strong>
      </article>
      <article class="status-card">
        <span class="label">API Base URL</span>
        <strong class="value">{{ apiBaseUrl }}</strong>
      </article>
      <article class="status-card">
        <span class="label">省份数量</span>
        <strong class="value">{{ provinces.length || '暂无数据' }}</strong>
      </article>
    </section>

    <section class="panel" aria-label="联调地区">
      <div class="panel-heading">
        <h2>真实测试地区</h2>
        <span v-if="selectedLocation.city" class="location-tag">
          {{ selectedLocation.province }} · {{ selectedLocation.city }}
          <template v-if="selectedLocation.district"> · {{ selectedLocation.district }}</template>
        </span>
      </div>
      <p v-if="!selectedLocation.city" class="empty-state">暂无地区数据</p>
      <div v-else class="data-grid">
        <div>
          <span class="label">天气日期</span>
          <strong>{{ displayValue(latestWeather?.date) }}</strong>
        </div>
        <div>
          <span class="label">天气</span>
          <strong>{{ displayValue(latestWeather?.weather) }}</strong>
        </div>
        <div>
          <span class="label">最高温度</span>
          <strong>{{ displayValue(latestWeather?.maxTemp) }}</strong>
        </div>
        <div>
          <span class="label">最低温度</span>
          <strong>{{ displayValue(latestWeather?.minTemp) }}</strong>
        </div>
        <div>
          <span class="label">AQI</span>
          <strong>{{ displayValue(latestAirQuality?.aqi) }}</strong>
        </div>
        <div>
          <span class="label">空气等级</span>
          <strong>{{ displayValue(latestAirQuality?.status) }}</strong>
        </div>
      </div>
    </section>

    <section class="panel" aria-label="Dashboard API 状态">
      <div class="panel-heading">
        <h2>Dashboard Overview</h2>
        <span :class="dashboard ? 'badge badge-success' : 'badge'">
          {{ dashboard ? '加载成功' : '暂无数据' }}
        </span>
      </div>
      <div v-if="basicStatistics" class="statistics">
        <div>
          <span class="label">天气记录</span>
          <strong>{{ basicStatistics.weatherRecordCount }}</strong>
        </div>
        <div>
          <span class="label">空气质量记录</span>
          <strong>{{ basicStatistics.airQualityRecordCount }}</strong>
        </div>
        <div>
          <span class="label">天气最新日期</span>
          <strong>{{ displayValue(basicStatistics.weatherLatestDate) }}</strong>
        </div>
        <div>
          <span class="label">空气快照时间</span>
          <strong>{{ displayValue(basicStatistics.airQualitySnapshotAt) }}</strong>
        </div>
      </div>
      <p v-else class="empty-state">Dashboard 数据暂无</p>
    </section>
  </main>
</template>

<style scoped>
.dashboard-page {
  width: min(1100px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
}

.page-header,
.panel-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}

.eyebrow,
.label,
.subtitle,
.notice,
.empty-state {
  color: #64748b;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 8px;
  font-size: clamp(28px, 4vw, 42px);
}

h2 {
  margin-bottom: 0;
  font-size: 20px;
}

.subtitle {
  margin-bottom: 0;
}

.refresh-button {
  padding: 10px 16px;
  color: white;
  background: #2563eb;
  border: 0;
  border-radius: 8px;
}

.refresh-button:disabled {
  cursor: wait;
  opacity: 0.6;
}

.notice {
  margin: 24px 0 0;
  padding: 12px 16px;
  background: #e8f0fe;
  border-radius: 8px;
}

.notice-error {
  color: #b42318;
  background: #fef0ef;
}

.status-grid,
.data-grid,
.statistics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.status-grid {
  margin-top: 28px;
}

.status-card,
.panel {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgb(15 23 42 / 5%);
}

.status-card {
  display: flex;
  min-height: 100px;
  flex-direction: column;
  justify-content: space-between;
  padding: 18px;
}

.panel {
  margin-top: 24px;
  padding: 24px;
}

.data-grid,
.statistics {
  margin-top: 24px;
}

.data-grid > div,
.statistics > div {
  display: flex;
  min-height: 70px;
  flex-direction: column;
  justify-content: space-between;
  padding: 14px;
  background: #f8fafc;
  border-radius: 8px;
}

.label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
}

.value,
.data-grid strong,
.statistics strong {
  overflow-wrap: anywhere;
}

.success,
.badge-success {
  color: #15803d;
}

.muted,
.badge {
  color: #64748b;
}

.location-tag,
.badge {
  padding: 5px 10px;
  font-size: 13px;
  background: #f1f5f9;
  border-radius: 999px;
}

.badge-success {
  background: #dcfce7;
}

@media (max-width: 760px) {
  .page-header {
    flex-direction: column;
  }

  .status-grid,
  .data-grid,
  .statistics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 480px) {
  .dashboard-page {
    width: min(100% - 24px, 1100px);
    padding-top: 24px;
  }

  .status-grid,
  .data-grid,
  .statistics {
    grid-template-columns: 1fr;
  }

  .panel {
    padding: 18px;
  }
}
</style>
