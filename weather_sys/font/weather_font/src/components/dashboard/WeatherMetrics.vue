<script setup>
import ChartState from './ChartState.vue'
import { formatNumber, formatTemperature, formatWind, formatPrecipitation } from '../../utils/formatters'

const props = defineProps({
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})

const metrics = [
  { key: 'maxTemp', label: '最高温度', formatter: formatTemperature },
  { key: 'minTemp', label: '最低温度', formatter: formatTemperature },
  { key: 'avgWind', label: '平均风速', formatter: formatWind },
  { key: 'maxWind', label: '最大风速', formatter: formatWind },
  { key: 'precipitation', label: '降水量', formatter: formatPrecipitation },
]
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.weather && !props.airQuality">
    <div class="metric-grid">
      <article v-for="metric in metrics" :key="metric.key" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.formatter(weather?.[metric.key]) }}</strong>
      </article>
      <article class="metric-card aqi-card">
        <span>空气质量 AQI</span>
        <strong>{{ formatNumber(airQuality?.aqi) }}</strong>
        <small>{{ airQuality?.status || '暂无等级' }}</small>
      </article>
    </div>
  </ChartState>
</template>

<style scoped>
.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}

.metric-card {
  display: flex;
  min-height: 52px;
  flex-direction: column;
  justify-content: space-between;
  padding: 8px 9px;
  background: rgb(8 54 101 / 42%);
  border: 1px solid rgb(42 145 206 / 26%);
  border-radius: 6px;
}

.metric-card span {
  color: var(--text-muted);
  font-size: 11px;
}

.metric-card strong {
  color: var(--text-primary);
  font-size: clamp(17px, 1.25vw, var(--font-metric));
  font-weight: 700;
  white-space: nowrap;
}

.metric-card small {
  color: var(--accent-green);
  font-size: 10px;
}

.aqi-card strong {
  color: var(--accent-cyan);
}

@media (max-width: 680px) {
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metric-card strong { font-size: 20px; }
}
</style>
