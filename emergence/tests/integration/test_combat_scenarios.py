"""Integration tests: run full encounters end-to-end per register."""

import random
import unittest

from emergence.engine.combat.encounter_runner import EncounterRunner
from emergence.engine.combat.verbs import CombatantRecord
from emergence.engine.combat.data_loader import load_encounters
from emergence.engine.schemas.encounter import CombatOutcome


def _make_player(tier=3) -> CombatantRecord:
    return CombatantRecord(
        id="player", side="player", tier=tier,
        strength=8, agility=8, perception=8,
        will=8, insight=8, might=8,
        phy_max=5, men_max=5, soc_max=5,
        exposure_max=4,
    )


class TestHumanRegisterEncounter(unittest.TestCase):
    """Run the raider ambush (human register) end-to-end."""

    def test_produces_valid_outcome(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        spec = next(e for e in encounters if e.id == "raider_ambush_cross_bronx")
        runner = EncounterRunner()
        rng = random.Random(12345)
        player = _make_player()
        outcome = runner.run(spec, player, rng)

        self.assertIsInstance(outcome, CombatOutcome)
        self.assertEqual(outcome.encounter_id, "raider_ambush_cross_bronx")
        self.assertIn(outcome.resolution, (
            "victory", "defeat", "escape", "parley", "stalemate",
        ))
        self.assertGreater(outcome.rounds_elapsed, 0)

    def test_serializes_cleanly(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        spec = next(e for e in encounters if e.id == "raider_ambush_cross_bronx")
        runner = EncounterRunner()
        outcome = runner.run(spec, _make_player(), random.Random(42))
        d = outcome.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("resolution", d)
        self.assertIn("enemy_states", d)

    def test_deterministic_replay(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        spec = next(e for e in encounters if e.id == "raider_ambush_cross_bronx")
        runner = EncounterRunner()
        o1 = runner.run(spec, _make_player(), random.Random(999))
        o2 = runner.run(spec, _make_player(), random.Random(999))
        self.assertEqual(o1.resolution, o2.resolution)
        self.assertEqual(o1.rounds_elapsed, o2.rounds_elapsed)


class TestCreatureRegisterEncounter(unittest.TestCase):
    """Run a creature register encounter end-to-end."""

    def test_produces_valid_outcome(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        spec = next(e for e in encounters if e.id == "hunter_pair_catskills")
        runner = EncounterRunner()
        outcome = runner.run(spec, _make_player(), random.Random(777))

        self.assertIsInstance(outcome, CombatOutcome)
        self.assertEqual(outcome.encounter_id, "hunter_pair_catskills")
        self.assertIn(outcome.resolution, (
            "victory", "defeat", "escape", "parley", "stalemate",
        ))


class TestEldritchRegisterEncounter(unittest.TestCase):
    """Run an eldritch register encounter end-to-end."""

    def test_produces_valid_outcome(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        eldritch = [e for e in encounters if e.combat_register == "eldritch" and len(e.enemies) > 0]
        self.assertTrue(len(eldritch) > 0, "No eldritch encounters with enemies found")
        spec = eldritch[0]
        runner = EncounterRunner()
        outcome = runner.run(spec, _make_player(), random.Random(555))

        self.assertIsInstance(outcome, CombatOutcome)
        self.assertIn(outcome.resolution, (
            "victory", "defeat", "escape", "parley", "stalemate",
        ))

    def test_serializes_cleanly(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        eldritch = [e for e in encounters if e.combat_register == "eldritch" and len(e.enemies) > 0]
        spec = eldritch[0]
        runner = EncounterRunner()
        outcome = runner.run(spec, _make_player(), random.Random(555))
        d = outcome.to_dict()
        self.assertIsInstance(d, dict)
        self.assertIn("narrative_log", d)


if __name__ == "__main__":
    unittest.main()
