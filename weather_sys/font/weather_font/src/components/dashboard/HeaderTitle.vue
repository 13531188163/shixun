<script setup>
import { computed } from 'vue'

const props = defineProps({
  location: { type: Object, default: null },
  dataDate: { type: String, default: '' },
  updatedAt: { type: String, default: '' },
  status: { type: String, default: '系统检查中' },
})

const locationLabel = computed(() => {
  const location = props.location || {}
  const parts = [location.province, location.city, location.district].filter(Boolean)
  if (location.scope === 'province' && location.province) parts.push('省级汇总')
  return parts.join(' · ') || '等待地区数据'
})

const statusClass = computed(() => (
  /失败|检查|不可用|异常/.test(props.status) ? 'is-warning' : 'is-ready'
))
</script>

<template>
  <header class="header-title" data-testid="header-title">
    <div class="header-context">
      <span class="context-kicker">CURRENT DATA REGION</span>
      <strong :title="locationLabel">{{ locationLabel }}</strong>
      <span class="context-caption">固定历史日期 · API / MySQL 数据源</span>
    </div>

    <div class="header-title-block">
      <p class="header-kicker">WEATHER &amp; AIR QUALITY DATA PLATFORM</p>
      <h1>天气与空气质量数据可视化平台</h1>
      <span class="title-rule" aria-hidden="true"><i /><b /><i /></span>
    </div>

    <div class="header-time">
      <span class="header-date">固定数据日期 · {{ dataDate || '--' }}</span>
      <strong>{{ updatedAt || '历史快照' }}</strong>
      <span :class="['system-status', statusClass]"><i />{{ status }}</span>
    </div>
  </header>
</template>

<style scoped>
.header-title {
  position: relative;
  display: grid;
  width: 100%;
  min-height: clamp(72px, 8vh, 94px);
  grid-template-columns: minmax(190px, 1fr) minmax(420px, 1.6fr) minmax(190px, 1fr);
  align-items: center;
  gap: 18px;
  padding: 10px clamp(12px, 1.4vw, 25px) 12px;
  overflow: hidden;
  background: linear-gradient(180deg, rgb(5 30 65 / 88%), rgb(3 16 37 / 18%));
  border: 1px solid rgb(49 166 220 / 42%);
  border-radius: 8px;
  box-shadow: inset 0 0 25px rgb(25 146 207 / 7%), 0 10px 30px rgb(0 8 26 / 24%);
}

.header-title::before {
  position: absolute;
  right: 11%;
  bottom: -2px;
  left: 11%;
  height: 3px;
  content: '';
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
  box-shadow: 0 0 16px var(--color-glow);
}

.header-title::after {
  position: absolute;
  top: 0;
  right: 0;
  width: 35%;
  height: 100%;
  pointer-events: none;
  content: '';
  background: linear-gradient(120deg, transparent, rgb(41 200 245 / 7%), transparent);
  transform: translateX(100%);
  animation: header-scan 8s ease-in-out infinite;
}

.header-context,
.header-time {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.header-context { align-items: flex-start; gap: 4px; }
.context-kicker,
.header-kicker { color: var(--color-primary); font-size: 9px; letter-spacing: 0.16em; }
.header-context strong { max-width: 100%; overflow: hidden; color: var(--color-text); font-size: clamp(13px, 1vw, 17px); text-overflow: ellipsis; white-space: nowrap; }
.context-caption { color: var(--color-text-muted); font-size: 10px; }

.header-title-block { display: flex; align-items: center; flex-direction: column; gap: 3px; text-align: center; }
.header-kicker { margin: 0; color: var(--color-text-muted); }
h1 {
  margin: 0;
  color: var(--color-text);
  font-size: clamp(24px, 2.25vw, 40px);
  font-weight: 700;
  letter-spacing: 0.13em;
  line-height: 1.18;
  background: linear-gradient(90deg, #a4eaff, #fff, #a4eaff);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgb(30 192 255 / 38%);
  white-space: nowrap;
}

.title-rule { display: flex; width: min(340px, 72%); align-items: center; justify-content: center; gap: 6px; }
.title-rule::before,
.title-rule::after { height: 1px; flex: 1; content: ''; background: linear-gradient(90deg, transparent, var(--color-primary)); }
.title-rule::after { transform: scaleX(-1); }
.title-rule i,
.title-rule b { display: block; width: 4px; height: 4px; background: var(--color-primary); border-radius: 50%; box-shadow: 0 0 8px var(--color-primary); }
.title-rule b { width: 7px; height: 7px; }

.header-time { align-items: flex-end; gap: 4px; color: var(--color-text-secondary); font-size: 11px; text-align: right; }
.header-date { color: var(--color-text-muted); }
.header-time strong { color: var(--color-text); font-size: clamp(15px, 1.35vw, 23px); letter-spacing: 0.06em; line-height: 1.1; }
.system-status { display: inline-flex; align-items: center; gap: 6px; margin-top: 2px; color: var(--accent-green); font-size: 10px; }
.system-status i { width: 7px; height: 7px; background: currentcolor; border-radius: 50%; box-shadow: 0 0 9px currentcolor; }
.system-status.is-warning { color: var(--danger); }

@keyframes header-scan {
  0%, 45% { opacity: 0; transform: translateX(100%); }
  60%, 78% { opacity: 1; transform: translateX(-220%); }
  100% { opacity: 0; transform: translateX(-220%); }
}

@media (max-width: 1500px) {
  .header-title { grid-template-columns: minmax(170px, 1fr) minmax(360px, 1.5fr) minmax(175px, 1fr); gap: 11px; }
  h1 { letter-spacing: 0.09em; }
}

@media (max-width: 900px) {
  .header-title { grid-template-columns: 1fr 1fr; }
  .header-title-block { grid-column: 1 / -1; grid-row: 1; }
  .header-context { grid-column: 1; grid-row: 2; }
  .header-time { grid-column: 2; grid-row: 2; }
  h1 { font-size: 27px; }
}

@media (max-width: 560px) {
  .header-title { display: flex; align-items: stretch; flex-direction: column; gap: 7px; }
  .header-title-block { order: -1; }
  .header-context,
  .header-time { align-items: flex-start; text-align: left; }
  .header-time { flex-direction: row; align-items: baseline; flex-wrap: wrap; gap: 8px; }
  .system-status { width: 100%; }
  h1 { font-size: 24px; letter-spacing: 0.05em; }
}

@media (prefers-reduced-motion: reduce) {
  .header-title::after { animation: none; }
}
</style>
