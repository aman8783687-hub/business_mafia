#!/usr/bin/env python3
"""Assembles one episode's final 1920x1080 render: Ken Burns zoompan per
scene, concatenation, an ambience-only audio mix (no music -- see
build_ambience.py), loudness mastering, and burned-in captions. Ported
from Dmoo Way's assemble_episode.py; the entire music-bed block is
deleted, replaced with an optional ambience bed as the only non-voice
audio input.

Usage (from MafiaOfBusiness/):
    python3 scripts/assemble_episode.py <episode-slug> [--no-ambience]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state, parse_resolution  # noqa: E402
import build_ambience  # noqa: E402
# build_captions is imported lazily inside main(), not here -- see this
# task's Interfaces note: it doesn't exist until Task 13, and this
# module must stay importable (for its own tests) before that lands.

WORKSPACE = SCRIPTS_DIR.parent
STATE = load_state()
FPS = STATE["format"]["fps"]
WIDTH, HEIGHT = parse_resolution(STATE["style_lock"]["resolution"])
TARGET_LUFS = STATE["audio"]["target_lufs"]
TRUE_PEAK = STATE["audio"]["true_peak_db"]
ZOOM_DELTA = STATE["format"]["zoom_delta"]

LOW_MEM_BITRATE = "3M"


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{result.stderr[-2000:]}")


def ffprobe_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return float(result.stdout.strip())


def beat_screen_duration(beats: list[dict], index: int, total_seconds: float) -> float:
    # Extends to the NEXT beat's start (or total_seconds for the last beat),
    # not its own end-start -- avoids -shortest truncating the ending.
    if index + 1 < len(beats):
        return beats[index + 1]["start"] - beats[index]["start"]
    return total_seconds - beats[index]["start"]


def caption_filter(ass_path: str) -> str:
    """ffmpeg filter graph that burns the ASS captions in. Uses the `ass`
    filter (not `subtitles`) because only it exposes `shaping`: libass
    defaults to simple shaping, which mangles Devanagari conjuncts and
    matras (found 2026-10-01); complex shaping uses HarfBuzz."""
    escaped = str(ass_path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return f"[0:v]ass='{escaped}':shaping=complex[v]"


def load_motion_by_scene(scenes_dir: Path) -> dict[int, str]:
    import json
    shotlist = json.loads((scenes_dir / "shotlist.json").read_text())
    return {entry["scene"]: entry.get("motion", "").lower() for entry in shotlist}


def pick_zoom_direction(motion: str, beat_number: int) -> str:
    if "out" in motion:
        return "out"
    if "in" in motion:
        return "in"
    return "out" if beat_number % 2 == 1 else "in"


def render_scene(image_path: Path, duration: float, out_path: Path, beat_number: int,
                  motion_by_scene: dict[int, str], low_mem: bool) -> None:
    width, height = (int(WIDTH * 0.6) // 2 * 2, int(HEIGHT * 0.6) // 2 * 2) if low_mem else (WIDTH, HEIGHT)
    frames = max(2, round(duration * FPS))
    direction = pick_zoom_direction(motion_by_scene.get(beat_number, ""), beat_number)
    zmax = 1 + ZOOM_DELTA
    z_expr = f"{zmax}-{ZOOM_DELTA}*on/({frames}-1)" if direction == "out" else f"1+{ZOOM_DELTA}*on/({frames}-1)"
    vf = (f"scale={width}:{height}:flags=lanczos,"
          f"zoompan=z='{z_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={width}x{height}:fps={FPS},"
          f"format=yuv420p")
    bitrate = LOW_MEM_BITRATE if low_mem else "10M"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(image_path), "-t", str(duration), "-vf", vf,
         "-c:v", "libx264", "-preset", "veryfast", "-b:v", bitrate, str(out_path)])


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    slug = argv[0]
    use_ambience = STATE.get("ambience", {}).get("enabled", False) and "--no-ambience" not in argv
    low_mem = bool(__import__("os").environ.get("LOW_MEM_RENDER"))

    episode_dir = WORKSPACE / "episodes" / slug
    audio_dir = episode_dir / "03_audio"
    scenes_dir = episode_dir / "05_scenes"
    edit_dir = episode_dir / "07_edit"
    edit_dir.mkdir(parents=True, exist_ok=True)

    import json
    timings = json.loads((audio_dir / "timings.json").read_text())
    beats = timings["beats"]
    total_seconds = timings["total_seconds"]

    missing = [b["beat"] for b in beats if not (scenes_dir / f"scene_{b['beat']:04d}.png").exists()]
    if missing:
        print(f"Missing scene PNGs for beats: {missing}", file=sys.stderr)
        return 1

    motion_by_scene = load_motion_by_scene(scenes_dir)
    clip_paths = []
    for i, b in enumerate(beats):
        duration = beat_screen_duration(beats, i, total_seconds)
        clip_path = edit_dir / f"clip_{b['beat']:04d}.mp4"
        render_scene(scenes_dir / f"scene_{b['beat']:04d}.png", duration, clip_path, b["beat"], motion_by_scene, low_mem)
        clip_paths.append(clip_path)

    concat_list = edit_dir / "concat_list.txt"
    concat_list.write_text("".join(f"file '{p.name}'\n" for p in clip_paths))
    body_silent = edit_dir / "body_silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(body_silent)])

    voice_path = audio_dir / "vo_master.wav"
    if use_ambience:
        ambience_path = build_ambience.build(slug, total_seconds)
        mix_graph = "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0[mixed]"
        inputs = ["-i", str(voice_path), "-i", str(ambience_path)]
    else:
        mix_graph = "[0:a]anull[mixed]"
        inputs = ["-i", str(voice_path)]

    mixed_audio = edit_dir / "mixed_audio.wav"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", mix_graph, "-map", "[mixed]", str(mixed_audio)])

    mastered_audio = edit_dir / "mastered_audio.wav"
    run(["ffmpeg", "-y", "-i", str(mixed_audio), "-af",
         f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11", str(mastered_audio)])

    captions_ass_path = None
    if STATE.get("captions", {}).get("enabled") and (audio_dir / "word_timings.json").exists():
        import build_captions  # deferred import -- see module-top comment
        captions_ass_path = build_captions.build(slug)
    else:
        print("No word_timings.json -- proceeding without burned-in captions.")

    output_path = edit_dir / f"redhat-engineer-{slug}-episode.mp4"
    cmd = ["ffmpeg", "-y", "-i", str(body_silent), "-i", str(mastered_audio)]
    if captions_ass_path:
        cmd += ["-filter_complex", caption_filter(str(captions_ass_path)), "-map", "[v]", "-map", "1:a"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    # CRF-based rate control, not a flat high ABR bitrate: these are slow
    # Ken Burns pans over still painted images, which compress very well,
    # so a quality target (CRF) with a cap (maxrate/bufsize) lands around
    # 3-5 Mbps average instead of pinning every frame to 10 Mbps. At a
    # 300-420s runtime, a flat 10M/10M encode produced ~400-450MB files --
    # well over Cloudinary's 100MB single-request upload cap. The
    # LOW_MEM_RENDER path keeps its own lower flat-bitrate encode
    # unchanged (it's already well under the cap).
    rate_control = (["-b:v", LOW_MEM_BITRATE, "-maxrate", LOW_MEM_BITRATE, "-bufsize", "8M"] if low_mem
                     else ["-crf", "22", "-maxrate", "6M", "-bufsize", "12M"])
    cmd += ["-c:v", "libx264", "-profile:v", "high", "-preset", "veryfast", "-threads", "2",
            *rate_control, "-r", str(FPS),
            "-c:a", "aac", "-b:a", "256k", "-shortest", str(output_path)]
    run(cmd)

    srt_path = edit_dir / "captions.srt"
    lines = []
    for i, b in enumerate(beats, start=1):
        def fmt(t):
            h, rem = divmod(t, 3600)
            m, s = divmod(rem, 60)
            ms = int((s - int(s)) * 1000)
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"
        lines.append(f"{i}\n{fmt(b['start'])} --> {fmt(b['end'])}\n{b['text']}\n")
    srt_path.write_text("\n".join(lines))

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
