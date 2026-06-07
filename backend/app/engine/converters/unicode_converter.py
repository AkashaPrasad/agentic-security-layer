"""Unicode substitution converter — replace chars with look-alikes."""

from __future__ import annotations

import random

from app.engine.converters.base import BaseConverter

# Map ASCII characters to visually similar Unicode homoglyphs
UNICODE_MAP: dict[str, list[str]] = {
    "a": ["\u0430", "\u00e0", "\u00e1"],  # Cyrillic а, à, á
    "c": ["\u0441", "\u00e7"],  # Cyrillic с, ç
    "e": ["\u0435", "\u00e8", "\u00e9"],  # Cyrillic е, è, é
    "i": ["\u0456", "\u00ec", "\u00ed"],  # Cyrillic і, ì, í
    "o": ["\u043e", "\u00f2", "\u00f3"],  # Cyrillic о, ò, ó
    "p": ["\u0440"],  # Cyrillic р
    "s": ["\u0455"],  # Cyrillic ѕ
    "u": ["\u00f9", "\u00fa"],  # ù, ú
    "x": ["\u0445"],  # Cyrillic х
    "y": ["\u0443"],  # Cyrillic у
    "A": ["\u0410", "\u00c0"],  # Cyrillic А, À
    "B": ["\u0412"],  # Cyrillic В
    "C": ["\u0421"],  # Cyrillic С
    "E": ["\u0415", "\u00c8"],  # Cyrillic Е, È
    "H": ["\u041d"],  # Cyrillic Н
    "I": ["\u0406", "\u00cc"],  # Cyrillic І, Ì
    "K": ["\u041a"],  # Cyrillic К
    "M": ["\u041c"],  # Cyrillic М
    "O": ["\u041e", "\u00d2"],  # Cyrillic О, Ò
    "P": ["\u0420"],  # Cyrillic Р
    "S": ["\u0405"],  # Cyrillic Ѕ
    "T": ["\u0422"],  # Cyrillic Т
    "X": ["\u0425"],  # Cyrillic Х
}

# Probability of substituting each eligible character
SUBSTITUTION_RATE = 0.4


class UnicodeConverter(BaseConverter):
    name = "unicode_substitution"
    description = "Replace characters with Unicode look-alikes"

    def convert(self, text: str) -> str:
        result = []
        for char in text:
            if char in UNICODE_MAP and random.random() < SUBSTITUTION_RATE:
                result.append(random.choice(UNICODE_MAP[char]))
            else:
                result.append(char)
        return "".join(result)
