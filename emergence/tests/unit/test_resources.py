"""Unit tests for resource progression."""

import unittest

from emergence.engine.progression.resources import (
    ResourceProgression,
    RESOURCE_TYPES,
    WEALTH_TYPES,
)


class TestResourceProgression(unittest.TestCase):

    def _make_char(self):
        return {}

    def test_initial_state(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        self.assertEqual(rp.get_resource("cu"), 0)

    def test_add_resource(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        result = rp.add_resource("cu", 500)
        self.assertEqual(result, 500)
        self.assertEqual(rp.get_resource("cu"), 500)

    def test_spend_resource_success(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("cu", 500)
        self.assertTrue(rp.spend_resource("cu", 200))
        self.assertEqual(rp.get_resource("cu"), 300)

    def test_spend_resource_failure(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("cu", 100)
        self.assertFalse(rp.spend_resource("cu", 200))
        self.assertEqual(rp.get_resource("cu"), 100)

    def test_has_resource(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        self.assertFalse(rp.has_resource("cu", 1))
        rp.add_resource("cu", 50)
        self.assertTrue(rp.has_resource("cu", 50))
        self.assertFalse(rp.has_resource("cu", 51))

    def test_cu_no_decay(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("cu", 1000)
        changes = rp.apply_wealth_decay(months=12)
        self.assertEqual(rp.get_resource("cu"), 1000)

    def test_scrip_decays(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("scrip", 1000)
        rp.apply_wealth_decay(months=12)
        self.assertLess(rp.get_resource("scrip"), 1000)

    def test_grain_decays_fast(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("grain_stores", 1000)
        rp.apply_wealth_decay(months=12)
        self.assertLess(rp.get_resource("grain_stores"), 1000)

    def test_follower_upkeep(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("retainers", 3)
        rp.add_resource("retinue", 1)
        result = rp.apply_follower_upkeep(wealth_available=1000)
        self.assertEqual(result["upkeep_cost"], 3 * 150 + 1 * 300)
        self.assertTrue(result["can_afford"])

    def test_follower_upkeep_cant_afford(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("retainers", 3)
        result = rp.apply_follower_upkeep(wealth_available=100)
        self.assertFalse(result["can_afford"])
        self.assertEqual(result["morale_penalty"], 1)

    def test_holding_upkeep(self):
        char = self._make_char()
        rp = ResourceProgression(char)
        rp.add_resource("holding_residence", 1)
        rp.add_resource("holding_fortified_position", 1)
        cost = rp.apply_holding_upkeep()
        self.assertEqual(cost, 30 + 80)

    def test_resource_types_defined(self):
        self.assertEqual(len(RESOURCE_TYPES), 7)

    def test_wealth_types_defined(self):
        self.assertEqual(len(WEALTH_TYPES), 6)


if __name__ == "__main__":
    unittest.main()
