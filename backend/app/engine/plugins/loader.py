"""Plugin loader inspired by promptfoo-style extensions.

Supports two integration patterns in plugin modules:
1) register(registrar): register custom converters/strategies
2) extension_hook(hook_name, context): handle lifecycle events
"""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from app.config import settings

logger = logging.getLogger(__name__)


HookFunc = Callable[[str, dict[str, Any]], dict[str, Any] | None]


@dataclass
class PluginRegistry:
    loaded_paths: set[str] = field(default_factory=set)
    loaded_names: list[str] = field(default_factory=list)
    hook_handlers: list[tuple[str, HookFunc]] = field(default_factory=list)
    plugin_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    load_errors: list[dict[str, str]] = field(default_factory=list)


_REGISTRY = PluginRegistry()


class PluginRegistrar:
    """API exposed to custom plugins for runtime registration."""

    def register_converter(self, name: str, converter_cls: type) -> None:
        from app.engine.converters import register_converter_class

        register_converter_class(name, converter_cls)

    def register_strategy(self, risk_category: str, strategy_cls: type) -> None:
        from app.engine.strategies import register_strategy_class

        register_strategy_class(risk_category, strategy_cls)


def _iter_plugin_files() -> list[Path]:
    configured = getattr(settings, "custom_plugin_paths", "")
    candidates: list[Path] = []

    if configured:
        for raw in str(configured).split(","):
            p = Path(raw.strip())
            if p.exists() and p.is_file() and p.suffix == ".py":
                candidates.append(p)
            elif p.exists() and p.is_dir():
                candidates.extend(sorted(p.glob("*.py")))

    # Default local plugin folder
    default_dir = Path(__file__).resolve().parents[3] / "plugins"
    if default_dir.exists() and default_dir.is_dir():
        candidates.extend(sorted(default_dir.glob("*.py")))

    # Deduplicate while preserving order
    dedup: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        key = str(p.resolve())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(p)
    return dedup


def _load_module_from_path(path: Path) -> ModuleType:
    module_name = f"custom_plugin_{path.stem}_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to create import spec for plugin: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _register_plugin_module(path: Path, module: ModuleType) -> None:
    registrar = PluginRegistrar()
    plugin_name = path.stem

    register_fn = getattr(module, "register", None)
    if callable(register_fn):
        register_fn(registrar)

    hook_fn = getattr(module, "extension_hook", None)
    if callable(hook_fn):
        _REGISTRY.hook_handlers.append((plugin_name, hook_fn))

    _REGISTRY.plugin_stats.setdefault(
        plugin_name,
        {
            "hooks_called": 0,
            "hook_errors": 0,
            "hooks": {},
            "last_called_at": None,
            "last_error": None,
            "last_error_at": None,
            "has_extension_hook": bool(callable(hook_fn)),
            "has_register": bool(callable(register_fn)),
        },
    )

    _REGISTRY.loaded_names.append(plugin_name)


def ensure_plugins_loaded() -> None:
    """Load custom plugins once per process."""
    if not bool(getattr(settings, "custom_plugins_enabled", True)):
        return

    for plugin_path in _iter_plugin_files():
        resolved = str(plugin_path.resolve())
        if resolved in _REGISTRY.loaded_paths:
            continue
        try:
            module = _load_module_from_path(plugin_path)
            _register_plugin_module(plugin_path, module)
            _REGISTRY.loaded_paths.add(resolved)
            logger.info("Loaded custom plugin: %s", plugin_path)
        except Exception as exc:
            _REGISTRY.load_errors.append(
                {
                    "plugin_path": resolved,
                    "error": str(exc),
                }
            )
            logger.exception("Failed to load custom plugin %s: %s", plugin_path, exc)


def emit_plugin_hook(hook_name: str, context: dict[str, Any]) -> dict[str, Any]:
    """Emit a lifecycle hook to all loaded plugins.

    Like promptfoo hooks, each plugin can mutate and return context.
    """
    ensure_plugins_loaded()

    current = dict(context)
    for plugin_name, hook in _REGISTRY.hook_handlers:
        stats = _REGISTRY.plugin_stats.setdefault(
            plugin_name,
            {
                "hooks_called": 0,
                "hook_errors": 0,
                "hooks": {},
                "last_called_at": None,
                "last_error": None,
                "last_error_at": None,
                "has_extension_hook": True,
                "has_register": False,
            },
        )
        hooks_map = stats.setdefault("hooks", {})
        per_hook = hooks_map.setdefault(
            hook_name,
            {
                "calls": 0,
                "errors": 0,
                "last_called_at": None,
            },
        )
        try:
            result = hook(hook_name, current)
            now = datetime.now(timezone.utc).isoformat()
            stats["hooks_called"] = int(stats.get("hooks_called", 0)) + 1
            stats["last_called_at"] = now
            per_hook["calls"] = int(per_hook.get("calls", 0)) + 1
            per_hook["last_called_at"] = now
            if isinstance(result, dict):
                current = result
        except Exception as exc:
            now = datetime.now(timezone.utc).isoformat()
            stats["hook_errors"] = int(stats.get("hook_errors", 0)) + 1
            stats["last_error"] = str(exc)
            stats["last_error_at"] = now
            per_hook["errors"] = int(per_hook.get("errors", 0)) + 1
            logger.exception("Plugin hook failed (%s): %s", hook_name, exc)
    return current


def load_single_plugin(path: Path) -> dict[str, Any]:
    """Load and activate a single plugin file immediately (no restart needed).

    Returns {"success": True, "name": stem} or {"success": False, "error": msg}.
    """
    ensure_plugins_loaded()
    resolved = str(path.resolve())
    # Allow re-loading by removing from loaded_paths if already there
    _REGISTRY.loaded_paths.discard(resolved)
    try:
        module = _load_module_from_path(path)
        _register_plugin_module(path, module)
        _REGISTRY.loaded_paths.add(resolved)
        logger.info("Loaded custom plugin: %s", path)
        return {"success": True, "name": path.stem}
    except Exception as exc:
        _REGISTRY.load_errors.append({"plugin_path": resolved, "error": str(exc)})
        logger.exception("Failed to load custom plugin %s: %s", path, exc)
        return {"success": False, "error": str(exc)}


def get_plugins_directory() -> Path:
    """Return the default plugins directory path (created if missing)."""
    default_dir = Path(__file__).resolve().parents[3] / "plugins"
    default_dir.mkdir(exist_ok=True)
    return default_dir


def list_loaded_plugins() -> list[str]:
    ensure_plugins_loaded()
    return list(_REGISTRY.loaded_names)


def get_plugin_health() -> dict[str, Any]:
    """Return runtime plugin health summary for UI/API usage."""
    ensure_plugins_loaded()

    plugin_items: list[dict[str, Any]] = []
    total_hook_calls = 0
    total_hook_errors = 0

    for name in _REGISTRY.loaded_names:
        stats = _REGISTRY.plugin_stats.get(name, {})
        hooks_called = int(stats.get("hooks_called", 0))
        hook_errors = int(stats.get("hook_errors", 0))
        total_hook_calls += hooks_called
        total_hook_errors += hook_errors

        plugin_items.append(
            {
                "name": name,
                "hooks_called": hooks_called,
                "hook_errors": hook_errors,
                "hooks": stats.get("hooks", {}),
                "last_called_at": stats.get("last_called_at"),
                "last_error": stats.get("last_error"),
                "last_error_at": stats.get("last_error_at"),
                "has_extension_hook": bool(stats.get("has_extension_hook", False)),
                "has_register": bool(stats.get("has_register", False)),
            }
        )

    return {
        "plugin_count": len(_REGISTRY.loaded_names),
        "total_hook_calls": total_hook_calls,
        "total_hook_errors": total_hook_errors,
        "plugins": plugin_items,
        "load_errors": list(_REGISTRY.load_errors),
    }
