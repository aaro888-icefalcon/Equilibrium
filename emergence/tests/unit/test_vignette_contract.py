"""Unit tests for vignette_contract: schema parsing + validator."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy

from emergence.engine.character_creation.vignette_contract import (
    VignetteOutput, validate_vignette_output,
)
from emergence.engine.character_creation.scaffolds import (
    VignetteScaffold, Option, PER_INDEX_DEFAULTS,
)
from emergence.engine.character_creation.seed_pools import compute_seed_pools
from emergence.engine.character_creation.character_factory import CreationState


def _v1_scaffold() -> VignetteScaffold:
    return VignetteScaffold(
        index=1,
        mechanical_slot="primary_cast",
        power_id="touch_strike",
        option_pool=[
            Option("touch", "Touch", "brush fingers"),
            Option("short", "Short", "arm's length"),
            Option("line", "Line", "2m sweep"),
        ],
        time_period="weeks after",
        region=None,
        stakes_register="first use",
        seed_pools=compute_seed_pools(CreationState(), 1),
        required_seeds=PER_INDEX_DEFAULTS[1]["required_seeds"],
    )


def _v1_golden() -> dict:
    return {
        "prose": "A block of Manhattan, cold.",
        "choices": [
            {"display_text": "Touch the wall.",
             "mechanical_binding": {"slot": "primary_cast", "option_id": "touch"},
             "mechanical_parenthetical": "(1 CP, touch, no action)",
             "seed_bundle": {
                 "npcs": [{"name": "Maria", "archetype": "survivor"}],
                 "locations": [{"id": "loc-manhattan-midtown"}],
                 "threats": [{"archetype": "knife_scavenger_survivor",
                              "name": "the man with the knife"}],
                 "history_record": "met Maria"}},
            {"display_text": "Read the room.",
             "mechanical_binding": {"slot": "primary_cast", "option_id": "short"},
             "mechanical_parenthetical": "(2 CP, 2m, minor)",
             "seed_bundle": {
                 "npcs": [{"name": "Paulo", "archetype": "rival"}],
                 "locations": [{"id": "loc-manhattan-midtown"}],
                 "threats": [{"archetype": "eldritch_persistent", "name": "the hum"}],
                 "history_record": "noticed Paulo"}},
            {"display_text": "Line burst.",
             "mechanical_binding": {"slot": "primary_cast", "option_id": "line"},
             "mechanical_parenthetical": "(3 CP, line 2m, move)",
             "seed_bundle": {
                 "npcs": [{"name": "Isabel", "archetype": "dependent"}],
                 "locations": [{"id": "loc-brooklyn-tower-districts"}],
                 "threats": [{"archetype": "warped_predator_personal", "name": "hunt"}],
                 "history_record": "pulled Isabel out"}},
        ],
    }


class TestFromJson(unittest.TestCase):
    def test_parses_str_and_dict(self):
        d = _v1_golden()
        out1 = VignetteOutput.from_json(d)
        out2 = VignetteOutput.from_json(json.dumps(d))
        self.assertEqual(len(out1.choices), 3)
        self.assertEqual(len(out2.choices), 3)

    def test_malformed_json_raises(self):
        with self.assertRaises(ValueError):
            VignetteOutput.from_json("{not valid")

    def test_non_dict_top_raises(self):
        with self.assertRaises(ValueError):
            VignetteOutput.from_json("[1,2,3]")

    def test_unknown_fields_tolerated(self):
        d = _v1_golden()
        d["choices"][0]["seed_bundle"]["npcs"][0]["extra_field"] = "ignored"
        out = VignetteOutput.from_json(d)
        self.assertEqual(out.choices[0].seed_bundle.npcs[0].name, "Maria")


class TestGolden(unittest.TestCase):
    def test_v1_golden_passes(self):
        out = VignetteOutput.from_json(_v1_golden())
        viols = validate_vignette_output(out, _v1_scaffold())
        self.assertEqual(viols, [])


class TestViolations(unittest.TestCase):
    def setUp(self):
        self.scaffold = _v1_scaffold()

    def _mutate(self, f):
        d = _v1_golden()
        f(d)
        return VignetteOutput.from_json(d)

    def test_too_few_choices(self):
        out = self._mutate(lambda d: d["choices"].pop())
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("expected 3" in v for v in viols))

    def test_wrong_slot(self):
        def f(d):
            d["choices"][0]["mechanical_binding"]["slot"] = "secondary_cast"
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("mechanical_slot" in v for v in viols))

    def test_option_not_in_pool(self):
        def f(d):
            d["choices"][0]["mechanical_binding"]["option_id"] = "not_a_real_option"
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("option_pool" in v for v in viols))

    def test_empty_parenthetical(self):
        def f(d):
            d["choices"][0]["mechanical_parenthetical"] = ""
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("parenthetical is empty" in v for v in viols))

    def test_parenthetical_identical_to_base(self):
        def f(d):
            d["choices"][0]["mechanical_parenthetical"] = "brush fingers"
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("identical to option base" in v for v in viols))

    def test_missing_required_seed(self):
        def f(d):
            d["choices"][0]["seed_bundle"]["npcs"] = []
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("seed_bundle.npcs" in v for v in viols))

    def test_unknown_threat_archetype(self):
        def f(d):
            d["choices"][0]["seed_bundle"]["threats"][0]["archetype"] = "not_a_real"
        out = self._mutate(f)
        viols = validate_vignette_output(out, self.scaffold)
        self.assertTrue(any("not a known archetype" in v for v in viols))


class TestV2RegionOutcomeRules(unittest.TestCase):
    def _v2_scaffold(self):
        state = CreationState()
        return VignetteScaffold(
            index=2,
            mechanical_slot="primary_rider",
            power_id="x",
            option_pool=[
                Option("bleed", "Bleed", "b"),
                Option("stun", "Stun", "s"),
                Option("mark", "Mark", "m"),
            ],
            time_period="autumn Y1",
            region=None,
            stakes_register="depart or stay",
            seed_pools=compute_seed_pools(state, 2),
            required_seeds=PER_INDEX_DEFAULTS[2]["required_seeds"],
        )

    def _v2_payload(self, outcomes):
        d = {
            "prose": "p",
            "choices": [],
        }
        slots = [("bleed", "(1, close)"), ("stun", "(2, short)"), ("mark", "(2, long)")]
        for (opt, paren), oc in zip(slots, outcomes):
            d["choices"].append({
                "display_text": f"choice {opt}",
                "mechanical_binding": {"slot": "primary_rider", "option_id": opt},
                "mechanical_parenthetical": paren,
                "seed_bundle": {
                    "npcs": [{"name": "n", "archetype": "ally"}],
                    "factions": [{"faction_id": "tower-lords", "standing_delta": 0}],
                    "threats": [{"archetype": "named_rival_human", "name": "x"}],
                    "region_outcome": oc,
                    "history_record": "h",
                },
            })
        return d

    def test_canonical_set_passes(self):
        out = VignetteOutput.from_json(
            self._v2_payload(["stay_nyc", "displaced_to", "traveled_to"]))
        viols = validate_vignette_output(out, self._v2_scaffold())
        self.assertEqual(viols, [])

    def test_double_displaced_passes(self):
        out = VignetteOutput.from_json(
            self._v2_payload(["stay_nyc", "displaced_to", "displaced_to"]))
        viols = validate_vignette_output(out, self._v2_scaffold())
        self.assertEqual(viols, [])

    def test_triple_displaced_fails(self):
        out = VignetteOutput.from_json(
            self._v2_payload(["displaced_to", "displaced_to", "displaced_to"]))
        viols = validate_vignette_output(out, self._v2_scaffold())
        self.assertTrue(any("region_outcome set" in v for v in viols))

    def test_invalid_value_fails(self):
        out = VignetteOutput.from_json(
            self._v2_payload(["stay_nyc", "displaced_to", "voyaged"]))
        viols = validate_vignette_output(out, self._v2_scaffold())
        self.assertTrue(any("not in" in v for v in viols))


class TestV4Rules(unittest.TestCase):
    def _v4_scaffold(self):
        state = CreationState(region="Philadelphia")
        return VignetteScaffold(
            index=4,
            mechanical_slot="secondary_rider",
            power_id="y",
            option_pool=[
                Option("tag", "Tag", "t"),
                Option("burn", "Burn", "b"),
                Option("hush", "Hush", "h"),
            ],
            time_period="spring Y2",
            region="Philadelphia",
            stakes_register="commit",
            seed_pools=compute_seed_pools(state, 4),
            required_seeds=PER_INDEX_DEFAULTS[4]["required_seeds"],
        )

    def _v4_payload(self, starting_flags, goal_counts):
        d = {"prose": "p", "choices": []}
        slots = [("tag", "(1, close)"), ("burn", "(2, short)"), ("hush", "(2, long)")]
        for i, ((opt, paren), starting, ng) in enumerate(
                zip(slots, starting_flags, goal_counts)):
            d["choices"].append({
                "display_text": f"choice {opt}",
                "mechanical_binding": {"slot": "secondary_rider", "option_id": opt},
                "mechanical_parenthetical": paren,
                "seed_bundle": {
                    "npcs": [{"name": f"n{i}", "archetype": "ally"}],
                    "locations": [{"id": "loc-philadelphia-bourse-floor", "is_starting": starting}],
                    "vows": [{"vow_id": "protector",
                              "goals": [{"id": f"g{i}_{k}", "description": "g"}
                                        for k in range(ng)]}],
                    "history_record": "h",
                },
            })
        return d

    def test_single_starting_meets_rule(self):
        out = VignetteOutput.from_json(
            self._v4_payload([True, False, False], [2, 2, 2]))
        viols = validate_vignette_output(out, self._v4_scaffold())
        self.assertEqual(viols, [])

    def test_no_starting_fails(self):
        out = VignetteOutput.from_json(
            self._v4_payload([False, False, False], [2, 2, 2]))
        viols = validate_vignette_output(out, self._v4_scaffold())
        self.assertTrue(any("is_starting" in v for v in viols))

    def test_multiple_starting_fails(self):
        out = VignetteOutput.from_json(
            self._v4_payload([True, True, False], [2, 2, 2]))
        viols = validate_vignette_output(out, self._v4_scaffold())
        self.assertTrue(any("is_starting" in v for v in viols))

    def test_too_few_goals_fails(self):
        out = VignetteOutput.from_json(
            self._v4_payload([True, False, False], [2, 1, 2]))
        viols = validate_vignette_output(out, self._v4_scaffold())
        self.assertTrue(any("vows goals" in v for v in viols))


if __name__ == "__main__":
    unittest.main()
