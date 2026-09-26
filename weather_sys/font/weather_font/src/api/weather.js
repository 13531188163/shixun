import request from './request'

export function getLatestWeather(params) {
  return request.get('/weather/latest', { params })
}

export function getWeatherTrend(params) {
  return request.get('/weather/trend', { params })
}

export function getCityWeatherComparison(params) {
  return request.get('/weather/city-comparison', { params })
}
