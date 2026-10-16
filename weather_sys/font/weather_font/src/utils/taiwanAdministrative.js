/**
 * 台湾行政区边界适配。
 *
 * DataV 的全国资源只把台湾省作为 710000 一个省级要素，并没有可供
 * 下钻的子级边界。这里使用项目内随前端发布的 taiwan-towns.topo.json：
 * 该文件来自 taiwan-atlas 的 MIT 分发版本，原始边界取自台湾内政部
 * / NLSC 开放资料。COUNTYCODE（5 位）和 TOWNCODE（8 位）原样保留，
 * 不把它们拼接成不存在的 710xxx 编码。
 */

export const TAIWAN_ADCODE = '710000'
export const TAIWAN_MAP_PATH = '/maps/taiwan-towns.topo.json'

// 22 个县市代码由台湾官方县市边界资料的 COUNTYCODE 字段核验而来。
// name 是页面展示用的简体名称，sourceName 保留原始资料名称。
export const TAIWAN_COUNTY_CODES = Object.freeze({
  '09007': Object.freeze({ name: '连江县', sourceName: '連江縣' }),
  '09020': Object.freeze({ name: '金门县', sourceName: '金門縣' }),
  '10002': Object.freeze({ name: '宜兰县', sourceName: '宜蘭縣' }),
  '10004': Object.freeze({ name: '新竹县', sourceName: '新竹縣' }),
  '10005': Object.freeze({ name: '苗栗县', sourceName: '苗栗縣' }),
  '10007': Object.freeze({ name: '彰化县', sourceName: '彰化縣' }),
  '10008': Object.freeze({ name: '南投县', sourceName: '南投縣' }),
  '10009': Object.freeze({ name: '云林县', sourceName: '雲林縣' }),
  '10010': Object.freeze({ name: '嘉义县', sourceName: '嘉義縣' }),
  '10013': Object.freeze({ name: '屏东县', sourceName: '屏東縣' }),
  '10014': Object.freeze({ name: '台东县', sourceName: '台東縣' }),
  '10015': Object.freeze({ name: '花莲县', sourceName: '花蓮縣' }),
  '10016': Object.freeze({ name: '澎湖县', sourceName: '澎湖縣' }),
  '10017': Object.freeze({ name: '基隆市', sourceName: '基隆市' }),
  '10018': Object.freeze({ name: '新竹市', sourceName: '新竹市' }),
  '10020': Object.freeze({ name: '嘉义市', sourceName: '嘉義市' }),
  '63000': Object.freeze({ name: '台北市', sourceName: '台北市' }),
  '64000': Object.freeze({ name: '高雄市', sourceName: '高雄市' }),
  '65000': Object.freeze({ name: '新北市', sourceName: '新北市' }),
  '66000': Object.freeze({ name: '台中市', sourceName: '台中市' }),
  '67000': Object.freeze({ name: '台南市', sourceName: '台南市' }),
  '68000': Object.freeze({ name: '桃园市', sourceName: '桃園市' }),
})

const TRADITIONAL_TO_SIMPLIFIED = Object.freeze({
  臺: '台', 連: '连', 江: '江', 門: '门', 蘭: '兰', 蘇: '苏', 澳: '澳', 蘆: '芦', 龜: '龟',
  復: '复', 竹: '竹', 苗: '苗', 栗: '栗',
  彰: '彰', 化: '化', 南: '南', 投: '投', 雲: '云', 嘉: '嘉', 義: '义', 屏: '屏',
  東: '东', 花: '花', 蓮: '莲', 澎: '澎', 湖: '湖', 基: '基', 隆: '隆', 高: '高',
  雄: '雄', 新: '新', 北: '北', 中: '中', 台: '台', 桃: '桃', 園: '园', 縣: '县',
  市: '市', 鎮: '镇', 鄉: '乡', 區: '区', 里: '里', 間: '间', 溪: '溪',
})

export function simplifyTaiwanName(value) {
  return String(value || '').replace(/[臺連門蘭蘇澳蘆龜復雲義東蓮園縣鎮鄉區]/gu, (character) => (
    TRADITIONAL_TO_SIMPLIFIED[character] || character
  ))
}

export function isTaiwanCountyCode(value) {
  return Object.prototype.hasOwnProperty.call(TAIWAN_COUNTY_CODES, String(value || '').trim())
}

export function isTaiwanTownCode(value) {
  return /^\d{8}$/.test(String(value || '').trim())
}

function decodeArc(topology, index) {
  const reversed = index < 0
  const arcIndex = reversed ? ~index : index
  const arc = topology.arcs?.[arcIndex]
  if (!Array.isArray(arc)) return []
  const scale = topology.transform?.scale || [1, 1]
  const translate = topology.transform?.translate || [0, 0]
  let x = 0
  let y = 0
  const points = arc.map((point) => {
    x += Number(point?.[0] || 0)
    y += Number(point?.[1] || 0)
    return [x * scale[0] + translate[0], y * scale[1] + translate[1]]
  })
  return reversed ? points.reverse() : points
}

function decodeRing(topology, arcIndexes) {
  if (!Array.isArray(arcIndexes)) return []
  const ring = []
  arcIndexes.forEach((index, partIndex) => {
    const points = decodeArc(topology, Number(index))
    if (!points.length) return
    ring.push(...(partIndex ? points.slice(1) : points))
  })
  if (ring.length > 2) {
    const first = ring[0]
    const last = ring[ring.length - 1]
    if (first[0] !== last[0] || first[1] !== last[1]) ring.push([...first])
  }
  return ring
}

export function topologyGeometryToGeoJson(topology, geometry) {
  if (!geometry || !['Polygon', 'MultiPolygon'].includes(geometry.type)) return null
  if (geometry.type === 'Polygon') {
    return {
      type: 'Polygon',
      coordinates: (geometry.arcs || []).map((ring) => decodeRing(topology, ring)).filter((ring) => ring.length > 3),
    }
  }
  return {
    type: 'MultiPolygon',
    coordinates: (geometry.arcs || [])
      .map((polygon) => polygon.map((ring) => decodeRing(topology, ring)).filter((ring) => ring.length > 3))
      .filter((polygon) => polygon.length),
  }
}

function countyProperties(source, townCount) {
  const code = String(source?.COUNTYCODE || '').trim()
  const mapping = TAIWAN_COUNTY_CODES[code]
  if (!mapping) return null
  return {
    adcode: code,
    taiwanCode: code,
    name: mapping.name,
    sourceName: String(source?.COUNTYNAME || mapping.sourceName),
    level: 'city',
    childrenNum: townCount,
    parent: { adcode: TAIWAN_ADCODE },
    parentAdcode: TAIWAN_ADCODE,
    codeSystem: 'COUNTYCODE',
  }
}

function townProperties(source) {
  const countyCode = String(source?.COUNTYCODE || '').trim()
  const townCode = String(source?.TOWNCODE || '').trim()
  if (!isTaiwanCountyCode(countyCode) || !isTaiwanTownCode(townCode)) return null
  return {
    adcode: townCode,
    taiwanCode: townCode,
    name: simplifyTaiwanName(source?.TOWNNAME),
    sourceName: String(source?.TOWNNAME || '').trim(),
    level: 'district',
    childrenNum: 0,
    parent: { adcode: countyCode },
    parentAdcode: countyCode,
    countyCode,
    codeSystem: 'TOWNCODE',
  }
}

function sourceFeature(topology, geometry, properties) {
  const geoJsonGeometry = topologyGeometryToGeoJson(topology, geometry)
  if (!properties || !geoJsonGeometry || !geoJsonGeometry.coordinates.length) return null
  return {
    type: 'Feature',
    id: properties.taiwanCode,
    properties,
    geometry: geoJsonGeometry,
  }
}

/**
 * Convert the vendored official-derived TopoJSON to the FeatureCollection shape
 * consumed by ECharts. `parentCode=710000` returns 22 counties/cities; a
 * verified 5-digit COUNTYCODE returns only its real TOWNCODE features.
 */
export function taiwanTopologyToFeatureCollection(topology, parentCode = TAIWAN_ADCODE) {
  if (!topology || topology.type !== 'Topology' || !topology.objects) {
    throw new Error('台湾行政区地图资源格式无效')
  }
  const requested = String(parentCode || '').trim()
  const towns = topology.objects.towns?.geometries || []
  const townCounts = towns.reduce((counts, geometry) => {
    const code = String(geometry?.properties?.COUNTYCODE || '').trim()
    if (isTaiwanCountyCode(code)) counts[code] = (counts[code] || 0) + 1
    return counts
  }, {})
  const sourceGeometries = requested === TAIWAN_ADCODE
    ? (topology.objects.counties?.geometries || [])
    : towns.filter((geometry) => String(geometry?.properties?.COUNTYCODE || '').trim() === requested)
  const features = sourceGeometries.map((geometry) => {
    const properties = requested === TAIWAN_ADCODE
      ? countyProperties(geometry?.properties, townCounts[String(geometry?.properties?.COUNTYCODE || '').trim()] || 0)
      : townProperties(geometry?.properties)
    return sourceFeature(topology, geometry, properties)
  }).filter(Boolean)
  if (!features.length) throw new Error(`台湾行政区没有可用边界（${requested}）`)
  return { type: 'FeatureCollection', features }
}
