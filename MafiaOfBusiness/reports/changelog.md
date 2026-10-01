# Changelog

## 2026-10-01 -- episode 1 finalized: 2026-10-01-petrol-pump (3:18, 198.4 s)

First episode of the channel. Topic: पेट्रोल पंप वाला असल में कितना कमाता है
(Dukaan & Retail). Script 27 beats / 530 words, check_script ok first pass
after expanding KHEL from 22 to 27 beats (first draft was 411 words, would
have stitched under 180 s). output/2026-10-01-petrol-pump/ has video,
thumbnail.png, captions.srt, metadata.json, posting.md. SABAK promises the
dumper episode next.

Deliberate deviations / recovery notes:
- Cloudflare Workers AI free daily quota (10,000 neurons) was exhausted
  mid-QA (~35 generations: 27 first-pass + 7 rerolls + 1 dry run). Quota
  resets 05:30 IST. All 27 beats already had images, so the pipeline could
  finish; only polish rerolls were blocked.
- Rerolled with new seeds: scene 1 (mouth on boss, thumbnail beat -- now
  clean), scene 10 (3 characters -> 2, one worker), scene 22 (off-model
  cartoon customer face + hand-mirror prop -> plain stickman handshake),
  scene 25 (gibberish baked-in jar labels "9ATH!"/"PANU" -> plain pots).
- Scene 25 reroll came back with brown terracotta pots (palette violation).
  No quota left to reroll, so fixed locally with PIL: desaturated the
  brown hue band to neutral grey (original backed up at
  .scratch/scene_0025.orig.png). Two faint orange highlight streaks remain
  on the left pots -- accepted.
- Scenes 10/22 rerolls still show a tiny neutral mouth dash on the boss
  (negative prompt already says no mouth; dice roll kept landing it).
  Accepted: fedora/gold band/suit/tie/dot eyes all correct, dash reads as
  neutral at video scale. If FLUX keeps adding mouths, consider a "no mouth,
  blank face" emphasis in the prompt builder.
- Shotlist descriptions for beats 10/22/25 were simplified in
  02_script/shotlist.json (source of truth) per the two-character rule.

## 2026-10-01 -- forked from RedHat Engineer

This repo was forked from `../imagine_error_gh_action/` (the RedHat Engineer
pipeline) for the Hindi channel Mafia of Business. Design:
`docs/superpowers/specs/2026-10-01-mafia-of-business-design.md`. Local only:
no Content Lab upload, no GitHub Actions; finished videos go to
`MafiaOfBusiness/output/<slug>/`, state to MongoDB `mafia_of_business_pipeline`.

## 2026-10-01 -- first live episode: 2026-10-01-petrol-pump

First end-to-end run of `./make-video` (opencode agent -> Hindi script -> narration -> FLUX scenes -> assembly -> thumbnail -> finalize). Result: 1920x1080, 198 s (3:18), `output/2026-10-01-petrol-pump/`, MongoDB `ready`. Checked by eye: boss on-model, black/white/gold only, Devanagari captions shaped correctly with gold highlight, annotated thumbnail renders; script follows the myth -> hisaab -> raaz -> rules structure with estimates labelled.

Defects found by the live run and fixed:
- libass default shaping mangled Devanagari (क्षत्रिय -> क्षत्रयि); captions now burn in via the `ass` filter with `shaping=complex` (test renders a real frame).
- `make-video` font check was flaky under `pipefail` (`fc-list | grep -q`); now captures output first.
