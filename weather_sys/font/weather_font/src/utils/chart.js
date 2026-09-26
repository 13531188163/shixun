import * as echarts from 'echarts'
import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'

export function useEChart(elementRef, getOption, sources = []) {
  let chart
  let resizeObserver
  let resizeTimer
  let mounted = false
  let renderVersion = 0
  let chartElement

  function scheduleResize() {
    if (resizeTimer) window.clearTimeout(resizeTimer)
    resizeTimer = window.setTimeout(() => {
      resizeTimer = undefined
      resize()
    }, 100)
  }

  async function render() {
    const version = ++renderVersion
    await nextTick()
    if (!mounted || version !== renderVersion) return
    if (!elementRef.value) {
      disposeChart()
      return
    }
    if (!chart || chartElement !== elementRef.value) {
      disposeChart()
      chartElement = elementRef.value
      chart = echarts.init(chartElement, undefined, { renderer: 'canvas' })
      observeElement(chartElement)
    }
    chart.setOption(getOption() || {}, true)
    scheduleResize()
  }

  function observeElement(element) {
    resizeObserver?.disconnect()
    resizeObserver = undefined
    if (typeof ResizeObserver === 'undefined' || !element) return
    resizeObserver = new ResizeObserver(scheduleResize)
    resizeObserver.observe(element)
  }

  function disposeChart() {
    resizeObserver?.disconnect()
    resizeObserver = undefined
    chart?.dispose()
    chart = undefined
    chartElement = undefined
  }

  function resize() {
    if (!mounted || !chart || chart.isDisposed?.()) return
    chart.resize({ animation: { duration: 0 } })
  }

  onMounted(() => {
    mounted = true
    render()
    window.addEventListener('resize', scheduleResize, { passive: true })
  })

  watch(sources, render, { deep: true })

  onBeforeUnmount(() => {
    mounted = false
    renderVersion += 1
    window.removeEventListener('resize', scheduleResize)
    resizeObserver?.disconnect()
    resizeObserver = undefined
    if (resizeTimer) window.clearTimeout(resizeTimer)
    resizeTimer = undefined
    disposeChart()
  })
}
