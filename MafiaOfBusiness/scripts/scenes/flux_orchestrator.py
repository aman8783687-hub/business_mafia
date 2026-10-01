"""Generates one episode's scene images with FLUX.2 [klein] on Cloudflare
Workers AI, conditioned on RedHat Engineer's host reference image so the
red-fedora stickman stays the same character from beat to beat. This is
the default image backend (IMAGE_BACKEND=flux).

One REST call per beat: POST /accounts/{id}/ai/run/@cf/black-forest-labs/<model>
with multipart fields prompt, width, height, seed and input_image_0 (the
reference). The reply is JSON with a base64 image at result.image. The
endpoint has no negative_prompt, guidance or steps parameters -- the look
comes from the style suffix plus the reference image.

Why this backend and not raphael/cloudflare-SDXL: the stickman host only
stays on-model when a reference image is sent with every request, and
neither of those can do that.

Free tier is 10,000 neurons/day, so a long episode can need a second day
of reruns; generate_scenes.py skips finished beats. A fatal error (bad
credentials, quota spent) stops the batch and every unfinished beat counts
as failed, so the run can simply be repeated later.

The HTTP call is injectable (`post`) so this is testable without the API
-- see tests/test_flux_orchestrator.py.
"""
from __future__ import annotations

import base64
import io
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import env_loader  # noqa: E402

API_BASE = "https://api.cloudflare.com/client/v4/accounts"
MODEL_PREFIX = "@cf/black-forest-labs/"
# 9B follows the whiteboard style lock (red/black/white only) noticeably
# better than 4B. Override with CLOUDFLARE_IMAGE_MODEL.
DEFAULT_MODEL = "flux-2-klein-9b"

REFERENCE_IMAGE = Path(__file__).resolve().parent.parent.parent / "brand" / "host" / "host-reference-clean.jpeg"
# Prepended to every prompt at request time (kept out of prompt_plan.json).
REFERENCE_INSTRUCTION = (
    "The stickman host is the exact same character as in the reference image "
    "(same red fedora, two dot eyes, no mouth, plain stick body). "
)

WORKERS = 3
MAX_ATTEMPTS = 6
REQUEST_TIMEOUT_SECONDS = 240
BACKOFF_BASE_SECONDS = 5
BACKOFF_MAX_SECONDS = 60

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_QUOTA_MARKERS = ("daily free allocation", "neurons")


class FluxError(RuntimeError):
    """A beat could not be generated (retries exhausted or a non-retryable API error)."""


class FluxFatalError(FluxError):
    """Every further beat would fail too (bad credentials or the daily quota is spent)."""


def _model() -> str:
    return env_loader.get("CLOUDFLARE_IMAGE_MODEL", "") or DEFAULT_MODEL


def _error_text(response) -> str:
    try:
        errors = response.json().get("errors") or []
        return "; ".join(str(e.get("message", e)) for e in errors) or response.text[:200]
    except ValueError:
        return response.text[:200]


def generate_image(entry: dict, reference_bytes: bytes, account_id: str, token: str, model: str,
                   post=requests.post, sleep_fn=time.sleep) -> bytes:
    """Return PNG bytes for one prompt-plan entry, retrying transient failures with backoff."""
    url = f"{API_BASE}/{account_id}/ai/run/{MODEL_PREFIX}{model}"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "prompt": REFERENCE_INSTRUCTION + entry["prompt"],
        "width": str(entry["width"]),
        "height": str(entry["height"]),
        "seed": str(entry["seed"]),
    }
    last = "no attempt made"
    for attempt in range(MAX_ATTEMPTS):
        try:
            response = post(url, headers=headers, data=data, timeout=REQUEST_TIMEOUT_SECONDS,
                            files={"input_image_0": ("reference.jpg", reference_bytes, "image/jpeg")})
        except (requests.ConnectionError, requests.Timeout) as err:
            last = f"network error: {err}"
        else:
            if response.status_code == 200:
                body = response.json()
                image_b64 = (body.get("result") or {}).get("image")
                if body.get("success") and image_b64:
                    out = io.BytesIO()
                    Image.open(io.BytesIO(base64.b64decode(image_b64))).convert("RGB").save(out, "PNG")
                    return out.getvalue()
                raise FluxError(f"200 without an image: {_error_text(response)}")
            last = f"HTTP {response.status_code}: {_error_text(response)}"
            if response.status_code in (401, 403):
                raise FluxFatalError(f"Cloudflare rejected the credentials ({last})")
            if any(marker in last.lower() for marker in _QUOTA_MARKERS):
                raise FluxFatalError(f"Cloudflare free daily quota is used up ({last})")
            if response.status_code not in _RETRYABLE_STATUS:
                raise FluxError(last)
        if attempt < MAX_ATTEMPTS - 1:
            sleep_fn(min(BACKOFF_BASE_SECONDS * 2 ** attempt, BACKOFF_MAX_SECONDS))
    raise FluxError(f"gave up after {MAX_ATTEMPTS} attempts ({last})")


def generate_episode_scenes(
    slug: str,
    prompt_plan_path: Path,
    out_dir: Path,
    beat_numbers: list[int],
    post=requests.post,
    sleep_fn=time.sleep,
    reference_path: Path = REFERENCE_IMAGE,
    workers: int = WORKERS,
    account_id: str | None = None,
    token: str | None = None,
) -> tuple[list[int], list[int]]:
    """Generate every beat in beat_numbers into out_dir/scene_XXXX.png.
    Returns (succeeded_beats, failed_beats); failures are also recorded in
    out_dir/_flux_debug/scene_XXXX.error.txt."""
    account_id = account_id or env_loader.get("CLOUDFLARE_ACCOUNT_ID")
    token = token or env_loader.get("CLOUDFLARE_API_TOKEN")
    plan_by_beat = {e["beat"]: e for e in json.loads(Path(prompt_plan_path).read_text())}
    selected = [plan_by_beat[b] for b in beat_numbers if b in plan_by_beat]
    model = _model()
    reference_bytes = Path(reference_path).read_bytes()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = out_dir / "_flux_debug"
    debug_dir.mkdir(exist_ok=True)

    stop = threading.Event()
    succeeded: list[int] = []
    failed: list[int] = []
    lock = threading.Lock()

    for b in beat_numbers:
        if b not in plan_by_beat:
            (debug_dir / f"scene_{b:04d}.error.txt").write_text(f"beat {b} not found in prompt plan")
            failed.append(b)

    def record_failure(beat: int, message: str) -> None:
        (debug_dir / f"scene_{beat:04d}.error.txt").write_text(message)
        with lock:
            failed.append(beat)

    def work(entry: dict) -> None:
        beat = entry["beat"]
        if stop.is_set():
            record_failure(beat, "skipped: an earlier beat hit a fatal error (credentials or daily quota)")
            return
        try:
            png = generate_image(entry, reference_bytes, account_id, token, model, post=post, sleep_fn=sleep_fn)
            (out_dir / f"scene_{beat:04d}.png").write_bytes(png)
            (debug_dir / f"scene_{beat:04d}.json").write_text(
                json.dumps({"model": model, "seed": entry["seed"], "bytes": len(png)}))
            print(f"[scene_{beat:04d}] OK", flush=True)
            with lock:
                succeeded.append(beat)
        except FluxFatalError as err:
            print(f"[scene_{beat:04d}] FAILED (stopping the batch) - {err}", file=sys.stderr, flush=True)
            stop.set()
            record_failure(beat, f"{type(err).__name__}: {err}")
        except Exception as err:  # noqa: BLE001 - log against this beat and carry on
            print(f"[scene_{beat:04d}] FAILED - {err}", file=sys.stderr, flush=True)
            record_failure(beat, f"{type(err).__name__}: {err}")

    print(f"Cloudflare Workers AI: {len(selected)} scene(s) with {model}", flush=True)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(work, selected))
    return sorted(succeeded), sorted(set(failed))
