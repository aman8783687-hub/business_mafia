# Captions

Pipeline: edge-tts WordBoundary events -> `generate_narration_chunks.py` `.wordbounds.jsonl` -> `stitch_audio.py` remap -> `word_timings.json` -> `subtitles/segment.py` phrase grouping -> `subtitles/ass_builder.py` styled ASS -> `build_captions.py` writes `captions.ass` -> `assemble_episode.py` burns it with ffmpeg's **`ass` filter and `shaping=complex`**.

**Why `ass` and complex shaping:** libass's default simple shaper mangles Devanagari conjuncts and matras (क्षत्रिय comes out as क्षत्रयि). Only the `ass` filter exposes `shaping`; complex shaping uses HarfBuzz. `tests/test_assemble_episode.py` renders a real frame to guard this.

Config knobs live in `channel_state.json`'s `captions` block: font **Noto Sans Devanagari** Bold (installed at `/usr/share/fonts/truetype/noto/`), size 58, no uppercasing, gold highlight `&H0017A0D4` (ASS `&H00BBGGRR` order), 2-4 words per caption, `max_chars_per_line` 22, `margin_v_ratio` 0.12, pop animation timing. The danda (।) is dropped from the displayed words.

Known limitation: timing can drift up to roughly 100 ms by a chunk's end due to `loudnorm`'s buffering; accepted.

Testing loop: `python3 scripts/build_captions.py <slug>` (fast, no re-encode), then render one frame (`ffmpeg ... -vf "ass=captions.ass:shaping=complex" -frames:v 1`) and look at it. Always check conjuncts (क्ष, त्र, श्र), the nukta (फ़, ज़) and i-matra placement.
