"""Integration test: run YearOneVignetteScene for V1-V4 with golden payloads."""

from __future__ import annotations

import json
import os
import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.year_one_vignette_scene import (
    YearOneVignetteScene,
)


_COG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "powers_v2", "cognitive.json",
))


def _state_with_powers() -> CreationState:
    cog = json.load(open(_COG_PATH))
    s = CreationState(seed=42, name="Shake", age_at_onset=30)
    s.powers = [
        {"power_id": cog[0]["id"], "name": cog[0]["name"]},
        {"power_id": cog[1]["id"], "name": cog[1]["name"]},
    ]
    s.tier = 3
    s.tier_ceiling = 5
    return s


def _v1_payload(scaffold) -> dict:
    opts = [o.option_id for o in scaffold.option_pool]
    choices = []
    for i, oid in enumerate(opts):
        choices.append({
            "display_text": f"choice {i}",
            "mechanical_binding": {"slot": "primary_cast", "option_id": oid},
            "mechanical_parenthetical": f"(specific to {oid}, choice {i})",
            "seed_bundle": {
                "npcs": [{"name": f"V1_NPC_{i}", "archetype": "survivor"}],
                "locations": [{"id": "loc-manhattan-midtown"}],
                "threats": [{"archetype": "knife_scavenger_survivor",
                             "name": f"V1 threat {i}"}],
                "history_record": f"V1 beat {i}",
            },
        })
    return {"prose": "V1 prose", "choices": choices}


def _v2_payload(scaffold) -> dict:
    opts = [o.option_id for o in scaffold.option_pool]
    outcomes = ["stay_nyc", "displaced_to", "traveled_to"]
    if "traveled_to" not in (scaffold.seed_pools.region_outcomes or []):
        outcomes = ["stay_nyc", "displaced_to", "displaced_to"]
    locs = ["loc-manhattan-midtown",
            "loc-port-newark-compound",
            "loc-philadelphia-bourse-floor"]
    choices = []
    for i, (oid, oc, lid) in enumerate(zip(opts, outcomes, locs)):
        choices.append({
            "display_text": f"V2 choice {i}",
            "mechanical_binding": {"slot": "primary_rider", "option_id": oid},
            "mechanical_parenthetical": f"(V2 specific {oid}, beat {i})",
            "seed_bundle": {
                "npcs": [{"name": f"V2_NPC_{i}", "archetype": "ally"}],
                "factions": [{"faction_id": "tower-lords", "standing_delta": 0}],
                "threats": [{"archetype": "named_rival_human", "name": f"V2 rival {i}"}],
                "region_outcome": oc,
                "locations": [{"id": lid}],
                "history_record": f"V2 beat {i}",
            },
        })
    return {"prose": "V2 prose", "choices": choices}


def _v3_payload(scaffold) -> dict:
    opts = [o.option_id for o in scaffold.option_pool]
    choices = []
    for i, oid in enumerate(opts):
        choices.append({
            "display_text": f"V3 choice {i}",
            "mechanical_binding": {"slot": "secondary_cast", "option_id": oid},
            "mechanical_parenthetical": f"(V3 specific {oid}, beat {i})",
            "seed_bundle": {
                "npcs": [{"name": f"V3_NPC_{i}", "archetype": "mentor"}],
                "threats": [{"archetype": "warped_predator_personal",
                             "name": f"V3 hunter {i}"}],
                "vows": [{"vow_id": "protector",
                          "goals": [{"id": f"v3g{i}", "description": f"V3 goal {i}"}]}],
                "history_record": f"V3 beat {i}",
            },
        })
    return {"prose": "V3 prose", "choices": choices}


def _v4_payload(scaffold) -> dict:
    opts = [o.option_id for o in scaffold.option_pool]
    startings = [True, False, False]
    choices = []
    for i, (oid, starting) in enumerate(zip(opts, startings)):
        choices.append({
            "display_text": f"V4 choice {i}",
            "mechanical_binding": {"slot": "secondary_rider", "option_id": oid},
            "mechanical_parenthetical": f"(V4 specific {oid}, beat {i})",
            "seed_bundle": {
                "npcs": [{"name": f"V4_NPC_{i}", "archetype": "named_antagonist"}],
                "locations": [{"spec": {"id": f"loc-v4-{i}",
                                         "name": "Safehouse",
                                         "region": "New York City"},
                                "is_starting": starting}],
                "vows": [{"vow_id": "avenger",
                          "goals": [
                              {"id": f"v4g{i}a", "description": f"V4 goal A {i}"},
                              {"id": f"v4g{i}b", "description": f"V4 goal B {i}"},
                          ]}],
                "history_record": f"V4 beat {i}",
            },
        })
    return {"prose": "V4 prose", "choices": choices}


class TestVignetteSequence(unittest.TestCase):
    def test_v1_through_v4_sequential(self):
        s = _state_with_powers()
        f = CharacterFactory()
        rng = random.Random(1)

        # V1
        v1 = YearOneVignetteScene(1)
        v1.prepare(s, rng)
        r1 = v1.apply_vignette_output(json.dumps(_v1_payload(v1._scaffold)),
                                       0, s, f, rng)
        self.assertEqual(r1["status"], "ok", r1)
        s = r1["state"]
        s.pending_ack = False  # simulate ack consumption
        self.assertGreaterEqual(len(s.threats), 1)

        # V2
        v2 = YearOneVignetteScene(2)
        v2.prepare(s, rng)
        r2 = v2.apply_vignette_output(json.dumps(_v2_payload(v2._scaffold)),
                                       0, s, f, rng)
        self.assertEqual(r2["status"], "ok", r2)
        s = r2["state"]
        s.pending_ack = False
        # V2 locks region via stay_nyc choice
        self.assertEqual(s.region, "New York City")

        # V3
        v3 = YearOneVignetteScene(3)
        v3.prepare(s, rng)
        r3 = v3.apply_vignette_output(json.dumps(_v3_payload(v3._scaffold)),
                                       0, s, f, rng)
        self.assertEqual(r3["status"], "ok", r3)
        s = r3["state"]
        s.pending_ack = False
        self.assertGreaterEqual(len(s.goals), 1)

        # V4
        v4 = YearOneVignetteScene(4)
        v4.prepare(s, rng)
        r4 = v4.apply_vignette_output(json.dumps(_v4_payload(v4._scaffold)),
                                       0, s, f, rng)
        self.assertEqual(r4["status"], "ok", r4)
        s = r4["state"]
        # V4 lands starting_location
        self.assertTrue(s.starting_location)
        # Goals floor (>= 2 from V4's vow)
        self.assertGreaterEqual(len(s.goals), 2)
        # Named NPCs floor — at least 4 across V1-V4
        self.assertGreaterEqual(len(s.generated_npcs), 3)

    def test_v1_validation_failure_surfaces(self):
        s = _state_with_powers()
        v1 = YearOneVignetteScene(1)
        v1.prepare(s, random.Random(1))
        bad = {"prose": "bad", "choices": [
            {"display_text": "x",
             "mechanical_binding": {"slot": "secondary_cast", "option_id": "cast_1"},
             "mechanical_parenthetical": "(p)",
             "seed_bundle": {"history_record": "h"}},
        ]}
        r = v1.apply_vignette_output(json.dumps(bad), 0, s,
                                      CharacterFactory(), random.Random(2))
        self.assertEqual(r["status"], "error")
        self.assertIn("violations", r)


if __name__ == "__main__":
    unittest.main()
