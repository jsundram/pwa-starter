#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""Commit-time checks for sw.js's precache contract.

sw.js precaches the app SHELL. Seven mistakes are cheap to catch here and expensive at runtime:

1. A staged SHELL file with an unchanged V. An edit to a precached file only reaches installed
   clients when V changes — forget the bump and the fix ships to the repo but never to anyone's
   home-screen copy. The single most common PWA deploy bug.
2. A SHELL entry that doesn't exist on disk. It can never be fetched, so it permanently wedges
   the old-generation collect: both cache generations pile up on every device, with the stale one
   still answering via the whole-store fallback. (#7)
3. A cross-origin SHELL entry. The fetch handler passes other origins straight through, so the
   entry would be cached but never served — vendor the file locally instead.
4. A V without a numeric tail. The tail is what makes sw.js's collect DIRECTIONAL (delete only
   strictly older generations); a non-numeric V makes collection silently stop, no error, no
   symptom, until caches pile up. Rename the stem freely — keep the digits.
5. app.js's VER_PREFIX not matching V's stem. checkVer() uses that prefix to decide whether a
   worker is installed at all, so a renamed stem on one side only makes the version tag go blank
   (no cache matches) or read a sibling app's caches — silently, since nothing throws. (#7)
6. app.js's APP_V not matching V. APP_V is the version the running bundle REPORTS, and what
   checkVer() compares against the server. Let it drift and a client running a stale bundle
   compares the wrong number: the tag reads current and never offers the update, on exactly the
   device that needs it. (#17)

Checks 1-6 read ONE commit, which is all the pre-commit hook has. That leaves a hole no single
commit can see: two branches off the same base can each bump v32 -> v33 byte-identically, and a
three-way merge resolves that without a conflict — so the second one lands its shell changes with
a net V delta of ZERO. Each PR was right about its own parent; the merge is still broken. Hence a
seventh check, which needs a second commit to compare against and so takes it as an argument:

7. `--base REF`: a branch that changes shell files without carrying V past the one REF is already
   on. What the branch CHANGED is read from the merge base (the diff a rebase, a squash and a
   stacked branch all leave alone); which V it must CLEAR is read from REF's TIP, which is what it
   is about to merge into — against the merge base instead, the motivating case passes, since both
   branches did differ from their own v32 base. It REPLACES checks 1-6 rather than joining them,
   being a different question asked with different information, and it is where CI earns its keep:
   CI has both sides of the merge and the hook has neither. Ported up from quartet-composers,
   which paid for it (its #32). (#15)

The pre-commit hook runs 1-6 warn-only; run them in CI with a real exit code, and the seventh on
pull requests with the base ref. By hand:
    python3 scripts/sw-lint.py
    python3 scripts/sw-lint.py --base origin/main
"""
import os, re, subprocess, sys


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True)


def ver(src):
    # Anchored to the DECLARATION — the same expression app.js's checkVer() uses (keep them in
    # agreement). sw.js's comments cite version names as examples, so a first-match-anywhere
    # scan would read a comment.
    m = re.search(r'const V\s*=\s*"([^"]*)"', src)
    return m.group(1) if m else None


def tail_of(v):
    """The numeric generation at the end of a V, or None if it hasn't got one."""
    m = re.search(r"(\d+)$", v or "")
    return int(m.group(1)) if m else None


def shell_entries(src):
    m = re.search(r"const SHELL\s*=\s*\[(.*?)\]", src, re.S)
    if not m:
        return []
    # Alternation, not a strip pass: deleting //-comments first would also eat the "//" inside a
    # cross-origin URL plus every entry after it on that line — failing open on exactly what the
    # cross-origin check exists to catch. Scanning left to right, a comment consumes any strings
    # it contains, so a commented-out entry ('// "./old-page.html",') is correctly ignored.
    return [s for s in re.findall(r'//[^\n]*|"([^"]+)"', m.group(1)) if s]


def shell_paths(src):
    """SHELL entries as repo-relative paths — the shape `git diff --name-only` emits.

    Normalizes the DIRECTORY form ("./", "./usage/") to the document it serves. Both V-bump checks
    compare SHELL against a list of changed files from git, and git never emits "usage/" — so a
    SHELL that lists only "./docs/" (a legitimate shape; it is the form this skeleton itself uses
    for "./" and "./usage/") was invisible to both of them. Upstream that was masked by
    "./usage/index.html" being listed explicitly as well.

    The existence check in main() has always normalized this way; the touched-set comparisons did
    not, which meant the two halves of the same file disagreed about what a shell entry IS.
    Cross-origin entries drop out — they can't be repo paths, and they're check 3's business.
    """
    out = set()
    for e in shell_entries(src):
        if "://" in e:
            continue
        p = e.lstrip("./")
        if not p or p.endswith("/"):
            p += "index.html"
        out.add(p)
    return out


# "The SHELL list could not be read" must never resolve to "nothing to check". An unparseable
# block (a SHELL spread from a constant, a nested bracket, a reformat the non-greedy regex reads
# short) yields an empty list, and every comparison against an empty list passes. That is the same
# "a check that passes when it could not run" failure the --base block commits against below, and
# it matters most in exactly the case this whole file is being synced for: six downstream copies
# whose service workers are shaped differently from ours.
NO_SHELL = ("could not read a SHELL list out of sw.js — the parser expects `const SHELL = [ … ]` "
            "with string literals. Every shell comparison would otherwise run against an EMPTY "
            "list and report success, so this reports instead.")


# Check 7. The hook cannot ask this: it sees one commit against its parent, so a branch that bumps
# v32 -> v33 from a base that has since become v33 looks correct at every step and still merges to
# a net delta of zero. CI has both sides.
#
# TWO references, deliberately, because the two halves are different questions:
#   - WHAT THIS BRANCH CHANGED is measured from the MERGE BASE, so a base that moved ahead does not
#     come back as files this branch touched. That is also the diff a rebase, a squash and a
#     stacked branch all leave unchanged.
#   - WHICH V IT HAS TO CLEAR is REF's TIP, because the tip is what it is about to merge into.
#     Against the merge base instead, the motivating case passes: both branches bumped v32 -> v33
#     off a v32 base, so each differs from its own merge base and the second still lands a net zero.
#
# Everything here is REPORTED rather than skipped, including "I could not read the base". Silence
# is what opened the hole in the first place — a check that passes when it could not run is a check
# reporting an answer it does not have.
def base_check(ref):
    mb = sh("git", "merge-base", ref, "HEAD")
    if mb.returncode != 0 or not mb.stdout.strip():
        return [f'no merge base between HEAD and "{ref}" — with a shallow checkout there is '
                "nothing to compare V against, so this check cannot run. Fetch enough history "
                "(actions/checkout with fetch-depth: 0) rather than letting it pass silently."]
    mb = mb.stdout.strip()

    head, base = sh("git", "show", "HEAD:sw.js"), sh("git", "show", f"{ref}:sw.js")
    if head.returncode != 0 or base.returncode != 0:
        return []                                 # sw.js added on this branch: no prior V to hold
    v, old = ver(head.stdout), ver(base.stdout)
    if v is None or old is None:
        return []                                 # no declaration to read; checks 1-6 own that

    # The UNION of both SHELL lists, because DROPPING an entry is itself a shell change: clients
    # that already cached it keep serving it out of the old generation until V moves.
    shell = shell_paths(head.stdout) | shell_paths(base.stdout)
    if not shell:
        return [NO_SHELL]
    diff = sh("git", "diff", "--name-only", mb, "HEAD")
    touched = sorted(set(diff.stdout.split()) & shell)
    if not touched:
        return []

    files = ", ".join(touched)
    if v == old:
        return [f'V is "{v}" on both this branch and {ref}, but the branch changes precached '
                f"shell files ({files}) — merging it leaves every installed client on the cached "
                "version. Bump V in sw.js."]
    # Any bump clears it (one generation per push is fine); the tail must only ever go UP, because
    # sw.js's collect deletes strictly LOWER generations — a backwards V makes this branch's own
    # cache the one that gets collected. A renamed stem is a deliberate reset (rule 4: rename
    # freely, keep the digits), so the tails aren't comparable and V simply differing is the whole
    # answer.
    if re.sub(r"\d+$", "", v) == re.sub(r"\d+$", "", old):
        t, ot = tail_of(v), tail_of(old)
        if t is not None and ot is not None and t < ot:
            return [f'V is "{v}" but {ref} is already on "{old}", and the branch changes precached '
                    f"shell files ({files}) — the numeric tail orders cache generations, so this "
                    f"one would be collected as the stale one. Bump past {ot}."]
    return []


def main():
    if "--base" in sys.argv:
        i = sys.argv.index("--base")
        if i + 1 >= len(sys.argv):
            print("  sw.js:\n   - --base needs a ref to compare against")
            return 1
        problems = base_check(sys.argv[i + 1])
        if not problems:
            return 0
        print("  sw.js:")
        for p in problems:
            print(f"   - {p}")
        return 1

    idx = sh("git", "show", ":sw.js")            # staged sw.js
    if idx.returncode != 0:
        return 0                                  # no sw.js in the index / not a repo
    src = idx.stdout
    v = ver(src)
    entries = shell_entries(src)
    problems = []

    if not entries:
        problems.append(NO_SHELL)

    if v is not None and tail_of(v) is None:
        problems.append(f'V is "{v}", which has no numeric tail. The tail is what makes sw.js\'s '
                        "collect directional (older generations only) — rename the stem freely, "
                        "but keep the digits.")

    # Downstream copies don't always vendor app.js (some graft only the version-tag region, some
    # skip it), so a missing file or a missing declaration is silence, not a problem.
    app = sh("git", "show", ":app.js")
    if v is not None and app.returncode == 0:
        m = re.search(r'const VER_PREFIX\s*=\s*"([^"]*)"', app.stdout)
        stem = re.sub(r"\d+$", "", v)
        if m and m.group(1) != stem:
            problems.append(f'app.js\'s VER_PREFIX is "{m.group(1)}" but sw.js\'s V stem is '
                            f'"{stem}" — checkVer() looks for caches under that prefix, so the '
                            "version tag silently stops tracking this app. Keep the two in "
                            "agreement.")
        # ver()'s regex is anchored to `const V`, so it never matches `const APP_V`; this one is
        # anchored the same way for the same reason.
        mv = re.search(r'const APP_V\s*=\s*"([^"]*)"', app.stdout)
        if mv and mv.group(1) != v:
            problems.append(f'app.js\'s APP_V is "{mv.group(1)}" but sw.js\'s V is "{v}" — '
                            "checkVer() reports APP_V as the version this device is RUNNING, so "
                            "a drifted pair compares the wrong number and the tag goes quiet on "
                            "a stale client. Bump both together.")

    top = sh("git", "rev-parse", "--show-toplevel").stdout.strip()
    for entry in entries:
        if "://" in entry:
            problems.append(f'SHELL entry "{entry}" is cross-origin — the fetch handler passes '
                            "other origins straight through, so it caches but never serves. "
                            "Vendor the file locally.")
            continue
        p = entry.lstrip("./")
        if not p:
            continue                              # "./" — the scope root, served as index.html
        if p.endswith("/"):
            p += "index.html"                     # a directory entry serves its index.html
        if top and not os.path.exists(os.path.join(top, p)):
            problems.append(f'SHELL entry "{entry}" doesn\'t exist ({p}) — an unfetchable entry '
                            "wedges the old-generation collect on every device. Fix the path, or "
                            "generate the file (icons: scripts/make-icons.sh).")

    shell = shell_paths(src)
    staged = set(sh("git", "diff", "--cached", "--name-only").stdout.split())
    touched = sorted((staged & shell) - {"sw.js"})
    if touched:
        head = sh("git", "show", "HEAD:sw.js")
        old = ver(head.stdout) if head.returncode == 0 else None
        if old is not None and v == old:          # not the first commit, and V unchanged
            problems.append(f'V is still "{v}" but this commit changes precached shell files '
                            f'({", ".join(touched)}) — bump V in sw.js or installed clients '
                            "keep the cached version.")

    if not problems:
        return 0
    print("  sw.js:")
    for p in problems:
        print(f"   - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
