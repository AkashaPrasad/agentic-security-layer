"""Token-boundary splitting converter — breaks sensitive words across token boundaries."""

from __future__ import annotations

import random
import re

from app.engine.converters.base import BaseConverter

# Words commonly flagged by safety filters
_SENSITIVE_WORDS = [
    "ignore", "bypass", "override", "hack", "exploit", "inject",
    "password", "credential", "secret", "admin", "delete", "drop",
    "system", "root", "sudo", "execute", "shell", "command",
    "disable", "restriction", "filter", "safety", "instruction",
    "unrestricted", "jailbreak", "forbidden", "illegal", "malware",
    "vulnerability", "attack", "exfiltrate", "escalat",
]

# Splitting strategies
_SPLIT_CHARS = [
    "\u200B",           # Zero-width space
    "\u200C",           # Zero-width non-joiner
    "\u200D",           # Zero-width joiner
    "\uFEFF",           # Zero-width no-break space
    "\u00AD",           # Soft hyphen
]


class TokenBoundarySplitConverter(BaseConverter):
    name = "token_boundary_split"
    description = "Split sensitive words with zero-width characters to break tokenizer alignment"

    def __init__(self, split_probability: float = 0.7):
        self._prob = split_probability

    def _split_word(self, word: str) -> str:
        """Insert zero-width characters at random positions inside a word."""
        if len(word) < 4:
            return word
        # Pick 1-2 split points
        n_splits = random.randint(1, min(2, len(word) - 2))
        positions = sorted(random.sample(range(1, len(word)), n_splits))
        parts: list[str] = []
        prev = 0
        for pos in positions:
            parts.append(word[prev:pos])
            prev = pos
        parts.append(word[prev:])
        sep = random.choice(_SPLIT_CHARS)
        return sep.join(parts)

    def convert(self, text: str) -> str:
        result = text
        for word in _SENSITIVE_WORDS:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            matches = list(pattern.finditer(result))
            # Process in reverse to preserve positions
            for m in reversed(matches):
                if random.random() < self._prob:
                    original = m.group()
                    split = self._split_word(original)
                    result = result[:m.start()] + split + result[m.end():]
        return result
