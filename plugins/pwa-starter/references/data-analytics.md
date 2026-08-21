# Data backends & analytics

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

## Google Sheets as a backend — read, write, and picking the access path — `ping.js`, `data.js`, `scripts/analytics.gs`
A private Google Sheet is the no-backend datastore these apps keep reaching for: free, no server,
editable from your phone, and you already trust Google with the data. **Writes** have exactly one path
(an Apps Script web app); **reads** have four, and the choice is a trade between *how much of the doc
you expose*, *whether you need it live*, and *how much parsing you ship*. Pick from the table, then
see [Analytics](data-analytics.md#analytics--goatcounter-for-public-stats-the-sheet-backend-for-known-audiences--pingjs-scriptsanalyticsgs-usage) for the write path worked end-to-end and wtq for a read one.

| Access | R/W | Exposes | Parse | Fresh? | Reach for it when |
|---|:--:|---|---|---|---|
| **Apps Script web app** (`doPost`/`doGet`, *Execute as: Me / Access: Anyone*) | R **+ W** | nothing — doc stays fully private, only the deployed function is public | you shape the JSON | live | the only way to **write**; also the only **private live read** (return just the columns you code) |
| **Publish-to-web CSV** (`/d/e/…/pub?gid=…&single=true&output=csv`) | R | only the **published tab** | trivial (`split`) | snapshot, ~min lag | the default read — one flat tab, zero dependencies |
| **Publish-to-web xlsx** (`…/pub?output=xlsx`) | R | only the published tab(s) | needs **SheetJS** | snapshot, ~min lag | many tabs, cell **colors/styling as data**, or real types (wtq) |
| **gviz query** (`/d/{id}/gviz/tq?tqx=out:csv&sheet=…&tq=select…`) | R | the **whole doc** (must be link-viewable) | CSV clean; JSON is wrapped | live | filter / select columns server-side without writing a script |
| **Sheets API v4** (`…/v4/…/values/{range}?key=…`) | R (W w/ OAuth) | whole doc **+ your API key in the client** | JSON | live | basically never here — skip unless you already have auth |

**The exposure column is the one that bites.** *Publish to web* makes only the tab you publish public —
the rest of the document stays private, independent of share settings — which is why both the
analytics mailbox and the `usage/` dashboard use it. *gviz* and the *Sheets API* read the **live**
document, so they require it be link-viewable and then expose **all** of it to anyone with the id.
*Apps Script* is the privacy maximalist: the doc is fully private and the endpoint returns only what
you code. So — writing, or a live read you won't make the whole sheet public for → Apps Script; a
simple public read → publish a tab; and the cute trick worth knowing (wtq) is that a **published xlsx
carries cell fills**, so *formatting becomes metadata* (background color = editorial status) and the
author never types a status column.

Gotchas, each of which cost a debugging session:
- **A plain Save doesn't redeploy an Apps Script** — Manage deployments → New version, or you're
  editing a script nobody's calling.
- **All-digit and date-like text get coerced** — an id `0042` becomes `42`, "2/3" becomes a `Date`.
  Format the column Plain-text (Apps Script side); read the cell's display text (`.w`, not `.v`) on
  the SheetJS side. The all-digit case silently breaks a hash/id join.
- **`/pub` lags and caches** — a publish-to-web read can be minutes behind the live sheet; fine for
  stale-while-revalidate, wrong if you need read-your-writes.
- **A published or link-shared tab is public forever to anyone with the URL** — keep no PII in it;
  hold names in a private tab and join at runtime (the analytics `=UID()` trick).
- **gviz JSON is wrapped** in `/*O_o*/google.visualization.Query.setResponse(…)` — strip it, or use `out:csv`.
- **A worksheet name can carry a trailing space** (`"Played "`) — exact-match tab lookups miss it.
- **Keep `doGet`/parsers tolerant of missing or old-shaped rows forever** — offline-queued writes ship
  yesterday's column layout.

Wire any read through the same stale-while-revalidate + committed-snapshot fallback as any cross-origin
data ([Offline](offline.md)) and surface the live/cached/offline state in the UI; `DATA_URL` in `data.js` is where
the read URL lands (empty = disabled, like `ping.js`'s `URL_`).

### Analytics — GoatCounter for public stats, the sheet backend for known audiences — `ping.js`, `scripts/analytics.gs`, `usage/`
**Two tools, picked by audience — and for most of these apps the audience is anonymous and public.**
The question that actually directs dev cycles is fleet-level — *which apps are alive, how much, on
what platforms* — so the default is **GoatCounter**: free, cookieless, one `async` script tag, and
volume/referrer/platform breakdowns with zero backend (haydn web's setup). It's exempt from the
no-uncached-CDN rule because the app never depends on it — it fails silently offline. One account
holds a site code per app, or share one code across apps with host-prefixed paths
(`goatcounter.count({path: location.host + location.pathname})`), so the whole fleet reads at a
glance. Reach for the **sheet-ping below** instead when the audience is a known roster (AKM: "did
Alice open it this week?" — the exception, not the rule), the tool is private / behind a strict
same-origin CSP, or offline opens must be recorded faithfully.

GoatCounter's offline caveats, verified against its published spec + a live CORS preflight (2026-07):
- The public `/count` pixel takes **no timestamp parameter** (`p/t/r/e/q/s/b/rnd` only). So a
  localStorage queue/flush (set `no_onload: true`, replay via `goatcounter.count()` on `online`)
  records offline opens at *flush* time — volume stays roughly honest; timing and session/visit
  counts skew, since a multi-day burst lands as one session (`hash(UA+IP+salt)` in a window).
- Faithful backdating exists one tier up: `POST /api/v0/count` accepts `created_at` per hit ("can
  be in the past, but not in the future"), and the API serves `Access-Control-Allow-Origin: *`
  with `Authorization` allowed — so it genuinely works from a static page with a count-only-scoped
  token (blast radius: fake pageviews, which the tokenless pixel already permits anyone).
- But notice what that queue + flush + authenticated batch-with-timestamps *is*: ping.js's
  transport rebuilt in order to rent the dashboard. If you're there, the sheet costs the same
  effort and adds the who — which is the signal you're on the wrong side of the fork.

When the audience is small and known, **a log you own beats a dashboard you rent.** This is the *write*
side of [Google Sheets as a backend](data-analytics.md#google-sheets-as-a-backend--read-write-and-picking-the-access-path--pingjs-datajs-scriptsanalyticsgs) put to one use — recording opens into an Apps Script mailbox
(anyone can drop a row, only you can read the sheet). What's analytics-specific on top of the transport:
- `ping.js` **queues opens in `localStorage` and flushes when online** (fire-and-forget, loaded last,
  never blocks render) — offline opens are recorded at open time, delivered later.
- Identify users by a **one-way hash** of a stable name (first 4 bytes of SHA-256), never the name —
  the log holds no PII; reverse it against your own roster with a `=UID()` formula *in the sheet*.
  Empty uid = an anonymous open (a useful "a stranger found the URL" tripwire).
- **`URL_` empty = disabled but harmless** — ship the client before the backend exists; the backlog
  flushes when the URL lands.
- The **`usage/` dashboard** reads the same data back — a publish-to-web CSV of the pings tab (the read
  path from the table above), crunched in the browser (`usage/crunch.js`), stale-while-revalidate from
  localStorage, `noindex`. Names never enter the repo — uids only; join at runtime if you want them.
