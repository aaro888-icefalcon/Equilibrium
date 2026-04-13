"""Migration framework for save file version upgrades.

Extends MigrationRegistry from serialization.py with file-level migration.
Applies migrations in order from save's version to current version.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.schemas.serialization import (
    CURRENT_SCHEMA_VERSION,
    MigrationRegistry,
    migration_registry,
)


def _version_tuple(v: str) -> Tuple[int, ...]:
    """Convert version string to tuple for comparison."""
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0,)


class SaveMigrator:
    """Migrates save files from one schema version to another."""

    def __init__(
        self,
        save_root: str,
        registry: MigrationRegistry | None = None,
    ) -> None:
        self.save_root = save_root
        self.registry = registry or migration_registry

    def needs_migration(self) -> bool:
        """Check if the save needs migration."""
        world_path = os.path.join(self.save_root, "world.json")
        if not os.path.exists(world_path):
            return False
        try:
            with open(world_path, "r", encoding="utf-8") as f:
                world = json.load(f)
            version = world.get("schema_version", "")
            return version != "" and version != CURRENT_SCHEMA_VERSION
        except (json.JSONDecodeError, OSError):
            return False

    def get_save_version(self) -> Optional[str]:
        """Get the schema version of the current save."""
        world_path = os.path.join(self.save_root, "world.json")
        if not os.path.exists(world_path):
            return None
        try:
            with open(world_path, "r", encoding="utf-8") as f:
                world = json.load(f)
            return world.get("schema_version")
        except (json.JSONDecodeError, OSError):
            return None

    def migrate(self, dry_run: bool = False) -> MigrationResult:
        """Migrate all save files to current version.

        If dry_run is True, reports what would change without writing.
        Returns MigrationResult with details.
        """
        errors: List[str] = []
        migrated_files: List[str] = []

        old_version = self.get_save_version()
        if old_version is None:
            return MigrationResult(
                success=False,
                from_version=None,
                to_version=CURRENT_SCHEMA_VERSION,
                migrated_files=[],
                errors=["No save found or world.json unreadable"],
            )

        if old_version == CURRENT_SCHEMA_VERSION:
            return MigrationResult(
                success=True,
                from_version=old_version,
                to_version=CURRENT_SCHEMA_VERSION,
                migrated_files=[],
                errors=[],
            )

        # Migrate each file
        file_entity_map = {
            "world.json": "world",
            "player/character.json": "player",
            "factions.json": "factions",
            "npcs.json": "npcs",
            "locations.json": "locations",
            "clocks.json": "clocks",
            "metadata.json": "metadata",
        }

        for rel_path, entity_type in file_entity_map.items():
            full_path = os.path.join(self.save_root, rel_path)
            if not os.path.exists(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                errors.append(f"Cannot read {rel_path}: {e}")
                continue

            migrated = self.registry.migrate(
                data, entity_type, CURRENT_SCHEMA_VERSION
            )

            if migrated is not data:
                migrated_files.append(rel_path)
                if not dry_run:
                    try:
                        tmp_path = full_path + ".mig.tmp"
                        with open(tmp_path, "w", encoding="utf-8") as f:
                            json.dump(migrated, f, indent=2, default=str)
                        os.replace(tmp_path, full_path)
                    except OSError as e:
                        errors.append(f"Cannot write {rel_path}: {e}")

        success = len(errors) == 0
        return MigrationResult(
            success=success,
            from_version=old_version,
            to_version=CURRENT_SCHEMA_VERSION,
            migrated_files=migrated_files,
            errors=errors,
        )


class MigrationResult:
    """Result of a migration operation."""

    def __init__(
        self,
        success: bool,
        from_version: Optional[str],
        to_version: str,
        migrated_files: List[str],
        errors: List[str],
    ) -> None:
        self.success = success
        self.from_version = from_version
        self.to_version = to_version
        self.migrated_files = migrated_files
        self.errors = errors
