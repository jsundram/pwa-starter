---
name: scaffold
description: Turn the pwa-starter skeleton into a new app — ask the essentials, replace the placeholders, generate icons and the share card, and verify it installs and works offline. Use when starting a new PWA, bootstrapping a project from pwa-starter, or making a new project based on the skeleton.
---

# Scaffold a new PWA from pwa-starter

## Step 0 — get the files

The skeleton is a **GitHub template**, and the new app wants its own git history — so the files come
from the repo, not from this plugin (an installed plugin lives in a cache, and a second copy of
`sw.js` would drift from the stamped original).

- *Use this template* on <https://github.com/jsundram/pwa-starter>, or
- `git clone --depth 1 https://github.com/jsundram/pwa-starter <name> && rm -rf <name>/.git && git -C <name> init`

Then work inside that directory.

Turn the skeleton
into *their* app. Do this in order:

1. **Ask the essentials** (one short round, don't guess):
   - App name + one-word short_name (home-screen label)
   - One-line tagline and one-sentence description
   - The eventual URL (`https://<user>.github.io/<repo>/` for Pages) — needed for absolute OG tags
   - Do they want **usage analytics**? Two tools, picked by audience ([references/data-analytics.md](../../references/data-analytics.md)): **GoatCounter**
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
4. **Wire analytics** (if wanted) per [references/data-analytics.md](../../references/data-analytics.md) — it's ~10 minutes and the app works fine without
   it (`URL_` empty = silently disabled).
5. **Verify** against [references/checklist.md](../../references/checklist.md) before declaring done. At minimum: it loads at a local
   server, installs, survives offline (load once, kill network, reopen), and the share card renders.
6. **Enable the hook:** `git config core.hooksPath .githooks` (the cache-bump guard).

Then hand back a short list of what's still on the user: deploy (flip on Pages), open once online to
prime the cache, Add to Home Screen.


## Step 7 — delete what belongs to the skeleton, not to the app

Root is both the deployed app *and* the template, so a fresh instance inherits this project's own
tooling. Remove:

- `.claude-plugin/` and `plugins/` — the marketplace and skills for *pwa-starter*, not for the new app
- `docs/plans/` — this project's planning docs
- `PROPAGATE.md` — the registry of pwa-starter's downstream copies

Keep `scripts/`, `tools/`, `.githooks/` and `.github/`: the lints, the toolchain check and CI are
exactly what the new app wants. Keep the `// pwa-starter: <file> @ <sha>` stamps — they are how the
new app stays tracked; see [propagate](../propagate/SKILL.md).

## Done when

- `grep -rn "APP\|USER.github.io\|One sentence on what this is" . --exclude-dir=.git` returns nothing
- `scripts/make-icons.sh && scripts/make-og.sh` succeed, and every icon path in `manifest.json` 200s
- `python3 scripts/sw-lint.py` and `node scripts/sw.test.mjs` both exit 0
- the deletions above are done — no `.claude-plugin/`, no `plugins/`
- it loads under `python3 -m http.server 8000`, installs, and survives load-once-then-offline
