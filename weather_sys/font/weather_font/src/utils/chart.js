import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'

export function useEChart(elementRef, getOption, sources = []) {
  let chart

  async function render() {
    await nextTick()
    if (!elementRef.value) return
    if (!chart) chart = echarts.init(elementRef.value)
    chart.setOption(getOption(), true)
    chart.resize()
  }

  function resize() {
    chart?.resize()
  }

  onMounted(() => {
    render()
    window.addEventListener('resize', resize)
  })

  watch(sources, render, { deep: true })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    chart?.dispose()
    chart = undefined
  })
}
