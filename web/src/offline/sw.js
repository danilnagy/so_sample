/*
 * The service worker that lets SoSample open without a network. It is written into the build
 * by the offline plugin in vite.config.ts, which replaces the two placeholders below with the
 * build's file list and a version derived from it; in development there is no service worker.
 *
 * On install it stores every file of the build (the page, scripts, styles, icons, and the
 * bundled kits and projects) in a cache named after the version. Pages are fetched from the
 * network first, so an online visit always gets the newest page, and from the cache when
 * offline; hashed files, which never change, come from the cache first. A new version
 * installs beside the old one and takes over once every tab of the old one has closed, so a
 * page never loads files from two versions; its activation removes the older caches.
 *
 * Only the build's own files are cached. The user's projects, samples and kits live in
 * IndexedDB, which the service worker never touches.
 */

const VERSION = '__VERSION__';
const FILES = __FILES__;
const CACHE = `sosample-${VERSION}`;
const scope = new URL(self.registration.scope);
const url = (path) => new URL(path, scope).href;
const PAGE = url('index.html');
// A server's Vary header (Vary: Origin on module scripts) would make a stored file miss when the
// page asks for it with different headers; every cached file is content-hashed or the page, so
// matching by address alone is safe.
const MATCH = { ignoreVary: true };

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES.map(url))));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key.startsWith('sosample-') && key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== scope.origin) return;
  if (request.mode === 'navigate') {
    // Any page of the app (/, /guide) is the one page: the network's when online, the cached one when not.
    event.respondWith(
      fetch(request).catch(() => caches.open(CACHE).then((cache) => cache.match(PAGE, MATCH)).then((page) => page ?? Response.error())),
    );
    return;
  }
  event.respondWith(caches.open(CACHE).then((cache) => cache.match(request, MATCH).then((hit) => hit ?? fetch(request))));
});
