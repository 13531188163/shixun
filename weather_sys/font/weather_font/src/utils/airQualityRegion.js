const CITY_ALIASES = Object.freeze({
  广安市: '广安',
  阿坝藏族羌族自治州: '阿坝',
  凉山彝族自治州: '凉山',
})

export function airQualityCityKey(value) {
  const text = String(value ?? '').trim()
  return CITY_ALIASES[text] || (text.endsWith('市') ? text.slice(0, -1) : text)
}

export function sameAirQualityCity(left, right) {
  return Boolean(left) && Boolean(right) && airQualityCityKey(left) === airQualityCityKey(right)
}
