<script setup>
defineProps({
  loading: Boolean,
  error: { type: String, default: '' },
  empty: Boolean,
  emptyMessage: { type: String, default: '暂无数据' },
})
</script>

<template>
  <div v-if="loading" class="panel-state">
    <div class="spinner" aria-hidden="true" />
    <span>正在读取真实数据…</span>
  </div>
  <div v-else-if="error" class="panel-state error">{{ error }}</div>
  <div v-else-if="empty" class="panel-state">{{ emptyMessage }}</div>
  <slot v-else />
</template>
