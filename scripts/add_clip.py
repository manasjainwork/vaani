"""Add one clip to data/own50/manifest.jsonl by answering a few questions.

Run it again for the next clip. It picks the first audio file that has no line yet.
"""

from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path("data/own50/manifest.jsonl")
AUDIO_DIR = Path("data/own50/audio")


def ask(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{question}{suffix}: ").strip() or default


def ask_turns() -> list[dict]:
    while True:
        raw = ask("Turn times in seconds, like 0.4-4.1 or 0.5-1.8,3.1-4.6")
        try:
            turns = []
            for part in raw.split(","):
                start, end = part.split("-")
                turns.append({"start": float(start), "end": float(end)})
            return turns
        except ValueError:
            print("Could not read that. Use start-end pairs in seconds, like 0.4-4.1")


def next_unlabelled() -> str | None:
    done: set[str] = set()
    if MANIFEST.exists():
        for line in MANIFEST.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])
    for wav in sorted(AUDIO_DIR.glob("clip_*.wav")):
        if wav.stem not in done:
            return wav.stem
    return None


def main() -> None:
    clip_id = next_unlabelled()
    if clip_id is None:
        print("Every clip in data/own50/audio already has a line in the manifest.")
        return
    print(f"Labelling {clip_id}.wav")
    text = ask("What was said (lowercase Roman Hinglish)")
    turns = ask_turns()
    speaker = ask("Speaker id (s1, s2, ...)", "s1")
    notes = ask("Notes (noise, fast speech, long pause, ...)")
    if ask("Did this speaker give consent? (yes/no)", "no").lower() != "yes":
        print("Not saved. A clip without consent must not be used. Delete its audio.")
        return
    row = {
        "id": clip_id,
        "audio": f"audio/{clip_id}.wav",
        "text": text,
        "turns": turns,
        "speaker": speaker,
        "consent": True,
        "notes": notes,
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Saved {clip_id}.")


if __name__ == "__main__":
    main()
