<script setup>
import DashboardHeader from '../dashboard/DashboardHeader.vue'

defineProps({
  pageNumber: { type: String, required: true },
  title: { type: String, required: true },
  description: { type: String, required: true },
  headerStatus: { type: String, default: '页面框架已就绪' },
  toolbarStatus: { type: String, default: '页面框架 · 等待后续业务开发' },
  dataDate: { type: String, default: '' },
})

const filterFields = ['区域级', '省份', '城市', '区县', '数据日期']
</script>

<template>
  <main class="dashboard-shell big-screen-shell">
    <DashboardHeader :location="{ scope: 'country' }" :data-date="dataDate" :status="headerStatus">
      <template #filters>
        <slot name="filters">
          <div class="big-screen-filter-layout">
            <div class="big-screen-filters" aria-label="区域筛选栏">
              <span class="big-screen-filter-title">区域筛选</span>
              <label v-for="field in filterFields" :key="field">
                <span>{{ field }}</span>
                <select disabled>
                  <option>待接入真实数据</option>
                </select>
              </label>
              <span class="big-screen-filter-caption">等待真实数据接口接入</span>
            </div>
          </div>
        </slot>
      </template>
    </DashboardHeader>

    <div class="dashboard-content big-screen-content">
      <div class="dashboard-toolbar big-screen-toolbar">
        <div class="big-screen-heading">
          <span class="big-screen-page-number">PAGE {{ pageNumber }}</span>
          <strong>{{ title }}</strong>
          <span>{{ description }}</span>
        </div>
        <span class="big-screen-status">{{ toolbarStatus }}</span>
      </div>

      <section class="big-screen-main" :aria-label="`${title}内容区域`">
        <slot />
      </section>
    </div>
  </main>
</template>

<style scoped>
.big-screen-content { gap: 10px; }

.big-screen-toolbar { min-height: 58px; }

.big-screen-heading {
  display: flex;
  min-width: 0;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 9px;
}

.big-screen-page-number,
.big-screen-filter-title {
  color: var(--accent-cyan);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.big-screen-heading strong {
  color: var(--color-text);
  font-size: 18px;
}

.big-screen-heading span:last-child,
.big-screen-status {
  color: var(--color-text-muted);
  font-size: 11px;
}

.big-screen-status { white-space: nowrap; }

.big-screen-filter-layout {
  width: 100%;
}

.big-screen-filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px 13px;
  padding: 7px 13px;
  background: linear-gradient(90deg, rgb(6 42 81 / 92%), rgb(4 28 61 / 84%));
  border: 1px solid rgb(35 143 211 / 58%);
  border-radius: 6px;
  box-shadow: inset 0 0 16px rgb(30 132 204 / 10%), 0 5px 16px rgb(0 8 26 / 18%);
}

.big-screen-filters label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
  font-size: 11px;
}

.big-screen-filters select {
  min-width: 128px;
  height: 32px;
  padding: 6px 24px 6px 9px;
  color: var(--color-text-secondary);
  font: inherit;
  background: linear-gradient(180deg, #0b315f, #08254b);
  border: 1px solid rgb(45 151 216 / 68%);
  border-radius: 4px;
  opacity: 0.72;
}

.big-screen-filter-caption {
  color: var(--color-text-muted);
  font-size: 10px;
  white-space: nowrap;
}

.big-screen-main {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

:slotted(.page-empty-area) {
  display: flex;
  min-height: 520px;
  flex: 1;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
  background:
    radial-gradient(circle at center, rgb(20 118 177 / 14%), transparent 58%),
    repeating-linear-gradient(90deg, transparent 0 44px, rgb(79 151 197 / 5%) 45px, transparent 46px),
    repeating-linear-gradient(0deg, transparent 0 44px, rgb(79 151 197 / 5%) 45px, transparent 46px),
    rgb(2 23 49 / 46%);
  border: 1px solid rgb(43 157 216 / 34%);
  border-radius: var(--panel-radius);
}

@media (max-width: 680px) {
  .big-screen-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .big-screen-status { white-space: normal; }

  .big-screen-filters {
    align-items: flex-start;
    flex-direction: column;
  }

  .big-screen-filters label {
    justify-content: space-between;
    width: 100%;
  }

  .big-screen-filters select { flex: 1; }

  :slotted(.page-empty-area) { min-height: 360px; }
}
</style>
