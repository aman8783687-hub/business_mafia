#!/usr/bin/env python3
"""Generate scene images for an episode. The image backend is picked by
the IMAGE_BACKEND setting: "perchance" (default: perchance.org's free
generator driven in headless Firefox, no daily quota, about one image a
minute, scenes/perchance_orchestrator.py), "flux" (FLUX.2 klein on
Cloudflare, conditioned on the host reference image, but the free 10,000
neurons/day cover only a handful of images, scenes/flux_orchestrator.py),
or "cloudflare" (SDXL, scenes/cloudflare_orchestrator.py, same quota).
perchance and cloudflare are text-prompt only: look at every scene.

For every beat in 03_audio/timings.json (skipping "real_photo" beats,
which stay hand-placed in 05_scenes/):
  1. Builds a prompt from 05_scenes/shotlist.json's description
     (scenes/prompt_builder.py).
  2. Writes/updates episodes/<slug>/05_scenes/prompt_plan.json.
  3. Drives the image backend to generate and download
     episodes/<slug>/05_scenes/scene_XXXX.png per beat, in
     parallel via a thread pool.

Usage (from MafiaOfBusiness/):
    python3 scripts/generate_scenes.py <episode-slug>

Options:
    --beats 1,3,5-7   Only (re)generate specific beat numbers. Use this
                       to reroll a beat that came out badly -- pair with
                       --seed.
    --seed N           Force this seed for the single beat selected by
                       --beats (requires exactly one beat). Both
                       flux and cloudflare honour seeds; perchance has
                       none, so any rerun of a beat is a new image.
    --dry-run          Write/update prompt_plan.json and print the plan,
                       but never call the image backend.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

WORKSPACE = SCRIPTS_DIR.parent

import env_loader
from scenes.prompt_builder import build_prompt_plan

DEFAULT_IMAGE_BACKEND = "perchance"


def generate_episode_scenes(slug, plan_path, out_dir, beat_numbers):
    """Dispatches to the configured image backend. Backends are imported
    lazily so a run never needs the other backend's credentials."""
    # An unset GitHub Actions variable arrives as an empty string.
    backend = (env_loader.get("IMAGE_BACKEND", "") or DEFAULT_IMAGE_BACKEND).lower()
    if backend == "perchance":
        from scenes import perchance_orchestrator as orchestrator
    elif backend == "flux":
        from scenes import flux_orchestrator as orchestrator
    elif backend == "cloudflare":
        from scenes import cloudflare_orchestrator as orchestrator
    else:
        raise SystemExit(f"Unknown IMAGE_BACKEND {backend!r} (use 'perchance', 'flux' or 'cloudflare')")
    print(f"Image backend: {backend}")
    return orchestrator.generate_episode_scenes(slug, plan_path, out_dir, beat_numbers)


def parse_beats_arg(arg: Optional[str]) -> Optional[set[int]]:
    """Parse '1,3,5-7' -> {1, 3, 5, 6, 7}. None means all beats."""
    if not arg:
        return None
    result: set[int] = set()
    for part in arg.split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            result.update(range(int(lo), int(hi) + 1))
        else:
            result.add(int(part))
    return result


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug", help="Episode folder name")
    ap.add_argument("--beats", help="Comma-separated beat numbers / ranges to (re)generate")
    ap.add_argument("--seed", type=int, help="Force this seed; requires exactly one beat via --beats")
    ap.add_argument("--attempt", type=int, default=0, help="Reroll all beats in this run with a new deterministic seed set")
    ap.add_argument("--dry-run", action="store_true", help="Write the prompt plan but never call the image backend")
    args = ap.parse_args(argv)

    beats_filter = parse_beats_arg(args.beats)
    if args.seed is not None and (not beats_filter or len(beats_filter) != 1):
        print("--seed requires exactly one beat selected via --beats", file=sys.stderr)
        return 1

    episode_dir = WORKSPACE / "episodes" / args.slug
    timings_path = episode_dir / "03_audio" / "timings.json"
    shotlist_path = episode_dir / "05_scenes" / "shotlist.json"
    plan_path = episode_dir / "05_scenes" / "prompt_plan.json"

    if not timings_path.exists():
        print(f"{timings_path} not found. Run stitch_audio.py first.", file=sys.stderr)
        return 1

    # shotlist.json is authored alongside script.md in 02_script/, then
    # copied forward to 05_scenes/ (run_episode.py does this copy as part
    # of its own pipeline run). When this script is run standalone --
    # e.g. as the documented manual review step, before run_episode.py --
    # 05_scenes/shotlist.json won't exist yet even though the real
    # authored copy in 02_script/ does. Do the same one-line copy here
    # instead of erroring, so the standalone workflow doesn't require
    # hand-authoring a second copy that run_episode.py would later
    # silently overwrite anyway.
    if not shotlist_path.exists():
        script_shotlist_path = episode_dir / "02_script" / "shotlist.json"
        if script_shotlist_path.exists():
            shotlist_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(script_shotlist_path, shotlist_path)
            print(f"Copied {script_shotlist_path} -> {shotlist_path}")
        else:
            print(
                f"Neither {shotlist_path} nor {script_shotlist_path} found. "
                "Write 02_script/shotlist.json first.",
                file=sys.stderr,
            )
            return 1

    timings = json.loads(timings_path.read_text())
    shotlist = json.loads(shotlist_path.read_text())
    shot_index = {entry["scene"]: entry for entry in shotlist}

    beats = timings["beats"]
    if beats_filter:
        beats = [b for b in beats if b["beat"] in beats_filter]
    else:
        scenes_dir = episode_dir / "05_scenes"
        beats = [
            b for b in beats
            if not ((scenes_dir / f"scene_{b['beat']:04d}.png").exists()
                    and (scenes_dir / f"scene_{b['beat']:04d}.png").stat().st_size > 0)
        ]

    seed_overrides = {}
    if args.seed is not None:
        (target_beat,) = beats_filter
        seed_overrides[target_beat] = args.seed

    new_entries = build_prompt_plan(args.slug, beats, shot_index, seed_overrides, attempt=args.attempt)

    existing_by_beat: dict[int, dict] = {}
    if plan_path.exists():
        existing_by_beat = {e["beat"]: e for e in json.loads(plan_path.read_text())}
    for entry in new_entries:
        existing_by_beat[entry["beat"]] = entry
    full_plan = [existing_by_beat[k] for k in sorted(existing_by_beat)]
    plan_path.write_text(json.dumps(full_plan, indent=2))

    print(f"Episode : {args.slug}")
    print(f"Beats   : {len(new_entries)} to generate"
          + (f" (filtering to {sorted(beats_filter)})" if beats_filter else "")
          + f", {len(full_plan) - len(new_entries)} unchanged in prompt_plan.json")
    for e in new_entries:
        print(f"  beat {e['beat']:04d}  seed={e['seed']}  {e['prompt'][:70]}...")

    if args.dry_run:
        print("\nDry run: no image backend calls made.")
        return 0

    if not new_entries:
        print("\nNothing to generate (all beats are real_photo or selection is empty).")
        return 0

    beat_numbers = [e["beat"] for e in new_entries]
    succeeded, failed = generate_episode_scenes(args.slug, plan_path, episode_dir / "05_scenes", beat_numbers)
    print(f"\n{len(succeeded)}/{len(beat_numbers)} scene(s) generated to {episode_dir / '05_scenes'}")
    if failed:
        print(f"FAILED beats: {sorted(failed)} -- retry with --beats N --seed <new>", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
