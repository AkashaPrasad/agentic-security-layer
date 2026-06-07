"""Plugins API routes — runtime plugin health, diagnostics, and upload."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.schemas.plugins import PluginHealthResponse, PluginUploadResponse
from app.engine.deps import get_current_user
from app.engine.plugins import get_plugin_health, get_plugins_directory, load_single_plugin
from app.storage.models import User

router = APIRouter(prefix="/plugins", tags=["plugins"])

# Maximum allowed plugin file size: 500 KB
_MAX_PLUGIN_SIZE = 500 * 1024


@router.get("/health", response_model=PluginHealthResponse)
async def get_plugins_health(
    current_user: User = Depends(get_current_user),
) -> PluginHealthResponse:
    """Return runtime plugin health and hook counters for UI visibility."""
    _ = current_user
    data = get_plugin_health()
    return PluginHealthResponse(**data)


@router.post("/upload", response_model=PluginUploadResponse)
async def upload_plugin(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> PluginUploadResponse:
    """Upload a custom plugin .py file and activate it immediately.

    The plugin is saved to the plugins/ directory and loaded without
    requiring a backend restart. It must expose a ``register(registrar)``
    function. An optional ``extension_hook(hook_name, context)`` function
    enables lifecycle hooks.
    """
    _ = current_user

    filename = file.filename or ""
    if not filename.endswith(".py"):
        raise HTTPException(
            status_code=400,
            detail="Only Python (.py) plugin files are accepted.",
        )

    # Prevent path traversal: use only the bare filename
    safe_name = Path(filename).name
    if not safe_name or safe_name.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    content = await file.read()
    if len(content) > _MAX_PLUGIN_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Plugin file exceeds {_MAX_PLUGIN_SIZE // 1024} KB limit.",
        )

    plugins_dir = get_plugins_directory()
    dest = plugins_dir / safe_name
    dest.write_bytes(content)

    result = load_single_plugin(dest)
    return PluginUploadResponse(
        success=result["success"],
        filename=safe_name,
        name=result.get("name", ""),
        error=result.get("error", ""),
    )
