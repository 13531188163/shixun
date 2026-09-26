<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { aqiStatusColor, formatNumber } from '../../utils/formatters'
import { ref } from 'vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)

function buildOption() {
  const rows = props.data || []
  const ordered = [...rows].reverse()
  return {
    animationDuration: 450,
    grid: { top: 8, right: 28, bottom: 8, left: 62, containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(3, 25, 53, 0.94)',
      borderColor: '#237ead',
      textStyle: { color: '#eef8ff' },
      formatter: (items) => {
        const item = items?.[0]
        const row = ordered[item?.dataIndex]
        return row ? `${row.city}<br/>AQI：${formatNumber(row.aqi)} · ${row.status || '未知'}` : ''
      },
    },
    xAxis: {
      type: 'value',
      min: 0,
      axisLabel: { color: '#6084a6', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(69, 137, 184, 0.16)' } },
    },
    yAxis: {
      type: 'category',
      data: ordered.map((row) => row.city),
      axisLabel: { color: '#8fb7d9', fontSize: 10 },
      axisLine: { lineStyle: { color: '#245478' } },
    },
    series: [{
      type: 'bar',
      barMaxWidth: 14,
      data: ordered.map((row) => ({ value: row.aqi ?? null, itemStyle: { color: aqiStatusColor(row.status), borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: '#8fb7d9', fontSize: 10 },
    }],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div ref="chartElement" class="echart ranking-chart" aria-label="空气质量低到高城市排名图" />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 280px;
}
</style>
