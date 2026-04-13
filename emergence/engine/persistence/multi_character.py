"""Multi-character save management — archive, list, switch characters.

Supports multiple characters in a single world save. Each character
gets its own subdirectory under player/.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from typing import Any, Dict, List, Optional


class MultiCharacterManager:
    """Manages multiple characters within a single save."""

    def __init__(self, save_root: str) -> None:
        self.save_root = save_root
        self._player_dir = os.path.join(save_root, "player")
        self._archive_dir = os.path.join(save_root, "player", "archive")

    def archive_character(self, reason: str = "death") -> Optional[str]:
        """Archive the current active character.

        Moves player/character.json to player/archive/{name}_{timestamp}/.
        Returns the archive ID or None if no active character.
        """
        active_path = os.path.join(self._player_dir, "character.json")
        if not os.path.exists(active_path):
            return None

        try:
            with open(active_path, "r", encoding="utf-8") as f:
                character = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        name = character.get("name", "unknown")
        safe_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        timestamp = int(time.time())
        archive_id = f"{safe_name}_{timestamp}"

        archive_path = os.path.join(self._archive_dir, archive_id)
        os.makedirs(archive_path, exist_ok=True)

        # Copy character file to archive
        dest = os.path.join(archive_path, "character.json")
        shutil.copy2(active_path, dest)

        # Write archive metadata
        meta = {
            "archive_id": archive_id,
            "name": name,
            "reason": reason,
            "archived_at": timestamp,
        }
        meta_path = os.path.join(archive_path, "archive_meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        # Remove active character
        os.unlink(active_path)

        return archive_id

    def list_characters(self) -> List[Dict[str, Any]]:
        """List all archived characters.

        Returns list of dicts with: archive_id, name, reason, archived_at.
        """
        if not os.path.exists(self._archive_dir):
            return []

        result = []
        for entry in sorted(os.listdir(self._archive_dir)):
            meta_path = os.path.join(self._archive_dir, entry, "archive_meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    result.append(meta)
                except (json.JSONDecodeError, OSError):
                    result.append({"archive_id": entry, "name": entry, "reason": "unknown"})

        return result

    def switch_character(self, archive_id: str) -> bool:
        """Restore an archived character as the active character.

        The currently active character (if any) is archived first.
        Returns True if switch was successful.
        """
        archive_path = os.path.join(self._archive_dir, archive_id, "character.json")
        if not os.path.exists(archive_path):
            return False

        # Archive current character first
        active_path = os.path.join(self._player_dir, "character.json")
        if os.path.exists(active_path):
            self.archive_character(reason="switched")

        # Restore from archive
        shutil.copy2(archive_path, active_path)

        # Remove from archive
        archive_dir = os.path.join(self._archive_dir, archive_id)
        shutil.rmtree(archive_dir)

        return True

    def has_active_character(self) -> bool:
        """Check if there is an active character."""
        return os.path.exists(os.path.join(self._player_dir, "character.json"))

    def get_active_character(self) -> Optional[Dict[str, Any]]:
        """Load the active character data."""
        active_path = os.path.join(self._player_dir, "character.json")
        if not os.path.exists(active_path):
            return None
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
