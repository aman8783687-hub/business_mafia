import env_loader
import state


def test_env_secret_with_trailing_newline_is_stripped(monkeypatch):
    monkeypatch.setenv("CONTENT_LAB_URL", "https://example.com\n")
    assert env_loader.get("CONTENT_LAB_URL") == "https://example.com"


def test_missing_required_env_raises(monkeypatch):
    monkeypatch.delenv("SOME_UNSET_VAR", raising=False)
    monkeypatch.setattr(env_loader, "load_env", lambda: {})
    import pytest
    with pytest.raises(RuntimeError):
        env_loader.get("SOME_UNSET_VAR")


def test_parse_resolution():
    assert state.parse_resolution("1920x1080") == (1920, 1080)


def test_channel_state_has_no_music_config():
    s = state.load_state()
    assert "music_bed_db_under_voice" not in s["audio"]
    assert s["ambience"]["enabled"] is True
    assert s["format"]["target_runtime_seconds"] == 360
    assert s["style_lock"]["aspect"] == "16:9"
    assert s["style_lock"]["character_name"] == "RedHat Engineer"


from scenes import prompt_builder


def test_build_prompt_includes_style_suffix():
    p = prompt_builder.build_prompt("the host holds a glowing transistor")
    assert p.endswith("the host holds a glowing transistor")
    assert p.startswith("hand-drawn black marker stickman")
    assert "photorealistic" not in p  # negative prompt is separate, not concatenated here


def test_derive_seed_is_stable_and_distinct():
    a = prompt_builder.derive_seed("ep-1", 1)
    b = prompt_builder.derive_seed("ep-1", 1)
    c = prompt_builder.derive_seed("ep-1", 2)
    assert a == b
    assert a != c


def test_build_prompt_plan_skips_real_photo_beats():
    beats = [{"beat": 1, "text": "..."}, {"beat": 2, "text": "..."}]
    shot_index = {1: {"description": "a foggy dock"}, 2: {"description": "n/a", "type": "real_photo"}}
    plan = prompt_builder.build_prompt_plan("ep-1", beats, shot_index)
    assert [e["beat"] for e in plan] == [1]
    assert plan[0]["width"] == 1024 and plan[0]["height"] == 576


def test_build_prompt_plan_includes_cfg_scale_and_steps():
    beats = [{"beat": 1, "text": "a scene"}]
    shot_index = {1: {"description": "a foggy dock"}}
    plan = prompt_builder.build_prompt_plan("ep-1", beats, shot_index)
    assert len(plan) == 1
    assert plan[0]["guidance_scale"] == 7.5
    assert plan[0]["num_inference_steps"] == 20


def test_derive_seed_is_distinct_across_attempts():
    seed_attempt_0 = prompt_builder.derive_seed("ep-1", 1, attempt=0)
    seed_attempt_1 = prompt_builder.derive_seed("ep-1", 1, attempt=1)
    assert seed_attempt_0 != seed_attempt_1
