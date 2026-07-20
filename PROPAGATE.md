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

**Stamping an app you didn't just sync?** Use `--at <sha>` with the commit it actually matches, not
`HEAD`. A stamp at HEAD claims it has changes it doesn't, and the checker will report it clean while
it's silently behind. When the true fork point is unknown, stamping at a known-good audit baseline is
honest as long as you only trust the log *forward* from there.

---

## sw.js

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
