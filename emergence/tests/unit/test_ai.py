"""Unit tests for emergence.engine.combat.ai."""

import unittest

from emergence.engine.combat.ai import (
    AiDecisionEngine,
    CombatantState,
    BattlefieldState,
    CombatAction,
    RETREAT_THRESHOLDS,
)


def _make_actor(**kwargs) -> CombatantState:
    defaults = dict(
        id="enemy_1", side="enemy", ai_profile="aggressive",
        tier=3, phy_current=0, phy_max=5,
    )
    defaults.update(kwargs)
    return CombatantState(**defaults)


def _make_player(**kwargs) -> CombatantState:
    defaults = dict(
        id="player", side="player", ai_profile="aggressive",
        tier=3, phy_current=0, phy_max=5,
    )
    defaults.update(kwargs)
    return CombatantState(**defaults)


def _state_with(actor, *others, **kwargs) -> BattlefieldState:
    combatants = {actor.id: actor}
    for o in others:
        combatants[o.id] = o
    return BattlefieldState(combatants=combatants, **kwargs)


class TestAggressiveProfile(unittest.TestCase):

    def test_chooses_attack_by_default(self):
        ai = AiDecisionEngine()
        actor = _make_actor()
        player = _make_player()
        state = _state_with(actor, player)
        action = ai.choose_action(actor, state)
        self.assertIn(action.action_type, ("Attack", "Power", "Finisher"))

    def test_retreats_at_high_phy_no_allies(self):
        ai = AiDecisionEngine()
        actor = _make_actor(phy_current=4)
        player = _make_player()
        state = _state_with(actor, player)
        self.assertTrue(ai.should_retreat(actor, state))

    def test_no_retreat_with_ally(self):
        ai = AiDecisionEngine()
        actor = _make_actor(phy_current=4)
        ally = CombatantState(
            id="ally", side="enemy", ai_profile="aggressive",
            tier=2, phy_current=0,
        )
        player = _make_player()
        state = _state_with(actor, ally, player)
        self.assertFalse(ai.should_retreat(actor, state))


class TestDefensiveProfile(unittest.TestCase):

    def test_retreats_when_no_allies(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="defensive", phy_current=0)
        player = _make_player()
        state = _state_with(actor, player)
        self.assertTrue(ai.should_retreat(actor, state))

    def test_stays_with_ally(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="defensive", phy_current=0)
        ally = CombatantState(
            id="ally", side="enemy", ai_profile="defensive",
            tier=2, phy_current=0,
        )
        player = _make_player()
        state = _state_with(actor, ally, player)
        self.assertFalse(ai.should_retreat(actor, state))


class TestTacticalProfile(unittest.TestCase):

    def test_prefers_assess_round_1_minor(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="tactical")
        player = _make_player()
        state = _state_with(actor, player, round_number=1)
        minor = ai.choose_minor(actor, state)
        self.assertIsNotNone(minor)
        self.assertEqual(minor.action_type, "Assess")

    def test_targets_exposed_first(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="tactical")
        p1 = _make_player(id="p1", is_exposed=True)
        p2 = CombatantState(
            id="p2", side="player", ai_profile="aggressive",
            tier=5, phy_current=0,
        )
        state = _state_with(actor, p1, p2)
        target = ai.pick_target(actor, state)
        self.assertEqual(target, "p1")


class TestPackProfile(unittest.TestCase):

    def test_degrades_to_aggressive_when_alone(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="pack")
        player = _make_player()
        state = _state_with(actor, player)
        # Pack with <2 allies should retreat
        self.assertTrue(ai.should_retreat(actor, state))

    def test_no_retreat_with_pack(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="pack")
        a2 = CombatantState(id="e2", side="enemy", ai_profile="pack", tier=2, phy_current=0)
        a3 = CombatantState(id="e3", side="enemy", ai_profile="pack", tier=2, phy_current=0)
        player = _make_player()
        state = _state_with(actor, a2, a3, player)
        self.assertFalse(ai.should_retreat(actor, state))


class TestOpportunistProfile(unittest.TestCase):

    def test_targets_exposed_over_others(self):
        ai = AiDecisionEngine()
        actor = _make_actor(ai_profile="opportunist")
        p1 = _make_player(id="p1", is_exposed=True)
        p2 = CombatantState(
            id="p2", side="player", ai_profile="aggressive",
            tier=5, phy_current=0,
        )
        state = _state_with(actor, p1, p2)
        target = ai.pick_target(actor, state)
        self.assertEqual(target, "p1")


class TestPickTarget(unittest.TestCase):

    def test_returns_none_when_no_enemies(self):
        ai = AiDecisionEngine()
        actor = _make_actor()
        state = _state_with(actor)
        self.assertIsNone(ai.pick_target(actor, state))

    def test_returns_player_when_only_enemy(self):
        ai = AiDecisionEngine()
        actor = _make_actor()
        player = _make_player()
        state = _state_with(actor, player)
        target = ai.pick_target(actor, state)
        self.assertEqual(target, "player")


class TestChooseMinor(unittest.TestCase):

    def test_default_minor_is_assess(self):
        ai = AiDecisionEngine()
        actor = _make_actor()
        player = _make_player()
        state = _state_with(actor, player)
        minor = ai.choose_minor(actor, state)
        self.assertIsNotNone(minor)
        self.assertEqual(minor.action_type, "Assess")


if __name__ == "__main__":
    unittest.main()
