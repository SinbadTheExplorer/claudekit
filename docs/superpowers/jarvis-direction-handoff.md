# Personal Voice Assistant ("Jarvis") — Direction Handoff

**Written:** 2026-10-29 · **For:** a fresh session picking up the user's personal voice-assistant idea and deciding how it fits their accounting-internship goal. Nothing has been built yet.

## Goal

The user wants **their own** voice-first AI companion: something they talk to (not type to), that has its own personality and avatar, remembers them, and does tasks they command. Inspirations: Delamain (Cyberpunk 2077), Jarvis, Sesame's Maya, and VisionQuest. Their main 90-day goal is still a **Big 4 accounting internship** (Deloitte, PwC, ...). The user worries the assistant is a "toy" that pulls time away from that goal.

**Recommended direction (not yet agreed by the user):** don't choose between the two. Build the assistant so its **first job is the internship hunt**:
- Voice mock interviews: behavioral questions plus technical accounting questions, with feedback afterwards. Voice is the right medium for this, so the voice stops being a toy.
- Internship application tracker plus deadline reminders.
- A daily finance news briefing that doubles as interview talking points.

No spec or plan exists yet. This file is the only authority.

## How to resume (do this first)

1. `git log --oneline -5` on `main`. There's no feature branch for this; nothing is built.
2. Read this file plus `CLAUDE.md` (especially the **Time Estimates & Deadlines Rule**).
3. Ask the user the open questions below. Don't build until they've answered.
4. **Immediate next action:** ask the user to share the saved Instagram video about an accounting tool, then help them decide between (a) the accounting project alone, (b) the assistant with the internship-first focus above, or (c) both, with the assistant time-boxed to one weekend.

## Current state (active files)

**Branch:** `main`. No assistant code exists anywhere yet.

**Existing pieces worth reusing:**
- `.github/workflows/news-hourly.yml`: an **hourly news-headline pipeline already runs** (github-actions commits "Update news headlines for ..."). The daily briefing should reuse this feed instead of building a new one.
- `bullion-live-map/scripts/generate_narration.py`: Johnny persona voice (ChatterboxTTS, actor reference recording) and Alfred (macOS `say` + ChatterboxVC).
- `docs/superpowers/specs/2026-08-01-bullion-persona-orb-design.md`: a persona orb design that can become the first avatar.

**Not mine — leave alone:** the Johnny and Alfred narration audio and scripts. The user considered redoing Johnny; the recommendation was **don't**. The 39 clips are user-reviewed and tuned (tempo 0.9 → 0.95 → 0.92). Reuse the persona, not the clips.

## What has changed

- `4ae4eae`: added the **Time Estimates & Deadlines Rule** to `CLAUDE.md`. Claude's own work is estimated in minutes or hours, the user's time at human speed, and external deadlines in real calendar time.
- Nothing else. This session was discussion only.

## What has failed / risks / caveats

- **Nothing has failed.** Nothing was built.
- **Hardware:** 2022 MacBook with 8 GB of memory, already slow. **Don't run models locally.** The Mac or phone should only be a browser client.
- **Findings from research (2026-10-29):**
  - Sesame open-sourced only **CSM-1B** (Apache 2.0, March 2025). The ~8B model behind Maya and Miles is **not** open. CSM-1B is voice output only and needs a graphics chip.
  - The responsive feel (streaming, turn detection, interruptions) comes from **Pipecat** (open source, BSD-2).
  - A cheap server without a graphics chip is *slower* than the Mac at running models. **Rent the brain** (Claude Haiku 5.5: $0.10 / $0.50 per million tokens in/out, about $0.70/mo at 50 exchanges a day). Never self-host it.
  - Phones work as the mic and speaker client, not as the host.
- **Architecture agreed in principle:** the user owns the persona, memory, voice, avatar and code. Only the brain is rented, behind a swappable one-line model config so there's no lock-in. Estimated total cost: about $6–20/mo.
- **Legal:** check that the voice actor's agreement covers synthetic or live-assistant use before cloning that voice.
- **Safety:** the assistant must be **read-only for anything financial** (no trades, no money movement).
- **User wellbeing:** the user said they want "someone to talk to" and was tired and self-critical at the end of this session. Be warm and direct, and don't pile on scope. Their stated bottleneck is finishing things, so keep every phase small and finishable.
- **Kill rule agreed:** one weekend for a working version, then 2 weeks of real use. If it isn't used daily, stop before the avatar work.

## What's next (ordered)

1. Get answers to the open questions:
   - Accounting project (Instagram video) vs. assistant vs. both?
   - Personality: Delamain-style butler, Johnny-style rocker, or a new character? What name?
   - Avatar: orb first (recommended), then 2D or 3D anime (VRoid Studio + three-vrm)?
2. **Phase 0** (Claude ~20 min, $0): a morning finance briefing built on the existing news-hourly feed. Ask what time, which topics, and whether to deliver by email or in the app.
3. **Phase 1** (Claude ~3–4 hrs · user 1 evening): Pipecat voice loop in the browser, Haiku 5.5 brain, Kokoro voice, persona, memory, orb avatar. First feature: **voice mock interview for Big 4 internships**.
4. **Phase 2** (Claude ~2 hrs): tasks: application tracker, calendar and Canvas reminders.
5. **Phase 3** (only if the kill-rule check passes): anime avatar upgrade.

## Verification idioms used in this project

- Nothing built yet. For the voice app: run it locally and check that the time from the end of speech to the first audio back is under about 2 s, that barge-in (interrupting) works, and that memory carries over between sessions.
- Repo convention: user-reviewed listening pass before committing any generated audio (see the `narration-regen-workflow` skill).
