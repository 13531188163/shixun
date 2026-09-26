<script setup>
import ChartState from './ChartState.vue'
import { formatDateTime, formatTemperature, formatWind, formatPrecipitation, weatherSymbol } from '../../utils/formatters'

const props = defineProps({
  weather: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.weather">
    <div class="weather-overview">
      <div class="weather-main">
        <span class="weather-symbol" aria-hidden="true">{{ weatherSymbol(weather.weather) }}</span>
        <div>
          <strong class="weather-name">{{ weather.weather || '--' }}</strong>
          <p>{{ weather.city || '--' }} · {{ weather.district || '代表区县' }}</p>
        </div>
      </div>
      <div class="weather-date">历史最新记录 · {{ formatDateTime(weather.date) }}</div>
      <div class="temperature-range">
        <span><b>{{ formatTemperature(weather.maxTemp) }}</b><small>最高</small></span>
        <span><b>{{ formatTemperature(weather.minTemp) }}</b><small>最低</small></span>
      </div>
      <div class="weather-detail-row">
        <span>平均风速 <b>{{ formatWind(weather.avgWind) }}</b></span>
        <span>最大风速 <b>{{ formatWind(weather.maxWind) }}</b></span>
        <span>降水 <b>{{ formatPrecipitation(weather.precipitation) }}</b></span>
      </div>
    </div>
  </ChartState>
</template>

<style scoped>
.weather-overview {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 13px;
}

.weather-symbol {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  color: var(--accent-cyan);
  font-size: 38px;
  line-height: 1;
  text-shadow: 0 0 16px var(--glow-color);
  background: rgb(10 88 145 / 30%);
  border: 1px solid var(--border-soft);
  border-radius: 50%;
}

.weather-name {
  color: var(--text-primary);
  font-size: 22px;
}

.weather-main p,
.weather-date {
  margin: 5px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.weather-date {
  padding-bottom: 10px;
  border-bottom: 1px solid rgb(39 140 204 / 22%);
}

.temperature-range {
  display: flex;
  gap: 28px;
}

.temperature-range span {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.temperature-range b {
  color: var(--text-primary);
  font-size: 25px;
}

.temperature-range small {
  color: var(--text-muted);
  font-size: 11px;
}

.weather-detail-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  color: var(--text-muted);
  font-size: 11px;
}

.weather-detail-row span {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.weather-detail-row b {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}
</style>
