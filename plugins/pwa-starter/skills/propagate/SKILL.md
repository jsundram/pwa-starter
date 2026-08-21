---
name: propagate
description: Carry a pwa-starter fix out to the apps that vendored its files, or adopt a copy into tracking. Use when asked which downstream copies are behind, to propagate or port a fix to other repos, to stamp a vendored file, or to check downstream drift.
---

# Propagate a fix to downstream copies

Apps built from this skeleton **vendor its files by copy**, not by dependency — deliberately, since
the premise is that deployed files need no build step. The cost is that a fix here reaches nobody
until someone carries it. This is that job.

## The mechanism

Never compare file contents. Every copy is *legitimately* modified — its own `SHELL`, its own `V`
prefix, branches deleted for features it doesn't use — so a diff is always non-empty and tells you
nothing. The useful question is **"which commit of ours was this synced from, and have we touched
that file since?"**, which makes drift a git range:

```js
// pwa-starter: sw.js @ bd16c21          ← one line near the top, survives local edits
```

```sh
python3 scripts/check-downstream.py ~/Dropbox/Code    # scan a tree of clones
python3 scripts/check-downstream.py --stamp ../foo/sw.js --at 2ed87e9
```

`PROPAGATE.md` turns "4 commits behind `sw.js`" into a to-do list by annotating the shas that need
downstream *action*; unlisted commits print "(may be cosmetic)". **Silence there is meaningful** —
keep it that way by not logging churn.

## Rules that cost a debugging session each

**Flow is two-way, and the stamp tracks one direction.** Several of these apps predate the skeleton —
they are where its content came from — and any app can still solve something worth pulling back.
`#9` (the lie-fi fix) arrived *from* `haydn-info-card`. So when an app grows something general,
**port it here first and let the stamp catch up**; don't leave it downstream and rely on remembering.

**Stamp only whole-file copies.** A fingerprint proves resemblance, not provenance. Two kinds must
stay unstamped: *independent implementations* (same idea, own code — `quartet-log/src/pullToRefresh.js`
is the **ancestor** this skeleton's version was written from) and *partial adopters* that took a
region, not the file (`quartets.boccherini.org/app.js` and `gallery-deck/web/public/app.js` took only
the ~59-line version-tag block). A file-level stamp on those reports them behind every commit
regardless of whether it touched the lines they actually took. If a region grows big enough to
warrant tracking, **split it into its own file first**, then stamp that.

**Use `--at` when adopting an existing app.** A stamp at `HEAD` claims it has changes it doesn't, and
the checker will report it clean while it is silently behind.

**Pin a copy out of tracking when a deployment makes a class of fixes moot** — append
`pinned: <reason>` to the stamp. The reason is mandatory context for future-you. Pin the *file*, not
the repo. `gallery-deck/web/public/sw.js` is the standing example: tailnet-only, media served live and
never cached, so the offline-robustness family does not apply.

**Port families together, not à la carte.** Some entries are a set of changes that are only correct
in combination — the `#7` offline family and the `#9` lie-fi family both say so explicitly. Read the
PROPAGATE entry before splitting one up. Ordering can matter too: `data.js`'s empty-payload guard must
land *before* its cache-first paint, or a cosmetic bug becomes an app-wedging one.

## Writing a PROPAGATE entry

One bullet per commit, short sha first, under a `## <filename>` heading — the parser is literal about
this shape, and about continuation lines being indented under the bullet.

```
## sw.js
- 0000000  what changed, and what downstream must do about it (#issue)
```

Write the **instruction**, not the changelog line: what a maintainer of a copy has to do, which pieces
must land together, what adopter-visible trade it carries, and which known copies are affected.

## Keep the registry honest

The stamp catches a copy falling behind the doc. Two failure modes run the other way, and the checker
now covers both — but only if you feed them.

**The doc falling behind the copies.** A "needs the full port" line that outlives the port is worse
than no line: it sends you to redo finished work. So when an entry names copies that must act, add a
machine-readable trailer under the bullet —

```
  Known-affected: quartets.boccherini.org/sw.js AKM/sw.js
```

— and the scan flags any of them it finds already stamped and current. Hyphenated and path-shaped on
purpose: entries also write "Known affected:" in prose, and a marker that collided with prose would
swallow the note instead of parsing it. When you finish a port, re-stamp the copy *and* update the
entry. (The `#9` entry claimed `quartets.boccherini.org` and `AKM/sw.js` were behind for weeks after
both were current; that is what motivated the check.)

**Deliberate non-copies resurfacing forever.** `pinned:` cannot express "this is not a copy" — a pin
lives inside a stamp, and a non-copy must not carry one. So known non-copies live in `NON_COPIES` in
`check-downstream.py`, keyed by path suffix with a mandatory reason, and are reported in their own
section instead of as untracked. Add an entry when you decide a resembling file is an independent
implementation or a partial adopter. An entry whose repo is scanned but whose file has moved is
reported **stale** — a suppression nobody re-checks is how a real copy gets silenced.

Discovery is deliberately *not* a hand-maintained list of repos — a list rots the first time you
forget one. Point the checker at a tree of clones; it finds copies by stamp and flags
unstamped-but-recognizable files so a forgotten repo surfaces itself. It sees only what you have
checked out, so scan a tree that holds every copy — a private repo needs credentials, not an
exception.
