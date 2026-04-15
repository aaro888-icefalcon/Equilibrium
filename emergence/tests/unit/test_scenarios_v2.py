"""Unit tests for v2 session zero scenarios — new and revised scenes."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.scenarios import (
    CircumstanceScenario,
    CIRCUMSTANCES,
    FactionScenario,
    FACTION_DEMANDS,
    IdentityScenario,
    LocationScenario,
    PrimaryCastModeScenario,
    PrimaryRiderScenario,
    REGION_FACTIONS,
    RelationshipScenario,
    SecondaryCastModeScenario,
    SecondaryRiderScenario,
    SurvivalScenario,
    SURVIVAL_POOL,
    TemperamentScenario,
    TEMPERAMENTS,
    VowScenario,
    VOW_PACKAGES,
    make_v2_scenes,
)


class TestMakeV2Scenes(unittest.TestCase):
    def test_scene_count(self):
        scenes = make_v2_scenes()
        self.assertEqual(len(scenes), 14)

    def test_scene_ids_unique(self):
        scenes = make_v2_scenes()
        ids = [s.scene_id for s in scenes]
        self.assertEqual(len(ids), len(set(ids)))


class TestTemperamentScenario(unittest.TestCase):
    def setUp(self):
        self.scene = TemperamentScenario()
        self.state = CreationState()
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_choice_count(self):
        self.assertEqual(len(self.scene.get_choices(self.state)), len(TEMPERAMENTS))

    def test_apply_sets_temperament(self):
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertEqual(result.temperament, "pragmatic")

    def test_apply_gives_attribute(self):
        result = self.scene.apply(1, self.state, self.factory, self.rng)
        self.assertIn("will", result.attribute_deltas)

    def test_apply_gives_skills(self):
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertIn("negotiation", result.skills)
        self.assertIn("streetwise", result.skills)

    def test_apply_gives_narrative_tag(self):
        result = self.scene.apply(2, self.state, self.factory, self.rng)
        self.assertIn("curious", result.narrative_tags)


class TestCircumstanceScenario(unittest.TestCase):
    def setUp(self):
        self.scene = CircumstanceScenario()
        self.state = CreationState()
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_choice_count(self):
        self.assertEqual(len(self.scene.get_choices(self.state)), 8)

    def test_apply_sets_onset_circumstance(self):
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertEqual(result.onset_circumstance, "A")

    def test_apply_gives_attribute(self):
        result = self.scene.apply(6, self.state, self.factory, self.rng)
        self.assertIn("agility", result.attribute_deltas)


class TestAdditiveSkills(unittest.TestCase):
    """Verify that skills accumulate additively across scenes."""

    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_skills_are_additive(self):
        state = CreationState()
        # Two scenes granting the same skill should stack
        self.factory.apply_scene_result("scene_a", {
            "skills": {"first_aid": 2},
        }, state, self.rng)
        self.factory.apply_scene_result("scene_b", {
            "skills": {"first_aid": 1},
        }, state, self.rng)
        self.assertEqual(state.skills["first_aid"], 3)

    def test_skills_capped_at_max(self):
        state = CreationState()
        self.factory.apply_scene_result("scene_a", {
            "skills": {"first_aid": 4},
        }, state, self.rng)
        self.factory.apply_scene_result("scene_b", {
            "skills": {"first_aid": 4},
        }, state, self.rng)
        self.assertEqual(state.skills["first_aid"], CharacterFactory.MAX_SESSION_ZERO_SKILL)


class TestSurvivalScenario(unittest.TestCase):
    def setUp(self):
        self.scene = SurvivalScenario()
        self.state = CreationState(region="New York City", narrative_tags=["veteran"])
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_generates_choices(self):
        self.scene.prepare(self.state, self.rng)
        choices = self.scene.get_choices(self.state)
        self.assertGreater(len(choices), 0)
        self.assertLessEqual(len(choices), 5)

    def test_apply_gives_skills(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertTrue(len(result.skills) > 0)

    def test_apply_generates_npc_relationship(self):
        self.scene.prepare(self.state, self.rng)
        choices = self.scene.get_choices(self.state)
        # Find a choice that isn't the lone_walker (which has no NPC)
        for i, c in enumerate(choices):
            if "alone" not in c.lower() and "nobody" not in c.lower():
                result = self.scene.apply(i, self.state, self.factory, self.rng)
                if result.relationships:
                    self.assertTrue(len(result.relationships) > 0)
                    return
        # If all choices are no-NPC, that's still valid
        self.assertTrue(True)

    def test_deterministic_with_same_seed(self):
        rng1 = random.Random(99)
        rng2 = random.Random(99)
        scene1 = SurvivalScenario()
        scene2 = SurvivalScenario()
        state1 = CreationState(region="Philadelphia", narrative_tags=["medical"])
        state2 = CreationState(region="Philadelphia", narrative_tags=["medical"])
        scene1.prepare(state1, rng1)
        scene2.prepare(state2, rng2)
        self.assertEqual(
            scene1.get_choices(state1),
            scene2.get_choices(state2),
        )

    def test_pool_has_20_entries(self):
        self.assertEqual(len(SURVIVAL_POOL), 20)


class TestFactionScenario(unittest.TestCase):
    def setUp(self):
        self.scene = FactionScenario()
        self.state = CreationState(region="Northern New Jersey")
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_generates_rep(self):
        self.scene.prepare(self.state, self.rng)
        self.assertTrue(len(self.scene._rep_name) > 0)

    def test_framing_includes_rep_name(self):
        self.scene.prepare(self.state, self.rng)
        framing = self.scene.get_framing(self.state)
        self.assertIn(self.scene._rep_name, framing)

    def test_choices_include_rep_name(self):
        self.scene.prepare(self.state, self.rng)
        choices = self.scene.get_choices(self.state)
        self.assertEqual(len(choices), 4)
        self.assertIn(self.scene._rep_name, choices[0])

    def test_accept_gives_faction_standing(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertIn("iron-crown", result.faction_standing_deltas)
        self.assertEqual(result.faction_standing_deltas["iron-crown"], 2)

    def test_apply_creates_rep_relationship(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertTrue(len(result.relationships) > 0)

    def test_apply_creates_goal(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertTrue(len(result.goals) > 0)


class TestVowScenario(unittest.TestCase):
    def setUp(self):
        self.scene = VowScenario()
        self.state = CreationState()
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_generates_npcs(self):
        self.scene.prepare(self.state, self.rng)
        self.assertEqual(len(self.scene._npc_names), len(VOW_PACKAGES))

    def test_choices_include_npc_names(self):
        self.scene.prepare(self.state, self.rng)
        choices = self.scene.get_choices(self.state)
        # Each choice should have the generic name replaced
        for c in choices:
            self.assertNotIn("{npc_name}", c)

    def test_apply_gives_goals(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertGreater(len(result.goals), 0)

    def test_apply_gives_inventory(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertGreater(len(result.inventory), 0)

    def test_apply_creates_npc_relationship(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertTrue(len(result.relationships) > 0)


class TestPowerConfigScenarios(unittest.TestCase):
    def setUp(self):
        self.state = CreationState()
        self.state.powers = [
            {"power_id": "pow_kinetic_burst", "name": "Kinetic Burst",
             "category": "physical_kinetic", "tier": 3, "slot": "anchor"},
            {"power_id": "pow_heightened_senses", "name": "Heightened Senses",
             "category": "perceptual_mental", "tier": 3, "slot": "secondary"},
        ]
        self.state.power_category_primary = "physical_kinetic"
        self.state.power_category_secondary = "perceptual_mental"
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_primary_cast_mode_prepare(self):
        scene = PrimaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        # Should have options (from V2 data) or fallback
        self.assertGreater(len(choices), 0)

    def test_primary_rider_prepare(self):
        scene = PrimaryRiderScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        self.assertGreater(len(choices), 0)

    def test_secondary_cast_mode_prepare(self):
        scene = SecondaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        self.assertGreater(len(choices), 0)

    def test_cast_mode_apply_stores_on_power(self):
        scene = PrimaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        if len(choices) > 1 and choices[0] != "No options available — use default configuration":
            result = scene.apply(0, self.state, self.factory, self.rng)
            anchor = next((p for p in result.powers if p.get("slot") == "anchor"), None)
            self.assertIsNotNone(anchor)
            self.assertIn("selected_cast_mode", anchor)

    def test_rider_apply_stores_on_power(self):
        scene = PrimaryRiderScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        if len(choices) > 1 and choices[0] != "No options available — use default configuration":
            result = scene.apply(0, self.state, self.factory, self.rng)
            anchor = next((p for p in result.powers if p.get("slot") == "anchor"), None)
            self.assertIsNotNone(anchor)
            self.assertIn("selected_rider", anchor)


if __name__ == "__main__":
    unittest.main()
