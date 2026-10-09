<script setup>
import ChartState from './ChartState.vue'
import ChinaMapChart from './ChinaMapChart.vue'
import { formatNumber, formatDateTime, formatTemperature } from '../../utils/formatters'

const props = defineProps({
  location: { type: Object, default: null },
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  airQualitySummary: { type: Object, default: null },
  statistics: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['area-select'])
</script>

<template>
  <!-- 地图边界是独立的真实资源；后端数据加载时保留地图，避免整块面板闪烁。 -->
  <ChartState :loading="false" error="" :empty="false">
    <div class="center-overview">
      <div class="area-heading">
        <div>
          <span class="area-kicker">FIXED DATA DATE</span>
          <h3>{{ location?.province || '--' }} · {{ location?.city || '省级汇总' }}</h3>
          <p>{{ location?.district || (location?.scope === 'province' ? '全省聚合' : '稳定代表区县') }} · {{ weather?.date || '固定日期数据' }}</p>
        </div>
        <div class="center-aqi">
          <span>AQI</span>
          <strong>{{ formatNumber(airQuality?.aqi ?? airQualitySummary?.averageAqi) }}</strong>
          <small>{{ airQuality?.status || (airQualitySummary ? '省级平均 AQI' : '暂无等级') }}</small>
        </div>
      </div>

      <div class="data-map" aria-label="全国行政区天气与空气质量地图">
        <ChinaMapChart
          :location="location"
          :weather="weather"
          :air-quality="airQuality"
          :loading="loading"
          :error="error"
          @area-select="emit('area-select', $event)"
        />
        <div class="map-weather-badge">
          <span>{{ weather?.weather || '--' }}</span>
          <strong>{{ formatTemperature(weather?.maxTemp) }}</strong>
          <small>当前最高温</small>
        </div>
      </div>

      <div class="center-facts">
        <div><span>天气最新日期</span><b>{{ formatDateTime(weather?.date) }}</b></div>
        <div><span>温度区间</span><b>{{ formatTemperature(weather?.minTemp) }} — {{ formatTemperature(weather?.maxTemp) }}</b></div>
        <div><span>天气记录</span><b>{{ formatNumber(statistics?.weatherRecordCount) }}</b></div>
        <div><span>AQI 快照</span><b>{{ formatDateTime(airQuality?.createdAt || airQualitySummary?.createdAt) }}</b></div>
      </div>
    </div>
  </ChartState>
</template>

<style scoped>
.center-overview {
  display: flex;
  min-height: 0;
  height: 100%;
  flex: 1;
  flex-direction: column;
  gap: 18px;
}

.area-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.area-kicker {
  color: var(--accent-cyan);
  font-size: 10px;
  letter-spacing: 0.16em;
}

h3 {
  margin: 7px 0 4px;
  color: var(--text-primary);
  font-size: clamp(19px, 2vw, 29px);
}

.area-heading p {
  margin: 0;
  color: var(--text-muted);
  font-size: 11px;
}

.center-aqi {
  display: flex;
  min-width: 64px;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.center-aqi span,
.center-aqi small {
  color: var(--text-muted);
  font-size: 10px;
}

.center-aqi strong {
  color: var(--accent-cyan);
  font-size: 28px;
  line-height: 1;
}

.center-aqi small {
  color: var(--accent-green);
}

.data-map {
  position: relative;
  display: grid;
  min-width: 0;
  min-height: 0;
  flex: 1;
  overflow: hidden;
  background: radial-gradient(circle, rgb(30 159 223 / 16%), transparent 58%), rgb(2 23 49 / 68%);
  border: 1px solid rgb(43 157 216 / 34%);
  border-radius: 8px;
}

.map-weather-badge {
  position: absolute;
  right: 17px;
  top: 102px;
  display: grid;
  min-width: 88px;
  padding: 8px 10px;
  place-items: end;
  align-content: center;
  gap: 2px;
  color: var(--text-primary);
  font-size: 11px;
  letter-spacing: 0.08em;
  background: rgb(3 27 57 / 78%);
  border: 1px solid rgb(50 201 238 / 56%);
  border-radius: 5px;
  box-shadow: 0 0 20px rgb(32 201 255 / 22%);
}

.map-weather-badge strong {
  color: var(--color-text);
  font-size: 18px;
  line-height: 1;
}

.map-weather-badge small {
  color: var(--color-text-muted);
  font-size: 9px;
  letter-spacing: 0.04em;
}

.center-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.center-facts div {
  display: flex;
  min-height: 46px;
  flex-direction: column;
  justify-content: space-between;
  gap: 5px;
  padding: 9px 10px;
  background: rgb(7 55 102 / 40%);
  border-left: 2px solid var(--accent-blue);
}

.center-facts span {
  color: var(--text-muted);
  font-size: 10px;
}

.center-facts b {
  overflow-wrap: anywhere;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}
</style>
