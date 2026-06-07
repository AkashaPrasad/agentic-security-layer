"""
Base converter abstract class.

All prompt converters inherit from BaseConverter and implement
the convert() method to transform prompt text.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseConverter(ABC):
    """
    Abstract base class for all prompt converters.

    A converter transforms input text into an obfuscated or
    re-encoded form to test whether safety filters can be bypassed.
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    def convert(self, text: str) -> str:
        """
        Transform the input text.

        Parameters
        ----------
        text : str
            The original prompt text.

        Returns
        -------
        str
            The converted/obfuscated text.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
