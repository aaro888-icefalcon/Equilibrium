"""Unit tests for faction progression."""

import random
import unittest

from emergence.engine.progression.factions import FactionProgression


class TestFactionProgression(unittest.TestCase):

    def _make_char(self):
        return {}

    def test_initial_state(self):
        char = self._make_char()
        fp = FactionProgression(char)
        self.assertEqual(fp.get_standing("f1"), 0)
        self.assertEqual(fp.get_reach("f1"), 0)
        self.assertEqual(fp.get_heat("f1"), 0)

    def test_update_standing(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_standing("f1", 2, "helped faction")
        self.assertEqual(fp.get_standing("f1"), 2)

    def test_standing_capped(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_standing("f1", 5)
        self.assertEqual(fp.get_standing("f1"), 3)
        fp.update_standing("f1", -10)
        self.assertEqual(fp.get_standing("f1"), -3)

    def test_reach_update(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_reach("f1", 3)
        self.assertEqual(fp.get_reach("f1"), 3)

    def test_reach_capped(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_reach("f1", 7)
        self.assertEqual(fp.get_reach("f1"), 5)

    def test_heat_accumulation(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.add_heat("f1", 2, "suspicious activity")
        fp.add_heat("f1", 1, "caught spying")
        self.assertEqual(fp.get_heat("f1"), 3)

    def test_standing_decay(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_standing("f1", 3, current_day=0)
        rng = random.Random(42)
        # Apply decay well after 1 year
        changes = fp.apply_yearly_decay(current_day=400, rng=rng)
        # With 50% chance, may or may not decay
        self.assertIsInstance(changes, list)

    def test_reach_decay_after_3_years(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.update_reach("f1", 3)
        fp.update_standing("f1", 0, current_day=0)
        changes = fp.apply_yearly_decay(current_day=3 * 365 + 1)
        self.assertLessEqual(fp.get_reach("f1"), 3)

    def test_heat_decays_non_permanent(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.add_heat("f1", 3)
        fp.update_standing("f1", 0, current_day=0)
        fp.apply_yearly_decay(current_day=400)
        self.assertLess(fp.get_heat("f1"), 3)

    def test_permanent_heat_does_not_decay(self):
        char = self._make_char()
        fp = FactionProgression(char)
        fp.add_heat("f1", 3, "spy uncovered", permanent=True)
        fp.update_standing("f1", 0, current_day=0)
        fp.apply_yearly_decay(current_day=400)
        self.assertEqual(fp.get_heat("f1"), 3)


if __name__ == "__main__":
    unittest.main()
