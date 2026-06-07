"""
PyRIT Bridge — integration layer for Microsoft PyRIT library.

Wraps PyRIT orchestrators, targets, converters, and scorers to work
within our engine's credential management, progress tracking, and
result persistence system.
"""

from __future__ import annotations

PYRIT_AVAILABLE = False
try:
    import pyrit  # noqa: F401
    PYRIT_AVAILABLE = True
except ImportError:
    pass

__all__ = ["PYRIT_AVAILABLE"]
