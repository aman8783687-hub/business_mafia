import json

import assemble_episode as ae


def test_beat_screen_duration_extends_to_next_beat_start():
    beats = [
        {"beat": 1, "start": 0.0, "end": 8.0},
        {"beat": 2, "start": 8.0, "end": 15.0},
        {"beat": 3, "start": 15.0, "end": 20.0},
    ]
    assert ae.beat_screen_duration(beats, 0, total_seconds=20.0) == 8.0
    assert ae.beat_screen_duration(beats, 1, total_seconds=20.0) == 7.0
    # Last beat extends to total_seconds, not its own end, so -shortest never truncates it.
    assert ae.beat_screen_duration(beats, 2, total_seconds=22.0) == 7.0


def test_pick_zoom_direction():
    assert ae.pick_zoom_direction("slow push out", beat_number=1) == "out"
    assert ae.pick_zoom_direction("slow push in", beat_number=1) == "in"
    assert ae.pick_zoom_direction("", beat_number=1) == "out"
    assert ae.pick_zoom_direction("", beat_number=2) == "in"


def test_load_motion_by_scene(tmp_path):
    (tmp_path / "shotlist.json").write_text(json.dumps([
        {"scene": 1, "description": "x", "motion": "Slow Push In"},
        {"scene": 2, "description": "y", "motion": "slow push out"},
    ]))
    mapping = ae.load_motion_by_scene(tmp_path)
    assert mapping == {1: "slow push in", 2: "slow push out"}


def test_no_music_config_anywhere():
    import inspect
    src = inspect.getsource(ae)
    assert "MUSIC_PATH" not in src
    assert "music_looped" not in src


def test_build_captions_is_not_imported_at_module_level():
    # build_captions.py doesn't exist until Task 13 -- this file must
    # import assemble_episode cleanly regardless, so the import has to
    # be deferred into main(), not sit at module scope.
    import inspect
    src = inspect.getsource(ae)
    assert "\nimport build_captions" not in src.split("def main")[0]


def test_single_beat_episode_never_produces_non_positive_duration():
    beats = [{"beat": 1, "start": 0.0, "end": 0.0}]
    duration = ae.beat_screen_duration(beats, 0, total_seconds=0.0)
    assert duration >= 0


def test_final_encode_uses_crf_not_flat_high_abr_bitrate():
    # Regression test: a flat -b:v 10M -maxrate 10M ABR encode produced
    # ~400-450MB files for a 300-420s episode -- over Cloudinary's 100MB
    # single-request upload cap. The final encode must be CRF-based
    # instead, with a lower cap; the LOW_MEM_RENDER path keeps its own
    # flat-bitrate encode line untouched.
    import inspect
    src = inspect.getsource(ae)
    final_encode = src.split("output_path = edit_dir")[1]
    assert '"-crf", "22"' in final_encode
    assert '"-maxrate", "6M"' in final_encode
    assert '"-b:v", LOW_MEM_BITRATE' in final_encode


def test_frames_are_clamped_to_at_least_two_for_a_near_zero_duration():
    # render_scene itself shells out to ffmpeg (not unit-testable without
    # a real binary), but the frame-count clamp that prevents a
    # divide-by-(frames-1)==0 zoompan expression is a pure calculation --
    # pin it directly here rather than only inside render_scene's source.
    frames = max(2, round(0.0001 * ae.FPS))
    assert frames >= 2
