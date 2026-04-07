import { test as setup, expect } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

const authFile = '.auth/admin.json'

setup('authenticate as admin', async ({ page }) => {
  const user = process.env.E2E_USER ?? 'admin'
  const pass = process.env.E2E_PASS ?? 'admin'

  await page.goto('/gui/login')

  await page.fill('[data-testid="input-username"]', user)
  await page.fill('[data-testid="input-password"]', pass)
  await page.click('[data-testid="btn-login"]')

  // Wait for redirect away from login
  await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10_000 })

  // Persist storage state (localStorage with JWT token)
  fs.mkdirSync(path.dirname(authFile), { recursive: true })
  await page.context().storageState({ path: authFile })
})
