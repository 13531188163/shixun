<script setup>
import { ref } from 'vue'

import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import {
  AXIS_NAME,
  CATEGORY_AXIS,
  CHART_COLORS,
  CHART_GRID,
  DARK_TOOLTIP,
  VALUE_AXIS,
  formatAxisDate,
  numericValue,
  rgba,
} from '../../utils/chartTheme'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)

function formatPrecipitation(value) {
  if (value === null || value === undefined || value === '') return '暂无数据'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric.toFixed(2) : '暂无数据'
}

function buildOption() {
  const rows = props.data || []
  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    grid: { ...CHART_GRID, top: 24, bottom: 34, left: 48, right: 18 },
    tooltip: {
      trigger: 'axis',
      ...DARK_TOOLTIP,
      axisPointer: { type: 'shadow', shadowStyle: { color: rgba(CHART_COLORS.cyan, 0.08) } },
      formatter: (items) => {
        if (!items?.length) return ''
        const item = items[0]
        const value = formatPrecipitation(item.value)
        return `<strong>${item.axisValue || '暂无数据'}</strong><br/>${item.marker}区域日均降水量：${value}${value === '暂无数据' ? '' : ' mm'}`
      },
    },
    xAxis: {
      type: 'category',
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
      name: 'mm',
      nameLocation: 'end',
      nameTextStyle: AXIS_NAME,
      axisLabel: { ...VALUE_AXIS.axisLabel, formatter: (value) => formatPrecipitation(value) },
    },
    series: [
      {
        name: '降水量',
        type: 'bar',
        barMaxWidth: 26,
        data: rows.map((row) => numericValue(row.precip)),
        itemStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: CHART_COLORS.coolLight },
              { offset: 1, color: CHART_COLORS.cool },
            ],
          },
          borderRadius: [3, 3, 0, 0],
        },
        emphasis: { focus: 'series' },
      },
    ],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length" empty-message="暂无降水观测数据">
    <div ref="chartElement" class="echart rainfall-trend-chart" aria-label="近30天降水趋势图" />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 100%;
  min-height: 190px;
  flex: 1 1 auto;
}
</style>
