import { createRequire } from 'node:module'
import { writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'

const [root, report, ...filters] = process.argv.slice(2)
const require = createRequire(join(root, 'package.json'))
const { createVitest } = await import(pathToFileURL(require.resolve('vitest/node')))
const vitest = await createVitest({ root, watch: false })
try {
  const { testModules, unhandledErrors } = await vitest.start(filters)
  const modules = testModules.map(module => ({
    moduleId: module.moduleId, state: module.state(), errors: module.errors(),
    tests: [...module.children.allTests()].map(test => ({
      name: test.fullName, ...test.result(), diagnostic: test.diagnostic(),
    })),
  }))
  await writeFile(report, JSON.stringify({
    success: testModules.every(module => module.ok()) && !unhandledErrors.length,
    testModules: modules, unhandledErrors,
  }))
} finally { await vitest.close() }
