"""Unit tests for emergence.engine.combat.damage."""

import unittest

from emergence.engine.combat.damage import (
    resolve_damage,
    allocate_to_tracks,
    compute_exposure_fill,
    DamageType,
    AFFINITY_PROFILES,
)
from emergence.engine.schemas.combatant import AffinityState


class TestAffinityMultipliers(unittest.TestCase):
    """Test affinity scaling in resolve_damage."""

    def test_vulnerable_1_5x(self):
        r = resolve_damage(4, 1, "physical_kinetic", "vulnerable", armor=0)
        # raw = 4 + tier_bonus(1)=0 = 4; vulnerable: ceil(4*1.5) = 6
        self.assertEqual(r.after_affinity, 6)

    def test_neutral_1x(self):
        r = resolve_damage(4, 1, "physical_kinetic", "neutral", armor=0)
        self.assertEqual(r.after_affinity, 4)

    def test_resistant_half_min1(self):
        r = resolve_damage(4, 1, "physical_kinetic", "resistant", armor=0)
        # floor(4*0.5) = 2
        self.assertEqual(r.after_affinity, 2)

    def test_resistant_sting_floor(self):
        """Resistant on 1 raw damage should still deal 1 (sting floor)."""
        r = resolve_damage(1, 0, "physical_kinetic", "resistant", armor=0)
        # raw=1+0=1; floor(1*0.5)=0 → sting floor → 1
        self.assertEqual(r.after_affinity, 1)

    def test_immune_zero(self):
        r = resolve_damage(10, 3, "physical_kinetic", "immune", armor=0)
        self.assertEqual(r.after_affinity, 0)
        self.assertEqual(r.final, 0)

    def test_absorb_heals(self):
        r = resolve_damage(9, 0, "physical_kinetic", "absorb", armor=0)
        # raw=9, absorb heals 9//3=3
        self.assertEqual(r.absorbed, 3)
        self.assertEqual(r.after_affinity, 0)
        self.assertEqual(r.final, 0)


class TestArmorReduction(unittest.TestCase):
    """Test armor reduces damage after affinity."""

    def test_armor_reduces(self):
        r = resolve_damage(6, 0, "physical_kinetic", "neutral", armor=2)
        self.assertEqual(r.after_armor, r.after_affinity - 2)

    def test_armor_floor_zero(self):
        r = resolve_damage(1, 0, "physical_kinetic", "neutral", armor=5)
        self.assertEqual(r.after_armor, 0)


class TestExposureFill(unittest.TestCase):
    """Test exposure fill calculation."""

    def test_positive_damage_gives_fill(self):
        fill = compute_exposure_fill(4, "neutral")
        # base_fill = 4//2 = 2, scaled=2*1.0=2, sting=1
        self.assertEqual(fill, 3)

    def test_zero_damage_zero_fill(self):
        fill = compute_exposure_fill(0, "neutral")
        self.assertEqual(fill, 0)

    def test_immune_zero_fill(self):
        fill = compute_exposure_fill(0, "immune")
        self.assertEqual(fill, 0)

    def test_vulnerable_double_fill(self):
        fill = compute_exposure_fill(4, "vulnerable")
        # base_fill=2, scaled=2*2.0=4, sting=1
        self.assertEqual(fill, 5)

    def test_crit_push(self):
        fill = compute_exposure_fill(4, "neutral", crit_statuses_applied=1)
        self.assertEqual(fill, 4)  # 3 base + 1 crit


class TestTrackAllocation(unittest.TestCase):
    """Test allocate_to_tracks."""

    def test_basic_physical(self):
        result = allocate_to_tracks(3, "physical_kinetic", {"physical": 1, "mental": 0, "social": 0})
        self.assertEqual(result["track_changes"]["physical"], 3)
        self.assertEqual(result["new_tracks"]["physical"], 4)

    def test_overflow_harm(self):
        result = allocate_to_tracks(4, "physical_kinetic", {"physical": 4, "mental": 0, "social": 0})
        # 4+4=8, cap=5, overflow=3 → harm tier 2
        self.assertEqual(result["new_tracks"]["physical"], 5)
        self.assertTrue(len(result["harm_events"]) > 0)
        self.assertEqual(result["harm_events"][0]["tier"], 2)

    def test_mental_overflow_to_physical(self):
        result = allocate_to_tracks(6, "perceptual_mental", {"physical": 0, "mental": 3, "social": 0})
        # mental: 3+6=9, cap=5, overflow=4 → spills to physical
        self.assertEqual(result["new_tracks"]["mental"], 5)
        self.assertIn("physical", result["track_changes"])

    def test_ec_crit_corruption(self):
        result = allocate_to_tracks(2, "eldritch_corruptive", {"physical": 0, "mental": 0, "social": 0}, is_crit=True)
        self.assertEqual(result["corruption"], 1)

    def test_zero_damage(self):
        result = allocate_to_tracks(0, "physical_kinetic", {"physical": 0, "mental": 0, "social": 0})
        self.assertEqual(result["track_changes"], {})


class TestAffinityProfiles(unittest.TestCase):
    """Test AFFINITY_PROFILES have all 7 damage types."""

    def test_all_profiles_have_seven_keys(self):
        for name, profile in AFFINITY_PROFILES.items():
            self.assertEqual(len(profile), 7, f"Profile '{name}' has {len(profile)} keys, expected 7")

    def test_standard_human_all_neutral(self):
        for dt, aff in AFFINITY_PROFILES["standard_human"].items():
            self.assertEqual(aff, "neutral", f"standard_human[{dt}] should be neutral")


if __name__ == "__main__":
    unittest.main()
