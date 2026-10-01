#!/usr/bin/env python3
"""Builds an episode's ambience bed. No music anywhere in this pipeline
-- this is the entire audio-beyond-voice pipeline. Ported in shape from
Dmoo Way's build_sfx.py; ambience.enabled defaults true in
channel_state.json (unlike Dmoo Way's checked-in gap where sfx.enabled
was absent and silently defaulted off)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402
from ambience import planner, mixer  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
AMBIENCE_DIR = WORKSPACE / "brand" / "ambience"


def build(slug: str, total_seconds: float | None = None) -> Path:
    episode_dir = WORKSPACE / "episodes" / slug
    timings = json.loads((episode_dir / "03_audio" / "timings.json").read_text())
    word_timings_path = episode_dir / "03_audio" / "word_timings.json"
    words = json.loads(word_timings_path.read_text())["words"] if word_timings_path.exists() else None

    config = load_state()["ambience"]
    manifest = json.loads((AMBIENCE_DIR / "manifest.json").read_text())
    override_path = episode_dir / "02_script" / "ambience_plan.json"
    override = json.loads(override_path.read_text()) if override_path.exists() else None

    cues = planner.plan(timings["beats"], words, config, override, set(manifest["effects"]))
    edit_dir = episode_dir / "07_edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    (edit_dir / "ambience_plan.resolved.json").write_text(json.dumps({"cues": cues}, indent=2))

    total = total_seconds if total_seconds is not None else timings["total_seconds"]
    out_path = edit_dir / "ambience_bed.wav"
    mixer.render_bed(cues, manifest, AMBIENCE_DIR, config["bed_db"], total, out_path)

    for c in cues:
        print(f"t={c['t']:.2f}  {c['sfx']:<16} {c['reason']}")
    return out_path


if __name__ == "__main__":
    build(sys.argv[1])
