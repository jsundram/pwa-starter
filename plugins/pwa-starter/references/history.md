# The maturity gradient (why the checklist exists)

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

**This table is a historical snapshot, deliberately not maintained.** It records the state of the
source apps *at the time they motivated this skeleton* — it's the evidence for why each checklist row
exists, not a status board. Several of these apps have since been retrofitted *from* this skeleton
(boccherini and haydn both have manifests and service workers now), which would make a
kept-current version circular: the apps that taught the checklist now pass it because of it. For
"which repos are downstream and need a fix propagated," see the registry, not this table.

The four source apps land at different points on exactly these axes; the gaps are the lesson. The
fifth column, gallery-deck, is the boundary case — it clears the checklist that matters for its
deployment (a private tailnet tool) but crosses the last row.

| Capability | boccherini | haydn web | lobsters | AKM | gallery-deck |
|---|:-:|:-:|:-:|:-:|:-:|
| Dark mode / responsive | ✅ | ✅ | ✅ | ✅ | ✅ |
| Favicon / icons | ❌ | ✅ | ✅ | ✅ | ✅ |
| OG / share card | ❌ | ✅ | ✅ | ✅ | ❌ |
| `apple-*` / theme-color | ❌ | partial | ✅ | ✅ | partial |
| Web app manifest | ❌ | ❌ | ✅ (runtime) | ✅ | ✅ |
| Offline service worker | ❌ | ❌ | ✅ (inlined) | ✅ | ✅ (shell) |
| Cache-bust discipline (`V` + lint) | — | — | — | ✅ | `V`, no lint |
| Usage analytics | ❌ | GoatCounter | ❌ | ✅ (own sheet) | ❌ |
| Backend / DB | ❌ | ❌ | ❌ | ❌ | ✅ |

Git history says the retrofits were remarkably uniform: **share-sheet metadata + a preview image**
(added late in lobsters *and* both haydn pages), **dark mode** (a whole PR saga in boccherini,
including a separate pass just for print/PDF), **mobile layout and tap-fallbacks for hover tooltips**
(haydn's scatter, boccherini's "mobile tooltips"), **favicons + meta polish**, **analytics**, and in
boccherini even the **`viewport` tag itself**. This skeleton front-loads all of it.

gallery-deck is the app that **graduated past the skeleton**: scaffolded from it, then grown a
FastAPI + SQLite + media backend — proof the "no backend" boundary is real, and where you stop
reaching for this checklist and start writing a server. It kept just three skeleton ideas (the SW
`V`-bump/network-first shell, the tap-to-update `#ver` tag, CSS-variable theming) and still managed a
fresh instance of the `sw.js` probe-cache gotcha below — the doc was right, the app forgot the guard.
