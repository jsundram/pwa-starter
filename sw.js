// Service worker: offline shell + cache-busting.
//
// THE ONE RULE: bump V whenever you change a precached SHELL file. A new V is what evicts the
// stale cache on activate — forget the bump and your fix ships to the repo but never to anyone's
// installed home-screen copy (iOS caches the SW aggressively). scripts/sw-lint.py guards this,
// and app.js surfaces a "tap to update" tag so a stuck phone is fixable in one tap.
//
// Strategy, by what the file IS rather than where it lives:
//   HTML/JS + navigations → network-first (a push is visible on the next reload without waiting
//     for a SW swap; falls back to cache offline)
//   JSON → stale-while-revalidate (it's data: paint from cache now, refresh behind it)
//   images and everything else → cache-first for speed; a V bump is what refreshes them
//   cross-origin data (your APIs) → straight through, never cached here
// Every cache write goes through cachePut(), which refuses to store an HTTP error.

const V = "app-v4";   // <-- BUMP ON EVERY SHELL CHANGE
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

// Cache-write gate. A fetch() only REJECTS on a network failure — a 404 or a
// mid-deploy 502 arrives as a RESOLVED response, so an ungated c.put() happily
// overwrites a good cached copy with an error body, which then survives as the
// offline fallback until the next V bump. (Same principle as data.js refusing to
// cache an empty 200: a 200-shaped response isn't necessarily a good one.)
//
// Opaque responses are the exception that must NOT be gated: a cross-origin
// no-cors fetch (a webfont, a CDN script) always reports ok:false and status:0
// no matter how it went, so `resp.ok` alone would silently disable font caching
// and break offline type. They're allowed through explicitly — the cost is that
// a failed opaque request is indistinguishable from a good one, so a bad one can
// still be cached. That's inherent to no-cors, not something the gate can fix.
function cachePut(req, resp) {
  if (!resp.ok && resp.type !== "opaque") return;
  const copy = resp.clone();
  caches.open(V).then(c => c.put(req, copy));
}

self.addEventListener("fetch", e => {
  const u = new URL(e.request.url);

  // Google Fonts (if used): cache-first so the type survives offline.
  if (u.hostname === "fonts.googleapis.com" || u.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.open(V).then(c =>
      c.match(e.request).then(r => r || fetch(e.request).then(resp => { cachePut(e.request, resp); return resp; }))));
    return;
  }

  // Cross-origin data (your APIs, third-party JSON): straight to network, don't touch the cache.
  if (u.origin !== location.origin) return;

  // The SW must never intercept or cache its own script: checkVer() probes
  // ./sw.js?_=<ts> to read the live version, and caching those probes both bloats
  // the cache (a new dead entry per resume) and — if .js is ever made cache-first
  // with ignoreSearch — serves a stale version back, wedging the "tap to update" tag.
  if (u.pathname.endsWith("/sw.js")) return;

  // Same-origin JSON → stale-while-revalidate: serve the cached copy IMMEDIATELY,
  // refresh behind it. This is the SW twin of data.js's cache-first paint. JSON here
  // is DATA (a committed dataset, the manifest), and network-first made every cold
  // start block on a round trip for it even with a perfectly good cached copy — the
  // exact stall that made haydn-info-card and quartets.boccherini.org wait on 100 KB+
  // of static JSON before first paint. The tradeoff is real but small: a JSON change
  // lands one load later than an HTML/JS change. If some .json of yours is genuinely
  // code-like and must be live, move it into the `live` test below.
  if (/\.json$/.test(u.pathname)) {
    e.respondWith(caches.match(e.request).then(cached => {
      const net = fetch(e.request).then(resp => { cachePut(e.request, resp); return resp; });
      e.waitUntil(net.catch(() => {}));   // keep the SW alive for the refresh; offline is fine
      return cached || net;               // no cached copy (first run) → wait for the network
    }));
    return;
  }

  // Same-origin: HTML/JS + navigations → network-first; other assets (images) → cache-first.
  const live = e.request.mode === "navigate" || u.pathname.endsWith("/") || /\.(html|js)$/.test(u.pathname);
  if (live) {
    e.respondWith(
      fetch(e.request).then(resp => {
        cachePut(e.request, resp);
        // A 4xx/5xx is a resolved fetch, so .catch() below never sees it — serve
        // the good cached copy instead of handing the app an error page.
        if (!resp.ok) return caches.match(e.request).then(r => r || resp);
        return resp;
      }).catch(() => caches.match(e.request).then(r => r || caches.match("./index.html")))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
        cachePut(e.request, resp);
        return resp;
      }))
    );
  }
});
