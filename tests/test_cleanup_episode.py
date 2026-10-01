import json

import pytest

import cleanup_episode as ce


def _make(tmp_path, finalize_log):
    ep = tmp_path / "ep-1"
    for d in ("03_audio", "05_scenes", "07_edit", "02_script", "08_publish"):
        (ep / d).mkdir(parents=True)
    (ep / "topic.json").write_text("{}")
    (ep / "02_script" / "f.bin").write_bytes(b"x")
    if finalize_log is not None:
        (ep / "08_publish" / "finalize_log.json").write_text(json.dumps(finalize_log))
    return ep


def test_refuses_to_clean_unfinalized_episode(tmp_path):
    with pytest.raises(RuntimeError):
        ce.cleanup(_make(tmp_path, None))


def test_refuses_to_clean_failed_finalize(tmp_path):
    with pytest.raises(RuntimeError):
        ce.cleanup(_make(tmp_path, {"status": "failed"}))


def test_deletes_media_keeps_records(tmp_path):
    ep = _make(tmp_path, {"status": "ok"})
    assert sorted(ce.cleanup(ep)) == ["03_audio", "05_scenes", "07_edit"]
    for keep in ("topic.json", "02_script/f.bin", "08_publish/finalize_log.json"):
        assert (ep / keep).exists()


def test_cleanup_is_idempotent(tmp_path):
    ep = _make(tmp_path, {"status": "ok"})
    ce.cleanup(ep)
    assert ce.cleanup(ep) == []
