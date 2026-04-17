"""Unit tests for the v4 threat archetype registry and threat floor."""

from __future__ import annotations

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation import threats


class TestThreatRegistry(unittest.TestCase):
    def test_registry_loads(self):
        reg = threats.get_threat_registry()
        self.assertGreaterEqual(len(reg), 10)
        # All ten expected ids present.
        expected = {
            "knife_scavenger_survivor", "iron_crown_notice",
            "warped_predator_personal", "eldritch_persistent",
            "named_rival_human", "faction_assassin_contract",
            "biokinetic_error_infection", "debt_holder",
            "ruined_former_ally", "family_complication",
        }
        self.assertTrue(expected.issubset(reg.keys()))

    def test_get_archetype(self):
        arc = threats.get_archetype("iron_crown_notice")
        self.assertIsNotNone(arc)
        self.assertEqual(arc.display_name, "Iron Crown attention")
        self.assertEqual(arc.pressure_default, 3)
        self.assertEqual(arc.pressure_range, (2, 5))
        self.assertEqual(arc.encounter_template, "iron_crown_squad")

    def test_unknown_archetype(self):
        self.assertIsNone(threats.get_archetype("not_a_real_id"))

    def test_clamp_pressure(self):
        self.assertEqual(threats.clamp_pressure("iron_crown_notice", 10), 5)
        self.assertEqual(threats.clamp_pressure("iron_crown_notice", 0), 2)
        self.assertEqual(threats.clamp_pressure("iron_crown_notice", 4), 4)
        # Unknown archetype falls back to 1..5 clamp.
        self.assertEqual(threats.clamp_pressure("unknown", 100), 5)
        self.assertEqual(threats.clamp_pressure("unknown", -5), 1)


class TestApplyNormalization(unittest.TestCase):
    def test_default_pressure_from_archetype(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(42)
        s = f.apply_scene_result("t", {"threats": [
            {"name": "captain", "standing": -2, "archetype": "iron_crown_notice"},
        ]}, s, r)
        self.assertEqual(s.threats[0]["pressure"], 3)
        self.assertEqual(s.threats[0]["archetype"], "iron_crown_notice")

    def test_pressure_clamped(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(42)
        s = f.apply_scene_result("t", {"threats": [
            {"name": "stranger", "standing": -2,
             "archetype": "knife_scavenger_survivor", "pressure": 99},
        ]}, s, r)
        self.assertEqual(s.threats[0]["pressure"], 4)

    def test_legacy_passthrough(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(42)
        s = f.apply_scene_result("t", {"threats": [
            {"name": "legacy", "standing": -2, "source": "old"},
        ]}, s, r)
        self.assertEqual(s.threats[0]["name"], "legacy")
        self.assertNotIn("pressure", s.threats[0])


class TestThreatFloor(unittest.TestCase):
    def test_floor_reaches_two_from_empty(self):
        s = CreationState(region="New York City")
        f = CharacterFactory()
        r = random.Random(1)
        s = f._ensure_threat_floor(s, r, floor=2)
        self.assertEqual(len(s.threats), 2)
        for t in s.threats:
            self.assertEqual(t["archetype"], "named_rival_human")
            self.assertEqual(t["pressure"], 2)
            self.assertEqual(t["standing"], -2)

    def test_floor_idempotent(self):
        s = CreationState(region="Philadelphia")
        f = CharacterFactory()
        r = random.Random(2)
        s = f._ensure_threat_floor(s, r, floor=2)
        before = len(s.threats)
        s = f._ensure_threat_floor(s, r, floor=2)
        self.assertEqual(len(s.threats), before)

    def test_floor_skips_when_already_met(self):
        s = CreationState(region="Delmarva")
        s.threats = [
            {"name": "existing1", "standing": -2, "source": "prior"},
            {"name": "existing2", "standing": -2, "source": "prior"},
        ]
        f = CharacterFactory()
        r = random.Random(3)
        s = f._ensure_threat_floor(s, r, floor=2)
        self.assertEqual(len(s.threats), 2)
        self.assertEqual(s.threats[0]["name"], "existing1")

    def test_floor_with_higher_target(self):
        s = CreationState(region="Lehigh Valley")
        f = CharacterFactory()
        r = random.Random(4)
        s = f._ensure_threat_floor(s, r, floor=4)
        self.assertEqual(len(s.threats), 4)


if __name__ == "__main__":
    unittest.main()
