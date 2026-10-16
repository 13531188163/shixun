import request from './request'

const WIND_REQUEST_TIMEOUT = 30000

function windParams(params = {}) {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ''))
}

export const getWindDates = (params) => request.get('/wind/dates', { params: windParams(params), timeout: WIND_REQUEST_TIMEOUT })
export const getWindCore = (params) => request.get('/wind/core', { params: windParams(params), timeout: WIND_REQUEST_TIMEOUT })
export const getWindTrend = (params) => request.get('/wind/trend', { params: windParams(params), timeout: WIND_REQUEST_TIMEOUT })
export const getWindDistribution = (params) => request.get('/wind/distribution', { params: windParams(params), timeout: WIND_REQUEST_TIMEOUT })
export const getRecentWind = (params) => request.get('/wind/recent', { params: windParams(params), timeout: WIND_REQUEST_TIMEOUT })
