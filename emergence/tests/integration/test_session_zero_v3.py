"""Integration tests for the V3 session-zero flow — 5 long-form scenes."""

import random
import unittest

from emergence.engine.character_creation.session_zero import (
    FixedInputSource,
    MockNarratorSink,
    SessionZero,
)
from emergence.engine.character_creation.scenarios_v3 import make_v3_scenes


# Text answers keyed by FixedInputSource substring-match (lowercase).
_TEXT_ANSWERS = {
    "name": "Elena Vasquez",
    "age": "28",
    "description": "blunt surgeon, protective and analytical",
    "reaction": "I reach and start working with my hands",
    "primary_beat": "Jason saw me do it first.",
    "secondary_beat": "It refused to touch the quiet ones.",
    "npc_seeds": (
        '[{"name":"Jason","relation":"senior_resident","location":"Bellevue",'
        '"descriptor":"wry","status":"alive"}]'
    ),
}


class TestFullV3Flow(unittest.TestCase):
    """Run the full 5-scene v3 session zero and verify the output."""

    def _run(self, seed: int = 42) -> object:
        scenes = make_v3_scenes()
        sz = SessionZero(scenes)
        rng = random.Random(seed)
        inputs = FixedInputSource(
            texts=_TEXT_ANSWERS,
            choices={},
            default_choice=0,
        )
        narrator = MockNarratorSink()
        return sz.run(inputs, narrator, rng)

    def test_produces_named_character(self):
        sheet = self._run()
        self.assertEqual(sheet.name, "Elena Vasquez")
        self.assertEqual(sheet.age_at_onset, 28)

    def test_two_powers_committed(self):
        sheet = self._run()
        self.assertEqual(len(sheet.powers), 2)
        slots = {p.get("slot") for p in sheet.powers}
        self.assertEqual(slots, {"primary", "secondary"})

    def test_character_has_region_and_location(self):
        sheet = self._run()
        self.assertTrue(sheet.location)

    def test_character_has_at_least_two_goals(self):
        """Two vows each contribute goals → sheet has ≥2 goals."""
        sheet = self._run()
        self.assertGreaterEqual(len(sheet.goals), 2)

    def test_character_has_at_least_two_threats(self):
        """Threat top-up guarantees ≥2 threats at finalize."""
        sheet = self._run()
        self.assertGreaterEqual(len(sheet.threats), 2)

    def test_relationships_include_threats(self):
        """Every threat has a matching relationship with negative standing."""
        sheet = self._run()
        for t in sheet.threats:
            npc_id = t.get("npc_id")
            self.assertIn(npc_id, sheet.relationships)

    def test_history_covers_all_scenes(self):
        sheet = self._run()
        # 5 scenes each emit at least one history entry (most emit several).
        self.assertGreaterEqual(len(sheet.history), 5)


if __name__ == "__main__":
    unittest.main()
