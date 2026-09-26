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
  formatAxisDate,
  numericValue,
  rgba,
  temperatureArea,
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
        const date = items[0]?.axisValue || '--'
        const lines = items.map((item) => `${item.marker}${item.seriesName}：${formatNumber(item.value)}°C`)
        return [`<strong>${date}</strong>`, ...lines].join('<br/>')
      },
    },
    legend: { ...DARK_LEGEND },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: rows.map((row) => row.date),
      ...CATEGORY_AXIS,
      axisLabel: {
        ...CATEGORY_AXIS.axisLabel,
        formatter: formatAxisDate,
        interval: rows.length > 10 ? 'auto' : 0,
        hideOverlap: true,
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
        type: 'line',
        smooth: true,
        connectNulls: false,
        showSymbol: rows.length <= 10,
        symbol: 'circle',
        symbolSize: 5,
        data: rows.map((row) => numericValue(row.maxTemp)),
        lineStyle: { width: 2.4, color: CHART_COLORS.warm },
        itemStyle: { color: CHART_COLORS.warmLight, borderColor: CHART_COLORS.warm, borderWidth: 1 },
        areaStyle: temperatureArea(CHART_COLORS.warm, 0.12),
        emphasis: { focus: 'series', scale: true },
      },
      {
        name: '最低温',
        type: 'line',
        smooth: true,
        connectNulls: false,
        showSymbol: rows.length <= 10,
        symbol: 'circle',
        symbolSize: 5,
        data: rows.map((row) => numericValue(row.minTemp)),
        lineStyle: { width: 2.4, color: CHART_COLORS.cool },
        itemStyle: { color: CHART_COLORS.coolLight, borderColor: CHART_COLORS.cool, borderWidth: 1 },
        areaStyle: temperatureArea(CHART_COLORS.cool, 0.06),
        emphasis: { focus: 'series', scale: true },
      },
    ],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div ref="chartElement" class="echart trend-chart" aria-label="历史天气最高最低温度趋势图" />
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
