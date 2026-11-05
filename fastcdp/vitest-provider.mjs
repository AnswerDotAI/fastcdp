import { createRequire } from 'node:module'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { mkdir, writeFile } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { pathToFileURL } from 'node:url'

const require = createRequire(join(process.cwd(), 'package.json'))
const { defineBrowserProvider, parseKeyDef, resolveScreenshotPath, assertBrowserApiWrite, assertBrowserFileAccess } =
  await import(pathToFileURL(require.resolve('@vitest/browser')))

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
  pending = new Map()
  id = 0
  constructor(project) {
    if (!process.env.FASTCDP_VITEST) throw new Error('Run these tests with Python fastcdp.vitest.Vitest')
    const script = join(project.config.root, '.vitest/fastcdp/locators.mjs')
    mkdirSync(dirname(script), { recursive: true })
    const source = readFileSync(new URL('./vitest-locators.mjs', import.meta.url), 'utf8')
      .replace("'@vitest/browser/locators'", JSON.stringify(require.resolve('@vitest/browser/locators')))
    writeFileSync(script, source)
    this.initScripts = [script]
    this.ws = new WebSocket(process.env.FASTCDP_VITEST)
    this.ready = new Promise((resolve, reject) => {
      this.ws.addEventListener('open', resolve, { once: true })
      this.ws.addEventListener('error', reject, { once: true })
    })
    this.ws.addEventListener('message', ({ data }) => {
      const message = JSON.parse(data)
      const pending = this.pending.get(message.id)
      if (!pending) return
      this.pending.delete(message.id)
      if (message.error) pending.reject(new Error(message.error))
      else pending.resolve(message.result)
    })
    this.ws.addEventListener('close', () => {
      for (const pending of this.pending.values()) pending.reject(new Error('fastcdp connection closed'))
      this.pending.clear()
    })
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
  async close() { await this.ready; this.ws.close() }
}
