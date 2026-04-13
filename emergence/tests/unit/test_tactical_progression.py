"""Unit tests for tactical progression — power marks and category bonuses."""

import unittest

from emergence.engine.progression.tactical import (
    TacticalProgression,
    POWER_MARK_THRESHOLDS,
    CATEGORY_BONUS_THRESHOLDS,
)


class TestTacticalProgression(unittest.TestCase):

    def _make_char(self, tier=3, tier_ceiling=10):
        return {"tier": tier, "tier_ceiling": tier_ceiling}

    def test_initial_state(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        self.assertEqual(tp.get_power_use_count("p1"), 0)
        self.assertEqual(tp.get_power_mark("p1"), 0)
        self.assertEqual(tp.get_category_bonus("physical"), 0)

    def test_log_increments_count(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        tp.log_power_use("p1", "physical")
        tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_use_count("p1"), 2)
        self.assertEqual(tp.get_category_use_count("physical"), 2)

    def test_mark_1_at_25_uses(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for i in range(24):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 0)

        result = tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 1)
        self.assertIn("condition cost", result)

    def test_mark_2_at_75_uses(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(75):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 2)

    def test_mark_3_at_200_uses(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(200):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 3)

    def test_mark_4_at_500_uses(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(500):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 4)

    def test_mark_5_at_1200_uses(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(1200):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 5)

    def test_tier_ceiling_doubles_mark_5(self):
        """At tier ceiling, mark 5 requires 2400 instead of 1200."""
        char = self._make_char(tier=5, tier_ceiling=5)
        tp = TacticalProgression(char)
        for _ in range(1200):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 4)  # Not 5 yet

        for _ in range(1200):  # Total 2400
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 5)

    def test_not_at_ceiling_normal_threshold(self):
        """Below tier ceiling, mark 5 at normal 1200."""
        char = self._make_char(tier=3, tier_ceiling=10)
        tp = TacticalProgression(char)
        for _ in range(1200):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 5)

    def test_effective_tier_bonus(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        self.assertEqual(tp.get_effective_tier_bonus("p1"), 0)
        for _ in range(1200):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_effective_tier_bonus("p1"), 1)

    def test_category_bonus_1_at_100(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(100):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_category_bonus("physical"), 1)

    def test_category_bonus_2_at_400(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(400):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_category_bonus("physical"), 2)

    def test_category_counts_across_powers(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(50):
            tp.log_power_use("p1", "physical")
        for _ in range(50):
            tp.log_power_use("p2", "physical")
        self.assertEqual(tp.get_category_use_count("physical"), 100)
        self.assertEqual(tp.get_category_bonus("physical"), 1)

    def test_multiple_powers_independent_marks(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(25):
            tp.log_power_use("p1", "physical")
        for _ in range(10):
            tp.log_power_use("p2", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 1)
        self.assertEqual(tp.get_power_mark("p2"), 0)

    def test_no_mark_below_threshold(self):
        char = self._make_char()
        tp = TacticalProgression(char)
        for _ in range(24):
            tp.log_power_use("p1", "physical")
        self.assertEqual(tp.get_power_mark("p1"), 0)


if __name__ == "__main__":
    unittest.main()
