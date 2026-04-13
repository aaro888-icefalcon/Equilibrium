"""Aging engine — age categories, attribute degradation, death checks.

Categories: young (16-29), mature (30-39), aging (40-49), old (50-59),
very_old (60-69), ancient (70-79), elder (80+).
Death roll: annually past 60, 1d20 + modifiers vs DC 8.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Tuple


# Valid die sizes for attributes
_VALID_DICE = [4, 6, 8, 10, 12]


def _die_down(current: int) -> int:
    """Reduce attribute by one die size."""
    idx = _VALID_DICE.index(current) if current in _VALID_DICE else 0
    return _VALID_DICE[max(0, idx - 1)]


def _die_up(current: int) -> int:
    """Increase attribute by one die size."""
    idx = _VALID_DICE.index(current) if current in _VALID_DICE else len(_VALID_DICE) - 1
    return _VALID_DICE[min(len(_VALID_DICE) - 1, idx + 1)]


class AgingEvent:
    """An aging-related event."""

    def __init__(self, description: str, mechanical: Dict[str, Any] | None = None) -> None:
        self.description = description
        self.mechanical = mechanical or {}


def get_age_category(age: int) -> str:
    """Return the age category for a given age."""
    if age < 30:
        return "young"
    if age < 40:
        return "mature"
    if age < 50:
        return "aging"
    if age < 60:
        return "old"
    if age < 70:
        return "very_old"
    if age < 80:
        return "ancient"
    return "elder"


class AgingEngine:
    """Manages age-related attribute changes and death checks."""

    def apply_yearly_aging(
        self,
        character: Dict[str, Any],
        rng: _random.Random | None = None,
    ) -> List[AgingEvent]:
        """Apply one year of aging effects. Returns list of events."""
        if rng is None:
            rng = _random.Random()

        age = character.get("age", 25)
        age += 1
        character["age"] = age
        events = []

        attrs = character.get("attributes", {})
        category = get_age_category(age)

        # 25: potential +1 attribute
        if age == 25:
            events.append(AgingEvent("Peak physical condition reached"))

        # 40s: strength -1, agility -1
        if age == 40:
            if "strength" in attrs:
                attrs["strength"] = _die_down(attrs["strength"])
            if "agility" in attrs:
                attrs["agility"] = _die_down(attrs["agility"])
            events.append(AgingEvent(
                "Aging effects begin — strength and agility decline",
                {"strength": -1, "agility": -1},
            ))

        # 45: insight may +1
        if age == 45:
            if rng.random() < 0.5 and "insight" in attrs:
                attrs["insight"] = _die_up(attrs["insight"])
                events.append(AgingEvent(
                    "Wisdom of experience — insight sharpens",
                    {"insight": 1},
                ))

        # 50s: cumulative declines
        if age == 50:
            if "strength" in attrs:
                attrs["strength"] = _die_down(attrs["strength"])
            if "agility" in attrs:
                attrs["agility"] = _die_down(attrs["agility"])
            if "perception" in attrs:
                attrs["perception"] = _die_down(attrs["perception"])
            ct = character.get("condition_tracks", {})
            ct["physical_max"] = ct.get("physical_max", 6) - 1
            character["condition_tracks"] = ct
            events.append(AgingEvent(
                "Age takes its toll — physical decline accelerates",
                {"strength": -1, "agility": -1, "perception": -1, "physical_max": -1},
            ))

        # 55: insight +1
        if age == 55:
            if "insight" in attrs:
                attrs["insight"] = _die_up(attrs["insight"])
                events.append(AgingEvent(
                    "Deep experience — insight grows",
                    {"insight": 1},
                ))

        # 60s: further decline, death roll begins
        if age == 60:
            if "strength" in attrs:
                attrs["strength"] = _die_down(attrs["strength"])
            if "agility" in attrs:
                attrs["agility"] = _die_down(attrs["agility"])
            if "perception" in attrs:
                attrs["perception"] = _die_down(attrs["perception"])
            ct = character.get("condition_tracks", {})
            ct["physical_max"] = ct.get("physical_max", 6) - 1
            character["condition_tracks"] = ct
            events.append(AgingEvent(
                "The body weakens — significant physical decline",
                {"strength": -1, "agility": -1, "perception": -1, "physical_max": -1},
            ))

        # Death roll annually past 60
        if age >= 60:
            died, roll_detail = self._death_roll(character, rng)
            if died:
                events.append(AgingEvent(
                    f"Death by old age at {age}",
                    {"death": True, "roll": roll_detail},
                ))
            else:
                events.append(AgingEvent(
                    f"Survived another year at age {age}",
                    {"death": False, "roll": roll_detail},
                ))

        return events

    def _death_roll(
        self,
        character: Dict[str, Any],
        rng: _random.Random,
    ) -> Tuple[bool, Dict[str, Any]]:
        """Annual death check. Roll 1d20 + mods vs DC 8.

        Returns (died, detail_dict).
        """
        age = character.get("age", 60)
        roll = rng.randint(1, 20)

        modifiers = 0

        # Physical track: -1 per filled segment
        ct = character.get("condition_tracks", {})
        physical = ct.get("physical", 0)
        modifiers -= physical

        # Persistent harm tier 3: -2 each
        harm_t3 = character.get("persistent_harm_tier_3", 0)
        modifiers -= harm_t3 * 2

        # Corruption above 2: -1 per segment
        corruption = character.get("corruption", 0)
        if corruption > 2:
            modifiers -= (corruption - 2)

        # Age above 60: -1 per 5 years
        modifiers -= max(0, (age - 60)) // 5

        # Species bonuses
        species = character.get("species", "human")
        if species in ("slow_breath",):
            modifiers += 2
        if species in ("stone_silent",):
            modifiers += 2
        if species in ("silver_hand", "quick_blooded"):
            modifiers -= 1

        # Medical care
        if character.get("medical_care", False):
            modifiers += 2

        # High stress
        if character.get("high_stress_past_year", False):
            modifiers -= 1

        total = roll + modifiers
        died = total < 8

        return died, {
            "roll": roll,
            "modifiers": modifiers,
            "total": total,
            "dc": 8,
            "died": died,
        }

    def check_death_proximity(self, character: Dict[str, Any]) -> Optional[str]:
        """Check for soft death warnings."""
        age = character.get("age", 25)
        if age < 58:
            return None
        if age >= 58 and age < 60:
            return "18_month_warning"
        # After 60, check margin
        return None
