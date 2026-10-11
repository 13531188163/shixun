/**
 * 行政区 GeoJSON 资源加载器。
 *
 * 全国地图使用仓库内经过确认的 china.json；省、市级边界按 adcode 从
 * DataV GeoAtlas 的公开 GeoJSON 接口按需加载。台湾省是明确的数据源适配：
 * DataV 只有 710000 省级轮廓，因此 710000 及其县市/乡镇边界从项目内随
 * 前端发布的官方资料派生 TopoJSON 转换而来。Promise 级缓存可以避免同一
 * 层级在面包屑返回、重复点击时重复发起请求，也不会把地图业务数据混入
 * GeoJSON 资源。
 */

import {
  isTaiwanCountyCode,
  isTaiwanTownCode,
  taiwanTopologyToFeatureCollection,
  TAIWAN_ADCODE,
  TAIWAN_MAP_PATH,
} from './taiwanAdministrative.js'

export const NATIONAL_ADCODE = '100000'
export const ADMIN_MAP_SOURCE = 'https://geo.datav.aliyun.com/areas_v3/bound'

const mapPromiseCache = new Map()
let taiwanTopologyPromise = null
let taiwanTopologyFetch = null

function asAdcode(value) {
  const text = String(value ?? '').trim()
  if (!/^\d{6}$/.test(text)) return ''
  return text
}

function asTaiwanFeatureCode(value) {
  const text = String(value ?? '').trim()
  return isTaiwanCountyCode(text) || isTaiwanTownCode(text) ? text : ''
}

function normalizeMapCode(value) {
  return asAdcode(value) || asTaiwanFeatureCode(value)
}

function validFeature(feature) {
  const properties = feature?.properties || {}
  const adcode = featureAdcode(feature)
  const name = String(properties.name || '').trim()
  return Boolean(adcode && name && feature?.geometry)
}

/**
 * 保留真实边界和行政区元数据，只过滤全国资源中代表南海示意图的空要素。
 */
export function normalizeAdministrativeGeoJson(payload, parentAdcode = NATIONAL_ADCODE) {
  if (!payload || payload.type !== 'FeatureCollection' || !Array.isArray(payload.features)) {
    throw new Error(`行政区地图资源格式无效（${parentAdcode}）`)
  }

  const features = payload.features.filter(validFeature)
  if (!features.length) throw new Error(`行政区地图资源没有可用边界（${parentAdcode}）`)

  return {
    ...payload,
    features,
  }
}

async function fetchGeoJson(url, fetchImpl) {
  const response = await fetchImpl(url)
  if (!response?.ok) throw new Error(`行政区地图资源请求失败（${response?.status || 'network'}）`)
  return response.json()
}

async function loadTaiwanTopology(fetchImpl) {
  if (taiwanTopologyPromise && taiwanTopologyFetch === fetchImpl) return taiwanTopologyPromise
  taiwanTopologyFetch = fetchImpl
  taiwanTopologyPromise = fetchGeoJson(TAIWAN_MAP_PATH, fetchImpl)
  taiwanTopologyPromise.catch(() => {
    if (taiwanTopologyFetch === fetchImpl) {
      taiwanTopologyPromise = null
      taiwanTopologyFetch = null
    }
  })
  return taiwanTopologyPromise
}

/**
 * 按行政区编码加载边界。返回同一个 Promise，避免并发重复请求。
 */
export function loadAdministrativeMap(adcode = NATIONAL_ADCODE, options = {}) {
  const normalizedAdcode = normalizeMapCode(adcode)
  if (!normalizedAdcode) return Promise.reject(new Error('行政区编码无效'))
  if (mapPromiseCache.has(normalizedAdcode)) return mapPromiseCache.get(normalizedAdcode)

  const fetchImpl = options.fetchImpl || globalThis.fetch
  if (typeof fetchImpl !== 'function') return Promise.reject(new Error('当前浏览器不支持地图资源加载'))

  const promise = (async () => {
    if (normalizedAdcode === TAIWAN_ADCODE || isTaiwanCountyCode(normalizedAdcode)) {
      const topology = await loadTaiwanTopology(fetchImpl)
      return normalizeAdministrativeGeoJson(
        taiwanTopologyToFeatureCollection(topology, normalizedAdcode),
        normalizedAdcode,
      )
    }
    if (isTaiwanTownCode(normalizedAdcode)) {
      throw new Error('台湾区县已是末级行政区，没有可加载的下一级边界')
    }
    const url = normalizedAdcode === NATIONAL_ADCODE
      ? '/maps/china.json'
      : `${ADMIN_MAP_SOURCE}/${normalizedAdcode}_full.json`
    const payload = await fetchGeoJson(url, fetchImpl)
    return normalizeAdministrativeGeoJson(payload, normalizedAdcode)
  })()

  mapPromiseCache.set(normalizedAdcode, promise)
  // 请求失败时允许用户重试，而不是永久缓存失败状态。
  promise.catch(() => mapPromiseCache.delete(normalizedAdcode))
  return promise
}

export function clearAdministrativeMapCache() {
  mapPromiseCache.clear()
  taiwanTopologyPromise = null
  taiwanTopologyFetch = null
}

export function featureAdcode(feature) {
  const properties = feature?.properties || {}
  return asAdcode(properties.adcode) || asTaiwanFeatureCode(properties.taiwanCode)
}

export function featureName(feature) {
  return String(feature?.properties?.name || '').trim()
}

/**
 * DataV 元数据同时覆盖 city、district 以及省直辖县级单位。
 * childrenNum 为 0 时即使 level 是 city，也已经是本数据源的末级可选区域。
 */
export function featureLevel(feature) {
  const level = String(feature?.properties?.level || '').trim().toLowerCase()
  if (level === 'province' || level === 'city' || level === 'district') return level
  return Number(feature?.properties?.childrenNum || 0) > 0 ? 'city' : 'district'
}

export function isTerminalFeature(feature) {
  // DataV 的全国资源把台湾省误标为 childrenNum=0；台湾适配器提供了真实
  // 县市边界，因此 710000 必须允许继续下钻。
  if (featureAdcode(feature) === TAIWAN_ADCODE && featureLevel(feature) === 'province') return false
  return Number(feature?.properties?.childrenNum || 0) === 0
    || featureLevel(feature) === 'district'
}

export function featureParentAdcode(feature) {
  return normalizeMapCode(feature?.properties?.parent?.adcode || feature?.properties?.parentAdcode)
}

export function mapSourceUrl(adcode) {
  const normalizedAdcode = normalizeMapCode(adcode)
  if (!normalizedAdcode) return ''
  if (normalizedAdcode === TAIWAN_ADCODE || isTaiwanCountyCode(normalizedAdcode) || isTaiwanTownCode(normalizedAdcode)) return TAIWAN_MAP_PATH
  return normalizedAdcode === NATIONAL_ADCODE
    ? '/maps/china.json'
    : `${ADMIN_MAP_SOURCE}/${normalizedAdcode}_full.json`
}
