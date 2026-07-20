// App boot + the PWA integration example. index.html owns structure, styles.css
// owns looks; app.js wires the runtime and hands you two hooks to fill in:
//   render()  — (re)fetch + repaint. Runs on load, resume, poll, and PTR.
//   paint()   — turn data into DOM. Kept separate so a theme change can repaint
//               WITHOUT a network round-trip.
//
// What it wires for you: service worker + "tap to update" tag, theme (with the
// JS-baked-color contract), stale-while-revalidate data, and the keep-fresh loop
// (foreground poll + resume re-pull + optional pull-to-refresh).

const VER_PREFIX = "app-v";        // must match the V prefix in sw.js
const DATA_URL = "";               // <-- your cross-origin data endpoint (empty = disabled, like ping.js)
const DATA_KEY = "main";           // localStorage cache slot for this endpoint
const STALE_MS = 5 * 60 * 1000;    // cached data older than this is worth re-fetching

let lastData = null;               // last payload, so a theme change can repaint without refetching

// ---- data + rendering ------------------------------------------------------
// CACHE-FIRST: peek → paint → revalidate → repaint only if changed. A returning
// visitor sees real data instantly instead of the placeholder, even on a flaky
// connection; the network round-trip happens behind the already-painted UI. Only
// the true first run (nothing cached) falls back to awaiting the network.
async function render(){
  const app = document.getElementById("app");
  if(!DATA_URL) return;            // no endpoint wired yet — leave the placeholder copy in index.html

  // Only the boot call needs the cache paint; on a poll/resume/PTR re-render the
  // screen already shows this data, so painting it again would just flash.
  const cached = lastData === null ? Data.peek(DATA_KEY) : null;
  if(cached){                      // instant paint from the cache, no await
    lastData = cached.data;
    paint(cached.data);
    showStale(cached);
  }

  try{
    const res = await Data.revalidate(DATA_URL, { key: DATA_KEY, timeoutMs: 5000 });
    if(res.changed || lastData === null){   // skip the repaint (and its flash) when nothing moved
      const first = lastData === null;
      lastData = res.data;
      if(first) paint(res.data);            // nothing on screen yet — no transition to make
      else applyUpdate(res.data);           // replacing live content — do it gently
    }
    showStale(res);                // always: clears the "cached · N min old" tag
  }catch{
    // Offline, timed out, or the endpoint returned an empty/invalid payload —
    // data.js refused to cache it, so whatever is on screen is still the best
    // copy we have. Only a run that never painted anything has nothing to show.
    const c = Data.peek(DATA_KEY);
    if(c) showStale(c);            // re-flag it stale: the network read didn't land
    else if(lastData === null) app.textContent = "Couldn't load data and nothing is cached yet — reconnect and reopen.";
  }
}

// Swap in freshly-revalidated data WITHOUT yanking the page out from under the
// reader. Cache-first means the user is already looking at content when the
// network lands, so a naive paint() resets scroll, drops focus, and pops layout.
// Three cheap defenses, in order of how much they matter:
//   1. don't repaint at all unless the payload changed  (res.changed, in render)
//   2. restore scroll — rebuilding a container resets it to 0
//   3. crossfade the swap via a View Transition where supported, so content
//      changes instead of blinking. Skipped under prefers-reduced-motion;
//      unsupported browsers just take the plain path.
// The focus restore below is a BONUS, not a guarantee: it only fires if paint()
// patches in place. A paint() that wipes and rebuilds its container destroys the
// focused node, so document.contains() fails and focus is simply lost — recovering
// it there means re-finding the element by id, which only your paint() can do.
// What's deliberately NOT here: deferring the update while the user is mid-
// interaction. That's real (see CLAUDE.md) but "mid-interaction" is app-specific
// — a form being typed into, a menu open, a drag in flight — so it belongs in
// your shouldDefer(), not in the skeleton.
function applyUpdate(data){
  const y = scrollY, active = document.activeElement;
  const swap = () => {
    paint(data);
    if(scrollY !== y) scrollTo(0, y);
    if(active && active !== document.activeElement && document.contains(active)) active.focus();
  };
  const still = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if(document.startViewTransition && !still) document.startViewTransition(swap);
  else swap();
}

function paint(data){
  // → your app goes here. Read `data`, paint the DOM. Runs on first load, on
  //   resume, after a pull-to-refresh, AND on every theme change — so keep it
  //   idempotent, and read any baked colors via Theme.getCssColor(token).
  document.getElementById("app").textContent = JSON.stringify(data);
}

function showStale(res){          // "loaded from cache, N min old" so the user knows they're offline
  const tag = document.getElementById("stale");
  if(!tag) return;
  if(res.stale){
    tag.hidden = false;
    tag.textContent = `cached · ${Math.round(res.ageMs / 60000)} min old`;
  }else{
    tag.hidden = true;
  }
}

// Re-fetch only if visible AND actually stale — so a backgrounded tab never
// fetches and a just-loaded one isn't hit again. ageMs() answers "how stale?"
// with no network call.
function maybeRefresh(){
  if(document.visibilityState !== "visible") return;
  if(!DATA_URL) return;
  if(Data.ageMs(DATA_KEY) < STALE_MS) return;
  render();
}

// ---- theme -----------------------------------------------------------------
function onThemeChange(){
  // theme.js already cleared the color cache before calling us. Repaint anything
  // that baked a color into JS (canvas/SVG); pure var(--…) elements updated free.
  updateThemeLabel();
  if(lastData) paint(lastData);
}

function wireThemeToggle(){
  const btn = document.getElementById("theme");
  if(!btn) return;
  btn.onclick = () => Theme.cycle();   // cycle fires onThemeChange, which updates the label
  updateThemeLabel();
}

function updateThemeLabel(){
  const btn = document.getElementById("theme");
  if(btn) btn.textContent = "Theme: " + Theme.get().replace(/^./, c => c.toUpperCase());
}

// ---- service-worker version tag (unchanged plumbing) -----------------------
async function checkVer(){
  const tag = document.getElementById("ver");
  if(!tag) return;
  let installed = "";
  try{ installed = (await caches.keys()).find(k => k.startsWith(VER_PREFIX)) || ""; }catch{}
  if(!installed){ tag.hidden = true; return; }

  let latest = "";
  try{   // ?_= + no-store dodges both the SW cache and the HTTP cache → the live sw.js on the server
    const src = await (await fetch("./sw.js?_=" + Date.now(), {cache:"no-store"})).text();
    latest = (src.match(new RegExp(VER_PREFIX + "\\d+")) || [""])[0];
  }catch{}   // offline: leave latest empty → neutral tag, never a false "behind"

  const behind = latest && latest !== installed;
  tag.hidden = false;
  tag.className = "ver" + (behind ? " behind" : "");
  tag.textContent = behind ? `${installed} → ${latest}` : installed;
  tag.title = behind ? "New version available — tap to update" : "Up to date";
  tag.onclick = behind ? forceUpdate : null;
}

async function forceUpdate(){   // the hammer: drop every cache, reload → SW reinstalls the latest shell
  try{ await Promise.all((await caches.keys()).map(k => caches.delete(k))); }catch{}
  location.reload();
}

// ---- boot ------------------------------------------------------------------
function boot(){
  if("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(()=>{});

  Theme.init();                       // re-apply pre-paint attr + watch the OS for auto-mode users
  Theme.subscribe(onThemeChange);
  wireThemeToggle();

  render();
  checkVer();

  if(window.PullToRefresh) new PullToRefresh({ onRefresh: render }).init();  // standalone-only, no-op elsewhere
  setInterval(maybeRefresh, STALE_MS);                                       // foreground poll

  // iOS home-screen apps RESUME rather than reload — re-pull (gated) + re-check
  // version on foreground.
  addEventListener("visibilitychange", () => { if(!document.hidden){ maybeRefresh(); checkVer(); } });
}

boot();
