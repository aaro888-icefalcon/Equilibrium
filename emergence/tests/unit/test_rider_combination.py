"""Unit tests for emergence.engine.combat.rider_combination."""

import unittest

from emergence.engine.combat.rider_combination import (
    validate_combination,
    compute_combination_cost,
    resolve_combined_riders,
)


class TestValidation(unittest.TestCase):

    def test_same_type_valid(self):
        r_a = {"rider_type": "strike", "power_id": "p1", "slot_id": "r1", "pool_cost": 1}
        r_b = {"rider_type": "strike", "power_id": "p2", "slot_id": "r1", "pool_cost": 1}
        valid, reason = validate_combination(r_a, r_b)
        self.assertTrue(valid)

    def test_different_type_invalid(self):
        r_a = {"rider_type": "strike", "power_id": "p1", "slot_id": "r1", "pool_cost": 1}
        r_b = {"rider_type": "maneuver", "power_id": "p2", "slot_id": "r1", "pool_cost": 1}
        valid, reason = validate_combination(r_a, r_b)
        self.assertFalse(valid)
        self.assertIn("Type mismatch", reason)

    def test_posture_type_rejected(self):
        r_a = {"rider_type": "posture", "power_id": "p1", "slot_id": "r1", "pool_cost": 0}
        r_b = {"rider_type": "posture", "power_id": "p2", "slot_id": "r1", "pool_cost": 0}
        valid, reason = validate_combination(r_a, r_b)
        self.assertFalse(valid)
        self.assertIn("Posture", reason)

    def test_self_combination_rejected(self):
        r = {"rider_type": "strike", "power_id": "p1", "slot_id": "r1", "pool_cost": 1}
        valid, reason = validate_combination(r, r)
        self.assertFalse(valid)


class TestCost(unittest.TestCase):

    def test_sum_plus_one(self):
        r_a = {"pool_cost": 1}
        r_b = {"pool_cost": 1}
        self.assertEqual(compute_combination_cost(r_a, r_b), 3)  # 1+1+1

    def test_different_costs(self):
        r_a = {"pool_cost": 2}
        r_b = {"pool_cost": 1}
        self.assertEqual(compute_combination_cost(r_a, r_b), 4)  # 2+1+1


class TestResolve(unittest.TestCase):

    def test_both_apply_on_full(self):
        r_a = {"rider_type": "strike", "power_id": "p1", "slot_id": "r1",
               "pool_cost": 1, "effect_parameters": {"bonus_damage": 2}}
        r_b = {"rider_type": "strike", "power_id": "p2", "slot_id": "r1",
               "pool_cost": 1, "effect_parameters": {"bonus_damage": 1}}
        result = resolve_combined_riders(r_a, r_b, None, "full")
        self.assertTrue(result["rider_a"]["effects"]["applied"])
        self.assertTrue(result["rider_b"]["effects"]["applied"])
        self.assertEqual(result["rider_a"]["effects"]["bonus_damage"], 2)
        self.assertEqual(result["rider_b"]["effects"]["bonus_damage"], 1)

    def test_neither_applies_on_failure(self):
        r_a = {"rider_type": "strike", "power_id": "p1", "slot_id": "r1",
               "pool_cost": 1, "effect_parameters": {"bonus_damage": 2}}
        r_b = {"rider_type": "strike", "power_id": "p2", "slot_id": "r1",
               "pool_cost": 1, "effect_parameters": {"bonus_damage": 1}}
        result = resolve_combined_riders(r_a, r_b, None, "failure")
        self.assertFalse(result["rider_a"]["effects"]["applied"])
        self.assertFalse(result["rider_b"]["effects"]["applied"])

    def test_cost_in_result(self):
        r_a = {"pool_cost": 1}
        r_b = {"pool_cost": 1}
        result = resolve_combined_riders(r_a, r_b, None, "full")
        self.assertEqual(result["total_cost"], 3)


if __name__ == "__main__":
    unittest.main()
