from pathlib import Path

import generate_narration_chunks as gnc


def test_normalize_section():
    assert gnc.normalize_section("[COLD_OPEN]") == "cold_open"
    assert gnc.normalize_section("RISING_MYSTERY") == "rising_mystery"


def test_beat_to_section_map(tmp_path):
    script = tmp_path / "script.md"
    script.write_text(
        "[COLD_OPEN]\n1. The keeper vanished mid-shift.\n\n"
        "[SETUP]\n2. It was 1920 on the Maine coast.\n3. He'd worked the light for nine years.\n\n"
        "[RISING_MYSTERY]\n4. The log stopped mid-sentence.\n"
    )
    mapping = gnc.beat_to_section_map(script)
    assert mapping == {1: "cold_open", 2: "setup", 3: "setup", 4: "rising_mystery"}


def test_voice_id_matches_channel_state():
    assert gnc.VOICE == gnc.STATE["voice"]["voice_id"] == "hi-IN-MadhurNeural"


def test_hindi_sections_map_and_default_comes_from_config(tmp_path):
    script = tmp_path / "script.md"
    script.write_text("1. बिना सेक्शन वाली लाइन।\n[HOOK]\n2. एक कप चाय।\n[RAAZ]\n3. असली खेल।\n")
    mapping = gnc.beat_to_section_map(script)
    assert mapping == {1: "khel", 2: "hook", 3: "raaz"}
    assert gnc.DEFAULT_SECTION == "khel"
    assert set(gnc.SECTION_PRESETS) == {"hook", "duniya", "khel", "raaz", "sabak"}
