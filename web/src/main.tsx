import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ErrorBoundary } from './app/components/ErrorBoundary.tsx'
import { applyTokens } from './app/tokens'

applyTokens()

// The layout needs container queries and :has() (Chrome, Edge and Firefox of 2023 on, Safari
// 16 on). An older browser gets a line saying so above the app, which may not lay out well.
if (typeof CSS !== 'undefined' && !(CSS.supports('container-type: inline-size') && CSS.supports('selector(:has(a))'))) {
  const note = document.createElement('p')
  note.className = 'browser-note'
  note.textContent = 'This browser is too old for SoSample\'s layout. Use a current Chrome, Edge, Firefox or Safari (16 or later).'
  document.body.prepend(note)
}

// Offline use: the built site registers its service worker (src/offline/sw.js), which keeps the
// app's own files so it opens without a network. The development server has none.
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {
      // Best effort: without it the app still works online.
    })
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
