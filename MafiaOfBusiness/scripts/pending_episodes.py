#!/usr/bin/env python3
"""Print slugs of episodes that were started (script.md exists) but not yet
finalized into output/. Exit 0 if none, 1 if any pending. An episode whose
media was deleted after a successful finalize counts as done."""
import json
import sys
from pathlib import Path

EPISODES = Path(__file__).resolve().parent.parent / "episodes"


def _finalized(episode_dir: Path) -> bool:
    try:
        log = json.loads((episode_dir / "08_publish" / "finalize_log.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(log, dict) and log.get("status") == "ok"


def find_pending(episodes_dir: Path) -> list[str]:
    if not episodes_dir.is_dir():
        return []
    return [
        ep.name
        for ep in sorted(episodes_dir.iterdir())
        if (ep / "02_script" / "script.md").exists() and not _finalized(ep)
    ]


if __name__ == "__main__":
    pending = find_pending(EPISODES)
    print("\n".join(pending))
    sys.exit(1 if pending else 0)
