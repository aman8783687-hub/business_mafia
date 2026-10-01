#!/usr/bin/env python3
"""Delete an episode's heavy media once finalize_episode.py copied the package to output/, so
nothing accumulates. Keeps topic.json, 02_script/ and 08_publish/ (a few KB).
Refuses to delete anything unless finalize_log.json shows status ok.

Usage: python3 scripts/cleanup_episode.py <episode-slug>
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
MEDIA_DIRS = ("03_audio", "05_scenes", "07_edit")


def _finalized(episode_dir: Path) -> bool:
    try:
        log = json.loads((episode_dir / "08_publish" / "finalize_log.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(log, dict) and log.get("status") == "ok"


def cleanup(episode_dir: Path) -> list[str]:
    if not _finalized(episode_dir):
        raise RuntimeError(f"refusing to clean {episode_dir.name}: episode not finalized")
    removed = []
    for name in MEDIA_DIRS:
        target = episode_dir / name
        if target.exists():
            shutil.rmtree(target)
            removed.append(name)
    return removed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/cleanup_episode.py <episode-slug>")
        sys.exit(1)
    try:
        print("removed:", cleanup(WORKSPACE / "episodes" / sys.argv[1]))
    except RuntimeError as err:
        print(err)
        sys.exit(1)
