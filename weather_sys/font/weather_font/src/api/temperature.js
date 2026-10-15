import request from './request'

const TEMPERATURE_REQUEST_TIMEOUT = 30000

function temperatureParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ''),
  )
}

export function getTemperatureAverage(params) {
  return request.get('/temperature/average', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}

export function getTemperatureDates(params) {
  return request.get('/temperature/dates', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}

export function getTemperatureExtremes(params) {
  return request.get('/temperature/extremes', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}

export function getTemperatureTrend(params) {
  return request.get('/temperature/trend', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}

export function getTemperatureMonthly(params) {
  return request.get('/temperature/monthly', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}

export function getRecentTemperature(params) {
  return request.get('/temperature/recent', { params: temperatureParams(params), timeout: TEMPERATURE_REQUEST_TIMEOUT })
}
