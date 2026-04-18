"""Unit tests for scaffolds.build_scaffold."""

from __future__ import annotations

import json
import os
import random
import unittest

from emergence.engine.character_creation.character_factory import CreationState
from emergence.engine.character_creation.scaffolds import (
    build_scaffold, PER_INDEX_DEFAULTS,
)


_DATA_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "powers_v2", "cognitive.json",
))


def _state_with_powers() -> CreationState:
    powers = json.load(open(_DATA_PATH))
    s = CreationState()
    s.powers = [
        {"power_id": powers[0]["id"], "name": powers[0]["name"]},
        {"power_id": powers[1]["id"], "name": powers[1]["name"]},
    ]
    return s


class TestWellFormed(unittest.TestCase):
    def test_v1_well_formed(self):
        s = _state_with_powers()
        sc = build_scaffold(s, 1, random.Random(1))
        self.assertEqual(sc.index, 1)
        self.assertEqual(sc.mechanical_slot, "primary_cast")
        self.assertEqual(len(sc.option_pool), 3)
        self.assertEqual(sc.required_seeds,
                         PER_INDEX_DEFAULTS[1]["required_seeds"])

    def test_v2_has_region_outcomes_and_require_flag(self):
        s = _state_with_powers()
        sc = build_scaffold(s, 2, random.Random(2))
        self.assertEqual(sc.mechanical_slot, "primary_rider")
        self.assertIsNotNone(sc.seed_pools.region_outcomes)
        self.assertTrue(sc.required_seeds.require_region_outcome)

    def test_v3_uses_secondary_power(self):
        s = _state_with_powers()
        sc = build_scaffold(s, 3, random.Random(3))
        self.assertEqual(sc.mechanical_slot, "secondary_cast")
        self.assertEqual(sc.power_id, s.powers[1]["power_id"])

    def test_v4_requires_starting(self):
        s = _state_with_powers()
        sc = build_scaffold(s, 4, random.Random(4))
        self.assertEqual(sc.mechanical_slot, "secondary_rider")
        self.assertTrue(sc.required_seeds.require_is_starting)
        self.assertGreaterEqual(sc.required_seeds.min_goals_from_vows, 2)


class TestEmptyPowers(unittest.TestCase):
    def test_no_powers_gives_empty_pool(self):
        sc = build_scaffold(CreationState(), 1, random.Random(1))
        self.assertEqual(sc.option_pool, [])


class TestPriorSummaries(unittest.TestCase):
    def test_only_vignette_type_entries(self):
        s = _state_with_powers()
        s.history.append({"type": "session_zero", "description": "not this"})
        s.history.append({"type": "character_creation_vignette",
                          "description": "picked first", "timestamp": "T+0"})
        s.history.append({"type": "character_creation_vignette",
                          "description": "picked second", "timestamp": "T+1"})
        sc = build_scaffold(s, 2, random.Random(1))
        self.assertEqual(sc.prior_vignette_summaries,
                         ["picked first", "picked second"])


class TestUnknownIndex(unittest.TestCase):
    def test_raises_on_bad_index(self):
        with self.assertRaises(ValueError):
            build_scaffold(CreationState(), 7, random.Random(1))


if __name__ == "__main__":
    unittest.main()
