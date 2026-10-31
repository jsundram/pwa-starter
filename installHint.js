// Install hint: a small banner that tells a visitor how to add the app to their Home Screen.
// OPTIONAL — delete this file and its <script> + CSS if you don't want it.
//
// WHY: no browser advertises an installable page well, and iOS doesn't advertise it at all.
//   - iOS / iPadOS: a page cannot install itself or even ask the browser to offer it. The only
//     path is the Share menu → Add to Home Screen (Safari, and since iOS 16.4 Chrome/Edge/Firefox
//     too), so all a page can do is SAY so. In iOS 26 Share moved under the ••• button in
//     Safari's compact tab bar, hence the "(or •••)".
//   - Chromium (Android Chrome/Edge/Samsung, desktop Chrome/Edge): the browser fires
//     beforeinstallprompt when the manifest makes the page installable. Keep the event and you
//     can show your own Install button that opens the browser's dialog.
//   - Firefox Android, desktop Safari (File → Add to Dock): no event and nothing worth saying.
//     The hint stays hidden.
//
// THE iOS GOTCHA it exists to head off: a Home Screen app on iOS gets its OWN storage, separate
// from Safari's. Anything saved in the Safari tab (a name, settings, a draft) is missing from the
// installed copy, so someone who sets up in Safari and installs afterwards has two copies that
// disagree — and has to set up again, or worse, keeps using both. So the iOS hint says to install
// FIRST. If your app asks for something up front, call InstallHint.show() right before it asks.
// (Android's installed copy shares Chrome's storage, so the note is iOS-only.)
//
// Desktop is off by default: desktop Chrome/Edge already put an install icon in the address bar,
// and a laptop gains little from it. Pass { desktop: true } to offer the button there too.
//
// Not handled: in-app browsers (Instagram, Facebook, X), which can't install at all and need
// "open in Safari/Chrome" first. A link texted to a few people opens in the real browser.
//
// Loaded as a classic script before app.js; exposes a global `InstallHint`.
// Styling lives in styles.css (#install-hint).

window.InstallHint = (() => {
  const KEY = "app-install-hint";   // localStorage: set once the visitor taps "Not now" or installs
  const STR = {                     // EDIT wording here; NAME is the Home Screen label
    ios: "Install NAME: tap Share (or ••• then Share), then Add to Home Screen.",
    iosNote: "Do it before you save anything here: the Home Screen app keeps its own storage, separate from Safari's.",
    prompt: "Install NAME on this device?",
    install: "Install",
    later: "Not now",
  };
  const SHARE_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M8 7l4-4 4 4"/><path d="M6 11H5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1h-1"/></svg>';

  const installed = () => matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  // iPadOS 13+ reports itself as a Mac; a Mac with a touchscreen is an iPad.
  const ios = () => /iPhone|iPad|iPod/.test(navigator.userAgent)
    || (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  const touch = () => matchMedia("(pointer: coarse)").matches;

  let opts = { auto: true, desktop: false };
  let deferred = null;              // the kept beforeinstallprompt event (Chromium)
  let el = null;

  const dismissed = () => { try { return !!localStorage.getItem(KEY); } catch { return false; } };
  const remember = why => { try { localStorage.setItem(KEY, why); } catch {} };
  const name = () => (document.querySelector('meta[name="apple-mobile-web-app-title"]') || {}).content
    || document.title;

  function render(kind) {
    hide();
    el = document.createElement("aside");
    el.id = "install-hint";
    el.setAttribute("aria-label", "Install this app");
    const p = document.createElement("p");
    if (kind === "ios") {
      p.innerHTML = STR.ios.replace("NAME", "<b></b>").replace("Share", "Share " + SHARE_ICON);
      p.querySelector("b").textContent = name();   // textContent: the title is not markup
      const note = document.createElement("small");
      note.textContent = STR.iosNote;
      p.append(document.createElement("br"), note);
    } else {
      p.textContent = STR.prompt.replace("NAME", name());
    }
    const row = document.createElement("div");
    if (kind === "prompt") row.append(button(STR.install, install, "primary"));
    row.append(button(STR.later, () => { remember("later"); hide(); }));
    el.append(p, row);
    document.body.appendChild(el);
  }

  function button(label, onclick, cls) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    if (cls) b.className = cls;
    b.onclick = onclick;
    return b;
  }

  async function install() {
    const e = deferred;
    deferred = null;                // prompt() works once per event
    hide();
    if (!e) return;
    e.prompt();
    try { if ((await e.userChoice).outcome === "accepted") remember("installed"); } catch {}
  }

  function hide() { if (el) { el.remove(); el = null; } }

  // Show the hint now, whatever "Not now" said earlier — the app chose this moment. Returns
  // whether there was anything to show: false once installed, or where this browser can't install.
  function show() {
    if (installed()) return false;
    if (ios()) { render("ios"); return true; }
    if (deferred && (touch() || opts.desktop)) { render("prompt"); return true; }
    return false;
  }

  function init(o = {}) {
    opts = { ...opts, ...o };
    if (installed()) return;
    // Chromium fires this when the page becomes installable — possibly well after load.
    // preventDefault keeps Android's own mini-infobar from competing with the banner.
    addEventListener("beforeinstallprompt", e => {
      e.preventDefault();
      deferred = e;
      if (opts.auto && !dismissed()) show();
    });
    addEventListener("appinstalled", () => { remember("installed"); deferred = null; hide(); });
    if (opts.auto && !dismissed() && ios()) show();
  }

  return { init, show, hide, get installed() { return installed(); } };
})();
