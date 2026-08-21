---
name: audit
description: Audit a web app against the pwa-starter checklist — share card, offline, installability, mobile, dark mode, accessibility — and report the gaps with evidence. Use when asked to audit an app, check what's missing versus pwa-starter, or find out whether a site is installable, offline-capable, or shareable.
---

# Audit an app against the pwa-starter checklist

Assess the app **in the current repo** against the checklist and report gaps. Do not rewrite the app.
Offer fixes; apply them only when asked, and port the *pattern*, never this skeleton's placeholder
styling — the target keeps its own design language.

The rubric is [`references/checklist.md`](../../references/checklist.md). Load a deep dive only when
the checklist flags that area: [offline](../../references/offline.md) ·
[sharing & install](../../references/sharing-install.md) ·
[mobile & dark mode](../../references/mobile-a11y.md) ·
[data & analytics](../../references/data-analytics.md) · [deploy](../../references/deploy.md) ·
[testing](../../references/testing.md) · [gotchas](../../references/gotchas.md).

## Step 1 — classify, before applying a single row

The checklist's advice is wrong for some classes if applied blindly. **Classify by what reaches the
browser, not by what built the site** — a React SSG that renders to static HTML is, for almost every
row, an ordinary static site. Classifying off the dependency list gets this backwards.

| Class | Signal (in the **output**) | What applies |
|---|---|---|
| **A** · static, no build | hand-written `index.html`; no build script | Everything, including the `V`-bump + `sw-lint` discipline |
| **B** · static *from* a build | a build emits `dist/`/`public/` of plain HTML; little or no runtime framework | Everything **except** cache-busting: content-hash the shell instead of hand-bumping `V` (see offline.md, "Have a build step?"). Audit the **generator** |
| **C** · runtime framework / SPA | a framework bundle + router ship to the browser; one shell HTML | Share card, icons, manifest, mobile, dark mode, a11y. Offline belongs to the framework (Workbox / `vite-plugin-pwa`) — report, don't retrofit `sw.js` |
| **D** · has a backend | a server, a DB, authed endpoints | Say so, stop at the offline family; see history.md (gallery-deck) |

State the class and the evidence for it in the first line of your report.

## Step 2 — read, don't glob

**Never conclude a feature is absent because a file is absent.** `lobsters-and-lighthouses` builds
its manifest at runtime as a Blob URL and inlines its service worker; a file-presence scan reports it
as having neither and is wrong twice — about the app the references cite for exactly that trick.

- Grep for the *behavior*: `serviceWorker.register`, `rel="manifest"`, a constructed Blob, `og:image`.
- For class B and C, read the files that **generate the `<head>`** — page templates, the SSG entry,
  the build script — plus the built output if it is available. A class-B app with no root
  `index.html` must never be reported as "everything missing".
- Check that referenced assets actually resolve. A manifest naming an icon that 404s fails silently.

## Step 3 — walk the checklist

Work [`references/checklist.md`](../../references/checklist.md) top to bottom. For every row record
✅ / ⚠️ / ❌ **with specific evidence** — the missing tag, the unversioned cache, the hover-only
tooltip — cited as `file:line`. "Looks fine" is not a finding; neither is a gap with no location.

Skip rows the class rules out, and say which you skipped and why.

## Step 4 — report

A table, **worst-first**, each row naming the fix and roughly what it costs.

| Gap | Evidence | Fix | Cost |
|---|---|---|---|

Lead with the high-leverage misses — share card, offline, cache-busting — over nitpicks. A link that
previews as a grey box outranks a missing `:focus-visible`.

Close with: the class and why, anything skipped, and an offer to apply a named subset. Then stop.

## Calibration

The known-answer case is `jsundram/quartet-chooser` (class B: `scripts/build.mjs` is a hand-rolled
SSG; React runs only at build time via `renderToStaticMarkup`; the browser gets static HTML, inlined
CSS and two dependency-free scripts). A correct audit finds at least:

- `og:image` is an **SVG** on every work and composer page (`src/lib/utils.js:44` →
  `src/templates/work.js:148`) — no preview in iMessage/WhatsApp/Slack
- the home card is a 512×512 square, not a 1200×630 raster (`src/pages/index.js:43`)
- no `twitter:card`, `og:url`, `og:type`, `og:image:width/height/alt`, no `<meta name="description">`
- `static/manifest.webmanifest` has **icons and nothing else** — no `name`, `short_name`,
  `start_url`, `display`, no `maskable` → installs unnamed on Android
- no `apple-mobile-web-app-*` metas; no 180×180 apple-touch-icon (sizes jump 144→192)
- no `theme-color`, no `color-scheme: light dark`; `viewport` lacks `viewport-fit=cover`
- no service worker — and it is a rehearsal-room app

An audit that misses the SVG `og:image`, or that tells this app to hand-bump a `V` constant, is wrong.
