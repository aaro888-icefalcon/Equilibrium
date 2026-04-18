"""Unit tests for OnsetScene (v4 scene 0)."""

from __future__ import annotations

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.onset_scene import OnsetScene


def _full_run_state() -> CreationState:
    s = CreationState(seed=42)
    f = CharacterFactory()
    r = random.Random(1)
    sc = OnsetScene()
    s = sc.apply_text(
        {"name": "Shake", "age": "30",
         "description": "surgeon, curious, analytical"},
        s, f, r,
    )
    sc.prepare(s, r)
    s = sc.apply(1, s, f, r)   # attention
    sc.prepare(s, r)
    s = sc.apply(2, s, f, r)   # engagement -> builds slate
    sc.prepare(s, r)
    s = sc.apply_multi([0, 1], s, f, r)  # slate
    return s


class TestPhases(unittest.TestCase):
    def test_phase_sequence(self):
        s = CreationState()
        sc = OnsetScene()
        self.assertEqual(sc._phase(s), "biography")
        s = sc.apply_text({"name": "x", "age": "25", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        self.assertEqual(sc._phase(s), "attention")
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))
        self.assertEqual(sc._phase(s), "engagement")
        sc.prepare(s, random.Random(1))
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))
        self.assertEqual(sc._phase(s), "slate")


class TestTextInput(unittest.TestCase):
    def test_clamps_age(self):
        s = CreationState()
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "200", "description": ""},
                          s, CharacterFactory(), random.Random(1))
        self.assertEqual(s.age_at_onset, 65)
        s2 = sc.apply_text({"name": "y", "age": "3", "description": ""},
                           CreationState(), CharacterFactory(), random.Random(1))
        self.assertEqual(s2.age_at_onset, 16)

    def test_default_name_when_empty(self):
        s = CreationState()
        sc = OnsetScene()
        s = sc.apply_text({"name": "   ", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        self.assertEqual(s.name, "Unknown")


class TestChoices(unittest.TestCase):
    def test_attention_phase_returns_three(self):
        s = CreationState()
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        self.assertEqual(len(sc.get_choices(s)), 3)

    def test_engagement_phase_returns_three(self):
        s = CreationState()
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))
        sc.prepare(s, random.Random(1))
        self.assertEqual(len(sc.get_choices(s)), 3)

    def test_slate_phase_returns_ten(self):
        s = _full_run_state()
        # At this point slate was already consumed; but pending_slate is still
        # set.  Verify.
        sc = OnsetScene()
        sc.prepare(s, random.Random(1))
        self.assertEqual(len(sc.get_choices(s)), 10)


class TestCompletionAndAck(unittest.TestCase):
    def test_not_complete_until_powers_picked(self):
        s = CreationState(seed=1)
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        self.assertFalse(sc.is_complete(s))
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))
        self.assertFalse(sc.is_complete(s))
        sc.prepare(s, random.Random(1))
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))
        self.assertFalse(sc.is_complete(s))
        # slate pick
        sc.prepare(s, random.Random(1))
        s = sc.apply_multi([0, 1], s, CharacterFactory(), random.Random(1))
        self.assertTrue(sc.is_complete(s))
        self.assertTrue(s.pending_ack)

    def test_tier_ceiling_set_on_completion(self):
        s = _full_run_state()
        self.assertEqual(s.tier, 3)
        self.assertEqual(s.tier_ceiling, 5)

    def test_two_powers_applied(self):
        s = _full_run_state()
        self.assertEqual(len(s.powers), 2)
        slots = [p.get("slot") for p in s.powers]
        self.assertEqual(slots, ["primary", "secondary"])


class TestReactionTagAccumulation(unittest.TestCase):
    def test_attention_tags_persist(self):
        s = CreationState(seed=1)
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        pre = set(s.reaction_tags)
        s = sc.apply(1, s, CharacterFactory(), random.Random(1))
        # attention option 1 = bus (kinetic/impact/Brawler)
        self.assertIn("kinetic", s.reaction_tags)
        self.assertIn("Brawler", s.reaction_tags)

    def test_engagement_tags_add_to_attention(self):
        s = CreationState(seed=1)
        sc = OnsetScene()
        s = sc.apply_text({"name": "x", "age": "30", "description": "d"},
                          s, CharacterFactory(), random.Random(1))
        s = sc.apply(0, s, CharacterFactory(), random.Random(1))  # attention: helicopter
        sc.prepare(s, random.Random(1))
        s = sc.apply(1, s, CharacterFactory(), random.Random(1))  # engagement: command
        self.assertIn("cognitive", s.reaction_tags)
        self.assertIn("dominant", s.reaction_tags)


if __name__ == "__main__":
    unittest.main()
