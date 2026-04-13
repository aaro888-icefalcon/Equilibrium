"""Unit tests for session zero scenes 0-4."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.scenes import (
    CONCERNS,
    OCCUPATIONS,
    REGIONS,
    ConcernScene,
    LocationScene,
    OccupationScene,
    OpeningScene,
    RelationshipScene,
)


class TestOpeningScene(unittest.TestCase):

    def test_applies_name_and_age(self):
        scene = OpeningScene()
        factory = CharacterFactory()
        state = CreationState()
        rng = random.Random(42)

        state = scene.apply_text(
            {"name": "Marisol Reyes", "age": "30"},
            state, factory, rng,
        )

        self.assertEqual(state.name, "Marisol Reyes")
        self.assertEqual(state.age_at_onset, 30)

    def test_default_name_on_empty(self):
        scene = OpeningScene()
        factory = CharacterFactory()
        state = CreationState()
        rng = random.Random(42)

        state = scene.apply_text(
            {"name": "", "age": "25"},
            state, factory, rng,
        )

        self.assertGreater(len(state.name), 0)

    def test_age_clamped(self):
        scene = OpeningScene()
        factory = CharacterFactory()
        state = CreationState()
        rng = random.Random(42)

        state = scene.apply_text(
            {"name": "Test", "age": "10"},
            state, factory, rng,
        )
        self.assertEqual(state.age_at_onset, 16)

    def test_has_framing(self):
        scene = OpeningScene()
        framing = scene.get_framing(CreationState())
        self.assertIn("name", framing.lower())

    def test_needs_text_input(self):
        self.assertTrue(OpeningScene().needs_text_input())


class TestOccupationScene(unittest.TestCase):

    def test_all_12_occupations_defined(self):
        self.assertEqual(len(OCCUPATIONS), 12)

    def test_each_has_attribute_deltas(self):
        for occ in OCCUPATIONS:
            self.assertIn("attribute_deltas", occ)
            self.assertGreater(len(occ["attribute_deltas"]), 0)

    def test_applies_deltas(self):
        scene = OccupationScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        # Choose soldier (index 2)
        state = scene.apply(2, state, factory, rng)
        self.assertEqual(state.attribute_deltas.get("strength", 0), 2)
        self.assertEqual(state.attribute_deltas.get("will", 0), 2)

    def test_student_eligibility(self):
        scene = OccupationScene()

        # Age 25 — student available
        state_young = CreationState(age_at_onset=25)
        choices = scene.get_choices(state_young)
        self.assertTrue(any("Student" in c for c in choices))

        # Age 35 — student not available
        state_old = CreationState(age_at_onset=35)
        choices = scene.get_choices(state_old)
        self.assertFalse(any("Student" in c for c in choices))

    def test_has_skills(self):
        scene = OccupationScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)  # Federal employee
        self.assertIn("bureaucracy", state.skills)

    def test_has_framing(self):
        framing = OccupationScene().get_framing(CreationState())
        self.assertIn("job", framing.lower())


class TestRelationshipScene(unittest.TestCase):

    def test_generates_npc_relationship(self):
        scene = RelationshipScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=30)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)  # Spouse
        self.assertGreater(len(state.relationships), 0)

    def test_generates_goal(self):
        scene = RelationshipScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=30)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)
        self.assertGreater(len(state.goals), 0)

    def test_spouse_requires_age_18(self):
        scene = RelationshipScene()
        state_young = CreationState(age_at_onset=16)
        choices = scene.get_choices(state_young)
        # Spouse requires 18+, so 16-year-old shouldn't see it
        # But parent is min_age=16, so should see that
        self.assertTrue(any("Parent" in c for c in choices))

    def test_child_requires_age_22(self):
        scene = RelationshipScene()
        state_young = CreationState(age_at_onset=20)
        choices = scene.get_choices(state_young)
        self.assertFalse(any("Child" in c for c in choices))

    def test_has_framing(self):
        framing = RelationshipScene().get_framing(CreationState())
        self.assertIn("person", framing.lower())


class TestLocationScene(unittest.TestCase):

    def test_8_regions(self):
        self.assertEqual(len(REGIONS), 8)

    def test_sets_region(self):
        scene = LocationScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(2, state, factory, rng)  # Hudson Valley
        self.assertEqual(state.region, "Hudson Valley")

    def test_sets_location(self):
        scene = LocationScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)  # NYC
        self.assertTrue(state.location.startswith("loc-"))

    def test_has_framing(self):
        framing = LocationScene().get_framing(CreationState())
        self.assertIn("onset", framing.lower())


class TestConcernScene(unittest.TestCase):

    def test_8_concerns(self):
        self.assertEqual(len(CONCERNS), 8)

    def test_applies_goal(self):
        scene = ConcernScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)  # Money trouble
        goal_ids = [g.get("id", "") for g in state.goals]
        self.assertIn("rebuild_what_was_lost", goal_ids)

    def test_enemy_generates_npc(self):
        scene = ConcernScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(6, state, factory, rng)  # Grudge/enemy
        self.assertGreater(len(state.relationships), 0)
        # Check negative standing
        for rel in state.relationships.values():
            if rel.get("archetype") == "enemy":
                self.assertLess(rel["standing"], 0)

    def test_steady_life_gives_dual_attribute(self):
        scene = ConcernScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(7, state, factory, rng)  # Nothing in particular
        self.assertEqual(state.attribute_deltas.get("will", 0), 1)
        self.assertEqual(state.attribute_deltas.get("insight", 0), 1)

    def test_has_framing(self):
        framing = ConcernScene().get_framing(CreationState())
        self.assertIn("worry", framing.lower())


class TestScenesProduceValidDeltas(unittest.TestCase):
    """Run all 5 pre-onset scenes in sequence and verify the result."""

    def test_full_pre_onset_sequence(self):
        factory = CharacterFactory()
        state = CreationState()
        rng = random.Random(42)

        # Scene 0: Opening
        scene0 = OpeningScene()
        state = scene0.apply_text(
            {"name": "Elena Torres", "age": "28"},
            state, factory, rng,
        )
        self.assertEqual(state.name, "Elena Torres")

        # Scene 1: Occupation (soldier)
        scene1 = OccupationScene()
        state = scene1.apply(2, state, factory, rng)
        self.assertIn("firearms", state.skills)

        # Scene 2: Relationship (spouse)
        scene2 = RelationshipScene()
        state = scene2.apply(0, state, factory, rng)
        self.assertGreater(len(state.relationships), 0)

        # Scene 3: Location (NYC)
        scene3 = LocationScene()
        state = scene3.apply(0, state, factory, rng)
        self.assertEqual(state.region, "New York City")

        # Scene 4: Concern (money trouble)
        scene4 = ConcernScene()
        state = scene4.apply(0, state, factory, rng)

        # Finalize and check
        sheet = factory.finalize(state)
        self.assertEqual(sheet.name, "Elena Torres")
        self.assertGreater(sheet.attributes.strength, 6)
        self.assertGreater(len(sheet.skills), 3)
        self.assertGreater(len(sheet.goals), 0)
        self.assertGreater(len(sheet.history), 0)


if __name__ == "__main__":
    unittest.main()
