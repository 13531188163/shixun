import request from './request'

export function getLatestWeather(params) {
  return request.get('/weather/latest', { params })
}

export function getWeatherDates(params) {
  return request.get('/weather/dates', { params })
}

export function getProvinceWeatherDates(params) {
  return request.get('/weather/province-dates', { params })
}

export function getNationalWeatherDates() {
  return request.get('/weather/national-dates')
}

export function getWeatherTrend(params) {
  return request.get('/weather/trend', { params })
}

export function getProvinceWeatherTrend(params) {
  return request.get('/weather/province-trend', { params })
}

export function getNationalWeatherTrend(params) {
  return request.get('/weather/national-trend', { params })
}

export function getCityWeatherComparison(params) {
  return request.get('/weather/city-comparison', { params })
}
