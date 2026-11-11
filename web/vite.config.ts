/// <reference types="vitest/config" />
import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'

import react from '@vitejs/plugin-react'
import { type Plugin, defineConfig } from 'vite'

/**
 * Offline use: writes sw.js into the build, the service worker in src/offline/sw.js with the
 * build's file list (every bundled file, the page, and the public icons and manifest) and a
 * version hashed from that list, so a changed build is a new cache. Build only; the
 * development server has no service worker.
 */
function offline(): Plugin {
  return {
    name: 'sosample-offline',
    apply: 'build',
    enforce: 'post',
    generateBundle(_options, bundle) {
      const files = Object.keys(bundle).filter((file) => !file.endsWith('.map'))
      const publicDir = resolve(__dirname, 'public')
      // Netlify's _headers is configuration, not a file the site serves.
      for (const file of readdirSync(publicDir)) if (!file.startsWith('_') && !file.startsWith('.')) files.push(file)
      files.sort()
      const version = createHash('sha256').update(files.join('\n')).digest('hex').slice(0, 12)
      const source = readFileSync(resolve(__dirname, 'src/offline/sw.js'), 'utf8')
        .replace("'__VERSION__'", JSON.stringify(version))
        .replace('__FILES__', JSON.stringify(files))
      this.emitFile({ type: 'asset', fileName: 'sw.js', source })
    },
  }
}

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
    plugins: [react(), offline()],
    resolve: { alias: { '@presets': presets } },
    test: { include: ['src/**/*.test.ts'], environment: 'node', testTimeout: 120000 },
  }
})
