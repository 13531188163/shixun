import test from 'node:test'
import assert from 'node:assert/strict'

import {
  ADMIN_MAP_SOURCE,
  NATIONAL_ADCODE,
  clearAdministrativeMapCache,
  featureLevel,
  isTerminalFeature,
  loadAdministrativeMap,
  mapSourceUrl,
  normalizeAdministrativeGeoJson,
} from '../src/utils/administrativeMap.js'
import {
  TAIWAN_MAP_PATH,
  taiwanTopologyToFeatureCollection,
} from '../src/utils/taiwanAdministrative.js'

function feature(adcode, name, level, childrenNum = 0) {
  return {
    type: 'Feature',
    properties: { adcode, name, level, childrenNum, parent: { adcode: 100000 } },
    geometry: { type: 'Polygon', coordinates: [] },
  }
}

function taiwanTopologyFixture() {
  return {
    type: 'Topology',
    transform: { scale: [1, 1], translate: [0, 0] },
    arcs: [
      [[0, 0], [1, 0], [0, 1], [-1, 0], [0, -1]],
      [[2, 0], [1, 0], [0, 1], [-1, 0], [0, -1]],
    ],
    objects: {
      counties: {
        type: 'GeometryCollection',
        geometries: [{
          type: 'Polygon',
          arcs: [[0]],
          properties: { COUNTYCODE: '10002', COUNTYNAME: '宜蘭縣' },
        }],
      },
      towns: {
        type: 'GeometryCollection',
        geometries: [{
          type: 'Polygon',
          arcs: [[1]],
          properties: {
            COUNTYCODE: '10002', COUNTYNAME: '宜蘭縣', TOWNCODE: '10002010', TOWNNAME: '宜蘭市',
          },
        }],
      },
    },
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

test('keeps Taiwan official county/town codes and allows 710000 drilldown', () => {
  const topology = taiwanTopologyFixture()
  const counties = taiwanTopologyToFeatureCollection(topology, '710000')
  const towns = taiwanTopologyToFeatureCollection(topology, '10002')

  assert.equal(counties.features.length, 1)
  assert.equal(counties.features[0].properties.adcode, '10002')
  assert.equal(counties.features[0].properties.parentAdcode, '710000')
  assert.equal(counties.features[0].properties.name, '宜兰县')
  assert.equal(counties.features[0].properties.childrenNum, 1)
  assert.equal(towns.features[0].properties.adcode, '10002010')
  assert.equal(towns.features[0].properties.parentAdcode, '10002')
  assert.equal(towns.features[0].properties.level, 'district')
  assert.equal(taiwanTopologyToFeatureCollection(topology, '710000').features[0].geometry.type, 'Polygon')
  assert.equal(isTerminalFeature({
    properties: { adcode: '710000', name: '台湾省', level: 'province', childrenNum: 0 },
  }), false)
})

test('loads Taiwan topology once for province and county views', async () => {
  clearAdministrativeMapCache()
  const calls = []
  const fixture = taiwanTopologyFixture()
  const fetchImpl = async (url) => {
    calls.push(url)
    return { ok: true, json: async () => fixture }
  }

  const province = await loadAdministrativeMap('710000', { fetchImpl })
  const county = await loadAdministrativeMap('10002', { fetchImpl })
  assert.equal(province.features.length, 1)
  assert.equal(county.features[0].properties.adcode, '10002010')
  assert.deepEqual(calls, [TAIWAN_MAP_PATH])
  assert.equal(mapSourceUrl('10002010'), TAIWAN_MAP_PATH)
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

test('uses real province resources for national-to-province navigation and keeps special-region sources explicit', () => {
  assert.equal(mapSourceUrl(NATIONAL_ADCODE), '/maps/china.json')
  assert.equal(mapSourceUrl('510000'), `${ADMIN_MAP_SOURCE}/510000_full.json`)
  assert.equal(mapSourceUrl('110000'), `${ADMIN_MAP_SOURCE}/110000_full.json`)
  assert.equal(mapSourceUrl('810000'), `${ADMIN_MAP_SOURCE}/810000_full.json`)
  assert.equal(mapSourceUrl('820000'), `${ADMIN_MAP_SOURCE}/820000_full.json`)
  assert.equal(mapSourceUrl('710000'), TAIWAN_MAP_PATH)
})

test('does not retain a failed province resource in the cache so retry can recover', async () => {
  clearAdministrativeMapCache()
  let calls = 0
  const fetchImpl = async (url) => {
    calls += 1
    if (url === `${mapSourceUrl('510000')}`) return { ok: false, status: 503, json: async () => ({}) }
    return { ok: true, json: async () => ({ type: 'FeatureCollection', features: [feature(510000, '四川省', 'province', 21)] }) }
  }

  await assert.rejects(loadAdministrativeMap('510000', { fetchImpl }), /请求失败/)
  await assert.rejects(loadAdministrativeMap('510000', { fetchImpl }), /请求失败/)
  assert.equal(calls, 2)
})

test('rejects malformed or invalid administrative codes', async () => {
  assert.throws(() => normalizeAdministrativeGeoJson({ type: 'FeatureCollection', features: [] }), /没有可用边界/)
  await assert.rejects(loadAdministrativeMap('37000'), /行政区编码无效/)
})
