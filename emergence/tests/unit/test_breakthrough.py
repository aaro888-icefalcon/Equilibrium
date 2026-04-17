"""Unit tests for breakthrough mechanics."""

import random
import unittest

from emergence.engine.progression.breakthrough import (
    BreakthroughEngine,
    BreakthroughTrigger,
    BreakthroughResult,
    BREAKTHROUGH_MARKS,
    MARK_POOLS,
)


class TestBreakthroughTriggers(unittest.TestCase):

    def setUp(self):
        self.engine = BreakthroughEngine()
        self.char = {
            "tier": 2,
            "tier_ceiling": 10,
            "primary_category": "physical_kinetic",
            "attributes": {"will": 8, "might": 8, "insight": 8},
            "powers": ["p1", "p2"],
        }
        self.world = {"current_time": {"day_count": 1000}}

    def test_near_death_triggers(self):
        event = {"type": "near_death"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 1)

    def test_near_death_blocked_at_ceiling(self):
        self.char["tier"] = 10
        self.char["tier_ceiling"] = 10
        event = {"type": "near_death"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNone(trigger)

    def test_mentorship_triggers(self):
        event = {
            "type": "mentorship_complete",
            "training_days": 90,
            "mentor_tier": 4,
            "mentor_category": "physical_kinetic",
            "mentor_name": "Sensei",
        }
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 2)

    def test_mentorship_requires_90_days(self):
        event = {
            "type": "mentorship_complete",
            "training_days": 89,
            "mentor_tier": 4,
            "mentor_category": "physical_kinetic",
        }
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNone(trigger)

    def test_eldritch_exposure_triggers(self):
        event = {"type": "eldritch_exposure", "cumulative_days": 3}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 3)

    def test_eldritch_entity_contact_triggers(self):
        event = {"type": "eldritch_exposure", "entity_contact": True, "cumulative_days": 0}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)

    def test_substance_triggers(self):
        event = {"type": "substance_ingestion", "substance_id": "catskill_mushroom"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 4)

    def test_ritual_triggers(self):
        event = {
            "type": "ritual_complete",
            "participant_count": 3,
            "highest_tier": 4,
            "duration_days": 1,
        }
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 5)

    def test_traumatic_loss_triggers(self):
        event = {"type": "npc_death", "standing_with_player": 2, "npc_name": "Elena"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 6)

    def test_traumatic_loss_requires_standing_2(self):
        event = {"type": "npc_death", "standing_with_player": 1}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNone(trigger)

    def test_sustained_crisis_triggers(self):
        event = {"type": "sustained_crisis", "track_value": 3, "duration_days": 14}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 7)

    def test_sacrifice_triggers(self):
        event = {"type": "sacrifice_complete", "sacrifice_type": "holding_burned"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNotNone(trigger)
        self.assertEqual(trigger.condition_id, 8)

    def test_recovery_blocks_triggers(self):
        self.char["breakthrough_recovery_days"] = 5
        event = {"type": "near_death"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNone(trigger)

    def test_unrecognized_event_no_trigger(self):
        event = {"type": "fishing"}
        trigger = self.engine.check_triggers(self.char, self.world, event)
        self.assertIsNone(trigger)


class TestBreakthroughResolution(unittest.TestCase):

    def setUp(self):
        self.engine = BreakthroughEngine()
        self.char = {
            "tier": 2,
            "tier_ceiling": 10,
            "primary_category": "physical_kinetic",
            "attributes": {"will": 8, "might": 8, "insight": 8},
            "powers": ["p1", "p2"],
            "breakthrough_marks": [],
        }

    def test_near_death_success(self):
        rng = random.Random(42)
        trigger = BreakthroughTrigger(1, "near_death")
        result = self.engine.resolve_breakthrough(self.char, trigger, rng)
        # With seed 42 and good stats, may or may not succeed
        self.assertIsInstance(result, BreakthroughResult)

    def test_eldritch_always_succeeds(self):
        trigger = BreakthroughTrigger(3, "eldritch_exposure")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertTrue(result.success)
        self.assertEqual(result.bt_type, "breadth")
        self.assertGreaterEqual(result.corruption_gained, 1)

    def test_sacrifice_always_succeeds(self):
        trigger = BreakthroughTrigger(8, "sacrifice")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertTrue(result.success)
        self.assertIn(result.bt_type, ["depth", "breadth"])

    def test_tier_increments(self):
        trigger = BreakthroughTrigger(3, "eldritch_exposure")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertEqual(result.new_tier, 3)

    def test_tier_capped_at_10(self):
        self.char["tier"] = 10
        trigger = BreakthroughTrigger(3, "eldritch_exposure")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertEqual(result.new_tier, 10)

    def test_mark_assigned(self):
        trigger = BreakthroughTrigger(3, "eldritch_exposure")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertIn(result.mark_id, BREAKTHROUGH_MARKS)

    def test_recovery_period(self):
        trigger = BreakthroughTrigger(8, "sacrifice")
        result = self.engine.resolve_breakthrough(self.char, trigger, random.Random(1))
        self.assertEqual(result.recovery_days, 7)


class TestBreakthroughApplication(unittest.TestCase):

    def setUp(self):
        self.engine = BreakthroughEngine()
        self.char = {
            "tier": 2,
            "tier_ceiling": 10,
            "primary_category": "physical_kinetic",
            "attributes": {"will": 8, "might": 8, "insight": 8},
            "powers": ["p1"],
            "breakthrough_marks": [],
            "corruption": 0,
        }

    def test_apply_success(self):
        result = BreakthroughResult(
            success=True, new_tier=3, mark_id="P1",
            mark_name="Densification", bt_type="depth",
            recovery_days=7, corruption_gained=0,
        )
        self.engine.apply_breakthrough(self.char, result)
        self.assertEqual(self.char["tier"], 3)
        self.assertIn("P1", self.char["breakthrough_marks"])
        self.assertEqual(self.char["breakthrough_recovery_days"], 7)

    def test_apply_updates_ceiling(self):
        self.char["tier_ceiling"] = 2
        result = BreakthroughResult(
            success=True, new_tier=3, mark_id="P1",
            mark_name="Densification", bt_type="depth",
        )
        self.engine.apply_breakthrough(self.char, result)
        self.assertEqual(self.char["tier_ceiling"], 3)

    def test_apply_failure_only_corruption(self):
        result = BreakthroughResult(
            success=False, corruption_gained=1,
            side_effects=["harm tier 2"],
        )
        self.engine.apply_breakthrough(self.char, result)
        self.assertEqual(self.char["tier"], 2)  # Unchanged
        self.assertEqual(self.char["corruption"], 1)

    def test_apply_records_history(self):
        result = BreakthroughResult(
            success=True, new_tier=3, mark_id="P1",
            mark_name="Densification", bt_type="depth",
        )
        self.engine.apply_breakthrough(self.char, result)
        history = self.char["breakthrough_history"]
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["tier_reached"], 3)


class TestMarkCatalog(unittest.TestCase):

    def test_24_marks_defined(self):
        self.assertGreaterEqual(len(BREAKTHROUGH_MARKS), 24)

    def test_all_pools_have_marks(self):
        for cat, pool in MARK_POOLS.items():
            # Cognitive carries both the old M-prefix (perceptual/mental)
            # and A-prefix (auratic) marks since those V1 categories merged.
            expected = 8 if cat == "cognitive" else 4
            self.assertEqual(
                len(pool), expected,
                f"Pool {cat} should have {expected} marks",
            )
            for mark_id in pool:
                self.assertIn(mark_id, BREAKTHROUGH_MARKS)

    def test_paradoxic_marks_have_corruption(self):
        for mark_id in MARK_POOLS["paradoxic"]:
            effects = BREAKTHROUGH_MARKS[mark_id]["effects"]
            self.assertGreaterEqual(
                effects.get("corruption", 0), 1,
                f"Paradoxic mark {mark_id} should include corruption",
            )


if __name__ == "__main__":
    unittest.main()
