"""Unit tests for emergence.engine.combat.posture_riders."""

import unittest
from types import SimpleNamespace

from emergence.engine.combat.posture_riders import (
    arm_rider,
    disarm_rider,
    disarm_all,
    apply_reactive_defense,
    apply_reactive_offense,
    apply_periodic,
    apply_amplify,
    apply_incoming_attack_riders,
    apply_end_of_round_riders,
)


def _make_combatant(**kwargs):
    defaults = dict(
        tier=3, pool=6, pool_max=6, base_pool_max=6,
        brace_uses=3, armed_posture_riders=[], phy=2, phy_max=5,
        current_posture="parry",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_rider(**kwargs):
    defaults = dict(
        slot_id="rider_1", rider_type="posture",
        sub_category="reactive_defense", pool_cost=0,
        compatible_postures=[], effect_parameters={"damage_reduction": 1},
    )
    defaults.update(kwargs)
    return defaults


class TestArmDisarm(unittest.TestCase):

    def test_arm_one_rider(self):
        c = _make_combatant()
        rider = _make_rider(sub_category="reactive_defense")
        self.assertTrue(arm_rider(c, "power_a", rider))
        self.assertEqual(len(c.armed_posture_riders), 1)
        # Pool max reduced by 1
        self.assertEqual(c.pool_max, 5)

    def test_arm_two_riders(self):
        c = _make_combatant()
        r1 = _make_rider(slot_id="r1", sub_category="periodic")
        r2 = _make_rider(slot_id="r2", sub_category="periodic")
        self.assertTrue(arm_rider(c, "p1", r1))
        self.assertTrue(arm_rider(c, "p2", r2))
        self.assertEqual(len(c.armed_posture_riders), 2)
        self.assertEqual(c.pool_max, 4)

    def test_arm_third_rider_rejected(self):
        c = _make_combatant()
        for i in range(2):
            arm_rider(c, f"p{i}", _make_rider(slot_id=f"r{i}", sub_category="periodic"))
        self.assertFalse(arm_rider(c, "p3", _make_rider(slot_id="r3", sub_category="periodic")))
        self.assertEqual(len(c.armed_posture_riders), 2)

    def test_reactive_defense_incompatible_with_aggressive(self):
        c = _make_combatant(current_posture="aggressive")
        rider = _make_rider(sub_category="reactive_defense")
        self.assertFalse(arm_rider(c, "p1", rider))

    def test_disarm_rider(self):
        c = _make_combatant()
        arm_rider(c, "p1", _make_rider(slot_id="r1"))
        self.assertEqual(len(c.armed_posture_riders), 1)
        self.assertTrue(disarm_rider(c, "p1", "r1"))
        self.assertEqual(len(c.armed_posture_riders), 0)
        self.assertEqual(c.pool_max, 6)

    def test_disarm_all(self):
        c = _make_combatant()
        arm_rider(c, "p1", _make_rider(slot_id="r1", sub_category="periodic"))
        arm_rider(c, "p2", _make_rider(slot_id="r2", sub_category="periodic"))
        removed = disarm_all(c)
        self.assertEqual(len(removed), 2)
        self.assertEqual(len(c.armed_posture_riders), 0)
        self.assertEqual(c.pool_max, 6)


class TestSubCategoryHandlers(unittest.TestCase):

    def test_reactive_defense(self):
        self.assertEqual(apply_reactive_defense({"damage_reduction": 2}, 5), 2)

    def test_reactive_defense_caps_at_damage(self):
        self.assertEqual(apply_reactive_defense({"damage_reduction": 5}, 3), 3)

    def test_reactive_offense(self):
        self.assertEqual(apply_reactive_offense({"counter_damage": 2}), 2)

    def test_periodic_heal(self):
        c = _make_combatant(phy=3)
        effects = apply_periodic({"heal_physical": 1}, c)
        self.assertEqual(effects["healed_physical"], 1)
        self.assertEqual(c.phy, 2)

    def test_periodic_pool_regen(self):
        c = _make_combatant(pool=4, pool_max=6)
        effects = apply_periodic({"pool_regen": 1}, c)
        self.assertEqual(effects["pool_regenerated"], 1)
        self.assertEqual(c.pool, 5)

    def test_amplify_crit_only(self):
        self.assertEqual(apply_amplify({"bonus_damage": 2, "crit_only": True}, is_crit=True), 2)
        self.assertEqual(apply_amplify({"bonus_damage": 2, "crit_only": True}, is_crit=False), 0)

    def test_amplify_always(self):
        self.assertEqual(apply_amplify({"bonus_damage": 1}, is_crit=False), 1)


class TestAggregate(unittest.TestCase):

    def test_stacking_reactive_defense(self):
        c = _make_combatant()
        arm_rider(c, "p1", _make_rider(
            slot_id="r1", sub_category="reactive_defense",
            effect_parameters={"damage_reduction": 1}))
        arm_rider(c, "p2", _make_rider(
            slot_id="r2", sub_category="reactive_defense",
            effect_parameters={"damage_reduction": 1}))
        result = apply_incoming_attack_riders(c, {"damage": 6})
        self.assertEqual(result["damage_reduction"], 2)

    def test_reactive_offense_counter(self):
        c = _make_combatant()
        arm_rider(c, "p1", _make_rider(
            slot_id="r1", sub_category="reactive_offense",
            effect_parameters={"counter_damage": 1}))
        result = apply_incoming_attack_riders(c, {"damage": 4})
        self.assertEqual(result["counter_damage"], 1)

    def test_end_of_round_periodic(self):
        c = _make_combatant(phy=3)
        arm_rider(c, "p1", _make_rider(
            slot_id="r1", sub_category="periodic",
            effect_parameters={"heal_physical": 1}))
        effects = apply_end_of_round_riders(c)
        self.assertEqual(len(effects), 1)
        self.assertEqual(c.phy, 2)


if __name__ == "__main__":
    unittest.main()
