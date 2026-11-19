import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname } from 'node:path'

const endpoint = process.env.CDP_ENDPOINT ?? 'http://127.0.0.1:9224'
const out = process.env.SHOT_OUT ?? 'docs/screenshots/shot.png'
const width = Number(process.env.SHOT_WIDTH ?? 1440)
const height = Number(process.env.SHOT_HEIGHT ?? 1000)
const login = process.env.SHOT_LOGIN === '1'
const target = process.env.SHOT_URL ?? 'http://127.0.0.1:5173/login'

const tabs = await (await fetch(`${endpoint}/json`)).json()
const tab = tabs.find((item) => item.type === 'page')
if (!tab) throw new Error('No page target')

const socket = new WebSocket(tab.webSocketDebuggerUrl)
const pending = new Map()
let nextId = 0
socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data)
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id)
    pending.delete(message.id)
    message.error ? reject(new Error(message.error.message)) : resolve(message.result)
  }
})
await new Promise((resolve, reject) => {
  socket.addEventListener('open', resolve, { once: true })
  socket.addEventListener('error', reject, { once: true })
})
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++nextId
    pending.set(id, { resolve, reject })
    socket.send(JSON.stringify({ id, method, params }))
  })
}
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

await send('Runtime.enable')
await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', {
  width,
  height,
  deviceScaleFactor: 1,
  mobile: width < 600,
})

if (login) {
  await send('Page.navigate', { url: 'http://127.0.0.1:5173/login' })
  await wait(3000)
  const result = await send('Runtime.evaluate', {
    expression: `fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email: 'resident@sara.ir', password: 'Resident12345!' })
    }).then(async (response) => ({ status: response.status, body: await response.text() }))`,
    awaitPromise: true,
    returnByValue: true,
  })
  console.log('login:', JSON.stringify(result.result.value).slice(0, 200))
  await wait(1000)
}

await send('Page.navigate', { url: target })
await wait(5000)

const screenshot = await send('Page.captureScreenshot', {
  format: 'png',
  fromSurface: true,
  captureBeyondViewport: false,
})
mkdirSync(dirname(out), { recursive: true })
writeFileSync(out, Buffer.from(screenshot.data, 'base64'))
console.log(`saved ${out}`)
socket.close()
