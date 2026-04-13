"""Unit tests for emergence.engine.sim.situation_generator — situation generation."""

import random
import unittest

from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Location,
    LocationConnection,
    NPC,
    NpcRelationshipState,
    Situation,
    SituationChoice,
    TickEvent,
)
from emergence.engine.sim.situation_generator import (
    SituationGenerator,
    _assess_tension,
    _encounter_probability,
)


def _make_location(**overrides) -> Location:
    defaults = dict(
        id="manhattan_lower",
        display_name="Lower Manhattan",
        controller="council",
        population=5000,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1),
        connections=[
            LocationConnection(to_location_id="manhattan_upper"),
        ],
        opportunities=["salvage_cache"],
    )
    defaults.update(overrides)
    return Location(**defaults)


def _make_npc(**overrides) -> NPC:
    defaults = dict(
        id="chen",
        display_name="Director Chen",
        location="manhattan_lower",
        status="alive",
    )
    defaults.update(overrides)
    return NPC(**defaults)


class TestTensionAssessment(unittest.TestCase):

    def test_calm_location(self):
        loc = _make_location(
            ambient=AmbientConditions(threat_level=0),
            dangers=[],
        )
        tension = _assess_tension(loc, [], [], {})
        self.assertEqual(tension, "calm")

    def test_threat_level_raises_tension(self):
        loc = _make_location(
            ambient=AmbientConditions(threat_level=4),
            dangers=["raiders"],
        )
        tension = _assess_tension(loc, [], [], {})
        self.assertIn(tension, ("tense", "volatile", "critical"))

    def test_npc_conflict_raises_tension(self):
        npc1 = _make_npc(id="npc1", relationships={
            "npc2": NpcRelationshipState(standing=-3),
        })
        npc2 = _make_npc(id="npc2")
        loc = _make_location(ambient=AmbientConditions(threat_level=2))
        tension = _assess_tension(loc, [npc1, npc2], [], {})
        self.assertIn(tension, ("uneasy", "tense", "volatile", "critical"))

    def test_near_complete_clock_raises_tension(self):
        loc = _make_location(
            ambient=AmbientConditions(threat_level=1),
            dangers=[],
        )
        clocks = {
            "crisis": Clock(id="crisis", current_segment=7, total_segments=8),
            "famine": Clock(id="famine", current_segment=6, total_segments=8),
        }
        tension = _assess_tension(loc, [], [], clocks)
        self.assertNotEqual(tension, "calm")

    def test_recent_events_raise_tension(self):
        loc = _make_location(
            ambient=AmbientConditions(threat_level=0),
            dangers=[],
        )
        events = [
            TickEvent(tick_timestamp="T+1y", entity_type="faction",
                      entity_id="x", event_type="diplomatic_escalation"),
            TickEvent(tick_timestamp="T+1y", entity_type="faction",
                      entity_id="x", event_type="territorial_contest"),
        ]
        tension = _assess_tension(loc, [], events, {})
        self.assertNotEqual(tension, "calm")


class TestEncounterProbability(unittest.TestCase):

    def test_calm_low_probability(self):
        loc = _make_location(ambient=AmbientConditions(threat_level=0))
        prob = _encounter_probability(loc, "calm", player_heat=0)
        self.assertLess(prob, 0.1)

    def test_critical_high_probability(self):
        loc = _make_location(ambient=AmbientConditions(threat_level=3))
        prob = _encounter_probability(loc, "critical", player_heat=5)
        self.assertGreater(prob, 0.3)

    def test_heat_increases_probability(self):
        loc = _make_location(ambient=AmbientConditions(threat_level=0))
        p_no_heat = _encounter_probability(loc, "uneasy", player_heat=0)
        p_high_heat = _encounter_probability(loc, "uneasy", player_heat=5)
        self.assertGreater(p_high_heat, p_no_heat)

    def test_probability_capped_at_80(self):
        loc = _make_location(ambient=AmbientConditions(threat_level=5))
        prob = _encounter_probability(loc, "critical", player_heat=10)
        self.assertLessEqual(prob, 0.8)


class TestSituationGeneration(unittest.TestCase):

    def test_produces_situation(self):
        gen = SituationGenerator()
        loc = _make_location()
        npc = _make_npc()
        situation = gen.generate_situation(
            {"tick_timestamp": "T+1y 0m 5d"},
            {"heat": 0},
            loc, [npc], [], {}, random.Random(42),
        )
        self.assertIsInstance(situation, Situation)
        self.assertEqual(situation.location, "manhattan_lower")
        self.assertIn("chen", situation.present_npcs)

    def test_choices_include_observation(self):
        gen = SituationGenerator()
        loc = _make_location()
        situation = gen.generate_situation(
            {}, {"heat": 0}, loc, [], [], {}, random.Random(42),
        )
        choice_ids = [c.id for c in situation.player_choices]
        self.assertIn("observe", choice_ids)

    def test_choices_include_dialogue(self):
        gen = SituationGenerator()
        loc = _make_location()
        npc = _make_npc()
        situation = gen.generate_situation(
            {}, {"heat": 0}, loc, [npc], [], {}, random.Random(42),
        )
        dialogue_choices = [c for c in situation.player_choices if c.type == "dialogue"]
        self.assertGreater(len(dialogue_choices), 0)

    def test_choices_include_travel(self):
        gen = SituationGenerator()
        loc = _make_location()
        situation = gen.generate_situation(
            {}, {"heat": 0}, loc, [], [], {}, random.Random(42),
        )
        travel_choices = [c for c in situation.player_choices if c.type == "travel"]
        self.assertGreater(len(travel_choices), 0)

    def test_choices_capped_at_6(self):
        gen = SituationGenerator()
        loc = _make_location(
            connections=[
                LocationConnection(to_location_id=f"loc{i}")
                for i in range(5)
            ],
            opportunities=["a", "b", "c"],
            dangers=["raiders"],
            ambient=AmbientConditions(threat_level=4),
        )
        npcs = [_make_npc(id=f"npc{i}") for i in range(5)]
        situation = gen.generate_situation(
            {}, {"heat": 0}, loc, npcs, [], {}, random.Random(42),
        )
        self.assertLessEqual(len(situation.player_choices), 6)

    def test_encounter_probability_set(self):
        gen = SituationGenerator()
        loc = _make_location(
            ambient=AmbientConditions(threat_level=3),
            dangers=["mutants"],
        )
        situation = gen.generate_situation(
            {}, {"heat": 3}, loc, [], [], {}, random.Random(42),
        )
        self.assertGreater(situation.encounter_probability, 0)

    def test_tension_reflected(self):
        gen = SituationGenerator()
        loc = _make_location(
            ambient=AmbientConditions(threat_level=4),
            dangers=["raiders", "mutants"],
        )
        situation = gen.generate_situation(
            {}, {"heat": 0}, loc, [], [], {}, random.Random(42),
        )
        self.assertIn(situation.tension, ("tense", "volatile", "critical"))


if __name__ == "__main__":
    unittest.main()
