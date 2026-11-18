"""Turn text into WAV files with Kokoro's Hindi voices.

Example:
    uv run python scripts/say.py "आपका ऑर्डर कल शाम तक पहुँच जाएगा"
    uv run python scripts/say.py "नमस्ते" --voice hf_beta
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

SAMPLE_RATE = 24_000
HINDI_VOICES = "hf_alpha,hf_beta,hm_omega,hm_psi"


def to_numpy(audio) -> np.ndarray:
    """Kokoro returns a torch tensor. Turn it into a plain NumPy array."""
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    return np.asarray(audio, dtype=np.float32)


def audio_of(item):
    """Newer Kokoro gives an object with .audio, older gives (text, phonemes, audio)."""
    audio = getattr(item, "audio", None)
    return audio if audio is not None else item[2]


def speak(pipeline, text: str, voice: str, speed: float) -> np.ndarray:
    pieces = [to_numpy(audio_of(item)) for item in pipeline(text, voice=voice, speed=speed)]
    if not pieces:
        raise SystemExit("Kokoro returned no audio for this text.")
    return np.concatenate(pieces)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Hindi text, best written in Devanagari")
    parser.add_argument("--voice", default=HINDI_VOICES, help="one voice or a comma list")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--out-dir", default="data/tts_samples")
    args = parser.parse_args()

    from kokoro import KPipeline  # imported late, it is a heavy library

    try:
        pipeline = KPipeline(lang_code="h", device=args.device)
    except TypeError:  # an older Kokoro without the device option
        pipeline = KPipeline(lang_code="h")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for voice in args.voice.split(","):
        audio = speak(pipeline, args.text, voice.strip(), args.speed)
        path = out_dir / f"{voice.strip()}.wav"
        sf.write(path, audio, SAMPLE_RATE)
        print(f"Saved {path} ({len(audio) / SAMPLE_RATE:.1f} seconds)")


if __name__ == "__main__":
    main()
