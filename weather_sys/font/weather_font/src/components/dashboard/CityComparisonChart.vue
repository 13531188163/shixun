<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { formatNumber } from '../../utils/formatters'
import {
  AXIS_NAME,
  CATEGORY_AXIS,
  CHART_COLORS,
  CHART_GRID,
  DARK_LEGEND,
  DARK_TOOLTIP,
  VALUE_AXIS,
  numericValue,
} from '../../utils/chartTheme'
import { ref } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)

function buildOption() {
  const rows = props.data || []
  const rotateLabels = rows.length > 6 ? 26 : 0
  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { ...CHART_GRID, top: 38, bottom: rotateLabels ? 48 : 34, left: 44 },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      ...DARK_TOOLTIP,
      formatter: (items) => {
        const city = items?.[0]?.axisValue || '--'
        const lines = (items || []).map((item) => `${item.marker}${item.seriesName}：${formatNumber(item.value)}°C`)
        return [`<strong>${city}</strong>`, ...lines].join('<br/>')
      },
    },
    legend: { ...DARK_LEGEND },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.city),
      ...CATEGORY_AXIS,
      axisLabel: {
        ...CATEGORY_AXIS.axisLabel,
        interval: 0,
        rotate: rotateLabels,
        hideOverlap: true,
        width: 64,
        overflow: 'truncate',
        ellipsis: '…',
      },
    },
    yAxis: {
      type: 'value',
      ...VALUE_AXIS,
      name: '°C',
      nameLocation: 'end',
      nameTextStyle: AXIS_NAME,
      axisLabel: { ...VALUE_AXIS.axisLabel, formatter: (value) => `${value}°` },
    },
    series: [
      {
        name: '最高温',
        type: 'bar',
        barMaxWidth: 17,
        barGap: '18%',
        data: rows.map((row) => numericValue(row.maxTemp)),
        itemStyle: { color: CHART_COLORS.warm, borderRadius: [3, 3, 0, 0] },
        emphasis: { focus: 'series', itemStyle: { color: CHART_COLORS.warmLight } },
      },
      {
        name: '最低温',
        type: 'bar',
        barMaxWidth: 17,
        data: rows.map((row) => numericValue(row.minTemp)),
        itemStyle: { color: CHART_COLORS.cool, borderRadius: [3, 3, 0, 0] },
        emphasis: { focus: 'series', itemStyle: { color: CHART_COLORS.coolLight } },
      },
    ],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div ref="chartElement" class="echart comparison-chart" aria-label="城市最高最低温度比较图" />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 100%;
  min-height: 140px;
  flex: 1 1 auto;
}
</style>
