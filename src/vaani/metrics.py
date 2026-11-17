"""Metrics for speech recognition.

We write these from scratch so that we understand every line.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass


# --8<-- [start:normalize]
def normalize_text(text: str) -> str:
    """Make two texts comparable: same Unicode form, lowercase, no punctuation."""
    text = unicodedata.normalize("NFC", text).lower()
    cleaned = []
    for ch in text:
        # Keep letters (L), marks (M) and numbers (N). Everything else becomes a space.
        # Marks matter: Hindi vowel signs (like the sign in "मेरा") are marks.
        if unicodedata.category(ch)[0] in ("L", "M", "N"):
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    return " ".join("".join(cleaned).split())
# --8<-- [end:normalize]


@dataclass(frozen=True)
class WerResult:
    """The WER number and where the mistakes came from."""

    wer: float
    substitutions: int
    deletions: int
    insertions: int
    reference_words: int


# --8<-- [start:wer]
def word_error_rate(
    reference: str, hypothesis: str, normalize: bool = True
) -> WerResult:
    """Word Error Rate = (substitutions + deletions + insertions) / reference words."""
    if normalize:
        reference = normalize_text(reference)
        hypothesis = normalize_text(hypothesis)

    ref = reference.split()
    hyp = hypothesis.split()
    n, m = len(ref), len(hyp)
    if n == 0:
        raise ValueError("The reference is empty after cleaning, so WER is undefined.")

    # dist[i][j] = fewest edits to turn the first i reference words
    # into the first j hypothesis words.
    dist = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dist[i][0] = i  # delete i words
    for j in range(m + 1):
        dist[0][j] = j  # insert j words

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dist[i][j] = dist[i - 1][j - 1]
            else:
                dist[i][j] = 1 + min(
                    dist[i - 1][j - 1],  # substitute
                    dist[i - 1][j],  # delete
                    dist[i][j - 1],  # insert
                )

    # Walk back from the end to count each kind of mistake.
    subs = dels = ins = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref[i - 1] == hyp[j - 1] and dist[i][j] == dist[i - 1][j - 1]:
            i, j = i - 1, j - 1
        elif i > 0 and j > 0 and dist[i][j] == dist[i - 1][j - 1] + 1:
            subs += 1
            i, j = i - 1, j - 1
        elif i > 0 and dist[i][j] == dist[i - 1][j] + 1:
            dels += 1
            i -= 1
        else:
            ins += 1
            j -= 1

    return WerResult(
        wer=dist[n][m] / n,
        substitutions=subs,
        deletions=dels,
        insertions=ins,
        reference_words=n,
    )
# --8<-- [end:wer]
