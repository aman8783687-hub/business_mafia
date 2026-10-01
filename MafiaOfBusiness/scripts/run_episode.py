#!/usr/bin/env python3
"""Run an episode through the entire mechanical pipeline, unattended:
audio -> scenes -> assembly -> thumbnail -> finalize into output/<slug>/.
No human confirmation step at any stage.

Preconditions this script does NOT create for you -- these are the
creative-writing parts of the pipeline and must already exist before
calling this:
  episodes/<slug>/01_research/sources.md        (per research-and-facts.md)
  episodes/<slug>/02_script/script.md          (per script-formula.md)
  episodes/<slug>/02_script/shotlist.json       (per visuals-and-animation.md)
  episodes/<slug>/03_audio/chunk_plan.json      (per voice-and-audio.md)
  episodes/<slug>/08_publish/metadata.json      (per publishing-and-metadata.md)

This script handles everything mechanical after that: narration
synthesis, stitching, scene generation, ffmpeg assembly, the thumbnail
(08_publish/thumbnail.png, from metadata.json's thumbnail_text), and
copying the package to output/<slug>/ and recording it in MongoDB (finalize_episode.py), then deleting the episode's intermediates. A stage
failure aborts the run with a clear message rather than continuing on
broken input: an audio failure poisons every later stage.

Usage: python3 scripts/run_episode.py <episode-slug>
"""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
SCRIPTS = WORKSPACE / "scripts"
LOCK_PATH = WORKSPACE / ".run_episode.lock"

# (stage name, script) in run order; the thumbnail runs between assembly and
# finalize as an optional stage (see main).
STAGES = [
    ("Check script", "check_script.py"),
    ("Narration", "generate_narration_chunks.py"),
    ("Stitch audio", "stitch_audio.py"),
    ("Generate scenes", "generate_scenes.py"),
    ("Assemble episode", "assemble_episode.py"),
    ("Finalize", "finalize_episode.py"),
    ("Cleanup", "cleanup_episode.py"),
]


def _subprocess_env() -> dict:
    # No extra environment to inject -- each stage script reads its own
    # config (API keys, credentials) via env_loader.py.
    return os.environ.copy()


def run_stage(name: str, args: list[str]) -> None:
    print(f"\n=== {name} ===")
    result = subprocess.run([sys.executable, *args], cwd=WORKSPACE, env=_subprocess_env())
    if result.returncode != 0:
        print(f"\n[run_episode] ABORTED at stage '{name}' (exit {result.returncode})")
        sys.exit(result.returncode)


def run_optional_stage(name: str, args: list[str]) -> None:
    """A stage whose failure must not stop the episode."""
    print(f"\n=== {name} ===")
    result = subprocess.run([sys.executable, *args], cwd=WORKSPACE, env=_subprocess_env())
    if result.returncode != 0:
        print(f"[run_episode] {name} failed (exit {result.returncode}); continuing without it")


def thumbnail_args(episode_dir: Path) -> list[str] | None:
    """make_thumbnail.py argv for this episode, or None when metadata.json has no thumbnail_text."""
    try:
        metadata = json.loads((episode_dir / "08_publish" / "metadata.json").read_text())
    except (OSError, ValueError):
        return None
    text = metadata.get("thumbnail_text")
    if not text:
        return None
    args = [str(SCRIPTS / "make_thumbnail.py"), text, "--out", str(episode_dir / "08_publish" / "thumbnail.png")]
    if metadata.get("thumbnail_accent_word"):
        args += ["--accent-word", metadata["thumbnail_accent_word"]]
    for note in (metadata.get("thumbnail_annotations") or [])[:4]:
        args += ["--annotation", note]
    beat = int(metadata.get("thumbnail_beat") or 1)
    scene = episode_dir / "05_scenes" / f"scene_{beat:04d}.png"
    if scene.exists():
        args += ["--scene", str(scene)]
    return args


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/run_episode.py <episode-slug>")
        sys.exit(1)

    # This project has no schedule yet (workflow_dispatch only -- see
    # AGENTS.md), but a single run's narration+scenes+assembly can still
    # take long enough to overlap a second manually-triggered run.
    # Without this, two
    # concurrent runs could both write episodes_published state at once,
    # or double-publish. Non-blocking: a second invocation while one is
    # already in progress exits cleanly rather than racing.
    lock_file = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"[run_episode] Another run_episode.py is already in progress ({LOCK_PATH} is locked) -- exiting without doing anything.")
        sys.exit(0)

    slug = sys.argv[1]
    episode_dir = WORKSPACE / "episodes" / slug

    required = [
        episode_dir / "01_research" / "sources.md",
        episode_dir / "02_script" / "script.md",
        episode_dir / "02_script" / "shotlist.json",
        episode_dir / "03_audio" / "chunk_plan.json",
        episode_dir / "08_publish" / "metadata.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing required inputs (the creative-writing stages haven't been done yet):")
        for m in missing:
            print(f"  {m}")
        sys.exit(1)

    # generate_scenes.py reads the shotlist from 05_scenes/, but it's
    # authored alongside script.md in 02_script/ -- copy it forward.
    scenes_dir = episode_dir / "05_scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(episode_dir / "02_script" / "shotlist.json", scenes_dir / "shotlist.json")

    for name, script in STAGES:
        if name == "Finalize":
            thumb = thumbnail_args(episode_dir)
            if thumb:
                run_optional_stage("Thumbnail", thumb)
        run_stage(name, [str(SCRIPTS / script), slug])

    print(f"\n=== DONE: {slug} ===")


if __name__ == "__main__":
    main()
