<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { useEChart } from '../../utils/chart'
import { DARK_TOOLTIP } from '../../utils/chartTheme'
import {
  NATIONAL_ADCODE,
  featureAdcode,
  featureLevel,
  featureName,
  featureParentAdcode,
  isTerminalFeature,
  loadAdministrativeMap,
  mapSourceUrl,
} from '../../utils/administrativeMap'

const props = defineProps({
  location: { type: Object, default: null },
  weather: { type: Object, default: null },
  airQuality: { type: Object, default: null },
  // 保留旧 prop，地图层级现在由自身导航栈管理。
  detailProvince: { type: String, default: '' },
  loading: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['area-select', 'province-select', 'navigation-change', 'map-reset', 'map-error'])

const chartElement = ref(null)
const mapReady = ref(false)
const mapLoading = ref(false)
const mapError = ref('')
const terminalMessage = ref('')
const currentMap = ref(null)
const selectedAdcode = ref('')
const hoveredAdcode = ref('')
const failedMapRequest = ref(null)
const navigation = ref([{ adcode: NATIONAL_ADCODE, name: '全国', level: 'country', parentAdcode: '' }])
let mapRequestVersion = 0
const registeredMapNames = new Set()

const currentNode = computed(() => navigation.value[navigation.value.length - 1])
const currentFeatures = computed(() => currentMap.value?.geoJson?.features || [])
const currentMapName = computed(() => currentMap.value?.mapName || '')
const currentLevel = computed(() => currentNode.value?.level || 'country')
const currentLevelLabel = computed(() => ({
  country: '全国省级边界',
  province: '省级地市边界',
  city: '地级区县边界',
  district: '区县详情',
}[currentLevel.value] || '行政区边界'))

function compactName(value) {
  return String(value || '').replace(/特别行政区|自治区|自治州|地区|盟|省|市$/u, '')
}

function comparableName(value) {
  return String(value || '').trim().replace(/\s+/gu, '')
    .replace(/特别行政区|自治区|自治州|地区|盟|省|市$/u, '')
}

function nodeFromFeature(feature) {
  return {
    adcode: featureAdcode(feature),
    name: featureName(feature),
    level: featureLevel(feature),
    parentAdcode: featureParentAdcode(feature),
    childrenNum: Number(feature?.properties?.childrenNum || 0),
  }
}

function businessFeature() {
  const target = props.location?.district || props.location?.city || props.location?.province
  if (!target) return null
  const exact = currentFeatures.value.find((feature) => featureName(feature) === target)
  if (exact) return exact
  const comparable = comparableName(target)
  return currentFeatures.value.find((feature) => comparableName(featureName(feature)) === comparable) || null
}

const businessSelectedAdcode = computed(() => featureAdcode(businessFeature()))
const effectiveSelectedAdcode = computed(() => selectedAdcode.value || businessSelectedAdcode.value)

function emitNavigation() {
  emit('navigation-change', navigation.value.map((item) => ({
    adcode: item.adcode,
    name: item.name,
    level: item.level,
    parentAdcode: item.parentAdcode || '',
  })))
}

function areaPayload(node, path) {
  const provinceNode = path.find((item) => item.level === 'province')
  const cityNode = [...path].reverse().find((item) => item.level === 'city')
  return {
    adcode: node.adcode,
    name: node.name,
    level: node.level,
    parentAdcode: node.parentAdcode || '',
    province: provinceNode?.name || '',
    city: cityNode?.name || '',
    district: node.level === 'district' ? node.name : '',
    path: path.map((item) => ({ ...item })),
    terminal: node.childrenNum === 0 || node.level === 'district',
  }
}

function emitAreaSelection(node, path) {
  if (node.level === 'province') emit('province-select', node.name)
  emit('area-select', areaPayload(node, path))
}

function registerMap(adcode, geoJson) {
  const mapName = 'weatherdemo-admin-' + adcode
  if (!registeredMapNames.has(mapName)) {
    echarts.registerMap(mapName, geoJson)
    registeredMapNames.add(mapName)
  }
  return mapName
}

async function loadMapAt(node, path, selected = node.adcode) {
  const requestVersion = ++mapRequestVersion
  mapLoading.value = true
  mapError.value = ''
  terminalMessage.value = ''
  try {
    const geoJson = await loadAdministrativeMap(node.adcode)
    if (requestVersion !== mapRequestVersion) return false
    currentMap.value = { adcode: node.adcode, mapName: registerMap(node.adcode, geoJson), geoJson }
    navigation.value = path
    selectedAdcode.value = selected || ''
    failedMapRequest.value = null
    mapReady.value = true
    emitNavigation()
    return true
  } catch (error) {
    if (requestVersion !== mapRequestVersion) return false
    mapError.value = error?.message || ('无法加载' + (node.name || '行政区') + '地图')
    failedMapRequest.value = { node, path, selected }
    emit('map-error', { ...node, message: mapError.value, source: mapSourceUrl(node.adcode) })
    return false
  } finally {
    if (requestVersion === mapRequestVersion) mapLoading.value = false
  }
}

function findFeature(params) {
  const code = String(params?.data?.adcode || '').trim()
  if (code) {
    const byCode = currentFeatures.value.find((feature) => featureAdcode(feature) === code)
    if (byCode) return byCode
  }
  const name = String(params?.name || params?.data?.name || '').trim()
  return currentFeatures.value.find((feature) => featureName(feature) === name) || null
}

function mapNavigationBase() {
  const currentAdcode = currentMap.value?.adcode
  const index = navigation.value.findIndex((item) => item.adcode === currentAdcode)
  return index >= 0 ? navigation.value.slice(0, index + 1) : navigation.value
}

async function handleMapClick(params) {
  const feature = findFeature(params)
  if (!feature) return
  const node = nodeFromFeature(feature)
  if (!node.adcode || !node.name) return
  const path = [...mapNavigationBase(), node]
  selectedAdcode.value = node.adcode
  emitAreaSelection(node, path)
  if (isTerminalFeature(feature)) {
    navigation.value = path
    terminalMessage.value = node.level === 'district'
      ? '已到区县级，左侧天气卡片显示该区县在所选固定日期的真实记录。'
      : '该行政区没有更下一级边界资源，已保留当前行政区作为末级选择。'
    emitNavigation()
    return
  }
  await loadMapAt(node, path)
}

async function navigateTo(index) {
  const target = navigation.value[index]
  if (!target) return
  const path = navigation.value.slice(0, index + 1)
  selectedAdcode.value = target.adcode === NATIONAL_ADCODE ? '' : target.adcode
  terminalMessage.value = ''
  if (target.adcode === NATIONAL_ADCODE) emit('map-reset')
  else emitAreaSelection(target, path)
  if (currentMap.value?.adcode === target.adcode) {
    navigation.value = path
    emitNavigation()
    return
  }
  await loadMapAt(target, path, selectedAdcode.value)
}

async function retryCurrentMap() {
  if (failedMapRequest.value) {
    const failed = failedMapRequest.value
    await loadMapAt(failed.node, failed.path, failed.selected)
    return
  }
  const target = currentMap.value
    ? navigation.value.find((item) => item.adcode === currentMap.value.adcode) || currentNode.value
    : currentNode.value
  const index = navigation.value.findIndex((item) => item.adcode === target.adcode)
  await loadMapAt(target, navigation.value.slice(0, index + 1), selectedAdcode.value)
}

function mapData() {
  const selected = effectiveSelectedAdcode.value
  return currentFeatures.value.map((feature) => {
    const adcode = featureAdcode(feature)
    const selectedArea = adcode && adcode === selected
    const hoveredArea = adcode && adcode === hoveredAdcode.value
    return {
      name: featureName(feature),
      adcode,
      value: selectedArea ? 1 : 0,
      itemStyle: {
        areaColor: selectedArea ? 'rgba(243, 171, 78, 0.74)' : hoveredArea ? 'rgba(35, 177, 227, 0.62)' : 'rgba(8, 67, 105, 0.68)',
        borderColor: selectedArea ? '#ffe0a3' : '#48c9f2',
        borderWidth: selectedArea ? 1.9 : 0.9,
        shadowColor: selectedArea ? '#ffb64f' : hoveredArea ? '#24d9ff' : 'transparent',
        shadowBlur: selectedArea ? 24 : hoveredArea ? 16 : 0,
      },
    }
  })
}

function buildGraphic() {
  const node = currentNode.value
  const recordLabel = props.weather?.recordCount
    ? '天气记录 ' + props.weather.recordCount
    : props.weather?.date
      ? '固定日期 ' + props.weather.date
      : '点击行政区查看真实记录'
  return [
    { type: 'text', left: 18, top: 13, z: 20, style: { text: node?.level === 'country' ? '全国天气与空气质量行政区分布' : node.name + ' · ' + currentLevelLabel.value, fill: '#c5efff', font: '700 13px Microsoft YaHei, sans-serif', textShadowColor: 'rgba(34, 207, 255, 0.45)', textShadowBlur: 8 } },
    { type: 'text', left: 19, top: 34, z: 20, style: { text: currentLevelLabel.value + '  ·  ' + recordLabel, fill: 'rgba(145, 203, 230, 0.72)', font: '10px Microsoft YaHei, sans-serif' } },
    {
      type: 'group', right: 14, top: 14, z: 30,
      children: [
        { type: 'rect', shape: { x: 0, y: 0, width: 138, height: 72, r: 5 }, style: { fill: 'rgba(3, 29, 60, 0.84)', stroke: node?.level === 'district' ? 'rgba(255, 190, 91, 0.72)' : 'rgba(55, 211, 247, 0.62)', lineWidth: 1, shadowColor: 'rgba(26, 195, 255, 0.22)', shadowBlur: 14 } },
        { type: 'text', left: 10, top: 8, style: { text: node?.level === 'country' ? 'NATIONAL SCOPE' : String(node?.level || '').toUpperCase() + ' SCOPE', fill: '#51d6f7', font: '9px Arial, sans-serif' } },
        { type: 'text', left: 10, top: 25, style: { text: node?.name || '全国', fill: '#eefbff', font: '700 15px Microsoft YaHei, sans-serif' } },
        { type: 'text', left: 10, top: 49, style: { text: '编码 ' + (node?.adcode || NATIONAL_ADCODE), fill: 'rgba(170, 217, 237, 0.8)', font: '10px Arial, sans-serif' } },
      ],
    },
    {
      type: 'group', left: 18, bottom: 14, z: 25,
      children: [
        { type: 'circle', shape: { cx: 5, cy: 5, r: 4 }, style: { fill: '#ffbe62', shadowColor: '#ffbe62', shadowBlur: 8 } },
        { type: 'text', left: 14, top: -1, style: { text: '当前选择', fill: '#a4cee4', font: '10px Microsoft YaHei, sans-serif' } },
        { type: 'line', shape: { x1: 78, y1: 5, x2: 112, y2: 5 }, style: { stroke: '#25c8ec', lineWidth: 2, shadowColor: '#25c8ec', shadowBlur: 5 } },
        { type: 'text', left: 122, top: -1, style: { text: '真实边界', fill: '#a4cee4', font: '10px Microsoft YaHei, sans-serif' } },
      ],
    },
    {
      type: 'group', right: 18, bottom: 18, z: 25,
      children: [
        { type: 'line', shape: { x1: 10, y1: 20, x2: 10, y2: 0 }, style: { stroke: '#8de8ff', lineWidth: 1.2 } },
        { type: 'polyline', shape: { points: [[5, 6], [10, 0], [15, 6]] }, style: { stroke: '#8de8ff', lineWidth: 1.2, fill: 'transparent' } },
        { type: 'text', left: 5, top: 23, style: { text: 'N', fill: '#9ed9ef', font: '9px Arial, sans-serif' } },
      ],
    },
  ]
}

function buildOption() {
  const mapName = currentMapName.value
  if (!mapName) return {}
  const level = currentLevel.value
  const data = mapData()
  const zoom = level === 'country' ? 1 : level === 'province' ? 1.04 : 1.08
  return {
    animationDuration: 420,
    animationDurationUpdate: 520,
    animationEasingUpdate: 'cubicOut',
    tooltip: {
      ...DARK_TOOLTIP,
      trigger: 'item',
      formatter: (params) => {
        const feature = findFeature(params)
        const node = feature ? nodeFromFeature(feature) : null
        if (!node) return '<strong>' + (params?.name || '--') + '</strong>'
        const hint = isTerminalFeature(feature) ? '已到末级，点击查看数据' : '点击进入下一级边界'
        return '<strong>' + node.name + '</strong><br/><span style="color:#8edcf4">' + hint + '</span><br/><span style="color:#8caec2">行政区编码：' + node.adcode + '</span>'
      },
    },
    geo: [
      {
        map: mapName, roam: false, silent: false, layoutCenter: ['50%', '52%'],
        layoutSize: level === 'country' ? '138%' : '128%', zoom,
        selectedMode: false,
        itemStyle: { areaColor: 'rgba(8, 48, 82, 0.62)', borderColor: 'rgba(73, 198, 238, 0.74)', borderWidth: 0.8, shadowColor: level === 'country' ? 'rgba(20, 192, 255, 0.48)' : 'rgba(255, 173, 70, 0.28)', shadowBlur: level === 'country' ? 14 : 18 },
        emphasis: { itemStyle: { areaColor: 'rgba(37, 161, 220, 0.62)', borderColor: '#d6f8ff', borderWidth: 1.35 }, label: { show: true, color: '#f4fdff', fontSize: level === 'country' ? 10 : 11, fontWeight: 700 } },
        label: { show: true, color: 'rgba(190, 230, 245, 0.76)', fontSize: level === 'country' ? 8 : 9, formatter: (params) => compactName(params.name) },
      },
      {
        map: 'weatherdemo-admin-' + NATIONAL_ADCODE, roam: false, silent: true,
        left: '78%', top: '68%', width: '19%', height: '23%',
        itemStyle: { areaColor: 'rgba(12, 75, 110, 0.62)', borderColor: 'rgba(58, 194, 235, 0.55)', borderWidth: 0.5 },
        label: { show: false },
      },
    ],
    series: [
      {
        name: '行政区边界', type: 'map', map: mapName, geoIndex: 0, roam: false, silent: false, data,
        label: { show: false }, itemStyle: { areaColor: 'rgba(5, 34, 64, 0.2)', borderColor: 'rgba(76, 202, 245, 0.6)', borderWidth: 0.7 },
        emphasis: { itemStyle: { areaColor: 'rgba(38, 187, 232, 0.52)' } },
      },
      {
        name: '行政区光晕', type: 'map', map: mapName, geoIndex: 0, silent: true,
        data: data.map((item) => ({ name: item.name, adcode: item.adcode, itemStyle: { areaColor: 'rgba(0, 171, 229, 0.08)', borderColor: item.adcode === effectiveSelectedAdcode.value ? 'rgba(255, 193, 95, 0.92)' : 'rgba(40, 222, 255, 0.74)', borderWidth: item.adcode === effectiveSelectedAdcode.value ? 3 : 2, shadowColor: item.adcode === effectiveSelectedAdcode.value ? 'rgba(255, 154, 44, 0.84)' : 'rgba(0, 195, 255, 0.72)', shadowBlur: item.adcode === effectiveSelectedAdcode.value ? 25 : 18 } })),
        label: { show: false },
      },
      {
        name: '全国缩略图', type: 'map', map: 'weatherdemo-admin-' + NATIONAL_ADCODE, geoIndex: 1, silent: true, data: [],
        label: { show: false }, itemStyle: { areaColor: 'rgba(12, 77, 111, 0.62)', borderColor: 'rgba(58, 194, 235, 0.55)', borderWidth: 0.45 },
      },
    ],
    graphic: buildGraphic(),
  }
}

async function initializeMap() {
  const root = navigation.value[0]
  await loadMapAt(root, [root], '')
}

watch(() => props.location?.province, async (province) => {
  if (!province || !currentMap.value) return
  const pathProvince = navigation.value.find((item) => item.level === 'province')
  if (!pathProvince || comparableName(pathProvince.name) === comparableName(province)) return
  const root = navigation.value[0]
  selectedAdcode.value = ''
  terminalMessage.value = ''
  if (currentMap.value.adcode === root.adcode) {
    navigation.value = [root]
    emitNavigation()
    return
  }
  await loadMapAt(root, [root], '')
})

onMounted(initializeMap)
useEChart(chartElement, buildOption, [
  () => mapReady.value, () => currentMapName.value, () => navigation.value,
  () => effectiveSelectedAdcode.value, () => hoveredAdcode.value,
  () => props.weather?.date, () => props.weather?.recordCount, () => props.airQuality?.aqi,
], {
  click: handleMapClick,
  mouseover: (params) => { hoveredAdcode.value = String(params?.data?.adcode || '') },
  mouseout: () => { hoveredAdcode.value = '' },
})
</script>

<template>
  <div class="map-shell">
    <nav class="map-breadcrumb" aria-label="行政区导航路径">
      <span class="breadcrumb-label">行政区</span>
      <template v-for="(item, index) in navigation" :key="item.adcode">
        <span v-if="index" class="breadcrumb-separator" aria-hidden="true">/</span>
        <button type="button" :class="['breadcrumb-item', { active: index === navigation.length - 1 }]" :aria-current="index === navigation.length - 1 ? 'page' : undefined" @click="navigateTo(index)">{{ item.name }}</button>
      </template>
    </nav>
    <div class="map-canvas">
      <div v-if="mapReady" ref="chartElement" class="echart china-map-chart" aria-label="可逐级钻取的全国行政区天气与空气质量地图" />
      <div v-else class="map-loading map-initial-loading">正在加载全国行政区边界…</div>
      <div v-if="mapLoading && mapReady" class="map-loading map-loading-overlay" aria-live="polite">正在切换真实行政区边界…</div>
      <div v-if="mapError" class="map-error" role="alert">
        <span>{{ mapError }}</span>
        <button type="button" @click="retryCurrentMap">重试</button>
      </div>
      <div v-if="terminalMessage && !mapError" class="map-terminal-note">{{ terminalMessage }}</div>
    </div>
    <p class="map-source">边界数据：DataV GeoAtlas · adcode · 按需加载并缓存；天气与空气质量仍来自后端数据库</p>
  </div>
</template>

<style scoped>
.map-shell { display: flex; min-height: 0; height: 100%; flex: 1; flex-direction: column; gap: 6px; }
.map-breadcrumb { display: flex; min-height: 26px; align-items: center; flex-wrap: wrap; gap: 4px; padding: 1px 8px; color: var(--text-muted); font-size: 10px; background: rgb(4 31 64 / 68%); border: 1px solid rgb(45 151 216 / 34%); border-radius: 4px; }
.breadcrumb-label { margin-right: 3px; color: var(--accent-cyan); font-weight: 700; letter-spacing: 0.08em; }
.breadcrumb-separator { color: rgb(127 187 214 / 62%); }
.breadcrumb-item { padding: 2px 4px; color: var(--text-secondary); font: inherit; background: transparent; border: 0; border-radius: 3px; cursor: pointer; }
.breadcrumb-item:hover, .breadcrumb-item:focus-visible { color: var(--text-primary); background: rgb(39 177 223 / 18%); outline: none; }
.breadcrumb-item.active { color: #ffe0a3; font-weight: 700; }
.map-canvas { position: relative; display: flex; min-height: 360px; flex: 1; overflow: hidden; background: radial-gradient(ellipse 66% 62% at 49% 48%, rgb(14 99 151 / 30%), transparent 70%), radial-gradient(circle at 51% 48%, rgb(38 190 225 / 11%), transparent 38%), repeating-linear-gradient(118deg, transparent 0 21px, rgb(61 147 187 / 4%) 22px, transparent 23px 46px), linear-gradient(180deg, #031a35 0%, #021229 58%, #020d20 100%); border-radius: 4px; }
.map-canvas::before { position: absolute; z-index: 0; inset: 0; pointer-events: none; content: ''; opacity: 0.46; background: repeating-linear-gradient(90deg, transparent 0 54px, rgb(82 176 217 / 5%) 55px, transparent 56px 110px), repeating-linear-gradient(0deg, transparent 0 54px, rgb(82 176 217 / 4%) 55px, transparent 56px 110px); mask-image: radial-gradient(ellipse at center, #000 24%, transparent 84%); }
.echart, .china-map-chart { position: relative; z-index: 1; width: 100%; height: 100%; min-height: 360px; flex: 1 1 auto; }
.map-loading, .map-error, .map-terminal-note { position: absolute; z-index: 4; color: var(--text-secondary); font-size: 11px; background: rgb(3 27 57 / 86%); border: 1px solid rgb(56 184 228 / 52%); border-radius: 5px; box-shadow: 0 0 18px rgb(32 201 255 / 16%); }
.map-initial-loading { inset: 0; display: grid; place-items: center; background: rgb(2 17 37 / 75%); border: 0; border-radius: 0; }
.map-loading-overlay { top: 9px; right: 9px; padding: 6px 9px; color: #bcefff; }
.map-error { top: 9px; right: 9px; display: flex; align-items: center; gap: 8px; max-width: min(88%, 420px); padding: 7px 9px; color: #ffd1d5; border-color: rgb(255 125 134 / 58%); }
.map-error button { padding: 3px 7px; color: var(--text-primary); font: inherit; background: rgb(28 79 112 / 82%); border: 1px solid rgb(74 203 241 / 62%); border-radius: 3px; cursor: pointer; }
.map-terminal-note { right: 9px; bottom: 9px; max-width: min(80%, 360px); padding: 6px 9px; color: #ffe0a3; }
.map-source { flex: 0 0 auto; margin: 0; color: rgb(145 203 230 / 58%); font-size: 9px; line-height: 1.3; }
</style>
