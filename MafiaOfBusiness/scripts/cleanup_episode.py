#!/usr/bin/env python3
"""Delete an episode's heavy media once Content Lab confirmed the upload, so
nothing accumulates. Keeps topic.json, 02_script/ and 08_publish/ (a few KB).
Refuses to delete anything unless upload_log.json shows content_lab status ok.

Usage: python3 scripts/cleanup_episode.py <episode-slug>
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
MEDIA_DIRS = ("03_audio", "05_scenes", "07_edit")


def _upload_confirmed(episode_dir: Path) -> bool:
    try:
        log = json.loads((episode_dir / "08_publish" / "upload_log.json").read_text())
    except (OSError, ValueError):
        return False
    entry = log.get("content_lab")
    return isinstance(entry, dict) and entry.get("status") == "ok"


def cleanup(episode_dir: Path) -> list[str]:
    if not _upload_confirmed(episode_dir):
        raise RuntimeError(f"refusing to clean {episode_dir.name}: Content Lab upload not confirmed")
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
