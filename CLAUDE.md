# CLAUDE.md — pwa-starter

Briefing for Claude Code working in (or from) this repo. Two jobs: **scaffold a new PWA** from this
skeleton, or **audit an existing app** against the checklist below. Read the relevant workflow, then
the checklist, then the pattern sections for the *why*.

## What this is

An opinionated skeleton for a small, static, single-author PWA: one or a few HTML files, no backend,
GitHub Pages / Netlify, opened on a phone and installed to the home screen. The philosophy is
**pure-pull, self-contained output** — the deployed files don't depend on any build step, and
*opening the app is the refresh*. It exists because four such apps each forgot the same things
(share cards, offline, cache-busting, install polish, dark mode, analytics) and retrofitted them
one painful commit at a time. This turns that into a checklist.

Not for: framework/SPA apps, anything with a real backend or auth, or large teams. The whole value
is that it's small enough to hold in your head.

---

## Workflow: New project ("make a new project based on pwa-starter")

The user has this skeleton as their starting files (a clone, or a GitHub template instance). Turn it
into *their* app. Do this in order:

1. **Ask the essentials** (one short round, don't guess):
   - App name + one-word short_name (home-screen label)
   - One-line tagline and one-sentence description
   - The eventual URL (`https://<user>.github.io/<repo>/` for Pages) — needed for absolute OG tags
   - Do they want **usage analytics**? Two tools, picked by audience (§Analytics): **GoatCounter**
     for anonymous public stats — the fleet default — or the **sheet-ping** (`ping.js` + `usage/`)
     when the audience is a known roster (AKM) or the tool is private. If GoatCounter or none:
     delete `usage/`, `ping.js`, `scripts/analytics.gs`, and the `ping.js`/`usage/` lines from
     `sw.js` + the `<script src="./ping.js">` in `index.html`; for GoatCounter add its script tag
     (last, `async`).
2. **Replace the placeholders** (they're deliberately grep-able). Search the whole tree:

   | Placeholder | Becomes | Where |
   |---|---|---|
   | `APP` | app / short name | index.html, manifest, usage, styles comment, sw.js offline page |
   | `APP — tagline` | real title | index.html `<title>`/OG, manifest `name` |
   | `One sentence on what this is.` | real description | index.html meta/OG |
   | `https://USER.github.io/APP/` | real absolute URL | index.html OG/canonical (must be absolute) |
   | `#f5f5f5` / `#1a1a1a` / `#2196f3` | real palette | styles.css vars, theme-color metas, manifest colors, sw.js `offlineFallback()` (inline by necessity — it renders when styles.css is unreachable) |
   | `app-v` | cache prefix (optional) | sw.js `V` **and** app.js `VER_PREFIX` (keep in sync!) — rename the *stem* only; the **numeric tail is load-bearing** (it orders cache generations for sw.js's collect and checkVer()'s ranking; sw-lint enforces it) |
   | `app-token` | a random token | ping.js + scripts/analytics.gs (must match) |
   | `app-pings` / `app-me` / `app-usage` | localStorage keys (optional rename) | ping.js, usage/index.html |
   | `app-theme` / `app-data:` | localStorage keys (optional rename) | theme.js **and** index.html pre-paint script (keep in sync!); data.js |
   | `DATA_URL` empty | your cross-origin data endpoint | app.js (empty = disabled, like ping.js's `URL_`) |

3. **Draw the icon.** Replace `assets/icon.svg` (and `assets/og.svg`) with something real, then run
   `scripts/make-icons.sh` + `scripts/make-og.sh`. Until you do, the head references PNGs that don't
   exist — generating them is step one, not a polish item.
4. **Wire analytics** (if wanted) per §Analytics — it's ~10 minutes and the app works fine without
   it (`URL_` empty = silently disabled).
5. **Verify** against the checklist below before declaring done. At minimum: it loads at a local
   server, installs, survives offline (load once, kill network, reopen), and the share card renders.
6. **Enable the hook:** `git config core.hooksPath .githooks` (the cache-bump guard).

Then hand back a short list of what's still on the user: deploy (flip on Pages), open once online to
prime the cache, Add to Home Screen.

## Workflow: Audit an existing app ("what's missing vs pwa-starter?")

The user points a session at their app's repo and references this one. Don't rewrite their app —
**assess it against the checklist and report gaps**, then offer to fix. Procedure:

1. Read their `index.html` head, any `sw.js`/`manifest.json`, and their CSS.
2. Walk the **checklist** below as a rubric. For each item: present ✅ / ⚠️ / ❌ with the specific
   evidence (the missing tag, the unversioned cache, the hover-only tooltip).
3. Report as a table, worst-first, each row naming the fix and roughly what it costs. Lead with the
   high-leverage misses (share card, offline, cache-busting) over nitpicks.
4. Offer to apply fixes — but keep the app's own design language; port the *pattern* from the
   skeleton file, not its placeholder styling.

This is exactly the Haydn / Boccherini use case. Known starting points for those two:
- **Boccherini** is a beautiful page that ships **no** favicon, OG card, manifest, service worker,
  or install metas — a near-total sweep of the checklist despite excellent dark-mode + responsive
  CSS. High-value, low-risk retrofit.
- **Haydn web** has favicons + OG + a preview image and GoatCounter analytics, but no manifest and
  no service worker (not installable, not offline). Its scatter page had to add mobile/touch layout
  and tap-fallbacks for hover tooltips after the fact — check any hover-only UI.

---

## File hierarchy (opinionated)

Deployed files live at the repo root (so GitHub Pages "deploy from root" just works and every path
stays relative). Everything that is *not* shipped to the browser is segregated:

- **Root** = the app: `index.html`, `styles.css`, `app.js`, `sw.js`, `manifest.json`, `ping.js`, and
  three small reference helpers `app.js` wires together — `theme.js` (three-state theme + the
  JS-baked-color contract), `data.js` (stale-while-revalidate with a timeout), and the optional
  `pullToRefresh.js` (standalone-only gesture; delete it + its CSS if unused).
- **`assets/`** = icons + share card. `icon.svg`/`og.svg` are the **sources of truth**; the PNGs
  are generated, never hand-edited.
- **`usage/`** = the self-contained analytics dashboard (its own page, precached, `noindex`).
- **`scripts/`** = tooling that never ships: asset rasterizers, `sw-lint.py`, `og-lint.py`, and
  `analytics.gs` (reference copy of the backend).
- **`tools/`** = `setup-environment.sh`, the idempotent build-toolchain check/installer, run from a
  `SessionStart` hook in `.claude/settings.json` so a fresh clone or cloud session can actually build.
- **`.githooks/`** = the warn-only pre-commit (runs `sw-lint.py` + `og-lint.py`).

Two deliberate opinions worth keeping: **CSS is a separate `styles.css`** (not inlined) so the
design system has one home — inlining is fine for a strict one-pager, but split it the moment there's
a second page. And **`app.js` owns boot**, `index.html` owns structure, `styles.css` owns looks — no
logic in the HTML beyond loading the scripts.

---

## The pre-share checklist

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
  load/foreground), or it stays blank offline forever. See §Offline: per-file brings a *partial*
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
  private/CSP-strict → the sheet-ping (§Analytics has the fork)
- [ ] Sheet path: ping pattern wired, loaded last, offline-queued, no PII in the log; `usage/`
  dashboard's `PINGS_CSV` points at the published pings tab
- [ ] GoatCounter path: script tag `async` and loaded last; the app must never *depend* on it —
  it's exempt from the no-uncached-CDN rule precisely because it fails silently offline

**Deploy**
- [ ] Relative paths throughout (works at `user.github.io/repo/`, not just a root domain)
- [ ] Opened at the real URL **online once** to prime the SW cache, then Add to Home Screen
- [ ] `.gitignore` keeps PII / large caches / generated previews out of the repo

---

## The maturity gradient (why the checklist exists)

**This table is a historical snapshot, deliberately not maintained.** It records the state of the
source apps *at the time they motivated this skeleton* — it's the evidence for why each checklist row
exists, not a status board. Several of these apps have since been retrofitted *from* this skeleton
(boccherini and haydn both have manifests and service workers now), which would make a
kept-current version circular: the apps that taught the checklist now pass it because of it. For
"which repos are downstream and need a fix propagated," see the registry, not this table.

The four source apps land at different points on exactly these axes; the gaps are the lesson. The
fifth column, gallery-deck, is the boundary case — it clears the checklist that matters for its
deployment (a private tailnet tool) but crosses the last row.

| Capability | boccherini | haydn web | lobsters | AKM | gallery-deck |
|---|:-:|:-:|:-:|:-:|:-:|
| Dark mode / responsive | ✅ | ✅ | ✅ | ✅ | ✅ |
| Favicon / icons | ❌ | ✅ | ✅ | ✅ | ✅ |
| OG / share card | ❌ | ✅ | ✅ | ✅ | ❌ |
| `apple-*` / theme-color | ❌ | partial | ✅ | ✅ | partial |
| Web app manifest | ❌ | ❌ | ✅ (runtime) | ✅ | ✅ |
| Offline service worker | ❌ | ❌ | ✅ (inlined) | ✅ | ✅ (shell) |
| Cache-bust discipline (`V` + lint) | — | — | — | ✅ | `V`, no lint |
| Usage analytics | ❌ | GoatCounter | ❌ | ✅ (own sheet) | ❌ |
| Backend / DB | ❌ | ❌ | ❌ | ❌ | ✅ |

Git history says the retrofits were remarkably uniform: **share-sheet metadata + a preview image**
(added late in lobsters *and* both haydn pages), **dark mode** (a whole PR saga in boccherini,
including a separate pass just for print/PDF), **mobile layout and tap-fallbacks for hover tooltips**
(haydn's scatter, boccherini's "mobile tooltips"), **favicons + meta polish**, **analytics**, and in
boccherini even the **`viewport` tag itself**. This skeleton front-loads all of it.

gallery-deck is the app that **graduated past the skeleton**: scaffolded from it, then grown a
FastAPI + SQLite + media backend — proof the "no backend" boundary is real, and where you stop
reaching for this checklist and start writing a server. It kept just three skeleton ideas (the SW
`V`-bump/network-first shell, the tap-to-update `#ver` tag, CSS-variable theming) and still managed a
fresh instance of the `sw.js` probe-cache gotcha below — the doc was right, the app forgot the guard.

---

## Patterns (the *why*, and the gotcha)

### HTML head / meta — `index.html`
- **OG image: absolute + raster + compressed.** iMessage/WhatsApp/Slack scrapers reject relative
  paths, won't render SVG, and skip images that are too big. 1200×630, run it through pngquant.
- **`theme-color` is per-scheme** (`media="(prefers-color-scheme: …)"`) — it tints the browser UI.
- **`color-scheme: light dark`** up top kills the first-paint white flash in dark mode.
- iOS reads `apple-touch-icon` + the `apple-mobile-web-app-*` metas and *mostly ignores the
  manifest*; Android reads the manifest. Ship both or one platform's install looks broken.

### Icons & share image — `assets/`, `scripts/make-*.sh`
One SVG is the source; rasterize from it, never hand-edit PNGs (they drift). `make-icons.sh` →
180/192/512; `make-og.sh` → the 1200×630 card. If the card has live `<text>`, the font must be
installed locally or the render falls back to a stock serif. **`make-og.sh` compresses the card and
hard-fails if it lands over ~250 KB** (a margin under WhatsApp's ~300 KB scrape cutoff), and
`og-lint.py` re-checks the staged PNG in the pre-commit — so "compress the share image" is enforced,
not remembered. That's the `sw-lint.py` discipline applied to the *other* forgot-it asset: a card too
big to scrape previews as a grey box, and you don't find out until someone texts the link back blank. Neat single-page trick (lobsters): one
SVG **data-URI** used for `apple-touch-icon` *and* a **runtime-generated manifest** (a tiny script
builds it as a Blob URL) — zero icon files. This skeleton uses real files since multi-page apps cache
them anyway.

A third-party previewer is a good first pass but not an audit: it renders its *own* simulation from
your tags rather than running Apple's or Meta's scraper (iMessage and WhatsApp, the two that matter
most here, have no official debugger at all), it happily previews a card too big for a scraper to
fetch — that's `og-lint.py`'s job, not its — and it can't clear a *cached* bad preview, which still
needs Facebook's Sharing Debugger or LinkedIn's Post Inspector (X's validator died in 2022). It also
needs a public URL, so it's a post-deploy check and no help to a tailnet/private app.

### Offline & the service worker — **the cache-busting gotcha** — `sw.js`, `app.js`, `data.js`, `sw-lint.py`
The one that bites hardest and latest.
- The SW precaches `SHELL` and serves it **cache-first** — no network on the critical path, so a
  load is instant and identical on a fast link, a slow one, or none. The network survives only as
  a **bounded** fallback (`withTimeout()`: ~3s with a cached page in hand, ~15s cold) for a first
  run or an evicted shell. The bound is not polish: `fetch()` only *rejects* on a genuine network
  failure, so on "lie-fi" (weak cell signal, a half-answering captive portal) it hangs instead —
  the offline `.catch()` never fires, `respondWith()` stays pending, and WebKit paints a blank
  screen while truly-offline works fine. Network-first also bought nothing here: `cachePut()`
  refuses SHELL urls, so every live-branch fetch paid latency to *discard* the bytes — freshness
  rides the V-bump → update-tag path. The one trade: a deploy shows after the update-tag tap / SW
  swap rather than on the next reload; the tag makes that a single tap. Corollary (now
  load-bearing): **every live `.html`/`.js` URL must be a `SHELL` file** — a non-shell one is
  served cache-first with no revalidation until a `V` bump collects the old generation, so a new
  page or script goes in `SHELL` (+ bump), never opportunistic caching. (#9)
- **`SHELL` isn't only app code — precache the *documents* users open where there's no signal.** AKM
  lists its concert-program **PDFs** in `SHELL` ("precached so they open offline at the venue"); same
  logic for a map tile in a canyon or a schedule at a festival. The test isn't "is it code?" but "will
  someone need to *open* this exactly where the network isn't?" — if so it belongs in the precache, not
  lazy runtime caching that only fills after a first online view.
- **Bump `V` on every shell-file change.** A new `V` is what refreshes the shell — the install that
  a new `V` triggers is the only thing that writes precached files. Forget it and your fix is in the
  repo but *never on anyone's phone* — iOS caches the SW aggressively. This bit AKM's "v77" rewrite
  (three commits, no bump, stale UI). `sw-lint.py` catches a staged `SHELL` file with an unchanged
  `V`, and the "tap to update" tag makes a stuck phone fixable by hand.
- **Precache per-file, never a bare `cache.addAll` — and know what that trade buys you into.**
  `addAll` is atomic: the cache is *complete* or *absent*. Absent is a live hazard — one 404 (a
  renamed file, icons not yet generated, a mid-deploy blip) rejects the whole install and the device
  gets **no cache at all**, i.e. blank offline; and iOS reclaims Cache API contents under storage
  pressure (~7 idle days) while keeping the cache *name* and registration, after which nothing ever
  re-populates it, because install only runs on a `V` bump. So `sw.js` precaches per-file
  (`ensureShell()`: fetch only what's *missing*, dedupe concurrent runs) and `app.js` pings
  `ensure-shell` on load, foreground, and `controllerchange` — one online launch repairs an evicted
  cache. **But per-file puts introduce a third state, *partial*, and three questions `addAll`
  answered implicitly become live:** (1) is this cache *complete* — and by what measure, presence or
  same-deploy coherence? (2) which *generation* answers a read when two caches coexist? (3) is a
  complete-looking cache actually *bootable*? Every bug in #7's seven downstream review rounds was
  one of these answered wrongly — an adopter who internalizes the intersection will catch the next
  one; an adopter who ports the patches one at a time will reintroduce them. The consequences, as
  implemented:
  - **Scope reads to the current version** (`cacheLookup()`: `caches.open(V).match()` first, whole
    store second). `CacheStorage.match()` iterates caches in *creation order*, so a lingering old
    generation otherwise answers first and serves the **previous release** offline indefinitely.
    The old cache still fills gaps — it's the net that makes a failed `V` bump survivable — but it
    can no longer outrank a complete current shell. If a downstream copy ports only one thing, port
    this: it closes the class by construction, not by timing.
  - **Repair before collect, and collect *directionally*.** `addAll`'s atomicity was also a guard: a
    failed install meant the old worker kept serving its complete cache. Per-file installs always
    resolve, so `activate` must top up first and only collect the old cache once this version's
    shell is complete — and the collect must delete only caches with a **lower numeric tail**, never
    "everything that isn't me": `skipWaiting()` means an incoming worker is `active` with
    `installing`/`waiting` both null, so an outgoing worker's collect would otherwise delete the new
    precache mid-fill. It must also be **re-runnable** (`activate` fires once per version — the
    `ensure-shell` message handler retries it), and a *permanently* unfetchable entry (a 404'd
    path — a SHELL-list bug no retry fixes) must not hold it hostage, or both generations pile up
    forever. This is why `V`'s numeric tail is load-bearing.
  - **`ensureShell()` owns the shell outright** — `cachePut()` refuses to write `SHELL` URLs. `V` is
    whatever the *current* worker declares, so opportunistic runtime writes let a redeploy (no `V`
    bump) overwrite shell files **one at a time**: the cache reports itself complete while holding a
    document from one deploy and scripts from another. The skeleton's shell is two coupled sets
    (index.html + styles.css + app.js + theme.js + data.js; usage/ + crunch.js), exactly the shape
    that skews into confusing bugs. Corollary: precached `.json` is *not* revalidated (the fetch
    would be discarded — pure cellular waste); a `V` bump refreshes it.
  - **Never let `respondWith()` resolve `undefined` or reject.** Both lookups missing resolved the
    old `.catch()` to `undefined` → WebKit fails the navigation ("Returned response is null") and
    iOS paints a **blank white screen**, no text, nothing to act on — the bug that started #7.
    Chromium survives it, which is why desktop testing never sees it. `offlineFallback()` is the
    terminal answer at every path: a readable inline page for navigations ("open it once with a
    connection…"), a bare 504 for subresources. Gate the `./index.html` fallback on
    `mode === "navigate"` (the `live` branch also matches `.js` — handing HTML to a script request
    makes it fail to *parse* instead of failing cleanly) **and on the root document** (answering an
    uncached `/usage/` navigation with the root page is the wrong document; the honest offline page
    beats one the user didn't ask for). Decide navigations *before* the `.json` branch.
  - **Don't serve a document you can't boot** (`BOOT_DEPS`/`bootable()`). Per-file means "document
    cached, boot-critical script missing" is reachable: the page half-renders with no error and no
    hint. List per document only what it *dies* without — gating on a nice-to-have replaces a
    working offline page with an error page. The skeleton's root as shipped needs nothing (static
    placeholder); the moment `paint()` owns your content, theme.js/data.js/app.js and any vendored
    chart lib belong in its list. usage/ needs crunch.js.
  - The `offlineFallback()` page **deliberately breaks two repo rules**: its CSS is inline (it
    renders precisely when styles.css is unreachable) and it hardcodes the placeholder palette +
    `system-ui` (a fallback that depends on a cached font defeats itself). Both are flagged in the
    replacement table — rebrand it with the rest.
- **Gate the SW's cache writes on `resp.ok` — a `fetch()` only rejects on a *network* failure.** A 404
  or a mid-deploy 502 arrives as a **resolved** response, so the naive
  `fetch(req).then(resp => { c.put(req, resp.clone()); return resp; })` writes the error body over a
  good cached copy, the `.catch()` never fires, and the poison survives as the offline fallback until
  the next `V` bump. It's the shell-cache twin of "never cache an empty 200" below. Subtleties:
  serve the **cached copy on a non-ok response** too (don't hand the app an error page when you have
  something good); **exempt opaque responses** — a cross-origin `no-cors` fetch (webfont, CDN
  script) always reports `ok:false`/`status:0`, so a bare `resp.ok` gate silently stops caching your
  fonts and breaks offline type; skip **redirected** responses (they can't satisfy a navigation) and
  **206** (`resp.ok` is *true* for a partial, then `put()` throws — matters the moment an app caches
  audio/video); `.catch()` the `put()` itself (non-GET, 206, quota all land there) and guard the
  whole fetch handler with `method !== "GET"` — a form POST is `mode === "navigate"`. `sw.js`'s
  `cachePut()` is the worked version. Every app that copied this file before the fix has the bug at
  two call sites.
- **`app.js` makes staleness visible + fixable in one tap:** it reads the installed cache name from
  `caches.keys()`, fetches the deployed `sw.js` (`?_=`+`no-store` to dodge both caches), and shows a
  tappable "installed → latest" tag when the server is ahead; tapping deletes all caches + reloads.
- Let **cross-origin data** (your APIs) pass straight through — don't cache it in the SW; do
  stale-while-revalidate in the app (localStorage) instead. Time-box the network read with a cache
  fallback so a flaky connection degrades to last-known data instead of hanging: race the fetch
  against a short timeout (quartet-log uses ~5s), and on timeout/failure serve the localStorage copy
  and *flag it stale in the UI* ("loaded from cache, N min old") so the user knows they're offline.
  The skeleton's `data.js` is that helper — `Data.load()` does the race, aborts the fetch on timeout,
  and returns `{data, stale, ageMs}`; `app.js` reads it and shows the stale tag.
- **Then go cache-first, so the first paint doesn't wait on the network at all.** Network-first still
  makes a returning visitor stare at the placeholder for up to the full timeout while a perfectly good
  cached copy sits in localStorage — exactly the "installed app, spotty signal" case this skeleton
  targets. Instead: read the cache *synchronously* and paint immediately, then revalidate in the
  background and repaint **only if the payload actually changed** (a cheap serialized diff avoids a
  needless flash). `data.js` exposes `Data.peek(key)` (sync, no network) and `Data.revalidate(url)`
  (network-only, returns a `changed` flag); `app.js`'s `render()` is `peek → paint → revalidate →
  repaint if changed`, awaiting the network only on a true first run. quartet-log's `3322370`.
- **Never cache an empty 200 — under cache-first it's not a stale-data bug, it's a wedge.** A valid
  but degenerate response (a transient server hiccup, a momentarily-empty sheet, a range that matched
  nothing) is still a `200`, and a naive `writeCache(key, await resp.json())` persists `[]`/`{}`/`null`
  happily. Network-first makes that a soft bug: the empty value quietly becomes the offline fallback
  served on every later timeout. Cache-first makes it *fatal* — `peek()` serves the empty payload,
  `paint()` throws, and since you painted from cache before revalidating, a reload just re-reads the
  same poisoned entry; the app can't self-heal without clearing localStorage. So gate the write on a
  validity predicate and treat an invalid payload exactly like a network failure — throw, fall back to
  the good cache, **don't overwrite it**. "Empty" is app-specific (`[]` vs `{}` vs `{items:[]}`), so it's
  `opts.valid`; `data.js`'s default rejects nullish and `[]`. quartet-log's `fd71bde`. Ship this
  *before* the cache-first paint above, never after — it's the guardrail that makes cache-first safe.
- **Cache-first paints twice — make the second paint gentle.** This is the cost of the instant paint
  above: the user is already *reading* when the network lands, so a naive repaint resets scroll, drops
  focus, and pops layout. Note the SW's stale-while-revalidate can't cause this (one request → one
  response; its refresh lands silently and shows up on the *next* load) — the jank lives entirely in
  the app-layer `peek → paint → revalidate → repaint` path. Four defenses, in descending order of how
  much they matter:
  1. **Don't repaint unless the payload changed.** `Data.revalidate()`'s `changed` flag kills the
     common case outright — most revalidations return identical bytes, and repainting those is pure
     cost. This one defense is worth more than the other three combined.
  2. **Restore scroll position** — rebuilding a container resets it to 0, which on a phone reads as
     the app "jumping" for no reason.
  3. **Crossfade the swap** with `document.startViewTransition(swap)` where supported, so content
     changes rather than blinking. Gate it on `prefers-reduced-motion: reduce` (a crossfade is
     non-essential motion), and let unsupported browsers fall through to the plain swap. Two caveats
     at real DOM size (#6, reviewed against musiclog): `startViewTransition` *freezes rendering*
     while the swap callback runs, so a heavy synchronous paint (a several-thousand-element SVG, a
     force layout) turns the crossfade into a visible stall; and its async snapshot→swap gap opens a
     window another repaint (theme flip, resize) can land in — a hazard that doesn't exist when all
     repaints are synchronous. Fine at skeleton scale; measure before keeping it in a big app.
  4. **Don't update at all while the user is mid-interaction.** A form being typed into, an open menu,
     a drag in flight — replacing content under any of those is worse than showing data a minute old.
     The move is to *hold* the update and surface an unobtrusive "new data — tap to refresh" affordance,
     exactly like the `#ver` tag does for a new service worker. Deliberately not in the skeleton, but
     the review (#6) found the *triggers* generalize even though the predicates don't: (a) an **open
     overlay** — menu, dropdown, tooltip, fullscreen mode, usually detectable as a state class;
     (b) **focus inside a form control**; (c) a **pointer gesture in flight**. Write those three as
     your app's `shouldDefer()`; a generic version would still be wrong everywhere.

  `app.js`'s `applyUpdate()` implements 1–3; 4 is yours. The floor for an app with real DOM is at least
  1 and 2 — 3 is polish. A **focus restore** was tried and cut (#6): it's dead code in both paint
  regimes — a wipe-and-rebuild `paint()` destroys the focused node (so `document.contains()` fails),
  and a patch-in-place one never loses focus. Real focus recovery means re-finding the element by id
  after the rebuild, which only your `paint()` can do.
- **Give staleness a visible badge, not just a tooltip.** wtq surfaces `data.js`'s state as a
  three-way colored footer chip — `live` (green) / `cached` (amber) / `offline` (red) — so "am I
  looking at fresh data?" is answerable at a glance. That's the concrete UI for the `{stale, ageMs}`
  the helper already returns; a `stale`/`age` string in a corner is the floor, a colored chip is the
  nicer version.
- **Add a committed static snapshot as the *last* fallback tier** — live → localStorage → a JSON file
  checked into the repo (and precached by the SW). The first-ever open with no cache and no network
  then still renders real data instead of an empty state. Two caveats wtq itself demonstrates: the
  snapshot only works if it's **actually committed AND precached** (wtq's `fetchFromStatic()` fetches
  a `quartets.json` that was never committed, so its bottom tier 404s — a fallback that only fires
  when everything else has already failed is exactly the one you never notice is broken), and it goes
  stale silently, so treat it as a floor, not a source — flag it `offline`/`static` in the badge above.
- **Webfonts survive offline only if the SW caches them** — they aren't iOS system fonts; without the
  cache an offline home-screen open falls back to Times/Courier. Same trap for a **CDN library**
  (SheetJS, a charting lib): a `<script src="https://cdn…">` the app can't run without is a hard
  offline dependency — an installed app with a manifest but an uncached CDN dep opens to nothing on a
  plane. Precache the CDN URL in the SW, or vendor a local copy. (wtq loads both SheetJS and Google
  Fonts from CDNs with no SW — installable, but not actually offline.)
- **Have a build step? Content-hash the shell instead of hand-bumping `V`.** The `V`-bump above is the
  discipline for a no-build app; if a bundler already emits your files, rename `app.[hash].js` /
  `styles.[hash].css` per build, rewrite the references in the *deployed* HTML (leave the source on
  stable names), and derive the SW cache name from those hashes. The cache version then moves
  automatically on every real change — nothing to forget, no `sw-lint` needed. quartet-log does exactly
  this: esbuild output + a `sw.js` template whose `V` is `bundlehash-csshash`, and it folds its data
  version into the bundle via a `--define` so even a pure data change busts the cache. Same effect as
  `V`, minus the human. This is exactly what the framework toolchains automate: **Workbox** (via
  `vite-plugin-pwa`'s `injectManifest`) globs the build output and injects `self.__WB_MANIFEST` — a
  precache list where every entry carries a per-file revision hash, so cache invalidation keys off
  those hashes with nothing to bump. Read the skeleton's `V`-bump + `sw-lint` as the **hand-rolled
  version of that**: the same content-revisioning discipline, done by a human because there's no build
  to do it. (Workbox 7.x / vite-plugin-pwa 0.20.x as of 2024–25.)

### Manifest / installability — `manifest.json`
`start_url:"./"` + relative `scope` so it works as a project page. Include a 512 `maskable` icon or
Android crops your square badly — and make the maskable a **full-bleed** tile (background fill, logo
inside the center-80% safe zone), not your transparent favicon, or the mask eats the edges. The spec
is concrete: the guaranteed-visible safe zone is a **circle of radius 40% of the icon width** (= the
central 80%), and the tile needs an **opaque background covering the whole area** or the mask crops
into art; set the manifest icon's `"purpose": "maskable"` (or `"any maskable"` on one icon to serve
both). Preview the crop across the OS mask shapes (circle / squircle / teardrop) at **maskable.app**
before shipping — it's a GUI eyeball-check, not something `make-icons.sh` can automate. Note: an
installed copy opens `start_url` many times — so the page you want opened *daily* should be the root,
and a "read once" invite/about page should be a *separate* URL you send, not the root.

**Seed per-device config with a link, not a re-typed form.** A no-backend app that needs a scrap of
setup (an API key, a data-source URL) faces an awful phone UX: retype it on a tiny keyboard. Instead,
read a `?data=…`/`?key=…` param on first load, persist it to `localStorage`, then strip it from the
URL — and give the *desktop* a "copy setup link" button that builds that URL. Configure once on the
big screen, AirDrop/iMessage the link to the phone, open it, done. quartet-log seeds its Google-Sheet
URL exactly this way. Flip side of the note above: a link that carries state **is** a send-once URL —
don't make it the `start_url` an installed copy reopens daily.

Left as prose, not a shipped file — it's ~10 lines and only some apps need it. But the two subtleties
that cost a debugging session are worth pinning down: strip the param with `history.replaceState`
(not `location.search = …`, which reloads and adds a history entry), and strip it **before** anything
reads the URL — a `fetch` leaks it in the `Referer` header, analytics log `location.href`. So run this
first thing at boot:

```js
// First load: adopt ?data=… (or ?key=…), then scrub it from the URL.
function consumeConfigParam(){
  const u = new URL(location.href);
  const v = u.searchParams.get("data");
  if(!v) return;
  if(isValid(v)) localStorage.setItem("app-data-url", v);   // validate BEFORE you trust it
  u.searchParams.delete("data");
  history.replaceState(null, "", u.pathname + u.search + u.hash);   // no reload, no history entry
}

// Desktop "copy setup link" builder — encodeURIComponent so the value survives the URL.
const buildSetupLink = v => `${location.origin}${location.pathname}?data=${encodeURIComponent(v)}`;
```

### Mobile — head + `styles.css`
- `viewport-fit=cover` **and** `env(safe-area-inset-*)` padding — one without the other clips content
  under the notch or wastes the inset.
- **Hover doesn't exist on touch.** Tooltips/popovers that only appear on `:hover` are invisible on a
  phone — give them a tap/click path. (Both haydn and boccherini shipped this fix late.) The subtle
  bug that costs a debugging session is the **double-fire**: on touch a single tap synthesizes *both*
  a `mouseover` and a `click`, so the naive "`mouseover` shows the tip, `click` runs the action" does
  both at once — the tip flashes and the link fires before you can read it. Fix by branching on
  whether the device has a real pointer: on a mouse, hover shows the tip and clicking the trigger
  runs the action; on touch, a tap only *toggles* the tip and the action moves to a dedicated control
  *inside* the bubble (so the first tap can't also fire it), with the bubble `pointer-events:none`
  except that control so it never blocks the triggers beneath. haydn's scatter `bindDotInteraction`
  is the worked example. The kernel, app-agnostic:

  ```js
  const TOUCH = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  function bindTip(trigger, {showTip, hideTip, action}){
    if(TOUCH){
      trigger.addEventListener("click", e => {           // a tap only opens the tip...
        e.preventDefault(); e.stopPropagation();          // ...never the action, never the doc-dismiss
        isOpen(trigger) ? hideTip() : showTip(trigger);   // ...and the action is a ▶ button in the tip
      });
    }else{
      trigger.addEventListener("pointerenter", () => showTip(trigger));
      trigger.addEventListener("pointerleave", hideTip);
      trigger.addEventListener("click", action);          // real pointer: no double-fire, run it
    }
  }
  document.addEventListener("click", hideTipIfOpen);       // tap elsewhere dismisses
  ```

  Left as a snippet, not a shipped file: the ~12-line kernel above is the reusable part; the bubble's
  positioning, styling, and content are app-specific enough that a generic component would fight every
  adopter's design. Only lift it into a `touch-tooltip.js` helper if an app has *many* such triggers.
- Target *real* touch devices with `@media (hover:none) and (pointer:coarse) and (max-width:800px)`
  when you want phone-specific sizing — a bare `max-width` also catches a shrunk desktop window.
- Fluid sizing with `clamp(min, vw, max)` scales cleanly desktop→tablet without a pile of breakpoints.
- iOS home-screen apps **resume** rather than reload — re-pull data on `visibilitychange`. That's the
  floor, not the ceiling: an installed app has **no browser chrome, so no reload button** — add a
  **pull-to-refresh** gesture *and* a **foreground poll** (a `setInterval`) so a left-open app freshens
  itself. Gate all three on `document.visibilityState === 'visible'` **and** a staleness threshold so a
  backgrounded tab never fetches and a fresh one isn't re-hit. The skeleton ships all three:
  `pullToRefresh.js` (the gesture, standalone-only) plus the gated `maybeRefresh()` poll and resume
  re-pull in `app.js`. Background Sync isn't an option — iOS standalone doesn't support it.
- **Prefetch the neighbors of any next/prev sequence.** A gallery, carousel, or paginated deck feels
  janky when a swipe lands on an undecoded image — the fix is to warm the browser HTTP cache for the
  neighbors *before* the user gets there: prefetch next **and** prev (an `Image()` with
  `decoding="async"` is enough), plus the **first item of the *next* group** so crossing a boundary
  is smooth too, not just steps within a group. Cheap, pure-client, and the single biggest
  perceived-smoothness win for a swipeable UI. gallery-deck's `prefetchNeighbors()` is the worked
  example — it warms the next/prev image in the current gallery *and* the first image of the next two
  posts (the core down-swipe loop) plus the previous post.

### Dark mode — `styles.css`, `theme.js`
Two entry points, both cheap: `@media (prefers-color-scheme: dark)` (what users get) and a `.dark`
class (force it for screenshots / a toggle / visual-regression baselines). Drive everything off CSS
custom properties so a mode is a variable swap, not a second stylesheet. Watch source order — a later
`@media print` block can clobber your dark vars; reset deliberately. Check contrast in **both** modes.

**The gotcha for canvas / SVG / d3 apps:** the variable swap only re-styles what the browser paints
*from CSS*. Any color you read **into JS** at render time — `ctx.fillStyle`, a d3
`.attr('fill', getCssColor('--accent'))`, a baked color scale — is frozen at the value it held when it
ran, and a mode flip won't touch it. So set a contract: components that bake colors expose a
`rerender()`, and one `onThemeChange()` — fired by both the toggle **and** the `matchMedia` listener
(so auto-mode users following the OS also update) — invalidates any color cache *first*, then calls
each `rerender()`. Purely `var(--…)`-driven components update for free; only the JS-baked ones need
plumbing. quartet-log's calendar and dashboard are the worked example. Bonus: a persisted three-state
toggle (`auto`/`light`/`dark`, default `auto`) plus a pre-paint inline `<script>` that stamps
`data-theme` before first paint kills the dark-mode FOUC without waiting for the bundle. The
skeleton's `theme.js` implements the contract — `subscribe()`, `getCssColor()`, and an
`invalidateColorCache()` that `notify()` fires *before* subscribers; `app.js`'s `onThemeChange()` is
the consumer (repaint from cached data, no refetch). The pre-paint stamp lives in `index.html`.

### Google Sheets as a backend — read, write, and picking the access path — `ping.js`, `data.js`, `scripts/analytics.gs`
A private Google Sheet is the no-backend datastore these apps keep reaching for: free, no server,
editable from your phone, and you already trust Google with the data. **Writes** have exactly one path
(an Apps Script web app); **reads** have four, and the choice is a trade between *how much of the doc
you expose*, *whether you need it live*, and *how much parsing you ship*. Pick from the table, then
see §Analytics for the write path worked end-to-end and wtq for a read one.

| Access | R/W | Exposes | Parse | Fresh? | Reach for it when |
|---|:--:|---|---|---|---|
| **Apps Script web app** (`doPost`/`doGet`, *Execute as: Me / Access: Anyone*) | R **+ W** | nothing — doc stays fully private, only the deployed function is public | you shape the JSON | live | the only way to **write**; also the only **private live read** (return just the columns you code) |
| **Publish-to-web CSV** (`/d/e/…/pub?gid=…&single=true&output=csv`) | R | only the **published tab** | trivial (`split`) | snapshot, ~min lag | the default read — one flat tab, zero dependencies |
| **Publish-to-web xlsx** (`…/pub?output=xlsx`) | R | only the published tab(s) | needs **SheetJS** | snapshot, ~min lag | many tabs, cell **colors/styling as data**, or real types (wtq) |
| **gviz query** (`/d/{id}/gviz/tq?tqx=out:csv&sheet=…&tq=select…`) | R | the **whole doc** (must be link-viewable) | CSV clean; JSON is wrapped | live | filter / select columns server-side without writing a script |
| **Sheets API v4** (`…/v4/…/values/{range}?key=…`) | R (W w/ OAuth) | whole doc **+ your API key in the client** | JSON | live | basically never here — skip unless you already have auth |

**The exposure column is the one that bites.** *Publish to web* makes only the tab you publish public —
the rest of the document stays private, independent of share settings — which is why both the
analytics mailbox and the `usage/` dashboard use it. *gviz* and the *Sheets API* read the **live**
document, so they require it be link-viewable and then expose **all** of it to anyone with the id.
*Apps Script* is the privacy maximalist: the doc is fully private and the endpoint returns only what
you code. So — writing, or a live read you won't make the whole sheet public for → Apps Script; a
simple public read → publish a tab; and the cute trick worth knowing (wtq) is that a **published xlsx
carries cell fills**, so *formatting becomes metadata* (background color = editorial status) and the
author never types a status column.

Gotchas, each of which cost a debugging session:
- **A plain Save doesn't redeploy an Apps Script** — Manage deployments → New version, or you're
  editing a script nobody's calling.
- **All-digit and date-like text get coerced** — an id `0042` becomes `42`, "2/3" becomes a `Date`.
  Format the column Plain-text (Apps Script side); read the cell's display text (`.w`, not `.v`) on
  the SheetJS side. The all-digit case silently breaks a hash/id join.
- **`/pub` lags and caches** — a publish-to-web read can be minutes behind the live sheet; fine for
  stale-while-revalidate, wrong if you need read-your-writes.
- **A published or link-shared tab is public forever to anyone with the URL** — keep no PII in it;
  hold names in a private tab and join at runtime (the analytics `=UID()` trick).
- **gviz JSON is wrapped** in `/*O_o*/google.visualization.Query.setResponse(…)` — strip it, or use `out:csv`.
- **A worksheet name can carry a trailing space** (`"Played "`) — exact-match tab lookups miss it.
- **Keep `doGet`/parsers tolerant of missing or old-shaped rows forever** — offline-queued writes ship
  yesterday's column layout.

Wire any read through the same stale-while-revalidate + committed-snapshot fallback as any cross-origin
data (§Offline) and surface the live/cached/offline state in the UI; `DATA_URL` in `data.js` is where
the read URL lands (empty = disabled, like `ping.js`'s `URL_`).

### Analytics — GoatCounter for public stats, the sheet backend for known audiences — `ping.js`, `scripts/analytics.gs`, `usage/`
**Two tools, picked by audience — and for most of these apps the audience is anonymous and public.**
The question that actually directs dev cycles is fleet-level — *which apps are alive, how much, on
what platforms* — so the default is **GoatCounter**: free, cookieless, one `async` script tag, and
volume/referrer/platform breakdowns with zero backend (haydn web's setup). It's exempt from the
no-uncached-CDN rule because the app never depends on it — it fails silently offline. One account
holds a site code per app, or share one code across apps with host-prefixed paths
(`goatcounter.count({path: location.host + location.pathname})`), so the whole fleet reads at a
glance. Reach for the **sheet-ping below** instead when the audience is a known roster (AKM: "did
Alice open it this week?" — the exception, not the rule), the tool is private / behind a strict
same-origin CSP, or offline opens must be recorded faithfully.

GoatCounter's offline caveats, verified against its published spec + a live CORS preflight (2026-07):
- The public `/count` pixel takes **no timestamp parameter** (`p/t/r/e/q/s/b/rnd` only). So a
  localStorage queue/flush (set `no_onload: true`, replay via `goatcounter.count()` on `online`)
  records offline opens at *flush* time — volume stays roughly honest; timing and session/visit
  counts skew, since a multi-day burst lands as one session (`hash(UA+IP+salt)` in a window).
- Faithful backdating exists one tier up: `POST /api/v0/count` accepts `created_at` per hit ("can
  be in the past, but not in the future"), and the API serves `Access-Control-Allow-Origin: *`
  with `Authorization` allowed — so it genuinely works from a static page with a count-only-scoped
  token (blast radius: fake pageviews, which the tokenless pixel already permits anyone).
- But notice what that queue + flush + authenticated batch-with-timestamps *is*: ping.js's
  transport rebuilt in order to rent the dashboard. If you're there, the sheet costs the same
  effort and adds the who — which is the signal you're on the wrong side of the fork.

When the audience is small and known, **a log you own beats a dashboard you rent.** This is the *write*
side of §Google Sheets as a backend put to one use — recording opens into an Apps Script mailbox
(anyone can drop a row, only you can read the sheet). What's analytics-specific on top of the transport:
- `ping.js` **queues opens in `localStorage` and flushes when online** (fire-and-forget, loaded last,
  never blocks render) — offline opens are recorded at open time, delivered later.
- Identify users by a **one-way hash** of a stable name (first 4 bytes of SHA-256), never the name —
  the log holds no PII; reverse it against your own roster with a `=UID()` formula *in the sheet*.
  Empty uid = an anonymous open (a useful "a stranger found the URL" tripwire).
- **`URL_` empty = disabled but harmless** — ship the client before the backend exists; the backlog
  flushes when the URL lands.
- The **`usage/` dashboard** reads the same data back — a publish-to-web CSV of the pings tab (the read
  path from the table above), crunched in the browser (`usage/crunch.js`), stale-while-revalidate from
  localStorage, `noindex`. Names never enter the repo — uids only; join at runtime if you want them.

### Multi-page — the shared-nav pattern — `nav.css`
This skeleton is a one-pager, but the moment there's a second HTML page (AKM has seven), two things
change. **CSS splits** (already the rule: inline is fine for a strict one-pager, split to `styles.css`
the instant there's a second page), and you need a **shared nav that doesn't fork per page**. AKM's
pattern, worth copying: the nav markup is *static in each page's HTML* (no JS builds it — it must
render before the bundle so there's no flash), and one `nav.css` styles it by **reusing each page's
own palette tokens** (`var(--ink/--muted/--line/--accent)`) rather than hard-coding colors — so the
nav themes correctly (light **and** dark) on every page with zero per-page overrides. Mark the current
page with **`aria-current="page"`** (static in the markup, not a JS-added class — it's the semantic
signal *and* the style hook), and collapse the wordmark to an abbreviation at a narrow breakpoint so it
never wraps into the links. One `SHELL` in `sw.js` enumerates every page + its JS + data so the whole
app is offline, and — the earlier note bites here — the page an installed copy reopens daily should be
the root; "read once" pages (about, invite) are *separate* URLs you send.

### Deploy
GitHub Pages, `main`/root, relative paths → `user.github.io/repo/`. After deploy, open the URL
**online once** to prime the SW cache, then Add to Home Screen. The only thing verifiable *live* is a
real cross-origin fetch — if that data renders at the Pages URL, everything downstream is proven.

**Decide public vs private up front — it's an indexing + PII posture, not an afterthought.** A public
app is fine to leave crawlable. A **private participant tool** (AKM: a roster app for one festival's
players) should be un-findable: put `<meta name="robots" content="noindex,nofollow">` on **every**
page *and* a site-wide `robots.txt` (`Disallow: /`) — belt and suspenders, since the meta and the file
each cover cases the other misses — and keep PII out of the repo entirely (hold names in a private
sheet, join at runtime; no committed fixtures). Note a `noindex` page is still *public to anyone with
the URL* — indexing control is not access control.

**GitHub Pages isn't the only target — a private PWA can be self-hosted.** gallery-deck runs on a Mac
mini and reaches the phone over **Tailscale Serve (HTTPS)** instead of Pages; installability + the SW
+ offline all still matter *identically*, but the checklist reshapes — the share card, `robots`, and
"prime online once" drop to low-stakes for a tool only ever opened on your own tailnet. Two moves
worth stealing whatever the host: pick a **neutral hostname before any HTTPS cert is issued** (cert
hostnames land in *public* Certificate Transparency logs, so a descriptive name leaks the app's
existence to the world — access control the `noindex` above can't give you), and default a
private-network tool to **localhost-bind + a strict same-origin CSP** so it's not reachable or
embeddable beyond where you put it.

### Propagating a fix to downstream copies — `PROPAGATE.md`, `scripts/check-downstream.py`
Apps built from this skeleton **vendor its files by copy**, not by dependency — deliberately, since
the premise is that deployed files need no build step. The cost is that a fix here reaches nobody:
`sw.js`'s ungated cache write shipped to three apps before anyone noticed. A submodule or npm package
would solve tracking and break the premise, so the answer is copy *with provenance*.

The trap to avoid is comparing file contents. Every downstream copy is **legitimately modified** — its
own `SHELL` list, its own `V` prefix, branches deleted for features it doesn't use (boccherini and
haydn both correctly dropped the Google Fonts handler rather than carry dead code). A diff is always
non-empty, so it tells you nothing. The useful question is *"which commit of ours was this synced
from, and have we touched that file since?"* — which makes drift a **git range**, not a diff:

```js
// pwa-starter: sw.js @ bd16c21          ← one line, near the top, survives local edits
```

Three parts, each covering a failure the others don't:
- **The stamp is the registry.** A hand-kept `DOWNSTREAM.md` rots the first time you forget to add a
  repo, and fails silently. `check-downstream.py` instead walks a tree of clones, reads stamps, and
  — the part that matters — flags **unstamped files that are recognizably ours** by fingerprint, so a
  repo you forgot surfaces itself. (Its first run turned up a copy in `viz.runningwithdata.com` that
  hadn't come up in any manual audit.)
- **`PROPAGATE.md` supplies the judgment.** "4 commits behind `sw.js`" is noise if three are comment
  tweaks. Only entries needing downstream *action* get listed, so the checker can print a real to-do
  list and mark unlisted commits "may be cosmetic". Silence there is meaningful — keep it that way by
  not logging churn.
- **Ordering can matter.** `data.js`'s empty-payload guard must land *before* its cache-first paint,
  or a cosmetic bug becomes an app-wedging one. Say so in the entry; the sha order won't.

### Reproducible dev environment (for Claude sessions)
If a project needs system tools to build/test (a headless browser for screenshots, `rsvg-convert`
for icons, `qpdf` for PDFs), put them in a `tools/setup-environment.sh` that's idempotent and detects
a sandbox, and run it from a `SessionStart` hook — so a fresh cloud session can actually build.
Boccherini learned this the hard way (WebKit install fixes, a setup script). Don't make every session
rediscover the dependency list. **This skeleton ships it:** `tools/setup-environment.sh` checks
`rsvg-convert` + `pngquant` (the only build-time deps; the deployed app has none), reports what's
missing, and auto-installs *only* in an unattended env (CI / container / `SETUP_AUTO_INSTALL=1`) so it
never mutates a laptop unprompted — and it's wired to a `SessionStart` hook in `.claude/settings.json`.
It's idempotent + non-fatal (always exits 0), the two rules that make it safe to run every session.
The full human-readable dependency table lives in the README's *Toolchain* section. Note the lints
(`sw-lint.py`/`og-lint.py`) carry PEP 723 `# /// script` blocks, so `uv run` provisions Python for
them — but they pull no packages, so plain `python3` works identically; uv is a convenience, not a
requirement.

### Testing without a build — `package.json` as a dev-only harness
A no-build app can still have real tests — the trick is keeping the harness *off* the deployed site.
AKM keeps a `package.json` whose own description says it plainly ("the site itself is static, this is
just the test harnesses"): `private: true`, a `playwright-core` devDependency, and `node` test scripts
— **no bundler, no build step reaches the shipped files.** The site stays hand-written; the tests are
tooling that never deploys (same segregation as `scripts/`). Two patterns worth stealing:
- **Network-gate any test that hits live data — skip (exit 0), don't fail, when it's unreachable.**
  AKM's tests that read the live Google Sheet exit cleanly offline or in a locked-down sandbox instead
  of going red, so "no network" never reads as "broken" (same idea as `setup-environment.sh` being
  non-fatal). Pure-logic tests run off a committed fixture and pass anywhere; PII-bearing data gets no
  committed fixture, so its tests are live-only and gated.
- **Test the *working tree* on a real phone before pushing — a Node/Playwright harness can't see a
  touchscreen.** Touch-only bugs (a `click`/`pointerdown`/`touchstart` handler that only misfires on
  iOS — see the double-fire gotcha in §Mobile) need a real device. AKM's method: `python3 -m http.server
  8000 --bind 0.0.0.0` + `ngrok http 8000` for a public HTTPS URL, opened in an **iOS Safari Private
  tab — which doesn't register the service worker, so nothing caches** and every reload is the latest
  code. That last bit is the point: it rules out "is this my fix or a stale SW?" at the same time, the
  question that otherwise eats an hour on any installed PWA.

---

## Gotchas grab-bag (each cost time once, across these repos)

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
  tree in a Safari **Private tab** (no SW registration) via `ngrok`; see §Testing without a build.
- **CDN library (SheetJS, a chart lib) not cached** → installable via the manifest, but opens to a
  blank app on a plane. Precache the CDN URL in the SW or vendor a local copy (see §Offline).
- **SW cached a 404/502 body** → `fetch()` resolves on an HTTP error, so an ungated `c.put()` overwrites
  a good cached file with an error page that outlives the outage. Gate on `resp.ok` — but exempt
  opaque responses or you silently stop caching webfonts. (§Offline)
- **Cached an empty 200** → the degenerate response becomes your offline fallback. Under cache-first
  it wedges the app permanently (paint from a poisoned cache, reload, repeat). Gate `writeCache` on a
  validity predicate. (§Offline)
- **Static fallback file never committed** → the bottom offline tier 404s, and since it only fires
  after live *and* cache have both failed, you never notice until you're offline. Commit + precache it.
- **Sheets: all-digit / date-like values coerced** → `0042`→`42` (breaks an id/hash join), `2/3`→a
  `Date`; format Plain-text, read `.w` not `.v`, mind trailing-space tab names. (§Google Sheets as a backend)
- **No `viewport` / `viewport-fit` / safe-area** → tiny text, or content under the notch.
- **Meaning in color alone** (red/green status, a colored dot) → invisible to the ~8% of men who are
  red-green colorblind. Pair every color with a word, glyph, or shape.
- **Hover-only tooltip** → invisible on every phone. Give it a tap path — and mind the touch
  double-fire (tap = `mouseover` + `click`); see the kernel snippet in §Mobile.
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
  (Manage deployments → New version). See §Google Sheets as a backend for the rest.
- **Named the root the "invite" page** → installed copies open it daily; keep root = the daily app.
- **PII in the repo** → a `noindex` page is still public to anyone with the URL. Keep data in a
  separate view-only sheet, pulled at runtime, never committed.
