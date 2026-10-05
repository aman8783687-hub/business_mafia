import json

import pytest

import finalize_episode as fe

META = {
    "title": "चाय वाला असल में कितना कमाता है? | Chai Business Model in Hindi",
    "title_alternates": ["चाय की टपरी का असली खेल", "₹10 की चाय में कितना मुनाफ़ा?"],
    "description": "एक कप चाय...\n\n⏱️ Chapters\n0:00 हुक",
    "tags": ["chai wala income", "चाय वाला कितना कमाता है"],
    "pinned_comment": "बोनस: ...",
    "community_post": "चाय वाला महीने में कितना कमाता है? A) 15k B) 50k C) 1 लाख+",
    "shorts_hook": {"start": 0.0, "end": 42.5},
    "playlist": "Khana & Street Food",
}


def _episode(tmp_path, slug="2026-10-02-chai-wala"):
    ep = tmp_path / "episodes" / slug
    for d in ("03_audio", "05_scenes", "07_edit", "08_publish", "02_script"):
        (ep / d).mkdir(parents=True)
    (ep / "07_edit" / f"mafia-of-business-{slug}.mp4").write_bytes(b"video")
    (ep / "07_edit" / "captions.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nएक\n")
    (ep / "08_publish" / "thumbnail.png").write_bytes(b"png")
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(META, ensure_ascii=False))
    (ep / "topic.json").write_text(json.dumps({"format": "list", "category": "Khana & Street Food"}))
    return ep


GOOD_INFO = {"width": 1920, "height": 1080, "duration": 601.2, "has_audio": True}


def test_verify_video_accepts_good_and_names_each_problem():
    assert fe.verify_video(GOOD_INFO, 480, 720) == []
    bad = {"width": 1280, "height": 720, "duration": 721.0, "has_audio": False}
    problems = fe.verify_video(bad, 480, 720)
    assert len(problems) == 3
    assert any("1280x720" in p for p in problems)
    assert any("721.0" in p for p in problems)
    assert any("audio" in p for p in problems)


def test_posting_md_has_everything_to_paste():
    md = fe.build_posting_md(META, 241.2)
    for needle in (META["title"], META["title_alternates"][1], "chai wala income", META["pinned_comment"],
                   META["community_post"], "0:00-0:42", "6-9 PM IST", "4:01", "Khana & Street Food"):
        assert needle in md


def test_finalize_copies_package_records_and_logs(tmp_path):
    ep = _episode(tmp_path)
    out_root = tmp_path / "output"
    records = []
    result = fe.finalize(ep, out_root, record=lambda slug, doc: records.append((slug, doc)),
                         probe=lambda p: GOOD_INFO)
    out = out_root / ep.name
    assert result["status"] == "ok"
    assert sorted(p.name for p in out.iterdir()) == sorted([
        f"mafia-of-business-{ep.name}.mp4", "thumbnail.png", "captions.srt", "metadata.json", "posting.md"])
    assert records[0][0] == ep.name and records[0][1]["status"] == "ready"
    assert records[0][1]["duration"] == 601.2
    assert (records[0][1]["format"], records[0][1]["category"]) == ("list", "Khana & Street Food")
    log = json.loads((ep / "08_publish" / "finalize_log.json").read_text())
    assert log["status"] == "ok" and log["output_dir"] == str(out)


def test_finalize_refuses_bad_video_and_writes_nothing(tmp_path):
    ep = _episode(tmp_path)
    with pytest.raises(RuntimeError, match="721.0"):
        fe.finalize(ep, tmp_path / "output", record=lambda *a: None,
                    probe=lambda p: {**GOOD_INFO, "duration": 721.0})
    assert not (tmp_path / "output").exists()
    assert not (ep / "08_publish" / "finalize_log.json").exists()


def test_finalize_rerun_after_cleanup_is_a_noop(tmp_path):
    ep = _episode(tmp_path)
    calls = []
    fe.finalize(ep, tmp_path / "output", record=lambda *a: calls.append(a), probe=lambda p: GOOD_INFO)
    import shutil
    shutil.rmtree(ep / "07_edit")  # cleanup ran
    result = fe.finalize(ep, tmp_path / "output", record=lambda *a: calls.append(a), probe=lambda p: GOOD_INFO)
    assert result["status"] == "ok"
    assert len(calls) == 1
