#!/usr/bin/env python3
"""Stitch an episode's narration chunks into vo_master.wav and write
timings.json (per-chunk AND per-beat timing, since scenes are cut one per
beat). Implements references/voice-and-audio.md's stitching spec:
trim each chunk to ~50ms head/tail silence, short fades to kill clicks,
gaps sized by structural distance (same-section vs section-break),
final loudness normalize to -14 LUFS / -1 dBTP, 48kHz/24-bit.

Usage: python3 scripts/stitch_audio.py <episode-slug>
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from state import load_state

WORKSPACE = Path(__file__).resolve().parent.parent
STATE = load_state()
_audio = STATE["audio"]
GAP_WITHIN_SECTION = _audio["gap_within_section_seconds"]
GAP_SECTION_BREAK = _audio["gap_section_break_seconds"]
FADE_SECONDS = _audio["fade_seconds"]
TRIM_SILENCE_DB = _audio["trim_silence_db"]
INTERNAL_SILENCE_MIN_DURATION = _audio["internal_silence_min_duration_seconds"]  # any internal pause longer than this is TTS dead air, not a deliberate breath
TARGET_LUFS = _audio["target_lufs"]
TRUE_PEAK = _audio["true_peak_db"]
SCENE_SECONDS_MIN = STATE["format"]["scene_seconds_min"]
SCENE_SECONDS_MAX = STATE["format"]["scene_seconds_max"]
RUNTIME_MIN = STATE["format"]["runtime_min_seconds"]
RUNTIME_MAX = STATE["format"]["runtime_max_seconds"]


def check_runtime(total_seconds: float, min_s: float, max_s: float) -> str | None:
    """None when the narration fits the channel's runtime window, else the
    message the agent acts on. Over the cap the fix is a shorter script,
    never a faster voice (spec 4.3)."""
    if total_seconds > max_s:
        return (f"narration {total_seconds:.1f}s is over the {max_s:.0f}s cap: trim the script "
                f"(~{(total_seconds - max_s) * 140 / 60:.0f} words), then rerun narration and stitch")
    if total_seconds < min_s:
        return (f"narration {total_seconds:.1f}s is too short (minimum {min_s:.0f}s): "
                f"add a money leak to [KHEL], then rerun narration and stitch")
    return None


def normalize_section(name: str) -> str:
    name = name.strip().lower().replace(" ", "_")
    return name[4:] if name.startswith("the_") else name


def parse_script(script_path: Path):
    """Return {beat_id: {"section": str, "text": str, "words": int}}."""
    raw = script_path.read_text()
    parts = re.split(r"\[([A-Z_]+)\]", raw)
    beats = {}
    for i in range(1, len(parts), 2):
        section = normalize_section(parts[i])
        body = parts[i + 1]
        for match in re.finditer(r"^\s*(\d+)\.\s*(.+)$", body, re.MULTILINE):
            beat_id, text = int(match.group(1)), match.group(2).strip()
            beats[beat_id] = {"section": section, "text": text, "words": len(text.split())}
    return beats


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def ffprobe_duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)])
    return float(out.strip())


def trim_and_fade(src: Path, dst: Path):
    # Trim leading/trailing silence to ~TRIM threshold, cut out any internal
    # dead air (TTS occasionally over-holds on a comma or em-dash), then
    # apply short fades in/out to remove any remaining click at the cut point.
    # Every piece written here is normalized to 48kHz stereo pcm_s24le.
    # The concat demuxer does NOT resample: if chunks stayed at edge-tts's
    # native 24kHz mono while gap silences were 48kHz stereo, the whole
    # stream got read at the first file's rate and every gap stretched
    # ~4x (0.55s -> 2.28s, 1.0s -> 4.06s).
    trimmed = dst.with_suffix(".trimmed.wav")
    run([
        "ffmpeg", "-y", "-i", str(src), "-af",
        f"silenceremove=start_periods=1:start_duration=0:start_threshold={TRIM_SILENCE_DB}:start_silence=0.05,"
        f"areverse,silenceremove=start_periods=1:start_duration=0:start_threshold={TRIM_SILENCE_DB}:start_silence=0.05,areverse",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
        str(trimmed),
    ])
    detrimmed = dst.with_suffix(".detrim.wav")
    run([
        "ffmpeg", "-y", "-i", str(trimmed), "-af",
        f"silenceremove=stop_periods=-1:stop_duration={INTERNAL_SILENCE_MIN_DURATION}:stop_threshold={TRIM_SILENCE_DB}",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
        str(detrimmed),
    ])
    dur = ffprobe_duration(detrimmed)
    fade_out_start = max(0.0, dur - FADE_SECONDS)
    run([
        "ffmpeg", "-y", "-i", str(detrimmed), "-af",
        f"afade=t=in:d={FADE_SECONDS},afade=t=out:st={fade_out_start}:d={FADE_SECONDS}",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le",
        str(dst),
    ])
    trimmed.unlink()
    detrimmed.unlink()
    return ffprobe_duration(dst)


def make_silence(seconds: float, workdir: Path) -> Path:
    path = workdir / f"silence_{seconds:.3f}.wav"
    if not path.exists():
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", str(seconds),
             "-c:a", "pcm_s24le", str(path)])
    return path


_SILENCE_RE = re.compile(r"silence_start:\s*([\d.]+)|silence_end:\s*([\d.]+)")


def _detect_silences(path: Path, db: str, min_duration: float) -> list[tuple[float, float]]:
    """Every silence interval >= min_duration in `path`, via ffmpeg's
    silencedetect (a read-only analysis filter -- doesn't modify audio,
    just logs to stderr). Used to figure out where trim_and_fade's
    silenceremove calls actually cut, so raw edge-tts word offsets (which
    know nothing about those cuts) can be remapped onto the trimmed
    timeline."""
    out = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", f"silencedetect=noise={db}:d={min_duration}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts, ends = [], []
    for m in _SILENCE_RE.finditer(out):
        if m.group(1):
            starts.append(float(m.group(1)))
        elif m.group(2):
            ends.append(float(m.group(2)))
    return list(zip(starts, ends))


def build_word_offset_map(raw_src: Path, trim_silence_db: str, internal_min_duration: float):
    """Returns a function raw_offset_seconds -> trimmed_track_offset_seconds
    for this one chunk's raw (pre-trim_and_fade) audio.

    Two passes, matching trim_and_fade's own two silenceremove stages:
    - A short-duration pass (0.02s) finds the leading silence (removed
      unconditionally by the start-trim stage regardless of length).
    - A pass at internal_min_duration finds internal pauses long enough
      to be cut by the stop_periods=-1 internal-removal stage; anything
      shorter is a natural pause trim_and_fade actually leaves alone, so
      it must NOT be subtracted here either.
    Both stages' cuts are subtracted cumulatively so a word after several
    removed gaps lands at the right spot in the final trimmed+faded file.
    The ~20ms afade in/out isn't corrected for -- well within tolerance
    for phrase-level caption sync.
    """
    all_silences = _detect_silences(raw_src, trim_silence_db, 0.02)
    leading_end = 0.0
    internal_cuts: list[tuple[float, float]] = []
    for start, end in all_silences:
        if start <= 0.05 and leading_end == 0.0:
            leading_end = end
        elif (end - start) >= internal_min_duration:
            internal_cuts.append((start, end))

    def remap(raw_offset: float) -> float:
        t = raw_offset - leading_end
        for start, end in internal_cuts:
            if start >= leading_end and end <= raw_offset:
                t -= (end - start)
        return max(0.0, t)

    return remap


def load_word_events(audio_dir: Path, chunk_index: str) -> list[dict]:
    path = audio_dir / f"chunk_{chunk_index}.wordbounds.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("type") != "WordBoundary":
            continue
        events.append({
            "text": msg["text"],
            "offset": msg["offset"] / 1e7,  # 100ns ticks -> seconds
            "duration": msg["duration"] / 1e7,
        })
    return events


def find_out_of_range_beats(beats: list[dict], min_seconds: float, max_seconds: float) -> list[int]:
    """Pure check against the format's per-scene target window (per
    script-formula.md's pacing guidance: ~20-35 words/beat -> 8-14s at
    ~150 wpm). Returns the beat numbers whose (end - start) duration
    falls outside [min_seconds, max_seconds]. Guidance, not a gate --
    an occasional short/long beat is fine; callers should warn, not fail."""
    return [b["beat"] for b in beats if not (min_seconds <= (b["end"] - b["start"]) <= max_seconds)]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/stitch_audio.py <episode-slug>")
        sys.exit(1)
    slug = sys.argv[1]
    episode_dir = WORKSPACE / "episodes" / slug
    audio_dir = episode_dir / "03_audio"
    chunk_plan = json.loads((audio_dir / "chunk_plan.json").read_text())["chunks"]
    beats = parse_script(episode_dir / "02_script" / "script.md")

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        concat_entries = []  # list of (path, duration)
        chunk_timings = []
        beat_timings = []
        word_timings = []
        cursor = 0.0
        prev_section = None

        for i, chunk in enumerate(chunk_plan):
            index = f"{chunk['id']:04d}"
            src = audio_dir / f"chunk_{index}.mp3"
            if not src.exists():
                print(f"Missing {src}, run generate_narration_chunks.py first.")
                sys.exit(1)
            trimmed = workdir / f"chunk_{index}.wav"
            duration = trim_and_fade(src, trimmed)

            first_beat_section = beats[chunk["beats"][0]]["section"]
            if i > 0:
                gap = GAP_SECTION_BREAK if first_beat_section != prev_section else GAP_WITHIN_SECTION
                silence = make_silence(gap, workdir)
                concat_entries.append((silence, gap))
                cursor += gap
            prev_section = beats[chunk["beats"][-1]]["section"]

            start = cursor
            end = cursor + duration

            word_events = load_word_events(audio_dir, index)
            if word_events:
                remap = build_word_offset_map(src, TRIM_SILENCE_DB, INTERNAL_SILENCE_MIN_DURATION)
                for w in word_events:
                    local_start = remap(w["offset"])
                    local_end = remap(w["offset"] + w["duration"])
                    if local_end <= local_start:  # word fell inside a trimmed gap -- skip rather than emit a zero/negative-length cue
                        continue
                    word_timings.append({
                        "text": w["text"],
                        "start": round(start + local_start, 3),
                        "end": round(start + local_end, 3),
                    })
            chunk_timings.append({
                "id": chunk["id"], "beats": chunk["beats"], "text": chunk["text"],
                "start": round(start, 3), "end": round(end, 3), "section": first_beat_section,
            })

            # Split this chunk's duration across its constituent beats,
            # proportional to each beat's word count.
            beat_ids = chunk["beats"]
            total_words = sum(beats[b]["words"] for b in beat_ids) or len(beat_ids)
            beat_cursor = start
            for b in beat_ids:
                share = beats[b]["words"] / total_words if total_words else 1 / len(beat_ids)
                b_dur = duration * share
                beat_timings.append({
                    "beat": b, "text": beats[b]["text"], "section": beats[b]["section"],
                    "start": round(beat_cursor, 3), "end": round(beat_cursor + b_dur, 3),
                })
                beat_cursor += b_dur

            concat_entries.append((trimmed, duration))
            cursor = end

        list_path = workdir / "concat_list.txt"
        with open(list_path, "w") as f:
            for path, _ in concat_entries:
                f.write(f"file '{path.resolve()}'\n")

        raw_concat = workdir / "raw_concat.wav"
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "pcm_s24le", "-ar", "48000", str(raw_concat)])

        out_path = audio_dir / "vo_master.wav"
        run([
            "ffmpeg", "-y", "-i", str(raw_concat), "-af",
            f"loudnorm=I={TARGET_LUFS}:TP={TRUE_PEAK}:LRA=11",
            "-ar", "48000", "-c:a", "pcm_s24le", str(out_path),
        ])

    total = ffprobe_duration(out_path)
    timings = {"total_seconds": round(total, 3), "chunks": chunk_timings, "beats": beat_timings}
    (audio_dir / "timings.json").write_text(json.dumps(timings, indent=2))

    print(f"vo_master.wav: {total:.1f}s ({int(total) // 60}:{int(total) % 60:02d})")
    print(f"timings.json written — {len(chunk_timings)} chunks, {len(beat_timings)} beats")

    out_of_range = find_out_of_range_beats(beat_timings, SCENE_SECONDS_MIN, SCENE_SECONDS_MAX)
    if out_of_range:
        print(f"WARNING: {len(out_of_range)} beat(s) fall outside the "
              f"{SCENE_SECONDS_MIN}-{SCENE_SECONDS_MAX}s scene target "
              f"(script-formula.md's per-beat pacing guidance): {out_of_range}")

    if word_timings:
        (audio_dir / "word_timings.json").write_text(json.dumps({"words": word_timings}, indent=2))
        print(f"word_timings.json written — {len(word_timings)} words (for animated captions)")
    else:
        print("No per-chunk .wordbounds.jsonl files found -- word_timings.json not written. "
              "Re-run generate_narration_chunks.py (it now captures word timing) to enable captions.")

    runtime_error = check_runtime(total, RUNTIME_MIN, RUNTIME_MAX)
    if runtime_error:
        print(f"ERROR: {runtime_error}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
