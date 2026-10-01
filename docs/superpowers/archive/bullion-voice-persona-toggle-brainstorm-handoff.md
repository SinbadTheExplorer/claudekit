# Bullion Voice Narration — Persona Toggle Redesign — Session Handoff

**Written:** 2026-07-31 · **For:** any future session resuming the brainstorming (NOT yet
implementation — no code has changed this session) for a two-persona narration voice
system, replacing the accent-flawed Chatterbox clone.

## Goal

Replace the Chatterbox-cloned narration voice (reported by the user to sound like it has
an Indian accent, not their own — see the now-superseded prior handoff for that
background) with a system built entirely on macOS's built-in "Jamie (Premium)" British
voice via the `say` CLI — **but the design grew substantially beyond a simple engine
swap during this session's brainstorming**, into a two-persona toggle with captions and
autoplay. None of it is implemented yet; this handoff exists because the user asked to
save progress and clear the session before the design was finalized into a written spec.

- **Committed but STALE spec** (v1, engine-swap only — read for background on the `say`
  vs. Chatterbox mechanics, but do NOT treat as the final design):
  `docs/superpowers/specs/2026-07-31-bullion-voice-british-swap-design.md` (commit
  `20a4bb7`, **not pushed** to origin).
- **No v2 spec file exists yet** — the fuller design (two personas, captions, autoplay)
  lives only in this handoff; see "What's next" for what still needs writing.
- Prior handoff (background on the accent problem and the abandoned cfg_weight-tuning
  approach — **fully superseded**, its whole premise was dropped in favor of replacing
  the voice outright): `docs/superpowers/voice-narration-accent-debug-handoff.md`.
- No separate progress ledger exists — this handoff **is** the ledger.

## How to resume (do this first)

1. Confirm branch/head: `git -C ~/claude-projects/claudekit log --oneline
   -5` should show `20a4bb7` at HEAD on `main`. `git rev-list --left-right --count
   origin/main...main` should read `0 1` — **`main` is 1 commit ahead of origin,
   unpushed.** `git status --short` should show only the standard pre-existing untracked
   noise (see "Not mine" below) plus this handoff file — no tracked changes, no code
   edits of any kind.
2. Re-invoke `superpowers:brainstorming` — this effort is still mid-flow (the "present
   design / get approval" step), not finished. The committed spec needs a v2 rewrite
   before this can move to `writing-plans`.
3. Read this handoff in full — it is the sole record of what was decided this session;
   nothing is written anywhere else yet.
4. **Immediate next action:** ask the user the question that was pending when they asked
   for this handoff — **who writes Johnny's ~6 pilot rocker scripts** (the resuming
   session drafting a first pass for review, or the user writing them directly). Then
   proceed to rewriting the spec (see "What's next").

## Current state (active files)

**Branch:** `main`, 1 commit ahead of origin (`20a4bb7`), not pushed. Working tree has
only the standard pre-existing untracked noise (see "Not mine") plus this handoff.

**Files created / changed (committed in `20a4bb7`):**
- `docs/superpowers/specs/2026-07-31-bullion-voice-british-swap-design.md` — describes
  ONLY the v1 design: swap Chatterbox → `say` CLI, single voice ("Jamie (Premium)"),
  `-r 200`, no toggle, no captions, no autoplay. **This is now incomplete/stale** —
  everything past that point in the conversation (two personas, captions, autoplay) was
  agreed verbally but never written into this file or a new one.

**Files later work will modify (untouched so far — zero code changes this session):**
- `bullion-live-map/scripts/generate_narration.py` — still 100% the original
  Chatterbox-based version (`torchaudio`, `ChatterboxTTS`, `VOICE_SAMPLE`). The v1 spec
  describes the intended `say`-based rewrite in detail; nothing has actually been
  edited.
- `bullion_mk18.html` / `bullion_mkultra.html` — `NARRATION_MANIFEST` unchanged (39
  entries from Phase 1); no persona-toggle UI, no caption box, no autoplay logic exist
  in either file yet.
- `bullion-live-map/audio/narration/*.mp3` — still the original Chatterbox-cloned clips
  (the bad-accent versions the user is trying to replace); not regenerated.

**Scratch workspace / traps:**
- ⚠️ **All audio A/B samples from this session live in THIS session's scratchpad, which
  will not exist for a fresh session:**
  `/private/tmp/claude-501/-Users-me/bea05920-826f-4dfb-9dec-6a1a9106e45d/scratchpad/voice-test/`
  — `daniel_standard.aiff`, `jamie_premium.aiff`, `jamie_premium_v2.aiff`,
  `system_default.aiff`, `rate_test.aiff`, `rate_default.aiff`, `pitch_test.aiff`,
  `pitch_plain.aiff`, `jamie_r200.aiff`, `rate_default_check.aiff`. None are needed to
  resume — they were disposable listening aids. Regenerate on demand:
  `say -v "Jamie (Premium)" -r <N> "<text>" -o <path>.aiff`.
- ⚠️ **The word-timing feasibility spike** lives at
  `/private/tmp/claude-501/-Users-me/bea05920-826f-4dfb-9dec-6a1a9106e45d/scratchpad/word_timing_spike.swift`
  (+ output `spike_out.caf`) — also session-scratch, will vanish. Full script and result
  reproduced below so nothing is lost; **do not re-run it expecting a different
  result without a genuinely new approach** (see "What has failed" below).
- ⚠️ An **even older, orphaned session's scratch dir** (a different session UUID,
  `d022e4c7-…`, referenced in the now-superseded prior handoff) still has the old
  Chatterbox `cfg_weight` A/B clips (`baseline_cfg05.wav`, `cfg08.wav`). These are moot
  now that Chatterbox is being dropped entirely — ignore if stumbled upon.
- ⚠️ `docs/superpowers/voice-narration-accent-debug-handoff.md` (the prior handoff) is
  **fully superseded** — its entire premise (tune Chatterbox's `cfg_weight` to fix the
  cloned voice's accent) was abandoned this session in favor of replacing the voice
  outright. Read only for background on how we got here, never as an active plan.

**Not mine — leave alone:** same pre-existing untracked noise as every prior handoff in
this project — `docs/chrome-mcp-setup.md`, `docs/project-overview.md`, `.claude/`,
`.agents/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.DS_Store` (multiple),
`bullion-live-map/__pycache__/`, `bullion-live-map/scripts/__pycache__/`,
`bullion-live-map/tests/__pycache__/`, `docs/superpowers/archive/`,
`docs/superpowers/plans/2026-07-24-bullion-mk14-mk15.md`,
`docs/superpowers/plans/2026-07-30-bullion-ui-fixes.md`,
`docs/superpowers/plans/2026-07-30-bullion-voice-narration-phase1.md`,
`docs/superpowers/bullion-ui-fixes-and-voice-phase1-execution-handoff.md` (archived this
session, see below). **Never `git add .`/`-A`.**

## What has changed

- **One commit this session:** `20a4bb7`, the v1 design spec (engine swap only — see
  above). That's the only artifact on disk anywhere reflecting this session's work; it
  is already incomplete relative to what was actually agreed later in the same
  conversation.
- **Zero implementation** — no script edits, no HTML edits, no audio regenerated.
- The conversation reached a fully-formed v2 design through several rounds of
  clarification plus one technical spike, but it was never written to a file before the
  user asked for this handoff. That full design is captured below and must be turned
  into a real spec on resume.

## What has failed / risks / caveats

- **Nothing has failed as code** — no implementation attempted yet, so nothing to fail
  in that sense.
- **CONFIRMED DEAD END: true word-level caption timing via AVSpeechSynthesizer.**
  Spiked this session (`word_timing_spike.swift`, reproduced below): calling
  `write(_:toBufferCallback:)` on an `AVSpeechUtterance` using the "Jamie (Premium)"
  voice, for an 8-word test sentence, **timed out after 15s with 0 audio frames
  delivered and 0 `willSpeakRangeOfSpeechString` boundary callbacks fired.** This isn't
  just "no timing data available" — the offline synthesis call itself appears to hang
  for this voice on this system, consistent with known AVSpeechSynthesizer flakiness
  found in Apple's own developer forums during this session's research. **Do not
  re-attempt this path without a genuinely new angle** (e.g., a non-Premium voice, or
  live `speak()`-based capture instead of offline `write()`) — the user already agreed
  to the fallback below after seeing this result.
  - Harmless trivia surfaced by the same spike: "Jamie (Premium)"'s internal
    `AVSpeechSynthesisVoice` identifier is `com.apple.voice.premium.en-GB.Malcolm` — an
    Apple internal rename, doesn't affect anything, but don't be alarmed if voice
    enumeration shows "Malcolm" instead of "Jamie."
  - **Agreed fallback:** captions use **estimated, character-count-proportional word
    timing** — split each clip's known total duration (from the generated MP3, via
    `afinfo`) across words by character-count share of the total text. Deterministic,
    needs no native API, not frame-perfect but reads convincingly.
- **UNRESOLVED — open question, asked but never answered:** who writes Johnny's ~6
  pilot rocker scripts (the resuming session drafting a first pass for the user's
  review, or the user writing them directly). This was the literal last thing asked
  before the user requested this handoff — **ask it again first**, before writing any
  rocker copy.
- **`-r 200` for the Alfred persona is provisional** — a first approximation (~9%
  faster than Jamie's default rate, measured on one sentence: the "fed" pilot node's
  text) of "slightly faster than default," matching what the user described tuning in
  System Settings. **Not yet confirmed by the user as sounding right** — they never
  explicitly signed off on this exact number, only agreed to the `say`-CLI approach in
  general.
- **Firmly ruled out this session, do not revisit:** cloning Jarvis's voice (Paul
  Bettany) or "combining voices" to approximate Keanu Reeves specifically — both
  declined on real-person consent/publicity-rights grounds, independent of licensing.
  (Researched CD Projekt Red's fan-content policy on request: it doesn't clearly cover
  AI voice reuse either way, and wouldn't override Keanu's personal consent even if it
  did — see chat history for the full explanation if the user asks again.) **The
  resolution the user accepted:** two personas built on the SAME synthetic "Jamie
  (Premium)" voice, differentiated by rate + hand-written wording, never by targeting
  any real person's actual voice.
- Commit `20a4bb7` is **local only, not pushed** to origin — flag before assuming it's
  live anywhere.

## What's next (ordered)

1. Re-invoke `superpowers:brainstorming` (mid-flow, not done) and ask the still-open
   question: who drafts Johnny's ~6 pilot rocker scripts.
2. Rewrite `docs/superpowers/specs/2026-07-31-bullion-voice-british-swap-design.md` (or
   write a new dated spec that formally supersedes it — resuming session's call) to
   cover the full v2 design agreed this session:
   - **Two personas, both shipped, listener-toggled**: "Alfred" (butler — the v1
     design's `say -v "Jamie (Premium)" -r 200` narration, using the existing
     factual/extracted node text) and "Johnny" (rocker — same voice/engine, a
     slower/looser rate, and **distinct hand-written flavor text**, not the page's
     factual copy).
   - **Johnny's script is hand-authored** and deliberately diverges from the
     factual on-page text used for display and for Alfred — reintroduces a
     manually-maintained text source (the exact pattern Phase 1 eliminated for
     Alfred/the page text, reintroduced here on purpose for one persona only).
     Needs its own drift-guard test: a coverage/non-empty check (does every piloted
     node have a Johnny script, is it non-empty), **not** a content-match-to-page-text
     check, since divergence from the page text is the intended behavior.
   - **Pilot Johnny on ~6 nodes only** (mirrors this project's own original
     Chatterbox-pilot precedent before Phase 1 scaled to 39) — not full 39-node
     coverage yet. Decide expansion after hearing the pilot.
   - **Speaker captions**: a caption box labeled with the active persona's name
     (e.g. "ALFRED:" / "JOHNNY:"), words revealed in sync with playback using
     **estimated character-count-proportional timing** against each clip's real
     duration (see "What has failed" — true API timing is a confirmed dead end).
   - **Autoplay**: narration plays automatically the first time each node is opened
     **per session**; reopening the same node later stays silent (the existing 🔊
     button remains available for replay). Does not apply to every open — only the
     first, per session.
3. Run the brainstorming skill's spec self-review, then get the user's explicit
   sign-off on the rewritten spec (per the skill's gate — do not skip to
   implementation without this).
4. Only then invoke `writing-plans` to produce the implementation plan — remember,
   **zero implementation has happened**: no script changes, no HTML/manifest changes,
   no audio regenerated. There is a full plan-writing pass ahead of any code work.
5. Ask the user whether to push `20a4bb7` now or bundle it with the next push.

## Verification idioms used in this project (for the resuming session)

- Audible correctness (accent, tone, whether a persona "feels" right) **cannot be
  automated** — always the user's ear via `afplay`/Finder/QuickTime, same as every
  prior audio decision in this project.
- To check whether a System Settings voice-personalization change actually reaches the
  `say` CLI: generate the same text twice and `shasum` both `.aiff` outputs — identical
  checksum means the CLI did **not** pick up the change (this is how we discovered
  pitch/timbre/sentence-pause sliders don't reach `say` at all, only the rate flag
  does).
- To check whether a `say` flag or legacy embedded command (`[[pbas]]`, `[[slnc]]`,
  etc.) actually did something vs. got spoken as literal text: compare
  `afinfo <file> | grep -i duration` between variants — a voice reading the command
  text literally comes out measurably *longer*, not just checksum-different.
- Native-API spikes (e.g. AVSpeechSynthesizer): always give them a real timeout (15s
  was enough to catch this session's hang) — don't let a Swift/PyObjC script block
  indefinitely testing an offline synthesis path; a hang IS the finding.

## Reproducing the word-timing feasibility spike

Confirmed dead end (see "What has failed") — reproduced here for reference, not to be
blindly re-run expecting a different result:

```swift
import Foundation
import AVFoundation

let synth = AVSpeechSynthesizer()

final class Delegate: NSObject, AVSpeechSynthesizerDelegate {
    var events: [(NSRange, Int)] = []
    var cumulativeFrames: Int = 0
}

let delegate = Delegate()
synth.delegate = delegate

let voices = AVSpeechSynthesisVoice.speechVoices()
guard let jamie = voices.first(where: { $0.name.contains("Jamie") }) else {
    print("Jamie voice not found. Available voices:")
    for v in voices { print(" -", v.name, v.identifier, "quality=\(v.quality.rawValue)") }
    exit(1)
}
print("Using voice: \(jamie.name) \(jamie.identifier) quality=\(jamie.quality.rawValue)")

let text = "The central bank controls interest rates."
let utterance = AVSpeechUtterance(string: text)
utterance.voice = jamie

var audioFile: AVAudioFile?
let sema = DispatchSemaphore(value: 0)

class BoundaryCatcher: NSObject, AVSpeechSynthesizerDelegate {
    var hits: [(String, NSRange)] = []
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, willSpeakRangeOfSpeechString characterRange: NSRange, utterance: AVSpeechUtterance) {
        let nsText = utterance.speechString as NSString
        let word = nsText.substring(with: characterRange)
        hits.append((word, characterRange))
        print("[boundary-callback] word='\(word)' range=\(characterRange)")
    }
}
let catcher = BoundaryCatcher()
synth.delegate = catcher

synth.write(utterance) { (buffer: AVAudioBuffer) in
    guard let pcm = buffer as? AVAudioPCMBuffer else { return }
    if pcm.frameLength == 0 {
        sema.signal()
        return
    }
    if audioFile == nil {
        let outURL = URL(fileURLWithPath: "/tmp/spike_out.caf")
        audioFile = try? AVAudioFile(forWriting: outURL, settings: pcm.format.settings)
    }
    try? audioFile?.write(from: pcm)
    delegate.cumulativeFrames += Int(pcm.frameLength)
}

let waitResult = sema.wait(timeout: .now() + 15)
print("wait result: \(waitResult)")
print("Total boundary callbacks fired: \(catcher.hits.count)")
print("Total audio frames written: \(delegate.cumulativeFrames)")
```

Run with: `swift word_timing_spike.swift`

**Result obtained this session:**
```
Using voice: Jamie (Premium) com.apple.voice.premium.en-GB.Malcolm quality=3
wait result: timedOut
Total boundary callbacks fired: 0
Total audio frames written: 0
```
