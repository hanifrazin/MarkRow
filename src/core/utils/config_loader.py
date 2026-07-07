import json
from pathlib import Path
from typing import Any

from src.core.config import ConfigManager, AppConfig

_OLD_ROOT_KEYS = {"columns", "default_input_dir", "default_output_dir", "tcid_format", "global_metadata_keys"}

_NEW_DEFAULTS: dict[str, dict[str, Any]] = {
    "global": {
        "default_input_dir": "samples/input",
        "default_output_dir": "samples/output",
        "tcid_format": "TC-{seq:03d}",
        "global_metadata_keys": [],
    },
    "excel": {
        "columns": [],
        "template_path": None,
    },
    "gherkin": {
        "language": "id",
        "default_tags": ["@mamow"],
        "indentation_spaces": 2,
        "tag_categories": {
            "smoke": ["@smoke"],
            "regression": ["@regression"],
        },
    },
}


def load_config(path: str | Path = "config.json") -> dict[str, Any]:
    p = Path(path)

    if not p.exists():
        data = {ns: dict(vals) for ns, vals in _NEW_DEFAULTS.items()}
        _write_config(p, data)
        return data

    try:
        with open(p, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Corrupted configuration file '{path}': {e}") from e

    if _is_old_format(data):
        data = _migrate_old_to_new(data)
        _write_config(p, data)
        print("[INFO] Config auto-migrated to new format.")

    _apply_defaults(data)
    return data


def _is_old_format(data: dict[str, Any]) -> bool:
    return "global" not in data and any(k in data for k in _OLD_ROOT_KEYS)


def _migrate_old_to_new(old: dict[str, Any]) -> dict[str, Any]:
    new: dict[str, Any] = {}

    new["global"] = {
        "default_input_dir": old.get("default_input_dir", "samples/input"),
        "default_output_dir": old.get("default_output_dir", "samples/output"),
        "tcid_format": old.get("tcid_format", "TC-{seq:03d}"),
        "global_metadata_keys": old.get("global_metadata_keys", []),
    }

    new["excel"] = {
        "columns": old.get("columns", []),
        "template_path": old.get("template_path"),
    }

    gherkin: dict[str, Any] = {
        "language": old.get("language", "id"),
        "default_tags": old.get("gherkin_default_tags", ["@mamow"]),
        "indentation_spaces": old.get("indentation_spaces", 2),
    }
    if "gherkin_tag_categories" in old:
        gherkin["tag_categories"] = old["gherkin_tag_categories"]
    new["gherkin"] = gherkin

    return new


def _apply_defaults(data: dict[str, Any]) -> None:
    for ns, defaults in _NEW_DEFAULTS.items():
        if ns not in data or not isinstance(data[ns], dict):
            data[ns] = {}
        for key, val in defaults.items():
            data[ns].setdefault(key, val)


def _write_config(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_config_with_migration(config_path: str | Path = "config.json") -> AppConfig:
    load_config(config_path)
    ConfigManager.load(config_path)
    return ConfigManager.get()
