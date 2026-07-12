// Usage crunch, in the browser. Reads the analytics sheet's pings tab (Publish-to-web CSV,
// CORS-clean) and turns it into a few honest numbers. No dependencies. Deliberately simple —
// grow it as questions come up. Everyone is keyed by the opaque uid; joining names back is
// app-specific and optional (see the note in index.html), so this file never sees a name.
//
// Expected CSV columns (from analytics.gs): received, opened, page, who
//   received = server clock when the row landed;  opened = the device clock at the actual open
//   (differs from received for an offline open that flushed late);  who = uid hash ("" = anonymous).
(function () {
  // Parse "M/D/YYYY H:M:S" into a UTC instant so day/hour bucketing never touches local time/DST.
  const T = s => {
    const m = /^(\d+)\/(\d+)\/(\d+)[ T](\d+):(\d+):(\d+)/.exec((s || "").trim());
    return m ? Date.UTC(+m[3], +m[1] - 1, +m[2], +m[4], +m[5], +m[6]) : null;
  };
  const day = ms => { const d = new Date(ms); return `${d.getUTCFullYear()}-${String(d.getUTCMonth()+1).padStart(2,"0")}-${String(d.getUTCDate()).padStart(2,"0")}`; };
  const hour = ms => new Date(ms).getUTCHours();

  // minimal RFC-4180 CSV: quoted fields, "" escapes, commas/newlines inside quotes.
  function parseCSV(text) {
    const rows = [[]]; let f = "", q = false;
    text = text.replace(/\r\n?/g, "\n");
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
      else if (c === '"') q = true;
      else if (c === ",") { rows[rows.length - 1].push(f); f = ""; }
      else if (c === "\n") { rows[rows.length - 1].push(f); f = ""; rows.push([]); }
      else f += c;
    }
    rows[rows.length - 1].push(f);
    if (rows.length && rows[rows.length - 1].length === 1 && rows[rows.length - 1][0] === "") rows.pop();
    if (!rows.length) return [];
    const head = rows[0].map(h => h.trim());
    return rows.slice(1).map(r => { const o = {}; head.forEach((h, i) => o[h] = r[i]); return o; });
  }

  function crunch(csvText) {
    const rows = [];
    for (const r of parseCSV(csvText)) {
      const opened = T(r.opened) || T(r.received);
      const page = (r.page || "").trim(), who = (r.who || "").trim();
      if (opened !== null && page && page !== "page") rows.push({ opened, page, who });
    }
    rows.sort((a, b) => a.opened - b.opened || (a.page < b.page ? -1 : 1) || (a.who < b.who ? -1 : 1));
    const raw = rows.length;

    // ping.js re-sends a queued ping if a flush is interrupted → dedup on (opened, page, who).
    const seen = new Set(), dd = [];
    for (const x of rows) { const k = `${x.opened}|${x.page}|${x.who}`; if (!seen.has(k)) { seen.add(k); dd.push(x); } }

    const users = new Map(), pages = new Map(), byDay = {}, byHour = new Array(24).fill(0);
    let anon = 0;
    for (const { opened, page, who } of dd) {
      byDay[day(opened)] = (byDay[day(opened)] || 0) + 1;
      byHour[hour(opened)]++;
      pages.set(page, (pages.get(page) || 0) + 1);
      if (!who) { anon++; continue; }
      users.set(who, (users.get(who) || 0) + 1);
    }
    const scmp = (a, b) => a < b ? -1 : a > b ? 1 : 0;
    return {
      raw, deduped: raw - dd.length, total: dd.length,
      users: users.size, anon,
      topUsers: [...users.entries()].map(([uid, n]) => ({ uid, n })).sort((a, b) => b.n - a.n || scmp(a.uid, b.uid)),
      pages: [...pages.entries()].map(([page, n]) => ({ page, n })).sort((a, b) => b.n - a.n || scmp(a.page, b.page)),
      byDay, byHour,
      firstDay: Object.keys(byDay).sort()[0] || null,
      lastDay: Object.keys(byDay).sort().slice(-1)[0] || null,
    };
  }

  const api = { crunch, parseCSV };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else window.UsageCrunch = api;
})();
