import json

import pending_episodes as pe


def _episode(base, slug, finalize_log=None):
    ep = base / slug
    (ep / "02_script").mkdir(parents=True)
    (ep / "02_script" / "script.md").write_text("[HOOK]\n1. x\n")
    if finalize_log is not None:
        (ep / "08_publish").mkdir(parents=True)
        (ep / "08_publish" / "finalize_log.json").write_text(json.dumps(finalize_log))
    return ep


def test_finalized_episode_is_not_pending(tmp_path):
    _episode(tmp_path, "a", {"status": "ok", "output_dir": "x"})
    assert pe.find_pending(tmp_path) == []


def test_unfinished_episode_is_pending(tmp_path):
    _episode(tmp_path, "b")
    assert pe.find_pending(tmp_path) == ["b"]
