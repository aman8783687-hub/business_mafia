#!/usr/bin/env python3
"""Generate the art for an episode's thumbnail: one FLUX image, composed
for the thumbnail rather than reused from a beat. The boss stands on the
right, big and curious (hand on chin), at the business, with gold money in
front; the left half stays empty white for make_thumbnail.py's title bands.

Reads metadata.json's `thumbnail_scene` (what is at the business: props,
money, setting) and writes 08_publish/thumbnail_scene.png. Skips the call
when that file already exists; --force regenerates, --seed picks a new roll.

Usage (from MafiaOfBusiness/):
    python3 scripts/generate_thumbnail_scene.py <slug> [--seed N] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
WORKSPACE = SCRIPTS.parent

import env_loader  # noqa: E402
from scenes import flux_orchestrator  # noqa: E402
from scenes.prompt_builder import build_prompt, derive_seed, WIDTH, HEIGHT  # noqa: E402

COMPOSITION = (
    "youtube thumbnail composition: the LEFT half of the image is completely empty white, "
    "everything is drawn in the RIGHT half; the boss stickman is large, on the right, "
    "one hand on his chin, looking curious and impressed, "
)


def build_thumbnail_prompt(description: str) -> str:
    return build_prompt(COMPOSITION + description)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    publish = WORKSPACE / "episodes" / args.slug / "08_publish"
    out = publish / "thumbnail_scene.png"
    if out.exists() and not args.force:
        print(f"{out} exists; skipping (use --force to regenerate)")
        return 0
    description = json.loads((publish / "metadata.json").read_text()).get("thumbnail_scene")
    if not description:
        print("metadata.json has no thumbnail_scene", file=sys.stderr)
        return 1
    entry = {
        "prompt": build_thumbnail_prompt(description),
        "seed": args.seed if args.seed is not None else derive_seed(args.slug, 0, attempt=77),
        "width": WIDTH,
        "height": HEIGHT,
    }
    png = flux_orchestrator.generate_image(
        entry,
        flux_orchestrator.REFERENCE_IMAGE.read_bytes(),
        env_loader.get("CLOUDFLARE_ACCOUNT_ID"),
        env_loader.get("CLOUDFLARE_API_TOKEN"),
        flux_orchestrator._model(),
    )
    out.write_bytes(png)
    print(f"Saved {out} (seed {entry['seed']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
