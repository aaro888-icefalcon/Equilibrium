"""Unit tests for emergence.engine.sim.encounter_generator — encounter generation."""

import random
import unittest

from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Location,
    LocationConnection,
    Situation,
    SituationChoice,
)
from emergence.engine.schemas.encounter import EncounterSpec
from emergence.engine.sim.encounter_generator import EncounterGenerator


def _make_situation(**overrides) -> Situation:
    defaults = dict(
        location="manhattan_lower",
        timestamp="T+1y 0m 5d",
        tension="tense",
        encounter_probability=0.3,
        player_choices=[],
    )
    defaults.update(overrides)
    return Situation(**defaults)


def _make_location(**overrides) -> Location:
    defaults = dict(
        id="manhattan_lower",
        display_name="Lower Manhattan",
        type="urban",
        controller="council",
        population=5000,
        ambient=AmbientConditions(threat_level=2),
    )
    defaults.update(overrides)
    return Location(**defaults)


class TestEncounterTrigger(unittest.TestCase):

    def test_high_probability_triggers(self):
        gen = EncounterGenerator()
        sit = _make_situation(encounter_probability=0.99)
        triggered = 0
        for seed in range(100):
            if gen.should_trigger_encounter(sit, random.Random(seed)):
                triggered += 1
        self.assertGreater(triggered, 90)

    def test_low_probability_rarely_triggers(self):
        gen = EncounterGenerator()
        sit = _make_situation(encounter_probability=0.01)
        triggered = 0
        for seed in range(100):
            if gen.should_trigger_encounter(sit, random.Random(seed)):
                triggered += 1
        self.assertLess(triggered, 10)


class TestEncounterSpecGeneration(unittest.TestCase):

    def test_produces_valid_spec(self):
        gen = EncounterGenerator()
        sit = _make_situation(tension="tense")
        loc = _make_location()
        player = {"id": "player", "heat": 2}
        spec = gen.generate_encounter(sit, loc, player, {}, random.Random(42))
        self.assertIsInstance(spec, EncounterSpec)
        self.assertEqual(spec.location, "manhattan_lower")
        self.assertIn(spec.combat_register, ("human", "creature", "eldritch"))

    def test_enemies_present(self):
        gen = EncounterGenerator()
        sit = _make_situation(tension="volatile")
        loc = _make_location()
        spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(42))
        self.assertGreater(len(spec.enemies), 0)

    def test_terrain_zones_present(self):
        gen = EncounterGenerator()
        sit = _make_situation()
        loc = _make_location()
        spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(42))
        self.assertGreater(len(spec.terrain_zones), 0)

    def test_conditions_present(self):
        gen = EncounterGenerator()
        sit = _make_situation()
        loc = _make_location()
        spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(42))
        self.assertGreater(len(spec.win_conditions), 0)
        self.assertGreater(len(spec.loss_conditions), 0)
        self.assertGreater(len(spec.escape_conditions), 0)


class TestRegisterDetermination(unittest.TestCase):

    def test_creature_danger_favors_creature_register(self):
        gen = EncounterGenerator()
        creature_count = 0
        for seed in range(200):
            sit = _make_situation()
            loc = _make_location(dangers=["mutant_activity", "feral_pack"])
            spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(seed))
            if spec.combat_register == "creature":
                creature_count += 1
        self.assertGreater(creature_count, 50, f"Creature register only {creature_count}/200")

    def test_eldritch_clock_favors_eldritch_register(self):
        gen = EncounterGenerator()
        eldritch_count = 0
        clocks = {
            "eldritch_tide": Clock(
                id="eldritch_tide", current_segment=7, total_segments=8,
            ),
        }
        for seed in range(200):
            sit = _make_situation()
            loc = _make_location()
            spec = gen.generate_encounter(sit, loc, {"id": "p"}, clocks, random.Random(seed))
            if spec.combat_register == "eldritch":
                eldritch_count += 1
        self.assertGreater(eldritch_count, 20, f"Eldritch register only {eldritch_count}/200")

    def test_human_parley_available(self):
        gen = EncounterGenerator()
        for seed in range(200):
            sit = _make_situation()
            loc = _make_location()
            spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(seed))
            if spec.combat_register == "human":
                self.assertTrue(spec.parley_available)
                return
        self.skipTest("No human register in 200 seeds")


class TestEnemyScaling(unittest.TestCase):

    def test_calm_fewer_enemies(self):
        gen = EncounterGenerator()
        counts = []
        for seed in range(50):
            sit = _make_situation(tension="calm")
            loc = _make_location()
            spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(seed))
            counts.append(len(spec.enemies))
        avg_calm = sum(counts) / len(counts)
        self.assertLessEqual(avg_calm, 1.5)

    def test_critical_more_enemies(self):
        gen = EncounterGenerator()
        counts = []
        for seed in range(50):
            sit = _make_situation(tension="critical")
            loc = _make_location()
            spec = gen.generate_encounter(sit, loc, {"id": "p"}, {}, random.Random(seed))
            counts.append(len(spec.enemies))
        avg_critical = sum(counts) / len(counts)
        self.assertGreater(avg_critical, 2.0)


if __name__ == "__main__":
    unittest.main()
