# Bullion Mk Ultra — Field-Note Discoverability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the 2 existing field notes (`credit→equit`, `usd→oil`) in `bullion_mkultra.html` discoverable — right now nothing in the graph, the Overview board, or the relationship panel signals which links have one, per the 2026-08-06 `/impeccable critique`'s second deferred P2.

**Architecture:** One shared foundation (a `FIELDNOTE_NODE_IDS` set + a `.fieldnote-badge` CSS class, Task 1), then three independent placements of the same badge — Overview board card (Task 2), 3D node label (Task 3), relationship row (Task 4) — plus an unrelated one-sentence onboarding addition (Task 5). Tasks 2-5 each depend only on Task 1's foundation, not on each other. A final task (Task 6) runs a consolidated probe across all four surfaces, the project's freeze-check, and a Chrome-MCP visual pass. **Writing more field notes or lowering the authoring bar is explicitly out of scope** — this plan only makes the existing 2 easier to find.

**Tech Stack:** Vanilla JS + CSS inside one static HTML file (`bullion-live-map/bullion_mkultra.html`), no build step, headless Chrome via CDP for verification (same harness this project's prior Mk Ultra passes used).

## Global Constraints

- **Target file: `bullion-live-map/bullion_mkultra.html` only.** `bullion_mk11.html`–`bullion_mk18.html` must remain byte-identical before and after this pass (freeze-check, Task 6).
- **`FIELDNOTE_NODE_IDS` must be derived from `LINKS` *after* the existing `PLUMBING_LINKS` → `LINKS` supersede-or-append merge block** (search for `PLUMBING_LINKS.forEach(pl => {`, the merge finishes at the closing `});` right before it). Reading `LINKS` or `PLUMBING_LINKS` separately, or before the merge runs, gives wrong results — this project's standing two-link-array trap.
- **No new assets or dependencies.** The badge is a single Unicode glyph (✎, U+270E) styled with the existing `var(--gold-dim)` color token — no images, no icon font.
- **The badge is decorative, not interactive.** Do not add a click handler to it, and do not nest it as a focusable element inside `.board-card` (already a `<button>`) — it's a passive signal only, per the approved design.
- **Headless-Chrome verification needs real (software) WebGL** — pass `--use-gl=angle --use-angle=swiftshader --enable-unsafe-swiftshader`, since the 3D label check (Task 3) depends on the `Renderer` module's async init having completed.
- **Never call `openAuditLog()` in a probe** — its animated modal stalls headless virtual-time. macOS has no `timeout` command to recover from a hang.
- **`docs/superpowers/` stays untracked** — this plan file and the spec it implements are deliberately not committed to git, per this project's standing convention (confirmed across multiple prior handoffs, and by `git status` showing every existing file under `docs/superpowers/specs/` as untracked). Do not `git add` anything under `docs/superpowers/`.
- **Do not `git push` without explicit user confirmation** — standing practice in this project. Task 6 stops after local commits and verification; pushing is a separate, explicit ask.
- **`gh` CLI is not installed.** Not needed for this pass (no GitHub API calls).

---

## Verification Harness (reused across all tasks)

**Headless-Chrome DOM/behavior probe**, with a different probe script per step:

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

**Chrome-MCP visual check**, reused in Task 6: navigate a tab to
`file://~/claude-projects/claudekit/bullion-live-map/bullion_mkultra.html`
(this is pre-push, so the live Pages URL doesn't have these changes yet), screenshot, and check
`read_console_messages` for 0 errors.

**Why probes poll instead of reading state immediately:** the 3D scene (`Renderer`, an IIFE at
`const Renderer = (function () {...})();`) initializes asynchronously behind real WebGL, and its
internal `labelEls` map is private to that closure — not reachable from an injected probe script.
Tasks 3 and 4's probes therefore poll on DOM presence (`#mkultra-labels > div` children, or
`.board-card` elements) rather than reading `Renderer`'s internals directly.

---

### Task 1: Foundation — `FIELDNOTE_NODE_IDS` set and `.fieldnote-badge` CSS class

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (~line 311, CSS `<style>` block — add one rule)
- Modify: `bullion-live-map/bullion_mkultra.html` (~line 1533, JS — add the constant right after the `PLUMBING_LINKS` merge block)

**Interfaces:**
- Produces: `FIELDNOTE_NODE_IDS` (top-level `const`, a `Set<string>` of node ids that participate in at least one link with a `fieldNote`), CSS class `.fieldnote-badge`. Both consumed by Tasks 2, 3, and 4.
- Consumes: nothing from other tasks. Reads the existing top-level `LINKS` array (already merged with `PLUMBING_LINKS` by the time this code runs — see Global Constraints).

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
const result = { ids: (typeof FIELDNOTE_NODE_IDS !== 'undefined') ? [...FIELDNOTE_NODE_IDS].sort() : 'UNDEFINED' };
console.log('PROBE_RESULT:' + JSON.stringify(result));
```

- [ ] **Step 2: Run the probe to verify it currently fails**

Run the Verification Harness. Expected: `PROBE_RESULT:{"ids":"UNDEFINED"}` — the constant doesn't exist yet.

- [ ] **Step 3: Add the CSS class**

Find (search for the exact text — do not trust the line number):
```css
  .rel-field-note-narrate:hover { color: var(--gold); }
```
Add immediately after it:
```css
  .fieldnote-badge { color: var(--gold-dim); font-size: 10px; margin-left: 3px; cursor: default; }
```

- [ ] **Step 4: Add the `FIELDNOTE_NODE_IDS` constant**

Find (search for the exact text — this is the last line of the `PLUMBING_LINKS.forEach` merge block):
```js
PLUMBING_LINKS.forEach(pl => {
  const i = LINKS.findIndex(l => l.s === pl.s && l.t === pl.t);
  if (i >= 0) {
    SUPERSEDED.push({ s:pl.s, t:pl.t, oldSign:LINKS[i].sign, newSign:pl.sign, oldWhy:LINKS[i].why });
    LINKS[i] = pl;
  } else {
    LINKS.push(pl);
  }
});
```
Add immediately after it:
```js

// Nodes that participate in at least one link carrying a first-person field note —
// drives the discoverability marker on board cards, node labels, and relationship rows.
const FIELDNOTE_NODE_IDS = new Set();
LINKS.forEach(l => { if (l.fieldNote) { FIELDNOTE_NODE_IDS.add(l.s); FIELDNOTE_NODE_IDS.add(l.t); } });
```

- [ ] **Step 5: Run the probe again to verify it passes**

Run the Verification Harness with the same Step 1 probe script. Expected:
`PROBE_RESULT:{"ids":["credit","equit","oil","usd"]}`

- [ ] **Step 6: Grep-verify the CSS rule landed**

```bash
grep -c "fieldnote-badge" bullion-live-map/bullion_mkultra.html
```
Expected: `1` (only the CSS rule exists so far — Tasks 2-4 will each add one more usage).

- [ ] **Step 7: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: add field-note badge foundation (FIELDNOTE_NODE_IDS + .fieldnote-badge)"
```

---

### Task 2: Board-card badge

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (`buildBoard`, ~line 2921-2927)

**Interfaces:**
- Consumes: `FIELDNOTE_NODE_IDS`, `.fieldnote-badge` (Task 1).
- Produces: nothing consumed elsewhere.

This is the most reliable of the three placements — `buildBoard()` runs once, unconditionally, at
init (line ~2678), and renders every node's card regardless of hub/focus state, so this badge is
always present in the DOM.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
function poll(){
  const cards = document.querySelectorAll('.board-card');
  if (!cards.length) return setTimeout(poll, 200);
  const check = id => { const c = document.querySelector('.board-card[data-id="' + id + '"]'); return !!(c && c.querySelector('.fieldnote-badge')); };
  const result = { credit: check('credit'), equit: check('equit'), usd: check('usd'), oil: check('oil'), fed_should_be_false: check('fed') };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
}
poll();
```

- [ ] **Step 2: Run the probe to verify it currently fails**

Run the Verification Harness. Expected: `PROBE_RESULT:{"credit":false,"equit":false,"usd":false,"oil":false,"fed_should_be_false":false}` — no badges anywhere yet.

- [ ] **Step 3: Add the badge to board cards**

Find (search for the exact text — do not trust the line number):
```js
      const card = document.createElement('button');
      card.className = 'board-card' + (n.isHub ? ' hub' : '');
      card.style.borderLeftColor = GROUP_COLOR[n.group] || '#8891a6';
      card.textContent = n.label;
      card.setAttribute('aria-label', n.label);
      card.dataset.id = n.id;
```
Replace with:
```js
      const card = document.createElement('button');
      card.className = 'board-card' + (n.isHub ? ' hub' : '');
      card.style.borderLeftColor = GROUP_COLOR[n.group] || '#8891a6';
      card.appendChild(document.createTextNode(n.label));
      if (FIELDNOTE_NODE_IDS.has(n.id)) {
        const badge = document.createElement('span');
        badge.className = 'fieldnote-badge';
        badge.textContent = '✎';
        badge.title = 'Field note — the creator’s own note on this link';
        card.appendChild(badge);
      }
      card.setAttribute('aria-label', n.label);
      card.dataset.id = n.id;
```
(`card.textContent = n.label` wiped any children on every call, which is why this switches to a text node + conditional appended span instead of a plain assignment — `card.appendChild(document.createTextNode(n.label))` is the direct equivalent for the no-badge case.)

- [ ] **Step 4: Run the probe again to verify it passes**

Run the Verification Harness with the same Step 1 probe script. Expected:
`PROBE_RESULT:{"credit":true,"equit":true,"usd":true,"oil":true,"fed_should_be_false":false}`

- [ ] **Step 5: Chrome-MCP visual spot-check**

Per the Verification Harness's Chrome-MCP check: open the local file, switch to the Overview
board tab, find the "Credit Markets" card, confirm a small gold pencil mark sits after its label
and doesn't wrap or crowd the card at normal width. Confirm 0 console errors.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: mark field-note nodes on the Overview board"
```

---

### Task 3: 3D node-label badge

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (`buildLabels`, ~line 1966-1979, inside the `Renderer` IIFE)

**Interfaces:**
- Consumes: `FIELDNOTE_NODE_IDS`, `.fieldnote-badge` (Task 1). `FIELDNOTE_NODE_IDS` is a top-level
  `const`, reachable from inside the `Renderer` IIFE the same way `GROUP_COLOR` already is on the
  line directly above this edit.
- Produces: nothing consumed elsewhere.

`buildLabels()` creates one DOM label div per node (not just hubs) up front; whether a given
label is ever shown is a separate, later visibility toggle (`labelEligible`) that this task does
not touch. The badge is opportunistic: visible whenever that node's label is already shown today
(hub, or a focused node's neighbor) — no change to which labels show.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
function poll(){
  const labels = document.querySelectorAll('#mkultra-labels > div');
  if (!labels.length) return setTimeout(poll, 300);
  const hasBadge = text => Array.from(labels).some(el => el.textContent.includes(text) && !!el.querySelector('.fieldnote-badge'));
  const result = {
    credit: hasBadge('Credit Markets'),
    equit: hasBadge('Equity Markets'),
    usd: hasBadge('US Dollar (DXY)'),
    oil: hasBadge('Oil Price (WTI)'),
    fed_should_be_false: hasBadge('Federal Reserve')
  };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
}
poll();
```

- [ ] **Step 2: Run the probe to verify it currently fails**

Run the Verification Harness. Expected: `PROBE_RESULT:{"credit":false,"equit":false,"usd":false,"oil":false,"fed_should_be_false":false}`

- [ ] **Step 3: Add the badge to node labels**

Find (search for the exact text — do not trust the line number):
```js
    nodesArr.forEach(d => {
      const el = document.createElement('div');
      el.textContent = d.label;
      Object.assign(el.style, {
        position: 'absolute', transform: 'translate(-50%, 0)', whiteSpace: 'nowrap',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: d.isHub ? '11px' : '9px',
        fontWeight: d.isHub ? '700' : '400',
        color: d.isHub ? (GROUP_COLOR[d.group] || 'var(--text-dim)') : 'rgba(216,220,230,0.85)',
        textShadow: '0 1px 3px rgba(0,0,0,0.85), 0 0 6px rgba(0,0,0,0.55)',
        display: 'none', willChange: 'transform, left, top',
      });
      labelContainer.appendChild(el);
      labelEls[d.id] = el;
    });
```
Replace with:
```js
    nodesArr.forEach(d => {
      const el = document.createElement('div');
      el.textContent = d.label;
      Object.assign(el.style, {
        position: 'absolute', transform: 'translate(-50%, 0)', whiteSpace: 'nowrap',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: d.isHub ? '11px' : '9px',
        fontWeight: d.isHub ? '700' : '400',
        color: d.isHub ? (GROUP_COLOR[d.group] || 'var(--text-dim)') : 'rgba(216,220,230,0.85)',
        textShadow: '0 1px 3px rgba(0,0,0,0.85), 0 0 6px rgba(0,0,0,0.55)',
        display: 'none', willChange: 'transform, left, top',
      });
      if (FIELDNOTE_NODE_IDS.has(d.id)) {
        const badge = document.createElement('span');
        badge.className = 'fieldnote-badge';
        badge.textContent = '✎';
        badge.title = 'Field note — the creator’s own note on this link';
        el.appendChild(badge);
      }
      labelContainer.appendChild(el);
      labelEls[d.id] = el;
    });
```

- [ ] **Step 4: Run the probe again to verify it passes**

Run the Verification Harness with the same Step 1 probe script. Expected:
`PROBE_RESULT:{"credit":true,"equit":true,"usd":true,"oil":true,"fed_should_be_false":false}`

- [ ] **Step 5: Chrome-MCP visual spot-check**

Open the local file, click the "Credit Markets" hub dot (or wait for hub labels to render — hubs
show labels by default). Confirm the label text shows a small gold pencil mark alongside it and
stays legible against the starfield background.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: mark field-note nodes in the 3D graph labels"
```

---

### Task 4: Relationship-row badge

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (`rowHtml`, ~line 2778-2791)

**Interfaces:**
- Consumes: `.fieldnote-badge` (Task 1). Reads `r.l.fieldNote` directly (existing per-link data,
  not `FIELDNOTE_NODE_IDS` — this placement needs to know about the *specific link*, not just
  "this node has one somewhere").
- Produces: nothing consumed elsewhere.

This is the only placement tied to the exact link rather than the node — once a visitor opens a
hub with many relationships, this lets them scan the compact row headers instead of reading every
expanded `.rel-detail` paragraph.

- [ ] **Step 1: Write the failing probe**

Substitute into the harness:
```js
function poll(){
  if (!document.getElementById('mkultra-canvas')) return setTimeout(poll, 300);
  function badgedTargets(nodeId){
    openDetail(nodeById[nodeId]);
    return Array.from(document.querySelectorAll('#rel-list .rel-row'))
      .filter(r => r.querySelector('.fieldnote-badge'))
      .map(r => r.dataset.to);
  }
  const result = { fromCredit: badgedTargets('credit'), fromUsd: badgedTargets('usd') };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
}
poll();
```

- [ ] **Step 2: Run the probe to verify it currently fails**

Run the Verification Harness. Expected: `PROBE_RESULT:{"fromCredit":[],"fromUsd":[]}` — no row carries a badge yet.

- [ ] **Step 3: Add the badge to the relationship row**

Find (search for the exact text — do not trust the line number):
```js
    return '<div class="rel-row" data-to="' + r.other + '">' +
        '<div class="rel-row-top">' +
          '<span class="rel-dot" style="background:' + color + '"></span>' +
          '<span class="rel-arrow">' + arrow + '</span>' +
          '<span class="rel-name">' + name + '</span>' +
          '<span class="rel-arrows" style="color:' + color + '" title="Direction and strength (? = unverified sign)">' + arrowGlyphs(r.l) + '</span>' +
          '<span class="rel-strength">' + strengthWord(r.l.w) + '</span>' +
        '</div>' +
```
Replace with:
```js
    return '<div class="rel-row" data-to="' + r.other + '">' +
        '<div class="rel-row-top">' +
          '<span class="rel-dot" style="background:' + color + '"></span>' +
          '<span class="rel-arrow">' + arrow + '</span>' +
          '<span class="rel-name">' + name + '</span>' +
          (r.l.fieldNote ? '<span class="fieldnote-badge" title="Field note — the creator’s own note on this link">&#9998;</span>' : '') +
          '<span class="rel-arrows" style="color:' + color + '" title="Direction and strength (? = unverified sign)">' + arrowGlyphs(r.l) + '</span>' +
          '<span class="rel-strength">' + strengthWord(r.l.w) + '</span>' +
        '</div>' +
```

- [ ] **Step 4: Run the probe again to verify it passes**

Run the Verification Harness with the same Step 1 probe script. Expected:
`PROBE_RESULT:{"fromCredit":["equit"],"fromUsd":["oil"]}` — exactly one badged row from each
node, pointing at the correct other end of the field-noted link.

- [ ] **Step 5: Chrome-MCP visual spot-check**

Open the local file, click the "Credit Markets" node, scroll the relationship list, confirm the
row heading to "Equity Markets" shows the pencil mark and that other rows in the same list do
not.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: mark the specific field-noted relationship row"
```

---

### Task 5: Onboarding mention

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (`COACH` array, step index 1, ~line 3013-3015)

**Interfaces:**
- Consumes: nothing from other tasks (a plain string change; thematically related to Tasks 1-4
  but has no code dependency on them).
- Produces: nothing consumed elsewhere.

One sentence appended to the existing "That card is the point" step — the step that already
introduces what a card shows. Not a new coach step (disproportionate for one sentence), and not
gated on the badge tasks landing first (the sentence is accurate regardless of implementation
order, though in practice this task should land last since it references the icon Tasks 2-4
introduce).

- [ ] **Step 1: Grep-verify the sentence is absent**

```bash
grep -c "creator left a first-person note" bullion-live-map/bullion_mkultra.html
```
Expected: `0`

- [ ] **Step 2: Add the sentence**

Find (search for the exact text — do not trust the line number):
```js
  { title: 'That card is the point',
    body: 'Each dot opens a plain-English card — what the player is and what it pushes on. The <b>lines that just lit up</b> are its cause-and-effect links.',
    cta: 'One more &rarr;', arrow: false },
```
Replace with:
```js
  { title: 'That card is the point',
    body: 'Each dot opens a plain-English card — what the player is and what it pushes on. The <b>lines that just lit up</b> are its cause-and-effect links.<br><br>A <span style="color:var(--gold-dim)">&#9998;</span> next to a name means the creator left a first-person note on why that link changed.',
    cta: 'One more &rarr;', arrow: false },
```

- [ ] **Step 3: Grep-verify the sentence landed**

```bash
grep -c "creator left a first-person note" bullion-live-map/bullion_mkultra.html
```
Expected: `1`

- [ ] **Step 4: Chrome-MCP visual spot-check**

Open the local file in beginner mode (default), step through the onboarding coach to "That card
is the point", confirm the new sentence renders on its own line below the existing copy and the
pencil glyph matches the gold-dim tone used elsewhere.

- [ ] **Step 5: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "Mk Ultra: mention the field-note marker in onboarding"
```

---

### Task 6: Consolidated verification, freeze-check, and stop

**Files:** none modified — verification only.

**Interfaces:** Consumes: the committed results of Tasks 1-5. Produces: nothing (terminal task).

- [ ] **Step 1: Freeze-check the untouched map versions**

```bash
git diff --stat -- bullion-live-map/bullion_mk1[1-8].html
```
Expected: empty output (no changes). This pass only ever touched `bullion_mkultra.html`.

- [ ] **Step 2: Consolidated headless probe across all four surfaces**

Substitute into the Verification Harness:
```js
function poll(){
  const cards = document.querySelectorAll('.board-card');
  const labels = document.querySelectorAll('#mkultra-labels > div');
  const canvasReady = document.getElementById('mkultra-canvas');
  if (!cards.length || !labels.length || !canvasReady) return setTimeout(poll, 300);
  const boardCheck = id => { const c = document.querySelector('.board-card[data-id="' + id + '"]'); return !!(c && c.querySelector('.fieldnote-badge')); };
  const labelCheck = text => Array.from(labels).some(el => el.textContent.includes(text) && !!el.querySelector('.fieldnote-badge'));
  function badgedTargets(nodeId){
    openDetail(nodeById[nodeId]);
    return Array.from(document.querySelectorAll('#rel-list .rel-row'))
      .filter(r => r.querySelector('.fieldnote-badge'))
      .map(r => r.dataset.to);
  }
  const result = {
    fieldnoteIds: [...FIELDNOTE_NODE_IDS].sort(),
    board: { credit: boardCheck('credit'), equit: boardCheck('equit'), usd: boardCheck('usd'), oil: boardCheck('oil'), fed: boardCheck('fed') },
    labels: { credit: labelCheck('Credit Markets'), equit: labelCheck('Equity Markets'), usd: labelCheck('US Dollar (DXY)'), oil: labelCheck('Oil Price (WTI)'), fed: labelCheck('Federal Reserve') },
    rows: { fromCredit: badgedTargets('credit'), fromUsd: badgedTargets('usd') }
  };
  console.log('PROBE_RESULT:' + JSON.stringify(result));
}
poll();
```
Expected: `fieldnoteIds` is `["credit","equit","oil","usd"]`; `board` and `labels` are all `true`
except `fed:false`; `rows.fromCredit` is `["equit"]` and `rows.fromUsd` is `["oil"]`. (This probe
doesn't check the onboarding sentence — that's covered by Task 5's grep check and Step 4 below.)

- [ ] **Step 3: Run the existing Python suites as a sanity check**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate
```
Expected: same pass counts as before this pass started (this work is CSS/JS-only inside
`bullion_mkultra.html` and shouldn't affect Python-side tests at all — a new failure here means
something unrelated broke, not a regression from Tasks 1-5, but investigate before proceeding
either way).

- [ ] **Step 4: Consolidated Chrome-MCP pass**

Open the local file in a fresh tab
(`file://~/claude-projects/claudekit/bullion-live-map/bullion_mkultra.html`).
In one session: check the Overview board for the pencil mark on "Credit Markets" / "Equity
Markets" / "US Dollar (DXY)" / "Oil Price (WTI)" cards; open "Credit Markets"' detail panel and
confirm the "Equity Markets" row carries the mark; step through onboarding to "That card is the
point" and confirm the new sentence renders. Screenshot each. Confirm `read_console_messages`
shows 0 errors across the whole pass.

- [ ] **Step 5: Report and stop — do not push**

Summarize what changed (5 commits: foundation, board card, 3D label, relationship row,
onboarding) and the verification results. **Do not run `git push`.** Per this project's standing
practice, pushing to `origin/main` needs explicit user confirmation — ask, don't assume.
