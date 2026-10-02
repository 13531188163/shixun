import request from './request'

export function getLatestWeather(params) {
  return request.get('/weather/latest', { params })
}

export function getWeatherDates(params) {
  return request.get('/weather/dates', { params })
}

export function getWeatherTrend(params) {
  return request.get('/weather/trend', { params })
}

export function getCityWeatherComparison(params) {
  return request.get('/weather/city-comparison', { params })
}
