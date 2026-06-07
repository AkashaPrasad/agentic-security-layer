"""Schemas for plugin health endpoints."""

from pydantic import BaseModel, Field


class PluginHookStats(BaseModel):
    calls: int = 0
    errors: int = 0
    last_called_at: str | None = None


class PluginHealthItem(BaseModel):
    name: str
    hooks_called: int = 0
    hook_errors: int = 0
    hooks: dict[str, PluginHookStats] = Field(default_factory=dict)
    last_called_at: str | None = None
    last_error: str | None = None
    last_error_at: str | None = None
    has_extension_hook: bool = False
    has_register: bool = False


class PluginLoadError(BaseModel):
    plugin_path: str
    error: str


class PluginHealthResponse(BaseModel):
    plugin_count: int = 0
    total_hook_calls: int = 0
    total_hook_errors: int = 0
    plugins: list[PluginHealthItem] = Field(default_factory=list)
    load_errors: list[PluginLoadError] = Field(default_factory=list)


class PluginUploadResponse(BaseModel):
    success: bool
    filename: str
    name: str = ""
    error: str = ""
