# PROPAGATE.md — changes downstream copies need

Apps built from this skeleton **vendor its files by copy**, not by dependency (deliberately: the
whole premise is that the deployed files need no build step). So a fix here doesn't reach them —
someone has to carry it over. This file is the list of what's worth carrying.

**Not a changelog.** Only entries that require downstream *action* belong here. A reworded comment
or a placeholder rename doesn't. `scripts/check-downstream.py` reads this file to turn "you're 4
commits behind `sw.js`" into an actual to-do list, and prints "(no PROPAGATE.md entry — may be
cosmetic)" for commits that aren't listed, so silence here is meaningful.

Format — one bullet per commit, short sha first, under a heading per file:

```
## sw.js
- 0000000  what changed, and what downstream must do about it (#issue)
```

To see who needs what:

```
python3 scripts/check-downstream.py ~/Dropbox/Code
```

**Flow is two-way, and the stamp only tracks one direction.** Several of these apps predate the
skeleton — they're where its content came from — and were *later* updated to adopt improvements from
it, which makes them semantically downstream now. That relationship keeps changing: any app can turn
out to have solved something worth pulling back into the common core (that's how most of this file's
patterns got here). The stamp records "synced *from* pwa-starter at sha X" and says nothing about
work flowing the other way. So when an app grows something general, **port it here first and let the
stamp catch up** — don't leave it downstream and rely on remembering, which is the exact failure this
whole mechanism exists to prevent. `musiclog` is the standing example in both directions.

**Only stamp whole-file copies.** This mechanism tracks provenance per *file*, because that's the
granularity `git log <sha>..HEAD -- <file>` can answer. A fingerprint match proves only
*resemblance*, so confirm a file is genuinely vendored end-to-end before adopting it. Two categories
recur, and neither should be stamped:

**Independent implementations** — same idea, own code:

| Flagged | Why it isn't a copy |
|---|---|
| `quartet-log/src/app.js` (a.k.a. `viz.runningwithdata.com/musiclog`) | 573-line ES-module `export class App` vs. this skeleton's 178-line classic script. Shares only `VER_PREFIX`, the fingerprint. |
| `quartet-log/src/pullToRefresh.js` | Independent implementation, own prose and code — and it's the **ancestor**: this skeleton's version was written from it. |

quartet-log is the sharpest case of the two-way flow above: it originated the cache-first paint
(`3322370`) and the empty-payload guard (`fd71bde`) that became `ddd9ab8` here, and already has both.
Reporting it "behind" that commit is backwards. Review it by hand.

**Partial adopters** — vendored a *region*, not the file:

| Flagged | What it actually took |
|---|---|
| `haydn-info-card/web/app.js`, `quartets.boccherini.org/app.js` | 59 lines: `VER_PREFIX` + `checkVer` + `forceUpdate` only. No `render`/`paint`/`showStale`/data layer. |
| `gallery-deck/web/public/app.js` | 479 lines of its own app, with the same version-tag block grafted in. |

A file-level stamp on these is worse than none: it would report them behind every `app.js` commit
regardless of whether the change touched the ~20 lines they actually took, and `app.js` is the file
most likely to churn. The version-tag block also has its own natural sync signal — `VER_PREFIX` must
match `sw.js`'s `V` prefix — so it doesn't need this. **If a region gets big or subtle enough to
warrant tracking, split it into its own file first**, then stamp that.

**Stamping an app you didn't just sync?** Use `--at <sha>` with the commit it actually matches, not
`HEAD`. A stamp at HEAD claims it has changes it doesn't, and the checker will report it clean while
it's silently behind. When the true fork point is unknown, stamping at a known-good audit baseline is
honest as long as you only trust the log *forward* from there.

---

## sw.js

- dd763ca  The #7 offline family: per-file precache (`ensureShell()`), version-scoped reads
  (`cacheLookup()`), repair-then-directional-collect (`topUpThenCollect()`), terminal
  `offlineFallback()`, `cachePut()` skipping SHELL/redirects/206 with a caught `put()`, the
  non-GET guard, navigations-before-`.json`, and per-document `BOOT_DEPS`. Fixes a blank white
  screen offline (WebKit/iOS) whenever the precache is empty or partial, plus stale-generation
  shadowing and mixed-deploy shells. **Porting constraints, in force:**
  - Per-file puts **must land together with** repair-before-collect + the directional collect —
    per-file alone removes the guard `addAll`'s atomicity provided, and "keep the old cache as a
    net" alone ships a stale-shadowing bug (`CacheStorage.match()` is creation-order). The collect
    must be **re-runnable** (message handler, not just `activate`) and compare **numeric
    generations**, not `installing || waiting` (that guard alone is insufficient — skipWaiting).
  - If a copy ports only one thing, port `cacheLookup()` — it closes the shadowing class by
    construction and makes the rest less delicate.
  - New contract: **`V` must end in digits** (the tail orders generations for the collect and the
    version tag), and app.js's `VER_PREFIX` must equal the `V` stem. The version regex
    `const V\s*=\s*"([^"]*)"` is now shared by app.js and the lint — keep all three in agreement.
  - The **app.js companion is required, not optional** (the vendored version-tag region):
    `requestShellTopUp()` on load/foreground/`controllerchange`, `checkVer()` ranking by numeric
    tail among *non-empty* caches, anchored version parse. Without the ranking fix the tag lies
    the moment two generations coexist — which the SW change makes a normal state.
  - `offlineFallback()` needs a per-app constant block (title, copy, palette); `BOOT_DEPS` is
    per-app judgment — list only what each document *dies* without.
  Known affected: `gallery-deck/web/public/sw.js` (still carries the byte-identical `addAll`
  install + bare `.catch(...)` fallback chain). `haydn-info-card` ported + verified (its
  `0075239`, stamped @ dd763ca).
  `quartets.boccherini.org` is the *upstream* for this change (fixed in its #24, deployed as
  boccherini-v9) — don't re-port it; just re-stamp its provenance line at dd763ca. Downstream
  copies of `scripts/sw-lint.py` (boccherini's `tools/sw_lint.py`) should also pick up the
  comment-safe SHELL parser + the three new checks (paths exist, no cross-origin, numeric tail).
  (pwa-starter#7)

- 2ed87e9  Gate every cache write on `resp.ok` via `cachePut()` — a 404/502 is a *resolved* fetch,
  so the old ungated `c.put()` overwrote a good cached file with an error body that then survived
  as the offline fallback until the next `V` bump. Patch **both** call sites (network-first and
  cache-first branches). Keep the opaque-response exemption or you silently stop caching webfonts.
  Known affected: `haydn-info-card/web/sw.js`, `quartets.boccherini.org/sw.js`,
  `gallery-deck/web/public/sw.js`. (pwa-starter#5)

- e88a743  Route `.json` stale-while-revalidate instead of network-first. Apps whose data is a
  committed `.json` were blocking first paint on a network round trip for it on every cold start,
  even with a good cached copy. Move `json` out of the `live` regex and add the SWR branch. Only
  worth carrying if the app fetches JSON at boot — `haydn-info-card` (`opera.json`, 107 KB) and
  `quartets.boccherini.org` (`peters.json`/`parts.json`/`opera.json`) both do.

## data.js

- ddd9ab8  Never cache an empty/invalid payload: gate `writeCache` on an `opts.valid` predicate and
  treat a bad payload exactly like a network failure. A valid-but-empty `200` otherwise becomes the
  offline fallback — and under cache-first it wedges the app permanently, since `peek()` re-serves
  the poison on every reload. Carry this **before** adopting cache-first, never after.
  Known affected: `wtq/js/data.js:216` (`setCache(fresh)` with no gate; its parsers return `[]` on
  a tab-name miss, and the read-side guard `cached && cached.pieces` passes `[]` through as truthy).
  (pwa-starter#4)

  The **same commit** also adds `Data.peek()` / `Data.revalidate()` and makes `render()` cache-first
  (paint from cache synchronously, revalidate behind it, repaint only if `changed`), plus
  `applyUpdate()` to keep that second paint from yanking the page. Those are optional enhancements —
  but if you port them, **port the guard first**: cache-first is what turns the empty-payload bug from
  cosmetic into app-wedging.
