import {
  Locator, selectorEngine, getByRoleSelector, getByLabelSelector, getByTextSelector,
  getByTestIdSelector, getByAltTextSelector, getByPlaceholderSelector, getByTitleSelector,
} from '@vitest/browser/locators'
import { page, server } from 'vitest/browser'
import { __INTERNAL } from 'vitest/internal/browser'

class FastCDPLocator extends Locator {
  constructor(selector, container) { super(); this.selector = selector; this._container = container }
  elements() { return selectorEngine.querySelectorAll(selectorEngine.parseSelector(this.selector), document) }
  locator(selector) { return new FastCDPLocator(`${this.selector} >> ${selector}`, this._container) }
  elementLocator(element) { return new FastCDPLocator(selectorEngine.generateSelectorSimple(element), element) }
}

page.extend({
  getByRole: (role, options) => new FastCDPLocator(getByRoleSelector(role, options)),
  getByLabelText: (text, options) => new FastCDPLocator(getByLabelSelector(text, options)),
  getByText: (text, options) => new FastCDPLocator(getByTextSelector(text, options)),
  getByAltText: (text, options) => new FastCDPLocator(getByAltTextSelector(text, options)),
  getByPlaceholder: (text, options) => new FastCDPLocator(getByPlaceholderSelector(text, options)),
  getByTitle: (text, options) => new FastCDPLocator(getByTitleSelector(text, options)),
  getByTestId: id => new FastCDPLocator(getByTestIdSelector(server.config.browser.locators.testIdAttribute, id)),
  elementLocator: element => new FastCDPLocator(selectorEngine.generateSelectorSimple(element), element),
})
__INTERNAL._createLocator = selector => new FastCDPLocator(selector)
globalThis.__fastcdp_find = (selector, options) => new FastCDPLocator(selector).findElement(options)
