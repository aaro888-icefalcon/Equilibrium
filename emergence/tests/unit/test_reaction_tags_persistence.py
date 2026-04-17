"""Regression test: reaction_tags persist across scenes, no implicit clear.

The v4 arc relies on reaction_tags staying alive so seed_pools can bias
later vignette pools on the player's accumulated signal.  This test
asserts tags accumulate, deduplicate, and never reset silently.
"""

from __future__ import annotations

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)


class TestReactionTagPersistence(unittest.TestCase):
    def test_accumulate_across_scenes(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(1)
        s = f.apply_scene_result("s1", {"reaction_tags": ["kinetic", "impact", "Brawler"]}, s, r)
        self.assertEqual(set(s.reaction_tags), {"kinetic", "impact", "Brawler"})
        s = f.apply_scene_result("s2", {"reaction_tags": ["cognitive", "perceptive"]}, s, r)
        self.assertEqual(
            set(s.reaction_tags),
            {"kinetic", "impact", "Brawler", "cognitive", "perceptive"},
        )

    def test_dedupe_on_append(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(2)
        s = f.apply_scene_result("s1", {"reaction_tags": ["kinetic"]}, s, r)
        s = f.apply_scene_result("s2", {"reaction_tags": ["kinetic", "Brawler"]}, s, r)
        self.assertEqual(s.reaction_tags, ["kinetic", "Brawler"])

    def test_preserved_across_unrelated_applies(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(3)
        s = f.apply_scene_result("s1", {"reaction_tags": ["cognitive"]}, s, r)
        s = f.apply_scene_result("s2", {"skills": {"surgery": 4}}, s, r)
        s = f.apply_scene_result("s3", {"threats": [{"name": "x"}]}, s, r)
        self.assertEqual(s.reaction_tags, ["cognitive"])

    def test_never_cleared_by_empty_payload(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(4)
        s = f.apply_scene_result("s1", {"reaction_tags": ["spatial"]}, s, r)
        s = f.apply_scene_result("s2", {}, s, r)
        self.assertEqual(s.reaction_tags, ["spatial"])


if __name__ == "__main__":
    unittest.main()
