"""Unit tests for emergence.engine.combat.pool."""

import unittest
from types import SimpleNamespace

from emergence.engine.combat.pool import (
    compute_base_pool_max,
    compute_effective_pool_max,
    init_pool,
    recalc_effective_pool_max,
    can_spend_pool,
    spend_pool,
    resolve_brace,
    refill_pool,
)


def _make_combatant(**kwargs):
    defaults = dict(
        tier=3, pool=0, pool_max=6, base_pool_max=6,
        brace_uses=3, armed_posture_riders=[], phy=0, phy_max=5,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestPoolMax(unittest.TestCase):

    def test_base_pool_max_t3(self):
        self.assertEqual(compute_base_pool_max(3), 6)

    def test_base_pool_max_t5(self):
        self.assertEqual(compute_base_pool_max(5), 8)

    def test_base_pool_max_t1(self):
        self.assertEqual(compute_base_pool_max(1), 4)

    def test_effective_pool_no_riders(self):
        self.assertEqual(compute_effective_pool_max(6, 0), 6)

    def test_effective_pool_one_rider(self):
        self.assertEqual(compute_effective_pool_max(6, 1), 5)

    def test_effective_pool_two_riders(self):
        self.assertEqual(compute_effective_pool_max(8, 2), 6)

    def test_effective_pool_floor_zero(self):
        self.assertEqual(compute_effective_pool_max(2, 5), 0)


class TestInitPool(unittest.TestCase):

    def test_init_t3_no_riders(self):
        c = _make_combatant(tier=3, armed_posture_riders=[])
        init_pool(c)
        self.assertEqual(c.base_pool_max, 6)
        self.assertEqual(c.pool_max, 6)
        self.assertEqual(c.pool, 6)
        self.assertEqual(c.brace_uses, 3)

    def test_init_t3_one_rider(self):
        c = _make_combatant(tier=3, armed_posture_riders=[{"power_id": "x"}])
        init_pool(c)
        self.assertEqual(c.pool_max, 5)
        self.assertEqual(c.pool, 5)

    def test_init_t5_two_riders(self):
        c = _make_combatant(tier=5, armed_posture_riders=[{}, {}])
        init_pool(c)
        self.assertEqual(c.base_pool_max, 8)
        self.assertEqual(c.pool_max, 6)
        self.assertEqual(c.pool, 6)


class TestRecalcEffective(unittest.TestCase):

    def test_recalc_after_arming(self):
        c = _make_combatant(base_pool_max=6, pool=6, pool_max=6, armed_posture_riders=[{}])
        recalc_effective_pool_max(c)
        self.assertEqual(c.pool_max, 5)
        # pool should be capped to new max
        self.assertEqual(c.pool, 5)

    def test_recalc_after_disarming(self):
        c = _make_combatant(base_pool_max=6, pool=4, pool_max=5, armed_posture_riders=[])
        recalc_effective_pool_max(c)
        self.assertEqual(c.pool_max, 6)
        # pool stays at 4, doesn't auto-refill
        self.assertEqual(c.pool, 4)


class TestSpendPool(unittest.TestCase):

    def test_spend_success(self):
        c = _make_combatant(pool=5)
        self.assertTrue(spend_pool(c, 2))
        self.assertEqual(c.pool, 3)

    def test_spend_insufficient(self):
        c = _make_combatant(pool=1)
        self.assertFalse(spend_pool(c, 3))
        self.assertEqual(c.pool, 1)  # unchanged

    def test_can_spend(self):
        c = _make_combatant(pool=3)
        self.assertTrue(can_spend_pool(c, 3))
        self.assertFalse(can_spend_pool(c, 4))


class TestBrace(unittest.TestCase):

    def test_brace_adds_one(self):
        c = _make_combatant(pool=4, pool_max=6, brace_uses=3)
        self.assertTrue(resolve_brace(c))
        self.assertEqual(c.pool, 5)
        self.assertEqual(c.brace_uses, 2)

    def test_brace_cap_at_effective_max(self):
        c = _make_combatant(pool=6, pool_max=6, brace_uses=3)
        self.assertFalse(resolve_brace(c))
        self.assertEqual(c.pool, 6)
        self.assertEqual(c.brace_uses, 3)  # not decremented

    def test_brace_three_use_limit(self):
        c = _make_combatant(pool=3, pool_max=6, brace_uses=3)
        self.assertTrue(resolve_brace(c))
        self.assertTrue(resolve_brace(c))
        self.assertTrue(resolve_brace(c))
        self.assertFalse(resolve_brace(c))
        self.assertEqual(c.pool, 6)
        self.assertEqual(c.brace_uses, 0)

    def test_brace_rejected_when_incapacitated(self):
        c = _make_combatant(pool=3, pool_max=6, brace_uses=3, phy=5, phy_max=5)
        self.assertFalse(resolve_brace(c))


class TestRefillPool(unittest.TestCase):

    def test_refill(self):
        c = _make_combatant(pool=2, pool_max=6, brace_uses=0)
        refill_pool(c)
        self.assertEqual(c.pool, 6)
        self.assertEqual(c.brace_uses, 3)


if __name__ == "__main__":
    unittest.main()
