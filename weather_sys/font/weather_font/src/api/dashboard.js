import request from './request'

export function getDashboardOverview(params) {
  return request.get('/dashboard/overview', { params })
}
