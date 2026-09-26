// Shared ECharts visual language for the dark dashboard. Business data stays
// in the view components; this module only contains presentation primitives.

export const CHART_COLORS = Object.freeze({
  warm: '#f6ac69',
  warmLight: '#ffd19f',
  cool: '#65adff',
  coolLight: '#a9d5ff',
  cyan: '#32c9ee',
  green: '#45d9ad',
  text: '#eaf6ff',
  textSecondary: '#9bb9d5',
  textMuted: '#718eac',
  axis: 'rgba(92, 153, 196, 0.48)',
  grid: 'rgba(83, 147, 194, 0.14)',
  tooltipBackground: 'rgba(3, 22, 48, 0.96)',
  tooltipBorder: 'rgba(72, 185, 235, 0.58)',
})

export const DARK_TOOLTIP = Object.freeze({
  backgroundColor: CHART_COLORS.tooltipBackground,
  borderColor: CHART_COLORS.tooltipBorder,
  borderWidth: 1,
  padding: [9, 12],
  textStyle: { color: CHART_COLORS.text, fontSize: 12 },
  extraCssText: 'box-shadow: 0 8px 24px rgba(0, 9, 25, 0.38);',
})

export const DARK_LEGEND = Object.freeze({
  top: 0,
  right: 0,
  itemWidth: 10,
  itemHeight: 6,
  itemGap: 14,
  textStyle: { color: CHART_COLORS.textSecondary, fontSize: 11 },
  selectedMode: false,
})

export const CATEGORY_AXIS = Object.freeze({
  axisLine: { lineStyle: { color: CHART_COLORS.axis, width: 1 } },
  axisTick: { show: false },
  axisLabel: { color: CHART_COLORS.textSecondary, fontSize: 11, margin: 9 },
})

export const VALUE_AXIS = Object.freeze({
  axisLine: { show: false },
  axisTick: { show: false },
  axisLabel: { color: CHART_COLORS.textMuted, fontSize: 10 },
  splitLine: { lineStyle: { color: CHART_COLORS.grid, width: 1 } },
})

export const AXIS_NAME = Object.freeze({
  color: CHART_COLORS.textMuted,
  fontSize: 10,
  padding: [0, 0, 0, 4],
})

export const CHART_GRID = Object.freeze({
  top: 34,
  right: 18,
  bottom: 30,
  left: 42,
  containLabel: true,
})

export function temperatureArea(color, opacity = 0.14) {
  return {
    color: {
      type: 'linear',
      x: 0,
      y: 0,
      x2: 0,
      y2: 1,
      colorStops: [
        { offset: 0, color: rgba(color, opacity) },
        { offset: 1, color: 'rgba(3, 27, 57, 0)' },
      ],
    },
  }
}

// ECharts accepts rgba strings directly; keeping this helper explicit makes
// the opacity intent clear and avoids coupling chart colors to CSS variables.
export function rgba(hex, alpha) {
  const value = String(hex).replace('#', '')
  if (value.length !== 6) return hex
  const red = Number.parseInt(value.slice(0, 2), 16)
  const green = Number.parseInt(value.slice(2, 4), 16)
  const blue = Number.parseInt(value.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, ${alpha})`
}

export function formatAxisDate(value) {
  const text = String(value ?? '')
  return text.length >= 10 && text[4] === '-' ? text.slice(5, 10) : text
}

export function numericValue(value) {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
