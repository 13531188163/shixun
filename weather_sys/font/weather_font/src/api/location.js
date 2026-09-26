import request from './request'

export function getProvinces() {
  return request.get('/locations/provinces')
}

export function getCities(params) {
  return request.get('/locations/cities', { params })
}

export function getDistricts(params) {
  return request.get('/locations/districts', { params })
}
