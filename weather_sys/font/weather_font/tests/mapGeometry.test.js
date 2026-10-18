import test from 'node:test'
import assert from 'node:assert/strict'

import { expandGeoBounds, fitGeoBounds, geoJsonBounds } from '../src/utils/mapGeometry.js'

const featureCollection = {
  type: 'FeatureCollection',
  features: [{
    type: 'Feature',
    geometry: { type: 'MultiPolygon', coordinates: [[[[100, 30], [110, 30], [110, 40], [100, 30]]]] },
  }],
}

test('calculates bounds for polygon and multipolygon coordinates', () => {
  assert.deepEqual(geoJsonBounds(featureCollection), {
    minX: 100, minY: 30, maxX: 110, maxY: 40, width: 10, height: 10, centerX: 105, centerY: 35,
  })
  assert.equal(geoJsonBounds({ type: 'FeatureCollection', features: [] }), null)
})

test('expands real bounds without changing the map center', () => {
  const bounds = geoJsonBounds(featureCollection)
  const expanded = expandGeoBounds(bounds, 0.1)
  assert.equal(expanded.minX, 99)
  assert.equal(expanded.maxY, 41)
  assert.equal((expanded.minX + expanded.maxX) / 2, bounds.centerX)
})

test('fits wide and tall regions within the available viewport', () => {
  const wide = fitGeoBounds({ minX: 0, minY: 0, maxX: 20, maxY: 5, width: 20, height: 5 }, { width: 800, height: 400 })
  const tall = fitGeoBounds({ minX: 0, minY: 0, maxX: 5, maxY: 20, width: 5, height: 20 }, { width: 800, height: 400 })
  assert.ok(wide.layoutSize > 0 && wide.layoutSize <= 180)
  assert.ok(tall.layoutSize > 0 && tall.layoutSize <= 180)
  assert.deepEqual(wide.center, ['50%', '50%'])
  assert.equal(wide.boundingCoords.length, 2)
  assert.equal(tall.zoom, 1)
})


