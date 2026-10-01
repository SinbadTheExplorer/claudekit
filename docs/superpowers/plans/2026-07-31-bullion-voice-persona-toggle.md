# Bullion Voice Narration — Two-Persona Toggle, Captions & Autoplay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the `say`-CLI British-voice engine swap (spec'd but never implemented) together with the Alfred/Johnny persona toggle, synced captions, and session-scoped autoplay described in
`docs/superpowers/specs/2026-07-31-bullion-voice-persona-toggle-design.md`.

**Architecture:** `bullion-live-map/scripts/generate_narration.py` drops Chatterbox entirely in favor of shelling out to macOS `say` + `ffmpeg` via one shared `synthesize()` helper, used both for Alfred (39 nodes, text extracted from the live `NODES` array — unchanged extraction logic) and Johnny (6 pilot nodes, hand-written scripts hardcoded in the script). `bullion_mk18.html` and `bullion_mkultra.html` each get a parallel, independent set of edits (this project has no shared JS module between the two files — every prior narration change duplicated logic across both, and this plan does the same): a `JOHNNY_MANIFEST` + `JOHNNY_SCRIPTS` pair alongside the existing `NARRATION_MANIFEST`, a global persona-toggle button persisted to `localStorage`, a caption box driven by character-count-proportional word timing against the real `Audio.duration`, and `sessionStorage`-tracked first-open autoplay.

**Tech Stack:** Python 3 stdlib only (`subprocess`, no venv needed anymore — this is a **reduction** in dependencies vs. the Chatterbox pipeline), macOS `say` CLI, `ffmpeg` (already a dependency), vanilla JS (no build step, matches both HTML files' existing style), `unittest`.

## Global Constraints

- Voice: `say -v "Jamie (Premium)"` (`en_GB`) — must fail loudly (raise/non-zero exit), never silently fall back, if the voice is missing. (Spec: "Voice / generation approach"; v1 spec: "Error handling.")
- Alfred's rate: `-r 200` (carried over from the v1 spec, still unconfirmed by ear until Task 1's manual check).
- Johnny's rate: `-r 170`, explicitly provisional — must be confirmed by ear against at least one alternative before being treated as final (spec: "Risks / unverified").
- Johnny pilot scope is exactly `fed`, `gold`, `vix`, `sec`, `repo`, `yield` — no more, no fewer, until a future decision to expand (spec: "Personas").
- Every change touches **both** `bullion_mk18.html` and `bullion_mkultra.html` identically unless the plan says otherwise (this project's standing duplication convention).
- Never `git add .` / `-A` — this repo has substantial pre-existing untracked noise (`.claude/`, `.agents/`, `docs/superpowers/archive/`, `__pycache__/`, etc.); stage only the files each task actually touches.
- Audible correctness (does a clip actually sound right) is never automatable in this project — every task involving generated audio has an explicit "ask the user" step instead of an assertion.

---

## Task 1: Engine swap — Alfred only (Chatterbox → `say` CLI)

**Files:**
- Modify: `bullion-live-map/scripts/generate_narration.py`
- Test: `bullion-live-map/scripts/test_generate_narration.py` (no changes needed this task — verifying it still passes unchanged is the check)

**Interfaces:**
- Produces: `synthesize(text: str, rate: int, output_mp3_path: Path) -> None` — shells `say` then `ffmpeg`, raises `RuntimeError` on failure. `SAY_VOICE: str`, `ALFRED_RATE: int` module constants. `extract_node_texts()` unchanged (still consumed by the test suite exactly as today).

- [ ] **Step 1: Replace the module header and drop the Chatterbox/`VOICE_SAMPLE` constants**

Edit `bullion-live-map/scripts/generate_narration.py` lines 1–19 (docstring + imports + `VOICE_SAMPLE`) to:

```python
#!/usr/bin/env python3
"""Generates narration MP3s via macOS's `say` CLI: Alfred (butler, all 39
nodes, factual on-page text extracted from bullion_mk18.html's live NODES
array) and Johnny (rocker, 6 pilot nodes, hand-written scripts hardcoded in
this file). Replaces the original Chatterbox voice-cloning engine, dropped
after the cloned voice was found to carry the wrong accent."""
import html
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "audio" / "narration"
SOURCE_HTML = ROOT / "bullion_mk18.html"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

SAY_VOICE = "Jamie (Premium)"
ALFRED_RATE = 200
```

(Leave `PROBE_SCRIPT`, `TITLE_RE`, `DUMP_TIMEOUT`, `EXIT_GRACE`, and `extract_node_texts()` — lines 21–117 in the current file — completely untouched.)

- [ ] **Step 2: Replace `main()` and add the `synthesize()` helper**

Replace the current `main()` (the block starting `def main():` through the end of the file, currently lines 120–156) with:

```python
def synthesize(text, rate, output_mp3_path):
    """Runs `say` at the given words-per-minute rate and converts the output
    to MP3 via ffmpeg. Fails loudly (raises RuntimeError) if the voice is
    missing or either subprocess errors — never falls back silently."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff_path = Path(tmp.name)
    try:
        try:
            subprocess.run(
                ["say", "-v", SAY_VOICE, "-r", str(rate), "-o", str(aiff_path), text],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f'`say -v "{SAY_VOICE}"` failed (exit {e.returncode}). Is the '
                f'"{SAY_VOICE}" voice installed? System Settings -> Accessibility -> '
                "Spoken Content -> System Voice -> Manage Voices."
            ) from e
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(aiff_path),
             "-codec:a", "libmp3lame", "-qscale:a", "2", str(output_mp3_path)],
            check=True,
        )
    finally:
        aiff_path.unlink(missing_ok=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nodes = extract_node_texts(SOURCE_HTML)
    print(f"Extracted {len(nodes)} node texts from {SOURCE_HTML.name}")
    for node in nodes:
        out = OUTPUT_DIR / f"node-{node['id']}.mp3"
        synthesize(node["text"], ALFRED_RATE, out)
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Sanity-check the `say` voice exists before running the full generation**

Run: `say -v "Jamie (Premium)" -o /tmp/bullion-voice-check.aiff "Testing the Jamie Premium voice." && afplay /tmp/bullion-voice-check.aiff`
Expected: plays a British voice reading the test sentence. If `say` errors here, stop — the voice isn't installed (System Settings → Accessibility → Spoken Content → Manage Voices) and nothing past this point will work.

- [ ] **Step 4: Run the existing extraction tests to confirm no regression**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`
Expected: `TestExtractNodeTexts` and `TestHtmlEntityRoundTrip` PASS (unaffected — `extract_node_texts` wasn't touched). `TestManifestCompleteness.test_every_manifest_file_exists_and_nonempty` will currently still PASS too, since it only checks the *old* Chatterbox files still exist on disk — that's expected; Step 5 replaces them in place.

- [ ] **Step 5: Regenerate all 39 Alfred clips**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 scripts/generate_narration.py`
Expected: 39 lines of `wrote .../audio/narration/node-<id>.mp3`, no traceback. No venv needed — this no longer imports `torchaudio`/`chatterbox`, plain `python3` works. This should take well under a minute (`say` is near-instant per clip, unlike the old CPU-bound Chatterbox inference).

- [ ] **Step 6: Re-run the test suite against the regenerated files**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`
Expected: all tests PASS, same count as Step 4 — now against real `say`-generated files instead of the old Chatterbox ones.

- [ ] **Step 7: Ask the user to confirm the voice sounds right (cannot be automated)**

Run: `afplay ~/claude-projects/claudekit/bullion-live-map/audio/narration/node-fed.mp3`
Ask the user: does this sound like the intended British "Jamie (Premium)" voice, at a natural pace, clearly the *actual* voice replacing the bad-accent Chatterbox clone? Do not proceed to Task 2 until they confirm — if it sounds wrong, this is a Task 1 bug (wrong voice name, wrong rate), not something to paper over.

- [ ] **Step 8: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/generate_narration.py bullion-live-map/audio/narration/
git commit -m "$(cat <<'EOF'
Swap narration engine from Chatterbox clone to macOS say (Alfred)

Implements the v1 design (docs/superpowers/specs/2026-07-31-bullion-voice-british-swap-design.md),
which was spec'd but never actually implemented. Regenerates all 39
Alfred clips via say -v "Jamie (Premium)" -r 200, replacing the
Chatterbox-cloned audio the user reported sounding like it had the
wrong accent.
EOF
)"
```

---

## Task 2: Johnny generation — scripts, rate, and pilot clips

**Files:**
- Modify: `bullion-live-map/scripts/generate_narration.py`

**Interfaces:**
- Consumes: `synthesize(text, rate, output_mp3_path)` from Task 1.
- Produces: `JOHNNY_SCRIPTS: dict[str, str]` (6 entries, keys `fed`, `gold`, `vix`, `sec`, `repo`, `yield`) and `JOHNNY_RATE: int` module constants — Task 3's tests and Task 4's front-end work both depend on these exact names and the exact 6 keys.

- [ ] **Step 1: Add `JOHNNY_RATE` and `JOHNNY_SCRIPTS`**

Insert immediately after `ALFRED_RATE = 200` in `generate_narration.py`:

```python
JOHNNY_RATE = 170  # provisional — confirmed against ALFRED_RATE by ear in Task 2, Step 2

JOHNNY_SCRIPTS = {
    "fed": "They call it the Federal Reserve. I call it the biggest chrome-plated puppet show in the world — a room full of suits who print money out of thin air and decide who eats and who don't. Rates go up, rates go down, and every time some corpo uptown gets richer while the street picks up the tab. Keeps prices 'stable,' they say. Sure. Stable for them.",
    "gold": "Gold. Old-world chrome, choom — no batteries, no code, can't be hacked, can't be printed. When the suits panic and the dollar starts bleeding out, everybody runs for the shiny rock like it's the last exit off a burning highway. Ironic, right? Most advanced economy on the planet, and when it all goes sideways, we're back to digging up shiny metal.",
    "vix": "They call it the fear index. I call it the market's heart-rate monitor right before a flatline. Number's low, everybody's cruising, thinks the good times never end. Number spikes past thirty — that's panic, choom, suits sprinting for the exits, dumping everything, prices crashing like a bad cyberware job.",
    "sec": "SEC. Supposed to be the cops on the beat, keeping the corpos honest. Half the time they're a step behind, chasing paper trails after the damage's already done. But pull 'em out of the picture and it's open season — little guy's holding a busted contract while the suits count their cut.",
    "repo": "Repo market. Nobody talks about it 'cause it's boring — banks trading bonds for cash overnight, greasing the wheels so the whole system doesn't seize up. But pull that plug, choom, everything stops. No headlines, no warning — just the whole city going dark 'cause the wiring underneath finally gave out.",
    "yield": "Yield curve. Line on a chart nobody looks at till it flips upside down — then suddenly everybody's screaming recession. Funny thing about the future: it's usually cheaper to borrow for than the present. When that flips, smart money thinks tomorrow's rough. Pay attention when it inverts, choom. The suits sure do.",
}
```

- [ ] **Step 2: Generate two rate variants of one script and ask the user to pick before touching `main()`**

Run:
```bash
cd ~/claude-projects/claudekit/bullion-live-map
say -v "Jamie (Premium)" -r 170 -o /tmp/johnny_r170.aiff "Gold. Old-world chrome, choom, no batteries, no code, can't be hacked, can't be printed."
say -v "Jamie (Premium)" -r 150 -o /tmp/johnny_r150.aiff "Gold. Old-world chrome, choom, no batteries, no code, can't be hacked, can't be printed."
afplay /tmp/johnny_r170.aiff && afplay /tmp/johnny_r150.aiff
```
Ask the user which rate (170 or 150, or a different number entirely) sounds like the "slower/looser" rocker delivery they described, versus Alfred's crisper `-r 200`. Update `JOHNNY_RATE` in `generate_narration.py` to whatever they pick before continuing — this is the confirmation the spec flagged as unresolved; do not skip it.

- [ ] **Step 3: Extend `main()` to generate Johnny's clips**

In `generate_narration.py`, add after the existing Alfred `for node in nodes:` loop inside `main()`:

```python
    for node_id, script in JOHNNY_SCRIPTS.items():
        out = OUTPUT_DIR / f"johnny-{node_id}.mp3"
        synthesize(script, JOHNNY_RATE, out)
        print(f"wrote {out}")
```

- [ ] **Step 4: Run generation and confirm all 6 Johnny clips are produced**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 scripts/generate_narration.py`
Expected: the existing 39 `node-<id>.mp3` lines, plus 6 new `johnny-<id>.mp3` lines (`johnny-fed.mp3`, `johnny-gold.mp3`, `johnny-vix.mp3`, `johnny-sec.mp3`, `johnny-repo.mp3`, `johnny-yield.mp3`).

- [ ] **Step 5: Ask the user to confirm Johnny sounds right (cannot be automated)**

Run: `afplay ~/claude-projects/claudekit/bullion-live-map/audio/narration/johnny-fed.mp3`
Ask the user: does the persona land — same British voice as Alfred, but a distinctly slower/looser rocker delivery, with the script's attitude coming through? If not, adjust `JOHNNY_RATE` and regenerate (Step 4) before moving on.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/generate_narration.py bullion-live-map/audio/narration/
git commit -m "$(cat <<'EOF'
Add Johnny rocker persona: 6 pilot scripts and generated clips

Hand-written scripts (Cyberpunk 2077 Johnny Silverhand register,
applied to each pilot node's actual financial content) for fed, gold,
vix, sec, repo, yield. Rate confirmed by ear against Alfred's -r 200.
EOF
)"
```

---

## Task 3: Automated tests for Johnny coverage and JS/Python sync

**Files:**
- Modify: `bullion-live-map/scripts/test_generate_narration.py`

**Interfaces:**
- Consumes: `gn.JOHNNY_SCRIPTS` (Task 2). `JOHNNY_MANIFEST` and `JOHNNY_SCRIPTS` JS object literals in both HTML files (Task 4 — written next, but these tests are written first per TDD and will fail until Task 4 lands; that's expected and correct for this step).
- Produces: `_js_object_keys(html_path, const_name)` and `_johnny_scripts_from_html(html_path)` helpers, generalized from the existing `_manifest_ids` so Task 4+ front-end work has a regression check.

- [ ] **Step 1: Generalize the existing `_manifest_ids` helper**

In `test_generate_narration.py`, replace the `TestManifestCompleteness._manifest_ids` method:

```python
    def _manifest_ids(self, html_path):
        text = html_path.read_text()
        start = text.index("const NARRATION_MANIFEST = {")
        end = text.index("};", start)
        body = text[start:end]
        return set(re.findall(r"^\s*(\w+):", body, re.M))
```

with a module-level, reusable version (delete the method from the class, add this at module scope near the top, after the `ROOT = ...` line):

```python
def _js_object_keys(html_path, const_name):
    text = html_path.read_text()
    start = text.index(f"const {const_name} = {{")
    end = text.index("};", start)
    body = text[start:end]
    return set(re.findall(r"^\s*(\w+):", body, re.M))


def _johnny_scripts_from_html(html_path):
    text = html_path.read_text()
    start = text.index("const JOHNNY_SCRIPTS = {")
    end = text.index("};", start)
    body = text[start:end]
    return dict(re.findall(r'(\w+):\s*"((?:\\.|[^"\\])*)"', body))
```

Then update the two call sites inside `TestManifestCompleteness` that used `self._manifest_ids(...)` to call `_js_object_keys(..., "NARRATION_MANIFEST")` instead:

```python
    def test_mk18_manifest_covers_every_node(self):
        nodes = gn.extract_node_texts(ROOT / "bullion_mk18.html")
        node_ids = {n["id"] for n in nodes}
        manifest_ids = _js_object_keys(ROOT / "bullion_mk18.html", "NARRATION_MANIFEST")
        self.assertEqual(node_ids, manifest_ids)

    def test_mkultra_manifest_covers_every_node(self):
        nodes = gn.extract_node_texts(ROOT / "bullion_mkultra.html")
        node_ids = {n["id"] for n in nodes}
        manifest_ids = _js_object_keys(ROOT / "bullion_mkultra.html", "NARRATION_MANIFEST")
        self.assertEqual(node_ids, manifest_ids)
```

- [ ] **Step 2: Run the suite to confirm this refactor alone doesn't break anything**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`
Expected: same PASS count as Task 1 Step 6 — this step only renamed/relocated a helper, no behavior change.

- [ ] **Step 3: Add the `TestJohnnyPersona` test class**

Append to `test_generate_narration.py`, before the `if __name__ == "__main__":` line:

```python
class TestJohnnyPersona(unittest.TestCase):
    """Guards Johnny's pilot scope and the Python/JS text duplication this
    persona deliberately reintroduces (see the design spec's rationale) —
    every place Johnny's script text lives must agree exactly."""

    EXPECTED_IDS = {"fed", "gold", "vix", "sec", "repo", "yield"}

    def test_johnny_scripts_cover_exactly_the_pilot_six(self):
        self.assertEqual(set(gn.JOHNNY_SCRIPTS.keys()), self.EXPECTED_IDS)

    def test_every_johnny_script_is_nonempty(self):
        for node_id, script in gn.JOHNNY_SCRIPTS.items():
            self.assertTrue(script.strip(), f"empty Johnny script for {node_id}")

    def test_every_johnny_clip_exists_and_nonempty(self):
        for node_id in gn.JOHNNY_SCRIPTS:
            f = ROOT / "audio" / "narration" / f"johnny-{node_id}.mp3"
            self.assertTrue(f.exists(), f"missing {f}")
            self.assertGreater(f.stat().st_size, 0, f"empty {f}")

    def test_mk18_johnny_manifest_matches_johnny_scripts_keys(self):
        ids = _js_object_keys(ROOT / "bullion_mk18.html", "JOHNNY_MANIFEST")
        self.assertEqual(ids, set(gn.JOHNNY_SCRIPTS.keys()))

    def test_mkultra_johnny_manifest_matches_johnny_scripts_keys(self):
        ids = _js_object_keys(ROOT / "bullion_mkultra.html", "JOHNNY_MANIFEST")
        self.assertEqual(ids, set(gn.JOHNNY_SCRIPTS.keys()))

    def test_mk18_johnny_caption_text_matches_python(self):
        js_scripts = _johnny_scripts_from_html(ROOT / "bullion_mk18.html")
        self.assertEqual(js_scripts, gn.JOHNNY_SCRIPTS)

    def test_mkultra_johnny_caption_text_matches_python(self):
        js_scripts = _johnny_scripts_from_html(ROOT / "bullion_mkultra.html")
        self.assertEqual(js_scripts, gn.JOHNNY_SCRIPTS)
```

- [ ] **Step 4: Run the suite and confirm the new tests fail for the expected reason**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`
Expected: `test_johnny_scripts_cover_exactly_the_pilot_six` and the nonempty/file-existence tests PASS (Task 2 already satisfies these). The four `mk18`/`mkultra` manifest/caption-text tests FAIL with a `ValueError`/`substring not found` from `_js_object_keys`/`_johnny_scripts_from_html` — expected, since `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS` don't exist in either HTML file yet. This is the correct red state; Task 4 turns it green.

- [ ] **Step 5: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/test_generate_narration.py
git commit -m "$(cat <<'EOF'
Add Johnny coverage and JS/Python text-sync tests

Extends the existing manifest-completeness pattern to Johnny's 6-node
pilot, plus a new check that the hand-written scripts embedded in both
HTML files (for captions) stay byte-identical to generate_narration.py's
copy. Four of the new tests are expected to fail until Task 4 adds
JOHNNY_MANIFEST/JOHNNY_SCRIPTS to the front end.
EOF
)"
```

---

## Task 4: Front-end — `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS` and the persona toggle

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `gn.JOHNNY_SCRIPTS` text (Task 2) — must be copied verbatim into both files' JS `JOHNNY_SCRIPTS` object.
- Produces: `resolveNarration(d)` returning `{file, persona, text}`; `playCurrentNarration(d)`; `narrationPersona` module-level state (`'alfred'`|`'johnny'`) — Task 5 (captions) and Task 6 (autoplay) both call `playCurrentNarration(d)`.

Apply the following edits **identically to both `bullion_mk18.html` and `bullion_mkultra.html`** (line numbers below are from `bullion_mkultra.html` at current HEAD; `bullion_mk18.html`'s equivalents are ~250 lines earlier but textually identical at each anchor).

- [ ] **Step 1: Add the persona-toggle button to the header toolbar**

Find the header-controls row containing `id="mode-toggle-btn"` (mkultra line 575, mk18 line 523). Insert immediately before that button:

```html
      <button class="btn" id="persona-toggle-btn" title="Switch narration voice between Alfred (butler) and Johnny (rocker)">&#127908; Alfred</button>
```

- [ ] **Step 2: Add `JOHNNY_MANIFEST` and `JOHNNY_SCRIPTS` next to `NARRATION_MANIFEST`**

Find `const NARRATION_MANIFEST = {` (mkultra line 3987, mk18 line 3324). Immediately after its closing `};`, insert:

```javascript
// Johnny (rocker persona) pilot: 6 nodes only, hand-written flavor text
// (deliberately NOT the factual page copy — see
// docs/superpowers/specs/2026-07-31-bullion-voice-persona-toggle-design.md).
// JOHNNY_SCRIPTS must stay byte-identical to generate_narration.py's copy —
// tested by scripts/test_generate_narration.py.
const JOHNNY_MANIFEST = {
  fed:   'johnny-fed.mp3',
  gold:  'johnny-gold.mp3',
  vix:   'johnny-vix.mp3',
  sec:   'johnny-sec.mp3',
  repo:  'johnny-repo.mp3',
  yield: 'johnny-yield.mp3',
};
const JOHNNY_SCRIPTS = {
  fed: "They call it the Federal Reserve. I call it the biggest chrome-plated puppet show in the world — a room full of suits who print money out of thin air and decide who eats and who don't. Rates go up, rates go down, and every time some corpo uptown gets richer while the street picks up the tab. Keeps prices 'stable,' they say. Sure. Stable for them.",
  gold: "Gold. Old-world chrome, choom — no batteries, no code, can't be hacked, can't be printed. When the suits panic and the dollar starts bleeding out, everybody runs for the shiny rock like it's the last exit off a burning highway. Ironic, right? Most advanced economy on the planet, and when it all goes sideways, we're back to digging up shiny metal.",
  vix: "They call it the fear index. I call it the market's heart-rate monitor right before a flatline. Number's low, everybody's cruising, thinks the good times never end. Number spikes past thirty — that's panic, choom, suits sprinting for the exits, dumping everything, prices crashing like a bad cyberware job.",
  sec: "SEC. Supposed to be the cops on the beat, keeping the corpos honest. Half the time they're a step behind, chasing paper trails after the damage's already done. But pull 'em out of the picture and it's open season — little guy's holding a busted contract while the suits count their cut.",
  repo: "Repo market. Nobody talks about it 'cause it's boring — banks trading bonds for cash overnight, greasing the wheels so the whole system doesn't seize up. But pull that plug, choom, everything stops. No headlines, no warning — just the whole city going dark 'cause the wiring underneath finally gave out.",
  yield: "Yield curve. Line on a chart nobody looks at till it flips upside down — then suddenly everybody's screaming recession. Funny thing about the future: it's usually cheaper to borrow for than the present. When that flips, smart money thinks tomorrow's rough. Pay attention when it inverts, choom. The suits sure do.",
};
```

- [ ] **Step 3: Add persona state, `resolveNarration`, and `playCurrentNarration`, right after `playNarration`**

Find `function playNarration(file) { ... }` (mkultra line 4032, mk18 line 3365). Immediately after its closing `}`, insert:

```javascript
let narrationPersona = localStorage.getItem('bullion-narration-persona') === 'johnny' ? 'johnny' : 'alfred';
function applyPersonaToggle() {
  const btn = document.getElementById('persona-toggle-btn');
  if (!btn) return;
  btn.innerHTML = narrationPersona === 'johnny' ? '&#127908; Johnny' : '&#127908; Alfred';
  btn.classList.toggle('active', narrationPersona === 'johnny');
}
document.getElementById('persona-toggle-btn').addEventListener('click', function() {
  narrationPersona = narrationPersona === 'alfred' ? 'johnny' : 'alfred';
  localStorage.setItem('bullion-narration-persona', narrationPersona);
  applyPersonaToggle();
});
applyPersonaToggle();

function resolveNarration(d) {
  if (narrationPersona === 'johnny' && JOHNNY_MANIFEST[d.id]) {
    return { file: JOHNNY_MANIFEST[d.id], persona: 'JOHNNY', text: JOHNNY_SCRIPTS[d.id] };
  }
  return { file: NARRATION_MANIFEST[d.id], persona: 'ALFRED', text: (d.beginner || []).join(' ') };
}
function playCurrentNarration(d) {
  const resolved = resolveNarration(d);
  if (!resolved.file) return;
  playNarration(resolved.file);
}
```

(`playCurrentNarration` only uses `resolved.file` for now — Task 5 extends `playNarration`'s signature and this call site together.)

- [ ] **Step 4: Rewire `openDetail()`'s narrate-button click handler**

Find, inside `openDetail(d)` (mkultra line 2614, mk18 line 1968):

```javascript
      narrateBtn.onclick = function() { playNarration(NARRATION_MANIFEST[d.id]); };
```

Replace with:

```javascript
      narrateBtn.onclick = function() { playCurrentNarration(d); };
```

- [ ] **Step 5: Manually verify the toggle actually switches audio**

This is UI behavior with no automated test in this project (per the standing "audible correctness can't be automated" idiom) — verify by hand:
1. Serve the files: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m http.server 8791` (or reuse a server already running, per the project's existing dev convention — check with `lsof -i :8791` first).
2. Open `http://localhost:8791/bullion_mkultra.html` in Chrome, open dev tools console (expect 0 errors on load).
3. Click the new "🎤 Alfred" button — it should read "🎤 Johnny" and highlight after one click.
4. Open the "fed" node, click 🔊 — confirm (by ear) it now plays the Johnny clip, not Alfred's.
5. Toggle back to Alfred, open "fed" again, click 🔊 — confirm it plays Alfred's clip again.
6. Open a node with no Johnny clip (e.g. "cftc" — not one of the 6 piloted nodes) while toggled to Johnny — confirm it falls back to playing Alfred's clip for that node.
7. Repeat steps 2–6 against `bullion_mk18.html`.
Report the outcome; do not proceed to Task 5 until this passes.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Add Alfred/Johnny persona toggle to both HTML files

Global, localStorage-persisted toggle in the header; JOHNNY_MANIFEST
+ JOHNNY_SCRIPTS alongside the existing NARRATION_MANIFEST; narrate
button now resolves the active persona per node, falling back to
Alfred for the 33 nodes without a Johnny clip.
EOF
)"
```

---

## Task 5: Front-end — captions

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `playCurrentNarration(d)` / `resolveNarration(d)` from Task 4.
- Produces: `playNarration(file, persona, text)` (persona/text now optional — existing 1-arg field-note call sites keep working, captions simply don't render for them), `startCaption(persona, text, duration)`, `clearCaption()`.

Apply identically to both files.

- [ ] **Step 1: Add the caption box markup**

Find `<div class="detail-live" id="detail-live"></div>` (mkultra line 605 area — inside `#detail-body`; mk18 line 553). Immediately after it, insert:

```html
    <div id="detail-caption" hidden></div>
```

- [ ] **Step 2: Add caption CSS**

Find the `.narrate-btn:hover { ... }` rule (mkultra line 217, mk18 line 188). Immediately after it, insert:

```css
  #detail-caption { margin: 8px 0; padding: 6px 8px; border-radius: 6px; background: var(--bg-panel2); border: 1px solid var(--border); font-size: 12px; line-height: 1.5; }
  #detail-caption[hidden] { display: none; }
  .caption-persona { color: var(--gold); font-weight: 700; margin-right: 4px; }
  .caption-words { color: var(--text); }
```

- [ ] **Step 3: Extend `playNarration` with caption support, and add `startCaption`/`clearCaption`**

Find `function playNarration(file) { ... }` (mkultra line 4032, mk18 line 3365) and replace the whole function with:

```javascript
let captionTimeouts = [];
function clearCaption() {
  captionTimeouts.forEach(clearTimeout);
  captionTimeouts = [];
  const host = document.getElementById('detail-caption');
  if (host) { host.hidden = true; host.innerHTML = ''; }
}
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
function playNarration(file, persona, text) {
  clearCaption();
  const audio = new Audio('audio/narration/' + file);
  if (persona && text) {
    audio.addEventListener('loadedmetadata', function() {
      startCaption(persona, text, audio.duration);
    });
  }
  audio.play().catch(function(err) {
    console.warn('Narration playback failed:', err);
  });
  return audio;
}
```

(Field-note narration call sites — e.g. mkultra's `onclick="playNarration('...')"` for `credit-equit`/`usd-oil`, line 2567 — keep calling `playNarration(file)` with one argument; `persona`/`text` are simply `undefined`, so `startCaption` never runs for those and behavior is unchanged. `bullion_mk18.html` has no field-note links, so this doesn't apply there.)

- [ ] **Step 4: Wire `playCurrentNarration` to pass persona and text**

Find `function playCurrentNarration(d) { ... }` (added in Task 4, Step 3) and replace its body:

```javascript
function playCurrentNarration(d) {
  const resolved = resolveNarration(d);
  if (!resolved.file) return;
  playNarration(resolved.file, resolved.persona, resolved.text);
}
```

- [ ] **Step 5: Clear captions when the detail panel closes**

Find `function closeDetail() { ... }` (mkultra line 2653, mk18 line 2006). Add `clearCaption();` as the first line inside the function body:

```javascript
function closeDetail() {
  clearCaption();
  openDetailNode = null;
  document.getElementById('detail-panel').classList.remove('open');
  document.getElementById('app').classList.remove('panel-open');
}
```

- [ ] **Step 6: Manually verify captions**

1. Serve and open both files as in Task 4 Step 5.
2. Open "fed", click 🔊 — confirm a caption box appears labeled "ALFRED:" and words fill in roughly in sync with the audio, finishing at or near when the clip ends.
3. Toggle to Johnny, reopen "fed", click 🔊 — confirm the label reads "JOHNNY:" and the rocker script's words appear.
4. Toggle to Johnny, open a non-piloted node (e.g. "cftc"), click 🔊 — confirm the caption reads "ALFRED:" (matching the fallback audio), not "JOHNNY:".
5. Close the panel mid-playback (click the × or open a different node) — confirm no further caption words appear after closing (no leaked `setTimeout`s writing into a hidden caption box).
6. Click a field-note 🔊 button in `bullion_mkultra.html` (e.g. under a node touching `credit→equit`) — confirm it still plays audio with 0 console errors and no caption box appears (expected — field notes aren't captioned, see Step 3's note).
Report the outcome before proceeding to Task 6.

- [ ] **Step 7: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Add synced captions to narration playback

Caption box labeled by the persona actually speaking, words revealed
via estimated character-count-proportional timing against the clip's
real duration (Audio.loadedmetadata) — true API word timing was a
confirmed dead end in prior brainstorming. Field-note clips are
unaffected (no caption, matching pilot scope).
EOF
)"
```

---

## Task 6: Front-end — session-scoped autoplay

**Files:**
- Modify: `bullion-live-map/bullion_mk18.html`
- Modify: `bullion-live-map/bullion_mkultra.html`

**Interfaces:**
- Consumes: `playCurrentNarration(d)` (Task 4/5).
- Produces: `maybeAutoplayNarration(d)`, called from `openDetail()`.

Apply identically to both files.

- [ ] **Step 1: Add `maybeAutoplayNarration`**

Find `function playCurrentNarration(d) { ... }` (Task 5, Step 4). Immediately after its closing `}`, insert:

```javascript
function maybeAutoplayNarration(d) {
  const key = 'bullion-narration-autoplayed';
  let seen;
  try { seen = JSON.parse(sessionStorage.getItem(key) || '[]'); } catch (e) { seen = []; }
  if (seen.includes(d.id)) return;
  seen.push(d.id);
  sessionStorage.setItem(key, JSON.stringify(seen));
  playCurrentNarration(d);
}
```

- [ ] **Step 2: Call it from `openDetail()` when a narration clip exists**

Find, inside `openDetail(d)` (Task 4, Step 4 left this in place):

```javascript
      narrateBtn.hidden = false;
      narrateBtn.onclick = function() { playCurrentNarration(d); };
```

Replace with:

```javascript
      narrateBtn.hidden = false;
      narrateBtn.onclick = function() { playCurrentNarration(d); };
      maybeAutoplayNarration(d);
```

- [ ] **Step 3: Manually verify autoplay fires once per node per session**

1. Serve and open `bullion_mkultra.html` fresh (or clear `sessionStorage` via dev tools first: `sessionStorage.clear()`).
2. Click into the "fed" node for the first time — confirm narration plays automatically without clicking 🔊, and the caption appears in sync.
3. Close the panel, reopen "fed" again in the same tab — confirm it does NOT autoplay this time (silent), but 🔊 still works for manual replay.
4. Open a different node, e.g. "gold", for the first time — confirm it autoplays.
5. Reload the page (same tab, so `sessionStorage` persists) and reopen "fed" — confirm it still does NOT autoplay (session survived the reload).
6. Open a new tab (fresh `sessionStorage`) and open "fed" — confirm it autoplays again (new session).
7. Repeat steps 1–4 against `bullion_mk18.html`.
Report the outcome before considering this task done.

- [ ] **Step 4: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/bullion_mk18.html bullion-live-map/bullion_mkultra.html
git commit -m "$(cat <<'EOF'
Add session-scoped autoplay on first node open

Narration plays automatically the first time a node is opened per
browser-tab session (sessionStorage-tracked, survives reloads);
reopening later stays silent, manual replay via the existing button
button is unaffected.
EOF
)"
```

---

## Task 7: Full manual regression pass and push decision

**Files:** none (verification only)

- [ ] **Step 1: Run the full Python suite**

Run: `cd ~/claude-projects/claudekit/bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`
Expected: all PASS, including every `TestJohnnyPersona` test from Task 3 (now green, since Tasks 4–5 supplied `JOHNNY_MANIFEST`/`JOHNNY_SCRIPTS` in both HTML files).

- [ ] **Step 2: Full manual click-through in real Chrome, both files**

For each of `bullion_mk18.html` and `bullion_mkultra.html`:
1. Load with dev tools open — confirm 0 console errors.
2. Click through several narrated nodes across different layers (not just the 6 Johnny-piloted ones) in both Alfred and Johnny toggle states — confirm audio, captions, and the Alfred-fallback behavior all hold up outside the 6 pilot nodes too.
3. Confirm the persona toggle button's label ("🎤 Alfred" / "🎤 Johnny") and highlight state persist correctly across a page reload (via `localStorage`).

- [ ] **Step 3: Ask the user whether to push now**

Per the spec and this project's standing convention (fail loudly, never silently ship), ask the user: push `main` to `origin` now (bundling this work with the still-unpushed `cf95f9c` spec commit and Tasks 1–6), or hold? Do not push without an explicit answer.

---

## Self-Review Notes

- **Spec coverage:** Personas/scripts (Task 2), toggle+localStorage (Task 4), captions+estimated timing (Task 5), autoplay+sessionStorage (Task 6), generation script + drift-guard tests (Tasks 1–3), fallback-caption-label rule (Task 4 Step 3 / Task 5 Step 6.4), field notes excluded from Johnny/captions (Task 5 Step 3 note) — all spec sections have a task.
- **Type/name consistency checked:** `synthesize(text, rate, output_mp3_path)` (Task 1) used identically in Task 2. `resolveNarration(d)` / `playCurrentNarration(d)` (Task 4) signatures unchanged through Tasks 5–6. `playNarration(file, persona, text)` (Task 5) call sites all updated together with the definition in the same task. `JOHNNY_SCRIPTS`/`JOHNNY_MANIFEST` key sets identical across Python (Task 2) and both HTML files (Task 4), enforced by Task 3's tests.
- **No placeholders:** every step has literal runnable code or an exact shell command; the two genuinely unresolved values (Johnny's rate, whether to push at the end) are handled as explicit "ask the user" steps, not TODOs.
