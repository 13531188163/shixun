<script setup>
import { ref } from 'vue'

import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import {
  AXIS_NAME,
  CATEGORY_AXIS,
  CHART_COLORS,
  CHART_GRID,
  DARK_LEGEND,
  DARK_TOOLTIP,
  VALUE_AXIS,
  numericValue,
  rgba,
  temperatureArea,
} from '../../utils/chartTheme'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)

function buildOption() {
  const rows = props.data || []
  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { ...CHART_GRID, top: 34, bottom: 34, left: 44 },
    tooltip: {
      trigger: 'axis',
      ...DARK_TOOLTIP,
      axisPointer: { type: 'line', lineStyle: { color: rgba(CHART_COLORS.cyan, 0.45), width: 1 } },
      formatter: (items) => {
        if (!items?.length) return ''
        const lines = items.map((item) => `${item.marker}${item.seriesName}：${item.value ?? '--'}°C`)
        return [`<strong>${items[0]?.axisValue || '--'}</strong>`, ...lines].join('<br/>')
      },
    },
    legend: { ...DARK_LEGEND, data: ['月度平均温度'] },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: rows.map((row) => row.month),
      ...CATEGORY_AXIS,
      axisLabel: { ...CATEGORY_AXIS.axisLabel, interval: 0, hideOverlap: true },
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
        name: '月度平均温度',
        type: 'line',
        smooth: true,
        connectNulls: false,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 6,
        data: rows.map((row) => numericValue(row.avgTemp)),
        lineStyle: { width: 2.4, color: CHART_COLORS.warm },
        itemStyle: { color: CHART_COLORS.warmLight, borderColor: CHART_COLORS.warm, borderWidth: 1 },
        areaStyle: temperatureArea(CHART_COLORS.warm, 0.12),
        emphasis: { focus: 'series', scale: true },
      },
    ],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div ref="chartElement" class="echart monthly-chart" aria-label="月度平均温度趋势图" />
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
