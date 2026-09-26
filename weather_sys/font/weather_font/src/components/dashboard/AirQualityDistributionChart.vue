<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
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
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(3, 25, 53, 0.94)',
      borderColor: '#237ead',
      textStyle: { color: '#eef8ff' },
      formatter: '{b}<br/>城市数：{c}（{d}%）',
    },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 10,
      itemHeight: 8,
      textStyle: { color: '#8fb7d9', fontSize: 10 },
    },
    series: [{
      type: 'pie',
      radius: ['47%', '72%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: true,
      label: { show: false },
      labelLine: { show: false },
      data: rows.map((row) => ({ value: row.count, name: row.status })),
      color: ['#36e0a0', '#f4d35e', '#ff9f43', '#ff6b6b', '#c56cf0', '#ad274d'],
    }],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length">
    <div ref="chartElement" class="echart distribution-chart" aria-label="空气质量等级实际分布图" />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 220px;
}
</style>
