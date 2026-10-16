<script setup>
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { aqiStatusColor, formatNumber } from '../../utils/formatters'
import { CHART_COLORS, DARK_TOOLTIP, numericValue, rgba } from '../../utils/chartTheme'
import { computed, ref } from 'vue'

const props = defineProps({
  value: { type: [Number, String], default: null },
  status: { type: String, default: '' },
  distribution: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)
const numericAqi = computed(() => numericValue(props.value))
const hasDistribution = computed(() => (props.distribution || []).some((row) => numericValue(row?.count) !== null))

function buildOption() {
  const aqi = numericAqi.value
  if (aqi !== null) {
    const cap = Math.max(300, aqi)
    const remaining = Math.max(cap - aqi, 0)
    const color = aqiStatusColor(props.status)
    return {
      animationDuration: 620,
      animationEasing: 'cubicOut',
      tooltip: { trigger: 'item', ...DARK_TOOLTIP, formatter: (params) => params.name === '当前 AQI' ? `当前 AQI：${formatNumber(aqi)}${props.status ? ` · ${props.status}` : ''}` : '' },
      title: {
        text: String(aqi), subtext: props.status || 'AQI', left: '50%', top: '34%', textAlign: 'center',
        textStyle: { color: CHART_COLORS.text, fontSize: 29, fontWeight: 700 },
        subtextStyle: { color, fontSize: 11, lineHeight: 20 },
      },
      series: [{
        type: 'pie', radius: ['56%', '76%'], center: ['50%', '50%'], startAngle: 90,
        avoidLabelOverlap: true, label: { show: false }, labelLine: { show: false },
        itemStyle: { borderColor: 'rgba(2, 16, 37, 0.9)', borderWidth: 3, shadowBlur: 13, shadowColor: rgba(color, 0.45) },
        emphasis: { scale: true, scaleSize: 5, itemStyle: { shadowBlur: 22, shadowColor: rgba(color, 0.72) } },
        data: [{ name: '当前 AQI', value: aqi, itemStyle: { color } }, { name: '参考余量', value: remaining, itemStyle: { color: 'rgba(32, 91, 132, 0.32)' } }],
      }],
    }
  }

  const chartData = (props.distribution || [])
    .map((row) => ({ name: row.status || '未知', value: numericValue(row.count) }))
    .filter((row) => row.value !== null)
  return {
    animationDuration: 520,
    tooltip: { trigger: 'item', ...DARK_TOOLTIP, formatter: (params) => `${params.marker}${params.name}：${params.value} 个城市（${params.percent}%）` },
    legend: { bottom: 0, left: 'center', itemWidth: 9, itemHeight: 8, textStyle: { color: CHART_COLORS.textSecondary, fontSize: 10 }, selectedMode: false },
    title: {
      text: String(chartData.reduce((sum, row) => sum + row.value, 0)),
      subtext: '城市样本',
      left: '50%', top: '29%', textAlign: 'center',
      textStyle: { color: CHART_COLORS.text, fontSize: 25, fontWeight: 700 },
      subtextStyle: { color: CHART_COLORS.textMuted, fontSize: 10, lineHeight: 18 },
    },
    series: [{ type: 'pie', radius: ['52%', '74%'], center: ['50%', '45%'], label: { show: false }, labelLine: { show: false }, data: chartData, color: ['#45d9ad', '#f4d36f', '#f39b65', '#e87983', '#b78be8'], itemStyle: { borderColor: 'rgba(2, 16, 37, 0.88)', borderWidth: 2, shadowBlur: 8, shadowColor: rgba(CHART_COLORS.cyan, 0.2) } }],
  }
}

useEChart(chartElement, buildOption, [() => numericAqi.value, () => props.status, () => props.distribution, () => props.loading, () => props.error])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="numericAqi === null && !hasDistribution" empty-message="当前固定快照暂无 AQI 数据">
    <div ref="chartElement" class="echart aqi-chart" data-testid="aqi-chart" aria-label="空气质量 AQI 环形图" />
  </ChartState>
</template>

<style scoped>
.echart { width: 100%; height: 100%; min-height: 145px; flex: 1 1 auto; }
</style>
