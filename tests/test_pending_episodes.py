import json

import pending_episodes as pe


def _episode(base, slug, upload_log=None):
    ep = base / slug
    (ep / "02_script").mkdir(parents=True)
    (ep / "02_script" / "script.md").write_text("[COLD_OPEN]\n1. x\n")
    if upload_log is not None:
        (ep / "08_publish").mkdir(parents=True)
        (ep / "08_publish" / "upload_log.json").write_text(json.dumps(upload_log))
    return ep


def test_cleaned_uploaded_episode_is_not_pending(tmp_path):
    _episode(tmp_path, "a", {"content_lab": {"status": "ok", "url": "u"}})
    assert pe.find_pending(tmp_path) == []


def test_unfinished_episode_is_pending(tmp_path):
    _episode(tmp_path, "b")
    assert pe.find_pending(tmp_path) == ["b"]
