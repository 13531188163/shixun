<script setup>
import { computed, ref } from 'vue'
import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import { CHART_COLORS, DARK_LEGEND, DARK_TOOLTIP } from '../../utils/chartTheme'
const props = defineProps({ data: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const element = ref(null)
const total = computed(() => (props.data || []).reduce((sum, row) => sum + Number(row.count || 0), 0))
const colors = ['#57d6ff', '#43df9c', '#f6c344', '#ff9b3e', '#ff5f72', '#9d56f2', '#7d4bd8', '#7c5ccf', '#7763c3', '#ef5e73']
function option() { const rows = props.data || []; return { tooltip: { trigger: 'item', ...DARK_TOOLTIP, formatter: (item) => `${item.marker}${item.name}<br/>天数：${item.value}（${item.percent}%）` }, legend: { ...DARK_LEGEND, orient: 'vertical', left: '52%', top: 'middle', data: rows.map((row) => row.name), formatter: (name) => { const row = rows.find((item) => item.name === name); return `{name|${name}} {count|${row?.count || 0}天} {percent|${row?.percentage || 0}%}` }, textStyle: { ...DARK_LEGEND.textStyle, rich: { name: { width: 56, color: CHART_COLORS.textSecondary }, count: { width: 38, color: CHART_COLORS.text }, percent: { width: 42, color: CHART_COLORS.text } } } }, graphic: [{ type: 'text', left: '25%', top: '42%', style: { text: `${total.value}天`, fill: CHART_COLORS.text, fontSize: 24, fontWeight: 700, textAlign: 'center' } }, { type: 'text', left: '25%', top: '57%', style: { text: '有效观测天数', fill: CHART_COLORS.textMuted, fontSize: 10, textAlign: 'center' } }], series: [{ type: 'pie', radius: ['45%', '70%'], center: ['25%', '51%'], label: { show: false }, data: rows.map((row, index) => ({ name: row.name, value: Number(row.count || 0), itemStyle: { color: colors[index % colors.length] } })) }] } }
useEChart(element, option, [() => props.data, () => props.loading, () => props.error, total])
</script>
<template><ChartState :loading="loading" :error="error" :empty="!data.length || total === 0" empty-message="暂无风力等级数据"><div ref="element" class="echart" aria-label="风力等级分布环形图" /></ChartState></template>
<style scoped>.echart { width: 100%; height: 100%; min-height: 235px; }</style>
