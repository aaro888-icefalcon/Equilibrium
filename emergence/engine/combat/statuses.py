"""Combat status effects engine for Emergence.

Manages the 7 closed-list statuses: bleeding, stunned, shaken, burning,
exposed, marked, corrupted.  No other statuses exist.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random


class StatusName(str, Enum):
    BLEEDING = "bleeding"
    STUNNED = "stunned"
    SHAKEN = "shaken"
    BURNING = "burning"
    EXPOSED = "exposed"
    MARKED = "marked"
    CORRUPTED = "corrupted"


@dataclass
class ActiveStatus:
    """A single active status on a combatant."""
    name: str
    duration: int          # rounds remaining; -1 = until explicit removal
    source: str            # who/what applied it
    applied_round: int = 0


class StatusEngine:
    """Manages combat status effects for all combatants in an encounter."""

    def __init__(self) -> None:
        # combatant_id -> list of ActiveStatus
        self._statuses: Dict[str, List[ActiveStatus]] = {}

    # ── core operations ──────────────────────────────────────────────

    def apply_status(self, combatant_id: str, status: ActiveStatus) -> List[str]:
        """Apply a status to a combatant.  Returns narrative event strings."""
        if combatant_id not in self._statuses:
            self._statuses[combatant_id] = []

        events: List[str] = []
        existing = self._find(combatant_id, status.name)

        if existing is not None:
            # Statuses don't stack — duration resets
            existing.duration = status.duration
            existing.source = status.source
            existing.applied_round = status.applied_round
            events.append(f"{status.name} duration reset on {combatant_id}")
        else:
            self._statuses[combatant_id].append(status)
            events.append(f"{status.name} applied to {combatant_id}")

        return events

    def remove_status(self, combatant_id: str, status_name: str) -> bool:
        """Remove a specific status.  Returns True if it was present."""
        lst = self._statuses.get(combatant_id, [])
        for i, s in enumerate(lst):
            if s.name == status_name:
                lst.pop(i)
                return True
        return False

    def get_statuses(self, combatant_id: str) -> List[ActiveStatus]:
        return list(self._statuses.get(combatant_id, []))

    def has_status(self, combatant_id: str, status_name: str) -> bool:
        return self._find(combatant_id, status_name) is not None

    # ── round ticks ──────────────────────────────────────────────────

    def tick_start_of_round(
        self, combatant_id: str, rng: random.Random
    ) -> List[dict]:
        """Process start-of-round ticks.  Returns list of effect dicts.

        Corrupted rolls a d6 for random scene-level cost.
        Burning/Bleeding now handled by tick_after_turn (per spec: end of turn).
        """
        effects: List[dict] = []

        if self.has_status(combatant_id, StatusName.CORRUPTED):
            roll = rng.randint(1, 6)
            if roll == 1:
                effects.append({"type": "narrative", "detail": "hallucination", "source": "corrupted"})
            elif roll == 2:
                effects.append({"type": "apply_status", "status": "shaken", "source": "corrupted"})
            elif roll == 5:
                effects.append({"type": "corruption_gain", "amount": 1, "source": "corrupted"})
            elif roll == 6:
                effects.append({
                    "type": "damage",
                    "track": "mental",
                    "amount": 1,
                    "damage_type": "eldritch_corruptive",
                    "source": "corrupted_sovereign_perception",
                })

        return effects

    def tick_after_turn(self, combatant_id: str) -> List[dict]:
        """Process end-of-turn ticks for a single combatant.

        Burning and Bleeding deal 1 damage each at end of the
        afflicted combatant's turn (spec §6.1).
        """
        effects: List[dict] = []

        if self.has_status(combatant_id, StatusName.BURNING):
            effects.append({
                "type": "damage",
                "track": "physical",
                "amount": 1,
                "damage_type": "matter_energy",
                "source": "burning",
            })

        if self.has_status(combatant_id, StatusName.BLEEDING):
            effects.append({
                "type": "damage",
                "track": "physical",
                "amount": 1,
                "damage_type": "physical_kinetic",
                "source": "bleeding",
            })

        return effects

    def tick_end_of_round(self, combatant_id: str) -> List[str]:
        """Decrement durations, remove expired statuses.  Returns events."""
        events: List[str] = []
        remaining: List[ActiveStatus] = []

        for s in self._statuses.get(combatant_id, []):
            if s.duration == -1:
                remaining.append(s)
                continue
            s.duration -= 1
            if s.duration <= 0:
                events.append(f"{s.name} expired on {combatant_id}")
            else:
                remaining.append(s)

        self._statuses[combatant_id] = remaining
        return events

    # ── modifier queries ─────────────────────────────────────────────

    def get_check_modifiers(self, combatant_id: str, verb: str) -> int:
        """Total modifier applied to the actor's own check due to statuses."""
        mod = 0
        if self.has_status(combatant_id, StatusName.SHAKEN):
            mod -= 1
        if self.has_status(combatant_id, StatusName.STUNNED):
            mod -= 2
        if self.has_status(combatant_id, StatusName.BURNING) and verb != "Disengage":
            mod -= 1
        return mod

    def get_attack_bonus_vs(self, target_id: str) -> int:
        """Bonus when attacking *target_id* based on their statuses."""
        bonus = 0
        if self.has_status(target_id, StatusName.MARKED):
            bonus += 2
        if self.has_status(target_id, StatusName.EXPOSED):
            bonus += 2
        return bonus

    def can_act(self, combatant_id: str) -> Tuple[bool, bool]:
        """Returns (can_major, can_minor)."""
        can_major = not self.has_status(combatant_id, StatusName.STUNNED)
        can_minor = True
        return can_major, can_minor

    def can_use_reaction(self, combatant_id: str) -> bool:
        return not self.has_status(combatant_id, StatusName.STUNNED)

    def can_spend_momentum(self, combatant_id: str) -> bool:
        if self.has_status(combatant_id, StatusName.SHAKEN):
            return False
        if self.has_status(combatant_id, StatusName.EXPOSED):
            return False
        return True

    # ── cleanup ──────────────────────────────────────────────────────

    def clear_all(self, combatant_id: str) -> None:
        """Remove all statuses (end-of-encounter)."""
        self._statuses[combatant_id] = []

    def clear_combatant(self, combatant_id: str) -> None:
        """Remove combatant from tracking entirely."""
        self._statuses.pop(combatant_id, None)

    def clear_scene_statuses(self, combatant_id: str) -> None:
        """Remove statuses that clear at end-of-scene (Shaken, Marked, Bleeding default)."""
        scene_clear = {StatusName.SHAKEN, StatusName.MARKED, StatusName.BLEEDING}
        self._statuses[combatant_id] = [
            s for s in self._statuses.get(combatant_id, [])
            if s.name not in scene_clear
        ]

    # ── internals ────────────────────────────────────────────────────

    def _find(self, combatant_id: str, name: str) -> Optional[ActiveStatus]:
        for s in self._statuses.get(combatant_id, []):
            if s.name == name:
                return s
        return None
