<script setup>
import { onBeforeUnmount, ref } from 'vue'

const now = ref(new Date())
const timer = window.setInterval(() => {
  now.value = new Date()
}, 1000)

onBeforeUnmount(() => window.clearInterval(timer))

function formatDate(value) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    weekday: 'short',
  }).format(value)
}

function formatTime(value) {
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).format(value)
}
</script>

<template>
  <header class="dashboard-header">
    <div class="header-brand">
      <span class="brand-mark">◈</span>
      <div>
        <p class="header-kicker">WEATHER &amp; AIR QUALITY DATA VISUALIZATION</p>
        <h1>天气与空气质量可视化大屏</h1>
      </div>
    </div>
    <div class="header-time">
      <span>{{ formatDate(now) }}</span>
      <strong>{{ formatTime(now) }}</strong>
      <span class="system-status"><i />系统运行正常</span>
    </div>
  </header>
</template>

<style scoped>
.dashboard-header {
  position: relative;
  display: flex;
  width: min(1920px, calc(100% - 48px));
  min-height: 104px;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  margin: 0 auto;
  padding: 20px 26px;
  border-bottom: 1px solid rgb(40 164 222 / 55%);
  background: linear-gradient(180deg, rgb(3 32 68 / 78%), rgb(3 19 43 / 20%));
}

.dashboard-header::after {
  position: absolute;
  right: 14%;
  bottom: -2px;
  left: 14%;
  height: 3px;
  content: '';
  background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
  box-shadow: 0 0 14px var(--glow-color);
}

.header-brand,
.header-time {
  display: flex;
  align-items: center;
}

.header-brand {
  gap: 14px;
}

.brand-mark {
  color: var(--accent-cyan);
  font-size: 36px;
  text-shadow: 0 0 14px var(--glow-color);
}

.header-kicker {
  margin: 0 0 4px;
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.18em;
}

h1 {
  margin: 0;
  color: #f3fbff;
  font-size: clamp(24px, 3vw, 42px);
  letter-spacing: 0.08em;
  text-shadow: 0 0 18px rgb(30 192 255 / 55%);
}

.header-time {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px 14px;
  color: var(--text-secondary);
  font-size: 13px;
  text-align: right;
}

.header-time strong {
  color: var(--text-primary);
  font-size: 25px;
  letter-spacing: 0.06em;
}

.system-status {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  color: var(--accent-green);
}

.system-status i {
  width: 8px;
  height: 8px;
  background: var(--accent-green);
  border-radius: 50%;
  box-shadow: 0 0 10px var(--accent-green);
}

@media (max-width: 680px) {
  .dashboard-header {
    width: calc(100% - 20px);
    align-items: flex-start;
    flex-direction: column;
    padding: 20px 0;
  }

  .header-time {
    justify-content: flex-start;
    text-align: left;
  }

  .system-status {
    justify-content: flex-start;
  }
}
</style>
