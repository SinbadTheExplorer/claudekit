# Bullion Mk Ultra — Identity-Pass Polish (P1s) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the three P1 findings from the 2026-08-06 `/impeccable critique` of `bullion_mkultra.html`'s editorial identity pass — a dead compass-cursor, site-wide undersized text, and a color-blind-unsafe palette — without touching anything outside those three.

**Architecture:** Three independent, non-overlapping edits to the same file: a JS state/cursor fix (Task 1), a CSS font-size sweep split into a reading-content bucket, an interactive-control bucket, and a micro-label bucket (Task 2), and a `GROUP_COLOR` hex re-hue for four swatches (Task 3). A final task (Task 4) runs the project's freeze-check and a consolidated visual pass. No task depends on another's output — order doesn't matter, but line numbers cited below are live-captured from the file as of 2026-08-06 and will drift once Task 1's insertions land; **locate every edit by the quoted anchor text, not by trusting the line number alone**, exactly as this project's prior plans require.

**Tech Stack:** Vanilla JS + CSS inside one static HTML file (`bullion-live-map/bullion_mkultra.html`), Three.js (r-whatever is vendored — already present, not changed here), headless Chrome via CDP for verification, no build step.

## Global Constraints

- **Target file: `bullion-live-map/bullion_mkultra.html` only.** `bullion_mk11.html`–`bullion_mk18.html` must remain byte-identical before and after this pass (freeze-check, Task 4).
- **No new assets or dependencies.** The cursor fix reuses the two SVG data-URIs already present in the file's CSS; the palette fix only changes hex literals already in `GROUP_COLOR`.
- **Headless-Chrome verification needs real (software) WebGL** — pass `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`, per this project's established idiom, since Mk Ultra's normal render path (and therefore `pickMesh()`/cursor behavior) depends on it.
- **Never call `openAuditLog()` in a probe** — its animated modal stalls headless virtual-time. macOS has no `timeout` command to recover from a hang.
- **`docs/superpowers/` stays untracked** — this plan file and the spec it implements are deliberately not committed to git, per this project's standing convention (confirmed across multiple prior handoffs). Do not `git add` anything under `docs/superpowers/`.
- **Do not `git push` without explicit user confirmation** — standing practice in this project. Task 4 stops after local commits and verification; pushing is a separate, explicit ask.
- **`gh` CLI is not installed.** Not needed for this pass (no GitHub API calls).

---

## Verification Harness (used by Tasks 1 and 4)

**Headless-Chrome DOM/behavior probe**, reused with a different probe script per step:

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

Substitute the exact text given in each step for `__PROBE_SCRIPT__`, ending in
`console.log('PROBE_RESULT:' + JSON.stringify(result))`.

**Chrome-MCP visual check**, reused in Task 4: navigate a tab to
`file://~/claude-projects/claudekit/bullion-live-map/bullion_mkultra.html`
(this is pre-push, so the live Pages URL doesn't have these changes yet), screenshot, and check
`read_console_messages` for 0 errors.

---

### Task 1: Fix the dead compass-rose cursor

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:1782` (add `isDragging` state + the two cursor
  data-URI constants)
- Modify: `bullion-live-map/bullion_mkultra.html:2205` area (add `applyCursor()` helper, just
  before `function onPointerMove`)
- Modify: `bullion-live-map/bullion_mkultra.html:2222` (`onPointerMove` — use the helper)
- Modify: `bullion-live-map/bullion_mkultra.html:2236-2252` (`onPointerDown` — set drag state)
- Modify: `bullion-live-map/bullion_mkultra.html:2253` area (`onPointerUp` — clear drag state)
- Modify: `bullion-live-map/bullion_mkultra.html:2275` area (`onPointerCancel` — clear drag state)

**Interfaces:**
- Produces: `CURSOR_GRAB`, `CURSOR_GRABBING` (string constants), `isDragging` (module-scoped
  `let`), `applyCursor()` (function, no params, no return — reads `hoveredId`/`isDragging`,
  writes `canvas.style.cursor`). None of these are consumed outside this task.
- Consumes: nothing from other tasks. Reads the existing module-scoped `canvas` and `hoveredId`
  variables already defined elsewhere in the file (`hoveredId` at line 1727, `canvas` assigned at
  line 2330).

Root cause: `#mkultra-canvas`'s CSS already defines the correct cursor (lines 145-150), but
`onPointerMove` sets `canvas.style.cursor` to the bare keyword `'grab'`/`'pointer'` on every
mouse move, and an inline style always beats a stylesheet rule — so the compass SVG has never
painted.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
const canvas = document.getElementById('mkultra-canvas');
canvas.dispatchEvent(new PointerEvent('pointermove', { clientX: 5, clientY: 5, pointerType: 'mouse', bubbles: true }));
const grabCursor = canvas.style.cursor;
canvas.dispatchEvent(new PointerEvent('pointerdown', { clientX: 5, clientY: 5, pointerType: 'mouse', bubbles: true }));
const grabbingCursor = canvas.style.cursor;
canvas.dispatchEvent(new PointerEvent('pointerup', { clientX: 5, clientY: 5, pointerType: 'mouse', bubbles: true }));
const releasedCursor = canvas.style.cursor;
const result = { grabCursor, grabbingCursor, releasedCursor };
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

(Coordinates `5,5` are near the canvas corner, off any node mesh, so `hoveredId` stays `null` and
the probe exercises the grab/grabbing path rather than the pointer/hover path.)

- [ ] **Step 2: Run the probe to verify it currently fails**

Run the Verification Harness (see above). Expected: `PROBE_RESULT:{"grabCursor":"grab","grabbingCursor":"grab","releasedCursor":"grab"}` — none of the three contain the SVG data-URI, confirming the bug.

- [ ] **Step 3: Add cursor constants and drag state**

Find this line (currently line 1782):
```js
  let downPos = null, downWasTouch = false, pressTimer = null, longPressId = null;
```
Add immediately after it:
```js
  let isDragging = false;
  const CURSOR_GRAB = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9' fill='none' stroke='%23d4b869' stroke-width='1.5'/%3E%3Cpath d='M12 4 L14.2 11 L12 20 L9.8 11 Z' fill='%23d4b869' stroke='%230b0e16' stroke-width='0.6'/%3E%3Ccircle cx='12' cy='12' r='1.6' fill='%230b0e16'/%3E%3C/svg%3E") 12 12, grab`;
  const CURSOR_GRABBING = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='9' fill='%23d4b869' fill-opacity='0.25' stroke='%23d4b869' stroke-width='1.5'/%3E%3Cpath d='M12 4 L14.2 11 L12 20 L9.8 11 Z' fill='%23d4b869' stroke='%230b0e16' stroke-width='0.6'/%3E%3Ccircle cx='12' cy='12' r='1.6' fill='%230b0e16'/%3E%3C/svg%3E") 12 12, grabbing`;
```
(These strings are copied verbatim from the existing `#mkultra-canvas` / `#mkultra-canvas:active`
CSS rules — same SVG, same encoding, same hotspot `12 12`.)

- [ ] **Step 4: Add the `applyCursor()` helper**

Find the comment block immediately before `onPointerMove` (search for `function onPointerMove(event) {` — do not trust the line number, it will have shifted by the 3 lines Step 3 just added). Insert this function immediately before it:
```js
  function applyCursor() {
    canvas.style.cursor = hoveredId ? 'pointer' : (isDragging ? CURSOR_GRABBING : CURSOR_GRAB);
  }
```

- [ ] **Step 5: Use the helper in `onPointerMove`**

Find (search for the exact text, don't trust the line number):
```js
    canvas.style.cursor = id ? 'pointer' : 'grab';
```
Replace with:
```js
    applyCursor();
```

- [ ] **Step 6: Set drag state in `onPointerDown`**

Find:
```js
  function onPointerDown(event) {
    downPos = [event.clientX, event.clientY];
    downWasTouch = event.pointerType === 'touch';
    clearTimeout(pressTimer);
```
Replace with:
```js
  function onPointerDown(event) {
    downPos = [event.clientX, event.clientY];
    downWasTouch = event.pointerType === 'touch';
    isDragging = !downWasTouch;
    applyCursor();
    clearTimeout(pressTimer);
```

- [ ] **Step 7: Clear drag state in `onPointerUp`**

Find:
```js
  function onPointerUp(event) {
    clearTimeout(pressTimer);
```
Replace with:
```js
  function onPointerUp(event) {
    isDragging = false;
    applyCursor();
    clearTimeout(pressTimer);
```

- [ ] **Step 8: Clear drag state in `onPointerCancel`**

Find:
```js
  function onPointerCancel() {
    clearTimeout(pressTimer);
```
Replace with:
```js
  function onPointerCancel() {
    isDragging = false;
    applyCursor();
    clearTimeout(pressTimer);
```

- [ ] **Step 9: Run the probe again to verify it passes**

Run the Verification Harness with the same Step 1 probe script (it's unchanged). Expected:
`PROBE_RESULT:{"grabCursor":"url(\"data:image/svg+xml,...grab","grabbingCursor":"url(\"data:image/svg+xml,...grabbing","releasedCursor":"url(\"data:image/svg+xml,...grab"}` —
`grabCursor` and `releasedCursor` both contain `fill='none'` (the un-pressed compass), `grabbingCursor` contains `fill-opacity='0.25'` (the pressed/filled compass). Exact string equality to the constants defined in Step 3 is the real pass condition — eyeball the fill/fill-opacity markers to confirm without needing to diff the whole data-URI by hand.

- [ ] **Step 10: Chrome-MCP visual spot-check**

Per the Verification Harness's Chrome-MCP check: open the local file in a fresh tab, hover the globe (should show a ring-and-compass-needle cursor, not the OS arrow), press and hold (should show the filled/glowing variant), release (reverts). Confirm 0 console errors.

- [ ] **Step 11: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: fix the compass-rose cursor — inline style was overriding the CSS on every pointer move"
```

---

### Task 2: Raise undersized text to a legible floor (split treatment)

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` — 22 CSS rules across the `<style>` block
  (exact selectors and line numbers below; none of these edits change line count, so line
  numbers are stable within this task and unaffected by Task 1 or Task 3).

**Interfaces:**
- Produces: nothing consumed elsewhere. Consumes: nothing from other tasks.

Three buckets, per the approved design:
- **Reading content → 12px** (sentences, definitions, explanations, warnings a visitor reads to
  understand something), except one nowrap-constrained tooltip → 11px (noted below).
- **Interactive control labels → 11px** (clickable button/link text — misreading these risks a
  wrong action, unlike a decorative tag).
- **Micro-labels/badges/tags → a 1px bump only** (8px→9px, 9px→10px); rules already at 10px or
  10.5px in this bucket are left unchanged — they're the accepted ceiling for this deliberately
  compact, uppercase/tracked UI convention, not a legibility failure. One exception (`.stat-label`)
  is left unchanged despite being informational, because it sits in a 90px-wide grid column and
  bumping it risks wrapping/truncation — noted below.

- [ ] **Step 1: Reading-content bucket — bump to 12px**

Change `font-size` on exactly these 15 selectors from their current value to `12px`. Each is a
single-property edit; find each selector's rule (search by selector name, not line number, since
these may reorder relative to each other only if you edit out of order — edit top-to-bottom to
avoid confusion) and change only the `font-size` value, leaving every other property untouched:

| Selector | Line | Current | New |
|---|---|---|---|
| `.detail-live .live-note` | 240 | `10px` | `12px` |
| `.rel-detail .rel-stat` | 307 | `10.5px` | `12px` |
| `#johnny-disclaimer-tip` | 398 | `10.5px` | `12px` |
| `.sim-note` | 552 | `10px` | `12px` |
| `.impact-why` | 581 | `10px` | `12px` |
| `.impacts-note` | 582 | `9.5px` | `12px` |
| `.gterm::after` | 593 | `10.5px` | `12px` |
| `.stats-context` | 601 | `10px` | `12px` |
| `.stats-foot` | 617 | `9px` | `12px` |
| `.scenario-explain` | 633 | `10.5px` | `12px` |
| `.manual-intro` | 640 | `10.5px` | `12px` |
| `.manual-help` | 656 | `9.5px` | `12px` |
| `.manual-warn` | 657 | `9px` | `12px` |
| `.mg-item .mg-read` | 662 | `10px` | `12px` |
| `.prov-sub` | 663 | `9.5px` | `12px` |

- [ ] **Step 2: Reading content with a width constraint → 11px**

`.orb-nudge-tip` (line 393) has `white-space: nowrap` inside a fixed-position tooltip anchored to
a 52px orb — jumping straight to 12px risks it overflowing its container before the nowrap forces
an ugly clip. Change its `font-size` from `10.5px` to `11px` only (leave `white-space: nowrap`
and everything else untouched).

- [ ] **Step 3: Interactive control labels → 11px**

Change these 2 selectors' `font-size` to `11px`:

| Selector | Line | Current | New |
|---|---|---|---|
| `.btn` (inside `@media (max-width: 640px)`) | 481 | `10px` | `11px` |
| `.disclaimer-link` | 669 | `10px` | `11px` |

- [ ] **Step 4: Micro-label bucket — 1px bump**

Change these 9 selectors' `font-size` by exactly +1px:

| Selector | Line | Current | New |
|---|---|---|---|
| `.rel-strength` | 304 | `9px` | `10px` |
| `.legend-causal-title` | 328 | `9px` | `10px` |
| `.orb-label` | 356 | `9px` | `10px` |
| `.metric-label` | 543 | `9px` | `10px` |
| `.metric-sub` | 547 | `9px` | `10px` |
| `.stat-label small` | 606 | `8px` | `9px` |
| `.tier-badge` | 626 | `9px` | `10px` |
| `.audit-badge` | 629 | `9px` | `10px` |
| `.manual-unit` | 646 | `9px` | `10px` |

`.manual-delta` at line 647 is already `10px` and is a micro-label per the design's numeric-chip
carve-out — no change (it's in the unchanged list in Step 5, not this table).

- [ ] **Step 5: Leave these unchanged — verify, don't edit**

Confirm these still read their original values (no edit needed, just don't touch them while
editing neighbors):
- `#brand-eyebrow` (114, `10px`) — micro-label at the category ceiling
- `#detail-body .section-label` (282, `10px`) — micro-label at the category ceiling
- `.rel-group-head` (292, `10px`) — micro-label at the category ceiling
- `.drawer-label` (549, `10px`) — micro-label at the category ceiling
- `.drawer-tag` (550, `10px`) — micro-label at the category ceiling
- `.stat-label` (605, `10px`) — informational, but lives in a `grid-template-columns: 90px 1fr
  54px` row; bumping it risks wrapping in the 90px column, so it's excluded from the
  reading-content floor by design
- `.manual-delta` (647, `10px`) — numeric-chip micro-label, already at the category ceiling

- [ ] **Step 6: Verify every touched rule via grep**

Run:
```bash
grep -c "font-size: *12px" bullion-live-map/bullion_mkultra.html
```
Expected: at least 15 more matches than before Step 1 (run `git diff --stat` and eyeball the
diff instead of a brittle exact count, since `12px` may already appear elsewhere in the file for
unrelated rules — the reliable check is `git diff bullion-live-map/bullion_mkultra.html` showing
exactly the 15 + 2 + 9 = 26 single-value `font-size` changes from Steps 1, 2 (only `.orb-nudge-tip`,
so 1 line), 3, and 4, and nothing else).

```bash
git diff bullion-live-map/bullion_mkultra.html | grep -E "^[+-].*font-size"
```
Expected: 27 pairs of `-`/`+` lines (one pair per changed selector: 15 from Step 1 + 1 from Step
2 + 2 from Step 3 + 9 from Step 4 — recount against the tables above if the number doesn't
match), each `+` line showing the target value from its table row and nothing else on the line
changed.

- [ ] **Step 7: Chrome-MCP visual crowding check**

Open the local file (per the Verification Harness's Chrome-MCP check). Screenshot the Advanced/
Tools header (the 9-control row flagged in the critique) and a node detail panel with the
relationship breakdown expanded. Confirm nothing visibly overlaps or wraps awkwardly. If the
Tools header now crowds, that's an acceptable trade flagged in the design (font-size floor was
prioritized over density) — only go back and drop a specific 12px rule to 11px if something
actually overlaps or clips, not just looks slightly larger.

- [ ] **Step 8: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: raise undersized text to a legible floor (reading content 11-12px, controls 11px, micro-labels bumped 1px)"
```

---

### Task 3: Re-hue the color-blind-unsafe palette pairs

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:912-923` (`GROUP_COLOR` object — 4 of 12 values)

**Interfaces:**
- Produces: nothing consumed elsewhere (same `GROUP_COLOR` object shape, only 4 values change).
- Consumes: nothing from other tasks.

Two pairs collapse under deuteranopia simulation: `sovereign`/`monetary` (ΔE≈2.7) and
`sectors`/`indicator`(ΔE≈4.2), measured with the Machado et al. (2009) sRGB deuteranopia matrix
and CIE Lab ΔE76. The replacement values below were found by a randomized search (120k+ trials,
hue constrained to ±20° of the original to preserve each swatch's hue family, saturation/
lightness constrained to the palette's existing band) that maximizes the minimum ΔE across the
full 12×12 pairwise matrix — not just the 2 flagged pairs — under **both** normal vision and the
deuteranopia simulation, so it doesn't trade one collision for a new one. Two pre-existing
near-misses among the *unchanged* 8 colors (`capmkt`/`fx` ΔE≈8.1, `regulator`/`fx` ΔE≈8.8, both
under deuteranopia) are untouched by this search and remain exactly as they were — they're a
pre-existing condition, not something this fix creates, and are explicitly out of scope per the
approved design (only fix what the critique flagged; don't expand scope to unflagged near-misses
mid-implementation).

**This is a first draft, not a final answer** — same caveat the original palette pass (`cf43c4d`)
should have carried and didn't. Step 3 below is a mandatory screenshot check with explicit
permission to adjust lightness/saturation (not hue family) if any pair doesn't read as
distinguishable in an actual render.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
const result = { GROUP_COLOR };
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe to verify current (unfixed) values**

Run the Verification Harness. Expected: `PROBE_RESULT:{"GROUP_COLOR":{"regulator":"#9aa4b2","sovereign":"#6fa2d1","monetary":"#ab93d4","commercial":"#9c6f52","shadow":"#6b9a92","capmkt":"#6fc7a6","sectors":"#e0926a","indicator":"#9cc26a","sentiment":"#b578ad","fx":"#8dbfb6","commodity":"#d4a843","geo":"#c97b8a"}}` —
confirms the pre-fix baseline (this is a documentation/confirmation step, not a real failing
assertion, since a plain object dump can't "fail").

- [ ] **Step 3: Change the 4 flagged hex values**

Find (line 912):
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
Replace with (only the 4 marked lines change):
```js
const GROUP_COLOR = {
  regulator:  '#9aa4b2',
  sovereign:  '#5271d7',  // was #6fa2d1 — widened from `monetary` under deuteranopia sim
  monetary:   '#9c91df',  // was #ab93d4 — widened from `sovereign` under deuteranopia sim
  commercial: '#9c6f52',
  shadow:     '#6b9a92',
  capmkt:     '#6fc7a6',
  sectors:    '#d74438',  // was #e0926a — widened from `indicator` under deuteranopia sim
  indicator:  '#b2da8b',  // was #9cc26a — widened from `sectors` under deuteranopia sim
  sentiment:  '#b578ad',
  fx:         '#8dbfb6',
  commodity:  '#d4a843',
  geo:        '#c97b8a',
};
```

- [ ] **Step 4: Run the probe again to verify the new values landed**

Run the Verification Harness with the same Step 1 probe. Expected: `sovereign` is `#5271d7`,
`monetary` is `#9c91df`, `sectors` is `#d74438`, `indicator` is `#b2da8b`, and all other 8 keys
are unchanged from Step 2's output.

- [ ] **Step 5: Chrome-MCP visual verification — normal vision**

Open the local file, open the legend/layer panel showing all 12 group swatches. Screenshot it.
Confirm by eye that `sovereign` (now a richer blue) and `monetary` (periwinkle/lavender-blue) read
as distinct, and `sectors` (now a warm red) and `indicator` (now a pale green) read as distinct.
If any pair still looks ambiguous to typical vision, that's a real signal to adjust — see Step 7.

- [ ] **Step 6: Deuteranopia-simulated verification**

Use a browser-based or OS-level color-blindness simulation (e.g. Chrome DevTools' built-in vision
deficiency emulation: DevTools → Rendering tab → "Emulate vision deficiencies" → Deuteranopia) on
the same legend screenshot from Step 5. Confirm all four re-hued swatches are still
distinguishable from their original collision partner and from the rest of the palette under the
simulation.

- [ ] **Step 7: Adjust if needed**

If Step 5 or Step 6 shows a pair that still reads as ambiguous, you have explicit permission to
adjust that swatch's lightness and/or saturation (not hue — don't drift out of the blue/purple/
red/green families established above, since that's what keeps the palette's "premium gold-on-
void" character intact) and re-run Steps 4-6 until it's visibly resolved. Don't skip this step
just because the math in the Step 3 comments says it should work — render and look, per this
project's standing lesson from the first palette pass.

- [ ] **Step 8: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: re-hue sovereign/monetary and sectors/indicator for deuteranopia-safe contrast"
```

---

### Task 4: Freeze-check and consolidated verification

**Files:** none modified — verification only.

**Interfaces:** Consumes: the committed results of Tasks 1-3. Produces: nothing (terminal task).

- [ ] **Step 1: Freeze-check the untouched map versions**

```bash
git diff --stat -- bullion-live-map/bullion_mk1[1-8].html
```
Expected: empty output (no changes). This pass only ever touched `bullion_mkultra.html`.

- [ ] **Step 2: Run the existing Python suites as a sanity check**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate
```
Expected: same pass counts as before this pass started (this work is CSS/JS-only inside
`bullion_mkultra.html` and shouldn't affect Python-side tests at all — a new failure here means
something unrelated broke, not a regression from Tasks 1-3, but investigate before proceeding
either way).

- [ ] **Step 3: Consolidated Chrome-MCP pass**

Open the local file in a fresh tab (`file://~/claude-projects/claudekit/bullion-live-map/bullion_mkultra.html`).
In one session: hover/drag the globe (cursor), open a node detail panel and the relationship
breakdown (text sizes), open the legend/layer panel (palette). Screenshot each. Confirm
`read_console_messages` shows 0 errors across the whole pass.

- [ ] **Step 4: Report and stop — do not push**

Summarize what changed (3 commits: cursor, text-sizes, palette) and the verification results.
**Do not run `git push`.** Per this project's standing practice, pushing to `origin/main` needs
explicit user confirmation — ask, don't assume, even though this is a low-risk pass.
