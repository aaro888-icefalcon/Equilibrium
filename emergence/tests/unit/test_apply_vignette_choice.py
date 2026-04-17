"""Unit tests for apply_vignette_choice: SeedBundle -> state round-trip."""

from __future__ import annotations

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.vignette_contract import (
    VignetteOutput, apply_vignette_choice,
)


def _one_choice_payload(**bundle_kwargs) -> dict:
    return {
        "prose": "p",
        "choices": [{
            "display_text": "a",
            "mechanical_binding": {"slot": "primary_cast", "option_id": "touch"},
            "mechanical_parenthetical": "(1 CP)",
            "seed_bundle": bundle_kwargs,
        }],
    }


class TestApplyRoundTrip(unittest.TestCase):
    def test_npcs_land_in_generated_npcs(self):
        p = _one_choice_payload(
            npcs=[{"name": "Maria", "archetype": "survivor", "standing": 1}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v1", CreationState(),
                                  CharacterFactory(), random.Random(1))
        names = {n["display_name"] for n in s.generated_npcs}
        self.assertIn("Maria", names)

    def test_starting_location_from_spec(self):
        p = _one_choice_payload(
            locations=[{"spec": {"id": "loc-new-safehouse",
                                 "name": "Safe", "region": "Hudson Valley"},
                        "is_starting": True}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v4",
                                  CreationState(region="Hudson Valley"),
                                  CharacterFactory(), random.Random(2))
        self.assertEqual(s.starting_location, "loc-new-safehouse")

    def test_faction_deltas_flow_through(self):
        p = _one_choice_payload(
            factions=[{"faction_id": "iron-crown",
                       "standing_delta": -2, "heat_delta": 3}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v2", CreationState(),
                                  CharacterFactory(), random.Random(3))
        self.assertEqual(s.faction_standing_deltas.get("iron-crown"), -2)
        self.assertEqual(s.heat_deltas.get("iron-crown"), 3)

    def test_threats_normalize_archetype_and_pressure(self):
        p = _one_choice_payload(
            threats=[{"archetype": "iron_crown_notice", "name": "captain"}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v2", CreationState(),
                                  CharacterFactory(), random.Random(4))
        # iron_crown_notice default = 3
        ic = [t for t in s.threats if t.get("archetype") == "iron_crown_notice"]
        self.assertEqual(len(ic), 1)
        self.assertEqual(ic[0]["pressure"], 3)

    def test_floor_enforced(self):
        p = _one_choice_payload(
            threats=[{"archetype": "knife_scavenger_survivor", "name": "x"}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v1",
                                  CreationState(region="New York City"),
                                  CharacterFactory(), random.Random(5),
                                  threat_floor=3)
        self.assertGreaterEqual(len(s.threats), 3)

    def test_pending_ack_set_after_apply(self):
        p = _one_choice_payload(npcs=[{"name": "x", "archetype": "ally"}])
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v1", CreationState(),
                                  CharacterFactory(), random.Random(6))
        self.assertTrue(s.pending_ack)

    def test_history_record_appended(self):
        p = _one_choice_payload(
            npcs=[{"name": "x", "archetype": "ally"}],
            history_record="a thing happened",
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v3", CreationState(),
                                  CharacterFactory(), random.Random(7))
        descs = [h["description"] for h in s.history]
        self.assertIn("a thing happened", descs)
        types = [h.get("type") for h in s.history]
        self.assertIn("character_creation_vignette", types)

    def test_vows_flatten_to_goals(self):
        p = _one_choice_payload(
            vows=[{"vow_id": "protector",
                   "goals": [{"id": "g1", "description": "first"},
                             {"id": "g2", "description": "second"}]}],
        )
        out = VignetteOutput.from_json(p)
        s = apply_vignette_choice(out.choices[0], "v4", CreationState(),
                                  CharacterFactory(), random.Random(8))
        descs = [g.get("description") for g in s.goals]
        self.assertIn("first", descs)
        self.assertIn("second", descs)


if __name__ == "__main__":
    unittest.main()
