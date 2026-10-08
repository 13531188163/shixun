import request from './request'

export function getDashboardOverview(params) {
  return request.get('/dashboard/overview', { params })
}

export function getProvinceDashboardOverview(params) {
  return request.get('/dashboard/province-overview', { params })
}
