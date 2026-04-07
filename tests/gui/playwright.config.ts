import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: '.',
  fullyParallel: false,
  retries: 1,
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:8080',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'admin-setup',
      testMatch: '**/auth.setup.ts',
    },
    {
      name: 'admin',
      testMatch: '**/admin/**/*.spec.ts',
      dependencies: ['admin-setup'],
      use: { storageState: '.auth/admin.json' },
    },
    {
      name: 'visu',
      testMatch: '**/visu/**/*.spec.ts',
      dependencies: ['admin-setup'],
      use: { storageState: '.auth/admin.json' },
    },
  ],
})
