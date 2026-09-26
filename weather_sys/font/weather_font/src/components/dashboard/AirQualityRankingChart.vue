<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { aqiStatusColor, formatNumber } from '../../utils/formatters'
import {
  CHART_COLORS,
  DARK_TOOLTIP,
  VALUE_AXIS,
  numericValue,
  rgba,
} from '../../utils/chartTheme'
import { ref } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
  order: { type: String, default: 'asc' },
})

const chartElement = ref(null)

function buildOption() {
  const rows = props.data || []
  // ECharts renders the first category at the bottom. Reversing the API's
  // stable order therefore keeps the best (lowest AQI) city at the top.
  const ordered = [...rows].reverse()
  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { top: 10, right: 38, bottom: 20, left: 64, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...DARK_TOOLTIP,
      formatter: (items) => {
        const item = items?.[0]
        const row = ordered[item?.dataIndex]
        return row
          ? `<strong>${row.city}</strong><br/>AQI：${formatNumber(row.aqi)} · ${row.status || '未知'}`
          : ''
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      ...VALUE_AXIS,
      axisLabel: { ...VALUE_AXIS.axisLabel, formatter: (value) => `${value}` },
      splitLine: { lineStyle: { color: CHART_COLORS.grid, width: 1 } },
    },
    yAxis: {
      type: 'category',
      data: ordered.map((row) => row.city),
      axisLine: { lineStyle: { color: CHART_COLORS.axis } },
      axisTick: { show: false },
      axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11, width: 58, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      barMaxWidth: 16,
      barMinHeight: 2,
      data: ordered.map((row) => {
        const value = numericValue(row.aqi)
        return {
          value,
          itemStyle: {
            color: aqiStatusColor(row.status),
            borderRadius: [0, 4, 4, 0],
          },
        }
      }),
      label: {
        show: true,
        position: 'right',
        distance: 7,
        color: CHART_COLORS.textSecondary,
        fontSize: 10,
        formatter: (params) => formatNumber(params.value),
      },
      itemStyle: { shadowBlur: 8, shadowColor: rgba(CHART_COLORS.cyan, 0.16) },
      emphasis: { focus: 'series' },
    }],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div
      ref="chartElement"
      class="echart ranking-chart"
      :aria-label="order === 'asc' ? '空气质量较优城市排名图' : 'AQI 较高城市排名图'"
    />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 100%;
  min-height: 160px;
  flex: 1 1 auto;
}
</style>
