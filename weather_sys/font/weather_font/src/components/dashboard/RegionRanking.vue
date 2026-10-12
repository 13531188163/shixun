<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { formatNumber } from '../../utils/formatters'
import {
  CHART_COLORS,
  DARK_TOOLTIP,
  VALUE_AXIS,
  numericValue,
  rgba,
} from '../../utils/chartTheme'
import { computed, ref } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)
const rows = computed(() => (props.data || [])
  .filter((row) => numericValue(row?.maxTemp) !== null)
  .sort((a, b) => numericValue(b.maxTemp) - numericValue(a.maxTemp) || String(a.city || '').localeCompare(String(b.city || '')))
  .slice(0, 10))

function buildOption() {
  const ordered = [...rows.value].reverse()
  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { top: 8, right: 42, bottom: 18, left: 54, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...DARK_TOOLTIP,
      formatter: (items) => {
        const item = items?.[0]
        const row = ordered[item?.dataIndex]
        return row
          ? `<strong>${row.city}</strong><br/>最高温：${formatNumber(row.maxTemp)}°C<br/>最低温：${formatNumber(row.minTemp)}°C`
          : ''
      },
    },
    xAxis: {
      type: 'value', min: 0, ...VALUE_AXIS,
      axisLabel: { ...VALUE_AXIS.axisLabel, formatter: (value) => `${value}°` },
    },
    yAxis: {
      type: 'category',
      data: ordered.map((row) => row.city),
      axisLine: { lineStyle: { color: CHART_COLORS.axis } },
      axisTick: { show: false },
      axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 10, width: 52, overflow: 'truncate' },
    },
    series: [{
      name: '最高温',
      type: 'bar',
      barMaxWidth: 14,
      data: ordered.map((row) => numericValue(row.maxTemp)),
      itemStyle: { color: CHART_COLORS.warm, borderRadius: [0, 4, 4, 0], shadowBlur: 9, shadowColor: rgba(CHART_COLORS.warm, 0.25) },
      label: { show: true, position: 'right', distance: 6, color: CHART_COLORS.textSecondary, fontSize: 10, formatter: (params) => `${formatNumber(params.value)}°` },
      emphasis: { focus: 'series', itemStyle: { color: CHART_COLORS.warmLight } },
    }],
  }
}

useEChart(chartElement, buildOption, [() => rows.value, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!rows.length" empty-message="当前区域暂无城市温度排名">
    <div ref="chartElement" class="echart region-ranking-chart" data-testid="region-ranking" aria-label="当前区域城市最高温排名图" />
  </ChartState>
</template>

<style scoped>
.echart { width: 100%; height: 100%; min-height: 145px; flex: 1 1 auto; }
</style>
