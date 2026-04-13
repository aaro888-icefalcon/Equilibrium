"""Unit tests for emergence.engine.sim.npc_behavior — NPC behavior engine."""

import random
import unittest

from emergence.engine.schemas.world import (
    NPC,
    NpcMemory,
    NpcRelationshipState,
    TickEvent,
)
from emergence.engine.sim.npc_behavior import NpcBehaviorEngine


def _make_npc(**overrides) -> NPC:
    defaults = dict(
        id="director_chen",
        display_name="Director Chen",
        location="manhattan_city_hall",
        status="alive",
    )
    defaults.update(overrides)
    return NPC(**defaults)


class TestMemoryDecay(unittest.TestCase):

    def test_memory_decays(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(memory=[
            NpcMemory(date="T+1y 0m 1d", event="battle", emotional_weight=5, decay_rate=0.5),
        ])
        engine._decay_memories(npc)
        self.assertAlmostEqual(npc.memory[0].emotional_weight, 4.5)

    def test_memory_removed_when_forgotten(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(memory=[
            NpcMemory(date="T+1y 0m 1d", event="trivial", emotional_weight=0.05, decay_rate=0.1),
        ])
        engine._decay_memories(npc)
        self.assertEqual(len(npc.memory), 0)

    def test_memory_floor_at_zero(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(memory=[
            NpcMemory(date="T+1y 0m 1d", event="old", emotional_weight=0.01, decay_rate=1.0),
        ])
        engine._decay_memories(npc)
        # Weight should floor at 0, then be removed
        self.assertEqual(len(npc.memory), 0)

    def test_strong_memory_persists(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(memory=[
            NpcMemory(date="T+1y 0m 1d", event="trauma", emotional_weight=10, decay_rate=0.01),
        ])
        # Run many ticks
        for _ in range(100):
            engine._decay_memories(npc)
        self.assertEqual(len(npc.memory), 1)
        self.assertGreater(npc.memory[0].emotional_weight, 0)


class TestRelationshipDrift(unittest.TestCase):

    def test_drift_toward_zero(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(relationships={
            "player": NpcRelationshipState(standing=3),
        })
        # Run many ticks until drift occurs
        for seed in range(500):
            events = engine._drift_relationships(npc, random.Random(seed), "T+1y 0m 1d")
            if events:
                self.assertEqual(npc.relationships["player"].standing, 2)
                return
        self.skipTest("No drift in 500 ticks")

    def test_no_drift_at_low_standing(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(relationships={
            "player": NpcRelationshipState(standing=1),
        })
        # Standing 1 is below threshold (abs >= 2), so no drift
        for seed in range(200):
            engine._drift_relationships(npc, random.Random(seed), "T+1y 0m 1d")
        self.assertEqual(npc.relationships["player"].standing, 1)

    def test_negative_drift_toward_zero(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(relationships={
            "player": NpcRelationshipState(standing=-3),
        })
        for seed in range(500):
            events = engine._drift_relationships(npc, random.Random(seed), "T+1y 0m 1d")
            if events:
                self.assertEqual(npc.relationships["player"].standing, -2)
                return
        self.skipTest("No drift in 500 ticks")


class TestScheduleEvaluation(unittest.TestCase):

    def test_patrol_movement(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(
            location="loc_a",
            schedule={"patrol": ["loc_a", "loc_b", "loc_c"]},
        )
        # Day 1 should be loc_b
        event = engine._evaluate_schedule(npc, {"day_count": 1}, "T+1y 0m 1d")
        self.assertIsNotNone(event)
        self.assertEqual(npc.location, "loc_b")
        self.assertEqual(event.event_type, "npc_movement")

    def test_no_movement_when_at_correct_location(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(
            location="loc_a",
            schedule={"patrol": ["loc_a", "loc_b"]},
        )
        # Day 0 → loc_a, already there
        event = engine._evaluate_schedule(npc, {"day_count": 0}, "T+1y 0m 0d")
        self.assertIsNone(event)

    def test_default_schedule(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(
            location="somewhere_else",
            schedule={"default": "home_base"},
        )
        event = engine._evaluate_schedule(npc, {}, "T+1y 0m 1d")
        self.assertIsNotNone(event)
        self.assertEqual(npc.location, "home_base")


class TestNpcActions(unittest.TestCase):

    def test_concern_addressed(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(current_concerns=["water shortage"])
        for seed in range(500):
            npc_copy = _make_npc(current_concerns=["water shortage"])
            events = engine._take_action(npc_copy, {}, random.Random(seed), "T+1y 0m 1d")
            if events and events[0].event_type == "concern_addressed":
                self.assertEqual(events[0].details["concern"], "water shortage")
                return
        self.skipTest("No concern action in 500 ticks")

    def test_goal_pursuit(self):
        engine = NpcBehaviorEngine()
        for seed in range(200):
            npc = _make_npc(goals=[
                {"id": "find_ally", "description": "Find allies", "progress": 3}
            ])
            events = engine._take_action(npc, {}, random.Random(seed), "T+1y 0m 1d")
            goal_events = [e for e in events if e.event_type == "goal_pursuit"]
            if goal_events:
                self.assertGreaterEqual(npc.goals[0]["progress"], 3)
                return
        self.skipTest("No goal pursuit in 200 ticks")


class TestNpcDisplacement(unittest.TestCase):

    def test_displace_changes_location_and_status(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(location="manhattan")
        event = engine.displace_npc(npc, "bronx", "faction_conflict", "T+1y 0m 1d")
        self.assertEqual(npc.location, "bronx")
        self.assertEqual(npc.status, "displaced")
        self.assertTrue(any("displaced" in c for c in npc.current_concerns))
        self.assertEqual(event.event_type, "npc_displaced")


class TestNpcRelationshipUpdate(unittest.TestCase):

    def test_relationship_created_if_missing(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc()
        engine.update_relationship(npc, "player", 1, "helped", "T+1y 0m 1d")
        self.assertIn("player", npc.relationships)
        self.assertEqual(npc.relationships["player"].standing, 1)

    def test_relationship_clamped(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(relationships={
            "player": NpcRelationshipState(standing=3),
        })
        engine.update_relationship(npc, "player", 5, "saved_life", "T+1y 0m 1d")
        self.assertEqual(npc.relationships["player"].standing, 3)

    def test_relationship_history_tracked(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc()
        engine.update_relationship(npc, "player", -1, "betrayed", "T+1y 0m 1d")
        self.assertEqual(len(npc.relationships["player"].history), 1)
        self.assertEqual(npc.relationships["player"].history[0]["reason"], "betrayed")


class TestDeadNpcSkipped(unittest.TestCase):

    def test_dead_npc_produces_no_events(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc(status="dead")
        events = engine.evaluate_npc_tick(npc, {}, random.Random(42), "T+1y 0m 1d")
        self.assertEqual(events, [])


class TestAddMemory(unittest.TestCase):

    def test_add_memory(self):
        engine = NpcBehaviorEngine()
        npc = _make_npc()
        engine.add_memory(npc, "witnessed battle", "T+1y 0m 5d", emotional_weight=7)
        self.assertEqual(len(npc.memory), 1)
        self.assertEqual(npc.memory[0].event, "witnessed battle")
        self.assertEqual(npc.memory[0].emotional_weight, 7)


if __name__ == "__main__":
    unittest.main()
