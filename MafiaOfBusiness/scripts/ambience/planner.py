"""Decides which ambience cue plays on which beat. Sparse by design --
most beats get nothing. Priority order (highest first): a fixed
cold-open atmosphere cue, a reveal sting at the climax, a heartbeat
building into it, then keyword-triggered cues from the episode's own
words/descriptions. Separately, a soft whoosh lands on every scene cut
(ambience.transitions) -- the one cue that is deliberately not sparse.
Manual overrides (02_script/ambience_plan.json) always win over anything
auto-placed. Ported in shape from Dmoo Way's sfx/planner.py. The fixed
cold-open wind and pre-reveal heartbeat are mystery-atmosphere cues;
channel_state.json's ambience.disable switches them off channel-wide."""
from __future__ import annotations

import random
import re


def _norm(word: str) -> str:
    return re.sub(r"[^a-z0-9$]", "", word.lower())


def _keyword_index(keywords: dict[str, list[str]]) -> list[tuple[re.Pattern, str]]:
    index = []
    for sfx, patterns in keywords.items():
        for pat in patterns:
            if pat.endswith("*"):
                regex = re.compile(f"^{re.escape(pat[:-1])}")
            else:
                regex = re.compile(f"^{re.escape(pat)}$")
            index.append((regex, sfx))
    return index


def _beat_at(beats: list[dict], t: float) -> dict:
    for b in beats:
        if b["start"] <= t < b["end"]:
            return b
    return beats[-1]


def _resolve_manual(cue: dict, beats: list[dict], words: list[dict] | None) -> float:
    if "t" in cue:
        return cue["t"]
    if "beat" in cue:
        for b in beats:
            if b["beat"] == cue["beat"]:
                return b["start"]
        raise ValueError(f"unknown beat in override: {cue['beat']}")
    if "word" in cue:
        occurrence = cue.get("occurrence", 1)
        seen = 0
        for w in words or []:
            if _norm(w["text"]) == _norm(cue["word"]):
                seen += 1
                if seen == occurrence:
                    return w["start"]
        raise ValueError(f"word {cue['word']!r} occurrence {occurrence} not found")
    raise ValueError(f"cue needs t/beat/word: {cue!r}")


def auto_cues(beats: list[dict], words: list[dict] | None, config: dict) -> list[dict]:
    cues: list[dict] = []
    if not beats:
        return cues

    # 1. A fixed atmosphere cue at the very start -- always present.
    cues.append({"sfx": "wind", "t": beats[0]["start"], "reason": "cold_open_atmosphere"})

    # 2. Reveal sting at the first climax_reveal beat (skip if it's the first beat).
    reveal_beat = next((b for b in beats if b["section"] == "climax_reveal"), None)
    if reveal_beat and reveal_beat is not beats[0]:
        cues.append({"sfx": "reveal_sting", "t": reveal_beat["start"], "reason": "reveal"})
        # 3. Heartbeat building in, 2 beats before the reveal if there's room.
        reveal_index = beats.index(reveal_beat)
        if reveal_index >= 2:
            build_beat = beats[reveal_index - 2]
            cues.append({"sfx": "heartbeat", "t": build_beat["start"], "reason": "building_dread"})

    # 4. A soft whoosh on every scene cut (each beat after the first), unless
    # the incoming beat's section already has its own cue (the reveal sting).
    # Variant and a small gain jitter are derived from the beat number, so a
    # re-render is reproducible but consecutive cuts don't sound identical.
    transitions = config.get("transitions") or {}
    if transitions.get("enabled"):
        variants = transitions["variants"]
        jitter = transitions.get("gain_jitter_db", 0.0)
        skip = set(transitions.get("skip_sections", []))
        for b in beats[1:]:
            if b["section"] in skip:
                continue
            rng = random.Random(b["beat"])
            cues.append({
                "sfx": variants[b["beat"] % len(variants)], "t": b["start"],
                "gain_db": round(rng.uniform(-jitter, jitter), 1),
                "reason": f"scene_cut beat {b['beat']}", "transition": True,
            })

    # 5. Keyword cues from the transcript (word-level if available, else per-beat description).
    index = _keyword_index(config["keywords"])
    if words:
        for w in words:
            token = _norm(w["text"])
            for regex, sfx in index:
                if regex.match(token):
                    cues.append({"sfx": sfx, "t": w["start"], "reason": f"keyword '{w['text']}'", "keyword": True})
                    break
    else:
        for b in beats:
            for token in re.findall(r"[a-zA-Z']+", b.get("text", "")):
                normed = _norm(token)
                for regex, sfx in index:
                    if regex.match(normed):
                        cues.append({"sfx": sfx, "t": b["start"], "reason": f"keyword '{token}'", "keyword": True})
                        break

    return cues


def plan(beats: list[dict], words: list[dict] | None, config: dict,
         override: dict | None, available: set[str]) -> list[dict]:
    manual_cues = []
    # Channel-wide disables (channel_state.json ambience.disable) plus this
    # episode's own 02_script/ambience_plan.json "disable".
    disabled = set(config.get("disable", [])) | set((override or {}).get("disable", []))
    if override and override.get("mode") == "replace":
        for c in override.get("cues", []):
            t = _resolve_manual(c, beats, words)
            manual_cues.append({"sfx": c["sfx"], "t": t, "reason": "manual", "manual": True})
        auto = []
    else:
        for c in (override or {}).get("cues", []):
            t = _resolve_manual(c, beats, words)
            manual_cues.append({"sfx": c["sfx"], "t": t, "reason": "manual", "manual": True})
        auto = [c for c in auto_cues(beats, words, config)
                if c["sfx"] not in disabled and not (c.get("transition") and "transition" in disabled)]

    all_cues = manual_cues + auto
    all_cues.sort(key=lambda c: c["t"])

    # Validate all cues (manual and auto) are available in the manifest.
    # This catches any typos or renamed effects early, not just manual overrides.
    for cue in all_cues:
        if cue["sfx"] not in available:
            raise ValueError(f"Unknown ambience effect {cue['sfx']!r} -- available: {sorted(available)}")

    min_gap = config.get("min_gap_seconds", 25.0)
    max_keyword = config.get("max_keyword_cues", 10)
    result: list[dict] = []
    keyword_count = 0
    for cue in all_cues:
        # Manual cues and scene-cut whooshes are never deduped -- a whoosh
        # belongs to every cut, however close together the cuts are.
        if cue.get("manual") or cue.get("transition"):
            result.append(cue)
            continue
        if cue.get("keyword"):
            if keyword_count >= max_keyword:
                continue
            # Only enforce min_gap between keyword cues, not between keyword and fixed atmosphere cues
            # (wind, reveal_sting, heartbeat). This allows multiple events (e.g., "door" + "storm")
            # within a beat, while still preventing rapid duplicates of the same keyword (e.g., three
            # "door" instances at t=0, t=1, t=2 dedupe to the first, not all three).
            if any(cue["t"] - r["t"] < min_gap and cue["t"] >= r["t"] and r.get("keyword") for r in result):
                continue
            keyword_count += 1
            result.append(cue)
            continue
        # Fixed atmosphere cues (wind, heartbeat, reveal_sting) dedup only
        # against each other -- a keyword cue must never cost the climax its sting.
        if any(abs(cue["t"] - r["t"]) < min_gap for r in result
               if not r.get("transition") and not r.get("keyword")):
            continue
        result.append(cue)

    result.sort(key=lambda c: c["t"])
    return result
