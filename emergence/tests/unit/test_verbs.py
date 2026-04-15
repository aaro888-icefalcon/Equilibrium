"""Unit tests for emergence.engine.combat.verbs — Rev 4 verb resolvers."""

import random
import unittest

from emergence.engine.combat.verbs import (
    CombatState,
    CombatantRecord,
    VerbResult,
    resolve_attack,
    resolve_power,
    resolve_assess,
    resolve_maneuver,
    resolve_parley,
    resolve_finisher,
)
from emergence.engine.combat.statuses import StatusEngine, StatusName, ActiveStatus


def _state_1v1(
    player_attrs=None, enemy_attrs=None, register="human"
) -> CombatState:
    """Build a minimal 1v1 CombatState."""
    p = dict(id="player", side="player", tier=3, strength=8, agility=8,
             perception=8, will=8, insight=8, might=8, phy_max=5, men_max=5, soc_max=5)
    if player_attrs:
        p.update(player_attrs)
    e = dict(id="enemy", side="enemy", tier=3, strength=6, agility=6,
             perception=6, will=6, insight=6, might=6, phy_max=5, men_max=5, soc_max=5)
    if enemy_attrs:
        e.update(enemy_attrs)
    state = CombatState(combat_register=register)
    state.combatants["player"] = CombatantRecord(**p)
    state.combatants["enemy"] = CombatantRecord(**e)
    return state


class TestResolveAttack(unittest.TestCase):

    def test_returns_verb_result(self):
        state = _state_1v1()
        rng = random.Random(42)
        result = resolve_attack("player", "enemy", state, rng)
        self.assertIsInstance(result, VerbResult)
        self.assertEqual(result.verb, "Attack")
        self.assertEqual(result.actor_id, "player")

    def test_deterministic(self):
        s1 = _state_1v1()
        s2 = _state_1v1()
        r1 = resolve_attack("player", "enemy", s1, random.Random(99))
        r2 = resolve_attack("player", "enemy", s2, random.Random(99))
        self.assertEqual(r1.success_tier, r2.success_tier)
        self.assertEqual(r1.damage_dealt, r2.damage_dealt)

    def test_damage_on_success(self):
        # Seed chosen so d8 rolls are decent
        state = _state_1v1()
        rng = random.Random(7)
        results = [resolve_attack("player", "enemy", _state_1v1(), random.Random(i))
                   for i in range(100)]
        hits = [r for r in results if r.damage_dealt > 0]
        self.assertTrue(len(hits) > 0, "Expected at least one hit in 100 rolls")

    def test_logs_to_action_log(self):
        state = _state_1v1()
        resolve_attack("player", "enemy", state, random.Random(1))
        self.assertTrue(len(state.action_log) >= 1)
        self.assertEqual(state.action_log[-1]["verb"], "Attack")


class TestResolvePower(unittest.TestCase):

    def test_returns_verb_result(self):
        state = _state_1v1()
        result = resolve_power("player", "enemy", state, random.Random(42))
        self.assertIsInstance(result, VerbResult)
        self.assertEqual(result.verb, "Power")

    def test_fumble_self_damage(self):
        # Run many attempts to find a fumble
        for seed in range(500):
            state = _state_1v1(
                player_attrs={"might": 4, "strength": 4},
                enemy_attrs={"agility": 12, "armor": 4},
            )
            result = resolve_power("player", "enemy", state, random.Random(seed))
            if result.success_tier == "fumble":
                self.assertEqual(result.self_damage, 2)
                return
        # Not a hard failure, just note it
        self.skipTest("No fumble found in 500 seeds")


class TestResolveAssess(unittest.TestCase):

    def test_returns_verb_result(self):
        state = _state_1v1()
        result = resolve_assess("player", "enemy", state, random.Random(42))
        self.assertIsInstance(result, VerbResult)
        self.assertEqual(result.verb, "Assess")

    def test_truths_revealed_on_success(self):
        for seed in range(200):
            state = _state_1v1()
            result = resolve_assess("player", "enemy", state, random.Random(seed))
            if result.success_tier in ("full", "critical"):
                self.assertGreater(result.narrative_data.get("truths_revealed", 0), 0)
                return
        self.skipTest("No success found in 200 seeds")


class TestResolveManeuver(unittest.TestCase):

    def test_returns_verb_result(self):
        state = _state_1v1()
        result = resolve_maneuver("player", state, random.Random(42))
        self.assertIsInstance(result, VerbResult)
        self.assertEqual(result.verb, "Maneuver")

    def test_grapple_opposed(self):
        state = _state_1v1()
        result = resolve_maneuver(
            "player", state, random.Random(42),
            target_id="enemy", maneuver_type="grapple",
        )
        self.assertIsNotNone(result.check)


class TestResolveParley(unittest.TestCase):

    def test_returns_verb_result(self):
        state = _state_1v1()
        result = resolve_parley("player", "enemy", state, random.Random(42))
        self.assertIsInstance(result, VerbResult)
        self.assertEqual(result.verb, "Parley")

    def test_sets_parleyed_recently_on_success(self):
        for seed in range(200):
            state = _state_1v1()
            result = resolve_parley("player", "enemy", state, random.Random(seed))
            if result.success_tier in ("full", "critical", "marginal"):
                self.assertTrue(state.player_parleyed_recently)
                return
        self.skipTest("No parley success in 200 seeds")


class TestResolveFinisher(unittest.TestCase):

    def test_requires_momentum_spend(self):
        state = _state_1v1()
        state.combatants["player"].momentum = 5
        state.status_engine.apply_status("enemy", ActiveStatus(
            name=StatusName.EXPOSED, duration=-1, source="track",
        ))
        resolve_finisher("player", "enemy", state, random.Random(42))
        self.assertEqual(state.combatants["player"].momentum, 0)

    def test_incapacitates_on_full(self):
        for seed in range(200):
            state = _state_1v1()
            state.combatants["player"].momentum = 5
            state.status_engine.apply_status("enemy", ActiveStatus(
                name=StatusName.EXPOSED, duration=-1, source="track",
            ))
            result = resolve_finisher("player", "enemy", state, random.Random(seed))
            if result.success_tier in ("full", "critical"):
                self.assertFalse(state.combatants["enemy"].active)
                return
        self.skipTest("No full finisher in 200 seeds")


if __name__ == "__main__":
    unittest.main()
