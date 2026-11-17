"""Suggest turn times for each clip with a simple loudness rule.

These are only suggestions. Check them by ear (for example in Audacity) before you
type them into the manifest, because the manifest is the truth we later judge the
VAD against. Accepting the suggestions blindly would make that test meaningless.
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

AUDIO_DIR = Path("data/own50/audio")
FRAME_SECONDS = 0.02
MIN_PAUSE = 0.6  # silence shorter than this stays inside one turn
MIN_SPEECH = 0.15  # sounds shorter than this are ignored
THRESHOLD_RATIO = 0.1  # a frame counts as speech if it is at least this loud
# compared with the loud parts of the clip


def read_wav(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        data = handle.readframes(handle.getnframes())
    if width != 2 or channels != 1:
        raise ValueError(f"{path}: expected 16-bit mono WAV, run prepare_audio.sh first")
    return rate, np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0


def suggest_turns(samples: np.ndarray, rate: int) -> list[tuple[float, float]]:
    frame = int(rate * FRAME_SECONDS)
    count = len(samples) // frame
    if count == 0:
        return []
    frames = samples[: count * frame].reshape(count, frame)
    rms = np.sqrt((frames**2).mean(axis=1))
    loud = float(np.percentile(rms, 95))
    if loud < 1e-4:
        return []
    active = rms > loud * THRESHOLD_RATIO

    segments: list[list[int]] = []
    start = None
    for i, is_active in enumerate(active):
        if is_active and start is None:
            start = i
        elif not is_active and start is not None:
            segments.append([start, i])
            start = None
    if start is not None:
        segments.append([start, count])

    merged: list[list[int]] = []
    for s, e in segments:
        if merged and (s - merged[-1][1]) * FRAME_SECONDS < MIN_PAUSE:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [
        (s * FRAME_SECONDS, e * FRAME_SECONDS)
        for s, e in merged
        if (e - s) * FRAME_SECONDS >= MIN_SPEECH
    ]


def main() -> None:
    paths = [Path(p) for p in sys.argv[1:]] or sorted(AUDIO_DIR.glob("clip_*.wav"))
    if not paths:
        print("No clips found. Run scripts/prepare_audio.sh first.")
        return
    for path in paths:
        rate, samples = read_wav(path)
        turns = suggest_turns(samples, rate)
        text = ",".join(f"{s:.2f}-{e:.2f}" for s, e in turns) or "(nothing found)"
        print(f"{path.name}  length {len(samples) / rate:.1f}s  suggested turns: {text}")


if __name__ == "__main__":
    main()
