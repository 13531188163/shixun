const DEFAULT_MARGIN = 0.84

function visitCoordinates(coordinates, visit) {
  if (!Array.isArray(coordinates) || !coordinates.length) return
  const first = coordinates[0]
  if (Array.isArray(first) && typeof first[0] === 'number' && typeof first[1] === 'number') {
    coordinates.forEach((point) => {
      if (Array.isArray(point) && Number.isFinite(point[0]) && Number.isFinite(point[1])) visit(point[0], point[1])
    })
    return
  }
  coordinates.forEach((child) => visitCoordinates(child, visit))
}

export function geoJsonBounds(geoJson) {
  const bounds = { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity }
  const features = Array.isArray(geoJson?.features) ? geoJson.features : []
  features.forEach((feature) => visitCoordinates(feature?.geometry?.coordinates, (x, y) => {
    bounds.minX = Math.min(bounds.minX, x)
    bounds.minY = Math.min(bounds.minY, y)
    bounds.maxX = Math.max(bounds.maxX, x)
    bounds.maxY = Math.max(bounds.maxY, y)
  }))
  if (![bounds.minX, bounds.minY, bounds.maxX, bounds.maxY].every(Number.isFinite)) return null
  const width = Math.max(bounds.maxX - bounds.minX, Number.EPSILON)
  const height = Math.max(bounds.maxY - bounds.minY, Number.EPSILON)
  return {
    ...bounds,
    width,
    height,
    centerX: (bounds.minX + bounds.maxX) / 2,
    centerY: (bounds.minY + bounds.maxY) / 2,
  }
}

export function expandGeoBounds(bounds, ratio = 0.03) {
  if (!bounds) return null
  const padX = bounds.width * ratio
  const padY = bounds.height * ratio
  return {
    minX: bounds.minX - padX,
    minY: bounds.minY - padY,
    maxX: bounds.maxX + padX,
    maxY: bounds.maxY + padY,
  }
}

/**
 * ECharts layoutSize is based on the shorter container side. Calculate a
 * safe size so the projected GeoJSON bounds keep a margin on every side.
 */
export function fitGeoBounds(bounds, viewport, margin = DEFAULT_MARGIN) {
  const width = Number(viewport?.width)
  const height = Number(viewport?.height)
  if (!bounds || !Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return { layoutSize: 84, zoom: 1, center: ['50%', '50%'], boundingCoords: null }
  }

  // ECharts GeoJSON maps use the default aspectScale 0.75. Using the same
  // scale here keeps the computed box consistent with the rendered map.
  const aspect = Math.max(bounds.width / bounds.height * 0.75, Number.EPSILON)
  const base = Math.min(width, height)
  const requiredSize = aspect >= 1
    ? Math.min(width, height * aspect)
    : Math.min(width / aspect, height)
  const size = Math.max(1, requiredSize * Math.min(Math.max(margin, 0.5), 0.95))
  const layoutSize = Math.max(24, Math.min(180, size / base * 100))
  const padded = expandGeoBounds(bounds)
  return {
    layoutSize,
    zoom: 1,
    center: ['50%', '50%'],
    boundingCoords: padded ? [[padded.minX, padded.maxY], [padded.maxX, padded.minY]] : null,
  }
}
