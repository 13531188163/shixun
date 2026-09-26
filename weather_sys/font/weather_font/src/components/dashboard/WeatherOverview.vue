<script setup>
import ChartState from './ChartState.vue'
import { formatDateTime, formatTemperature, formatWind, formatPrecipitation, weatherTypeClass } from '../../utils/formatters'

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
        <span :class="['weather-symbol', weatherTypeClass(weather.weather)]" aria-hidden="true"><i /></span>
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
  gap: 8px;
}

.weather-main {
  display: flex;
  align-items: center;
  gap: 13px;
}

.weather-symbol {
  position: relative;
  display: grid;
  width: 48px;
  height: 48px;
  flex: none;
  place-items: center;
  color: var(--accent-cyan);
  text-shadow: 0 0 16px var(--glow-color);
  background: rgb(10 88 145 / 30%);
  border: 1px solid var(--border-soft);
  border-radius: 50%;
}

.weather-symbol::before,
.weather-symbol::after,
.weather-symbol i {
  position: absolute;
  display: block;
  content: '';
}

.weather-symbol i {
  width: 18px;
  height: 18px;
  border: 2px solid currentcolor;
  border-radius: 50%;
}

.weather-icon-sun i {
  background: rgb(246 172 105 / 80%);
  border-color: var(--color-warm);
  box-shadow: 0 0 0 5px rgb(246 172 105 / 12%), 0 0 12px rgb(246 172 105 / 55%);
}

.weather-icon-sun::before,
.weather-icon-sun::after {
  width: 32px;
  height: 2px;
  background: var(--color-warm);
  box-shadow: 0 -12px 0 -0.3px var(--color-warm), 0 12px 0 -0.3px var(--color-warm);
}

.weather-icon-sun::after { transform: rotate(90deg); }

.weather-icon-cloud i {
  width: 29px;
  height: 14px;
  top: 22px;
  border-radius: 10px;
  background: rgb(165 236 255 / 20%);
}

.weather-icon-cloud::before,
.weather-icon-partly::before {
  width: 15px;
  height: 15px;
  top: 14px;
  left: 12px;
  border: 2px solid currentcolor;
  border-radius: 50%;
  background: var(--color-bg-raised);
}

.weather-icon-partly { color: var(--color-warm); }
.weather-icon-partly i { left: 19px; top: 23px; color: var(--color-primary-light); }

.weather-icon-rain i,
.weather-icon-snow i {
  width: 27px;
  height: 13px;
  top: 19px;
  border-radius: 10px;
  background: rgb(165 236 255 / 18%);
}

.weather-icon-rain::before,
.weather-icon-rain::after {
  width: 2px;
  height: 9px;
  top: 34px;
  background: var(--color-cool);
  transform: rotate(24deg);
  box-shadow: 9px 0 0 var(--color-cool), 18px 0 0 var(--color-cool);
}

.weather-icon-snow::before {
  width: 24px;
  height: 2px;
  top: 35px;
  background: var(--color-primary-light);
  box-shadow: 0 0 7px var(--color-primary-light);
  transform: rotate(45deg);
}

.weather-icon-snow::after {
  width: 24px;
  height: 2px;
  top: 35px;
  background: var(--color-primary-light);
  box-shadow: 0 0 7px var(--color-primary-light);
  transform: rotate(-45deg);
}

.weather-name {
  color: var(--text-primary);
  font-size: 20px;
}

.weather-main p,
.weather-date {
  margin: 5px 0 0;
  color: var(--text-muted);
  font-size: 12px;
}

.weather-date {
  padding-bottom: 6px;
  border-bottom: 1px solid rgb(39 140 204 / 22%);
}

.temperature-range {
  display: flex;
  gap: 22px;
}

.temperature-range span {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.temperature-range b {
  color: var(--text-primary);
  font-size: 22px;
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
  font-size: 11px;
  font-weight: 600;
}
</style>
