# Mafia of Business Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork the RedHat Engineer video pipeline into a local-only pipeline that makes 3-5 minute Hindi "how does X make money" story videos for the Mafia of Business channel, finalized into `output/<slug>/` with MongoDB state.

**Architecture:** Copy `../imagine_error_gh_action/` into this repo (working dir renamed `ImagineError/` -> `MafiaOfBusiness/`), then change only what language, length, branding and the local-only target require: `channel_state.json` config, a Hindi/length guard, Devanagari-safe captions/ambience/thumbnail, a `finalize_episode.py` stage replacing the Content Lab upload, and a rewritten agent skill (topics, Hindi script formula, SEO). An opencode agent driven by `cycle_prompt.md` writes each episode; Python stages produce it.

**Tech Stack:** Python 3.12, edge-tts 7.2.8 (`hi-IN-MadhurNeural`), FLUX.2 klein on Cloudflare Workers AI, ffmpeg (libass + HarfBuzz), Pillow 12 (raqm), pymongo/mongomock, pytest, numpy (sound synthesis only), opencode CLI.

**Spec:** `docs/superpowers/specs/2026-10-01-mafia-of-business-design.md`

## Global Constraints

- Repo root: `/home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action/`; source fork: `/home/devdevil/development/kaggle-experiment/imagine_error_gh_action/` -- **never modify the source repo**.
- Working dir `MafiaOfBusiness/`; skill `.claude/skills/mafia-of-business-youtube/`; MongoDB db `mafia_of_business_pipeline` (`MONGODB_DB` overrides).
- Local only: no Content Lab, no GitHub workflow, no slot logic, no raphael backend.
- Runtime: target 240 s, allowed 180-300 s, **hard cap 300 s**; fix by trimming the script, never by speeding the voice.
- Video 16:9, 1920x1080, 30 fps. Scene holds 5-7 s.
- Voice `hi-IN-MadhurNeural`; sections in order `[HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK]`.
- Palette black, white, gold `#D4A017` (ASS `&H0017A0D4`). Font Noto Sans Devanagari Bold `/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf`.
- Narration in Devanagari, numbers as words (no digits); whole script at least 90% Devanagari letters; no beat with more than 2 Latin-script words.
- Final package: `MafiaOfBusiness/output/<slug>/` = `mafia-of-business-<slug>.mp4`, `thumbnail.png`, `captions.srt`, `metadata.json`, `posting.md`.
- Secrets in `.env` (gitignored, exists already): `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MONGODB_URI`. Never print their values.
- Git author is the repo's local config (Yashraj Motwani). No Claude co-author trailer (operator's global rule).
- Run tests with `.venv/bin/python -m pytest -q` from the repo root.

## Review Focus

1. **Devanagari matras/nukta in keyword matching** -- 'मुनाफ़ा' must not collapse to 'मनफ'; NFC-normalized tokens with combining marks kept. Test in Task 6.
2. **Digits inside narration but not in beat numbers** -- `12. ...` beat index is fine, `10,000` in the text is rejected. Test in Task 4.
3. **Runtime exactly at the boundaries** (180.0 s, 300.0 s pass; 300.5 s fails) -- Test in Task 3.
4. **Re-running finalize** on an already finalized episode (intermediates already deleted) must succeed without duplicating anything. Test in Task 8.
5. **A thumbnail title whose accent word carries punctuation or the ₹ sign** (`₹40 लाख?` with accent `₹40`) must still colour the accent word. Test in Task 7.

---

### Task 1: Fork the RedHat pipeline into this repo

**Files:**
- Create (copied): `make-video`, `README.md`, `AGENTS.md`, `tests/`, `.claude/skills/mafia-of-business-youtube/`, `MafiaOfBusiness/{channel_state.json,cycle_prompt.md,scripts/,brand/ambience/,seed/,reports/,episodes/.gitkeep}`
- Delete after copy: `MafiaOfBusiness/scripts/publish_all.py`, `MafiaOfBusiness/scripts/publish_content_lab.py`, `MafiaOfBusiness/scripts/scenes/raphael_orchestrator.py`, `tests/test_publish_content_lab.py`, `tests/test_raphael_orchestrator.py`
- Modify: `tests/conftest.py`, `tests/test_state_db.py`, `tests/test_generate_scenes.py`, `MafiaOfBusiness/scripts/generate_scenes.py`, `MafiaOfBusiness/scripts/state_db.py`, `MafiaOfBusiness/scripts/build_ambience.py`, `MafiaOfBusiness/seed/topic_bank.seed.json`, `MafiaOfBusiness/reports/*.md`

**Interfaces:**
- Produces: the full RedHat test suite passing in this repo with paths under `MafiaOfBusiness/`; `state_db.DEFAULT_DB_NAME == "mafia_of_business_pipeline"`.

- [ ] **Step 1: Copy the source tree**

```bash
cd /home/devdevil/development/kaggle-experiment
SRC=imagine_error_gh_action; DST=mafia_of_business_gh_action
cp $SRC/make-video $SRC/README.md $SRC/AGENTS.md $DST/
rsync -a --exclude __pycache__ $SRC/tests/ $DST/tests/
mkdir -p $DST/.claude/skills
rsync -a $SRC/.claude/skills/redhat-engineer-youtube/ $DST/.claude/skills/mafia-of-business-youtube/
rsync -a --exclude __pycache__ --exclude .scratch --exclude .run_episode.lock \
  --exclude '/episodes/*/' --exclude '/brand/host/' --exclude '/brand/style_reference/' \
  $SRC/ImagineError/ $DST/MafiaOfBusiness/
cd $DST
rm MafiaOfBusiness/scripts/publish_all.py MafiaOfBusiness/scripts/publish_content_lab.py \
   MafiaOfBusiness/scripts/scenes/raphael_orchestrator.py \
   tests/test_publish_content_lab.py tests/test_raphael_orchestrator.py
ls MafiaOfBusiness/brand/host MafiaOfBusiness/episodes
```

Expected: `brand/host` lists only `host-reference-clean.jpeg` (the approved boss stickman, already committed); `episodes` holds only `.gitkeep`.

- [ ] **Step 2: Rename paths and the DB name**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action
grep -rl "ImagineError" make-video README.md AGENTS.md tests MafiaOfBusiness .claude | xargs sed -i 's/ImagineError/MafiaOfBusiness/g'
sed -i 's/DEFAULT_DB_NAME = "imagine_error_pipeline"/DEFAULT_DB_NAME = "mafia_of_business_pipeline"/' MafiaOfBusiness/scripts/state_db.py
sed -i 's/AMBIENCE_DIR = WORKSPACE.parent \/ "MafiaOfBusiness" \/ "brand" \/ "ambience" if False else WORKSPACE \/ "brand" \/ "ambience"/AMBIENCE_DIR = WORKSPACE \/ "brand" \/ "ambience"/' MafiaOfBusiness/scripts/build_ambience.py
grep -n "AMBIENCE_DIR =" MafiaOfBusiness/scripts/build_ambience.py
```

Expected: `AMBIENCE_DIR = WORKSPACE / "brand" / "ambience"`.

- [ ] **Step 3: Empty the seed so RedHat topics never reach the new DB**

`state_db.get_db()` seeds the topic bank on first contact with an empty DB, so this must happen before anything talks to MongoDB. Overwrite `MafiaOfBusiness/seed/topic_bank.seed.json` with:

```json
{"queued": []}
```

(Task 10 fills it with Hindi topics.)

- [ ] **Step 4: Reset reports**

Overwrite `MafiaOfBusiness/reports/changelog.md`:

```markdown
# Changelog

## 2026-10-01 -- forked from RedHat Engineer

This repo was forked from `../imagine_error_gh_action/` (the RedHat Engineer
pipeline) for the Hindi channel Mafia of Business. Design:
`docs/superpowers/specs/2026-10-01-mafia-of-business-design.md`. Local only:
no Content Lab upload, no GitHub Actions; finished videos go to
`MafiaOfBusiness/output/<slug>/`, state to MongoDB `mafia_of_business_pipeline`.
```

Overwrite `MafiaOfBusiness/reports/experiments.md`:

```markdown
# Experiments

None yet.
```

- [ ] **Step 5: Drop the raphael backend from scene dispatch**

In `MafiaOfBusiness/scripts/generate_scenes.py` replace the backend selection block:

```python
    if backend == "flux":
        from scenes import flux_orchestrator as orchestrator
    elif backend == "raphael":
        from scenes import raphael_orchestrator as orchestrator
    elif backend == "cloudflare":
        from scenes import cloudflare_orchestrator as orchestrator
    else:
        raise SystemExit(f"Unknown IMAGE_BACKEND {backend!r} (use 'flux', 'raphael' or 'cloudflare')")
```

with:

```python
    if backend == "flux":
        from scenes import flux_orchestrator as orchestrator
    elif backend == "cloudflare":
        from scenes import cloudflare_orchestrator as orchestrator
    else:
        raise SystemExit(f"Unknown IMAGE_BACKEND {backend!r} (use 'flux' or 'cloudflare')")
```

In `tests/test_generate_scenes.py` replace `test_backend_defaults_to_flux_and_can_be_switched` with:

```python
def test_backend_defaults_to_flux_and_can_be_switched(monkeypatch):
    from scenes import cloudflare_orchestrator, flux_orchestrator

    calls = []
    monkeypatch.setattr(flux_orchestrator, "generate_episode_scenes",
                        lambda *a: calls.append("flux") or ([1], []))
    monkeypatch.setattr(cloudflare_orchestrator, "generate_episode_scenes",
                        lambda *a: calls.append("cloudflare") or ([1], []))

    monkeypatch.setattr(generate_scenes.env_loader, "load_env", lambda: {})
    monkeypatch.delenv("IMAGE_BACKEND", raising=False)
    assert generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1]) == ([1], [])
    monkeypatch.setenv("IMAGE_BACKEND", "")
    generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1])
    monkeypatch.setenv("IMAGE_BACKEND", "cloudflare")
    generate_scenes.generate_episode_scenes("ep", "plan.json", "out", [1])
    assert calls == ["flux", "flux", "cloudflare"]
```

In `tests/test_state_db.py` replace `test_default_db_name_is_imagine_error` with:

```python
def test_default_db_name_is_mafia_of_business(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost/ignored")
    assert state_db.DEFAULT_DB_NAME == "mafia_of_business_pipeline"
```

- [ ] **Step 6: Create the venv and run the suite**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action
python3 -m venv .venv
.venv/bin/pip install -q edge-tts pymongo requests pillow pytest mongomock numpy
.venv/bin/python -m pytest -q
```

Expected: all tests pass (RedHat config is still in place, so channel-value assertions still hold).

- [ ] **Step 7: Commit**

```bash
git add -A
git status --short | grep -E "\.env$|output/|episodes/.+/" && echo "STOP: secret or media staged" || true
git commit -m "Fork RedHat Engineer pipeline into MafiaOfBusiness (local only)"
```

---

### Task 2: Channel config, voice and boss stickman prompts

**Files:**
- Modify: `MafiaOfBusiness/channel_state.json` (full rewrite)
- Modify: `MafiaOfBusiness/scripts/scenes/flux_orchestrator.py:50-53` (`REFERENCE_INSTRUCTION`), module docstring line 2-3
- Modify: `tests/test_env_and_prompt_builder.py`, `tests/test_generate_narration_chunks.py`, `tests/test_stitch_audio.py`
- Test: `tests/test_channel_state.py` (new)

**Interfaces:**
- Produces (config keys later tasks read): `voice.voice_id`, `voice.default_section` (`"khel"`), `voice.settings.section_presets.{hook,duniya,khel,raaz,sabak}`, `format.runtime_min_seconds` (180), `format.runtime_max_seconds` (300), `format.sections` (ordered list), `captions.font_family`, `captions.uppercase` (false), `captions.title`, `ambience.reveal_section` (`"raaz"`), `thumbnail.{font_path,accent_rgb,frame_rgb}`, `channel.name`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_channel_state.py`:

```python
import state
from scenes import flux_orchestrator, prompt_builder


S = state.load_state()


def test_channel_identity_and_language():
    assert S["channel"]["name"] == "Mafia of Business"
    assert S["channel"]["language"] == "hi"


def test_hindi_voice_and_sections():
    assert S["voice"]["voice_id"] == "hi-IN-MadhurNeural"
    assert S["format"]["sections"] == ["hook", "duniya", "khel", "raaz", "sabak"]
    assert set(S["voice"]["settings"]["section_presets"]) == set(S["format"]["sections"])
    assert S["voice"]["default_section"] == "khel"


def test_runtime_window_is_three_to_five_minutes():
    f = S["format"]
    assert (f["runtime_min_seconds"], f["target_runtime_seconds"], f["runtime_max_seconds"]) == (180, 240, 300)
    assert (f["scene_seconds_min"], f["scene_seconds_max"]) == (5, 7)


def test_gold_devanagari_captions():
    c = S["captions"]
    assert c["font_family"] == "Noto Sans Devanagari"
    assert c["highlight_color_ass"] == "&H0017A0D4"
    assert c["uppercase"] is False


def test_boss_stickman_style_lock():
    suffix = prompt_builder.STYLE_SUFFIX
    assert "black fedora with a gold band" in suffix
    assert "red" not in suffix.replace("no red", "")
    assert "black fedora" in flux_orchestrator.REFERENCE_INSTRUCTION
    assert "red fedora" not in flux_orchestrator.REFERENCE_INSTRUCTION
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_channel_state.py -q`
Expected: FAIL (`channel.name` is `RedHat Engineer`).

- [ ] **Step 3: Rewrite `MafiaOfBusiness/channel_state.json`**

Write the whole file:

```json
{
  "channel": {
    "name": "Mafia of Business",
    "handles": {"note": "Posting is done by hand by the operator from MafiaOfBusiness/output/<slug>/."},
    "autonomy": {
      "publish_without_approval": true,
      "authorized_by": "operator, 2026-10-01, explicit instruction to build this pipeline",
      "scope": "Producing one video per run into output/<slug>/ via scripts/run_episode.py. Does NOT authorize posting anywhere or skipping compliance-and-safety.md.",
      "known_risk": "No automated visual QA step exists for generated scenes -- see SKILL.md."
    },
    "timezone": "Asia/Kolkata",
    "publish_cadence": "1 video per ./make-video run",
    "language": "hi",
    "topic": "How everyday Indian businesses and people actually make money (chai tapri, dhaba, gym, tuition centre, wedding planner, politician...), told as a Hindi story, never as a math lecture."
  },
  "voice": {
    "provider": "edge-tts",
    "model": "edge-tts (Microsoft Edge online neural TTS, free, no API key)",
    "voice_id": "hi-IN-MadhurNeural",
    "fallback_voice_id": "hi-IN-SwaraNeural",
    "default_section": "khel",
    "settings": {
      "audio_profile": "Confident adult male Hindi narrator, an insider telling you how the game really works. Emotion via per-section rate/volume/pitch (custom SSML is blocked server-side).",
      "section_presets": {
        "hook":   {"rate": "-6%", "volume": "+0%", "pitch": "-2Hz", "note": "The rupee shock or question. Slow, weighty."},
        "duniya": {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz", "note": "The world: who this person is, what everyone thinks they earn."},
        "khel":   {"rate": "+6%", "volume": "+5%", "pitch": "+1Hz", "note": "The money game, stream by stream. Energetic."},
        "raaz":   {"rate": "-5%", "volume": "+0%", "pitch": "-1Hz", "note": "The secret trick. Slower, conspiratorial."},
        "sabak":  {"rate": "-8%", "volume": "-2%", "pitch": "-2Hz", "note": "Takeaway, comment question, next episode. Calm."}
      }
    },
    "seed": null,
    "max_chunk_seconds": 20,
    "chunking_rule": "2-3 sentences per chunk, saved as 03_audio/chunk_0001.mp3 ..., stitched by scripts/stitch_audio.py.",
    "status": "LOCKED",
    "notes": "Never change mid-video. Log any change in reports/changelog.md."
  },
  "style_lock": {
    "image_prompt_suffix": "hand-drawn black marker stickman on a clean white whiteboard, thick confident marker strokes, the stickman wears a black fedora with a gold band, a thin black outline suit jacket and a small solid gold tie, exactly two black dot eyes and NO mouth, calm neutral face, thin single-line stick limbs, no text, no letters, no numbers, one or two simple hand-drawn marker props only, money props drawn in gold, no arrows, lots of empty white space, only black, white and gold colors, no red, whiteboard explainer animation look",
    "negative_prompt": "color photo, photorealistic, 3d render, shading, gradients, text, letters, numbers, watermark, mouth, red, extra colors",
    "aspect": "16:9",
    "resolution": "1920x1080",
    "generation_resolution": "1024x576",
    "provider": "flux2-klein-9b-via-cloudflare-workers-ai",
    "model": "@cf/black-forest-labs/flux-2-klein-9b",
    "cfg_scale": 7.5,
    "steps": 20,
    "character_name": "The Boss",
    "reference_assets": [
      "MafiaOfBusiness/brand/host/host-reference-clean.jpeg -- the boss stickman (variant 1 of 4, seed 11, approved 2026-10-01), sent with every scene request."
    ],
    "generation_notes": "FLUX.2 klein takes the reference image, which keeps the boss on-model. More than 2 distinct characters per shot collapses to 1; write multi-character beats as shot/reverse-shot. Indian settings (chai stall, dhaba, mandi, auto, wedding tent) are described as one or two simple props.",
    "status": "LOCKED"
  },
  "audio": {
    "target_lufs": -14.0,
    "true_peak_db": -1.0,
    "trim_silence_db": "-50dB",
    "internal_silence_min_duration_seconds": 0.3,
    "gap_within_section_seconds": 0.4,
    "gap_section_break_seconds": 0.8,
    "fade_seconds": 0.02,
    "pacing_note": "Tighter than RedHat (0.55/1.0): a 4-minute video keeps momentum."
  },
  "ambience": {
    "enabled": true,
    "bed_db": -18,
    "min_gap_seconds": 20.0,
    "max_keyword_cues": 10,
    "reveal_section": "raaz",
    "keywords": {
      "coin_clink": ["पैस*", "रुपय*", "रुपए", "कमाई", "कमात*", "मुनाफ़*", "मुनाफा", "प्रॉफ़िट", "प्रॉफिट", "सिक्क*"],
      "cash_register": ["बिल", "बिक्री", "बेच*", "ग्राहक*", "कस्टमर*"],
      "sizzle": ["चाय", "तंदूर", "खाना", "तेल", "कड़ाही", "आग"],
      "crowd_murmur": ["भीड़", "बाज़ार", "बाजार", "मंडी", "मेला"],
      "paper_rustle": ["हिसाब", "नोट*", "कागज़*", "कागज*", "किताब*"]
    },
    "disable": ["wind", "creak", "heartbeat", "footsteps", "whisper", "temple_bell", "drum", "distant_thunder", "silence_sting"],
    "note": "No music. Soft whoosh on every scene cut, a reveal sting on the first [RAAZ] beat, sparse money/food/market keyword cues (Devanagari stems, * = prefix).",
    "transitions": {
      "enabled": true,
      "variants": ["whoosh_soft_1", "whoosh_soft_2", "whoosh_soft_3"],
      "gain_jitter_db": 2.0,
      "skip_sections": ["raaz"],
      "note": "Skipped on raaz beats, which get reveal_sting on the first one."
    }
  },
  "format": {
    "target_runtime_seconds": 240,
    "runtime_min_seconds": 180,
    "runtime_max_seconds": 300,
    "runtime_note": "Hard cap 300 s: stitch_audio.py and finalize_episode.py fail outside 180-300 s. Fix by trimming the script, never by speeding the voice.",
    "sections": ["hook", "duniya", "khel", "raaz", "sabak"],
    "words_per_minute": 140,
    "words_per_minute_note": "Measured 2026-10-01: hi-IN-MadhurNeural at default rate speaks ~140 Hindi words/min. Budget ~480-600 words for 240 s.",
    "scene_seconds_min": 5,
    "scene_seconds_max": 7,
    "fps": 30,
    "zoom_delta": 0.05,
    "animation_stage": "enabled",
    "animation_stage_note": "Ken Burns push in/out per scene via ffmpeg zoompan; direction from shotlist 'motion', else alternating.",
    "no_intro_outro": "No intro sting or outro card. The hook beat is the first scene."
  },
  "captions": {
    "enabled": true,
    "engine": "ass_libass",
    "title": "Mafia of Business animated captions",
    "font_family": "Noto Sans Devanagari",
    "font_family_note": "Installed at /usr/share/fonts/truetype/noto/; libass + HarfBuzz shape conjuncts and matras.",
    "fonts_dir": null,
    "font_size": 58,
    "bold": true,
    "uppercase": false,
    "max_chars_per_line": 22,
    "primary_color_ass": "&H00FFFFFF",
    "highlight_color_ass": "&H0017A0D4",
    "highlight_color_note": "Gold #D4A017 in ASS &H00BBGGRR order.",
    "outline_color_ass": "&H00000000",
    "outline_width": 3.5,
    "shadow_depth": 1.2,
    "alignment": 2,
    "margin_v_ratio": 0.12,
    "safe_margin_side_px": 80,
    "max_words_per_caption": 4,
    "min_words_per_caption": 2,
    "max_gap_within_phrase_seconds": 0.2,
    "pop_scale_percent": 115,
    "pop_duration_ms": 120,
    "settle_duration_ms": 100,
    "animation_style": "pop_and_highlight"
  },
  "thumbnail": {
    "font_path": "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf",
    "accent_rgb": [212, 160, 23],
    "frame_rgb": [212, 160, 23],
    "text_rgb": [255, 255, 255],
    "outline_rgb": [17, 17, 17]
  },
  "counters": {"episodes_published": 0, "buffer_ready": 0},
  "active_experiment": null,
  "baselines": {
    "ctr_30d": null,
    "avg_view_duration_30d": null,
    "baselines_note": "Filled by the operator from YouTube Studio; never invented by the agent."
  }
}
```

- [ ] **Step 4: Update the flux reference instruction**

In `MafiaOfBusiness/scripts/scenes/flux_orchestrator.py` replace:

```python
REFERENCE_INSTRUCTION = (
    "The stickman host is the exact same character as in the reference image "
    "(same red fedora, two dot eyes, no mouth, plain stick body). "
)
```

with:

```python
REFERENCE_INSTRUCTION = (
    "The stickman host is the exact same character as in the reference image "
    "(same black fedora with a gold band, thin suit outline, gold tie, two dot eyes, no mouth). "
)
```

and in its docstring replace `conditioned on RedHat Engineer's host reference image so the\nred-fedora stickman` with `conditioned on Mafia of Business's host reference image so the\nboss stickman`.

- [ ] **Step 5: Update the tests that pinned RedHat values**

`tests/test_env_and_prompt_builder.py`: in `test_channel_state_has_no_music_config` change `== 360` to `== 240` and `== "RedHat Engineer"` to `== "The Boss"`.

`tests/test_generate_narration_chunks.py`: replace `test_voice_id_matches_channel_state` with:

```python
def test_voice_id_matches_channel_state():
    assert gnc.VOICE == gnc.STATE["voice"]["voice_id"] == "hi-IN-MadhurNeural"
```

`tests/test_stitch_audio.py`: in `test_config_pulled_from_channel_state` change `0.55` to `0.4` and `1.0` to `0.8`.

- [ ] **Step 6: Run the suite**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Mafia of Business channel config: Hindi voice, 3-5 min format, boss stickman, gold captions"
```

---

### Task 3: Section-agnostic narration and the runtime guard

**Files:**
- Modify: `MafiaOfBusiness/scripts/generate_narration_chunks.py` (default section from config)
- Modify: `MafiaOfBusiness/scripts/stitch_audio.py` (add `check_runtime`, call it in `main`)
- Test: `tests/test_generate_narration_chunks.py`, `tests/test_stitch_audio.py`

**Interfaces:**
- Consumes: `voice.default_section`, `format.runtime_min_seconds`, `format.runtime_max_seconds` (Task 2).
- Produces: `stitch_audio.check_runtime(total_seconds: float, min_s: float, max_s: float) -> str | None` (None = ok, else a one-line error message); `stitch_audio.main()` exits 3 when it returns a message. `generate_narration_chunks.DEFAULT_SECTION: str`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_stitch_audio.py`:

```python
def test_check_runtime_boundaries():
    assert stitch_audio.check_runtime(180.0, 180, 300) is None
    assert stitch_audio.check_runtime(300.0, 180, 300) is None
    msg = stitch_audio.check_runtime(300.5, 180, 300)
    assert "300.5" in msg and "trim the script" in msg
    msg = stitch_audio.check_runtime(170.0, 180, 300)
    assert "170.0" in msg and "too short" in msg


def test_runtime_limits_come_from_channel_state():
    assert (stitch_audio.RUNTIME_MIN, stitch_audio.RUNTIME_MAX) == (180, 300)
```

Append to `tests/test_generate_narration_chunks.py`:

```python
def test_hindi_sections_map_and_default_comes_from_config(tmp_path):
    script = tmp_path / "script.md"
    script.write_text("1. बिना सेक्शन वाली लाइन।\n[HOOK]\n2. एक कप चाय।\n[RAAZ]\n3. असली खेल।\n")
    mapping = gnc.beat_to_section_map(script)
    assert mapping == {1: "khel", 2: "hook", 3: "raaz"}
    assert gnc.DEFAULT_SECTION == "khel"
    assert set(gnc.SECTION_PRESETS) == {"hook", "duniya", "khel", "raaz", "sabak"}
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_stitch_audio.py tests/test_generate_narration_chunks.py -q`
Expected: FAIL (`check_runtime` missing; beat 1 maps to `rising_mystery`).

- [ ] **Step 3: Implement**

In `generate_narration_chunks.py` replace:

```python
DEFAULT_PRESET = SECTION_PRESETS.get("rising_mystery", {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"})
```

with:

```python
DEFAULT_SECTION = STATE["voice"]["default_section"]
DEFAULT_PRESET = SECTION_PRESETS.get(DEFAULT_SECTION, {"rate": "+0%", "volume": "+0%", "pitch": "+0Hz"})
```

and replace both remaining `"rising_mystery"` literals (`current_section = "rising_mystery"` and `section_map.get(first_beat, "rising_mystery")`) with `DEFAULT_SECTION`. Change the docstring's first line to `"""Synthesizes Mafia of Business's Hindi narration via edge-tts, one chunk at a`.

In `stitch_audio.py`, after `SCENE_SECONDS_MAX = ...` add:

```python
RUNTIME_MIN = STATE["format"]["runtime_min_seconds"]
RUNTIME_MAX = STATE["format"]["runtime_max_seconds"]


def check_runtime(total_seconds: float, min_s: float, max_s: float) -> str | None:
    """None when the narration fits the channel's runtime window, else the
    message the agent acts on. Over the cap the fix is a shorter script,
    never a faster voice (spec 4.3)."""
    if total_seconds > max_s:
        return (f"narration {total_seconds:.1f}s is over the {max_s:.0f}s cap: trim the script "
                f"(~{(total_seconds - max_s) * 140 / 60:.0f} words), then rerun narration and stitch")
    if total_seconds < min_s:
        return (f"narration {total_seconds:.1f}s is too short (minimum {min_s:.0f}s): "
                f"add a money stream to [KHEL], then rerun narration and stitch")
    return None
```

At the very end of `main()` (after the `word_timings` block) add:

```python
    runtime_error = check_runtime(total, RUNTIME_MIN, RUNTIME_MAX)
    if runtime_error:
        print(f"ERROR: {runtime_error}", file=sys.stderr)
        sys.exit(3)
```

(`sys` is already imported in `stitch_audio.py`; confirm with `grep -n "^import sys" MafiaOfBusiness/scripts/stitch_audio.py`, add `import sys` if absent.)

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Hindi section presets by config; enforce the 3-5 minute runtime window"
```

---

### Task 4: Hindi script guard (`check_script.py`)

**Files:**
- Create: `MafiaOfBusiness/scripts/check_script.py`
- Test: `tests/test_check_script.py`

**Interfaces:**
- Consumes: `format.sections` (Task 2).
- Produces: `check_script.check(script_text: str, sections: list[str]) -> list[str]` (list of problems; empty = ok). CLI `python3 scripts/check_script.py <slug>` exits 1 and prints problems. Task 9 runs it as a stage.

- [ ] **Step 1: Write the failing test**

Create `tests/test_check_script.py`:

```python
import check_script

SECTIONS = ["hook", "duniya", "khel", "raaz", "sabak"]

GOOD = """# चाय वाला
Target runtime: 4:00

[HOOK]
1. एक कप चाय दस रुपये की, पर उसमें मुनाफ़ा कितना?

[DUNIYA]
2. सुबह पाँच बजे रमेश अपनी टपरी खोलता है।

[KHEL]
3. दूध, चीनी और पत्ती मिलाकर लागत तीन रुपये आती है।

[RAAZ]
12. असली कमाई चाय से नहीं, साथ बिकने वाले बिस्कुट से होती है।

[SABAK]
13. आपके शहर में चाय कितने की है? कमेंट में बताइए।
"""


def test_good_script_passes():
    assert check_script.check(GOOD, SECTIONS) == []


def test_beat_numbers_are_not_digits_in_narration():
    # "12." is a beat index, not narration -- must not be flagged.
    assert not any("digit" in p for p in check_script.check(GOOD, SECTIONS))


def test_digits_in_narration_are_rejected():
    bad = GOOD.replace("लागत तीन रुपये", "लागत 3 रुपये")
    problems = check_script.check(bad, SECTIONS)
    assert any("beat 3" in p and "digit" in p for p in problems)


def test_english_sentence_is_rejected():
    bad = GOOD.replace("सुबह पाँच बजे रमेश अपनी टपरी खोलता है।",
                       "Every morning Ramesh opens his tea stall at five.")
    problems = check_script.check(bad, SECTIONS)
    assert any("beat 2" in p and "Devanagari" in p for p in problems)


def test_a_few_english_business_words_are_fine():
    ok = GOOD.replace("असली कमाई", "असली profit")
    assert check_script.check(ok, SECTIONS) == []


def test_missing_and_out_of_order_sections():
    missing = GOOD.replace("[RAAZ]\n", "")
    assert any("missing" in p and "RAAZ" in p for p in check_script.check(missing, SECTIONS))
    swapped = GOOD.replace("[DUNIYA]", "[TMP]").replace("[KHEL]", "[DUNIYA]").replace("[TMP]", "[KHEL]")
    assert any("order" in p for p in check_script.check(swapped, SECTIONS))
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_check_script.py -q`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_script'`.

- [ ] **Step 3: Implement**

Create `MafiaOfBusiness/scripts/check_script.py`:

```python
#!/usr/bin/env python3
"""Hindi script guard, run by run_episode.py before narration.

Fails an episode's 02_script/script.md when:
  - a section tag is missing or out of order ([HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK]);
  - a narration beat contains a digit (edge-tts reads digits badly in Hindi,
    so numbers are written as words: "दस हज़ार", not "10,000");
  - a beat has more than two Latin-script words (an English sentence slipped
    in; one or two English business words like "profit" are fine);
  - the whole script is under 90% Devanagari letters.

Usage: python3 scripts/check_script.py <episode-slug>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
MIN_DEVANAGARI_RATIO = 0.9
MAX_LATIN_WORDS_PER_BEAT = 2

_TAG_RE = re.compile(r"^\[([A-Z_]+)\]\s*$")
_BEAT_RE = re.compile(r"^(\d+)\.\s+(.*)$")
_DIGIT_RE = re.compile(r"[0-9०-९]")
_LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")


def _devanagari_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha() or "ऀ" <= c <= "ॿ"]
    if not letters:
        return 1.0
    return sum("ऀ" <= c <= "ॿ" for c in letters) / len(letters)


def check(script_text: str, sections: list[str]) -> list[str]:
    problems: list[str] = []
    seen: list[str] = []
    narration: list[str] = []
    for raw in script_text.splitlines():
        line = raw.strip()
        tag = _TAG_RE.match(line)
        if tag:
            seen.append(tag.group(1).lower())
            continue
        beat = _BEAT_RE.match(line)
        if not beat:
            continue
        number, text = beat.group(1), beat.group(2)
        narration.append(text)
        if _DIGIT_RE.search(text):
            problems.append(f"beat {number}: contains a digit -- write numbers as Hindi words: {text}")
        latin = _LATIN_WORD_RE.findall(text)
        if len(latin) > MAX_LATIN_WORDS_PER_BEAT:
            problems.append(f"beat {number}: {len(latin)} English words -- write it in Hindi Devanagari: {text}")
    ratio = _devanagari_ratio(" ".join(narration))
    if ratio < MIN_DEVANAGARI_RATIO:
        problems.append(f"script is only {ratio:.0%} Devanagari letters (minimum 90%)")
    for name in sections:
        if name not in seen:
            problems.append(f"missing section [{name.upper()}]")
    present = [s for s in seen if s in sections]
    if present != [s for s in sections if s in present]:
        problems.append(f"sections out of order: {' '.join(s.upper() for s in present)} "
                        f"(expected {' '.join(s.upper() for s in sections)})")
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/check_script.py <episode-slug>")
        return 1
    script = WORKSPACE / "episodes" / sys.argv[1] / "02_script" / "script.md"
    problems = check(script.read_text(), load_state()["format"]["sections"])
    for p in problems:
        print(f"SCRIPT PROBLEM: {p}")
    if not problems:
        print("script.md ok")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_check_script.py -q`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "Add Hindi script guard: section order, no digits, Devanagari ratio"
```

---

### Task 5: Devanagari captions

**Files:**
- Modify: `MafiaOfBusiness/scripts/subtitles/ass_builder.py` (title from config; strip danda `।` from displayed words)
- Test: `tests/test_captions.py`

**Interfaces:**
- Consumes: `captions.title`, `captions.uppercase`, `captions.font_family` (Task 2).
- Produces: `ass_builder.build_ass(phrases, config, width, height) -> str` (same signature).

- [ ] **Step 1: Write the failing tests**

In `tests/test_captions.py` change the existing assertion `assert "Title: RedHat Engineer animated captions" in ass` to `assert "Title: Mafia of Business animated captions" in ass` and add `"title": "Mafia of Business animated captions",` to that test's `config` dict. Then append:

```python
HINDI_CONFIG = {
    "title": "Mafia of Business animated captions",
    "font_family": "Noto Sans Devanagari", "font_size": 58, "bold": True, "uppercase": False,
    "max_chars_per_line": 22,
    "primary_color_ass": "&H00FFFFFF", "outline_color_ass": "&H00000000",
    "highlight_color_ass": "&H0017A0D4", "outline_width": 3.5, "shadow_depth": 1.2,
    "alignment": 2, "margin_v_ratio": 0.12, "safe_margin_side_px": 80,
    "pop_scale_percent": 115, "pop_duration_ms": 120, "settle_duration_ms": 100,
}


def _hindi_words():
    texts = ["एक", "कप", "चाय", "दस", "रुपये", "की।", "मुनाफ़ा", "कितना?"]
    return [{"text": t, "start": i * 0.3, "end": i * 0.3 + 0.25} for i, t in enumerate(texts)]


def test_devanagari_phrases_never_split_a_word():
    phrases = segment.segment_phrases(_hindi_words(), max_words=4, min_words=2, max_gap_seconds=0.2)
    flat = [w["text"] for p in phrases for w in p]
    assert flat == [w["text"] for w in _hindi_words()]
    assert all(len(p) <= 4 for p in phrases)


def test_devanagari_ass_keeps_text_and_font_and_drops_danda():
    phrases = segment.segment_phrases(_hindi_words(), max_words=4, min_words=2, max_gap_seconds=0.2)
    ass = ass_builder.build_ass(phrases, HINDI_CONFIG, 1920, 1080)
    assert "Style: Caption,Noto Sans Devanagari,58" in ass
    assert "मुनाफ़ा" in ass and "रुपये" in ass
    assert "।" not in ass
    assert "\\c&H0017A0D4" in ass
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_captions.py -q`
Expected: FAIL (title hard-coded to RedHat; `।` present).

- [ ] **Step 3: Implement**

In `ass_builder.py`, change the header line `Title: RedHat Engineer animated captions` to `Title: {config.get('title', 'animated captions')}`.

Replace the `display = ...` line inside the word loop:

```python
                    display = _escape(w["text"].upper() if uppercase else w["text"])
```

with:

```python
                    shown = w["text"].replace("।", "").strip() or w["text"]
                    display = _escape(shown.upper() if uppercase else shown)
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/python -m pytest tests/test_captions.py -q`
Expected: all pass.

- [ ] **Step 5: Render a real caption frame and look at it**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action
S=MafiaOfBusiness/.scratch; mkdir -p $S
.venv/bin/python - <<'EOF'
import json, sys
sys.path.insert(0, "MafiaOfBusiness/scripts")
from state import load_state
from subtitles import segment, ass_builder
cfg = load_state()["captions"]
words = [{"text": t, "start": i*0.4, "end": i*0.4+0.35} for i, t in enumerate(
    ["क्षत्रिय", "श्रीमान", "प्रॉफ़िट", "मुनाफ़ा", "ज़्यादा", "कमाई।"])]
ph = segment.segment_phrases(words, 4, 2, 0.2)
open("MafiaOfBusiness/.scratch/test.ass", "w").write(ass_builder.build_ass(ph, cfg, 1920, 1080))
EOF
ffmpeg -loglevel error -y -f lavfi -i color=c=gray:s=1920x1080:d=3 -vf "subtitles=$S/test.ass" -frames:v 1 -ss 0.5 $S/caption_frame.png
```

Open `MafiaOfBusiness/.scratch/caption_frame.png` (Read tool) and confirm: conjuncts क्ष, त्र, श्र render joined (no dotted circles, no boxes), the nukta in फ़/ज़ sits under the letter, one word is gold. If anything renders as boxes, stop and report -- do not change fonts silently.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Devanagari captions: config title, drop danda, gold highlight"
```

---

### Task 6: Hindi-aware ambience (keywords, reveal section, new sounds)

**Files:**
- Modify: `MafiaOfBusiness/scripts/ambience/planner.py` (`_norm`, `_keyword_index`, reveal section, per-beat tokenizer)
- Modify: `MafiaOfBusiness/scripts/ambience/synth_library.py` (append 4 effects)
- Regenerate: `MafiaOfBusiness/brand/ambience/{coin_clink,cash_register,sizzle,crowd_murmur}.wav`, `manifest.json`
- Test: `tests/test_ambience_planner.py`

**Interfaces:**
- Consumes: `ambience.keywords`, `ambience.reveal_section`, `ambience.disable` (Task 2).
- Produces: `planner._norm(word: str) -> str` (NFC, lowercase, keeps letters, digits, `$` and Unicode combining marks); `planner.auto_cues` reads `config.get("reveal_section", "climax_reveal")`. Manifest gains effects `coin_clink`, `cash_register`, `sizzle`, `crowd_murmur`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_ambience_planner.py`:

```python
HINDI_CONFIG = {
    "keywords": {"coin_clink": ["पैस*", "मुनाफ़*"], "sizzle": ["चाय"]},
    "disable": ["wind", "heartbeat"],
    "reveal_section": "raaz",
}


def test_norm_keeps_devanagari_matras_and_nukta():
    assert planner._norm("मुनाफ़ा,") == planner._norm("मुनाफ़ा")
    assert planner._norm("मुनाफ़ा") not in ("", "मनफ")
    assert planner._norm("जानेंगे") == "जानेंगे"
    # precomposed फ़ (U+095E) and फ + nukta compare equal
    assert planner._norm("फ़") == planner._norm("फ़")


def test_hindi_keyword_cues_fire_on_word_timings():
    beats = [{"beat": 1, "text": "x", "section": "khel", "start": 0.0, "end": 40.0}]
    words = [{"text": "पैसे", "start": 1.0, "end": 1.3}, {"text": "चाय।", "start": 30.0, "end": 30.4}]
    cues = planner.plan(beats, words, HINDI_CONFIG, None, available={"coin_clink", "sizzle", "wind", "heartbeat"})
    assert [(c["sfx"], c["t"]) for c in cues if c.get("keyword")] == [("coin_clink", 1.0), ("sizzle", 30.0)]


def test_hindi_keywords_fall_back_to_beat_text():
    beats = [{"beat": 1, "text": "असली मुनाफ़ा यहाँ है", "section": "khel", "start": 0.0, "end": 5.0}]
    cues = planner.plan(beats, None, HINDI_CONFIG, None, available={"coin_clink", "sizzle", "wind", "heartbeat"})
    assert any(c["sfx"] == "coin_clink" for c in cues)


def test_reveal_sting_follows_configured_section():
    beats = [
        {"beat": i, "text": "x", "section": s, "start": (i - 1) * 10.0, "end": i * 10.0 - 1}
        for i, s in enumerate(["hook", "duniya", "khel", "raaz", "sabak"], start=1)
    ]
    cues = planner.plan(beats, None, HINDI_CONFIG, None, available={"reveal_sting", "wind", "heartbeat"})
    assert [c["t"] for c in cues if c["sfx"] == "reveal_sting"] == [30.0]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_ambience_planner.py -q`
Expected: the 4 new tests FAIL; existing tests pass.

- [ ] **Step 3: Implement planner changes**

In `planner.py` add `import unicodedata` next to `import re`, and replace `_norm` and `_keyword_index`:

```python
def _norm(word: str) -> str:
    """NFC, lowercase, keep letters/digits/$ and combining marks. Combining
    marks matter: Devanagari matras and the nukta are category M, and
    dropping them turns 'मुनाफ़ा' into 'मनफ'."""
    word = unicodedata.normalize("NFC", word.lower())
    return "".join(c for c in word if c.isalnum() or c == "$" or unicodedata.category(c).startswith("M"))


def _keyword_index(keywords: dict[str, list[str]]) -> list[tuple[re.Pattern, str]]:
    index = []
    for sfx, patterns in keywords.items():
        for pat in patterns:
            if pat.endswith("*"):
                regex = re.compile(f"^{re.escape(_norm(pat[:-1]))}")
            else:
                regex = re.compile(f"^{re.escape(_norm(pat))}$")
            index.append((regex, sfx))
    return index
```

In `auto_cues`, replace:

```python
    # 2. Reveal sting at the first climax_reveal beat (skip if it's the first beat).
    reveal_beat = next((b for b in beats if b["section"] == "climax_reveal"), None)
```

with:

```python
    # 2. Reveal sting at the first reveal-section beat (skip if it's the first beat).
    reveal_section = config.get("reveal_section", "climax_reveal")
    reveal_beat = next((b for b in beats if b["section"] == reveal_section), None)
```

In the per-beat fallback replace `re.findall(r"[a-zA-Z']+", b.get("text", ""))` with `b.get("text", "").split()`.

- [ ] **Step 4: Run planner tests**

Run: `.venv/bin/python -m pytest tests/test_ambience_planner.py -q`
Expected: all pass.

- [ ] **Step 5: Add the four effects to the synth library**

In `synth_library.py`, after the last effect function and before `EFFECTS = {`, add (appended after the originals so the RNG stream for existing WAVs is unchanged):

```python
# --- Mafia of Business money/food/market effects (2026-10-01). Appended
# last so every earlier WAV stays byte-identical on regeneration. ---

def _coin_clink(duration=0.6) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    out = np.zeros(n)
    for start, f in ((0.0, 3100.0), (0.09, 4200.0), (0.17, 3600.0)):
        i0 = int(SR * start)
        tt = t[: n - i0]
        out[i0:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 18)
    return _peak_normalize(out)


def _cash_register(duration=0.9) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    click = RNG.standard_normal(n) * np.exp(-t * 60) * 0.6
    bell_start = int(SR * 0.12)
    tb = t[: n - bell_start]
    bell = np.zeros(n)
    bell[bell_start:] = (np.sin(2 * np.pi * 2600 * tb) + 0.5 * np.sin(2 * np.pi * 5200 * tb)) * np.exp(-tb * 6)
    return _peak_normalize(click + bell)


def _sizzle(duration=2.0) -> np.ndarray:
    n = int(SR * duration)
    noise = RNG.standard_normal(n)
    hiss = noise - np.convolve(noise, np.ones(6) / 6, mode="same")
    crackle = (RNG.random(n) > 0.9993) * RNG.uniform(0.5, 1.0, n)
    return _peak_normalize((hiss * 0.5 + crackle) * _envelope(n, int(SR * 0.2), int(SR * 0.6)))


def _crowd_murmur(duration=3.0) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    noise = RNG.standard_normal(n)
    babble = np.convolve(noise, np.ones(40) / 40, mode="same")
    swell = 0.6 + 0.4 * np.sin(2 * np.pi * 1.7 * t) * np.sin(2 * np.pi * 0.6 * t)
    return _peak_normalize(babble * swell * _envelope(n, int(SR * 0.5), int(SR * 0.8)))
```

and add to the end of the `EFFECTS` dict:

```python
    "coin_clink": (_coin_clink, -8.0, "two or three small coins clinking"),
    "cash_register": (_cash_register, -9.0, "a drawer click and a small register bell"),
    "sizzle": (_sizzle, -10.0, "a short hot-oil sizzle with a few crackles"),
    "crowd_murmur": (_crowd_murmur, -12.0, "a low market crowd murmur"),
```

Change the docstring's `Imagine Error's ambience sound library` to `the channel's ambience sound library`.

- [ ] **Step 6: Regenerate and verify old WAVs are unchanged**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action/MafiaOfBusiness
mkdir -p .scratch
md5sum brand/ambience/whoosh_soft_1.wav brand/ambience/reveal_sting.wav > .scratch/before.md5
../.venv/bin/python scripts/ambience/synth_library.py
md5sum -c .scratch/before.md5
python3 -c "import json; print(sorted(json.load(open('brand/ambience/manifest.json'))['effects']))"
```

Expected: `md5sum -c` prints `OK` for both; the effect list includes `cash_register`, `coin_clink`, `crowd_murmur`, `sizzle`. If an old WAV changed, a new function was inserted before the originals -- move it to the end.

- [ ] **Step 7: Run suite and commit**

```bash
cd .. && .venv/bin/python -m pytest -q
git add -A && git commit -m "Hindi-aware ambience: Devanagari keyword matching, raaz reveal sting, money/food/market sounds"
```

---

### Task 7: Annotated "hisaab" thumbnail (Devanagari, gold)

**Files:**
- Modify: `MafiaOfBusiness/scripts/make_thumbnail.py`
- Modify: `MafiaOfBusiness/scripts/run_episode.py` (`thumbnail_args` passes annotations)
- Test: `tests/test_make_thumbnail.py` (new)

**Interfaces:**
- Consumes: `thumbnail.{font_path,accent_rgb,frame_rgb,text_rgb,outline_rgb}` (Task 2), `brand/host/host-reference-clean.jpeg`, `metadata.json` fields `thumbnail_text`, `thumbnail_accent_word`, `thumbnail_beat`, `thumbnail_annotations` (list of up to 4 short strings).
- Produces: `make_thumbnail.is_accent(word: str, accent_word: str | None) -> bool`; `render_annotated_thumbnail(words, accent_word, annotations, scene_path) -> PIL.Image` (default layout, spec 5.5); `render_scene_thumbnail(words, accent_word, scene_path) -> PIL.Image` and `render_host_thumbnail(words, accent_word) -> PIL.Image` (fallbacks). CLI: `title --accent-word W --scene P --annotation A [--annotation B ...] --out O`. `run_episode.thumbnail_args(episode_dir)` adds one `--annotation` per entry (max 4) before `--scene`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_make_thumbnail.py`:

```python
import json

from PIL import Image

import make_thumbnail as mt
import run_episode


def test_accent_match_ignores_trailing_punctuation_and_handles_rupee():
    assert mt.is_accent("₹40", "₹40")
    assert mt.is_accent("लाख?", "लाख")
    assert not mt.is_accent("चाय", "लाख")
    assert not mt.is_accent("चाय", None)


def _gold_pixels(img):
    gold = tuple(mt.ACCENT)
    return sum(1 for p in img.getdata() if all(abs(a - b) < 30 for a, b in zip(p, gold)))


def _scene(tmp_path):
    scene = tmp_path / "scene.png"
    Image.new("RGB", (1024, 576), (255, 255, 255)).save(scene)
    return scene


def test_annotated_layout_draws_annotations_with_gold_arrows(tmp_path):
    scene = _scene(tmp_path)
    bare = mt.render_annotated_thumbnail(["पेट्रोल", "पंप", "का", "हिसाब"], "हिसाब", [], scene)
    noted = mt.render_annotated_thumbnail(["पेट्रोल", "पंप", "का", "हिसाब"], "हिसाब",
                                          ["₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "कैश फ़्लो"], scene)
    assert noted.size == (1280, 720)
    assert _gold_pixels(noted) > _gold_pixels(bare) + 1500  # four gold arrows
    dark = lambda im: sum(1 for p in im.getdata() if max(p) < 60)
    assert dark(noted) > dark(bare) + 3000  # four black labels


def test_annotated_layout_survives_long_labels_and_missing_scene(tmp_path):
    img = mt.render_annotated_thumbnail(["ढाबे", "का", "हिसाब"], None,
                                        ["दाल = हीरो, बाक़ी सब साइड", "₹1.5 का पापड़ ₹10 में"], None)
    assert img.size == (1280, 720)


def test_scene_and_host_fallbacks_render(tmp_path):
    assert mt.render_scene_thumbnail(["असली", "खेल"], None, _scene(tmp_path)).size == (1280, 720)
    plain = mt.render_host_thumbnail(["चाय", "में", "₹70?"], None)
    accented = mt.render_host_thumbnail(["चाय", "में", "₹70?"], "₹70?")
    assert _gold_pixels(accented) > _gold_pixels(plain) + 1000


def test_latin_letters_are_rejected_but_digits_and_rupee_pass():
    import pytest
    mt.check_no_latin(["₹4.5/लीटर", "पहले पेमेंट"])
    with pytest.raises(SystemExit, match="ईएमआई"):
        mt.check_no_latin(["लोन EMI"])


def test_title_bottom_includes_matras_below_the_line():
    from PIL import ImageDraw, ImageFont
    img = Image.new("RGB", (1280, 300), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(mt.FONT_BOLD, 100)
    bottom = mt._draw_title(draw, ["पेट्रोल"], font, 10, 10, 120, None, fill=(0, 0, 0), stroke=0)
    rows_with_ink = [y for y in range(300) if any(img.getpixel((x, y))[0] < 128 for x in range(0, 700, 2))]
    assert bottom >= max(rows_with_ink)


def test_devanagari_font_is_shaped_not_tofu():
    from PIL import ImageFont, features
    assert features.check("raqm"), "Pillow needs raqm to shape Devanagari"
    font = ImageFont.truetype(mt.FONT_BOLD, 80)
    # 'क्ष' shaped is ONE conjunct, narrower than क + ष side by side
    assert font.getlength("क्ष") < font.getlength("क") + font.getlength("ष")


def test_thumbnail_args_pass_up_to_four_annotations_before_scene(tmp_path):
    ep = tmp_path / "ep"
    (ep / "08_publish").mkdir(parents=True)
    (ep / "05_scenes").mkdir()
    (ep / "05_scenes" / "scene_0001.png").write_bytes(b"png")
    notes = ["₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "कैश फ़्लो", "पाँचवाँ"]
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(
        {"thumbnail_text": "पेट्रोल पंप का हिसाब", "thumbnail_annotations": notes}, ensure_ascii=False))
    args = run_episode.thumbnail_args(ep)
    passed = [args[k + 1] for k, a in enumerate(args) if a == "--annotation"]
    assert passed == notes[:4]
    assert args[-2] == "--scene"
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_make_thumbnail.py -q`
Expected: FAIL (`is_accent`, `ACCENT`, `render_annotated_thumbnail` missing).

- [ ] **Step 3: Implement `make_thumbnail.py`**

Replace the whole file with:

```python
#!/usr/bin/env python3
"""
Locked Mafia of Business thumbnail template (spec 5.5): a "hisaab"
infographic on a white whiteboard -- title band on top ("पेट्रोल पंप का
हिसाब", accent word in gold, gold underline), the episode's scene in the
centre, 3-4 money annotations left and right with gold arrows pointing in,
gold frame. Black/white/gold only.

Usage:
    python3 make_thumbnail.py "पेट्रोल पंप का हिसाब" --accent-word हिसाब \
        --annotation "₹4.5/लीटर" --annotation "लोन ईएमआई" \
        --scene .../05_scenes/scene_0001.png --out .../08_publish/thumbnail.png

Without --annotation: the scene full-bleed with the title on it. Without a
scene: the boss stickman on the left, title on the right.
"""
import argparse
import math
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from state import load_state  # noqa: E402

HOST_IMAGE = ROOT / "brand" / "host" / "host-reference-clean.jpeg"
_T = load_state()["thumbnail"]
FONT_BOLD = _T["font_path"]

CANVAS_W, CANVAS_H = 1280, 720
ACCENT = tuple(_T["accent_rgb"])
FRAME = tuple(_T["frame_rgb"])
TEXT = tuple(_T["text_rgb"])
OUTLINE = tuple(_T["outline_rgb"])
WHITE = (255, 255, 255)
_TRAILING = ":,.?!।"
_METRIC = "कHg"  # Devanagari headline + matras are taller than Latin "Hg"

# Annotated layout geometry.
TITLE_BOX = (50, 24, CANVAS_W - 50, 150)          # x0, y0, x1, y1
SCENE_BOX = (340, 175, CANVAS_W - 340, CANVAS_H - 30)
LABEL_MAX_W = 290
# (label anchor, arrow target); left labels anchor on their left edge, right on their right edge.
ANNOTATION_SLOTS = [
    ((40, 230), (SCENE_BOX[0] + 30, 330)),
    ((CANVAS_W - 40, 230), (SCENE_BOX[2] - 30, 330)),
    ((40, 500), (SCENE_BOX[0] + 30, 520)),
    ((CANVAS_W - 40, 500), (SCENE_BOX[2] - 30, 520)),
]


def is_accent(word, accent_word):
    if not accent_word:
        return False
    return word.rstrip(_TRAILING) == accent_word.rstrip(_TRAILING)


def load_host_cutout():
    """Crop the host figure tightly out of its white-background reference."""
    im = Image.open(HOST_IMAGE).convert("RGB")
    bbox = im.convert("L").point(lambda p: 0 if p > 245 else 255).getbbox()
    if bbox:
        pad = 20
        l, t, r, b = bbox
        im = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))
    return im


def _line_h(font):
    box = font.getbbox(_METRIC)
    return box[3] - box[1]


def wrap_words(words, font, max_width, draw):
    """Greedy wrap into as many lines as needed - caller decides what counts as fitting."""
    lines, current = [], []
    for w in words:
        trial = current + [w]
        if draw.textlength(" ".join(trial), font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def fit_font(draw, words, max_width, max_height, font_path, start_size=140, min_size=32):
    """Largest size where the wrapped title fits the box in at most 2 lines;
    raises rather than silently dropping words."""
    size = start_size
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_words(words, font, max_width, draw)
        if len(lines) <= 2:
            total_h = _line_h(font) * len(lines) * 1.25
            widest = max(draw.textlength(line, font=font) for line in lines)
            if total_h <= max_height and widest <= max_width:
                return font, lines
        size -= 4
    raise SystemExit(f"Title '{' '.join(words)}' doesn't fit the template even at {min_size}px -- shorten it.")


def _draw_title(draw, lines, font, x0, y, step, accent_word, fill=None, stroke=10, center_width=None):
    """Draw the title; return the lowest drawn pixel row (matras below the
    line included), so anything placed under it never cuts through them."""
    bottom = y
    for line in lines:
        x = x0
        if center_width:
            x = x0 + (center_width - draw.textlength(line, font=font)) / 2
        bottom = max(bottom, draw.textbbox((x, y), line, font=font, stroke_width=stroke)[3])
        for w in line.split():
            color = ACCENT if is_accent(w, accent_word) else (fill or TEXT)
            draw.text((x, y), w, font=font, fill=color, stroke_width=stroke, stroke_fill=OUTLINE if fill is None else WHITE)
            x += draw.textlength(w + " ", font=font)
        y += step
    return bottom


def check_no_latin(texts):
    """Noto Sans Devanagari has no Latin letters (they render as boxes);
    digits, ₹ and punctuation are fine."""
    bad = [t for t in texts if re.search(r"[A-Za-z]", t)]
    if bad:
        raise SystemExit(f"Thumbnail text must be Devanagari (digits and ₹ are fine), "
                         f"e.g. EMI -> ईएमआई: {bad}")


def _arrow(draw, start, end, color, width=7, head=24):
    draw.line([start, end], fill=color, width=width)
    ang = math.atan2(end[1] - start[1], end[0] - start[0])
    for d in (2.6, -2.6):
        draw.line([end, (end[0] + head * math.cos(ang + d), end[1] + head * math.sin(ang + d))], fill=color, width=width)


def _label_font(draw, text):
    for size in range(48, 26, -2):
        font = ImageFont.truetype(FONT_BOLD, size)
        if draw.textlength(text, font=font) <= LABEL_MAX_W:
            return font
    return ImageFont.truetype(FONT_BOLD, 26)


def _fit_into(img, box):
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / img.width, (y1 - y0) / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)))
    return img, (x0 + (x1 - x0 - img.width) // 2, y0 + (y1 - y0 - img.height) // 2)


def render_annotated_thumbnail(words, accent_word, annotations, scene_path):
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), WHITE)
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = TITLE_BOX
    font, lines = fit_font(draw, words, x1 - x0, y1 - y0, FONT_BOLD, start_size=110, min_size=40)
    step = int(_line_h(font) * 1.2)
    bottom = _draw_title(draw, lines, font, x0, y0, step, accent_word, fill=OUTLINE, stroke=0, center_width=x1 - x0)
    draw.rectangle([CANVAS_W // 2 - 260, bottom + 8, CANVAS_W // 2 + 260, bottom + 16], fill=ACCENT)

    art = Image.open(scene_path).convert("RGB") if scene_path and Path(scene_path).exists() else load_host_cutout()
    art, pos = _fit_into(art, SCENE_BOX)
    canvas.paste(art, pos)

    for text, ((ax, ay), target) in zip(annotations[:4], ANNOTATION_SLOTS):
        lfont = _label_font(draw, text)
        w = draw.textlength(text, font=lfont)
        left_side = ax < CANVAS_W / 2
        x = ax if left_side else ax - w
        draw.text((x, ay), text, font=lfont, fill=OUTLINE, stroke_width=3, stroke_fill=WHITE)
        start = (x + w + 10, ay + _line_h(lfont) // 2 + 10) if left_side else (x - 10, ay + _line_h(lfont) // 2 + 10)
        _arrow(draw, start, target, ACCENT)

    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def render_scene_thumbnail(words, accent_word, scene_path):
    """Fallback without annotations: scene full-bleed, big white outlined title."""
    canvas = Image.open(scene_path).convert("RGB")
    scale = max(CANVAS_W / canvas.width, CANVAS_H / canvas.height)
    canvas = canvas.resize((int(canvas.width * scale) + 1, int(canvas.height * scale) + 1))
    left, top = (canvas.width - CANVAS_W) // 2, (canvas.height - CANVAS_H) // 2
    canvas = canvas.crop((left, top, left + CANVAS_W, top + CANVAS_H))
    draw = ImageDraw.Draw(canvas)
    margin = 50
    font, lines = fit_font(draw, words, int(CANVAS_W * 0.62), CANVAS_H - 2 * margin, FONT_BOLD, start_size=190)
    step = int(_line_h(font) * 1.25)
    _draw_title(draw, lines, font, margin, (CANVAS_H - step * len(lines)) // 2, step, accent_word)
    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def render_host_thumbnail(words, accent_word):
    """Fallback without a scene: boss on the left (on its white card), title on the right, on black."""
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (17, 17, 17))
    draw = ImageDraw.Draw(canvas)
    left_w = int(CANVAS_W * 0.42)
    host, pos = _fit_into(load_host_cutout(), (30, 30, left_w - 30, CANVAS_H))
    canvas.paste(host, pos)
    draw.rectangle([left_w, 0, left_w + 6, CANVAS_H], fill=FRAME)
    text_x0 = left_w + 50
    font, lines = fit_font(draw, words, CANVAS_W - text_x0 - 50, CANVAS_H - 120, FONT_BOLD)
    step = int(_line_h(font) * 1.25)
    _draw_title(draw, lines, font, text_x0, (CANVAS_H - step * len(lines)) // 2, step, accent_word)
    draw.rectangle([0, 0, CANVAS_W - 1, CANVAS_H - 1], outline=FRAME, width=14)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title", help="2-4 Devanagari words, e.g. 'पेट्रोल पंप का हिसाब'")
    ap.add_argument("--accent-word", default=None, help="One word from the title to draw in gold")
    ap.add_argument("--annotation", action="append", default=[], help="A money note with an arrow (max 4)")
    ap.add_argument("--scene", default=None, help="Path to a generated scene PNG")
    ap.add_argument("--out", default=str(ROOT / "brand" / "thumbnail-template-preview.png"))
    args = ap.parse_args()

    words = args.title.split()
    if len(words) > 4:
        raise SystemExit(f"Title has {len(words)} words; the locked template allows at most 4.")
    check_no_latin([args.title, *args.annotation])
    scene = args.scene if args.scene and Path(args.scene).exists() else None
    if args.annotation:
        canvas = render_annotated_thumbnail(words, args.accent_word, args.annotation, scene)
    elif scene:
        canvas = render_scene_thumbnail(words, args.accent_word, scene)
    else:
        canvas = render_host_thumbnail(words, args.accent_word)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    print(f"Saved {out_path} ({CANVAS_W}x{CANVAS_H})")
    small = canvas.resize((210, 118), Image.LANCZOS)
    small_path = out_path.with_name(out_path.stem + "-210x118-preview.png")
    small.save(small_path)
    print(f"Saved legibility check {small_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Pass annotations from metadata**

In `run_episode.py`'s `thumbnail_args`, after the `--accent-word` block and before the `beat = ...` line, add:

```python
    for note in (metadata.get("thumbnail_annotations") or [])[:4]:
        args += ["--annotation", note]
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest tests/test_make_thumbnail.py tests/test_run_episode.py -q`
Expected: all pass. If `test_annotated_layout_draws_annotations_with_gold_arrows`'s pixel thresholds miss by a small margin, print the two counts and check the rendered image by eye before touching a threshold; a threshold may only move if the image is visibly correct.

- [ ] **Step 6: Render all three layouts and look**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action/MafiaOfBusiness
mkdir -p .scratch
../.venv/bin/python scripts/make_thumbnail.py "पेट्रोल पंप का हिसाब" --accent-word हिसाब \
  --annotation "₹4.5/लीटर" --annotation "पहले पेमेंट" --annotation "लोन ईएमआई" --annotation "कैश फ़्लो" \
  --scene brand/host/host-reference-clean.jpeg --out .scratch/thumb_annotated.png
../.venv/bin/python scripts/make_thumbnail.py "जिम का असली खेल" --accent-word खेल --scene brand/host/host-reference-clean.jpeg --out .scratch/thumb_scene.png
../.venv/bin/python scripts/make_thumbnail.py "चाय में ₹70?" --accent-word "₹70?" --out .scratch/thumb_host.png
```

Read all three PNGs and `thumb_annotated-210x118-preview.png`. Confirm: matras and conjuncts correct, the gold underline sits below every matra, ₹ renders (not a box), arrows point from labels toward the scene, no label overlaps the scene or the title, the title band reads at 210x118. (₹ and digits were verified to render with Noto Sans Devanagari Bold on 2026-10-01; Latin letters do not, hence `check_no_latin`.)

- [ ] **Step 7: Commit**

```bash
cd .. && git add -A && git commit -m "Annotated hisaab thumbnail: Devanagari title band, money notes with gold arrows"
```

---

### Task 8: Finalize stage (replaces the Content Lab upload)

**Files:**
- Create: `MafiaOfBusiness/scripts/finalize_episode.py`
- Modify: `MafiaOfBusiness/scripts/cleanup_episode.py` (gate on `finalize_log.json`)
- Modify: `MafiaOfBusiness/scripts/pending_episodes.py` (done = finalized)
- Modify: `MafiaOfBusiness/scripts/assemble_episode.py:146` (output filename)
- Test: `tests/test_finalize_episode.py` (new), `tests/test_cleanup_episode.py`, `tests/test_pending_episodes.py`

**Interfaces:**
- Consumes: `07_edit/mafia-of-business-<slug>.mp4`, `07_edit/captions.srt`, `08_publish/{metadata.json,thumbnail.png}`, `03_audio/timings.json` (for chapters when needed), `format.runtime_*`.
- Produces:
  - `finalize_episode.verify_video(info: dict, min_s: float, max_s: float) -> list[str]` where `info = {"width": int, "height": int, "duration": float, "has_audio": bool}`.
  - `finalize_episode.build_posting_md(metadata: dict, duration: float) -> str`.
  - `finalize_episode.finalize(episode_dir: Path, output_root: Path, record=None, probe=None) -> dict` returns `{"status": "ok", "output_dir": str, "duration": float}`; writes `08_publish/finalize_log.json`; `record(slug, doc)` is called once with the Mongo episode fields (injected so tests need no DB; CLI passes a state_db writer).
  - `cleanup_episode.cleanup(episode_dir) -> list[str]` now requires `finalize_log.json` `status == "ok"`.
  - `pending_episodes.find_pending(episodes_dir) -> list[str]` treats `finalize_log.json` ok as done.
  - Output filename `07_edit/mafia-of-business-<slug>.mp4`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_finalize_episode.py`:

```python
import json

import pytest

import finalize_episode as fe

META = {
    "title": "चाय वाला असल में कितना कमाता है? | Chai Business Model in Hindi",
    "title_alternates": ["चाय की टपरी का असली खेल", "₹10 की चाय में कितना मुनाफ़ा?"],
    "description": "एक कप चाय...\n\n⏱️ Chapters\n0:00 हुक",
    "tags": ["chai wala income", "चाय वाला कितना कमाता है"],
    "pinned_comment": "बोनस: ...",
    "community_post": "चाय वाला महीने में कितना कमाता है? A) 15k B) 50k C) 1 लाख+",
    "shorts_hook": {"start": 0.0, "end": 42.5},
    "playlist": "Khana & Street Food",
}


def _episode(tmp_path, slug="2026-10-02-chai-wala"):
    ep = tmp_path / "episodes" / slug
    for d in ("03_audio", "05_scenes", "07_edit", "08_publish", "02_script"):
        (ep / d).mkdir(parents=True)
    (ep / "07_edit" / f"mafia-of-business-{slug}.mp4").write_bytes(b"video")
    (ep / "07_edit" / "captions.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nएक\n")
    (ep / "08_publish" / "thumbnail.png").write_bytes(b"png")
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(META, ensure_ascii=False))
    return ep


GOOD_INFO = {"width": 1920, "height": 1080, "duration": 241.2, "has_audio": True}


def test_verify_video_accepts_good_and_names_each_problem():
    assert fe.verify_video(GOOD_INFO, 180, 300) == []
    bad = {"width": 1280, "height": 720, "duration": 301.0, "has_audio": False}
    problems = fe.verify_video(bad, 180, 300)
    assert len(problems) == 3
    assert any("1280x720" in p for p in problems)
    assert any("301.0" in p for p in problems)
    assert any("audio" in p for p in problems)


def test_posting_md_has_everything_to_paste():
    md = fe.build_posting_md(META, 241.2)
    for needle in (META["title"], META["title_alternates"][1], "chai wala income", META["pinned_comment"],
                   META["community_post"], "0:00-0:42", "6-9 PM IST", "4:01", "Khana & Street Food"):
        assert needle in md


def test_finalize_copies_package_records_and_logs(tmp_path):
    ep = _episode(tmp_path)
    out_root = tmp_path / "output"
    records = []
    result = fe.finalize(ep, out_root, record=lambda slug, doc: records.append((slug, doc)),
                         probe=lambda p: GOOD_INFO)
    out = out_root / ep.name
    assert result["status"] == "ok"
    assert sorted(p.name for p in out.iterdir()) == sorted([
        f"mafia-of-business-{ep.name}.mp4", "thumbnail.png", "captions.srt", "metadata.json", "posting.md"])
    assert records[0][0] == ep.name and records[0][1]["status"] == "ready"
    assert records[0][1]["duration"] == 241.2
    log = json.loads((ep / "08_publish" / "finalize_log.json").read_text())
    assert log["status"] == "ok" and log["output_dir"] == str(out)


def test_finalize_refuses_bad_video_and_writes_nothing(tmp_path):
    ep = _episode(tmp_path)
    with pytest.raises(RuntimeError, match="301.0"):
        fe.finalize(ep, tmp_path / "output", record=lambda *a: None,
                    probe=lambda p: {**GOOD_INFO, "duration": 301.0})
    assert not (tmp_path / "output").exists()
    assert not (ep / "08_publish" / "finalize_log.json").exists()


def test_finalize_rerun_after_cleanup_is_a_noop(tmp_path):
    ep = _episode(tmp_path)
    calls = []
    fe.finalize(ep, tmp_path / "output", record=lambda *a: calls.append(a), probe=lambda p: GOOD_INFO)
    import shutil
    shutil.rmtree(ep / "07_edit")  # cleanup ran
    result = fe.finalize(ep, tmp_path / "output", record=lambda *a: calls.append(a), probe=lambda p: GOOD_INFO)
    assert result["status"] == "ok"
    assert len(calls) == 1
```

Replace `tests/test_cleanup_episode.py` with:

```python
import json

import pytest

import cleanup_episode as ce


def _make(tmp_path, finalize_log):
    ep = tmp_path / "ep-1"
    for d in ("03_audio", "05_scenes", "07_edit", "02_script", "08_publish"):
        (ep / d).mkdir(parents=True)
    (ep / "topic.json").write_text("{}")
    (ep / "02_script" / "f.bin").write_bytes(b"x")
    if finalize_log is not None:
        (ep / "08_publish" / "finalize_log.json").write_text(json.dumps(finalize_log))
    return ep


def test_refuses_to_clean_unfinalized_episode(tmp_path):
    with pytest.raises(RuntimeError):
        ce.cleanup(_make(tmp_path, None))


def test_refuses_to_clean_failed_finalize(tmp_path):
    with pytest.raises(RuntimeError):
        ce.cleanup(_make(tmp_path, {"status": "failed"}))


def test_deletes_media_keeps_records(tmp_path):
    ep = _make(tmp_path, {"status": "ok"})
    assert sorted(ce.cleanup(ep)) == ["03_audio", "05_scenes", "07_edit"]
    for keep in ("topic.json", "02_script/f.bin", "08_publish/finalize_log.json"):
        assert (ep / keep).exists()


def test_cleanup_is_idempotent(tmp_path):
    ep = _make(tmp_path, {"status": "ok"})
    ce.cleanup(ep)
    assert ce.cleanup(ep) == []
```

Replace `tests/test_pending_episodes.py` with:

```python
import json

import pending_episodes as pe


def _episode(base, slug, finalize_log=None):
    ep = base / slug
    (ep / "02_script").mkdir(parents=True)
    (ep / "02_script" / "script.md").write_text("[HOOK]\n1. x\n")
    if finalize_log is not None:
        (ep / "08_publish").mkdir(parents=True)
        (ep / "08_publish" / "finalize_log.json").write_text(json.dumps(finalize_log))
    return ep


def test_finalized_episode_is_not_pending(tmp_path):
    _episode(tmp_path, "a", {"status": "ok", "output_dir": "x"})
    assert pe.find_pending(tmp_path) == []


def test_unfinished_episode_is_pending(tmp_path):
    _episode(tmp_path, "b")
    assert pe.find_pending(tmp_path) == ["b"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_finalize_episode.py tests/test_cleanup_episode.py tests/test_pending_episodes.py -q`
Expected: FAIL (`finalize_episode` missing; cleanup/pending still read `upload_log.json`).

- [ ] **Step 3: Implement `finalize_episode.py`**

Create `MafiaOfBusiness/scripts/finalize_episode.py`:

```python
#!/usr/bin/env python3
"""Final stage (replaces RedHat's Content Lab upload): verify the render,
copy the posting package to output/<slug>/, record the episode in MongoDB
as "ready", and write 08_publish/finalize_log.json. cleanup_episode.py
deletes intermediates only after this log says ok. Idempotent: a rerun on a
finalized episode does nothing.

Usage: python3 scripts/finalize_episode.py <episode-slug>
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
from state import load_state  # noqa: E402

WORKSPACE = SCRIPTS_DIR.parent
OUTPUT_ROOT = WORKSPACE / "output"

CHECKLIST = """## Posting checklist
- [ ] Post between 6-9 PM IST (daily if you can: both reference channels grew on one video a day).
- [ ] Upload the video; set the thumbnail from thumbnail.png.
- [ ] Paste title, description and tags from this file.
- [ ] Video language and default audio language: Hindi. Upload captions.srt as Hindi subtitles.
- [ ] Not made for kids. Altered/synthetic content: yes (AI voice and images).
- [ ] Add to the playlist named above (one playlist per vertical).
- [ ] Pin the comment below within minutes of publishing.
- [ ] Post the community poll (ideally a day before).
- [ ] Turn off auto-dubbing.
- [ ] Optional: cut a Short from the hook range below.
- [ ] Then run: python3 scripts/state_db.py episode-posted <slug> <youtube-url>
"""


def _mmss(seconds: float) -> str:
    s = int(round(seconds))
    return f"{s // 60}:{s % 60:02d}"


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
         "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), {})
    return {
        "width": int(video.get("width", 0)), "height": int(video.get("height", 0)),
        "duration": float(data["format"]["duration"]),
        "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
    }


def verify_video(info: dict, min_s: float, max_s: float) -> list[str]:
    problems = []
    if (info["width"], info["height"]) != (1920, 1080):
        problems.append(f"video is {info['width']}x{info['height']}, expected 1920x1080")
    if not min_s <= info["duration"] <= max_s:
        problems.append(f"video is {info['duration']:.1f}s, allowed {min_s:.0f}-{max_s:.0f}s")
    if not info["has_audio"]:
        problems.append("video has no audio stream")
    return problems


def build_posting_md(metadata: dict, duration: float) -> str:
    hook = metadata.get("shorts_hook") or {}
    parts = [
        f"# {metadata['title']}", "",
        f"Runtime: {_mmss(duration)}", "",
        "## Title", metadata["title"], "",
        "## Alternate titles (for Test & Compare)",
        *[f"- {t}" for t in metadata.get("title_alternates", [])], "",
        "## Description", metadata.get("description", ""), "",
        "## Tags", ", ".join(metadata.get("tags", [])), "",
        "## Playlist", metadata.get("playlist", "(not set)"), "",
        "## Pinned comment", metadata.get("pinned_comment", ""), "",
        "## Community poll", metadata.get("community_post", ""), "",
        "## Shorts hook range",
        f"{_mmss(hook['start'])}-{_mmss(hook['end'])}" if hook else "(not set)", "",
        CHECKLIST,
    ]
    return "\n".join(parts)


def _default_record(slug: str, doc: dict) -> None:
    import state_db
    state_db.episode_ready(state_db.get_db(), slug, doc)


def finalize(episode_dir: Path, output_root: Path = OUTPUT_ROOT, record=None, probe=probe) -> dict:
    record = record or _default_record
    slug = episode_dir.name
    log_path = episode_dir / "08_publish" / "finalize_log.json"
    if log_path.exists():
        log = json.loads(log_path.read_text())
        if log.get("status") == "ok":
            print(f"{slug} already finalized -> {log['output_dir']}")
            return log

    fmt = load_state()["format"]
    video = episode_dir / "07_edit" / f"mafia-of-business-{slug}.mp4"
    srt = episode_dir / "07_edit" / "captions.srt"
    metadata_path = episode_dir / "08_publish" / "metadata.json"
    thumb = episode_dir / "08_publish" / "thumbnail.png"
    missing = [str(p) for p in (video, srt, metadata_path, thumb) if not p.exists()]
    if missing:
        raise RuntimeError(f"cannot finalize {slug}, missing: {', '.join(missing)}")
    info = probe(video)
    problems = verify_video(info, fmt["runtime_min_seconds"], fmt["runtime_max_seconds"])
    if problems:
        raise RuntimeError(f"cannot finalize {slug}: " + "; ".join(problems))

    metadata = json.loads(metadata_path.read_text())
    out_dir = output_root / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in (video, srt, metadata_path, thumb):
        shutil.copy2(src, out_dir / src.name)
    (out_dir / "posting.md").write_text(build_posting_md(metadata, info["duration"]))

    now = datetime.now(timezone.utc).isoformat()
    record(slug, {"title": metadata["title"], "duration": round(info["duration"], 1),
                  "output_dir": str(out_dir), "status": "ready", "finalized_at": now})
    log = {"status": "ok", "output_dir": str(out_dir), "duration": round(info["duration"], 1), "at": now}
    log_path.write_text(json.dumps(log, indent=2))
    print(f"finalized {slug} -> {out_dir}")
    return log


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/finalize_episode.py <episode-slug>")
        sys.exit(1)
    try:
        finalize(WORKSPACE / "episodes" / sys.argv[1])
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
```

Note the `duration` check in `test_finalize_copies_package_records_and_logs` expects `241.2`; `round(241.2, 1) == 241.2`, fine.

- [ ] **Step 4: Update cleanup and pending**

In `cleanup_episode.py` replace `_upload_confirmed` and its use:

```python
def _finalized(episode_dir: Path) -> bool:
    try:
        log = json.loads((episode_dir / "08_publish" / "finalize_log.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(log, dict) and log.get("status") == "ok"


def cleanup(episode_dir: Path) -> list[str]:
    if not _finalized(episode_dir):
        raise RuntimeError(f"refusing to clean {episode_dir.name}: episode not finalized")
```

(rest of `cleanup` unchanged). Docstring: replace "once Content Lab confirmed the upload" with "once finalize_episode.py copied the package to output/", and "unless upload_log.json shows content_lab status ok" with "unless finalize_log.json shows status ok".

In `pending_episodes.py` replace `_uploaded` with:

```python
def _finalized(episode_dir: Path) -> bool:
    try:
        log = json.loads((episode_dir / "08_publish" / "finalize_log.json").read_text())
    except (OSError, ValueError):
        return False
    return isinstance(log, dict) and log.get("status") == "ok"
```

and `not _uploaded(ep)` with `not _finalized(ep)`. Docstring: "not yet finalized into output/. Exit 0 if none, 1 if any pending."

In `assemble_episode.py` replace `output_path = edit_dir / f"redhat-engineer-{slug}-episode.mp4"` with `output_path = edit_dir / f"mafia-of-business-{slug}.mp4"`, and the comment mentioning "Cloudinary's 100MB single-request upload cap" with "a reasonable local file size".

- [ ] **Step 5: Run tests**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass except none -- `test_finalize_episode.py` does not touch Mongo (record injected). `state_db.episode_ready` is added in Task 9; nothing calls `_default_record` in tests.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "Finalize stage: verify render, package output/<slug>/ with posting.md, gate cleanup on it"
```

---

### Task 9: State, orchestration and the local runner

**Files:**
- Modify: `MafiaOfBusiness/scripts/state_db.py` (drop slots; `episode_ready`, `episode_posted`, `episode-posted` CLI; status from `finalize_log.json`)
- Modify: `MafiaOfBusiness/scripts/run_episode.py` (script check stage, finalize instead of upload)
- Modify: `MafiaOfBusiness/scripts/run_cycle.sh`, `make-video`
- Test: `tests/test_state_db.py`, `tests/test_run_episode.py`

**Interfaces:**
- Consumes: `finalize_episode.py`, `check_script.py`, `cleanup_episode.py` CLIs.
- Produces: `state_db.episode_ready(db, slug: str, doc: dict) -> None` (upsert, `status` from doc); `state_db.episode_posted(db, slug: str, url: str) -> None` (sets `status: "posted"`, `youtube_url`); `state_db._episode_status(files) -> tuple[str, str | None]` returns `("ready", output_dir)` when `08_publish/finalize_log.json` is ok; `run_episode.STAGES: list[tuple[str, str]]` (stage name, script file) in run order.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_state_db.py`:

```python
def test_episode_ready_then_posted(db):
    state_db.episode_ready(db, "2026-10-02-chai", {"title": "t", "status": "ready", "output_dir": "/o"})
    doc = db.episodes.find_one({"_id": "2026-10-02-chai"})
    assert doc["status"] == "ready" and doc["output_dir"] == "/o"
    state_db.episode_posted(db, "2026-10-02-chai", "https://youtu.be/x")
    doc = db.episodes.find_one({"_id": "2026-10-02-chai"})
    assert doc["status"] == "posted" and doc["youtube_url"] == "https://youtu.be/x"


def test_episode_status_reads_finalize_log():
    assert state_db._episode_status({}) == ("pending", None)
    files = {"08_publish/finalize_log.json": '{"status": "ok", "output_dir": "/o"}'}
    assert state_db._episode_status(files) == ("ready", "/o")


def test_push_does_not_downgrade_a_posted_episode(db, tmp_path, monkeypatch):
    monkeypatch.setattr(state_db, "STATE_PATH", tmp_path / "missing.json")
    ep = tmp_path / "episodes" / "e1" / "08_publish"
    ep.mkdir(parents=True)
    (ep / "finalize_log.json").write_text('{"status": "ok", "output_dir": "/o"}')
    state_db.episode_posted(db, "e1", "https://youtu.be/x")
    state_db.push(db, tmp_path)
    assert db.episodes.find_one({"_id": "e1"})["status"] == "posted"


def test_no_slot_commands_remain():
    assert not hasattr(state_db, "slot_check")
```

Replace `tests/test_run_episode.py`'s first test's argument values to Hindi (shows the thumbnail path still works) and append a stage-order test. Final file:

```python
import json

import run_episode


def _episode(tmp_path, metadata, scenes=()):
    ep = tmp_path / "ep"
    (ep / "08_publish").mkdir(parents=True)
    (ep / "08_publish" / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False))
    (ep / "05_scenes").mkdir()
    for name in scenes:
        (ep / "05_scenes" / name).write_bytes(b"png")
    return ep


def test_thumbnail_args_use_text_accent_output_and_scene(tmp_path):
    ep = _episode(tmp_path, {"thumbnail_text": "चाय में ₹70?", "thumbnail_accent_word": "₹70?"},
                  scenes=["scene_0001.png"])
    args = run_episode.thumbnail_args(ep)
    assert args[1] == "चाय में ₹70?"
    assert args[args.index("--accent-word") + 1] == "₹70?"
    assert args[args.index("--out") + 1].endswith("08_publish/thumbnail.png")
    assert args[args.index("--scene") + 1].endswith("05_scenes/scene_0001.png")


def test_thumbnail_beat_selects_the_scene_and_missing_scene_falls_back(tmp_path):
    ep = _episode(tmp_path, {"thumbnail_text": "X", "thumbnail_beat": 3}, scenes=["scene_0003.png"])
    assert run_episode.thumbnail_args(ep)[-1].endswith("scene_0003.png")
    ep2 = _episode(tmp_path / "b", {"thumbnail_text": "X", "thumbnail_beat": 9})
    assert "--scene" not in run_episode.thumbnail_args(ep2)


def test_no_thumbnail_text_means_no_thumbnail_stage(tmp_path):
    assert run_episode.thumbnail_args(_episode(tmp_path, {"title": "x"})) is None


def test_stage_order_checks_script_first_and_finalizes_before_cleanup():
    scripts = [s for _, s in run_episode.STAGES]
    assert scripts[0] == "check_script.py"
    assert scripts.index("finalize_episode.py") < scripts.index("cleanup_episode.py")
    assert "publish_all.py" not in scripts
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_state_db.py tests/test_run_episode.py -q`
Expected: FAIL (`episode_ready`, `STAGES` missing).

- [ ] **Step 3: Implement state_db changes**

In `state_db.py`:
1. Docstring: first line `"""Mafia of Business's MongoDB-backed state: topic bank, episode records,` / second line `and channel_state.json's live counters. There is`; replace the three `slot-*` usage lines with:
   ```
       state_db.py episode-posted <slug> <url> -- mark a finalized episode as posted on YouTube
   ```
2. In `EPISODE_TEXT_FILES` replace `"08_publish/upload_log.json",` with `"08_publish/finalize_log.json",`.
3. Delete `SLOT_HOURS`, `current_slot`, `slot_check`, `slot_done`, `slot_failed`, and the three `slot-*` branches in `main`.
4. Replace `_episode_status` with:

```python
def _episode_status(files: dict) -> tuple[str, str | None]:
    raw = files.get("08_publish/finalize_log.json")
    if raw:
        try:
            log = json.loads(raw)
            if log.get("status") == "ok":
                return "ready", log.get("output_dir")
        except json.JSONDecodeError:
            pass
    return "pending", None
```

5. In `_push_episodes`, replace the `db.episodes.update_one(...)` call with one that never downgrades a posted episode and stores the output dir:

```python
        existing = db.episodes.find_one({"_id": ep_dir.name}) or {}
        if existing.get("status") == "posted":
            status = "posted"
        db.episodes.update_one(
            {"_id": ep_dir.name},
            {"$set": {
                "slug": ep_dir.name, "topic": topic, "status": status, "output_dir": url,
                "files": files, "updated_at": datetime.now(timezone.utc).isoformat(),
            }},
            upsert=True,
        )
```

6. Add after `topic_reject`:

```python
def episode_ready(db, slug: str, doc: dict) -> None:
    db.episodes.update_one({"_id": slug}, {"$set": {"slug": slug, **doc}}, upsert=True)


def episode_posted(db, slug: str, url: str) -> None:
    db.episodes.update_one(
        {"_id": slug},
        {"$set": {"slug": slug, "status": "posted", "youtube_url": url,
                  "posted_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
```

7. In `main`, the `recent` branch prints `ep.get('youtube_url') or ep.get('output_dir') or ''` instead of `ep.get('url') or ''`; add:

```python
    elif cmd == "episode-posted":
        episode_posted(db, rest[0], rest[1])
```

8. `_restore_unfinished_episodes` keeps restoring `status: "pending"` only (unchanged).

- [ ] **Step 4: Implement run_episode changes**

In `run_episode.py`:
1. Docstring line 3: `audio -> scenes -> assembly -> thumbnail -> finalize into output/<slug>/.`; replace "uploading to Content Lab (the operator posts by hand), then deleting the episode's media" with "copying the package to output/<slug>/ and recording it in MongoDB (finalize_episode.py), then deleting the episode's intermediates"; delete the sentence about `publish_all.py`'s per-platform "log and continue" (keep "A stage failure aborts the run with a clear message rather than continuing on broken input.").
2. Add after `LOCK_PATH`:

```python
# (stage name, script) in run order; the thumbnail runs between assembly and
# finalize as an optional stage (see main).
STAGES = [
    ("Check script", "check_script.py"),
    ("Narration", "generate_narration_chunks.py"),
    ("Stitch audio", "stitch_audio.py"),
    ("Generate scenes", "generate_scenes.py"),
    ("Assemble episode", "assemble_episode.py"),
    ("Finalize", "finalize_episode.py"),
    ("Cleanup", "cleanup_episode.py"),
]
```

3. Replace the block from `run_stage("Narration", ...)` through `run_stage("Cleanup", ...)` with:

```python
    for name, script in STAGES:
        if name == "Finalize":
            thumb = thumbnail_args(episode_dir)
            if thumb:
                run_optional_stage("Thumbnail", thumb)
        run_stage(name, [str(SCRIPTS / script), slug])
```

4. Change `run_optional_stage`'s docstring to `"""A stage whose failure must not stop the episode."""`. Note: `finalize_episode.py` requires `thumbnail.png`, so a failed thumbnail stops at finalize with a clear "missing" message -- intended (the spec makes the thumbnail part of the package).

- [ ] **Step 5: Implement runner changes**

In `MafiaOfBusiness/scripts/run_cycle.sh`:
1. Header comment: `# One Mafia of Business run (local): makes exactly ONE episode and finalizes it into\n# output/<slug>/. opencode is re-invoked (up to MAX_ATTEMPTS) until a NEW finalized\n# episode is recorded; each retry receives the tail of the last attempt.`; delete the two lines about `IMAGINE_ERROR_SLOT`.
2. Delete the `mark_slot()` function and both `mark_slot ...` calls.
3. Rename `uploaded_count` to `finalized_count` (definition and both uses) with body:

```bash
finalized_count() {
  python3 - <<'PY'
import json, pathlib
n = 0
for f in pathlib.Path("episodes").glob("*/08_publish/finalize_log.json"):
    try:
        n += json.loads(f.read_text()).get("status") == "ok"
    except (OSError, ValueError, AttributeError):
        pass
print(n)
PY
}
```

4. Replace the retry text `the previous attempt ended before a NEW episode was uploaded to Content Lab` with `the previous attempt ended before a NEW episode was finalized into output/`, and the success echo with `echo "=== episode finalized ($before -> $after) ==="`.

Replace `make-video` with:

```bash
#!/usr/bin/env bash
# Make ONE Mafia of Business episode locally: an opencode agent picks a topic,
# writes the Hindi script, and the pipeline renders it into
# MafiaOfBusiness/output/<slug>/ (video, thumbnail, captions, posting.md).
#
#   ./make-video
#
# Output is shown live and saved to MafiaOfBusiness/.scratch/local_run_<timestamp>.log.
# Optional env: OPENCODE_MODEL, MAX_ATTEMPTS (default 4).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

case "${1:-}" in
  "") ;;
  -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) echo "unknown option: $1 (try --help)" >&2; exit 2 ;;
esac

if [ ! -x .venv/bin/python3 ]; then
  echo "first run: creating .venv..."
  python3 -m venv .venv
fi
if ! .venv/bin/python3 -c "import edge_tts, pymongo, requests, PIL" 2>/dev/null; then
  echo "installing edge-tts, pymongo, requests, pillow..."
  .venv/bin/pip install -q edge-tts pymongo requests pillow
fi
export PATH="$ROOT/.venv/bin:$HOME/.opencode/bin:$PATH"

for tool in ffmpeg ffprobe opencode; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 1; }
done
fc-list | grep -q "Noto Sans Devanagari" || {
  echo "missing font Noto Sans Devanagari (sudo apt install fonts-noto-core)" >&2; exit 1; }
[ -f .env ] || { echo "missing $ROOT/.env (needs CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, MONGODB_URI)" >&2; exit 1; }

cd MafiaOfBusiness
mkdir -p .scratch output
log=".scratch/local_run_$(date +%Y%m%d_%H%M%S).log"
echo "logging to MafiaOfBusiness/$log"
bash scripts/run_cycle.sh 2>&1 | tee "$log"
exit "${PIPESTATUS[0]}"
```

- [ ] **Step 6: Run tests and lint the shell**

```bash
.venv/bin/python -m pytest -q
bash -n make-video && bash -n MafiaOfBusiness/scripts/run_cycle.sh && echo shell-ok
grep -rn "IMAGINE_ERROR\|slot\|upload_log\|publish_all\|content_lab\|Content Lab" MafiaOfBusiness/scripts make-video
```

Expected: tests pass; `shell-ok`; the grep prints nothing.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "Local orchestration: script check + finalize stages, episode-posted, no slots"
```

---

### Task 10: Agent skill, cycle prompt, topic seed and docs

**Files:**
- Rewrite: `.claude/skills/mafia-of-business-youtube/SKILL.md`
- Rewrite: `.claude/skills/mafia-of-business-youtube/references/{topic-strategy,script-formula,thumbnail-and-metadata,publishing-and-metadata,voice-and-audio,character-bible,compliance-and-safety,analytics-and-growth}.md`
- Edit: `.claude/skills/mafia-of-business-youtube/references/{research-and-facts,visuals-and-animation,ambience-sound,captions,edit-and-assembly,setup-and-state}.md`
- Rewrite: `MafiaOfBusiness/cycle_prompt.md`, `MafiaOfBusiness/seed/topic_bank.seed.json`, `AGENTS.md`, `README.md`
- Test: `tests/test_seed_and_docs.py` (new)

**Interfaces:**
- Consumes: every stage name and file from Tasks 2-9 (`check_script.py`, `finalize_episode.py`, `finalize_log.json`, `output/<slug>/`, `episode-posted`, section tags, `metadata.json` fields `title_alternates`, `pinned_comment`, `community_post`, `shorts_hook`, `topic.json` field `keywords`).
- Produces: an agent operating manual that matches the code, and a seed of at least 30 topics.

- [ ] **Step 1: Write the failing test**

Create `tests/test_seed_and_docs.py`:

```python
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WS = ROOT / "MafiaOfBusiness"
SKILL = ROOT / ".claude" / "skills" / "mafia-of-business-youtube"


def test_seed_has_30_complete_topics_across_categories():
    queued = json.loads((WS / "seed" / "topic_bank.seed.json").read_text())["queued"]
    assert len(queued) >= 30
    for t in queued:
        for key in ("topic", "category", "setting", "myth", "angle", "visual_hooks", "score", "keywords"):
            assert key in t, (t.get("topic"), key)
        assert 3 <= len(t["keywords"]) <= 5
    assert len({t["category"] for t in queued}) >= 6
    # abstract/distant topics flopped for comparable channels (spec 4.1)
    for flop in ("आईपीएल", "यूपीआई", "कोचिंग", "ट्रेन"):
        assert not any(flop in t["topic"] for t in queued), flop
    assert len({t["topic"] for t in queued}) == len(queued)


def test_docs_reference_current_pipeline_only():
    texts = [p.read_text() for p in [*SKILL.rglob("*.md"), WS / "cycle_prompt.md", ROOT / "AGENTS.md", ROOT / "README.md"]]
    blob = "\n".join(texts)
    for stale in ("Content Lab", "content_lab", "upload_log", "publish_all", "RedHat", "red fedora",
                  "COLD_OPEN", "RISING_MYSTERY", "CLIMAX_REVEAL", "en-US-Ava", "slot-check"):
        assert stale not in blob, stale
    for needed in ("[HOOK]", "[RAAZ]", "finalize_log.json", "output/", "hi-IN-MadhurNeural", "check_script.py",
                   "thumbnail_annotations", "आपके सवाल", "playlist", "मान लीजिए"):
        assert needed in blob, needed


def test_skill_frontmatter_names_the_channel():
    head = (SKILL / "SKILL.md").read_text().split("---")[1]
    assert re.search(r"^name: mafia-of-business-youtube$", head, re.M)
    assert "Mafia of Business" in head
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_seed_and_docs.py -q`
Expected: FAIL (seed empty; docs still RedHat).

- [ ] **Step 3: Write the topic seed**

Overwrite `MafiaOfBusiness/seed/topic_bank.seed.json` with these 32 entries (six verticals from spec 4.1 plus one politician episode; order = queue order, strongest first). Exact content:

```json
{"queued": [
 {"topic": "पेट्रोल पंप वाला असल में कितना कमाता है", "category": "Dukaan & Retail", "setting": "A highway petrol pump", "myth": "पंप खोल लो, बैठे-बैठे नोट गिनो", "angle": "Of roughly a hundred rupees per litre the dealer keeps only a few rupees of commission; tanker paid in advance, loan EMI and staff eat the rest, so volume and the side business decide everything.", "visual_hooks": ["a fuel nozzle", "a tanker truck", "a cash box"], "score": 10, "keywords": ["petrol pump business profit", "petrol pump kitna kamata hai", "पेट्रोल पंप कितना कमाता है", "petrol pump dealer margin"]},
 {"topic": "डंपर मालिक असल में कितना कमाता है", "category": "Transport & Heavy Vehicles", "setting": "A tipper truck at a construction site", "myth": "एक डंपर ले लो, रोज़ का पैसा पक्का", "angle": "Down payment, EMI, diesel, driver, tyres and idle days in the rainy season; one bad month can wipe out three good ones.", "visual_hooks": ["a dumper unloading sand", "a diesel pump", "a calendar with rain"], "score": 10, "keywords": ["dumper business in india", "tipper truck income", "डंपर कितना कमाता है", "dumper business profit"]},
 {"topic": "ढाबे वाला असल में कितना कमाता है", "category": "Khana & Street Food", "setting": "A highway dhaba with truck parking", "myth": "ढाबा चलाना तो आसान है, खाना बनाओ बेचो", "angle": "The dal is the hero, the papad and chai carry the margin, and wasted food goes in the dustbin every night.", "visual_hooks": ["a pot of dal", "a charpai and a truck", "a tandoor"], "score": 10, "keywords": ["dhaba business profit", "dhaba kitna kamata hai", "ढाबा कितना कमाता है", "dhaba business in hindi"]},
 {"topic": "पोल्ट्री फ़ार्म असल में कितना कमाता है", "category": "Farming & Pashu", "setting": "A broiler shed in a village", "myth": "मुर्गी पालो, चालीस दिन में पैसा", "angle": "Chicks, feed, medicine and the market rate on selling day; one disease or one price crash decides the batch.", "visual_hooks": ["a shed full of chicks", "a feed sack", "a weighing scale"], "score": 10, "keywords": ["poultry farming profit", "poultry farm business", "पोल्ट्री फार्म कितना कमाता है", "murgi palan profit"]},
 {"topic": "चाय वाला असल में कितना कमाता है", "category": "Khana & Street Food", "setting": "A roadside chai tapri outside a station", "myth": "दस रुपये की चाय, इसमें क्या कमाई", "angle": "A ten-rupee cup costs a few rupees to make; volume and the biscuit counter are the real game.", "visual_hooks": ["a steaming kettle", "a row of small glasses", "a dawn crowd"], "score": 9, "keywords": ["chai wala income", "tea stall business profit", "चाय वाला कितना कमाता है"]},
 {"topic": "जिम वाला असल में कितना कमाता है", "category": "Services", "setting": "A neighbourhood gym in January and in March", "myth": "जिम में तो भीड़ है, खूब कमाई होगी", "angle": "Yearly memberships sold in January to people who stop coming by March; equipment EMI and rent are the risk.", "visual_hooks": ["a crowded gym", "an empty gym", "a membership card"], "score": 9, "keywords": ["gym business profit", "gym owner income", "जिम वाला कितना कमाता है"]},
 {"topic": "किराना दुकान वाला असल में कितना कमाता है", "category": "Dukaan & Retail", "setting": "A neighbourhood kirana store", "myth": "दुकान है, ग्राहक आते रहते हैं", "angle": "Thin margins, udhaar to regulars, distributor schemes and a few high-margin items keep it alive against apps.", "visual_hooks": ["shelves of packets", "an udhaar notebook", "a delivery bike"], "score": 9, "keywords": ["kirana store profit", "kirana business margin", "किराना दुकान कितना कमाती है"]},
 {"topic": "मशरूम की खेती असल में कितना कमाती है", "category": "Farming & Pashu", "setting": "A dark room of mushroom bags", "myth": "छोटे कमरे में लाखों की खेती", "angle": "Low space, fast cycles, but contamination and selling before it spoils decide the profit.", "visual_hooks": ["hanging mushroom bags", "a dark room", "a basket of mushrooms"], "score": 9, "keywords": ["mushroom farming profit", "mushroom ki kheti", "मशरूम की खेती कितना कमाती है"]},
 {"topic": "ट्रक मालिक असल में कितना कमाता है", "category": "Transport & Heavy Vehicles", "setting": "A truck on a long highway route", "myth": "ट्रक है तो माल है, माल है तो पैसा", "angle": "Freight rate, diesel, toll, driver, empty return trips; the return load is the real profit.", "visual_hooks": ["a loaded truck", "a toll barrier", "an empty truck coming back"], "score": 9, "keywords": ["truck business profit", "transport business in india", "ट्रक मालिक कितना कमाता है"]},
 {"topic": "मोमो वाला असल में कितना कमाता है", "category": "Khana & Street Food", "setting": "An evening momo cart in a market", "myth": "मोमो का ठेला, छोटा धंधा", "angle": "Cheap flour and filling, fast steaming, and the chutney that brings people back.", "visual_hooks": ["a steamer tower", "a plate of momos", "an evening queue"], "score": 9, "keywords": ["momo business profit", "momo stall income", "मोमो वाला कितना कमाता है"]},
 {"topic": "नाई की दुकान असल में कितना कमाती है", "category": "Services", "setting": "A small barber shop", "myth": "कटिंग से कितना कमा लेगा", "angle": "Haircuts fill the day, but shaves, facials, chair rent and Sunday rush make the month.", "visual_hooks": ["a barber chair", "scissors and comb", "a Sunday queue"], "score": 8, "keywords": ["salon business profit", "barber shop income", "नाई कितना कमाता है"]},
 {"topic": "मछली पालन असल में कितना कमाता है", "category": "Farming & Pashu", "setting": "A village fish pond", "myth": "तालाब में मछली डालो, बड़ी होगी, बेचो", "angle": "Seed fish, feed, oxygen and the one hot night that can kill a pond.", "visual_hooks": ["a pond", "a fishing net", "a feed bag"], "score": 8, "keywords": ["fish farming profit", "machli palan", "मछली पालन कितना कमाता है"]},
 {"topic": "जेसीबी किराए पर देने वाला कितना कमाता है", "category": "Transport & Heavy Vehicles", "setting": "A JCB on hourly rent", "myth": "जेसीबी घंटे के हिसाब से, पैसा ही पैसा", "angle": "Hourly rent looks huge; EMI, operator, diesel and idle days tell the real story.", "visual_hooks": ["a JCB digging", "a clock", "an operator cabin"], "score": 8, "keywords": ["jcb business profit", "jcb rent per hour", "जेसीबी कितना कमाता है"]},
 {"topic": "पानी पूरी वाला असल में कितना कमाता है", "category": "Khana & Street Food", "setting": "An evening golgappa cart", "myth": "पानी पूरी का ठेला, दो पैसे की कमाई", "angle": "Ingredients cost little; plates per hour and a loyal evening crowd decide the day.", "visual_hooks": ["a cart with a pot of pani", "hands filling puris", "a queue"], "score": 8, "keywords": ["pani puri business profit", "golgappa income", "पानी पूरी वाला कितना कमाता है"]},
 {"topic": "मेडिकल स्टोर असल में कितना कमाता है", "category": "Dukaan & Retail", "setting": "A chemist shop near a hospital", "myth": "दवाई तो हर कोई खरीदता है", "angle": "Branded vs generic margins, expiry losses and the doctor nearby decide the business.", "visual_hooks": ["shelves of medicine boxes", "a prescription slip", "a hospital gate"], "score": 8, "keywords": ["medical store profit", "medical shop margin", "मेडिकल स्टोर कितना कमाता है"]},
 {"topic": "कबाड़ीवाला असल में कितना कमाता है", "category": "Recycling & Small Industry", "setting": "A kabadi godown", "myth": "कबाड़ में क्या रखा है", "angle": "Buy cheap by the kilo, sort, sell by material to bigger dealers; sorting is the secret.", "visual_hooks": ["a scale with scrap", "piles of paper and metal", "a cycle cart"], "score": 9, "keywords": ["kabadi business profit", "scrap business in india", "कबाड़ीवाला कितना कमाता है"]},
 {"topic": "डेयरी फ़ार्म असल में कितना कमाता है", "category": "Farming & Pashu", "setting": "A small dairy with ten buffaloes", "myth": "भैंस रखो, रोज़ दूध, रोज़ पैसा", "angle": "Feed is most of the cost; dry months, vet bills and the milk rate decide the profit.", "visual_hooks": ["a buffalo", "a milk can", "a fodder pile"], "score": 8, "keywords": ["dairy farming profit", "dairy business", "डेयरी फार्म कितना कमाता है"]},
 {"topic": "टेंट हाउस वाला असल में कितना कमाता है", "category": "Services", "setting": "A tent house godown in wedding season", "myth": "शादी का सीज़न, बस तीन महीने का काम", "angle": "Buy once, rent a hundred times; the off-season and damage decide the year.", "visual_hooks": ["a folded shamiana", "stacked chairs", "a loaded truck"], "score": 8, "keywords": ["tent house business profit", "tent house income", "टेंट हाउस कितना कमाता है"]},
 {"topic": "ई-रिक्शा वाला दिन में कितना बचाता है", "category": "Transport & Heavy Vehicles", "setting": "An e-rickshaw on a city route", "myth": "बैटरी से चलता है, खर्चा ही नहीं", "angle": "Battery charging, daily rent if not owned, battery replacement after a year or two.", "visual_hooks": ["an e-rickshaw", "a charging point", "a battery"], "score": 8, "keywords": ["e rickshaw income", "e rickshaw business profit", "ई रिक्शा कितना कमाता है"]},
 {"topic": "लॉन्ड्री वाला असल में कितना कमाता है", "category": "Services", "setting": "A neighbourhood laundry and press shop", "myth": "कपड़े धोने में क्या कमाई", "angle": "Per-piece pricing, electricity, and the press that earns more than the machine.", "visual_hooks": ["a pile of clothes", "an iron", "a washing machine"], "score": 7, "keywords": ["laundry business profit", "dhobi income", "लॉन्ड्री कितना कमाती है"]},
 {"topic": "कोल्ड स्टोरेज असल में कितना कमाता है", "category": "Recycling & Small Industry", "setting": "A potato cold storage", "myth": "बस गोदाम ठंडा रखो, किराया लो", "angle": "Rent per sack per season, electricity bills, and the years when prices crash and farmers abandon stock.", "visual_hooks": ["sacks of potatoes", "a big cold room", "an electricity meter"], "score": 8, "keywords": ["cold storage business profit", "cold storage income", "कोल्ड स्टोरेज कितना कमाता है"]},
 {"topic": "जूस वाला असल में कितना कमाता है", "category": "Khana & Street Food", "setting": "A summer juice stall", "myth": "गर्मी में खूब बिकता है", "angle": "Fruit wastage, ice and the three summer months that pay for the whole year.", "visual_hooks": ["a juicer", "a pile of oranges", "a glass with ice"], "score": 7, "keywords": ["juice shop profit", "juice business income", "जूस वाला कितना कमाता है"]},
 {"topic": "हार्डवेयर की दुकान असल में कितना कमाती है", "category": "Dukaan & Retail", "setting": "A hardware shop near new construction", "myth": "पेंच-कील बेचकर क्या कमाएगा", "angle": "Small items carry big margins, contractors buy on credit, construction booms decide the year.", "visual_hooks": ["a box of screws", "paint cans", "a contractor with a list"], "score": 7, "keywords": ["hardware shop profit", "hardware business", "हार्डवेयर दुकान कितना कमाती है"]},
 {"topic": "मोबाइल रिपेयर वाला असल में कितना कमाता है", "category": "Services", "setting": "A mobile repair counter", "myth": "छोटा काउंटर, छोटी कमाई", "angle": "Screen swaps and accessories sold to every walk-in carry the margin.", "visual_hooks": ["a cracked screen", "a tiny screwdriver", "a wall of covers"], "score": 7, "keywords": ["mobile repair shop income", "mobile repair business", "मोबाइल रिपेयर कितना कमाता है"]},
 {"topic": "बकरी पालन असल में कितना कमाता है", "category": "Farming & Pashu", "setting": "A goat farm before Eid", "myth": "बकरी पालो, बकरीद पर बेचो", "angle": "Feed, shelter and disease all year; one festival season decides the price.", "visual_hooks": ["a goat", "a fodder bundle", "a village market"], "score": 8, "keywords": ["goat farming profit", "bakri palan", "बकरी पालन कितना कमाता है"]},
 {"topic": "ट्रैक्टर किराए पर देने वाला कितना कमाता है", "category": "Transport & Heavy Vehicles", "setting": "A tractor rented by the hour at sowing time", "myth": "खेती के सीज़न में खूब काम", "angle": "Two short seasons of demand, EMI all year, and implements that earn extra.", "visual_hooks": ["a tractor in a field", "a plough", "a calendar"], "score": 7, "keywords": ["tractor rent business", "tractor income", "ट्रैक्टर किराया कितना कमाता है"]},
 {"topic": "ज्वेलर सोने पर कैसे कमाता है", "category": "Dukaan & Retail", "setting": "A family jewellery shop before Dhanteras", "myth": "सोना महँगा, तो ज्वेलर अमीर", "angle": "Making charges, wastage and exchange offers; the gold price itself is not the margin.", "visual_hooks": ["a gold necklace", "a small weighing scale", "an old ring"], "score": 8, "keywords": ["jeweller profit", "making charges explained", "ज्वेलर कितना कमाता है"]},
 {"topic": "प्लास्टिक रीसाइक्लिंग असल में कितना कमाती है", "category": "Recycling & Small Industry", "setting": "A small plastic recycling unit", "myth": "कचरे से सोना", "angle": "Buying sorted plastic, shredding, granules; electricity and steady supply decide the margin.", "visual_hooks": ["a sack of bottles", "a shredder", "a pile of granules"], "score": 8, "keywords": ["plastic recycling business", "plastic recycling plant profit", "प्लास्टिक रीसाइक्लिंग कितना कमाती है"]},
 {"topic": "आटा चक्की वाला असल में कितना कमाता है", "category": "Recycling & Small Industry", "setting": "A village flour mill", "myth": "चक्की तो चलती रहती है", "angle": "Per-kilo grinding charge, electricity, and packaged flour as the bigger opportunity.", "visual_hooks": ["a flour mill", "a sack of wheat", "a bag of atta"], "score": 7, "keywords": ["atta chakki business profit", "flour mill income", "आटा चक्की कितना कमाती है"]},
 {"topic": "रेस्टोरेंट वाले असल में कैसे कमाते हैं", "category": "Khana & Street Food", "setting": "A mid-size family restaurant", "myth": "खाना महँगा, तो मुनाफ़ा भी बड़ा", "angle": "Food is not the profit centre; drinks, desserts, menu design and table turnover are.", "visual_hooks": ["a menu card", "a cold drink bottle", "a table cleared fast"], "score": 9, "keywords": ["restaurant business profit", "restaurant owner income", "रेस्टोरेंट कितना कमाता है"]},
 {"topic": "वेडिंग प्लानर असल में कितना कमाता है", "category": "Services", "setting": "A big Indian wedding", "myth": "शादी में तो लाखों का खेल", "angle": "A fee on top plus commissions from venues, decorators and caterers.", "visual_hooks": ["a mandap", "a phone with vendor calls", "a flower arch"], "score": 7, "keywords": ["wedding planner income", "wedding planner business", "वेडिंग प्लानर कितना कमाता है"]},
 {"topic": "नेता जी की कमाई: क़ानूनी हिसाब", "category": "Neta & System", "setting": "An MLA's year: salary, allowances, election affidavit", "myth": "नेता बनते ही पैसा", "angle": "Only documented, legal income: salary, allowances, pension, assets declared in public affidavits. No named living person accused of anything.", "visual_hooks": ["a microphone", "an affidavit file", "a car with a flag"], "score": 7, "keywords": ["mla salary india", "politician income", "नेता कितना कमाते हैं"]}
]}
```

- [ ] **Step 4: Write `SKILL.md`**

Overwrite `.claude/skills/mafia-of-business-youtube/SKILL.md`:

````markdown
---
name: mafia-of-business-youtube
description: Operate the "Mafia of Business" Hindi YouTube channel end to end -- 3-5 minute 16:9 stickman story videos about how everyday Indian businesses and people actually make money (chai wala, gym, restaurant, politician...). Use this skill for ANY task on this channel: topic, research, Hindi script, narration, scenes, assembly, thumbnail, SEO metadata, or improvements. Trigger it even for one slice ("aaj ki script likho", "redo the thumbnail") and whenever Mafia of Business, kaise kamata hai, or an episode appears.
---

# Mafia of Business -- Autonomous Channel Operator

You are the sole producer, scriptwriter, scene director and editor of one Hindi YouTube channel, **Mafia of Business**: how the businesses and people every Indian knows actually make money, told as a story by an insider who knows the game. One video per run. You stop at a finished package in `output/<slug>/`; the operator posts it to YouTube by hand.

"Mafia" is a metaphor for the insider's playbook. The channel never glorifies crime and never teaches fraud.

## The one thing that matters most

Hisaab, told as a story. Break the myth everyone believes ("पंप खोल लो, बैठे-बैठे नोट गिनो") with simple money facts carried by a character (रमेश, introduced with "मान लीजिए"): one rupee number per beat, named costs (EMI, rent, diesel, staff), no formulas, no tables. If a sentence sounds like an accounts class, rewrite it as something that happens to रमेश.

## What wins (competitor research, 2026-10-01)

Two comparable Hindi channels grew fast on boring, hyper-local cash businesses (petrol pump 720K views, dumper 241K, poultry 69K, dhaba 62K) while abstract topics flopped (UPI, IPL, coaching, railways: under 2K). Same title template and same infographic thumbnail on every video. Stay in the six verticals of `topic-strategy.md`.

## Brand invariants

| Element | Locked value |
|---|---|
| Host | The boss stickman (`brand/host/host-reference-clean.jpeg`): black fedora with a gold band, thin suit outline, gold tie, two dot eyes, no mouth. Sent with every scene. |
| Palette | Black, white, gold `#D4A017`. Gold is the accent and the colour of money. No red, no other colour. |
| Art | Hand-drawn marker stickman on a white whiteboard, one or two simple props, lots of empty space. No on-image text (FLUX cannot draw Devanagari). |
| Voice | edge-tts `hi-IN-MadhurNeural`, male, locked in `channel_state.json`. |
| Language | Conversational Hindi in Devanagari. Common English business words stay English but in Devanagari (प्रॉफ़िट, मार्जिन, कस्टमर). Numbers as words. |
| Runtime | 180-300 s, target 240. Hard cap 300 s. |
| Aspect | 16:9, 1920x1080. |
| Audio | No music. Whoosh on scene cuts, reveal sting on [RAAZ], sparse money/food/market cues. |
| Thumbnail | `scripts/make_thumbnail.py` "hisaab" infographic: "<X> का हिसाब" title band, the scene in the centre, 3-4 money notes with gold arrows, gold frame. Same every episode. |

## Workspace

```
MafiaOfBusiness/
|-- channel_state.json     locked config; MongoDB supplies only counters
|-- brand/host/            boss stickman reference
|-- brand/ambience/        synthesized effects + manifest.json
|-- episodes/<slug>/       topic.json, 01_research, 02_script, 03_audio, 05_scenes, 07_edit, 08_publish
|-- output/<slug>/         FINISHED: video, thumbnail.png, captions.srt, metadata.json, posting.md
|-- scripts/               the pipeline
|-- reports/               changelog.md, experiments.md
```

Topics, counters and episode records live in MongoDB (`scripts/state_db.py`, db `mafia_of_business_pipeline`).

## Pipeline

0. Topic -- `topic-strategy.md`.
1. Research -- `research-and-facts.md`. `01_research/sources.md` is required.
2. Script + shotlist -- `script-formula.md`. Tags `[HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK]`. `scripts/check_script.py <slug>` must pass.
3. Narration -- `voice-and-audio.md`: `generate_narration_chunks.py`, `stitch_audio.py` (fails outside 180-300 s).
4. Scenes -- `visuals-and-animation.md`, `character-bible.md`: `generate_scenes.py`.
5. Assembly -- `edit-and-assembly.md`, `captions.md`, `ambience-sound.md`: `assemble_episode.py`.
6. Package -- `thumbnail-and-metadata.md`, `publishing-and-metadata.md`: `08_publish/metadata.json`.
7. Finalize -- `run_episode.py` runs 2-6, builds the thumbnail, then `finalize_episode.py` (verifies the video, writes `output/<slug>/` and `posting.md`, records MongoDB `ready`, writes `08_publish/finalize_log.json`) and `cleanup_episode.py`.
8. Log -- `reports/changelog.md`.

## Quality gate

1. Runtime 180-300 s; audio -14 LUFS; no dead air.
2. Every scene: boss on-model (black fedora with gold band, no mouth), only black/white/gold, no shading, no on-image text, at most two characters. Reroll bad beats.
3. Scenes 5-7 s each.
4. Every rupee figure, date and "first" claim traces to `01_research/sources.md`, or is said as an estimate ("अंदाज़न", "लगभग") with a round range.
5. First sentence: a rupee shock or a question. The [RAAZ] secret is teased in [HOOK] and paid off.
6. Thumbnail beat (default 1) shows the boss at the business with the subject centred and empty space left and right (for the annotations). Title follows the series template; title and thumbnail promise exactly what the video delivers.
7. `metadata.json` complete (see `publishing-and-metadata.md`).
8. Captions legible; ambience never masks the voice.

Known accepted risk: no automated visual QA. Look at every generated PNG yourself.

## When to stop and ask the human

- A topic would name a living person in a critical light, accuse a named company of wrongdoing without a court or regulator finding, or touch caste or religion beyond a respectful documented overview.
- Sources conflict on a central figure and you cannot resolve it.
- A brand change is implied (voice, art, palette, format).
- A credential appears in a chat message, or anything would cost money, need terms signed, or post anywhere.

Everything else: decide, act, log it.

## Reference index

| File | Read it when |
|---|---|
| `setup-and-state.md` | How state is stored |
| `topic-strategy.md` | Choosing a topic; refilling the bank |
| `research-and-facts.md` | Gathering sources; the fact gate |
| `script-formula.md` | Writing the Hindi script |
| `voice-and-audio.md` | chunk_plan.json, narration, stitching |
| `character-bible.md` | Any character or style question |
| `visuals-and-animation.md` | Shotlist, scene generation, rerolls |
| `ambience-sound.md` | ambience_plan.json overrides |
| `edit-and-assembly.md` | Running assemble_episode.py |
| `captions.md` | Debugging captions |
| `thumbnail-and-metadata.md` | Thumbnail, title, description, tags, SEO |
| `publishing-and-metadata.md` | metadata.json fields and finalize |
| `compliance-and-safety.md` | Any factual claim, politicians, brands, YouTube policy |
| `analytics-and-growth.md` | Operator notes on performance |
````

- [ ] **Step 5: Write `script-formula.md`**

Overwrite `references/script-formula.md`:

````markdown
# Script formula (Hindi)

The script is the video. Assume the viewer's thumb is over the back button the whole time.

## Specs

- **Length:** about 480-600 Hindi words for 240 s (`hi-IN-MadhurNeural` speaks ~140 words/min). `stitch_audio.py` fails over 300 s or under 180 s: trim or add, never speed the voice.
- **Language:** conversational Hindi in Devanagari, the way people talk at a chai stall, not textbook shuddh Hindi. English business words stay English but in Devanagari: प्रॉफ़िट, मार्जिन, कस्टमर, ब्रांड.
- **Numbers as words:** "दस रुपये", "पचास हज़ार", "दो लाख". Never digits (`check_script.py` rejects them).
- **Hisaab, not math:** one rupee number per beat, carried by the character. Named costs (ईएमआई, किराया, डीज़ल, स्टाफ़, बिजली) are good. No formulas, no stacked percentages, no tables.
- **Voice:** second person, present tense. "आप सुबह पाँच बजे दुकान खोलते हैं..." beats "दुकानदार सुबह दुकान खोलता था".
- **Sentences:** short. Vary rhythm. A three-word line after a long one lands hard: "और यहीं है खेल।"
- **No filler:** no "नमस्कार दोस्तों", no "आज के इस वीडियो में", no channel intro. They cost the seconds you can least afford.
- **No calculations on screen or in speech:** if a number needs a calculation to understand, replace it with a comparison ("एक कप पर जितना कमाता है, उतने में आपका बिस्कुट आता है").

## Structure

### [HOOK] (0:00-0:20) -- myth, then one number
Open on the belief everyone has, then break it with one number, then tease the secret:
- "पेट्रोल पंप खोल लो, बैठे-बैठे नोट गिनो... सुनने में कितना आसान लगता है ना?"
- "पर पंचानवे रुपये के पेट्रोल में मालिक को मिलते हैं सिर्फ़ साढ़े चार रुपये।"
- "और आख़िर में वो एक बात, जिस पर पूरा धंधा टिका है।"

### [DUNIYA] (0:20-1:00) -- the character and the setup
Introduce a hypothetical owner with a common name, always as an example: "मान लीजिए रमेश..." (never presented as a real person). What he invests, where, why he started. Put the viewer there: "आपने भी देखा होगा..."

### [KHEL] (1:00-3:00) -- पैसा कहाँ बनता है, कहाँ डूबता है
First the money coming in, then the leaks: EMI, rent, staff, bijli, diesel, wastage, udhaar. Each leak is a small scene with रमेश and one rupee number. Include one comparison (highway vs gaon, small vs big, good month vs bad month).

### [RAAZ] (3:00-3:45) -- the hero product or the hidden twist
The one non-obvious thing the business really runs on: the dal that carries the dhaba, the papad bought at डेढ़ रुपये and sold at दस, the tanker that must be paid before a single litre is sold, the one bad month that sinks a dumper owner. Slow down. Pay off the hook's tease explicitly.

### [SABAK] (last 20-40 s) -- rules and the payoff
Two or three simple rules (मेन्यू छोटा रखो, इमरजेंसी फ़ंड, बार-बार आने वाला ग्राहक मार्जिन से बड़ा). The payoff line: "ये धंधा पेट्रोल का नहीं, कैश-फ़्लो और भरोसे का है।" One specific comment question ("आपके शहर में एक प्लेट मोमो कितने की है?"). Name the next episode ("अगली बार: डंपर वाले का पूरा हिसाब"). Ask for the subscribe once, about the series.

## Retention rules

- Mark the script every 30 seconds (~70 words). At each mark ask: what changed? If nothing, add a turn, a question to the viewer, a new character or a new place.
- Never stack two abstract lines without something the stickman can act out.
- Kill the second-best example. Three great leaks beat five okay ones.
- Every estimate is said as one: "अंदाज़न", "लगभग", with a round range.

## Format of `02_script/script.md`

```markdown
# चाय वाला असल में कितना कमाता है
Target runtime: 4:00

[HOOK]
1. दस रुपये की चाय, इसमें क्या कमाई... सुनने में तो यही लगता है ना?
2. पर बनाने में लगते हैं सिर्फ़ तीन रुपये। और असली कमाई चाय से होती भी नहीं। वो राज़ आख़िर में।

[DUNIYA]
3. ...

[KHEL]
...

[RAAZ]
...

[SABAK]
...
```

Beat numbers are ASCII digits followed by a dot; narration text has no digits. Run `python3 scripts/check_script.py <slug>` after writing.
````

- [ ] **Step 6: Write `topic-strategy.md`**

Overwrite `references/topic-strategy.md`:

```markdown
# Topic strategy

## What belongs on this channel

"Kaise kamata hai?" for **boring, hyper-local, cash businesses from Bharat**: the businesses every Indian passes daily, where everyone has a guess and nobody has a good video. The test: is there a myth ("बैठे-बैठे नोट गिनो") that simple hisaab overturns?

Evidence (operator's research, 2026-10-01): comparable channels' breakouts were petrol pump (720K, 65x average), dumper (241K), poultry (69K), dhaba (62K), mushroom (60K), kirana (44K), transport (42K). Abstract or distant topics flopped: UPI 673, IPL 688, coaching 809, luxury 903, cashback 918, railways 1.7K, black money 2.1K. Do not queue apps, finance concepts, sports leagues, luxury or government systems.

## Verticals (the `category` field; each is a YouTube playlist)

1. **Farming & Pashu** -- poultry, mushroom, fish, dairy, goat, bee-keeping.
2. **Transport & Heavy Vehicles** -- dumper/tipper, truck, JCB, tractor rental, school van, e-rickshaw.
3. **Khana & Street Food** -- chai, momo, pani puri, dhaba, juice, sweet shop, restaurant.
4. **Dukaan & Retail** -- kirana, petrol pump, medical store, hardware, jeweller.
5. **Services** -- barber, laundry, gym, tent house, mobile repair, wedding planner.
6. **Recycling & Small Industry** -- kabadiwala, plastic recycling, cold storage, atta chakki, brick kiln.
7. **Neta & System** -- the politician episode only (legal income, `compliance-and-safety.md`); not before episode 10.

Never two episodes in a row from the same vertical. Farming and heavy vehicles drew most of one competitor's views: keep at least one of every three episodes in those two.

## Scoring (1-10 each, average, queue at 7.0+)

- **Relatability** -- does every Indian pass this business?
- **Myth gap** -- is there a belief the hisaab overturns, and a [RAAZ] twist?
- **Search demand** -- do people type "X business profit" / "X kitna kamata hai"? Check YouTube search suggestions.
- **Visual** -- can the boss stickman act it out with one or two props?

## Series chaining

Each [SABAK] names the next topic; pick it next unless it breaks the vertical rotation or compliance.

## Keywords and myth

Every topic carries `keywords` (3-5 query phrases mixing Hinglish, Devanagari and English) and `myth` (the belief the hook breaks). Copy both into `topic.json`.

## Refilling the bank

When `topics-count` shows fewer than 8 queued, add topics with `python3 scripts/state_db.py topic-add` (JSON list on stdin) until more than 15 are queued. Each item: `topic` (Devanagari, "<X> असल में कितना कमाता है"), `category` (a vertical above), `setting`, `myth`, `angle`, `visual_hooks` (3), `score`, `keywords` (3-5). Never a topic already used.
```

- [ ] **Step 7: Write `thumbnail-and-metadata.md` (SEO)**

Overwrite `references/thumbnail-and-metadata.md`:

````markdown
# Thumbnail, title, metadata and SEO

Packaging decides whether the video is clicked; retention decides whether YouTube shows it to more people. Never trade one for the other: no promise the video does not keep. Same template every episode, so the series is recognisable.

## Thumbnail: the "hisaab" infographic (`scripts/make_thumbnail.py`, run by `run_episode.py`)

- White whiteboard, gold frame. Title band on top: `thumbnail_text` = "<X> का हिसाब" (2-4 Devanagari words), `thumbnail_accent_word` = "हिसाब" or the business name, drawn in gold, gold underline.
- Centre: the thumbnail scene (`thumbnail_beat`, default 1): the boss at the business, subject centred, empty space left and right.
- `thumbnail_annotations`: 3-4 money notes, each 2-3 words, ~12 characters max, placed left and right with gold arrows: "₹4.5/लीटर", "पहले पेमेंट", "लोन ईएमआई", "दाल = हीरो", "बर्बादी ₹2,500/दिन". Digits and ₹ are fine; **no Latin letters** (the font has none; the script refuses them): write ईएमआई, not EMI. Every figure must be in `sources.md` or said in the video as an estimate.
- Legibility: open `thumbnail-210x118-preview.png`; if the title band isn't readable at that size, shorten it.

## Title: one series template

`<X> वाला असल में कितना कमाता है? | <X in English> Business Profit in Hindi`

e.g. `पेट्रोल पंप वाला असल में कितना कमाता है? | Petrol Pump Business Profit in Hindi`. Adapt the Devanagari half to the business ("<X> असल में कितना कमाता है?", "<X> की असली कमाई?"), keep the English half. 45-80 characters. Put two variations in `title_alternates` for YouTube's Test & Compare.

## Description

```
[Myth hook in Hindi + the main Hinglish search phrase, within the first 150 characters.]

[2-3 Hindi sentences on what the video reveals, without giving away the RAAZ.]

⏱️ Chapters
0:00 [hook label in Hindi]
0:xx रमेश की कहानी
0:xx पैसा कहाँ बनता है, कहाँ डूबता है
0:xx असली राज़
0:xx सबक

🔍 आपके सवाल (Your Queries):
[15-20 search phrases, one per line: Hinglish, Devanagari and English variants]

📚 Sources
- [source] -- [URL]

🎩 Mafia of Business -- हर धंधे का असली हिसाब, हिंदी में।

#MafiaOfBusiness #BusinessModel #[TopicHashtag]
```

Chapters come from `03_audio/timings.json` section start times; at least four, first at 0:00. Leave out subscribe/playlist links; the operator adds them.

## Tags

15-25, within YouTube's 500-character limit: the main query in Hinglish, Devanagari and English ("petrol pump kitna kamata hai", "पेट्रोल पंप कितना कमाता है", "petrol pump business profit"), cost/investment variants ("petrol pump investment", "petrol pump dealer margin"), common misspellings, and series terms ("business model in hindi", "Mafia of Business").

## Playlist

`playlist` = the topic's vertical (`topic-strategy.md`). `posting.md` tells the operator which playlist to add the video to.

## Engagement package (in `metadata.json`, copied into `posting.md`)

- `pinned_comment`: a bonus fact plus a question, in Hindi.
- `community_post`: a one-line poll ("पेट्रोल पंप मालिक को एक लीटर पर कितना मिलता है? A) ₹20 B) ₹10 C) ₹5 से कम").
- `shorts_hook`: `{"start": 0.0, "end": <end of the last [HOOK] or first [DUNIYA] beat, 30-55 s>}` from `timings.json`, for a hand-cut Short.
````

- [ ] **Step 8: Write `publishing-and-metadata.md`**

Overwrite `references/publishing-and-metadata.md`:

```markdown
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
```

- [ ] **Step 9: Write the remaining rewritten references**

`references/voice-and-audio.md` (overwrite):

```markdown
# Voice and audio

- Voice: edge-tts `hi-IN-MadhurNeural` (fallback `hi-IN-SwaraNeural`, only after logging why in `reports/changelog.md`). Locked in `channel_state.json`.
- Section presets (rate/volume/pitch) per tag: `hook` slow and weighty, `duniya` neutral, `khel` faster, `raaz` slower and conspiratorial, `sabak` calm. A beat with no tag above it uses `khel`.
- `03_audio/chunk_plan.json`: `{"chunks": [{"id": 1, "beats": [1, 2], "text": "<the beats' Hindi text joined>"}, ...]}`, 2-3 sentences per chunk, never across a section tag.
- `generate_narration_chunks.py <slug>` writes `chunk_XXXX.mp3` + `.wordbounds.jsonl` (word timing for captions); `stitch_audio.py <slug>` trims, joins with 0.4 s gaps (0.8 s at section breaks), masters to -14 LUFS and writes `timings.json`, `word_timings.json`.
- `stitch_audio.py` exits 3 when the narration is outside 180-300 s. Fix the script, delete the changed chunks' mp3/jsonl, rerun both.
- Hindi pronunciation: write numbers as words; write English business words in Devanagari (प्रॉफ़िट); if a word is mispronounced, respell it phonetically in Devanagari and regenerate that chunk.
```

`references/character-bible.md` (overwrite):

```markdown
# Character bible

## The Boss (host)

- Reference: `brand/host/host-reference-clean.jpeg` (approved 2026-10-01), sent with every scene by `scenes/flux_orchestrator.py`.
- Look: thin black stick body and limbs, round white head, two black dot eyes, **no mouth**, black fedora with a gold band, thin black suit-jacket outline, small solid gold tie.
- Personality (shown through poses, not faces): calm, knowing, slightly amused -- the insider who explains the game. Leans on counters, points at props, counts coins, tips the hat.
- Never: a mouth, a red hat, coloured clothes beyond the gold tie and band, guns or crime props.

## Other characters

- Plain stickmen (no hat) as customers, shopkeepers, workers, suppliers. Give them one identifying prop: an apron for the chai wala, a dumbbell for the gym trainer, a turban or a sari outline where the story needs it, drawn simply and respectfully.
- At most two characters per shot; write conversations as shot/reverse-shot pairs.

## Style lock

The `image_prompt_suffix` in `channel_state.json` is prepended to every prompt. Black, white and gold only. Money (coins, notes, ₹ bags) is drawn in gold. No text, letters or numbers in the image.
```

`references/compliance-and-safety.md` (overwrite):

```markdown
# Compliance and safety

## Facts

- Every rupee figure, date, name and "first" claim comes from `01_research/sources.md` (news reports, annual reports, government data, court or regulator orders, documented interviews).
- Undocumented figures are estimates: say "अंदाज़न"/"लगभग" with a round range, and record the basis in `sources.md`. Never an invented exact figure.

## Politicians and officials

- Only legal, documented income: salary, allowances, pension, assets declared in public election affidavits, aggregate reports (e.g. ADR analyses).
- No named living person is accused of anything. Corruption appears only as reported, sourced, aggregate facts, called "आरोप" when it is an allegation.

## Hypothetical characters

- रमेश, राजू, शर्मा जी are examples. Introduce them with "मान लीजिए" and never present them as real people or real interviews.
- Their numbers come from `sources.md` (or are said as estimates with a range).

## "Mafia" is a metaphor

- No glorifying real crime; no how-to for fraud, tax evasion, adulteration or cheating customers.
- A scam can be explained so viewers protect themselves, ending on how to spot it.

## Brands and companies

- Company-level facts from filings, annual reports and reputable press.
- No claim that a named company cheats customers unless a court or regulator found so, cited in the video.
- Never attack a living founder.

## Religion and caste

- Never a business angle on caste. Temple-trust topics: respectful, documented, aggregate only.

## YouTube

- Altered/synthetic content disclosure: yes (AI voice and images). Not made for kids.
- No copyrighted music, logos drawn as-is, or real photos.
```

`references/analytics-and-growth.md` (overwrite):

```markdown
# Analytics and growth

The pipeline has no YouTube data, and the agent never invents performance numbers. Operator notes (pasted into a run, or in `reports/experiments.md`) are the only signal.

## What the agent can do

- Choose topics per `topic-strategy.md` with real search demand.
- Make the first 20 seconds earn the rest (`script-formula.md`): retention is the lever.
- Change one variable at a time when trying something new; log it in `reports/experiments.md`.

## For the operator (outside the pipeline)

Post on a fixed schedule at 6-9 PM IST; cut a Short from `shorts_hook`; add every episode to its vertical's playlist; pin the comment early; post the community poll; reply to early comments; after 48 hours, if CTR is low, try a `title_alternates` entry via Test & Compare.
```

- [ ] **Step 10: Edit the kept references**

For each file below, apply exactly these edits (read the file first; keep everything else):

- `research-and-facts.md`: replace any channel name with "Mafia of Business"; replace mystery/legend wording with: "Sources for money facts: annual reports, company filings, government data (e.g. MyNeta/ADR affidavit summaries, ministry pages), reputable business press, documented interviews. Typical costs and prices for street businesses may come from several news features or documented vendor interviews; record each as an estimate with its basis." Keep the rule that `01_research/sources.md` is required.
- `visuals-and-animation.md`: replace `red`/`red-fedora` with the boss description from `character-bible.md`; replace "6-10 s" with "5-7 s"; add "Indian settings (petrol pump, dhaba, poultry shed, dumper, kirana, gym) as one or two simple props." Replace any thumbnail-beat composition rule with "the thumbnail beat (default 1) shows the boss at the business, subject centred, empty space left and right for the annotations". Remove any raphael mention.
- `ambience-sound.md`: replace section names with `hook/duniya/khel/raaz/sabak`, `climax_reveal` with `raaz`, and the keyword list with the Devanagari stems from `channel_state.json` (`coin_clink`, `cash_register`, `sizzle`, `crowd_murmur`, `paper_rustle`); note "`*` = prefix match on NFC-normalized Devanagari, matras kept."
- `captions.md`: font Noto Sans Devanagari, gold highlight `&H0017A0D4`, 2-4 words per caption, danda dropped from display, no uppercase.
- `edit-and-assembly.md`: output `07_edit/mafia-of-business-<slug>.mp4`; target 240 s.
- `setup-and-state.md`: db `mafia_of_business_pipeline`; status values `pending/ready/posted`; `finalize_log.json` replaces `upload_log.json`; remove slot commands; add `episode-posted`; `.env` keys `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`, `MONGODB_URI`.

Then run: `grep -rn -i "redhat\|red fedora\|content lab\|upload_log\|cold_open\|rising_mystery\|climax_reveal\|raphael\|slot" .claude/skills/mafia-of-business-youtube` -- expected: no output.

- [ ] **Step 11: Write `cycle_prompt.md`**

Overwrite `MafiaOfBusiness/cycle_prompt.md`:

```markdown
Operate the Mafia of Business channel autonomously for one cycle, and do not stop until a NEW episode, made in this cycle, is finalized into output/<slug>/. You are the supervisor: nobody will step in, so when something fails you diagnose it and find another way.

Use the mafia-of-business-youtube skill (../.claude/skills/mafia-of-business-youtube/SKILL.md) for every judgment call; read its references/*.md files before the matching stage. Everything runs from this directory (MafiaOfBusiness/). python3, ffmpeg and edge-tts are on PATH.

DONE MEANS: `python3 scripts/pending_episodes.py` exits 0 AND this episode's `08_publish/finalize_log.json` shows status ok AND `output/<slug>/posting.md` exists. Print all three before claiming completion. If you cannot get there after several different approaches, say so with the concrete blocker.

STATE: Topics live only in MongoDB. Use `python3 scripts/state_db.py`: `topics [queued|used|rejected]`, `topics-count`, `topic-add` (JSON object or list on stdin, each with `topic`, `category`, `setting`, `score`, `angle`, `visual_hooks`, `keywords`; duplicates skipped), `topic-use "<name>"`, `topic-reject "<name>" "<reason>"`. channel_state.json counters and unfinished episodes' text files are loaded from MongoDB before you start and saved back when the run ends. Never run git commit or git push. Never post anywhere.

FILE RULES: use `.scratch/` in this directory for temporary files.

1. Resume check: run `python3 scripts/pending_episodes.py`. If it prints a slug, resume it from whichever stage has missing outputs. If it prints nothing, start a new episode.

2. Run `python3 scripts/state_db.py topics-count`. If `queued` is under 8, refill per topic-strategy.md's "Refilling the bank" until above 15.

3. Pick the next topic per topic-strategy.md (prefer the topic the previous episode's [SABAK] promised; never the same vertical twice in a row: `python3 scripts/state_db.py recent 3`). Slug: `YYYY-MM-DD-<short-english-slug>`. Research first: `episodes/<slug>/01_research/sources.md` per research-and-facts.md. Then write `topic.json` (with `keywords` and `myth`), `02_script/script.md` + `shotlist.json` (script-formula.md, Hindi, tags [HOOK] [DUNIYA] [KHEL] [RAAZ] [SABAK], myth-then-number hook, a "मान लीजिए" character, numbers as words, ~480-600 words; beat 1's shot is the thumbnail scene: boss at the business, subject centred), and run `python3 scripts/check_script.py <slug>` until it prints `script.md ok`. Write `03_audio/chunk_plan.json` (voice-and-audio.md). Check compliance-and-safety.md. Mark the topic used: `python3 scripts/state_db.py topic-use "<topic>"`.

4. `python3 scripts/generate_narration_chunks.py <slug>` then `python3 scripts/stitch_audio.py <slug>`. If stitch exits 3 (runtime outside 180-300 s), edit the script and chunk plan, delete the changed chunks' files, and rerun both. Then write `08_publish/metadata.json` (publishing-and-metadata.md, thumbnail-and-metadata.md) using `03_audio/timings.json` for chapters and `shorts_hook`.

5. `python3 scripts/generate_scenes.py <slug>`. Look at every `05_scenes/scene_*.png` against SKILL.md's quality gate (boss on-model, black/white/gold only, no text, at most two characters) and reroll bad beats with `--beats N --seed <new>`.

6. `python3 scripts/run_episode.py <slug>`. It is idempotent: it checks the script, skips finished audio/scenes, assembles, builds the thumbnail, finalizes into output/<slug>/ and cleans up.

RECOVERY:
- A scene's `05_scenes/_flux_debug/scene_XXXX.error.txt` shows a failure: reroll it. If it says the Cloudflare daily quota is used up, stop and report it (the quota resets at 05:30 IST); finished beats are skipped on the next run.
- A stage errors: read the error, fix the cause, rerun that stage.
- Never re-create an episode that already exists.

7. Log deliberate deviations in `reports/changelog.md`.

8. Report the DONE MEANS evidence and the output folder path.

Stop and message the operator only for SKILL.md's "When to stop and ask" cases.
```

- [ ] **Step 12: Write `AGENTS.md` and `README.md`**

Overwrite `AGENTS.md`:

```markdown
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
```

Overwrite `README.md`:

````markdown
# Mafia of Business

Makes one Hindi YouTube video per run: how everyday Indian businesses and people actually make money (chai wala, gym, restaurant, politician...), told as a 3-5 minute stickman story. Nothing is posted anywhere; the finished package lands in `MafiaOfBusiness/output/<slug>/` and you post it by hand.

Each run: an opencode agent picks a topic from the MongoDB bank, researches it and writes a Hindi script and SEO metadata; edge-tts (`hi-IN-MadhurNeural`) records the narration; FLUX.2 klein on Cloudflare Workers AI draws the scenes with the boss stickman as a reference image; ffmpeg renders 1920x1080 with Devanagari captions and light ambience (no music); a Devanagari thumbnail is built; the package is copied to `output/<slug>/`.

## Setup

1. `.env` in this folder (gitignored):
   ```
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_API_TOKEN=...
   MONGODB_URI=...
   ```
2. Installed: `ffmpeg`, `opencode` (`~/.opencode/bin`), font Noto Sans Devanagari (`sudo apt install fonts-noto-core`).
3. Optional env: `OPENCODE_MODEL`, `MAX_ATTEMPTS` (default 4), `IMAGE_BACKEND` (`flux` default), `CLOUDFLARE_IMAGE_MODEL`, `MONGODB_DB`.

Cloudflare's free tier is 10,000 neurons a day for this account; a ~45-scene episode can use most of it. A run stopped by the quota resumes with `./make-video` after 05:30 IST.

## Running

```bash
./make-video
```

## Posting

Open `MafiaOfBusiness/output/<slug>/posting.md`: it has the title, alternates, description, tags, playlist, pinned comment, community poll, Shorts range and a checklist. Post daily if you can (both reference channels grew on one video a day). After posting:

```bash
cd MafiaOfBusiness && ../.venv/bin/python scripts/state_db.py episode-posted <slug> <youtube-url>
```

## Tests

```bash
.venv/bin/python -m pytest -q
```
````

- [ ] **Step 13: Run tests**

Run: `.venv/bin/python -m pytest -q`
Expected: all pass. If `test_docs_reference_current_pipeline_only` names a stale string, fix that file; do not weaken the test.

- [ ] **Step 14: Commit**

```bash
git add -A && git commit -m "Hindi channel skill, SEO packaging rules, cycle prompt, 32-topic seed, docs"
```

---

### Task 11: Live verification (real services)

**Files:**
- No code. Evidence goes to `MafiaOfBusiness/reports/changelog.md`.

**Interfaces:**
- Consumes: everything above; `.env` credentials; MongoDB; Cloudflare; edge-tts; opencode.

- [ ] **Step 1: Mongo connection and seeding**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action/MafiaOfBusiness
../.venv/bin/python scripts/state_db.py topics-count
```

Expected: `{"queued": 32, "used": 0, "rejected": 0}`. If `queued` is not 32 the DB already existed with other data: stop and report (never drop it).

- [ ] **Step 2: Full local run**

```bash
cd /home/devdevil/development/kaggle-experiment/mafia_of_business_gh_action
./make-video
```

Run in the background (it takes 20-60 minutes); watch `MafiaOfBusiness/.scratch/local_run_*.log`. Expected end: `=== episode finalized (0 -> 1) ===`.

- [ ] **Step 3: Inspect the package by eye**

```bash
ls -la MafiaOfBusiness/output/*/
ffprobe -v error -show_entries stream=codec_type,width,height:format=duration -of compact MafiaOfBusiness/output/*/*.mp4
ffmpeg -loglevel error -y -ss 30 -i MafiaOfBusiness/output/*/*.mp4 -frames:v 1 MafiaOfBusiness/.scratch/frame_30s.png
ffmpeg -loglevel error -y -ss 150 -i MafiaOfBusiness/output/*/*.mp4 -frames:v 1 MafiaOfBusiness/.scratch/frame_150s.png
```

Read `frame_30s.png`, `frame_150s.png`, `output/<slug>/thumbnail.png` and `posting.md`. Confirm: 1920x1080, duration 180-300 s, captions are Devanagari with correctly joined conjuncts and a gold highlight, the boss is on-model, the thumbnail's Devanagari and ₹ render, `posting.md` is complete Hindi/Hinglish. Listen to the first 20 s (`ffplay -t 20 <mp4>` or open it) for Hindi voice quality.

- [ ] **Step 4: Mongo record**

```bash
cd MafiaOfBusiness && ../.venv/bin/python scripts/state_db.py recent 1
```

Expected: `<slug>\tready\t<output dir>`.

- [ ] **Step 5: Log and commit**

Append to `MafiaOfBusiness/reports/changelog.md` a dated entry: first live episode slug, runtime, number of scene rerolls, any manual fixes and anything that looked wrong. Then:

```bash
cd .. && git add MafiaOfBusiness/reports/changelog.md && git commit -m "First live Mafia of Business episode: verification notes"
```

If any check in Step 3 fails, fix the cause in the owning task's code with a test, rerun `python3 scripts/run_episode.py <slug>` (finalize is idempotent only after success, so a failed finalize simply reruns), and record the fix in the changelog.
