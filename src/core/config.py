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


class ConfigManager:
    _config: Optional[AppConfig] = None

    @classmethod
    def load(cls, config_path: str | Path = "config.json") -> AppConfig:
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._config = AppConfig(**data)
                return cls._config
        raise FileNotFoundError(f"Configuration file not found at {path}")

    @classmethod
    def get(cls) -> AppConfig:
        if cls._config is None:
            return cls.load()
        return cls._config
