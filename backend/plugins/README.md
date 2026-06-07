# Custom Plugins

This project supports custom plugins inspired by promptfoo extension hooks and plugin registries.

## Where plugins are loaded from

- Default directory: `backend/plugins/*.py`
- Optional additional paths via env var: `CUSTOM_PLUGIN_PATHS`
  - Comma-separated file and/or directory paths

## Enable/disable

- `CUSTOM_PLUGINS_ENABLED=true` (default)

## Plugin module API

A plugin file can define either or both:

1. `register(registrar)`
- Register runtime classes:
  - `registrar.register_converter(name, converter_cls)`
  - `registrar.register_strategy(risk_category, strategy_cls)`

2. `extension_hook(hook_name, context)`
- Handle lifecycle events and optionally return updated context.

Supported hooks:
- `before_experiment`
- `before_generation`
- `after_generation`
- `before_each_prompt`
- `after_each_prompt`
- `after_experiment`

## Example

See `backend/plugins/example_custom_plugin.py`.

## Safety notes

- Plugins run as Python code in-process and have full backend permissions.
- Use only trusted plugin files.
