"""
Converters package — prompt obfuscation / encoding converters.

Each converter transforms prompt text to bypass safety filters
through encoding, translation, or reformatting.
"""

from __future__ import annotations

from app.engine.converters.base import BaseConverter
from app.engine.converters.base64_converter import Base64Converter
from app.engine.converters.rot13_converter import ROT13Converter
from app.engine.converters.unicode_converter import UnicodeConverter
from app.engine.converters.payload_split import PayloadSplitConverter
from app.engine.converters.leetspeak import LeetspeakConverter
from app.engine.converters.translation import TranslationConverter
from app.engine.converters.jailbreak_wrapper import JailbreakWrapperConverter
from app.engine.converters.homoglyph import HomoglyphConverter
from app.engine.converters.token_split import TokenBoundarySplitConverter
from app.engine.converters.structured_smuggle import StructuredDataSmuggleConverter
from app.engine.converters.code_injection import CodeModeInjectionConverter
from app.engine.converters.multilingual_mix import MultilingualMixConverter
# New converters (GitHub research)
from app.engine.converters.ascii_art import ASCIIArtConverter
from app.engine.converters.morse import MorseConverter
from app.engine.converters.braille import BrailleConverter
from app.engine.converters.caesar_cipher import CaesarCipherConverter
from app.engine.converters.atbash import AtbashConverter
from app.engine.converters.nato import NATOConverter
from app.engine.converters.zalgo import ZalgoConverter
from app.engine.converters.zero_width import ZeroWidthConverter
from app.engine.converters.binary import BinaryConverter
from app.engine.converters.codechameleon import CodeChameleonConverter
from app.engine.converters.persuasion import PersuasionConverter
from app.engine.converters.tense import TenseConverter
from app.engine.converters.gcg_suffix import GCGSuffixConverter

# Registry: converter_name → Converter class
CONVERTER_REGISTRY: dict[str, type[BaseConverter]] = {
    "base64": Base64Converter,
    "rot13": ROT13Converter,
    "unicode_substitution": UnicodeConverter,
    "unicode": UnicodeConverter,
    "payload_split": PayloadSplitConverter,
    "leetspeak": LeetspeakConverter,
    "translation": TranslationConverter,
    "jailbreak_wrapper": JailbreakWrapperConverter,
    "homoglyph": HomoglyphConverter,
    "token_boundary_split": TokenBoundarySplitConverter,
    "structured_data_smuggle": StructuredDataSmuggleConverter,
    "code_mode_injection": CodeModeInjectionConverter,
    "multilingual_mix": MultilingualMixConverter,
    # New converters (GitHub research: PyRIT, garak, FuzzyAI)
    "ascii_art": ASCIIArtConverter,
    "morse": MorseConverter,
    "braille": BrailleConverter,
    "caesar_cipher": CaesarCipherConverter,
    "atbash": AtbashConverter,
    "nato_phonetic": NATOConverter,
    "zalgo": ZalgoConverter,
    "zero_width": ZeroWidthConverter,
    "binary": BinaryConverter,
    "codechameleon": CodeChameleonConverter,
    "persuasion": PersuasionConverter,
    "tense": TenseConverter,
    "gcg_suffix": GCGSuffixConverter,
}


def register_converter_class(name: str, converter_cls: type[BaseConverter]) -> None:
    """Register or override a converter at runtime (custom plugins)."""
    key = str(name).strip().lower()
    if not key:
        raise ValueError("Converter name cannot be empty")
    if not issubclass(converter_cls, BaseConverter):
        raise ValueError("converter_cls must inherit BaseConverter")
    CONVERTER_REGISTRY[key] = converter_cls


def get_converter(name: str) -> BaseConverter:
    """Get converter instance by name."""
    cls = CONVERTER_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown converter: {name}")
    return cls()


def get_all_converters() -> list[BaseConverter]:
    """Get instances of all available converters."""
    return [cls() for cls in CONVERTER_REGISTRY.values()]


__all__ = [
    "BaseConverter",
    "CONVERTER_REGISTRY",
    "get_converter",
    "get_all_converters",
]
