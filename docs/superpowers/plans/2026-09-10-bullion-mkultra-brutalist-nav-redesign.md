# Bullion Mk Ultra Brutalist Nav Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize `bullion_mkultra.html`'s top-level navigation from 4 destinations (3D Map / Overview / Markets / Tools drawer) into 3 (Market / Analysis / Causal Link), and replace its visual language (navy/gold/rounded-cards/emoji) with a flat brutalist system (near-black, red-orange accent, thick rule lines, oversized numerals, an italic-Greek-Δ used both functionally and as background texture).

**Architecture:** Single-file edit, no new files — matches this project's existing one-file-per-map-version convention (mk11 through mkultra all live as standalone HTML). Nine tasks, each a complete working state committed directly to `main`. Tasks 1-2 are global (CSS tokens, icon sweep) and touch many small spots; Tasks 3-8 work tab-by-tab; Task 9 is a whole-app verification pass. No task depends on unmerged work from a later task — each commit leaves the live site fully functional, even mid-redesign.

**Amendment (2026-09-11, added during execution):** Task 8's own review surfaced a real gap in this plan (traced to the spec's Phase 4 description never using the word "restyle," unlike Phases 3/5) — the Analysis tab's internal content (health score, scenario stats, glossary, chain-reaction cards, etc.) and some detail-panel internals were never assigned to any of the original 9 tasks, so nobody ever restyled them; Task 5 correctly scoped itself to a container-only conversion per its own brief, and Task 7 correctly scoped to container ids only. **Task 8b** (inserted below, between Task 8 and Task 9) closes this gap. Task 9 (verification-only, no code changes) could not have caught or fixed this on its own.

**Tech Stack:** Vanilla HTML/CSS/JS (no build step, no framework), Three.js r160 (vendored, untouched by this plan), the project's existing headless-chrome-verification skill (CDP probe) for visual checks, Python `tests/` suite for the non-visual regression check in Task 9.

**Spec:** `docs/superpowers/specs/2026-09-09-bullion-mkultra-brutalist-nav-redesign-design.md`

## Global Constraints

- Every task's commit must leave `bullion_mkultra.html` in a fully working state — never a broken intermediate (per the spec's "direct on main, in phases" build strategy and this project's standing "never publish a truncated state" discipline).
- No change to `data.json`/`news.json` shape, `fetch_bullion_data.py`, `ELASTICITY`/`NODE_ELASTICITY` *values*, or the Three.js scene's own rendering (lighting/glow/orbit controls) — visual/structural changes to surrounding chrome only.
- Accent color is `#ff3300` everywhere a UI element needs the brand color. `--gold` (`#d4b869`) is kept as a CSS variable but only for literal gold-colored *data* (e.g. the word/number "GOLD"), never for buttons/nav/active-states/borders from Task 1 onward.
- No `border-radius` on anything touched by this redesign — thick (2-3px) solid rule lines replace rounded card borders.
- No gradients anywhere touched by this redesign (the existing `#starfield` radial-gradients are explicitly in scope for removal in Task 1 — they're a gradient-heavy decorative layer the spec's "no gradients" rule directly contradicts, even though the spec's own Visual System section didn't call it out by name).
- Δ (delta, U+0394) is styled `font-family: Georgia, "Times New Roman", serif; font-style: italic;` in both its functional (inline, prefixing a numeric change value) and textural (oversized, ~7% opacity, ghosted behind a hero stat) uses.
- The existing `beginnerMode` toggle, its `applyBeginnerMode()`/`.adv-control` show-hide mechanism, and the coach-mark tour (`#coach`, `renderCoach()`) keep their exact current behavior — visual restyle only, per explicit user decision during planning (2026-09-10). Do not redesign when/what they hide.
- Every phase gets a `headless-chrome-verification` CDP-probe screenshot before its commit (same method used for the Fed-odds card, 2026-09-08) — visual correctness is asserted from a real render, not from reading the CSS.

---

### Task 1: Design tokens, base type, starfield flatten

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:31-53` (`:root` block)
- Modify: `bullion-live-map/bullion_mkultra.html:58-69` (`html, body` base rule)
- Modify: `bullion-live-map/bullion_mkultra.html:70-83` (`#starfield`)

**Interfaces:**
- Produces: a new `--accent: #ff3300;` CSS variable, consumed by every later task in place of `--gold`/`--gold-dim` wherever a rule is doing UI/brand coloring (buttons, active states, nav, borders) rather than literal data coloring.
- Produces: `--bg-deep`, `--bg-panel`, `--bg-panel2`, `--border` repointed to near-black/flat values, inherited automatically by every existing rule that already references them (no further edits needed elsewhere for background color alone).
- Produces: `body`'s `font-family` repointed to a condensed sans stack, inherited by everything that doesn't set its own `font-family` (headings still override via `--font-display`, untouched).

- [ ] **Step 1: Update the `:root` custom properties**

Current (`bullion_mkultra.html:31-53`):
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
  --blue:       #4d7fb8;
  --blue-dim:   #24425e;
  --red-dim:    #7a2e1f;
  --amber:      #e0b15a;
  --up:         #e0654f;
  --down:       #7bbf8e;
  --warn:       #e0b15a;
  --scenario-active: #8b0000;
  --font-display: "Times New Roman", Times, serif;
}
```

Replace with:
```css
:root {
  --bg-deep:    #000000;
  --bg-panel:   #0d0d0d;
  --bg-panel2:  #0d0d0d;
  --border:     #ffffff;
  --text:       #ffffff;
  --text-dim:   #999999;
  --gold:       #d4b869;   /* literal data color only (e.g. "GOLD $2,847.30") — never UI/brand from here on */
  --gold-dim:   #a8925a;
  --accent:     #ff3300;   /* new: the single UI/brand accent, replacing --gold's old role */
  --green:      #7bbf8e;
  --red:        #e0654f;
  --blue:       #4d7fb8;
  --blue-dim:   #24425e;
  --red-dim:    #7a2e1f;
  --amber:      #e0b15a;
  --up:         #e0654f;
  --down:       #7bbf8e;
  --warn:       #e0b15a;
  --scenario-active: #8b0000;
  --font-display: Georgia, "Times New Roman", serif;       /* italic-Greek-friendly serif for Δ and display headings */
  --font-condensed: "Arial Narrow", "Helvetica Neue", Arial, sans-serif;
}
```

Note: `--border` going fully white (`#ffffff`) is deliberate — brutalist rule lines are solid, high-contrast dividers, not the old subtle `#1e2436` hairline. Anything currently drawing a 1px `var(--border)` line will now draw a stark white one; later tasks (3-8) thicken the load-bearing ones (nav, section dividers) to 2-3px as they're touched, but this token change alone already removes the "subtle dark-on-dark" look everywhere immediately.

- [ ] **Step 2: Update the base `html, body` rule**

Current (`bullion_mkultra.html:58-69`), only the `font-family` line changes:
```css
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```
becomes:
```css
    font-family: var(--font-condensed);
```
(Leave every other line in this rule — the `100dvh`/`overscroll-behavior`/`touch-action` layout-safety comments and values — untouched; they're layout mechanics, not visual language.)

- [ ] **Step 3: Flatten `#starfield`**

Current (`bullion_mkultra.html:70-83`):
```css
  #starfield {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
      radial-gradient(1px 1px at 10% 20%, rgba(255,255,255,0.55), transparent),
      radial-gradient(1px 1px at 80% 10%, rgba(255,255,255,0.4), transparent),
      radial-gradient(1.5px 1.5px at 60% 70%, rgba(255,255,255,0.5), transparent),
      radial-gradient(1px 1px at 30% 85%, rgba(255,255,255,0.35), transparent),
      radial-gradient(1px 1px at 90% 60%, rgba(255,255,255,0.45), transparent),
      radial-gradient(1.5px 1.5px at 45% 35%, rgba(255,255,255,0.3), transparent),
      radial-gradient(1px 1px at 20% 55%, rgba(255,255,255,0.4), transparent),
      radial-gradient(1px 1px at 70% 90%, rgba(255,255,255,0.3), transparent),
      radial-gradient(ellipse at 50% 0%, rgba(80,60,140,0.10), transparent 60%),
      radial-gradient(ellipse at 20% 100%, rgba(40,80,120,0.08), transparent 55%);
  }
```

Replace with:
```css
  #starfield {
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background: var(--bg-deep);
  }
```

This removes both the star dots and the purple/blue nebula glow (all `radial-gradient`, forbidden by the Global Constraints). `#starfield` sits behind `#app` (`z-index: 0` vs `#app`'s `z-index: 1`) purely as a background-fill layer at this point — keep the element and rule rather than deleting it, since `#app`'s own background isn't set and removing `#starfield` entirely would require adding a background elsewhere to avoid an unstyled-white flash-of-unstyled-content risk on slow loads.

- [ ] **Step 4: Screenshot and verify**

Serve the directory locally and screenshot the default (3D Map) view with the `headless-chrome-verification` skill's static-capture recipe:
```bash
pkill -f cdp-shot- 2>/dev/null
(cd bullion-live-map && python3 -m http.server 8792 >/tmp/bullion-http.log 2>&1 &)
sleep 1
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
  --user-data-dir=/tmp/cdp-shot-$$ --window-size=1280,800 \
  --screenshot=/tmp/task1-tokens.png \
  "http://localhost:8792/bullion_mkultra.html"
```
Expected: near-black background (no navy, no visible star/nebula gradient texture), white/high-contrast borders wherever a panel border used to be subtle dark-gray, body text in a narrower/condensed sans than before. The 3D scene itself, the gold `<h1>Bullion</h1>` title, and any `var(--gold)`-colored data text are UNCHANGED at this point — only backgrounds/borders/base type shifted. Read the PNG to confirm visually, not just that the command exited 0.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 1/9: design tokens, base type, flatten starfield

New --accent (#ff3300) token for later tasks to adopt as the UI/brand
color, near-black background tokens, condensed-sans base font, and the
starfield's radial-gradient star/nebula texture flattened to a solid
fill -- gradients are explicitly disallowed by the brutalist direction.
--gold stays defined but is no longer used for UI chrome from here on,
only literal gold-price data text.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Global icon/emoji sweep

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (multiple non-contiguous spots, listed below)

**Interfaces:**
- Consumes: nothing new from Task 1.
- Produces: no emoji/pictographic-icon characters remain anywhere in the file except the news list's ▲▼ sentiment triangles (explicitly out of scope, spec's Decisions section) and the `#brand-mark` SVG logo / `#persona-orb`'s inline SVG (both bespoke vector graphics, not emoji).

This task deliberately SKIPS the 3 view-tab buttons (`bullion_mkultra.html:893-895`, currently `&#9673; 3D Map` / `&#9638; Overview` / `&#128200; Markets`) and the `#controls-drawer-btn`/`#audit-log-btn`/`#mode-toggle-btn` header buttons (`897`, `902`, `903`) — those get rewritten wholesale in Tasks 3 and 7 when their surrounding structure changes, so stripping their icons here would just be overwritten. Every other emoji/icon in the file is in scope.

- [ ] **Step 1: Strip icon glyphs from static button/label markup**

`bullion_mkultra.html:1067` — leave as-is: `&#x2197;` is a plain Unicode arrow (↗), not an emoji, matches the "plain Unicode glyph" exception already carved out for ▲▼.

`bullion_mkultra.html:2381` and `:3359` — both `badge.textContent = '✎';`. Change both to:
```js
badge.textContent = 'note';
```
(A plain-text tag reading "note" in the existing small `.fieldnote-badge`-style element, consistent with the brutalist system's preference for small uppercase text labels over pictographic glyphs. Check the CSS rule this badge uses — likely needs `text-transform: uppercase; font-size: 9px; letter-spacing: 0.08em;` added if not already present; search for the badge's class name at both call sites and confirm before assuming it needs new styling.)

`bullion_mkultra.html:1763` (a comment, not rendered — update for accuracy, not required for correctness):
```js
// Shared title text for the field-note discoverability badge ("note") — used on board cards,
```

- [ ] **Step 2: Strip icon glyphs from coach-mark body text**

`bullion_mkultra.html:3846`, inside a template string:
```js
'A <span style="color:var(--gold-dim)">&#9998;</span> next to a name means...'
```
becomes:
```js
'A <span style="color:var(--gold-dim)">note</span> tag next to a name means...'
```

`bullion_mkultra.html:3849`, inside a template string:
```js
'Ready for live market data, scenarios and sources? Open <b>&#9881; Tools</b>, top-right.'
```
becomes:
```js
'Ready for live market data, scenarios and sources? Open <b>Tools</b>, top-right.'
```

- [ ] **Step 3: Strip icon glyphs from live/pipeline status text**

`bullion_mkultra.html:5888`:
```js
el.textContent = liveNames.length ? `🕗 Showing ${selectedHistoryDate}` : `🕗 ${selectedHistoryDate} (no data, simulated)`;
```
becomes:
```js
el.textContent = liveNames.length ? `Showing ${selectedHistoryDate}` : `${selectedHistoryDate} (no data, simulated)`;
```

`bullion_mkultra.html:5890`:
```js
el.textContent = '⚪ Simulated';
```
becomes:
```js
el.textContent = 'Simulated';
```

`bullion_mkultra.html:6807`:
```js
bar.textContent = '⚠ ' + pipelineAlarmMessage(liveness, generatedAt);
```
becomes:
```js
bar.textContent = pipelineAlarmMessage(liveness, generatedAt);
```
(Check `#pipeline-alarm`'s CSS — it already renders on a distinct `rgba(224,177,90,0.16)` warm background with `color: var(--warn)`, so the color alone still signals "this is a warning" without the ⚠ glyph. If that visual distinction feels too quiet once the ⚠ is gone, add a `border-left: 3px solid var(--warn);` to `#pipeline-alarm` instead of restoring the emoji — decide by looking at the Task 1 screenshot's rendering of this bar, not in the abstract.)

- [ ] **Step 4: Strip icon glyphs from `provenanceBadgeText()`**

`bullion_mkultra.html:7005-7021`, four `return` statements in this function all get their leading emoji + space removed, text otherwise unchanged:
```js
function provenanceBadgeText(prov) {
  if (!prov || !prov.ok) return 'Simulated';
  const entries = Object.entries(prov.fields || {})
                        .filter(([, f]) => f.class === 'measured');
  if (!entries.length) return 'Simulated';
  const flagged = entries.filter(([, f]) => f.state === 'flagged').length;
  if (flagged) return 'Live · ' + flagged + ' of ' + entries.length + ' may be failing';
  if (entries.every(([, f]) => f.state === 'unknown')) {
    return 'Live · ' + entries.length + ' fields · freshness unknown';
  }
  const present = EXPECTED_MEASURED_FIELDS.filter(name =>
    prov.fields && prov.fields[name] && prov.fields[name].class === 'measured').length;
  if (present < EXPECTED_MEASURED_FIELDS.length) {
    const missingCount = EXPECTED_MEASURED_FIELDS.length - present;
    return 'Live · ' + present + ' of ' + EXPECTED_MEASURED_FIELDS.length
         + ' fields — ' + missingCount + ' missing';
  }
  return 'Live · ' + entries.length + ' fields current';
}
```
(Only the four `return` lines' leading `'⚪ '`/`'🟠 '`/`'🟢 '` literals are removed; every other character, including the rest of each string, stays exactly as it is today.)

- [ ] **Step 5: Screenshot and verify**

Re-run the Task 1 screenshot recipe (same server, new screenshot path `/tmp/task2-icons.png`). Confirm the header badge area (wherever `provenanceBadgeText()`'s output renders — check its call site if unsure) shows plain text with no emoji, and that the disclaimer/coach text (if visible without extra clicks) has no leftover `&#9998;`/`&#9881;` glyphs. Grep the file for the removed characters to catch anything missed:
```bash
grep -n '✎\|⚪\|🟠\|🟢\|🕗\|⚠' bullion-live-map/bullion_mkultra.html
```
Expected: no output (every one of those characters is gone from the file).

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 2/9: strip emoji/icon glyphs, plain text throughout

Removes pencil/gear/circle/clock/warning emoji from badge text, coach-mark
copy, and the live-data provenance status strings -- all of them were
decorating text that already said the same thing in words. Skips the 3
view-tab buttons and the Controls/Audit Log/Tools header buttons, which
get rebuilt in later tasks; skips the news list's plain-Unicode /\
sentiment triangles per the approved spec's explicit exception.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Nav shell — 3-tab restructure, `showView()` rewrite, `.btn`/`.tab` brutalist base

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:892-903` (`#header-controls` markup)
- Modify: `bullion-live-map/bullion_mkultra.html:122-129` (`.btn` base CSS)
- Modify: `bullion-live-map/bullion_mkultra.html:157-161` (`#view-tabs`/`.tab` CSS)
- Modify: `bullion-live-map/bullion_mkultra.html:3767-3805` (`showView()` and its tab click-handler wiring)

**Interfaces:**
- Consumes: `--accent` (Task 1).
- Produces: `showView(which)` now accepts exactly `'market' | 'analysis' | 'causal-link'` (renamed from today's `'3d' | 'board' | 'markets'`). Tasks 4-7 call `showView('market')`, `showView('analysis')`, `showView('causal-link')` respectively wherever the old view names were referenced (search the file for `showView('` after this task lands — Tasks 4/5/6/7 each need their own pass to catch every remaining old-name call site relevant to their surface, e.g. `render-fallback-btn`'s `showView('board')` call becomes part of Causal Link's internal toggle, not `showView()` at all — see Task 6).
- Produces: a `#causal-link-subview` internal toggle target (`'3d' | 'board'`) that Task 6/7 wire up — this task only reserves the DOM id and CSS class name so later tasks have a stable contract, it does not implement the toggle itself (Causal Link's default sub-view stays 3D per the spec, wired in Task 7 alongside the 3D chrome).

- [ ] **Step 1: Rewrite the tab bar markup**

Current (`bullion_mkultra.html:892-903`):
```html
      <div id="view-tabs" role="tablist" aria-label="View">
        <button class="btn tab active" id="tab-3d" role="tab" aria-selected="true">&#9673; 3D Map</button>
        <button class="btn tab" id="tab-board" role="tab" aria-selected="false">&#9638; Overview</button>
        <button class="btn tab" id="tab-markets" role="tab" aria-selected="false">&#128200; Markets</button>
      </div>
      <button class="btn adv-control" id="controls-drawer-btn" title="Open scenarios, metrics and AI analysis">&#9776; Controls</button>
      <button class="btn active adv-control" id="live-toggle-btn" title="Switch between live market data and the fully simulated baseline">Live Data</button>
      <button class="btn adv-control" id="expand-all-btn">Expand All</button>
      <button class="btn adv-control" id="collapse-all-btn">Collapse All</button>
      <button class="btn adv-control" id="reset-view-btn">Reset View</button>
      <button class="btn adv-control" id="audit-log-btn" title="Every causal number on this map, with its confidence tier and source">&#9888; Audit Log</button>
      <button class="btn active" id="mode-toggle-btn" title="Open the full analyst toolkit — live data, scenarios, metrics and sources. Click again to return to the simple view.">&#9881; Tools</button>
```

Replace the `#view-tabs` block only (leave `controls-drawer-btn`/`live-toggle-btn`/`expand-all-btn`/`collapse-all-btn`/`reset-view-btn`/`audit-log-btn`/`mode-toggle-btn` exactly where they are for now — Task 7 relocates/rewires them alongside the Causal Link 3D chrome, since `expand-all-btn`/`collapse-all-btn`/`reset-view-btn`/`live-toggle-btn`/`audit-log-btn` are all 3D-map/data-specific controls that belong under Causal Link once it's built, and moving them before Causal Link exists as a tab would leave them homeless):
```html
      <div id="view-tabs" role="tablist" aria-label="View">
        <button class="btn tab active" id="tab-market" role="tab" aria-selected="true">Market</button>
        <button class="btn tab" id="tab-analysis" role="tab" aria-selected="false">Analysis</button>
        <button class="btn tab" id="tab-causal-link" role="tab" aria-selected="false">Causal Link</button>
      </div>
```

Note this makes **Market** the default/first tab (`active`/`aria-selected="true"`) rather than today's 3D Map default. This is a deliberate consequence of the reordering, not called out explicitly in the spec — flag it in the PR/commit message (already done in Step 5's commit message below) so it's a visible, reviewable choice rather than a silent side effect. If the user wants Causal Link (carrying the 3D map) to stay the landing view, that's a one-line swap of which button carries `active`/`aria-selected="true"` plus which branch `showView()` defaults to in Step 3 below — flag this to the user when this task's commit is reviewed, don't decide it silently.

- [ ] **Step 2: Restyle `.btn` and the tab-segment CSS to brutalist**

Current (`bullion_mkultra.html:122-129`):
```css
  .btn {
    background: var(--bg-panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 6px 10px; font-size: 11px; cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    white-space: nowrap;
  }
  .btn:hover { background: #182034; border-color: #2a3352; }
  .btn.active { background: rgba(212,184,105,0.15); border-color: var(--gold-dim); color: var(--gold); }
```

Replace with:
```css
  .btn {
    background: var(--bg-panel2); color: var(--text); border: 1px solid var(--border);
    border-radius: 0; padding: 6px 10px; font-size: 11px; cursor: pointer;
    text-transform: uppercase; letter-spacing: 0.08em; font-weight: 700;
    transition: background 0.15s, color 0.15s;
    white-space: nowrap;
  }
  .btn:hover { background: #1a1a1a; }
  .btn.active { background: var(--accent); border-color: var(--accent); color: #fff; }
```

Current (`bullion_mkultra.html:157-161`):
```css
  #view-tabs { display: flex; margin-right: 4px; }
  #view-tabs .tab { border-radius: 0; }
  #view-tabs .tab:not(:first-child) { border-left: none; }
  #view-tabs .tab:first-child { border-radius: 6px 0 0 6px; }
  #view-tabs .tab:last-child { border-radius: 0 6px 6px 0; }
```

Replace with:
```css
  #view-tabs { display: flex; margin-right: 4px; border: 2px solid var(--border); }
  #view-tabs .tab { border: none; }
  #view-tabs .tab:not(:last-child) { border-right: 2px solid var(--border); }
```
(The `border-radius` rules are dropped entirely — `.btn`'s own `border-radius: 0` from above already covers the flat-corner requirement, and the per-tab radius overrides no longer apply to anything.)

- [ ] **Step 3: Rewrite `showView()` and its click-handler wiring**

Current (`bullion_mkultra.html:3767-3805`):
```js
function showView(which) {
  const is3d = which === '3d';
  const stageEl = document.getElementById('stage');
  stageEl.style.display = is3d ? '' : 'none';
  document.getElementById('board-view').hidden = which !== 'board';
  document.getElementById('markets-view').hidden = which !== 'markets';
  document.getElementById('legend-and-controls').hidden = !is3d;
  const tabs = { '3d': 'tab-3d', 'board': 'tab-board', 'markets': 'tab-markets' };
  for (const [name, id] of Object.entries(tabs)) {
    const el = document.getElementById(id);
    const active = name === which;
    el.classList.toggle('active', active);
    el.setAttribute('aria-selected', String(active));
  }
  const orb = document.getElementById('persona-orb');
  if (orb) {
    orb.classList.toggle('orb-docked', !is3d);
    (is3d ? stageEl : document.body).appendChild(orb);
  }
  if (is3d) Renderer.redraw();
}
document.getElementById('tab-3d').addEventListener('click', () => showView('3d'));
document.getElementById('tab-markets').addEventListener('click', () => showView('markets'));
document.getElementById('tab-board').addEventListener('click', () => showView('board'));
```

Replace with:
```js
// causalLinkSubView tracks which of Causal Link's two internal renderings
// (3D constellation, default; 2D board, secondary) is showing -- Task 7
// wires the toggle button that changes this; this task only introduces the
// variable and the branch so 'causal-link' has somewhere concrete to read
// from immediately, rather than leaving showView() half-built until Task 7.
let causalLinkSubView = '3d';

function showView(which) {
  const showCausal3d = which === 'causal-link' && causalLinkSubView === '3d';
  const stageEl = document.getElementById('stage');
  stageEl.style.display = showCausal3d ? '' : 'none';
  document.getElementById('board-view').hidden = !(which === 'causal-link' && causalLinkSubView === 'board');
  document.getElementById('markets-view').hidden = which !== 'market';
  document.getElementById('analysis-view').hidden = which !== 'analysis';
  document.getElementById('legend-and-controls').hidden = !showCausal3d;
  const tabs = { 'market': 'tab-market', 'analysis': 'tab-analysis', 'causal-link': 'tab-causal-link' };
  for (const [name, id] of Object.entries(tabs)) {
    const el = document.getElementById(id);
    const active = name === which;
    el.classList.toggle('active', active);
    el.setAttribute('aria-selected', String(active));
  }
  const orb = document.getElementById('persona-orb');
  if (orb) {
    orb.classList.toggle('orb-docked', !showCausal3d);
    (showCausal3d ? stageEl : document.body).appendChild(orb);
  }
  if (showCausal3d) Renderer.redraw();
}
document.getElementById('tab-market').addEventListener('click', () => showView('market'));
document.getElementById('tab-analysis').addEventListener('click', () => showView('analysis'));
document.getElementById('tab-causal-link').addEventListener('click', () => showView('causal-link'));
```

Note `#analysis-view` (referenced above) does not exist as an element yet — Task 5 creates it. Until Task 5 lands, `document.getElementById('analysis-view').hidden = ...` will throw on every `showView()` call once `tab-analysis` is clickable, so this task's `#header-controls` markup from Step 1 must NOT yet make `tab-analysis` reachable in a way that breaks the page. Handle this by guarding the line defensively in this task and removing the guard in Task 5:
```js
  const analysisEl = document.getElementById('analysis-view');
  if (analysisEl) analysisEl.hidden = which !== 'analysis';
```
Task 5, Step 3 removes this guard once `#analysis-view` is real (search for this exact guarded line and replace it with the unguarded version from the snippet above).

- [ ] **Step 4: Fix the one other `showView()` call site**

`bullion_mkultra.html:2161` currently reads:
```js
document.getElementById('render-fallback-btn').addEventListener('click', () => showView('board'));
```
This button is the WebGL-unavailable fallback prompt ("switch to the 2D board"). Update it to reflect the new state model:
```js
document.getElementById('render-fallback-btn').addEventListener('click', () => {
  causalLinkSubView = 'board';
  showView('causal-link');
});
```

- [ ] **Step 5: Screenshot and verify**

Re-run the screenshot recipe. Confirm: 3 tabs read "Market" / "Analysis" / "Causal Link" in the condensed uppercase brutalist style, flat corners, a 2px border frame around the tab group with a 2px divider between tabs, active tab filled solid `#ff3300`. Click each tab via the CDP probe (`document.querySelector('#tab-analysis').click()` etc. — see the Fed-odds card's probe script for the pattern) and confirm no JS console errors (Task 5 hasn't built `#analysis-view` yet, so clicking Analysis is expected to show a guarded-empty panel, not throw — verify the guard from Step 3 actually prevents an exception).

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 3/9: 3-tab nav shell (Market/Analysis/Causal Link)

Collapses the 4-destination nav (3D Map/Overview/Markets/Tools-drawer)
into 3 top-level tabs. showView() now keys off 'market'/'analysis'/
'causal-link' instead of '3d'/'board'/'markets'; Causal Link carries an
internal 3D-vs-2D sub-view (causalLinkSubView) wired fully in a later
task. .btn/.tab base CSS goes flat-cornered with a solid #ff3300 active
state, replacing the rounded gold-tinted look.

NOTE: this makes Market the default landing tab (was 3D Map) as a direct
consequence of tab order -- flagging for review, not a silent decision.

#analysis-view doesn't exist until the Analysis-tab task lands; showView()
guards that lookup until then so Market/Causal Link stay fully functional
in the meantime.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Market tab restyle

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:191-221` (Markets-tab CSS block, incl. `.market-card`)
- Modify: `bullion-live-map/bullion_mkultra.html` — the `fed-odds-card`/`fed-odds-*` CSS block added 2026-09-08 (search `.fed-odds-card` to locate; it sits immediately before `#markets-news` in the same stylesheet region)
- Modify: `bullion-live-map/bullion_mkultra.html` — `buildMarketIndexCard()` (search `function buildMarketIndexCard`) to add the functional-Δ prefix to its change indicator

**Interfaces:**
- Consumes: `--accent`, `--font-display` (italic Δ), condensed base font (Task 1); `.btn` brutalist base (Task 3, for any buttons inside this tab).
- Produces: a reusable `.hero-stat` / `.hero-stat-ghost` CSS pattern (oversized number + ghosted background Δ) that Tasks 5 and 7 each apply to their own tab's hero stat (Analysis's health-score number, Causal Link's node-count or similar) — defined once here, reused by class name rather than redefined per tab.

- [ ] **Step 1: Restyle `.market-card` to flat/ruled**

Current (`bullion_mkultra.html:198-214`, the relevant subset):
```css
  .market-card {
    flex: 1 1 220px; min-width: 200px; max-width: 320px;
    display: block; background: var(--bg-panel2); color: var(--text);
    border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px;
    text-decoration: none; cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .market-card:hover { background: #182034; border-color: #2a3352; }
  .market-card-name {
    font-size: 12px; font-weight: 700; letter-spacing: 0.06em;
    text-transform: uppercase; color: var(--gold); margin-bottom: 6px;
  }
  .market-card-value { font-size: 26px; font-weight: 700; line-height: 1.1; }
  .market-card-change { font-size: 13px; font-weight: 600; margin-top: 2px; }
```

Replace with:
```css
  .market-card {
    flex: 1 1 220px; min-width: 200px; max-width: 320px;
    display: block; background: var(--bg-panel); color: var(--text);
    border: none; border-top: 3px solid #fff; border-radius: 0; padding: 16px 18px 12px;
    text-decoration: none; cursor: pointer;
    transition: background 0.15s;
    position: relative; overflow: hidden;
  }
  .market-card:hover { background: #161616; }
  .market-card-name {
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em;
    text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;
  }
  .market-card-value { font-size: 46px; font-weight: 800; line-height: 0.95; }
  .market-card-change { font-size: 13px; font-weight: 700; margin-top: 4px; }
  .market-card-change::before { content: "\0394 "; font-family: var(--font-display); font-style: italic; }
```
(`.market-card-value` jumps from 26px to 46px to match the spec's "extreme type-scale contrast" rule against the now-11px label — this is the oversized-numeral treatment applied to the existing index cards. `.market-card-change::before` is the functional-Δ prefix: every price-change percentage in this tab now literally reads "Δ +0.8%" instead of "+0.8%".)

`.market-card-change.up`/`.market-card-change.down` (further down in the same CSS block, not shown above — locate and confirm) keep their existing `var(--green)`/`var(--red)` coloring; leave those two rules untouched, only the base `.market-card-change` rule above changes.

- [ ] **Step 2: Add the `.hero-stat`/`.hero-stat-ghost` reusable pattern**

Add this new CSS block immediately after the `.market-card-change` rules from Step 1 (this is the general-purpose version of the "oversized number + ghosted Δ" pattern shown in the approved mockup — Task 4 defines it once here since Market is the first tab built against it, Tasks 5 and 7 reuse the same two class names for their own hero stats rather than redefining the pattern):
```css
  .hero-stat { position: relative; overflow: hidden; padding: 4px 0; }
  .hero-stat-ghost {
    position: absolute; right: -6px; top: -14px; font-size: 96px; font-weight: 400;
    font-family: var(--font-display); font-style: italic; color: #fff; opacity: 0.07;
    line-height: 1; pointer-events: none; z-index: 0;
  }
  .hero-stat > * { position: relative; z-index: 1; }
```

- [ ] **Step 3: Apply the ghost-Δ to the Fed-odds card's headline number**

Locate `.fed-odds-card`'s CSS (added 2026-09-08, immediately before `#markets-news`) and its corresponding JS in `buildFedOddsCard()`. Wrap the existing headline text in a `.hero-stat` container with a ghost Δ, matching the pattern from Step 2. In `buildFedOddsCard()`, find:
```js
  const headline = document.createElement('div');
  headline.className = 'fed-odds-headline';
  headline.textContent = fedOddsHeadline(kalshi, polymarket);
  card.appendChild(headline);
```
Wrap it:
```js
  const heroWrap = document.createElement('div');
  heroWrap.className = 'hero-stat';
  const ghost = document.createElement('span');
  ghost.className = 'hero-stat-ghost';
  ghost.textContent = 'Δ';
  ghost.setAttribute('aria-hidden', 'true');
  heroWrap.appendChild(ghost);
  const headline = document.createElement('div');
  headline.className = 'fed-odds-headline';
  headline.textContent = fedOddsHeadline(kalshi, polymarket);
  heroWrap.appendChild(headline);
  card.appendChild(heroWrap);
```
Also restyle `.fed-odds-card`'s own container rule (rounded/bordered today, matching `.market-card`'s old look) the same way `.market-card` was restyled in Step 1: `border-radius: 0`, `border-top: 3px solid #fff` in place of the all-around 1px border, background `var(--bg-panel)`.

- [ ] **Step 4: Restyle the news list**

`#news-list` currently has `border: 1px solid var(--border); border-radius: 8px;` (search `#news-list {` in the Markets-tab CSS block) — change to `border: none; border-top: 3px solid #fff; border-radius: 0;`, matching the other two restyled cards. Leave `.news-category`'s `border-left: 3px solid var(--cat-color, ...)` untouched — the per-category color coding is a functional signal (matches `CATEGORY_COLOR`), not decorative chrome, and isn't part of this redesign's scope. Leave the ▲▼ sentiment glyphs untouched per the spec's explicit exception.

- [ ] **Step 5: Screenshot and verify**

Re-run the screenshot recipe, navigate to the Market tab (`document.querySelector('#tab-market').click()`). Confirm: index cards and the Fed-odds card show oversized bold numerals against tiny uppercase labels, flat top-rule borders (no rounded corners, no all-around border), the price-change indicators read "Δ +N%"/"Δ -N%", and a faint ghosted Δ sits behind the Fed-odds headline. Confirm no console errors.

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 4/9: Market tab brutalist restyle

Index cards, Fed-odds card and the news list all move from rounded
all-around borders to flat top-rule dividers with oversized numerals.
Price-change values now read "Δ +N%" (functional italic-Greek-delta
prefix). Introduces the reusable .hero-stat/.hero-stat-ghost pattern
(oversized stat + faded background Δ) that later tasks reuse for
Analysis's health score and Causal Link's hero number rather than
redefining it per tab.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Analysis tab — promote the drawer to a real tab

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:972-1071+` (the `#control-drawer` markup — read the full drawer through its closing tag before starting; the excerpt seen during planning ran through line 1071 but the element continues further, confirm the true end before editing)
- Modify: CSS for `#control-drawer`/`#drawer-header`/`#drawer-body` (search these ids; today's rules implement a slide-out panel — `transform`/`position: fixed` mechanics — that need to become a normal static in-flow tab panel)
- Modify: `bullion-live-map/bullion_mkultra.html` — `function showView` guard from Task 3, Step 3 (remove the guard)
- Modify: `bullion-live-map/bullion_mkultra.html:6364` (`controls-drawer-btn` click handler and `openDrawer`/`closeDrawer` functions — search for their definitions)

**Interfaces:**
- Consumes: `.hero-stat`/`.hero-stat-ghost` (Task 4), `.btn` brutalist base (Task 3), `--accent` (Task 1).
- Produces: `#analysis-view`, a new top-level `role="tabpanel"` sibling of `#markets-view`/`#board-view`, containing everything that used to be `#drawer-body`'s children. `showView('analysis')` (already wired in Task 3) now has a real element to toggle.

- [ ] **Step 1: Read the full drawer before editing**

```bash
grep -n '<div id="control-drawer"' bullion-live-map/bullion_mkultra.html
grep -n '</div>' bullion-live-map/bullion_mkultra.html | awk -F: '$1 > 973' | head -40
```
Use this to find the drawer's true closing `</div>`, then read the full range with the Read tool before making any edit — the excerpt gathered during planning (lines 972-1071) covers the scenario simulator, manual-drivers section, live-metrics grid, and the start of the macro-analysis/health-score section, but not confirmed to be the complete element. Do not truncate content when moving it.

- [ ] **Step 2: Convert the drawer markup into a tab panel**

Change the opening wrapper from:
```html
<!-- ── Control drawer: scenarios, live metrics, glossary, AI analysis ── -->
<div id="control-drawer">
  <div id="drawer-header">
    <div class="dh-title">Scenarios &amp; Analysis</div>
    <button id="drawer-close" aria-label="Close">&times;</button>
  </div>
  <div id="drawer-body">
```
to:
```html
<div id="analysis-view" role="tabpanel" aria-label="Analysis" hidden>
```
Remove the `#drawer-header` block entirely (its title/close-button made sense for a slide-out panel; a tab panel doesn't need an in-panel close button — closing now just means clicking a different tab, same as Market/Causal Link). Keep every child of `#drawer-body` (scenario grid, manual-drivers section, live-metrics grid, macro-analysis/health-score section, and whatever else Step 1 revealed past line 1071) exactly as-is, just re-parented directly under the new `#analysis-view` instead of under `#drawer-body`. Change the drawer's closing tags (`</div></div>` for `#drawer-body`/`#control-drawer`) to a single `</div>` for `#analysis-view`.

- [ ] **Step 3: Remove the Task 3 guard now that `#analysis-view` is real**

In `showView()`, find:
```js
  const analysisEl = document.getElementById('analysis-view');
  if (analysisEl) analysisEl.hidden = which !== 'analysis';
```
Replace with the unguarded version:
```js
  document.getElementById('analysis-view').hidden = which !== 'analysis';
```

- [ ] **Step 4: Retire the drawer's open/close JS, repoint `controls-drawer-btn`**

Find `openDrawer`/`closeDrawer` (or equivalently-named functions — search `function openDrawer\|function closeDrawer\|classList.*drawer.*open` for the actual names) and the `controls-drawer-btn` click listener at `bullion_mkultra.html:6364`. The slide-out open/close animation logic (adding/removing an `.open` class that drove the `transform`) is no longer meaningful once `#analysis-view` is a plain tab panel — replace the click handler:
```js
document.getElementById('controls-drawer-btn').addEventListener('click', openDrawer);
```
with:
```js
document.getElementById('controls-drawer-btn').addEventListener('click', () => showView('analysis'));
```
Delete the now-unused `openDrawer`/`closeDrawer` function bodies and the `#drawer-close` click listener (search for it) — confirm via `grep -n "openDrawer\|closeDrawer\|drawer-close"` that nothing else in the file still calls them before deleting; if something else does, keep the functions but have them call `showView('analysis')` instead of toggling the old `.open` class.

Leave `controls-drawer-btn` itself where it is in the header for this task (still inside `.adv-control`, still hidden in beginner mode) — Task 7 is where it and its sibling `.adv-control` buttons get their final placement inside Causal Link's chrome or wherever they land; this task only makes clicking it switch to the Analysis tab instead of opening a drawer.

- [ ] **Step 5: Convert `#control-drawer`'s CSS from slide-out panel to static tab panel**

Find the CSS rules for `#control-drawer` (the `position: fixed`/`transform`/`.open` mechanics) and `#drawer-body` (scroll/padding). Replace the id selector `#control-drawer` with `#analysis-view` throughout that CSS block, and remove the `position: fixed`, `transform`, `right`/`left`, `.open`/`transition` rules that implemented the slide animation — `#analysis-view` should lay out the same way `#markets-view`/`#board-view` already do (`flex: 1 1 auto; overflow: auto; padding: ...`), matching `#markets-view`'s existing rule (`bullion_mkultra.html:192-196`) as the pattern to follow rather than inventing new layout rules. Apply the `.hero-stat`/`.hero-stat-ghost` pattern from Task 4 to the health-score number (`#health-num`) the same way it was applied to the Fed-odds headline — wrap it and add a ghost Δ span.

- [ ] **Step 6: Screenshot and verify**

Re-run the screenshot recipe, click `#tab-analysis`. Confirm: the scenario buttons, manual-driver sliders, live-metrics grid, and health-score/narrative section all render as a normal static page (not a slide-out panel — no leftover `transform`/animation), the health-score number has a ghosted Δ behind it, and clicking `#controls-drawer-btn` (if visible — it's still `.adv-control`, so only visible in advanced mode; toggle `#mode-toggle-btn` first if needed) switches to the Analysis tab rather than opening anything separate. Confirm no console errors, and specifically confirm `openDrawer`/`closeDrawer` deletion didn't leave a dangling reference by checking the console for `ReferenceError`.

- [ ] **Step 7: Run the existing test suite**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -20
```
Expected: same pass count as before this task (this change doesn't touch anything the Python suite asserts on, but confirm nothing regressed before committing).

- [ ] **Step 8: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 5/9: Analysis tab (drawer -> real tab panel)

The Tools drawer's content (scenario simulator, manual driver sliders,
live-metrics grid, health score, narrative, backtest) becomes a normal
static tab panel (#analysis-view) instead of a slide-out drawer.
controls-drawer-btn now switches tabs instead of opening a panel;
openDrawer/closeDrawer and their slide-animation CSS are retired.
Health-score number gets the .hero-stat ghost-Delta treatment from the
Market tab task.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Causal Link — 2D board re-skin

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:163-189` (`#board-view`, `.board-col`, `.board-col-head`, `.board-card` CSS)
- Modify: `bullion-live-map/bullion_mkultra.html:927` (`#board-view` markup — no structural change needed, only its parent's tab association)

**Interfaces:**
- Consumes: `.hero-stat` pattern (Task 4, if a hero number is added to the board — optional, see Step 2), `--accent` (Task 1).
- Produces: nothing new consumed by later tasks — Task 7 is independent of this one and could in principle ship first; kept in this order only because the spec lists 2D-board-reskin before 3D-chrome in its phase list.

- [ ] **Step 1: Restyle the board columns and cards**

Current (`bullion_mkultra.html:171-189`):
```css
  .board-col { flex: 1 0 150px; min-width: 150px; max-width: 240px; display: flex; flex-direction: column; gap: 8px; }
  .board-col-head {
    font-size: 11px; font-weight: 700; letter-spacing: 0.08em; color: var(--gold);
    text-align: center; padding: 5px 8px; border-radius: 999px; text-transform: uppercase;
    background: rgba(8,10,18,0.82); border: 1px solid rgba(212,184,105,0.35);
    position: sticky; top: 0; z-index: 1;
  }
  .board-card {
    display: block; width: 100%; text-align: left;
    background: var(--bg-panel2); color: var(--text);
    border: 1px solid var(--border); border-left-width: 4px;
    border-radius: 6px; padding: 7px 9px; font-size: 12px; cursor: pointer;
    transition: background 0.15s, border-color 0.15s, opacity 0.32s ease;
  }
  .board-card:hover { background: #182034; border-color: #2a3352; }
  .board-card.hub { font-weight: 700; }
  .board-card.dimmed { opacity: 0.12; }
```

Replace with:
```css
  .board-col { flex: 1 0 150px; min-width: 150px; max-width: 240px; display: flex; flex-direction: column; gap: 6px; }
  .board-col-head {
    font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #fff;
    text-align: center; padding: 5px 8px; border-radius: 0; text-transform: uppercase;
    background: #000; border: none; border-bottom: 2px solid var(--accent);
    position: sticky; top: 0; z-index: 1;
  }
  .board-card {
    display: block; width: 100%; text-align: left;
    background: var(--bg-panel); color: var(--text);
    border: none; border-left: 3px solid var(--border);
    border-radius: 0; padding: 7px 9px; font-size: 12px; cursor: pointer;
    transition: background 0.15s, opacity 0.32s ease;
  }
  .board-card:hover { background: #161616; }
  .board-card.hub { font-weight: 700; border-left-color: var(--accent); }
  .board-card.dimmed { opacity: 0.12; }
```
(`.board-col-head`'s old `rgba(8,10,18,0.82)`/gold-tinted-border look becomes solid black with a bottom accent rule — same "section header as a hard divider, not a soft pill" treatment used for `.market-card-name` in Task 4. `.board-card`'s per-card colored left-border, which today signals node group/layer via inline `style` — confirm this is set inline per-card in the JS that builds these cards (search `board-card` in JS, likely near `buildBoard()`) rather than in this CSS block; if so, leave that per-node-group coloring logic untouched, it's functional signal like the news categories' `--cat-color`, not decorative chrome.)

- [ ] **Step 2 (optional, confirm with a screenshot before deciding): add a hero stat to the board header**

If `#board-view` has an obvious single summary number worth foregrounding (e.g. a node/link count shown elsewhere already — check the 3D map's own header area for a pattern to mirror, search for `NODES.length` usage near the board-building code), wrap it in `.hero-stat`/`.hero-stat-ghost` the same way Tasks 4 and 5 did. If no such number exists in the board view today, skip this step — do not invent new content to force the pattern in; the spec's hero-stat requirement was about each TAB having one, and Causal Link's hero stat can live in the 3D chrome instead (Task 7) rather than needing one in both its sub-views.

- [ ] **Step 3: Screenshot and verify**

Re-run the screenshot recipe. Get to the 2D board via the CDP probe by directly invoking the fallback path added in Task 3 (`document.querySelector('#render-fallback-btn').click()` if visible, or set `causalLinkSubView = 'board'` via `Runtime.evaluate` then call `showView('causal-link')`, since no dedicated 2D/3D toggle button exists until Task 7). Confirm: column headers are solid black with a bottom accent rule, cards have a flat left-border accent (no rounded corners, no all-around subtle border), hover state is a flat near-black fill with no border-color animation.

- [ ] **Step 4: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 6/9: Causal Link 2D board brutalist re-skin

Board column headers and node cards move from rounded/gold-tinted/
translucent styling to flat black headers with a solid accent
underline and flat left-border-accented cards. Per-node-group left-
border coloring (functional signal, not decoration) is untouched.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Causal Link — 3D chrome restyle + relocate Live Data/Expand/Collapse/Reset/Audit Log

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:938-965` (`#detail-panel`, `#legend-and-controls` markup/CSS)
- Modify: `bullion-live-map/bullion_mkultra.html:892-903` area — relocate `controls-drawer-btn` removal artifact and `live-toggle-btn`/`expand-all-btn`/`collapse-all-btn`/`reset-view-btn`/`audit-log-btn`/`mode-toggle-btn` into Causal Link's own chrome
- Modify: `bullion-live-map/bullion_mkultra.html:6176+` (`openAuditLog()`'s own inline-styled popup document — light token pass, not a rebuild)
- Add: a 3D/2D sub-view toggle inside `#causal-link` chrome (the reserved contract from Task 3)

**Interfaces:**
- Consumes: `.hero-stat` (Task 4), `causalLinkSubView` variable and `showView()` (Task 3).
- Produces: nothing new consumed by later tasks (Task 8 is a whole-app sweep, doesn't depend on this task's internals beyond it being done).

- [ ] **Step 1: Add a 3D/2D toggle and relocate the 3D-specific header buttons**

Currently `live-toggle-btn`/`expand-all-btn`/`collapse-all-btn`/`reset-view-btn`/`audit-log-btn` live in `#header-controls`, global to every tab (hidden via `.adv-control` in beginner mode, but present in the header regardless of which tab is active once in advanced mode — confirm this is actually true by checking whether `#header-controls` is a sibling of `#view-tabs` inside the always-visible `#header`, which the markup read during planning confirms it is). Move all five buttons (plus a new toggle button) out of `#header-controls` and into a new small toolbar rendered only when Causal Link is the active tab. Add this markup immediately before `#board-view` (`bullion_mkultra.html:927`):
```html
<div id="causal-link-toolbar" hidden>
  <button class="btn" id="causal-subview-toggle">2D</button>
  <button class="btn active adv-control" id="live-toggle-btn" title="Switch between live market data and the fully simulated baseline">Live Data</button>
  <button class="btn adv-control" id="expand-all-btn">Expand All</button>
  <button class="btn adv-control" id="collapse-all-btn">Collapse All</button>
  <button class="btn adv-control" id="reset-view-btn">Reset View</button>
  <button class="btn adv-control" id="audit-log-btn" title="Every causal number on this map, with its confidence tier and source">Audit Log</button>
</div>
```
Remove these same five `<button>` elements from `#header-controls` (`bullion_mkultra.html:898-902`) — do not duplicate the ids. `controls-drawer-btn` and `mode-toggle-btn` stay in `#header-controls` (they're not Causal-Link-specific: `controls-drawer-btn` now routes to the Analysis tab per Task 5, and `mode-toggle-btn` is the global beginner/advanced toggle, relevant everywhere).

- [ ] **Step 2: Wire the toggle and toolbar visibility into `showView()`**

In `showView()`, add toolbar visibility alongside the existing tab-panel visibility lines:
```js
  document.getElementById('causal-link-toolbar').hidden = which !== 'causal-link';
```
Add the toggle's click handler (near the other tab click handlers from Task 3):
```js
document.getElementById('causal-subview-toggle').addEventListener('click', () => {
  causalLinkSubView = causalLinkSubView === '3d' ? 'board' : '3d';
  document.getElementById('causal-subview-toggle').textContent = causalLinkSubView === '3d' ? '2D' : '3D';
  showView('causal-link');
});
```
(Button label always names the view you'd switch TO, not the one you're on — "2D" while viewing 3D, "3D" while viewing 2D. Initialize its `textContent` to `'2D'` in the markup from Step 1, matching `causalLinkSubView`'s default of `'3d'`.)

Also update Task 3's `render-fallback-btn` handler, which sets `causalLinkSubView = 'board'` directly — after this task, also flip the toggle button's own label to stay in sync:
```js
document.getElementById('render-fallback-btn').addEventListener('click', () => {
  causalLinkSubView = 'board';
  document.getElementById('causal-subview-toggle').textContent = '3D';
  showView('causal-link');
});
```

- [ ] **Step 3: Restyle `#detail-panel` and `#legend-and-controls`**

Read the full CSS rules for `#detail-panel` and `#legend-and-controls` (search both ids; not fully captured during planning) before editing. Apply the same transformation pattern used in every prior task: replace `border-radius` with `0`, replace all-around subtle borders with a single flat accent-colored rule line on one edge (top or left, whichever matches the panel's slide-in direction if it has one), replace any `rgba(212,184,105,...)` gold-tinted translucent backgrounds with solid `var(--bg-panel)` or `#000`. Apply `.hero-stat`/`.hero-stat-ghost` to `#detail-title` if the detail panel has a single prominent number worth foregrounding this way (it likely doesn't — `#detail-title` is a node NAME, not a stat — skip if so, don't force it).

- [ ] **Step 4: Light token pass on the Audit Log popup document**

`openAuditLog()` (`bullion_mkultra.html:6176+`) writes a completely separate HTML document via `window.open()` with its own hardcoded inline `<style>` (`body{background:#0d1117;color:#c9d1d9;...}`, confirmed during planning). This is NOT part of the main page's DOM and does not inherit `:root` CSS variables. Do a literal find-and-replace within that inline style string only (do not restructure the audit log's content or layout, which is unrelated to this redesign's scope):
- `background:#0d1117` → `background:#000`
- Any accent/link color in that inline stylesheet currently using a gold-ish hex (check the full style string past what was read during planning) → `#ff3300`
- Leave the `measured`/`directional`/`unverified` confidence-tier colors (`.seg.measured`/`.seg.directional`/`.seg.unverified` and their `<b>` equivalents, likely green/amber/red) untouched — those are functional data-encoding colors, not brand chrome, same reasoning as the news category colors and board-card group colors left alone in Tasks 4 and 6.

- [ ] **Step 5: Screenshot and verify**

Re-run the screenshot recipe, click `#tab-causal-link`. Confirm: the toolbar (2D/3D toggle, Live Data, Expand/Collapse/Reset, Audit Log) appears only on this tab (click Market or Analysis and confirm it disappears), toggling 2D/3D actually switches `#board-view`/`#stage` visibility and updates the button label, and `#detail-panel`/`#legend-and-controls` (click a node to open the detail panel) show flat brutalist styling. Click `#audit-log-btn` and confirm the popup opens with the updated dark palette (this may require handling the popup as a new CDP target — if the probe template's single-target assumption makes this awkward, a plain screenshot of the main page after confirming the button exists and is wired (no console error on click) is an acceptable fallback for this specific sub-check; note in the commit message if the popup itself wasn't visually re-screenshotted).

- [ ] **Step 6: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 7/9: Causal Link 3D chrome + control relocation

Live Data/Expand All/Collapse All/Reset View/Audit Log move out of the
always-present header into a toolbar that only shows on the Causal Link
tab, alongside a new 2D/3D sub-view toggle. detail-panel and legend-and-
controls get the flat brutalist treatment. The Audit Log's separate
popup document (window.open, its own inline stylesheet, never inherited
:root variables) gets a light token pass -- background and accent color
only, confidence-tier data colors left untouched.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: Consistency pass — disclaimer modal, coach marks, remaining chrome

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html:7076+` (`#disclaimer-overlay`/`#disclaimer-modal`)
- Modify: `bullion-live-map/bullion_mkultra.html:908-914` (`#coach` — coach-mark tour bubble)
- Modify: `bullion-live-map/bullion_mkultra.html:565-573` and `3820-3890` (beginner-mode CSS comments/`mode-toggle-btn` styling — visual only, per Global Constraints keep its behavior identical)
- Modify: any remaining spot flagged by a fresh full-file grep in Step 1 below

**Interfaces:**
- Consumes: everything from Tasks 1-7. This task adds nothing new for later consumption — it's the last content task before Task 9's pure-verification pass.

- [ ] **Step 1: Grep for anything still using the old visual language**

```bash
grep -n "border-radius: [1-9]\|rgba(212,184,105\|var(--gold)" bullion-live-map/bullion_mkultra.html | grep -v "data\|literal\|GOLD\|gold_px\|m-gold\|gold-price\|#header h1"
```
(This is a starting filter, not exhaustive — read each hit and judge case-by-case: `var(--gold)` on an element displaying the literal word/price "GOLD" is correct and stays; `var(--gold)` on a button/border/active-state is a leftover that should become `var(--accent)`; a `border-radius` on something clearly decorative rather than functional should go to `0`. Don't blanket-replace without reading each hit — this project's own `#header h1` gold title color, for instance, is arguably fine to keep gold since "Bullion" as a wordmark is literal brand-name-as-data in the same spirit as the "GOLD" price text, but confirm this reads intentionally rather than inconsistently once seen in the Step 3 screenshot; it's a judgment call not resolved by the spec, flag it in the commit message either way.)

- [ ] **Step 2: Restyle the disclaimer modal and coach-mark bubble**

Read both elements' full CSS (search `#disclaimer-modal`, `#coach`) before editing — neither was fully captured during planning. Apply the same established pattern: flat corners, solid rule-line borders/dividers instead of soft rounded panels, `var(--accent)` in place of any gold/blue brand-colored buttons or highlights inside them. The coach-mark's dot-progress indicator (`.coach-dot`/`.coach-dot.on`, referenced in the markup at line 910) likely uses a rounded-pill style — flatten to small square or line-segment indicators consistent with the rest of the redesign, but do not change `renderCoach()`'s logic, timing, or copy (out of scope — see Global Constraints on the coach tour's behavior).

- [ ] **Step 3: Full-app screenshot sweep**

Screenshot all three tabs (Market, Analysis, Causal Link in both 3D and 2D sub-views), the detail panel open on a node, the disclaimer modal, and the coach-mark bubble (trigger it if it doesn't appear automatically — check `coachDone`/`localStorage` gating logic found near `renderCoach()` and reset it via the CDP probe's `evalJS` if needed to force it visible for the screenshot). Confirm the whole app now reads as one coherent visual system — no leftover rounded card, no leftover gold-as-UI-accent, no leftover emoji anywhere (re-run the Task 2 grep for emoji characters as a final confirmation across the whole file, not just the spots targeted in Task 2).

- [ ] **Step 4: Commit**

```bash
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 8/9: consistency pass (disclaimer, coach marks)

Sweeps the disclaimer modal and coach-mark tour bubble to the flat
brutalist system, and fixes any remaining rounded-corner/gold-as-accent
leftovers found by a full-file grep. Coach-mark tour behavior, timing
and copy are unchanged -- visual treatment only.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8b: Analysis-tab and detail-panel internals restyle

**Added 2026-09-11**, mid-execution, after Task 8's review surfaced this gap (see the plan-level Amendment note above). Not part of the original 9-task sequence — inserted between Task 8 and Task 9 because Task 9 has no code-change mechanism and would ship this gap otherwise.

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (CSS only — every selector below, all inside the existing stylesheet block; no markup or JS changes)

**Interfaces:**
- Consumes: `--accent`, `--bg-panel`, `--bg-deep`, `--border`, `--text`, `--text-dim` (Task 1). No new tokens introduced.
- Produces: nothing consumed by later tasks — this is a leaf CSS-only task.

This task restyles CSS that has existed, untouched, since before this redesign began — none of it was ever in any prior task's scope (Task 5 was explicitly a container-only conversion; Task 7 was explicitly scoped to container ids only). Two categories of selector appear below: **restyle** (card/button/panel chrome — the redesign's actual target) and **leave alone, confirmed functional** (confidence-tier indicator colors, already-established exceptions elsewhere in this plan for the exact same color family — do not "fix" these, they are correct as-is and flattening/recoloring them would be a *new* defect, not a fix).

- [ ] **Step 1: `.run-btn`'s sibling `.spinner` — the one parked item from Task 8's re-review**

Current (`bullion_mkultra.html:726`):
```css
  .spinner { display: inline-block; width: 12px; height: 12px; border: 1.5px solid var(--border); border-top-color: var(--gold); border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }
```
Change only `border-top-color`:
```css
  .spinner { display: inline-block; width: 12px; height: 12px; border: 1.5px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.7s linear infinite; flex-shrink: 0; }
```
(The `border-radius: 50%` stays — a loading spinner's circular shape is the established "functional shape" exception, same as the small indicator dots elsewhere in this file. Only its color was gold-as-accent; that's what's being fixed.)

- [ ] **Step 2: `#analysis-view` scenario/metrics chrome — flatten to the file's zero-radius convention**

Current (`bullion_mkultra.html:660-667`, `:684`, `:693-694`):
```css
  select.scenario-select {
    /* ...existing declarations, confirm exact current content before editing... */
  }
  select.scenario-select optgroup { background: var(--bg-panel); color: var(--gold-dim); font-style: normal; }
  select.scenario-select option { background: var(--bg-panel); color: var(--text); }
  select.scenario-select.active {
    /* ... */
  }
  .metrics-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; background: var(--border); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
  .drawer-tag { font-size: 10px; padding: 2px 8px; border-radius: 10px; background: var(--bg-panel2); color: var(--gold); border: 1px solid var(--border); cursor: pointer; }
  .drawer-tag:hover { border-color: var(--gold-dim); }
```
Read `select.scenario-select`'s and `select.scenario-select.active`'s full current declarations before editing (not fully captured during planning) — then apply, to every rule in this step: `border-radius: 0` everywhere one currently appears (`.metrics-grid`, `.drawer-tag`, and `select.scenario-select` if it has one), and swap `.drawer-tag`'s `color: var(--gold)` / `:hover`'s `border-color: var(--gold-dim)` to `var(--accent)` (it's a clickable show/hide toggle, squarely "buttons/nav/active-states" per the Global Constraint). Leave `select.scenario-select optgroup`'s `color: var(--gold-dim)` as a judgment call matching this task's own `#header h1` precedent from Task 8 (native `<select>` styling has limited cross-browser control; a muted label color on an optgroup reads closer to typographic voice than brand chrome) — state your decision either way in the commit message, same as Task 8 did for the wordmark.

- [ ] **Step 3: `.state-alert` / `.narrative-box` / `.glossary-view` / `.chain-card` — flatten borders, drop radius**

Current (`bullion_mkultra.html:700-705`, `:739`, `:746`):
```css
  .state-alert { font-size: 11px; padding: 6px 9px; border-radius: 6px; border: 1px solid; line-height: 1.4; }
  .state-alert.risk-off { background: rgba(224,101,79,0.12); color: var(--up); border-color: rgba(224,101,79,0.5); }
  .state-alert.tight { background: rgba(224,177,90,0.12); color: var(--warn); border-color: rgba(224,177,90,0.5); }
  .state-alert.normal { background: rgba(123,191,142,0.12); color: var(--green); border-color: rgba(123,191,142,0.5); }
  .narrative-box { font-size: 12px; color: var(--text-dim); line-height: 1.6; background: var(--bg-panel2); border-radius: 6px; padding: 10px; border: 1px solid var(--border); white-space: pre-wrap; }
  .glossary-view { padding: 9px 11px; font-size: 11px; color: var(--text-dim); background: var(--bg-deep); overflow-y: auto; touch-action: pan-y; border-radius: 6px; max-height: 240px; border: 1px solid var(--border); }
  .chain-card { border: 1px solid var(--border); border-radius: 6px; padding: 9px 11px; background: var(--bg-panel2); }
```
Replace each `border-radius: 6px` with `border-radius: 0`. Leave `.state-alert.risk-off/.tight/.normal`'s `background`/`color`/`border-color` values (the `rgba(...)`+`var(--up)`/`var(--warn)`/`var(--green)` triad) completely untouched — these are functional risk-state indicators (same semantic-color pattern as `.market-card-change.up`/`.down`, already an established exception throughout this plan), only `.state-alert`'s own base `border-radius` changes. `.narrative-box`/`.glossary-view`/`.chain-card` keep their existing `border: 1px solid var(--border)` (a plain border, not gold-tinted) — only drop the radius; do not convert these to the "3px top-rule" pattern used for larger cards elsewhere, a 1px all-around border on a small text container reads fine flat, and forcing the top-rule pattern onto every single small box in this tab would look repetitive rather than deliberate.

- [ ] **Step 4: `.health-bar-bg`/`.health-bar-fill`/`.stat-track` — flatten, no color change**

Current (`bullion_mkultra.html:721-722`, `:790`):
```css
  .health-bar-bg { height: 7px; background: var(--bg-deep); border-radius: 4px; overflow: hidden; border: 1px solid var(--border); }
  .health-bar-fill { height: 100%; border-radius: 4px; transition: width 0.8s ease, background 0.8s ease; }
  .stat-track { position: relative; height: 14px; background: var(--bg-deep); border-radius: 4px; border: 1px solid var(--border); overflow: hidden; }
```
Replace each `border-radius: 4px` with `border-radius: 0`. No color changes — `.health-bar-fill`'s fill color is set inline per-reading (green/amber/red status), `.stat-track-mid`'s `var(--gold-dim)` center-line marker (line 791, immediately below `.stat-track`) is a fine typographic/marker use, not UI chrome — leave it.

- [ ] **Step 5: `.chain-badge`/`.chain-net-badge`/`.gterm::after` — flatten, leave tier colors alone**

Current (`bullion_mkultra.html:750-756`, `:776`):
```css
  .chain-net-badge { margin-left: 6px; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
  .chain-badge { font-size: 9px; padding: 1px 5px; border-radius: 8px; text-transform: uppercase; letter-spacing: 0.03em; }
  .chain-conf-measured { background: rgba(212,184,105,0.18); color: var(--gold); }
  .chain-conf-directional { background: rgba(136,145,166,0.18); color: var(--text-dim); }
  .gterm::after { content: attr(data-def); position: absolute; left: 0; top: calc(100% + 5px); width: max-content; max-width: min(250px, 72vw); background: #14161f; color: var(--text); border: 1px solid rgba(212,184,105,0.45); border-radius: 6px; padding: 6px 9px; font-size: 12px; line-height: 1.5; font-weight: 400; font-style: normal; text-transform: none; letter-spacing: normal; white-space: normal; box-shadow: 0 6px 18px rgba(0,0,0,0.65); z-index: 80; opacity: 0; visibility: hidden; pointer-events: none; transition: opacity 0.12s; }
```
Replace `.chain-net-badge`'s and `.chain-badge`'s own `border-radius` with `0`. **Do NOT touch `.chain-conf-measured`/`.chain-conf-directional`** (and the `.chain-conf-unverified` rule that follows them, not shown above but present in the file) — these are the SAME measured/directional/unverified confidence-tier color family that Task 7 explicitly, correctly left untouched in the Audit Log popup; touching them here would contradict that established precedent. For `.gterm::after` (the glossary-term tooltip): replace `border-radius: 6px` with `0` and swap its gold-tinted border `rgba(212,184,105,0.45)` to a neutral `var(--border)` or `var(--accent)` (your call — this one genuinely is decorative chrome, not a tier indicator, since it's a generic definition-tooltip background, not a confidence signal).

- [ ] **Step 6: `.tier-badge`/`.audit-badge` — flatten shape only, keep functional color**

Current (`bullion_mkultra.html:809-814`):
```css
  .tier-badge { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.05em; padding: 1px 5px; margin-right: 4px; border-radius: 3px;
    border: 1px solid currentColor; opacity: 0.9; vertical-align: 1px; cursor: help; }
  .audit-badge { display: inline-block; font-size: 10px; font-weight: 700; text-transform: uppercase;
                 letter-spacing: 0.05em; color: var(--warn, #e0b15a); border: 1px dashed var(--warn, #e0b15a);
                 border-radius: 3px; padding: 0 4px; margin-right: 4px; }
```
Replace both `border-radius: 3px` with `0`. `.tier-badge`'s `border: 1px solid currentColor` (inherits whichever tier color — measured/directional/unverified — is applied via a sibling class) and `.audit-badge`'s `var(--warn, #e0b15a)` are both functional confidence/warning indicators — leave every color untouched, shape only.

- [ ] **Step 7: detail-panel internals — `.rel-row`, `#narration-caption`, `.rel-summary .swatch`**

Current (`bullion_mkultra.html:420-424`):
```css
  .rel-row {
    border: 1px solid var(--border); border-radius: 8px; padding: 7px 9px; margin-bottom: 5px;
    background: var(--bg-panel2); cursor: pointer; transition: border-color 0.15s;
  }
  .rel-row:hover { border-color: var(--gold-dim); }
```
Replace with:
```css
  .rel-row {
    border: 1px solid var(--border); border-radius: 0; padding: 7px 9px; margin-bottom: 5px;
    background: var(--bg-panel2); cursor: pointer; transition: border-color 0.15s;
  }
  .rel-row:hover { border-color: var(--accent); }
```

Current (`bullion_mkultra.html:373-382`):
```css
  #narration-caption {
    position: fixed; left: 50%; bottom: 22px; transform: translateX(-50%);
    z-index: 20; max-width: min(640px, 88vw);
    padding: 10px 18px; border-radius: 10px;
    background: rgba(11,14,22,0.9); backdrop-filter: blur(6px);
    border: 1px solid var(--border);
    font-size: 13px; line-height: 1.5; text-align: center;
    box-shadow: 0 8px 28px rgba(0,0,0,0.45);
    pointer-events: none;
  }
```
Change `border-radius: 10px` to `0`, and `background: rgba(11,14,22,0.9); backdrop-filter: blur(6px);` to a solid `background: var(--bg-panel);` (no `backdrop-filter` — matches the flat/no-blur treatment already applied to `#detail-panel`/`#legend-box` in Task 7). Leave `box-shadow` alone — it's a subtitle-style legibility aid over the 3D scene, not brand chrome, and this task's scope is color/radius, not shadow removal (no prior task in this plan removed a functional legibility shadow either).

Current (`bullion_mkultra.html:413`):
```css
  .rel-summary .swatch { width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0; }
```
Change to `border-radius: 0`. (This is a small color-swatch key, not a dot — flat reads correctly here, unlike the genuinely-round `.rel-dot`/`.legend-dot` indicators elsewhere, which stay round.)

- [ ] **Step 8: `.manual-ctrls input[type=range]` accent color**

Current (`bullion_mkultra.html:834`):
```css
  .manual-ctrls input[type=range] { flex: 1 1 auto; min-width: 0; accent-color: var(--gold); height: 18px; }
```
Change `accent-color: var(--gold)` to `accent-color: var(--accent)`.

- [ ] **Step 9: JS-parse safety check**

This task is CSS-only, but run the standing check anyway:
```bash
cd bullion-live-map && python3 -c "
import re
html = open('bullion_mkultra.html', encoding='utf-8').read()
scripts = re.findall(r'<script(?:(?!type=\"importmap\")[^>])*>(.*?)</script>', html, re.S)
main = max(scripts, key=len)
open('/tmp/extracted_main_script.js','w',encoding='utf-8').write(main)
"
node --check /tmp/extracted_main_script.js && echo "PARSES OK"
```

- [ ] **Step 10: Screenshot and verify**

Screenshot the Analysis tab in full (scroll through: scenario grid, manual drivers with the range slider, live-metrics grid, health score/narrative, node picker, chain-reaction cards, glossary), and the detail panel open on a node with at least one relationship that has a field-note (to see `.rel-row` rendered). Confirm: no rounded corners anywhere except the explicitly-kept functional shapes (spinner, small indicator dots), no gold used as a clickable/interactive-state color anywhere in this tab, all confidence-tier colors (`.state-alert.*`, `.chain-conf-*`, `.tier-badge`, `.audit-badge`) render exactly as they did before this task (same colors, just flat corners). Re-run `grep -n "border-radius: [1-9]" bullion-live-map/bullion_mkultra.html` and confirm every remaining hit is one of the explicitly-kept exceptions (functional dots/spinner/legend patterns/persona-orb/Three.js canvas — cross-check against the list in the ledger's "gap confirmed + deepened" entry if unsure whether a given remaining hit is a legitimate keep).

- [ ] **Step 11: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Bullion Mk Ultra redesign 8b/9: Analysis-tab + detail-panel internals restyle

Closes a real gap in the original plan (surfaced by Task 8's review, not
any implementer's fault -- Task 5 correctly scoped to a container-only
drawer->tab conversion, Task 7 correctly scoped to container ids only,
and the design spec's own Phase 4 never said "restyle" the way Phases
3/5 did). Flattens border-radius and swaps gold-as-clickable-accent to
--accent across .run-btn's spinner, the scenario/metrics chrome,
state-alert/narrative-box/glossary-view/chain-card, health-bar/stat-
track, chain-badge/gterm tooltip, tier-badge/audit-badge (shape only),
and detail-panel's rel-row/narration-caption/swatch. Every confidence-
tier color (measured/directional/unverified, risk-off/tight/normal,
warn) is explicitly left untouched throughout -- same functional-color
exception already established for the Audit Log popup in Task 7.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Final verification

**Files:** none modified — verification only.

**Interfaces:** none — terminal task.

- [ ] **Step 1: Run the full Python test suite**

```bash
cd bullion-live-map && python3 -m unittest discover -s tests -v 2>&1 | tail -30
```
Expected: identical pass count to the baseline recorded before Task 1 started (record that baseline count when starting Task 1's Step 4, if not already known from recent project history, so this comparison is against a real number, not an assumption).

- [ ] **Step 2: Run `tests/freshness_test.html`'s underlying assertions if it has a headless runner**

Check whether this project already has a way to run `tests/freshness_test.html` outside a manual browser open (search `freshness_test` in any `.sh`/CI workflow file). If yes, run it. If it's manual-browser-only, open it via the CDP probe pattern and confirm its pass/fail summary the same way the 2026-08-04 pipeline-fix session did (per project memory) — this test asserts the JS/Python cadence-tolerance tables stay in sync and that `index.html`'s `CURRENT_MAP` resolution still finds `bullion_mkultra.html`; nothing in this redesign should have touched either, but confirm rather than assume.

- [ ] **Step 3: Full click-through with the CDP probe**

One consolidated probe script: load the page, click through Market → Analysis → Causal Link (3D) → Causal Link (2D via the toggle) → open a node's detail panel → close it → open the disclaimer → close it → toggle beginner/advanced mode via `#mode-toggle-btn` and confirm `.adv-control` elements actually hide/show. Capture console messages throughout (same `Runtime.consoleAPICalled`/`Runtime.exceptionThrown` listener pattern used for the Fed-odds card verification) and confirm zero errors/warnings across the entire sequence.

- [ ] **Step 4: Report to the user**

Per this project's standing workflow rule (Implementation stage: "Claude must explain what changed and why, in plain language, before I accept it"), summarize what shipped across all 9 tasks, any judgment calls flagged along the way (Market as new default tab from Task 3, the `#header h1`/`--gold` wordmark question from Task 8, whether the Audit Log popup got a real screenshot or just a wiring check from Task 7), and confirm test-suite/verification results — before the user is asked to treat the redesign as done.

---

## Self-Review Notes

(For the plan author's own use before handing this off — not a task the executor runs.)

- **Spec coverage:** all 6 spec phases map onto Tasks 1-9 (Phase 1→Task 1, Phase 2→Task 2, Phase 3→Tasks 3-4, Phase 4→Task 5, Phase 5→Tasks 6-7, Phase 6→Task 8), plus Task 9 as the verification pass the spec's Testing section calls for but didn't itself number as a phase.
- **Open judgment calls flagged to surface at review, not decided silently:** Market becoming the default tab (Task 3), the `#header h1` "Bullion" wordmark's gold color (Task 8), whether the Audit Log popup's restyle gets a full screenshot or just a click-doesn't-error check (Task 7) — each is called out in its task's commit message so the user sees it without having to read the diff.
- **Type/id consistency check:** `causalLinkSubView` (Task 3) is read and written identically in Tasks 3, 6, and 7 — same variable name, same two string values `'3d'`/`'board'` throughout. `#analysis-view` (Task 3's guarded reference, Task 5's real element) uses the same id in both places. `.hero-stat`/`.hero-stat-ghost` (defined Task 4) are referenced by the same two class names in Tasks 5 and 6/7 without redefinition.
