"""Unit tests for emergence.engine.combat.data_loader."""

import unittest

from emergence.engine.combat.data_loader import (
    load_powers,
    load_enemies,
    load_encounters,
)


class TestLoadPowers(unittest.TestCase):

    def test_loads_48_powers(self):
        powers = load_powers("emergence/data/powers")
        self.assertEqual(len(powers), 48, f"Expected 48 powers, got {len(powers)}")

    def test_all_have_id_and_name(self):
        powers = load_powers("emergence/data/powers")
        for pid, p in powers.items():
            self.assertEqual(pid, p.id)
            self.assertTrue(len(p.name) > 0, f"Power {pid} missing name")

    def test_all_have_valid_category(self):
        valid = {
            "physical_kinetic", "perceptual_mental", "matter_energy",
            "biological_vital", "auratic", "temporal_spatial", "eldritch_corruptive",
        }
        powers = load_powers("emergence/data/powers")
        for pid, p in powers.items():
            self.assertIn(p.category, valid, f"Power {pid} has invalid category {p.category}")

    def test_missing_directory_returns_empty(self):
        powers = load_powers("emergence/data/nonexistent")
        self.assertEqual(len(powers), 0)


class TestLoadEnemies(unittest.TestCase):

    def test_loads_30_enemies(self):
        enemies = load_enemies("emergence/data/enemies")
        self.assertEqual(len(enemies), 30, f"Expected 30 enemies, got {len(enemies)}")

    def test_all_have_id(self):
        enemies = load_enemies("emergence/data/enemies")
        for eid, e in enemies.items():
            self.assertEqual(eid, e.id)

    def test_all_have_tier(self):
        enemies = load_enemies("emergence/data/enemies")
        for eid, e in enemies.items():
            self.assertGreaterEqual(e.tier, 1, f"Enemy {eid} has tier < 1")

    def test_missing_directory_returns_empty(self):
        enemies = load_enemies("emergence/data/nonexistent")
        self.assertEqual(len(enemies), 0)


class TestLoadEncounters(unittest.TestCase):

    def test_loads_12_encounters(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        self.assertEqual(len(encounters), 12, f"Expected 12 encounters, got {len(encounters)}")

    def test_all_have_id(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        for enc in encounters:
            self.assertTrue(len(enc.id) > 0)

    def test_most_have_enemies(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        with_enemies = [enc for enc in encounters if len(enc.enemies) > 0]
        self.assertGreater(len(with_enemies), 8, "Expected most encounters to have enemies")

    def test_missing_file_returns_empty(self):
        encounters = load_encounters("emergence/data/nonexistent.json")
        self.assertEqual(len(encounters), 0)

    def test_round_trip_to_dict(self):
        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        for enc in encounters:
            d = enc.to_dict()
            self.assertIsInstance(d, dict)
            self.assertEqual(d["id"], enc.id)


if __name__ == "__main__":
    unittest.main()
