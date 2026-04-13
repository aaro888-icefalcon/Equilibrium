"""Relationship progression — standing, trust, state transitions, decay.

Standing -3..+3 (player→NPC), trust 0-5 (NPC→player).
State machine: neutral→cordial→warm→loyal; cold→antagonist→blood_feud.
Absence decay: 0.4/month for positive, 0.3/month drift toward 0 for negative.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Tuple


# State thresholds (standing, trust) → state name
STATE_THRESHOLDS = [
    (3, 4, "loyal"),
    (2, 3, "warm"),
    (1, 2, "cordial"),
    (0, 0, "neutral"),
    (-1, None, "cold"),
    (-2, None, "antagonist"),
    (-3, None, "blood_feud"),
]


class RelationshipProgression:
    """Manages relationship standing, trust, and state transitions."""

    def __init__(self, character: Dict[str, Any]) -> None:
        self.character = character
        if "relationships" not in character:
            character["relationships"] = {}

    def _ensure_relationship(self, npc_id: str) -> Dict[str, Any]:
        """Ensure a relationship entry exists."""
        rels = self.character["relationships"]
        if npc_id not in rels:
            rels[npc_id] = {
                "standing": 0,
                "trust": 0,
                "state": "neutral",
                "locked_until_day": 0,
                "absence_months": 0,
                "events": [],
            }
        return rels[npc_id]

    def update_standing(
        self,
        npc_id: str,
        delta: int,
        reason: str = "",
        current_day: int = 0,
    ) -> Dict[str, Any]:
        """Update standing with an NPC. Returns the updated relationship."""
        rel = self._ensure_relationship(npc_id)

        # Check if locked
        if current_day < rel.get("locked_until_day", 0):
            return rel

        rel["standing"] = max(-3, min(3, rel["standing"] + delta))
        rel["absence_months"] = 0  # Reset absence on interaction

        if reason:
            rel["events"].append({"day": current_day, "reason": reason, "delta": delta})

        # Update state
        self._update_state(rel)
        return rel

    def update_trust(self, npc_id: str, delta: int) -> Dict[str, Any]:
        """Update NPC trust. Returns the updated relationship."""
        rel = self._ensure_relationship(npc_id)
        rel["trust"] = max(0, min(5, rel["trust"] + delta))
        self._update_state(rel)
        return rel

    def get_standing(self, npc_id: str) -> int:
        """Get current standing with an NPC."""
        rel = self.character.get("relationships", {}).get(npc_id)
        if rel is None:
            return 0
        return rel["standing"]

    def get_trust(self, npc_id: str) -> int:
        """Get current NPC trust level."""
        rel = self.character.get("relationships", {}).get(npc_id)
        if rel is None:
            return 0
        return rel["trust"]

    def get_state(self, npc_id: str) -> str:
        """Get current relationship state."""
        rel = self.character.get("relationships", {}).get(npc_id)
        if rel is None:
            return "neutral"
        return rel.get("state", "neutral")

    def apply_betrayal(self, npc_id: str, current_day: int = 0) -> None:
        """Apply betrayal: standing -3, locked for 60 days."""
        rel = self._ensure_relationship(npc_id)
        rel["standing"] = -3
        rel["locked_until_day"] = current_day + 60
        rel["state"] = "betrayed"
        rel["events"].append({"day": current_day, "reason": "betrayal", "delta": 0})

    def apply_absence_decay(
        self,
        npc_id: str,
        months: int = 1,
        rng: _random.Random | None = None,
    ) -> None:
        """Apply absence-based standing decay."""
        if rng is None:
            rng = _random.Random()

        rel = self._ensure_relationship(npc_id)
        rel["absence_months"] = rel.get("absence_months", 0) + months

        for _ in range(months):
            standing = rel["standing"]
            if standing > 0:
                # Decay: 60% stay, 40% decay by 1
                if rng.random() < 0.4:
                    rel["standing"] = max(0, standing - 1)
            elif standing < 0:
                # Drift toward 0: 70% stay, 30% drift by 1
                if rng.random() < 0.3:
                    rel["standing"] = min(0, standing + 1)

        self._update_state(rel)

    def handle_npc_death(self, npc_id: str, current_day: int = 0) -> Dict[str, Any]:
        """Handle death of an NPC. Lock relationship, apply mental damage."""
        rel = self._ensure_relationship(npc_id)
        standing = rel["standing"]

        rel["state"] = "dead"
        rel["locked_until_day"] = 999999  # Permanently locked

        # Mental damage based on standing
        mental_damage = 0
        if standing >= 3:
            mental_damage = 2
        elif standing >= 2:
            mental_damage = 1

        rel["events"].append({
            "day": current_day,
            "reason": "death",
            "mental_damage": mental_damage,
        })

        return {"mental_damage": mental_damage, "standing": standing}

    def _update_state(self, rel: Dict[str, Any]) -> None:
        """Update relationship state based on standing and trust."""
        # Don't override special states
        if rel.get("state") in ("dead", "betrayed", "blood_feud"):
            if rel["state"] == "blood_feud" and rel["standing"] > -3:
                pass  # Blood feud can soften over time
            else:
                return

        standing = rel["standing"]
        trust = rel["trust"]

        if standing >= 3 and trust >= 4:
            rel["state"] = "loyal"
        elif standing >= 2 and trust >= 3:
            rel["state"] = "warm"
        elif standing >= 1 and trust >= 2:
            rel["state"] = "cordial"
        elif standing <= -3:
            rel["state"] = "blood_feud"
        elif standing <= -2:
            rel["state"] = "antagonist"
        elif standing <= -1:
            rel["state"] = "cold"
        else:
            rel["state"] = "neutral"
