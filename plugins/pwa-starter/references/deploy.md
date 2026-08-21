# Deploy & multi-page

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

## Multi-page — the shared-nav pattern

> **A pattern to add, not a shipped file.** The skeleton is a one-pager and ships no `nav.css`; the
> filename below is the convention to create when a second page appears.

This skeleton is a one-pager, but the moment there's a second HTML page (AKM has seven), two things
change. **CSS splits** (already the rule: inline is fine for a strict one-pager, split to `styles.css`
the instant there's a second page), and you need a **shared nav that doesn't fork per page**. AKM's
pattern, worth copying: the nav markup is *static in each page's HTML* (no JS builds it — it must
render before the bundle so there's no flash), and one `nav.css` styles it by **reusing each page's
own palette tokens** (`var(--ink/--muted/--line/--accent)`) rather than hard-coding colors — so the
nav themes correctly (light **and** dark) on every page with zero per-page overrides. Mark the current
page with **`aria-current="page"`** (static in the markup, not a JS-added class — it's the semantic
signal *and* the style hook), and collapse the wordmark to an abbreviation at a narrow breakpoint so it
never wraps into the links. One `SHELL` in `sw.js` enumerates every page + its JS + data so the whole
app is offline, and — the earlier note bites here — the page an installed copy reopens daily should be
the root; "read once" pages (about, invite) are *separate* URLs you send.

### Deploy
GitHub Pages, `main`/root, relative paths → `user.github.io/repo/`. After deploy, open the URL
**online once** to prime the SW cache, then Add to Home Screen. The only thing verifiable *live* is a
real cross-origin fetch — if that data renders at the Pages URL, everything downstream is proven.

**Decide public vs private up front — it's an indexing + PII posture, not an afterthought.** A public
app is fine to leave crawlable. A **private participant tool** (AKM: a roster app for one festival's
players) should be un-findable: put `<meta name="robots" content="noindex,nofollow">` on **every**
page *and* a site-wide `robots.txt` (`Disallow: /`) — belt and suspenders, since the meta and the file
each cover cases the other misses — and keep PII out of the repo entirely (hold names in a private
sheet, join at runtime; no committed fixtures). Note a `noindex` page is still *public to anyone with
the URL* — indexing control is not access control.

**GitHub Pages isn't the only target — a private PWA can be self-hosted.** gallery-deck runs on a Mac
mini and reaches the phone over **Tailscale Serve (HTTPS)** instead of Pages; installability + the SW
+ offline all still matter *identically*, but the checklist reshapes — the share card, `robots`, and
"prime online once" drop to low-stakes for a tool only ever opened on your own tailnet. Two moves
worth stealing whatever the host: pick a **neutral hostname before any HTTPS cert is issued** (cert
hostnames land in *public* Certificate Transparency logs, so a descriptive name leaks the app's
existence to the world — access control the `noindex` above can't give you), and default a
private-network tool to **localhost-bind + a strict same-origin CSP** so it's not reachable or
embeddable beyond where you put it.
