# Mafia of Business

Makes one Hindi YouTube video per run: how everyday Indian businesses and people actually make money (chai wala, gym, restaurant, politician...), told as a 3-5 minute stickman story. Nothing is posted anywhere; the finished package lands in `MafiaOfBusiness/output/<slug>/` and you post it by hand.

Each run: an opencode agent picks a topic from the MongoDB bank, researches it and writes a Hindi script and SEO metadata; edge-tts (`hi-IN-MadhurNeural`) records the narration; FLUX.2 klein on Cloudflare Workers AI draws the scenes with the boss stickman as a reference image; ffmpeg renders 1920x1080 with Devanagari captions and light ambience (no music); a Devanagari thumbnail is built; the package is copied to `output/<slug>/`.

## Setup

1. `.env` in this folder (gitignored):
   ```
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_API_TOKEN=...
   MONGODB_URI=...
   ```
2. Installed: `ffmpeg`, `opencode` (`~/.opencode/bin`), font Noto Sans Devanagari (`sudo apt install fonts-noto-core`).
3. Optional env: `OPENCODE_MODEL`, `MAX_ATTEMPTS` (default 4), `IMAGE_BACKEND` (`flux` default), `CLOUDFLARE_IMAGE_MODEL`, `MONGODB_DB`.

Cloudflare's free tier is 10,000 neurons a day for this account; a ~45-scene episode can use most of it. A run stopped by the quota resumes with `./make-video` after 05:30 IST.

## Running

```bash
./make-video
```

## Posting

Open `MafiaOfBusiness/output/<slug>/posting.md`: it has the title, alternates, description, tags, playlist, pinned comment, community poll, Shorts range and a checklist. Post daily if you can (both reference channels grew on one video a day). After posting:

```bash
cd MafiaOfBusiness && ../.venv/bin/python scripts/state_db.py episode-posted <slug> <youtube-url>
```

## Tests

```bash
.venv/bin/python -m pytest -q
```
