"""Builds image prompts and prompt_plan.json entries for generate_scenes.py.
Consistency comes from every beat sharing the identical style text (see
channel_state.json's style_lock) and, on the default flux backend, from the
host reference image that scenes/flux_orchestrator.py sends with each
request. negative_prompt/cfg/steps are carried in the plan only for the
cloudflare-SDXL fallback backend; FLUX.2 klein ignores them."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from state import load_state  # noqa: E402

_STATE = load_state()["style_lock"]

STYLE_SUFFIX = _STATE["image_prompt_suffix"]
NEGATIVE_PROMPT = _STATE["negative_prompt"]

# Generation resolution, independent of channel_state.json's final-render
# resolution (1920x1080) -- assemble_episode.py's ffmpeg scale step
# handles the upscale. Matches the size validated in the brainstorm spike.
WIDTH, HEIGHT = 1024, 576
CFG_SCALE = _STATE["cfg_scale"]
STEPS = _STATE["steps"]


def build_prompt(description: str) -> str:
    # Style first: FLUX.2 klein weights the start of the prompt most, and the
    # whiteboard look (red/black/white only) is what must never drift.
    return f"{STYLE_SUFFIX}, {description}"


def derive_seed(slug: str, beat: int, attempt: int = 0) -> int:
    """Deterministic default seed for a beat: stable across reruns of the
    same episode/beat/attempt, distinct across beats/episodes/attempts."""
    digest = hashlib.sha256(f"{slug}:{beat}:{attempt}".encode()).hexdigest()
    return int(digest[:8], 16)


def build_prompt_plan(
    slug: str,
    beats: list[dict],
    shot_index: dict[int, dict],
    seed_overrides: dict[int, int] | None = None,
    attempt: int = 0,
) -> list[dict]:
    seed_overrides = seed_overrides or {}
    plan = []
    for b in beats:
        beat_num = b["beat"]
        shot = shot_index.get(beat_num, {})
        if (shot.get("type") or "").lower() == "real_photo":
            continue
        description = shot.get("description", b.get("text", ""))
        seed = seed_overrides.get(beat_num, derive_seed(slug, beat_num, attempt))
        plan.append({
            "beat": beat_num,
            "prompt": build_prompt(description),
            "seed": seed,
            "width": WIDTH,
            "height": HEIGHT,
            "guidance_scale": CFG_SCALE,
            "num_inference_steps": STEPS,
        })
    return plan
