import io
import json

from PIL import Image

from scenes import perchance_orchestrator as po


def _jpeg(w, h, colour=(240, 240, 238)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), colour).save(buf, "JPEG")
    return buf.getvalue()


def _plan(tmp_path, beats):
    path = tmp_path / "prompt_plan.json"
    path.write_text(json.dumps([{"beat": b, "prompt": f"beat {b} prompt", "seed": 1,
                                 "width": 1024, "height": 576} for b in beats]))
    return path


class FakeSession:
    """Stands in for BrowserSession: returns queued results per generate() call."""

    def __init__(self, results):
        self.results = list(results)
        self.prompts = []
        self.reloads = 0
        self.style = "No style"

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def open_page(self):
        self.reloads += 1

    async def generate(self, prompt):
        self.prompts.append(prompt)
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result


def test_landscape_is_padded_not_cropped_and_paper_goes_white():
    png = po.to_scene_png(_jpeg(768, 512))
    img = Image.open(io.BytesIO(png))
    assert img.size == (1024, 576)
    assert img.getpixel((5, 288)) == (255, 255, 255)      # pad
    assert img.getpixel((512, 288)) == (255, 255, 255)    # off-white paper snapped


def test_ink_survives_and_wide_images_are_trimmed():
    png = po.to_scene_png(_jpeg(2000, 576, colour=(20, 20, 20)))
    img = Image.open(io.BytesIO(png))
    assert img.size == (1024, 576)
    assert max(img.getpixel((512, 288))) < 60


def test_generates_each_beat_with_the_mouth_guard(tmp_path):
    session = FakeSession([_jpeg(768, 512), _jpeg(768, 512)])
    ok, failed = po.generate_episode_scenes("s", _plan(tmp_path, [1, 2]), tmp_path / "out", [1, 2],
                                            session_factory=lambda: session)
    assert (ok, failed) == ([1, 2], [])
    assert all(p.startswith(po.PROMPT_PREFIX) for p in session.prompts)
    assert Image.open(tmp_path / "out" / "scene_0002.png").size == (1024, 576)
    meta = json.loads((tmp_path / "out" / "_flux_debug" / "scene_0001.json").read_text())
    assert meta["backend"] == "perchance"


def test_timeout_reloads_and_retries_once(tmp_path):
    session = FakeSession([None, _jpeg(768, 512)])
    ok, failed = po.generate_episode_scenes("s", _plan(tmp_path, [1]), tmp_path / "out", [1],
                                            session_factory=lambda: session)
    assert (ok, failed) == ([1], [])
    assert session.reloads == 1


def test_stops_after_consecutive_failures(tmp_path):
    session = FakeSession([None] * 6)
    beats = [1, 2, 3, 4]
    ok, failed = po.generate_episode_scenes("s", _plan(tmp_path, beats), tmp_path / "out", beats,
                                            session_factory=lambda: session)
    assert (ok, failed) == ([], beats)
    assert len(session.prompts) == 6   # beat 4 is skipped without a request
    assert "skipped" in (tmp_path / "out" / "_flux_debug" / "scene_0004.error.txt").read_text()


def test_page_error_fails_the_rest_and_missing_beats_are_reported(tmp_path):
    session = FakeSession([_jpeg(768, 512), po.PerchanceError("generator frame never appeared")])
    ok, failed = po.generate_episode_scenes("s", _plan(tmp_path, [1, 2, 3]), tmp_path / "out", [1, 2, 3, 9],
                                            session_factory=lambda: session)
    assert ok == [1]
    assert failed == [2, 3, 9]
    assert "frame never appeared" in (tmp_path / "out" / "_flux_debug" / "scene_0003.error.txt").read_text()
