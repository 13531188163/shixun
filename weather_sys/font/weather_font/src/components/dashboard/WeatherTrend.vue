<script setup>
import WeatherTrendChart from './WeatherTrendChart.vue'

defineProps({
  data: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})
</script>

<template>
  <div class="weather-trend" data-testid="weather-trend">
    <WeatherTrendChart :data="data" :loading="loading" :error="error" />
  </div>
</template>

<style scoped>
.weather-trend { display: flex; min-height: 0; height: 100%; flex: 1; flex-direction: column; }
</style>
