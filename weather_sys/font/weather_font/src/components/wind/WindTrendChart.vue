<script setup>
import { ref } from 'vue'
import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import { AXIS_NAME, CATEGORY_AXIS, CHART_COLORS, CHART_GRID, DARK_LEGEND, DARK_TOOLTIP, VALUE_AXIS, formatAxisDate, numericValue } from '../../utils/chartTheme'

const props = defineProps({ data: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const element = ref(null)
const number = (value) => value === null || value === undefined || !Number.isFinite(Number(value)) ? '暂无数据' : Number(value).toFixed(2)
function option() {
  const rows = props.data || []
  return {
    animationDuration: 500, grid: { ...CHART_GRID, top: 34, bottom: 34, left: 48, right: 18 },
    tooltip: { trigger: 'axis', ...DARK_TOOLTIP, formatter: (items) => `<strong>${items?.[0]?.axisValue || '暂无数据'}</strong><br/>${(items || []).map((item) => `${item.marker}${item.seriesName}：${number(item.value)}${number(item.value) === '暂无数据' ? '' : ' m/s'}`).join('<br/>')}` },
    legend: { ...DARK_LEGEND, data: ['平均风速', '最大风速'] },
    xAxis: { type: 'category', data: rows.map((row) => row.date), ...CATEGORY_AXIS, axisLabel: { ...CATEGORY_AXIS.axisLabel, formatter: formatAxisDate, hideOverlap: true } },
    yAxis: { type: 'value', ...VALUE_AXIS, name: 'm/s', nameTextStyle: AXIS_NAME, axisLabel: { ...VALUE_AXIS.axisLabel, formatter: (value) => number(value) } },
    series: [
      { name: '平均风速', type: 'line', smooth: true, connectNulls: false, data: rows.map((row) => numericValue(row.avgWind)), symbolSize: 6, itemStyle: { color: CHART_COLORS.cyan }, lineStyle: { color: CHART_COLORS.cyan, width: 2 } },
      { name: '最大风速', type: 'line', smooth: true, connectNulls: false, data: rows.map((row) => numericValue(row.maxWind)), symbolSize: 6, itemStyle: { color: '#ffad45' }, lineStyle: { color: '#ffad45', width: 2 } },
    ],
  }
}
useEChart(element, option, [() => props.data, () => props.loading, () => props.error])
</script>
<template><ChartState :loading="loading" :error="error" :empty="!data.length" empty-message="暂无风速观测数据"><div ref="element" class="echart" aria-label="近30天风速变化趋势图" /></ChartState></template>
<style scoped>.echart { width: 100%; height: 100%; min-height: 235px; }</style>
