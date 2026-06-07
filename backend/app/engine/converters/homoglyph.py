"""Homoglyph converter — replaces Latin characters with visually identical Unicode glyphs."""

from __future__ import annotations

import random

from app.engine.converters.base import BaseConverter

# Latin → Cyrillic / Greek / special look-alike mapping
_HOMOGLYPH_MAP: dict[str, list[str]] = {
    "a": ["\u0430", "\u0251"],          # Cyrillic а, Latin alpha
    "c": ["\u0441", "\u03F2"],          # Cyrillic с, Greek lunate sigma
    "d": ["\u0501"],                     # Cyrillic ԁ
    "e": ["\u0435", "\u04BD"],          # Cyrillic е, Cyrillic ҽ
    "h": ["\u04BB"],                     # Cyrillic һ
    "i": ["\u0456", "\u0269"],          # Cyrillic і, Latin iota
    "j": ["\u0458"],                     # Cyrillic ј
    "k": ["\u043A"],                     # Cyrillic к
    "l": ["\u04CF", "\u0406"],          # Cyrillic ӏ, Cyrillic І
    "o": ["\u043E", "\u03BF", "\u0D20"],  # Cyrillic о, Greek omicron
    "p": ["\u0440", "\u03C1"],          # Cyrillic р, Greek rho
    "s": ["\u0455"],                     # Cyrillic ѕ
    "x": ["\u0445", "\u04B3"],          # Cyrillic х, Cyrillic ҳ
    "y": ["\u0443"],                     # Cyrillic у
    "A": ["\u0410"],                     # Cyrillic А
    "B": ["\u0412"],                     # Cyrillic В
    "C": ["\u0421"],                     # Cyrillic С
    "E": ["\u0415"],                     # Cyrillic Е
    "H": ["\u041D"],                     # Cyrillic Н
    "K": ["\u041A"],                     # Cyrillic К
    "M": ["\u041C"],                     # Cyrillic М
    "O": ["\u041E", "\u039F"],          # Cyrillic О, Greek Omicron
    "P": ["\u0420"],                     # Cyrillic Р
    "S": ["\u0405"],                     # Cyrillic Ѕ
    "T": ["\u0422"],                     # Cyrillic Т
    "X": ["\u0425"],                     # Cyrillic Х
}


class HomoglyphConverter(BaseConverter):
    name = "homoglyph"
    description = "Replace Latin characters with visually identical Unicode look-alikes (Cyrillic, Greek)"

    def __init__(self, replacement_rate: float = 0.4):
        self._rate = replacement_rate

    def convert(self, text: str) -> str:
        chars: list[str] = []
        for ch in text:
            if ch in _HOMOGLYPH_MAP and random.random() < self._rate:
                chars.append(random.choice(_HOMOGLYPH_MAP[ch]))
            else:
                chars.append(ch)
        return "".join(chars)
