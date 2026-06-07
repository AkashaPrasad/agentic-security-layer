"""
PyRIT Converter Bridge — maps our converters to PyRIT converters.

When PyRIT is available, bridges between our converter interface and
PyRIT's PromptConverter classes. Falls back to our engine converters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.engine.converters import CONVERTER_REGISTRY, get_converter

if TYPE_CHECKING:
    from app.engine.converters.base import BaseConverter

logger = logging.getLogger(__name__)

# Map our converter names to PyRIT converter class names
PYRIT_CONVERTER_MAP: dict[str, str] = {
    "base64": "Base64Converter",
    "rot13": "ROT13Converter",
    "unicode_substitution": "UnicodeSubstitutionConverter",
    "payload_split": "PromptSplittingConverter",
    "leetspeak": "LeetspeakConverter",
    "translation": "TranslationConverter",
    "jailbreak_wrapper": "JailbreakWrapperConverter",  # Custom (ours)
}


def get_pyrit_converter(name: str) -> object | None:
    """
    Get a PyRIT converter instance for the given converter name.

    Returns None if PyRIT is not installed or the converter is not available.
    Falls back to our engine's converter.
    """
    try:
        from app.engine.pyrit_bridge import PYRIT_AVAILABLE

        if not PYRIT_AVAILABLE:
            return None

        pyrit_class_name = PYRIT_CONVERTER_MAP.get(name)
        if not pyrit_class_name:
            return None

        # Try to import from PyRIT
        from pyrit.prompt_converter import (  # type: ignore[import-not-found]
            Base64Converter,
            ROT13Converter,
            UnicodeSubstitutionConverter,
            LeetspeakConverter,
        )

        converter_map = {
            "Base64Converter": Base64Converter,
            "ROT13Converter": ROT13Converter,
            "UnicodeSubstitutionConverter": UnicodeSubstitutionConverter,
            "LeetspeakConverter": LeetspeakConverter,
        }

        cls = converter_map.get(pyrit_class_name)
        if cls:
            return cls()

    except Exception as e:
        logger.debug("PyRIT converter %s not available: %s", name, e)

    return None


def convert_with_fallback(name: str, text: str) -> str:
    """
    Convert text using PyRIT converter if available, otherwise fall back
    to our engine's converter.
    """
    # Try PyRIT first
    pyrit_conv = get_pyrit_converter(name)
    if pyrit_conv is not None:
        try:
            # PyRIT converters use convert_async or convert methods
            if hasattr(pyrit_conv, "convert"):
                result = pyrit_conv.convert(text)
                if isinstance(result, str):
                    return result
        except Exception:
            pass

    # Fallback to our converter
    our_converter = get_converter(name)
    return our_converter.convert(text)
