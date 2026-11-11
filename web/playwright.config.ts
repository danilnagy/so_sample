import { defineConfig } from '@playwright/test';

/**
 * Visual tests: the app in the system Chrome at phone widths, checked for layout
 * (nothing wider than the screen) and against screenshot baselines. Baselines were made on
 * macOS; on another platform run `npm run test:visual:update` first and read the diffs.
 */
export default defineConfig({
  testDir: 'e2e',
  testMatch: '**/*.visual.ts',
  snapshotPathTemplate: '{testDir}/__screenshots__/{projectName}/{arg}{ext}',
  fullyParallel: true,
  retries: 0,
  reporter: [['list']],
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01 } },
  use: {
    channel: 'chrome',
    baseURL: 'http://localhost:4173',
    deviceScaleFactor: 1,
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'phone-320', use: { viewport: { width: 320, height: 568 } } },
    { name: 'phone-390', use: { viewport: { width: 390, height: 844 } } },
  ],
  webServer: {
    command: 'npm run dev -- --port 4173 --strictPort',
    url: 'http://localhost:4173',
    reuseExistingServer: true,
    timeout: 60000,
  },
});
