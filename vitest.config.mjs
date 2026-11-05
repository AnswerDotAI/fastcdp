import { defineConfig } from 'vitest/config'
import { fastcdp } from './fastcdp/vitest-provider.mjs'

export default defineConfig({
  test: {
    include: ['tests/vitest.test.js'],
    env: { FASTCDP_TEST_FAILURE: process.env.FASTCDP_TEST_FAILURE || '' },
    browser: {
      enabled: true,
      provider: fastcdp(),
      instances: [{ browser: 'chromium' }],
      ui: false,
      screenshotDirectory: '.vitest/screenshots',
    },
  },
})
