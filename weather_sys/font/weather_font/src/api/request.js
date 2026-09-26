import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
  headers: {
    Accept: 'application/json',
  },
})

request.interceptors.response.use(
  (response) => {
    const payload = response.data
    if (!payload || typeof payload !== 'object' || typeof payload.code !== 'number') {
      const error = new Error('API response format is invalid')
      error.response = response
      return Promise.reject(error)
    }
    if (payload.code !== 200) {
      const error = new Error(payload.message || 'API request failed')
      error.response = response
      error.apiResponse = payload
      return Promise.reject(error)
    }
    return payload
  },
  (error) => {
    const apiResponse = error.response?.data
    const normalizedError = new Error(
      apiResponse?.message || error.message || 'API request failed',
    )
    normalizedError.response = error.response
    normalizedError.apiResponse = apiResponse
    return Promise.reject(normalizedError)
  },
)

export default request
