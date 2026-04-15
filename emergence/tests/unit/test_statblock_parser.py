"""Unit tests for emergence.engine.combat.statblock_parser."""

import os
import unittest

from emergence.engine.combat.statblock_parser import (
    parse_statblock_file,
    parse_all_powers,
)
from emergence.engine.combat.data_loader import load_powers_v2


PART1 = "emergence-power-statblocks-part1-clean.md"
PART2 = "emergence-power-statblocks-part2-spatial-paradoxic.md"


@unittest.skipUnless(os.path.exists(PART1), "Statblock files not present")
class TestStatblockParser(unittest.TestCase):

    def test_parse_count(self):
        powers = parse_all_powers(PART1, PART2)
        real = [p for p in powers if p["category"]]
        self.assertGreaterEqual(len(real), 190)
        self.assertLessEqual(len(real), 210)

    def test_regeneration_structure(self):
        powers = parse_all_powers(PART1, PART2)
        regen = next((p for p in powers if p["name"] == "Regeneration"), None)
        self.assertIsNotNone(regen)
        self.assertEqual(regen["category"], "somatic")
        self.assertEqual(regen["sub_category"], "vitality")
        self.assertEqual(regen["pair_role"], "Complement")
        self.assertEqual(len(regen["cast_modes"]), 3)
        self.assertEqual(len(regen["rider_slots"]), 3)
        self.assertNotEqual(regen["capstone_options"][0]["name"], "")

    def test_cast_mode_details(self):
        powers = parse_all_powers(PART1, PART2)
        regen = next((p for p in powers if p["name"] == "Regeneration"), None)
        cast1 = regen["cast_modes"][0]
        self.assertEqual(cast1["action_cost"], "minor")
        self.assertEqual(cast1["pool_cost"], 1)
        self.assertIn("defense", cast1["effect_families"])

    def test_rider_details(self):
        powers = parse_all_powers(PART1, PART2)
        regen = next((p for p in powers if p["name"] == "Regeneration"), None)
        rider_a = regen["rider_slots"][0]
        self.assertIn("periodic", rider_a["sub_category"])

    def test_id_generation(self):
        powers = parse_all_powers(PART1, PART2)
        regen = next((p for p in powers if p["name"] == "Regeneration"), None)
        self.assertEqual(regen["id"], "somatic_vitality_regeneration")

    def test_category_distribution(self):
        powers = parse_all_powers(PART1, PART2)
        real = [p for p in powers if p["category"]]
        cats = {}
        for p in real:
            cats[p["category"]] = cats.get(p["category"], 0) + 1
        self.assertEqual(len(cats), 6)
        for cat in ("somatic", "cognitive", "material", "kinetic", "spatial", "paradoxic"):
            self.assertIn(cat, cats)
            self.assertGreaterEqual(cats[cat], 25)


@unittest.skipUnless(os.path.exists("emergence/data/powers_v2"), "Generated power JSON not present")
class TestPowerV2Loader(unittest.TestCase):

    def test_load_200_powers(self):
        powers = load_powers_v2("emergence/data/powers_v2")
        self.assertEqual(len(powers), 200)

    def test_round_trip(self):
        powers = load_powers_v2("emergence/data/powers_v2")
        regen = powers.get("somatic_vitality_regeneration")
        self.assertIsNotNone(regen)
        d = regen.to_dict()
        self.assertEqual(d["name"], "Regeneration")
        self.assertEqual(len(d["cast_modes"]), 3)


if __name__ == "__main__":
    unittest.main()
