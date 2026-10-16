import request from './request'

export function getComparisonLocations() {
  return request.get('/comparison/locations')
}

export function getComparison(params) {
  return request.get('/comparison', { params })
}
