import test from 'node:test'
import assert from 'node:assert/strict'

import {
  buildRegionThumbnail,
  clearRegionThumbnailCache,
  regionThumbnailCacheSize,
} from '../src/utils/regionThumbnail.js'

function polygonFeature(adcode, coordinates) {
  return {
    type: 'Feature',
    properties: { adcode, name: '测试区域' },
    geometry: { type: 'Polygon', coordinates },
  }
}

test('converts a polygon to a centered, y-inverted SVG path', () => {
  clearRegionThumbnailCache()
  const thumbnail = buildRegionThumbnail(polygonFeature('100001', [[
    [0, 0], [10, 0], [10, 20], [0, 20], [0, 0],
  ]]), { width: 120, height: 80 })

  assert.equal(thumbnail.viewBox, '0 0 120 80')
  assert.match(thumbnail.path, /^M/)
  assert.match(thumbnail.path, /Z$/)
  assert.ok(thumbnail.bounds.maxY > thumbnail.bounds.minY)
})

test('supports multipolygon features and reuses the geometry cache', () => {
  clearRegionThumbnailCache()
  const feature = {
    type: 'Feature',
    properties: { adcode: '100002', name: '多岛区域' },
    geometry: {
      type: 'MultiPolygon',
      coordinates: [
        [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]],
        [[[6, 6], [8, 6], [8, 8], [6, 8], [6, 6]]],
      ],
    },
  }

  const first = buildRegionThumbnail(feature)
  const second = buildRegionThumbnail(feature)
  assert.strictEqual(first, second)
  assert.equal(regionThumbnailCacheSize(), 1)
  assert.match(first.path, /M/g)
})

test('returns null for missing or unsupported geometry', () => {
  clearRegionThumbnailCache()
  assert.equal(buildRegionThumbnail({ properties: { adcode: '100003' } }), null)
  assert.equal(buildRegionThumbnail({ geometry: { type: 'Point', coordinates: [1, 2] } }), null)
  assert.equal(regionThumbnailCacheSize(), 0)
})
