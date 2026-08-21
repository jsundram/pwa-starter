# CLAUDE.md — pwa-starter

Briefing for Claude Code **working on this repo**. If you came here to *use* the skeleton — scaffold
an app, audit one, propagate a fix — that lives in the plugin, not here:

| Want to | Run | Source |
|---|---|---|
| Audit an existing app against the checklist | `/pwa-starter:audit` | `plugins/pwa-starter/skills/audit/` |
| Start a new PWA from this skeleton | `/pwa-starter:scaffold` | `plugins/pwa-starter/skills/scaffold/` |
| Carry a fix out to downstream copies | `/pwa-starter:propagate` | `plugins/pwa-starter/skills/propagate/` |

Install once, then they work in any repo:

```sh
/plugin marketplace add jsundram/pwa-starter
/plugin install pwa-starter@jsundram
```

The knowledge itself lives in [`plugins/pwa-starter/references/`](plugins/pwa-starter/references/):
`checklist` (the rubric) plus deep dives — `offline`, `sharing-install`, `mobile-a11y`,
`data-analytics`, `deploy`, `testing`, `gotchas`, `history`.

## What this is

An opinionated skeleton for a small, static, single-author PWA: a few HTML files, no backend, hosted
on Pages/Netlify, opened on a phone and installed to the home screen. **Pure-pull, self-contained
output** — the deployed files depend on no build step, and *opening the app is the refresh*. Not for
framework/SPA apps, real backends or auth, or large teams; the value is that it fits in your head.

The repo is three things at once, and the rules below exist because two of them break quietly: the
**template** new apps copy, the **common core** those apps vendor by copy, and the **registry** that
tracks where the copies are.

---

## File hierarchy (opinionated)

Deployed files live at the repo root (so GitHub Pages "deploy from root" just works and every path
stays relative). Everything that is *not* shipped to the browser is segregated:

- **Root** = the deployed app *and* the template a new project copies: `index.html`, `styles.css`,
  `app.js`, `sw.js`, `manifest.json`, `ping.js`, plus `theme.js` (three-state theme + the
  JS-baked-color contract), `data.js` (stale-while-revalidate with a timeout) and the optional
  `pullToRefresh.js` (standalone-only gesture).
- **`assets/`** = icons + share card; `icon.svg`/`og.svg` are the sources, the PNGs are generated.
- **`usage/`** = the self-contained analytics dashboard (own page, precached, `noindex`).
- **`scripts/`** = tooling that never ships: rasterizers, `sw-lint.py`, `og-lint.py`,
  `check-downstream.py`, `sw.test.mjs`, `analytics.gs`.
- **`tools/`**, **`.githooks/`**, **`.github/`** = setup script, warn-only pre-commit, CI.
- **`plugins/pwa-starter/`** + **`.claude-plugin/`** = the skills and references. Self-contained on
  purpose: an installed plugin is copied to a cache and cannot read files outside its own directory,
  so nothing in there may reference `../../sw.js`. **The scaffold workflow deletes both** — root is
  also the template, and a new app must not inherit this project's plugin manifest.

**CSS is a separate `styles.css`**, and **`app.js` owns boot** while `index.html` owns structure —
no logic in the HTML beyond loading the scripts.

---

## Rules for changing this repo

**Never move, rename, or gratuitously touch a stamped file.** Those are `sw.js`, `app.js`, `data.js`,
`theme.js`, `ping.js`, `pullToRefresh.js`. Downstream copies carry `// pwa-starter: <file> @ <sha>`,
and `scripts/check-downstream.py` computes drift as `git log <sha>..HEAD -- <basename>` — so a rename
silently breaks tracking, and a comment-only touch flips every copy in the fleet to `BEHIND 1`. If a
change is cosmetic, keep it out of these files; if it is real, add a PROPAGATE.md entry.

**Bump `V` in `sw.js` on every shell change.** A new `V` is the only thing that triggers the install
that writes precached files — forget it and the fix is in the repo but never on anyone's phone. Keep
`V`'s **numeric tail** (rename the stem freely): it orders cache generations for the directional
collect and for `checkVer()`'s ranking. `app.js`'s `VER_PREFIX` must match `V`'s stem. `sw-lint.py`
enforces all of this.

**Every live `.html`/`.js` URL must be in `SHELL`.** The shell is served cache-first with no
revalidation, so a non-shell page or script is served stale until a `V` bump collects the old
generation. New page or script → add it to `SHELL` and bump. Never lean on opportunistic caching.

**`offlineFallback()` deliberately breaks two repo rules** — its CSS is inline and it hardcodes the
palette plus `system-ui`, because it renders precisely when `styles.css` and any cached font are
unreachable. Rebrand it with the rest; don't "fix" it.

**Icons and the share card are generated.** `assets/icon.svg` and `og.svg` are the sources of truth;
never hand-edit the PNGs. `scripts/make-og.sh` hard-fails over ~250 KB and `og-lint.py` re-checks the
staged card, so card size is enforced rather than remembered.

**PROPAGATE.md is not a changelog.** Only entries that require downstream *action* belong in it —
`check-downstream.py` prints "(no PROPAGATE.md entry — may be cosmetic)" for unlisted commits, so
silence there is meaningful. Keep it that way by not logging churn. Ordering can matter: say so in
the entry when one change must land before another.

**Stamp only whole-file copies.** A fingerprint match proves resemblance, not provenance. Independent
implementations and partial adopters (a vendored *region*) must stay unstamped — a file-level stamp on
those reports them behind every commit regardless of whether it touched the lines they took.

**Before you commit:** `python3 scripts/sw-lint.py && node scripts/sw.test.mjs`. Enable the hook once
per clone with `git config core.hooksPath .githooks`. CI runs both with real exit codes; the
staged-diff checks (the `V` bump, the OG card size) only bite locally in the hook.

---

## Dev environment

`tools/setup-environment.sh` checks the only build-time deps — `rsvg-convert` and `pngquant`; the
deployed app has none — and auto-installs *only* in an unattended env (CI / container /
`SETUP_AUTO_INSTALL=1`) so it never mutates a laptop unprompted. It is idempotent and always exits 0,
the two properties that make it safe to run every session, and `.claude/settings.json` runs it from a
`SessionStart` hook. The README's *Toolchain* table is the human-readable version. The lints carry
PEP 723 blocks so `uv run` works, but they pull no packages — plain `python3` is equivalent.
