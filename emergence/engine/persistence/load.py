"""Load manager — classifies and loads save files.

Classification: FRESH (no save), PARTIAL (incomplete), VALID (all files present),
CORRUPT (JSON parse error), VERSION_MISMATCH (schema version incompatible).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple


class LoadResult:
    """Result of loading a save."""

    def __init__(
        self,
        classification: str,
        world: Dict[str, Any] | None = None,
        player: Dict[str, Any] | None = None,
        factions: Dict[str, Any] | None = None,
        npcs: Dict[str, Any] | None = None,
        locations: Dict[str, Any] | None = None,
        clocks: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
        errors: List[str] | None = None,
    ) -> None:
        self.classification = classification
        self.world = world
        self.player = player
        self.factions = factions
        self.npcs = npcs
        self.locations = locations
        self.clocks = clocks
        self.metadata = metadata
        self.errors = errors or []


class LoadManager:
    """Loads and classifies save files."""

    REQUIRED_FILES = [
        "world.json",
        "player/character.json",
        "factions.json",
        "npcs.json",
        "locations.json",
        "clocks.json",
    ]

    CURRENT_SCHEMA_VERSION = "1.0"

    def __init__(self, save_root: str) -> None:
        self.save_root = save_root

    def classify(self) -> str:
        """Classify the save state.

        Returns one of: FRESH, PARTIAL, VALID, CORRUPT, VERSION_MISMATCH.
        """
        if not os.path.exists(self.save_root):
            return "FRESH"

        # Check for world.json (save-complete marker)
        world_path = os.path.join(self.save_root, "world.json")
        if not os.path.exists(world_path):
            # Check for any JSON files (partial save)
            for rf in self.REQUIRED_FILES:
                if os.path.exists(os.path.join(self.save_root, rf)):
                    return "PARTIAL"
            return "FRESH"

        # Try to parse world.json
        try:
            with open(world_path, "r", encoding="utf-8") as f:
                world = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return "CORRUPT"

        # Check schema version
        version = world.get("schema_version", "")
        if version and version != self.CURRENT_SCHEMA_VERSION:
            return "VERSION_MISMATCH"

        # Check all required files
        for rf in self.REQUIRED_FILES:
            path = os.path.join(self.save_root, rf)
            if not os.path.exists(path):
                return "PARTIAL"

        return "VALID"

    def load_save(self) -> LoadResult:
        """Load all save files and return a LoadResult."""
        classification = self.classify()

        if classification == "FRESH":
            return LoadResult(classification="FRESH")

        if classification == "CORRUPT":
            return LoadResult(
                classification="CORRUPT",
                errors=["world.json is corrupt or unparseable"],
            )

        # Attempt to load all files
        errors = []
        world = self._load_json("world.json", errors)
        player = self._load_json("player/character.json", errors)
        factions = self._load_json("factions.json", errors)
        npcs = self._load_json("npcs.json", errors)
        locations = self._load_json("locations.json", errors)
        clocks = self._load_json("clocks.json", errors)
        metadata = self._load_json("metadata.json", errors, required=False)

        if errors and classification == "VALID":
            classification = "PARTIAL"

        # Version check
        if world and world.get("schema_version", "") != self.CURRENT_SCHEMA_VERSION:
            classification = "VERSION_MISMATCH"

        return LoadResult(
            classification=classification,
            world=world,
            player=player,
            factions=factions,
            npcs=npcs,
            locations=locations,
            clocks=clocks,
            metadata=metadata,
            errors=errors,
        )

    def _load_json(
        self,
        relative_path: str,
        errors: list,
        required: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Load a single JSON file."""
        path = os.path.join(self.save_root, relative_path)
        if not os.path.exists(path):
            if required:
                errors.append(f"Missing: {relative_path}")
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            errors.append(f"Corrupt: {relative_path} ({e})")
            return None

    def cleanup_stale_temps(self) -> int:
        """Remove stale .tmp files from failed saves. Returns count removed."""
        if not os.path.exists(self.save_root):
            return 0
        count = 0
        for root, dirs, files in os.walk(self.save_root):
            for f in files:
                if f.endswith(".tmp"):
                    try:
                        os.unlink(os.path.join(root, f))
                        count += 1
                    except OSError:
                        pass
        return count
