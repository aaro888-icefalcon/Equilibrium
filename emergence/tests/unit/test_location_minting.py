"""Unit tests for v4 location minting + starting_location + pending_ack."""

from __future__ import annotations

import dataclasses
import json
import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)


class TestLocationMinting(unittest.TestCase):
    def test_reference_existing_location(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(1)
        s = f.apply_scene_result("t", {"locations": [
            {"id": "loc-kingston-hv", "is_starting": False},
        ]}, s, r)
        self.assertEqual(len(s.generated_locations), 1)
        self.assertEqual(s.generated_locations[0]["id"], "loc-kingston-hv")
        self.assertEqual(s.starting_location, "")

    def test_mint_new_location_with_spec(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(2)
        s = f.apply_scene_result("t", {"locations": [
            {"spec": {"id": "loc-safehouse-01", "name": "Safehouse",
                      "region": "Hudson Valley"},
             "is_starting": True},
        ]}, s, r)
        self.assertEqual(s.starting_location, "loc-safehouse-01")
        self.assertEqual(len(s.generated_locations), 1)
        self.assertEqual(
            s.generated_locations[0]["spec"]["region"], "Hudson Valley",
        )

    def test_starting_from_referenced_id(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(3)
        s = f.apply_scene_result("t", {"locations": [
            {"id": "loc-philadelphia-bourse-floor", "is_starting": True},
        ]}, s, r)
        self.assertEqual(s.starting_location, "loc-philadelphia-bourse-floor")

    def test_multiple_entries_last_starting_wins(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(4)
        s = f.apply_scene_result("t", {"locations": [
            {"id": "loc-a", "is_starting": False},
            {"id": "loc-b", "is_starting": True},
            {"id": "loc-c", "is_starting": True},
        ]}, s, r)
        self.assertEqual(s.starting_location, "loc-c")
        self.assertEqual(len(s.generated_locations), 3)


class TestPendingAck(unittest.TestCase):
    def test_default_false(self):
        s = CreationState()
        self.assertFalse(s.pending_ack)

    def test_set_via_apply(self):
        s = CreationState()
        f = CharacterFactory()
        r = random.Random(5)
        s = f.apply_scene_result("t", {"pending_ack": True}, s, r)
        self.assertTrue(s.pending_ack)
        s = f.apply_scene_result("t2", {"pending_ack": False}, s, r)
        self.assertFalse(s.pending_ack)


class TestRoundTrip(unittest.TestCase):
    def test_state_roundtrips_through_dict(self):
        s = CreationState(region="Hudson Valley")
        f = CharacterFactory()
        r = random.Random(6)
        s = f.apply_scene_result("t", {
            "locations": [{"spec": {"id": "loc-new", "name": "New",
                                     "region": "Hudson Valley"},
                           "is_starting": True}],
            "pending_ack": True,
        }, s, r)
        raw = json.dumps(dataclasses.asdict(s), default=str)
        revived_dict = json.loads(raw)
        revived = CreationState(**revived_dict)
        self.assertEqual(revived.starting_location, "loc-new")
        self.assertTrue(revived.pending_ack)
        self.assertEqual(len(revived.generated_locations), 1)


if __name__ == "__main__":
    unittest.main()
