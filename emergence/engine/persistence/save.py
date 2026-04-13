"""Save manager — atomic writes per state-persistence spec.

Full save: leaves-first, world.json last. Lightweight save for combat rounds.
Save throttling (5s minimum between full saves).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional


class SaveManager:
    """Manages save operations with atomic writes and throttling."""

    MIN_SAVE_INTERVAL = 5.0  # seconds

    def __init__(self, save_root: str) -> None:
        self.save_root = save_root
        self._last_save_time = 0.0

    def full_save(
        self,
        world: Dict[str, Any],
        player: Dict[str, Any],
        factions: Dict[str, Any],
        npcs: Dict[str, Any],
        locations: Dict[str, Any],
        clocks: Dict[str, Any],
        metadata: Dict[str, Any] | None = None,
    ) -> bool:
        """Full save — all game state. Returns True if saved, False if throttled."""
        now = time.time()
        if now - self._last_save_time < self.MIN_SAVE_INTERVAL:
            return False

        os.makedirs(self.save_root, exist_ok=True)

        # Leaves first: entities before world
        self._atomic_write("player/character.json", player)
        self._atomic_write("factions.json", factions)
        self._atomic_write("npcs.json", npcs)
        self._atomic_write("locations.json", locations)
        self._atomic_write("clocks.json", clocks)

        if metadata:
            self._atomic_write("metadata.json", metadata)

        # World last (acts as save-complete marker)
        self._atomic_write("world.json", world)

        self._last_save_time = time.time()
        return True

    def lightweight_save(
        self,
        combat_state: Dict[str, Any],
    ) -> None:
        """Lightweight save for combat rounds — just combat state."""
        os.makedirs(self.save_root, exist_ok=True)
        self._atomic_write("combat_state.json", combat_state)

    def _atomic_write(self, relative_path: str, data: Any) -> None:
        """Write data atomically using temp-and-rename."""
        full_path = os.path.join(self.save_root, relative_path)
        dir_path = os.path.dirname(full_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        tmp_path = full_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, full_path)
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            raise

    def save_exists(self) -> bool:
        """Check if a valid save exists (world.json present)."""
        return os.path.exists(os.path.join(self.save_root, "world.json"))

    def list_save_files(self) -> list:
        """List all JSON files in the save directory."""
        if not os.path.exists(self.save_root):
            return []
        result = []
        for root, dirs, files in os.walk(self.save_root):
            for f in files:
                if f.endswith(".json"):
                    rel = os.path.relpath(os.path.join(root, f), self.save_root)
                    result.append(rel)
        return sorted(result)
