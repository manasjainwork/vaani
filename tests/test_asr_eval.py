from pathlib import Path

import pytest

from vaani.asr_eval import corpus_wer, evaluate
from vaani.data import Clip, Turn


def make_clip(clip_id: str, text: str) -> Clip:
    return Clip(
        id=clip_id,
        audio_path=Path(f"{clip_id}.wav"),
        text=text,
        turns=(Turn(0.0, 1.0),),
        speaker="s1",
        consent=True,
    )


def fake_recognizer(answers: dict[str, str]):
    return lambda path: answers[path.stem]


def test_perfect_recognizer_scores_zero():
    clips = [make_clip("a", "mera order kab aayega")]
    scores = evaluate(clips, fake_recognizer({"a": "mera order kab aayega"}))
    assert corpus_wer(scores) == 0.0
    assert scores[0].hypothesis == "mera order kab aayega"


def test_corpus_wer_counts_long_clips_more():
    clips = [make_clip("short", "hello world"), make_clip("long", "a b c d e f g h")]
    answers = {"short": "hello there", "long": "a b c d e f g h"}
    scores = evaluate(clips, fake_recognizer(answers))
    assert scores[0].result.wer == pytest.approx(0.5)
    assert scores[1].result.wer == 0.0
    # 1 mistake in 10 words, not the average of 0.5 and 0.0
    assert corpus_wer(scores) == pytest.approx(0.1)


def test_script_mismatch_is_counted_as_errors():
    clips = [make_clip("a", "mera order kab aayega")]
    scores = evaluate(clips, fake_recognizer({"a": "मेरा ऑर्डर कब आएगा"}))
    assert corpus_wer(scores) == pytest.approx(1.0)
