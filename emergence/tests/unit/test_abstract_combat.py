"""Unit tests for emergence.engine.sim.abstract_combat — off-screen combat resolution."""

import random
import unittest

from emergence.engine.sim.abstract_combat import resolve_abstract_combat


def _make_attacker(**overrides):
    d = {"id": "council", "tier": 3, "military_capacity": 100}
    d.update(overrides)
    return d


def _make_defender(**overrides):
    d = {"id": "raiders", "tier": 3, "military_capacity": 80, "defensive_capacity": 2}
    d.update(overrides)
    return d


class TestAbstractCombatDeterminism(unittest.TestCase):

    def test_same_seed_same_result(self):
        atk = _make_attacker()
        dfd = _make_defender()
        r1 = resolve_abstract_combat(atk, dfd, {}, random.Random(42))
        r2 = resolve_abstract_combat(atk, dfd, {}, random.Random(42))
        self.assertEqual(r1["winner"], r2["winner"])
        self.assertEqual(r1["margin"], r2["margin"])
        self.assertEqual(r1["casualty_scale"], r2["casualty_scale"])


class TestTierAdvantage(unittest.TestCase):

    def test_higher_tier_wins_more(self):
        wins = 0
        for seed in range(200):
            atk = _make_attacker(tier=5, military_capacity=100)
            dfd = _make_defender(tier=1, military_capacity=50)
            result = resolve_abstract_combat(atk, dfd, {}, random.Random(seed))
            if result["winner"] == "council":
                wins += 1
        # Tier 5 vs tier 1 should win most of the time
        self.assertGreater(wins, 150, f"High-tier won only {wins}/200")

    def test_lower_tier_can_win(self):
        wins = 0
        for seed in range(200):
            atk = _make_attacker(tier=3, military_capacity=120)
            dfd = _make_defender(tier=4, military_capacity=60, defensive_capacity=1)
            result = resolve_abstract_combat(atk, dfd, {}, random.Random(seed))
            if result["winner"] == "council":
                wins += 1
        # Weaker side should win sometimes due to dice variance
        self.assertGreater(wins, 0, "Weaker side never won in 200 trials")


class TestContextModifiers(unittest.TestCase):

    def test_surprise_helps_attacker(self):
        surprise_wins = 0
        normal_wins = 0
        for seed in range(200):
            atk = _make_attacker(tier=3)
            dfd = _make_defender(tier=3)
            r_surprise = resolve_abstract_combat(
                atk, dfd, {"surprise": True}, random.Random(seed)
            )
            r_normal = resolve_abstract_combat(
                atk, dfd, {}, random.Random(seed)
            )
            if r_surprise["winner"] == "council":
                surprise_wins += 1
            if r_normal["winner"] == "council":
                normal_wins += 1
        self.assertGreater(surprise_wins, normal_wins)

    def test_terrain_advantage(self):
        adv_wins = 0
        dis_wins = 0
        for seed in range(200):
            atk = _make_attacker(tier=3)
            dfd = _make_defender(tier=3)
            r_adv = resolve_abstract_combat(
                atk, dfd, {"terrain_advantage": 2}, random.Random(seed)
            )
            r_dis = resolve_abstract_combat(
                atk, dfd, {"terrain_advantage": -2}, random.Random(seed)
            )
            if r_adv["winner"] == "council":
                adv_wins += 1
            if r_dis["winner"] == "council":
                dis_wins += 1
        self.assertGreater(adv_wins, dis_wins)


class TestCasualties(unittest.TestCase):

    def test_result_has_required_keys(self):
        result = resolve_abstract_combat(
            _make_attacker(), _make_defender(), {}, random.Random(42)
        )
        self.assertIn("winner", result)
        self.assertIn("loser", result)
        self.assertIn("margin", result)
        self.assertIn("casualty_scale", result)
        self.assertIn("casualties_attacker", result)
        self.assertIn("casualties_defender", result)
        self.assertIn("consequences", result)

    def test_casualty_scale_valid(self):
        for seed in range(100):
            result = resolve_abstract_combat(
                _make_attacker(), _make_defender(), {}, random.Random(seed)
            )
            self.assertIn(result["casualty_scale"],
                          ("light", "moderate", "heavy", "devastating"))


class TestConsequences(unittest.TestCase):

    def test_devastating_produces_consequences(self):
        # Find a devastating result
        for seed in range(500):
            atk = _make_attacker(tier=6, military_capacity=200)
            dfd = _make_defender(tier=1, military_capacity=20, defensive_capacity=0)
            result = resolve_abstract_combat(atk, dfd, {}, random.Random(seed))
            if result["casualty_scale"] == "devastating":
                self.assertGreater(len(result["consequences"]), 0)
                types = [c["type"] for c in result["consequences"]]
                self.assertIn("territory_change", types)
                self.assertIn("faction_weakened", types)
                return
        self.skipTest("No devastating result in 500 seeds")


if __name__ == "__main__":
    unittest.main()
