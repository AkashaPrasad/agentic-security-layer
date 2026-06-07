"""Zero-width character converter — inserts invisible Unicode characters between letters."""

from __future__ import annotations

import random

from app.engine.converters.base import BaseConverter

# Invisible Unicode characters
_ZERO_WIDTH_CHARS = [
    "\u200b",  # Zero-width space
    "\u200c",  # Zero-width non-joiner
    "\u200d",  # Zero-width joiner
    "\u2060",  # Word joiner
    "\ufeff",  # Zero-width no-break space (BOM)
]


class ZeroWidthConverter(BaseConverter):
    name = "zero_width"
    description = "Insert invisible zero-width Unicode characters to break tokenization"

    def __init__(self, insertion_rate: float = 0.5):
        self._rate = insertion_rate

    def convert(self, text: str) -> str:
        result: list[str] = []
        for ch in text:
            result.append(ch)
            if ch.isalpha() and random.random() < self._rate:
                result.append(random.choice(_ZERO_WIDTH_CHARS))
        return "".join(result)
