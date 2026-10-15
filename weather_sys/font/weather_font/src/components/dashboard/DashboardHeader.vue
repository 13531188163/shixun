<script setup>
import { computed } from 'vue'

const props = defineProps({
  location: { type: Object, default: null },
  dataDate: { type: String, default: '' },
  status: { type: String, default: '系统检查中' },
})

const navigation = [
  { label: '首页大屏', path: '/' },
  { label: '温度分析', path: '/temperature' },
  { label: '降水分析', path: '/rainfall' },
  { label: '风力分析', path: '/wind' },
  { label: '空气质量', path: '/air-quality' },
  { label: '区域对比', path: '/comparison' },
]

const locationLabel = computed(() => {
  const location = props.location || {}
  const parts = [location.province, location.city, location.district].filter(Boolean)
  if (location.scope === 'country') return '全国汇总'
  if (location.scope === 'province' && location.province) parts.push('省级汇总')
  return parts.join(' · ') || '等待地区数据'
})

const statusClass = computed(() => (
  /失败|检查|不可用|异常/.test(props.status) ? 'is-warning' : 'is-ready'
))
</script>

<template>
  <header class="dashboard-header" :aria-label="locationLabel">
    <div class="header-main">
      <RouterLink class="brand-lockup" to="/" aria-label="返回首页大屏">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 64 46" focusable="false">
            <path d="M17 38h31a10 10 0 0 0 1-20 15 15 0 0 0-28-3A12 12 0 0 0 17 38Z" />
          </svg>
        </span>
        <strong class="brand-title">全国天气态势大屏</strong>
      </RouterLink>

      <nav class="header-navigation" aria-label="平台页面导航">
        <RouterLink
          v-for="item in navigation"
          :key="item.path"
          :to="item.path"
          class="header-navigation-link"
          exact-active-class="is-active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="header-time">
        <span class="clock-mark" aria-hidden="true">
          <svg viewBox="0 0 34 34" focusable="false">
            <circle cx="17" cy="17" r="13" />
            <path d="M17 9v8l5 3" />
          </svg>
        </span>
        <div class="header-time-copy">
          <strong>{{ dataDate || '--' }}</strong>
          <span>固定数据日期</span>
          <span :class="['system-status', statusClass]"><i />{{ status }}</span>
        </div>
      </div>
    </div>

    <div v-if="$slots.filters" class="header-filter-row">
      <slot name="filters" />
    </div>
  </header>
</template>

<style scoped>
.dashboard-header {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: var(--header-height);
  flex-direction: column;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgb(4 30 65 / 95%), rgb(3 16 37 / 94%)),
    linear-gradient(90deg, transparent, rgb(17 89 150 / 22%), transparent);
  border-bottom: 1px solid rgb(37 147 211 / 72%);
  box-shadow: 0 7px 24px rgb(0 9 29 / 26%);
}

.dashboard-header::before {
  position: absolute;
  inset: 0;
  pointer-events: none;
  content: '';
  background:
    linear-gradient(120deg, transparent 0 3%, rgb(45 191 255 / 22%) 3.1%, transparent 3.25% 96.5%, rgb(45 191 255 / 17%) 96.6%, transparent 96.8%),
    linear-gradient(180deg, transparent 0 78%, rgb(32 166 226 / 12%), transparent 80%);
  opacity: 0.95;
}

.dashboard-header::after {
  position: absolute;
  right: 4%;
  bottom: -1px;
  left: 4%;
  height: 2px;
  pointer-events: none;
  content: '';
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent);
  box-shadow: 0 0 16px var(--color-glow);
}

.header-main,
.header-filter-row {
  position: relative;
  z-index: 1;
  width: min(1920px, calc(100% - 32px));
  margin: 0 auto;
}

.header-main {
  display: grid;
  min-height: 64px;
  grid-template-columns: minmax(300px, 1fr) auto minmax(250px, 1fr);
  align-items: center;
  gap: 20px;
  padding: 6px 16px;
}

.brand-lockup {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  justify-self: start;
  gap: 12px;
  color: var(--color-text);
  text-decoration: none;
}

.brand-mark {
  display: inline-flex;
  width: 48px;
  height: 38px;
  align-items: center;
  justify-content: center;
  color: var(--color-primary-light);
  filter: drop-shadow(0 0 7px rgb(28 201 255 / 42%));
}

.brand-mark svg {
  width: 46px;
  height: 34px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3.5;
}

.brand-title {
  overflow: hidden;
  color: var(--color-text);
  font-size: clamp(22px, 1.85vw, 31px);
  font-weight: 700;
  letter-spacing: 0.08em;
  line-height: 1;
  text-shadow: 0 0 15px rgb(30 192 255 / 34%);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-navigation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  padding: 3px;
  background: linear-gradient(180deg, rgb(8 57 104 / 88%), rgb(4 31 66 / 84%));
  border: 1px solid rgb(31 142 215 / 66%);
  border-radius: 6px;
  box-shadow: inset 0 0 15px rgb(20 124 199 / 16%), 0 0 14px rgb(0 139 230 / 12%);
}

.header-navigation-link {
  min-width: 92px;
  padding: 10px 15px;
  color: var(--color-text-secondary);
  font-size: 13px;
  text-align: center;
  text-decoration: none;
  border: 1px solid transparent;
  border-radius: 4px;
  white-space: nowrap;
  transition: color 160ms ease, background-color 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.header-navigation-link:hover,
.header-navigation-link:focus-visible,
.header-navigation-link.is-active {
  color: var(--color-text);
  background: linear-gradient(180deg, rgb(18 138 220 / 70%), rgb(7 74 137 / 74%));
  border-color: rgb(37 190 255 / 82%);
  outline: none;
  box-shadow: inset 0 0 12px rgb(78 211 255 / 19%), 0 0 12px rgb(14 165 242 / 21%);
}

.header-time {
  display: flex;
  min-width: 0;
  align-items: center;
  justify-self: end;
  gap: 10px;
  color: var(--color-text-secondary);
}

.clock-mark {
  display: inline-flex;
  width: 34px;
  height: 34px;
  flex: none;
  color: var(--color-primary-light);
  filter: drop-shadow(0 0 7px rgb(28 201 255 / 40%));
}

.clock-mark svg {
  width: 34px;
  height: 34px;
  fill: none;
  stroke: currentcolor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.8;
}

.header-time-copy {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  flex-direction: column;
  gap: 2px;
}

.header-time-copy strong {
  color: var(--color-primary-light);
  font-size: 17px;
  font-weight: 600;
  letter-spacing: 0.04em;
  line-height: 1.1;
  white-space: nowrap;
}

.header-time-copy > span:not(.system-status) {
  color: var(--color-text-secondary);
  font-size: 10px;
}

.system-status {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--accent-green);
  font-size: 9px;
  white-space: nowrap;
}

.system-status i {
  width: 6px;
  height: 6px;
  background: currentcolor;
  border-radius: 50%;
  box-shadow: 0 0 8px currentcolor;
}

.system-status.is-warning { color: var(--danger); }

.header-filter-row {
  display: flex;
  min-height: 53px;
  align-items: center;
  padding: 5px 0 8px;
}

:slotted(.header-selection-layout),
:slotted(.big-screen-filter-layout) {
  width: 100%;
}

@media (max-width: 1500px) {
  .header-main,
  .header-filter-row { width: calc(100% - 20px); }

  .header-main { grid-template-columns: minmax(255px, 1fr) auto minmax(210px, 1fr); gap: 12px; }
  .header-navigation-link { min-width: 76px; padding-inline: 9px; font-size: 12px; }
  .brand-title { font-size: 26px; }
  .header-time-copy strong { font-size: 15px; }
}

@media (max-width: 1100px) {
  .header-main { grid-template-columns: minmax(220px, 1fr) auto minmax(170px, 1fr); }
  .header-navigation-link { min-width: 64px; padding-inline: 6px; font-size: 11px; }
  .brand-title { font-size: 23px; }
  .header-time { gap: 6px; }
  .clock-mark,
  .clock-mark svg { width: 29px; height: 29px; }
}

@media (max-width: 900px) {
  .header-main { grid-template-columns: 1fr 1fr; }
  .brand-lockup { grid-column: 1; }
  .header-time { grid-column: 2; }
  .header-navigation { grid-column: 1 / -1; grid-row: 2; justify-self: stretch; overflow-x: auto; }
  .header-navigation-link { flex: 1 0 auto; }
  .header-main { padding-top: 8px; padding-bottom: 8px; }
}

@media (max-width: 560px) {
  .header-main,
  .header-filter-row { width: calc(100% - 16px); }

  .header-main {
    display: flex;
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
    padding-inline: 0;
  }

  .brand-lockup { justify-content: center; }
  .brand-title { font-size: 24px; }
  .header-navigation { order: 2; justify-content: flex-start; }
  .header-time { justify-content: center; order: 1; }
  .header-filter-row { padding-top: 0; }
}
</style>
