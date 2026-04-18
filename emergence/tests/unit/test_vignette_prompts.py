"""Unit tests for vignette_prompts.render_prompt."""

from __future__ import annotations

import json
import os
import random
import unittest

from emergence.engine.character_creation.character_factory import CreationState
from emergence.engine.character_creation.scaffolds import build_scaffold
from emergence.engine.character_creation.vignette_prompts import render_prompt


_COG_PATH = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "data", "powers_v2", "cognitive.json",
))


def _state() -> CreationState:
    powers = json.load(open(_COG_PATH))
    s = CreationState()
    s.powers = [
        {"power_id": powers[0]["id"], "name": powers[0]["name"]},
        {"power_id": powers[1]["id"], "name": powers[1]["name"]},
    ]
    return s


class TestRender(unittest.TestCase):
    def test_every_index_renders_six_sections(self):
        s = _state()
        for idx in (1, 2, 3, 4):
            sc = build_scaffold(s, idx, random.Random(idx))
            prompt = render_prompt(sc)
            self.assertIn("# Vignette", prompt)
            self.assertIn("# World compaction", prompt)
            self.assertIn("# Mechanical constraint", prompt)
            self.assertIn("# Seeding requirements", prompt)
            self.assertIn("# Output format", prompt)
            self.assertIn("# Register reminders", prompt)

    def test_slot_name_in_prompt(self):
        s = _state()
        for idx, slot in ((1, "primary_cast"), (2, "primary_rider"),
                          (3, "secondary_cast"), (4, "secondary_rider")):
            sc = build_scaffold(s, idx, random.Random(idx))
            prompt = render_prompt(sc)
            self.assertIn(slot, prompt)

    def test_v2_exposes_region_outcomes(self):
        s = _state()
        sc = build_scaffold(s, 2, random.Random(2))
        prompt = render_prompt(sc)
        self.assertIn("Region outcomes", prompt)
        self.assertIn("stay_nyc", prompt)

    def test_v4_flags_is_starting(self):
        s = _state()
        sc = build_scaffold(s, 4, random.Random(4))
        prompt = render_prompt(sc)
        self.assertIn("is_starting", prompt)

    def test_option_pool_shown_when_power_known(self):
        s = _state()
        sc = build_scaffold(s, 1, random.Random(1))
        prompt = render_prompt(sc)
        for opt in sc.option_pool:
            self.assertIn(opt.option_id, prompt)

    def test_empty_power_flags_error(self):
        sc = build_scaffold(CreationState(), 1, random.Random(1))
        prompt = render_prompt(sc)
        self.assertIn("no power configured", prompt)

    def test_reaction_tags_propagate(self):
        s = _state()
        sc = build_scaffold(s, 3, random.Random(3))
        prompt = render_prompt(sc, reaction_tags=["cognitive", "perceptive"])
        self.assertIn("cognitive", prompt)
        self.assertIn("perceptive", prompt)


if __name__ == "__main__":
    unittest.main()
