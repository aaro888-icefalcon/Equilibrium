"""Unit tests for scenario_pool — tag extraction, vignette selection, pick_six."""

import os
import random
import unittest

from emergence.engine.combat.data_loader import load_powers_v2
from emergence.engine.character_creation import scenario_pool


_V2_DIR = os.path.join("emergence", "data", "powers_v2")


def _all_powers():
    return list(load_powers_v2(_V2_DIR).values())


class TestExtractTags(unittest.TestCase):
    def test_empty_returns_empty(self):
        self.assertEqual(scenario_pool.extract_tags(""), [])
        self.assertEqual(scenario_pool.extract_tags("   "), [])

    def test_single_word_matches(self):
        tags = scenario_pool.extract_tags("fight")
        self.assertIn("kinetic", tags)
        self.assertIn("impact", tags)

    def test_dedups(self):
        tags = scenario_pool.extract_tags("fight fight fight")
        self.assertEqual(tags.count("kinetic"), 1)

    def test_preserves_first_seen_order(self):
        tags = scenario_pool.extract_tags("hide fight")
        self.assertLess(tags.index("phasing"), tags.index("impact"))

    def test_unknown_words_contribute_nothing(self):
        self.assertEqual(scenario_pool.extract_tags("qwerty asdf"), [])

    def test_description_tags_merge_both_tables(self):
        # 'surgeon' is in SELF_DESCRIPTION_KEYWORDS; 'fight' is in REACTION_KEYWORDS.
        tags = scenario_pool.extract_description_tags("surgeon who will fight")
        self.assertIn("somatic", tags)
        self.assertIn("kinetic", tags)


class TestSelectVignette(unittest.TestCase):
    def test_slot_1_is_slot_1(self):
        v = scenario_pool.select_vignette(1, random.Random(0))
        self.assertEqual(v["slot"], 1)
        self.assertTrue(v["id"].startswith("v1_"))

    def test_slot_2_is_slot_2(self):
        v = scenario_pool.select_vignette(2, random.Random(0))
        self.assertEqual(v["slot"], 2)
        self.assertTrue(v["id"].startswith("v2_"))

    def test_exclude_ids_honored(self):
        first = scenario_pool.select_vignette(1, random.Random(0))
        second = scenario_pool.select_vignette(1, random.Random(0), exclude_ids=(first["id"],))
        self.assertNotEqual(first["id"], second["id"])

    def test_deterministic_with_seed(self):
        a = scenario_pool.select_vignette(1, random.Random(12345))
        b = scenario_pool.select_vignette(1, random.Random(12345))
        self.assertEqual(a["id"], b["id"])


class TestPickSix(unittest.TestCase):
    def setUp(self):
        self.powers = _all_powers()

    def test_returns_exactly_six(self):
        picks = scenario_pool.pick_six(self.powers, ["kinetic"], random.Random(0))
        self.assertEqual(len(picks), 6)

    def test_no_duplicates(self):
        picks = scenario_pool.pick_six(self.powers, ["kinetic"], random.Random(0))
        ids = {p.id for p in picks}
        self.assertEqual(len(ids), 6)

    def test_exclude_category(self):
        picks = scenario_pool.pick_six(
            self.powers, ["kinetic"], random.Random(0), exclude_category="kinetic",
        )
        for p in picks:
            self.assertNotEqual(p.category, "kinetic")

    def test_top_weighted_first(self):
        picks = scenario_pool.pick_six(
            self.powers, ["kinetic", "impact"], random.Random(0),
        )
        # The first pick should have a non-zero score under these tags.
        score = scenario_pool.score_power(picks[0], ["kinetic", "impact"])
        self.assertGreater(score, 0)

    def test_handles_empty_tags(self):
        picks = scenario_pool.pick_six(self.powers, [], random.Random(0))
        self.assertEqual(len(picks), 6)

    def test_deterministic_with_seed(self):
        a_ids = [p.id for p in scenario_pool.pick_six(self.powers, ["kinetic"], random.Random(7))]
        b_ids = [p.id for p in scenario_pool.pick_six(self.powers, ["kinetic"], random.Random(7))]
        self.assertEqual(a_ids, b_ids)


class TestCatalogShape(unittest.TestCase):
    """Safety net that the V2 catalog is reachable and non-trivial."""

    def test_catalog_has_200_powers(self):
        self.assertEqual(len(_all_powers()), 200)

    def test_all_six_categories_present(self):
        cats = {p.category for p in _all_powers()}
        self.assertEqual(
            cats,
            {"kinetic", "material", "paradoxic", "spatial", "somatic", "cognitive"},
        )


if __name__ == "__main__":
    unittest.main()
