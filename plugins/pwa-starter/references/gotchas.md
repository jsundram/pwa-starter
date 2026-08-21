# Gotchas grab-bag (each cost time once, across these repos)

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

- **Forgot the share card** → the link previews as a blank grey box. Do OG + `make-og.sh` early.
- **Relative or SVG `og:image`** → no preview in iMessage/WhatsApp. Absolute + raster.
- **OG image too big** → some scrapers skip it (grey box). `make-og.sh` fails + `og-lint.py` guards the commit; keep it under ~250 KB.
- **Forgot to bump `V`** → fix ships to the repo, never to phones. `sw-lint.py` guards it.
- **`respondWith()` resolved `undefined` (or rejected)** → WebKit fails the navigation ("Returned
  response is null") and iOS shows a **blank white screen** — no text, nothing to act on. Chromium
  survives it, so desktop testing never sees it. Terminal `offlineFallback()` at every path. (#7)
- **Unbounded network wait in the SW** → on "lie-fi" (slow-but-alive signal) the fetch neither
  resolves nor rejects, so `respondWith()` stays *pending* — same blank screen as above, but
  truly-offline works, which is why testing with the network killed never catches it. Shell
  cache-first + `withTimeout()` (warm/cold bounds) on the fallback fetch; `scripts/sw.test.mjs`
  holds the contract under a fake clock. (#9)
- **Bare `cache.addAll` precache** → one 404 rejects the whole install (no cache at all), and an
  iOS-evicted cache (name kept, contents dropped) never re-fills, since install only runs on a `V`
  bump — working online, blank offline, *permanently*. Per-file `ensureShell()` + top-up pings. (#7)
- **Old cache generation shadows the new** → `CacheStorage.match()` iterates in *creation* order,
  so a lingering old cache serves the previous release offline and wedges the version tag. Scope
  reads to the current `V` first (`cacheLookup()`), and collect old generations *directionally* —
  only lower numeric tails, only once the current shell is complete. (#7)
- **Runtime writes into the shell** → a redeploy with no `V` bump overwrites shell files one at a
  time; the cache stays "complete" while mixing two deploys (a document from one driving scripts
  from another). `cachePut()` skips `SHELL` URLs — the install owns them. (#7)
- **Unanchored version regex in `checkVer()`** → a first-match-anywhere scan for `app-v\d+` matches
  a *comment* and pins a permanent "tap to update" tag that does nothing when tapped. Parse the
  declaration: `const V\s*=\s*"…"` — same expression as `sw-lint.py`. (#7)
- **SW caches its own version probe** → `checkVer()` fetches `./sw.js?_=<ts>` on every resume; if the
  fetch handler caches it, each resume writes a dead unique-key entry (unbounded growth between
  deploys), and any cache-first-`.js` adopter serves a stale probe back so "tap to update" never
  lights. Guard: `if (u.pathname.endsWith("/sw.js")) return;` before the live branch.
- **Webfont not in the SW cache** → offline opens fall back to system serif.
- **Testing a fix on an installed PWA** → you're fighting the SW cache, not your code. Test the working
  tree in a Safari **Private tab** (no SW registration) via `ngrok`; see [Testing without a build](testing.md).
- **CDN library (SheetJS, a chart lib) not cached** → installable via the manifest, but opens to a
  blank app on a plane. Precache the CDN URL in the SW or vendor a local copy (see [Offline](offline.md)).
- **SW cached a 404/502 body** → `fetch()` resolves on an HTTP error, so an ungated `c.put()` overwrites
  a good cached file with an error page that outlives the outage. Gate on `resp.ok` — but exempt
  opaque responses or you silently stop caching webfonts. ([Offline](offline.md))
- **Cached an empty 200** → the degenerate response becomes your offline fallback. Under cache-first
  it wedges the app permanently (paint from a poisoned cache, reload, repeat). Gate `writeCache` on a
  validity predicate. ([Offline](offline.md))
- **Static fallback file never committed** → the bottom offline tier 404s, and since it only fires
  after live *and* cache have both failed, you never notice until you're offline. Commit + precache it.
- **Sheets: all-digit / date-like values coerced** → `0042`→`42` (breaks an id/hash join), `2/3`→a
  `Date`; format Plain-text, read `.w` not `.v`, mind trailing-space tab names. ([Google Sheets as a backend](data-analytics.md#google-sheets-as-a-backend--read-write-and-picking-the-access-path--pingjs-datajs-scriptsanalyticsgs))
- **No `viewport` / `viewport-fit` / safe-area** → tiny text, or content under the notch.
- **Meaning in color alone** (red/green status, a colored dot) → invisible to the ~8% of men who are
  red-green colorblind. Pair every color with a word, glyph, or shape.
- **Hover-only tooltip** → invisible on every phone. Give it a tap path — and mind the touch
  double-fire (tap = `mouseover` + `click`); see the kernel snippet in [Mobile](mobile-a11y.md).
- **Manifest but no `apple-*` metas** → Android installs clean, iOS install looks broken.
- **Blank `name` / wrong-path icon in the manifest** → Android installs an unnamed app with a broken
  glyph. It fails silently (no build error); open the manifest and confirm every icon URL 200s.
- **Transparent favicon reused as the `maskable` icon** → Android's mask crops into the artwork. Give
  maskable its own full-bleed tile.
- **JS-baked color (canvas/d3) after a theme flip** → frozen at the old value; the CSS-var swap can't
  reach it. Re-render on theme change; CSS-var elements update free.
- **Retyping a config URL on a phone keyboard** → seed it with a `?data=` link + a desktop "copy setup
  link" button instead.
- **iOS resumes, doesn't reload** → stale data unless you re-pull on `visibilitychange`.
- **Print with dark-mode CSS** → wastes ink; links unclickable on paper. `@media print` resets.
- **Sheets: a plain Save doesn't redeploy the Apps Script** → you're editing a script nobody's calling
  (Manage deployments → New version). See [Google Sheets as a backend](data-analytics.md#google-sheets-as-a-backend--read-write-and-picking-the-access-path--pingjs-datajs-scriptsanalyticsgs) for the rest.
- **Named the root the "invite" page** → installed copies open it daily; keep root = the daily app.
- **PII in the repo** → a `noindex` page is still public to anyone with the URL. Keep data in a
  separate view-only sheet, pulled at runtime, never committed.

