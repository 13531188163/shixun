import axios from 'axios'

const DEFAULT_GET_CACHE_TTL = 30_000
const getCache = new Map()
const pendingGets = new Map()

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
    const timeoutMessage = error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT'
      ? '查询超时，请重试'
      : ''
    const normalizedError = new Error(
      apiResponse?.message || timeoutMessage || error.message || 'API request failed',
    )
    normalizedError.response = error.response
    normalizedError.apiResponse = apiResponse
    return Promise.reject(normalizedError)
  },
)

function stableParams(value) {
  if (value === null || value === undefined) return ''
  if (Array.isArray(value)) return `[${value.map(stableParams).join(',')}]`
  if (typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${key}:${stableParams(value[key])}`).join('|')}}`
  }
  return String(value)
}

function cacheKey(url, params) {
  return `${url}?${stableParams(params)}`
}

function trimCache() {
  while (getCache.size > 100) {
    const oldestKey = getCache.keys().next().value
    if (oldestKey === undefined) break
    getCache.delete(oldestKey)
  }
}

// Dashboard data is read-only historical data.  Keep successful GET responses
// briefly and share an in-flight request so route switches do not issue the
// same database query repeatedly.
const rawGet = request.get.bind(request)
request.get = (url, config = {}) => {
  const {
    cache: cacheEnabled = true,
    cacheTtl = DEFAULT_GET_CACHE_TTL,
    ...axiosConfig
  } = config
  if (cacheEnabled === false || cacheTtl <= 0) return rawGet(url, axiosConfig)

  const key = cacheKey(url, axiosConfig.params)
  const now = Date.now()
  const cached = getCache.get(key)
  if (cached && cached.expiresAt > now) return Promise.resolve(cached.payload)
  if (cached) getCache.delete(key)
  if (pendingGets.has(key)) return pendingGets.get(key)

  const pending = rawGet(url, axiosConfig)
    .then((payload) => {
      getCache.set(key, { expiresAt: Date.now() + cacheTtl, payload })
      trimCache()
      return payload
    })
    .finally(() => pendingGets.delete(key))
  pendingGets.set(key, pending)
  return pending
}

export function clearRequestCache() {
  getCache.clear()
}

export default request
