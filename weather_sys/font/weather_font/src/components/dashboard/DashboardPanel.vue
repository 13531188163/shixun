<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
})
</script>

<template>
  <article class="dashboard-panel">
    <header class="panel-header">
      <div class="panel-heading-copy">
        <h2 class="panel-title">{{ title }}</h2>
      </div>
      <p v-if="subtitle" class="panel-subtitle" :title="subtitle">{{ subtitle }}</p>
      <slot name="header" />
    </header>
    <div class="panel-body">
      <slot />
    </div>
  </article>
</template>
