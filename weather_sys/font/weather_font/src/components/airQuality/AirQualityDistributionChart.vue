<script setup>
import { computed, ref } from 'vue'
import ChartState from '../dashboard/ChartState.vue'
import { useEChart } from '../../utils/chart'
import { CHART_COLORS, DARK_LEGEND, DARK_TOOLTIP } from '../../utils/chartTheme'
const props = defineProps({ data: { type: Array, default: () => [] }, loading: Boolean, error: { type: String, default: '' } })
const element = ref(null); const total = computed(() => (props.data || []).reduce((s, x) => s + Number(x.count || 0), 0)); const colors = ['#36e0a0','#f4d35e','#ff9f43','#ff6b6b','#c56cf0','#ff4f76']
function option(){const rows=props.data||[];return{tooltip:{trigger:'item',...DARK_TOOLTIP,formatter:(x)=>`${x.marker}${x.name}<br/>城市：${x.value}（${x.percent}%）`},legend:{...DARK_LEGEND,orient:'vertical',left:'52%',top:'middle',data:rows.map(x=>x.status),formatter:(name)=>{const x=rows.find(y=>y.status===name);return `{name|${name}} {count|${x?.count||0}} {pct|${x?.percentage||0}%}`},textStyle:{...DARK_LEGEND.textStyle,rich:{name:{width:70,color:CHART_COLORS.textSecondary},count:{width:32,color:CHART_COLORS.text},pct:{width:45,color:CHART_COLORS.text}}}},graphic:[{type:'text',left:'25%',top:'42%',style:{text:`${total.value}`,fill:CHART_COLORS.text,fontSize:25,fontWeight:700,textAlign:'center'}},{type:'text',left:'25%',top:'57%',style:{text:'有效城市',fill:CHART_COLORS.textMuted,fontSize:11,textAlign:'center'}}],series:[{type:'pie',radius:['44%','70%'],center:['25%','51%'],label:{show:false},data:rows.map((x,i)=>({name:x.status,value:Number(x.count||0),itemStyle:{color:colors[i%colors.length]}}))}]}}
useEChart(element, option, [() => props.data, () => props.loading, () => props.error, total])
</script>
<template><ChartState :loading="loading" :error="error" :empty="!data.length || !total" empty-message="暂无空气质量等级数据"><div ref="element" class="air-distribution" aria-label="空气质量等级分布环形图" /></ChartState></template>
<style scoped>.air-distribution{width:100%;height:100%;min-height:220px}</style>
