"""Integration tests for progression — combat use, sim interactions, persistence."""

import json
import os
import random
import tempfile
import unittest

from emergence.engine.progression.tactical import TacticalProgression
from emergence.engine.progression.skills import SkillProgression
from emergence.engine.progression.relationships import RelationshipProgression
from emergence.engine.progression.factions import FactionProgression
from emergence.engine.progression.resources import ResourceProgression
from emergence.engine.progression.corruption import CorruptionEngine
from emergence.engine.progression.arcs import ArcTracker
from emergence.engine.persistence.save import SaveManager
from emergence.engine.persistence.load import LoadManager


def _make_char():
    return {
        "name": "Elena",
        "age": 30,
        "tier": 3,
        "tier_ceiling": 10,
        "primary_category": "physical_kinetic",
        "attributes": {"strength": 8, "will": 8, "insight": 6},
        "corruption": 0,
        "resources": {},
        "goals": [],
    }


class TestCombatPowerMarks(unittest.TestCase):
    """Power use in combat should generate strengthening marks."""

    def test_combat_power_use_creates_marks(self):
        char = _make_char()
        tac = TacticalProgression(char)

        # Simulate 25 combat uses of a power
        for _ in range(25):
            tac.log_power_use("pk_push", "physical_kinetic")

        self.assertEqual(tac.get_power_mark("pk_push"), 1)

    def test_multiple_powers_in_combat(self):
        char = _make_char()
        tac = TacticalProgression(char)

        for _ in range(25):
            tac.log_power_use("pk_push", "physical_kinetic")
            tac.log_power_use("pk_shield", "physical_kinetic")

        self.assertEqual(tac.get_power_mark("pk_push"), 1)
        self.assertEqual(tac.get_power_mark("pk_shield"), 1)
        # Category should be at 50 (25+25)
        self.assertEqual(tac.get_category_use_count("physical_kinetic"), 50)


class TestSimInteractionStanding(unittest.TestCase):
    """Sim interactions should change standings."""

    def test_trade_increases_standing(self):
        char = _make_char()
        rels = RelationshipProgression(char)
        factions = FactionProgression(char)

        rels.update_standing("merchant_npc", 1, "successful trade")
        factions.update_standing("bourse", 1, "traded at market")

        self.assertEqual(rels.get_standing("merchant_npc"), 1)
        self.assertEqual(factions.get_standing("bourse"), 1)

    def test_hostile_action_decreases_standing(self):
        char = _make_char()
        rels = RelationshipProgression(char)
        factions = FactionProgression(char)

        rels.update_standing("guard_npc", -2, "attacked")
        factions.update_standing("iron_crown", -1, "defied orders")

        self.assertEqual(rels.get_standing("guard_npc"), -2)
        self.assertEqual(factions.get_standing("iron_crown"), -1)


class TestProgressionPersistsSave(unittest.TestCase):
    """Progression state should persist across save/load cycles."""

    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            char = _make_char()

            # Apply progression
            TacticalProgression(char).log_power_use("p1", "physical_kinetic")
            SkillProgression(char).log_skill_use("melee")
            RelationshipProgression(char).update_standing("npc1", 2)
            FactionProgression(char).update_standing("f1", 1)
            ResourceProgression(char).add_resource("cu", 500)
            CorruptionEngine().apply_corruption(char, 0.5, "test")

            # Save
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player=char,
                factions={}, npcs={}, locations={}, clocks={},
            )

            # Load
            loader = LoadManager(tmpdir)
            result = loader.load_save()
            loaded = result.player

            # Verify progression state preserved
            self.assertEqual(loaded["power_use_counts"]["p1"], 1)
            self.assertEqual(loaded["skill_use_counts"]["melee"], 1)
            self.assertEqual(loaded["relationships"]["npc1"]["standing"], 2)
            self.assertEqual(loaded["faction_standings"]["f1"]["standing"], 1)
            self.assertEqual(loaded["resources"]["cu"], 500)
            self.assertEqual(loaded["corruption"], 0.5)

    def test_marks_persist(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            char = _make_char()
            tac = TacticalProgression(char)
            for _ in range(25):
                tac.log_power_use("p1", "physical_kinetic")

            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player=char,
                factions={}, npcs={}, locations={}, clocks={},
            )

            loader = LoadManager(tmpdir)
            loaded = loader.load_save().player
            self.assertEqual(loaded["power_marks"]["p1"], 1)


class TestCorruptionIntegration(unittest.TestCase):
    """Test corruption interacts with other systems."""

    def test_corruption_affects_faction_cap(self):
        char = _make_char()
        engine = CorruptionEngine()
        factions = FactionProgression(char)

        engine.apply_corruption(char, 5, "eldritch")
        self.assertTrue(char.get("faction_standing_cap") == 1)

    def test_corruption_arc_detection(self):
        char = _make_char()
        char["prev_corruption_segment"] = 0
        engine = CorruptionEngine()
        arcs = ArcTracker()

        engine.apply_corruption(char, 3, "eldritch")
        events = arcs.check_arc_progress(char, {})
        c_events = [e for e in events if "corruption" in e.arc_type]
        self.assertGreater(len(c_events), 0)


if __name__ == "__main__":
    unittest.main()
