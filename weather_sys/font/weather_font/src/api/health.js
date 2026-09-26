import request from './request'

export function getHealth() {
  return request.get('/health')
}
