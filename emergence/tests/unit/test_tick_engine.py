"""Unit tests for emergence.engine.sim.tick_engine — daily/seasonal tick orchestrator."""

import random
import unittest

from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Faction,
    FactionRelationship,
    FactionTerritory,
    Location,
    NPC,
    WorldState,
)
from emergence.engine.sim.tick_engine import TickEngine


def _make_world() -> WorldState:
    return WorldState(current_time={
        "in_world_date": "T+1y 0m 0d",
        "onset_date_real": "2025-01-01",
        "year": 1,
        "day_count": 0,
    })


def _make_faction(fid="council") -> Faction:
    return Faction(
        id=fid,
        display_name=f"Faction {fid}",
        territory=FactionTerritory(primary_region="Manhattan"),
        resources={"military": 100},
    )


def _make_npc(nid="npc1", location="loc1") -> NPC:
    return NPC(id=nid, display_name=f"NPC {nid}", location=location, status="alive")


def _make_location(lid="loc1") -> Location:
    return Location(
        id=lid, display_name=f"Location {lid}",
        controller="council", population=1000,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1),
    )


def _make_clock(cid="clock1") -> Clock:
    return Clock(
        id=cid, display_name=f"Clock {cid}",
        current_segment=2, total_segments=8,
        advance_conditions=[{"type": "always"}],
        advance_rate={"probability": 0.5},
    )


class TestDailyTick(unittest.TestCase):

    def test_time_advances(self):
        engine = TickEngine()
        world = _make_world()
        events = engine.run_daily_tick(
            world, {}, {}, {}, {}, None, random.Random(42)
        )
        self.assertEqual(world.current_time["day_count"], 1)
        self.assertEqual(world.current_time["year"], 1)

    def test_multiple_ticks_advance_correctly(self):
        engine = TickEngine()
        world = _make_world()
        for _ in range(365):
            engine.run_daily_tick(world, {}, {}, {}, {}, None, random.Random(42))
        self.assertEqual(world.current_time["day_count"], 365)
        self.assertEqual(world.current_time["year"], 2)

    def test_events_produced(self):
        engine = TickEngine()
        world = _make_world()
        factions = {"council": _make_faction()}
        npcs = {"npc1": _make_npc()}
        locations = {"loc1": _make_location()}
        clocks = {"clock1": _make_clock()}

        total_events = 0
        for i in range(30):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, random.Random(i)
            )
            total_events += len(events)
        self.assertGreater(total_events, 0, "Expected some events in 30 ticks")

    def test_clock_advances_over_time(self):
        engine = TickEngine()
        world = _make_world()
        clock = _make_clock(cid="test_clock")
        clock.advance_rate = {"probability": 1.0}
        clocks = {"test_clock": clock}

        initial = clock.current_segment
        for i in range(30):
            engine.run_daily_tick(world, {}, {}, {}, clocks, None, random.Random(i))
        self.assertGreater(clock.current_segment, initial)

    def test_npc_presence_synced(self):
        engine = TickEngine()
        world = _make_world()
        npc = _make_npc(nid="chen", location="manhattan")
        loc = _make_location(lid="manhattan")
        engine.run_daily_tick(
            world, {}, {"chen": npc}, {"manhattan": loc}, {}, None, random.Random(42)
        )
        self.assertIn("chen", loc.npcs_present)


class TestSeasonalTick(unittest.TestCase):

    def test_season_changes_at_90_days(self):
        engine = TickEngine()
        world = _make_world()
        loc = _make_location()
        locations = {"loc1": loc}

        # Run to day 90
        for i in range(90):
            events = engine.run_daily_tick(
                world, {}, {}, locations, {}, None, random.Random(i)
            )

        season_events = [e for e in events if e.event_type == "season_change"]
        self.assertEqual(len(season_events), 1)

    def test_all_four_seasons_cycle(self):
        engine = TickEngine()
        world = _make_world()
        loc = _make_location()
        locations = {"loc1": loc}

        seasons_seen = set()
        for i in range(360):
            events = engine.run_daily_tick(
                world, {}, {}, locations, {}, None, random.Random(i)
            )
            for e in events:
                if e.event_type == "season_change":
                    seasons_seen.add(e.details["season"])
        self.assertEqual(seasons_seen, {"spring", "summer", "autumn", "winter"})


class TestTickDeterminism(unittest.TestCase):

    def test_same_seed_same_events(self):
        def run_30_days(seed):
            engine = TickEngine()
            world = _make_world()
            factions = {"council": _make_faction()}
            npcs = {"npc1": _make_npc()}
            locations = {"loc1": _make_location()}
            clocks = {"clock1": _make_clock()}
            all_events = []
            rng = random.Random(seed)
            for _ in range(30):
                events = engine.run_daily_tick(
                    world, factions, npcs, locations, clocks, None, rng
                )
                all_events.extend(events)
            return [(e.entity_id, e.event_type) for e in all_events]

        run1 = run_30_days(999)
        run2 = run_30_days(999)
        self.assertEqual(run1, run2)


if __name__ == "__main__":
    unittest.main()
