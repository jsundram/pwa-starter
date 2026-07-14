// Data: stale-while-revalidate with a network timeout — the concrete version of
// the SW's rule "let cross-origin data pass straight through; cache it in the
// APP, not the service worker."
//
// One pull can end three ways:
//   - network wins  → FRESH data, cache written for next time
//   - network times out or errors, cache exists → last-known data, flagged STALE
//   - network fails AND no cache (first run offline) → throws; caller shows an error
//
// Subtleties ironed out here so nobody re-derives them:
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

  function readCache(key) {
    try {
      const raw = localStorage.getItem(cacheKey(key));
      if (raw == null) return null;
      return { data: JSON.parse(raw), ts: parseInt(localStorage.getItem(stampKey(key)) || "0", 10) };
    } catch { return null; }
  }

  function writeCache(key, data) {
    try {
      localStorage.setItem(cacheKey(key), JSON.stringify(data));
      localStorage.setItem(stampKey(key), String(Date.now()));
    } catch { /* quota/full: skip caching, still return the fresh data */ }
  }

  // Returns { data, source:"fresh"|"cache", stale:boolean, ageMs:number }.
  async function load(url, opts) {
    opts = opts || {};
    const key = opts.key || url;
    const timeoutMs = opts.timeoutMs || DEFAULT_TIMEOUT;
    const cached = readCache(key);

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
      writeCache(key, data);
      return { data, source: "fresh", stale: false, ageMs: 0 };
    } catch (err) {
      clearTimeout(timer);
      if (cached) return { data: cached.data, source: "cache", stale: true, ageMs: Date.now() - cached.ts };
      throw err;                               // first run, offline, nothing cached — let the caller handle it
    }
  }

  // Age of the cached copy in ms (Infinity if never fetched). Lets the poll ask
  // "is this stale enough to re-fetch?" without touching the network.
  function ageMs(key) {
    const c = readCache(key);
    return c ? Date.now() - c.ts : Infinity;
  }

  return { load, ageMs };
})();
