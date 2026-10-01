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
_BEAT_RE = re.compile(r"^(\d+)\.\s+(.*)$")
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
            continue
        number, text = beat.group(1), beat.group(2)
        narration.append(text)
        if _DIGIT_RE.search(text):
            problems.append(f"beat {number}: contains a digit -- write numbers as Hindi words: {text}")
        latin = _LATIN_WORD_RE.findall(text)
        if len(latin) > MAX_LATIN_WORDS_PER_BEAT:
            problems.append(f"beat {number}: {len(latin)} English words -- write it in Hindi Devanagari: {text}")
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


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/check_script.py <episode-slug>")
        return 1
    script = WORKSPACE / "episodes" / sys.argv[1] / "02_script" / "script.md"
    problems = check(script.read_text(), load_state()["format"]["sections"])
    for p in problems:
        print(f"SCRIPT PROBLEM: {p}")
    if not problems:
        print("script.md ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
