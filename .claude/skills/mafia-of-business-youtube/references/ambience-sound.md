# Ambience sound (no music)

There is no music anywhere in this pipeline. A sparse ambience layer
plays under the narration instead: wind, creak, distant thunder,
heartbeat, footsteps, silence sting, whisper, reveal sting, plus (since
2026-09-29) three soft scene-cut whooshes and six common story effects
(temple bell, fire crackle, water, drum, metal clang, paper rustle) — all
synthesized locally (`scripts/ambience/synth_library.py`, run once, never
in CI) so there is no licensing question at all.

## Channel settings for RedHat Engineer

This layer was built for a mystery channel. For the tech channel, `channel_state.json` `ambience.disable` switches off the mystery-atmosphere effects channel-wide (`wind`, `creak`, `heartbeat`, `footsteps`, `whisper`, `temple_bell`, `drum`), which removes the always-on cold-open wind and the pre-reveal heartbeat. What stays: the scene-cut whooshes, the `reveal_sting` at the climax, and keyword cues for `distant_thunder`, `fire_crackle`, `water`, `metal_clang`, `paper_rustle` and `silence_sting` (technology-story words: forge, patent, lightning, river, hammer, gear, paper). An episode can switch an effect back on by listing it in `02_script/ambience_plan.json` `cues`.

## Auto placement (priority order)

1. `wind` — once at the very first beat (disabled on this channel, see above).
2. `reveal_sting` — at the first `climax_reveal`-section beat (skipped if that's the first beat).
3. `heartbeat` — two beats before the reveal (disabled on this channel).
4. Keyword cues — matched against each word/beat description against
   `channel_state.json`'s `ambience.keywords` (a trailing `*` = prefix
   match). Capped at `ambience.max_keyword_cues` (10), at least
   `ambience.min_gap_seconds` (25s) apart.
5. Scene-cut whooshes — one on every beat after the first
   (`ambience.transitions`), peaking exactly on the cut (the clip's
   manifest `hit_offset`). Variant and a ±2 dB jitter come from the beat
   number. Skipped on `climax_reveal` beats (they get `reveal_sting`).
   Never removed by the min-gap rule.

Fixed cues (1-3) dedup only against each other, so a keyword cue can
never cost the climax its reveal sting.

Apart from the quiet cut whoosh, most beats get nothing — this is
intentional. Ambience is atmosphere, not a hit-every-beat sound design
pass. To turn whooshes off for one episode: `"disable": ["transition"]`.

## Override

`episodes/<slug>/02_script/ambience_plan.json`:

```json
{
  "mode": "add",
  "disable": ["whisper"],
  "cues": [
    {"sfx": "creak", "beat": 12},
    {"sfx": "heartbeat", "word": "silence", "occurrence": 1}
  ]
}
```

Levels: `ambience.bed_db` (-18) sets the whole ambience track relative to
the mastered voice.
