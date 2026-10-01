# Voice and audio

Voice: edge-tts `en-US-AvaMultilingualNeural` (female), locked in `channel_state.json`. Never change mid-video; log any change in `reports/changelog.md`.

Chunking: 2-3 sentences per edge-tts call, up to ~20 s each -- a 6-minute episode is roughly 15-25 generations. Long single generations drift in volume and slur, so chunking is not optional. `03_audio/chunk_plan.json`:
`{"chunks": [{"id": 1, "beats": [1, 2], "text": "..."}]}`.

Each chunk takes the rate/volume/pitch preset of the script section it opens in (`voice.settings.section_presets`): `cold_open` slow and deliberate, `setup` neutral, `rising_mystery` faster and more energetic, `climax_reveal` slower with weight, `aftermath` calm and quiet. Emotion is not via SSML (Microsoft blocks it server-side), only these three knobs.

Stitching gaps: `gap_within_section_seconds` 0.55, `gap_section_break_seconds` 1.0. Loudness -14 LUFS integrated, true peak <= -1 dBTP, 48 kHz.

Words per minute is ~140, so 700-950 words gives 5-7 minutes. After stitching, check the real runtime: under 300 s means add beats, over 420 s means cut.

`timings.json`: `{"total_seconds", "chunks": [...], "beats": [{"beat", "text", "section", "start", "end"}]}`. `word_timings.json`: `{"words": [{"text", "start", "end"}]}` (drives captions and keyword ambience cues).

Say it so the TTS can: spell out numbers that would be mispronounced ("nineteen forty-seven"), avoid acronyms it fumbles, and read the script aloud once before generating.

No music. See `ambience-sound.md` for the only other audio layer.
