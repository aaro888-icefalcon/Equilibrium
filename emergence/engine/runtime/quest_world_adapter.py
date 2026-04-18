"""Adapter implementing WorldView over the step_cli state dicts.

The step_cli runtime loads world state as a dict-of-dicts (per
_load_full_state). The quest module expects a WorldView with typed lookup
methods. This adapter bridges them without requiring quest code to know
about the runtime's persistence format.

Mutations applied via apply_deltas persist through to state["player"],
state["npcs"], state["factions"], and state["clocks"] because the adapter
holds the same dicts by reference.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class StepWorldAdapter:
    """Dict-backed WorldView."""

    def __init__(self, state: Dict[str, Any]) -> None:
        self._state = state
        self._player = state.get("player") or {}
        self._npcs = state.get("npcs") or {}
        self._factions = state.get("factions") or {}
        self._clocks = state.get("clocks") or {}
        self._quest_seeds: List[Dict[str, Any]] = []
        # ensure relational containers exist on the player dict
        self._player.setdefault("relationships", {})
        self._player.setdefault("statuses", [])
        self._player.setdefault("threats", [])
        self._player.setdefault("inventory", [])
        self._player.setdefault("heat", {})
        self._player.setdefault("condition_tracks", {"physical": 0, "mental": 0, "social": 0})
        self._player.setdefault("history", [])

    def player(self) -> Dict[str, Any]:
        return self._player

    def get_faction(self, faction_id: str) -> Optional[Dict[str, Any]]:
        return self._factions.get(faction_id)

    def get_npc(self, npc_id: str) -> Optional[Dict[str, Any]]:
        return self._npcs.get(npc_id)

    def get_clock(self, clock_id: str) -> Optional[Dict[str, Any]]:
        return self._clocks.get(clock_id)

    def add_quest_seed(self, archetype: str, seed: Dict[str, Any]) -> None:
        self._quest_seeds.append({"archetype": archetype, "seed": seed})

    def add_history_event(self, event: Dict[str, Any]) -> None:
        self._player.setdefault("history", []).append(event)

    @property
    def pending_quest_seeds(self) -> List[Dict[str, Any]]:
        return list(self._quest_seeds)
