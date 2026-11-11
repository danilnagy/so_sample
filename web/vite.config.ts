/// <reference types="vitest/config" />
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The bundled kits and projects: the synthesized set in src/presets, or, with `--mode tr`
// (npm run dev:tr), the TR-sample set in presets-tr, built locally from a sample pack
// (npm run presets -- --pack "<folder>"). That audio may not be redistributed, so the TR
// mode serves the app locally and refuses to build a site.
// https://vite.dev/config/
export default defineConfig(({ mode, command }) => {
  const tr = mode === 'tr'
  const presets = resolve(__dirname, tr ? 'presets-tr' : 'src/presets')
  if (tr && command === 'build') throw new Error('The TR presets are for local use only: build without --mode tr.')
  if (tr && !existsSync(resolve(presets, 'index.json'))) throw new Error('No web/presets-tr: run npm run presets -- --pack "<TR pack folder>" first.')
  return {
    plugins: [react()],
    resolve: { alias: { '@presets': presets } },
    test: { include: ['src/**/*.test.ts'], environment: 'node', testTimeout: 120000 },
  }
})
