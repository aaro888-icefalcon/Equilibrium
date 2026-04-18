"""Tests for the deterministic bucket sampler in JobBundleScene.

The sampler narrows the location's archetype pool to five archetypes that
satisfy the plan's bucket minimums before the narrator writes cards. These
tests verify that every location in data/job_archetypes.json can satisfy
the minimums, and that the sampler's output is stable under a fixed seed.
"""

from __future__ import annotations

import random
import unittest

from emergence.engine.character_creation.job_bundle_scene import (
    BUCKET_MIN,
    BUNDLE_CARDS_REQUIRED,
    JobBundleScene,
)


class TestBucketSampler(unittest.TestCase):
    def setUp(self) -> None:
        self.scene = JobBundleScene()
        self.pools = self.scene._load_archetypes()

    def test_every_location_samples_five_cards(self) -> None:
        for loc_id, pool in self.pools.items():
            with self.subTest(location=loc_id):
                rng = random.Random(42)
                picked = self.scene.sample_archetypes(pool, rng, BUNDLE_CARDS_REQUIRED)
                self.assertEqual(len(picked), BUNDLE_CARDS_REQUIRED)
                ids = [a["id"] for a in picked]
                self.assertEqual(len(set(ids)), BUNDLE_CARDS_REQUIRED, f"duplicate ids in {loc_id}")

    def test_every_location_satisfies_bucket_minimums(self) -> None:
        for loc_id, pool in self.pools.items():
            with self.subTest(location=loc_id):
                rng = random.Random(42)
                picked = self.scene.sample_archetypes(pool, rng, BUNDLE_CARDS_REQUIRED)
                for bucket, minimum in BUCKET_MIN.items():
                    count = sum(1 for a in picked if bucket in (a.get("theme_tags") or []))
                    self.assertGreaterEqual(
                        count, minimum,
                        f"{loc_id}: bucket {bucket!r} got {count}, expected >= {minimum}"
                    )

    def test_sampler_deterministic_under_fixed_seed(self) -> None:
        loc_id = "manhattan_fragment"
        pool = self.pools[loc_id]
        rng1 = random.Random(7)
        rng2 = random.Random(7)
        picked1 = [a["id"] for a in self.scene.sample_archetypes(pool, rng1)]
        picked2 = [a["id"] for a in self.scene.sample_archetypes(pool, rng2)]
        self.assertEqual(picked1, picked2)

    def test_sampler_raises_when_pool_too_small(self) -> None:
        tiny_pool = [
            {"id": "a1", "theme_tags": ["old_skills"]},
            {"id": "a2", "theme_tags": ["old_skills"]},
        ]
        with self.assertRaises(RuntimeError):
            self.scene.sample_archetypes(tiny_pool, random.Random(0), 5)

    def test_all_20_locations_present(self) -> None:
        self.assertEqual(len(self.pools), 20)


if __name__ == "__main__":
    unittest.main()
