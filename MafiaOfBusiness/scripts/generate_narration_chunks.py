#!/usr/bin/env python3
"""Synthesizes RedHat Engineer's narration via edge-tts, one chunk at a
time, applying a per-section rate/volume/pitch preset for a story-
documentary pacing arc. Ported from Dmoo Way's generate_narration_chunks.py
-- same mechanism, different voice and section names.

Usage (from MafiaOfBusiness/):
    python3 scripts/generate_narration_chunks.py <episode-slug>
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

import edge_tts

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
STATE = load_state()
VOICE = STATE["voice"]["voice_id"]
SECTION_PRESETS = {
    name: {"rate": p["rate"], "volume": p["volume"], "pitch": p["pitch"]}
    for name, p in STATE["voice"]["settings"]["section_presets"].items()
}
DEFAULT_PRESET = SECTION_PRESETS.get("rising_mystery", {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"})

_SECTION_RE = re.compile(r"^\[([A-Z_]+)\]\s*$")
_BEAT_RE = re.compile(r"^(\d+)\.\s+(.*)$")


def normalize_section(name: str) -> str:
    return name.strip().strip("[]").lower()


def beat_to_section_map(script_path: Path) -> dict[int, str]:
    mapping: dict[int, str] = {}
    current_section = "rising_mystery"
    for line in script_path.read_text().splitlines():
        section_match = _SECTION_RE.match(line.strip())
        if section_match:
            current_section = normalize_section(section_match.group(1))
            continue
        beat_match = _BEAT_RE.match(line.strip())
        if beat_match:
            mapping[int(beat_match.group(1))] = current_section
    return mapping


async def synth(text: str, preset: dict, out_path: Path, wordbounds_path: Path) -> None:
    communicate = edge_tts.Communicate(
        text, VOICE, rate=preset["rate"], volume=preset["volume"], pitch=preset["pitch"],
        boundary="WordBoundary",
    )
    with open(wordbounds_path, "w") as wb_fh, open(out_path, "wb") as audio_fh:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_fh.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                wb_fh.write(json.dumps({
                    "offset": chunk["offset"], "duration": chunk["duration"],
                    "text": chunk["text"], "type": "WordBoundary",
                }) + "\n")


async def main() -> None:
    slug = sys.argv[1]
    episode_dir = WORKSPACE / "episodes" / slug
    audio_dir = episode_dir / "03_audio"
    chunk_plan_path = audio_dir / "chunk_plan.json"
    script_path = episode_dir / "02_script" / "script.md"

    plan = json.loads(chunk_plan_path.read_text())
    section_map = beat_to_section_map(script_path)

    failures = []
    for chunk in plan["chunks"]:
        chunk_id = chunk["id"]
        out_path = audio_dir / f"chunk_{chunk_id:04d}.mp3"
        wb_path = audio_dir / f"chunk_{chunk_id:04d}.wordbounds.jsonl"
        if out_path.exists() and out_path.stat().st_size > 0 and wb_path.exists() and wb_path.stat().st_size > 0:
            continue
        first_beat = chunk["beats"][0]
        section = section_map.get(first_beat, "rising_mystery")
        preset = SECTION_PRESETS.get(section, DEFAULT_PRESET)
        try:
            await synth(chunk["text"], preset, out_path, wb_path)
            print(f"[chunk_{chunk_id:04d}] OK ({section})")
        except Exception as err:  # noqa: BLE001 - log and continue to next chunk
            print(f"[chunk_{chunk_id:04d}] FAILED - {err}")
            failures.append(chunk_id)

    print("=== SUMMARY ===")
    print(f"{len(plan['chunks']) - len(failures)}/{len(plan['chunks'])} chunks ok")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
