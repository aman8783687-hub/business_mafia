from ambience import planner

CONFIG = {
    "min_gap_seconds": 25.0,
    "max_keyword_cues": 10,
    "keywords": {
        "wind": ["wind*", "storm*"],
        "creak": ["creak*", "door*"],
        "heartbeat": ["heart*", "dread"],
    },
}


def test_beat_with_no_keyword_match_gets_no_cue():
    beats = [
        {"beat": 1, "text": "The keeper vanished mid-shift.", "section": "cold_open", "start": 0.0, "end": 10.0},
        {"beat": 2, "text": "It was quiet on the coast.", "section": "setup", "start": 10.0, "end": 20.0},
    ]
    cues = planner.auto_cues(beats, None, CONFIG)
    keyword_cues = [c for c in cues if c.get("keyword")]
    beat_2_start, beat_2_end = 10.0, 20.0
    assert not any(beat_2_start <= c["t"] < beat_2_end for c in keyword_cues)


def test_cold_open_always_gets_wind():
    beats = [{"beat": 1, "text": "no keyword here", "section": "cold_open", "start": 0.0, "end": 10.0}]
    cues = planner.auto_cues(beats, None, CONFIG)
    assert any(c["sfx"] == "wind" and c["reason"] == "cold_open_atmosphere" for c in cues)


def test_keyword_cue_placed_on_matching_word():
    beats = [{"beat": 1, "text": "The door creaked open in the storm.", "section": "rising_mystery", "start": 0.0, "end": 12.0}]
    words = [
        {"text": "The", "start": 0.0, "end": 0.3}, {"text": "door", "start": 0.3, "end": 0.8},
        {"text": "creaked", "start": 0.8, "end": 1.4}, {"text": "open", "start": 1.4, "end": 1.8},
        {"text": "in", "start": 1.8, "end": 2.0}, {"text": "the", "start": 2.0, "end": 2.2},
        {"text": "storm", "start": 2.2, "end": 2.8},
    ]
    cues = planner.plan(beats, words, CONFIG, override=None, available={"wind", "creak", "heartbeat"})
    reasons = [c["reason"] for c in cues if c.get("keyword")]
    assert any("door" in r or "creaked" in r or "storm" in r for r in reasons)


def test_dedup_drops_cue_within_min_gap():
    beats = [
        {"beat": 1, "text": "door door door", "section": "rising_mystery", "start": 0.0, "end": 5.0},
    ]
    words = [{"text": "door", "start": t, "end": t + 0.3} for t in (0.0, 1.0, 2.0)]
    cues = planner.plan(beats, words, CONFIG, override=None, available={"creak", "wind"})
    keyword_times = sorted(c["t"] for c in cues if c.get("keyword"))
    assert len(keyword_times) <= 1


def test_keyword_cue_appears_shortly_after_atmosphere_cue():
    # Verify that keyword cues are NOT dropped just because they're within min_gap
    # of a non-keyword atmosphere cue (like wind at t=0). This proves the
    # keyword-only dedup logic is working: we allow "door" at t=0.3 even though
    # it's only 0.3s after wind at t=0.0, far less than the 25s min_gap.
    beats = [{"beat": 1, "text": "door opens", "section": "rising_mystery", "start": 0.0, "end": 10.0}]
    words = [
        {"text": "door", "start": 0.3, "end": 0.8},
        {"text": "opens", "start": 0.8, "end": 1.2},
    ]
    cues = planner.plan(beats, words, CONFIG, override=None, available={"wind", "creak"})
    keyword_cues = [c for c in cues if c.get("keyword")]
    # Should have a keyword cue for "door" at t=0.3, not dropped by wind at t=0.0
    assert any(c["t"] == 0.3 for c in keyword_cues), f"Expected keyword cue at t=0.3, got {keyword_cues}"


def test_auto_cue_unavailable_raises_error():
    # If auto_cues() produces an effect not in available, plan() must raise.
    # Wind is always generated at beat[0]["start"], so excluding it from available
    # should cause a ValueError.
    import pytest
    beats = [{"beat": 1, "text": "x", "section": "setup", "start": 0.0, "end": 5.0}]
    with pytest.raises(ValueError, match="Unknown ambience effect 'wind'"):
        planner.plan(beats, None, CONFIG, override=None, available={"creak"})


def test_unknown_sfx_in_override_raises():
    import pytest
    beats = [{"beat": 1, "text": "x", "section": "setup", "start": 0.0, "end": 5.0}]
    override = {"mode": "add", "cues": [{"sfx": "nonexistent", "beat": 1}]}
    with pytest.raises(ValueError):
        planner.plan(beats, None, CONFIG, override, available={"wind"})


TRANSITION_CONFIG = {
    **CONFIG,
    "transitions": {
        "enabled": True,
        "variants": ["whoosh_soft_1", "whoosh_soft_2", "whoosh_soft_3"],
        "gain_jitter_db": 2.0,
        "skip_sections": ["climax_reveal"],
    },
}
WHOOSHES = {"whoosh_soft_1", "whoosh_soft_2", "whoosh_soft_3"}


def _beats(sections):
    return [
        {"beat": i + 1, "text": "x", "section": s, "start": i * 10.0, "end": i * 10.0 + 9.0}
        for i, s in enumerate(sections)
    ]


def test_transition_whoosh_on_every_cut_except_first_and_skipped_sections():
    beats = _beats(["cold_open", "setup", "setup", "investigation", "climax_reveal", "aftermath"])
    cues = planner.plan(beats, None, TRANSITION_CONFIG, override=None,
                        available={"wind", "heartbeat", "reveal_sting"} | WHOOSHES)
    whoosh_times = sorted(c["t"] for c in cues if c.get("transition"))
    # Cuts at 10, 20, 30, 40(reveal -> skipped), 50. None at t=0.
    assert whoosh_times == [10.0, 20.0, 30.0, 50.0]
    assert all(c["sfx"] in WHOOSHES for c in cues if c.get("transition"))


def test_transitions_survive_min_gap_dedup():
    # Cuts only 3s apart, far below the 25s min_gap -- none may be dropped.
    beats = [{"beat": i + 1, "text": "x", "section": "setup", "start": i * 3.0, "end": i * 3.0 + 2.5}
             for i in range(5)]
    cues = planner.plan(beats, None, TRANSITION_CONFIG, override=None, available={"wind"} | WHOOSHES)
    assert len([c for c in cues if c.get("transition")]) == 4


def test_transition_variant_and_gain_are_deterministic_and_vary():
    beats = _beats(["setup"] * 10)
    a = [c for c in planner.auto_cues(beats, None, TRANSITION_CONFIG) if c.get("transition")]
    b = [c for c in planner.auto_cues(beats, None, TRANSITION_CONFIG) if c.get("transition")]
    assert a == b
    assert len({c["sfx"] for c in a}) > 1
    assert all(abs(c["gain_db"]) <= 2.0 for c in a)
    assert len({c["gain_db"] for c in a}) > 1


def test_transitions_off_when_config_absent_or_disabled_by_override():
    beats = _beats(["setup"] * 4)
    assert not any(c.get("transition") for c in planner.auto_cues(beats, None, CONFIG))
    cues = planner.plan(beats, None, TRANSITION_CONFIG, override={"disable": ["transition"]},
                        available={"wind"} | WHOOSHES)
    assert not any(c.get("transition") for c in cues)


def test_new_common_keywords_trigger_cues():
    config = {**CONFIG, "keywords": {"temple_bell": ["bell*", "temple*"], "fire_crackle": ["fire", "flame*"]}}
    beats = [{"beat": 1, "text": "x", "section": "setup", "start": 0.0, "end": 60.0}]
    words = [{"text": "temple", "start": 1.0, "end": 1.4}, {"text": "flames,", "start": 30.0, "end": 30.5}]
    cues = planner.plan(beats, words, config, override=None, available={"wind", "temple_bell", "fire_crackle"})
    assert {(c["sfx"], c["t"]) for c in cues if c.get("keyword")} == {("temple_bell", 1.0), ("fire_crackle", 30.0)}


def test_keyword_cue_never_suppresses_reveal_sting():
    beats = _beats(["cold_open", "setup", "investigation", "climax_reveal"])
    words = [{"text": "door", "start": 22.0, "end": 22.4}]  # 8s before the reveal at t=30
    cues = planner.plan(beats, words, TRANSITION_CONFIG, override=None,
                        available={"wind", "creak", "heartbeat", "reveal_sting"} | WHOOSHES)
    assert any(c["sfx"] == "reveal_sting" and c["t"] == 30.0 for c in cues)


def test_channel_level_disable_suppresses_fixed_cues():
    beats = [
        {"beat": i, "start": float(i * 10), "section": sec, "text": "x"}
        for i, sec in enumerate(["cold_open", "setup", "rising_mystery", "climax_reveal"], start=1)
    ]
    config = {"keywords": {}, "disable": ["wind", "heartbeat"]}
    cues = planner.plan(beats, None, config, None, available={"wind", "heartbeat", "reveal_sting"})
    assert {c["sfx"] for c in cues} == {"reveal_sting"}


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
