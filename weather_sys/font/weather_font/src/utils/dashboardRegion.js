/**
 * Pure helpers used by the homepage to keep map names and selector values in
 * the same normalized shape.  Database-backed options are still supplied by
 * the caller; this module never invents an administrative area.
 */

const EXPLICIT_REGION_ALIASES = {
  内蒙古: '内蒙古',
  内蒙古自治区: '内蒙古',
  广西: '广西',
  广西壮族自治区: '广西',
  宁夏: '宁夏',
  宁夏回族自治区: '宁夏',
  新疆: '新疆',
  新疆维吾尔自治区: '新疆',
  西藏: '西藏',
  西藏自治区: '西藏',
  阿坝: '阿坝藏族羌族自治州',
  阿坝藏族羌族自治州: '阿坝藏族羌族自治州',
  凉山: '凉山彝族自治州',
  凉山彝族自治州: '凉山彝族自治州',
  甘孜: '甘孜藏族自治州',
  甘孜藏族自治州: '甘孜藏族自治州',
}

export function comparableRegionName(value) {
  const raw = String(value || '').trim().replace(/\s+/gu, '')
  const canonical = EXPLICIT_REGION_ALIASES[raw] || raw
  return canonical.replace(/特别行政区|自治区|自治州|地区|盟|省|市$/u, '')
}

export function resolveRegionOption(options, value) {
  const raw = String(value || '').trim()
  if (!raw) return ''
  return options.find((item) => String(item) === raw)
    || options.find((item) => comparableRegionName(item) === comparableRegionName(raw))
    || raw
}

export function regionScope(province, city, district) {
  if (!province) return 'country'
  return city || district ? 'city' : 'province'
}

export function regionSelection({ province = '', city = '', district = '' } = {}) {
  return {
    province: String(province || '').trim(),
    city: String(city || '').trim(),
    district: String(district || '').trim(),
    scope: regionScope(province, city, district),
  }
}
