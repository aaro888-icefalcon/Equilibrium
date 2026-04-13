"""Unit tests for aging engine."""

import random
import unittest

from emergence.engine.progression.aging import (
    AgingEngine,
    get_age_category,
)


class TestAgeCategories(unittest.TestCase):

    def test_young(self):
        self.assertEqual(get_age_category(16), "young")
        self.assertEqual(get_age_category(29), "young")

    def test_mature(self):
        self.assertEqual(get_age_category(30), "mature")
        self.assertEqual(get_age_category(39), "mature")

    def test_aging(self):
        self.assertEqual(get_age_category(40), "aging")

    def test_old(self):
        self.assertEqual(get_age_category(50), "old")

    def test_very_old(self):
        self.assertEqual(get_age_category(60), "very_old")

    def test_ancient(self):
        self.assertEqual(get_age_category(70), "ancient")

    def test_elder(self):
        self.assertEqual(get_age_category(80), "elder")


class TestAgingEngine(unittest.TestCase):

    def _make_char(self, age=25):
        return {
            "age": age,
            "species": "human",
            "attributes": {
                "strength": 8, "agility": 8, "will": 8,
                "insight": 6, "perception": 8, "might": 8,
            },
            "condition_tracks": {"physical_max": 6},
        }

    def test_age_increments(self):
        char = self._make_char(age=24)
        engine = AgingEngine()
        engine.apply_yearly_aging(char, random.Random(42))
        self.assertEqual(char["age"], 25)

    def test_age_40_strength_decline(self):
        char = self._make_char(age=39)
        engine = AgingEngine()
        events = engine.apply_yearly_aging(char, random.Random(42))
        self.assertEqual(char["attributes"]["strength"], 6)  # 8 -> 6
        self.assertEqual(char["attributes"]["agility"], 6)

    def test_age_50_further_decline(self):
        char = self._make_char(age=49)
        engine = AgingEngine()
        events = engine.apply_yearly_aging(char, random.Random(42))
        # strength was 8, now -1 die (only 50s effect, starting from 8)
        self.assertEqual(char["attributes"]["strength"], 6)
        self.assertEqual(char["attributes"]["perception"], 6)

    def test_death_roll_at_60(self):
        char = self._make_char(age=59)
        engine = AgingEngine()
        events = engine.apply_yearly_aging(char, random.Random(42))
        # Should have a death roll event
        death_events = [e for e in events if "death" in e.mechanical]
        self.assertGreater(len(death_events), 0)

    def test_death_roll_favorable_odds_young_old(self):
        """At 60 with good health, death should be unlikely."""
        char = self._make_char(age=59)
        engine = AgingEngine()
        rng = random.Random(42)
        deaths = 0
        for seed in range(100):
            test_char = self._make_char(age=59)
            events = engine.apply_yearly_aging(test_char, random.Random(seed))
            for e in events:
                if e.mechanical.get("death"):
                    deaths += 1
        # At age 60 with 0 modifiers, DC 8 on d20 = 35% death rate
        # Most should survive
        self.assertLess(deaths, 60)

    def test_death_roll_high_age_more_likely(self):
        """At 80+ death should be more likely."""
        deaths = 0
        for seed in range(100):
            char = self._make_char(age=79)
            char["corruption"] = 3
            char["condition_tracks"]["physical"] = 3
            engine = AgingEngine()
            events = engine.apply_yearly_aging(char, random.Random(seed))
            for e in events:
                if e.mechanical.get("death"):
                    deaths += 1
        self.assertGreater(deaths, 30)  # Higher death rate

    def test_medical_care_bonus(self):
        char = self._make_char(age=69)
        char["medical_care"] = True
        engine = AgingEngine()
        # With medical care, modifiers get +2
        # This just verifies it runs without error
        events = engine.apply_yearly_aging(char, random.Random(42))
        self.assertIsInstance(events, list)


if __name__ == "__main__":
    unittest.main()
