import base64
import io
import json

import pytest
from PIL import Image

from scenes import flux_orchestrator as fo


def _png_b64():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


class FakeResponse:
    def __init__(self, status=200, body=None, text=""):
        self.status_code = status
        self._body = body if body is not None else {}
        self.text = text

    def json(self):
        return self._body


def ok():
    return FakeResponse(200, {"success": True, "result": {"image": _png_b64()}})


def entry(beat=1):
    return {"beat": beat, "prompt": "the host points at a chart", "seed": 7, "width": 1024, "height": 576}


def test_generate_image_sends_reference_and_returns_png():
    seen = {}

    def post(url, headers=None, data=None, files=None, timeout=None):
        seen.update(url=url, data=data, files=files)
        return ok()

    png = fo.generate_image(entry(), b"ref", "acct", "tok", "flux-2-klein-9b", post=post)
    assert png.startswith(b"\x89PNG")
    assert seen["url"].endswith("/acct/ai/run/@cf/black-forest-labs/flux-2-klein-9b")
    assert seen["data"]["prompt"].startswith(fo.REFERENCE_INSTRUCTION)
    assert seen["data"]["seed"] == "7"
    assert seen["files"]["input_image_0"][1] == b"ref"


def test_generate_image_retries_429_then_succeeds():
    calls, sleeps = [], []

    def post(*a, **k):
        calls.append(1)
        return FakeResponse(429, {"errors": [{"message": "slow down"}]}) if len(calls) == 1 else ok()

    assert fo.generate_image(entry(), b"r", "a", "t", "m", post=post, sleep_fn=sleeps.append).startswith(b"\x89PNG")
    assert sleeps == [fo.BACKOFF_BASE_SECONDS]


def test_quota_used_up_is_fatal_without_retrying():
    calls = []

    def post(*a, **k):
        calls.append(1)
        return FakeResponse(429, {"errors": [{"message": "you have used your daily free allocation of 10,000 neurons"}]})

    with pytest.raises(fo.FluxFatalError):
        fo.generate_image(entry(), b"r", "a", "t", "m", post=post, sleep_fn=lambda s: None)
    assert len(calls) == 1


def test_bad_credentials_are_fatal():
    with pytest.raises(fo.FluxFatalError):
        fo.generate_image(entry(), b"r", "a", "t", "m", post=lambda *a, **k: FakeResponse(403, {"errors": []}))


def test_generate_episode_scenes_writes_pngs_and_records_failures(tmp_path):
    plan = tmp_path / "prompt_plan.json"
    bad = dict(entry(2), prompt="BAD beat")
    plan.write_text(json.dumps([entry(1), bad]))
    ref = tmp_path / "ref.jpg"
    ref.write_bytes(b"ref")

    def post(url, headers=None, data=None, files=None, timeout=None):
        return FakeResponse(400, {"errors": [{"message": "bad"}]}) if "BAD" in data["prompt"] else ok()

    out = tmp_path / "scenes"
    done, failed = fo.generate_episode_scenes(
        "ep", plan, out, [1, 2, 9], post=post, sleep_fn=lambda s: None, reference_path=ref,
        workers=1, account_id="a", token="t")
    assert done == [1]
    assert failed == [2, 9]
    assert (out / "scene_0001.png").read_bytes().startswith(b"\x89PNG")
    assert "not found in prompt plan" in (out / "_flux_debug" / "scene_0009.error.txt").read_text()
    assert (out / "_flux_debug" / "scene_0002.error.txt").exists()
