<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import {
  CHART_COLORS,
  DARK_TOOLTIP,
  numericValue,
  rgba,
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
  const chartData = rows
    .map((row) => ({ name: row.status || '未知', value: numericValue(row.count) }))
    .filter((row) => row.value !== null)
  const total = chartData.reduce((sum, row) => sum + row.value, 0)
  const statusColors = ['#45d9ad', '#f4d36f', '#f39b65', '#e87983', '#b78be8', '#7c8edb']
  return {
    animationDuration: 560,
    animationEasing: 'cubicOut',
    tooltip: {
      trigger: 'item',
      ...DARK_TOOLTIP,
      formatter: (params) => `${params.marker}<strong>${params.name}</strong><br/>城市数：${params.value}（${params.percent}%）`,
    },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 10,
      itemHeight: 8,
      itemGap: 12,
      textStyle: { color: CHART_COLORS.textSecondary, fontSize: 10 },
      selectedMode: false,
    },
    title: {
      text: String(total),
      subtext: '城市样本',
      left: '50%',
      top: '30%',
      textAlign: 'center',
      textStyle: { color: CHART_COLORS.text, fontSize: 24, fontWeight: 700 },
      subtextStyle: { color: CHART_COLORS.textMuted, fontSize: 10, lineHeight: 18 },
    },
    series: [{
      type: 'pie',
      radius: ['48%', '72%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      label: { show: false },
      labelLine: { show: false },
      padAngle: 1.5,
      itemStyle: {
        borderColor: 'rgba(2, 16, 37, 0.88)',
        borderWidth: 2,
        shadowBlur: 8,
        shadowColor: rgba(CHART_COLORS.cyan, 0.12),
      },
      emphasis: {
        scale: true,
        scaleSize: 4,
        itemStyle: { shadowBlur: 16, shadowColor: rgba(CHART_COLORS.cyan, 0.28) },
      },
      data: chartData,
      color: statusColors,
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
  height: 100%;
  min-height: 140px;
  flex: 1 1 auto;
}
</style>
