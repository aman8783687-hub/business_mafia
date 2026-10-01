"""Pure-stdlib ambience mixer -- no numpy at runtime (the GitHub Actions
runner has none; ambience clips are pre-synthesized, see synth_library.py).
Ported from Dmoo Way's sfx/mixer.py; identical gain-staging math."""
from __future__ import annotations

import array
import wave
from pathlib import Path


def _read_wav_samples(path: Path) -> tuple[array.array, int]:
    with wave.open(str(path), "rb") as f:
        sample_rate = f.getframerate()
        raw = f.readframes(f.getnframes())
    return array.array("h", raw), sample_rate


def render_bed(cues: list[dict], manifest: dict, ambience_dir: Path, bed_db: float,
                total_seconds: float, out_path: Path) -> None:
    sample_rate = manifest["sample_rate"]
    total_samples = int(total_seconds * sample_rate)
    buffer = [0.0] * total_samples

    for cue in cues:
        effect = manifest["effects"][cue["sfx"]]
        samples, clip_rate = _read_wav_samples(ambience_dir / effect["file"])
        assert clip_rate == sample_rate, f"{effect['file']} sample rate mismatch"
        gain = 10 ** ((bed_db + effect["gain_db"] + cue.get("gain_db", 0.0)) / 20) / 32768
        hit_offset_samples = int(effect["hit_offset"] * sample_rate)
        start_sample = int(cue["t"] * sample_rate) - hit_offset_samples
        for i, s in enumerate(samples):
            idx = start_sample + i
            if 0 <= idx < total_samples:
                buffer[idx] += s * gain

    clipped = [max(-32767, min(32767, int(round(v * 32768)))) for v in buffer]
    with wave.open(str(out_path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(array.array("h", clipped).tobytes())
