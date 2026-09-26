<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <article class="dashboard-panel">
    <header class="panel-header">
      <div>
        <h2 class="panel-title">{{ title }}</h2>
        <p v-if="subtitle" class="panel-subtitle">{{ subtitle }}</p>
      </div>
      <slot name="header" />
    </header>
    <div class="panel-body">
      <slot />
    </div>
  </article>
</template>
