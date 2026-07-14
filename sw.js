// Service worker: offline shell + cache-busting.
//
// THE ONE RULE: bump V whenever you change a precached SHELL file. A new V is what evicts the
// stale cache on activate — forget the bump and your fix ships to the repo but never to anyone's
// installed home-screen copy (iOS caches the SW aggressively). scripts/sw-lint.py guards this,
// and app.js surfaces a "tap to update" tag so a stuck phone is fixable in one tap.
//
// Strategy: shell HTML/JS/JSON is network-first (a push is visible on the next reload without
// waiting for a SW swap; falls back to cache offline); big static assets (images) stay cache-first
// for speed — a V bump is what refreshes them. Cross-origin data (your APIs) passes straight through.

const V = "app-v2";   // <-- BUMP ON EVERY SHELL CHANGE
const SHELL = [
  "./", "./index.html", "./styles.css",
  "./app.js", "./theme.js", "./data.js", "./pullToRefresh.js", "./ping.js", "./manifest.json",
  "./assets/icon.svg", "./assets/icon-180.png", "./assets/icon-192.png", "./assets/icon-512.png",
  "./usage/", "./usage/index.html", "./usage/crunch.js",
  // ...add every file the app needs offline: more pages, data JSON, self-hosted fonts.
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(V).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== V).map(k => caches.delete(k))))   // evict old versions
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);

  // Google Fonts (if used): cache-first so the type survives offline.
  if (u.hostname === "fonts.googleapis.com" || u.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(V).then(c =>
      c.match(e.request).then(r => r || fetch(e.request).then(resp => { c.put(e.request, resp.clone()); return resp; }))));
    return;
  }

  // Cross-origin data (your APIs, third-party JSON): straight to network, don't touch the cache.
  if (u.origin !== location.origin) return;

  // Same-origin: HTML/JS/JSON + navigations → network-first; other assets (images) → cache-first.
  const live = e.request.mode === "navigate" || u.pathname.endsWith("/") || /\.(html|js|json)$/.test(u.pathname);
  if (live) {
    e.respondWith(
      fetch(e.request).then(resp => {
        const copy = resp.clone();
        caches.open(V).then(c => c.put(e.request, copy));
        return resp;
      }).catch(() => caches.match(e.request).then(r => r || caches.match("./index.html")))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
        const copy = resp.clone();
        caches.open(V).then(c => c.put(e.request, copy));
        return resp;
      }))
    );
  }
});
