# State

`channel_state.json` is the single source of truth for anything that must not drift; MongoDB holds the topic bank and the small text state that has to survive between GitHub Actions runs.

## `channel_state.json`

Locked config, loaded by every script through `scripts/state.py`'s `load_state()`:

- `voice`: edge-tts voice id and the per-section rate/volume/pitch presets (`cold_open`, `setup`, `rising_mystery`, `climax_reveal`, `aftermath`), chunk limits.
- `style_lock`: the image prompt suffix, aspect `16:9`, resolution `1920x1080`, reference dataset, generation notes.
- `audio`: loudness target (-14 LUFS), true peak, silence-trimming values, gaps.
- `format`: runtime target and hard range (`target_runtime_range_seconds`, 300-420), words per minute, scene length, fps, zoom, `video_maxrate`.
- `ambience`: keyword cues, `disable` list (channel-wide), scene-cut whooshes.
- `counters`: `episodes_published`, bumped once per episode by `publish_all.py`.

Anything that must be identical across videos lives here, not in your head and not as a second copy inside a script or doc. Any change to a locked value gets a dated line in `reports/changelog.md` with the reason. If a value in state contradicts what you were about to do, state wins.

## MongoDB (database `imagine_error_pipeline`, name kept from the fork so existing counters, slots and used-topic history carry over)

`scripts/state_db.py` is the only interface:

| Command | Does |
|---|---|
| `topics [queued\|used\|rejected]` | list topics (default queued) |
| `topics-count` | how many topics per status |
| `topic-add` | add queued topics: a JSON object or list on stdin, each needing `topic` and `category` plus `setting`, `score`, `angle`, `visual_hooks` |
| `topic-use "<name>"` | queued -> used, stamped with today's date |
| `topic-reject "<name>" "<why>"` | -> rejected |
| `recent [N]` | recently made episodes with status |
| `pull` / `push` | run start / run end (the workflow's `run_cycle.sh` does both) |

Collections: `topics`, `episodes` (script, shotlist, chunk plan, metadata, `01_research/sources.md`, `08_publish/upload_log.json` for each episode), `state` (`channel_state`), `slots`.

At the start of a run `pull` restores the text files of unfinished episodes and takes only the live keys (`counters`, `baselines`, `active_experiment`) from MongoDB. Everything else in `channel_state.json` comes from git, so a config change (voice, style, format) ships with the commit and a stale database copy can never undo it; an empty database is seeded once from `seed/topic_bank.seed.json` and `channel_state.json`. At the end `push` saves counters and episode text. Only text is stored: audio, images and video never go to the database.

Environment (GitHub Actions secrets, or a local `.env` for `make-video`): `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` (optional `CLOUDFLARE_IMAGE_MODEL`), `MONGODB_URI`, `CONTENT_LAB_URL`, `CONTENT_LAB_API_KEY`; optional `IMAGE_BACKEND` (`flux` default). Nothing is committed to git by the pipeline.

## Experiment ledger (`reports/experiments.md`)

One row per experiment, one variable live at a time:

```
| # | Start date | Variable changed | Hypothesis | Videos | Result | Keep? |
```
