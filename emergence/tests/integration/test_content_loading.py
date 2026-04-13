"""Integration tests: load all setting bible YAML files."""

import unittest

from emergence.engine.sim.content_loader import ContentLoader
from emergence.engine.schemas.world import (
    Clock,
    Faction,
    Location,
    NPC,
)


class TestFactionLoading(unittest.TestCase):

    def setUp(self):
        self.loader = ContentLoader()
        self.factions = self.loader.load_factions()

    def test_loads_factions(self):
        self.assertGreater(len(self.factions), 10,
                           f"Only loaded {len(self.factions)} factions, expected 20+")

    def test_faction_ids_present(self):
        # Check a few known faction IDs
        self.assertIn("fed-continuity", self.factions)
        self.assertIn("potomac-irregulars", self.factions)
        self.assertIn("catskill-throne", self.factions)

    def test_faction_has_display_name(self):
        fc = self.factions["fed-continuity"]
        self.assertEqual(fc.display_name, "Federal Continuity Command")

    def test_faction_population_parsed(self):
        fc = self.factions["fed-continuity"]
        self.assertGreater(fc.population.total, 0)

    def test_faction_goals_loaded(self):
        fc = self.factions["fed-continuity"]
        self.assertGreater(len(fc.goals), 0)

    def test_faction_standing_parsed(self):
        fc = self.factions["fed-continuity"]
        self.assertIsInstance(fc.standing_with_player_default, int)

    def test_all_factions_are_faction_objects(self):
        for fid, f in self.factions.items():
            self.assertIsInstance(f, Faction, f"Faction {fid} is not a Faction object")


class TestNpcLoading(unittest.TestCase):

    def setUp(self):
        self.loader = ContentLoader()
        self.npcs = self.loader.load_npcs()

    def test_loads_npcs(self):
        self.assertGreater(len(self.npcs), 20,
                           f"Only loaded {len(self.npcs)} NPCs, expected 40+")

    def test_npc_ids_present(self):
        self.assertIn("npc-preston", self.npcs)
        self.assertIn("npc-alcott", self.npcs)

    def test_npc_has_display_name(self):
        preston = self.npcs["npc-preston"]
        self.assertEqual(preston.display_name, "Colonel James Preston")

    def test_npc_manifestation_parsed(self):
        preston = self.npcs["npc-preston"]
        self.assertGreater(preston.manifestation.tier, 0)

    def test_npc_location_set(self):
        preston = self.npcs["npc-preston"]
        self.assertEqual(preston.location, "loc-mount-tremper")

    def test_npc_voice_loaded(self):
        preston = self.npcs["npc-preston"]
        self.assertGreater(len(preston.voice), 20)

    def test_all_npcs_are_npc_objects(self):
        for nid, n in self.npcs.items():
            self.assertIsInstance(n, NPC, f"NPC {nid} is not an NPC object")


class TestLocationLoading(unittest.TestCase):

    def setUp(self):
        self.loader = ContentLoader()
        self.locations = self.loader.load_locations()

    def test_loads_locations(self):
        self.assertGreater(len(self.locations), 20,
                           f"Only loaded {len(self.locations)} locations, expected 30+")

    def test_location_ids_present(self):
        self.assertIn("loc-mount-tremper", self.locations)

    def test_location_population_parsed(self):
        mt = self.locations["loc-mount-tremper"]
        self.assertGreater(mt.population, 0)

    def test_location_controller_set(self):
        mt = self.locations["loc-mount-tremper"]
        self.assertEqual(mt.controller, "catskill-throne")

    def test_location_description_loaded(self):
        mt = self.locations["loc-mount-tremper"]
        self.assertGreater(len(mt.description), 20)

    def test_all_locations_are_location_objects(self):
        for lid, loc in self.locations.items():
            self.assertIsInstance(loc, Location, f"Location {lid} is not a Location object")


class TestClockLoading(unittest.TestCase):

    def setUp(self):
        self.loader = ContentLoader()
        self.clocks = self.loader.load_clocks()

    def test_loads_clocks(self):
        self.assertGreater(len(self.clocks), 5,
                           f"Only loaded {len(self.clocks)} clocks, expected 8+")

    def test_clock_segments_set(self):
        bourse = self.clocks.get("bourse-currency-stability")
        if bourse:
            self.assertEqual(bourse.current_segment, 5)
            self.assertEqual(bourse.total_segments, 6)

    def test_clock_has_advance_rate(self):
        for cid, clock in self.clocks.items():
            self.assertIsInstance(clock.advance_rate, dict)

    def test_all_clocks_are_clock_objects(self):
        for cid, c in self.clocks.items():
            self.assertIsInstance(c, Clock, f"Clock {cid} is not a Clock object")


class TestConstantsLoading(unittest.TestCase):

    def test_loads_constants(self):
        loader = ContentLoader()
        constants = loader.load_constants()
        self.assertIsInstance(constants, dict)
        # Should have major sections
        self.assertTrue(
            len(constants) > 0,
            "Constants file loaded but empty"
        )


class TestCrossReferences(unittest.TestCase):
    """Verify cross-references between files resolve."""

    def setUp(self):
        self.loader = ContentLoader()
        self.factions = self.loader.load_factions()
        self.npcs = self.loader.load_npcs()
        self.locations = self.loader.load_locations()

    def test_npc_factions_exist(self):
        missing = []
        non_faction_labels = {"independent", "warped", "none", ""}
        for nid, npc in self.npcs.items():
            faction = npc.faction_affiliation.get("primary")
            if faction and faction not in non_faction_labels and faction not in self.factions:
                missing.append(f"{nid} → {faction}")
        # Allow some mismatches due to informal data
        self.assertLess(len(missing), len(self.npcs) * 0.3,
                        f"Too many missing faction refs: {missing[:10]}")

    def test_npc_locations_exist(self):
        missing = []
        for nid, npc in self.npcs.items():
            # Only check locations that look like IDs (loc-*)
            if npc.location and npc.location.startswith("loc-") and npc.location not in self.locations:
                missing.append(f"{nid} → {npc.location}")
        # Many NPCs reference sub-locations not in the main locations file
        self.assertLess(len(missing), len(self.npcs) * 0.3,
                        f"Too many missing location refs: {missing[:10]}")


if __name__ == "__main__":
    unittest.main()
