"""Find an order number in what the customer said.

Order numbers have exactly four digits. The parser is strict on purpose: when it is
not sure, it returns None, and the agent asks the customer to say the number again.
A wrong guess is worse than asking again, because it could show someone else's order.
"""

from __future__ import annotations

import unicodedata

from vaani.metrics import normalize_text

ORDER_NUMBER_LENGTH = 4
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# --8<-- [start:digit_words]
_DIGIT_WORDS = {
    "0": ["zero", "shunya", "jeero", "जीरो", "ज़ीरो", "शून्य"],
    "1": ["one", "ek", "एक"],
    "2": ["two", "do", "दो"],
    "3": ["three", "teen", "तीन"],
    "4": ["four", "char", "chaar", "चार"],
    "5": ["five", "paanch", "panch", "पाँच", "पांच"],
    "6": ["six", "chhe", "chhah", "छह", "छः", "छे"],
    "7": ["seven", "saat", "सात"],
    "8": ["eight", "aath", "आठ"],
    "9": ["nine", "nau", "नौ"],
}
# --8<-- [end:digit_words]
DIGIT_OF = {
    unicodedata.normalize("NFC", word).lower(): digit
    for digit, words in _DIGIT_WORDS.items()
    for word in words
}


def digit_runs(text: str) -> list[str]:
    """Every unbroken stretch of digits (written or spoken) in the text."""
    runs: list[str] = []
    current = ""
    for token in normalize_text(text.translate(_DEVANAGARI_DIGITS)).split():
        if token.isascii() and token.isdigit():
            current += token
        elif token in DIGIT_OF:
            current += DIGIT_OF[token]
        elif current:
            runs.append(current)
            current = ""
    if current:
        runs.append(current)
    return runs


# --8<-- [start:parse]
def parse_order_number(text: str) -> str | None:
    """The one four-digit number in the text, or None if there is none or more than one."""
    candidates = [run for run in digit_runs(text) if len(run) == ORDER_NUMBER_LENGTH]
    return candidates[0] if len(candidates) == 1 else None
# --8<-- [end:parse]
