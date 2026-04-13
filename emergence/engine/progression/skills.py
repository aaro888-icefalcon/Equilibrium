"""Skill progression — 32 skills with use-based proficiency advancement.

Thresholds: 5/20/60/150/350/750/1500/3000/7000/15000.
Prerequisites, synergies, and skill checks.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Tuple


# Proficiency thresholds
SKILL_THRESHOLDS = [5, 20, 60, 150, 350, 750, 1500, 3000, 7000, 15000]

# 32 skills organized in 7 clusters
SKILL_CLUSTERS = {
    "combat": ["firearms", "melee", "brawling", "thrown", "tactics"],
    "physical_survival": [
        "stealth", "urban_movement", "wilderness", "weather_read",
        "animal_handling", "swimming",
    ],
    "craft_technical": ["craft", "basic_repair", "scavenging", "agriculture", "cooking"],
    "medical": ["first_aid", "surgery", "pharmacology", "field_medicine"],
    "social": ["negotiation", "intimidation", "command", "instruction", "streetwise"],
    "knowledge": ["literacy", "languages", "history", "regional_geography", "bureaucracy"],
    "other": ["perception_check", "faction_etiquette"],
}

ALL_SKILLS = []
for cluster in SKILL_CLUSTERS.values():
    ALL_SKILLS.extend(cluster)

# Synergies: prereq_skill at level 4 → bonus_skill gains +1 to checks
SYNERGIES = {
    "first_aid": [("surgery", 4)],
    "agriculture": [("cooking", 4)],
    "streetwise": [("negotiation", 4)],
    "tactics": [("command", 4)],
    "literacy": [("history", 4), ("bureaucracy", 4), ("languages", 4)],
    "wilderness": [("weather_read", 4), ("animal_handling", 4)],
    "urban_movement": [("stealth", 4)],
    "melee": [("brawling", 4)],
    "firearms": [("thrown", 4)],
}

# Prerequisites: skill requires prereq at min_level
PREREQUISITES = {
    "surgery": [("first_aid", 4, 3)],   # surgery >= 3 requires first_aid >= 4
    "field_medicine": [("first_aid", 4, 4), ("pharmacology", 3, 4)],
    "command": [("tactics", 3, 3)],       # command >= 3 requires tactics >= 3
    "bureaucracy": [("literacy", 5, 5)],  # bureaucracy >= 5 requires literacy >= 5
    "pharmacology": [("literacy", 4, 5)], # pharmacology >= 5 requires literacy >= 4
}


class SkillProgression:
    """Tracks skill use and proficiency advancement."""

    def __init__(self, character: Dict[str, Any]) -> None:
        self.character = character
        if "skill_use_counts" not in character:
            character["skill_use_counts"] = {}
        if "skill_proficiencies" not in character:
            character["skill_proficiencies"] = {}

    def log_skill_use(self, skill_id: str) -> Optional[int]:
        """Log a skill use. Returns new proficiency level if threshold crossed."""
        counts = self.character["skill_use_counts"]
        counts[skill_id] = counts.get(skill_id, 0) + 1

        return self.check_proficiency_increase(skill_id)

    def check_proficiency_increase(self, skill_id: str) -> Optional[int]:
        """Check if skill has crossed proficiency threshold.

        Returns new level if increased, None otherwise.
        """
        use_count = self.character["skill_use_counts"].get(skill_id, 0)
        current_level = self.character["skill_proficiencies"].get(skill_id, 0)

        if current_level >= 10:
            return None

        target_level = current_level + 1
        if target_level > len(SKILL_THRESHOLDS):
            return None

        threshold = SKILL_THRESHOLDS[target_level - 1]
        if use_count >= threshold:
            # Check prerequisites
            if not self._meets_prerequisites(skill_id, target_level):
                return None
            self.character["skill_proficiencies"][skill_id] = target_level
            return target_level

        return None

    def get_proficiency(self, skill_id: str) -> int:
        """Get current proficiency level for a skill."""
        return self.character["skill_proficiencies"].get(skill_id, 0)

    def get_use_count(self, skill_id: str) -> int:
        """Get total use count for a skill."""
        return self.character["skill_use_counts"].get(skill_id, 0)

    def get_synergy_bonus(self, skill_id: str) -> int:
        """Get synergy bonus for a skill based on prerequisites."""
        bonus = 0
        for prereq_skill, synergy_targets in SYNERGIES.items():
            prereq_level = self.get_proficiency(prereq_skill)
            for target_skill, required_level in synergy_targets:
                if target_skill == skill_id and prereq_level >= required_level:
                    bonus += 1
        return bonus

    def resolve_skill_check(
        self,
        skill_id: str,
        attribute_value: int,
        dc: int,
        rng: _random.Random | None = None,
    ) -> Tuple[bool, int]:
        """Resolve a skill check.

        Returns (success, roll_result).
        """
        if rng is None:
            rng = _random.Random()

        proficiency = self.get_proficiency(skill_id)
        synergy = self.get_synergy_bonus(skill_id)

        # Roll 1d(attribute) + proficiency + synergy
        roll = rng.randint(1, max(attribute_value, 1))
        total = roll + proficiency + synergy

        # Untrained penalty
        if proficiency == 0:
            total -= 2

        return (total >= dc, total)

    def _meets_prerequisites(self, skill_id: str, target_level: int) -> bool:
        """Check if prerequisites are met for reaching target_level."""
        prereqs = PREREQUISITES.get(skill_id, [])
        for prereq_skill, prereq_level, skill_floor in prereqs:
            if target_level >= skill_floor:
                actual = self.get_proficiency(prereq_skill)
                if actual < prereq_level:
                    return False
        return True
