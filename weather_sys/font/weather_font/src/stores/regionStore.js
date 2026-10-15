import { reactive, ref } from 'vue'

function createMapRegion() {
  return {
    adcode: '',
    name: '',
    level: '',
    parentAdcode: '',
    province: '',
    city: '',
    district: '',
    scope: 'country',
    path: [],
    terminal: false,
  }
}

function createDataRegion() {
  return {
    province: '',
    city: '',
    district: '',
    scope: 'country',
  }
}

export const mapRegion = reactive(createMapRegion())
export const dataRegion = reactive(createDataRegion())
export const currentDate = ref('')

function regionScope(value, fallback = 'province') {
  if (value?.scope) return value.scope
  if (value?.city) return 'city'
  if (value?.province) return 'province'
  return fallback
}

function writeMapRegion(value = {}) {
  Object.assign(mapRegion, {
    ...createMapRegion(),
    ...value,
    province: String(value.province || ''),
    city: String(value.city || ''),
    district: String(value.district || ''),
    scope: regionScope(value, 'country'),
    path: Array.isArray(value.path) ? value.path.map((item) => ({ ...item })) : [],
  })
}

function writeDataRegion(value = {}) {
  Object.assign(dataRegion, {
    ...createDataRegion(),
    province: String(value.province || ''),
    city: String(value.city || ''),
    district: String(value.district || ''),
    scope: regionScope(value, value?.province ? 'province' : 'country'),
  })
}

export function setMapRegion(value) {
  writeMapRegion(value)
}

export function setDataRegion(value) {
  writeDataRegion(value)
}

export function setCurrentDate(value) {
  currentDate.value = String(value || '')
}

export const regionStore = {
  mapRegion,
  dataRegion,
  currentDate,
  setMapRegion,
  setDataRegion,
  setCurrentDate,
}
