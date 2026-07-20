// Data: stale-while-revalidate with a network timeout — the concrete version of
// the SW's rule "let cross-origin data pass straight through; cache it in the
// APP, not the service worker."
//
// TWO SHAPES, pick per app:
//   load()                  — network-first. One pull ends three ways:
//                               network wins  → FRESH data, cache written
//                               timeout/error + cache → last-known data, flagged STALE
//                               timeout/error + no cache → throws; caller shows an error
//   peek() + revalidate()   — CACHE-FIRST. Paint the cached copy synchronously at
//                             boot (no await, no placeholder), then revalidate in
//                             the background and repaint only if `changed`.
// Cache-first is the better default once an app has real data: a returning visitor
// on a flaky connection sees real content immediately instead of staring at the
// placeholder for up to the full timeout. app.js's render() shows the pattern.
//
// Subtleties ironed out here so nobody re-derives them:
//   - NEVER cache an empty/degenerate 200. A transient server hiccup or a
//     momentarily-empty sheet returns a valid `[]`, and caching it poisons the
//     offline fallback — under cache-first it's worse than stale, it's a WEDGE:
//     peek() serves the empty payload, paint() throws, and reloading re-reads the
//     same poisoned cache forever. "Empty" is app-specific, so it's a predicate:
//     pass opts.valid; the default rejects null/undefined and [].
//   - clearTimeout() the moment the network wins, so the abort timer can't fire
//     mid-`.json()` and turn a good response into a cache fallback.
//   - AbortController actually cancels the in-flight fetch on timeout — it doesn't
//     keep running to late-write the cache after we've already served stale.
//   - a quota/full localStorage write is swallowed: you still get the fresh data,
//     you just don't cache it. (localStorage is sync + ~5MB + iOS-evictable — for
//     big payloads reach for the Cache API or IndexedDB instead.)
//   - ageMs(key) answers "how stale?" with NO network hit, so the foreground poll
//     can decide whether to even try.
//
// Loaded as a classic script before app.js; exposes a global `Data`.

window.Data = (function () {
  const DEFAULT_TIMEOUT = 5000;                 // quartet-log's ~5s; tune per app
  const cacheKey = k => "app-data:" + k;        // grep-able key prefix
  const stampKey = k => "app-data:" + k + ":ts";

  // The floor, not the ceiling: override with opts.valid when "empty" means
  // something else for your payload ({} , {items:[]}, a missing field, …).
  const DEFAULT_VALID = d => d != null && !(Array.isArray(d) && d.length === 0);

  function readRaw(key) {
    try { return localStorage.getItem(cacheKey(key)); } catch { return null; }
  }

  function readCache(key) {
    const raw = readRaw(key);
    if (raw == null) return null;
    try {
      return { data: JSON.parse(raw), ts: parseInt(localStorage.getItem(stampKey(key)) || "0", 10) };
    } catch { return null; }                   // corrupt entry: treat as absent
  }

  function writeCache(key, data) {
    try {
      localStorage.setItem(cacheKey(key), JSON.stringify(data));
      localStorage.setItem(stampKey(key), String(Date.now()));
    } catch { /* quota/full: skip caching, still return the fresh data */ }
  }

  // Network-only pull: fetch → timeout race → validity gate → cache write.
  // Returns { data, changed }. Throws on timeout, HTTP error, bad JSON, or an
  // invalid payload — every one of which must leave the existing cache untouched.
  async function fetchFresh(url, opts) {
    const key = opts.key || url;
    const timeoutMs = opts.timeoutMs || DEFAULT_TIMEOUT;
    const valid = opts.valid || DEFAULT_VALID;
    const before = readRaw(key);               // snapshot BEFORE the write, to diff against

    const ctrl = new AbortController();
    let timer;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => { ctrl.abort(); reject(new Error("timeout")); }, timeoutMs);
    });

    try {
      const resp = await Promise.race([fetch(url, { signal: ctrl.signal }), timeout]);
      clearTimeout(timer);                     // network won — stop the abort timer BEFORE reading the body
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      if (!valid(data)) throw new Error("empty/invalid payload");   // fall back to cache; don't poison it
      writeCache(key, data);
      return { data, changed: JSON.stringify(data) !== before };
    } finally {
      clearTimeout(timer);
    }
  }

  // Network-first. Returns { data, source:"fresh"|"cache", stale, ageMs, changed }.
  async function load(url, opts) {
    opts = opts || {};
    const key = opts.key || url;
    const cached = readCache(key);
    try {
      const { data, changed } = await fetchFresh(url, opts);
      return { data, source: "fresh", stale: false, ageMs: 0, changed };
    } catch (err) {
      if (cached) return { data: cached.data, source: "cache", stale: true, ageMs: Date.now() - cached.ts, changed: false };
      throw err;                               // first run, offline, nothing cached — let the caller handle it
    }
  }

  // SYNCHRONOUS cached read — the first half of cache-first. Returns
  // { data, source:"cache", stale:true, ageMs } or null if nothing is cached.
  // No network, no await: safe to call and paint from during boot.
  function peek(key) {
    const c = readCache(key);
    return c ? { data: c.data, source: "cache", stale: true, ageMs: Date.now() - c.ts } : null;
  }

  // Background half of cache-first: network-only, writes the cache, and reports
  // whether the payload actually differs from what was cached — so the caller can
  // skip a needless repaint (and the flash that comes with it). Throws like load()
  // does when there's no cache: offline/invalid means "keep showing what you have".
  async function revalidate(url, opts) {
    opts = opts || {};
    const { data, changed } = await fetchFresh(url, opts);
    return { data, source: "fresh", stale: false, ageMs: 0, changed };
  }

  // Age of the cached copy in ms (Infinity if never fetched). Lets the poll ask
  // "is this stale enough to re-fetch?" without touching the network.
  function ageMs(key) {
    const c = readCache(key);
    return c ? Date.now() - c.ts : Infinity;
  }

  return { load, peek, revalidate, ageMs };
})();
