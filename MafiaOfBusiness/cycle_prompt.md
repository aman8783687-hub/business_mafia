Operate the RedHat Engineer channel autonomously for one publish cycle, and do not stop until a NEW episode, made in this cycle, is actually uploaded to the Content Lab website. (Each run makes exactly one new episode.) You are the supervisor of this whole cycle: nobody will step in, so when something fails you diagnose it and find another way.

Use the redhat-engineer-youtube skill (../.claude/skills/redhat-engineer-youtube/SKILL.md) for every judgment call; read its references/*.md files before the matching stage. Everything runs from this directory (MafiaOfBusiness/). All tools (python3, ffmpeg, edge-tts) are already on PATH.

DONE MEANS: `python3 scripts/pending_episodes.py` exits 0 AND this episode's `08_publish/upload_log.json` shows content_lab status ok. Do not claim completion without printing both. If you cannot get there after trying several different approaches, say so with the concrete blocker.

STATE: Topics live only in MongoDB (there is no topic_bank.json). Use `python3 scripts/state_db.py`: `topics [queued|used|rejected]` lists them, `topics-count` counts them, `topic-add` adds new queued topics (a JSON object or list on stdin, each with `topic`, `category`, `setting`, `score`, `angle`, `visual_hooks`; duplicates are skipped), `topic-use "<name>"` marks a queued topic as used, `topic-reject "<name>" "<reason>"` rejects one. Changes to topics are saved instantly. channel_state.json and unfinished episodes' text files are loaded from MongoDB before you start and saved back automatically when the run ends. Never run git commit or git push, and do not store audio, images or video anywhere but this run's working folders.

UPLOAD RULE: the only upload is `scripts/run_episode.py` (which calls `publish_all.py`): it uploads the video to Cloudinary and registers it with the Content Lab website using the CONTENT_LAB_URL / CONTENT_LAB_API_KEY environment variables. The operator downloads it there and posts by hand. Never post anywhere else. If the upload fails, diagnose and retry; rerunning is safe because it is idempotent by slug. Do not run cleanup_episode.py yourself; run_episode.py does it after a confirmed upload.

FILE RULES: use `.scratch/` inside this directory for any downloaded or temporary files.

0. Concurrency is handled by GitHub Actions; there is no lock file beyond `.run_episode.lock`. Work only in this directory (MafiaOfBusiness/).

1. Resume check: run `python3 scripts/pending_episodes.py`. If it prints a slug, resume it (skip topic selection and creative writing, continue from whichever stage has missing outputs). If it prints nothing, start a new episode with step 2.

2. The channel covers the story and mysteries behind technological innovation (see the skill). First run `python3 scripts/state_db.py topics queued` and reject every queued topic that is not a technology story with `topic-reject "<name>" "off-focus: not a technology story"` (the bank may still hold old Indian-history mystery topics). Then run `python3 scripts/state_db.py topics-count`. If `queued` is under 8, refill it per topic-strategy.md's "Refilling the bank" section (real, documented technology stories, category balance, no topic already published, never a living person in a critical light) with `topic-add` until `queued` is back above 15.

3. Pick the next topic per topic-strategy.md. Research it first: write `episodes/<slug>/01_research/sources.md` per research-and-facts.md (every date, name, number and "first" claim sourced; run_episode.py refuses to start without it). Then create `topic.json`, `02_script/script.md` + `shotlist.json` (script-formula.md; the section tags are [COLD_OPEN] [SETUP] [RISING_MYSTERY] [CLIMAX_REVEAL] [AFTERMATH]), `03_audio/chunk_plan.json` (voice-and-audio.md), and `08_publish/metadata.json` with title, description, tags, `thumbnail_text` and `thumbnail_accent_word` (publishing-and-metadata.md, thumbnail-and-metadata.md). Write the thumbnail beat (beat 1) with its subject on the right and empty space on the left. Check compliance-and-safety.md for any factual-sounding claim. Mark the topic used with `python3 scripts/state_db.py topic-use "<topic name>"`.

4. Generate and QA the mechanical assets: `python3 scripts/generate_narration_chunks.py <slug>`, then `python3 scripts/stitch_audio.py <slug>`, then `python3 scripts/generate_scenes.py <slug>` (it skips beats that already have a PNG). Look at every `05_scenes/scene_*.png` against SKILL.md's quality gate (host on-model, red/black/white only, no shading, no on-image text, at most two characters) and reroll bad beats with `--beats N --seed <new>`.

5. Run `python3 scripts/run_episode.py <slug>`. It is idempotent.

RECOVERY:
- If a beat's debug record (`05_scenes/_flux_debug/scene_XXXX.error.txt`) shows a failure, reroll that beat: `python3 scripts/generate_scenes.py <slug> --beats N --seed <new>`. If the record says the Cloudflare daily quota is used up (10,000 neurons/day on the free tier), wait for the reset and re-run `generate_scenes.py` (finished beats are skipped); do not switch `IMAGE_BACKEND` to raphael/cloudflare, which cannot keep the host on-model, unless the operator says so.
- If a stage errors, read the error, fix the cause and rerun that stage.
- If the upload fails, rerun `python3 scripts/publish_all.py <slug>`, then `python3 scripts/cleanup_episode.py <slug>` only after it reports ok.
- Never re-create an episode that already exists and never upload the same episode twice.

6. Log deliberate deviations in `reports/changelog.md`.

7. Report the evidence for DONE MEANS (the pending_episodes.py result and the upload_log.json content).

Stop and message the operator only for the cases in SKILL.md's "When to stop and ask" section.
