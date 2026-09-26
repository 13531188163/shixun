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
    grid: { top: 38, right: 12, bottom: 30, left: 34, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(3, 25, 53, 0.94)',
      borderColor: '#237ead',
      textStyle: { color: '#eef8ff' },
      valueFormatter: (value) => `${formatNumber(value)}°C`,
    },
    legend: { top: 0, right: 0, textStyle: { color: '#8fb7d9', fontSize: 11 } },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.city),
      axisLabel: { color: '#8fb7d9', fontSize: 10, interval: 0, rotate: rows.length > 6 ? 24 : 0 },
      axisLine: { lineStyle: { color: '#245478' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#6084a6', fontSize: 10, formatter: '{value}°' },
      splitLine: { lineStyle: { color: 'rgba(69, 137, 184, 0.16)' } },
    },
    series: [
      { name: '最高温', type: 'bar', barMaxWidth: 18, data: rows.map((row) => row.maxTemp ?? null), itemStyle: { color: '#3ee5ff', borderRadius: [3, 3, 0, 0] } },
      { name: '最低温', type: 'bar', barMaxWidth: 18, data: rows.map((row) => row.minTemp ?? null), itemStyle: { color: '#438cff', borderRadius: [3, 3, 0, 0] } },
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
  height: 226px;
}
</style>
