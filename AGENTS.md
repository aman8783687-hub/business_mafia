# RedHat Engineer channel -- start here

This directory is the production system for the "RedHat Engineer" YouTube
channel: 5-7 minute, 16:9 stickman explainers about the **story and mysteries
behind technological innovation**, past and present (legends, disputed
claims, missing papers, conspiracy theories: told fairly, then checked against
the record), uploaded to Content Lab. If you're an agent picking up work here,
read in this order:

1. **`.claude/skills/redhat-engineer-youtube/SKILL.md`** -- the operating
   manual. Read this before doing anything on this channel. Its
   `references/` folder has one file per pipeline stage.
2. **`MafiaOfBusiness/channel_state.json`** -- the live, locked config: voice
   (edge-tts `en-US-AvaMultilingualNeural`, female), visual style lock
   (red-fedora stickman on a whiteboard, FLUX.2 klein with a reference
   image), format targets (16:9, 5-7 min), counters.
3. **The MongoDB topic bank** (`python3 scripts/state_db.py topics`) --
   queued/used/rejected topics.
4. **`MafiaOfBusiness/reports/changelog.md`** -- dated log of every deliberate
   deviation, including the 2026-09-30 conversion from the Indian-history
   mystery channel this repo was forked for ("Imagine Error"). The
   `MafiaOfBusiness/` directory name is left over from that.

## How this deployment runs

This repo runs on GitHub Actions (`.github/workflows/redhat-engineer.yml`):
one video per run, produced by an opencode agent following
`MafiaOfBusiness/cycle_prompt.md`, uploaded to the Content Lab website, then its
media is deleted. The thumbnail and metadata are attached to the run as an
artifact. There is no publishing to any social platform; the operator posts
by hand from Content Lab. Secrets come from the environment
(`CONTENT_LAB_URL`, `CONTENT_LAB_API_KEY`, `CLOUDFLARE_API_TOKEN`,
`CLOUDFLARE_ACCOUNT_ID`, `MONGODB_URI`). Topic bank, counters and episode
records live in MongoDB (`scripts/state_db.py`), not in git; only the live
keys (`counters`, `baselines`, `active_experiment`) are read back from Mongo,
so config in `channel_state.json` always comes from git.

## Design notes

- Images: FLUX.2 klein on Cloudflare Workers AI, conditioned on
  `brand/host/host-reference-clean.jpeg` with every request
  (`scripts/scenes/flux_orchestrator.py`, `IMAGE_BACKEND=flux`, the default).
  `raphael` and `cloudflare` (SDXL) remain as text-only fallbacks that cannot
  keep the host on-model. Free tier is 10,000 neurons/day; re-run
  `generate_scenes.py` after a reset, finished beats are skipped.
- Host: the red-fedora stickman, same character every scene. Two distinct
  characters per shot at most.
- No music. Sparse synthesized ambience (scene-cut whooshes, a reveal sting,
  a few keyword effects) under the narration at a fixed low gain.
- Format: 16:9 / 1920x1080, 5-7 minute (target 360 s) episodes, 6-10 s scene
  holds.
- Female narrator, section presets `cold_open / setup / rising_mystery /
  climax_reveal / aftermath` (a story's hook, setup, escalation, turn and
  landing).

## Pipeline commands, in order

All commands run from `MafiaOfBusiness/`; the workflow puts `python3`, `ffmpeg`
and `edge-tts` on PATH. `<slug>` is the episode folder name.

1. Topic, research, script -- write `episodes/<slug>/{topic.json,
   01_research/sources.md, 02_script/script.md, 02_script/shotlist.json}` by
   hand per `topic-strategy.md`, `research-and-facts.md`, `script-formula.md`.
2. Write `episodes/<slug>/03_audio/chunk_plan.json` by hand (see
   `voice-and-audio.md`), then:
   `python3 scripts/generate_narration_chunks.py <slug>`
   `python3 scripts/stitch_audio.py <slug>`
3. Scenes -- `python3 scripts/generate_scenes.py <slug>` generates one 16:9
   image per beat. Review every generated PNG; reroll a bad one with
   `--beats N --seed <new>`.
4. `python3 scripts/assemble_episode.py <slug>` -- Ken Burns zoompan per beat,
   concatenates, mixes in ambience (no music), masters loudness, burns
   captions. Writes `episodes/<slug>/07_edit/redhat-engineer-<slug>-episode.mp4`
   + `07_edit/captions.srt`.
5. Write `episodes/<slug>/08_publish/metadata.json` by hand (title,
   description, tags, `thumbnail_text`; see `publishing-and-metadata.md`).
6. `python3 scripts/run_episode.py <slug>` runs the remaining stages (it
   re-runs 2-4 as needed, then builds `08_publish/thumbnail.png`), uploads to
   Content Lab (`publish_all.py`), then deletes the episode's media
   (`cleanup_episode.py`).
7. `reports/changelog.md` and `reports/experiments.md` -- update by hand.
