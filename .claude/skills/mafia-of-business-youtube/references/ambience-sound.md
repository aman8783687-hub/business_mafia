# Ambience sound (no music)

There is no music anywhere in this pipeline. A sparse ambience layer plays under the narration: a soft whoosh on every scene cut, a reveal sting on the first [RAAZ] beat, and a few keyword effects. All effects are synthesized locally (`scripts/ambience/synth_library.py`, run once by hand) so there is no licensing question.

## Channel settings

`channel_state.json` `ambience.disable` switches off the mystery-atmosphere effects channel-wide (`wind`, `creak`, `heartbeat`, `footsteps`, `whisper`, `temple_bell`, `drum`, `distant_thunder`, `silence_sting`). What plays:

- `whoosh_soft_1/2/3` on every cut after the first (skipped on `raaz` beats).
- `reveal_sting` at the first `raaz` beat (`ambience.reveal_section`).
- Keyword cues from Devanagari stems (a trailing `*` = prefix match on NFC-normalized text, matras kept): `coin_clink` (पैसा, रुपये, कमाई, मुनाफ़ा, प्रॉफ़िट, सिक्के), `cash_register` (बिल, बिक्री, बेचना, ग्राहक, कस्टमर), `sizzle` (चाय, तंदूर, खाना, तेल, कड़ाही, आग), `crowd_murmur` (भीड़, बाज़ार, मंडी, मेला), `paper_rustle` (हिसाब, नोट, काग़ज़, किताब). Capped at `ambience.max_keyword_cues` (10), at least `ambience.min_gap_seconds` (20 s) apart.

Most beats get nothing; that is intentional. To turn whooshes off for one episode: `"disable": ["transition"]`.

## Override

`episodes/<slug>/02_script/ambience_plan.json`:

```json
{
  "mode": "add",
  "disable": ["sizzle"],
  "cues": [
    {"sfx": "coin_clink", "beat": 12},
    {"sfx": "cash_register", "word": "बिल", "occurrence": 1}
  ]
}
```

Level: `ambience.bed_db` (-18) sets the whole ambience track relative to the mastered voice.
