export const RADAR_FIELDS = Object.freeze([
  { key: 'avgTempEstimate', name: '平均温度', unit: ' ℃', digits: 2 },
  { key: 'totalPrecip', name: '降水累计', unit: ' mm', digits: 2 },
  { key: 'avgWind', name: '平均风速', unit: ' m/s', digits: 2 },
  { key: 'aqiSnapshot', name: 'AQI快照', unit: '', digits: 0 },
])

export function finiteNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

export function metricValue(city, field) {
  if (field === 'aqiSnapshot') return finiteNumber(city?.aqiSnapshot?.aqi)
  return finiteNumber(city?.weatherMetrics?.[field])
}

export function baselineRange(baseline, field) {
  const range = baseline?.[field]
  const minimum = finiteNumber(range?.min)
  const maximum = finiteNumber(range?.max)
  return minimum === null || maximum === null ? null : { minimum, maximum }
}

export function selectRadarDimensions(cities, baseline, fields = RADAR_FIELDS) {
  if (!Array.isArray(cities) || cities.length === 0) return []
  return fields.filter((field) => {
    if (!baselineRange(baseline, field.key)) return false
    return cities.every((city) => metricValue(city, field.key) !== null)
  })
}

export function normalizeRadarValue(field, city, baseline) {
  const value = metricValue(city, field.key)
  const range = baselineRange(baseline, field.key)
  if (value === null || !range) return null
  if (range.minimum === range.maximum) return 0.5
  const normalized = (value - range.minimum) / (range.maximum - range.minimum)
  return Number.isFinite(normalized) ? Math.max(0, Math.min(1, normalized)) : null
}

export function buildRadarValues(cities, dimensions, baseline) {
  if (!Array.isArray(cities) || !Array.isArray(dimensions)) return []
  return cities.map((city) => dimensions.map((field) => normalizeRadarValue(field, city, baseline)))
}
