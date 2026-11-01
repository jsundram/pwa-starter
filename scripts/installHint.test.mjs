#!/usr/bin/env node
// Behavioral tests for installHint.js — WHEN the install banner shows, and what it remembers.
//
// It loads installHint.js UNMODIFIED under a mocked browser (navigator, matchMedia, localStorage,
// a minimal DOM) and fires beforeinstallprompt / appinstalled by hand, so every platform branch
// runs in plain node. No dependencies, no browser.
//
//     node scripts/installHint.test.mjs
//
// Logic only. Layout (44px buttons, safe-area inset, the dark card) needs a real browser and an
// eye; check it once when you restyle the banner. Exits non-zero on any failed assertion.
import { readFileSync } from "node:fs";

const SRC = readFileSync(new URL("../installHint.js", import.meta.url), "utf8");

// ---- a DOM just big enough for render() ------------------------------------
// innerHTML is only ever the iOS message; it yields a <b> exactly when the markup holds one,
// which is the case the NAME placeholder decides.
function node(tag) {
  return {
    tag, id: "", className: "", textContent: "", onclick: null, children: [], parent: null, attrs: {}, _html: "", _b: null,
    setAttribute(k, v) { this.attrs[k] = v; },
    append(...cs) { for (const c of cs) { c.parent = this; this.children.push(c); } },
    appendChild(c) { this.append(c); return c; },
    remove() { if (this.parent) { this.parent.children = this.parent.children.filter((c) => c !== this); this.parent = null; } },
    set innerHTML(h) { this._html = h; this.children = []; this._b = h.includes("<b></b>") ? node("b") : null; },
    get innerHTML() { return this._html; },
    querySelector(sel) { return sel === "b" ? this._b : null; },
  };
}
const text = (n) => [n._html, n._b ? n._b.textContent : "", n.textContent, ...n.children.map(text)].join(" ");
const buttons = (n) => n.tag === "button" ? [n] : n.children.flatMap(buttons);

// ---- platforms ---------------------------------------------------------------
const IPHONE = { ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X)", platform: "iPhone", touchPoints: 5, coarse: true };
const IPAD = { ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", platform: "MacIntel", touchPoints: 5, coarse: true };
const MAC = { ua: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)", platform: "MacIntel", touchPoints: 0, coarse: false };
const ANDROID = { ua: "Mozilla/5.0 (Linux; Android 14; Pixel 8)", platform: "Linux armv8l", touchPoints: 5, coarse: true };

// One page load. Pass the same `store` to a second load to model a reload.
function load(dev, { store = {}, standalone = false, displayStandalone = false, storageThrows = false,
                     title = "Demo", src = SRC } = {}) {
  const listeners = {};
  const body = node("body");
  const window = {};
  const navigator = { userAgent: dev.ua, platform: dev.platform, maxTouchPoints: dev.touchPoints };
  if (standalone) navigator.standalone = true;
  const matchMedia = (q) => ({ matches: q.includes("display-mode: standalone") ? displayStandalone
                                       : q.includes("pointer: coarse") ? dev.coarse : false });
  const localStorage = storageThrows
    ? { getItem() { throw new Error("SecurityError"); }, setItem() { throw new Error("SecurityError"); } }
    : { getItem: (k) => store[k] ?? null, setItem: (k, v) => { store[k] = String(v); } };
  const document = {
    body, title,
    createElement: node,
    querySelector: (sel) => sel.includes("apple-mobile-web-app-title") ? { content: title } : null,
  };
  const addEventListener = (t, fn) => { listeners[t] = fn; };
  new Function("window", "navigator", "matchMedia", "localStorage", "document", "addEventListener", src)(
    window, navigator, matchMedia, localStorage, document, addEventListener,
  );
  const banner = () => body.children.find((c) => c.id === "install-hint") || null;
  const tap = async (label) => { const b = buttons(banner() || node("x")).find((b) => b.textContent === label); if (b) await b.onclick(); return !!b; };
  return { IH: window.InstallHint, store, banner, tap, fire: (t, e = {}) => listeners[t] && listeners[t](e), listens: (t) => t in listeners };
}
function bip(outcome = "accepted") {
  return { defaultPrevented: false, prompted: false, preventDefault() { this.defaultPrevented = true; },
           prompt() { this.prompted = true; }, userChoice: Promise.resolve({ outcome }) };
}
const flush = async () => { for (let i = 0; i < 10; i++) await Promise.resolve(); };

let pass = 0, fail = 0;
const ok = (name, cond, detail = "") => { if (cond) { pass++; console.log("  ok   -", name); } else { fail++; console.log("  FAIL -", name, detail); } };
const labels = (pg) => (pg.banner() ? buttons(pg.banner()).map((b) => b.textContent) : []);

(async () => {
  let pg, e;

  // --- iOS: no event exists, so the hint is the steps, shown at init -------------------------
  pg = load(IPHONE);
  pg.IH.init();
  ok("iPhone tab → banner at init", !!pg.banner());
  ok("iPhone banner names the app and carries the storage note", /Demo/.test(text(pg.banner())) && /own storage/.test(text(pg.banner())));
  ok("iPhone banner has only Not now (iOS can't be prompted)", labels(pg).join() === "Not now", labels(pg).join());

  pg = load(IPAD);
  pg.IH.init();
  ok("iPad reporting as a Mac → banner", !!pg.banner());

  const store = {};
  pg = load(IPHONE, { store });
  pg.IH.init();
  await pg.tap("Not now");
  ok("Not now → banner gone, remembered", !pg.banner() && store["app-install-hint"] === "later", JSON.stringify(store));
  pg = load(IPHONE, { store });
  pg.IH.init();
  ok("reload after Not now → no banner", !pg.banner());
  ok("show() overrides Not now", pg.IH.show() === true && !!pg.banner());

  pg = load(IPHONE, { title: '<img src=x onerror="alert(1)">' });
  pg.IH.init();
  ok("title goes in as text, not markup", pg.banner().children[0]._b.textContent.startsWith("<img") && !pg.banner().children[0]._html.includes("<img"));

  // Rewording the message without NAME must still render — no placeholder, no crash.
  pg = load(IPHONE, { src: SRC.replace(/ios: "Install NAME:/, 'ios: "Install this app:') });
  let threw = null;
  try { pg.IH.init(); } catch (err) { threw = err; }
  ok("iOS wording without NAME → renders, no throw", !threw && !!pg.banner(), String(threw));

  pg = load(IPHONE);
  pg.IH.init({ auto: false });
  ok("{ auto: false } → nothing at init", !pg.banner());
  ok("{ auto: false } → show() shows it", pg.IH.show() === true && !!pg.banner());

  // --- installed: never ----------------------------------------------------------------------
  pg = load(IPHONE, { standalone: true });
  pg.IH.init();
  ok("iOS Home Screen app → no banner, show() refuses", !pg.banner() && pg.IH.show() === false && pg.IH.installed);
  pg = load(ANDROID, { displayStandalone: true });
  pg.IH.init();
  ok("installed Android app → no listeners, show() refuses", !pg.listens("beforeinstallprompt") && pg.IH.show() === false);

  // --- Chromium: wait for beforeinstallprompt, then offer the browser's own dialog ----------
  pg = load(ANDROID);
  pg.IH.init();
  ok("Android before the event → no banner", !pg.banner());
  pg.fire("beforeinstallprompt", (e = bip("accepted")));
  ok("Android event → default prevented, banner with Install", e.defaultPrevented && labels(pg).join() === "Install,Not now", labels(pg).join());
  await pg.tap("Install");
  await flush();
  ok("Install → prompt() called, banner gone", e.prompted && !pg.banner());
  ok("accepted dialog → remembered as installed", pg.store["app-install-hint"] === "installed", JSON.stringify(pg.store));

  pg = load(ANDROID);
  pg.IH.init();
  pg.fire("beforeinstallprompt", (e = bip("dismissed")));
  await pg.tap("Install");
  await flush();
  ok("cancelled dialog → remembered as Not now", pg.store["app-install-hint"] === "later", JSON.stringify(pg.store));
  const s2 = pg.store;
  pg = load(ANDROID, { store: s2 });
  pg.IH.init();
  pg.fire("beforeinstallprompt", (e = bip()));
  ok("reload after a cancelled dialog → no banner", !pg.banner());
  ok("…but show() still offers Install", pg.IH.show() === true && labels(pg).includes("Install"));

  pg = load(ANDROID);
  pg.IH.init();
  pg.fire("beforeinstallprompt", bip());
  pg.fire("appinstalled");
  ok("appinstalled → banner gone, remembered", !pg.banner() && pg.store["app-install-hint"] === "installed");

  // --- desktop: off unless asked ---------------------------------------------------------------
  pg = load(MAC);
  pg.IH.init();
  pg.fire("beforeinstallprompt", bip());
  ok("desktop Chromium → no banner by default", !pg.banner());
  pg = load(MAC);
  pg.IH.init({ desktop: true });
  pg.fire("beforeinstallprompt", bip());
  ok("desktop Chromium + { desktop: true } → banner", labels(pg).includes("Install"));
  pg = load(MAC);
  pg.IH.init();
  ok("desktop Safari (no event) → nothing, show() refuses", !pg.banner() && pg.IH.show() === false);

  // --- storage blocked (private mode, blocked site data) -------------------------------------
  pg = load(IPHONE, { storageThrows: true });
  threw = null;
  try { pg.IH.init(); await pg.tap("Not now"); } catch (err) { threw = err; }
  ok("localStorage throws → banner still works, Not now still closes it", !threw && !pg.banner(), String(threw));

  console.log(`\n${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})();
