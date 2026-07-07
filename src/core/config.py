import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class ColumnConfig(BaseModel):
    id: str
    name: str
    width: int
    visible: bool
    order: int


class AppConfig(BaseModel):
    default_input_dir: str
    default_output_dir: str
    tcid_format: str
    global_metadata_keys: list[str] = Field(default_factory=list)
    columns: list[ColumnConfig]
    template_path: str | None = None
    default_tags: list[str] = Field(default_factory=lambda: ["@regression"])
    language: str = "id"
    indentation_spaces: int = 2
    tag_categories: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "smoke": ["@smoke"],
            "regression": ["@regression"],
            "sanity": ["@sanity"],
            "positive": ["@positive"],
            "negative": ["@negative"],
        }
    )


class ConfigManager:
    _config: Optional[AppConfig] = None

    @classmethod
    def load(cls, config_path: str | Path = "config.json") -> AppConfig:
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data: dict = json.load(f)
            if "global" in data or "excel" in data or "gherkin" in data:
                flat: dict = {}
                for ns in ("global", "excel", "gherkin"):
                    if ns in data and isinstance(data[ns], dict):
                        flat.update(data[ns])
                data = flat
            _LEGACY_KEY_MAP = {
                "gherkin_default_tags": "default_tags",
                "gherkin_tag_categories": "tag_categories",
            }
            for old_key, new_key in _LEGACY_KEY_MAP.items():
                if old_key in data and new_key not in data:
                    data[new_key] = data.pop(old_key)
            cls._config = AppConfig(**data)
            return cls._config
        raise FileNotFoundError(f"Configuration file not found at {path}")

    @classmethod
    def get(cls) -> AppConfig:
        if cls._config is None:
            return cls.load()
        return cls._config
