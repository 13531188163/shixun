<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import RegionThumbnail from './RegionThumbnail.vue'
import { featureAdcode, featureName, isTerminalFeature } from '../../utils/administrativeMap'

const props = defineProps({
  features: { type: Array, default: () => [] },
  selectedAdcode: { type: [String, Number], default: '' },
  parentName: { type: String, default: '全国' },
  levelLabel: { type: String, default: '行政区边界' },
  loading: Boolean,
})

const emit = defineEmits(['select', 'enter'])
const scroller = ref(null)
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const cardElements = new Map()
let resizeObserver = null
let boundScroller = null
let updateFrame = 0
let pointerStartX = 0
let pointerStartScroll = 0
let pointerActive = false
let suppressClick = false

const normalizedSelected = computed(() => String(props.selectedAdcode || ''))
// 即使某个真实要素缺少几何，也保留卡片并显示“轮廓不可用”，避免把
// 数据源缺失悄悄伪装成“没有这个行政区”。
const cards = computed(() => props.features.filter((feature) => featureName(feature)))
const hasOverflow = computed(() => canScrollLeft.value || canScrollRight.value)

function cardCode(feature, index) {
  return String(featureAdcode(feature) || featureName(feature) || index)
}

function setCardElement(element, feature, index) {
  const key = cardCode(feature, index)
  if (element) cardElements.set(key, element)
  else cardElements.delete(key)
}

function updateScrollState() {
  const element = scroller.value
  if (!element) return
  canScrollLeft.value = element.scrollLeft > 1
  canScrollRight.value = element.scrollLeft + element.clientWidth < element.scrollWidth - 1
}

function bindScroller() {
  const element = scroller.value
  if (element === boundScroller) return
  if (boundScroller) boundScroller.removeEventListener('scroll', scheduleScrollState)
  resizeObserver?.disconnect()
  boundScroller = element || null
  if (!boundScroller) return
  boundScroller.addEventListener('scroll', scheduleScrollState, { passive: true })
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(scheduleScrollState)
    resizeObserver.observe(boundScroller)
  }
}

function scheduleScrollState() {
  if (updateFrame) return
  updateFrame = requestAnimationFrame(() => {
    updateFrame = 0
    updateScrollState()
  })
}

function scrollBy(distance) {
  const element = scroller.value
  if (!element) return
  element.scrollBy({ left: distance, behavior: 'smooth' })
}

function scrollPrevious() {
  scrollBy(-(scroller.value?.clientWidth || 320) * 0.78)
}

function scrollNext() {
  scrollBy((scroller.value?.clientWidth || 320) * 0.78)
}

function handleWheel(event) {
  const element = scroller.value
  if (!element || element.scrollWidth <= element.clientWidth) return
  const distance = event.deltaX || event.deltaY
  if (!distance) return
  const atStart = distance < 0 && element.scrollLeft <= 1
  const atEnd = distance > 0 && element.scrollLeft + element.clientWidth >= element.scrollWidth - 1
  if (atStart || atEnd) return
  event.preventDefault()
  element.scrollBy({ left: distance, behavior: 'auto' })
}

function handlePointerDown(event) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  const element = scroller.value
  if (!element) return
  pointerActive = true
  suppressClick = false
  pointerStartX = event.clientX
  pointerStartScroll = element.scrollLeft
  element.classList.add('is-dragging')
  element.setPointerCapture?.(event.pointerId)
}

function handlePointerMove(event) {
  if (!pointerActive || !scroller.value) return
  const delta = event.clientX - pointerStartX
  if (Math.abs(delta) > 5) suppressClick = true
  if (!suppressClick) return
  scroller.value.scrollLeft = pointerStartScroll - delta
  scheduleScrollState()
}

function handlePointerUp(event) {
  if (!pointerActive) return
  pointerActive = false
  scroller.value?.releasePointerCapture?.(event.pointerId)
  scroller.value?.classList.remove('is-dragging')
  if (suppressClick) window.setTimeout(() => { suppressClick = false }, 0)
}

function handleSelect(feature, event) {
  if (suppressClick) {
    event?.preventDefault()
    event?.stopPropagation()
    return
  }
  emit('select', feature)
}

function handleEnter(feature, event) {
  event?.preventDefault()
  event?.stopPropagation()
  if (props.loading) return
  emit('enter', feature)
}

function scrollSelectedIntoView() {
  const selected = normalizedSelected.value
  if (!selected) return
  const index = cards.value.findIndex((feature) => cardCode(feature, 0) === selected)
  if (index < 0) return
  const element = cardElements.get(cardCode(cards.value[index], index))
  element?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
}

watch(() => [props.features, normalizedSelected.value], async () => {
  await nextTick()
  bindScroller()
  updateScrollState()
  scrollSelectedIntoView()
}, { deep: true })

watch(scroller, async () => {
  await nextTick()
  bindScroller()
  updateScrollState()
})

onMounted(() => {
  bindScroller()
  updateScrollState()
  window.addEventListener('resize', scheduleScrollState)
})

onBeforeUnmount(() => {
  if (updateFrame) cancelAnimationFrame(updateFrame)
  resizeObserver?.disconnect()
  boundScroller?.removeEventListener('scroll', scheduleScrollState)
  window.removeEventListener('resize', scheduleScrollState)
  cardElements.clear()
})
</script>

<template>
  <section class="region-carousel" aria-label="行政区横向导航">
    <div class="carousel-heading">
      <div>
        <span class="carousel-kicker">REGION NAVIGATION</span>
        <strong>区域导航</strong>
        <small>{{ parentName }} · {{ levelLabel }}</small>
      </div>
      <span v-if="cards.length" class="carousel-count">{{ cards.length }} 个区域</span>
    </div>

    <div v-if="cards.length" class="carousel-track-wrap">
      <button type="button" class="carousel-arrow previous" :disabled="!canScrollLeft" aria-label="向左滚动" @click="scrollPrevious">‹</button>
      <div
        ref="scroller"
        class="carousel-track"
        @wheel="handleWheel"
        @pointerdown="handlePointerDown"
        @pointermove="handlePointerMove"
        @pointerup="handlePointerUp"
        @pointercancel="handlePointerUp"
      >
        <article
          v-for="(feature, index) in cards"
          :key="cardCode(feature, index)"
          :ref="(element) => setCardElement(element, feature, index)"
          :class="['region-card', { selected: cardCode(feature, index) === normalizedSelected }]"
          :aria-current="cardCode(feature, index) === normalizedSelected ? 'true' : undefined"
          role="button"
          tabindex="0"
          @click="handleSelect(feature, $event)"
          @dblclick="handleEnter(feature, $event)"
          @keydown.enter="handleEnter(feature, $event)"
        >
          <RegionThumbnail :feature="feature" :selected="cardCode(feature, index) === normalizedSelected" />
          <div class="region-card-meta">
            <strong>{{ featureName(feature) }}</strong>
            <small>{{ featureAdcode(feature) || '编码不可用' }}</small>
          </div>
          <button type="button" class="enter-region" :disabled="loading" @click="handleEnter(feature, $event)">
            {{ isTerminalFeature(feature) ? '查看数据' : '进入区域' }}
          </button>
        </article>
      </div>
      <button type="button" class="carousel-arrow next" :disabled="!canScrollRight" aria-label="向右滚动" @click="scrollNext">›</button>
    </div>

    <p v-else class="carousel-empty">当前层级没有可用的真实行政区边界数据</p>
    <span v-if="hasOverflow" class="carousel-hint">可拖动或滚轮横向浏览</span>
  </section>
</template>

<style scoped>
.region-carousel {
  position: relative;
  z-index: 5;
  min-width: 0;
  width: 100%;
  flex: 0 0 auto;
  padding: 7px 10px 8px;
  background: linear-gradient(180deg, rgb(4 34 67 / 93%), rgb(2 20 43 / 96%));
  border: 1px solid rgb(43 164 216 / 45%);
  border-radius: 5px;
  box-shadow: inset 0 0 20px rgb(22 144 206 / 8%), 0 0 16px rgb(13 139 194 / 10%);
}

.carousel-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin: 0 4px 6px;
}

.carousel-heading > div {
  display: flex;
  align-items: baseline;
  min-width: 0;
  gap: 8px;
}

.carousel-kicker {
  color: var(--accent-cyan);
  font-size: 8px;
  letter-spacing: 0.15em;
}

.carousel-heading strong {
  color: var(--text-primary);
  font-size: 12px;
}

.carousel-heading small,
.carousel-count,
.carousel-hint {
  color: var(--text-muted);
  font-size: 9px;
}

.carousel-count { flex: 0 0 auto; }

.carousel-track-wrap {
  position: relative;
  display: flex;
  min-width: 0;
  align-items: stretch;
  gap: 5px;
}

.carousel-track {
  display: flex;
  min-width: 0;
  flex: 1;
  gap: 7px;
  overflow-x: auto;
  overscroll-behavior-inline: contain;
  scrollbar-width: thin;
  scrollbar-color: rgb(52 192 233 / 58%) transparent;
  cursor: grab;
  touch-action: pan-y;
}

.carousel-track.is-dragging {
  cursor: grabbing;
  user-select: none;
}

.carousel-track::-webkit-scrollbar { height: 3px; }
.carousel-track::-webkit-scrollbar-thumb { background: rgb(52 192 233 / 58%); border-radius: 3px; }

.carousel-arrow {
  align-self: center;
  width: 22px;
  height: 54px;
  flex: 0 0 22px;
  color: #9feaff;
  font-size: 26px;
  line-height: 1;
  background: rgb(5 57 93 / 80%);
  border: 1px solid rgb(54 190 231 / 50%);
  border-radius: 4px;
  cursor: pointer;
}

.carousel-arrow:hover:not(:disabled),
.carousel-arrow:focus-visible:not(:disabled) { color: #fff2c9; border-color: #ffc66d; outline: none; }
.carousel-arrow:disabled { color: rgb(130 176 198 / 30%); background: rgb(5 32 59 / 55%); border-color: rgb(53 121 151 / 24%); cursor: default; }

.region-card {
  display: grid;
  min-width: 128px;
  width: 128px;
  flex: 0 0 128px;
  gap: 4px;
  padding: 5px;
  color: var(--text-secondary);
  background: linear-gradient(155deg, rgb(8 62 101 / 83%), rgb(3 35 67 / 92%));
  border: 1px solid rgb(39 151 202 / 50%);
  border-radius: 5px;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
}

.region-card:hover,
.region-card:focus-visible { transform: translateY(-1px); border-color: rgb(104 216 244 / 88%); outline: none; box-shadow: 0 0 12px rgb(23 177 229 / 22%); }
.region-card.selected { background: linear-gradient(155deg, rgb(83 65 39 / 90%), rgb(31 42 52 / 96%)); border-color: #ffc76b; box-shadow: 0 0 15px rgb(255 166 50 / 30%), inset 0 0 12px rgb(255 193 80 / 9%); }

.region-card-meta { display: flex; min-width: 0; align-items: baseline; justify-content: space-between; gap: 4px; }
.region-card-meta strong { overflow: hidden; color: var(--text-primary); font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.region-card-meta small { color: rgb(145 203 230 / 67%); font-size: 8px; }
.enter-region { padding: 2px 4px; color: #a9eaff; font-size: 8px; background: rgb(10 78 117 / 72%); border: 1px solid rgb(56 185 226 / 48%); border-radius: 3px; cursor: pointer; }
.region-card.selected .enter-region { color: #ffe0a3; border-color: rgb(255 192 89 / 70%); background: rgb(111 76 33 / 52%); }
.enter-region:disabled { cursor: wait; opacity: 0.5; }
.carousel-empty { margin: 4px; color: var(--text-muted); font-size: 10px; }
.carousel-hint { display: block; margin: 4px 4px 0; color: rgb(145 203 230 / 52%); }

@media (max-width: 760px) {
  .carousel-heading > div { gap: 5px; }
  .carousel-kicker { display: none; }
  .region-card { min-width: 116px; width: 116px; flex-basis: 116px; }
}
</style>
