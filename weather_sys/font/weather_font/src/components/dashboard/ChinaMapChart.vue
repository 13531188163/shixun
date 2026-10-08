<script setup>
import { computed, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { DARK_TOOLTIP } from '../../utils/chartTheme'

const MAP_NAME = 'weatherdemo-china'

const props = defineProps({
  location: { type: Object, default: null },
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  detailProvince: { type: String, default: '' },
  loading: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['province-select'])

const chartElement = ref(null)
const mapReady = ref(false)
const mapError = ref('')
const mapFeatures = ref([])
const mapGeoJson = ref(null)

function stripAdministrativeSuffix(value) {
  return String(value || '').replace(/省|市|自治区|特别行政区$/u, '')
}

function provinceNameForMap(province) {
  if (!province || !mapFeatures.value.length) return ''
  const names = mapFeatures.value
  return names.find((name) => name === province)
    || names.find((name) => name.startsWith(province) || province.startsWith(name.replace(/省|市|自治区|特别行政区$/u, '')))
    || ''
}

const selectedProvince = computed(() => provinceNameForMap(props.location?.province))
const detailProvince = computed(() => provinceNameForMap(props.detailProvince))
const displayProvince = computed(() => stripAdministrativeSuffix(detailProvince.value || selectedProvince.value))

function collectPoints(value, points = []) {
  if (!Array.isArray(value)) return points
  if (typeof value[0] === 'number' && typeof value[1] === 'number') {
    points.push(value)
    return points
  }
  value.forEach((item) => collectPoints(item, points))
  return points
}

function provinceView(name) {
  if (!name || !mapGeoJson.value) return null
  const feature = mapGeoJson.value.features?.find((item) => item?.properties?.name === name)
  const points = collectPoints(feature?.geometry?.coordinates)
  if (!points.length) return null
  const longitudes = points.map((point) => point[0])
  const latitudes = points.map((point) => point[1])
  const minLongitude = Math.min(...longitudes)
  const maxLongitude = Math.max(...longitudes)
  const minLatitude = Math.min(...latitudes)
  const maxLatitude = Math.max(...latitudes)
  const span = Math.max(maxLongitude - minLongitude, maxLatitude - minLatitude)
  return {
    center: [(minLongitude + maxLongitude) / 2, (minLatitude + maxLatitude) / 2],
    zoom: Math.min(7, Math.max(1.7, 38 / Math.max(span, 1))),
  }
}

const detailView = computed(() => provinceView(detailProvince.value))

function provinceData(selected, detail) {
  return mapFeatures.value.map((name) => {
    const isSelected = name === selected
    const isDetail = name === detail
    const dimmed = Boolean(detail && !isDetail)
    return {
      name,
      value: isSelected ? 1 : 0,
      itemStyle: {
        areaColor: isDetail
          ? 'rgba(243, 171, 78, 0.72)'
          : isSelected
            ? 'rgba(30, 195, 239, 0.68)'
            : dimmed
              ? 'rgba(7, 42, 72, 0.34)'
              : 'rgba(10, 67, 105, 0.66)',
        borderColor: isDetail
          ? '#ffe0a3'
          : isSelected
            ? '#bff6ff'
            : dimmed
              ? 'rgba(59, 147, 184, 0.28)'
              : 'rgba(72, 197, 235, 0.72)',
        borderWidth: isDetail ? 1.8 : isSelected ? 1.45 : 0.8,
        shadowColor: isDetail ? '#ffbd5d' : isSelected ? '#21d7ff' : 'transparent',
        shadowBlur: isDetail ? 26 : isSelected ? 20 : 0,
      },
    }
  })
}

function buildGraphic(selected, detail) {
  const scopeLabel = detail ? `${displayProvince.value} · 省级范围` : '全国 · 省级选择'
  const recordLabel = props.weather?.recordCount
    ? `记录 ${props.weather.recordCount}`
    : '点击省份查看汇总'
  const dateLabel = props.weather?.date || '固定观测日期'
  return [
    {
      type: 'text',
      left: 18,
      top: 14,
      z: 20,
      style: {
        text: detail ? `${displayProvince.value} · 省级天气与空气质量视图` : '全国天气与空气质量分布',
        fill: '#c5efff',
        font: '700 13px Microsoft YaHei, sans-serif',
        textShadowColor: 'rgba(34, 207, 255, 0.45)',
        textShadowBlur: 8,
      },
    },
    {
      type: 'text',
      left: 19,
      top: 34,
      z: 20,
      style: {
        text: `${scopeLabel}  ·  ${dateLabel}`,
        fill: 'rgba(145, 203, 230, 0.72)',
        font: '10px Microsoft YaHei, sans-serif',
      },
    },
    {
      type: 'group',
      right: 14,
      top: 14,
      z: 30,
      children: [
        {
          type: 'rect',
          shape: { x: 0, y: 0, width: 126, height: 72, r: 5 },
          style: {
            fill: 'rgba(3, 29, 60, 0.82)',
            stroke: detail ? 'rgba(255, 190, 91, 0.72)' : 'rgba(55, 211, 247, 0.62)',
            lineWidth: 1,
            shadowColor: detail ? 'rgba(255, 170, 65, 0.28)' : 'rgba(26, 195, 255, 0.22)',
            shadowBlur: 14,
          },
        },
        { type: 'text', left: 10, top: 8, style: { text: detail ? 'PROVINCE SCOPE' : 'NATIONAL SCOPE', fill: '#51d6f7', font: '9px Arial, sans-serif' } },
        { type: 'text', left: 10, top: 25, style: { text: displayProvince.value || '全国', fill: '#eefbff', font: '700 15px Microsoft YaHei, sans-serif' } },
        { type: 'text', left: 10, top: 49, style: { text: recordLabel, fill: 'rgba(170, 217, 237, 0.8)', font: '10px Microsoft YaHei, sans-serif' } },
      ],
    },
    {
      type: 'group',
      left: 18,
      bottom: 14,
      z: 25,
      children: [
        { type: 'circle', shape: { cx: 5, cy: 5, r: 4 }, style: { fill: detail ? '#ffbe62' : '#41d8f5', shadowColor: detail ? '#ffbe62' : '#41d8f5', shadowBlur: 8 } },
        { type: 'text', left: 14, top: -1, style: { text: detail ? '当前省级范围' : '省级边界', fill: '#a4cee4', font: '10px Microsoft YaHei, sans-serif' } },
        { type: 'line', shape: { x1: 95, y1: 5, x2: 129, y2: 5 }, style: { stroke: '#25c8ec', lineWidth: 2, shadowColor: '#25c8ec', shadowBlur: 5 } },
        { type: 'text', left: 139, top: -1, style: { text: '行政区边界', fill: '#a4cee4', font: '10px Microsoft YaHei, sans-serif' } },
      ],
    },
    {
      type: 'group',
      right: 18,
      bottom: 18,
      z: 25,
      children: [
        { type: 'line', shape: { x1: 10, y1: 20, x2: 10, y2: 0 }, style: { stroke: '#8de8ff', lineWidth: 1.2 } },
        { type: 'polyline', shape: { points: [[5, 6], [10, 0], [15, 6]] }, style: { stroke: '#8de8ff', lineWidth: 1.2, fill: 'transparent' } },
        { type: 'text', left: 5, top: 23, style: { text: 'N', fill: '#9ed9ef', font: '9px Arial, sans-serif' } },
      ],
    },
    {
      type: 'group',
      right: 14,
      bottom: 82,
      z: 25,
      children: [
        { type: 'rect', shape: { x: 0, y: 0, width: 104, height: 68, r: 2 }, style: { fill: 'rgba(2, 29, 57, 0.86)', stroke: 'rgba(51, 199, 239, 0.72)', lineWidth: 1 } },
        { type: 'text', left: 8, top: 6, style: { text: '南海诸岛', fill: '#9bd9ef', font: '9px Microsoft YaHei, sans-serif' } },
        { type: 'line', shape: { x1: 12, y1: 29, x2: 84, y2: 29 }, style: { stroke: 'rgba(46, 177, 224, 0.44)', lineWidth: 1 } },
        { type: 'line', shape: { x1: 18, y1: 43, x2: 66, y2: 48 }, style: { stroke: 'rgba(46, 177, 224, 0.35)', lineWidth: 1 } },
        { type: 'text', left: 8, top: 51, style: { text: '行政区示意', fill: 'rgba(151, 203, 224, 0.72)', font: '9px Microsoft YaHei, sans-serif' } },
      ],
    },
  ]
}

function buildOption() {
  const selected = selectedProvince.value
  const detail = detailProvince.value
  const view = detailView.value
  const mapData = provinceData(selected, detail)
  const dimmed = Boolean(detail)

  return {
    animationDuration: 520,
    animationEasing: 'cubicOut',
    tooltip: {
      ...DARK_TOOLTIP,
      trigger: 'item',
      formatter: (params) => {
        const marker = params.name === selected ? '<br/><span style="color:#45d9ad">当前选择省份</span>' : ''
        return `<strong>${params.name || '--'}</strong>${marker}`
      },
    },
    geo: [{
      map: MAP_NAME,
      roam: false,
      silent: false,
      layoutCenter: ['50%', detail ? '50%' : '49%'],
      layoutSize: detail ? '122%' : '112%',
      ...(view ? { center: view.center, zoom: view.zoom } : {}),
      selectedMode: false,
      itemStyle: {
        areaColor: 'rgba(8, 48, 82, 0.62)',
        borderColor: 'rgba(73, 198, 238, 0.65)',
        borderWidth: 0.8,
        shadowColor: detail ? 'rgba(255, 173, 70, 0.36)' : 'rgba(20, 192, 255, 0.42)',
        shadowBlur: detail ? 18 : 14,
      },
      emphasis: {
        itemStyle: {
          areaColor: 'rgba(37, 161, 220, 0.58)',
          borderColor: '#d6f8ff',
          borderWidth: 1.2,
        },
        label: { show: true, color: '#f4fdff', fontSize: 11, fontWeight: 700 },
      },
      label: {
        show: true,
        color: dimmed ? 'rgba(155, 195, 215, 0.32)' : 'rgba(190, 230, 245, 0.72)',
        fontSize: detail ? 9 : 8,
        formatter: (params) => {
          if (detail && params.name !== detail) return ''
          return stripAdministrativeSuffix(params.name)
        },
      },
      regions: selected ? [{
        name: selected,
        itemStyle: {
          areaColor: detail ? 'rgba(243, 171, 78, 0.72)' : 'rgba(39, 190, 239, 0.68)',
          borderColor: detail ? '#ffe0a3' : '#c4f7ff',
          borderWidth: detail ? 1.8 : 1.5,
          shadowColor: detail ? 'rgba(255, 154, 44, 0.9)' : 'rgba(44, 222, 255, 0.85)',
          shadowBlur: 22,
        },
        label: { color: '#ffffff', fontWeight: 700 },
      }] : [],
    }, {
      map: MAP_NAME,
      roam: false,
      silent: true,
      left: '77%',
      top: '67%',
      width: '20%',
      height: '24%',
      itemStyle: {
        areaColor: 'rgba(12, 75, 110, 0.62)',
        borderColor: 'rgba(58, 194, 235, 0.55)',
        borderWidth: 0.5,
      },
      label: { show: false },
    }],
    series: [{
      name: '行政区光晕',
      type: 'map',
      map: MAP_NAME,
      geoIndex: 0,
      silent: true,
      data: mapData,
      itemStyle: {
        areaColor: 'rgba(0, 171, 229, 0.12)',
        borderColor: detail ? 'rgba(255, 193, 95, 0.82)' : 'rgba(40, 222, 255, 0.8)',
        borderWidth: detail ? 3 : 2.4,
        shadowColor: detail ? 'rgba(255, 154, 44, 0.82)' : 'rgba(0, 195, 255, 0.76)',
        shadowBlur: detail ? 26 : 22,
      },
      label: { show: false },
    }, {
      name: '省级范围',
      type: 'map',
      map: MAP_NAME,
      geoIndex: 0,
      roam: false,
      silent: false,
      ...(view ? { center: view.center, zoom: view.zoom } : {}),
      data: mapData,
      label: { show: false },
      itemStyle: { areaColor: 'rgba(5, 34, 64, 0.18)', borderColor: 'rgba(76, 202, 245, 0.56)', borderWidth: 0.75 },
      emphasis: { itemStyle: { areaColor: 'rgba(38, 187, 232, 0.52)' } },
    },
      {
        name: '全国缩略图',
        type: 'map',
        map: MAP_NAME,
        geoIndex: 1,
        silent: true,
        data: mapData,
        label: { show: false },
        itemStyle: { areaColor: 'rgba(12, 77, 111, 0.62)', borderColor: 'rgba(58, 194, 235, 0.55)', borderWidth: 0.45 },
      }],
    graphic: buildGraphic(selected, detail),
  }
}

async function loadMap() {
  try {
    const response = await fetch('/maps/china.json')
    if (!response.ok) throw new Error(`地图资源请求失败（${response.status}）`)
    const geoJson = await response.json()
    if (!geoJson?.features?.length) throw new Error('地图资源为空')
    echarts.registerMap(MAP_NAME, geoJson)
    mapGeoJson.value = geoJson
    mapFeatures.value = geoJson.features
      .map((feature) => feature?.properties?.name)
      .filter(Boolean)
    mapReady.value = true
  } catch (error) {
    mapError.value = error?.message || '全国地图加载失败'
  }
}

function handleMapClick(params) {
  if (params?.name) emit('province-select', params.name)
}

onMounted(loadMap)
useEChart(chartElement, buildOption, [
  () => mapReady.value,
  () => selectedProvince.value,
  () => detailProvince.value,
  () => props.weather?.date,
  () => props.weather?.recordCount,
  () => props.airQuality?.aqi,
  () => props.loading,
  () => props.error,
], { click: handleMapClick })
</script>

<template>
  <ChartState :loading="loading" :error="error || mapError" :empty="!mapReady && !mapError">
    <div v-if="mapError" class="map-error">全国地图暂时不可用</div>
    <div v-else ref="chartElement" class="echart china-map-chart" aria-label="全国行政区天气与空气质量地图" />
  </ChartState>
</template>

<style scoped>
.echart,
.china-map-chart {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 310px;
  flex: 1 1 auto;
  overflow: hidden;
  background:
    radial-gradient(ellipse 66% 62% at 49% 48%, rgb(14 99 151 / 30%), transparent 70%),
    radial-gradient(circle at 51% 48%, rgb(38 190 225 / 11%), transparent 38%),
    repeating-linear-gradient(118deg, transparent 0 21px, rgb(61 147 187 / 4%) 22px, transparent 23px 46px),
    linear-gradient(180deg, #031a35 0%, #021229 58%, #020d20 100%);
}

.china-map-chart::before {
  position: absolute;
  z-index: 0;
  inset: 0;
  pointer-events: none;
  content: '';
  opacity: 0.46;
  background:
    repeating-linear-gradient(90deg, transparent 0 54px, rgb(82 176 217 / 5%) 55px, transparent 56px 110px),
    repeating-linear-gradient(0deg, transparent 0 54px, rgb(82 176 217 / 4%) 55px, transparent 56px 110px);
  mask-image: radial-gradient(ellipse at center, #000 24%, transparent 84%);
}

.china-map-chart::after {
  position: absolute;
  z-index: 0;
  right: 18%;
  bottom: 9%;
  left: 18%;
  height: 22%;
  pointer-events: none;
  content: '';
  background: linear-gradient(180deg, transparent, rgb(27 166 216 / 13%), transparent);
  filter: blur(16px);
}

.map-error {
  display: grid;
  min-height: 240px;
  flex: 1;
  place-items: center;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
