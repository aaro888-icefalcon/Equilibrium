"""Integration test: situation → encounter spec → validates cleanly."""

import random
import unittest

from emergence.tests.helpers.synthetic_world import make_synthetic_world
from emergence.engine.sim.situation_generator import SituationGenerator
from emergence.engine.sim.encounter_generator import EncounterGenerator
from emergence.engine.schemas.encounter import EncounterSpec


class TestSituationToEncounterSpec(unittest.TestCase):
    """Generate situations and encounter specs from synthetic world."""

    def test_generate_situation_from_world(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        gen = SituationGenerator()
        loc = locations["bronx_market"]
        npcs_present = [npcs["ghost"]]
        situation = gen.generate_situation(
            {"tick_timestamp": "T+1y 0m 5d"},
            {"heat": 2},
            loc, npcs_present, [], clocks, random.Random(42),
        )
        self.assertIsNotNone(situation)
        self.assertEqual(situation.location, "bronx_market")
        self.assertGreater(len(situation.player_choices), 0)

    def test_encounter_spec_from_situation(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        sit_gen = SituationGenerator()
        enc_gen = EncounterGenerator()

        loc = locations["bronx_fortress"]
        situation = sit_gen.generate_situation(
            {"tick_timestamp": "T+1y 0m 10d"},
            {"heat": 3},
            loc, [], [], clocks, random.Random(42),
        )

        spec = enc_gen.generate_encounter(
            situation, loc, {"id": "player", "heat": 3},
            clocks, random.Random(42),
        )
        self.assertIsInstance(spec, EncounterSpec)
        self.assertEqual(spec.location, "bronx_fortress")
        self.assertGreater(len(spec.enemies), 0)
        self.assertIn(spec.combat_register, ("human", "creature", "eldritch"))

    def test_multiple_specs_varied(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        sit_gen = SituationGenerator()
        enc_gen = EncounterGenerator()

        registers_seen = set()
        for seed in range(100):
            loc = locations["bronx_fortress"]
            situation = sit_gen.generate_situation(
                {}, {"heat": 2}, loc, [], [], clocks, random.Random(seed),
            )
            spec = enc_gen.generate_encounter(
                situation, loc, {"id": "p", "heat": 2},
                clocks, random.Random(seed),
            )
            registers_seen.add(spec.combat_register)

        # Should see at least 2 different registers given the mix of dangers
        self.assertGreaterEqual(len(registers_seen), 2,
                                f"Only saw registers: {registers_seen}")


if __name__ == "__main__":
    unittest.main()
