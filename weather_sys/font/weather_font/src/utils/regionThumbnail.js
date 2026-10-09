/**
 * 将真实行政区 GeoJSON 几何转换为轻量 SVG path。
 *
 * 缩略图不创建 ECharts 实例，且只缓存几何计算结果；数据仍来自
 * administrativeMap 的真实 GeoJSON 资源，不在这里补造行政区轮廓。
 */

const thumbnailCache = new Map()

function normalizeNumber(value) {
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function geometryRings(feature) {
  const geometry = feature?.geometry || feature
  if (!geometry || !geometry.type || !Array.isArray(geometry.coordinates)) return []

  if (geometry.type === 'Polygon') return geometry.coordinates
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flat()
  return []
}

function validRing(ring) {
  return Array.isArray(ring)
    ? ring.map((point) => [normalizeNumber(point?.[0]), normalizeNumber(point?.[1])])
      .filter(([x, y]) => x !== null && y !== null)
    : []
}

function geometryKey(feature) {
  const properties = feature?.properties || {}
  const adcode = String(properties.adcode || properties.parent?.adcode || feature?.id || '')
  const geometry = feature?.geometry || (feature?.type && feature?.coordinates ? feature : {})
  return adcode + ':' + geometry.type + ':' + JSON.stringify(geometry.coordinates || null)
}

/**
 * Build an SVG path in a fixed viewBox. Returns null when the feature does not
 * contain a supported geometry so the UI can show an explicit unavailable state.
 */
export function buildRegionThumbnail(feature, options = {}) {
  const width = Math.max(24, Number(options.width) || 100)
  const height = Math.max(24, Number(options.height) || 72)
  const padding = Math.max(1, Number(options.padding) || 8)
  const rings = geometryRings(feature).map(validRing).filter((ring) => ring.length >= 3)
  if (!rings.length) return null

  const key = `${width}x${height}x${padding}:${geometryKey(feature)}`
  const cached = thumbnailCache.get(key)
  if (cached) return cached

  const points = rings.flat()
  const xs = points.map(([x]) => x)
  const ys = points.map(([, y]) => y)
  const minX = Math.min(...xs)
  const maxX = Math.max(...xs)
  const minY = Math.min(...ys)
  const maxY = Math.max(...ys)
  const sourceWidth = Math.max(maxX - minX, Number.EPSILON)
  const sourceHeight = Math.max(maxY - minY, Number.EPSILON)
  const availableWidth = Math.max(1, width - padding * 2)
  const availableHeight = Math.max(1, height - padding * 2)
  const scale = Math.min(availableWidth / sourceWidth, availableHeight / sourceHeight)
  const offsetX = (width - sourceWidth * scale) / 2
  const offsetY = (height - sourceHeight * scale) / 2

  const path = rings.map((ring) => {
    const commands = ring.map(([x, y], index) => {
      // SVG y grows downwards while geographic latitude grows upwards.
      const px = offsetX + (x - minX) * scale
      const py = offsetY + (maxY - y) * scale
      return `${index ? 'L' : 'M'}${px.toFixed(2)},${py.toFixed(2)}`
    })
    return commands.join(' ') + ' Z'
  }).join(' ')

  const result = {
    path,
    viewBox: `0 0 ${width} ${height}`,
    width,
    height,
    bounds: { minX, minY, maxX, maxY },
  }
  thumbnailCache.set(key, result)
  return result
}

export function clearRegionThumbnailCache() {
  thumbnailCache.clear()
}

export function regionThumbnailCacheSize() {
  return thumbnailCache.size
}
