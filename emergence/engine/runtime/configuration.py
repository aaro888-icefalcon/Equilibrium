"""Game configuration — loads settings from simple key=value files.

No external dependencies. Supports comments (#), string/int/float/bool values.
"""

from __future__ import annotations

import dataclasses
import os
from typing import Any, Dict, Optional


@dataclasses.dataclass
class GameConfig:
    """All game configuration settings with defaults."""

    save_root: str = "saves/default"
    log_level: str = "info"
    seed: int = 0  # 0 = random
    autosave_interval: int = 300  # seconds
    narrator_mode: str = "mock"  # "mock" or "live"
    narrator_max_tokens: int = 500
    narrator_temperature: float = 0.7
    combat_animation_delay: float = 0.0
    tick_speed: str = "normal"  # "fast", "normal", "slow"
    color_output: bool = True
    debug_mode: bool = False
    dry_run: bool = False


def load_config(path: str) -> GameConfig:
    """Load config from a key=value text file. Missing keys use defaults."""
    config = GameConfig()

    if not os.path.exists(path):
        return config

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            # Strip surrounding quotes
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]

            if hasattr(config, key):
                field_type = type(getattr(config, key))
                try:
                    if field_type is bool:
                        setattr(config, key, value.lower() in ("true", "1", "yes"))
                    elif field_type is int:
                        setattr(config, key, int(value))
                    elif field_type is float:
                        setattr(config, key, float(value))
                    else:
                        setattr(config, key, value)
                except (ValueError, TypeError):
                    pass  # Keep default

    return config


def save_config(config: GameConfig, path: str) -> None:
    """Write config to a key=value file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Emergence game configuration\n")
        for field in dataclasses.fields(config):
            value = getattr(config, field.name)
            if isinstance(value, bool):
                f.write(f"{field.name} = {'true' if value else 'false'}\n")
            elif isinstance(value, str) and " " in value:
                f.write(f'{field.name} = "{value}"\n')
            else:
                f.write(f"{field.name} = {value}\n")
