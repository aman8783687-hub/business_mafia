#!/usr/bin/env python3
"""Hindi script guard, run by run_episode.py before narration.

Fails an episode's 02_script/script.md when:
  - a section tag is missing or out of order ([HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK]);
  - a narration beat contains a digit (edge-tts reads digits badly in Hindi,
    so numbers are written as words: "दस हज़ार", not "10,000");
  - a beat has more than two Latin-script words (an English sentence slipped
    in; one or two English business words like "profit" are fine);
  - the whole script is under 90% Devanagari letters.

Usage: python3 scripts/check_script.py <episode-slug>
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
MIN_DEVANAGARI_RATIO = 0.9
MAX_LATIN_WORDS_PER_BEAT = 2

_TAG_RE = re.compile(r"^\[([A-Z_]+)\]\s*$")
_BEAT_RE = re.compile(r"^(\d+)\.\s*(.+)$")  # same shape as stitch_audio.parse_script
_DIGIT_RE = re.compile(r"[0-9०-९]")
_LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")


def _devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha() or "ऀ" <= c <= "ॿ"]
    if not letters:
        return 1.0
    return sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters)


def check(script_text: str, sections: list[str]) -> list[str]:
    problems: list[str] = []
    seen: list[str] = []
    narration: list[str] = []
    for raw in script_text.splitlines():
        line = raw.strip()
        tag = _TAG_RE.match(line)
        if tag:
            seen.append(tag.group(1).lower())
            continue
        beat = _BEAT_RE.match(line)
        if not beat:
            # Headings, the runtime note and blank lines are fine. Anything else is
            # text stitch_audio would silently drop and these checks would never see.
            if line and not line.startswith("#") and not line.lower().startswith("target runtime"):
                problems.append(f"line without a beat number is invisible to captions and checks "
                                f"(put it in its beat's line): {line}")
            continue
        number, text = beat.group(1), beat.group(2)
        narration.append(text)
        problems += _spoken_text_problems(f"beat {number}", text)
    ratio = _devanagari_ratio(" ".join(narration))
    if ratio < MIN_DEVANAGARI_RATIO:
        problems.append(f"script is only {ratio:.0%} Devanagari letters (minimum 90%)")
    for name in sections:
        if name not in seen:
            problems.append(f"missing section [{name.upper()}]")
    present = [s for s in seen if s in sections]
    if present != [s for s in sections if s in present]:
        problems.append(f"sections out of order: {' '.join(s.upper() for s in present)} "
                        f"(expected {' '.join(s.upper() for s in sections)})")
    return problems


def _spoken_text_problems(label: str, text: str) -> list[str]:
    problems = []
    if _DIGIT_RE.search(text):
        problems.append(f"{label}: contains a digit -- write numbers as Hindi words: {text}")
    latin = _LATIN_WORD_RE.findall(text)
    if len(latin) > MAX_LATIN_WORDS_PER_BEAT:
        problems.append(f"{label}: {len(latin)} English words -- write it in Hindi Devanagari: {text}")
    return problems


def check_chunk_plan(script_text: str, plan: dict) -> list[str]:
    """chunk_plan.json "text" is what edge-tts actually speaks, and the agent
    writes it as a separate copy of the script (a mispronounced word may be
    respelled there on purpose), so it is checked on its own: no digits, no
    English sentences, every script beat covered by exactly one chunk."""
    script_beats = {int(m.group(1)) for m in
                    (_BEAT_RE.match(line.strip()) for line in script_text.splitlines()) if m}
    problems: list[str] = []
    seen: dict[int, int] = {}
    for chunk in plan.get("chunks", []):
        problems += _spoken_text_problems(f"chunk {chunk['id']}", chunk["text"])
        for beat in chunk["beats"]:
            if beat not in script_beats:
                problems.append(f"chunk {chunk['id']}: beat {beat} not in script.md")
            elif beat in seen:
                problems.append(f"beat {beat} is in more than one chunk ({seen[beat]} and {chunk['id']})")
            seen.setdefault(beat, chunk["id"])
    for beat in sorted(script_beats - set(seen)):
        problems.append(f"beat {beat} is in no chunk of chunk_plan.json")
    return problems


def check_metadata(metadata: dict) -> list[str]:
    """Everything the thumbnail needs, checked before narration and scenes
    spend anything: make_thumbnail.py would otherwise fail at the very end."""
    problems = []
    text = metadata.get("thumbnail_text")
    if not text:
        problems.append("metadata.json has no thumbnail_text (the thumbnail is part of the package)")
    elif len(text.split()) > 4:
        problems.append(f"thumbnail_text has {len(text.split())} words; at most 4 words: {text}")
    notes = metadata.get("thumbnail_annotations") or []
    if len(notes) > 4:
        problems.append(f"{len(notes)} thumbnail_annotations; at most 4 annotations")
    latin = [t for t in [text or "", *notes] if re.search(r"[A-Za-z]", t)]
    if latin:
        problems.append(f"Latin letters in thumbnail text (the Devanagari font has none, e.g. EMI -> ईएमआई): {latin}")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/check_script.py <episode-slug>")
        return 1
    episode = WORKSPACE / "episodes" / sys.argv[1]
    script_text = (episode / "02_script" / "script.md").read_text()
    problems = check(script_text, load_state()["format"]["sections"])
    plan_path = episode / "03_audio" / "chunk_plan.json"
    if plan_path.exists():
        problems += check_chunk_plan(script_text, json.loads(plan_path.read_text()))
    metadata_path = episode / "08_publish" / "metadata.json"
    if metadata_path.exists():
        problems += check_metadata(json.loads(metadata_path.read_text()))
    for p in problems:
        print(f"SCRIPT PROBLEM: {p}")
    if not problems:
        print("script.md ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
