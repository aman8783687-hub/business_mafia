# Mafia of Business channel -- start here

This directory is the production system for the Hindi YouTube channel **Mafia of Business**: 3-5 minute, 16:9 stickman story videos about how everyday Indian businesses and people actually make money. Local only: each run finalizes one video into `MafiaOfBusiness/output/<slug>/`; the operator posts it by hand. If you are an agent picking up work here, read in this order:

1. `.claude/skills/mafia-of-business-youtube/SKILL.md` -- the operating manual; its `references/` has one file per stage.
2. `MafiaOfBusiness/channel_state.json` -- locked config: voice `hi-IN-MadhurNeural`, boss-stickman style lock, 180-300 s format, gold captions.
3. The MongoDB topic bank: `python3 scripts/state_db.py topics`.
4. `MafiaOfBusiness/reports/changelog.md`.

## How a run works

`./make-video` -> `MafiaOfBusiness/scripts/run_cycle.sh` (loads state from MongoDB, runs an opencode agent on `cycle_prompt.md` up to 4 times, saves state) -> the agent writes topic, research, Hindi script and metadata -> `scripts/run_episode.py <slug>`: `check_script.py`, narration, stitch (runtime guard), scenes, assembly, thumbnail, `finalize_episode.py` (verify, copy to `output/<slug>/`, `posting.md`, MongoDB `ready`), `cleanup_episode.py`.

Secrets in `.env` (gitignored): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MONGODB_URI`. State in MongoDB db `mafia_of_business_pipeline`.

Forked on 2026-10-01 from the sibling pipeline in `../imagine_error_gh_action/`; design in `docs/superpowers/specs/2026-10-01-mafia-of-business-design.md`.
