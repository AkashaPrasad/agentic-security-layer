"""Custom plugin loading and lifecycle hooks for the red-team engine."""

from app.engine.plugins.loader import (
    ensure_plugins_loaded,
    emit_plugin_hook,
    get_plugin_health,
    get_plugins_directory,
    list_loaded_plugins,
    load_single_plugin,
)

__all__ = [
    "ensure_plugins_loaded",
    "emit_plugin_hook",
    "get_plugin_health",
    "get_plugins_directory",
    "list_loaded_plugins",
    "load_single_plugin",
]
