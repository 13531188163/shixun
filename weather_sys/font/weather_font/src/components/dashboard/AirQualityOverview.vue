<script setup>
import { computed } from 'vue'
import ChartState from './ChartState.vue'
import { aqiStatusClass, formatDateTime, formatNumber } from '../../utils/formatters'

const props = defineProps({
  airQuality: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})

const gaugeStyle = computed(() => {
  const value = Number(props.airQuality?.aqi)
  const percent = Number.isFinite(value) ? Math.min(100, Math.max(0, (value / 300) * 100)) : 0
  return { background: `conic-gradient(var(--accent-cyan) ${percent}%, rgb(17 67 105 / 48%) ${percent}% 100%)` }
})
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.airQuality">
    <div class="air-quality-overview">
      <div class="aqi-gauge" :style="gaugeStyle">
        <div class="aqi-gauge-inner">
          <strong>{{ formatNumber(airQuality.aqi) }}</strong>
          <span>AQI</span>
        </div>
      </div>
      <div class="aqi-summary">
        <span class="aqi-city">{{ airQuality.city || '--' }} · {{ airQuality.province || '--' }}</span>
        <strong :class="aqiStatusClass(airQuality.status)">{{ airQuality.status || '暂无等级' }}</strong>
        <small>空气质量快照 · {{ formatDateTime(airQuality.createdAt) }}</small>
      </div>
    </div>
  </ChartState>
</template>

<style scoped>
.air-quality-overview {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 22px;
  min-height: 176px;
}

.aqi-gauge {
  display: grid;
  width: 132px;
  height: 132px;
  place-items: center;
  border-radius: 50%;
  box-shadow: 0 0 22px rgb(32 201 255 / 18%);
  transform: rotate(-25deg);
}

.aqi-gauge-inner {
  display: flex;
  width: 104px;
  height: 104px;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 3px;
  background: #062344;
  border: 1px solid rgb(62 229 255 / 28%);
  border-radius: 50%;
  transform: rotate(25deg);
}

.aqi-gauge-inner strong {
  color: var(--text-primary);
  font-size: 31px;
  line-height: 1;
}

.aqi-gauge-inner span {
  color: var(--text-muted);
  font-size: 11px;
}

.aqi-summary {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
}

.aqi-city {
  overflow-wrap: anywhere;
  color: var(--text-secondary);
  font-size: 13px;
}

.aqi-summary strong {
  font-size: 22px;
}

.aqi-summary small {
  color: var(--text-muted);
  font-size: 10px;
  line-height: 1.5;
}

.aqi-good { color: var(--accent-green); }
.aqi-moderate { color: #f4d35e; }
.aqi-light { color: #ff9f43; }
.aqi-medium { color: #ff6b6b; }
.aqi-heavy { color: #c56cf0; }
.aqi-severe { color: #ff4f76; }
.aqi-unknown { color: var(--text-muted); }

@media (max-width: 1280px) {
  .air-quality-overview { gap: 12px; }
  .aqi-gauge { width: 108px; height: 108px; }
  .aqi-gauge-inner { width: 84px; height: 84px; }
}
</style>
