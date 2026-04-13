"""Unit tests for corruption engine."""

import random
import unittest

from emergence.engine.progression.corruption import (
    CorruptionEngine,
    CORRUPTION_EFFECTS,
)


class TestCorruptionEngine(unittest.TestCase):

    def _make_char(self, corruption=0):
        return {
            "corruption": corruption,
            "attributes": {"will": 8},
            "species": "human",
        }

    def test_initial_baseline(self):
        char = self._make_char()
        engine = CorruptionEngine()
        self.assertEqual(engine.get_corruption_level(char), 0)
        self.assertEqual(engine.get_corruption_label(char), "baseline")

    def test_apply_corruption(self):
        char = self._make_char()
        engine = CorruptionEngine()
        effects = engine.apply_corruption(char, 1, "eldritch power use")
        self.assertEqual(char["corruption"], 1)
        self.assertGreater(len(effects), 0)

    def test_corruption_capped_at_6(self):
        char = self._make_char()
        engine = CorruptionEngine()
        engine.apply_corruption(char, 10, "overwhelming")
        self.assertEqual(char["corruption"], 6)

    def test_segment_labels(self):
        engine = CorruptionEngine()
        self.assertEqual(engine.get_corruption_label(self._make_char(0)), "baseline")
        self.assertEqual(engine.get_corruption_label(self._make_char(1)), "touched_cosmetic")
        self.assertEqual(engine.get_corruption_label(self._make_char(2)), "touched_perceptible")
        self.assertEqual(engine.get_corruption_label(self._make_char(3)), "changed_visible")
        self.assertEqual(engine.get_corruption_label(self._make_char(4)), "changed_significant")
        self.assertEqual(engine.get_corruption_label(self._make_char(5)), "transforming")
        self.assertEqual(engine.get_corruption_label(self._make_char(6)), "transformed")

    def test_transformation_at_6(self):
        char = self._make_char(5)
        engine = CorruptionEngine()
        effects = engine.apply_corruption(char, 1, "final push")
        self.assertEqual(char["corruption"], 6)
        self.assertEqual(char.get("status"), "transformed")
        self.assertTrue(char.get("sheet_locked"))

    def test_segment_5_effects(self):
        char = self._make_char(4)
        engine = CorruptionEngine()
        effects = engine.apply_corruption(char, 1, "eldritch")
        self.assertTrue(char.get("aging_halted"))
        self.assertEqual(char.get("faction_standing_cap"), 1)

    def test_monthly_will_check_at_5(self):
        char = self._make_char(5)
        char["attributes"]["will"] = 4  # Low will, likely to fail
        engine = CorruptionEngine()
        # With low will (d4), DC 12 always fails
        effects = engine.check_corruption_consequences(char, random.Random(42))
        self.assertEqual(char["corruption"], 6)

    def test_reversibility(self):
        engine = CorruptionEngine()
        self.assertTrue(engine.is_reversible(self._make_char(2)))
        self.assertTrue(engine.is_reversible(self._make_char(4)))
        self.assertFalse(engine.is_reversible(self._make_char(5)))
        self.assertFalse(engine.is_reversible(self._make_char(6)))

    def test_reversal_segments_1_2(self):
        char = self._make_char(2)
        engine = CorruptionEngine()
        result = engine.attempt_reversal(char, "absence")
        self.assertIsNotNone(result)
        self.assertEqual(char["corruption"], 1)

    def test_reversal_segments_3_4_time_limited(self):
        char = self._make_char(4)
        char["age"] = 30
        engine = CorruptionEngine()
        result = engine.attempt_reversal(char, "biokinetic")
        self.assertIsNotNone(result)
        self.assertEqual(char["corruption"], 3)
        # Second attempt within 5 years should fail (still at segment 3-4)
        result2 = engine.attempt_reversal(char, "biokinetic")
        self.assertIsNone(result2)

    def test_reversal_segment_5_special_method(self):
        char = self._make_char(5)
        engine = CorruptionEngine()
        result = engine.attempt_reversal(char, "patron_release")
        self.assertIsNotNone(result)
        self.assertEqual(char["corruption"], 4)

    def test_reversal_segment_6_irreversible(self):
        char = self._make_char(6)
        engine = CorruptionEngine()
        result = engine.attempt_reversal(char, "patron_release")
        self.assertIsNone(result)

    def test_sources_tracked(self):
        char = self._make_char()
        engine = CorruptionEngine()
        engine.apply_corruption(char, 1, "eldritch")
        engine.apply_corruption(char, 0.5, "exposure")
        sources = char["corruption_sources"]
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["source"], "eldritch")

    def test_effects_defined_for_all_segments(self):
        for seg in range(7):
            self.assertIn(seg, CORRUPTION_EFFECTS)


if __name__ == "__main__":
    unittest.main()
