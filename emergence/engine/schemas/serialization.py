"""Serialization helpers for Emergence schemas.

Provides JSON round-trip serialization, schema versioning, and migration framework.
"""
import json
import os
from typing import Any, Dict, Type, Optional
from datetime import datetime

CURRENT_SCHEMA_VERSION = "1.0"


def to_json(obj: Any, indent: int = 2) -> str:
    """Serialize a dataclass instance to JSON string."""
    if hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict(), indent=indent)
    return json.dumps(obj, indent=indent, default=str)


def from_json(json_str: str) -> Dict:
    """Deserialize JSON string to dict."""
    return json.loads(json_str)


def save_to_file(obj: Any, filepath: str) -> None:
    """Atomically save a dataclass to a JSON file using temp-and-rename."""
    import tempfile
    data = obj.to_dict() if hasattr(obj, 'to_dict') else obj
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    # Write to temp file first, then atomic rename
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp_path, filepath)
    except:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def load_from_file(filepath: str) -> Dict:
    """Load a JSON file and return as dict."""
    with open(filepath, 'r') as f:
        return json.load(f)


def check_schema_version(data: Dict, expected: str = CURRENT_SCHEMA_VERSION) -> bool:
    """Check if data has expected schema version."""
    return data.get('schema_version') == expected


class MigrationRegistry:
    """Registry for schema migrations."""

    def __init__(self):
        self._migrations: Dict[tuple, callable] = {}

    def register(self, from_version: str, to_version: str, entity_type: str):
        """Decorator to register a migration function."""
        def decorator(func):
            self._migrations[(from_version, to_version, entity_type)] = func
            return func
        return decorator

    def migrate(self, data: Dict, entity_type: str, target_version: str = CURRENT_SCHEMA_VERSION) -> Dict:
        """Migrate data to target version."""
        current = data.get('schema_version', '1.0')
        if current == target_version:
            return data
        key = (current, target_version, entity_type)
        if key in self._migrations:
            return self._migrations[key](data)
        return data  # No migration needed or available


migration_registry = MigrationRegistry()
