const endpoint = process.env.CDP_ENDPOINT ?? 'http://127.0.0.1:9223'
const target = process.env.CDP_URL ?? 'http://127.0.0.1:5173/login'
const expression =
  process.env.CDP_EXPR ??
  `({
    innerWidth: window.innerWidth,
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    shell: document.querySelector('.auth-shell')?.getBoundingClientRect().toJSON(),
    main: document.querySelector('main')?.getBoundingClientRect().toJSON(),
    card: document.querySelector('.auth-card')?.getBoundingClientRect().toJSON(),
    grid: getComputedStyle(document.querySelector('.auth-shell')).gridTemplateColumns,
    mainMinWidth: getComputedStyle(document.querySelector('main')).minWidth,
    bodyOverflowX: getComputedStyle(document.body).overflowX
  })`

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
await send('Runtime.enable')
await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', {
  width: 390,
  height: 844,
  deviceScaleFactor: 1,
  mobile: true,
})
await send('Page.navigate', { url: target })
await new Promise((resolve) => setTimeout(resolve, 5000))
const result = await send('Runtime.evaluate', { expression, returnByValue: true })
console.log(JSON.stringify(result.result.value, null, 2))
socket.close()
