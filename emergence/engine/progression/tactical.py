"""Tactical progression — power use tracking and strengthening marks.

Thresholds per spec: 25/75/200/500/1200 (mark 5 doubled at tier ceiling).
Category bonuses at 100/400/1000/2500 sum across powers in same category.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# Power strengthening mark thresholds and effects
POWER_MARK_THRESHOLDS = [
    (25, 1, "-1 condition cost on cheaper track power taxes"),
    (75, 2, "One new option in power's effect parameters"),
    (200, 3, "-1 corruption cost on uses inflicting corruption (floor 0)"),
    (500, 4, "Range/duration/area extended one step"),
    (1200, 5, "Effective tier +1 for opposed checks"),
]

# Category bonus thresholds
CATEGORY_BONUS_THRESHOLDS = [
    (100, 1, "New tier-1 power available; 7-day learning ritual"),
    (400, 2, "Tier-2 power if tier >= 2; else second tier-1"),
    (1000, 3, "Integrate two existing powers into combined verb"),
    (2500, 4, "tier_ceiling +1 (one-time per category; max +3)"),
]


class TacticalProgression:
    """Tracks power use and computes strengthening marks."""

    def __init__(self, character: Dict[str, Any]) -> None:
        self.character = character
        # Ensure tracking structures exist
        if "power_use_counts" not in character:
            character["power_use_counts"] = {}
        if "power_marks" not in character:
            character["power_marks"] = {}
        if "category_use_counts" not in character:
            character["category_use_counts"] = {}
        if "category_bonuses" not in character:
            character["category_bonuses"] = {}

    def log_power_use(self, power_id: str, category: str) -> Optional[str]:
        """Log a power use. Returns description of new mark if threshold crossed."""
        counts = self.character["power_use_counts"]
        counts[power_id] = counts.get(power_id, 0) + 1
        use_count = counts[power_id]

        # Track category total
        cat_counts = self.character["category_use_counts"]
        cat_counts[category] = cat_counts.get(category, 0) + 1

        # Check power strengthening
        mark_result = self.check_strengthening(power_id)

        # Check category bonus
        cat_result = self.check_category_bonus(category)

        if mark_result:
            return mark_result[1]
        if cat_result:
            return cat_result[1]
        return None

    def check_strengthening(self, power_id: str) -> Optional[Tuple[int, str]]:
        """Check if a power has crossed a strengthening threshold.

        Returns (mark_level, description) if a new mark was earned, else None.
        """
        use_count = self.character["power_use_counts"].get(power_id, 0)
        current_mark = self.character["power_marks"].get(power_id, 0)

        char_tier = self.character.get("tier", 1)
        tier_ceiling = self.character.get("tier_ceiling", 10)

        for threshold, mark_level, description in POWER_MARK_THRESHOLDS:
            if mark_level <= current_mark:
                continue

            # At tier ceiling, mark 5 threshold doubles
            effective_threshold = threshold
            if mark_level == 5 and char_tier >= tier_ceiling:
                effective_threshold = threshold * 2

            if use_count >= effective_threshold:
                self.apply_strengthening_mark(power_id, mark_level)
                return (mark_level, description)

        return None

    def apply_strengthening_mark(self, power_id: str, mark: int) -> None:
        """Apply a strengthening mark to a power."""
        self.character["power_marks"][power_id] = mark

    def check_category_bonus(self, category: str) -> Optional[Tuple[int, str]]:
        """Check if category-wide use has crossed a bonus threshold.

        Returns (bonus_level, description) if a new bonus was earned, else None.
        """
        total = self.character["category_use_counts"].get(category, 0)
        current_bonus = self.character["category_bonuses"].get(category, 0)

        for threshold, bonus_level, description in CATEGORY_BONUS_THRESHOLDS:
            if bonus_level <= current_bonus:
                continue
            if total >= threshold:
                self.character["category_bonuses"][category] = bonus_level
                return (bonus_level, description)

        return None

    def get_power_mark(self, power_id: str) -> int:
        """Get the current strengthening mark for a power."""
        return self.character["power_marks"].get(power_id, 0)

    def get_category_bonus(self, category: str) -> int:
        """Get the current category bonus level."""
        return self.character["category_bonuses"].get(category, 0)

    def get_power_use_count(self, power_id: str) -> int:
        """Get the total use count for a power."""
        return self.character["power_use_counts"].get(power_id, 0)

    def get_category_use_count(self, category: str) -> int:
        """Get the total use count across all powers in a category."""
        return self.character["category_use_counts"].get(category, 0)

    def get_effective_tier_bonus(self, power_id: str) -> int:
        """Get the effective tier bonus from mark 5."""
        if self.get_power_mark(power_id) >= 5:
            return 1
        return 0
