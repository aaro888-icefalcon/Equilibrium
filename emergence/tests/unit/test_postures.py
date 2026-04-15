"""Unit tests for emergence.engine.combat.postures."""

import random
import unittest
from types import SimpleNamespace

from emergence.engine.combat.postures import (
    resolve_posture_defense,
    get_attacker_tn_modifier,
    change_posture,
    validate_posture_rider_compat,
    PARRY, BLOCK, DODGE, AGGRESSIVE,
)


def _make_target(**kwargs):
    defaults = dict(
        strength=8, agility=8, perception=8, will=8, insight=8, might=8,
        current_posture="parry",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestPostureDefense(unittest.TestCase):

    def test_aggressive_no_defense(self):
        target = _make_target()
        result = resolve_posture_defense(target, AGGRESSIVE, 15, random.Random(1))
        self.assertFalse(result["negated"])
        self.assertEqual(result["damage_reduction"], 0)
        self.assertIsNone(result["defender_roll"])

    def test_block_flat_reduction(self):
        target = _make_target(might=10)
        result = resolve_posture_defense(target, BLOCK, 15, random.Random(1))
        self.assertFalse(result["negated"])
        self.assertEqual(result["damage_reduction"], 5)  # 10 // 2

    def test_block_with_low_might(self):
        target = _make_target(might=4)
        result = resolve_posture_defense(target, BLOCK, 15, random.Random(1))
        self.assertEqual(result["damage_reduction"], 2)  # 4 // 2

    def test_parry_success_negates(self):
        """With high attributes and low attacker total, parry should sometimes negate."""
        target = _make_target(perception=12, agility=12)
        rng = random.Random(42)
        # Low attacker total — easy to parry
        negated_count = 0
        for seed in range(100):
            result = resolve_posture_defense(target, PARRY, 8, random.Random(seed))
            if result["negated"]:
                negated_count += 1
        self.assertGreater(negated_count, 0, "Parry should negate at least sometimes")

    def test_parry_gives_counter_bonus(self):
        """Successful parry should give counter_bonus = 1."""
        target = _make_target(perception=12, agility=12)
        for seed in range(200):
            result = resolve_posture_defense(target, PARRY, 6, random.Random(seed))
            if result["negated"] and result["counter_bonus"] > 0:
                self.assertEqual(result["counter_bonus"], 1)
                return
        self.fail("Expected at least one parry with counter bonus in 200 trials")

    def test_dodge_all_or_nothing(self):
        """Dodge either negates or doesn't — never reduces."""
        target = _make_target(agility=10, insight=10)
        for seed in range(100):
            result = resolve_posture_defense(target, DODGE, 10, random.Random(seed))
            # Either negated or no reduction
            self.assertEqual(result["damage_reduction"], 0)

    def test_dodge_success_negates(self):
        target = _make_target(agility=12, insight=12)
        negated = 0
        for seed in range(100):
            result = resolve_posture_defense(target, DODGE, 8, random.Random(seed))
            if result["negated"]:
                negated += 1
        self.assertGreater(negated, 0)


class TestAttackerTnModifier(unittest.TestCase):

    def test_aggressive_gives_bonus(self):
        self.assertEqual(get_attacker_tn_modifier(AGGRESSIVE), -1)

    def test_parry_no_modifier(self):
        self.assertEqual(get_attacker_tn_modifier(PARRY), 0)

    def test_block_no_modifier(self):
        self.assertEqual(get_attacker_tn_modifier(BLOCK), 0)


class TestChangePosture(unittest.TestCase):

    def test_change_posture(self):
        target = _make_target(current_posture="parry")
        old = change_posture(target, "aggressive")
        self.assertEqual(old, "parry")
        self.assertEqual(target.current_posture, "aggressive")

    def test_invalid_posture_raises(self):
        target = _make_target()
        with self.assertRaises(ValueError):
            change_posture(target, "invalid")


class TestPostureRiderCompat(unittest.TestCase):

    def test_reactive_defense_incompatible_with_aggressive(self):
        self.assertFalse(validate_posture_rider_compat("reactive_defense", AGGRESSIVE, []))

    def test_reactive_defense_compatible_with_parry(self):
        self.assertTrue(validate_posture_rider_compat("reactive_defense", PARRY, []))

    def test_explicit_posture_list_blocks(self):
        self.assertFalse(validate_posture_rider_compat("periodic", DODGE, ["parry", "block"]))

    def test_explicit_posture_list_allows(self):
        self.assertTrue(validate_posture_rider_compat("periodic", PARRY, ["parry", "block"]))

    def test_empty_compat_list_allows_all(self):
        self.assertTrue(validate_posture_rider_compat("periodic", DODGE, []))


if __name__ == "__main__":
    unittest.main()
