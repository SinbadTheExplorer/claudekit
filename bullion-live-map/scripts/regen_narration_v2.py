#!/usr/bin/env python3
"""Resumable driver for regenerating all 100 narration clips (39 nodes +
11 events, x Alfred+Johnny) after the 2026-08-02 review-fix constant changes
(ALFRED_RATE 213, JOHNNY_TEMPO 0.95, loudnorm added to both, plus item 8's
new event-triggered lines). Mirrors the prior session's per-node marker-file
pattern (audio/narration/.johnny_tempo90_done.txt) since full-batch runs of
generate_narration.main() have been killed mid-run before. Safe to re-run:
already-done "persona-id" lines in the marker file are skipped, and the
marker is flushed to disk after every single clip so a kill loses at most
one in-flight clip.

Restructured (2026-08-02, 2nd attempt): generates ALL Alfred clips first
with only ChatterboxVC resident, fully releases it (del + gc + MPS cache
empty), THEN loads ChatterboxTTS and generates all Johnny clips — instead
of loading both large models up front and holding both resident for the
whole run. This machine has only 8GB unified memory (confirmed via
`sysctl hw.memsize`) and `sysctl vm.swapusage` showed heavy swap use during
the first attempt, which loaded both models simultaneously; halving peak
model-memory footprint is the concrete, code-side half of the memory-
pressure fix (the other half being closing other apps before running)."""
import gc
import sys
from pathlib import Path

PROJECT_SCRIPTS = Path("~/claude-projects/claudekit/bullion-live-map/scripts")
sys.path.insert(0, str(PROJECT_SCRIPTS))
import generate_narration as gn

MARKER_PATH = gn.OUTPUT_DIR / ".regen_2026-08-02_v2_done.txt"


def load_done():
    if not MARKER_PATH.exists():
        return set()
    return set(l.strip() for l in MARKER_PATH.read_text().splitlines() if l.strip())


def mark_done(key):
    with MARKER_PATH.open("a") as f:
        f.write(key + "\n")


def release_model(*objs):
    """Drops references and forces MPS to actually free the freed memory —
    without emptying the cache allocator, torch tends to hold onto freed
    device memory for reuse rather than returning it to the OS, which would
    defeat the point of unloading a model before loading the next one."""
    for o in objs:
        del o
    gc.collect()
    try:
        import torch
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
    except Exception:
        pass


def main():
    if not gn._voice_installed(gn.SAY_VOICE):
        raise RuntimeError(f'"{gn.SAY_VOICE}" is not installed.')

    gn.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gn.ensure_reference_clips()

    done = load_done()
    nodes = gn.extract_node_texts(gn.SOURCE_HTML)
    node_ids = [n["id"] for n in nodes]
    johnny_ids = list(gn.JOHNNY_SCRIPTS.keys())
    if set(node_ids) != set(johnny_ids):
        raise RuntimeError(
            f"Node/Johnny id mismatch: only-in-nodes={set(node_ids)-set(johnny_ids)} "
            f"only-in-johnny={set(johnny_ids)-set(node_ids)}"
        )
    text_by_id = {n["id"]: n["text"] for n in nodes}
    event_ids = list(gn.EVENT_IDS)

    alfred_node_remaining = [i for i in node_ids if f"alfred-{i}" not in done]
    alfred_event_remaining = [i for i in event_ids if f"event-alfred-{i}" not in done]
    johnny_node_remaining = [i for i in node_ids if f"johnny-{i}" not in done]
    johnny_event_remaining = [i for i in event_ids if f"event-johnny-{i}" not in done]
    print(f"Alfred remaining: {len(alfred_node_remaining)} node + {len(alfred_event_remaining)} event. "
          f"Johnny remaining: {len(johnny_node_remaining)} node + {len(johnny_event_remaining)} event.")

    # ── Alfred pass: only ChatterboxVC resident ─────────────────────────
    if alfred_node_remaining or alfred_event_remaining:
        print("Loading ChatterboxVC + building Alfred's blend...")
        vc = gn.load_vc_model()
        alfred_dict = gn.alfred_ref_dict(vc)

        for node_id in alfred_node_remaining:
            out = gn.OUTPUT_DIR / f"node-{node_id}.mp3"
            gn.synthesize(text_by_id[node_id], gn.ALFRED_RATE, out, vc, alfred_dict)
            mark_done(f"alfred-{node_id}")
            print(f"[alfred] wrote {out}")
        for event_id in alfred_event_remaining:
            out = gn.OUTPUT_DIR / f"event-{event_id}.mp3"
            gn.synthesize(gn.EVENT_ALFRED_SCRIPTS[event_id], gn.ALFRED_RATE, out, vc, alfred_dict)
            mark_done(f"event-alfred-{event_id}")
            print(f"[event-alfred] wrote {out}")

        print("Releasing ChatterboxVC before loading ChatterboxTTS...")
        release_model(vc, alfred_dict)
    else:
        print("No Alfred clips remaining, skipping ChatterboxVC entirely.")

    # ── Johnny pass: only ChatterboxTTS resident ────────────────────────
    if johnny_node_remaining or johnny_event_remaining:
        print("Loading ChatterboxTTS for Johnny...")
        tts = gn.load_tts_model()

        for node_id in johnny_node_remaining:
            out = gn.OUTPUT_DIR / f"johnny-{node_id}.mp3"
            gn.synthesize_johnny(gn.JOHNNY_SCRIPTS[node_id], out, tts)
            mark_done(f"johnny-{node_id}")
            print(f"[johnny] wrote {out}")
        for event_id in johnny_event_remaining:
            out = gn.OUTPUT_DIR / f"johnny-event-{event_id}.mp3"
            gn.synthesize_johnny(gn.EVENT_JOHNNY_SCRIPTS[event_id], out, tts)
            mark_done(f"event-johnny-{event_id}")
            print(f"[event-johnny] wrote {out}")
    else:
        print("No Johnny clips remaining, skipping ChatterboxTTS entirely.")

    print("All 78 node clips + 22 event clips present.")


if __name__ == "__main__":
    main()
