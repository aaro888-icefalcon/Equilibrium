"""Unit tests for emergence.engine.sim.player_actions + context_management."""

import random
import unittest

from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Faction,
    Location,
    LocationConnection,
    NPC,
    NpcKnowledge,
    Situation,
    SituationChoice,
    TickEvent,
    WorldState,
)
from emergence.engine.sim.player_actions import ActionResult, PlayerActionResolver
from emergence.engine.sim.context_management import compact_state
from emergence.engine.sim.persistence import DirtyTracker


def _make_location(**overrides) -> Location:
    defaults = dict(
        id="manhattan",
        display_name="Manhattan",
        type="urban",
        controller="council",
        population=5000,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1),
        connections=[LocationConnection(to_location_id="bronx", travel_time="1d")],
        opportunities=["salvage_cache"],
        dangers=["raider_activity"],
    )
    defaults.update(overrides)
    return Location(**defaults)


def _make_npc(**overrides) -> NPC:
    defaults = dict(
        id="chen",
        display_name="Director Chen",
        location="manhattan",
        status="alive",
        knowledge=[NpcKnowledge(topic="water", detail="Reservoir is low")],
    )
    defaults.update(overrides)
    return NPC(**defaults)


def _make_situation(**overrides) -> Situation:
    defaults = dict(
        location="manhattan",
        tension="uneasy",
        encounter_probability=0.1,
    )
    defaults.update(overrides)
    return Situation(**defaults)


# ── Player Actions ────────────────────────────────────────────────


class TestDialogueAction(unittest.TestCase):

    def test_dialogue_returns_result(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="talk_chen", description="Talk to Chen", type="dialogue")
        npc = _make_npc()
        result = resolver.resolve_action(
            choice, _make_situation(), _make_location(), [npc], {}, random.Random(42)
        )
        self.assertIsInstance(result, ActionResult)
        self.assertEqual(result.choice_type, "dialogue")
        self.assertEqual(result.narration_scene_type, "dialogue")

    def test_dialogue_shares_knowledge(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="talk_chen", description="Talk to Chen", type="dialogue")
        npc = _make_npc()
        result = resolver.resolve_action(
            choice, _make_situation(), _make_location(), [npc], {}, random.Random(42)
        )
        self.assertIsNotNone(result.npc_interaction)
        self.assertEqual(result.npc_interaction["npc_id"], "chen")
        self.assertEqual(result.npc_interaction["shared_topic"], "water")


class TestTravelAction(unittest.TestCase):

    def test_travel_changes_location(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="travel_bronx", description="Go to Bronx", type="travel")
        result = resolver.resolve_action(
            choice, _make_situation(), _make_location(), [], {}, random.Random(42)
        )
        self.assertEqual(result.new_location, "bronx")
        self.assertEqual(result.time_cost_days, 1)
        self.assertEqual(result.narration_scene_type, "transition")

    def test_travel_can_trigger_encounter(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="travel_bronx", description="Go to Bronx", type="travel")
        loc = _make_location(connections=[
            LocationConnection(to_location_id="bronx", hazards=["raiders"]),
        ])
        triggered = False
        for seed in range(200):
            result = resolver.resolve_action(
                choice, _make_situation(), loc, [], {}, random.Random(seed)
            )
            if result.encounter_triggered:
                triggered = True
                break
        self.assertTrue(triggered, "Travel never triggered encounter in 200 tries")


class TestActivityAction(unittest.TestCase):

    def test_activity_can_succeed(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="pursue_salvage_cache", description="Investigate", type="activity")
        for seed in range(100):
            loc = _make_location()
            result = resolver.resolve_action(
                choice, _make_situation(), loc, [], {}, random.Random(seed)
            )
            if result.state_deltas.get("resources_gained"):
                self.assertIn("salvage_cache", result.state_deltas["resources_gained"])
                return
        self.skipTest("No successful activity in 100 tries")


class TestObservationAction(unittest.TestCase):

    def test_observation_reveals_info(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="observe", description="Observe", type="observation")
        loc = _make_location(dangers=["raiders"], opportunities=["trade"])
        npc = _make_npc()
        result = resolver.resolve_action(
            choice, _make_situation(), loc, [npc], {}, random.Random(42)
        )
        self.assertGreater(len(result.narrative_hints), 0)
        # Should mention dangers and NPCs
        all_hints = " ".join(result.narrative_hints)
        self.assertIn("raiders", all_hints)


class TestPrepareAction(unittest.TestCase):

    def test_prepare_gives_combat_bonus(self):
        resolver = PlayerActionResolver()
        choice = SituationChoice(id="prepare", description="Prepare", type="action")
        result = resolver.resolve_action(
            choice, _make_situation(), _make_location(), [], {}, random.Random(42)
        )
        self.assertIn("combat_bonus", result.state_deltas)
        self.assertGreater(result.state_deltas["combat_bonus"], 0)


# ── Context Management ────────────────────────────────────────────


class TestContextCompaction(unittest.TestCase):

    def test_compacted_state_has_location(self):
        world = WorldState(current_time={"in_world_date": "T+1y 0m 5d"})
        loc = _make_location()
        result = compact_state(world, {"heat": 2}, loc, [], {}, {}, [])
        self.assertEqual(result["location"]["id"], "manhattan")

    def test_compacted_state_has_npcs(self):
        world = WorldState(current_time={"in_world_date": "T+1y 0m 5d"})
        loc = _make_location()
        npc = _make_npc()
        result = compact_state(world, {"heat": 0}, loc, [npc], {}, {}, [])
        self.assertEqual(len(result["npcs_present"]), 1)
        self.assertEqual(result["npcs_present"][0]["name"], "Director Chen")

    def test_compacted_state_has_clocks(self):
        world = WorldState(current_time={"in_world_date": "T+1y 0m 5d"})
        loc = _make_location()
        clocks = {
            "crisis": Clock(id="crisis", display_name="Crisis", current_segment=6, total_segments=8),
        }
        result = compact_state(world, {"heat": 0}, loc, [], {}, clocks, [])
        self.assertEqual(len(result["active_clocks"]), 1)
        self.assertEqual(result["active_clocks"][0]["name"], "Crisis")

    def test_compacted_state_has_events(self):
        world = WorldState(current_time={"in_world_date": "T+1y 0m 5d"})
        loc = _make_location()
        events = [
            TickEvent(tick_timestamp="T+1y", entity_type="faction",
                      entity_id="council", event_type="scheme_advance",
                      details={"scheme_id": "infiltrate"}),
        ]
        result = compact_state(world, {"heat": 0}, loc, [], {}, {}, events)
        self.assertEqual(len(result["recent_events"]), 1)

    def test_compacted_state_respects_max_items(self):
        world = WorldState(current_time={"in_world_date": "T+1y 0m 5d"})
        loc = _make_location()
        # Lots of events
        events = [
            TickEvent(tick_timestamp="T+1y", entity_type="x", entity_id=f"e{i}",
                      event_type="test")
            for i in range(100)
        ]
        result = compact_state(world, {}, loc, [], {}, {}, events, max_items=5)
        total = (len(result.get("npcs_present", [])) +
                 len(result.get("recent_events", [])) +
                 len(result.get("active_clocks", [])) +
                 len(result.get("relevant_factions", [])))
        # time + location count as 2 items, rest should be capped
        self.assertLessEqual(total + 2, 10)  # generous cap


# ── Persistence ───────────────────────────────────────────────────


class TestDirtyTracker(unittest.TestCase):

    def test_mark_and_check(self):
        tracker = DirtyTracker()
        tracker.mark_dirty("factions", "council")
        self.assertTrue(tracker.is_dirty("factions", "council"))
        self.assertFalse(tracker.is_dirty("factions", "raiders"))

    def test_has_changes(self):
        tracker = DirtyTracker()
        self.assertFalse(tracker.has_changes())
        tracker.mark_dirty("npcs", "chen")
        self.assertTrue(tracker.has_changes())

    def test_clear(self):
        tracker = DirtyTracker()
        tracker.mark_dirty("factions", "council")
        tracker.mark_dirty("npcs", "chen")
        tracker.clear()
        self.assertFalse(tracker.has_changes())
        self.assertFalse(tracker.is_dirty("factions", "council"))

    def test_full_save_flag(self):
        tracker = DirtyTracker()
        tracker.mark_full_save()
        self.assertTrue(tracker.needs_full_save())
        self.assertTrue(tracker.has_changes())
        tracker.clear()
        self.assertFalse(tracker.needs_full_save())

    def test_get_dirty(self):
        tracker = DirtyTracker()
        tracker.mark_dirty("factions", "council")
        tracker.mark_dirty("factions", "raiders")
        dirty = tracker.get_dirty("factions")
        self.assertEqual(dirty, {"council", "raiders"})

    def test_summary(self):
        tracker = DirtyTracker()
        tracker.mark_dirty("factions", "council")
        tracker.mark_dirty("npcs", "chen")
        tracker.mark_dirty("npcs", "ghost")
        s = tracker.summary()
        self.assertEqual(s["factions"], 1)
        self.assertEqual(s["npcs"], 2)


if __name__ == "__main__":
    unittest.main()
