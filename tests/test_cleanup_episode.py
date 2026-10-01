import json

import cleanup_episode as ce


def _make(tmp_path, upload_log):
    ep = tmp_path / "ep-1"
    for d in ("03_audio", "05_scenes", "07_edit", "02_script", "08_publish"):
        (ep / d).mkdir(parents=True)
    (ep / "topic.json").write_text("{}")
    (ep / "02_script" / "f.bin").write_bytes(b"x")
    (ep / "08_publish" / "upload_log.json").write_text(json.dumps(upload_log))
    return ep


def test_refuses_to_clean_unconfirmed_upload(tmp_path):
    ep = _make(tmp_path, {"content_lab": {"status": "failed"}})
    import pytest
    with pytest.raises(RuntimeError):
        ce.cleanup(ep)


def test_deletes_media_keeps_records(tmp_path):
    ep = _make(tmp_path, {"content_lab": {"status": "ok"}})
    assert sorted(ce.cleanup(ep)) == ["03_audio", "05_scenes", "07_edit"]
    for d in ("03_audio", "05_scenes", "07_edit"):
        assert not (ep / d).exists()
    for keep in ("topic.json", "02_script/f.bin", "08_publish/upload_log.json"):
        assert (ep / keep).exists()


def test_cleanup_is_idempotent(tmp_path):
    ep = _make(tmp_path, {"content_lab": {"status": "ok"}})
    ce.cleanup(ep)
    assert ce.cleanup(ep) == []
