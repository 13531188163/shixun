import test from 'node:test'
import assert from 'node:assert/strict'

import {
  NATIONAL_ADCODE,
  clearAdministrativeMapCache,
  featureLevel,
  isTerminalFeature,
  loadAdministrativeMap,
  mapSourceUrl,
  normalizeAdministrativeGeoJson,
} from '../src/utils/administrativeMap.js'

function feature(adcode, name, level, childrenNum = 0) {
  return {
    type: 'Feature',
    properties: { adcode, name, level, childrenNum, parent: { adcode: 100000 } },
    geometry: { type: 'Polygon', coordinates: [] },
  }
}

test('normalizes real FeatureCollection and discards non-boundary placeholder features', () => {
  const result = normalizeAdministrativeGeoJson({
    type: 'FeatureCollection',
    features: [
      feature(370000, '山东省', 'province', 16),
      { type: 'Feature', properties: { adcode: '100000_JD', name: '' } },
      { type: 'Feature', properties: { adcode: 370001, name: '无几何要素' } },
    ],
  })

  assert.equal(result.features.length, 1)
  assert.equal(result.features[0].properties.name, '山东省')
})

test('recognizes terminal city-level direct-admin units and district units', () => {
  const directAdminCity = feature(469001, '五指山市', 'city', 0)
  const district = feature(370502, '东营区', 'district', 0)
  const cityWithChildren = feature(370500, '东营市', 'city', 5)

  assert.equal(featureLevel(directAdminCity), 'city')
  assert.equal(isTerminalFeature(directAdminCity), true)
  assert.equal(featureLevel(district), 'district')
  assert.equal(isTerminalFeature(district), true)
  assert.equal(isTerminalFeature(cityWithChildren), false)
})

test('loads national and child maps by adcode and reuses the in-flight promise', async () => {
  clearAdministrativeMapCache()
  const calls = []
  const fetchImpl = async (url) => {
    calls.push(url)
    return {
      ok: true,
      json: async () => ({ type: 'FeatureCollection', features: [feature(370000, '山东省', 'province', 16)] }),
    }
  }

  const first = loadAdministrativeMap(NATIONAL_ADCODE, { fetchImpl })
  const second = loadAdministrativeMap(NATIONAL_ADCODE, { fetchImpl })
  assert.strictEqual(first, second)
  await first
  await loadAdministrativeMap('370000', { fetchImpl })

  assert.deepEqual(calls, ['/maps/china.json', `${mapSourceUrl('370000')}`])
})

test('rejects malformed or invalid administrative codes', async () => {
  assert.throws(() => normalizeAdministrativeGeoJson({ type: 'FeatureCollection', features: [] }), /没有可用边界/)
  await assert.rejects(loadAdministrativeMap('37000'), /行政区编码无效/)
})
