"""Unit tests for emergence.engine.combat.resolution."""

import random
import unittest

from emergence.engine.combat.resolution import (
    roll_die,
    roll_check,
    classify_result,
    tier_gap_modifier,
    compute_defense_value,
    compute_mental_defense,
    compute_initiative_bonus,
    SuccessTier,
    CheckResult,
    VALID_DIE_SIZES,
)


class TestRollDie(unittest.TestCase):
    """Tests for roll_die()."""

    def test_valid_die_sizes(self):
        rng = random.Random(1)
        for size in sorted(VALID_DIE_SIZES):
            result = roll_die(size, rng)
            self.assertGreaterEqual(result, 1)
            self.assertLessEqual(result, size)

    def test_degraded_die_below_4(self):
        rng = random.Random(42)
        results = [roll_die(2, rng) for _ in range(100)]
        self.assertTrue(all(0 <= r <= 3 for r in results))
        # Should sometimes be 0
        self.assertIn(0, results)

    def test_invalid_die_size_raises(self):
        rng = random.Random(1)
        with self.assertRaises(ValueError):
            roll_die(7, rng)

    def test_deterministic_with_seed(self):
        r1 = roll_die(8, random.Random(99))
        r2 = roll_die(8, random.Random(99))
        self.assertEqual(r1, r2)


class TestClassifyResult(unittest.TestCase):
    """Tests for classify_result()."""

    def test_double_ones_is_fumble(self):
        tier = classify_result(1, 1, 1, 20, 10)
        self.assertEqual(tier, SuccessTier.FUMBLE)

    def test_critical_doubles(self):
        # Both dice 8, total 8 >= TN 8
        tier = classify_result(8, 8, 8, 8, 8)
        self.assertEqual(tier, SuccessTier.CRITICAL)

    def test_full_success(self):
        # total 15, TN 10 → margin +5 → Full
        tier = classify_result(10, 5, 10, 15, 10)
        self.assertEqual(tier, SuccessTier.FULL)

    def test_marginal_success(self):
        # total 11, TN 10 → margin +1 → Marginal
        tier = classify_result(6, 5, 6, 11, 10)
        self.assertEqual(tier, SuccessTier.MARGINAL)

    def test_partial_failure(self):
        # total 8, TN 10 → margin -2 → Partial Failure
        tier = classify_result(5, 3, 5, 8, 10)
        self.assertEqual(tier, SuccessTier.PARTIAL_FAILURE)

    def test_failure(self):
        # total 6, TN 10 → margin -4 → Failure
        tier = classify_result(4, 2, 4, 6, 10)
        self.assertEqual(tier, SuccessTier.FAILURE)

    def test_deep_fumble(self):
        # total 3, TN 10 → margin -7 → Fumble
        tier = classify_result(2, 3, 3, 3, 10)
        self.assertEqual(tier, SuccessTier.FUMBLE)


class TestRollCheck(unittest.TestCase):
    """Tests for roll_check()."""

    def test_basic_check_returns_check_result(self):
        rng = random.Random(42)
        result = roll_check(8, 6, [2], 10, rng)
        self.assertIsInstance(result, CheckResult)
        self.assertEqual(result.tn, 10)
        self.assertEqual(result.margin, result.total - result.tn)

    def test_modifier_clamping(self):
        rng = random.Random(1)
        result = roll_check(6, 6, [10, 10], 10, rng)
        # Max mod is +6, so total = high + 6
        self.assertLessEqual(result.total, 12 + 6)

    def test_negative_modifier_clamping(self):
        rng = random.Random(1)
        result = roll_check(6, 6, [-10, -10], 10, rng)
        # Min mod is -6, so total = high - 6
        self.assertGreaterEqual(result.total, 1 - 6)

    def test_deterministic(self):
        r1 = roll_check(8, 6, [1], 10, random.Random(77))
        r2 = roll_check(8, 6, [1], 10, random.Random(77))
        self.assertEqual(r1, r2)

    def test_monte_carlo_distribution(self):
        """d8+d6 with +3 mod vs TN10: success rate should be roughly 20-70%."""
        rng = random.Random(12345)
        successes = sum(
            1 for _ in range(10000)
            if roll_check(8, 6, [3], 10, rng).margin >= 0
        )
        rate = successes / 10000
        self.assertGreater(rate, 0.15)
        self.assertLess(rate, 0.75)


class TestTierGapModifier(unittest.TestCase):
    """Tests for tier_gap_modifier()."""

    def test_equal_tiers(self):
        self.assertEqual(tier_gap_modifier(3, 3), (0, 0))

    def test_attacker_higher(self):
        atk_mod, def_mod = tier_gap_modifier(5, 3)
        self.assertGreater(atk_mod, 0)
        self.assertLessEqual(def_mod, 0)

    def test_defender_higher(self):
        atk_mod, def_mod = tier_gap_modifier(2, 5)
        self.assertLessEqual(atk_mod, 0)
        self.assertGreater(def_mod, 0)

    def test_gap_1(self):
        self.assertEqual(tier_gap_modifier(4, 3), (1, 0))


class TestDerivedValues(unittest.TestCase):
    """Tests for compute_defense_value and compute_mental_defense."""

    def test_defense_value(self):
        self.assertEqual(compute_defense_value(8, 2), 10)

    def test_mental_defense(self):
        self.assertEqual(compute_mental_defense(6, 0), 6)

    def test_initiative_bonus(self):
        self.assertEqual(compute_initiative_bonus(8, 6), 4)


if __name__ == "__main__":
    unittest.main()
