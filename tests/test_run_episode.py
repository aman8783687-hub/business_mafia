import json

import run_episode


def _episode(tmp_path, metadata, scenes=()):
    ep = tmp_path / "ep"
    (ep / "08_publish").mkdir(parents=True)
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False))
    (ep / "05_scenes").mkdir()
    for name in scenes:
        (ep / "05_scenes" / name).write_bytes(b"png")
    return ep


def test_thumbnail_args_use_text_accent_output_and_scene(tmp_path):
    ep = _episode(tmp_path, {"thumbnail_text": "चाय में ₹70?", "thumbnail_accent_word": "₹70?"},
                  scenes=["scene_0001.png"])
    args = run_episode.thumbnail_args(ep)
    assert args[1] == "चाय में ₹70?"
    assert args[args.index("--accent-word") + 1] == "₹70?"
    assert args[args.index("--out") + 1].endswith("08_publish/thumbnail.png")
    assert args[args.index("--scene") + 1].endswith("05_scenes/scene_0001.png")


def test_thumbnail_beat_selects_the_scene_and_missing_scene_falls_back(tmp_path):
    ep = _episode(tmp_path, {"thumbnail_text": "X", "thumbnail_beat": 3}, scenes=["scene_0003.png"])
    assert run_episode.thumbnail_args(ep)[-1].endswith("scene_0003.png")
    ep2 = _episode(tmp_path / "b", {"thumbnail_text": "X", "thumbnail_beat": 9})
    assert "--scene" not in run_episode.thumbnail_args(ep2)


def test_no_thumbnail_text_means_no_thumbnail_stage(tmp_path):
    assert run_episode.thumbnail_args(_episode(tmp_path, {"title": "x"})) is None


def test_stage_order_checks_script_first_and_finalizes_before_cleanup():
    scripts = [s for _, s in run_episode.STAGES]
    assert scripts[0] == "check_script.py"
    assert scripts.index("finalize_episode.py") < scripts.index("cleanup_episode.py")
    assert "publish_all.py" not in scripts
