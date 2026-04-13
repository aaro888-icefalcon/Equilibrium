"""Integration test: complete session zero → valid CharacterSheet.

5 seeds → 5 different characters. All validate.
"""

import random
import unittest

from emergence.engine.character_creation.character_factory import CharacterFactory
from emergence.engine.character_creation.session_zero import (
    FixedInputSource,
    MockNarratorSink,
    SessionZero,
)
from emergence.engine.character_creation.scenes import (
    ConcernScene,
    LocationScene,
    OccupationScene,
    OpeningScene,
    RelationshipScene,
)
from emergence.engine.character_creation.manifestation import ManifestationScene
from emergence.engine.character_creation.year_one import (
    CriticalIncidentScene,
    FactionEncounterScene,
    FirstWeeksScene,
    SettlingScene,
)
from emergence.engine.schemas.character import CharacterSheet


def _make_scenes():
    return [
        OpeningScene(),
        OccupationScene(),
        RelationshipScene(),
        LocationScene(),
        ConcernScene(),
        ManifestationScene(),
        FirstWeeksScene(),
        FactionEncounterScene(),
        CriticalIncidentScene(),
        SettlingScene(),
    ]


class TestFullSessionZero(unittest.TestCase):

    def _run_session(self, seed: int, choices: dict = None, texts: dict = None):
        scenes = _make_scenes()
        sz = SessionZero(scenes=scenes)
        narrator = MockNarratorSink()
        inp = FixedInputSource(
            texts=texts or {"name": "Test Character", "age": "28"},
            choices=choices or {},
            default_choice=0,
        )
        rng = random.Random(seed)
        return sz.run(inp, narrator, rng), narrator

    def test_produces_character_sheet(self):
        sheet, _ = self._run_session(42)
        self.assertIsInstance(sheet, CharacterSheet)

    def test_character_has_name(self):
        sheet, _ = self._run_session(42, texts={"name": "Elena Torres", "age": "30"})
        self.assertEqual(sheet.name, "Elena Torres")

    def test_character_has_attributes(self):
        sheet, _ = self._run_session(42)
        self.assertGreaterEqual(sheet.attributes.strength, 4)
        self.assertLessEqual(sheet.attributes.strength, 10)

    def test_character_has_powers(self):
        sheet, _ = self._run_session(42)
        self.assertGreater(len(sheet.powers), 0)

    def test_character_has_skills(self):
        sheet, _ = self._run_session(42)
        self.assertGreater(len(sheet.skills), 0)

    def test_character_has_goals(self):
        sheet, _ = self._run_session(42)
        self.assertGreater(len(sheet.goals), 0)

    def test_character_has_history(self):
        sheet, _ = self._run_session(42)
        self.assertGreater(len(sheet.history), 0)

    def test_character_has_tier(self):
        sheet, _ = self._run_session(42)
        self.assertIn(sheet.tier, [1, 2, 3, 4])

    def test_character_has_location(self):
        sheet, _ = self._run_session(42)
        self.assertGreater(len(sheet.location), 0)

    def test_narrator_receives_payloads(self):
        _, narrator = self._run_session(42)
        self.assertGreater(len(narrator.payloads), 0)

    def test_five_seeds_five_different_characters(self):
        sheets = []
        for seed in [10, 20, 30, 40, 50]:
            sheet, _ = self._run_session(seed)
            sheets.append(sheet)

        # All should be valid CharacterSheets
        for sheet in sheets:
            self.assertIsInstance(sheet, CharacterSheet)
            self.assertGreater(len(sheet.powers), 0)

        # At least some should differ in primary category
        categories = {s.power_category_primary for s in sheets}
        # With 5 random seeds, should see at least 2 different categories
        self.assertGreater(len(categories), 1,
                           f"All 5 characters got same category: {categories}")

    def test_different_choices_different_characters(self):
        # Default choices (all 0) vs different choices
        sheet1, _ = self._run_session(42, choices={})
        sheet2, _ = self._run_session(42, choices={
            "Scene sz_1": 5,  # Tradesperson
            "Scene sz_2": 3,  # Sibling
            "Scene sz_3": 2,  # Hudson Valley
            "Scene sz_4": 7,  # Steady life
        })

        # Should produce different skill sets
        self.assertNotEqual(sheet1.skills, sheet2.skills)

    def test_session_zero_choices_recorded(self):
        sheet, _ = self._run_session(42)
        self.assertIn("sz_0", sheet.session_zero_choices)
        self.assertIn("sz_1", sheet.session_zero_choices)
        self.assertIn("sz_5", sheet.session_zero_choices)


class TestCharacterValidity(unittest.TestCase):
    """Verify generated characters have valid references."""

    def test_tier_and_category_consistent(self):
        scenes = _make_scenes()
        sz = SessionZero(scenes=scenes)
        narrator = MockNarratorSink()
        inp = FixedInputSource(
            texts={"name": "Validation Test", "age": "25"},
        )
        sheet = sz.run(inp, narrator, random.Random(99))

        self.assertIn(sheet.tier, [1, 2, 3, 4, 5])
        self.assertEqual(sheet.tier_ceiling, sheet.tier + 2)
        self.assertGreater(len(sheet.power_category_primary), 0)

    def test_attributes_in_valid_range(self):
        scenes = _make_scenes()
        sz = SessionZero(scenes=scenes)
        narrator = MockNarratorSink()
        inp = FixedInputSource(texts={"name": "Range Test", "age": "40"})
        sheet = sz.run(inp, narrator, random.Random(77))

        for attr_name in ["strength", "agility", "perception", "will", "insight", "might"]:
            val = getattr(sheet.attributes, attr_name)
            self.assertGreaterEqual(val, 4, f"{attr_name} too low: {val}")
            self.assertLessEqual(val, 10, f"{attr_name} too high: {val}")


if __name__ == "__main__":
    unittest.main()
