# Bullion Orb Translucency + Custom Glyphs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drop the persona orb's resting opacity to match a map node's translucency and
replace its emoji icons with original translucent SVG glyphs, in both `bullion_mk18.html`
and `bullion_mkultra.html`.

**Architecture:** Pure CSS + inline-SVG + one-function JS edit to an already-shipped,
self-contained UI element (`#persona-orb`). No new state, no data flow, no build step —
both target files are single static HTML documents edited in place.

**Tech Stack:** Plain HTML/CSS/vanilla JS (no framework, no bundler). Verification via
`claude-in-chrome` screenshots (this project's established idiom for CSS/visual
correctness — `getComputedStyle()` reads are unreliable for animated/transitioning
properties on backgrounded tabs, so trust rendered screenshots) and the existing Python
test suite for regression-only sanity (pure front-end change, suite is expected to be
unaffected).

## Global Constraints

- Every change must be applied **identically** to both `bullion-live-map/bullion_mk18.html`
  and `bullion-live-map/bullion_mkultra.html` — this project's standing convention, verified
  in this plan by diffing the touched regions after each task.
- **Never `git add -A` or `git add .`** — stage the two target files by exact path only.
  This repo has pre-existing untracked noise (`.claude/`, `docs/superpowers/archive/`,
  `__pycache__/`, etc.) that must never be swept into a commit.
- The new SVG glyphs must be **original designs**, not a reproduction of CD Projekt Red's
  actual trademarked Cyberpunk 2077 "Samurai" band logo — angular/samurai-inspired only.
- Resting orb opacity is `0.4`, matching the existing `NODE_BASE_OPACITY = 0.4` constant
  (defined elsewhere in each file's THREE.js section) — this equality is intentional, not
  a coincidence, and should stay commented as such in the CSS.
- Scope is `.orb-core` (circle + glyph) only — `.orb-label` (the persona name text) and
  `.orb-nudge-tip` stay at full opacity/unaffected.
- Do not touch narration sync (`setOrbNarrating`, `startCaption`/`clearCaption`, the
  per-word `pulseOrb`), positioning (`#detail-panel.open ~ #persona-orb`), or the parked
  narration-overlap bug — all out of scope, per the design spec.

---

## Task 1: Orb resting opacity (CSS only)

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (orb CSS block, ~line 304-309)
- Modify: `bullion-live-map/bullion_mk18.html` (identical orb CSS block, ~line 271-276)

**Interfaces:**
- Consumes: nothing new — existing `#persona-orb.idle` / `#persona-orb.active` classes,
  already toggled by `setOrbNarrating()` (untouched by this task).
- Produces: the visual opacity contract every later task (Task 2's icon swap) renders
  inside — `.orb-core` at rest is `opacity: 0.4`, breathing to `0.65`, and `1.0` on
  hover/focus/active. Task 2 does not depend on this numerically, but both tasks touch the
  same element and should be verified together at the end.

- [ ] **Step 1: Edit the CSS in `bullion_mkultra.html`**

Find this exact block (it is unique in the file):

```css
  #persona-orb.idle .orb-core { animation: orbBreathe 3.6s ease-in-out infinite; }
  @keyframes orbBreathe {
    0%, 100% { transform: scale(1);    opacity: 0.75; }
    50%      { transform: scale(1.12); opacity: 1;    }
  }
  #persona-orb.active .orb-core.pulse { animation: orbPulse 0.32s ease-out; }
```

Replace it with:

```css
  #persona-orb.idle .orb-core { animation: orbBreathe 3.6s ease-in-out infinite; }
  @keyframes orbBreathe {
    /* 0.4 matches NODE_BASE_OPACITY — resting orb reads at the same
       translucency as a resting map node. */
    0%, 100% { transform: scale(1);    opacity: 0.4;  }
    50%      { transform: scale(1.12); opacity: 0.65; }
  }
  #persona-orb.active .orb-core { opacity: 1; }
  #persona-orb:hover .orb-core,
  #persona-orb:focus-visible .orb-core { opacity: 1 !important; }
  #persona-orb.active .orb-core.pulse { animation: orbPulse 0.32s ease-out; }
```

(The `!important` on the hover/focus rule is required — it's the only way a static
declaration overrides a running CSS animation's own keyframe values, per the CSS
Animations spec. This is expected, standard behavior, not a workaround.)

- [ ] **Step 2: Apply the identical edit to `bullion_mk18.html`**

Same old block, same new block, verbatim (the CSS text is byte-identical between the two
files at this location — confirmed before writing this plan).

- [ ] **Step 3: Verify parity between the two files**

```bash
cd bullion-live-map
diff <(grep -A8 "orb.idle .orb-core { animation" bullion_mk18.html) \
     <(grep -A8 "orb.idle .orb-core { animation" bullion_mkultra.html)
```

Expected: no output (identical).

- [ ] **Step 4: Screenshot-verify visually**

Open `bullion_mkultra.html` in a Chrome tab (via `claude-in-chrome`, `file://` path is
fine — this is a static file). Screenshot the orb in its default idle state: it should
read as clearly more translucent/dim than before (roughly matching the translucency of a
resting map node bubble, not the near-solid look it had before). Hover the orb and
screenshot again: it should snap to fully opaque. Repeat both checks on `bullion_mk18.html`.

- [ ] **Step 5: Run the regression suite**

```bash
cd bullion-live-map
python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v
```

Expected: 96/96 passing, unchanged (this is a pure front-end CSS change and should not
affect it — this step just confirms no accidental cross-contamination).

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "Dim persona orb to match node resting opacity, brighten on hover/active"
```

---

## Task 2: Custom translucent SVG glyphs

**Files:**
- Modify: `bullion-live-map/bullion_mkultra.html` (`.orb-icon` CSS ~line 293, initial
  markup ~line 673-678, `applyPersonaToggle()` ~line 4180-4189)
- Modify: `bullion-live-map/bullion_mk18.html` (identical locations, ~line 260, 621-626,
  3513-3521)

**Interfaces:**
- Consumes: nothing from Task 1 (independent element concerns — icon content vs. opacity
  — though both live inside the same `.orb-core`).
- Produces: `ALFRED_ICON_SVG` / `JOHNNY_ICON_SVG` string constants used by
  `applyPersonaToggle()`; no other code in either file references these, so no downstream
  interface risk.

- [ ] **Step 1: Update `.orb-icon` CSS sizing in `bullion_mkultra.html`**

Find:

```css
  .orb-icon { font-size: 24px; line-height: 1; }
```

Replace with:

```css
  .orb-icon { display: flex; }
  .orb-icon svg { display: block; width: 24px; height: 24px; }
```

- [ ] **Step 2: Replace the initial Alfred emoji markup in `bullion_mkultra.html`**

Find this exact block:

```html
<div id="persona-orb" title="Switch narration voice" class="idle persona-alfred"
     role="button" tabindex="0" aria-label="Switch narration voice, currently Alfred">
  <div class="orb-core"><span class="orb-icon">&#127913;</span></div>
  <div class="orb-label">Alfred</div>
  <div class="orb-nudge-tip" hidden>Tap to switch narrator voice</div>
</div>
```

Replace with:

```html
<div id="persona-orb" title="Switch narration voice" class="idle persona-alfred"
     role="button" tabindex="0" aria-label="Switch narration voice, currently Alfred">
  <div class="orb-core"><span class="orb-icon"><svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
    <path d="M7 15 L17 15 L17 17 L7 17 Z" fill="#fff" fill-opacity="0.55"/>
    <path d="M9 6 L15 6 L15 15 L9 15 Z" fill="#fff" fill-opacity="0.55"/>
    <path d="M9 8.5 L15 8.5 L15 9.5 L9 9.5 Z" fill="#fff" fill-opacity="0.35"/>
    <path d="M17.5 16 L20.5 20 L19 22" stroke="#fff" stroke-width="1.4" stroke-opacity="0.55" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </svg></span></div>
  <div class="orb-label">Alfred</div>
  <div class="orb-nudge-tip" hidden>Tap to switch narrator voice</div>
</div>
```

- [ ] **Step 3: Replace the icon-swap logic in `applyPersonaToggle()` in `bullion_mkultra.html`**

Find this exact block:

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
```

Replace with:

```javascript
const ALFRED_ICON_SVG = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">' +
  '<path d="M7 15 L17 15 L17 17 L7 17 Z" fill="#fff" fill-opacity="0.55"/>' +
  '<path d="M9 6 L15 6 L15 15 L9 15 Z" fill="#fff" fill-opacity="0.55"/>' +
  '<path d="M9 8.5 L15 8.5 L15 9.5 L9 9.5 Z" fill="#fff" fill-opacity="0.35"/>' +
  '<path d="M17.5 16 L20.5 20 L19 22" stroke="#fff" stroke-width="1.4" stroke-opacity="0.55" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' +
  '</svg>';
const JOHNNY_ICON_SVG = '<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">' +
  '<path d="M12 2 L15.5 5.5 L12 9 L8.5 5.5 Z" fill="#fff" fill-opacity="0.55"/>' +
  '<path d="M6 8 L18 8 L20 13 L15.5 22 L8.5 22 L4 13 Z" fill="#fff" fill-opacity="0.55"/>' +
  '<path d="M12 8 L12 22" stroke="#fff" stroke-width="1" stroke-opacity="0.3" fill="none"/>' +
  '</svg>';
function applyPersonaToggle() {
  const orb = document.getElementById('persona-orb');
  if (!orb) return;
  const isJohnny = narrationPersona === 'johnny';
  orb.classList.toggle('persona-alfred', !isJohnny);
  orb.classList.toggle('persona-johnny', isJohnny);
  orb.querySelector('.orb-icon').innerHTML = isJohnny ? JOHNNY_ICON_SVG : ALFRED_ICON_SVG;
  orb.querySelector('.orb-label').textContent = isJohnny ? 'Johnny' : 'Alfred';
  orb.setAttribute('aria-label', 'Switch narration voice, currently ' + (isJohnny ? 'Johnny' : 'Alfred'));
}
```

(`applyPersonaToggle()` is called both on load and from `toggleNarrationPersona()` — this
change covers both paths in one place; no other call site touches `.orb-icon`.)

- [ ] **Step 4: Apply Steps 1-3 identically to `bullion_mk18.html`**

Same three old/new blocks, verbatim (confirmed byte-identical to `bullion_mkultra.html` at
these locations before writing this plan).

- [ ] **Step 5: Verify parity between the two files**

```bash
cd bullion-live-map
diff <(grep -A10 "ALFRED_ICON_SVG" bullion_mk18.html) <(grep -A10 "ALFRED_ICON_SVG" bullion_mkultra.html)
```

Expected: no output (identical).

- [ ] **Step 6: Screenshot-verify visually**

In `bullion_mkultra.html`: screenshot the orb showing Alfred's glyph (translucent top-hat
mark, legible at 24px, not a solid block). Click the orb to switch to Johnny, screenshot
again (translucent angular kabuto/samurai mark). Confirm neither glyph looks like a raw
emoji and both look like semi-transparent "frosted glass" shapes over the gradient
circle, per the design spec. Repeat both checks on `bullion_mk18.html`. If either glyph's
proportions look off at actual render size, adjust the path coordinates in place and
re-screenshot — the spec explicitly treats these coordinates as a starting point, not
pixel-final.

- [ ] **Step 7: Run the regression suite**

```bash
cd bullion-live-map
python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v
```

Expected: 96/96 passing, unchanged.

- [ ] **Step 8: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "Replace persona orb emoji with original translucent SVG glyphs"
```

---

## Final check

- [ ] Both files still open and render with no console errors (check via
  `read_console_messages` in the same Chrome tabs used for screenshots).
- [ ] `git status --short` shows only the two modified files staged/committed across both
  tasks — no accidental inclusion of the pre-existing untracked noise.
- [ ] Ask the user for their own live-browser look, same standing limitation as every
  prior orb change in this project (automation can't judge final visual/motion polish).
