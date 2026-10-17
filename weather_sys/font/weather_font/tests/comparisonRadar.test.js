import test from 'node:test'
import assert from 'node:assert/strict'
import {
  RADAR_FIELDS,
  buildRadarValues,
  finiteNumber,
  normalizeRadarValue,
  selectRadarDimensions,
} from '../src/utils/comparisonRadar.js'

const baseline = {
  avgTempEstimate: { min: -20, max: 40 },
  totalPrecip: { min: 0, max: 200 },
  avgWind: { min: 0, max: 20 },
  aqiSnapshot: { min: 10, max: 300 },
}

function city(index, overrides = {}) {
  return {
    province: `省${index}`,
    city: `城市${index}`,
    weatherMetrics: { avgTempEstimate: -5 + index, totalPrecip: 20 + index, avgWind: 2 + index },
    aqiSnapshot: { aqi: 40 + index },
    ...overrides,
  }
}

test('keeps three weather dimensions when AQI is missing for two cities', () => {
  const cities = [city(1, { aqiSnapshot: { aqi: null } }), city(2, { aqiSnapshot: { aqi: null } })]
  assert.deepEqual(selectRadarDimensions(cities, baseline).map((field) => field.key), [
    'avgTempEstimate', 'totalPrecip', 'avgWind',
  ])
})

test('supports two, three and four cities without requiring four dimensions', () => {
  for (const count of [2, 3, 4]) {
    assert.equal(selectRadarDimensions(Array.from({ length: count }, (_, index) => city(index)), baseline).length, 4)
  }
})

test('distinguishes zero, negative temperatures, strings and invalid values', () => {
  assert.equal(finiteNumber(0), 0)
  assert.equal(finiteNumber('-8.5'), -8.5)
  assert.equal(finiteNumber(''), null)
  assert.equal(finiteNumber(null), null)
  assert.equal(finiteNumber(Number.NaN), null)
  assert.equal(finiteNumber(Number.POSITIVE_INFINITY), null)
  const stringMetrics = [
    city(1, { weatherMetrics: { avgTempEstimate: '-8.5', totalPrecip: '0', avgWind: '2.4' } }),
    city(2, { weatherMetrics: { avgTempEstimate: '0', totalPrecip: '4.2', avgWind: '3.1' } }),
  ]
  assert.deepEqual(selectRadarDimensions(stringMetrics, baseline).map((field) => field.key), [
    'avgTempEstimate', 'totalPrecip', 'avgWind', 'aqiSnapshot',
  ])
})

test('uses a stable real baseline and handles equal ranges without NaN', () => {
  const equalBaseline = { ...baseline, avgWind: { min: 3, max: 3 } }
  const value = normalizeRadarValue(RADAR_FIELDS[2], city(1, { weatherMetrics: { avgWind: 3 } }), equalBaseline)
  assert.equal(value, 0.5)
  const values = buildRadarValues([city(1), city(2)], RADAR_FIELDS.slice(0, 3), baseline)
  assert.equal(values.length, 2)
  assert.equal(values[0].length, 3)
  assert.equal(values[1].length, 3)
  assert.ok(values.flat().every((item) => Number.isFinite(item)))
})

test('excludes AQI only when one selected city has no snapshot', () => {
  const cities = [city(1), city(2, { aqiSnapshot: { aqi: undefined } }), city(3)]
  const dimensions = selectRadarDimensions(cities, baseline)
  assert.equal(dimensions.length, 3)
  assert.ok(!dimensions.some((field) => field.key === 'aqiSnapshot'))
})
