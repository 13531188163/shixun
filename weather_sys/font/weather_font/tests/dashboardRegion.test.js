import test from 'node:test'
import assert from 'node:assert/strict'

import {
  comparableRegionName,
  regionScope,
  regionSelection,
  resolveRegionOption,
} from '../src/utils/dashboardRegion.js'

test('resolves map administrative suffixes to selector options', () => {
  assert.equal(resolveRegionOption(['四川', '云南'], '四川省'), '四川')
  assert.equal(resolveRegionOption(['甘孜藏族自治州'], '甘孜藏族自治州'), '甘孜藏族自治州')
  assert.equal(resolveRegionOption(['阿坝'], '阿坝藏族羌族自治州'), '阿坝')
  assert.equal(resolveRegionOption(['白玉县'], '白玉县'), '白玉县')
  assert.equal(comparableRegionName('内蒙古自治区'), '内蒙古')
  assert.equal(resolveRegionOption(['新疆', '青海'], '新疆维吾尔自治区'), '新疆')
  assert.equal(resolveRegionOption(['宁夏', '甘肃'], '宁夏回族自治区'), '宁夏')
  assert.equal(resolveRegionOption(['广西'], '广西壮族自治区'), '广西')
})

test('keeps country, province, city and district scopes explicit', () => {
  assert.equal(regionScope('', '', ''), 'country')
  assert.equal(regionScope('四川', '', ''), 'province')
  assert.equal(regionScope('四川', '甘孜藏族自治州', ''), 'city')
  assert.equal(regionScope('四川', '甘孜藏族自治州', '白玉县'), 'city')
  assert.deepEqual(regionSelection({ province: '四川', city: '甘孜', district: '白玉县' }), {
    province: '四川', city: '甘孜', district: '白玉县', scope: 'city',
  })
})
