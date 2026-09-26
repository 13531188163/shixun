import request from './request'

export function getLatestAirQuality(params) {
  return request.get('/air-quality/latest', { params })
}

export function getAirQualityRanking(params) {
  return request.get('/air-quality/ranking', { params })
}

export function getAirQualityDistribution() {
  return request.get('/air-quality/distribution')
}
