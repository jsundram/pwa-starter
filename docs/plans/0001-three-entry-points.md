# Plan 0001 — Three entry points: propagate, audit, scaffold

**Status:** proposed · **Branch:** `claude/pwa-starter-future-sn3mnd` · **Base:** `3ec3032`

This document is both the **work order** and the **review rubric**. Execute the phases in order;
review each one against its *Done when* checks. Every check is a command whose output you can paste
into a PR. Nothing here is finished because it was written — only because its checks pass.

---

## Context

`pwa-starter` began (2026-07-12) as a checklist distilled from four hand-built PWAs. Four weeks
later it does four different jobs, and the file that grew fastest — `CLAUDE.md`, 283 → 850 lines —
is trying to serve all four at once while being injected in full into every session in this repo.

| Job | Artifact | Churn | Status today |
|---|---|---:|---|
| 1. Keep downstream copies in sync | `PROPAGATE.md`, `scripts/check-downstream.py`, stamps | 204 + 285 | Works, but runs only when remembered |
| 2. Audit an existing app | CLAUDE.md §checklist + §Patterns + §Gotchas | 1048 | Needs manual setup in every target repo |
| 3. Bootstrap a new project | `index.html`, `styles.css`, `manifest.json`, `assets/` | 1–2 commits each | Works; the files are finished |
| 4. Be the shared common core | `sw.js`, `app.js`, `data.js`, `theme.js` | 774 + 313 | Works; this is what actually gets maintained |

Jobs 1 and 4 **require** a git repo — the provenance stamp is `pwa-starter: sw.js @ <sha>` and drift
is `git log <sha>..HEAD -- sw.js`. Job 3 is already correctly a GitHub template. Only job 2 wants to
be a skill, and it is the one served worst today.

**So: the repo stays a repo.** What changes is that the knowledge stops living in project
instructions and starts living in a plugin published *from* this same repo — one tree, three ways in.

### Target shape

```
pwa-starter/
├── index.html  styles.css  manifest.json  assets/  usage/   ← template (untouched)
├── sw.js  app.js  data.js  theme.js  ping.js  pullToRefresh.js  ← STAMPED — must not move
├── scripts/  tools/  .githooks/  .github/  PROPAGATE.md      ← untouched
├── CLAUDE.md                          ← slimmed to ~85 lines of maintainer rules
├── docs/plans/0001-three-entry-points.md   ← this file
├── .claude-plugin/marketplace.json     ← NEW
└── plugins/pwa-starter/                ← NEW (the plugin; copied to a cache on install)
    ├── .claude-plugin/plugin.json
    ├── skills/{audit,scaffold,propagate}/SKILL.md
    └── references/*.md                 ← the prose moved out of CLAUDE.md
```

After install: `/pwa-starter:audit`, `/pwa-starter:scaffold`, `/pwa-starter:propagate` — in any repo.

---

## Invariants

These must hold **after every phase**, not just at the end. They are the audit backbone; re-run them
at any commit.

| # | Invariant | Check |
|---|---|---|
| I1 | No stamped file moved, renamed, or changed | `git diff --stat 3ec3032..HEAD -- sw.js app.js data.js theme.js ping.js pullToRefresh.js` is **empty** |
| I2 | Downstream report is byte-identical to baseline | `diff /tmp/downstream-before.txt /tmp/downstream-after.txt` |
| I3 | `PROPAGATE.md` still parses (the reader is literal about `## <file>` / `- <sha> note`) | `git diff 3ec3032..HEAD -- PROPAGATE.md` is empty, **or** I2 passes |
| I4 | No history rewrite | `git merge-base --is-ancestor 3ec3032 HEAD` exits 0 |
| I5 | Shipped app still lints and tests green | `python3 scripts/sw-lint.py && node scripts/sw.test.mjs` |
| I6 | No prose lost in the move | word-count check in Phase 1 |

**Why I1 matters more than it looks.** `check-downstream.py` computes drift as
`git log <sha>..HEAD -- <basename>`. Touch `sw.js` for a comment tweak and every stamped copy in the
fleet flips to `BEHIND 1` with `(nothing listed in PROPAGATE.md — likely cosmetic)`. The tool handles
it gracefully, but the signal degrades. **A documentation refactor must never touch a stamped file.**
If a phase genuinely needs to, split it into its own commit and add a PROPAGATE entry.

---

## Phase 0 — Baseline

Cheap, and it is what turns "we kept the downstream relationships" from a hope into a check.

**Do**

1. `python3 scripts/check-downstream.py ~/Dropbox/Code > /tmp/downstream-before.txt 2>&1; echo "exit=$?" >> /tmp/downstream-before.txt`
2. `python3 scripts/sw-lint.py; node scripts/sw.test.mjs` — record both exit codes.
3. `wc -w CLAUDE.md > /tmp/claudemd-before.txt`

**Done when**

- [ ] `/tmp/downstream-before.txt` exists and its trailing summary line is recorded in the PR body.
- [ ] Both lints/tests pass at base (if they do not, fix that *first*, on its own branch).

**Review:** the PR body quotes the baseline summary line (`N up to date, N behind, …`). Without it,
I2 is unverifiable and the whole "keep downstream relationships" claim is unaudited.

### Baseline as measured (2026-08-21, all 46 account repos enumerated)

```
4 up to date, 0 behind, 1 pinned, 3 untracked, 0 unusable
```

**The fleet is fully in sync.** Every stamped copy verified to genuinely carry the post-#9 code
(`withTimeout`, `isTransientStatus`, `cacheLookup`, `bootable`, `offlineFallback` all present) — the
stamps are truthful, not merely present.

| Repo · file | State |
|---|---|
| `AKM/sw.js` | stamped `@ 3ec3032`, current (`akm-v109`) |
| `haydn-info-card/web/sw.js` | stamped `@ 3ec3032`, current (`haydn-v16`) |
| `haydn-info-card/web/app.js` | stamped `@ dd763ca` — which *is* the last `app.js` commit |
| `quartets.boccherini.org/sw.js` | stamped `@ 3ec3032`, current (`boccherini-v9`) |
| `gallery-deck/web/public/sw.js` | pinned `@ 2ed87e9`, 7 behind, reason recorded — working as designed |
| `quartet-log/src/pullToRefresh.js` · `quartets.boccherini.org/app.js` · `gallery-deck/web/public/app.js` | untracked candidates — all three are **deliberate** non-stamps already documented in PROPAGATE.md |
| `quartet-chooser`, `haydnenthusiasts.org`, `haydn-lowdn`, `boccherini-sampler`, and every other account repo | **not copies** — no skeleton basenames, none of the six fingerprints |

Two problems this baseline exposes, both fixed in Phase 5:

1. **PROPAGATE.md's `#9` known-affected notes are stale in the opposite direction from the one this
   machinery guards against.** Entry `64b442d` still says `quartets.boccherini.org` "carries the old
   network-first live branch verbatim and needs the full port" and that `AKM/sw.js` is an "unstamped
   ancestor-pattern worker … behind three families at once … treat it as a modernization pass." Both
   were done and stamped; the note was never updated. The tooling catches copies falling behind the
   doc — nothing catches the doc falling behind the copies.
2. **The three untracked candidates are permanent false positives.** Each is a documented, correct
   decision not to stamp, but `check-downstream.py` has no way to record that: `pinned:` lives
   *inside a stamp*, and a non-copy must not carry a stamp. So every scan, forever, reports three
   items that are working as intended — the same signal erosion as an unannotated cosmetic commit.

---

## Phase 1 — Extract the knowledge from CLAUDE.md

Pure content relocation. No behavior change, no shared-file edits.

**Do**

1. Create `plugins/pwa-starter/references/` and move these CLAUDE.md sections **verbatim** (fix only
   headings and cross-links):

   | CLAUDE.md section | Lines | → |
   |---|---:|---|
   | The pre-share checklist | 111–225 | `references/checklist.md` |
   | Offline & the service worker | 294–484 | `references/offline.md` |
   | HTML head/meta · Icons & share image · Manifest | 267–293, 485–525 | `references/sharing-install.md` |
   | Mobile · Dark mode | 526–598 | `references/mobile-a11y.md` |
   | Google Sheets as a backend · Analytics | 599–681 | `references/data-analytics.md` |
   | Multi-page · Deploy | 682–718 | `references/deploy.md` |
   | Testing without a build | 763–783 | `references/testing.md` |
   | Gotchas grab-bag | 784–850 | `references/gotchas.md` |
   | The maturity gradient | 226–264 | `references/history.md` |

2. Slim `CLAUDE.md` to what a session *working on this repo* needs — target ≤ 90 lines:
   What this is · File hierarchy · the maintainer rules (bump `V`; `VER_PREFIX` tracks `V`'s stem;
   run the lints; never hand-edit the PNGs; stamp only whole-file copies; PROPAGATE is not a
   changelog; **never move a stamped file**) · the SessionStart/toolchain note · a link table to
   `plugins/pwa-starter/references/`.
3. Keep §Workflow:New-project and §Workflow:Audit text aside — Phases 3 and 4 consume it.
4. Update `README.md` links that point into CLAUDE.md anchors.
5. Fix two stale references while you are in here: CLAUDE.md cites a `nav.css` that does not exist
   (mark it explicitly as *a pattern to add*, not a shipped file) and describes AKM's `package.json`
   harness as if aspirational — `references/testing.md` should describe what this repo actually does
   (`scripts/sw.test.mjs`, zero-dependency node, mocked SW globals, wired into CI).

**Done when**

- [ ] I1 passes — `git diff --stat 3ec3032..HEAD -- sw.js app.js data.js theme.js ping.js pullToRefresh.js` is empty.
- [ ] I6 — no prose lost. The blocks destined for `references/` are exactly lines 111–264, 267–718
      and 763–850 of the base `CLAUDE.md`, so compare them directly:

      ```sh
      git show 3ec3032:CLAUDE.md | sed -n '111,264p;267,718p;763,850p' | wc -w
      cat plugins/pwa-starter/references/*.md | wc -w
      ```

      The second should exceed the first only by the new per-file headings — call it **+5% ceiling,
      0% floor**. Coming in *under* means content was dropped; well over means it was rewritten.
      Either way that is a different PR than this one.
- [x] **CLAUDE.md shrinks by ~10×, measured in words.** ~~`wc -l CLAUDE.md` ≤ 90~~ — criterion
      amended during execution, and the reason is worth recording rather than quietly dropping.
      Lines are a bad proxy here: this repo's prose wraps at ~95 chars, so a line count rewards
      re-wrapping and punishes nothing. Words track context cost, which is the actual goal.

      | | Before | After |
      |---|---:|---:|
      | words | 10,503 | 926 |
      | lines | 850 | 108 |

      108 lines is over the original 90. I compressed the header, the file hierarchy, "What this is"
      and the dev-environment section to get there, and stopped: what remains is eight
      maintainer rules, each a trap with a real consequence (a rename that silently breaks stamp
      tracking, a missed `V` bump that strands a fix, a non-`SHELL` script served stale forever).
      Cutting those to reach an arbitrary line count optimizes the metric, not the goal.
- [ ] `grep -rn "CLAUDE.md#" README.md docs/ plugins/` returns no dead anchors.
- [ ] I5 passes.

**Review:** the diff should read as `R` (rename/move) plus link edits. Any *prose* change inside a
moved block is out of scope for this phase — call it out or revert it. Blast radius: none downstream.

---

## Phase 2 — Publish the plugin shell

**Do**

1. `.claude-plugin/marketplace.json`:

```json
{
  "name": "jsundram",
  "owner": { "name": "Jason Sundram" },
  "plugins": [
    {
      "name": "pwa-starter",
      "source": "./plugins/pwa-starter",
      "description": "Audit, scaffold, and propagate small static PWAs",
      "version": "0.1.0"
    }
  ]
}
```

   Marketplace named `jsundram`, not `pwa-starter`, so future fleet plugins share one catalog and the
   install command does not read `pwa-starter@pwa-starter`.

2. `plugins/pwa-starter/.claude-plugin/plugin.json`:

```json
{
  "name": "pwa-starter",
  "description": "Checklist, scaffolder, and downstream-sync helper for small static PWAs",
  "version": "0.1.0",
  "author": { "name": "Jason Sundram" },
  "homepage": "https://github.com/jsundram/pwa-starter"
}
```

3. Add `.claude-plugin/`, `plugins/`, and `docs/plans/` to the **delete list** in the scaffold
   workflow (Phase 4). Repo root is also the template, so a "Use this template" instance would
   otherwise inherit a plugin manifest for someone else's project.
4. Local smoke test: `claude --plugin-dir ./plugins/pwa-starter` in a scratch dir.

**Done when**

- [ ] `python3 -c "import json;[json.load(open(p)) for p in ['.claude-plugin/marketplace.json','plugins/pwa-starter/.claude-plugin/plugin.json']]"` exits 0.
- [ ] `/plugin marketplace add jsundram/pwa-starter` then `/plugin install pwa-starter@jsundram`
      succeeds from a *different* repo. **Verify the `owner/repo` shorthand** — if it is rejected,
      fall back to a local path (`/plugin marketplace add ~/Dropbox/Code/pwa-starter`) and record
      which form worked.
- [ ] `/pwa-starter:` autocompletes after `/reload-plugins`.

**Review:** confirm the plugin directory is self-contained. Installed plugins are **copied to a
cache**, and a copied plugin cannot reach files outside its own directory — so nothing under
`plugins/pwa-starter/` may reference `../../sw.js` or `../../docs/`. This is the constraint that
decided the layout; a reviewer should check it explicitly, because the failure is silent until
someone installs from GitHub rather than running locally.

---

## Phase 3 — The `audit` skill *(requirement 2)*

`plugins/pwa-starter/skills/audit/SKILL.md`. Frontmatter: a `description` that fires on "audit this
app", "what's missing vs pwa-starter", "is this installable/offline".

**Do**

1. **Step one is scope detection, before any checklist row** — and the dividing line is **what
   reaches the browser**, not what built it. A React SSG that renders to static HTML is, for almost
   every row, an ordinary static site; classifying by dependency list gets this backwards.

   | Class | Signal (in the **output**) | What applies |
   |---|---|---|
   | A · static, no build | hand-written `index.html`; no build script | Everything, including the `V`-bump + `sw-lint` discipline |
   | B · static **from** a build | a build emits `dist/`/`public/` of plain HTML; little or no runtime framework | Everything **except** cache-busting — content-hash the shell instead of hand-bumping `V` (`references/offline.md`, "Have a build step?"). Audit the **generator**, not a hand-written `index.html` that may not exist |
   | C · runtime framework / SPA | a framework bundle + router ship to the browser; one shell HTML | Share card, icons, manifest, mobile, dark mode, a11y. Offline is the framework's job (Workbox / `vite-plugin-pwa`) — report, do not retrofit `sw.js` |
   | D · has a backend | a server, a DB, authed endpoints | Say so and stop at the offline family; see gallery-deck in `references/history.md` |

2. For class B and C, **read the files that generate the `<head>`** — the page template, the SSG
   entry, the build script — and where possible the built output. Say this in the skill: a class-B
   app with no root `index.html` must not be reported as "everything missing."
3. **Never audit by globbing for filenames.** Absence of `manifest.json` or `sw.js` on disk does not
   mean absence of a manifest or a service worker: `lobsters-and-lighthouses` builds its manifest at
   runtime as a Blob URL and inlines its worker (`references/sharing-install.md` cites it as the
   zero-icon-files trick), so a file-presence scan reports it as having neither and is wrong twice.
   Grep for the *behavior* — `registerServiceWorker`, `rel="manifest"`, a constructed Blob — then read
   the code.
3. Emit the report as a table, worst-first, `✅/⚠️/❌` with **specific evidence** (the missing tag,
   the unversioned cache, the hover-only tooltip) and a rough cost per fix. Lead with share card,
   offline, cache-busting; nitpicks last.
4. Offer fixes but **do not apply them unasked**, and port the *pattern*, never the placeholder
   styling — the target app keeps its own design language.
5. Link, don't inline: `references/checklist.md` is the rubric; the deep-dives load on demand.

**Done when**

- [ ] Dry run against **`jsundram/quartet-chooser`** — a real, known-answer case, audited by hand
      below — produces a report that:
  - [ ] classifies it **class B**: `scripts/build.mjs` is a hand-rolled SSG (Gatsby is gone) that
        renders each route to `dist/<route>/index.html`; React runs **only at build time**
        (`renderToStaticMarkup`), and the browser gets static HTML, inlined CSS and two dependency-free
        vanilla scripts. Not an SPA — the full checklist applies;
  - [ ] does **not** tell it to hand-bump a `V` constant;
  - [ ] reads `scripts/build.mjs` (`page_html()`), `src/pages/*.js` and `src/templates/*.js` for head
        metadata instead of reporting "no `index.html`, everything missing";
  - [ ] finds at least these, with file-and-line evidence (the known-answer set):

        | Finding | Evidence |
        |---|---|
        | `og:image` is an **SVG** on every work and composer page — no preview in iMessage/WhatsApp/Slack | `src/lib/utils.js:44` returns `/<Composer>-Original.svg`, used by `src/templates/work.js:148` and `composer.js` |
        | Home page card is a 512×512 square, not a 1200×630 raster | `src/pages/index.js:43` → `static/icon.png` |
        | No `twitter:card`, `og:url`, `og:type`, `og:image:width/height/alt` anywhere | all three `Head` exports |
        | No `<meta name="description">` (only `og:description`) | all three `Head` exports |
        | Manifest has **icons and nothing else** — no `name`, `short_name`, `start_url`, `display`, `theme_color`, no `maskable` → installs unnamed on Android | `static/manifest.webmanifest` |
        | No `apple-mobile-web-app-*` metas; no 180×180 apple-touch-icon (sizes jump 144→192) | `scripts/build.mjs` `page_html()` + manifest icon list |
        | No `theme-color`, no `color-scheme: light dark` | `page_html()` |
        | `viewport` lacks `viewport-fit=cover`; carries legacy `shrink-to-fit=no` | `page_html()` |
        | No service worker — not offline, and this is a *rehearsal-room* app | no `sw.js` anywhere |
- [ ] Dry run against a **class A** app (`haydn-info-card`) still produces the full checklist including
      the `V`/`sw-lint` rows — i.e. scope detection did not silently disable the core rubric.
- [ ] `SKILL.md` ≤ 500 lines; every deep-dive is a link, not an inline copy.

**Review:** the class-B branch is the whole point of this phase — misclassify and the skill either
gives wrong cache-busting advice or declares a perfectly good static site unauditable. Check the
quartet-chooser run against the table above by hand; do not trust the summary.

**Deploy note (surfaced by the same dry run).** Nothing in quartet-chooser is actually
Netlify-specific: no `_redirects`, no `_headers`, no functions or edge handlers — `netlify.toml` is
just `command` + `publish`. `404.html` and directory-index clean URLs work identically on GitHub
Pages. So it **could** be a Pages app: add a `CNAME` to `static/` (copied through verbatim by
`build.mjs` step 7 — today the custom domain lives only in Netlify's UI, so it is not in the repo),
add a build-and-deploy workflow next to the existing `test.yml`, repoint DNS, drop `netlify.toml`.
The one real coupling is that every asset path is **root-absolute** (`/js/shuffle.js`,
`/manifest.webmanifest`, `SITE_URL`-prefixed OG images), so this works at a domain root — a custom
domain or a user page — but **not** at a project path like `jsundram.github.io/quartet-chooser/`
without a base-path pass. Worth a row in `references/deploy.md`: the skeleton's "relative paths
throughout" rule is what buys project-page portability, and an absolute-path site has traded it away.

---

## Phase 4 — The `scaffold` skill *(requirement 3)*

`plugins/pwa-starter/skills/scaffold/SKILL.md`, from CLAUDE.md §Workflow:New project (lines 21–62).

**Do**

1. Carry over verbatim: the one-round question set (name, short_name, tagline, description, absolute
   URL, analytics choice), the placeholder replacement table, icon generation, the verify step, and
   `git config core.hooksPath .githooks`.
2. **The files come from the template repo, not from the plugin.** An installed plugin lives in a
   cache; a new project wants its own git history. So the skill's step 1 is "Use this template" on
   GitHub (or `git clone --depth 1 && rm -rf .git`), and the skill orchestrates from there. This also
   avoids a second copy of `sw.js` that would drift from the stamped original.
3. Extend the existing delete-list to include `.claude-plugin/`, `plugins/`, `docs/plans/`,
   and `PROPAGATE.md` — none of which belong in a fresh app.
4. Keep the analytics fork (GoatCounter default; sheet-ping for a known roster) pointing at
   `references/data-analytics.md`.

**Done when**

- [ ] End-to-end dry run into a scratch directory produces an app where:
  - [ ] `grep -rn "APP\|USER.github.io\|One sentence on what this is" . --exclude-dir=.git` returns nothing;
  - [ ] `scripts/make-icons.sh && scripts/make-og.sh` succeed and every icon path in `manifest.json` resolves;
  - [ ] `python3 scripts/sw-lint.py` exits 0;
  - [ ] `node scripts/sw.test.mjs` exits 0;
  - [ ] the deleted-list files are gone;
  - [ ] it loads at `python3 -m http.server`, installs, and survives load-once-then-offline.
- [ ] The scratch app contains **no** `.claude-plugin/` or `plugins/` directory.

**Review:** the placeholder grep is the one that catches a half-done scaffold. Run it yourself.

---

## Phase 5 — The `propagate` skill and a registry heartbeat *(requirement 1)*

**Do**

1. `plugins/pwa-starter/skills/propagate/SKILL.md`, from CLAUDE.md §Propagating a fix (719–747) plus
   PROPAGATE.md's own rules: two-way flow (port upstream *first*, let the stamp catch up), stamp only
   whole-file copies, `--at` for an older sync point, `pinned:` with a mandatory reason, and how to
   write a PROPAGATE entry that is an instruction rather than a changelog line.
2. **Teach the checker about deliberate non-copies** — the fix for baseline problem 2. `pinned:`
   cannot express it, because it lives inside a stamp and a non-copy must not carry one. Add a
   suppression list the checker reads (path globs plus a mandatory reason, mirroring `pinned:`), and
   report those separately from genuine untracked candidates. Seed it with the three standing cases:
   `quartet-log/src/pullToRefresh.js` (the ancestor this skeleton's copy was written *from*),
   `quartets.boccherini.org/app.js` and `gallery-deck/web/public/app.js` (partial adopters that took
   only the ~59-line version-tag region). Keep discovery-by-fingerprint intact — the point is to
   silence *known* answers, never to stop looking.
3. **Add a staleness check for PROPAGATE's own prose** — the fix for baseline problem 1, and the gap
   nothing currently covers. A "known affected: X needs the full port" line that stays after X is
   stamped current is worse than no line, because it sends you to re-do finished work. Cheapest
   version: have the checker cross-reference each entry's named repos against their live stamps and
   flag any that claims a copy is behind when the scan says it is current.
4. Give the registry a heartbeat. `check-downstream.py` is the third-most-churned file here and runs
   only when remembered. Add a scheduled workflow that clones the known copies and runs the checker,
   opening/updating one issue when anything is behind. Keep it **non-fatal on clone failure** — the
   repo's own ethos: "no network" must not read as "the fleet is broken."
   **Declare what it cannot see.** `musiclog` / `viz.runningwithdata.com` is a standing two-way
   example in PROPAGATE.md, but there is no GitHub repo for it — `runningwithdata.com` is a Jekyll
   blog with no skeleton files. A CI heartbeat that clones GitHub repos will structurally miss it, so
   the local `check-downstream.py ~/Dropbox/Code` run stays authoritative and the workflow must say
   so in its output rather than implying full coverage.
5. Fleet resolution is **complete as of the Phase 0 baseline** — all 46 account repos enumerated,
   19 web-shaped ones cloned and scanned. `quartet-chooser`, `haydnenthusiasts.org`, `haydn-lowdn`
   and `boccherini-sampler` are confirmed **non-copies** (no skeleton basenames, none of the six
   fingerprints). Record them in PROPAGATE.md's known-non-copies table so future scans stay quiet.

**Done when**

- [ ] `python3 scripts/check-downstream.py ~/Dropbox/Code > /tmp/downstream-after.txt` and **I2 holds**
      (`diff` against the Phase 0 baseline is empty).
- [ ] The scheduled workflow runs green on a manual dispatch and its report matches the local run.
- [ ] Each of the four repos above is either stamped or explicitly recorded as a non-copy.

**Review:** I2 is the acceptance test for requirement 1 in its entirety. If the diff is non-empty,
something in Phases 1–4 touched a tracked file — find it before merging.

---

## Phase 6 — Housekeeping

**Do**

1. Close **#9** — its work landed in `77fcb35` (cache-first serve, warm/cold bounds, nav-5xx throw,
   catch-path re-read, `scripts/sw.test.mjs`, `.github/workflows/checks.yml`).
2. Close **#8**, recording that the repo answered it with a **third** option neither the issue's A nor
   B proposed: a zero-dependency node script running `sw.js` unmodified under mocked SW globals and a
   fake clock — no browser engine, no `package.json`, no `node_modules`, and it runs in CI. That is a
   better answer than either option and deserves to be written down before the issue disappears.
3. Update `README.md` to lead with the three entry points; the "starter" job is the finished one.

**Done when**

- [ ] #8 and #9 closed with a comment naming the commit that resolved each.
- [ ] README's two-ways-to-use section is three ways, with the install command.

---

## Review rubric

For reviewing the whole change, independent of the phases:

1. **Requirement 1 — downstream preserved.** I1, I2, I4 pass. This is objective; do not accept prose.
2. **Requirement 2 — audits other repos.** The quartet-chooser run is in the PR, it classifies
   class B without recommending a `V` bump, and it finds every row of the known-answer table in
   Phase 3. A run that misses the SVG `og:image` has not earned a pass.
3. **Requirement 3 — bootstraps new projects.** The scratch-app placeholder grep is empty and
   `sw-lint` + `sw.test.mjs` pass inside it.
4. **No knowledge lost.** I6's word count, and `references/` renders on GitHub with working links.
5. **No context regression.** CLAUDE.md is ~926 words, down from 10,503 (~10x). See Phase 1 for why the criterion is words, not lines.
6. **Self-containment.** Nothing under `plugins/pwa-starter/` reaches outside itself.

## Out of scope

Deliberately not here, to keep the diff reviewable:

- Rewriting any prose while moving it (Phase 1 is a move, not an edit).
- Changing any stamped file (`sw.js`, `app.js`, `data.js`, `theme.js`, `ping.js`,
  `pullToRefresh.js`) for any reason — see I1.
- Fixing quartet-chooser, or migrating it off Netlify. Phase 3 audits it to prove the skill works;
  acting on the findings is that repo's own issue.
- Publishing to a public marketplace or writing `claude plugin eval` cases — the audience is one
  fleet; revisit only if that changes.
- Renaming the repo. "pwa-starter" names the least active job, but a rename breaks every stamp's
  human-readable prefix and every inbound link for no functional gain.

## Risks

| Risk | Mitigation |
|---|---|
| A docs commit touches a stamped file and adds fleet-wide noise | I1, checked every phase |
| Plugin references a path outside its directory; works locally, breaks on install | Phase 2 review item; test via a real GitHub install, not just `--plugin-dir` |
| Template instances inherit `plugins/` + `.claude-plugin/` | Phase 4 delete-list, with a scratch-app assertion |
| Audit skill gives class-A advice to a class-B app | Phase 3 dry runs on one of each |
| Audit skill classifies by dependency list rather than by output, and writes off a static-HTML SSG as an un-auditable SPA | Class table keys on what reaches the browser; quartet-chooser is the regression case |
| `/plugin marketplace add owner/repo` shorthand not supported | Phase 2 records the working form; local-path fallback |

---

## Appendix — audit backlog

Coarse triage from a marker scan of the 19 web-shaped repos (2026-08-21). **This is a worklist, not
an audit** — it greps for signals, which is exactly the method Phase 3 step 3 forbids the skill from
relying on. `lobsters-and-lighthouses` is the proof: it shows `manifest 0 / sw 0` here and in fact has
both, generated at runtime. Treat every row as "run `/pwa-starter:audit` here", ordered by how much
the app looks like it would benefit.

| Repo | Shape | Apparent gaps |
|---|---|---|
| `haydnenthusiasts.org` | 8 static HTML pages | No manifest, no SW, no `apple-touch-icon`, no dark mode; 1 of 8 pages has `og:image`. The boccherini "before" case again — high value, low risk |
| `quartet-chooser` | class B SSG | The hand-audited table in Phase 3 — SVG `og:image` fleet-wide, icons-only manifest, no SW |
| `wtq` | single page + manifest | No `og:image`, no dark mode, no SW (matches `references/history.md`) |
| `lobsters-and-lighthouses` | 3 pages, Netlify | Has OG + `apple-touch-icon`; **verify the runtime manifest and inlined SW by reading, not globbing**; no dark mode |
| `haydn-lowdn` · `maestoso-127` · `nh_tax_map` · `haydn-canon` | one-page viz | No PWA metadata at all — decide per app whether any is meant to be installed |
| `somerville-typemap` | one-page viz | Dark mode only; nothing else |
| `boccherini-sampler` · `github-month-review` | one/two pages | Partial OG; no manifest, no SW |
| `cjs-archive` | 361-page static archive | 350 pages carry `apple-touch-icon` and there is a manifest — likely fine; confirm the share card |
| `AKM` · `haydn-info-card` · `quartets.boccherini.org` · `quartet-log` · `gallery-deck` | already downstream | Not audit targets — they *are* the common core. Keep them in the propagate lane |

Order of attack: `haydnenthusiasts.org` first (biggest gap, real audience), then `wtq`, then
`quartet-chooser`. The one-page vizzes are probably fine as pages and should not be forced into
being apps — "does anyone open this on a phone twice?" is the filter.
