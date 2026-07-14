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
   - Do they want **usage analytics**? (If no, delete `usage/`, `ping.js`, `scripts/analytics.gs`,
     and the `ping.js`/`usage/` lines from `sw.js` + the `<script src="./ping.js">` in `index.html`.)
2. **Replace the placeholders** (they're deliberately grep-able). Search the whole tree:

   | Placeholder | Becomes | Where |
   |---|---|---|
   | `APP` | app / short name | index.html, manifest, usage, styles comment |
   | `APP — tagline` | real title | index.html `<title>`/OG, manifest `name` |
   | `One sentence on what this is.` | real description | index.html meta/OG |
   | `https://USER.github.io/APP/` | real absolute URL | index.html OG/canonical (must be absolute) |
   | `#f5f5f5` / `#1a1a1a` / `#2196f3` | real palette | styles.css vars, theme-color metas, manifest colors |
   | `app-v` | cache prefix (optional) | sw.js `V` **and** app.js `VER_PREFIX` (keep in sync!) |
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
the link and gets a grey box, or installs it and it won't open on a plane.

**Share / link preview** — `index.html` head, `scripts/make-og.sh`
- [ ] `<title>` + `meta[description]` are real (not a default)
- [ ] OG: `og:title/description/url/image` (+ `image:width/height/alt`)
- [ ] Twitter: `twitter:card=summary_large_image` + `title/description/image`
- [ ] **`og:image` is an ABSOLUTE https URL to a RASTER (PNG/JPG), 1200×630, compressed** — not relative, not SVG
- [ ] Card is **under the scraper size budget** — `make-og.sh` compresses + hard-fails over ~250 KB, and `og-lint.py` guards the commit (same pre-commit as `sw-lint.py`); a too-big card previews as a grey box
- [ ] The share image exists and renders (open it; paste the page URL into a chat to test the scrape)

**Icons / install** — `manifest.json`, `assets/`, `scripts/make-icons.sh`
- [ ] `icon.svg` source → 180/192/512 PNGs (generated, not hand-edited)
- [ ] `link[rel=icon]` (svg + png) + `link[rel=apple-touch-icon]` (180)
- [ ] `manifest.json` linked: `name`, `short_name`, `start_url:"./"`, `display:"standalone"`, icons incl. a `maskable`
- [ ] `apple-mobile-web-app-capable` + `-title` metas (iOS ignores the manifest)
- [ ] `theme-color`, one per color scheme

**Offline / cache-busting** — `sw.js`, `app.js`, `scripts/sw-lint.py`
- [ ] Service worker registered + precaching the shell (`SHELL` lists every offline-needed file)
- [ ] **A version constant `V` bumped on every shell change** — the #1 gotcha
- [ ] `app.js`'s `VER_PREFIX` matches `sw.js`'s `V` prefix (drives the "tap to update" tag)
- [ ] `sw-lint.py` wired into the pre-commit hook / CI
- [ ] Tested offline: load online once, kill the network, reopen — still works

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

**Print** (only if the app is meant to be printed / PDF'd) — `styles.css`
- [ ] `@media print` resets dark backgrounds to white/black (ink) and hides interactive chrome
- [ ] Remember links aren't clickable on paper — don't rely on them; show the URL/QR if it matters

**Analytics** (optional) — `ping.js`, `scripts/analytics.gs`, `usage/`
- [ ] Google-Sheet ping pattern wired, loaded last, offline-queued, no PII in the log
- [ ] `usage/` dashboard's `PINGS_CSV` points at the published pings tab

**Deploy**
- [ ] Relative paths throughout (works at `user.github.io/repo/`, not just a root domain)
- [ ] Opened at the real URL **online once** to prime the SW cache, then Add to Home Screen
- [ ] `.gitignore` keeps PII / large caches / generated previews out of the repo

---

## The maturity gradient (why the checklist exists)

The four source apps land at different points on exactly these axes; the gaps are the lesson.

| Capability | boccherini | haydn web | lobsters | AKM |
|---|:-:|:-:|:-:|:-:|
| Dark mode / responsive | ✅ | ✅ | ✅ | ✅ |
| Favicon / icons | ❌ | ✅ | ✅ | ✅ |
| OG / share card | ❌ | ✅ | ✅ | ✅ |
| `apple-*` / theme-color | ❌ | partial | ✅ | ✅ |
| Web app manifest | ❌ | ❌ | ✅ (runtime) | ✅ |
| Offline service worker | ❌ | ❌ | ✅ (inlined) | ✅ |
| Cache-bust discipline (`V` + lint) | — | — | — | ✅ |
| Usage analytics | ❌ | GoatCounter | ❌ | ✅ (own sheet) |

Git history says the retrofits were remarkably uniform: **share-sheet metadata + a preview image**
(added late in lobsters *and* both haydn pages), **dark mode** (a whole PR saga in boccherini,
including a separate pass just for print/PDF), **mobile layout and tap-fallbacks for hover tooltips**
(haydn's scatter, boccherini's "mobile tooltips"), **favicons + meta polish**, **analytics**, and in
boccherini even the **`viewport` tag itself**. This skeleton front-loads all of it.

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

### Offline & the service worker — **the cache-busting gotcha** — `sw.js`, `app.js`, `data.js`, `sw-lint.py`
The one that bites hardest and latest.
- The SW precaches `SHELL` and serves it cache-first (or network-first with cache fallback).
- **Bump `V` on every shell-file change.** A new `V` evicts the stale cache on `activate`. Forget it
  and your fix is in the repo but *never on anyone's phone* — iOS caches the SW aggressively. This
  bit AKM's "v77" rewrite (three commits, no bump, stale UI). `sw-lint.py` catches a staged `SHELL`
  file with an unchanged `V`.
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
  `V`, minus the human.

### Manifest / installability — `manifest.json`
`start_url:"./"` + relative `scope` so it works as a project page. Include a 512 `maskable` icon or
Android crops your square badly — and make the maskable a **full-bleed** tile (background fill, logo
inside the center-80% safe zone), not your transparent favicon, or the mask eats the edges. Note: an
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

### Analytics — an application of the sheet backend — `ping.js`, `scripts/analytics.gs`, `usage/`
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

### Deploy
GitHub Pages, `main`/root, relative paths → `user.github.io/repo/`. After deploy, open the URL
**online once** to prime the SW cache, then Add to Home Screen. The only thing verifiable *live* is a
real cross-origin fetch — if that data renders at the Pages URL, everything downstream is proven.

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

---

## Gotchas grab-bag (each cost time once, across these repos)

- **Forgot the share card** → the link previews as a blank grey box. Do OG + `make-og.sh` early.
- **Relative or SVG `og:image`** → no preview in iMessage/WhatsApp. Absolute + raster.
- **OG image too big** → some scrapers skip it (grey box). `make-og.sh` fails + `og-lint.py` guards the commit; keep it under ~250 KB.
- **Forgot to bump `V`** → fix ships to the repo, never to phones. `sw-lint.py` guards it.
- **SW caches its own version probe** → `checkVer()` fetches `./sw.js?_=<ts>` on every resume; if the
  fetch handler caches it, each resume writes a dead unique-key entry (unbounded growth between
  deploys), and any cache-first-`.js` adopter serves a stale probe back so "tap to update" never
  lights. Guard: `if (u.pathname.endsWith("/sw.js")) return;` before the network-first branch.
- **Webfont not in the SW cache** → offline opens fall back to system serif.
- **CDN library (SheetJS, a chart lib) not cached** → installable via the manifest, but opens to a
  blank app on a plane. Precache the CDN URL in the SW or vendor a local copy (see §Offline).
- **Static fallback file never committed** → the bottom offline tier 404s, and since it only fires
  after live *and* cache have both failed, you never notice until you're offline. Commit + precache it.
- **Sheets: all-digit / date-like values coerced** → `0042`→`42` (breaks an id/hash join), `2/3`→a
  `Date`; format Plain-text, read `.w` not `.v`, mind trailing-space tab names. (§Google Sheets as a backend)
- **No `viewport` / `viewport-fit` / safe-area** → tiny text, or content under the notch.
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
