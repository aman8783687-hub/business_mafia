# Visuals and animation

## Building the shotlist

From `03_audio/timings.json`, one scene roughly every 6-10 seconds of narration: a 6-minute episode is typically 36-60 scenes. The whiteboard style has little to look at, so it is cut faster than a painted documentary.

Each entry is `{"scene": N, "description": "...", "motion": "slow push in"}`. Write a description as one simple drawing: the host doing one thing, plus one or two marker props. Never ask for text, numbers, labels, arrows or diagrams inside the image; captions carry the words. `type: "real_photo"` marks a beat to fill by hand; `generate_scenes.py` skips it (rare, see `compliance-and-safety.md`).

**Two characters per shot at most.** FLUX.2 klein collapses a third distinct character to one rendered subject. Write crowded moments as shot and reverse-shot pairs.

**Write the thumbnail beat for the thumbnail.** The scene named by `metadata.json` `thumbnail_beat` (default 1, the hook) becomes the thumbnail background with large title text on the left. Describe it with the subject on the right third of the frame, empty white space on the left, one bold hero prop, and the host reacting to it.

## Generating scenes

`python3 scripts/generate_scenes.py <slug>` builds a prompt per beat (`scripts/scenes/prompt_builder.py`: style suffix, then the beat description) and calls the backend named by `IMAGE_BACKEND`:

- **`flux` (default).** `scripts/scenes/flux_orchestrator.py`: FLUX.2 [klein] 9B on Cloudflare Workers AI, with `brand/host/host-reference-clean.jpeg` sent as the reference image on every beat so the host stays the same character. Three beats run in parallel; 429/5xx are retried with backoff. Seeds are honoured. Free tier is 10,000 neurons/day: if `05_scenes/_flux_debug/*.error.txt` says the daily quota is used up, finish other work, wait, and re-run (finished beats are skipped).
- **`raphael`** and **`cloudflare`** (SDXL) are text-prompt-only fallbacks. They cannot take the reference image, so the host drifts off-model. Use only if flux is down, and say so in the changelog.

Generation size is 1024x576; assembly upscales to 1920x1080. Options: `--beats 1,3,5-7`, `--seed N` (one beat), `--attempt N` (new seed set), `--dry-run`.

**Review every generated PNG before assembling.** Reroll anything off-model: extra colours, a mouth on the host, shading, text in the image, a wrong number of characters. `generate_scenes.py --beats N --seed <new>`.

## Animation

Every scene gets a Ken Burns push in/out via ffmpeg zoompan, ~5% zoom ramped over the scene. No flat static hold, and no AI motion (it melts stick figures).

## On-screen text

No baked-in image text. Captions carry the words (`captions.md`).
