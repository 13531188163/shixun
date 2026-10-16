<script setup>
import { ref } from 'vue'
import * as echarts from 'echarts'
import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import { CHART_COLORS, DARK_TOOLTIP } from '../../utils/chartTheme'

const props = defineProps({ data: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const emit = defineEmits(['province-select'])
const element = ref(null); const mapReady = ref(false); const mapError = ref('')
const compact = (v) => String(v || '').replace(/特别行政区|自治区|省|市$/u, '')
const color = (aqi) => { const n = Number(aqi); if (!Number.isFinite(n)) return '#10385f'; if (n <= 50) return '#35d99b'; if (n <= 100) return '#f3d34a'; if (n <= 150) return '#ff9e43'; if (n <= 200) return '#f05d68'; if (n <= 300) return '#b55dde'; return '#7d284e' }
const rowFor = (name) => props.data.find((row) => compact(row.province) === compact(name))
function option() {
  const rows = props.data || []
  return { tooltip: { ...DARK_TOOLTIP, trigger: 'item', formatter: (item) => { const row = rowFor(item.name); return `<strong>${item.name}</strong><br/>有效城市：${row?.cityCount ?? '暂无数据'}<br/>城市样本平均 AQI：${row?.averageAqi ?? '暂无数据'}<br/>状态：${row?.status || '暂无数据'}` } }, visualMap: { min: 0, max: 300, show: true, left: 14, bottom: 16, text: ['高', '低'], textStyle: { color: CHART_COLORS.textSecondary, fontSize: 10 }, inRange: { color: ['#35d99b', '#f3d34a', '#ff9e43', '#f05d68', '#b55dde', '#7d284e'] }, calculable: false }, series: [{ type: 'map', map: 'weatherdemo-air-china', roam: false, selectedMode: false, data: rows.map((row) => ({ name: row.province, value: Number.isFinite(Number(row.averageAqi)) ? Number(row.averageAqi) : null, cityCount: row.cityCount, status: row.status, itemStyle: { areaColor: color(row.averageAqi) } })), itemStyle: { areaColor: '#10385f', borderColor: '#4acaf1', borderWidth: 0.8 }, emphasis: { itemStyle: { areaColor: '#38bde9' }, label: { show: true, color: '#fff' } }, label: { show: true, color: '#b8e8f7', fontSize: 9, formatter: (p) => compact(p.name) } }] }
}
useEChart(element, option, [() => props.data, () => props.loading, () => props.error, () => mapReady.value], { click: (params) => emit('province-select', rowFor(params?.name)?.province || params?.name || '') })
async function loadMap() { try { const response = await fetch('/maps/china.json'); if (!response.ok) throw new Error('地图边界加载失败'); echarts.registerMap('weatherdemo-air-china', await response.json()); mapReady.value = true } catch (reason) { mapError.value = reason?.message || '地图边界加载失败' } }
loadMap()
</script>
<template><ChartState :loading="loading || (!mapReady && !mapError)" :error="error || mapError" :empty="!data.length" empty-message="暂无可匹配的省级空气质量数据"><div ref="element" class="air-map" aria-label="全国空气质量省级地图" /></ChartState></template>
<style scoped>.air-map{width:100%;height:100%;min-height:410px;}</style>
