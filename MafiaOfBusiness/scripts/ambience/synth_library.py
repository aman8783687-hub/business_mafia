#!/usr/bin/env python3
"""One-time local generation of the channel's ambience sound library --
run this script by hand, commit its output (brand/ambience/*.wav +
manifest.json), and never run it in CI (the GitHub Actions runner has no
numpy, matching Dmoo Way's own sfx/synth_library.py precedent). All
effects are synthesized (sines/filtered noise), so there is no licensing
concern -- see channel_state.json's ambience.note.

Usage (from MafiaOfBusiness/, with numpy installed locally):
    python3 scripts/ambience/synth_library.py
"""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "brand" / "ambience"
SR = 48000
RNG = np.random.default_rng(20260927)


def _write_wav(path: Path, samples: np.ndarray) -> None:
    samples = np.clip(samples, -1.0, 1.0)
    int16 = (samples * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(int16.tobytes())


def _envelope(n: int, attack: int, release: int) -> np.ndarray:
    env = np.ones(n)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release)
    return env


def _wind(duration=6.0) -> np.ndarray:
    n = int(SR * duration)
    noise = RNG.standard_normal(n)
    # Low-pass via a simple moving average to turn white noise into a windy rumble.
    kernel = np.ones(400) / 400
    filtered = np.convolve(noise, kernel, mode="same")
    return filtered * 0.6 * _envelope(n, int(SR * 1.0), int(SR * 1.5))


def _creak(duration=1.2) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    freq = 180 + 60 * np.sin(2 * np.pi * 0.8 * t)
    tone = np.sin(2 * np.pi * np.cumsum(freq) / SR)
    noise = RNG.standard_normal(n) * 0.15
    return (tone * 0.5 + noise) * _envelope(n, int(SR * 0.05), int(SR * 0.3))


def _distant_thunder(duration=3.0) -> np.ndarray:
    n = int(SR * duration)
    noise = RNG.standard_normal(n)
    kernel = np.ones(800) / 800
    rumble = np.convolve(noise, kernel, mode="same")
    return rumble * 0.8 * _envelope(n, int(SR * 0.3), int(SR * 2.0))


def _heartbeat(duration=2.0) -> np.ndarray:
    n = int(SR * duration)
    out = np.zeros(n)
    for start in (0.0, 0.35):
        i0 = int(SR * start)
        thump_n = int(SR * 0.15)
        t = np.linspace(0, 0.15, thump_n)
        thump = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 20)
        out[i0:i0 + thump_n] += thump
    return out * 0.7


def _footsteps(duration=1.6) -> np.ndarray:
    n = int(SR * duration)
    out = np.zeros(n)
    for start in (0.0, 0.8):
        i0 = int(SR * start)
        step_n = int(SR * 0.08)
        noise = RNG.standard_normal(step_n) * np.exp(-np.linspace(0, 8, step_n))
        out[i0:i0 + step_n] += noise
    return out * 0.5


def _silence_sting(duration=1.0) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    tone = np.sin(2 * np.pi * 55 * t)
    return tone * 0.25 * _envelope(n, int(SR * 0.1), int(SR * 0.7))


def _whisper(duration=1.5) -> np.ndarray:
    n = int(SR * duration)
    noise = RNG.standard_normal(n)
    kernel = np.ones(60) / 60
    hiss = np.convolve(noise, kernel, mode="same")
    return hiss * 0.3 * _envelope(n, int(SR * 0.1), int(SR * 0.5))


def _reveal_sting(duration=2.5) -> np.ndarray:
    n = int(SR * duration)
    t = np.linspace(0, duration, n)
    tone = np.sin(2 * np.pi * 110 * t) + 0.5 * np.sin(2 * np.pi * 220 * t)
    return tone * 0.5 * _envelope(n, int(SR * 0.05), int(SR * 2.0))


# --- Scene-transition whooshes and common story effects (2026-09-29). ---
# Appended after the originals so the shared RNG stream -- and therefore the
# original eight WAVs -- come out byte-identical on a full regeneration.
# Unlike the originals, these are peak-normalized so their manifest gain_db
# is the only loudness knob. Gains were set against a real edge-tts
# narration sample (~-19 dBFS RMS) to sit ~18-23 dB under the voice.

def _peak_normalize(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    return x * (peak / max(np.max(np.abs(x)), 1e-9))


def _swept_bandpass(noise: np.ndarray, freqs: np.ndarray, q: float) -> np.ndarray:
    """Chamberlin state-variable band-pass with a per-sample cutoff."""
    out = np.empty_like(noise)
    low = band = 0.0
    damp = 1.0 / q
    for i, x in enumerate(noise):
        f = 2 * np.sin(np.pi * freqs[i] / SR)
        high = x - low - damp * band
        band += f * high
        low += f * band
        out[i] = band
    return out


def _whoosh(duration: float, peak_at: float, f_start: float, f_peak: float, f_end: float) -> np.ndarray:
    """Band-passed noise whose center frequency and level rise to a peak at
    `peak_at` seconds (the manifest's hit_offset, landed on the cut) then fall."""
    n = int(SR * duration)
    k = int(SR * peak_at)
    freqs = np.concatenate([np.geomspace(f_start, f_peak, k), np.geomspace(f_peak, f_end, n - k)])
    env = np.concatenate([np.linspace(0, 1, k) ** 2.2, np.linspace(1, 0, n - k) ** 1.6])
    return _peak_normalize(_swept_bandpass(RNG.standard_normal(n), freqs, q=1.4) * env)


def _whoosh_soft_1() -> np.ndarray:
    return _whoosh(1.0, 0.55, 250, 1400, 400)


def _whoosh_soft_2() -> np.ndarray:
    return _whoosh(1.2, 0.65, 180, 1000, 300)


def _whoosh_soft_3() -> np.ndarray:
    return _whoosh(0.9, 0.5, 320, 1800, 500)


def _temple_bell(duration=3.5) -> np.ndarray:
    n = int(SR * duration)
    t = np.arange(n) / SR
    f0 = 520.0
    # Inharmonic partials of a cast bell, higher ones decaying faster.
    partials = [(0.5, 0.6, 1.2), (1.0, 1.0, 1.6), (1.19, 0.45, 2.2), (1.56, 0.35, 2.8),
                (2.0, 0.3, 3.4), (2.74, 0.18, 4.5), (3.0, 0.12, 5.5)]
    tone = sum(a * np.sin(2 * np.pi * f0 * r * t + RNG.uniform(0, 2 * np.pi)) * np.exp(-t * d)
               for r, a, d in partials)
    strike = RNG.standard_normal(n) * np.exp(-t * 90) * 0.3
    return _peak_normalize((tone + strike) * _envelope(n, int(SR * 0.003), int(SR * 0.4)))


def _fire_crackle(duration=3.0) -> np.ndarray:
    n = int(SR * duration)
    bed = np.convolve(RNG.standard_normal(n), np.ones(120) / 120, mode="same") * 4.0
    pops = np.zeros(n)
    for _ in range(38):
        i0 = int(RNG.uniform(0, n - 600))
        length = int(RNG.uniform(60, 500))
        pops[i0:i0 + length] += RNG.standard_normal(length) * np.exp(-np.linspace(0, 9, length)) * RNG.uniform(0.3, 1.0)
    return _peak_normalize((bed + pops) * _envelope(n, int(SR * 0.4), int(SR * 0.8)))


def _water(duration=3.5) -> np.ndarray:
    n = int(SR * duration)
    t = np.arange(n) / SR
    flow = np.convolve(RNG.standard_normal(n), np.ones(40) / 40, mode="same")
    flow *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.9 * t) * np.sin(2 * np.pi * 0.37 * t + 1.0)
    bubbles = np.zeros(n)
    for _ in range(22):
        i0 = int(RNG.uniform(0, n - 3000))
        length = int(SR * RNG.uniform(0.02, 0.05))
        bt = np.arange(length) / SR
        f = RNG.uniform(300, 900) * (1 + 3 * bt / bt[-1])  # rising chirp, like a small bubble
        bubbles[i0:i0 + length] += np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-bt * 60) * 0.15
    return _peak_normalize((flow + bubbles) * _envelope(n, int(SR * 0.6), int(SR * 1.0)))


def _drum(duration=2.4) -> np.ndarray:
    n = int(SR * duration)
    out = np.zeros(n)
    for start, amp in ((0.0, 1.0), (0.42, 0.7), (0.84, 0.9)):
        i0 = int(SR * start)
        hit_n = int(SR * 0.6)
        ht = np.arange(hit_n) / SR
        f = 58 + 60 * np.exp(-ht * 25)  # pitch drops on impact, like a skin drum
        body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-ht * 7)
        slap = RNG.standard_normal(hit_n) * np.exp(-ht * 120) * 0.25
        out[i0:i0 + hit_n] += (body + slap) * amp
    return _peak_normalize(out)


def _metal_clang(duration=1.8) -> np.ndarray:
    n = int(SR * duration)
    t = np.arange(n) / SR
    partials = [(1180, 1.0, 5), (1870, 0.7, 7), (2650, 0.5, 9), (3410, 0.35, 12), (4730, 0.2, 16)]
    ring = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in partials)
    impact = RNG.standard_normal(n) * np.exp(-t * 150) * 0.8
    return _peak_normalize(ring + impact)


def _paper_rustle(duration=1.2) -> np.ndarray:
    n = int(SR * duration)
    noise = RNG.standard_normal(n)
    hiss = noise - np.convolve(noise, np.ones(8) / 8, mode="same")  # crude high-pass
    bursts = np.zeros(n)
    for _ in range(9):
        i0 = int(RNG.uniform(0, n - 4000))
        length = int(SR * RNG.uniform(0.03, 0.12))
        bursts[i0:i0 + length] += np.hanning(length) * RNG.uniform(0.4, 1.0)
    return _peak_normalize(hiss * (bursts + 0.05) * _envelope(n, int(SR * 0.02), int(SR * 0.2)))


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


EFFECTS = {
    "wind": (_wind, -4.0, "a low, filtered windy rumble, loops well as a bed"),
    "creak": (_creak, -6.0, "a single wooden door/floorboard creak"),
    "distant_thunder": (_distant_thunder, -3.0, "a distant, low thunder rumble"),
    "heartbeat": (_heartbeat, -8.0, "two low heartbeat thumps"),
    "footsteps": (_footsteps, -10.0, "two soft footstep taps"),
    "silence_sting": (_silence_sting, -12.0, "a very quiet sustained low tone for an eerie pause"),
    "whisper": (_whisper, -10.0, "a soft breathy hiss"),
    "reveal_sting": (_reveal_sting, -5.0, "a low two-tone sting for the climax/reveal beat"),
    "whoosh_soft_1": (_whoosh_soft_1, -5.0, "a soft rising whoosh for a scene cut", 0.55),
    "whoosh_soft_2": (_whoosh_soft_2, -5.0, "a slower, darker whoosh for a scene cut", 0.65),
    "whoosh_soft_3": (_whoosh_soft_3, -5.0, "a short, brighter whoosh for a scene cut", 0.5),
    "temple_bell": (_temple_bell, -3.0, "a single distant temple bell strike"),
    "fire_crackle": (_fire_crackle, -3.0, "a low fire bed with sparse crackles"),
    "water": (_water, -5.0, "flowing water with a few small bubbles"),
    "drum": (_drum, -2.0, "three low skin-drum hits"),
    "metal_clang": (_metal_clang, -6.0, "a single ringing metal strike"),
    "paper_rustle": (_paper_rustle, -4.0, "a brief rustle of old paper"),
    "coin_clink": (_coin_clink, -8.0, "two or three small coins clinking"),
    "cash_register": (_cash_register, -9.0, "a drawer click and a small register bell"),
    "sizzle": (_sizzle, -10.0, "a short hot-oil sizzle with a few crackles"),
    "crowd_murmur": (_crowd_murmur, -12.0, "a low market crowd murmur"),
}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {"note": "All effects synthesized locally, no licensing concern.", "sample_rate": SR, "effects": {}}
    for name, (fn, gain_db, description, *rest) in EFFECTS.items():
        hit_offset = rest[0] if rest else 0.0
        samples = fn()
        file_name = f"{name}.wav"
        _write_wav(OUT_DIR / file_name, samples)
        manifest["effects"][name] = {
            "file": file_name, "hit_offset": hit_offset, "duration": len(samples) / SR,
            "gain_db": gain_db, "description": description,
        }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {len(EFFECTS)} effects + manifest.json to {OUT_DIR}")


if __name__ == "__main__":
    main()
