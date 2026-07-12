// App boot. Put your real logic in render(); the scaffolding below is the PWA plumbing you want
// on day one: register the service worker, and show the installed cache version with a
// "tap to update" affordance when the deployed version is ahead (the fix for "my phone is stuck
// on the old version" — iOS caches the SW aggressively).

const VER_PREFIX = "app-v";   // must match the V prefix in sw.js

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

function render(){
  // → your app goes here. Read data, paint the DOM, etc.
}

function boot(){
  if("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(()=>{});
  render();
  checkVer();
  // iOS home-screen apps RESUME rather than reload — re-pull data + re-check version on foreground.
  addEventListener("visibilitychange", () => { if(!document.hidden){ render(); checkVer(); } });
}

boot();
