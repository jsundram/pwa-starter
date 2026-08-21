# Mobile, touch, and dark mode

> Deep-dive reference for the [pre-share checklist](checklist.md) — part of
> [pwa-starter](https://github.com/jsundram/pwa-starter).

## Mobile — head + `styles.css`
- `viewport-fit=cover` **and** `env(safe-area-inset-*)` padding — one without the other clips content
  under the notch or wastes the inset.
- **Hover doesn't exist on touch.** Tooltips/popovers that only appear on `:hover` are invisible on a
  phone — give them a tap/click path. (Both haydn and boccherini shipped this fix late.) The subtle
  bug that costs a debugging session is the **double-fire**: on touch a single tap synthesizes *both*
  a `mouseover` and a `click`, so the naive "`mouseover` shows the tip, `click` runs the action" does
  both at once — the tip flashes and the link fires before you can read it. Fix by branching on
  whether the device has a real pointer: on a mouse, hover shows the tip and clicking the trigger
  runs the action; on touch, a tap only *toggles* the tip and the action moves to a dedicated control
  *inside* the bubble (so the first tap can't also fire it), with the bubble `pointer-events:none`
  except that control so it never blocks the triggers beneath. haydn's scatter `bindDotInteraction`
  is the worked example. The kernel, app-agnostic:

  ```js
  const TOUCH = "ontouchstart" in window || navigator.maxTouchPoints > 0;
  function bindTip(trigger, {showTip, hideTip, action}){
    if(TOUCH){
      trigger.addEventListener("click", e => {           // a tap only opens the tip...
        e.preventDefault(); e.stopPropagation();          // ...never the action, never the doc-dismiss
        isOpen(trigger) ? hideTip() : showTip(trigger);   // ...and the action is a ▶ button in the tip
      });
    }else{
      trigger.addEventListener("pointerenter", () => showTip(trigger));
      trigger.addEventListener("pointerleave", hideTip);
      trigger.addEventListener("click", action);          // real pointer: no double-fire, run it
    }
  }
  document.addEventListener("click", hideTipIfOpen);       // tap elsewhere dismisses
  ```

  Left as a snippet, not a shipped file: the ~12-line kernel above is the reusable part; the bubble's
  positioning, styling, and content are app-specific enough that a generic component would fight every
  adopter's design. Only lift it into a `touch-tooltip.js` helper if an app has *many* such triggers.
- Target *real* touch devices with `@media (hover:none) and (pointer:coarse) and (max-width:800px)`
  when you want phone-specific sizing — a bare `max-width` also catches a shrunk desktop window.
- Fluid sizing with `clamp(min, vw, max)` scales cleanly desktop→tablet without a pile of breakpoints.
- iOS home-screen apps **resume** rather than reload — re-pull data on `visibilitychange`. That's the
  floor, not the ceiling: an installed app has **no browser chrome, so no reload button** — add a
  **pull-to-refresh** gesture *and* a **foreground poll** (a `setInterval`) so a left-open app freshens
  itself. Gate all three on `document.visibilityState === 'visible'` **and** a staleness threshold so a
  backgrounded tab never fetches and a fresh one isn't re-hit. The skeleton ships all three:
  `pullToRefresh.js` (the gesture, standalone-only) plus the gated `maybeRefresh()` poll and resume
  re-pull in `app.js`. Background Sync isn't an option — iOS standalone doesn't support it.
- **Prefetch the neighbors of any next/prev sequence.** A gallery, carousel, or paginated deck feels
  janky when a swipe lands on an undecoded image — the fix is to warm the browser HTTP cache for the
  neighbors *before* the user gets there: prefetch next **and** prev (an `Image()` with
  `decoding="async"` is enough), plus the **first item of the *next* group** so crossing a boundary
  is smooth too, not just steps within a group. Cheap, pure-client, and the single biggest
  perceived-smoothness win for a swipeable UI. gallery-deck's `prefetchNeighbors()` is the worked
  example — it warms the next/prev image in the current gallery *and* the first image of the next two
  posts (the core down-swipe loop) plus the previous post.

### Dark mode — `styles.css`, `theme.js`
Two entry points, both cheap: `@media (prefers-color-scheme: dark)` (what users get) and a `.dark`
class (force it for screenshots / a toggle / visual-regression baselines). Drive everything off CSS
custom properties so a mode is a variable swap, not a second stylesheet. Watch source order — a later
`@media print` block can clobber your dark vars; reset deliberately. Check contrast in **both** modes.

**The gotcha for canvas / SVG / d3 apps:** the variable swap only re-styles what the browser paints
*from CSS*. Any color you read **into JS** at render time — `ctx.fillStyle`, a d3
`.attr('fill', getCssColor('--accent'))`, a baked color scale — is frozen at the value it held when it
ran, and a mode flip won't touch it. So set a contract: components that bake colors expose a
`rerender()`, and one `onThemeChange()` — fired by both the toggle **and** the `matchMedia` listener
(so auto-mode users following the OS also update) — invalidates any color cache *first*, then calls
each `rerender()`. Purely `var(--…)`-driven components update for free; only the JS-baked ones need
plumbing. quartet-log's calendar and dashboard are the worked example. Bonus: a persisted three-state
toggle (`auto`/`light`/`dark`, default `auto`) plus a pre-paint inline `<script>` that stamps
`data-theme` before first paint kills the dark-mode FOUC without waiting for the bundle. The
skeleton's `theme.js` implements the contract — `subscribe()`, `getCssColor()`, and an
`invalidateColorCache()` that `notify()` fires *before* subscribers; `app.js`'s `onThemeChange()` is
the consumer (repaint from cached data, no refetch). The pre-paint stamp lives in `index.html`.
