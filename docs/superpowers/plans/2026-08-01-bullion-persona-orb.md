# Bullion Persona Orb Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the header `#persona-toggle-btn` button in `bullion_mk18.html` and `bullion_mkultra.html` with a persistent, bottom-right floating "persona orb" that shows the active narration persona, breathes at idle, pulses per spoken word during narration, and toggles persona on click/keyboard — per `docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`.

**Architecture:** Pure front-end, no build step, edited identically in both HTML files (this project's standing duplication convention — no shared JS module exists between the two files). The orb reuses 100% of the existing persona machinery from the prior toggle plan (`narrationPersona`, `resolveNarration`, `startCaption`/`clearCaption`, the `'bullion-narration-persona'` `localStorage` key) — this plan only replaces the *visual* control and adds a new pulse/nudge layer on top of `startCaption`'s existing per-word timer. `applyPersonaToggle()` is repurposed (same name, same call sites) rather than duplicated.

**Tech Stack:** Vanilla JS (no build step, matches both files' existing style), CSS custom properties + `@keyframes`, `localStorage`/`sessionStorage` (existing keys reused, one new key added).

## Global Constraints

- The orb replaces `#persona-toggle-btn` entirely — no dual UI. The old button's markup **and** its unguarded `document.getElementById('persona-toggle-btn').addEventListener(...)` registration must be removed together, in the same task/commit — that registration line has no null-check today, so removing only the button first would throw `TypeError: Cannot read properties of null` at script load and silently break every top-level statement after it in the same inline `<script>` block (map rendering, node clicks, everything). (Spec: "Removal.")
- Default persona stays **Alfred** — unchanged, verified in the static markup, in `applyPersonaToggle()`'s logic, and in `narrationPersona`'s existing init line.
- Icons: Alfred = 🎩 (`&#127913;` in HTML / `\u{1F3A9}` in JS), Johnny = 👹 (`\u{1F479}` in JS). No hand-drawn SVG icons — plain Unicode glyphs only, matching this project's existing icon convention. (Spec: "Icons / colors.")
- New CSS custom properties, added to `:root` in both files alongside the existing `--gold`/`--gold-dim`/`--green`/`--red`: `--blue: #4d7fb8;`, `--blue-dim: #24425e;`, `--red-dim: #7a2e1f;`. No other palette changes.
- `#persona-orb`'s `z-index` is `15` — above `#stage`/`#legend-box` (`10`), below `#detail-panel` (`20`), matching the existing panel-vs-content stacking order.
- Reuses the **existing** `narrationPersona` variable and `'bullion-narration-persona'` `localStorage` key exactly as the current toggle button uses them — no new persona-state surface.
- One genuinely new state surface: `sessionStorage['bullion-orb-nudge-shown']`, gating the one-time first-visit nudge. Deliberately **not** reusing `#mode-toggle-btn`'s `.tools-ready`/`onFirstInteraction()` machinery — that's a different, already-used affordance.
- `#persona-orb` is a `div[role=button][tabindex=0]`, not a native `<button>` — every click handler on it needs a matching `keydown` (Enter/Space) handler, since a non-native element gets no free keyboard activation. (Spec: "Component markup.")
- No Python/backend changes — pure front-end, both files.
- Apply every change **identically** to both `bullion_mk18.html` and `bullion_mkultra.html` unless a step says otherwise.
- Never `git add .` / `-A` — this repo has substantial pre-existing untracked noise (`.claude/`, `.agents/`, `docs/superpowers/archive/`, `__pycache__/`, etc.); stage only the files each task actually touches.
- No automated tests exist or are planned for this feature (pure UI/CSS/animation, same category as the prior plan's Tasks 4-6) — every task's verification is a manual claude-in-chrome or real-Chrome pass. Whether the pulse *feels* right in sync with real audio is explicitly **not** verifiable by automation in this project — a human-in-a-focused-tab step, per the standing project idiom.

---

## Task 1: Orb component — tokens, markup, and CSS (idle/gradient/placement, both breakpoints)

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Produces: `#persona-orb` element (with children `.orb-core > .orb-icon`, `.orb-label`, `.orb-nudge-tip`), classes `.idle`/`.active`/`.persona-alfred`/`.persona-johnny`/`.nudge`/`.pulse` (defined here, driven by later tasks), `--blue`/`--blue-dim`/`--red-dim` CSS custom properties. Removes `#persona-toggle-btn` and its now-dangling click-listener registration.

Apply identically to both files. Anchors below are exact, byte-identical text present in both files today — search for the text, not the line number (line numbers given are current-`HEAD` references only, `bullion_mk18.html` / `bullion_mkultra.html` respectively).

- [ ] **Step 1: Add the three new color tokens**

Find, inside `:root { ... }` (mk18 line 34, mkultra line 37):

```css
    --red:        #e0654f;
```

Insert immediately after it:

```css
    --blue:       #4d7fb8;
    --blue-dim:   #24425e;
    --red-dim:    #7a2e1f;
```

- [ ] **Step 2: Add the orb's CSS block**

Find (mk18 lines 240-244, mkultra lines 273-276 — identical text in both files):

```css
  .legend-causal-title {
    width: 100%; font-size: 9px; text-transform: uppercase; letter-spacing: 0.07em;
    color: var(--gold-dim); font-weight: 700; margin: 2px 0 0;
  }
```

Immediately after its closing `}`, insert:

```css

  /* ── Persona orb: floating narration-persona indicator, replaces the old
     header toggle button (#persona-toggle-btn) ───────────────────────── */
  #persona-orb {
    position: fixed; right: 18px; bottom: 18px; z-index: 15;
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    cursor: pointer; transition: transform 0.28s ease;
  }
  .orb-core {
    width: 52px; height: 52px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  }
  .orb-icon { font-size: 24px; line-height: 1; }
  .orb-label {
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-dim);
  }
  #persona-orb.persona-alfred .orb-core {
    background: radial-gradient(circle at 35% 30%, #9fc6f5, var(--blue) 55%, var(--blue-dim));
  }
  #persona-orb.persona-johnny .orb-core {
    background: radial-gradient(circle at 35% 30%, #f2a08f, var(--red) 55%, var(--red-dim));
  }
  #persona-orb.idle .orb-core { animation: orbBreathe 3.6s ease-in-out infinite; }
  @keyframes orbBreathe {
    0%, 100% { transform: scale(1);    opacity: 0.75; }
    50%      { transform: scale(1.12); opacity: 1;    }
  }
  #persona-orb.active .orb-core.pulse { animation: orbPulse 0.32s ease-out; }
  @keyframes orbPulse {
    0%   { transform: scale(1);    box-shadow: 0 0 0 0 currentColor; }
    60%  { transform: scale(1.22); box-shadow: 0 0 0 10px transparent; }
    100% { transform: scale(1);    box-shadow: 0 0 0 0 transparent; }
  }
  #persona-orb.nudge .orb-core { animation: toolsPulse 2s ease-out 3; }
  .orb-nudge-tip {
    position: absolute; right: 0; bottom: 100%; margin-bottom: 8px;
    background: rgba(11,14,22,0.95); border: 1px solid var(--border); border-radius: 6px;
    padding: 4px 8px; font-size: 10.5px; white-space: nowrap; color: var(--text-dim);
  }
  #app.panel-open #persona-orb { transform: translateX(calc(-1 * min(380px, 92vw))); }
```

(`#persona-orb.nudge .orb-core` reuses the existing `toolsPulse` `@keyframes`, already defined earlier in both files' `<style>` block — no new keyframe needed for the nudge ring. The `#app.panel-open #persona-orb` desktop shift is written directly against `#detail-panel`'s real `width: min(380px, 92vw)` — see Task 1's Step 4 note below for why this doesn't reuse `#stage`'s existing `-11vw` shift rule.)

- [ ] **Step 3: Add the mobile repositioning rule**

Find, inside the `@media (max-width: 640px) { ... }` block (mk18 line 324, mkultra line 358 — identical text in both files):

```css
    #app.panel-open #stage { transform: translateY(-16vh); }
```

Immediately after it (still inside the same media-query block, before its closing `}`), insert:

```css
    #app.panel-open #persona-orb { transform: translateY(calc(-62vh - 12px)); }
```

This lifts the orb clear above the mobile bottom sheet (`#detail-panel`'s `max-height: 62vh` on this breakpoint) whenever it's open — without this, the orb would sit underneath the sheet exactly while narration is playing, since the sheet slides up from the bottom edge on mobile instead of in from the right like on desktop.

- [ ] **Step 4: Replace the header button with the orb markup**

Find (mk18 line 527, mkultra line 579 — identical text in both files):

```html
      <button class="btn" id="persona-toggle-btn" title="Switch narration voice between Alfred (butler) and Johnny (rocker)">&#127908; Alfred</button>
```

Delete this line entirely (no replacement here — the orb markup goes near `#legend-box`, not in the header; see Step 5).

- [ ] **Step 5: Add the orb markup near `#legend-box`**

Find (mk18 line 566, mkultra line 618 — identical text in both files):

```html
<div id="legend-box"></div>
```

Immediately after it, insert:

```html
<div id="persona-orb" title="Switch narration voice" class="idle persona-alfred"
     role="button" tabindex="0" aria-label="Switch narration voice, currently Alfred">
  <div class="orb-core"><span class="orb-icon">&#127913;</span></div>
  <div class="orb-label">Alfred</div>
  <div class="orb-nudge-tip" hidden>Tap to switch narrator voice</div>
</div>
```

`#legend-box` is bottom-**left** (`left:12px; bottom:12px`); the orb sits at the mirror position, bottom-**right** — the two never overlap. The `persona-alfred` class is included in the static markup (matching the default persona) so the gradient renders correctly on first paint, before Task 2's `applyPersonaToggle()` init call runs.

- [ ] **Step 6: Remove the now-dangling click-listener registration**

Find (mk18 lines 3441-3445, mkultra lines 4108-4112 — identical text in both files):

```javascript
document.getElementById('persona-toggle-btn').addEventListener('click', function() {
  narrationPersona = narrationPersona === 'alfred' ? 'johnny' : 'alfred';
  localStorage.setItem('bullion-narration-persona', narrationPersona);
  applyPersonaToggle();
});
```

Delete these 5 lines entirely. **This must happen in this same task/commit as Step 4's button removal** — this line has no null-check on `document.getElementById('persona-toggle-btn')`, so with the button gone (Step 4) but this line still present, it throws `TypeError: Cannot read properties of null (reading 'addEventListener')` the moment the script runs, halting every top-level statement after it in the same inline `<script>` block — breaking the whole app, not just the orb. After deletion, the surrounding code reads:

```javascript
function applyPersonaToggle() {
  const btn = document.getElementById('persona-toggle-btn');
  if (!btn) return;
  btn.innerHTML = narrationPersona === 'johnny' ? '&#127908; Johnny' : '&#127908; Alfred';
  btn.classList.toggle('active', narrationPersona === 'johnny');
}
applyPersonaToggle();
```

This is a safe, working intermediate state: `applyPersonaToggle()` still runs (called on the last line shown above) but now no-ops via its own `if (!btn) return;` guard, since `#persona-toggle-btn` no longer exists. The orb is visible with its static default (idle, blue, "Alfred") but isn't yet clickable or dynamically updated — Task 2 fixes that. Nothing crashes.

- [ ] **Step 7: Manually verify the orb appears and the app still works**

1. Serve the files: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m http.server 8791` (check `lsof -i :8791` first in case a server from a prior session is already running).
2. Open `http://localhost:8791/bullion_mk18.html` in Chrome with dev tools open — confirm **0 console errors** on load (this is the critical check for Step 6's crash risk).
3. Confirm a blue circular orb with 🎩 and the label "Alfred" appears bottom-right, gently breathing (scale/opacity pulsing every ~3.6s).
4. Confirm the map still loads and node clicks still open the detail panel normally — the orb isn't clickable yet (expected, Task 2 wires that), but nothing else in the app should be broken.
5. Open a node's detail panel — confirm the orb shifts left to clear the panel (desktop width).
6. Resize the Chrome window below 640px wide, open a node's detail panel again — confirm the orb shifts *up* to clear the mobile bottom sheet instead of getting covered by it.
7. Repeat steps 2-6 against `bullion_mkultra.html`.

Report the outcome before proceeding to Task 2.

- [ ] **Step 8: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Replace persona-toggle-btn with the persona orb component

Adds the floating #persona-orb (idle breathe, per-persona gradient,
desktop + mobile panel-open repositioning) near #legend-box in both
HTML files, and removes the old header button along with its now-
dangling click-listener registration. The orb isn't interactive yet
(Task 2) — this task only ships the visual component and confirms
removing the old button doesn't break page load.
EOF
)"
```

---

## Task 2: Wire click/keyboard toggle — repurpose `applyPersonaToggle()`

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `#persona-orb` markup (Task 1), existing `narrationPersona` variable and `'bullion-narration-persona'` `localStorage` key.
- Produces: `applyPersonaToggle()` — same name, new body, now targets the orb instead of the removed button. `toggleNarrationPersona()` — new, called by both a `click` and a `keydown` (Enter/Space) listener on `#persona-orb`. (Task 4 will add one more line to `toggleNarrationPersona()`'s body — a `dismissOrbNudge()` call — once that function exists.)

Apply identically to both files.

- [ ] **Step 1: Replace `applyPersonaToggle()`'s body and add the toggle handlers**

Find (mk18 lines 3435-3440, mkultra lines 4102-4107 — identical text in both files, and now immediately followed by `applyPersonaToggle();` per Task 1 Step 6):

```javascript
function applyPersonaToggle() {
  const btn = document.getElementById('persona-toggle-btn');
  if (!btn) return;
  btn.innerHTML = narrationPersona === 'johnny' ? '&#127908; Johnny' : '&#127908; Alfred';
  btn.classList.toggle('active', narrationPersona === 'johnny');
}
applyPersonaToggle();
```

Replace the whole block with:

```javascript
function applyPersonaToggle() {
  const orb = document.getElementById('persona-orb');
  if (!orb) return;
  const isJohnny = narrationPersona === 'johnny';
  orb.classList.toggle('persona-alfred', !isJohnny);
  orb.classList.toggle('persona-johnny', isJohnny);
  orb.querySelector('.orb-icon').textContent = isJohnny ? '\u{1F479}' : '\u{1F3A9}';
  orb.querySelector('.orb-label').textContent = isJohnny ? 'Johnny' : 'Alfred';
  orb.setAttribute('aria-label', 'Switch narration voice, currently ' + (isJohnny ? 'Johnny' : 'Alfred'));
}
function toggleNarrationPersona() {
  narrationPersona = narrationPersona === 'alfred' ? 'johnny' : 'alfred';
  localStorage.setItem('bullion-narration-persona', narrationPersona);
  applyPersonaToggle();
}
const orbEl = document.getElementById('persona-orb');
orbEl.addEventListener('click', toggleNarrationPersona);
orbEl.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleNarrationPersona(); }
});
applyPersonaToggle();
```

(`\u{1F479}` = 👹, `\u{1F3A9}` = 🎩 — the same two glyphs as Task 1's static markup `&#127913;` HTML entity, written here as JS string escapes since this runs inside a `<script>` block, not HTML. The `keydown` handler exists because `#persona-orb` is a `div[role=button]`, not a native `<button>` — it gets no free Enter/Space activation.)

- [ ] **Step 2: Manually verify the toggle works by mouse and keyboard**

1. Serve and open both files as in Task 1 Step 7.
2. Click the orb — confirm it flips to 👹/red/"Johnny", `localStorage.getItem('bullion-narration-persona')` (check via dev tools console) reads `'johnny'`, and the `aria-label` (inspect the element) updates to mention Johnny.
3. Click again — confirm it flips back to 🎩/blue/"Alfred".
4. Tab to the orb with the keyboard (confirm it receives a visible focus outline — browser default is fine, no custom focus style was specified), press Enter — confirm it toggles. Press Space — confirm it toggles again.
5. Reload the page — confirm the orb shows whichever persona was last selected (persisted via `localStorage`), not always defaulting back to Alfred.
6. Repeat steps 2-5 against the other file.

Report the outcome before proceeding to Task 3.

- [ ] **Step 3: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Wire click/keyboard persona toggle on the orb

Repurposes applyPersonaToggle() (same name, same call sites) to drive
the orb's icon/label/gradient/aria-label instead of the removed
button. Adds toggleNarrationPersona() plus paired click/keydown
handlers so the orb is keyboard-accessible, matching this project's
existing convention for non-native interactive elements.
EOF
)"
```

---

## Task 3: Narration pulse sync

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `startCaption(persona, text, duration)` / `clearCaption()` (existing, unmodified signatures) — this task edits their bodies, not their contracts.
- Produces: `pulseOrb()` — new. `#persona-orb` now gains `.active`/loses `.idle` at the top of `startCaption()`, and the reverse inside `clearCaption()`.

Apply identically to both files.

- [ ] **Step 1: Add `pulseOrb()`**

Find (identical text in both files, immediately before `function clearCaption() {`):

```javascript
let captionTimeouts = [];
```

Immediately after it, insert:

```javascript
function pulseOrb() {
  const core = document.querySelector('#persona-orb .orb-core');
  if (!core) return;
  core.classList.remove('pulse');
  void core.offsetWidth;   // force reflow so the animation retriggers
  core.classList.add('pulse');
}
```

- [ ] **Step 2: Toggle `.active`/`.idle` in `clearCaption()`**

Find (identical text in both files):

```javascript
function clearCaption() {
  captionTimeouts.forEach(clearTimeout);
  captionTimeouts = [];
  const host = document.getElementById('detail-caption');
  if (host) { host.hidden = true; host.innerHTML = ''; }
}
```

Replace with:

```javascript
function clearCaption() {
  const orb = document.getElementById('persona-orb');
  if (orb) { orb.classList.remove('active'); orb.classList.add('idle'); }
  captionTimeouts.forEach(clearTimeout);
  captionTimeouts = [];
  const host = document.getElementById('detail-caption');
  if (host) { host.hidden = true; host.innerHTML = ''; }
}
```

- [ ] **Step 3: Toggle `.active`/`.idle` and pulse per word in `startCaption()`**

Find (identical text in both files):

```javascript
function startCaption(persona, text, duration) {
  const host = document.getElementById('detail-caption');
  if (!host || !text) return;
  const words = text.trim().split(/\s+/);
  const totalChars = words.reduce(function(sum, w) { return sum + w.length; }, 0) || 1;
  host.hidden = false;
  host.innerHTML = '<span class="caption-persona">' + persona + ':</span> <span class="caption-words"></span>';
  const wordsHost = host.querySelector('.caption-words');
  let elapsed = 0;
  let shown = '';
  words.forEach(function(word, i) {
    const wordDuration = (word.length / totalChars) * duration;
    captionTimeouts.push(setTimeout(function() {
      shown += (i > 0 ? ' ' : '') + word;
      wordsHost.textContent = shown;
    }, elapsed * 1000));
    elapsed += wordDuration;
  });
}
```

Replace with:

```javascript
function startCaption(persona, text, duration) {
  const orb = document.getElementById('persona-orb');
  if (orb) { orb.classList.remove('idle'); orb.classList.add('active'); }
  const host = document.getElementById('detail-caption');
  if (!host || !text) return;
  const words = text.trim().split(/\s+/);
  const totalChars = words.reduce(function(sum, w) { return sum + w.length; }, 0) || 1;
  host.hidden = false;
  host.innerHTML = '<span class="caption-persona">' + persona + ':</span> <span class="caption-words"></span>';
  const wordsHost = host.querySelector('.caption-words');
  let elapsed = 0;
  let shown = '';
  words.forEach(function(word, i) {
    const wordDuration = (word.length / totalChars) * duration;
    captionTimeouts.push(setTimeout(function() {
      shown += (i > 0 ? ' ' : '') + word;
      wordsHost.textContent = shown;
      pulseOrb();
    }, elapsed * 1000));
    elapsed += wordDuration;
  });
}
```

(The `.active`/`.idle` toggle is placed *before* the `if (!host || !text) return;` early-return so the orb's narration state stays correct — "is anything narrating" — even in the edge case where the caption host is missing, rather than being coupled to whether captions specifically can render.)

- [ ] **Step 4: Manually verify pulse-per-word and active/idle transitions**

1. Serve and open both files as in Task 1 Step 7.
2. Open the "fed" node, click 🔊 — confirm the orb switches from the slow idle breathe to a sharp per-word pulse in rough sync with the caption text filling in.
3. Let the clip finish (or close the panel mid-playback) — confirm the orb returns to the slow idle breathe, and no further pulses fire after `clearCaption()` runs (no leaked `setTimeout`s still calling `pulseOrb()` on a stale playback).
4. Open a different node while one is narrating — confirm the orb doesn't get stuck in `.active` (i.e., `clearCaption()`'s call at the top of `playNarration()` correctly resets it before the new node's `startCaption()` re-activates it).
5. Repeat steps 2-4 against the other file.

Whether the pulse *feels* right in sync with real audio (not just that it fires) is not verifiable by automation — this is the one part of this step that's a genuine subjective human check, independent of the open `say`-CLI voice-quality question.

Report the outcome before proceeding to Task 4.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Sync the orb's pulse to narration playback

pulseOrb() retriggers a CSS animation per revealed caption word,
called from startCaption()'s existing per-word setTimeout schedule —
no second timer system. #persona-orb gains .active in startCaption()
and reverts to .idle in clearCaption(), the same two functions that
already gate captions, so narration state has one source of truth.
EOF
)"
```

---

## Task 4: First-visit nudge

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `toggleNarrationPersona()` (Task 2), `startCaption()` (Task 3) — both modified here to call the new `dismissOrbNudge()`.
- Produces: `dismissOrbNudge()` — new. A one-time `sessionStorage`-gated nudge shown on load.

Apply identically to both files.

- [ ] **Step 1: Add the nudge init check and `dismissOrbNudge()`**

Find (identical text in both files, the last line of Task 2's Step 1 block):

```javascript
applyPersonaToggle();
```

(This appears exactly once in this area — immediately after the `orbEl.addEventListener('keydown', ...)` block from Task 2. Do not confuse with any other `applyPersonaToggle()` call.) Immediately after it, insert:

```javascript
if (!sessionStorage.getItem('bullion-orb-nudge-shown')) {
  const nudgeOrb = document.getElementById('persona-orb');
  nudgeOrb.classList.add('nudge');
  nudgeOrb.querySelector('.orb-nudge-tip').hidden = false;
}
function dismissOrbNudge() {
  sessionStorage.setItem('bullion-orb-nudge-shown', '1');
  const orb = document.getElementById('persona-orb');
  if (!orb) return;
  orb.classList.remove('nudge');
  orb.querySelector('.orb-nudge-tip').hidden = true;
}
```

- [ ] **Step 2: Dismiss the nudge on first click/keyboard toggle**

Find, inside `toggleNarrationPersona()` (Task 2, Step 1 — identical text in both files):

```javascript
function toggleNarrationPersona() {
  narrationPersona = narrationPersona === 'alfred' ? 'johnny' : 'alfred';
  localStorage.setItem('bullion-narration-persona', narrationPersona);
  applyPersonaToggle();
}
```

Replace with:

```javascript
function toggleNarrationPersona() {
  narrationPersona = narrationPersona === 'alfred' ? 'johnny' : 'alfred';
  localStorage.setItem('bullion-narration-persona', narrationPersona);
  applyPersonaToggle();
  dismissOrbNudge();
}
```

- [ ] **Step 3: Dismiss the nudge on first narration**

Find, at the top of `startCaption()` (Task 3, Step 3 — identical text in both files):

```javascript
function startCaption(persona, text, duration) {
  const orb = document.getElementById('persona-orb');
  if (orb) { orb.classList.remove('idle'); orb.classList.add('active'); }
```

Replace with:

```javascript
function startCaption(persona, text, duration) {
  dismissOrbNudge();
  const orb = document.getElementById('persona-orb');
  if (orb) { orb.classList.remove('idle'); orb.classList.add('active'); }
```

- [ ] **Step 4: Manually verify the nudge shows once and dismisses correctly**

1. Serve and open `bullion_mk18.html` fresh in a **new** Chrome tab (or clear `sessionStorage` via dev tools: `sessionStorage.clear()`, then reload).
2. Confirm the orb shows a brief ring-pulse (reusing the existing "⚙ Tools" glow animation) and a tooltip reading "Tap to switch narrator voice" on load.
3. Click the orb (or wait for the ring-pulse's 3 iterations to finish, then narrate a node instead) — confirm the tooltip and ring-pulse class both clear, and `sessionStorage.getItem('bullion-orb-nudge-shown')` now reads `'1'`.
4. Reload the page (same tab, `sessionStorage` persists) — confirm the nudge does **not** reappear.
5. Open a **new** tab (fresh `sessionStorage`) — confirm the nudge appears again in the new tab.
6. As a second path: clear `sessionStorage` again, reload, and this time dismiss the nudge by opening a node and letting narration autoplay/play (instead of clicking the orb) — confirm the nudge clears via `startCaption()`'s call too, not just the click path.
7. Repeat steps 1-6 against `bullion_mkultra.html`.

Report the outcome before proceeding to Task 5.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Add first-visit nudge to the persona orb

One-time ring-pulse (reusing the existing toolsPulse keyframe) plus a
tooltip, gated by a new sessionStorage flag independent of the
mode-toggle-btn's own progressive-disclosure flag. Dismissed on
whichever comes first: clicking/keyboard-toggling the orb, or the
first narration actually starting.
EOF
)"
```

---

## Task 5: Full manual regression pass and push decision

**Files:** none (verification only)

- [ ] **Step 1: Full manual click-through in real Chrome, both files**

For each of `bullion_mk18.html` and `bullion_mkultra.html`:
1. Load with dev tools open — confirm 0 console errors.
2. Confirm the old `#persona-toggle-btn` is gone from the header and `#persona-orb` is the only persona control, bottom-right.
3. Click through several narrated nodes across different layers (not just the 6 Johnny-piloted ones) in both Alfred and Johnny toggle states — confirm audio, captions, orb pulse, and the Alfred-fallback behavior (for nodes without a Johnny clip) all still hold up, matching the prior toggle plan's own Task 7 regression pass.
4. Confirm the orb's persona state (icon/color/label) persists correctly across a page reload via `localStorage`, exactly as the old button did.
5. Confirm keyboard-only operation: Tab to the orb, Enter/Space toggles it, with no mouse involved.
6. Confirm desktop panel-open repositioning (orb shifts left) and, via a narrow (<640px) Chrome window, mobile panel-open repositioning (orb shifts up above the bottom sheet).
7. Confirm the first-visit nudge behavior from Task 4 one more time in a fresh tab.

- [ ] **Step 2: Re-run the existing Python suite to confirm no regression**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
Expected: all PASS, same count as the prior toggle plan's Task 7 (96/96) — this feature is pure front-end and shouldn't have touched anything the Python suite covers; this step exists only to confirm that's actually true, not assumed.

- [ ] **Step 3: Ask the user whether to push now**

Per this project's standing convention (fail loudly, never silently ship), ask the user: push `main` to `origin` now — bundling this orb work with the still-unpushed `bd4012d` (Task 6 of the prior persona-toggle plan) and this plan's Tasks 1-4 — or hold? Do not push without an explicit answer; a prior "hold" from an earlier session does not carry forward, and neither does a future "yes" carry backward.

---

## Self-Review Notes

- **Spec coverage:** Component markup + z-index (Task 1, Steps 2/5), icons/colors + new tokens (Task 1, Steps 1/2/5; Task 2, Step 1), idle/active states (Task 1 Step 2; Task 3), narration sync (Task 3), click-toggle-persona incl. keyboard accessibility (Task 2), placement/panel-open repositioning desktop+mobile (Task 1, Steps 2/3), first-visit nudge (Task 4), removal (Task 1, Steps 4/6; Task 2, Step 1), testing (every task's manual-verification step + Task 5's full pass) — every spec section maps to a task.
- **Type/name consistency checked:** `applyPersonaToggle()` keeps its exact name and call sites across Tasks 1→2 (Task 1 leaves the old body temporarily no-op'd via its own guard; Task 2 replaces the body, not the name). `startCaption(persona, text, duration)` / `clearCaption()` signatures are unchanged from the prior toggle plan across Tasks 3-4 — only bodies are edited, and each edit's "Find" block is the literal output of the previous edit, so the anchors stay valid task-to-task. `toggleNarrationPersona()` is defined in Task 2 and only gains one appended line in Task 4 (`dismissOrbNudge();`) — never renamed. `pulseOrb()` (Task 3) and `dismissOrbNudge()` (Task 4) are each defined once and referenced identically wherever called.
- **Sequencing/safety checked:** Task 1 explicitly calls out and defuses the one real crash risk in this plan (removing `#persona-toggle-btn` before its dangling listener registration) by doing both in the same task/commit — every other task leaves the app in a working, verifiable state after its own commit, matching this project's standing convention of no broken intermediate states between commits.
- **No placeholders:** every step has literal, complete code (CSS blocks, JS functions, exact HTML) or an exact shell/manual-check command; the two dimensions the design spec deliberately left unfixed at the pixel level (`.orb-core` size, `.orb-label` type scale) are filled in here with concrete values consistent with this codebase's existing scale (`.legend-causal-title`'s 9px/uppercase treatment, `.legend-dot`'s sub-10px sizing) rather than left open.
