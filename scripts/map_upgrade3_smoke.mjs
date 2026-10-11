/*
 * Optional local browser smoke test for Map Upgrade 3.
 *
 * Start Vite and Chrome with --remote-debugging-port=9222, then run:
 *   node scripts/map_upgrade3_smoke.mjs
 * The script only reads rendered state and clicks real carousel controls; it
 * does not write application data.
 */

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

async function waitFor(command, expression, label, timeout = 15000) {
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

async function clickFirstCard(command) {
  const clicked = await evaluate(command, `(() => {
    const card = document.querySelector('.region-card')
    if (!card) return false
    card.click()
    return true
  })()`)
  if (!clicked) throw new Error('当前层级没有可点击的区域卡片')
}

async function returnNational(command) {
  await evaluate(command, `document.querySelector('.breadcrumb-item')?.click()`)
  await waitFor(command, `document.querySelectorAll('.breadcrumb-item').length === 1`, '返回全国')
}

async function breadcrumb(command) {
  return evaluate(command, ` [...document.querySelectorAll('.breadcrumb-item')].map((item) => item.textContent.trim()) `)
}

const checks = []
function record(name, passed, detail) {
  checks.push({ name, passed, detail })
  console.log(`${passed ? 'PASS' : 'FAIL'} ${name}${detail ? ` — ${detail}` : ''}`)
}

const { socket, command } = await connect()
try {
  await command('Page.navigate', { url: baseUrl })
  await sleep(1200)
  await waitFor(command, `document.querySelectorAll('.region-card').length > 0`, '全国区域卡片')
  record('全国地图加载', true, `${await evaluate(command, 'document.querySelectorAll(".region-card").length')} 个区域卡片`)

  await clickCard(command, '台湾省')
  const taiwanPath = await waitFor(command, `document.querySelectorAll('.breadcrumb-item').length === 2 && document.querySelector('.breadcrumb-item.active')?.textContent.includes('台湾')`, '台湾省地图')
  const taiwanCount = await waitFor(command, `document.querySelectorAll('.region-card').length === 22 ? 22 : 0`, '台湾 22 个县市卡片')
  record('台湾省下钻', Boolean(taiwanPath && taiwanCount), `${taiwanCount} 个县市卡片`)

  await clickCard(command, '宜兰县')
  const countyPath = await waitFor(command, `document.querySelectorAll('.breadcrumb-item').length === 3 && document.querySelector('.breadcrumb-item.active')?.textContent.includes('宜兰')`, '台湾县市地图')
  const townCount = await waitFor(command, `document.querySelectorAll('.region-card').length > 0`, '台湾乡镇卡片')
  record('台湾县市→乡镇', Boolean(countyPath && townCount), `${await evaluate(command, 'document.querySelectorAll(".region-card").length')} 个乡镇卡片`)
  await clickFirstCard(command)
  const taiwanTerminal = await waitFor(command, `document.querySelector('.map-terminal-note')?.textContent.includes('区县')`, '台湾乡镇末级提示')
  await waitFor(command, `document.querySelector('.dashboard-alert')?.textContent.includes('暂无') || [...document.querySelectorAll('.panel-state')].some((item) => item.textContent.includes('暂无'))`, '台湾暂无数据提示')
  const taiwanBody = await evaluate(command, 'document.body.innerText')
  const taiwanNoData = taiwanBody.includes('暂无数据库天气/AQI覆盖') || taiwanBody.includes('暂无天气') || taiwanBody.includes('暂无空气质量')
  const taiwanPanelState = await evaluate(command, `JSON.stringify({
    breadcrumb: [...document.querySelectorAll('.breadcrumb-item')].map((item) => item.textContent.trim()),
    heading: document.querySelector('.area-heading h3')?.textContent.trim() || '',
    subheading: document.querySelector('.area-heading p')?.textContent.trim() || '',
    alert: document.querySelector('.dashboard-alert')?.textContent.trim() || '',
  })`)
  record('台湾末级暂无数据提示', Boolean(taiwanTerminal && taiwanNoData), taiwanNoData ? '不伪造天气或 AQI' : `${taiwanPanelState}`)

  await returnNational(command)
  await clickCard(command, '福建省')
  await waitFor(command, `document.querySelector('.breadcrumb-item.active')?.textContent.includes('福建')`, '福建省级地图')
  await clickCard(command, '福州市')
  await waitFor(command, `document.querySelector('.breadcrumb-item.active')?.textContent.includes('福州')`, '福州市地图')
  const fujianChildCount = await evaluate(command, 'document.querySelectorAll(".region-card").length')
  await clickFirstCard(command)
  const fujianTerminalOrMap = await waitFor(command, `document.querySelectorAll('.breadcrumb-item').length >= 4`, '福建区县地图或末级')
  record('福建→福州→区县', Boolean(fujianTerminalOrMap && fujianChildCount > 0), `${fujianChildCount} 个区县卡片`)

  await returnNational(command)
  // 连续点击两个全国卡片，最后一次点击应赢得异步地图请求。
  await evaluate(command, `(() => {
    const cards = [...document.querySelectorAll('.region-card')]
    const fujian = cards.find((item) => item.textContent.includes('福建省'))
    const xinjiang = cards.find((item) => item.textContent.includes('新疆维吾尔自治区'))
    fujian?.click()
    xinjiang?.click()
    return Boolean(fujian && xinjiang)
  })()`)
  const rapidPath = await waitFor(command, `document.querySelector('.breadcrumb-item.active')?.textContent.includes('新疆')`, '连续点击后的最终区域')
  record('连续快速点击请求竞争', Boolean(rapidPath), (await breadcrumb(command)).join(' / '))
  await clickCard(command, '乌鲁木齐市')
  await waitFor(command, `document.querySelector('.breadcrumb-item.active')?.textContent.includes('乌鲁木齐')`, '乌鲁木齐地图')
  await clickCard(command, '天山区')
  const terminal = await waitFor(command, `document.querySelector('.map-terminal-note')?.textContent.includes('区县')`, '天山区末级提示')
  record('新疆→乌鲁木齐→天山区', Boolean(terminal), (await breadcrumb(command)).join(' / '))

  const dateChange = await evaluate(command, `(() => {
    const select = document.querySelectorAll('.selection-controls select')[2]
    if (!select || select.options.length < 2) return null
    const next = select.options[select.options.length - 1].value
    if (next === select.value) return null
    select.value = next
    select.dispatchEvent(new Event('change', { bubbles: true }))
    return next
  })()`)
  if (dateChange) {
    const dateVisible = await waitFor(command, `document.querySelector('.fixed-date')?.textContent.includes(${JSON.stringify(dateChange)})`, '固定日期联动')
    record('切换固定日期更新面板', Boolean(dateVisible), String(dateChange))
  } else {
    record('切换固定日期更新面板', false, '当前区域没有第二个可选观测日期，未验证变化')
  }

  const beforeDrag = (await breadcrumb(command)).join('/')
  await evaluate(command, `(() => {
    const track = document.querySelector('.carousel-track')
    if (!track) return false
    track.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true, clientX: 500, pointerId: 9, button: 0 }))
    track.dispatchEvent(new PointerEvent('pointermove', { bubbles: true, clientX: 380, pointerId: 9, buttons: 1 }))
    track.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, clientX: 380, pointerId: 9 }))
    return true
  })()`)
  await sleep(400)
  const afterDrag = (await breadcrumb(command)).join('/')
  record('拖动不触发钻取', beforeDrag === afterDrag, `${beforeDrag} → ${afterDrag}`)

  const dateCount = await evaluate(command, 'document.querySelectorAll(".selection-controls select")[2]?.options.length || 0')
  record('固定日期控件存在', dateCount > 0, `${dateCount} 个日期选项`)
} finally {
  socket.close()
}

if (checks.some((item) => !item.passed)) process.exitCode = 1
