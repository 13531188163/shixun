<script setup>
import ChartState from './ChartState.vue'
import { formatNumber, formatPrecipitation, formatTemperature, formatWind } from '../../utils/formatters'

const props = defineProps({
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  airQualitySummary: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})

function unavailable(value) {
  return value === null || value === undefined || value === '' ? '未提供' : value
}
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.weather && !props.airQuality">
    <div class="weather-metrics-panel" data-testid="weather-metrics-panel">
      <div class="metrics-hero">
        <div>
          <span class="metrics-kicker">SELECTED WEATHER RECORD</span>
          <strong>{{ weather?.weather || '暂无天气状况' }}</strong>
          <small>{{ weather?.date || '固定日期暂无记录' }}</small>
        </div>
        <div class="hero-range">
          <span>日温区间</span>
          <b>{{ formatTemperature(weather?.minTemp) }} — {{ formatTemperature(weather?.maxTemp) }}</b>
        </div>
      </div>

      <div class="metric-grid">
        <article class="metric-card metric-card-accent">
          <span>当前气温</span>
          <strong>未提供</strong>
          <small>源表无逐时字段</small>
        </article>
        <article class="metric-card">
          <span>最高温度</span>
          <strong>{{ formatTemperature(weather?.maxTemp) }}</strong>
          <small>日记录</small>
        </article>
        <article class="metric-card">
          <span>最低温度</span>
          <strong>{{ formatTemperature(weather?.minTemp) }}</strong>
          <small>日记录</small>
        </article>
        <article class="metric-card">
          <span>平均风速</span>
          <strong>{{ formatWind(weather?.avgWind) }}</strong>
          <small>weather_data</small>
        </article>
        <article class="metric-card">
          <span>最大风速</span>
          <strong>{{ formatWind(weather?.maxWind) }}</strong>
          <small>weather_data</small>
        </article>
        <article class="metric-card">
          <span>降水量</span>
          <strong>{{ formatPrecipitation(weather?.precipitation) }}</strong>
          <small>日累计</small>
        </article>
        <article class="metric-card metric-card-muted">
          <span>相对湿度</span>
          <strong>{{ unavailable(weather?.humidity) }}</strong>
          <small>数据库未提供</small>
        </article>
        <article class="metric-card metric-card-muted">
          <span>风向</span>
          <strong>{{ unavailable(weather?.windDirection) }}</strong>
          <small>数据库未提供</small>
        </article>
        <article class="metric-card aqi-card">
          <span>空气质量 AQI</span>
          <strong>{{ formatNumber(airQuality?.aqi ?? airQualitySummary?.averageAqi) }}</strong>
          <small>{{ airQuality?.status || (airQualitySummary ? '省级平均 AQI' : '暂无等级') }}</small>
        </article>
      </div>
    </div>
  </ChartState>
</template>

<style scoped>
.weather-metrics-panel { display: flex; min-height: 0; flex: 1; flex-direction: column; gap: 10px; }
.metrics-hero {
  display: flex;
  min-width: 0;
  align-items: flex-end;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 11px;
  background: linear-gradient(120deg, rgb(12 78 126 / 58%), rgb(7 39 78 / 42%));
  border: 1px solid rgb(50 183 231 / 32%);
  border-radius: 6px;
  box-shadow: inset 0 0 18px rgb(21 163 220 / 8%);
}
.metrics-hero > div:first-child { display: flex; min-width: 0; flex-direction: column; gap: 3px; }
.metrics-kicker { color: var(--accent-cyan); font-size: 8px; letter-spacing: 0.12em; }
.metrics-hero strong { overflow: hidden; color: var(--text-primary); font-size: clamp(18px, 1.5vw, 25px); text-overflow: ellipsis; white-space: nowrap; }
.metrics-hero small { color: var(--text-muted); font-size: 10px; }
.hero-range { display: flex; min-width: 0; flex-direction: column; align-items: flex-end; gap: 3px; text-align: right; }
.hero-range span { color: var(--text-muted); font-size: 10px; }
.hero-range b { color: var(--accent-cyan); font-size: 13px; white-space: nowrap; }
.metric-grid { display: grid; min-height: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }
.metric-card { display: flex; min-width: 0; min-height: 57px; flex-direction: column; justify-content: space-between; gap: 4px; padding: 7px 8px; background: rgb(8 54 101 / 42%); border: 1px solid rgb(42 145 206 / 28%); border-radius: 5px; }
.metric-card span { color: var(--text-muted); font-size: 10px; }
.metric-card strong { overflow: hidden; color: var(--text-primary); font-size: clamp(14px, 1.1vw, 21px); font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.metric-card small { overflow: hidden; color: var(--text-muted); font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
.metric-card-accent strong { color: var(--accent-cyan); }
.metric-card-muted strong { color: var(--text-muted); font-size: 14px; }
.aqi-card { border-color: rgb(69 217 173 / 42%); background: linear-gradient(145deg, rgb(13 85 104 / 42%), rgb(8 49 84 / 48%)); }
.aqi-card strong { color: var(--accent-green); }
.aqi-card small { color: var(--accent-green); }

@media (max-width: 1500px) {
  .metrics-hero { padding: 8px 9px; }
  .metric-grid { gap: 5px; }
  .metric-card { min-height: 49px; padding: 6px 7px; }
  .metric-card strong { font-size: 15px; }
}

@media (max-width: 680px) {
  .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .metrics-hero { align-items: flex-start; flex-direction: column; }
  .hero-range { align-items: flex-start; text-align: left; }
}
</style>
