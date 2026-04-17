"""Extended smoke test — long game simulation.

Tests 5 in-world years of ticking with progression, aging, combat encounters,
relationship dynamics, and eventual natural death + descendant continuation.
"""

import random
import unittest

from emergence.engine.progression.tactical import TacticalProgression
from emergence.engine.progression.breakthrough import BreakthroughEngine
from emergence.engine.progression.skills import SkillProgression
from emergence.engine.progression.relationships import RelationshipProgression
from emergence.engine.progression.factions import FactionProgression
from emergence.engine.progression.resources import ResourceProgression
from emergence.engine.progression.aging import AgingEngine, get_age_category
from emergence.engine.progression.family import FamilyEngine
from emergence.engine.progression.corruption import CorruptionEngine
from emergence.engine.progression.arcs import ArcTracker


def _make_test_character(seed=42):
    """Create a character for long-game testing."""
    rng = random.Random(seed)
    return {
        "name": "Elena",
        "age": 25,
        "species": "human",
        "tier": 2,
        "tier_ceiling": 10,
        "primary_category": "kinetic",
        "attributes": {
            "strength": 8, "agility": 8, "will": 8,
            "insight": 6, "perception": 8, "might": 8,
        },
        "condition_tracks": {"physical": 0, "physical_max": 6, "mental": 0},
        "powers": ["pk_force_push", "pk_kinetic_shield"],
        "goals": [
            {"description": "Build a clinic", "progress": 0, "status": "active"},
            {"description": "Find lost family", "progress": 0, "status": "active"},
        ],
        "corruption": 0,
        "resources": {"cu": 500, "scrip": 200},
        "partner": {"name": "Marcus", "species": "human"},
        "children": [],
    }


class TestLongGame5Years(unittest.TestCase):
    """Simulate 5 in-world years of gameplay."""

    def test_5_year_simulation(self):
        rng = random.Random(42)
        char = _make_test_character(42)

        tac = TacticalProgression(char)
        bt_engine = BreakthroughEngine()
        skills = SkillProgression(char)
        rels = RelationshipProgression(char)
        factions = FactionProgression(char)
        resources = ResourceProgression(char)
        aging = AgingEngine()
        family = FamilyEngine()
        corruption = CorruptionEngine()
        arcs = ArcTracker()

        events_total = 0
        encounters = 0
        breakthroughs = 0

        for year in range(5):
            # Yearly: aging, family, faction decay
            aging_events = aging.apply_yearly_aging(char, rng)
            family_events = family.check_family_events(char, {}, rng)
            corruption.check_corruption_consequences(char, rng)
            factions.apply_yearly_decay(current_day=year * 365, rng=rng)
            resources.apply_wealth_decay(months=12)

            events_total += len(aging_events) + len(family_events)

            # Simulate ~20 encounters per year
            for _ in range(20):
                encounters += 1

                # Use powers
                tac.log_power_use("pk_force_push", "kinetic")
                tac.log_power_use("pk_kinetic_shield", "kinetic")

                # Use skills
                skills.log_skill_use("melee")
                skills.log_skill_use("tactics")
                skills.log_skill_use("first_aid")

                # Build relationships
                if rng.random() < 0.1:
                    rels.update_standing("npc_merchant", 1, "trade", year * 365)
                if rng.random() < 0.05:
                    factions.update_standing("f_bourse", 1, "deal", year * 365)

                # Earn resources
                resources.add_resource("cu", rng.randint(10, 50))

                # Small corruption chance
                if rng.random() < 0.02:
                    corruption.apply_corruption(char, 0.1, "ambient")

                # Check breakthrough
                if rng.random() < 0.01:
                    event = {"type": "near_death"}
                    trigger = bt_engine.check_triggers(char, {}, event, rng=rng)
                    if trigger:
                        result = bt_engine.resolve_breakthrough(char, trigger, rng)
                        bt_engine.apply_breakthrough(char, result)
                        if result.success:
                            breakthroughs += 1

            # Progress goals
            char["goals"][0]["progress"] = min(100, char["goals"][0]["progress"] + 20)

            # Arc check
            arc_events = arcs.check_arc_progress(char, {})
            events_total += len(arc_events)

        # Verify state is valid
        self.assertEqual(char["age"], 30)
        self.assertGreater(encounters, 0)
        self.assertGreater(events_total, 0)

        # Power marks should have advanced
        self.assertGreater(tac.get_power_use_count("pk_force_push"), 0)
        # At 100 uses (5 years × 20 encounters), should have mark 2 (75 threshold)
        self.assertGreaterEqual(tac.get_power_mark("pk_force_push"), 2)

        # Skills should have leveled
        self.assertGreater(skills.get_proficiency("melee"), 0)
        self.assertGreater(skills.get_proficiency("tactics"), 0)

        # Resources should exist
        self.assertGreater(resources.get_resource("cu"), 0)

        # Goals should have progressed
        self.assertEqual(char["goals"][0]["status"], "completed")

        # No schema violations
        self.assertIsInstance(char["corruption"], (int, float))
        self.assertLessEqual(char["corruption"], 6)
        self.assertGreaterEqual(char["tier"], 2)


class TestAgingThroughDeath(unittest.TestCase):
    """Test character aging to death and descendant continuation."""

    def test_aging_to_death(self):
        rng = random.Random(42)
        char = _make_test_character(42)
        char["age"] = 55  # Start older
        char["children"] = [
            {"name": "Ada", "age": 20, "species": "human", "manifested": True, "tier": 1},
        ]

        aging = AgingEngine()
        family = FamilyEngine()
        died = False

        for year in range(50):  # Up to age 105
            events = aging.apply_yearly_aging(char, rng)
            family.check_family_events(char, {}, rng)

            for e in events:
                if e.mechanical.get("death"):
                    died = True
                    break
            if died:
                break

        # Should eventually die
        self.assertTrue(died, f"Character survived to age {char['age']}")
        self.assertGreater(char["age"], 55)

    def test_descendant_creation(self):
        rng = random.Random(42)
        parent = _make_test_character(42)
        parent["age"] = 70
        parent["children"] = [
            {"name": "Ada", "age": 25, "species": "human", "manifested": True,
             "tier": 2, "primary_category": "cognitive"},
        ]
        parent["relationships"] = {
            "npc1": {"standing": 3, "state": "loyal"},
            "npc2": {"standing": 0, "state": "neutral"},
        }
        parent["resources"] = {"cu": 1000, "scrip": 500}

        family = FamilyEngine()
        descendant = family.create_descendant(parent, {}, rng)

        self.assertEqual(descendant["name"], "Ada")
        self.assertEqual(descendant["age"], 25)
        self.assertIn("Elena", descendant["lineage"])
        self.assertEqual(descendant["inherited_resources"]["cu"], 500)
        self.assertIn("npc1", descendant["inherited_relationships"])


class TestProgressionPersistence(unittest.TestCase):
    """Test that progression state serializes correctly."""

    def test_all_progression_state_is_dict_serializable(self):
        """All progression state should be plain dicts (JSON-safe)."""
        import json
        char = _make_test_character(42)

        # Apply various progression
        TacticalProgression(char).log_power_use("p1", "kinetic")
        SkillProgression(char).log_skill_use("melee")
        RelationshipProgression(char).update_standing("npc1", 1)
        FactionProgression(char).update_standing("f1", 2)
        ResourceProgression(char).add_resource("cu", 100)
        CorruptionEngine().apply_corruption(char, 0.5, "test")

        # Should serialize cleanly
        serialized = json.dumps(char, default=str)
        loaded = json.loads(serialized)
        self.assertEqual(loaded["name"], "Elena")
        self.assertIn("power_use_counts", loaded)
        self.assertIn("skill_use_counts", loaded)
        self.assertIn("relationships", loaded)
        self.assertIn("faction_standings", loaded)


if __name__ == "__main__":
    unittest.main()
