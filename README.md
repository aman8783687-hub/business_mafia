# Business Mafia (repo: Mafia of Business)

Makes one Hindi YouTube video per run: how everyday Indian businesses and people actually make money (chai wala, gym, restaurant, politician...), told as a 3-5 minute stickman story. Nothing is posted anywhere; the finished package lands in `MafiaOfBusiness/output/<slug>/` and you post it by hand.

Each run: an opencode agent picks a topic from the MongoDB bank, researches it and writes a Hindi script and SEO metadata; edge-tts (`hi-IN-MadhurNeural`) records the narration; perchance.org (driven in headless Firefox, free, no quota) draws the scenes and FLUX.2 klein on Cloudflare draws the thumbnail scene with the boss stickman as a reference image; ffmpeg renders 1920x1080 with Devanagari captions and light ambience (no music); a Devanagari thumbnail is built; the package is copied to `output/<slug>/`.

## Setup

1. `.env` in this folder (gitignored):
   ```
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_API_TOKEN=...
   MONGODB_URI=...
   ```
2. Installed: `ffmpeg`, `opencode` (`~/.opencode/bin`), font Noto Sans Devanagari (`sudo apt install fonts-noto-core`).
3. Optional env: `OPENCODE_MODEL`, `MAX_ATTEMPTS` (default 4), `IMAGE_BACKEND` (`perchance` default, `flux`, `cloudflare`), `PERCHANCE_STYLE`, `CLOUDFLARE_IMAGE_MODEL`, `MONGODB_DB`.

Scenes take about a minute each on perchance (`make-video` installs Playwright and its Firefox). Cloudflare's free 10,000 neurons a day now buy only ~6 FLUX klein 9B images, so FLUX is kept for the thumbnail scene; a run stopped by that quota resumes with `./make-video` after 05:30 IST.

## Running

```bash
./make-video
```

## GitHub Actions (one-click video + 24h download link)

Actions tab → **Business Mafia – Make Video** → Run workflow. Optional
inputs: `topic_override` (exact bank name), `topic_hint` (free text),
`max_attempts`. Scenes render on **Perchance** (free, no quota, no key —
headless Firefox is installed by the workflow, ~1 min/scene). The run executes `run_cycle.sh` on a
runner, then `scripts/upload_cloudinary.py <slug>`:

- video uploads to Cloudinary folder `business-mafia/` (public,
  `fl_attachment` download link);
- the **⬇️ Download video** link is printed in the run summary and saved
  in `output/<slug>/cloudinary.json`;
- the episode package is also attached as an artifact (retention 1 day);
- `cleanup-cloudinary.yml` runs hourly and deletes uploads older than 24h.

Secrets (repo Settings → Secrets → Actions): `MONGODB_URI`,
`CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`.
No LLM key needed — opencode runs free, no auth.
Optional: `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` (thumbnail scene
only — without them the thumbnail falls back to a beat scene).
Vars: `OPENCODE_MODEL`, `MAX_ATTEMPTS`, `PERCHANCE_STYLE`.

## Posting

Open `MafiaOfBusiness/output/<slug>/posting.md`: it has the title, alternates, description, tags, playlist, pinned comment, community poll, Shorts range and a checklist. Post daily if you can (both reference channels grew on one video a day). After posting:

```bash
cd MafiaOfBusiness && ../.venv/bin/python scripts/state_db.py episode-posted <slug> <youtube-url>
```

## Tests

```bash
.venv/bin/python -m pytest -q
```
