"""Sim persistence — dirty-flag tracking for incremental saves.

Tracks which entities have been modified since the last save,
enabling efficient partial saves rather than full world serialization.
"""

from __future__ import annotations

from typing import Any, Dict, Set


class DirtyTracker:
    """Tracks modification state of world entities for incremental saves."""

    def __init__(self) -> None:
        self._dirty: Dict[str, Set[str]] = {
            "factions": set(),
            "npcs": set(),
            "locations": set(),
            "clocks": set(),
            "world": set(),
            "player": set(),
        }
        self._full_save_needed = False

    def mark_dirty(self, entity_type: str, entity_id: str) -> None:
        """Mark an entity as modified since last save."""
        if entity_type in self._dirty:
            self._dirty[entity_type].add(entity_id)

    def mark_full_save(self) -> None:
        """Flag that a full save is needed (e.g., after structural changes)."""
        self._full_save_needed = True

    def is_dirty(self, entity_type: str, entity_id: str) -> bool:
        """Check if a specific entity needs saving."""
        return entity_id in self._dirty.get(entity_type, set())

    def get_dirty(self, entity_type: str) -> Set[str]:
        """Get all dirty entity IDs for a type."""
        return set(self._dirty.get(entity_type, set()))

    def needs_full_save(self) -> bool:
        """Check if a full save is required."""
        return self._full_save_needed

    def has_changes(self) -> bool:
        """Check if anything has been modified."""
        if self._full_save_needed:
            return True
        return any(ids for ids in self._dirty.values())

    def clear(self) -> None:
        """Clear all dirty flags (called after successful save)."""
        for key in self._dirty:
            self._dirty[key] = set()
        self._full_save_needed = False

    def summary(self) -> Dict[str, int]:
        """Return counts of dirty entities per type."""
        return {k: len(v) for k, v in self._dirty.items() if v}
