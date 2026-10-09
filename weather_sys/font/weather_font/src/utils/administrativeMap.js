/**
 * 行政区 GeoJSON 资源加载器。
 *
 * 全国地图使用仓库内经过确认的 china.json；省、市级边界按 adcode 从
 * DataV GeoAtlas 的公开 GeoJSON 接口按需加载。Promise 级缓存可以避免同一
 * 层级在面包屑返回、重复点击时重复发起请求，也不会把地图业务数据混入
 * GeoJSON 资源。
 */

export const NATIONAL_ADCODE = '100000'
export const ADMIN_MAP_SOURCE = 'https://geo.datav.aliyun.com/areas_v3/bound'

const mapPromiseCache = new Map()

function asAdcode(value) {
  const text = String(value ?? '').trim()
  if (!/^\d{6}$/.test(text)) return ''
  return text
}

function validFeature(feature) {
  const properties = feature?.properties || {}
  const adcode = asAdcode(properties.adcode)
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

/**
 * 按行政区编码加载边界。返回同一个 Promise，避免并发重复请求。
 */
export function loadAdministrativeMap(adcode = NATIONAL_ADCODE, options = {}) {
  const normalizedAdcode = asAdcode(adcode)
  if (!normalizedAdcode) return Promise.reject(new Error('行政区编码无效'))
  if (mapPromiseCache.has(normalizedAdcode)) return mapPromiseCache.get(normalizedAdcode)

  const fetchImpl = options.fetchImpl || globalThis.fetch
  if (typeof fetchImpl !== 'function') return Promise.reject(new Error('当前浏览器不支持地图资源加载'))

  const promise = (async () => {
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
}

export function featureAdcode(feature) {
  return asAdcode(feature?.properties?.adcode)
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
  return Number(feature?.properties?.childrenNum || 0) === 0
    || featureLevel(feature) === 'district'
}

export function featureParentAdcode(feature) {
  return asAdcode(feature?.properties?.parent?.adcode)
}

export function mapSourceUrl(adcode) {
  const normalizedAdcode = asAdcode(adcode)
  if (!normalizedAdcode) return ''
  return normalizedAdcode === NATIONAL_ADCODE
    ? '/maps/china.json'
    : `${ADMIN_MAP_SOURCE}/${normalizedAdcode}_full.json`
}
