<script setup>
defineProps({
  provinces: { type: Array, default: () => [] },
  cities: { type: Array, default: () => [] },
  districts: { type: Array, default: () => [] },
  selection: { type: Object, required: true },
  loading: Boolean,
})

defineEmits(['province-change', 'city-change', 'district-change'])
</script>

<template>
  <div class="location-selector">
    <span class="selector-label">数据地区</span>
    <label>
      <span>省份</span>
      <select
        :value="selection.province"
        :disabled="loading"
        @change="$emit('province-change', $event.target.value)"
      >
        <option value="">请选择省份</option>
        <option v-for="province in provinces" :key="province" :value="province">{{ province }}</option>
      </select>
    </label>
    <label>
      <span>城市</span>
      <select
        :value="selection.city"
        :disabled="loading || !selection.province"
        @change="$emit('city-change', $event.target.value)"
      >
        <option value="">请选择城市</option>
        <option v-for="city in cities" :key="city" :value="city">{{ city }}</option>
      </select>
    </label>
    <label>
      <span>区县</span>
      <select
        :value="selection.district"
        :disabled="loading || !selection.city"
        @change="$emit('district-change', $event.target.value)"
      >
        <option value="">全部 / 稳定代表区县</option>
        <option v-for="district in districts" :key="district" :value="district">{{ district }}</option>
      </select>
    </label>
    <span v-if="loading" class="selector-loading">更新中…</span>
  </div>
</template>

<style scoped>
.location-selector {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.selector-label {
  margin-right: 5px;
  color: var(--accent-cyan);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 12px;
}

select {
  min-width: 112px;
  padding: 7px 26px 7px 9px;
  color: var(--text-primary);
  background: rgb(4 33 67 / 92%);
  border: 1px solid var(--border-soft);
  border-radius: 6px;
  outline: none;
}

select:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 8px rgb(32 201 255 / 28%);
}

select:disabled {
  cursor: wait;
  opacity: 0.55;
}

.selector-loading {
  color: var(--text-muted);
  font-size: 12px;
}

@media (max-width: 680px) {
  .location-selector {
    align-items: stretch;
    flex-direction: column;
  }

  label {
    justify-content: space-between;
  }

  select {
    flex: 1;
  }
}
</style>
