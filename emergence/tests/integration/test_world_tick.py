"""Integration test: 365 daily ticks on synthetic world."""

import random
import unittest

from emergence.tests.helpers.synthetic_world import make_synthetic_world
from emergence.engine.sim.tick_engine import TickEngine


class TestWorldTick365Days(unittest.TestCase):
    """Synthetic world ticks 365 days without errors."""

    def test_365_days_clean(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(12345)

        all_events = []
        for day in range(365):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, rng
            )
            all_events.extend(events)

        # Should have advanced to year 2
        self.assertEqual(world.current_time["day_count"], 365)
        self.assertEqual(world.current_time["year"], 2)

        # Should have produced many events
        self.assertGreater(len(all_events), 50,
                           f"Only {len(all_events)} events in 365 days")

    def test_clocks_advance(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(42)

        initial_segments = {cid: c.current_segment for cid, c in clocks.items()}
        for _ in range(365):
            engine.run_daily_tick(world, factions, npcs, locations, clocks, None, rng)

        advanced = 0
        for cid, clock in clocks.items():
            if clock.current_segment > initial_segments[cid]:
                advanced += 1
        self.assertGreater(advanced, 0, "No clocks advanced in 365 days")

    def test_factions_act(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(42)

        all_events = []
        for _ in range(365):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, rng
            )
            all_events.extend(events)

        faction_events = [e for e in all_events if e.entity_type == "faction"]
        self.assertGreater(len(faction_events), 10,
                           f"Only {len(faction_events)} faction events in 365 days")

    def test_npcs_move(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(42)

        all_events = []
        for _ in range(365):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, rng
            )
            all_events.extend(events)

        npc_events = [e for e in all_events if e.entity_type == "npc"]
        self.assertGreater(len(npc_events), 5,
                           f"Only {len(npc_events)} NPC events in 365 days")

    def test_locations_update(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(42)

        all_events = []
        for _ in range(365):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, rng
            )
            all_events.extend(events)

        loc_events = [e for e in all_events if e.entity_type == "location"]
        self.assertGreater(len(loc_events), 5,
                           f"Only {len(loc_events)} location events in 365 days")

    def test_seasons_cycle(self):
        world, factions, npcs, locations, clocks = make_synthetic_world()
        engine = TickEngine()
        rng = random.Random(42)

        all_events = []
        for _ in range(365):
            events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, None, rng
            )
            all_events.extend(events)

        season_events = [e for e in all_events if e.event_type == "season_change"]
        self.assertEqual(len(season_events), 4, "Should see 4 season changes in 365 days")

    def test_deterministic_replay(self):
        def run_year(seed):
            world, factions, npcs, locations, clocks = make_synthetic_world()
            engine = TickEngine()
            rng = random.Random(seed)
            events = []
            for _ in range(365):
                events.extend(engine.run_daily_tick(
                    world, factions, npcs, locations, clocks, None, rng
                ))
            return [(e.entity_id, e.event_type) for e in events]

        r1 = run_year(777)
        r2 = run_year(777)
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
