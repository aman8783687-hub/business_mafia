#!/usr/bin/env python3
"""Final stage (local, no upload): verify the render,
copy the posting package to output/<slug>/, record the episode in MongoDB
as "ready", and write 08_publish/finalize_log.json. cleanup_episode.py
deletes intermediates only after this log says ok. Idempotent: a rerun on a
finalized episode does nothing.

Usage: python3 scripts/finalize_episode.py <episode-slug>
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
OUTPUT_ROOT = WORKSPACE / "output"

CHECKLIST = """## Posting checklist
- [ ] Post between 6-9 PM IST (daily if you can: both reference channels grew on one video a day).
- [ ] Upload the video; set the thumbnail from thumbnail.png.
- [ ] Paste title, description and tags from this file.
- [ ] Video language and default audio language: Hindi. Upload captions.srt as Hindi subtitles.
- [ ] Not made for kids. Altered/synthetic content: yes (AI voice and images).
- [ ] Add to the playlist named above (one playlist per vertical).
- [ ] Pin the comment below within minutes of publishing.
- [ ] Post the community poll (ideally a day before).
- [ ] Turn off auto-dubbing.
- [ ] Optional: cut a Short from the hook range below.
- [ ] Then run: python3 scripts/state_db.py episode-posted <slug> <youtube-url>
"""


def _mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
         "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    return {
        "width": int(video.get("width", 0)), "height": int(video.get("height", 0)),
        "duration": float(data["format"]["duration"]),
        "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def verify_video(info: dict, min_s: float, max_s: float) -> list[str]:
    problems = []
    if (info["width"], info["height"]) != (1920, 1080):
        problems.append(f"video is {info['width']}x{info['height']}, expected 1920x1080")
    if not min_s <= info["duration"] <= max_s:
        problems.append(f"video is {info['duration']:.1f}s, allowed {min_s:.0f}-{max_s:.0f}s")
    if not info["has_audio"]:
        problems.append("video has no audio stream")
    return problems


def build_posting_md(metadata: dict, duration: float) -> str:
    hook = metadata.get("shorts_hook") or {}
    parts = [
        f"# {metadata['title']}", "",
        f"Runtime: {_mmss(duration)}", "",
        "## Title", metadata["title"], "",
        "## Alternate titles (for Test & Compare)",
        *[f"- {t}" for t in metadata.get("title_alternates", [])], "",
        "## Description", metadata.get("description", ""), "",
        "## Tags", ", ".join(metadata.get("tags", [])), "",
        "## Playlist", metadata.get("playlist", "(not set)"), "",
        "## Pinned comment", metadata.get("pinned_comment", ""), "",
        "## Community poll", metadata.get("community_post", ""), "",
        "## Shorts hook range",
        f"{_mmss(hook['start'])}-{_mmss(hook['end'])}" if hook else "(not set)", "",
        CHECKLIST,
    ]
    return "\n".join(parts)


def _default_record(slug: str, doc: dict) -> None:
    import state_db
    state_db.episode_ready(state_db.get_db(), slug, doc)


def finalize(episode_dir: Path, output_root: Path = OUTPUT_ROOT, record=None, probe=probe) -> dict:
    record = record or _default_record
    slug = episode_dir.name
    log_path = episode_dir / "08_publish" / "finalize_log.json"
    if log_path.exists():
        log = json.loads(log_path.read_text())
        if log.get("status") == "ok":
            print(f"{slug} already finalized -> {log['output_dir']}")
            return log

    fmt = load_state()["format"]
    video = episode_dir / "07_edit" / f"mafia-of-business-{slug}.mp4"
    srt = episode_dir / "07_edit" / "captions.srt"
    metadata_path = episode_dir / "08_publish" / "metadata.json"
    thumb = episode_dir / "08_publish" / "thumbnail.png"
    missing = [str(p) for p in (video, srt, metadata_path, thumb) if not p.exists()]
    if missing:
        raise RuntimeError(f"cannot finalize {slug}, missing: {', '.join(missing)}")
    info = probe(video)
    problems = verify_video(info, fmt["runtime_min_seconds"], fmt["runtime_max_seconds"])
    if problems:
        raise RuntimeError(f"cannot finalize {slug}: " + "; ".join(problems))

    metadata = json.loads(metadata_path.read_text())
    out_dir = output_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in (video, srt, metadata_path, thumb):
        shutil.copy2(src, out_dir / src.name)
    (out_dir / "posting.md").write_text(build_posting_md(metadata, info["duration"]))

    now = datetime.now(timezone.utc).isoformat()
    record(slug, {"title": metadata["title"], "duration": round(info["duration"], 1),
                  "output_dir": str(out_dir), "status": "ready", "finalized_at": now})
    log = {"status": "ok", "output_dir": str(out_dir), "duration": round(info["duration"], 1), "at": now}
    log_path.write_text(json.dumps(log, indent=2))
    print(f"finalized {slug} -> {out_dir}")
    return log


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/finalize_episode.py <episode-slug>")
        sys.exit(1)
    try:
        finalize(WORKSPACE / "episodes" / sys.argv[1])
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
