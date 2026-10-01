"""Loads the channel's locked configuration."""
from __future__ import annotations

import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
STATE_PATH = WORKSPACE / "channel_state.json"


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text())


def parse_resolution(resolution: str) -> tuple[int, int]:
    w, h = resolution.split("x")
    return int(w), int(h)
