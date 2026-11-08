import { expect, test } from 'vitest'
import { page, userEvent } from 'vitest/browser'

test('native typing, shortcuts, focus and click', async ({ onTestFinished }) => {
  document.body.innerHTML = '<label>Code<textarea></textarea></label><button>Run</button><output></output>'
  const events = []
  const input = document.querySelector('textarea')
  const button = document.querySelector('button')
  const controller = new AbortController()
  onTestFinished(() => controller.abort())
  for (const type of ['input', 'keydown', 'click']) {
    document.addEventListener(type, event => events.push({ type, trusted: event.isTrusted }), { signal: controller.signal })
  }
  button.onclick = () => { document.querySelector('output').textContent = input.value }
  const code = page.getByRole('textbox', { name: 'Code' })
  await code.fill('original')
  await userEvent.type(code, ' text\nnext')
  await expect.element(code).toHaveValue('original text\nnext')
  await userEvent.keyboard(navigator.platform.includes('Mac') ? '{Meta>}a{/Meta}' : '{Control>}a{/Control}')
  await userEvent.type(code, '41 + 1')
  await userEvent.tab()
  await expect.element(page.getByRole('button', { name: 'Run' })).toHaveFocus()
  await userEvent.keyboard('{Enter}')
  await expect.element(page.getByRole('status')).toHaveTextContent('41 + 1')
  await userEvent.tab({ shift: true })
  await expect.element(code).toHaveFocus()
  await code.clear()
  await code.fill('42')
  button.style.cssText = 'display: block; margin-top: 100vh'
  window.addEventListener('scroll', () => {
    const replacement = button.cloneNode(true)
    replacement.onclick = button.onclick
    button.replaceWith(replacement)
  }, { once: true })
  await page.getByRole('button', { name: 'Run' }).click()
  await expect.element(page.getByRole('status')).toHaveTextContent('42')
  expect(events.length).toBeGreaterThan(5)
  expect(events.every(event => event.trusted)).toBe(true)
})

test.skipIf(!import.meta.env.FASTCDP_TEST_FAILURE)('failure retains its rendered page', () => {
  document.body.innerHTML = '<h1>Inspect this failure</h1>'
  expect(document.querySelector('h1').textContent).toBe('Expected heading')
})
