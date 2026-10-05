# Visuals and animation

## Building the shotlist

From `03_audio/timings.json`, one scene per beat, roughly every 7-10 seconds of narration: a 10-minute episode is typically 65-85 scenes (about 70-90 minutes on perchance). Vary the shots so a long video never looks repetitive: wide (the boss at the business), close (one prop, a hand counting coins), the example owner alone, a before/after pair.

Each entry is `{"scene": N, "description": "...", "motion": "slow push in"}`. Write a description as one simple drawing: the boss doing one thing, plus one or two marker props (a fuel nozzle, a dal pot, a dumper, a poultry shed, a gym bench, a shelf of packets). Money props (coins, notes, a ₹ bag) are drawn in gold. Never ask for text, numbers, labels, arrows or diagrams inside the image (FLUX cannot draw Devanagari); captions carry the words. `type: "real_photo"` marks a beat to fill by hand; `generate_scenes.py` skips it (rare).

**Two characters per shot at most.** FLUX.2 klein collapses a third distinct character to one rendered subject. Write crowded moments as shot and reverse-shot pairs. The example owner (रमेश) is a plain stickman with one identifying prop; the boss is the hat-and-suit host.

**The thumbnail has its own art.** `generate_thumbnail_scene.py` draws it from `metadata.json` `thumbnail_scene`, already composed for the thumbnail (boss large on the right, curious, left half empty). Beat 1 is an ordinary hook shot; it is only the fallback art if that generation fails (`thumbnail_beat` picks a different fallback beat).

## Generating scenes

`python3 scripts/generate_scenes.py <slug>` builds a prompt per beat (`scripts/scenes/prompt_builder.py`: style suffix, then the beat description) and calls the backend named by `IMAGE_BACKEND`:

- **`perchance` (default).** perchance.org's free text-to-image generator, driven in a headless Firefox by `scripts/scenes/perchance_orchestrator.py` (style "No style", Landscape, padded to 16:9, near-white snapped to white). Free, no login, no daily quota, about one image a minute, one beat at a time; a timed-out beat reloads the page and retries once, and three failed beats in a row stop the batch. There is no reference image and no seed: the boss stays on-model only through the style text, and every prompt starts with a no-mouth guard because a smiling mouth is its most common defect. A rerun of a beat is a new random image. Tested 2026-10-04: on-model boss, black/white/gold, clean whiteboard.
- **`flux`.** FLUX.2 [klein] 9B on Cloudflare Workers AI with the host reference image. Best character consistency, but at current pricing (~1,400 neurons an image) the free 10,000 neurons/day cover only ~6 images, so it is used for the thumbnail scene and the odd stubborn reroll (`IMAGE_BACKEND=flux python3 scripts/generate_scenes.py <slug> --beats N`), not whole episodes.
- **`cloudflare`** (SDXL) is a text-prompt-only fallback on the same quota.

Generation size is 1024x576; assembly upscales to 1920x1080. Options: `--beats 1,3,5-7`, `--seed N` (one beat), `--attempt N`, `--dry-run`.

**Review every generated PNG before assembling.** Reroll anything off-model: red or extra colours, a mouth on the host, shading, text in the image, a wrong number of characters. `generate_scenes.py --beats N` (perchance draws a fresh image; on flux add `--seed <new>`). If a beat stays off-model after three rerolls, simplify its description (one prop, the boss alone).

## Animation

Every scene gets a Ken Burns push in/out via ffmpeg zoompan, ~5% zoom ramped over the scene. No flat static hold, and no AI motion (it melts stick figures).

## On-screen text

No baked-in image text. Captions carry the words (`captions.md`).
