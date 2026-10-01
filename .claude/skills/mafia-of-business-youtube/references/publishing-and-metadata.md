# Metadata and finalize

The pipeline never posts anywhere. `run_episode.py` ends with `finalize_episode.py`, which copies the package to `output/<slug>/` for the operator.

## `08_publish/metadata.json` (write before `run_episode.py`)

| Field | Rule |
|---|---|
| `title` | Required. The series template, 45-80 chars (see `thumbnail-and-metadata.md`). |
| `title_alternates` | The two rejected candidate titles. |
| `description` | Myth hook with the search phrase in the first 150 chars, summary, chapters, "🔍 आपके सवाल" block, sources, channel line, 3 hashtags. |
| `tags` | 15-25, Hinglish + Devanagari + English variants, under 500 characters. |
| `thumbnail_text` | 2-4 Devanagari words. Without it no thumbnail is made and finalize fails. |
| `thumbnail_accent_word` | One word from `thumbnail_text`, drawn in gold. |
| `thumbnail_beat` | Scene number for the thumbnail centre (default 1). |
| `thumbnail_annotations` | 3-4 money notes, Devanagari + digits/₹ only (see `thumbnail-and-metadata.md`). |
| `playlist` | The topic's vertical. |
| `pinned_comment` | Bonus fact + question, Hindi. |
| `community_post` | One-line poll, Hindi. |
| `shorts_hook` | `{"start": s, "end": s}` from `timings.json`. |
| `made_for_kids` | `false`. |
| `synthetic_disclosure` | `true`. |

## Finalize

`finalize_episode.py <slug>` checks the video (1920x1080, audio present, 180-300 s), copies video, thumbnail, captions.srt and metadata.json to `output/<slug>/`, writes `posting.md` (everything to paste into YouTube Studio plus the posting checklist), records the episode in MongoDB as `ready`, and writes `08_publish/finalize_log.json` (`status: ok`). Then `cleanup_episode.py` deletes `03_audio/`, `05_scenes/`, `07_edit/`. Rerunning finalize on a finished episode does nothing.

If finalize fails, read its message, fix the cause (usually runtime: trim the script and rerun from narration), and rerun `run_episode.py <slug>`.

After posting, the operator runs `python3 scripts/state_db.py episode-posted <slug> <youtube-url>`.
