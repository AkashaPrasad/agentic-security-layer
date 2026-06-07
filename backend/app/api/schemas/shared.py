"""
Shared Pydantic schemas used across multiple API modules.
"""

from uuid import UUID

from pydantic import BaseModel


class UserBrief(BaseModel):
    """Lightweight user reference embedded in responses."""

    id: UUID
    email: str
    full_name: str | None = None

    model_config = {"from_attributes": True}


class ProviderBrief(BaseModel):
    """Lightweight provider reference embedded in responses."""

    id: UUID
    name: str
    provider_type: str

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
    code: str


class MessageResponse(BaseModel):
    """Generic success message."""

    message: str
