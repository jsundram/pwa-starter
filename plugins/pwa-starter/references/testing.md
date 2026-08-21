# Testing without a build

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

## What this repo actually does

The skeleton's own answer is **`scripts/sw.test.mjs`**: it loads `sw.js` *unmodified* under mocked
service-worker globals (`self`, `caches`, `fetch`, `Response`) and a fake clock, so the `withTimeout`
bounds run deterministically and instantly. Zero dependencies, no `package.json`, no `node_modules`,
no browser engine — plain `node scripts/sw.test.mjs`, wired into `.github/workflows/checks.yml`
alongside `sw-lint.py` and run warn-only from `.githooks/pre-commit`.

Keep its `process.exitCode = 1` hang guard: with only fake timers, a hung handler drains node's event
loop and exits 0 — silently green on the exact regression the suite exists to catch.

It covers the fetch handler only. The precache/generation half — `ensureShell()`, the directional
collect, `cacheLookup()`'s V-scoping — is held by prose and `sw-lint.py`, not by these tests.

## The heavier option — `package.json` as a dev-only harness

When an app needs a real browser (a touch gesture, a rendered layout), the trick is keeping the
harness *off* the deployed site. AKM keeps a `package.json` whose own description says it plainly ("the site itself is static, this is
just the test harnesses"): `private: true`, a `playwright-core` devDependency, and `node` test scripts
— **no bundler, no build step reaches the shipped files.** The site stays hand-written; the tests are
tooling that never deploys (same segregation as `scripts/`). Two patterns worth stealing:
- **Network-gate any test that hits live data — skip (exit 0), don't fail, when it's unreachable.**
  AKM's tests that read the live Google Sheet exit cleanly offline or in a locked-down sandbox instead
  of going red, so "no network" never reads as "broken" (same idea as `setup-environment.sh` being
  non-fatal). Pure-logic tests run off a committed fixture and pass anywhere; PII-bearing data gets no
  committed fixture, so its tests are live-only and gated.
- **Test the *working tree* on a real phone before pushing — a Node/Playwright harness can't see a
  touchscreen.** Touch-only bugs (a `click`/`pointerdown`/`touchstart` handler that only misfires on
  iOS — see the double-fire gotcha in [Mobile](mobile-a11y.md)) need a real device. AKM's method: `python3 -m http.server
  8000 --bind 0.0.0.0` + `ngrok http 8000` for a public HTTPS URL, opened in an **iOS Safari Private
  tab — which doesn't register the service worker, so nothing caches** and every reload is the latest
  code. That last bit is the point: it rules out "is this my fix or a stale SW?" at the same time, the
  question that otherwise eats an hour on any installed PWA.
