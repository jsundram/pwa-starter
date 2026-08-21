# Sharing & install — head, icons, share card, manifest

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

## HTML head / meta — `index.html`
- **OG image: absolute + raster + compressed.** iMessage/WhatsApp/Slack scrapers reject relative
  paths, won't render SVG, and skip images that are too big. 1200×630, run it through pngquant.
- **`theme-color` is per-scheme** (`media="(prefers-color-scheme: …)"`) — it tints the browser UI.
- **`color-scheme: light dark`** up top kills the first-paint white flash in dark mode.
- iOS reads `apple-touch-icon` + the `apple-mobile-web-app-*` metas and *mostly ignores the
  manifest*; Android reads the manifest. Ship both or one platform's install looks broken.

### Icons & share image — `assets/`, `scripts/make-*.sh`
One SVG is the source; rasterize from it, never hand-edit PNGs (they drift). `make-icons.sh` →
180/192/512; `make-og.sh` → the 1200×630 card. If the card has live `<text>`, the font must be
installed locally or the render falls back to a stock serif. **`make-og.sh` compresses the card and
hard-fails if it lands over ~250 KB** (a margin under WhatsApp's ~300 KB scrape cutoff), and
`og-lint.py` re-checks the staged PNG in the pre-commit — so "compress the share image" is enforced,
not remembered. That's the `sw-lint.py` discipline applied to the *other* forgot-it asset: a card too
big to scrape previews as a grey box, and you don't find out until someone texts the link back blank. Neat single-page trick (lobsters): one
SVG **data-URI** used for `apple-touch-icon` *and* a **runtime-generated manifest** (a tiny script
builds it as a Blob URL) — zero icon files. This skeleton uses real files since multi-page apps cache
them anyway.

A third-party previewer is a good first pass but not an audit: it renders its *own* simulation from
your tags rather than running Apple's or Meta's scraper (iMessage and WhatsApp, the two that matter
most here, have no official debugger at all), it happily previews a card too big for a scraper to
fetch — that's `og-lint.py`'s job, not its — and it can't clear a *cached* bad preview, which still
needs Facebook's Sharing Debugger or LinkedIn's Post Inspector (X's validator died in 2022). It also
needs a public URL, so it's a post-deploy check and no help to a tailnet/private app.

## Manifest / installability — `manifest.json`
`start_url:"./"` + relative `scope` so it works as a project page. Include a 512 `maskable` icon or
Android crops your square badly — and make the maskable a **full-bleed** tile (background fill, logo
inside the center-80% safe zone), not your transparent favicon, or the mask eats the edges. The spec
is concrete: the guaranteed-visible safe zone is a **circle of radius 40% of the icon width** (= the
central 80%), and the tile needs an **opaque background covering the whole area** or the mask crops
into art; set the manifest icon's `"purpose": "maskable"` (or `"any maskable"` on one icon to serve
both). Preview the crop across the OS mask shapes (circle / squircle / teardrop) at **maskable.app**
before shipping — it's a GUI eyeball-check, not something `make-icons.sh` can automate. Note: an
installed copy opens `start_url` many times — so the page you want opened *daily* should be the root,
and a "read once" invite/about page should be a *separate* URL you send, not the root.

**Seed per-device config with a link, not a re-typed form.** A no-backend app that needs a scrap of
setup (an API key, a data-source URL) faces an awful phone UX: retype it on a tiny keyboard. Instead,
read a `?data=…`/`?key=…` param on first load, persist it to `localStorage`, then strip it from the
URL — and give the *desktop* a "copy setup link" button that builds that URL. Configure once on the
big screen, AirDrop/iMessage the link to the phone, open it, done. quartet-log seeds its Google-Sheet
URL exactly this way. Flip side of the note above: a link that carries state **is** a send-once URL —
don't make it the `start_url` an installed copy reopens daily.

Left as prose, not a shipped file — it's ~10 lines and only some apps need it. But the two subtleties
that cost a debugging session are worth pinning down: strip the param with `history.replaceState`
(not `location.search = …`, which reloads and adds a history entry), and strip it **before** anything
reads the URL — a `fetch` leaks it in the `Referer` header, analytics log `location.href`. So run this
first thing at boot:

```js
// First load: adopt ?data=… (or ?key=…), then scrub it from the URL.
function consumeConfigParam(){
  const u = new URL(location.href);
  const v = u.searchParams.get("data");
  if(!v) return;
  if(isValid(v)) localStorage.setItem("app-data-url", v);   // validate BEFORE you trust it
  u.searchParams.delete("data");
  history.replaceState(null, "", u.pathname + u.search + u.hash);   // no reload, no history entry
}

// Desktop "copy setup link" builder — encodeURIComponent so the value survives the URL.
const buildSetupLink = v => `${location.origin}${location.pathname}?data=${encodeURIComponent(v)}`;
```
