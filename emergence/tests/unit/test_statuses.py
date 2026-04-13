"""Unit tests for emergence.engine.combat.statuses."""

import random
import unittest

from emergence.engine.combat.statuses import StatusEngine, StatusName, ActiveStatus


class TestStatusApplyRemove(unittest.TestCase):
    """Test apply / remove / has_status basics."""

    def setUp(self):
        self.engine = StatusEngine()

    def test_apply_new_status(self):
        events = self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BLEEDING, duration=3, source="sword", applied_round=1,
        ))
        self.assertTrue(self.engine.has_status("p1", StatusName.BLEEDING))
        self.assertTrue(len(events) > 0)

    def test_apply_duplicate_resets_duration(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BLEEDING, duration=2, source="a", applied_round=1,
        ))
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BLEEDING, duration=5, source="b", applied_round=2,
        ))
        statuses = self.engine.get_statuses("p1")
        bleeding = [s for s in statuses if s.name == StatusName.BLEEDING]
        self.assertEqual(len(bleeding), 1)
        self.assertEqual(bleeding[0].duration, 5)

    def test_remove_status(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.STUNNED, duration=1, source="hit",
        ))
        removed = self.engine.remove_status("p1", StatusName.STUNNED)
        self.assertTrue(removed)
        self.assertFalse(self.engine.has_status("p1", StatusName.STUNNED))

    def test_remove_absent_returns_false(self):
        self.assertFalse(self.engine.remove_status("p1", StatusName.STUNNED))

    def test_get_statuses_empty(self):
        self.assertEqual(self.engine.get_statuses("nobody"), [])


class TestAllSevenStatuses(unittest.TestCase):
    """Verify all 7 statuses can be applied."""

    def test_all_seven(self):
        engine = StatusEngine()
        for sn in StatusName:
            engine.apply_status("p1", ActiveStatus(
                name=sn, duration=2, source="test",
            ))
        self.assertEqual(len(engine.get_statuses("p1")), 7)


class TestTickBehavior(unittest.TestCase):
    """Test start-of-round and end-of-round ticks."""

    def setUp(self):
        self.engine = StatusEngine()

    def test_burning_deals_damage_after_turn(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BURNING, duration=3, source="fire",
        ))
        effects = self.engine.tick_after_turn("p1")
        damage_effects = [e for e in effects if e["type"] == "damage"]
        self.assertEqual(len(damage_effects), 1)
        self.assertEqual(damage_effects[0]["amount"], 1)

    def test_bleeding_deals_damage_after_turn(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BLEEDING, duration=3, source="slash",
        ))
        effects = self.engine.tick_after_turn("p1")
        damage_effects = [e for e in effects if e["type"] == "damage"]
        self.assertEqual(len(damage_effects), 1)
        self.assertEqual(damage_effects[0]["source"], "bleeding")

    def test_corrupted_tick_rolls_d6(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.CORRUPTED, duration=3, source="eldritch",
        ))
        # Run many times to exercise different d6 outcomes
        rng = random.Random(42)
        all_effects = []
        for _ in range(20):
            effects = self.engine.tick_start_of_round("p1", rng)
            all_effects.extend(effects)
        # Should produce at least one effect type from corrupted
        self.assertTrue(len(all_effects) > 0)

    def test_end_of_round_decrements(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.SHAKEN, duration=2, source="fear",
        ))
        self.engine.tick_end_of_round("p1")
        # Duration should now be 1
        statuses = self.engine.get_statuses("p1")
        self.assertTrue(self.engine.has_status("p1", StatusName.SHAKEN))
        self.engine.tick_end_of_round("p1")
        # Should expire
        self.assertFalse(self.engine.has_status("p1", StatusName.SHAKEN))

    def test_permanent_status_not_decremented(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.EXPOSED, duration=-1, source="track",
        ))
        self.engine.tick_end_of_round("p1")
        self.assertTrue(self.engine.has_status("p1", StatusName.EXPOSED))


class TestModifierQueries(unittest.TestCase):
    """Test get_check_modifiers and get_attack_bonus_vs."""

    def setUp(self):
        self.engine = StatusEngine()

    def test_shaken_minus_1(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.SHAKEN, duration=2, source="fear",
        ))
        self.assertEqual(self.engine.get_check_modifiers("p1", "Attack"), -1)

    def test_stunned_minus_2(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.STUNNED, duration=1, source="hit",
        ))
        self.assertEqual(self.engine.get_check_modifiers("p1", "Attack"), -2)

    def test_burning_minus_1_non_disengage(self):
        self.engine.apply_status("p1", ActiveStatus(
            name=StatusName.BURNING, duration=2, source="fire",
        ))
        self.assertEqual(self.engine.get_check_modifiers("p1", "Attack"), -1)
        self.assertEqual(self.engine.get_check_modifiers("p1", "Disengage"), 0)

    def test_marked_plus_2_attack_bonus(self):
        self.engine.apply_status("t1", ActiveStatus(
            name=StatusName.MARKED, duration=2, source="assess",
        ))
        self.assertEqual(self.engine.get_attack_bonus_vs("t1"), 2)

    def test_exposed_plus_2_attack_bonus(self):
        self.engine.apply_status("t1", ActiveStatus(
            name=StatusName.EXPOSED, duration=-1, source="track",
        ))
        self.assertEqual(self.engine.get_attack_bonus_vs("t1"), 2)

    def test_stacked_bonus(self):
        self.engine.apply_status("t1", ActiveStatus(
            name=StatusName.MARKED, duration=2, source="assess",
        ))
        self.engine.apply_status("t1", ActiveStatus(
            name=StatusName.EXPOSED, duration=-1, source="track",
        ))
        self.assertEqual(self.engine.get_attack_bonus_vs("t1"), 4)


class TestCanAct(unittest.TestCase):

    def test_stunned_blocks_major(self):
        engine = StatusEngine()
        engine.apply_status("p1", ActiveStatus(
            name=StatusName.STUNNED, duration=1, source="hit",
        ))
        can_major, can_minor = engine.can_act("p1")
        self.assertFalse(can_major)
        self.assertTrue(can_minor)

    def test_no_status_can_act(self):
        engine = StatusEngine()
        can_major, can_minor = engine.can_act("p1")
        self.assertTrue(can_major)
        self.assertTrue(can_minor)


class TestSceneClear(unittest.TestCase):

    def test_clear_scene_statuses(self):
        engine = StatusEngine()
        engine.apply_status("p1", ActiveStatus(name=StatusName.SHAKEN, duration=2, source="a"))
        engine.apply_status("p1", ActiveStatus(name=StatusName.MARKED, duration=2, source="b"))
        engine.apply_status("p1", ActiveStatus(name=StatusName.BURNING, duration=3, source="c"))
        engine.clear_scene_statuses("p1")
        self.assertFalse(engine.has_status("p1", StatusName.SHAKEN))
        self.assertFalse(engine.has_status("p1", StatusName.MARKED))
        self.assertTrue(engine.has_status("p1", StatusName.BURNING))


if __name__ == "__main__":
    unittest.main()
