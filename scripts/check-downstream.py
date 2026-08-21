#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Find repos carrying a copy of this skeleton's files and report what they're missing.

THE PROBLEM: these files are vendored BY COPY, and every copy is legitimately modified — a
different SHELL list, a different V prefix, branches deleted for features the app doesn't use.
So "does this file differ from ours?" is useless: the answer is always yes. What actually matters
is "which commit of OURS was this synced from, and have we changed it since?"

THE MECHANISM: each downstream copy carries a one-line provenance stamp near the top,

    // pwa-starter: sw.js @ bd16c21

and drift is then a git range (`git log <sha>..HEAD -- sw.js`) rather than a diff — immune to
local modification. PROPAGATE.md turns the raw commit list into a to-do list by annotating the
shas that actually require downstream action, so a comment tweak doesn't read like a bug fix.

Discovery is deliberately NOT a hand-maintained list of repos: a list rots silently the first
time you forget to add one. Point this at a directory of clones and it finds copies by stamp,
and flags unstamped-but-recognizable files as candidates so a forgotten repo surfaces itself.

A copy whose deployment makes a class of fixes moot can be PINNED — append a reason to its stamp:

    // pwa-starter: sw.js @ 2ed87e9 pinned: tailnet-only, no real offline mode

Pinned copies are reported separately (with how far they've drifted, so the decision stays
visible) and never read as an undone task or fail the scan. The reason is mandatory context for
future-you; delete the clause to resume tracking. Pin the FILE, not the repo — a pinned sw.js
doesn't exempt a data.js copy next to it.

    python3 scripts/check-downstream.py ~/Dropbox/Code       # scan a tree of clones
    python3 scripts/check-downstream.py ../foo ../bar        # or specific repos
    python3 scripts/check-downstream.py --stamp ../foo/sw.js             # adopt at our HEAD
    python3 scripts/check-downstream.py --stamp ../foo/sw.js --at 2ed87e9 # ...or at an older sync point

A copy that only RESEMBLES ours — an independent implementation, or a partial adopter that took a
region rather than the file — must not be stamped at all, and `pinned:` can't say so (a pin lives
inside a stamp). Those go in NON_COPIES below, with a reason, and are reported separately instead of
nagging as untracked on every run.

The stamp catches a copy falling behind the doc; nothing caught the DOC falling behind the copies, so
a PROPAGATE entry may carry `Known-affected: <repo>/<path> …` and the scan contradicts any of those
it finds already current.

Exits 1 if anything is behind, if a NON_COPIES entry has rotted, or if a PROPAGATE claim is
contradicted — so CI can gate on it. Unstamped candidates are informational.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files this skeleton owns. A downstream copy of one of these is what we track.
# The fingerprint is a string distinctive enough to recognize a copy that has drifted
# far from ours but is still recognizably descended from it.
SHARED = {
    "sw.js": "BUMP ON EVERY SHELL CHANGE",
    "data.js": "window.Data",
    "theme.js": "window.Theme",
    "app.js": "VER_PREFIX",
    "ping.js": "APP_PAGE",          # not the localStorage key — that's meant to be renamed
    "pullToRefresh.js": "PullToRefresh",
}

STAMP = re.compile(r"pwa-starter:\s*(\S+?)\s*@\s*([0-9a-f]{7,40})(?:\s+pinned:\s*(\S[^\n]*))?")
SKIP = {".git", "node_modules", "vendor", "dist", "build", ".venv", "__pycache__"}
HEAD_LINES = 40          # a stamp belongs near the top; don't scan whole files

# Files that are recognizably ours but deliberately NOT tracked. A fingerprint proves
# resemblance, not provenance, and `pinned:` can't express this: a pin lives INSIDE a stamp,
# and a non-copy must not carry a stamp at all. Without this table the same correct decisions
# resurface as "untracked candidates" on every scan, forever — the exact signal erosion that
# PROPAGATE.md's "not a changelog" rule guards against on the other side.
# Keyed by path suffix; the reason is mandatory context for future-you, same as a pin's.
NON_COPIES = {
    "quartet-log/src/pullToRefresh.js":
        "independent implementation, and the ANCESTOR — this skeleton's version was written from it",
    "quartets.boccherini.org/app.js":
        "partial adopter: took the ~59-line VER_PREFIX/checkVer/forceUpdate region, not the file",
    "gallery-deck/web/public/app.js":
        "partial adopter: 479 lines of its own app with the version-tag block grafted in",
}


def sh(*a, cwd=ROOT):
    return subprocess.run(a, capture_output=True, text=True, cwd=cwd)


def head(path, n=HEAD_LINES):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return "".join(next(f, "") for _ in range(n))
    except OSError:
        return ""


def read_propagate():
    """PROPAGATE.md → {(file, sha): note}.

    Keyed by FILE AND sha, not sha alone: one commit routinely touches several files with
    different downstream consequences. ddd9ab8, for instance, rewrote data.js but touched
    sw.js only to bump V — filing its data.js note against sw.js too would tell you to go
    patch a service worker over a change that never touched its logic.

    Entries are `- <sha>  note`, under a `## <filename>` heading, and continuation lines
    (indented under the bullet) are folded into the note.

    One continuation line is structured rather than folded:

        Known-affected: quartets.boccherini.org/sw.js AKM/sw.js

    Hyphenated, and every token must look like `<repo>/<path>` — because entries already write
    "Known affected:" in prose, and a marker that collides with prose would silently swallow a
    note instead of parsing it. (It did, once, while this check was being written.)

    Those paths are cross-checked against the live scan, because the failure this whole file
    guards against runs BOTH ways. The stamp catches a copy falling behind the doc; nothing
    catches the doc falling behind the copies — and a "needs the full port" line that outlives
    the port is worse than no line, since it sends you to redo finished work. Returns
    (notes, affected).
    """
    notes, affected = {}, {}
    path = os.path.join(ROOT, "PROPAGATE.md")
    if not os.path.exists(path):
        return notes, affected
    fname, key = None, None
    for line in open(path, encoding="utf-8"):
        h = re.match(r"##\s+(\S+)", line)
        if h:
            fname, key = h.group(1), None
            continue
        m = re.match(r"\s*[-*]\s+([0-9a-f]{7,40})\s+(.*)", line)
        if m and fname:
            key = (fname, m.group(1))
            notes[key] = m.group(2).strip()
        elif key and line.startswith(("  ", "\t")) and line.strip():
            a = re.match(r"\s*Known-affected:\s*(.+)", line)
            toks = a.group(1).split() if a else []
            if toks and all(re.fullmatch(r"[\w.-]+/[\w./-]+", x) for x in toks):
                affected.setdefault(key, []).extend(toks)
            else:
                notes[key] += " " + line.strip()   # fold the wrapped remainder in
        elif not line.strip():
            key = None
    return notes, affected


def wrap(text, width=88, indent=" " * 14):
    """Wrap a note so a multi-line entry stays readable in the terminal."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return ("\n" + indent).join(lines)


def commits_since(sha, fname):
    """Commits to `fname` in THIS repo after `sha`. (None, reason) if the sha is unusable."""
    if sh("git", "cat-file", "-e", sha + "^{commit}").returncode != 0:
        return None, f"unknown commit {sha} — not in this repo (rebased? typo?)"
    r = sh("git", "log", "--format=%h\t%s", f"{sha}..HEAD", "--", fname)
    if r.returncode != 0:
        return None, r.stderr.strip()
    out = [ln.split("\t", 1) for ln in r.stdout.splitlines() if ln.strip()]
    return out, None


def match_non_copy(path):
    """The NON_COPIES key this path is a known non-copy under, or None."""
    norm = path.replace(os.sep, "/")
    for key in NON_COPIES:
        if norm == key or norm.endswith("/" + key):
            return key
    return None


def scanned_repos(roots):
    """Repo directory names this scan actually covered.

    Used to tell a STALE NON_COPIES entry (its repo was scanned, the file is gone) from one
    that simply wasn't in scope this run — otherwise scanning a single repo would report every
    other entry as stale, and the staleness signal would be worth nothing.
    """
    names = set()
    for root in roots:
        root = os.path.abspath(root)
        if os.path.isdir(os.path.join(root, ".git")):
            names.add(os.path.basename(root))
            continue
        try:
            entries = os.listdir(root)
        except OSError:
            continue
        names.update(d for d in entries
                     if os.path.isdir(os.path.join(root, d)) and not d.startswith("."))
    return names


def walk(roots):
    """Yield every file under `roots` whose basename is one we own (skipping this repo)."""
    for root in roots:
        root = os.path.abspath(root)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP and not d.startswith(".")]
            if os.path.abspath(dirpath) == ROOT:      # never audit ourselves
                dirnames[:] = []
                continue
            for fn in filenames:
                if fn in SHARED:
                    yield os.path.join(dirpath, fn)


def stamp_file(path, at=None):
    """Write a provenance stamp for `path` at `at` (default: our current HEAD).

    Pass --at when the copy is synced from an OLDER commit than HEAD, which is the
    normal case when adopting an existing app: stamping it at HEAD would claim it
    has changes it doesn't, and the checker would report it clean while it's behind.
    """
    fname = os.path.basename(path)
    if fname not in SHARED:
        sys.exit(f"{fname} isn't a file this skeleton owns ({', '.join(sorted(SHARED))})")
    # A NON_COPIES entry is a decision that this file is NOT vendored from us. Stamping it would
    # assert the opposite and start reporting it behind every commit to a file it never copied,
    # so refuse here rather than let the two records contradict each other.
    key = match_non_copy(path)
    if key:
        sys.exit(f"{path}\n  is listed in NON_COPIES: {NON_COPIES[key]}\n"
                 f"  Stamping it would claim it IS a whole-file copy. Remove the NON_COPIES entry "
                 f"first if that decision has changed.")
    ref = at or "HEAD"
    if sh("git", "cat-file", "-e", ref + "^{commit}").returncode != 0:
        sys.exit(f"{ref} isn't a commit in this repo")
    sha = sh("git", "rev-parse", "--short", ref).stdout.strip()
    with open(path, encoding="utf-8") as f:
        body = f.read()
    if STAMP.search(body[:4000]):
        sys.exit(f"{path} is already stamped — edit the sha by hand if you mean to re-adopt it")
    comment = "#" if fname.endswith((".py", ".sh")) else "//"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"{comment} pwa-starter: {fname} @ {sha}\n{body}")
    print(f"stamped {path} @ {sha}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", default=[os.path.dirname(ROOT)],
                    help="repos or a directory of clones to scan (default: this repo's parent)")
    ap.add_argument("--stamp", metavar="FILE", help="adopt FILE and exit (see --at)")
    ap.add_argument("--at", metavar="SHA", help="with --stamp: the commit FILE was synced from (default HEAD)")
    args = ap.parse_args()

    if args.stamp:
        return stamp_file(args.stamp, args.at)

    notes, affected = read_propagate()
    behind, candidates, ok, broken, pinned = [], [], 0, [], []
    roots = args.paths or [os.path.dirname(ROOT)]
    known, matched_keys, current = [], set(), []

    for path in walk(roots):
        fname = os.path.basename(path)
        text = head(path)
        m = STAMP.search(text)
        if not m:
            # A deliberate non-copy is a settled decision, not an open question — report it
            # separately so it never reads as a to-do. Checked BEFORE the fingerprint, since
            # every entry here matches one by construction.
            key = match_non_copy(path)
            if key:
                matched_keys.add(key)
                known.append((path, NON_COPIES[key]))
                continue
            # Unstamped: is it recognizably ours? Read the whole file for the fingerprint,
            # since a copy may have moved things around.
            if SHARED[fname] in open(path, encoding="utf-8", errors="replace").read():
                candidates.append(path)
            continue
        stamped_name, sha, pin = m.group(1), m.group(2), m.group(3)
        commits, err = commits_since(sha, stamped_name)
        if err:
            broken.append((path, err))               # a pinned stamp still needs a real sha
        elif pin is not None:
            pinned.append((path, sha, len(commits), pin.strip()))
        elif commits:
            behind.append((path, sha, commits, stamped_name))
        else:
            ok += 1
            current.append(path)

    rel = lambda p: os.path.relpath(p, os.path.dirname(ROOT))

    for path, sha, commits, stamped_name in behind:
        print(f"\n{rel(path)}  @ {sha}")
        print(f"  BEHIND {len(commits)}:")
        actionable = 0
        for short, subject in commits:
            note = notes.get((stamped_name, short))
            print(f"    {short}  {subject}")
            if note:
                actionable += 1
                print(f"              → {wrap(note)}")
        if not actionable:
            print(f"              (nothing listed for {stamped_name} in PROPAGATE.md — likely cosmetic)")

    for path, err in broken:
        print(f"\n{rel(path)}\n  STAMP UNUSABLE: {err}")

    if pinned:
        print("\nPinned (deliberately not tracked — delete the 'pinned:' clause in the stamp to resume):")
        for path, sha, n, reason in pinned:
            print(f"  {rel(path)}  @ {sha}  ({n} behind)  — {reason}")

    if known:
        print("\nKnown non-copies (deliberately untracked — see NON_COPIES in this script):")
        for path, reason in sorted(known):
            print(f"  {rel(path)}  — {reason}")

    # An entry whose repo WAS scanned but whose file is gone has rotted: the path moved or the
    # copy was deleted, and a suppression nobody re-checks is how a real copy gets silenced.
    covered = scanned_repos(roots)
    stale = [k for k in NON_COPIES
             if k not in matched_keys and k.split("/")[0] in covered]
    if stale:
        print("\nSTALE NON_COPIES entries (repo scanned, file not found — fix or drop them):")
        for k in sorted(stale):
            print(f"  {k}")

    # The doc-behind-copies check: a claim that a copy needs work, contradicted by the scan.
    def is_current(claim):
        return any(p.replace(os.sep, "/").endswith("/" + claim) for p in current)

    stale_claims = [(f, sha, c) for (f, sha), paths in sorted(affected.items())
                    for c in paths if is_current(c)]
    if stale_claims:
        print("\nSTALE PROPAGATE claims (entry says these need work; the scan says current):")
        for f, sha, c in stale_claims:
            print(f"  {f} {sha}  claims {c}")
        print("  \u2192 the port landed and the note didn't: update the entry.")

    if candidates:
        print("\nUnstamped copies (recognizably ours, not yet tracked):")
        for path in candidates:
            print(f"  {rel(path)}")
        print("  → adopt with: python3 scripts/check-downstream.py --stamp <file>")

    print(f"\n{ok} up to date, {len(behind)} behind, {len(pinned)} pinned, "
          f"{len(known)} known non-copies, {len(candidates)} untracked, {len(broken)} unusable")
    return 1 if behind or broken or stale or stale_claims else 0


if __name__ == "__main__":
    sys.exit(main())
