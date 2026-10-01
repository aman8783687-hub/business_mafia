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


def test_every_configured_ambience_effect_exists_in_the_manifest():
    import json
    from pathlib import Path
    amb = Path(__file__).resolve().parent.parent / "MafiaOfBusiness" / "brand" / "ambience"
    manifest = json.loads((amb / "manifest.json").read_text())["effects"]
    wanted = set(S["ambience"]["keywords"]) | set(S["ambience"]["transitions"]["variants"]) | {"reveal_sting"}
    assert wanted <= set(manifest), sorted(wanted - set(manifest))
    for name in wanted:
        assert (amb / manifest[name]["file"]).stat().st_size > 1000, name
