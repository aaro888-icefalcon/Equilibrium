"""Unit tests for manifestation scene (Scene 5)."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.manifestation import (
    ManifestationScene,
    _roll_category,
    _roll_tier,
)


class TestRollCategory(unittest.TestCase):

    def test_returns_valid_category(self):
        valid = {
            "physical_kinetic", "perceptual_mental", "matter_energy",
            "biological_vital", "auratic", "temporal_spatial", "eldritch_corruptive",
        }
        for circ in "ABCDEFGH":
            cat = _roll_category(circ, random.Random(42))
            self.assertIn(cat, valid, f"Circumstance {circ} gave invalid category {cat}")

    def test_crisis_circumstance_favors_physical(self):
        # Circumstance G (in motion) has 1.8x physical weight
        rng = random.Random(1)
        results = [_roll_category("G", random.Random(i)) for i in range(200)]
        physical_count = sum(1 for r in results if r == "physical_kinetic")
        # Should be well above baseline 28%
        self.assertGreater(physical_count / len(results), 0.30)

    def test_asleep_favors_perceptual(self):
        results = [_roll_category("F", random.Random(i)) for i in range(200)]
        perceptual_count = sum(1 for r in results if r == "perceptual_mental")
        self.assertGreater(perceptual_count / len(results), 0.15)


class TestRollTier(unittest.TestCase):

    def test_returns_valid_tier(self):
        for _ in range(100):
            tier = _roll_tier("A", [], random.Random(_))
            self.assertIn(tier, [1, 2, 3, 4])

    def test_distribution_favors_low_tier(self):
        tiers = [_roll_tier("A", [], random.Random(i)) for i in range(500)]
        t1_count = sum(1 for t in tiers if t == 1)
        self.assertGreater(t1_count / len(tiers), 0.35)

    def test_veteran_boosts_tier3(self):
        tiers_base = [_roll_tier("A", [], random.Random(i)) for i in range(500)]
        tiers_vet = [_roll_tier("A", ["veteran"], random.Random(i)) for i in range(500)]
        t3_base = sum(1 for t in tiers_base if t >= 3)
        t3_vet = sum(1 for t in tiers_vet if t >= 3)
        self.assertGreaterEqual(t3_vet, t3_base)


class TestManifestationScene(unittest.TestCase):

    def _make_state(self) -> CreationState:
        state = CreationState(name="Test", age_at_onset=25, seed=42)
        state.scene_choices["sz_3"] = {"onset_circumstance": "A"}
        return state

    def test_generates_power_choices(self):
        scene = ManifestationScene()
        state = self._make_state()
        choices = scene.get_choices(state)
        self.assertGreater(len(choices), 0)

    def test_applies_powers(self):
        scene = ManifestationScene()
        factory = CharacterFactory()
        state = self._make_state()
        rng = random.Random(42)

        choices = scene.get_choices(state)
        state = scene.apply(0, state, factory, rng)

        self.assertGreater(len(state.powers), 0)
        self.assertGreater(state.tier, 0)
        self.assertGreater(len(state.power_category_primary), 0)

    def test_has_breakthrough_record(self):
        scene = ManifestationScene()
        factory = CharacterFactory()
        state = self._make_state()
        rng = random.Random(42)

        scene.get_choices(state)
        state = scene.apply(0, state, factory, rng)

        self.assertGreater(len(state.breakthroughs), 0)

    def test_tier_ceiling_set(self):
        scene = ManifestationScene()
        factory = CharacterFactory()
        state = self._make_state()
        rng = random.Random(42)

        scene.get_choices(state)
        state = scene.apply(0, state, factory, rng)

        self.assertEqual(state.tier_ceiling, state.tier + 2)

    def test_deterministic(self):
        scene1 = ManifestationScene()
        scene2 = ManifestationScene()
        state1 = self._make_state()
        state2 = self._make_state()
        factory = CharacterFactory()

        choices1 = scene1.get_choices(state1)
        choices2 = scene2.get_choices(state2)
        self.assertEqual(choices1, choices2)


if __name__ == "__main__":
    unittest.main()
