<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'

const props = defineProps({
  location: { type: Object, default: null },
  status: { type: String, default: '系统检查中' },
})

const now = ref(new Date())
const timer = window.setInterval(() => {
  now.value = new Date()
}, 1000)

onBeforeUnmount(() => window.clearInterval(timer))

const locationLabel = computed(() => {
  const location = props.location || {}
  return [location.province, location.city, location.district].filter(Boolean).join(' · ') || '等待地区数据'
})

const statusClass = computed(() => (
  /失败|检查|不可用|异常/.test(props.status) ? 'is-warning' : 'is-ready'
))

function pad(value) {
  return String(value).padStart(2, '0')
}

function formatDate(value) {
  const parts = new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  }).formatToParts(value)
  const get = (type) => parts.find((part) => part.type === type)?.value || ''
  return `${get('year')}-${get('month')}-${get('day')} ${get('weekday')}`
}

function formatTime(value) {
  return `${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`
}
</script>

<template>
  <header class="dashboard-header">
    <div class="header-context">
      <span class="context-kicker">CURRENT DATA REGION</span>
      <strong>{{ locationLabel }}</strong>
      <span class="context-caption">历史最新记录 · API 数据源</span>
    </div>

    <div class="header-title-block">
      <p class="header-kicker">WEATHER &amp; AIR QUALITY DATA PLATFORM</p>
      <h1>天气与空气质量数据可视化平台</h1>
      <span class="title-rule" aria-hidden="true"><i /><b /><i /></span>
    </div>

    <div class="header-time">
      <span class="header-date">{{ formatDate(now) }}</span>
      <strong>{{ formatTime(now) }}</strong>
      <span :class="['system-status', statusClass]"><i />{{ status }}</span>
    </div>
  </header>
</template>

<style scoped>
.dashboard-header {
  position: relative;
  display: grid;
  width: min(1920px, calc(100% - 32px));
  min-height: var(--header-height);
  grid-template-columns: minmax(220px, 1fr) minmax(420px, 1.5fr) minmax(220px, 1fr);
  align-items: center;
  gap: 18px;
  margin: 0 auto;
  padding: 10px 16px 11px;
  border-bottom: 1px solid var(--color-panel-border);
  background: linear-gradient(180deg, rgb(4 30 65 / 76%), rgb(3 16 37 / 12%));
}

.dashboard-header::before {
  position: absolute;
  right: 12%;
  bottom: -2px;
  left: 12%;
  height: 3px;
  content: '';
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
  box-shadow: 0 0 14px var(--color-glow);
}

.header-context,
.header-time {
  display: flex;
  min-width: 0;
  flex-direction: column;
}

.header-context {
  gap: 3px;
  align-items: flex-start;
}

.context-kicker,
.header-kicker {
  color: var(--color-primary);
  font-size: 9px;
  letter-spacing: 0.15em;
}

.header-context strong {
  overflow: hidden;
  max-width: 100%;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.context-caption {
  color: var(--color-text-muted);
  font-size: 10px;
}

.header-title-block {
  display: flex;
  align-items: center;
  flex-direction: column;
  gap: 3px;
  text-align: center;
}

.header-kicker {
  margin: 0;
  color: var(--color-text-muted);
}

h1 {
  margin: 0;
  color: var(--color-text);
  font-size: var(--font-title);
  font-weight: 700;
  letter-spacing: 0.14em;
  line-height: 1.2;
  background: linear-gradient(90deg, #a4eaff, #fff, #a4eaff);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 18px rgb(30 192 255 / 35%);
  white-space: nowrap;
}

.title-rule {
  display: flex;
  width: min(300px, 70%);
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.title-rule::before,
.title-rule::after {
  height: 1px;
  flex: 1;
  content: '';
  background: linear-gradient(90deg, transparent, var(--color-primary));
}

.title-rule::after { transform: scaleX(-1); }

.title-rule i,
.title-rule b {
  display: block;
  width: 4px;
  height: 4px;
  background: var(--color-primary);
  border-radius: 50%;
  box-shadow: 0 0 8px var(--color-primary);
}

.title-rule b {
  width: 7px;
  height: 7px;
}

.header-time {
  align-items: flex-end;
  gap: 3px;
  color: var(--color-text-secondary);
  font-size: 11px;
  text-align: right;
}

.header-time strong {
  color: var(--color-text);
  font-size: 24px;
  letter-spacing: 0.08em;
  line-height: 1;
}

.system-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 2px;
  color: var(--accent-green);
  font-size: 10px;
}

.system-status i {
  width: 7px;
  height: 7px;
  background: currentcolor;
  border-radius: 50%;
  box-shadow: 0 0 9px currentcolor;
}

.system-status.is-warning { color: var(--danger); }

@media (max-width: 1500px) {
  .dashboard-header { width: calc(100% - 20px); }
  .dashboard-header { grid-template-columns: minmax(170px, 1fr) minmax(360px, 1.5fr) minmax(180px, 1fr); }
  .header-time strong { font-size: 20px; }
  h1 { letter-spacing: 0.1em; }
}

@media (max-width: 900px) {
  .dashboard-header { grid-template-columns: 1fr 1fr; }
  .header-title-block { grid-column: 1 / -1; grid-row: 1; }
  .header-context { grid-column: 1; grid-row: 2; }
  .header-time { grid-column: 2; grid-row: 2; }
  h1 { font-size: 27px; }
}

@media (max-width: 560px) {
  .dashboard-header { display: flex; align-items: stretch; flex-direction: column; gap: 7px; }
  .header-title-block { order: -1; }
  .header-context,
  .header-time { align-items: flex-start; text-align: left; }
  .header-time { flex-direction: row; align-items: baseline; flex-wrap: wrap; gap: 8px; }
  .system-status { width: 100%; }
  h1 { font-size: 25px; letter-spacing: 0.06em; }
}
</style>
