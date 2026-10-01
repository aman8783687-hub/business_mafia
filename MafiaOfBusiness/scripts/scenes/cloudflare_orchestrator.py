"""Drives Cloudflare Workers AI to generate one episode's scene images in
parallel. Every job carries the identical model, negative prompt, and
sampling parameters (see channel_state.json's style_lock) -- consistency
comes from the shared request body and a single hosted checkpoint, not
from a LoRA. Cloudflare Workers AI's hosted image models do not support
loading a custom community LoRA the way AI Horde did (confirmed
empirically before this replaced AI Horde as the image backend -- see
reports/changelog.md for the validation notes and the resulting style
change this caused: the specific storybook-oil-pastel look is gone,
replaced by a still-cohesive flat-painterly look carried by the prompt
suffix alone).

Unlike AI Horde (a community volunteer pool needing submit/poll/download
as three separate steps against a job queue), Cloudflare's API is
synchronous: one POST returns the finished image directly. This makes
the submit-pacer/poll-loop machinery AI Horde needed unnecessary -- a
plain thread pool with per-request retry-on-429/5xx is enough.

All HTTP calls go through the injectable `session` (defaults to the
`requests` module) so this is fully testable without hitting the real
API -- see tests/test_cloudflare_orchestrator.py.
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import env_loader  # noqa: E402
from state import load_state  # noqa: E402

API_BASE = "https://api.cloudflare.com/client/v4/accounts"
MODEL = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
RETRY_ATTEMPTS = 5

_STYLE = load_state()["style_lock"]
NEGATIVE_PROMPT = _STYLE["negative_prompt"]


class CloudflareError(RuntimeError):
    """Raised for a non-transient Cloudflare Workers AI request failure."""


def _headers(api_token: str) -> dict:
    return {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}


def generate_one(entry: dict, api_token: str, account_id: str, session=requests,
                  sleep_fn=time.sleep) -> bytes:
    """POSTs one beat's request and returns the raw PNG bytes. Retries a
    429 (rate limited) or 5xx (transient) response with backoff; any
    other non-200 status raises immediately."""
    body = {
        "prompt": entry["prompt"],
        "negative_prompt": NEGATIVE_PROMPT,
        "width": entry["width"],
        "height": entry["height"],
        "num_steps": entry["num_inference_steps"],
        "guidance": entry["guidance_scale"],
        "seed": entry["seed"],
    }
    url = f"{API_BASE}/{account_id}/ai/run/{MODEL}"
    last_error = None
    for attempt in range(RETRY_ATTEMPTS):
        r = session.post(url, json=body, headers=_headers(api_token), timeout=60)
        if r.status_code == 429:
            wait = float(r.headers.get("retry-after", 2)) + attempt
            sleep_fn(wait)
            continue
        if r.status_code >= 500:
            last_error = f"{r.status_code} {r.text[:200]}"
            sleep_fn(1 + attempt)
            continue
        if r.status_code != 200:
            raise CloudflareError(f"beat {entry['beat']} failed: {r.status_code} {r.text[:300]}")
        return r.content
    raise CloudflareError(f"beat {entry['beat']} failed after {RETRY_ATTEMPTS} retries: {last_error}")


def generate_episode_scenes(
    slug: str,
    prompt_plan_path: Path,
    out_dir: Path,
    beat_numbers: list[int],
    api_token: str | None = None,
    account_id: str | None = None,
    session=requests,
    sleep_fn=time.sleep,
    max_workers: int = 8,
) -> tuple[list[int], list[int]]:
    api_token = api_token or env_loader.get("CLOUDFLARE_API_TOKEN")
    account_id = account_id or env_loader.get("CLOUDFLARE_ACCOUNT_ID")
    plan = json.loads(Path(prompt_plan_path).read_text())
    plan_by_beat = {e["beat"]: e for e in plan}

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    debug_dir = out_dir / "_cloudflare_debug"
    debug_dir.mkdir(exist_ok=True)

    selected = [plan_by_beat[b] for b in beat_numbers if b in plan_by_beat]
    missing = [b for b in beat_numbers if b not in plan_by_beat]

    succeeded: list[int] = []
    failed: list[int] = []
    for b in missing:
        (debug_dir / f"scene_{b:04d}.error.txt").write_text(f"beat {b} not found in prompt plan")
        failed.append(b)

    def _one(entry: dict) -> tuple[int, bool]:
        beat = entry["beat"]
        try:
            png_bytes = generate_one(entry, api_token, account_id, session=session, sleep_fn=sleep_fn)
            if not png_bytes.startswith(b"\x89PNG"):
                raise CloudflareError(f"beat {beat}: response was not a PNG ({len(png_bytes)} bytes)")
            out_path = out_dir / f"scene_{beat:04d}.png"
            out_path.write_bytes(png_bytes)
            (debug_dir / f"scene_{beat:04d}.json").write_text(
                json.dumps({"model": MODEL, "seed": entry["seed"], "bytes": len(png_bytes)})
            )
            return beat, out_path.exists() and out_path.stat().st_size > 0
        except Exception as e:
            # Broad on purpose: a network error (requests.RequestException),
            # a malformed retry-after header (ValueError), our own
            # CloudflareError, or any other unexpected failure must all be
            # recorded against this beat and never abort the other beats'
            # futures.
            (debug_dir / f"scene_{beat:04d}.error.txt").write_text(f"{type(e).__name__}: {e}")
            return beat, False

    if selected:
        with ThreadPoolExecutor(max_workers=max(1, min(max_workers, len(selected)))) as ex:
            for beat, ok in ex.map(_one, selected):
                (succeeded if ok else failed).append(beat)
    return sorted(succeeded), sorted(failed)
