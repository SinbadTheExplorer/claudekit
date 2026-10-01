# Bullion Narration Voice-Conversion Blend ("Thamie") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reduce the reported "robotic/synthetic" quality of Bullion's `say`-CLI narration by adding a voice-conversion pass (via `ChatterboxVC`) that re-colors Alfred's and Johnny's timbre toward a blend of reference voices, plus a small Johnny-only pitch-down for more spite, without changing pronunciation, timing, or the front-end.

**Architecture:** Two-stage generation in `generate_narration.py`: Stage 1 (unchanged) — `say -v "Jamie (Premium)"` generates content audio at each persona's tuned rate. Stage 2 (new) — that audio is run through `ChatterboxVC`, converting its timbre against a persona-specific *blended* target: Alfred averages the speaker x-vector of `Jamie (Premium)` + the user's own voice; Johnny averages `Tom (Enhanced)` + the user's own voice + `Jamie (Premium)`. Only the fixed-size x-vector is averaged — the variable-length acoustic prompt (`prompt_token`/`prompt_feat`) is taken from a single designated clip (the user's own voice) to avoid blending mismatched spectrograms. Johnny's converted output then gets one further step: a -1.5 semitone pitch-down for a meaner edge (Alfred is untouched by this). Output contract (filenames, `OUTPUT_DIR`) is unchanged; front-end needs zero changes since caption/pulse timing derives from `audio.duration` at playback time.

**Tech Stack:** Python 3.12, `chatterbox-tts` (`ChatterboxVC`), `torch`, `librosa`, `soundfile` — all already installed in `bullion-live-map/.venv-narration` (leftover from the original Chatterbox engine, confirmed present, no new dependency to install). macOS `say` CLI (`Jamie (Premium)`, `Tom (Enhanced)` — both confirmed installed via `say -v '?'`). `ffmpeg` (already a dependency of the existing script).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-01-bullion-thamie-voice-blend-design.md` — read it before starting; this plan implements it exactly, including its 2026-08-01 correction (average only the x-vector `embedding`, not the whole `ref_dict`).
- **Environment split, load-bearing for every task below:** `generate_narration.py` currently has zero third-party imports and its existing test suite runs under plain system `python3` (confirmed: `/opt/homebrew/bin/python3` has no `torch` installed). This plan adds voice-conversion functions that need `torch`/`librosa`/`soundfile`/`chatterbox` — **those imports must be lazy (inside the function bodies that need them), not at module top level**, so the existing fast tests keep running under plain `python3` unmodified. Anything that actually loads `ChatterboxVC` or calls the new blend functions — the new test file, the spike script, and real narration generation — must run under `.venv-narration/bin/python3`, never plain `python3`.
- No front-end changes anywhere in this plan (confirmed engine-agnostic caption/pulse sync — see spec's "Front-end wiring" section).
- No UI toggle, no pitch/formant differentiation beyond the rate split and Johnny's single -1.5 semitone pitch-down, no new `user_voice.wav` recording — see spec's "Explicitly not building".
- Fail loudly, no silent fallback — matches the existing script's posture (missing voice raises `RuntimeError`, same class of failure for a missing reference clip or missing `user_voice.wav`).
- Audible quality is **never automatable** — every task below that touches actual sound ends in a human listening step, not an automated pass/fail.

---

### Task 1: Feasibility spike — validate the blend mechanism (hard gate)

**Files:**
- Create: `bullion-live-map/scripts/spike_voice_blend.py` (throwaway — self-contained, not imported by production code, safe to delete once this task's gate passes)

**Interfaces:**
- Consumes: `bullion-live-map/audio/voice_sample/user_voice.wav` (existing), `bullion-live-map/audio/narration/node-fed.mp3` and `johnny-fed.mp3` (existing, already-committed clips).
- Produces: two listenable files on disk (paths printed by the script) for the user to judge by ear. Nothing here is consumed by later tasks — Task 2 reimplements the validated logic as production code with tests, deliberately not importing this throwaway script.

- [ ] **Step 1: Write the spike script**

```python
#!/usr/bin/env python3
"""Throwaway spike: validates the embedding-averaging voice-blend mechanism
before any of it is wired into generate_narration.py for real. Produces two
converted clips for a human listening test — see
docs/superpowers/specs/2026-08-01-bullion-thamie-voice-blend-design.md's
"Feasibility spike" section. Run with .venv-narration/bin/python3, not plain
python3 (needs torch/chatterbox, which are not installed for system python3).
"""
import subprocess
import tempfile
from pathlib import Path

import librosa
import soundfile as sf
import torch
from chatterbox.vc import ChatterboxVC, S3GEN_SR

ROOT = Path(__file__).resolve().parent.parent
VOICE_SAMPLE_DIR = ROOT / "audio" / "voice_sample"
USER_VOICE_PATH = VOICE_SAMPLE_DIR / "user_voice.wav"
TOM_SAMPLE_PATH = VOICE_SAMPLE_DIR / "tom_sample.wav"
JAMIE_SAMPLE_PATH = VOICE_SAMPLE_DIR / "jamie_sample.wav"
TOM_VOICE = "Tom (Enhanced)"
JAMIE_VOICE = "Jamie (Premium)"
REFERENCE_SENTENCE = (
    "This is a reference recording used only to capture this voice's tone "
    "and timbre for narration blending."
)

ALFRED_INPUT = ROOT / "audio" / "narration" / "node-fed.mp3"
JOHNNY_INPUT = ROOT / "audio" / "narration" / "johnny-fed.mp3"
OUTPUT_DIR = ROOT / "audio" / "voice_sample" / "spike_output"


def synthesize_reference_wav(voice_name, output_wav_path):
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff_path = Path(tmp.name)
    try:
        subprocess.run(
            ["say", "-v", voice_name, "-o", str(aiff_path), REFERENCE_SENTENCE],
            check=True,
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(aiff_path), str(output_wav_path)],
            check=True,
        )
    finally:
        aiff_path.unlink(missing_ok=True)


def embed_clip(vc, wav_path):
    wav, _ = librosa.load(str(wav_path), sr=S3GEN_SR)
    wav = wav[: ChatterboxVC.DEC_COND_LEN]
    return vc.s3gen.embed_ref(wav, S3GEN_SR, device=vc.device)


def blended_ref_dict(vc, embedding_clip_paths, prompt_clip_path):
    cache = {}
    for path in set(embedding_clip_paths) | {prompt_clip_path}:
        cache[path] = embed_clip(vc, path)
    embeddings = torch.stack(
        [cache[p]["embedding"] for p in embedding_clip_paths], dim=0
    )
    prompt_dict = cache[prompt_clip_path]
    return {
        "prompt_token": prompt_dict["prompt_token"],
        "prompt_token_len": prompt_dict["prompt_token_len"],
        "prompt_feat": prompt_dict["prompt_feat"],
        "prompt_feat_len": prompt_dict["prompt_feat_len"],
        "embedding": embeddings.mean(dim=0),
    }


def convert(vc, ref_dict, input_path, output_path):
    vc.ref_dict = ref_dict
    wav = vc.generate(str(input_path))
    sf.write(str(output_path), wav.squeeze(0).cpu().numpy(), S3GEN_SR)


def main():
    if not USER_VOICE_PATH.exists():
        raise RuntimeError(f"{USER_VOICE_PATH} is missing.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not TOM_SAMPLE_PATH.exists():
        print(f"Synthesizing {TOM_SAMPLE_PATH.name} via say -v \"{TOM_VOICE}\"...")
        synthesize_reference_wav(TOM_VOICE, TOM_SAMPLE_PATH)
    if not JAMIE_SAMPLE_PATH.exists():
        print(f"Synthesizing {JAMIE_SAMPLE_PATH.name} via say -v \"{JAMIE_VOICE}\"...")
        synthesize_reference_wav(JAMIE_VOICE, JAMIE_SAMPLE_PATH)

    print("Loading ChatterboxVC (first run downloads model weights)...")
    vc = ChatterboxVC.from_pretrained(device="mps")

    print("Building Alfred's 2-way blend (Jamie + user)...")
    alfred_dict = blended_ref_dict(
        vc,
        embedding_clip_paths=[JAMIE_SAMPLE_PATH, USER_VOICE_PATH],
        prompt_clip_path=USER_VOICE_PATH,
    )
    alfred_out = OUTPUT_DIR / "alfred_blend_spike.wav"
    convert(vc, alfred_dict, ALFRED_INPUT, alfred_out)
    print(f"wrote {alfred_out}")

    print("Building Johnny's 3-way blend (Tom + user + Jamie)...")
    johnny_dict = blended_ref_dict(
        vc,
        embedding_clip_paths=[TOM_SAMPLE_PATH, USER_VOICE_PATH, JAMIE_SAMPLE_PATH],
        prompt_clip_path=USER_VOICE_PATH,
    )
    johnny_out = OUTPUT_DIR / "johnny_blend_spike.wav"
    convert(vc, johnny_dict, JOHNNY_INPUT, johnny_out)
    print(f"wrote {johnny_out}")

    print("\nListen to both files, then report back:")
    print(f"  afplay {alfred_out}")
    print(f"  afplay {johnny_out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the spike**

Run: `cd bullion-live-map && .venv-narration/bin/python3 scripts/spike_voice_blend.py`

Expected: prints progress lines, ends with two `wrote ...` lines pointing at
`audio/voice_sample/spike_output/alfred_blend_spike.wav` and
`.../johnny_blend_spike.wav`. Takes roughly 1-2 minutes on this machine (Apple
M2, `mps` backend) — model load ~15s, each clip's embedding extraction ~10s,
each conversion ~20s.

- [ ] **Step 3: Verify the output files are real audio, not empty/corrupt**

Run: `cd bullion-live-map && afinfo audio/voice_sample/spike_output/alfred_blend_spike.wav && afinfo audio/voice_sample/spike_output/johnny_blend_spike.wav`

Expected: both report a nonzero "estimated duration" (roughly matching
`node-fed.mp3`'s and `johnny-fed.mp3`'s own durations — the conversion
preserves timing, only timbre changes).

- [ ] **Step 4: HARD GATE — human listening test, do not proceed past this step automatically**

Play both files for the user (`afplay audio/voice_sample/spike_output/alfred_blend_spike.wav`, same for Johnny's) and ask directly: does this sound like a coherent blended voice, and is the accent still correct (not drifted, per the original Chatterbox complaint this whole feature exists to avoid repeating)?

- If **yes** for both personas: proceed to Task 2.
- If **no**: do not proceed to Task 2. Per the spec's stated fallback, try dropping the weakest contributor from the failing blend (e.g. 2-way instead of 3-way for Johnny — drop `Tom` or `Jamie` and re-run the spike) before considering Approach 2 (direct local cloning) or Approach 3 (cloud TTS) from the spec's "Approaches considered" section. This is a genuine decision point for the user, not something to guess past.

- [ ] **Step 5: Commit the spike script**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/spike_voice_blend.py
git commit -m "$(cat <<'EOF'
Add throwaway spike script validating the voice-blend mechanism

Confirms embedding-averaging (Jamie+user for Alfred, Tom+user+Jamie
for Johnny via ChatterboxVC) produces a listenable result before any
of it is wired into the production narration pipeline.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

(`audio/voice_sample/spike_output/*.wav` and `audio/voice_sample/tom_sample.wav` /
`jamie_sample.wav` are left untracked at this point — Task 2 decides whether the
sample clips get committed as part of the real pipeline.)

---

### Task 2: Production blend-embedding helpers, with unit tests

**Depends on:** Task 1's gate passing (yes on both personas, or a revised blend confirmed to pass).

**Files:**
- Modify: `bullion-live-map/scripts/generate_narration.py` (add constants + functions; no changes to existing `extract_node_texts`, `_voice_installed`)
- Create: `bullion-live-map/scripts/test_voice_blend.py` (new file, kept separate from `test_generate_narration.py` deliberately — see Global Constraints on the environment split; this file requires `.venv-narration/bin/python3`, the existing test file does not)

**Interfaces:**
- Produces (consumed by Task 3):
  - `TOM_VOICE: str`, `VOICE_SAMPLE_DIR: Path`, `USER_VOICE_PATH: Path`, `TOM_SAMPLE_PATH: Path`, `JAMIE_SAMPLE_PATH: Path` — module-level constants.
  - `ensure_reference_clips() -> None` — generates `tom_sample.wav`/`jamie_sample.wav` via `say` if missing; raises `RuntimeError` if `user_voice.wav` is missing.
  - `load_vc_model() -> ChatterboxVC` — lazy-imports and loads the model once.
  - `embed_reference_clip(vc, wav_path: Path) -> dict` — one clip's conditioning dict.
  - `build_blended_ref_dict(vc, embedding_clip_paths: list[Path], prompt_clip_path: Path) -> dict` — averages `embedding` across `embedding_clip_paths`; takes `prompt_token`/`prompt_token_len`/`prompt_feat`/`prompt_feat_len` from `prompt_clip_path` alone.
  - `alfred_ref_dict(vc) -> dict`, `johnny_ref_dict(vc) -> dict` — the two persona-specific blends.
  - `convert_voice(vc, ref_dict: dict, input_audio_path: Path, output_wav_path: Path) -> None` — runs conversion, writes a wav file.
  - `JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES: float` — `-1.5`, validated by ear in the Task 1 spike.
  - `apply_johnny_meanness(wav_path: Path) -> None` — in-place pitch-shift of a wav file, Johnny-only.

- [ ] **Step 1: Write the failing tests for `build_blended_ref_dict`**

Create `bullion-live-map/scripts/test_voice_blend.py`:

```python
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_narration as gn

ROOT = Path(__file__).resolve().parent.parent


class TestBuildBlendedRefDict(unittest.TestCase):
    """build_blended_ref_dict must average only the fixed-size 'embedding'
    x-vector across clips, and take the variable-length acoustic prompt
    (prompt_token/prompt_feat) from exactly one designated clip — see the
    design spec's 2026-08-01 correction. Averaging prompt_token/prompt_feat
    across differently-shaped clips would shape-mismatch or produce mush."""

    def _fake_ref_dict(self, embedding_value, prompt_token_value):
        return {
            "embedding": torch.tensor([[embedding_value, embedding_value + 1.0]]),
            "prompt_token": torch.tensor([[prompt_token_value]]),
            "prompt_token_len": torch.tensor([1]),
            "prompt_feat": torch.tensor([[[float(prompt_token_value)]]]),
            "prompt_feat_len": None,
        }

    def test_averages_embedding_across_two_clips(self):
        clip_a = Path("/fake/a.wav")
        clip_b = Path("/fake/b.wav")
        fakes = {
            clip_a: self._fake_ref_dict(1.0, 11),
            clip_b: self._fake_ref_dict(3.0, 22),
        }
        with patch(
            "generate_narration.embed_reference_clip",
            side_effect=lambda vc, path: fakes[path],
        ):
            result = gn.build_blended_ref_dict(
                vc=object(),
                embedding_clip_paths=[clip_a, clip_b],
                prompt_clip_path=clip_b,
            )
        self.assertTrue(
            torch.equal(result["embedding"], torch.tensor([[2.0, 3.0]]))
        )

    def test_prompt_fields_come_from_the_designated_clip_only(self):
        clip_a = Path("/fake/a.wav")
        clip_b = Path("/fake/b.wav")
        clip_c = Path("/fake/c.wav")
        fakes = {
            clip_a: self._fake_ref_dict(1.0, 11),
            clip_b: self._fake_ref_dict(3.0, 22),
            clip_c: self._fake_ref_dict(5.0, 33),
        }
        with patch(
            "generate_narration.embed_reference_clip",
            side_effect=lambda vc, path: fakes[path],
        ):
            result = gn.build_blended_ref_dict(
                vc=object(),
                embedding_clip_paths=[clip_a, clip_b, clip_c],
                prompt_clip_path=clip_a,
            )
        self.assertTrue(
            torch.equal(result["prompt_token"], fakes[clip_a]["prompt_token"])
        )
        self.assertTrue(
            torch.equal(result["prompt_feat"], fakes[clip_a]["prompt_feat"])
        )
        self.assertIsNone(result["prompt_feat_len"])

    def test_three_way_average_matches_johnny_blend_shape(self):
        clip_a = Path("/fake/a.wav")
        clip_b = Path("/fake/b.wav")
        clip_c = Path("/fake/c.wav")
        fakes = {
            clip_a: self._fake_ref_dict(0.0, 1),
            clip_b: self._fake_ref_dict(3.0, 2),
            clip_c: self._fake_ref_dict(6.0, 3),
        }
        with patch(
            "generate_narration.embed_reference_clip",
            side_effect=lambda vc, path: fakes[path],
        ):
            result = gn.build_blended_ref_dict(
                vc=object(),
                embedding_clip_paths=[clip_a, clip_b, clip_c],
                prompt_clip_path=clip_b,
            )
        self.assertTrue(
            torch.equal(result["embedding"], torch.tensor([[3.0, 4.0]]))
        )


class TestEnsureReferenceClips(unittest.TestCase):
    def test_raises_if_user_voice_missing(self):
        with patch.object(gn, "USER_VOICE_PATH", Path("/nonexistent/user_voice.wav")):
            with self.assertRaises(RuntimeError) as ctx:
                gn.ensure_reference_clips()
            self.assertIn("missing", str(ctx.exception))

    def test_synthesizes_missing_tom_and_jamie_clips(self):
        with patch.object(gn, "USER_VOICE_PATH", ROOT / "audio" / "voice_sample" / "user_voice.wav"), \
             patch.object(gn, "TOM_SAMPLE_PATH", Path("/tmp/does-not-exist-tom.wav")), \
             patch.object(gn, "JAMIE_SAMPLE_PATH", Path("/tmp/does-not-exist-jamie.wav")), \
             patch("generate_narration.synthesize_reference_wav") as mock_synth:
            gn.ensure_reference_clips()
            self.assertEqual(mock_synth.call_count, 2)


class TestApplyJohnnyMeanness(unittest.TestCase):
    """Johnny gets a -1.5 semitone post-conversion pitch-down (validated by
    ear in the Task 1 spike, see the design spec's "Persona voice-color
    tweak" section); Alfred must not be touched by this. Patches the real
    librosa/soundfile module paths, not generate_narration's namespace —
    apply_johnny_meanness imports them lazily inside its own body (see
    Global Constraints), so there is no generate_narration.librosa
    attribute to patch; `import librosa` inside the function still binds to
    the same module object patch() modifies here."""

    def test_pitch_shifts_by_the_configured_semitone_amount(self):
        with patch("librosa.load", return_value=("fake_audio_array", 24000)) as mock_load, \
             patch("librosa.effects.pitch_shift", return_value="shifted_audio_array") as mock_shift, \
             patch("soundfile.write") as mock_write:
            gn.apply_johnny_meanness(Path("/fake/johnny-fed.wav"))

            mock_load.assert_called_once_with("/fake/johnny-fed.wav", sr=None)
            mock_shift.assert_called_once_with(
                "fake_audio_array",
                sr=24000,
                n_steps=gn.JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES,
            )
            mock_write.assert_called_once_with(
                "/fake/johnny-fed.wav", "shifted_audio_array", 24000
            )

    def test_configured_amount_is_a_modest_pitch_down(self):
        self.assertEqual(gn.JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES, -1.5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd bullion-live-map && .venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v`

Expected: FAIL — `AttributeError: module 'generate_narration' has no attribute 'build_blended_ref_dict'` (and similar for `ensure_reference_clips`, `apply_johnny_meanness`, `JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES`).

- [ ] **Step 3: Add the reference-clip and blend-embedding functions to `generate_narration.py`**

Add these constants near the existing `SAY_VOICE`/`ALFRED_RATE`/`JOHNNY_RATE` constants (around line 21-24):

```python
TOM_VOICE = "Tom (Enhanced)"
VOICE_SAMPLE_DIR = ROOT / "audio" / "voice_sample"
USER_VOICE_PATH = VOICE_SAMPLE_DIR / "user_voice.wav"
TOM_SAMPLE_PATH = VOICE_SAMPLE_DIR / "tom_sample.wav"
JAMIE_SAMPLE_PATH = VOICE_SAMPLE_DIR / "jamie_sample.wav"
VOICE_BLEND_REFERENCE_TEXT = (
    "This is a reference recording used only to capture this voice's tone "
    "and timbre for narration blending."
)
JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES = -1.5
```

Add these functions after `synthesize()` (heavy imports are lazy/local to each
function — see Global Constraints: this keeps `generate_narration.py` importable
under plain `python3` for the existing fast tests):

```python
def synthesize_reference_wav(voice_name, output_wav_path):
    """Generates a short reference clip for `voice_name` via `say`, used only
    to extract a speaker embedding for voice-conversion blending — never
    played directly. Fails loudly, same posture as synthesize()."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff_path = Path(tmp.name)
    try:
        try:
            subprocess.run(
                ["say", "-v", voice_name, "-o", str(aiff_path), VOICE_BLEND_REFERENCE_TEXT],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f'`say -v "{voice_name}"` failed (exit {e.returncode}) while '
                "generating a voice-blend reference clip."
            ) from e
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(aiff_path), str(output_wav_path)],
            check=True,
        )
    finally:
        aiff_path.unlink(missing_ok=True)


def ensure_reference_clips():
    """Generates tom_sample.wav / jamie_sample.wav via `say` if missing.
    user_voice.wav is never generated here — it's a real recording, not
    something this script can produce; raises if it's absent."""
    VOICE_SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    if not USER_VOICE_PATH.exists():
        raise RuntimeError(
            f"{USER_VOICE_PATH} is missing. This is a real recording of the "
            "user's voice, not something this script can generate."
        )
    if not TOM_SAMPLE_PATH.exists():
        synthesize_reference_wav(TOM_VOICE, TOM_SAMPLE_PATH)
    if not JAMIE_SAMPLE_PATH.exists():
        synthesize_reference_wav(SAY_VOICE, JAMIE_SAMPLE_PATH)


def load_vc_model():
    """Loads ChatterboxVC once. Expensive (real model weights) — callers
    should call this exactly once per script run and reuse the result."""
    from chatterbox.vc import ChatterboxVC
    return ChatterboxVC.from_pretrained(device="mps")


def embed_reference_clip(vc, wav_path):
    """Extracts ChatterboxVC's conditioning dict for one reference clip,
    truncated to the model's DEC_COND_LEN the same way
    ChatterboxVC.set_target_voice() does internally."""
    import librosa
    from chatterbox.vc import ChatterboxVC, S3GEN_SR
    wav, _ = librosa.load(str(wav_path), sr=S3GEN_SR)
    wav = wav[: ChatterboxVC.DEC_COND_LEN]
    return vc.s3gen.embed_ref(wav, S3GEN_SR, device=vc.device)


def build_blended_ref_dict(vc, embedding_clip_paths, prompt_clip_path):
    """Averages the fixed-size speaker x-vector ('embedding') across
    embedding_clip_paths, but takes the variable-length acoustic prompt
    ('prompt_token'/'prompt_token_len'/'prompt_feat') from prompt_clip_path
    alone — averaging those across clips of different lengths would either
    shape-mismatch or blend unrelated spectrograms into mush. See the design
    spec's "Blend mechanism" section (corrected 2026-08-01)."""
    import torch
    cache = {}
    for path in set(embedding_clip_paths) | {prompt_clip_path}:
        cache[path] = embed_reference_clip(vc, path)

    embeddings = torch.stack(
        [cache[path]["embedding"] for path in embedding_clip_paths], dim=0
    )
    prompt_dict = cache[prompt_clip_path]
    return {
        "prompt_token": prompt_dict["prompt_token"],
        "prompt_token_len": prompt_dict["prompt_token_len"],
        "prompt_feat": prompt_dict["prompt_feat"],
        "prompt_feat_len": prompt_dict["prompt_feat_len"],
        "embedding": embeddings.mean(dim=0),
    }


def alfred_ref_dict(vc):
    """Alfred's 2-way blend: Jamie (the content voice) + the user's own voice."""
    return build_blended_ref_dict(
        vc,
        embedding_clip_paths=[JAMIE_SAMPLE_PATH, USER_VOICE_PATH],
        prompt_clip_path=USER_VOICE_PATH,
    )


def johnny_ref_dict(vc):
    """Johnny's 3-way blend: Tom + the user's own voice + Jamie."""
    return build_blended_ref_dict(
        vc,
        embedding_clip_paths=[TOM_SAMPLE_PATH, USER_VOICE_PATH, JAMIE_SAMPLE_PATH],
        prompt_clip_path=USER_VOICE_PATH,
    )


def convert_voice(vc, ref_dict, input_audio_path, output_wav_path):
    """Runs ChatterboxVC conversion against a pre-built (possibly blended)
    ref_dict and writes the result as a wav file."""
    import soundfile as sf
    vc.ref_dict = ref_dict
    wav = vc.generate(str(input_audio_path))
    sf.write(str(output_wav_path), wav.squeeze(0).cpu().numpy(), vc.sr)


def apply_johnny_meanness(wav_path):
    """In-place pitch-shift of a converted wav file by
    JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES, for a slightly harsher edge.
    Johnny-only — never called for Alfred's output. Validated by ear in the
    Task 1 spike; see the design spec's "Persona voice-color tweak"
    section."""
    import librosa
    import soundfile as sf
    y, sr = librosa.load(str(wav_path), sr=None)
    y_shifted = librosa.effects.pitch_shift(
        y, sr=sr, n_steps=JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES
    )
    sf.write(str(wav_path), y_shifted, sr)
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `cd bullion-live-map && .venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v`

Expected: PASS, all 7 tests (`test_averages_embedding_across_two_clips`,
`test_prompt_fields_come_from_the_designated_clip_only`,
`test_three_way_average_matches_johnny_blend_shape`,
`test_raises_if_user_voice_missing`,
`test_synthesizes_missing_tom_and_jamie_clips`,
`test_pitch_shifts_by_the_configured_semitone_amount`,
`test_configured_amount_is_a_modest_pitch_down`).

- [ ] **Step 5: Verify the existing fast test suite still runs under plain `python3` (no accidental heavy import at module scope)**

Run: `cd bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`

Expected: PASS, same 22 tests as before this task — proves the new functions'
heavy imports are correctly scoped inside function bodies, not polluting
module-level import time.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/generate_narration.py bullion-live-map/scripts/test_voice_blend.py
git commit -m "$(cat <<'EOF'
Add production voice-blend helpers to generate_narration.py

build_blended_ref_dict averages only ChatterboxVC's fixed-size speaker
x-vector across reference clips, taking the acoustic prompt from one
designated clip (the user's own voice) — see the design spec's
2026-08-01 correction. Heavy ML imports are lazy/function-local so the
existing fast test suite keeps running under plain python3. Also adds
apply_johnny_meanness, a -1.5 semitone post-conversion pitch-down
applied to Johnny only.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Wire voice conversion into the real pipeline, regenerate all clips

**Depends on:** Task 2 committed.

**Files:**
- Modify: `bullion-live-map/scripts/generate_narration.py` (`synthesize()` and `main()`)

**Interfaces:**
- Consumes: everything from Task 2 (`ensure_reference_clips`, `load_vc_model`, `alfred_ref_dict`, `johnny_ref_dict`, `convert_voice`, `apply_johnny_meanness`).
- Produces: regenerated `audio/narration/*.mp3` files (same filenames as today, now voice-converted; Johnny's additionally pitch-shifted).

- [ ] **Step 1: Rewrite `synthesize()` to run its output through voice conversion (and, optionally, the meanness pitch-shift)**

Replace the existing `synthesize()` function body with:

```python
def synthesize(text, rate, output_mp3_path, vc, ref_dict, pitch_shift_semitones=None):
    """Runs `say` at the given words-per-minute rate, converts the result
    through ChatterboxVC against the given (possibly blended) ref_dict,
    optionally pitch-shifts it (Johnny only, via pitch_shift_semitones), and
    encodes the final result to MP3 via ffmpeg. Fails loudly on any
    subprocess or model error — never falls back silently."""
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
        aiff_path = Path(tmp.name)
    wav_in_path = aiff_path.with_suffix(".in.wav")
    wav_out_path = aiff_path.with_suffix(".out.wav")
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
            ["ffmpeg", "-y", "-i", str(aiff_path), str(wav_in_path)],
            check=True,
        )
        convert_voice(vc, ref_dict, wav_in_path, wav_out_path)
        if pitch_shift_semitones is not None:
            apply_johnny_meanness(wav_out_path)

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(wav_out_path),
             "-codec:a", "libmp3lame", "-qscale:a", "2", str(output_mp3_path)],
            check=True,
        )
    finally:
        aiff_path.unlink(missing_ok=True)
        wav_in_path.unlink(missing_ok=True)
        wav_out_path.unlink(missing_ok=True)
```

Note: `pitch_shift_semitones` is passed through only to decide *whether* to call
`apply_johnny_meanness` (which always uses the module constant
`JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES` internally) — `main()` in Step 2 passes
`JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES` for Johnny's calls and leaves the
parameter at its `None` default for Alfred's.

- [ ] **Step 2: Update `main()` to load the model once, build both blends once, and pass them through**

Replace the existing `main()` function body with:

```python
def main():
    # Verify both voices are installed before generating anything
    if not _voice_installed(SAY_VOICE):
        raise RuntimeError(
            f'"{SAY_VOICE}" is not installed. System Settings -> Accessibility -> '
            "Spoken Content -> System Voice -> Manage Voices."
        )
    if not _voice_installed(TOM_VOICE):
        raise RuntimeError(
            f'"{TOM_VOICE}" is not installed. System Settings -> Accessibility -> '
            "Spoken Content -> System Voice -> Manage Voices."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_reference_clips()

    print("Loading ChatterboxVC (first run downloads model weights)...")
    vc = load_vc_model()
    print("Building Alfred's blend (Jamie + user)...")
    alfred_dict = alfred_ref_dict(vc)
    print("Building Johnny's blend (Tom + user + Jamie)...")
    johnny_dict = johnny_ref_dict(vc)

    nodes = extract_node_texts(SOURCE_HTML)
    print(f"Extracted {len(nodes)} node texts from {SOURCE_HTML.name}")
    for node in nodes:
        out = OUTPUT_DIR / f"node-{node['id']}.mp3"
        synthesize(node["text"], ALFRED_RATE, out, vc, alfred_dict)
        print(f"wrote {out}")

    for node_id, script in JOHNNY_SCRIPTS.items():
        out = OUTPUT_DIR / f"johnny-{node_id}.mp3"
        synthesize(
            script, JOHNNY_RATE, out, vc, johnny_dict,
            pitch_shift_semitones=JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES,
        )
        print(f"wrote {out}")
```

- [ ] **Step 3: Verify the fast test suite still passes (it doesn't call `main()`/`synthesize()` directly, but confirms nothing else broke)**

Run: `cd bullion-live-map && python3 -m unittest scripts.test_generate_narration -v`

Expected: PASS, same 22 tests — `TestManifestCompleteness` and
`TestJohnnyPersona`'s file-existence checks will start failing only after
Step 4 regenerates the files with (temporarily) different content underneath
the same filenames; they check existence/non-emptiness, not audio content, so
they should still pass throughout.

- [ ] **Step 4: Regenerate all narration clips through the new pipeline**

Run: `cd bullion-live-map && .venv-narration/bin/python3 scripts/generate_narration.py`

Expected: prints the same progress lines as before (extraction count, blend
construction, one `wrote ...` line per of the 39 node clips + 6 Johnny clips +
2 link clips), completes without raising. This regenerates all 47 existing
`audio/narration/*.mp3` files in place, now voice-converted — expect this to
take several minutes (model load once + 47 clips × ~2 ffmpeg calls + 1
conversion each).

- [ ] **Step 5: Run the full project test suite**

Run: `cd bullion-live-map && python3 -m unittest discover -s tests && python3 -m unittest test_calibrate && python3 -m unittest scripts.test_generate_narration -v`

Expected: same pass count as the documented baseline (96/96) — this suite
never re-runs generation itself, it only checks the regenerated files exist,
are non-empty, and that manifests/text still line up, so it should be
unaffected by the underlying audio content changing.

Also run: `.venv-narration/bin/python3 -m unittest scripts.test_voice_blend -v`

Expected: PASS, same 7 tests from Task 2.

- [ ] **Step 6: Commit**

```bash
cd ~/claude-projects/claudekit
git add bullion-live-map/scripts/generate_narration.py bullion-live-map/audio/narration/ bullion-live-map/audio/voice_sample/tom_sample.wav bullion-live-map/audio/voice_sample/jamie_sample.wav
git status --short
```

Review the `git status --short` output before committing — confirm only the
expected `audio/narration/*.mp3` files, `generate_narration.py`, and the two
new reference clips show as modified/added (not any of the "Not mine" files
noted in the project's standing handoff convention). Then:

```bash
git commit -m "$(cat <<'EOF'
Wire voice-conversion blend into narration generation, regenerate all clips

synthesize()/main() now run say's output through ChatterboxVC against
each persona's blended target (Alfred: Jamie+user, Johnny:
Tom+user+Jamie) before encoding to MP3, with Johnny's output additionally
pitch-shifted -1.5 semitones for a meaner edge. All 47 existing
narration clips regenerated in place under the new pipeline.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Manual verification and push

**Depends on:** Task 3 committed, all regenerated clips present.

**Files:** none (no code changes — verification only).

- [ ] **Step 1: Manual browser check (no console errors)**

Using Chrome (claude-in-chrome or manual), open `bullion_mkultra.html` locally,
click through a few node detail panels for both Alfred and Johnny, confirm
narration plays and 0 console errors — same idiom used for every prior audio
change in this project (per the spec's "Testing" section).

- [ ] **Step 2: HARD GATE — human listening pass on real regenerated clips (not the spike's single sample)**

Ask the user to listen to a handful of the actual regenerated clips across
both personas (not just the Task 1 spike's one-clip-each sample) and confirm:
does it sound less robotic than before, is the accent still correct, and
(Johnny specifically) does the meanness pitch-down land right at -1.5
semitones across a range of his actual scripts, not just the one spike clip?
This is the actual acceptance criterion for the whole feature — do not report
this plan as complete without an explicit yes from the user here. Also
revisit the "not fully convincing yet" note from Task 1's gate explicitly —
does that concern still stand on full-length real clips, or has it resolved?

- If **no** (robotic/accent regression): this is a real regression to
  investigate, not something to patch around — go back to Task 1's spike
  with a revised blend (drop a contributor, or try prompt-clip anchored on a
  different clip) rather than tweaking pipeline code blindly.
- If Johnny's meanness amount is off: adjust
  `JOHNNY_MEANNESS_PITCH_SHIFT_SEMITONES` in `generate_narration.py` and
  re-run Task 3 Step 4 (regeneration) — a quick, cheap iteration, no need to
  revisit the blend itself for this specific adjustment.

- [ ] **Step 3: Ask for a fresh push decision**

Per this project's standing convention (every prior handoff notes this
explicitly), ask the user directly whether to push now — a fresh yes/no for
this session, never reusing a prior session's "hold" or "yes". If yes:

```bash
cd ~/claude-projects/claudekit
git push origin main
```

- [ ] **Step 4: Confirm GitHub Pages deploys successfully**

If pushed, check the Actions run completes (per the project's own recent
lesson in `bullion-persona-orb-shipped-handoff.md`: don't assume a push
deployed cleanly — check Actions, since a `curl -sI`/`last-modified` check
alone can't distinguish "still deploying" from "build failed"):

```bash
gh run list --repo SinbadTheExplorer/claudekit --limit 3
```

Expected: the run for this push's commit shows `completed`/`success`.
