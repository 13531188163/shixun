<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { formatNumber } from '../../utils/formatters'
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
    animationDuration: 450,
    grid: { top: 28, right: 14, bottom: 28, left: 34, containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(3, 25, 53, 0.94)',
      borderColor: '#237ead',
      textStyle: { color: '#eef8ff' },
      formatter: (items) => {
        const date = items?.[0]?.axisValue || '--'
        const lines = items.map((item) => `${item.marker}${item.seriesName}：${formatNumber(item.value)}°C`)
        return [date, ...lines].join('<br/>')
      },
    },
    legend: { top: 0, right: 0, textStyle: { color: '#8fb7d9', fontSize: 11 } },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: rows.map((row) => row.date),
      axisLabel: { color: '#6084a6', fontSize: 10 },
      axisLine: { lineStyle: { color: '#245478' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6084a6', fontSize: 10, formatter: '{value}°' },
      splitLine: { lineStyle: { color: 'rgba(69, 137, 184, 0.16)' } },
    },
    series: [
      {
        name: '最高温',
        type: 'line',
        smooth: true,
        connectNulls: false,
        symbol: 'circle',
        symbolSize: 5,
        data: rows.map((row) => row.maxTemp ?? null),
        lineStyle: { width: 2, color: '#3ee5ff' },
        itemStyle: { color: '#3ee5ff' },
        areaStyle: { color: 'rgba(62, 229, 255, 0.08)' },
      },
      {
        name: '最低温',
        type: 'line',
        smooth: true,
        connectNulls: false,
        symbol: 'circle',
        symbolSize: 5,
        data: rows.map((row) => row.minTemp ?? null),
        lineStyle: { width: 2, color: '#438cff' },
        itemStyle: { color: '#438cff' },
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
  height: 226px;
}
</style>
