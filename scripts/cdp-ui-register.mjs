/* End-to-end browser check of the registration form. */
const endpoint = process.env.CDP_ENDPOINT ?? 'http://127.0.0.1:9227'
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
await send('Page.navigate', { url: 'http://127.0.0.1:5173/register' })
await wait(3500)

const filled = await send('Runtime.evaluate', {
  expression: `(() => {
    const email = 'ui.tester.' + Date.now() + '@sara.ir';
    const set = (selector, value) => {
      const el = document.querySelector(selector);
      if (!el) throw new Error('missing ' + selector);
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
      setter.call(el, value);
      el.dispatchEvent(new Event('input', { bubbles: true }));
    };
    set('#full_name', 'کاربر آزمایشی');
    set('#email', email);
    set('#phone', '09121234567');
    set('#password', 'NewResident12345!');
    set('#confirmPassword', 'NewResident12345!');
    const terms = document.querySelector('input[type=checkbox]');
    if (!terms.checked) terms.click();
    document.querySelector('form').requestSubmit();
    return { email };
  })()`,
  returnByValue: true,
})
console.log('fill:', JSON.stringify(filled, null, 2).slice(0, 1500))
await wait(6000)

const state = await send('Runtime.evaluate', {
  expression: `({
    url: location.pathname,
    heading: document.querySelector('h1')?.innerText ?? null,
    alert: document.querySelector('[role="alert"]')?.innerText ?? null,
    errors: [...document.querySelectorAll('.field-error')].map((node) => node.innerText)
  })`,
  returnByValue: true,
})
console.log('state:', JSON.stringify(state.result.value, null, 2))
socket.close()
