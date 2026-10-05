"""Generates one episode's scene images on perchance.org's free text-to-image
generator (IMAGE_BACKEND=perchance, the default). Free, no login, no daily
quota, about one image a minute.

Perchance has no API a script can call: direct requests get a Cloudflare 403,
and the results live in cross-origin iframes. So this drives the real page
in a headless Firefox (Playwright), following the operator's playbook
(~/Desktop/amazon kdp/PERCHANCE_PLAYBOOK.md):

- a real Firefox User-Agent and navigator.webdriver masked, or clicking
  Generate silently does nothing;
- the generator frame is the one whose URL contains ".perchance.org/ai-text-to-image"
  (leading dot), not the top page and not image-generation.perchance.org;
- dropdowns are set by matching option text (the layout changes per load),
  through selectedIndex + input/change events;
- before each click, snapshot the gallery's image srcs; the new image is the
  first data:image <img> wider than 200 px that was not there before, read
  from the nested image-generation.perchance.org/embed frames.

Each image is fitted to 16:9 (padded at the sides with its whiteboard
colour) and resized to 1024x576 PNG, the size the flux backend produces,
so assembly is unchanged.

There is no reference image and no seed: the boss stays on-model only
through the style text in every prompt, so look at every scene and reroll
off-model beats with generate_scenes.py --beats N (a reroll is simply a new
random image).

The browser is injectable (`session_factory`) so this is testable without
the site -- see tests/test_perchance_orchestrator.py.
"""
from __future__ import annotations

import asyncio
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import env_loader  # noqa: E402

# Prepended to every prompt: without a reference image the boss often gets a
# smiling mouth, the most common off-model defect in the first test.
PROMPT_PREFIX = "The stickman's face is only two black dots for eyes, no mouth, no smile. "
GENERATOR_URL = "https://perchance.org/ai-text-to-image-generator"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
DEFAULT_STYLE = "No style"   # the option is shown in bold Unicode; matched after NFKC
SHAPE = "Landscape"
COUNT = "2"                  # the smallest batch the page offers; the first new image is kept
OUT_W, OUT_H = 1024, 576
IMAGE_TIMEOUT_SECONDS = 300
POLL_SECONDS = 2
ATTEMPTS_PER_BEAT = 2        # a timed-out beat reloads the page and tries once more
MAX_CONSECUTIVE_FAILURES = 3  # the site is down or has changed: stop the batch

CONTROLS_JS = """(want) => {
  const norm = (t) => t.normalize('NFKC').trim();
  const sels = Array.from(document.querySelectorAll('select'));
  const pick = (s, needle) => {
    if (!s) return 'NOSEL';
    const opts = Array.from(s.options);
    const o = opts.find(x => norm(x.text) === needle) || opts.find(x => norm(x.text).indexOf(needle) >= 0);
    if (!o) return 'MISS:' + needle;
    s.selectedIndex = opts.indexOf(o);
    s.dispatchEvent(new Event('input', {bubbles: true}));
    s.dispatchEvent(new Event('change', {bubbles: true}));
    return 'OK:' + norm(o.text);
  };
  const has = (s, f) => Array.from(s.options).some(o => f(norm(o.text)));
  const styleSel = sels.find(s => has(s, t => t === 'Painted Anime'));
  const shapeSel = sels.find(s => has(s, t => t === 'Landscape'));
  const countSel = sels.find(s => { const t = Array.from(s.options).map(o => norm(o.text)); return t.includes('2') && t.length <= 8; });
  return [pick(styleSel, want.style), pick(shapeSel, want.shape), pick(countSel, want.count)];
}"""

PROMPT_JS = """(p) => {
  const tas = Array.from(document.querySelectorAll('textarea.paragraph-input'));
  const t = tas.find(x => (x.placeholder || '').indexOf('store prompts') < 0) || tas[tas.length - 1];
  t.focus(); t.value = p;
  t.dispatchEvent(new Event('input', {bubbles: true}));
  t.dispatchEvent(new Event('change', {bubbles: true}));
}"""

GALLERY_JS = "() => Array.from(document.querySelectorAll('img')).map(i => ({src: i.src, w: i.naturalWidth}))"


class PerchanceError(RuntimeError):
    """The page could not be loaded or driven (site down, Cloudflare challenge, UI changed)."""


def _style() -> str:
    return env_loader.get("PERCHANCE_STYLE", "") or DEFAULT_STYLE


WHITE_FLOOR = 215  # channel values above this are paper, snapped to pure white


def to_scene_png(raw: bytes) -> bytes:
    """Fit to 16:9 and resize to the scene size; returns PNG bytes.
    Perchance's Landscape is 3:2: cropping it to 16:9 cut the boss's fedora,
    so a too-tall image is padded at the sides with white. Its paper is
    off-white, so near-white is snapped to white first, which hides the
    seam and matches the flux scenes' clean whiteboard."""
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img = img.point(lambda v: 255 if v > WHITE_FLOOR else v)
    w, h = img.size
    if w * 9 < h * 16:    # too tall: widen with whiteboard
        tw = h * 16 // 9
        canvas = Image.new("RGB", (tw, h), (255, 255, 255))
        canvas.paste(img, ((tw - w) // 2, 0))
        img = canvas
    elif w * 9 > h * 16:  # too wide: trim the sides
        tw = h * 16 // 9
        left = (w - tw) // 2
        img = img.crop((left, 0, left + tw, h))
    out = io.BytesIO()
    img.resize((OUT_W, OUT_H), Image.LANCZOS).save(out, "PNG")
    return out.getvalue()


def decode_data_url(src: str) -> bytes:
    return base64.b64decode(src.split(",", 1)[1])


class BrowserSession:
    """One headless Firefox on the Perchance generator page."""

    def __init__(self, style: str):
        self.style = style
        self._pw = self._browser = self.page = self.gen = None

    async def __aenter__(self):
        from playwright.async_api import async_playwright
        self._pw = await async_playwright().start()
        self._browser = await self._pw.firefox.launch(headless=True)
        await self.open_page()
        return self

    async def __aexit__(self, *exc):
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def open_page(self):
        if self.page:
            await self.page.context.close()
        ctx = await self._browser.new_context(viewport={"width": 1400, "height": 900}, user_agent=USER_AGENT)
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        self.page = await ctx.new_page()
        await self.page.goto(GENERATOR_URL, timeout=60000)
        self.gen = None
        for _ in range(15):
            await self.page.wait_for_timeout(2000)
            frames = [f for f in self.page.frames
                      if ".perchance.org/ai-text-to-image" in f.url and "image-generation" not in f.url]
            if frames:
                self.gen = frames[0]
                break
        if not self.gen:
            raise PerchanceError("generator frame never appeared (Cloudflare challenge or the page changed)")
        await self.page.wait_for_timeout(3000)
        result = await self.gen.evaluate(CONTROLS_JS, {"style": self.style, "shape": SHAPE, "count": COUNT})
        print(f"Perchance controls: {result}", flush=True)
        if any(not r.startswith("OK:") for r in result):
            raise PerchanceError(f"could not set the generator controls: {result}")

    async def _gallery(self) -> list[dict]:
        images = []
        for frame in self.page.frames:
            if "image-generation.perchance.org/embed" not in frame.url:
                continue
            try:
                images += await frame.evaluate(GALLERY_JS)
            except Exception:  # noqa: BLE001 - a frame mid-reload; the next poll sees it
                continue
        return images

    async def generate(self, prompt: str, timeout: float = IMAGE_TIMEOUT_SECONDS) -> bytes | None:
        """Raw image bytes for one prompt, or None on timeout."""
        await self.gen.evaluate(PROMPT_JS, prompt)
        baseline = {i["src"] for i in await self._gallery()}
        button = await self.gen.query_selector('button:has-text("generate")')
        if not button:
            raise PerchanceError("no generate button on the page")
        await button.click()
        for _ in range(int(timeout / POLL_SECONDS)):
            await self.page.wait_for_timeout(POLL_SECONDS * 1000)
            for image in await self._gallery():
                if image["src"].startswith("data:image") and image["w"] > 200 and image["src"] not in baseline:
                    return decode_data_url(image["src"])
        return None


async def _run(selected: list[dict], out_dir: Path, debug_dir: Path, session_factory) -> tuple[list[int], list[int]]:
    succeeded: list[int] = []
    failed: list[int] = []

    def record_failure(beat: int, message: str) -> None:
        (debug_dir / f"scene_{beat:04d}.error.txt").write_text(message)
        failed.append(beat)

    consecutive = 0
    try:
        async with session_factory() as session:
            for n, entry in enumerate(selected):
                beat = entry["beat"]
                if consecutive >= MAX_CONSECUTIVE_FAILURES:
                    record_failure(beat, f"skipped: {MAX_CONSECUTIVE_FAILURES} beats in a row failed (site down or changed)")
                    continue
                raw = None
                for attempt in range(ATTEMPTS_PER_BEAT):
                    try:
                        raw = await session.generate(PROMPT_PREFIX + entry["prompt"])
                    except PerchanceError:
                        raise
                    except Exception as err:  # noqa: BLE001 - page crashed mid-beat; reload and retry
                        print(f"[scene_{beat:04d}] error: {err}", file=sys.stderr, flush=True)
                    if raw:
                        break
                    if attempt < ATTEMPTS_PER_BEAT - 1:
                        await session.open_page()
                if not raw:
                    consecutive += 1
                    print(f"[scene_{beat:04d}] FAILED - no image", file=sys.stderr, flush=True)
                    record_failure(beat, f"PerchanceError: no new image after {ATTEMPTS_PER_BEAT} attempts")
                    continue
                consecutive = 0
                png = to_scene_png(raw)
                (out_dir / f"scene_{beat:04d}.png").write_bytes(png)
                (debug_dir / f"scene_{beat:04d}.json").write_text(json.dumps(
                    {"backend": "perchance", "style": session.style, "prompt": entry["prompt"], "bytes": len(png)}))
                (debug_dir / f"scene_{beat:04d}.error.txt").unlink(missing_ok=True)
                succeeded.append(beat)
                print(f"[scene_{beat:04d}] OK ({n + 1}/{len(selected)})", flush=True)
    except PerchanceError as err:
        print(f"Perchance FAILED (stopping the batch) - {err}", file=sys.stderr, flush=True)
        for entry in selected:
            if entry["beat"] not in succeeded and entry["beat"] not in failed:
                record_failure(entry["beat"], f"PerchanceError: {err}")
    return sorted(succeeded), sorted(set(failed))


def generate_episode_scenes(
    slug: str,
    prompt_plan_path: Path,
    out_dir: Path,
    beat_numbers: list[int],
    session_factory=None,
) -> tuple[list[int], list[int]]:
    """Generate every beat in beat_numbers into out_dir/scene_XXXX.png, one at
    a time. Returns (succeeded_beats, failed_beats); failures are also
    recorded in out_dir/_flux_debug/scene_XXXX.error.txt (the same place as
    the flux backend, so the recovery steps are the same)."""
    plan_by_beat = {e["beat"]: e for e in json.loads(Path(prompt_plan_path).read_text())}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = out_dir / "_flux_debug"
    debug_dir.mkdir(exist_ok=True)

    missing = [b for b in beat_numbers if b not in plan_by_beat]
    for b in missing:
        (debug_dir / f"scene_{b:04d}.error.txt").write_text(f"beat {b} not found in prompt plan")
    selected = [plan_by_beat[b] for b in beat_numbers if b in plan_by_beat]
    style = _style()
    session_factory = session_factory or (lambda: BrowserSession(style))
    print(f"Perchance: {len(selected)} scene(s), style {style!r}, about a minute each", flush=True)
    succeeded, failed = asyncio.run(_run(selected, out_dir, debug_dir, session_factory))
    return succeeded, sorted(set(failed) | set(missing))
