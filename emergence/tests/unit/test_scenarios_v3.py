"""Unit tests for the V3 session-zero scenarios — 5 long-form scenes."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.scenarios_v3 import (
    AwakeningScene,
    FirstYearScene,
    OnsetAndBiographyScene,
    PowersConfigScene,
    StandingAndVowsScene,
    make_v3_scenes,
)


class TestMakeV3Scenes(unittest.TestCase):
    def test_scene_count(self):
        scenes = make_v3_scenes()
        self.assertEqual(len(scenes), 5)

    def test_scene_ids(self):
        ids = [s.scene_id for s in make_v3_scenes()]
        self.assertEqual(ids, [
            "sz_v3_onset_bio",
            "sz_v3_awakening",
            "sz_v3_powers_config",
            "sz_v3_first_year",
            "sz_v3_standing_vows",
        ])


class TestOnsetAndBiographyScene(unittest.TestCase):
    def setUp(self):
        self.scene = OnsetAndBiographyScene()
        self.state = CreationState(seed=42)
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_scenario_code_has_setting_details(self):
        code = self.scene.get_scenario_code(self.state)
        self.assertIn("setting_details", code)
        self.assertIn("regions", code["setting_details"])

    def test_text_prompts_include_name_age_description_npc_seeds(self):
        keys = [p["key"] for p in self.scene.text_prompts(self.state)]
        for k in ("name", "age", "description", "npc_seeds"):
            self.assertIn(k, keys)

    def test_apply_text_sets_name_and_occupation(self):
        result = self.scene.apply_text(
            {"name": "Ada", "age": "28", "description": "surgeon", "npc_seeds": ""},
            self.state, self.factory, self.rng,
        )
        self.assertEqual(result.name, "Ada")
        self.assertEqual(result.age_at_onset, 28)
        self.assertEqual(result.occupation, "medical")

    def test_apply_text_parses_npc_seeds(self):
        result = self.scene.apply_text(
            {
                "name": "Ada", "age": "28", "description": "surgeon",
                "npc_seeds": (
                    '[{"name":"Jason","relation":"senior_resident",'
                    '"location":"Bellevue","descriptor":"wry",'
                    '"status":"alive"}]'
                ),
            },
            self.state, self.factory, self.rng,
        )
        self.assertEqual(len(result.npc_seeds), 1)
        self.assertEqual(result.npc_seeds[0]["name"], "Jason")


class TestAwakeningScene(unittest.TestCase):
    def setUp(self):
        self.scene = AwakeningScene()
        self.state = CreationState(seed=42)
        self.state.self_description = "surgeon curious and analytical"
        self.state.reaction_tags = ["cognitive"]
        self.factory = CharacterFactory()
        self.rng = random.Random(42)

    def test_prepare_yields_slate_and_vignette(self):
        self.scene.prepare(self.state, self.rng)
        self.assertEqual(len(self.scene._options), 10)
        self.assertTrue(self.scene._vignette.get("id", "").startswith("v1_"))

    def test_scenario_code_has_power_slate(self):
        self.scene.prepare(self.state, self.rng)
        code = self.scene.get_scenario_code(self.state)
        self.assertEqual(len(code["power_slate"]), 10)
        for entry in code["power_slate"]:
            self.assertIn("category", entry)
            self.assertIn("identity", entry)

    def test_apply_text_then_apply_multi_commits_two_powers(self):
        self.scene.prepare(self.state, self.rng)
        state = self.scene.apply_text(
            {"reaction": "I study"}, self.state, self.factory, self.rng,
        )
        self.assertEqual(len(state.pending_slate), 10)
        state = self.scene.apply_multi([0, 1], state, self.factory, self.rng)
        self.assertEqual(len(state.powers), 2)
        self.assertEqual(state.tier, 3)
        self.assertEqual(state.pending_slate, [])


class TestPowersConfigScene(unittest.TestCase):
    def setUp(self):
        # Bootstrap state with two committed powers via AwakeningScene.
        self.factory = CharacterFactory()
        self.rng = random.Random(42)
        self.state = CreationState(seed=42)
        self.state.self_description = "surgeon curious and analytical"
        self.state.reaction_tags = ["cognitive"]
        aw = AwakeningScene()
        aw.prepare(self.state, random.Random(42))
        self.state = aw.apply_text({}, self.state, self.factory, random.Random(42))
        self.state = aw.apply_multi([0, 1], self.state, self.factory, random.Random(42))

    def test_prepare_loads_casts_and_riders_for_both_powers(self):
        scene = PowersConfigScene()
        scene.prepare(self.state, self.rng)
        self.assertGreater(len(scene._primary_casts), 0)
        self.assertGreater(len(scene._primary_riders), 0)
        self.assertGreater(len(scene._secondary_casts), 0)
        self.assertGreater(len(scene._secondary_riders), 0)

    def test_must_state_mechanics_includes_verbatim_strings(self):
        scene = PowersConfigScene()
        scene.prepare(self.state, self.rng)
        mech = scene.get_must_state_mechanics(self.state)
        self.assertGreater(len(mech), 0)
        joined = " ".join(mech)
        # Verbatim substrings: range, duration, pool cost, action.
        self.assertIn("range:", joined)
        self.assertIn("duration:", joined)
        self.assertIn("pool cost:", joined)
        self.assertIn("action", joined)

    def test_choice_groups_has_four_slices(self):
        scene = PowersConfigScene()
        scene.prepare(self.state, self.rng)
        groups = scene.get_choice_groups(self.state)
        self.assertEqual(len(groups), 4)
        labels = [g["label"] for g in groups]
        self.assertTrue(any("cast" in l for l in labels))
        self.assertTrue(any("rider" in l for l in labels))

    def test_apply_multi_writes_selections_onto_power_entries(self):
        scene = PowersConfigScene()
        scene.prepare(self.state, self.rng)
        state = scene.apply_multi([0, 0, 0, 0], self.state, self.factory, self.rng)
        for p in state.powers:
            self.assertIn("selected_cast_mode", p)
            self.assertIn("selected_rider", p)


class TestFirstYearScene(unittest.TestCase):
    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)
        self.state = CreationState(
            seed=42,
            narrative_tags=["medical"],
            npc_seeds=[{
                "name": "Jason",
                "relation": "senior_resident",
                "location": "Bellevue",
                "descriptor": "wry",
                "status": "alive",
                "seed_index": 0,
            }],
        )

    def test_prepare_presents_five_survival_scenarios(self):
        scene = FirstYearScene()
        scene.prepare(self.state, self.rng)
        self.assertLessEqual(len(scene._presented_survival), 5)
        self.assertGreater(len(scene._presented_survival), 0)

    def test_scenario_code_exposes_three_groups(self):
        scene = FirstYearScene()
        scene.prepare(self.state, self.rng)
        code = scene.get_scenario_code(self.state)
        self.assertIn("regions_available", code)
        self.assertIn("survival_scenarios", code)
        self.assertIn("relationship_webs", code)

    def test_apply_multi_sets_region_and_relationships(self):
        scene = FirstYearScene()
        scene.prepare(self.state, self.rng)
        state = scene.apply_multi([0, 0, 0], self.state, self.factory, self.rng)
        self.assertTrue(state.region)
        self.assertTrue(state.location)
        self.assertGreater(len(state.relationships), 0)


class TestStandingAndVowsScene(unittest.TestCase):
    def setUp(self):
        self.factory = CharacterFactory()
        self.rng = random.Random(42)
        self.state = CreationState(
            seed=42,
            region="Northern New Jersey",
            npc_seeds=[],
        )

    def test_prepare_resolves_faction_rep(self):
        scene = StandingAndVowsScene()
        scene.prepare(self.state, self.rng)
        self.assertTrue(scene._rep_name)
        self.assertEqual(scene._faction["id"], "iron-crown")

    def test_apply_multi_two_vows_yields_multiple_goals(self):
        scene = StandingAndVowsScene()
        scene.prepare(self.state, self.rng)
        state = scene.apply_multi([0, 0, 1], self.state, self.factory, self.rng)
        # At least 1 posture goal + 2 vows × ~2 goals each = ≥5 goals.
        self.assertGreaterEqual(len(state.goals), 3)

    def test_threat_top_up_guarantees_two_threats(self):
        scene = StandingAndVowsScene()
        scene.prepare(self.state, self.rng)
        state = scene.apply_multi([0, 0, 1], self.state, self.factory, self.rng)
        self.assertGreaterEqual(len(state.threats), 2)

    def test_play_posture_makes_rep_a_threat(self):
        scene = StandingAndVowsScene()
        scene.prepare(self.state, self.rng)
        # posture index 3 = "play"
        state = scene.apply_multi([3, 0, 1], self.state, self.factory, self.rng)
        rep_ids = {t.get("npc_id") for t in state.threats}
        self.assertIn(scene._rep_id, rep_ids)


class TestThreatsFinalize(unittest.TestCase):
    """Verify finalize() merges threats into relationships and sheet.threats."""

    def test_finalize_carries_threats_to_sheet(self):
        factory = CharacterFactory()
        state = CreationState(seed=42)
        state.threats.append({
            "npc_id": "npc-test-foe",
            "name": "Kato",
            "standing": -3,
            "source": "test",
            "summary": "test foe",
        })
        sheet = factory.finalize(state)
        self.assertEqual(len(sheet.threats), 1)
        self.assertEqual(sheet.threats[0]["name"], "Kato")
        # Threat also lands in relationships as negative standing.
        self.assertIn("npc-test-foe", sheet.relationships)
        self.assertEqual(sheet.relationships["npc-test-foe"].standing, -3)


if __name__ == "__main__":
    unittest.main()
