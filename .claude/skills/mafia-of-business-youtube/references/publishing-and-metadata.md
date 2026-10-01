# Metadata and publishing

The pipeline never posts to YouTube. It uploads the video and its text to Content Lab (Cloudinary storage plus a listing in the RedHat Engineer section); the operator downloads it and posts by hand. Never drive a browser to post.

## `08_publish/metadata.json`

Write it before `run_episode.py`.

| Field | Rule |
|---|---|
| `title` | Required. 45-60 characters, interesting word first, one idea, a promise the video keeps (formulas in `thumbnail-and-metadata.md`). Put the real search term in it ("Indus script", "Antikythera mechanism"), not only curiosity. |
| `description` | Full description from `thumbnail-and-metadata.md`: hook with the main search term, summary, chapters (first at `0:00`, at least three, timestamps from `timings.json` `start` times), sources from `01_research/sources.md`, channel line, hashtags last. |
| `tags` | 8-15. `RedHat Engineer` is added automatically. |
| `thumbnail_text` | 2-4 words, uppercase. Without it no thumbnail is made. |
| `thumbnail_accent_word` | One word from `thumbnail_text`, drawn in red. |
| `thumbnail_beat` | Scene number used as the thumbnail background (default 1). |
| `made_for_kids` | `false`. |
| `synthetic_disclosure` | `true`. |

## The upload

`run_episode.py` runs `publish_all.py` -> `publish_content_lab.py`: sign, upload to Cloudinary, register `{title, description, tags}` under project `redhat-engineer`. Idempotent by slug; result in `08_publish/upload_log.json`. After a confirmed upload `cleanup_episode.py` removes `03_audio/`, `05_scenes/` and `07_edit/`; `topic.json`, `01_research/`, `02_script/` and `08_publish/` stay.

Content Lab has no thumbnail field, so the thumbnail (`08_publish/thumbnail.png`) reaches the operator as a GitHub Actions run artifact (see the workflow) and stays in the episode folder on a local run. The operator attaches it when posting.

If the upload fails: read `upload_log.json`, fix the cause, and re-run `python3 scripts/publish_all.py <slug>`; run `cleanup_episode.py` only after it reports ok.

## Limits

The operator posts by hand, so there is no analytics feedback inside the cycle. Do not invent performance numbers.
