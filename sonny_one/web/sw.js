/* Cache only this demo's public static shell, never API traffic or user data. */
'use strict';
const CACHE = 'sonny-one-shell-v1';
const SHELL = ['/', '/assets/styles.css', '/assets/app.js', '/assets/icon.svg', '/assets/manifest.webmanifest'];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL)));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('sonny-one-shell-') && key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.search || !SHELL.includes(url.pathname)) return;
  event.respondWith(fetch(event.request).catch(() => caches.open(CACHE).then(cache => cache.match(url.pathname)).then(cached => cached || Response.error())));
});
