/* Minimal CDP probe: navigate, wait, print console errors and the app DOM. */
const endpoint = process.env.CDP_ENDPOINT ?? 'http://127.0.0.1:9222'
const target = process.env.CDP_URL ?? 'http://127.0.0.1:5173/login'

const tabs = await (await fetch(`${endpoint}/json`)).json()
const tab = tabs.find((item) => item.type === 'page')
if (!tab) throw new Error('No page target found')

const socket = new WebSocket(tab.webSocketDebuggerUrl)
const pending = new Map()
const logs = []
let nextId = 0

socket.addEventListener('message', (event) => {
  const message = JSON.parse(event.data)
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id)
    pending.delete(message.id)
    message.error ? reject(new Error(message.error.message)) : resolve(message.result)
    return
  }
  if (message.method === 'Runtime.exceptionThrown') {
    const details = message.params.exceptionDetails
    logs.push(
      `[exception] ${details.exception?.description ?? details.text} @ ${details.url ?? ''}:${details.lineNumber ?? ''}`,
    )
  }
  if (message.method === 'Log.entryAdded') {
    const entry = message.params.entry
    logs.push(`[${entry.level}] ${entry.text} ${entry.url ?? ''}`)
  }
  if (message.method === 'Runtime.consoleAPICalled') {
    const text = message.params.args.map((arg) => arg.value ?? arg.description ?? '').join(' ')
    logs.push(`[console.${message.params.type}] ${text}`)
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
await send('Log.enable')
await send('Page.enable')
await send('Page.navigate', { url: target })
await new Promise((resolve) => setTimeout(resolve, 6000))

const state = await send('Runtime.evaluate', {
  expression: `({
    url: location.href,
    app: document.getElementById('app')?.innerHTML ?? null,
    bodyText: document.body.innerText?.slice(0, 500) ?? null
  })`,
  returnByValue: true,
})

console.log(JSON.stringify(state.result.value, null, 2))
console.log('--- browser log ---')
console.log(logs.join('\n') || '(empty)')
socket.close()
