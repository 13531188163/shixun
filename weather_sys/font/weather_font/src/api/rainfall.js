import request from './request'

const RAINFALL_REQUEST_TIMEOUT = 30000

function rainfallParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ''),
  )
}

export function getRainfallDates(params) {
  return request.get('/rainfall/dates', {
    params: rainfallParams(params),
    timeout: RAINFALL_REQUEST_TIMEOUT,
  })
}

export function getRainfallCore(params) {
  return request.get('/rainfall/core', {
    params: rainfallParams(params),
    timeout: RAINFALL_REQUEST_TIMEOUT,
  })
}

export function getRecentRainfall(params) {
  return request.get('/rainfall/recent', {
    params: rainfallParams(params),
    timeout: RAINFALL_REQUEST_TIMEOUT,
  })
}

export function getRainfallTrend(params) {
  return request.get('/rainfall/trend', {
    params: rainfallParams(params),
    timeout: RAINFALL_REQUEST_TIMEOUT,
  })
}

export function getRainfallDistribution(params) {
  return request.get('/rainfall/distribution', {
    params: rainfallParams(params),
    timeout: RAINFALL_REQUEST_TIMEOUT,
  })
}
