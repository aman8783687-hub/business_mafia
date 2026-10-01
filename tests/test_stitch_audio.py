import json
import subprocess

import stitch_audio


def test_config_pulled_from_channel_state():
    assert stitch_audio.GAP_WITHIN_SECTION == 0.55
    assert stitch_audio.GAP_SECTION_BREAK == 1.0
    assert stitch_audio.TARGET_LUFS == -14.0


def test_parse_script(tmp_path):
    script = tmp_path / "script.md"
    script.write_text("[COLD_OPEN]\n1. The keeper vanished mid-shift.\n\n[SETUP]\n2. It was 1920.\n")
    parsed = stitch_audio.parse_script(script)
    assert parsed[1]["section"] == "cold_open"
    assert parsed[1]["text"] == "The keeper vanished mid-shift."
    assert parsed[1]["words"] == 4
    assert parsed[2]["section"] == "setup"


def test_make_silence_produces_correct_duration(tmp_path):
    path = stitch_audio.make_silence(0.5, tmp_path)
    duration = stitch_audio.ffprobe_duration(path)
    assert abs(duration - 0.5) < 0.05


def test_find_out_of_range_beats_flags_short_and_long_beats():
    beats = [
        {"beat": 1, "start": 0.0, "end": 10.0},   # 10s -- in range
        {"beat": 2, "start": 10.0, "end": 15.0},  # 5s -- too short
        {"beat": 3, "start": 15.0, "end": 23.0},  # 8s -- in range (boundary)
        {"beat": 4, "start": 23.0, "end": 37.0},  # 14s -- in range (boundary)
        {"beat": 5, "start": 37.0, "end": 55.0},  # 18s -- too long
    ]
    assert stitch_audio.find_out_of_range_beats(beats, 8.0, 14.0) == [2, 5]


def test_find_out_of_range_beats_reads_bounds_not_hardcoded():
    # Same beats, but a wider window makes everything pass -- proves the
    # bounds are parameters, not baked-in 8/14 constants.
    beats = [
        {"beat": 1, "start": 0.0, "end": 5.0},
        {"beat": 2, "start": 5.0, "end": 23.0},
    ]
    assert stitch_audio.find_out_of_range_beats(beats, 1.0, 100.0) == []
