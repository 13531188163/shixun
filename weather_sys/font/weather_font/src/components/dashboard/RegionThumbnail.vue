<script setup>
import { computed } from 'vue'
import { buildRegionThumbnail } from '../../utils/regionThumbnail'

const props = defineProps({
  feature: { type: Object, default: null },
  selected: Boolean,
  width: { type: Number, default: 100 },
  height: { type: Number, default: 66 },
})

const thumbnail = computed(() => buildRegionThumbnail(props.feature, {
  width: props.width,
  height: props.height,
  padding: 7,
}))
</script>

<template>
  <div :class="['region-thumbnail', { selected }]" :style="{ height: `${height}px` }" aria-hidden="true">
    <svg v-if="thumbnail" :viewBox="thumbnail.viewBox" preserveAspectRatio="xMidYMid meet">
      <path :d="thumbnail.path" fill-rule="evenodd" />
    </svg>
    <span v-else class="thumbnail-unavailable">轮廓不可用</span>
  </div>
</template>

<style scoped>
.region-thumbnail {
  display: grid;
  width: 100%;
  height: 66px;
  place-items: center;
  overflow: hidden;
  background: radial-gradient(circle at 50% 44%, rgb(24 128 181 / 24%), transparent 67%), rgb(3 34 66 / 78%);
  border: 1px solid rgb(44 170 218 / 45%);
  border-radius: 5px;
  transition: border-color 180ms ease, background 180ms ease, box-shadow 180ms ease;
}

svg {
  width: 100%;
  height: 100%;
  padding: 4px;
  overflow: visible;
}

path {
  fill: rgb(18 91 137 / 76%);
  stroke: #39c8f2;
  stroke-width: 1.15;
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 2px rgb(33 196 244 / 65%));
  transition: fill 180ms ease, stroke 180ms ease, filter 180ms ease;
}

.region-thumbnail.selected {
  background: radial-gradient(circle at 50% 44%, rgb(208 138 44 / 33%), transparent 68%), rgb(49 51 53 / 72%);
  border-color: rgb(255 200 100 / 84%);
  box-shadow: 0 0 14px rgb(255 172 67 / 28%), inset 0 0 14px rgb(255 185 78 / 12%);
}

.region-thumbnail.selected path {
  fill: rgb(218 153 54 / 78%);
  stroke: #ffe2a6;
  filter: drop-shadow(0 0 3px rgb(255 173 50 / 90%));
}

.thumbnail-unavailable {
  padding: 4px;
  color: rgb(164 204 223 / 72%);
  font-size: 9px;
  text-align: center;
}
</style>
