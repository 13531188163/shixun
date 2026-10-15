<script setup>
import { computed, ref } from 'vue'

import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import { CHART_COLORS, DARK_LEGEND, DARK_TOOLTIP } from '../../utils/chartTheme'

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const chartElement = ref(null)
const levelColors = Object.freeze({
  无降水: '#7890ad',
  小雨: '#48c4f1',
  中雨: '#4f78ff',
  大雨: '#f5be3e',
  暴雨: '#f05a67',
})

const totalCount = computed(() => (props.data || []).reduce((sum, row) => sum + Number(row.count || 0), 0))
const rainyCount = computed(() => (props.data || [])
  .filter((row) => row.level !== '无降水')
  .reduce((sum, row) => sum + Number(row.count || 0), 0))

function percentage(count) {
  const total = totalCount.value
  if (!total) return '0.0'
  return ((Number(count || 0) / total) * 100).toFixed(1)
}

function buildOption() {
  const rows = props.data || []
  return {
    animationDuration: 520,
    tooltip: {
      trigger: 'item',
      ...DARK_TOOLTIP,
      formatter: (item) => `${item.marker}${item.name}<br/>天数：${item.value}（${item.percent}%）`,
    },
    legend: {
      ...DARK_LEGEND,
      orient: 'vertical',
      top: 'middle',
      left: '49%',
      right: 0,
      width: '51%',
      itemWidth: 10,
      itemHeight: 10,
      data: rows.map((row) => row.level),
      formatter: (name) => {
        const row = rows.find((item) => item.level === name)
        const count = Number(row?.count || 0)
        return `{name|${name}}{count|${count}天}{percent|${percentage(count)}%}`
      },
      textStyle: {
        ...DARK_LEGEND.textStyle,
        rich: {
          name: { width: 52, color: CHART_COLORS.textSecondary, fontSize: 11 },
          count: { width: 38, color: CHART_COLORS.text, fontSize: 11, align: 'right' },
          percent: { width: 43, color: CHART_COLORS.text, fontSize: 11, align: 'right' },
        },
      },
    },
    graphic: [
      {
        type: 'text',
        left: '27%',
        top: '42%',
        style: {
          text: `${rainyCount.value}天`,
          fill: CHART_COLORS.text,
          fontSize: 25,
          fontWeight: 700,
          textAlign: 'center',
        },
      },
      {
        type: 'text',
        left: '27%',
        top: '57%',
        style: {
          text: '总降水天数',
          fill: CHART_COLORS.textMuted,
          fontSize: 11,
          textAlign: 'center',
        },
      },
    ],
    series: [
      {
        name: '降水等级',
        type: 'pie',
        radius: ['48%', '73%'],
        center: ['27%', '51%'],
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        data: rows.map((row) => ({
          name: row.level,
          value: Number(row.count || 0),
          itemStyle: { color: levelColors[row.level] || CHART_COLORS.cyan },
        })),
        emphasis: {
          scale: true,
          scaleSize: 5,
          itemStyle: { shadowBlur: 16, shadowColor: 'rgba(36, 193, 242, 0.28)' },
        },
      },
    ],
  }
}

useEChart(chartElement, buildOption, [() => props.data, () => props.loading, () => props.error, totalCount, rainyCount])
</script>

<template>
  <ChartState :loading="loading" :error="error" :empty="!props.data.length || totalCount === 0" empty-message="暂无降水等级数据">
    <div ref="chartElement" class="echart rainfall-distribution-chart" aria-label="降水等级分布环形图" />
  </ChartState>
</template>

<style scoped>
.echart {
  width: 100%;
  height: 100%;
  min-height: 190px;
  flex: 1 1 auto;
}
</style>
