"""Unit tests for procedural NPC generator."""

import random
import unittest

from emergence.engine.sim.npc_generator import (
    SPECIES_LIST,
    generate_npc,
    generate_npc_batch,
)
from emergence.engine.schemas.world import NPC


class TestGenerateNpc(unittest.TestCase):

    def test_returns_npc_object(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertIsInstance(npc, NPC)

    def test_has_display_name(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreater(len(npc.display_name), 3)
        self.assertIn(" ", npc.display_name)

    def test_species_from_valid_list(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertIn(npc.species, SPECIES_LIST)

    def test_manifestation_has_tier(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreaterEqual(npc.manifestation.tier, 1)
        self.assertLessEqual(npc.manifestation.tier, 10)

    def test_manifestation_has_category(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertIn(npc.manifestation.category, [
            "physical", "perceptual", "matter_energy",
            "biological", "auratic", "temporal_spatial", "eldritch",
        ])

    def test_age_in_range(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreaterEqual(npc.age, 18)
        self.assertLessEqual(npc.age, 65)

    def test_has_voice(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreater(len(npc.voice), 10)

    def test_has_role(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreater(len(npc.role), 0)

    def test_has_personality_traits(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreater(len(npc.personality_traits), 0)

    def test_has_goals(self):
        npc = generate_npc(rng=random.Random(42))
        self.assertGreater(len(npc.goals), 0)

    def test_archetype_sets_role(self):
        npc = generate_npc(archetype="healer", rng=random.Random(42))
        self.assertEqual(npc.role, "healer")

    def test_constraints_override_species(self):
        npc = generate_npc(constraints={"species": "wide_sighted"}, rng=random.Random(42))
        self.assertEqual(npc.species, "wide_sighted")

    def test_constraints_override_tier(self):
        npc = generate_npc(constraints={"tier": 7}, rng=random.Random(42))
        self.assertEqual(npc.manifestation.tier, 7)

    def test_constraints_override_age(self):
        npc = generate_npc(constraints={"age": 22}, rng=random.Random(42))
        self.assertEqual(npc.age, 22)

    def test_constraints_override_faction(self):
        npc = generate_npc(constraints={"faction": "iron-crown"}, rng=random.Random(42))
        self.assertEqual(npc.faction_affiliation["primary"], "iron-crown")

    def test_constraints_override_location(self):
        npc = generate_npc(constraints={"location": "loc-mount-tremper"}, rng=random.Random(42))
        self.assertEqual(npc.location, "loc-mount-tremper")

    def test_deterministic_with_seed(self):
        npc1 = generate_npc(rng=random.Random(99))
        npc2 = generate_npc(rng=random.Random(99))
        self.assertEqual(npc1.display_name, npc2.display_name)
        self.assertEqual(npc1.species, npc2.species)
        self.assertEqual(npc1.manifestation.tier, npc2.manifestation.tier)


class TestGenerateBatch(unittest.TestCase):

    def test_generates_requested_count(self):
        npcs = generate_npc_batch(10, rng=random.Random(42))
        self.assertEqual(len(npcs), 10)

    def test_names_diverse(self):
        npcs = generate_npc_batch(20, rng=random.Random(42))
        names = {npc.display_name for npc in npcs}
        # At least 80% unique names
        self.assertGreater(len(names), 16)

    def test_species_diverse(self):
        npcs = generate_npc_batch(100, rng=random.Random(42))
        species = {npc.species for npc in npcs}
        # With 100 NPCs and weighted sampling, should see multiple species
        self.assertGreater(len(species), 3)

    def test_tier_distribution_reasonable(self):
        npcs = generate_npc_batch(200, rng=random.Random(42))
        tiers = [npc.manifestation.tier for npc in npcs]
        # Most should be T1-T3
        low_tiers = sum(1 for t in tiers if t <= 3)
        self.assertGreater(low_tiers / len(tiers), 0.6)

    def test_all_are_npc_objects(self):
        npcs = generate_npc_batch(10, rng=random.Random(42))
        for npc in npcs:
            self.assertIsInstance(npc, NPC)


if __name__ == "__main__":
    unittest.main()
