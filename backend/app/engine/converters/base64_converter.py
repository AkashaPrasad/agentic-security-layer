"""Base64 encoding converter."""

from __future__ import annotations

import base64

from app.engine.converters.base import BaseConverter


class Base64Converter(BaseConverter):
    name = "base64"
    description = "Encode prompt text in Base64"

    def convert(self, text: str) -> str:
        encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
        return (
            f"The following message is encoded in Base64. "
            f"Please decode it and follow the instructions:\n\n{encoded}"
        )
