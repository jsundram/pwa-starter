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

STAMP = re.compile(r"pwa-starter:\s*(\S+?)\s*@\s*([0-9a-f]{7,40})")
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
    """Commits to `fname` in THIS repo after `sha`. (None, reason) if the sha is unusable."""
    if sh("git", "cat-file", "-e", sha + "^{commit}").returncode != 0:
        return None, f"unknown commit {sha} — not in this repo (rebased? typo?)"
    r = sh("git", "log", "--format=%h\t%s", f"{sha}..HEAD", "--", fname)
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

    notes = read_propagate()
    behind, candidates, ok, broken = [], [], 0, []

    for path in walk(args.paths or [os.path.dirname(ROOT)]):
        fname = os.path.basename(path)
        text = head(path)
        m = STAMP.search(text)
        if not m:
            # Unstamped: is it recognizably ours? Read the whole file for the fingerprint,
            # since a copy may have moved things around.
            if SHARED[fname] in open(path, encoding="utf-8", errors="replace").read():
                candidates.append(path)
            continue
        stamped_name, sha = m.group(1), m.group(2)
        commits, err = commits_since(sha, stamped_name)
        if err:
            broken.append((path, err))
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

    if candidates:
        print("\nUnstamped copies (recognizably ours, not yet tracked):")
        for path in candidates:
            print(f"  {rel(path)}")
        print("  → adopt with: python3 scripts/check-downstream.py --stamp <file>")

    print(f"\n{ok} up to date, {len(behind)} behind, {len(candidates)} untracked, {len(broken)} unusable")
    return 1 if behind or broken else 0


if __name__ == "__main__":
    sys.exit(main())
