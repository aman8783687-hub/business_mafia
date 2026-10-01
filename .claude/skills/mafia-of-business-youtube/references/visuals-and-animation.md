# Visuals and animation

## Building the shotlist

From `03_audio/timings.json`, one scene roughly every 5-7 seconds of narration: a 4-minute episode is typically 35-50 scenes. The whiteboard style has little to look at, so it is cut fast.

Each entry is `{"scene": N, "description": "...", "motion": "slow push in"}`. Write a description as one simple drawing: the boss doing one thing, plus one or two marker props (a fuel nozzle, a dal pot, a dumper, a poultry shed, a gym bench, a shelf of packets). Money props (coins, notes, a ₹ bag) are drawn in gold. Never ask for text, numbers, labels, arrows or diagrams inside the image (FLUX cannot draw Devanagari); captions carry the words. `type: "real_photo"` marks a beat to fill by hand; `generate_scenes.py` skips it (rare).

**Two characters per shot at most.** FLUX.2 klein collapses a third distinct character to one rendered subject. Write crowded moments as shot and reverse-shot pairs. The example owner (रमेश) is a plain stickman with one identifying prop; the boss is the hat-and-suit host.

**Write the thumbnail beat for the thumbnail.** The scene named by `metadata.json` `thumbnail_beat` (default 1, the hook) sits in the centre of the annotated thumbnail: the boss at the business, subject centred, empty white space left and right for the money notes.

## Generating scenes

`python3 scripts/generate_scenes.py <slug>` builds a prompt per beat (`scripts/scenes/prompt_builder.py`: style suffix, then the beat description) and calls the backend named by `IMAGE_BACKEND`:

- **`flux` (default).** FLUX.2 [klein] 9B on Cloudflare Workers AI, with `brand/host/host-reference-clean.jpeg` sent as the reference image on every beat so the boss stays the same character. Three beats in parallel; 429/5xx retried with backoff; seeds honoured. Free tier is 10,000 neurons/day for this channel's own Cloudflare account: if `05_scenes/_flux_debug/*.error.txt` says the daily quota is used up, stop and resume after 05:30 IST (finished beats are skipped).
- **`cloudflare`** (SDXL) is a text-prompt-only fallback that cannot take the reference image; the boss drifts off-model. Use only if flux is down, and say so in the changelog.

Generation size is 1024x576; assembly upscales to 1920x1080. Options: `--beats 1,3,5-7`, `--seed N` (one beat), `--attempt N`, `--dry-run`.

**Review every generated PNG before assembling.** Reroll anything off-model: red or extra colours, a mouth on the host, shading, text in the image, a wrong number of characters. `generate_scenes.py --beats N --seed <new>`.

## Animation

Every scene gets a Ken Burns push in/out via ffmpeg zoompan, ~5% zoom ramped over the scene. No flat static hold, and no AI motion (it melts stick figures).

## On-screen text

No baked-in image text. Captions carry the words (`captions.md`).
