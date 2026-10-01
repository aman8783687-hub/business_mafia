import json

import pytest

from scenes import cloudflare_orchestrator as co

# A minimal, genuinely valid 1x1 transparent PNG -- real magic bytes so
# the `startswith(b"\x89PNG")` validity check in the module under test
# is exercised against real data, not a placeholder string.
_TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeResponse:
    def __init__(self, status_code=200, content=b"", headers=None, text=""):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}
        self.text = text


def make_entry(beat=1, seed=42):
    return {"beat": beat, "prompt": "a foggy dock, style", "seed": seed,
            "width": 1024, "height": 576, "guidance_scale": 7.5, "num_inference_steps": 20}


def test_generate_one_returns_png_bytes():
    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(200, content=_TINY_PNG)

    result = co.generate_one(make_entry(), "token123", "acct123", session=Session())
    assert result == _TINY_PNG


def test_generate_one_retries_on_429():
    sleeps = []
    calls = []

    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            calls.append(1)
            if len(calls) == 1:
                return FakeResponse(429, headers={"retry-after": "3"})
            return FakeResponse(200, content=_TINY_PNG)

    result = co.generate_one(make_entry(), "token123", "acct123", session=Session(),
                              sleep_fn=lambda s: sleeps.append(s))
    assert result == _TINY_PNG
    assert len(calls) == 2
    # wait = float(retry-after) + attempt; attempt is 0 on the first loop
    # iteration, so this must be a real backoff derived from the header,
    # not an ignored fixed/zero sleep.
    assert sleeps == [3.0]


def test_generate_one_retries_on_5xx_then_raises_if_persistent():
    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(500, text="boom")

    with pytest.raises(co.CloudflareError):
        co.generate_one(make_entry(), "token123", "acct123", session=Session(), sleep_fn=lambda s: None)


def test_generate_one_raises_immediately_on_other_error_status():
    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(400, text="bad request")

    with pytest.raises(co.CloudflareError):
        co.generate_one(make_entry(), "token123", "acct123", session=Session(), sleep_fn=lambda s: None)


def test_generate_one_sends_style_lock_and_entry_params():
    """Pins the exact request body every job must carry (negative prompt
    from style_lock, and the entry's own width/height/steps/guidance/seed
    mapped to Cloudflare's field names) by capturing the actual POST body
    and URL generate_one sends."""
    captured = {}

    class CapturingSession:
        def post(self, url, json=None, headers=None, timeout=None):
            captured["url"] = url
            captured["body"] = json
            captured["headers"] = headers
            return FakeResponse(200, content=_TINY_PNG)

    entry = make_entry()
    co.generate_one(entry, "token123", "acct123", session=CapturingSession())

    assert captured["url"] == f"{co.API_BASE}/acct123/ai/run/{co.MODEL}"
    assert captured["headers"]["Authorization"] == "Bearer token123"
    body = captured["body"]
    assert body["negative_prompt"] == co.NEGATIVE_PROMPT
    assert body["negative_prompt"]  # the SDXL fallback always sends the channel's negative prompt
    assert body["width"] == entry["width"]
    assert body["height"] == entry["height"]
    assert body["num_steps"] == entry["num_inference_steps"]
    assert body["guidance"] == entry["guidance_scale"]
    assert body["seed"] == entry["seed"]
    assert body["prompt"] == entry["prompt"]


def test_generate_episode_scenes_all_succeed(tmp_path):
    plan = [make_entry(1, seed=1), make_entry(2, seed=2)]
    plan_path = tmp_path / "prompt_plan.json"
    plan_path.write_text(json.dumps(plan))

    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(200, content=_TINY_PNG)

    succeeded, failed = co.generate_episode_scenes(
        "ep-1", plan_path, tmp_path / "out", [1, 2],
        api_token="token123", account_id="acct123", session=Session(), sleep_fn=lambda s: None,
    )
    assert succeeded == [1, 2]
    assert failed == []
    assert (tmp_path / "out" / "scene_0001.png").read_bytes() == _TINY_PNG
    assert (tmp_path / "out" / "_cloudflare_debug" / "scene_0001.json").exists()


def test_generate_episode_scenes_partial_failure(tmp_path):
    plan = [make_entry(1, seed=1), make_entry(2, seed=2)]
    plan_path = tmp_path / "prompt_plan.json"
    plan_path.write_text(json.dumps(plan))

    class FlakySession:
        def post(self, url, json=None, headers=None, timeout=None):
            if json["seed"] == 1:
                return FakeResponse(200, content=_TINY_PNG)
            return FakeResponse(400, text="bad request")

    succeeded, failed = co.generate_episode_scenes(
        "ep-1", plan_path, tmp_path / "out", [1, 2],
        api_token="token123", account_id="acct123", session=FlakySession(), sleep_fn=lambda s: None,
    )
    assert succeeded == [1]
    assert failed == [2]
    assert (tmp_path / "out" / "_cloudflare_debug" / "scene_0002.error.txt").exists()


def test_generate_episode_scenes_missing_beat_is_reported_as_failed(tmp_path):
    """A beat requested that has no matching entry in the prompt plan
    must not be silently dropped -- it must show up in `failed` with an
    explanatory debug file, not vanish from both lists."""
    plan = [make_entry(1, seed=1)]
    plan_path = tmp_path / "prompt_plan.json"
    plan_path.write_text(json.dumps(plan))

    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(200, content=_TINY_PNG)

    succeeded, failed = co.generate_episode_scenes(
        "ep-1", plan_path, tmp_path / "out", [1, 99],
        api_token="token123", account_id="acct123", session=Session(), sleep_fn=lambda s: None,
    )
    assert succeeded == [1]
    assert failed == [99]
    error_text = (tmp_path / "out" / "_cloudflare_debug" / "scene_0099.error.txt").read_text()
    assert "99" in error_text


def test_generate_episode_scenes_non_png_response_is_recorded_as_failed(tmp_path):
    """A response that returns 200 but isn't actually a PNG (e.g. a JSON
    error body Cloudflare returned with a 200 status by mistake) must be
    caught by the magic-byte check and recorded as a failure, not written
    to disk as a corrupt image."""
    plan = [make_entry(1, seed=1)]
    plan_path = tmp_path / "prompt_plan.json"
    plan_path.write_text(json.dumps(plan))

    class Session:
        def post(self, url, json=None, headers=None, timeout=None):
            return FakeResponse(200, content=b'{"not": "a png"}')

    succeeded, failed = co.generate_episode_scenes(
        "ep-1", plan_path, tmp_path / "out", [1],
        api_token="token123", account_id="acct123", session=Session(), sleep_fn=lambda s: None,
    )
    assert succeeded == []
    assert failed == [1]
    error_text = (tmp_path / "out" / "_cloudflare_debug" / "scene_0001.error.txt").read_text()
    assert "CloudflareError" in error_text


def test_generate_episode_scenes_unexpected_exception_is_recorded_not_raised(tmp_path):
    """A non-CloudflareError exception (a malformed response, a network
    error, etc.) for one beat must not abort the whole batch or the other
    beats' results -- it must be recorded against just that beat."""
    plan = [make_entry(1, seed=1), make_entry(2, seed=2)]
    plan_path = tmp_path / "prompt_plan.json"
    plan_path.write_text(json.dumps(plan))

    class BrokenForOneBeatSession:
        def post(self, url, json=None, headers=None, timeout=None):
            if json["seed"] == 2:
                raise ConnectionError("simulated network failure")
            return FakeResponse(200, content=_TINY_PNG)

    succeeded, failed = co.generate_episode_scenes(
        "ep-1", plan_path, tmp_path / "out", [1, 2],
        api_token="token123", account_id="acct123", session=BrokenForOneBeatSession(), sleep_fn=lambda s: None,
    )
    assert succeeded == [1]
    assert failed == [2]
    error_text = (tmp_path / "out" / "_cloudflare_debug" / "scene_0002.error.txt").read_text()
    assert "ConnectionError" in error_text
