# Bullion Mk Ultra — Editorial Identity Pass Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give `bullion_mkultra.html` a deliberate visual identity — Times-New-Roman
headers/titles, a re-spaced 12-color legend palette, a "Bullion" wordmark + monogram, two
authored field-note annotations, a custom drag-to-spin cursor, and a real fallback card instead
of a silent black void when WebGL/the Three.js CDN is unavailable.

**Architecture:** This is a single-file app — every change lands in
`bullion-live-map/bullion_mkultra.html` (CSS in the `<style>` block, markup in `<body>`, logic
in the inline `<script>` blocks). No new files, no build step, no new external dependencies.

**Tech Stack:** Vanilla JS + D3 (bundled) + Three.js r160 via a pinned jsDelivr importmap
(unchanged). No test framework exists for this file's JS/CSS; verification is headless-Chrome
DOM probes plus Chrome-MCP visual screenshots, per this project's established idiom.

## Global Constraints

- **Target file: `bullion-live-map/bullion_mkultra.html` ONLY.** Never touch `bullion_mk11.html`
  through `bullion_mk18.html` — they are frozen. Verify with `shasum -a 256 bullion_mk15.html
  bullion_mk16.html bullion_mk17.html bullion_mk18.html` before Task 1 and after Task 6; the
  four hashes must be identical both times.
- **No new external dependencies.** Times New Roman is a system font (no `@font-face`, no
  webfont hosting, no CSP change). The WebGL fallback adds no new host.
- **`gh` CLI is not installed.** Use `git push origin main` directly (works from this Bash
  tool); use raw `curl` + the credential-store token only if a GitHub API call is ever needed
  (it isn't, for this plan).
- **Never call `openAuditLog()` in a headless probe** — its animated modal stalls headless
  virtual-time and hangs the run.
- **macOS has no `timeout` command** — headless runs rely on `--virtual-time-budget` instead.
- **Field-note copy in Task 5 is explicitly a draft placeholder the user may edit** — implement
  it as real, shippable copy (not a `TBD` string), but do not treat the exact wording as
  precious; the user already knows it's a starting draft.
- **Palette hex values in Task 2 are a first-pass draft** (hand-reasoned for hue/lightness
  separation, not rendered/verified in a real browser before being written into this plan).
  Task 2's own verification step is a mandatory visual check with explicit permission to adjust
  values that don't read as distinguishable once actually rendered — do not skip that step.

## Verification Harness (used by every task below)

**Headless-Chrome DOM probe**, reused per-task with a different probe script:

```bash
rm -rf /tmp/mkultra-probe && mkdir -p /tmp/mkultra-probe
cp bullion-live-map/bullion_mkultra.html bullion-live-map/data.json /tmp/mkultra-probe/
python3 - "/tmp/mkultra-probe/bullion_mkultra.html" <<'PYEOF'
import sys
path = sys.argv[1]
html = open(path, encoding='utf-8').read()
idx = html.rfind('</body>')  # rfind: there's a decoy </body> inside a JS string earlier in the file
probe = '''<script>
__PROBE_SCRIPT__
</script>
'''
open(path, 'w', encoding='utf-8').write(html[:idx] + probe + html[idx:])
PYEOF
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --allow-file-access-from-files --virtual-time-budget=15000 \
  --enable-logging=stderr --v=1 \
  --use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader \
  "file:///tmp/mkultra-probe/bullion_mkultra.html" 2>/tmp/mkultra-probe/chrome.log
grep "PROBE_" /tmp/mkultra-probe/chrome.log
```

Each task below gives the exact text to substitute for `__PROBE_SCRIPT__` (always ending in
`console.log('PROBE_RESULT:' + JSON.stringify(result))` so `grep PROBE_` shows the outcome).
The `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader` flags give the headless
instance real WebGL; Task 6 explicitly runs a second time **without** those flags to exercise
the no-WebGL fallback path using genuinely-absent WebGL rather than a mock.

**Chrome-MCP visual check**, reused per-task: navigate a tab to
`https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`
(the live Pages URL) is only valid *after* a push — during development, navigate instead to
`file://~/claude-projects/claudekit/bullion-live-map/bullion_mkultra.html`,
screenshot, and check `read_console_messages` for 0 errors.

---

### Task 1: Typography — Times New Roman for every header/title

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:27-43` (add `--font-display` custom property
  and a new global heading rule), `bullion-live-map/bullion_mkultra.html:89` (confirm no
  conflicting `font-family`, no edit needed there — see Step 3 note)

**Interfaces:**
- Produces: CSS custom property `--font-display` on `:root`, consumed by Task 3 (header
  wordmark) and applied globally to `h1, h2, h3, .legend-causal-title, #detail-title,
  #coach-title`.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
const cs = getComputedStyle(document.documentElement);
const result = {
  fontDisplayVar: cs.getPropertyValue('--font-display').trim(),
  h1Font: getComputedStyle(document.querySelector('h1')).fontFamily,
};
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe, verify it fails**

Run the harness (see Verification Harness above). Expected: `PROBE_RESULT:{"fontDisplayVar":"","h1Font":"-apple-system, ..."}` — i.e. `fontDisplayVar` is empty and `h1Font` does NOT contain `Times New Roman`.

- [ ] **Step 3: Implement**

In `bullion-live-map/bullion_mkultra.html`, find the `:root { ... }` block (currently lines
27-42, ending `--warn: #e0b15a;` then `}`). Add one new line inside it, and one new rule
immediately after its closing brace, before the existing `* { box-sizing: border-box; }` line:

```css
  :root {
    --bg-deep:    #05060a;
    --bg-panel:   #0b0e16;
    --bg-panel2:  #111522;
    --border:     #1e2436;
    --text:       #d8dce6;
    --text-dim:   #8891a6;
    --gold:       #d4b869;
    --gold-dim:   #a8925a;
    --green:      #7bbf8e;
    --red:        #e0654f;
    --amber:      #e0b15a;
    --up:         #e0654f;
    --down:       #7bbf8e;
    --warn:       #e0b15a;
    --font-display: "Times New Roman", Times, serif;
  }
  h1, h2, h3, .legend-causal-title, #detail-title, #coach-title {
    font-family: var(--font-display);
  }
  * { box-sizing: border-box; }
```

(The two new lines are `--font-display: ...` inside `:root`, and the whole `h1, h2, h3, ...`
rule right after. `* { box-sizing: border-box; }` is the existing next line — leave it as-is,
just insert before it.)

No edit is needed at `#header h1` (line 89) or the responsive rule (line ~305): neither
declares its own `font-family`, so both inherit `var(--font-display)` from the new rule via
normal CSS cascade (equal specificity, later rule wins) without conflicting with their existing
`font-size`/`color`/`letter-spacing`/`font-weight` declarations.

- [ ] **Step 4: Run the probe again, verify it passes**

Expected: `PROBE_RESULT:{"fontDisplayVar":"\"Times New Roman\", Times, serif","h1Font":"\"Times New Roman\", Times, serif"}` (exact quoting/whitespace may vary slightly by Chrome version — the key check is `h1Font` now contains `Times New Roman`).

- [ ] **Step 5: Chrome-MCP visual check**

Screenshot the header, an open node-detail panel (click any glowing node), the legend
(bottom-left), and the Audit Log modal — confirm all headings render in a serif face, no text
overflow/clipping/wrapping regression at both a desktop width (~1400px) and a narrow width
(~380px, matching the existing `@media` breakpoint around line 305). Confirm 0 console errors
via `read_console_messages`.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: Times New Roman for all headers and titles"
```

---

### Task 2: Color palette — re-space the crowded GROUP_COLOR swatches

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:697-710` (the `GROUP_COLOR` object literal)

**Interfaces:**
- Consumes: nothing new.
- Produces: updated hex values. No other code changes needed — `buildLegend()` (~2743),
  node/globe mesh coloring (~2092, ~2269), and board-card border color (~2585) already read
  `GROUP_COLOR[group]` dynamically.

**Problem being fixed:** `monetary #b79be0`, `commercial #8f9ee0`, `shadow #b586c8` crowd the
same purple hue family; `sovereign #7fb4e0` and `fx #8fb0c8` crowd the same blue family;
`sentiment #e0c264` sits only ~4° of hue from the `--gold` accent `#d4b869`, diluting it. 6 of
the 12 groups need to move; the other 6 (`regulator`, `capmkt`, `sectors`, `indicator`,
`commodity`, `geo`) were not flagged as crowded and are left **byte-identical** to avoid
introducing new collisions while fixing old ones.

- [ ] **Step 1: Write the failing probe**

```js
const result = {};
['regulator','sovereign','monetary','commercial','shadow','capmkt','sectors','indicator','sentiment','fx','commodity','geo']
  .forEach(g => { result[g] = GROUP_COLOR[g]; });
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe, verify it fails (shows the OLD values)**

Expected (current state):
```
{"regulator":"#9aa4b2","sovereign":"#7fb4e0","monetary":"#b79be0","commercial":"#8f9ee0","shadow":"#b586c8","capmkt":"#6fc7a6","sectors":"#e0926a","indicator":"#9cc26a","sentiment":"#e0c264","fx":"#8fb0c8","commodity":"#d4a843","geo":"#c97b8a"}
```

- [ ] **Step 3: Implement**

Replace the `GROUP_COLOR` object at `bullion-live-map/bullion_mkultra.html:697-710`:

```js
const GROUP_COLOR = {
  regulator:  '#9aa4b2',
  sovereign:  '#6fa2d1',
  monetary:   '#ab93d4',
  commercial: '#9c6f52',
  shadow:     '#6b9a92',
  capmkt:     '#6fc7a6',
  sectors:    '#e0926a',
  indicator:  '#9cc26a',
  sentiment:  '#b578ad',
  fx:         '#8dbfb6',
  commodity:  '#d4a843',
  geo:        '#c97b8a',
};
```

Six values changed (`sovereign`, `monetary`, `commercial`, `shadow`, `sentiment`, `fx`); six are
untouched (`regulator`, `capmkt`, `sectors`, `indicator`, `commodity`, `geo`).

- [ ] **Step 4: Run the probe again, verify it passes**

Expected: the six changed keys now show their new hex values above; the six unchanged keys show
their original values (confirming nothing else moved).

- [ ] **Step 5: Chrome-MCP visual check (mandatory, not optional polish)**

Screenshot the legend (bottom-left "Layers (tap to filter)" section) large enough to see all 12
dots clearly (use `zoom` on that region if the screenshot is too small to judge by eye). Confirm
every dot is distinguishable from its neighbors in the list. Pay closest attention to two zones
flagged as risk during design: **`shadow` vs `fx`** (both teal-family; differentiated by `shadow`
being darker/duller and `fx` lighter/sandier — confirm this reads clearly, not just in theory) and
**`commercial` vs `sectors`** (both warm/brown-orange family; differentiated by `commercial`
being darker/muted and `sectors` brighter/more saturated). If either pair still reads as
ambiguous at actual legend-dot size, adjust the offending hex value(s) by eye (shift lightness
or saturation further apart) and re-screenshot — do not ship a palette where two swatches are
hard to tell apart. Also click into the 3D globe and confirm node colors updated (nodes use the
same `GROUP_COLOR` map). Confirm 0 console errors.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: re-space the GROUP_COLOR palette to fix crowded purples/blues and the gold collision"
```

---

### Task 3: Header — "Bullion" wordmark + monogram

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:509-514` (header markup), `:73-90` (header CSS)

**Interfaces:**
- Consumes: `var(--font-display)` from Task 1.
- Produces: `#brand-mark` (SVG monogram), `#brand-text`, `#brand-eyebrow` (new elements later
  tasks don't depend on, but must not collide with any existing id).

- [ ] **Step 1: Write the failing probe**

```js
const h1 = document.querySelector('#header h1');
const result = {
  brandMarkExists: !!document.getElementById('brand-mark'),
  h1Text: h1 ? h1.textContent.trim() : null,
  eyebrowExists: !!document.getElementById('brand-eyebrow'),
};
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe, verify it fails**

Expected: `{"brandMarkExists":false,"h1Text":"US Financial System — Mk Ultra Constellation","eyebrowExists":false}`

- [ ] **Step 3: Implement**

Replace the header's title block at `bullion-live-map/bullion_mkultra.html:509-514`:

```html
  <div id="header">
    <div id="brand">
      <svg id="brand-mark" width="22" height="22" viewBox="0 0 32 32" fill="none" aria-hidden="true" focusable="false">
        <circle cx="16" cy="16" r="13" stroke="var(--gold)" stroke-width="1.4" stroke-dasharray="46 35" stroke-linecap="round" transform="rotate(-40 16 16)"/>
        <circle cx="16" cy="16" r="8.5" stroke="var(--gold)" stroke-width="1.4" stroke-dasharray="28 25" stroke-linecap="round" transform="rotate(120 16 16)"/>
        <circle cx="16" cy="16" r="2" fill="var(--gold)"/>
      </svg>
      <div id="brand-text">
        <h1>Bullion</h1>
        <div id="brand-eyebrow">US Financial System &mdash; Mk Ultra Constellation</div>
        <div class="subtitle" id="node-count-label">See how one Fed move ripples through banks, the dollar, gold and inflation.</div>
        <div class="subtitle adv-control" id="live-badge" style="margin-top:2px"></div>
      </div>
    </div>
```

(This replaces the old `<div><h1>...</h1><div class="subtitle" ...>` wrapper — the
`node-count-label` and `live-badge` divs keep their exact ids/classes/inline styles unchanged,
just re-nested one level deeper under `#brand-text`. The `#header-controls` div and everything
inside it, immediately following in the original file, is untouched.)

Add CSS. Modify the existing `#header h1` rule at line 89 and add three new rules right after
it (still inside the `<style>` block, same neighborhood):

```css
  #brand { display: flex; align-items: center; gap: 10px; min-width: 0; }
  #header h1 { font-size: 20px; margin: 0; color: var(--gold); letter-spacing: 0.01em; font-weight: 700; line-height: 1.05; }
  #brand-eyebrow { font-size: 10px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.07em; margin-top: 2px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
  #brand-mark { flex: 0 0 auto; }
```

(`#brand-eyebrow` explicitly re-declares the sans-serif stack rather than inheriting
`--font-display` — it's a small-caps-style descriptor line, not a title, and pairing a serif
headline with a sans eyebrow is the deliberate editorial contrast, not an oversight.)

Also update the narrow-viewport rule (currently `bullion-live-map/bullion_mkultra.html:305-306`,
`#header h1 { font-size: 13px; } #header .subtitle { display: none; }`) by adding one line so
the eyebrow hides at the same breakpoint as the subtitle:

```css
    #header h1 { font-size: 17px; }
    #header .subtitle { display: none; }
    #brand-eyebrow { display: none; }
```

- [ ] **Step 4: Run the probe again, verify it passes**

Expected: `{"brandMarkExists":true,"h1Text":"Bullion","eyebrowExists":true}`

- [ ] **Step 5: Chrome-MCP visual check**

Screenshot the header at desktop width and at the narrow breakpoint (~380px). Confirm: the
monogram renders as two offset gold arcs + a center dot (not a broken/invisible SVG), "Bullion"
reads clearly in the serif face from Task 1, the eyebrow line sits directly under it in a
smaller sans caps style, and at narrow width the eyebrow disappears cleanly (no leftover gap or
overlap) same as the existing subtitle behavior. Confirm the header-controls button row on the
right is unaffected. Confirm 0 console errors.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: promote the Bullion wordmark + monogram into the in-app header"
```

---

### Task 4: Signature interaction — compass-rose drag cursor

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:102-103` (`#network-svg` cursor rules),
  `bullion-live-map/bullion_mkultra.html:2056` (canvas inline `cssText`, remove `cursor:grab`
  so the new stylesheet rule isn't overridden by higher-specificity inline style)

**Interfaces:** none (pure CSS + one inline-style edit).

- [ ] **Step 1: Write the failing probe**

This one must run *after* the 3D canvas has mounted (it's created dynamically in `Renderer.build()`), so wait for it:

```js
function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
(async () => {
  await wait(3000);
  const canvas = document.getElementById('mkultra-canvas');
  const result = {
    canvasExists: !!canvas,
    canvasInlineCursor: canvas ? canvas.style.cursor : null,
    canvasComputedCursor: canvas ? getComputedStyle(canvas).cursor : null,
  };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
})();
```

- [ ] **Step 2: Run the probe, verify it fails**

Expected: `{"canvasExists":true,"canvasInlineCursor":"grab","canvasComputedCursor":"grab"}` — the
cursor is currently plain `grab`, set inline.

- [ ] **Step 3: Implement**

In `bullion-live-map/bullion_mkultra.html`, replace the two existing cursor rules at lines
102-103:

```css
  #network-svg { width: 100%; height: 100%; display: block; }
  #mkultra-canvas {
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9' fill='none' stroke='%23d4b869' stroke-width='1.5'/%3E%3Cpath d='M12 4 L14.2 11 L12 20 L9.8 11 Z' fill='%23d4b869' stroke='%230b0e16' stroke-width='0.6'/%3E%3Ccircle cx='12' cy='12' r='1.6' fill='%230b0e16'/%3E%3C/svg%3E") 12 12, grab;
  }
  #mkultra-canvas:active {
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9' fill='%23d4b869' fill-opacity='0.25' stroke='%23d4b869' stroke-width='1.5'/%3E%3Cpath d='M12 4 L14.2 11 L12 20 L9.8 11 Z' fill='%23d4b869' stroke='%230b0e16' stroke-width='0.6'/%3E%3Ccircle cx='12' cy='12' r='1.6' fill='%230b0e16'/%3E%3C/svg%3E") 12 12, grabbing;
  }
```

(The `:active` variant fills the compass ring with translucent gold, signalling "engaged"
without changing the icon shape. `#network-svg`'s own `cursor:grab`/`:active` declarations are
removed since Mk Ultra's interactive surface is the canvas, not the SVG — the SVG only holds
defs/filters here per the earlier `svgEl.style.display='none'` behavior in `Renderer.build()`.)

Then at `bullion-live-map/bullion_mkultra.html:2056`, remove `cursor:grab;` from the inline
`cssText` (inline styles beat any stylesheet rule regardless of selector specificity, so leaving
it in would make Step 3's new `#mkultra-canvas` rule silently do nothing):

```js
    canvas.style.cssText = 'width:100%;height:100%;display:block;touch-action:none;';
```

(was: `'width:100%;height:100%;display:block;cursor:grab;touch-action:none;'`)

- [ ] **Step 4: Run the probe again, verify it passes**

Expected: `canvasInlineCursor` is now `""` (empty — no inline cursor set), and
`canvasComputedCursor` starts with `url("data:image/svg+xml` (the exact string is long; check
`canvasComputedCursor.includes('data:image/svg+xml')` is true rather than an exact match).

- [ ] **Step 5: Chrome-MCP visual check**

Hover the mouse over the 3D globe and use `zoom` on the cursor area to confirm the compass-rose
glyph renders (not a broken-image icon — if it renders as a plain arrow, the data-URI SVG has a
syntax error and needs fixing). Click-and-hold to confirm the `:active` state shows the filled
variant. Confirm dragging the globe still rotates it (behavior unchanged, only the cursor
appearance changed). Confirm 0 console errors.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: custom compass-rose cursor signals the globe is drag-to-spin"
```

---

### Task 5: Field-note annotations on two corrected links

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:1215` (`credit→equit` link object),
  `bullion-live-map/bullion_mkultra.html:1235` (`usd→oil` link object),
  `bullion-live-map/bullion_mkultra.html:2454-2485` (`buildRelationships`'s `rowHtml`),
  `bullion-live-map/bullion_mkultra.html` CSS block (new `.rel-field-note` rule near line 222)

**Interfaces:**
- Consumes: link objects' existing `stat`/`note`/`why` string fields (pattern to follow).
- Produces: new optional `fieldNote` string field on `LINKS` entries; `rowHtml` renders it when
  present. No other code needs to know about this field — `parse_links()` in `calibrate.py`
  reads the LINKS array file-independently and does not need updating (it doesn't consume
  `fieldNote`).

- [ ] **Step 1: Write the failing probe**

```js
const credit = LINKS.find(l => l.s === 'credit' && l.t === 'equit');
const usdOil = LINKS.find(l => l.s === 'usd' && l.t === 'oil');
const result = {
  creditHasFieldNote: !!(credit && credit.fieldNote),
  usdOilHasFieldNote: !!(usdOil && usdOil.fieldNote),
};
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe, verify it fails**

Expected: `{"creditHasFieldNote":false,"usdOilHasFieldNote":false}`

- [ ] **Step 3: Implement — add `fieldNote` to the two link objects**

At `bullion-live-map/bullion_mkultra.html:1215`, add a `fieldNote` property to the existing
object (keep every existing field unchanged, just add one more key):

```js
  {s:'credit', t:'equit', w:1, sign:-1, conf:'measured', why:'Tight credit spreads signal confidence and easy corporate funding, which supports stocks.', stat:'HY spreads and the S&P move inversely, roughly -0.7. Tighter spreads lift equities (FRED). Fitted over 199 usable daily changes in the train split: slope=-0.08569, |t|=12.5. The sign shown is the fitted one; the earlier hand sign was +1.', fieldNote:'I originally had wider credit spreads lifting stocks — which, looking back, never made sense. Once I actually measured it, spreads widening tracks equities falling, the way you’d expect.'},
```

At `bullion-live-map/bullion_mkultra.html:1235`:

```js
  {s:'usd', t:'oil', w:1, sign:1, conf:'measured', note:'The sign here is the fitted one and disagrees with the pricing mechanism in `why`. Over this window the dollar and crude rose together.', why:'Crude is priced in dollars, so a stronger dollar makes it pricier for foreign buyers - which argues for an inverse link.', stat:'Long-run studies find a weak inverse link, roughly -0.3 (EIA). Fitted over 198 usable daily changes in the train split: slope=+0.02732, |t|=4.7. The sign shown is the fitted one; the earlier hand sign was -1. The textbook dollar-pricing channel is negative, so this window reads as a demand-led regime rather than a refutation.', fieldNote:'I had this coded as dollar up → oil down — the textbook FX-pricing story everyone learns. The data disagreed. Over this window it’s actually positive. I’m leaving that in and telling you it’s weird rather than hiding it.'},
```

**Step 3b: Render it.** In `buildRelationships`'s `rowHtml` (currently
`bullion-live-map/bullion_mkultra.html:2454-2485`), the `.rel-stat` line is:

```js
          '<span class="rel-stat">&#9873; ' + enrichText(r.l.stat || '') + '</span></div>' +
```

Change it to append a conditional field-note span right after:

```js
          '<span class="rel-stat">&#9873; ' + enrichText(r.l.stat || '') + '</span>' +
          (r.l.fieldNote ? '<div class="rel-field-note">' + enrichText(r.l.fieldNote) + '</div>' : '') +
          '</div>' +
```

**Step 3c: Style it.** Add a new CSS rule near the existing `.rel-detail .rel-stat` rule
(`bullion-live-map/bullion_mkultra.html:222`):

```css
  .rel-field-note { display: block; margin-top: 6px; padding-top: 6px; border-top: 1px dashed rgba(212,184,105,0.4); font-family: var(--font-display); font-style: italic; color: var(--text); font-size: 12px; line-height: 1.45; }
  .rel-field-note::before { content: "— "; color: var(--gold-dim); }
```

(An em-dash prefix in gold-dim reads like a signed margin note, visually distinct from the
`.rel-stat`'s flag-icon-prefixed sourced citation directly above it.)

- [ ] **Step 4: Run the probe again, verify it passes**

Expected: `{"creditHasFieldNote":true,"usdOilHasFieldNote":true}`

- [ ] **Step 5: Chrome-MCP visual check**

Open the detail panel for the node `credit` (or `equit` — either side of the link shows it) and
for `usd` (or `oil`), and for each expand/scroll to the relevant relationship row. Confirm the
field note renders in italic serif below the sourced stat line, separated by the dashed rule,
and reads as clearly distinct from the `stat:`/`why:` text above it. Confirm a node **without**
a field note (e.g. any other relationship row) shows no extra empty space (the conditional
render must not leave a stray empty `<div>`). Confirm 0 console errors.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: add first-person field notes on the two links the honesty pass corrected"
```

---

### Task 6: WebGL / CDN fallback — replace the silent black void

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:2032-2036` (`Renderer.build`'s top),
  `bullion-live-map/bullion_mkultra.html:2047` (wrap `WebGLRenderer` construction in try/catch),
  and add two new private helper functions inside the `Renderer` IIFE plus one new CSS rule.

**Interfaces:**
- Consumes: `stageEl` (module-level const, already in scope inside the `Renderer` IIFE),
  `showView` (top-level function declaration at `bullion-live-map/bullion_mkultra.html:2595`,
  reachable from inside the IIFE via function-declaration hoisting in this classic-script file).
- Produces: `#render-fallback` DOM element (id, for probes/CSS only — no other task reads it).

- [ ] **Step 1: Write the failing probe (the "no WebGL" path)**

```js
function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
(async () => {
  await wait(4000);
  const result = {
    fallbackShown: !!document.getElementById('render-fallback'),
    canvasExists: !!document.getElementById('mkultra-canvas'),
  };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
})();
```

- [ ] **Step 2: Run the probe TWICE to verify the failing baseline**

Run A — **omit** the `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader` flags
from the harness command (genuine no-WebGL headless environment). Expected (current, broken,
behavior): `{"fallbackShown":false,"canvasExists":false}` — i.e. neither the old canvas nor any
explanatory card appears; the void is silent, confirming the bug.

Run B — **with** the swiftshader flags (as in the harness default). Expected:
`{"fallbackShown":false,"canvasExists":true}` — the normal 3D path still works; this run is the
regression guard, re-run again after Step 3 to confirm it's unaffected.

- [ ] **Step 3: Implement**

Add two private helpers inside the `Renderer` IIFE. Place them near the top of the IIFE, right
after the existing `let scene, camera, webglRenderer, ...` variable declarations (around
`bullion-live-map/bullion_mkultra.html:1514`):

```js
  function hasWebGLSupport() {
    try {
      const c = document.createElement('canvas');
      return !!(c.getContext('webgl2') || c.getContext('webgl') || c.getContext('experimental-webgl'));
    } catch (e) { return false; }
  }

  function showRenderFallback() {
    if (document.getElementById('render-fallback')) return; // don't duplicate on re-entry
    const card = document.createElement('div');
    card.id = 'render-fallback';
    card.innerHTML =
      '<h2>Here’s the same map, flattened</h2>' +
      '<p>This view needs 3D graphics your browser isn’t giving us right now. The Overview board shows every node and link the same way, without WebGL.</p>' +
      '<button class="btn run-btn" id="render-fallback-btn">Open the Overview board</button>';
    stageEl.appendChild(card);
    document.getElementById('render-fallback-btn').addEventListener('click', () => showView('board'));
  }
```

Then change the top of `build()` (currently `bullion-live-map/bullion_mkultra.html:2032-2036`):

```js
  async function build(nodesArr) {
    await threeLoad;
    if (!THREE) return; // Three.js failed to load (CDN blocked/offline) — fail soft, no crash.
    disposeScene();
    if (svgEl) svgEl.style.display = 'none'; // Mk Ultra's render layer is the canvas mounted below, not the SVG
```

to:

```js
  async function build(nodesArr) {
    if (!hasWebGLSupport()) { showRenderFallback(); return; }
    const loaded = await Promise.race([
      threeLoad.then(() => true),
      new Promise(resolve => setTimeout(() => resolve(false), 8000)),
    ]);
    if (!loaded || !THREE) { showRenderFallback(); return; } // CDN blocked, offline, or timed out
    disposeScene();
    if (svgEl) svgEl.style.display = 'none'; // Mk Ultra's render layer is the canvas mounted below, not the SVG
```

And wrap the renderer construction (currently `bullion-live-map/bullion_mkultra.html:2047`):

```js
    webglRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
```

to:

```js
    try {
      webglRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    } catch (err) {
      console.error('Mk Ultra: WebGL context creation failed', err);
      showRenderFallback();
      return;
    }
```

Add CSS right after the existing `#stage { ... }` rule
(`bullion-live-map/bullion_mkultra.html:101`):

```css
  #render-fallback {
    position: absolute; inset: 0; z-index: 5;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 12px; padding: 32px; text-align: center;
    background: var(--bg-deep);
  }
  #render-fallback h2 { font-size: 18px; margin: 0; }
  #render-fallback p { font-size: 13px; color: var(--text-dim); max-width: 360px; margin: 0; line-height: 1.5; }
```

(`h2` picks up `var(--font-display)` automatically from Task 1's global rule — no font-family
declared here.)

- [ ] **Step 4: Run the probe again, verify both runs now pass**

Run A (no swiftshader flags): expected `{"fallbackShown":true,"canvasExists":false}` — the card
now appears instead of a silent void.

Run B (with swiftshader flags): expected `{"fallbackShown":false,"canvasExists":true}` — the
normal path is unaffected, confirming this is a real regression guard, not a coincidence.

- [ ] **Step 5: Chrome-MCP visual check**

In a normal (WebGL-capable) browser tab, confirm the 3D map still loads exactly as before (no
visible change — the fallback should never appear here). Then, to see the fallback rendered for
real: temporarily edit a **throwaway copy** of the file (not the committed one) to point the
importmap's `three` URL at an invalid host (e.g. `https://127.0.0.1:1/three.module.js`), open
that copy in Chrome MCP, and confirm the card appears with readable copy, a working "Open the
Overview board" button that switches to the 2D board, and 0 console errors (the `console.error`
call is expected/intentional and does not count as a failure — confirm no *uncaught* errors).
Delete the throwaway copy afterward.

- [ ] **Step 6: Freeze check**

```bash
cd ~/claude-projects/claudekit/bullion-live-map
shasum -a 256 bullion_mk15.html bullion_mk16.html bullion_mk17.html bullion_mk18.html
```

Compare against the hashes recorded before Task 1 — all four must match exactly.

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: replace the silent black void with a real WebGL/CDN fallback card"
```

---

## After Task 6

- Run the project's existing Python suite as a sanity check (should be unaffected by this
  pass): `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest
  test_calibrate`.
- `git push origin main` (confirm with the user first, per this project's standing practice of
  pushing directly once local verification passes).
- Confirm the live Pages URL serves the update within ~30-90s:
  `https://sinbadtheexplorer.github.io/claudekit/bullion-live-map/bullion_mkultra.html`
