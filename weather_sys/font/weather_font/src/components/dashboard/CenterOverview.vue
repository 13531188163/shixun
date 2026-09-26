<script setup>
import ChartState from './ChartState.vue'
import { formatNumber, formatDateTime, formatTemperature } from '../../utils/formatters'

const props = defineProps({
  location: { type: Object, default: null },
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  statistics: { type: Object, default: null },
  loading: Boolean,
  error: { type: String, default: '' },
})
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.location && !props.weather && !props.airQuality">
    <div class="center-overview">
      <div class="area-heading">
        <div>
          <span class="area-kicker">CURRENT DATA REGION</span>
          <h3>{{ location?.province || '--' }} · {{ location?.city || '--' }}</h3>
          <p>{{ location?.district || '稳定代表区县' }} · source-backed latest snapshot</p>
        </div>
        <div class="center-aqi">
          <span>AQI</span>
          <strong>{{ formatNumber(airQuality?.aqi) }}</strong>
          <small>{{ airQuality?.status || '暂无等级' }}</small>
        </div>
      </div>

      <div class="data-visual-placeholder" aria-label="区域数据抽象可视化区域">
        <div class="visual-grid" aria-hidden="true" />
        <span class="visual-orbit orbit-one" aria-hidden="true" />
        <span class="visual-orbit orbit-two" aria-hidden="true" />
        <span class="visual-core" aria-hidden="true">{{ weather?.weather || 'DATA' }}</span>
        <div class="visual-caption">
          <b>区域数据聚合视图</b>
          <span>MAP PLACEHOLDER · GEO DATA FUTURE ENHANCEMENT</span>
        </div>
      </div>

      <div class="center-facts">
        <div><span>天气最新日期</span><b>{{ formatDateTime(weather?.date) }}</b></div>
        <div><span>温度区间</span><b>{{ formatTemperature(weather?.minTemp) }} — {{ formatTemperature(weather?.maxTemp) }}</b></div>
        <div><span>天气记录</span><b>{{ formatNumber(statistics?.weatherRecordCount) }}</b></div>
        <div><span>AQI 快照</span><b>{{ formatDateTime(airQuality?.createdAt) }}</b></div>
      </div>
    </div>
  </ChartState>
</template>

<style scoped>
.center-overview {
  display: flex;
  min-height: 486px;
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

.data-visual-placeholder {
  position: relative;
  display: grid;
  min-height: 300px;
  flex: 1;
  place-items: center;
  overflow: hidden;
  background: radial-gradient(circle, rgb(30 159 223 / 16%), transparent 58%), rgb(2 23 49 / 68%);
  border: 1px solid rgb(43 157 216 / 34%);
  border-radius: 8px;
}

.visual-grid {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(90deg, transparent 0 34px, rgb(55 159 216 / 10%) 34px 35px), repeating-linear-gradient(0deg, transparent 0 34px, rgb(55 159 216 / 10%) 34px 35px);
  transform: perspective(260px) rotateX(55deg) translateY(42px) scale(1.35);
  transform-origin: center bottom;
}

.visual-orbit,
.visual-core {
  position: absolute;
  border: 1px solid rgb(62 229 255 / 52%);
  border-radius: 50%;
}

.visual-orbit {
  width: 190px;
  height: 94px;
  box-shadow: 0 0 18px rgb(32 201 255 / 25%);
  transform: rotate(-24deg);
}

.orbit-two {
  width: 270px;
  height: 135px;
  border-color: rgb(67 140 255 / 44%);
  transform: rotate(34deg);
}

.visual-core {
  display: grid;
  width: 100px;
  height: 100px;
  place-items: center;
  color: var(--text-primary);
  font-size: 11px;
  letter-spacing: 0.1em;
  background: radial-gradient(circle, rgb(62 229 255 / 44%), rgb(8 58 101 / 80%) 58%, transparent 64%);
  border-color: var(--accent-cyan);
  box-shadow: 0 0 32px rgb(32 201 255 / 50%);
}

.visual-caption {
  position: absolute;
  right: 15px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 3px;
  color: var(--text-muted);
  font-size: 9px;
  letter-spacing: 0.08em;
}

.visual-caption b {
  color: var(--text-secondary);
  font-size: 11px;
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
