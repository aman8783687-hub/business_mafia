Operate the Business Mafia channel (folders say MafiaOfBusiness) autonomously for one cycle, and do not stop until a NEW episode, made in this cycle, is finalized into output/<slug>/. You are the supervisor: nobody will step in, so when something fails you diagnose it and find another way.

Use the mafia-of-business-youtube skill (../.claude/skills/mafia-of-business-youtube/SKILL.md) for every judgment call; read its references/*.md files before the matching stage. Everything runs from this directory (MafiaOfBusiness/). python3, ffmpeg and edge-tts are on PATH.

DONE MEANS: `python3 scripts/pending_episodes.py` exits 0 AND this episode's `08_publish/finalize_log.json` shows status ok AND `output/<slug>/posting.md` exists. Print all three before claiming completion. If you cannot get there after several different approaches, say so with the concrete blocker.

STATE: Topics live only in MongoDB. Use `python3 scripts/state_db.py`: `topics [queued|used|rejected]`, `topics-count`, `topic-add` (JSON object or list on stdin, each with `topic`, `category`, `setting`, `score`, `angle`, `visual_hooks`, `keywords`; duplicates skipped), `topic-use "<name>"`, `topic-reject "<name>" "<reason>"`. channel_state.json counters and unfinished episodes' text files are loaded from MongoDB before you start and saved back when the run ends. Never run git commit or git push. Never post anywhere.

FILE RULES: use `.scratch/` in this directory for temporary files.

1. Resume check: run `python3 scripts/pending_episodes.py`. If it prints a slug, resume it from whichever stage has missing outputs. If it prints nothing, start a new episode.

2. Run `python3 scripts/state_db.py topics-count`. If `queued` is under 8, refill per topic-strategy.md's "Refilling the bank" until above 15.

3. Pick the next topic per topic-strategy.md (prefer the topic the previous episode's [SABAK] promised; never the same vertical twice in a row: `python3 scripts/state_db.py recent 3`). Slug: `YYYY-MM-DD-<short-english-slug>`. Research first: `episodes/<slug>/01_research/sources.md` per research-and-facts.md. Then write `topic.json` (with `keywords` and `myth`), `02_script/script.md` + `shotlist.json` (script-formula.md, Hindi, tags [HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK], a "मान लीजिए" character, numbers as words, ~1,250-1,500 words for 8-12 minutes, 7-10 s beats). `topic.json` carries `format`: `kamai` (deep dive, ends with "आप शुरू करना चाहें तो") or `list` ("₹X से शुरू करें ये N बिज़नेस"); alternate them (`recent 3`), and follow script-formula.md's structure for that format. Follow script-formula.md's "Tone": the good side of business, every cost paired with the owner's fix, [RAAZ] is the owner's smart move, end on a win, no doom words, no get-rich promises, and run `python3 scripts/check_script.py <slug>` until it prints `script.md ok`. Write `03_audio/chunk_plan.json` (voice-and-audio.md). Check compliance-and-safety.md. Mark the topic used: `python3 scripts/state_db.py topic-use "<topic>"`.

4. `python3 scripts/generate_narration_chunks.py <slug>` then `python3 scripts/stitch_audio.py <slug>`. If stitch exits 3 (runtime outside 480-720 s), edit the script and chunk plan, delete the changed chunks' files, and rerun both. Then write `08_publish/metadata.json` (publishing-and-metadata.md, thumbnail-and-metadata.md) using `03_audio/timings.json` for chapters and `shorts_hook`. Run `python3 scripts/check_script.py <slug>` again: with the chunk plan and metadata present it also checks that the spoken chunk text has no digits or English sentences, that every beat is in exactly one chunk, and that the thumbnail is buildable (`thumbnail_text` as "<X> वाला | कितना कमाता है?" or "₹<X> से शुरू | ये <N> बिज़नेस" with at most 4 Devanagari words per line, a `thumbnail_scene` description, an optional `thumbnail_badge`, no Latin letters). Fix everything it prints before continuing.

5. `python3 scripts/generate_scenes.py <slug>` and `python3 scripts/generate_thumbnail_scene.py <slug>`. Look at `08_publish/thumbnail_scene.png` (boss on-model, large on the right, left half clear; else `--force --seed <new>`). Look at every `05_scenes/scene_*.png` against SKILL.md's quality gate (boss on-model, black/white/gold only, no text, at most two characters) and reroll bad beats with `--beats N` (each rerun is a new image).

6. `python3 scripts/run_episode.py <slug>`. It is idempotent: it checks the script, skips finished audio/scenes, assembles, generates the thumbnail scene and builds the thumbnail, finalizes into output/<slug>/ and cleans up.

RECOVERY:
- A scene's `05_scenes/_flux_debug/scene_XXXX.error.txt` shows a failure: rerun `generate_scenes.py <slug>` (finished beats are skipped). Scenes come from perchance.org in headless Firefox (about a minute each, no quota). If every beat fails (generator frame never appeared, controls not set), the site is down or changed: wait ten minutes and retry once, then stop and report it. If the thumbnail scene's FLUX call says the Cloudflare daily quota is used up, `run_episode.py` falls back to a beat scene; note it in the changelog.
- A stage errors: read the error, fix the cause, rerun that stage.
- An episode that cannot be finished (rejected topic, unsalvageable script): retire it with `python3 scripts/state_db.py episode-abandon <slug> "<why>"`, then start a new episode. A stuck pending episode otherwise fails every later cycle.
- Never re-create an episode that already exists.

7. Log deliberate deviations in `reports/changelog.md`.

8. Report the DONE MEANS evidence and the output folder path.

Stop and message the operator only for SKILL.md's "When to stop and ask" cases.
