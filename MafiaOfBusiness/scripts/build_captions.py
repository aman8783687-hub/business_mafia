#!/usr/bin/env python3
"""Build episodes/<slug>/07_edit/captions.ass -- the animated, burned-in
caption track -- from 03_audio/word_timings.json. Called by
assemble_episode.py; runnable standalone for iterating on caption style
without re-encoding the whole video (see references/captions.md's
"Testing" section for a fast preview loop).

Usage: python3 scripts/build_captions.py <episode-slug>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import load_state, parse_resolution
from subtitles.segment import segment_phrases
from subtitles.ass_builder import build_ass

WORKSPACE = Path(__file__).resolve().parent.parent


def build(slug: str) -> Path:
    episode_dir = WORKSPACE / "episodes" / slug
    word_timings_path = episode_dir / "03_audio" / "word_timings.json"
    if not word_timings_path.exists():
        raise FileNotFoundError(
            f"{word_timings_path} not found -- run generate_narration_chunks.py "
            "(captures word timing) then stitch_audio.py first."
        )
    words = json.loads(word_timings_path.read_text())["words"]

    state = load_state()
    config = state["captions"]
    width, height = parse_resolution(state["style_lock"]["resolution"])

    phrases = segment_phrases(
        words, config["max_words_per_caption"], config["min_words_per_caption"],
        config.get("max_gap_within_phrase_seconds", 0.2),
    )
    ass_content = build_ass(phrases, config, width, height)

    edit_dir = episode_dir / "07_edit"
    edit_dir.mkdir(parents=True, exist_ok=True)
    out_path = edit_dir / "captions.ass"
    out_path.write_text(ass_content)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/build_captions.py <episode-slug>")
        sys.exit(1)
    path = build(sys.argv[1])
    print(f"Wrote {path}")
