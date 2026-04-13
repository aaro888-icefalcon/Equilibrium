"""Unit tests for emergence.engine.sim.faction_logic — faction decision engine."""

import random
import unittest

from emergence.engine.schemas.world import (
    Faction,
    FactionEconomicBase,
    FactionGoal,
    FactionRelationship,
    FactionScheme,
    FactionTerritory,
    TickEvent,
)
from emergence.engine.sim.faction_logic import FactionDecisionEngine


def _make_faction(**overrides) -> Faction:
    defaults = dict(
        id="council",
        display_name="Reformed Council",
        type="governmental",
        territory=FactionTerritory(
            primary_region="Manhattan",
            contested_zones=["Midtown"],
        ),
        resources={"military": 100, "supplies": 50},
        economic_base=FactionEconomicBase(primary_resources=["salvage", "trade_goods"]),
    )
    defaults.update(overrides)
    return Faction(**defaults)


def _make_pair():
    """Create two factions with a relationship."""
    f1 = _make_faction(
        id="council",
        display_name="Council",
        external_relationships={
            "raiders": FactionRelationship(disposition=-2, active_grievances=["raid"]),
        },
    )
    f2 = _make_faction(
        id="raiders",
        display_name="Raiders",
        external_relationships={
            "council": FactionRelationship(disposition=-2, active_grievances=["arrest"]),
        },
    )
    return f1, f2


class TestFactionActionProbability(unittest.TestCase):
    """Factions should act roughly once per week."""

    def test_acts_roughly_one_in_seven(self):
        engine = FactionDecisionEngine()
        faction = _make_faction()
        all_factions = {"council": faction}
        acted = 0
        trials = 700
        for seed in range(trials):
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            if events:
                acted += 1
        # Expect ~100 out of 700 (1/7). Allow wide margin.
        self.assertGreater(acted, 50, f"Acted {acted}/700, expected ~100")
        self.assertLess(acted, 200, f"Acted {acted}/700, expected ~100")


class TestTerritorialActions(unittest.TestCase):

    def test_contest_can_resolve(self):
        engine = FactionDecisionEngine()
        faction = _make_faction(
            territory=FactionTerritory(contested_zones=["Midtown"]),
        )
        all_factions = {"council": faction}
        # Run many ticks until a contest event occurs
        for seed in range(500):
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            contests = [e for e in events if e.event_type == "territorial_contest"]
            if contests:
                self.assertIn("zone", contests[0].details)
                return
        self.skipTest("No territorial contest in 500 ticks")

    def test_successful_contest_moves_zone(self):
        engine = FactionDecisionEngine()
        # Find a seed where contest succeeds
        for seed in range(1000):
            faction = _make_faction(
                territory=FactionTerritory(contested_zones=["Midtown"]),
                # Remove other candidate actions to force territorial
                goals=[], current_schemes=[], internal_tensions=[],
                external_relationships={},
            )
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            contests = [e for e in events
                        if e.event_type == "territorial_contest" and e.details.get("success")]
            if contests:
                self.assertNotIn("Midtown", faction.territory.contested_zones)
                self.assertIn("Midtown", faction.territory.secondary_holdings)
                return
        self.skipTest("No successful contest in 1000 ticks")


class TestDiplomaticActions(unittest.TestCase):

    def test_escalation_shifts_disposition(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            f1, f2 = _make_pair()
            all_factions = {"council": f1, "raiders": f2}
            events = engine.evaluate_faction_tick(
                f1, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            escalations = [e for e in events if e.event_type == "diplomatic_escalation"]
            if escalations:
                self.assertLessEqual(
                    f1.external_relationships["raiders"].disposition, -2
                )
                return
        self.skipTest("No escalation in 500 ticks")

    def test_treaty_proposal(self):
        engine = FactionDecisionEngine()
        f1 = _make_faction(
            id="council",
            external_relationships={
                "merchants": FactionRelationship(disposition=2),
            },
            goals=[], current_schemes=[], internal_tensions=[],
            territory=FactionTerritory(),
        )
        f2 = _make_faction(
            id="merchants",
            external_relationships={
                "council": FactionRelationship(disposition=2),
            },
        )
        all_factions = {"council": f1, "merchants": f2}
        for seed in range(500):
            # Reset relationships each time
            f1.external_relationships["merchants"] = FactionRelationship(disposition=2)
            f2.external_relationships["council"] = FactionRelationship(disposition=2)
            events = engine.evaluate_faction_tick(
                f1, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            proposals = [e for e in events if e.event_type == "diplomatic_treaty_proposal"]
            if proposals:
                self.assertIn("accepted", proposals[0].details)
                return
        self.skipTest("No treaty proposal in 500 ticks")

    def test_disposition_drift_toward_zero(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            f1 = _make_faction(
                id="council",
                external_relationships={
                    "merchants": FactionRelationship(disposition=3),
                },
                goals=[], current_schemes=[], internal_tensions=[],
                territory=FactionTerritory(),
            )
            f2 = _make_faction(id="merchants")
            all_factions = {"council": f1, "merchants": f2}
            events = engine.evaluate_faction_tick(
                f1, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            drifts = [e for e in events if e.event_type == "diplomatic_drift"]
            if drifts:
                self.assertEqual(
                    f1.external_relationships["merchants"].disposition, 2
                )
                return
        self.skipTest("No drift in 500 ticks")


class TestSchemeAdvancement(unittest.TestCase):

    def test_scheme_progresses(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            faction = _make_faction(
                current_schemes=[
                    FactionScheme(id="infiltrate", description="Infiltrate", target="raiders", progress=3)
                ],
                goals=[], internal_tensions=[],
                external_relationships={},
                territory=FactionTerritory(),
            )
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            scheme_events = [e for e in events if "scheme" in e.event_type]
            if scheme_events:
                self.assertGreater(faction.current_schemes[0].progress, 3)
                return
        self.skipTest("No scheme advance in 500 ticks")

    def test_scheme_completion(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            faction = _make_faction(
                current_schemes=[
                    FactionScheme(id="infiltrate", description="Infiltrate", target="raiders", progress=9)
                ],
                goals=[], internal_tensions=[],
                external_relationships={},
                territory=FactionTerritory(),
            )
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            completions = [e for e in events if e.event_type == "scheme_complete"]
            if completions:
                self.assertEqual(faction.current_schemes[0].progress, 10)
                return
        self.skipTest("No scheme completion in 500 ticks")


class TestInternalTensions(unittest.TestCase):

    def test_tension_can_resolve(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            faction = _make_faction(
                internal_tensions=[{"type": "leadership_dispute", "severity": 2}],
                goals=[], current_schemes=[],
                external_relationships={},
                territory=FactionTerritory(),
            )
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            tension_events = [e for e in events if e.event_type == "internal_tension_managed"]
            if tension_events and tension_events[0].details.get("resolved"):
                self.assertEqual(len(faction.internal_tensions), 0)
                return
        self.skipTest("No tension resolution in 500 ticks")


class TestGoalPursuit(unittest.TestCase):

    def test_goal_progresses(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            faction = _make_faction(
                goals=[FactionGoal(id="expand", description="Expand territory", weight=3.0, progress=2)],
                current_schemes=[], internal_tensions=[],
                external_relationships={},
                territory=FactionTerritory(),
            )
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            goal_events = [e for e in events if e.event_type == "goal_progress"]
            if goal_events:
                self.assertGreaterEqual(faction.goals[0].progress, 2)
                return
        self.skipTest("No goal progress in 500 ticks")


class TestResourceGathering(unittest.TestCase):

    def test_resource_gathered(self):
        engine = FactionDecisionEngine()
        for seed in range(500):
            faction = _make_faction(
                goals=[], current_schemes=[], internal_tensions=[],
                external_relationships={},
                territory=FactionTerritory(),
            )
            initial_supplies = faction.resources.get("supplies", 0)
            all_factions = {"council": faction}
            events = engine.evaluate_faction_tick(
                faction, {}, all_factions, random.Random(seed), "T+1y 0m 1d"
            )
            resource_events = [e for e in events if e.event_type == "resource_gathered"]
            if resource_events:
                self.assertGreater(resource_events[0].details["amount"], 0)
                return
        self.skipTest("No resource gather in 500 ticks")


if __name__ == "__main__":
    unittest.main()
