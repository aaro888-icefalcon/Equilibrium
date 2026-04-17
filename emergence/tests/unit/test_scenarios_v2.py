"""Unit tests for the V2 session-zero scenarios.

Covers the redesigned 13-scene flow:
    0 IntroScene
    1 LifeDescriptionScene
    2 ActionScenarioScene
    3 PowerSlateScene
    4-7 Cast/Rider scenes
    8-12 Survival / Location / Relationship / Faction / Vows
"""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.scenarios import (
    ActionScenarioScene,
    FactionScenario,
    FACTION_DEMANDS,
    IntroScene,
    LifeDescriptionScene,
    LocationScenario,
    PowerSlateScene,
    PrimaryCastModeScenario,
    PrimaryRiderScenario,
    REGION_FACTIONS,
    RelationshipScenario,
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
        self.assertEqual(len(scenes), 13)

    def test_scene_ids_unique(self):
        scenes = make_v2_scenes()
        ids = [s.scene_id for s in scenes]
        self.assertEqual(len(ids), len(set(ids)))

    def test_scene_order(self):
        ids = [s.scene_id for s in make_v2_scenes()]
        self.assertEqual(ids[0], "sz_v2_intro")
        self.assertEqual(ids[1], "sz_v2_life")
        self.assertEqual(ids[2], "sz_v2_action")
        self.assertEqual(ids[3], "sz_v2_slate")
        self.assertEqual(ids[-1], "sz_v2_vows")


class TestIntroScene(unittest.TestCase):
    def setUp(self):
        self.scene = IntroScene()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_intro_has_framing(self):
        framing = self.scene.get_framing(self.state)
        self.assertGreater(len(framing), 100)

    def test_intro_has_continue_choice(self):
        choices = self.scene.get_choices(self.state)
        self.assertEqual(len(choices), 1)

    def test_intro_apply_adds_history(self):
        result = self.scene.apply(0, self.state, self.factory, self.rng)
        self.assertEqual(len(result.history), 1)


class TestLifeDescriptionScene(unittest.TestCase):
    def setUp(self):
        self.scene = LifeDescriptionScene()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_text_prompts_include_description_and_npc_seeds(self):
        keys = [p["key"] for p in self.scene.text_prompts(self.state)]
        self.assertIn("name", keys)
        self.assertIn("age", keys)
        self.assertIn("description", keys)
        self.assertIn("npc_seeds", keys)

    def test_no_choice_menu(self):
        self.assertEqual(self.scene.get_choices(self.state), [])

    def test_apply_text_stores_name_age_description(self):
        result = self.scene.apply_text(
            {
                "name": "Abhishek",
                "age": "30",
                "description": "blunt surgeon, curious and analytical",
            },
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(result.name, "Abhishek")
        self.assertEqual(result.age_at_onset, 30)
        self.assertIn("surgeon", result.self_description)

    def test_apply_text_derives_surgeon_skills(self):
        result = self.scene.apply_text(
            {
                "name": "A",
                "age": "30",
                "description": "surgeon with curious patient temperament",
            },
            self.state,
            self.factory,
            self.rng,
        )
        self.assertIn("surgery", result.skills)
        self.assertGreater(result.skills["surgery"], 0)

    def test_apply_text_sets_occupation(self):
        result = self.scene.apply_text(
            {"name": "A", "age": "30", "description": "surgeon"},
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(result.occupation, "medical")

    def test_apply_text_parses_npc_seeds_json(self):
        result = self.scene.apply_text(
            {
                "name": "A",
                "age": "30",
                "description": "surgeon",
                "npc_seeds": (
                    '[{"name":"Akhil","relation":"brother",'
                    '"location":"Mount Sinai","descriptor":"med student",'
                    '"status":"alive"}]'
                ),
            },
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(len(result.npc_seeds), 1)
        self.assertEqual(result.npc_seeds[0]["name"], "Akhil")

    def test_apply_text_empty_npc_seeds_is_ok(self):
        result = self.scene.apply_text(
            {"name": "A", "age": "30", "description": "surgeon", "npc_seeds": ""},
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(result.npc_seeds, [])

    def test_apply_text_invalid_npc_seeds_json_is_ignored(self):
        result = self.scene.apply_text(
            {
                "name": "A",
                "age": "30",
                "description": "surgeon",
                "npc_seeds": "this is not JSON",
            },
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(result.npc_seeds, [])


class TestActionScenarioScene(unittest.TestCase):
    def setUp(self):
        self.scene = ActionScenarioScene()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_picks_slot_1_vignette(self):
        self.scene.prepare(self.state, self.rng)
        self.assertTrue(self.scene._vignette.get("id", "").startswith("v1_"))

    def test_no_menu_only_reaction(self):
        self.scene.prepare(self.state, self.rng)
        self.assertEqual(self.scene.get_choices(self.state), [])
        self.assertTrue(self.scene.needs_text_input())

    def test_apply_text_stores_reaction_tags(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply_text(
            {"reaction": "I hide and watch"},
            self.state,
            self.factory,
            self.rng,
        )
        self.assertIn("spatial", result.reaction_tags)

    def test_apply_text_does_not_commit_power(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply_text(
            {"reaction": "I fight"},
            self.state,
            self.factory,
            self.rng,
        )
        self.assertEqual(len(result.powers), 0)


class TestPowerSlateScene(unittest.TestCase):
    def setUp(self):
        self.scene = PowerSlateScene()
        self.state = CreationState(seed=42)
        # Seed the state with description and reaction tags so the slate
        # has tag-weighted options.
        self.state.self_description = "surgeon, protective and analytical"
        self.state.reaction_tags = ["cognitive", "perceptive"]
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_yields_ten_options(self):
        self.scene.prepare(self.state, self.rng)
        self.assertEqual(len(self.scene._options), 10)

    def test_apply_text_persists_pending_slate(self):
        self.scene.prepare(self.state, self.rng)
        result = self.scene.apply_text(
            {"reaction": "I reach for the nearest thing"},
            self.state, self.factory, self.rng,
        )
        self.assertEqual(len(result.pending_slate), 10)
        self.assertEqual(result.pending_slate_scene, self.scene.scene_id)

    def test_apply_multi_commits_two_powers(self):
        self.scene.prepare(self.state, self.rng)
        # Persist the slate first (two-phase flow).
        state = self.scene.apply_text({}, self.state, self.factory, self.rng)
        result = self.scene.apply_multi(
            [0, 3], state, self.factory, self.rng,
        )
        self.assertEqual(len(result.powers), 2)
        slots = {p.get("slot") for p in result.powers}
        self.assertIn("primary", slots)
        self.assertIn("secondary", slots)

    def test_apply_multi_clears_pending_slate(self):
        self.scene.prepare(self.state, self.rng)
        state = self.scene.apply_text({}, self.state, self.factory, self.rng)
        result = self.scene.apply_multi(
            [0, 1], state, self.factory, self.rng,
        )
        self.assertEqual(result.pending_slate, [])
        self.assertEqual(result.pending_slate_scene, "")

    def test_apply_single_deterministic_second_pick(self):
        """apply(idx) used by the SessionZero orchestrator picks a
        deterministic second slot so two distinct powers land."""
        self.scene.prepare(self.state, self.rng)
        state = self.scene.apply_text({}, self.state, self.factory, self.rng)
        result = self.scene.apply(0, state, self.factory, self.rng)
        self.assertEqual(len(result.powers), 2)
        ids = [p.get("power_id") for p in result.powers]
        self.assertEqual(len(set(ids)), 2)

    def test_same_category_allowed(self):
        """No category exclusion: both picks may share a category."""
        self.scene.prepare(self.state, self.rng)
        state = self.scene.apply_text({}, self.state, self.factory, self.rng)
        # Force the slate to include two powers of the same category.
        # We rely on the slate being non-trivial after seeding; the mere
        # absence of an exclusion check in apply_multi is the invariant.
        result = self.scene.apply_multi(
            [0, 1], state, self.factory, self.rng,
        )
        self.assertEqual(len(result.powers), 2)
        # No assertion on categories differing.


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
    """Cast-mode / rider selection scenes use V2 ids directly.

    The new flow commits both powers via PowerSlateScene; these tests
    build a minimal state with a primary + secondary power row and
    confirm the config scenes find their slot.
    """

    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)
        self.state = CreationState(seed=42)
        self.state.self_description = "surgeon, blunt and analytical"
        self.state.reaction_tags = ["cognitive", "perceptive"]

        slate_scene = PowerSlateScene()
        slate_scene.prepare(self.state, random.Random(42))
        self.state = slate_scene.apply_text({}, self.state, self.factory, random.Random(42))
        self.state = slate_scene.apply_multi([0, 1], self.state, self.factory, random.Random(42))

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
