"""Faction progression — standing, reach, heat, decay.

Standing -3..+3, reach 0-5. Heat integration. Yearly decay:
50% chance of drift toward 0 if |standing| >= 1.
Reach decays 1 per 3 years if no event.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional


class FactionProgression:
    """Manages player standing, reach, and heat with factions."""

    def __init__(self, character: Dict[str, Any]) -> None:
        self.character = character
        if "faction_standings" not in character:
            character["faction_standings"] = {}

    def _ensure_faction(self, faction_id: str) -> Dict[str, Any]:
        """Ensure a faction entry exists."""
        factions = self.character["faction_standings"]
        if faction_id not in factions:
            factions[faction_id] = {
                "standing": 0,
                "reach": 0,
                "heat": 0,
                "last_event_day": 0,
                "events": [],
            }
        return factions[faction_id]

    def update_standing(
        self,
        faction_id: str,
        delta: int,
        reason: str = "",
        current_day: int = 0,
    ) -> Dict[str, Any]:
        """Update standing with a faction."""
        fac = self._ensure_faction(faction_id)
        fac["standing"] = max(-3, min(3, fac["standing"] + delta))
        fac["last_event_day"] = current_day
        if reason:
            fac["events"].append({"day": current_day, "reason": reason, "delta": delta})
        return fac

    def update_reach(self, faction_id: str, delta: int) -> Dict[str, Any]:
        """Update reach within a faction."""
        fac = self._ensure_faction(faction_id)
        fac["reach"] = max(0, min(5, fac["reach"] + delta))
        return fac

    def add_heat(
        self,
        faction_id: str,
        amount: int,
        source: str = "",
        permanent: bool = False,
    ) -> None:
        """Add heat with a faction."""
        fac = self._ensure_faction(faction_id)
        fac["heat"] = fac.get("heat", 0) + amount
        if permanent:
            fac["permanent_heat"] = fac.get("permanent_heat", 0) + amount

    def get_standing(self, faction_id: str) -> int:
        fac = self.character.get("faction_standings", {}).get(faction_id)
        return fac["standing"] if fac else 0

    def get_reach(self, faction_id: str) -> int:
        fac = self.character.get("faction_standings", {}).get(faction_id)
        return fac["reach"] if fac else 0

    def get_heat(self, faction_id: str) -> int:
        fac = self.character.get("faction_standings", {}).get(faction_id)
        return fac.get("heat", 0) if fac else 0

    def apply_yearly_decay(
        self,
        current_day: int,
        rng: _random.Random | None = None,
    ) -> List[str]:
        """Apply yearly standing and reach decay. Returns list of changes."""
        if rng is None:
            rng = _random.Random()
        changes = []

        for fac_id, fac in self.character.get("faction_standings", {}).items():
            days_since = current_day - fac.get("last_event_day", 0)

            # Standing decay: 50% chance toward 0 per year
            standing = fac["standing"]
            if abs(standing) >= 1 and days_since >= 365:
                if rng.random() < 0.5:
                    if standing > 0:
                        fac["standing"] -= 1
                        changes.append(f"{fac_id}: standing {standing} -> {fac['standing']}")
                    elif standing < 0:
                        fac["standing"] += 1
                        changes.append(f"{fac_id}: standing {standing} -> {fac['standing']}")

            # Reach decay: -1 per 3 years if no event
            reach = fac["reach"]
            if reach > 0 and days_since >= 3 * 365:
                fac["reach"] = max(0, reach - 1)
                changes.append(f"{fac_id}: reach {reach} -> {fac['reach']}")

            # Heat decay: -1/year unless permanent
            heat = fac.get("heat", 0)
            permanent = fac.get("permanent_heat", 0)
            if heat > permanent and days_since >= 365:
                fac["heat"] = max(permanent, heat - 1)
                changes.append(f"{fac_id}: heat {heat} -> {fac['heat']}")

        return changes
