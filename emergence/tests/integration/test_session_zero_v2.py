"""Integration tests for the V2 session-zero flow — full 13-scene character creation."""

import random
import unittest

from emergence.engine.character_creation.session_zero import (
    FixedInputSource,
    MockNarratorSink,
    SessionZero,
)
from emergence.engine.character_creation.scenarios import make_v2_scenes


# Text answers keyed by the substring FixedInputSource matches against.
# Substrings are lowercased in get_text(), so these must be lowercase.
_TEXT_ANSWERS = {
    "name": "Elena Vasquez",
    "age": "28",
    "description": "blunt surgeon, protective and analytical, patient under pressure",
    "reaction": "I reach in and start working on the bleeder with both hands",
    "narrative": "My senior resident Jason saw me do it. He didn't speak for a minute.",
    "npc_seeds": "[]",
}


class TestFullV2Flow(unittest.TestCase):
    """Run the full 13-scene v2 session zero and verify the output."""

    def _run_session_zero(self, seed: int, default_choice: int = 0) -> object:
        scenes = make_v2_scenes()
        sz = SessionZero(scenes)
        rng = random.Random(seed)
        input_source = FixedInputSource(
            texts=_TEXT_ANSWERS,
            choices={},
            default_choice=default_choice,
        )
        narrator = MockNarratorSink()
        return sz.run(input_source, narrator, rng)

    def test_produces_valid_character(self):
        sheet = self._run_session_zero(seed=42)
        self.assertEqual(sheet.name, "Elena Vasquez")
        self.assertEqual(sheet.age_at_onset, 28)
        self.assertEqual(sheet.current_age, 29)
        self.assertEqual(sheet.tier, 3)

    def test_has_two_powers(self):
        sheet = self._run_session_zero(seed=42)
        self.assertEqual(len(sheet.powers), 2)
        slots = {p.get("slot") for p in sheet.powers}
        self.assertIn("primary", slots)
        self.assertIn("secondary", slots)

    def test_powers_are_v2_ids(self):
        sheet = self._run_session_zero(seed=42)
        v2_category_prefixes = {
            "kinetic_", "material_", "paradoxic_",
            "spatial_", "somatic_", "cognitive_",
        }
        for power in sheet.powers:
            pid = power.get("power_id", "")
            self.assertTrue(
                any(pid.startswith(prefix) for prefix in v2_category_prefixes),
                f"power_id {pid!r} is not a V2 id",
            )

    def test_has_skills(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.skills), 0)

    def test_skills_capped(self):
        sheet = self._run_session_zero(seed=42)
        for skill, val in sheet.skills.items():
            self.assertGreater(val, 0)
            self.assertLessEqual(val, 6)

    def test_has_relationships(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.relationships), 0)

    def test_has_goals(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.goals), 0)

    def test_has_history(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.history), 0)

    def test_has_location(self):
        sheet = self._run_session_zero(seed=42)
        self.assertTrue(sheet.location)

    def test_has_inventory(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.inventory), 0)

    def test_determinism(self):
        """Same seed produces identical character."""
        sheet1 = self._run_session_zero(seed=123)
        sheet2 = self._run_session_zero(seed=123)
        self.assertEqual(sheet1.name, sheet2.name)
        self.assertEqual(sheet1.skills, sheet2.skills)
        self.assertEqual(sheet1.tier, sheet2.tier)
        self.assertEqual(len(sheet1.powers), len(sheet2.powers))
        for p1, p2 in zip(sheet1.powers, sheet2.powers):
            self.assertEqual(p1.get("power_id"), p2.get("power_id"))

    def test_session_zero_choices_recorded(self):
        sheet = self._run_session_zero(seed=42)
        self.assertGreater(len(sheet.session_zero_choices), 0)

    def test_all_13_scenes_run(self):
        sheet = self._run_session_zero(seed=42)
        # Most scenes contribute history entries; a few (intro) contribute one.
        self.assertGreaterEqual(len(sheet.history), 8)


class TestNpcSeedParsing(unittest.TestCase):
    """The life-description scene accepts structured NPC seeds."""

    def test_seeds_round_trip_into_creation_state(self):
        from emergence.engine.character_creation.scenarios import LifeDescriptionScene
        from emergence.engine.character_creation.character_factory import (
            CharacterFactory,
            CreationState,
        )

        scene = LifeDescriptionScene()
        state = CreationState(seed=1)
        factory = CharacterFactory()
        rng = random.Random(1)

        json_seeds = (
            '[{"name":"Jason","relation":"senior_resident","location":"Bellevue",'
            '"descriptor":"wry, blunt","status":"alive"},'
            '{"name":"Akhil","relation":"brother","location":"Mount Sinai",'
            '"descriptor":"med student","status":"alive"}]'
        )
        result = scene.apply_text(
            {
                "name": "Abhishek Rao",
                "age": "30",
                "description": "blunt surgeon, curious and analytical reader",
                "npc_seeds": json_seeds,
            },
            state, factory, rng,
        )
        self.assertEqual(len(result.npc_seeds), 2)
        names = {s["name"] for s in result.npc_seeds}
        self.assertEqual(names, {"Jason", "Akhil"})


if __name__ == "__main__":
    unittest.main()
