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
| `quartet-log/src/updateChecker.js` (a.k.a. `viz.runningwithdata.com/musiclog`) | The version-tag region, split out of its `app.js` (the "split it into its own file" move prescribed below) — but an independent implementation, not the vendored block: it reads a build-emitted `version.json` instead of regex-parsing `sw.js` source, and compares content-hash `V` strings for equality (no numeric tail to rank). Discovery-only in `check-downstream.py` — its basename isn't a file we own, so it can't be stamped; its `app.js` no longer contains the fingerprint at all. |
| `quartet-log/src/pullToRefresh.js` | Independent implementation, own prose and code — and it's the **ancestor**: this skeleton's version was written from it. |

quartet-log is the sharpest case of the two-way flow above: it originated the cache-first paint
(`3322370`) and the empty-payload guard (`fd71bde`) that became `ddd9ab8` here, and already has both.
Reporting it "behind" that commit is backwards. Review it by hand.

Its 2026-08 architecture-hardening pass adds two standing **pull-back candidates**: the
`version.json` probe (its codegen writes `{"version":…}` next to `sw.js`, and the update check reads
that — no shared-V-regex contract, no parsing `sw.js` source) and the `gen_sw.mjs` codegen itself
(the SHELL list generated from the deploy directory's actual contents, and `V` a content hash over
every precached asset, so any asset change — icon, manifest, data — moves it; no hand-bumped
constant). Both presume a build step, so they'd land here as optional `scripts/` codegen, not as
changes to the no-build deployed files.

**Partial adopters** — vendored a *region*, not the file:

| Flagged | What it actually took |
|---|---|
| `haydn-info-card/web/app.js`, `quartets.boccherini.org/app.js` | 59 lines: `VER_PREFIX` + `checkVer` + `forceUpdate` only. No `render`/`paint`/`showStale`/data layer. |
| `gallery-deck/web/public/app.js` | 479 lines of its own app, with the same version-tag block grafted in. |

A file-level stamp on these is worse than none: it would report them behind every `app.js` commit
regardless of whether the change touched the ~20 lines they actually took, and `app.js` is the file
most likely to churn. The version-tag block also has its own natural sync signal — `APP_V` must
*equal* `sw.js`'s `V`, and `VER_PREFIX` must match its stem, both enforced by `sw-lint.py` — so it
doesn't need this. That signal only fires on a copy that kept those names, though: `AKM` renamed
its way out of both and went unnoticed through `#17`. **If a region gets big or subtle enough to
warrant tracking, split it into its own file first**, then stamp that.

**Stamping an app you didn't just sync?** Use `--at <sha>` with the commit it actually matches, not
`HEAD`. A stamp at HEAD claims it has changes it doesn't, and the checker will report it clean while
it's silently behind. When the true fork point is unknown, stamping at a known-good audit baseline is
honest as long as you only trust the log *forward* from there.

**A copy can be pinned out of tracking.** When a deployment makes a whole class of fixes moot,
append `pinned: <reason>` to the file's stamp line —

```js
// pwa-starter: sw.js @ 2ed87e9 pinned: tailnet-only, no real offline mode
```

— and the checker reports it separately (still showing how far it has drifted, so the decision
stays visible) instead of as an undone task, and never fails CI on it. The reason is mandatory
context for future-you; delete the clause to resume tracking. Pin the *file*, not the repo: a
pinned `sw.js` doesn't exempt a `data.js` sitting next to it. gallery-deck's `sw.js` is the
standing example — its content is served live by its backend and deliberately never cached
(`/api/media/*`), so it has no real offline mode and the offline-robustness family doesn't apply;
it stays pinned at `2ed87e9` unless it ever grows an offline content cache.

---

## sw.js

- 77fcb35  Serve the live branch (HTML/JS + navigations) **cache-first with a bounded network fallback** —
  fixes the "lie-fi" blank screen: `fetch()` only rejects on a genuine failure, so a slow-but-alive
  link (weak cell signal, half-answering captive portal) hung the old network-first
  `respondWith()` forever and WebKit painted a blank page, while truly-offline worked. **Port the
  pieces together, not à la carte:** (1) cache-first serve, gated on `bootable()` for navigations;
  (2) `withTimeout()` with TWO bounds — warm 3s (cached page in hand) / cold 15s (first run or
  evicted shell) — never unbounded; (3) a navigation **transient** `!resp.ok` (≥500, 408, 429)
  **throws** into the catch (a nav 5xx must not serve a cached-but-unbootable document) — but an
  **opaqueredirect passes through** (nav redirect mode is "manual", so a healthy 301 arrives as
  status 0 / ok:false and must reach the browser to be followed — GitHub Pages 301s slashless
  directory urls) and a **permanent 4xx passes through** (the server's real 404 beats an offline
  page that lies to an online user); this refines haydn#10, whose blanket throw has both bugs —
  port THIS version, including back into haydn; (4) the catch **re-reads the cache**
  (`cacheLookup || cached || shell || offlineFallback`) rather than trusting the pre-network
  snapshot — an `ensure-shell` repair can land inside the timeout window; this regression was
  introduced and caught once already during the original downstream rewrite; (5) the test harness
  `scripts/sw.test.mjs` — loads sw.js unmodified under mocked SW globals + a fake clock; keep its
  `process.exitCode = 1` hang guard or a hung handler drains node's event loop and exits 0,
  silently green on the exact regression the suite exists to catch. Adopter-visible trade: a
  deploy shows after the update-tag tap / SW swap, not on the very next reload. Corollary now
  load-bearing: **every live `.html`/`.js` URL must be in `SHELL`** (+ V bump) — a non-shell one
  is served cache-first with no revalidation until the old generation is collected.
  Known affected: `haydn-info-card` is the **upstream** for this change (its #10) — don't
  re-port the strategy, but DO back-port the opaqueredirect/404 refinement above, then re-stamp
  its `web/sw.js` at this sha. `quartets.boccherini.org` carries the old network-first live
  branch verbatim and needs the full port. `AKM/sw.js` (unstamped ancestor-pattern worker) is
  behind **three** families at once — the ungated `c.put` (2ed87e9), the #7 offline family
  (undefined-resolving catch, bare `addAll`-era precache), and this one — and its venue use case
  (weak signal at a concert hall) is the lie-fi scenario verbatim; treat it as a modernization
  pass, not a patch. `musiclog` has hand-ported this family (bounded warm/cold
  timeouts, opaqueredirect pass-through, never-undefined terminal fallback — its `static/sw.js`
  cites this sha) while deliberately staying network-first: its content-hashed `V` makes reload
  the natural freshness path, so the fix there is the bounds, not the strategy. `gallery-deck` stays pinned (no
  real offline mode; note lie-fi over its tailnet still blanks navigations — a bounded fallback
  would at least fail visibly if it ever unpins). (pwa-starter#9)

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
    **SUPERSEDED in part by `cef3cd2` (the `## app.js` section below): the ranking and the
    non-empty filter are gone.** They were treating a symptom — a cache key can't report what the
    page is running at all — and `APP_V` settles it at the source. If you are porting both entries
    at once, skip straight to the later one; `requestShellTopUp()` and the anchored parse still
    stand.
  - `offlineFallback()` needs a per-app constant block (title, copy, palette); `BOOT_DEPS` is
    per-app judgment — list only what each document *dies* without.
  Known affected: `haydn-info-card` ported + verified (its `0075239`, stamped @ dd763ca).
  `gallery-deck/web/public/sw.js` still carries the `addAll` install + bare `.catch(...)` chain
  but is **pinned** (tailnet-only; content is backend-served and never cached, so it has no real
  offline mode) — unpin and port if that ever changes.
  `quartets.boccherini.org` is the *upstream* for this change (fixed in its #24, deployed as
  boccherini-v9) — don't re-port it; just re-stamp its provenance line at dd763ca. Downstream
  copies of `scripts/sw-lint.py` (boccherini's `tools/sw_lint.py`) should also pick up the
  comment-safe SHELL parser + the three new checks (paths exist, no cross-origin, numeric tail).
  `musiclog` has hand-ported the load-bearing constraint (its `ensureShell()` tops up missing
  entries, verifies, and gates the collect on a verified-complete shell) — adapted, not copied:
  its content-hash `V` has no numeric tail to order generations by, so the collect keys on
  completeness instead of direction, with old generations serving via `caches.match()` until the
  new shell completes. (pwa-starter#7)

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
  `quartets.boccherini.org` (`peters.json`/`parts.json`/`opera.json`) both do. `musiclog` has
  hand-ported it (boot blocks on its work catalogs; its revalidation writes under the bare
  pathname so versioned `?v=<hash>` requests replace the precached entry instead of piling up
  per-hash copies that lose every `ignoreSearch` match).

---

## app.js

- cef3cd2  **The version tag compares `APP_V` — the running bundle — instead of the Cache Storage
  key.** A key describes what is stored, not what the page is executing, and after a worker
  activates those differ permanently: `sw.js` calls `skipWaiting()`/`clients.claim()` and
  `topUpThenCollect()` drops older generations, so the key set flips to the new version while the
  open page keeps running the bundle it parsed at launch (`clients.claim()` reloads nothing).
  `checkVer()` then found `installed === latest`, set `behind = false`, and left `tag.onclick`
  null — a device stranded one release back was told it was current, with the one affordance that
  unsticks it by hand hidden, because the tag did not believe an update existed. A standalone PWA
  that is never force-quit holds that state indefinitely. **Port all three pieces:** (1) a
  `const APP_V` declared next to `VER_PREFIX` and kept equal to `sw.js`'s `V`; (2) `behind`,
  `textContent` and the tag title reading `APP_V` instead of `installed`; (3) the cache lookup
  reduced to a boolean "is a worker installed at all" — **drop the ranking and the non-empty
  filter with it.** Both existed to stop the key from lying about currency, which `APP_V` settles
  at the source, and keeping the filter now does active harm: it hides the tag on a device whose
  new cache is still the empty placeholder `ensureShellOnce()` opens, which is precisely the
  stranded device it was written to protect. `scripts/sw-lint.py` check 6 enforces the
  `APP_V`/`V` pair; carry that too, or the contract is prose again.
  Known affected — the full precondition is *reads `installed` from `caches.keys()`* **and** *ships
  a worker that calls `skipWaiting()` + `clients.claim()`*, and every copy below was checked
  against both:

  | Copy | State |
  |---|---|
  | `quartets.boccherini.org/app.js:45` | current block verbatim — straight port |
  | `lissajous-tuner/app.js:661` | current block verbatim, but see the note below |
  | `quartet-composers/app.js:1308` | current block verbatim — straight port |
  | `haydn-info-card/web/app.js:46` | current block verbatim — straight port |
  | `AKM/app.js:1215` | independent `SWVER`/`NEWVER` variant, same flaw — hand-carried |
  | `gallery-deck/web/public/app.js` | **fixed** at `gd-v24`; where the bug was found |
  | `quartet-log/src/updateChecker.js:38` | independent implementation, same flaw — hand-carried |

  Two of these need more than a copy-paste. `lissajous-tuner` **already has the value it needs**:
  `build.js` carries a deploy-stamped `.v`, loaded by the same document load as `app.js`, so it is
  a genuine running-bundle marker — its own comment already admits the gap ("they agree unless the
  cache is mid-swap"). Change which value it compares rather than adding a constant. And
  `quartet-log` has the flaw despite already using the `version.json` probe this file lists as a
  pull-back candidate: that probe improves how `latest` is obtained and is **orthogonal** to this,
  which is on the `installed` side — its own comment still says "the installed version is just the
  `ql-` cache key". It is discovery-only here, so it needs a hand-carried fix, and its content-hash
  `V` has no numeric tail to rank, which makes the boolean gate the natural shape there anyway.

  `AKM` is the cautionary one: it was invisible to `check-downstream.py` for this entire bug's
  lifetime, because `app.js` was fingerprinted on the single string `VER_PREFIX` and AKM's copy
  inlines the prefix as `/^akm-v/`. The same commit makes every fingerprint a *tuple* — see the
  `scripts/` note below. (pwa-starter#17)

  The **same commit** adds a README note on what the host must do: don't let the shell be served
  with **heuristic freshness**. Not a code change, but it is the second, independent cause of the
  identical symptom — a host that sends no `Cache-Control` lets the browser invent a lifetime from
  `Last-Modified` and answer from the HTTP cache without contacting the server, so the version
  reads current while the bundle goes stale. Only the **cold** path is exposed (the shell is served
  cache-first, and the per-file precache uses `cache: "reload"`): the live branch's bounded network
  fallback on a first run or an evicted shell, plus whatever `cachePut()` stores. Only downstreams
  that host their own shell need it — GitHub Pages sends `max-age=600` + ETag, an explicit lifetime,
  which is enough to stop the guessing. `gallery-deck` hit both causes at once (its shell is served
  by Starlette's `StaticFiles`, which sends no `Cache-Control` at all).

---

## sw-lint.py

- 857fc28  **Check 7, `--base REF`: the V comparison a single commit cannot make.** Checks 1-6 read
  one commit, which is all the pre-commit hook has. Two branches off one base can each bump
  `v32 -> v33` byte-identically; the three-way merge resolves that **without a conflict**, and the
  second one lands its shell changes with a net `V` delta of **zero**. Each side was right about
  its own parent and the merged result is stale on every installed client. Ported up from
  `quartet-composers`, which paid for it (its #32) — the direction `PROPAGATE.md`'s preamble asks
  for. **Port all four pieces:** (1) `tail_of()`; (2) `base_check()`, reading *what changed* from
  the **merge base** (the diff a rebase, squash and stacked branch all leave alone) and *which V
  it must clear* from **REF's tip** (against the merge base, the motivating case passes); (3) the
  `--base` dispatch in `main()`, which REPLACES checks 1-6 rather than joining them; (4)
  `scripts/sw-lint.test.py`, which builds real throwaway repos with real branches — the incident
  is invisible to any test that builds one branch, so the harness is the check's evidence, not
  decoration.

  Two things a copy gets wrong if it ports the code without the reasoning. The touched set is the
  **union of both `SHELL` lists**, because dropping an entry is itself a shell change (clients that
  cached it keep serving it from the old generation until `V` moves) — upstream's harness has a
  case for exactly this that the original lacked. And "I could not read the base" is **reported,
  not skipped**: a check that passes when it could not run is the failure mode the whole thing
  exists to close.

  Wiring: CI on pull requests only, with **`fetch-depth: 0`** — the default shallow checkout has no
  merge base, and the check will correctly refuse to pass. Not in the pre-commit hook, which has
  neither side of the merge. Numbering note for adopters: this is **check 7 here** because 6 is the
  `APP_V` pair (#17); in `quartet-composers` the same code is check 6. (pwa-starter#15)

---

## check-downstream.py

Upstream-only — no copy of this exists downstream. It is listed because it is how you find out
whether the entries above ever landed, so a gap in it is a gap in all of them.

- cef3cd2  **Fingerprints are now a tuple per file, matched with `any()`.** A single fingerprint is
  a single point of failure, and it failed silently: `app.js` was recognized only by the literal
  `VER_PREFIX`, so `AKM/app.js` — which inlines its prefix as `/^akm-v/` — never appeared in any
  scan, stamped or candidate, while carrying the `#17` bug. Widening it surfaced four previously
  invisible copies (`AKM/app.js`, `AKM/ping.js`, and quartet-log's two generated `sw.js`). If you
  maintain your own copy of this script, name several independent landmarks per file so one local
  rename can't switch discovery off. (pwa-starter#17)

- 854d957  **The three `scripts/` files are tracked now, and `SHARED` carries each file's path
  here.** `sw-lint.py`, `og-lint.py` and `sw.test.mjs` are vendored like everything else and were
  never in `SHARED`, so the walk never yielded them — downstream copies have been carrying
  `pwa-starter: sw-lint.py @ <sha>` stamps that **nothing read**. Adding them exposed the second
  half: drift is `git log <sha>..HEAD -- <name>`, git reads that as a pathspec, and a bare
  basename matches nothing for a file at `scripts/…`. Tracked-but-always-clean is worse than
  untracked — it turns a gap into a green light — so `SHARED` is now `basename → (path here,
  fingerprints)` and `main()` self-checks that every path still exists. Two copies are
  deliberately **not** fingerprinted: `AKM/scripts/sw-lint.py` and
  `gallery-deck/scripts/sw-lint.py` implement check 1 and nothing else, in their own words —
  independent works that share the idea, not the code, and flagging them would report them behind
  commits they were never going to take. (pwa-starter#15)

  Turning this on surfaced a downstream in **no** registry: **`github-month-review`** vendors
  `og-lint.py`, `make-icons.sh` and `make-og.sh` — the share-card and icon layer — and has no
  `sw.js`, no `manifest.json` and no worker registration at all. It is a legitimate partial
  adopter of the sharing half, not a lapsed PWA; offline entries do not apply to it. Noted here so
  it stops reading as an unexplained gap on every scan.

---

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

---

## .nojekyll

- f54b770  **Add an empty `.nojekyll` to your repo root.** Without it GitHub Pages builds
  the repo with Jekyll, which renders every markdown file in it through Liquid — `CLAUDE.md`,
  `PROPAGATE.md`, any note you keep — and excludes every path beginning with `_` from the output.
  Neither is anything a skeleton app asked for, and both fail in the same direction: silently, at
  deploy time, days after the commit. quartet-composers is the worked example. `dce5a99` there
  documented a parse bug by quoting the literal it had misread, "as the literal `` {{ ``", and an
  unterminated `{{` is a Liquid PARSE error rather than a bad substitution — so the build died,
  `pages build and deployment` went red, and the site served its last good commit for two days
  while two merges landed on top of it. Nobody noticed until a reader said the version tag looked
  old.
  **Presence is the whole content**, so this one cannot carry a provenance stamp — an empty file
  has nowhere to put a comment, and `check-downstream.py` finds copies by stamp. Check it with
  `ls -a`, not with the scan. Adding it is safe wherever the app is the tree it publishes: no
  `_config.yml`, no front matter, no Liquid in `index.html`. If a downstream DOES want Jekyll to
  render something, it wants a `_config.yml` instead — and then it owns an `exclude:` list that
  every new doc has to be added to, which is the trade this file exists to warn about.
