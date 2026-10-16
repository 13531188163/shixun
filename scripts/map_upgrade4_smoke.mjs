/*
 * Browser smoke test for Map Upgrade 4.
 *
 * Prerequisites: start Flask on 5000, Vite on 5173 and Chrome with
 * --remote-debugging-port=9222, then run `node scripts/map_upgrade4_smoke.mjs`.
 * The script only reads rendered state and clicks real UI controls.
 */
import { writeFileSync, mkdirSync } from 'node:fs'

const baseUrl = process.env.WEATHERDEMO_URL || 'http://127.0.0.1:5173/'
const cdpUrl = process.env.CDP_URL || 'http://127.0.0.1:9222/json'
const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds))

async function connect() {
  const targets = await (await fetch(cdpUrl)).json()
  const target = targets.find((item) => item.type === 'page' && item.url.startsWith(baseUrl)) || targets.find((item) => item.type === 'page')
  if (!target?.webSocketDebuggerUrl) throw new Error(`没有找到 ${baseUrl} 的 Chrome 页面`)
  const socket = new WebSocket(target.webSocketDebuggerUrl)
  const pending = new Map()
  let sequence = 0
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    const resolver = pending.get(message.id)
    if (!resolver) return
    pending.delete(message.id)
    if (message.error) resolver.reject(new Error(message.error.message))
    else resolver.resolve(message.result)
  })
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  const command = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++sequence
    pending.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
  await command('Runtime.enable')
  return { socket, command }
}

async function evaluate(command, expression) {
  const result = await command('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
  return result?.result?.value
}

async function waitFor(command, expression, label, timeout = 20000) {
  const started = Date.now()
  while (Date.now() - started < timeout) {
    const value = await evaluate(command, expression)
    if (value) return value
    await sleep(250)
  }
  throw new Error(`等待超时：${label}`)
}

async function clickCard(command, name) {
  const clicked = await evaluate(command, `(() => {
    const card = [...document.querySelectorAll('.region-card')].find((item) => item.textContent.includes(${JSON.stringify(name)}))
    if (!card) return false
    card.click()
    return true
  })()`)
  if (!clicked) throw new Error(`没有找到区域卡片：${name}`)
}

async function setViewport(command, width, height) {
  await command('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false })
  await evaluate(command, 'window.dispatchEvent(new Event("resize"))')
  await sleep(250)
}

async function navigateFresh(command) {
  // Page.navigate 返回时旧文档可能仍在 DOM 中；先等待新文档 ready，
  // 避免把旧地图卡片误当成新一轮验收的初始状态。
  await command('Page.navigate', { url: `${baseUrl}?map4Smoke=${Date.now()}` })
  await waitFor(command, 'document.readyState === "complete"', '页面文档加载完成', 30000)
  await sleep(350)
}

const checks = []
function record(name, passed, detail = '') {
  checks.push({ name, passed, detail })
  console.log(`${passed ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`)
}

const { socket, command } = await connect()
try {
  await navigateFresh(command)
  await waitFor(command, 'document.querySelector("[data-testid=dashboard-layout]") && document.querySelectorAll(".region-card").length > 0', 'Map4 页面与全国卡片')

  for (const viewport of [[1920, 1080], [1366, 768], [1100, 800]]) {
    await setViewport(command, ...viewport)
    const metrics = await evaluate(command, `(() => {
      const rect = (selector) => { const node = document.querySelector(selector); const box = node?.getBoundingClientRect(); return box ? { width: Math.round(box.width), height: Math.round(box.height) } : null }
      return {
        viewport: [window.innerWidth, window.innerHeight],
        horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
        layout: rect('[data-testid=dashboard-layout]'),
        center: rect('.dashboard-layout-center'),
        map: rect('.map-canvas'),
        carousel: rect('.region-carousel'),
        chartCount: document.querySelectorAll('[data-testid=weather-trend], [data-testid=aqi-chart], [data-testid=region-ranking]').length,
      }
    })()`)
    const valid = metrics.layout?.width > 0 && metrics.center?.width > 0 && metrics.map?.height > 0 && metrics.carousel?.height > 0 && !metrics.horizontalOverflow
    record(`${viewport[0]}×${viewport[1]} 响应式布局`, valid, JSON.stringify(metrics))
  }

  await setViewport(command, 1366, 768)
  await navigateFresh(command)
  await waitFor(command, 'document.querySelectorAll(".region-card").length > 0', '全国地图重载')
  await clickCard(command, '福建省')
  await waitFor(command, 'document.querySelector(".breadcrumb-item.active")?.textContent.includes("福建")', '福建省地图')
  await waitFor(command, 'document.querySelector("[data-testid=weather-metrics-panel]") && document.querySelector("[data-testid=aqi-chart]") && document.querySelector("[data-testid=region-ranking]")', '福建数据面板完成加载')
  const fujianMetrics = await evaluate(command, `({ cards: document.querySelectorAll('.region-card').length, heading: document.querySelector('.area-heading h3')?.textContent.trim() || '', chartCount: document.querySelectorAll('[data-testid=weather-trend], [data-testid=aqi-chart], [data-testid=region-ranking]').length })`)
  record('全国→福建省与大屏面板联动', fujianMetrics.cards > 0 && fujianMetrics.chartCount === 3, JSON.stringify(fujianMetrics))

  await clickCard(command, '泉州市')
  await waitFor(command, 'document.querySelector(".breadcrumb-item.active")?.textContent.includes("泉州")', '泉州市地图')
  await waitFor(command, 'document.querySelector("[data-testid=weather-metrics-panel]") && document.querySelector("[data-testid=aqi-chart]") && document.querySelector("[data-testid=region-ranking]")', '泉州数据面板完成加载')
  const quanzhou = await evaluate(command, `(() => {
    return {
      path: [...document.querySelectorAll('.breadcrumb-item')].map((item) => item.textContent.trim()),
      title: document.querySelector('[data-testid=header-title]')?.textContent.trim() || '',
      metrics: document.querySelector('[data-testid=weather-metrics-panel]') !== null,
      aqi: document.querySelector('[data-testid=aqi-chart]') !== null,
      ranking: document.querySelector('[data-testid=region-ranking]') !== null,
    }
  })()`)
  record('点击泉州后地图、左右面板同步', quanzhou.path.some((item) => item.includes('泉州')) && quanzhou.metrics && quanzhou.aqi && quanzhou.ranking, JSON.stringify(quanzhou))

  const beforeDrag = (await evaluate(command, '[...document.querySelectorAll(".breadcrumb-item")].map((item) => item.textContent.trim()).join("/")'))
  await evaluate(command, `(() => {
    const track = document.querySelector('.carousel-track')
    if (!track) return false
    track.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 500, pointerId: 19, button: 0 }))
    track.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: 350, pointerId: 19, buttons: 1 }))
    track.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 350, pointerId: 19 }))
    return true
  })()`)
  await sleep(350)
  const afterDrag = await evaluate(command, '[...document.querySelectorAll(".breadcrumb-item")].map((item) => item.textContent.trim()).join("/")')
  record('拖动底部导航不误触发钻取', beforeDrag === afterDrag, `${beforeDrag} → ${afterDrag}`)

  await evaluate(command, 'window.scrollTo(0, 0)')
  const screenshot = await command('Page.captureScreenshot', { format: 'png' })
  const outputDir = 'C:\\Users\\白衣辞镜\\AppData\\Local\\Temp\\weatherdemo-map4'
  mkdirSync(outputDir, { recursive: true })
  writeFileSync(`${outputDir}\\dashboard-quanzhou-1366.png`, Buffer.from(screenshot.data, 'base64'))

  await evaluate(command, 'document.querySelector(".breadcrumb-item")?.click()')
  await waitFor(command, 'document.querySelectorAll(".breadcrumb-item").length === 1 && document.querySelectorAll(".region-card").length === 34', '返回全国')
  record('面包屑返回全国', true, `${await evaluate(command, 'document.querySelectorAll(".region-card").length')} 个全国区域`)

  console.log(`SCREENSHOT ${outputDir}\\dashboard-quanzhou-1366.png`)
} finally {
  await command('Emulation.clearDeviceMetricsOverride').catch(() => {})
  socket.close()
}

if (checks.some((item) => !item.passed)) process.exitCode = 1
