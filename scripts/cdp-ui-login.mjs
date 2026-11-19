/* End-to-end browser check of the real login form (no API shortcuts). */
const endpoint = process.env.CDP_ENDPOINT ?? 'http://127.0.0.1:9226'
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
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false })
await send('Page.navigate', { url: 'http://127.0.0.1:5173/login' })
await wait(3500)

const filled = await send('Runtime.evaluate', {
  expression: `(() => {
    const email = document.querySelector('#email');
    const password = document.querySelector('#password');
    if (!email || !password) return { ok: false, reason: 'fields missing' };
    const set = (el, value) => {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(el, value);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    };
    set(email, 'resident@sara.ir');
    set(password, 'Resident12345!');
    document.querySelector('form').requestSubmit();
    return { ok: true };
  })()`,
  returnByValue: true,
})
console.log('fill:', JSON.stringify(filled.result.value))
await wait(5000)

const state = await send('Runtime.evaluate', {
  expression: `({
    url: location.pathname,
    heading: document.querySelector('h1')?.innerText ?? null,
    alert: document.querySelector('[role="alert"]')?.innerText ?? null,
    hasDashboard: Boolean(document.querySelector('main#main-content'))
  })`,
  returnByValue: true,
})
console.log('state:', JSON.stringify(state.result.value, null, 2))
socket.close()
