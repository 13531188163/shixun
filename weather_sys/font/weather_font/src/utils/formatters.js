export function formatNumber(value, suffix = '--') {
  if (value === null || value === undefined || value === '') return suffix
  return typeof value === 'number' ? String(value) : value
}

export function formatTemperature(value) {
  const formatted = formatNumber(value)
  return formatted === '--' ? formatted : `${formatted}°C`
}

export function formatWind(value) {
  const formatted = formatNumber(value)
  return formatted === '--' ? formatted : `${formatted} m/s`
}

export function formatPrecipitation(value) {
  const formatted = formatNumber(value)
  return formatted === '--' ? formatted : `${formatted} mm`
}

export function formatDateTime(value) {
  return formatNumber(value)
}

export function weatherSymbol(weather) {
  const text = String(weather || '')
  if (text.includes('雪')) return '❄'
  if (text.includes('雨')) return '☂'
  if (text.includes('阴')) return '☁'
  if (text.includes('云')) return '◒'
  if (text.includes('晴')) return '☀'
  return '◌'
}

export function aqiStatusClass(status) {
  const text = String(status || '')
  if (text.includes('严重')) return 'aqi-severe'
  if (text.includes('优')) return 'aqi-good'
  if (text.includes('良')) return 'aqi-moderate'
  if (text.includes('轻')) return 'aqi-light'
  if (text.includes('中')) return 'aqi-medium'
  if (text.includes('重')) return 'aqi-heavy'
  return 'aqi-unknown'
}

export function aqiStatusColor(status) {
  const classes = {
    'aqi-good': '#36e0a0',
    'aqi-moderate': '#f4d35e',
    'aqi-light': '#ff9f43',
    'aqi-medium': '#ff6b6b',
    'aqi-heavy': '#c56cf0',
    'aqi-severe': '#ad274d',
  }
  return classes[aqiStatusClass(status)] || '#8da8c8'
}
