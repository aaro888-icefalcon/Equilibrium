"""Unit tests for family engine."""

import random
import unittest

from emergence.engine.progression.family import FamilyEngine, FamilyEvent


class TestFamilyEngine(unittest.TestCase):

    def _make_char(self, age=30, partner=True):
        char = {
            "name": "Elena",
            "age": age,
            "species": "human",
            "primary_category": "physical_kinetic",
            "attributes": {"strength": 8, "will": 8},
            "resources": {"cu": 500},
            "children": [],
        }
        if partner:
            char["partner"] = {"name": "Marcus", "species": "human"}
        return char

    def test_no_partner_no_children(self):
        char = self._make_char(partner=False)
        engine = FamilyEngine()
        events = engine.check_family_events(char, {}, random.Random(42))
        birth_events = [e for e in events if e.event_type == "child_born"]
        self.assertEqual(len(birth_events), 0)

    def test_child_birth_possible(self):
        """Over many years, a partnered character should have children."""
        engine = FamilyEngine()
        births = 0
        for seed in range(200):
            char = self._make_char(age=25)
            events = engine.check_family_events(char, {}, random.Random(seed))
            births += len([e for e in events if e.event_type == "child_born"])
        self.assertGreater(births, 0)

    def test_child_aging(self):
        char = self._make_char()
        char["children"] = [{"name": "Ada", "age": 5, "manifested": False, "tier": 0}]
        engine = FamilyEngine()
        engine.check_family_events(char, {}, random.Random(42))
        self.assertEqual(char["children"][0]["age"], 6)

    def test_child_manifestation(self):
        """Over many seeds, some children should manifest during puberty."""
        engine = FamilyEngine()
        manifested = 0
        for seed in range(200):
            char = self._make_char()
            char["children"] = [{"name": "Ada", "age": 14, "manifested": False, "tier": 0}]
            events = engine.check_family_events(char, {}, random.Random(seed))
            if any(e.event_type == "child_manifests" for e in events):
                manifested += 1
        self.assertGreater(manifested, 0)

    def test_create_descendant_from_child(self):
        char = self._make_char(age=65)
        char["children"] = [
            {"name": "Ada", "age": 20, "species": "human", "manifested": True, "tier": 1, "primary_category": "auratic"},
        ]
        engine = FamilyEngine()
        desc = engine.create_descendant(char, {}, random.Random(42))
        self.assertEqual(desc["name"], "Ada")
        self.assertEqual(desc["age"], 20)
        self.assertIn("Elena", desc["lineage"])

    def test_create_descendant_no_children(self):
        char = self._make_char()
        char["children"] = []
        engine = FamilyEngine()
        desc = engine.create_descendant(char, {}, random.Random(42))
        self.assertIn("Elena", desc["name"])
        self.assertEqual(desc["age"], 16)

    def test_inherit_resources(self):
        char = self._make_char()
        char["resources"] = {"cu": 1000, "scrip": 200}
        char["children"] = [{"name": "Ada", "age": 18, "species": "human"}]
        engine = FamilyEngine()
        desc = engine.create_descendant(char, {}, random.Random(42))
        self.assertEqual(desc["inherited_resources"]["cu"], 500)
        self.assertEqual(desc["inherited_resources"]["scrip"], 100)

    def test_inherit_relationships(self):
        char = self._make_char()
        char["relationships"] = {
            "npc1": {"standing": 3, "state": "loyal"},
            "npc2": {"standing": 1, "state": "cordial"},
            "npc3": {"standing": -3, "state": "dead"},
        }
        char["children"] = [{"name": "Ada", "age": 18, "species": "human"}]
        engine = FamilyEngine()
        desc = engine.create_descendant(char, {}, random.Random(42))
        self.assertIn("npc1", desc["inherited_relationships"])
        self.assertNotIn("npc2", desc["inherited_relationships"])  # standing only 1
        self.assertNotIn("npc3", desc["inherited_relationships"])  # dead

    def test_fertility_decreases_with_age(self):
        engine = FamilyEngine()
        self.assertGreater(engine._get_fertility(25), engine._get_fertility(45))
        self.assertEqual(engine._get_fertility(60), 0.0)


if __name__ == "__main__":
    unittest.main()
