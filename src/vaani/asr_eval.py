"""Score a speech recognizer on our own clips.

The recognizer is passed in as a plain function (audio path in, text out), so this
file does not depend on any speech library and is easy to test.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from vaani.data import Clip
from vaani.metrics import WerResult, word_error_rate

Transcriber = Callable[[Path], str]


@dataclass(frozen=True)
class ClipScore:
    """What the recognizer wrote for one clip, and how many mistakes it made."""

    clip_id: str
    reference: str
    hypothesis: str
    result: WerResult


def evaluate(clips: Sequence[Clip], transcribe: Transcriber) -> list[ClipScore]:
    """Run the recognizer on every clip and score it against the correct text."""
    scores = []
    for clip in clips:
        hypothesis = transcribe(clip.audio_path)
        result = word_error_rate(clip.text, hypothesis)
        scores.append(ClipScore(clip.id, clip.text, hypothesis, result))
    return scores


# --8<-- [start:corpus]
def corpus_wer(scores: Sequence[ClipScore]) -> float:
    """One WER for the whole set: all mistakes divided by all reference words.

    This is not the average of the per-clip numbers. A long clip should count more
    than a short one, because it holds more words.
    """
    errors = sum(
        s.result.substitutions + s.result.deletions + s.result.insertions for s in scores
    )
    words = sum(s.result.reference_words for s in scores)
    return errors / words
# --8<-- [end:corpus]
