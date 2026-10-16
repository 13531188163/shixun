<script setup>
/**
 * 只负责 Dashboard 的空间编排，不持有地图或业务状态。
 * 所有数据请求、行政区钻取和选中状态仍由 DashboardView/ChinaMapChart 管理。
 */
</script>

<template>
  <main class="dashboard-layout" data-testid="dashboard-layout">
    <header v-if="$slots.header" class="dashboard-layout-header">
      <slot name="header" />
    </header>

    <section v-if="$slots.toolbar" class="dashboard-layout-toolbar" aria-label="数据筛选与服务状态">
      <slot name="toolbar" />
    </section>

    <p v-if="$slots.alert" class="dashboard-layout-alert" role="alert">
      <slot name="alert" />
    </p>

    <div class="dashboard-layout-main">
      <section class="dashboard-layout-column dashboard-layout-left" aria-label="天气数据面板">
        <slot name="left" />
      </section>
      <section class="dashboard-layout-column dashboard-layout-center" aria-label="行政区地图面板">
        <slot name="center" />
      </section>
      <section class="dashboard-layout-column dashboard-layout-right" aria-label="空气质量分析面板">
        <slot name="right" />
      </section>
    </div>

    <footer v-if="$slots.bottom" class="dashboard-layout-bottom">
      <slot name="bottom" />
    </footer>
  </main>
</template>

<style scoped>
.dashboard-layout {
  position: relative;
  display: grid;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  height: 100dvh;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  gap: clamp(7px, 0.7vw, 12px);
  padding: clamp(8px, 0.85vw, 16px);
  overflow: hidden;
  isolation: isolate;
  color: var(--color-text);
  background:
    radial-gradient(ellipse 45% 55% at 50% 48%, rgb(9 76 131 / 31%), transparent 78%),
    radial-gradient(ellipse 42% 45% at 5% 13%, rgb(9 44 90 / 38%), transparent 84%),
    linear-gradient(180deg, #061a36 0%, #020d20 43%, #020b1b 100%);
}

.dashboard-layout::before {
  position: fixed;
  z-index: -1;
  inset: 0;
  pointer-events: none;
  content: '';
  background:
    repeating-linear-gradient(90deg, transparent 0 83px, var(--color-grid) 83px 84px),
    repeating-linear-gradient(0deg, transparent 0 83px, var(--color-grid) 83px 84px);
  opacity: 0.52;
}

.dashboard-layout-header,
.dashboard-layout-toolbar,
.dashboard-layout-alert,
.dashboard-layout-bottom {
  min-width: 0;
}

.dashboard-layout-toolbar {
  display: flex;
  min-height: 0;
  flex-direction: column;
  gap: 7px;
}

.dashboard-layout-alert {
  margin: 0;
  padding: 9px 12px;
  color: var(--danger);
  font-size: 12px;
  background: rgb(100 24 48 / 32%);
  border: 1px solid rgb(255 125 134 / 40%);
  border-radius: 6px;
}

.dashboard-layout-main {
  display: grid;
  min-width: 0;
  min-height: 0;
  grid-template-columns: minmax(230px, 0.9fr) minmax(520px, 2fr) minmax(260px, 0.92fr);
  gap: clamp(8px, 0.75vw, 14px);
}

.dashboard-layout-column {
  display: flex;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
  gap: clamp(8px, 0.65vw, 12px);
}

.dashboard-layout-center :deep(.dashboard-panel) {
  min-height: 0;
  flex: 1 1 auto;
}

.dashboard-layout-left :deep(.dashboard-panel),
.dashboard-layout-right :deep(.dashboard-panel) {
  min-height: 0;
  flex: 1 1 0;
}

.dashboard-layout-left :deep(.panel-body),
.dashboard-layout-right :deep(.panel-body) {
  min-height: 0;
}

@media (max-width: 1699px) {
  .dashboard-layout {
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .dashboard-layout-main {
    grid-template-columns: minmax(220px, 0.84fr) minmax(500px, 1.7fr) minmax(235px, 0.84fr);
  }
}

@media (max-width: 1199px) {
  .dashboard-layout-main {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-layout-center {
    grid-column: 1 / -1;
    grid-row: 1;
    min-height: 560px;
  }

  .dashboard-layout-left {
    grid-column: 1;
    grid-row: 2;
  }

  .dashboard-layout-right {
    grid-column: 2;
    grid-row: 2;
  }
}

@media (max-width: 760px) {
  .dashboard-layout {
    height: auto;
    min-height: 100vh;
    padding: 8px;
  }

  .dashboard-layout-main {
    display: flex;
    flex-direction: column;
  }

  .dashboard-layout-center {
    order: -1;
    min-height: 500px;
  }

  .dashboard-layout-left,
  .dashboard-layout-right {
    min-height: 260px;
  }
}
</style>
