# pwa-starter

An opinionated starting point for a small, static, single-author **PWA** — the kind you build in a
weekend, host on GitHub Pages, open on your phone, and text to a few people. It ships with the
things that always get bolted on *late*: a share card, offline caching, install polish, dark mode,
cache-busting, and dead-simple private analytics.

It's the distilled memory of four hand-built web apps
([AKM](https://github.com/jsundram/akm),
[lobsters-and-lighthouses](https://github.com/jsundram/lobsters-and-lighthouses),
[haydn-info-card](https://github.com/jsundram/haydn-info-card),
[quartets.boccherini.org](https://github.com/jsundram/quartets.boccherini.org)) — every one of
which grew the same list of forgotten-then-retrofitted features. This repo turns that list into a
checklist and a working file set so the next app starts past those mistakes.

## Two ways to use it

**Start a new project** — clone this repo (or use it as a GitHub *template*), open a Claude Code
session in it, and say:

> I'd like to make a new project based on pwa-starter.

Claude follows [`CLAUDE.md`](CLAUDE.md) → *New project*: it asks for the name / description / URL,
replaces the placeholders, generates the icons, and hands you a running app.

**Audit an app you already have** — open a Claude session in that app's repo, add this repo to the
session, and say:

> Audit this app against the pwa-starter checklist and tell me what's missing.

Claude follows [`CLAUDE.md`](CLAUDE.md) → *Audit an existing app*: it runs the checklist against
your code and reports the gaps (this is exactly how you'd bring Haydn or Boccherini up to spec).

## What's in the box

```
index.html      app shell + head (OG, icons, apple metas, theme-color, safe-area)
styles.css      design system — CSS variables, light + dark, responsive, print
app.js          boot: SW registration + "you're on an old version, tap to update" tag
sw.js           offline precache + the cache-busting version constant V
manifest.json   installability
ping.js         optional: queue-offline usage pings → a private Google Sheet
usage/          optional: a client-side dashboard that reads those pings back
assets/         icon.svg + og.svg (sources) → run the scripts to rasterize
scripts/        make-icons.sh · make-og.sh · sw-lint.py · analytics.gs (backend reference)
.githooks/      pre-commit that runs sw-lint (enable: git config core.hooksPath .githooks)
```

## First run

```sh
scripts/make-icons.sh          # icon.svg → the PNGs the head + manifest reference (needs rsvg-convert)
scripts/make-og.sh             # og.svg → assets/og.png (the share card)
python3 -m http.server 8000    # open http://localhost:8000/  — installable + offline after one load
```

Then read [`CLAUDE.md`](CLAUDE.md) for the full checklist and the reasoning behind each piece.
