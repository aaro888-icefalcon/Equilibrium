"""Integration tests: build initial world state from setting bible content."""

import unittest

from emergence.engine.sim.initial_state import build_initial_world, validate_initial_state
from emergence.engine.sim.content_loader import ContentLoader
from emergence.engine.schemas.world import (
    Clock,
    Faction,
    Location,
    NPC,
    WorldState,
)


class TestBuildInitialWorld(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.world, cls.factions, cls.npcs, cls.locations, cls.clocks = build_initial_world()

    def test_world_is_world_state(self):
        self.assertIsInstance(self.world, WorldState)

    def test_time_is_t_plus_1(self):
        self.assertEqual(self.world.current_time["year"], 1)
        self.assertEqual(self.world.current_time["month"], 0)
        self.assertEqual(self.world.current_time["day"], 0)

    def test_season_is_spring(self):
        self.assertEqual(self.world.current_time["season"], "spring")

    def test_factions_loaded(self):
        self.assertGreater(len(self.factions), 10)
        for fid, f in self.factions.items():
            self.assertIsInstance(f, Faction)

    def test_npcs_loaded(self):
        self.assertGreater(len(self.npcs), 20)
        for nid, n in self.npcs.items():
            self.assertIsInstance(n, NPC)

    def test_locations_loaded(self):
        self.assertGreater(len(self.locations), 20)
        for lid, loc in self.locations.items():
            self.assertIsInstance(loc, Location)

    def test_clocks_loaded(self):
        self.assertGreater(len(self.clocks), 5)
        for cid, c in self.clocks.items():
            self.assertIsInstance(c, Clock)

    def test_npc_location_sync(self):
        """NPCs with valid location IDs appear in that location's npcs_present."""
        synced = 0
        for nid, npc in self.npcs.items():
            if npc.location and npc.location in self.locations:
                loc = self.locations[npc.location]
                if hasattr(loc, 'npcs_present') and nid in loc.npcs_present:
                    synced += 1
        self.assertGreater(synced, 10,
                           f"Only {synced} NPCs synced to locations")


class TestValidateInitialState(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.world, cls.factions, cls.npcs, cls.locations, cls.clocks = build_initial_world()

    def test_validation_produces_few_warnings(self):
        warnings = validate_initial_state(
            self.world, self.factions, self.npcs, self.locations, self.clocks
        )
        # Allow some warnings for informal data, but not too many
        self.assertLess(len(warnings), 20,
                        f"Too many validation warnings: {warnings[:10]}")

    def test_no_critical_warnings(self):
        warnings = validate_initial_state(
            self.world, self.factions, self.npcs, self.locations, self.clocks
        )
        critical = [w for w in warnings if "Only" in w]
        self.assertEqual(len(critical), 0,
                         f"Critical entity count warnings: {critical}")

    def test_clock_segments_valid(self):
        warnings = validate_initial_state(
            self.world, self.factions, self.npcs, self.locations, self.clocks
        )
        clock_warnings = [w for w in warnings if "segment" in w.lower()]
        self.assertEqual(len(clock_warnings), 0,
                         f"Clock segment warnings: {clock_warnings}")


class TestInitialWorldTickable(unittest.TestCase):
    """Verify the initial world state can be ticked by the simulation engine."""

    @classmethod
    def setUpClass(cls):
        cls.world, cls.factions, cls.npcs, cls.locations, cls.clocks = build_initial_world()

    def test_tick_30_days(self):
        """Tick the full bible world 30 days without errors."""
        import random
        from emergence.engine.sim.tick_engine import TickEngine

        engine = TickEngine()
        rng = random.Random(42)
        player = {"id": "player", "heat": 0, "location": "loc-mount-tremper"}

        all_events = []
        for day in range(30):
            events = engine.run_daily_tick(
                self.world, self.factions, self.npcs,
                self.locations, self.clocks, player, rng,
            )
            all_events.extend(events)

        self.assertGreater(len(all_events), 0,
                           "No events generated in 30 days")
        # Verify time advanced (tick engine uses day_count)
        self.assertEqual(self.world.current_time.get("day_count", 0), 30)


if __name__ == "__main__":
    unittest.main()
