# The pre-share checklist

> The rubric. Deep dives: [offline](offline.md) · [sharing & install](sharing-install.md) ·
> [mobile & dark mode](mobile-a11y.md) · [data & analytics](data-analytics.md) ·
> [deploy](deploy.md) · [testing](testing.md) · [gotchas](gotchas.md) · [history](history.md).

The rubric for both workflows. None of it is hard; all of it is easy to forget until someone texts
the link and gets a grey box, or installs it and it won't open on a plane. And there's no longer a
robot to catch these for you — Lighthouse **removed its PWA category in v12 (May 2024)** and
PageSpeed dropped it too (Chrome no longer even requires a service worker for installability), so no
automated audit grades a PWA anymore. This checklist *is* the audit. (A service worker is now about
*offline*, not installability — but iOS still needs one to open on a plane, so it stays mandatory here.)

**Share / link preview** — `index.html` head, `scripts/make-og.sh`
- [ ] `<title>` + `meta[description]` are real (not a default)
- [ ] OG: `og:title/description/url/image` (+ `image:width/height/alt`)
- [ ] Twitter: `twitter:card=summary_large_image` + `title/description/image`
- [ ] **`og:image` is an ABSOLUTE https URL to a RASTER (PNG/JPG), 1200×630, compressed** — not relative, not SVG
- [ ] Card is **under the scraper size budget** — `make-og.sh` compresses + hard-fails over ~250 KB, and `og-lint.py` guards the commit (same pre-commit as `sw-lint.py`); a too-big card previews as a grey box
- [ ] The share image exists and renders — a previewer ([opengraph.xyz](https://www.opengraph.xyz/),
  opengraph.dev) for a fast multi-platform read of the tags, then **paste the URL into a real chat**,
  which is the only ground truth

**Icons / install** — `manifest.json`, `assets/`, `scripts/make-icons.sh`
- [ ] `icon.svg` source → 180/192/512 PNGs (generated, not hand-edited)
- [ ] `link[rel=icon]` (svg + png) + `link[rel=apple-touch-icon]` (180)
- [ ] `manifest.json` linked: `name`, `short_name`, `start_url:"./"`, `display:"standalone"`, icons incl. a `maskable`
- [ ] `apple-mobile-web-app-capable` + `-title` metas (iOS ignores the manifest)
- [ ] `theme-color`, one per color scheme

**Offline / cache-busting** — `sw.js`, `app.js`, `scripts/sw-lint.py`
- [ ] Service worker registered + precaching the shell (`SHELL` lists every offline-needed file)
- [ ] **A version constant `V` bumped on every shell change** — the #1 gotcha. `V` must keep a
  **numeric tail** (rename the stem freely) — it orders cache generations
- [ ] `app.js`'s `VER_PREFIX` matches `sw.js`'s `V` stem (drives the "tap to update" tag)
- [ ] **Per-file precache, never a bare `cache.addAll`** — one 404 rejects an atomic install and the
  device gets *no cache at all*; and an evicted-but-registered cache must **self-heal** (top-up on
  load/foreground), or it stays blank offline forever. See [Offline](offline.md): per-file brings a *partial*
  state, and completeness / generations / bootability then have to be handled together
- [ ] **`respondWith()` never resolves `undefined`, rejects, *or hangs*** — a terminal
  `offlineFallback()` Response at every path, or WebKit/iOS paints a blank white screen with
  nothing to act on. The hang is the sneaky third case: `fetch()` only *rejects* on real failure,
  so on "lie-fi" (a slow-but-alive link) an unbounded network wait leaves `respondWith()` pending
  forever — serve the shell **cache-first** with a `withTimeout()` bound on its network fallback.
  (The fonts / first-run-JSON / image fallbacks are deliberately unbounded — a hang there stalls a
  subresource, not the document, matching what the browser does with no SW — but if your app
  *depends* on one of those cold paths, bound it the same way)
- [ ] Shell served **cache-first**, network only as the bounded fallback — which makes "every live
  `.html`/`.js` URL is in `SHELL`" load-bearing: a non-shell one is served stale until a `V` bump
  collects the old generation, so new pages/scripts go in `SHELL` (+ bump), not runtime caching
- [ ] `sw-lint.py` wired into the pre-commit hook / CI (V bump, numeric tail, SHELL paths exist,
  no cross-origin entries), and `scripts/sw.test.mjs` in CI (the behavioral half: cache-first
  serves, lie-fi bounds, offline fallbacks — runs `sw.js` unmodified under mocked SW globals.
  Fetch-handler coverage only: the precache/generation half — `ensureShell()`, the directional
  collect, `cacheLookup()`'s V-scoping — is held by prose + `sw-lint.py`, not by these tests)
- [ ] **No uncached third-party dependency** — every `<script src="https://cdn…">`, webfont, and CSS
  the app can't run without is either **precached in `SHELL`** or **vendored locally**. This is the
  one that passes every other check and still opens blank on a plane: the manifest installs fine, the
  shell caches fine, and the app dies on a CDN it can't reach. Vendoring is the safer of the two (a
  precached CDN URL still breaks if the CDN changes the path, and pins you to their uptime + privacy
  posture); haydn and boccherini both self-host d3, wtq loads SheetJS + Google Fonts from CDNs.
- [ ] **Cache writes gated on `resp.ok`** (with opaque responses exempt) — an HTTP error is a
  *resolved* fetch and will otherwise overwrite good cached files
- [ ] Data `.json` served stale-while-revalidate, not network-first, so first paint doesn't block on
  it (precached `.json` is not revalidated at all — a `V` bump refreshes it)
- [ ] Tested offline **three ways**, because "load online once, kill the network, reopen"
  pre-guarantees a populated, coherent, single-generation cache and so can't catch the family of
  bugs in #7: (1) that basic case; (2) with an **empty precache** (clear site data, go offline,
  open — must show the offline page, not a blank screen); (3) **across an update** — bump `V`,
  reload once, go offline: the new shell serves and the old cache gets collected. Every defect in
  #7's seven review rounds was invisible on a fresh install and only appeared on the update path

**Mobile** — head + `styles.css`
- [ ] `viewport` tag present with `viewport-fit=cover` (forgetting it entirely is a classic miss)
- [ ] `env(safe-area-inset-*)` padding (clear of notch / home indicator)
- [ ] `color-scheme: light dark` meta (no white flash before CSS)
- [ ] Touch targets ≥ ~44px; nothing overflows a 375px screen
- [ ] **Any hover-only UI (tooltips, popovers) has a tap fallback** — hover doesn't exist on touch
- [ ] `overscroll-behavior-y:none` if you don't want the standalone rubber-band bounce

**Dark mode** — `styles.css`
- [ ] `@media (prefers-color-scheme: dark)` overrides (follows the OS)
- [ ] Optional `.dark` class mirror for forced testing / a toggle / visual regression
- [ ] Contrast checked in *both* modes (WCAG AA)

**Accessibility (the cheap floor)** — head + `styles.css`
The build-time-cheap, retrofit-expensive slice — worth it even at a handful of users, because the
need isn't proportional to user count (one colorblind user in ~12 men clears the bar) and most of it
helps *you* too (sunlight, one-handed, tired). Skip the heavy tier (full screen-reader pass, ARIA
live regions, WCAG AAA) unless you know a user needs it.
- [ ] **Never encode meaning in color alone** — pair every color-coded state with a word, glyph, or
  shape (the `live`/`cached`/`offline` chip is color **+ label**, a colorblind user reads the label)
- [ ] Contrast AA in both schemes and touch targets ≥44px (covered under Dark mode / Mobile above)
- [ ] **Semantic controls** — a tappable thing is a `<button>`/`<a>`, not a click-handler `<div>`;
  real headings; one `<h1>`. Free keyboard + screen-reader support falls out of it.
- [ ] **Every control has an accessible name** — visible text, or `aria-label` on an icon-only button
- [ ] **Visible focus** — don't `outline:none` without a replacement (`:focus-visible`)
- [ ] `alt` on meaningful images (decorative → `alt=""`); the share card already has `og:image:alt`
- [ ] `@media (prefers-reduced-motion: reduce)` neutralizes non-essential transitions/animations

**Print** (only if the app is meant to be printed / PDF'd) — `styles.css`
- [ ] `@media print` resets dark backgrounds to white/black (ink) and hides interactive chrome
- [ ] Remember links aren't clickable on paper — don't rely on them; show the URL/QR if it matters

**Analytics** (optional) — `ping.js`, `scripts/analytics.gs`, `usage/`, or a GoatCounter tag
- [ ] The right tool for the audience: anonymous/public → GoatCounter; known roster or
  private/CSP-strict → the sheet-ping ([Analytics](data-analytics.md#analytics--goatcounter-for-public-stats-the-sheet-backend-for-known-audiences--pingjs-scriptsanalyticsgs-usage) has the fork)
- [ ] Sheet path: ping pattern wired, loaded last, offline-queued, no PII in the log; `usage/`
  dashboard's `PINGS_CSV` points at the published pings tab
- [ ] GoatCounter path: script tag `async` and loaded last; the app must never *depend* on it —
  it's exempt from the no-uncached-CDN rule precisely because it fails silently offline

**Deploy**
- [ ] Relative paths throughout (works at `user.github.io/repo/`, not just a root domain)
- [ ] Opened at the real URL **online once** to prime the SW cache, then Add to Home Screen
- [ ] `.gitignore` keeps PII / large caches / generated previews out of the repo
