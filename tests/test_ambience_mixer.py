import json
import wave

from ambience import mixer


def test_render_bed_places_cue_at_correct_time(tmp_path):
    manifest = {"sample_rate": 48000, "effects": {
        "wind": {"file": "wind.wav", "hit_offset": 0.0, "duration": 1.0, "gain_db": 0.0},
    }}
    ambience_dir = tmp_path / "ambience"
    ambience_dir.mkdir()
    with wave.open(str(ambience_dir / "wind.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(48000)
        f.writeframes((b"\xff\x7f" * 48000))  # 1s of max-amplitude int16 samples

    out_path = tmp_path / "bed.wav"
    mixer.render_bed(
        cues=[{"sfx": "wind", "t": 2.0}],
        manifest=manifest, ambience_dir=ambience_dir, bed_db=-18, total_seconds=5.0, out_path=out_path,
    )
    with wave.open(str(out_path), "rb") as f:
        assert f.getframerate() == 48000
        assert f.getnframes() == 5 * 48000
        frames = f.readframes(f.getnframes())
    import array
    samples = array.array("h", frames)
    # Silence before t=2.0s, non-silence at and after.
    assert max(abs(s) for s in samples[:int(48000 * 1.5)]) == 0
    assert max(abs(s) for s in samples[int(48000 * 2.1):int(48000 * 2.5)]) > 0
