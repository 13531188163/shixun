import request from './request'

export function getLatestAirQuality(params) {
  return request.get('/air-quality/latest', { params })
}

export function getAirQualityRanking(params) {
  return request.get('/air-quality/ranking', { params })
}

export function getAirQualityDistribution(params) {
  return request.get('/air-quality/distribution', { params })
}

export function getAirQualityOverview(params) {
  return request.get('/air-quality/overview', { params })
}

export function getAirQualityProvinces() {
  return request.get('/air-quality/provinces')
}

export function getAirQualityCities(params) {
  return request.get('/air-quality/cities', { params })
}

export function getAirQualityLevels(params) {
  return request.get('/air-quality/levels', { params })
}
