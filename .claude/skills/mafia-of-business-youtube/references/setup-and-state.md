# State

`channel_state.json` is the single source of truth for anything that must not drift; MongoDB holds the topic bank and the small text state that has to survive between runs.

## `channel_state.json`

Locked config, loaded by every script through `scripts/state.py`'s `load_state()`:

- `voice`: edge-tts voice id (`hi-IN-MadhurNeural`), the per-section rate/volume/pitch presets (`hook`, `duniya`, `khel`, `raaz`, `sabak`), `default_section`, chunk limits.
- `style_lock`: the image prompt suffix (boss stickman, black/white/gold), aspect `16:9`, resolution `1920x1080`.
- `audio`: loudness target (-14 LUFS), true peak, silence trimming, gaps.
- `format`: `runtime_min_seconds` 180, `target_runtime_seconds` 240, `runtime_max_seconds` 300, `sections`, scene length 5-7 s, fps, zoom.
- `ambience`, `captions`, `thumbnail`: effect keywords, caption style, thumbnail colours and font.
- `counters`: `episodes_published`.

Anything that must be identical across videos lives here, not in a doc or a second copy in a script. Any change to a locked value gets a dated line in `reports/changelog.md` with the reason. If state contradicts what you were about to do, state wins.

## MongoDB (database `mafia_of_business_pipeline`; `MONGODB_DB` overrides)

`scripts/state_db.py` is the only interface:

| Command | Does |
|---|---|
| `topics [queued\|used\|rejected]` | list topics (default queued) |
| `topics-count` | how many topics per status |
| `topic-add` | add queued topics: a JSON object or list on stdin, each needing `topic` and `category` plus `setting`, `myth`, `angle`, `visual_hooks`, `score`, `keywords` |
| `topic-use "<name>"` | queued -> used, stamped with today's date |
| `topic-reject "<name>" "<why>"` | -> rejected |
| `recent [N]` | recently made episodes with status (`pending`, `ready`, `posted`, `abandoned`) |
| `episode-posted <slug> <url>` | the operator marks a finalized episode as posted |
| `episode-abandon <slug> "<why>"` | retire an episode that cannot be finished (marker `08_publish/abandoned.json`; status `abandoned`) |
| `pull` / `push` | run start / run end (`run_cycle.sh` does both) |

Collections: `topics`, `episodes` (script, shotlist, chunk plan, metadata, `01_research/sources.md`, `08_publish/finalize_log.json`, plus `output_dir` and status), `state` (`channel_state`).

At the start of a run `pull` restores the text files of unfinished episodes and takes only the live keys (`counters`, `baselines`, `active_experiment`) from MongoDB; all other config comes from git, so a config change ships with the commit and a stale database copy can never undo it. An empty database is seeded once from `seed/topic_bank.seed.json`. At the end `push` saves counters and episode text; a posted episode is never downgraded. Only text is stored: audio, images and video never go to the database.

Environment (`.env` in the repo root, gitignored): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` (optional `CLOUDFLARE_IMAGE_MODEL`), `MONGODB_URI`; optional `IMAGE_BACKEND` (`flux` default), `MONGODB_DB`. Nothing is committed to git by the pipeline.

## Experiment ledger (`reports/experiments.md`)

One row per experiment, one variable live at a time:

```
| # | Start date | Variable changed | Hypothesis | Videos | Result | Keep? |
```
