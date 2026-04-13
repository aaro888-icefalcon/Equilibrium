"""Unit tests for emergence.engine.sim.location_dynamics — location dynamics engine."""

import random
import unittest

from emergence.engine.schemas.world import (
    AmbientConditions,
    Location,
    NPC,
    TickEvent,
)
from emergence.engine.sim.location_dynamics import LocationEngine


def _make_location(**overrides) -> Location:
    defaults = dict(
        id="manhattan_lower",
        display_name="Lower Manhattan",
        type="urban",
        region="Manhattan",
        controller="reformed_council",
        population=5000,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1),
    )
    defaults.update(overrides)
    return Location(**defaults)


class TestEconomicShift(unittest.TestCase):

    def test_economic_worsening_with_dangers(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(
                economic_state="sufficient",
                dangers=["raider_activity"],
            )
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            shifts = [e for e in events if e.event_type == "economic_shift"]
            if shifts:
                self.assertEqual(shifts[0].details["from"], "sufficient")
                self.assertEqual(shifts[0].details["to"], "strained")
                return
        self.skipTest("No economic shift in 500 ticks")

    def test_economic_improvement_safe_location(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(
                economic_state="strained",
                dangers=[],
                controller="reformed_council",
            )
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            shifts = [e for e in events if e.event_type == "economic_shift"]
            if shifts and shifts[0].details["direction"] == "improved":
                self.assertEqual(shifts[0].details["to"], "sufficient")
                return
        self.skipTest("No improvement in 500 ticks")

    def test_thriving_cannot_improve_further(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(economic_state="thriving", dangers=[], controller="x")
            engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            # Should never go above thriving
            self.assertIn(loc.economic_state, ["thriving", "sufficient"])


class TestPopulationMigration(unittest.TestCase):

    def test_exodus_during_crisis(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(economic_state="crisis", population=1000)
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            exodus = [e for e in events if e.event_type == "population_exodus"]
            if exodus:
                self.assertLess(loc.population, 1000)
                return
        self.skipTest("No exodus in 500 ticks")

    def test_influx_during_thriving(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(economic_state="thriving", population=1000)
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            influx = [e for e in events if e.event_type == "population_influx"]
            if influx:
                self.assertGreater(loc.population, 1000)
                return
        self.skipTest("No influx in 500 ticks")

    def test_population_never_negative(self):
        engine = LocationEngine()
        loc = _make_location(economic_state="collapsed", population=3)
        for seed in range(500):
            loc.economic_state = "collapsed"
            engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            self.assertGreaterEqual(loc.population, 0)


class TestDangerEscalation(unittest.TestCase):

    def test_threat_level_increases(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(
                ambient=AmbientConditions(threat_level=1),
                dangers=["raiders"],
            )
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            escalations = [e for e in events if e.event_type == "danger_escalation"]
            if escalations:
                self.assertEqual(loc.ambient.threat_level, 2)
                return
        self.skipTest("No danger escalation in 500 ticks")

    def test_threat_level_capped_at_5(self):
        engine = LocationEngine()
        loc = _make_location(
            ambient=AmbientConditions(threat_level=5),
            dangers=["mutants"],
        )
        for seed in range(500):
            loc.ambient.threat_level = 5
            engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            self.assertLessEqual(loc.ambient.threat_level, 5)


class TestOpportunityGeneration(unittest.TestCase):

    def test_opportunity_appears(self):
        engine = LocationEngine()
        for seed in range(500):
            loc = _make_location(opportunities=[])
            events = engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            opps = [e for e in events if e.event_type == "opportunity_appeared"]
            if opps:
                self.assertEqual(len(loc.opportunities), 1)
                return
        self.skipTest("No opportunity in 500 ticks")

    def test_opportunity_capped_at_3(self):
        engine = LocationEngine()
        loc = _make_location(opportunities=["a", "b", "c"])
        for seed in range(500):
            loc.opportunities = ["a", "b", "c"]
            engine.evaluate_location_tick(loc, {}, random.Random(seed), "T+1y 0m 1d")
            self.assertLessEqual(len(loc.opportunities), 3)


class TestNpcPresenceSync(unittest.TestCase):

    def test_sync_updates_presence(self):
        engine = LocationEngine()
        loc1 = _make_location(id="loc1")
        loc2 = _make_location(id="loc2")
        npc1 = NPC(id="npc1", location="loc1", status="alive")
        npc2 = NPC(id="npc2", location="loc2", status="alive")
        npc3 = NPC(id="npc3", location="loc1", status="alive")
        locations = {"loc1": loc1, "loc2": loc2}
        npcs = {"npc1": npc1, "npc2": npc2, "npc3": npc3}
        engine.sync_npc_presence(locations, npcs)
        self.assertEqual(sorted(loc1.npcs_present), ["npc1", "npc3"])
        self.assertEqual(loc2.npcs_present, ["npc2"])

    def test_dead_npcs_excluded(self):
        engine = LocationEngine()
        loc = _make_location(id="loc1")
        npc = NPC(id="npc1", location="loc1", status="dead")
        engine.sync_npc_presence({"loc1": loc}, {"npc1": npc})
        self.assertEqual(loc.npcs_present, [])


class TestControllerChange(unittest.TestCase):

    def test_controller_change(self):
        engine = LocationEngine()
        loc = _make_location(controller="council")
        event = engine.change_controller(loc, "raiders", "military_takeover", "T+1y 0m 1d")
        self.assertEqual(loc.controller, "raiders")
        self.assertEqual(event.event_type, "controller_change")
        self.assertEqual(event.details["from"], "council")
        self.assertEqual(event.details["to"], "raiders")
        self.assertEqual(len(loc.history), 1)


if __name__ == "__main__":
    unittest.main()
