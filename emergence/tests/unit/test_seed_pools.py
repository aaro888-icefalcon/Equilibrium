"""Unit tests for seed_pools.compute_seed_pools across V1-V4 x 7 regions."""

from __future__ import annotations

import unittest

from emergence.engine.character_creation.character_factory import CreationState
from emergence.engine.character_creation.seed_pools import (
    SeedPools, compute_seed_pools,
)


_REGIONS = [
    "New York City", "Northern New Jersey", "Hudson Valley",
    "Central New Jersey", "Philadelphia", "Lehigh Valley", "Delmarva",
]


class TestV1(unittest.TestCase):
    def test_returns_nyc_default(self):
        p = compute_seed_pools(CreationState(), 1)
        self.assertEqual(p.region, "New York City")
        self.assertTrue(p.factions)
        self.assertTrue(p.locations)
        self.assertTrue(p.threats)
        self.assertIsNone(p.region_outcomes)

    def test_all_archetypes_eligible(self):
        p = compute_seed_pools(CreationState(), 1)
        self.assertGreaterEqual(len(p.threats), 10)


class TestV2(unittest.TestCase):
    def test_default_is_three_outcomes_stay_displaced_displaced(self):
        p = compute_seed_pools(CreationState(), 2)
        self.assertEqual(p.region, None)  # not yet locked
        self.assertEqual(p.region_outcomes,
                         ["stay_nyc", "displaced_to", "displaced_to"])

    def test_travel_hook_enables_traveled_to(self):
        s = CreationState()
        s.generated_npcs.append({
            "display_name": "Dock worker",
            "location": "loc-port-newark-compound",
        })
        p = compute_seed_pools(s, 2)
        self.assertEqual(p.region_outcomes,
                         ["stay_nyc", "displaced_to", "traveled_to"])

    def test_travel_hook_via_history(self):
        s = CreationState()
        s.history.append({
            "type": "character_creation_vignette",
            "description": "Followed a stranger toward Philadelphia.",
        })
        p = compute_seed_pools(s, 2)
        self.assertIn("traveled_to", p.region_outcomes)

    def test_v2_excludes_consumed_non_recurrable(self):
        s = CreationState()
        s.threats = [
            {"name": "captain", "archetype": "iron_crown_notice"},
            {"name": "stranger", "archetype": "knife_scavenger_survivor"},
        ]
        p = compute_seed_pools(s, 2)
        # iron_crown_notice is not recurrable; knife_scavenger_survivor is.
        self.assertNotIn("iron_crown_notice", p.threats)
        self.assertIn("knife_scavenger_survivor", p.threats)


class TestV3(unittest.TestCase):
    def test_every_region_has_pool(self):
        for region in _REGIONS:
            s = CreationState(region=region)
            p = compute_seed_pools(s, 3)
            self.assertEqual(p.region, region, f"region mismatch for {region}")
            self.assertTrue(p.factions, f"no factions for {region}")
            self.assertTrue(p.locations, f"no locations for {region}")
            self.assertTrue(p.vow_packages, f"no vows for {region}")

    def test_threats_filter_respects_consumption(self):
        s = CreationState(region="New York City")
        s.threats = [
            {"name": "contract", "archetype": "faction_assassin_contract"},
        ]
        p = compute_seed_pools(s, 3)
        self.assertNotIn("faction_assassin_contract", p.threats)  # not recurrable


class TestV4(unittest.TestCase):
    def test_every_region_has_startable_location(self):
        for region in _REGIONS:
            s = CreationState(region=region)
            p = compute_seed_pools(s, 4)
            startables = [l for l in p.locations if l.get("startable")]
            self.assertTrue(startables, f"{region}: no startable locations")

    def test_named_antagonist_always_available(self):
        # Even when every human archetype is consumed, fallback forces one.
        s = CreationState(region="Philadelphia")
        s.threats = [
            {"name": "n", "archetype": "named_rival_human"},
            {"name": "n", "archetype": "faction_assassin_contract"},
            {"name": "n", "archetype": "ruined_former_ally"},
            {"name": "n", "archetype": "iron_crown_notice"},
        ]
        p = compute_seed_pools(s, 4)
        # named_rival_human is recurrable so it stays eligible; guarantee the
        # named-antagonist pool is populated.
        self.assertIn("named_rival_human", p.threats)

    def test_vow_packages_at_least_two(self):
        s = CreationState(region="Hudson Valley")
        p = compute_seed_pools(s, 4)
        self.assertGreaterEqual(len(p.vow_packages), 2)


class TestDispatch(unittest.TestCase):
    def test_unknown_index_raises(self):
        with self.assertRaises(ValueError):
            compute_seed_pools(CreationState(), 0)
        with self.assertRaises(ValueError):
            compute_seed_pools(CreationState(), 5)


if __name__ == "__main__":
    unittest.main()
