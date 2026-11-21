import { spawn } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  defineBrowserProvider, parseKeyDef, resolveScreenshotPath,
  assertBrowserApiWrite, assertBrowserFileAccess,
} from '@vitest/browser'

function startBridge() {
  const proc = spawn('fastcdp-vitest-bridge', [], { stdio: ['pipe', 'pipe', 'inherit'] })
  const url = new Promise((resolve, reject) => {
    let buf = ''
    proc.once('error', err => reject(new Error(`Failed to start fastcdp-vitest-bridge: ${err.message}`)))
    proc.once('exit', (code, signal) => reject(new Error(`fastcdp-vitest-bridge exited before ready (code=${code}, signal=${signal})`)))
    proc.stdout.setEncoding('utf8')
    proc.stdout.on('data', chunk => {
      buf += chunk
      const nl = buf.indexOf('\n')
      if (nl !== -1) resolve(buf.slice(0, nl).trim())
    })
  })
  return { proc, url }
}

function checkOptions(options = {}, allowed = []) {
  for (const key of Object.keys(options)) {
    if (!['timeout', 'strict', ...allowed].includes(key)) throw new Error(`fastcdp does not support option "${key}"`)
  }
}

export function fastcdp() {
  return defineBrowserProvider({
    name: 'fastcdp', supportedBrowser: ['chromium'],
    providerFactory(project) { return new FastCDPProvider(project) },
  })
}

class FastCDPProvider {
  name = 'fastcdp'
  supportsParallelism = false
  initScripts = [fileURLToPath(new URL('./vitest-locators.mjs', import.meta.url))]
  pending = new Map()
  id = 0
  constructor(project) {
    this.ready = this._connect()
    this.ready.catch(() => {})
    const command = (action, payload) => async (context, ...args) => this.call(action, {
      sessionId: context.sessionId, testPath: context.testPath, ...payload(...args),
    })
    const commands = {
      click: command('click', (target, options) => { checkOptions(options); return { target, options } }),
      hover: command('hover', (target, options) => { checkOptions(options); return { target, options } }),
      clear: command('clear', (target, options) => { checkOptions(options); return { target, options } }),
      fill: command('fill', (target, text, options) => { checkOptions(options); return { target, text, options } }),
      type: command('type', (target, text, options) => {
        checkOptions(options, ['skipClick', 'skipAutoClose', 'unreleased'])
        return { target, actions: parseKeyDef(text), options }
      }),
      keyboard: command('keyboard', (text, state) => ({ actions: parseKeyDef(text), unreleased: state.unreleased })),
      cleanup: command('cleanup', state => ({ unreleased: state.unreleased })),
      tab: command('tab', options => { checkOptions(options, ['shift']); return options }),
      viewport: command('viewport', options => options),
      takeScreenshot: async (context, name, options = {}) => {
        checkOptions(options, ['element', 'target', 'path', 'save', 'base64'])
        const path = resolveScreenshotPath(context.testPath, name, context.project.config, options.path)
        const base64 = await this.call('screenshot', {
          testPath: context.testPath, target: options.element, options: { timeout: options.timeout },
        })
        const buffer = Buffer.from(base64, 'base64')
        if (options.save) {
          assertBrowserApiWrite(context.project, path)
          assertBrowserFileAccess(context.project, path)
          await mkdir(dirname(path), { recursive: true })
          await writeFile(path, buffer)
        }
        return { buffer, path }
      },
    }
    for (const [name, fn] of Object.entries(commands)) project.browser.registerCommand(`__vitest_${name}`, fn)
  }
  async _connect() {
    let url = process.env.FASTCDP_VITEST
    if (!url) {
      const bridge = startBridge()
      this.bridge = bridge.proc
      url = await bridge.url
    }
    const ws = new WebSocket(url)
    this.ws = ws
    ws.addEventListener('message', ({ data }) => {
      const message = JSON.parse(data)
      const pending = this.pending.get(message.id)
      if (!pending) return
      this.pending.delete(message.id)
      if (message.error) pending.reject(new Error(message.error))
      else pending.resolve(message.result)
    })
    ws.addEventListener('close', () => {
      for (const pending of this.pending.values()) pending.reject(new Error('fastcdp connection closed'))
      this.pending.clear()
    })
    await new Promise((resolve, reject) => {
      ws.addEventListener('open', resolve, { once: true })
      ws.addEventListener('error', () => reject(new Error(`Failed to connect to fastcdp bridge at ${url}`)), { once: true })
    })
  }
  async call(action, payload) {
    await this.ready
    const id = ++this.id
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      this.ws.send(JSON.stringify({ id, action, ...payload }))
    })
  }
  getCommandsContext() { return {} }
  async openPage(sessionId, url) { await this.call('open', { sessionId, url }) }
  async close() {
    try { await this.ready } catch {}
    if (this.ws && this.ws.readyState < WebSocket.CLOSING) this.ws.close()
    if (this.bridge) {
      const proc = this.bridge
      this.bridge = null
      proc.stdin.end()
      if (proc.exitCode === null && proc.signalCode === null) {
        proc.kill('SIGTERM')
        await new Promise(resolve => {
          const timer = setTimeout(() => { proc.kill('SIGKILL'); resolve() }, 3000)
          timer.unref()
          proc.once('exit', () => { clearTimeout(timer); resolve() })
        })
      }
    }
  }
}
