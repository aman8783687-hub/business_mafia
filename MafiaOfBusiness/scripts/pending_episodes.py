#!/usr/bin/env python3
"""Print slugs of episodes that were started (script.md exists) but not yet
finalized into output/. Exit 0 if none, 1 if any pending. An episode whose
media was deleted after a successful finalize counts as done."""
import json
import sys
from pathlib import Path

EPISODES = Path(__file__).resolve().parent.parent / "episodes"


sys.path.insert(0, str(Path(__file__).resolve().parent))
from cleanup_episode import is_finalized  # noqa: E402


def _done(episode_dir: Path) -> bool:
    """Finalized, or retired by `state_db.py episode-abandon`."""
    return is_finalized(episode_dir) or (episode_dir / "08_publish" / "abandoned.json").exists()


def find_pending(episodes_dir: Path) -> list[str]:
    if not episodes_dir.is_dir():
        return []
    return [
        ep.name
        for ep in sorted(episodes_dir.iterdir())
        if (ep / "02_script" / "script.md").exists() and not _done(ep)
    ]


if __name__ == "__main__":
    pending = find_pending(EPISODES)
    print("\n".join(pending))
    sys.exit(1 if pending else 0)
