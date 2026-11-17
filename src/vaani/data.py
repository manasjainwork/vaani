"""Loading evaluation clips from a manifest file.

A manifest is a text file with one JSON object per line, one line per audio clip.
The audio itself never goes into git. Only the manifest format is public.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REQUIRED_FIELDS = ("id", "audio", "text", "turns", "speaker", "consent")


@dataclass(frozen=True)
class Turn:
    """One stretch of speech inside a clip, in seconds."""

    start: float
    end: float


@dataclass(frozen=True)
class Clip:
    """One recorded clip with its correct text and turn times."""

    id: str
    audio_path: Path
    text: str
    turns: tuple[Turn, ...]
    speaker: str
    consent: bool
    notes: str = ""


# --8<-- [start:parse]
def _parse_row(row: dict, base: Path) -> Clip:
    missing = [name for name in REQUIRED_FIELDS if name not in row]
    if missing:
        raise ValueError(f"missing fields: {missing}")
    if row["consent"] is not True:
        raise ValueError(f"clip {row['id']!r} has no consent, it must not be used")
    if not str(row["text"]).strip():
        raise ValueError(f"clip {row['id']!r} has an empty transcript")

    turns = tuple(Turn(float(t["start"]), float(t["end"])) for t in row["turns"])
    if not turns:
        raise ValueError(f"clip {row['id']!r} has no turns")
    previous_end = 0.0
    for turn in turns:
        if turn.start < previous_end or turn.end <= turn.start:
            raise ValueError(f"clip {row['id']!r} has bad turn times: {turn}")
        previous_end = turn.end

    return Clip(
        id=str(row["id"]),
        audio_path=base / row["audio"],
        text=str(row["text"]),
        turns=turns,
        speaker=str(row["speaker"]),
        consent=True,
        notes=str(row.get("notes", "")),
    )
# --8<-- [end:parse]


def load_manifest(path: str | Path, check_audio: bool = True) -> list[Clip]:
    """Read every clip in a manifest. Stops with a clear message on the first problem."""
    path = Path(path)
    clips: list[Clip] = []
    seen: set[str] = set()
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            clip = _parse_row(json.loads(line), path.parent)
        except (json.JSONDecodeError, ValueError, TypeError) as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
        if clip.id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate clip id {clip.id!r}")
        seen.add(clip.id)
        if check_audio and not clip.audio_path.exists():
            raise FileNotFoundError(f"{path}:{line_number}: audio file not found: {clip.audio_path}")
        clips.append(clip)
    return clips
