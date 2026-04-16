"""Unit tests for the V2 session-zero scenarios (12-scene flow)."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.scenarios import (
    FactionScenario,
    FACTION_DEMANDS,
    IdentityScenario,
    LocationScenario,
    PrimaryCastModeScenario,
    PrimaryRiderScenario,
    REGION_FACTIONS,
    RelationshipScenario,
    Scenario1Scenario,
    Scenario2Scenario,
    SecondaryCastModeScenario,
    SecondaryRiderScenario,
    SurvivalScenario,
    SURVIVAL_POOL,
    V2_CATEGORY_LABELS,
    VowScenario,
    VOW_PACKAGES,
    make_v2_scenes,
)


class TestMakeV2Scenes(unittest.TestCase):
    def test_scene_count(self):
        scenes = make_v2_scenes()
        self.assertEqual(len(scenes), 12)

    def test_scene_ids_unique(self):
        scenes = make_v2_scenes()
        ids = [s.scene_id for s in scenes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_scene_order(self):
        ids = [s.scene_id for s in make_v2_scenes()]
        self.assertEqual(ids[0], "sz_v2_identity")
        self.assertEqual(ids[1], "sz_v2_scenario1")
        self.assertEqual(ids[2], "sz_v2_scenario2")
        self.assertEqual(ids[-1], "sz_v2_vows")


class TestIdentityScenario(unittest.TestCase):
    def setUp(self):
        self.scene = IdentityScenario()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_text_prompts_include_description(self):
        keys = [p["key"] for p in self.scene.text_prompts(self.state)]
        self.assertIn("name", keys)
        self.assertIn("age", keys)
        self.assertIn("description", keys)

    def test_apply_text_stores_description_and_tags(self):
        result = self.scene.apply_text(
            {"name": "Abhishek", "age": "30",
             "description": "blunt surgeon, protective and analytical"},
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(result.name, "Abhishek")
        self.assertEqual(result.age_at_onset, 30)
        self.assertIn("blunt", result.self_description.lower())
        self.assertGreater(len(result.reaction_tags), 0)


class TestScenario1Scenario(unittest.TestCase):
    def setUp(self):
        self.scene = Scenario1Scenario()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_selects_slot_1_vignette(self):
        self.scene.prepare(self.state, self.rng)
        self.assertTrue(self.scene._vignette.get("id", "").startswith("v1_"))

    def test_always_returns_six_choices(self):
        self.scene.prepare(self.state, self.rng)
        self.assertEqual(len(self.scene.get_choices(self.state)), 6)

    def test_apply_commits_v2_power_at_tier_3(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertEqual(len(result.powers), 1)
        power = result.powers[0]
        self.assertEqual(power["slot"], "anchor")
        self.assertEqual(power["tier"], 3)
        self.assertIn(power["category"], V2_CATEGORY_LABELS)
        self.assertEqual(result.tier, 3)
        self.assertEqual(result.tier_ceiling, 5)


class TestScenario2Scenario(unittest.TestCase):
    def setUp(self):
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()

        # Seed scene 1 first so scene 2 knows what to exclude.
        s1 = Scenario1Scenario()
        s1.prepare(self.state, random.Random(42))
        self.state = s1.apply(0, self.state, self.factory, random.Random(42))

        self.scene = Scenario2Scenario()
        self.rng = random.Random(42)

    def test_prepare_selects_slot_2_vignette(self):
        self.scene.prepare(self.state, self.rng)
        self.assertTrue(self.scene._vignette.get("id", "").startswith("v2_"))

    def test_options_exclude_primary_category(self):
        primary = self.state.power_category_primary
        self.scene.prepare(self.state, self.rng)
        for p in self.scene._options:
            self.assertNotEqual(p.category, primary)

    def test_apply_commits_secondary(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        anchor = [p for p in result.powers if p["slot"] == "anchor"]
        secondary = [p for p in result.powers if p["slot"] == "secondary"]
        self.assertEqual(len(anchor), 1)
        self.assertEqual(len(secondary), 1)
        self.assertNotEqual(anchor[0]["category"], secondary[0]["category"])


class TestAdditiveSkills(unittest.TestCase):
    """Verify that skills accumulate additively across scenes."""

    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_skills_are_additive(self):
        state = CreationState()
        self.factory.apply_scene_result("scene_a", {"skills": {"first_aid": 2}}, state, self.rng)
        self.factory.apply_scene_result("scene_b", {"skills": {"first_aid": 1}}, state, self.rng)
        self.assertEqual(state.skills["first_aid"], 3)

    def test_skills_capped_at_max(self):
        state = CreationState()
        self.factory.apply_scene_result("scene_a", {"skills": {"first_aid": 4}}, state, self.rng)
        self.factory.apply_scene_result("scene_b", {"skills": {"first_aid": 4}}, state, self.rng)
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

    def test_accept_gives_faction_standing(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertIn("iron-crown", result.faction_standing_deltas)
        self.assertEqual(result.faction_standing_deltas["iron-crown"], 2)


class TestVowScenario(unittest.TestCase):
    def setUp(self):
        self.scene = VowScenario()
        self.state = CreationState()
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_apply_gives_goals(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertGreater(len(result.goals), 0)

    def test_apply_gives_inventory(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertGreater(len(result.inventory), 0)


class TestPowerConfigScenarios(unittest.TestCase):
    """Cast-mode / rider selection scenes use V2 ids directly."""

    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)
        self.state = CreationState(seed=42)

        # Build an anchor + secondary via the scenario scenes, so the
        # power_id values in state match real V2 entries.
        s1 = Scenario1Scenario()
        s1.prepare(self.state, random.Random(42))
        self.state = s1.apply(0, self.state, self.factory, random.Random(42))

        s2 = Scenario2Scenario()
        s2.prepare(self.state, random.Random(43))
        self.state = s2.apply(0, self.state, self.factory, random.Random(43))

    def test_primary_cast_mode_prepare_finds_options(self):
        scene = PrimaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        self.assertGreater(len(choices), 0)

    def test_primary_rider_prepare_finds_options(self):
        scene = PrimaryRiderScenario()
        scene.prepare(self.state, self.rng)
        choices = scene.get_choices(self.state)
        self.assertGreater(len(choices), 0)

    def test_cast_mode_has_narrative_prompt(self):
        scene = PrimaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        prompts = scene.text_prompts(self.state)
        self.assertEqual(len(prompts), 1)
        self.assertEqual(prompts[0]["key"], "narrative")

    def test_cast_mode_narrative_awards_skill(self):
        scene = PrimaryCastModeScenario()
        scene.prepare(self.state, self.rng)
        result = scene.apply_text(
            {"narrative": "My senior resident Jason saw me do it first."},
            self.state, self.factory, self.rng,
        )
        self.assertIn(scene._narrative_skill, result.skills)


if __name__ == "__main__":
    unittest.main()
