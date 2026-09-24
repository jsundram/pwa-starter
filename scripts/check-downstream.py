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

Exits 1 if anything is behind, so CI can gate on it. Unstamped candidates are informational.
"""
import argparse
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Files this skeleton owns, keyed by BASENAME (what a downstream copy is called) → the path the
# file lives at HERE, plus a tuple of fingerprints.
#
# THE PATH IS NOT COSMETIC. Drift is `git log <sha>..HEAD -- <path>`, and git takes that as a
# pathspec: a bare "sw-lint.py" matches nothing when the file is at scripts/sw-lint.py, so every
# stamped copy would report UP TO DATE forever. A tracked file that silently never reports is
# worse than an untracked one — it converts a gap into a green light. Root-level files were fine
# by accident; adding the scripts/ ones is what surfaced this.
#
# FINGERPRINTS: strings distinctive enough to recognize a copy that has drifted far from ours but
# is still recognizably descended from it. ANY one matching is enough, and that is the point of
# the tuple: a single fingerprint is a single point of failure, and it failed silently. `app.js`
# was fingerprinted on "VER_PREFIX" alone, so AKM's copy — which inlines the prefix as /^akm-v/
# and keeps no such constant — was invisible to every scan while carrying the #17 bug. A forgotten
# repo surfacing itself is this script's one job; name several independent landmarks per file so
# one local rename can't switch it off. (#17)
#
# Deliberately NOT fingerprinted: AKM's and gallery-deck's scripts/sw-lint.py. Both implement
# check 1 and nothing else, in their own words — independent works that share the idea, not the
# code. Fingerprinting them would report them behind every sw-lint commit they were never going
# to take. They are tracked the way other independent implementations are: by name, in
# PROPAGATE.md.
SHARED = {
    "sw.js": ("sw.js", ("BUMP ON EVERY SHELL CHANGE", "ensureShell", "offlineFallback")),
    "data.js": ("data.js", ("window.Data", "writeCache", "revalidate")),
    "theme.js": ("theme.js", ("window.Theme", "invalidateColorCache", "getCssColor")),
    "app.js": ("app.js", ("VER_PREFIX", "requestShellTopUp", "ensure-shell")),
    # not the localStorage key — that's meant to be renamed
    "ping.js": ("ping.js", ("APP_PAGE", "URL_")),
    "pullToRefresh.js": ("pullToRefresh.js", ("PullToRefresh",)),
    # Tooling. Not shipped to the browser, but vendored just the same — and until now invisible:
    # these carry provenance stamps that nothing read, because the walk only yields basenames
    # listed here. #15 proposed pushing lint features downstream on the strength of a stamp that
    # was inert.
    "sw-lint.py": ("scripts/sw-lint.py", ("shell_entries", "precache contract")),
    "og-lint.py": ("scripts/og-lint.py", ("blob_size", "grey box")),
    "sw.test.mjs": ("scripts/sw.test.mjs", ("mocked Service Worker", "NET_TIMEOUT")),
}

# Tracked regions living under a DIFFERENT basename downstream. Discovery only: there is
# no upstream file to run `git log -- <name>` against, so these can never be stamped —
# the PROPAGATE.md tables explain each copy by hand. quartet-log's app.js split moved its
# version-tag region into updateChecker.js (the "split it into its own file" move the
# partial-adopters note prescribes); without this entry the region silently vanishes from
# the scan the moment a fingerprint leaves a basename we own.
DISCOVER_ONLY = {
    "updateChecker.js": (None, ("VER_PREFIX", "forceUpdate")),   # no upstream path, by definition
}
PATHS = {k: v[0] for k, v in {**SHARED, **DISCOVER_ONLY}.items()}
FINGERPRINTS = {k: v[1] for k, v in {**SHARED, **DISCOVER_ONLY}.items()}

STAMP = re.compile(r"pwa-starter:\s*(\S+?)\s*@\s*([0-9a-f]{7,40})(?:\s+pinned:\s*(\S[^\n]*))?")
SKIP = {".git", "node_modules", "vendor", "dist", "build", ".venv", "__pycache__"}
HEAD_LINES = 40          # a stamp belongs near the top; don't scan whole files


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
    """
    notes, path = {}, os.path.join(ROOT, "PROPAGATE.md")
    if not os.path.exists(path):
        return notes
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
            notes[key] += " " + line.strip()       # fold the wrapped remainder in
        elif not line.strip():
            key = None
    return notes


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
    """Commits to `fname` in THIS repo after `sha`. (None, reason) if the sha is unusable.

    Logs against the file's path HERE, not the basename the stamp carries: git reads the trailing
    argument as a pathspec, and a bare basename matches nothing for a file that isn't at the root.
    That failure is silent and reads as "up to date" — see the note on SHARED.
    """
    if sh("git", "cat-file", "-e", sha + "^{commit}").returncode != 0:
        return None, f"unknown commit {sha} — not in this repo (rebased? typo?)"
    path = PATHS.get(fname) or fname
    r = sh("git", "log", "--format=%h\t%s", f"{sha}..HEAD", "--", path)
    if r.returncode != 0:
        return None, r.stderr.strip()
    out = [ln.split("\t", 1) for ln in r.stdout.splitlines() if ln.strip()]
    return out, None


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
                if fn in FINGERPRINTS:
                    yield os.path.join(dirpath, fn)


def stamp_file(path, at=None):
    """Write a provenance stamp for `path` at `at` (default: our current HEAD).

    Pass --at when the copy is synced from an OLDER commit than HEAD, which is the
    normal case when adopting an existing app: stamping it at HEAD would claim it
    has changes it doesn't, and the checker would report it clean while it's behind.
    """
    fname = os.path.basename(path)
    if fname in DISCOVER_ONLY:
        sys.exit(f"{fname} is discovery-only — no upstream {fname} to log against; see PROPAGATE.md")
    if fname not in SHARED:
        sys.exit(f"{fname} isn't a file this skeleton owns ({', '.join(sorted(SHARED))})")
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

    # Self-check, because the failure this guards is invisible: a SHARED path that no longer
    # exists here logs zero commits for every copy of it, and the scan reports them up to date.
    # Moving or renaming one of our own files is the way that happens, and nothing else notices.
    missing = [f"{n} → {p}" for n, p in sorted(PATHS.items())
               if p and not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print("SHARED paths that don't exist here — drift for these reads as CLEAN, wrongly:")
        for m in missing:
            print(f"  {m}")
        return 1

    notes = read_propagate()
    behind, candidates, ok, broken, pinned, discovered = [], [], 0, [], [], []

    for path in walk(args.paths or [os.path.dirname(ROOT)]):
        fname = os.path.basename(path)
        text = head(path)
        m = STAMP.search(text)
        if not m:
            # Unstamped: is it recognizably ours? Read the whole file and accept ANY of the
            # file's fingerprints, since a copy may have moved things around or renamed the one
            # landmark we happened to pick. Discovery-only hits get their own bucket — the
            # generic one ends in a --stamp suggestion these must always refuse.
            body = open(path, encoding="utf-8", errors="replace").read()
            if any(fp in body for fp in FINGERPRINTS[fname]):
                (discovered if fname in DISCOVER_ONLY else candidates).append(path)
            continue
        if fname in DISCOVER_ONLY:
            # A hand-added stamp here would always read clean (`git log -- <name>` over a
            # file we don't have is empty) — surface it instead of silently passing it.
            broken.append((path, "discovery-only region — no upstream file to log against; "
                                 "remove the stamp (see PROPAGATE.md)"))
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

    if candidates:
        print("\nUnstamped copies (recognizably ours, not yet tracked):")
        for path in candidates:
            print(f"  {rel(path)}")
        print("  → adopt with: python3 scripts/check-downstream.py --stamp <file>")

    if discovered:
        print("\nDiscovery-only regions (tracked by hand in PROPAGATE.md — do not stamp):")
        for path in discovered:
            print(f"  {rel(path)}")

    print(f"\n{ok} up to date, {len(behind)} behind, {len(pinned)} pinned, "
          f"{len(candidates)} untracked, {len(discovered)} discovery-only, {len(broken)} unusable")
    return 1 if behind or broken else 0


if __name__ == "__main__":
    sys.exit(main())
