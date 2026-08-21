# Offline & the service worker — **the cache-busting gotcha** — `sw.js`, `app.js`, `data.js`, `sw-lint.py`

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

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
