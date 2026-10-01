# Voice and audio

- Voice: edge-tts `hi-IN-MadhurNeural` (fallback `hi-IN-SwaraNeural`, only after logging why in `reports/changelog.md`). Locked in `channel_state.json`.
- Section presets (rate/volume/pitch) per tag: `hook` slow and weighty, `duniya` neutral, `khel` faster, `raaz` slower and conspiratorial, `sabak` calm. A beat with no tag above it uses `khel`.
- `03_audio/chunk_plan.json`: `{"chunks": [{"id": 1, "beats": [1, 2], "text": "<the beats' Hindi text joined>"}, ...]}`, 2-3 sentences per chunk, never across a section tag.
- The chunk `text` is what edge-tts actually speaks: `check_script.py <slug>` rejects digits or English sentences in it and requires every script beat in exactly one chunk (a deliberate phonetic respelling of a mispronounced word is allowed).
- `generate_narration_chunks.py <slug>` writes `chunk_XXXX.mp3` + `.wordbounds.jsonl` (word timing for captions); `stitch_audio.py <slug>` trims, joins with 0.4 s gaps (0.8 s at section breaks), masters to -14 LUFS and writes `timings.json`, `word_timings.json`.
- `stitch_audio.py` exits 3 when the narration is outside 180-300 s. Fix the script, delete the changed chunks' mp3/jsonl, rerun both.
- Hindi pronunciation: write numbers as words; write English business words in Devanagari (प्रॉफ़िट); if a word is mispronounced, respell it phonetically in Devanagari and regenerate that chunk.
