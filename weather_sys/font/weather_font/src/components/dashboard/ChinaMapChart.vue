<script setup>
import { computed, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import ChartState from './ChartState.vue'
import { useEChart } from '../../utils/chart'
import { CHART_COLORS, DARK_TOOLTIP } from '../../utils/chartTheme'

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

function provinceNameForMap(province) {
  if (!province || !mapFeatures.value.length) return ''
  const names = mapFeatures.value
  return names.find((name) => name === province)
    || names.find((name) => name.startsWith(province) || province.startsWith(name.replace(/省|市|自治区|特别行政区$/u, '')))
    || ''
}

const selectedProvince = computed(() => provinceNameForMap(props.location?.province))
const detailProvince = computed(() => provinceNameForMap(props.detailProvince))

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

function buildOption() {
  const selected = selectedProvince.value
  const detail = detailProvince.value
  const view = detailView.value
  const mapData = mapFeatures.value.map((name) => ({
    name,
    value: name === selected ? 1 : 0,
    itemStyle: name === selected
      ? { areaColor: 'rgba(39, 190, 239, 0.68)', borderColor: '#b8f4ff', borderWidth: 1.35 }
      : undefined,
  }))

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
    geo: {
      map: MAP_NAME,
      roam: false,
      silent: false,
      layoutCenter: ['50%', detail ? '50%' : '49%'],
      layoutSize: detail ? '118%' : '110%',
      ...(view ? { center: view.center, zoom: view.zoom } : {}),
      selectedMode: false,
      itemStyle: {
        areaColor: 'rgba(12, 69, 116, 0.66)',
        borderColor: 'rgba(76, 202, 245, 0.78)',
        borderWidth: 0.8,
        shadowColor: 'rgba(26, 203, 255, 0.42)',
        shadowBlur: 8,
      },
      emphasis: {
        itemStyle: {
          areaColor: 'rgba(37, 161, 220, 0.58)',
          borderColor: '#d6f8ff',
          borderWidth: 1.2,
        },
        label: { show: true, color: '#f0fbff', fontSize: 10, fontWeight: 600 },
      },
      label: {
        show: true,
        color: 'rgba(186, 226, 245, 0.68)',
        fontSize: 9,
        formatter: (params) => {
          if (detail && params.name !== detail) return ''
          return params.name.replace(/省|市|自治区|特别行政区$/u, '')
        },
      },
      regions: selected ? [{
        name: selected,
        itemStyle: {
          areaColor: 'rgba(39, 190, 239, 0.68)',
          borderColor: '#c4f7ff',
          borderWidth: 1.5,
          shadowColor: 'rgba(44, 222, 255, 0.85)',
          shadowBlur: 22,
        },
        label: { color: '#ffffff', fontWeight: 700 },
      }] : [],
    },
    series: [{
      name: '行政区边界',
      type: 'map',
      map: MAP_NAME,
      geoIndex: 0,
      roam: false,
      silent: false,
      ...(view ? { center: view.center, zoom: view.zoom } : {}),
      data: mapData,
      label: { show: false },
      itemStyle: { areaColor: 'transparent', borderColor: 'transparent' },
      emphasis: { itemStyle: { areaColor: 'transparent' } },
    }],
    graphic: [
      {
        type: 'text',
        left: 18,
        top: 15,
        style: {
          text: detail ? `${detail}省级详细视图` : '全国行政区数据视图',
          fill: '#9ed9f2',
          font: '600 12px Microsoft YaHei, sans-serif',
        },
      },
      {
        type: 'text',
        right: 16,
        bottom: 15,
        style: {
          text: detail ? '省份已放大 · 可返回全国' : (selected ? `当前高亮：${selected}` : '当前省份待选择'),
          fill: CHART_COLORS.cyan,
          font: '11px Microsoft YaHei, sans-serif',
          textAlign: 'right',
        },
      },
    ],
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
  () => props.weather?.weather,
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
  width: 100%;
  height: 100%;
  min-height: 310px;
  flex: 1 1 auto;
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
