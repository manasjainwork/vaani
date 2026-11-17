import random

import jiwer
import pytest

from vaani.metrics import normalize_text, word_error_rate


def test_perfect_match_is_zero():
    result = word_error_rate("mera order kab aayega", "mera order kab aayega")
    assert result.wer == 0.0
    assert (result.substitutions, result.deletions, result.insertions) == (0, 0, 0)


def test_one_substitution():
    result = word_error_rate("mera order kab aayega", "mera order kab ayega")
    assert result.wer == pytest.approx(0.25)
    assert result.substitutions == 1


def test_one_deletion():
    result = word_error_rate("mera order kab aayega", "mera order aayega")
    assert result.wer == pytest.approx(0.25)
    assert result.deletions == 1


def test_one_insertion():
    result = word_error_rate("mera order aayega", "mera order kab aayega")
    assert result.wer == pytest.approx(1 / 3)
    assert result.insertions == 1


def test_mixed_mistakes():
    result = word_error_rate("the cat sat on the mat", "the cat sit on mat")
    assert result.wer == pytest.approx(2 / 6)
    assert result.substitutions == 1
    assert result.deletions == 1
    assert result.insertions == 0


def test_empty_hypothesis_means_everything_deleted():
    result = word_error_rate("hello world", "")
    assert result.wer == 1.0
    assert result.deletions == 2


def test_wer_can_be_above_one():
    result = word_error_rate("hi", "hi there my friend")
    assert result.wer == pytest.approx(3.0)


def test_empty_reference_raises():
    with pytest.raises(ValueError):
        word_error_rate("   ", "anything")


def test_normalization_ignores_case_and_punctuation():
    assert word_error_rate("Hello, World!", "hello world").wer == 0.0


def test_hindi_words_are_kept_whole():
    out = normalize_text("मेरा ऑर्डर कब आएगा?")
    assert "?" not in out
    assert len(out.split()) == 4


def test_matches_jiwer_on_random_sentences():
    rng = random.Random(0)
    vocab = ["mera", "order", "kab", "aayega", "refund", "kya", "hua", "bhai", "ji"]
    for _ in range(300):
        ref = " ".join(rng.choices(vocab, k=rng.randint(1, 12)))
        hyp = " ".join(rng.choices(vocab, k=rng.randint(1, 12)))
        assert word_error_rate(ref, hyp).wer == pytest.approx(jiwer.wer(ref, hyp))
