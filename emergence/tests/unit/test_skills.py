"""Unit tests for skill progression."""

import random
import unittest

from emergence.engine.progression.skills import (
    SkillProgression,
    SKILL_THRESHOLDS,
    ALL_SKILLS,
    SYNERGIES,
    PREREQUISITES,
)


class TestSkillProgression(unittest.TestCase):

    def _make_char(self):
        return {"attributes": {"might": 8, "will": 8, "insight": 8, "agility": 8}}

    def test_initial_state(self):
        char = self._make_char()
        sp = SkillProgression(char)
        self.assertEqual(sp.get_proficiency("melee"), 0)
        self.assertEqual(sp.get_use_count("melee"), 0)

    def test_log_increments_count(self):
        char = self._make_char()
        sp = SkillProgression(char)
        sp.log_skill_use("melee")
        sp.log_skill_use("melee")
        self.assertEqual(sp.get_use_count("melee"), 2)

    def test_proficiency_1_at_5_uses(self):
        char = self._make_char()
        sp = SkillProgression(char)
        for _ in range(4):
            sp.log_skill_use("melee")
        self.assertEqual(sp.get_proficiency("melee"), 0)
        result = sp.log_skill_use("melee")
        self.assertEqual(result, 1)
        self.assertEqual(sp.get_proficiency("melee"), 1)

    def test_proficiency_2_at_20_uses(self):
        char = self._make_char()
        sp = SkillProgression(char)
        for _ in range(20):
            sp.log_skill_use("melee")
        self.assertEqual(sp.get_proficiency("melee"), 2)

    def test_proficiency_3_at_60_uses(self):
        char = self._make_char()
        sp = SkillProgression(char)
        for _ in range(60):
            sp.log_skill_use("melee")
        self.assertEqual(sp.get_proficiency("melee"), 3)

    def test_32_skills_defined(self):
        self.assertEqual(len(ALL_SKILLS), 32)

    def test_no_duplicate_skills(self):
        self.assertEqual(len(ALL_SKILLS), len(set(ALL_SKILLS)))

    def test_surgery_requires_first_aid(self):
        char = self._make_char()
        sp = SkillProgression(char)
        # Try to level surgery to 3 without first_aid
        char["skill_use_counts"]["surgery"] = 60
        result = sp.check_proficiency_increase("surgery")
        # Should reach 2 but not 3 (blocked by prerequisite)
        # First, it would increment to 1, then 2
        char["skill_proficiencies"]["surgery"] = 2
        char["skill_use_counts"]["surgery"] = 60
        result = sp.check_proficiency_increase("surgery")
        self.assertIsNone(result)  # Blocked at 3

    def test_surgery_with_first_aid_prereq_met(self):
        char = self._make_char()
        sp = SkillProgression(char)
        char["skill_proficiencies"]["first_aid"] = 4
        char["skill_proficiencies"]["surgery"] = 2
        char["skill_use_counts"]["surgery"] = 60
        result = sp.check_proficiency_increase("surgery")
        self.assertEqual(result, 3)

    def test_synergy_bonus(self):
        char = self._make_char()
        sp = SkillProgression(char)
        char["skill_proficiencies"]["first_aid"] = 4
        bonus = sp.get_synergy_bonus("surgery")
        self.assertEqual(bonus, 1)

    def test_no_synergy_without_prereq(self):
        char = self._make_char()
        sp = SkillProgression(char)
        char["skill_proficiencies"]["first_aid"] = 3
        bonus = sp.get_synergy_bonus("surgery")
        self.assertEqual(bonus, 0)

    def test_skill_check_success(self):
        char = self._make_char()
        sp = SkillProgression(char)
        char["skill_proficiencies"]["melee"] = 5
        rng = random.Random(42)
        success, total = sp.resolve_skill_check("melee", 8, dc=5, rng=rng)
        # With proficiency 5 and d8, total should be reasonable
        self.assertIsInstance(success, bool)

    def test_untrained_penalty(self):
        char = self._make_char()
        sp = SkillProgression(char)
        rng = random.Random(42)
        _, total = sp.resolve_skill_check("surgery", 8, dc=5, rng=rng)
        # With proficiency 0, should have -2 penalty
        # Total = roll(1-8) + 0 + 0 - 2
        self.assertLessEqual(total, 8 - 2 + 0)

    def test_multiple_literacy_synergies(self):
        char = self._make_char()
        sp = SkillProgression(char)
        char["skill_proficiencies"]["literacy"] = 4
        self.assertEqual(sp.get_synergy_bonus("history"), 1)
        self.assertEqual(sp.get_synergy_bonus("bureaucracy"), 1)
        self.assertEqual(sp.get_synergy_bonus("languages"), 1)


if __name__ == "__main__":
    unittest.main()
