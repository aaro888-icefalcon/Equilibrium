"""End-to-end integration test for the six-scene character creation flow.

Drives SessionZero with a FixedInputSource + a MockNarrator that returns
canned JSON payloads for classifier / bundle / quest / bridge. Verifies:

- CharacterSheet finalized with attributes, skills, powers, NPCs
- QuestState holds exactly 5 quests (4 background + 1 urgent)
- Opening scene meta references the urgent quest
- No narrator-authored state that bypasses validation
"""

from __future__ import annotations

import random
import unittest
from typing import Any, Dict

from emergence.engine.character_creation.session_zero import (
    FixedInputSource,
    SessionZero,
)


# ---------------------------------------------------------------------------
# Mock narrator — canned outputs for each scene
# ---------------------------------------------------------------------------


CLASSIFIER_OUTPUT: Dict[str, Any] = {
    "attributes": {
        "strength": 6, "agility": 8, "perception": 8,
        "will": 8, "insight": 10, "might": 6,
        "rationale": "surgeon: Agility + Insight lifted; Will for chief role.",
    },
    "skills": {
        "surgery": 5, "first_aid": 5, "pharmacology": 4,
        "field_medicine": 3, "literacy": 4, "bureaucracy": 3,
        "brawling": 2, "history": 3, "tactics": 2,
        "rationale": "vascular surgeon + academic chief + TKD background",
    },
    "npcs": [
        {"name": "Akhil Rao", "relation": "sibling", "role": "bond",
         "bond": {"trust": 3, "loyalty": 3, "tension": 0},
         "distance": "near", "notes": "med student at Mount Sinai"},
        {"name": "Jason Park", "relation": "coworker", "role": "bond",
         "bond": {"trust": 2, "loyalty": 2, "tension": 1},
         "distance": "near", "notes": "wry senior co-resident"},
        {"name": "Jessica Nguyen", "relation": "coworker", "role": "contact",
         "bond": {"trust": 2, "loyalty": 1, "tension": 0},
         "distance": "near", "notes": "kind and blunt junior"},
    ],
}


def _bundle_output() -> Dict[str, Any]:
    """Five distinct Manhattan-Fragment job cards."""
    cards = []
    for i, (jid, title) in enumerate([
        ("job_mf_echo_watcher", "Echo-Watcher for a Tower Lord"),
        ("job_mf_clinic_runner", "Street Clinic Runner"),
        ("job_mf_salvage_broker", "Salvage Broker — Midtown"),
        ("job_mf_tower_medic", "Tower-Lord House Medic"),
        ("job_mf_visiting_surgeon", "Visiting Surgeon to the Commonage"),
    ]):
        cards.append({
            "job_id": jid,
            "title": title,
            "daily_loop": f"Working out of a {title.lower()} post in Lower Manhattan.",
            "skill_tilts": {"surgery": 1, "first_aid": 1},
            "factions": {
                "positive": [{"faction_id": "brooklyn_tower_lords", "standing": 1, "role": "employer"}],
                "negative": [{"faction_id": "iron_crown_newark", "standing": -1, "reason": "rival jurisdiction"}],
            },
            "npcs": [
                {"npc_id": f"npc_{jid}_mentor", "name": "Dr. Hallam", "role": "ally",
                 "relation": "mentor", "bond": {"trust": 2, "loyalty": 2, "tension": 0},
                 "hook": "Takes you on as an understudy."},
                {"npc_id": f"npc_{jid}_coworker", "name": "Nurse Petra", "role": "ally",
                 "relation": "coworker", "bond": {"trust": 2, "loyalty": 2, "tension": 0},
                 "hook": "Senior circulating nurse."},
                {"npc_id": f"npc_{jid}_rival", "name": "Weiss Jr.", "role": "rival",
                 "relation": "colleague", "bond": {"trust": 0, "loyalty": 0, "tension": 3},
                 "hook": "Passed over for attending; quietly furious."},
            ],
            "threats": [{"archetype": "debt_holder", "hook": "A Tower Lord captain is owed a favor."}],
            "starting_location": "rittenhouse_square_philadelphia",
            "opening_vignette_seed": "The bell rings three times — an Iron Crown summons.",
        })
    return {"cards": cards}


def _quest_output() -> Dict[str, Any]:
    """Eight quests; 4 flagged as backstory; 4 remain for urgent pick."""
    quests = []
    for i in range(8):
        qid = f"q_test_{i:02d}"
        quests.append({
            "id": qid,
            "archetype": "extraction",
            "goal": f"Extract the Q{i} packet from the contested zone before the sweep",
            "hook_scene": {"established_on_turn": 0, "inciting_event": f"Q{i} hook fires."},
            "central_conflict": {
                "nature": "time-critical under hostile jurisdiction",
                "proxy_antagonist_id": f"npc_q{i}_antagonist",
            },
            "bright_lines": [
                {"id": "bl_sweep", "description": "sweep arrives",
                 "check_condition": {"type": "macrostructure", "op": "<=", "value": 0},
                 "telegraph_text": "a distant bell toll"},
                {"id": "bl_target_dies",
                 "description": "target dies before extraction",
                 "check_condition": {"type": "npc_status", "npc_id": f"npc_q{i}_target", "status": "dead"},
                 "telegraph_text": "target's injury visible and worsening"},
            ],
            "macrostructure": {
                "variable_name": "hours_until_sweep", "current": 5, "threshold": 0,
                "direction": "decrement",
                "tick_triggers": ["world_pulse", "scene_close"],
            },
            "success_condition": {
                "type": "and",
                "predicates": [
                    {"type": "npc_status", "npc_id": f"npc_q{i}_target", "status": "extracted"},
                    {"type": "pc_location_not", "location_id": "corvid_corridor"},
                ],
            },
            "resolution": {
                "world_deltas_on_success": [
                    {"op": "faction_standing_delta", "faction_id": "brooklyn_tower_lords", "delta": 1},
                ],
                "world_deltas_on_failure": {
                    "bl_sweep": [{"op": "npc_status_set", "npc_id": f"npc_q{i}_target", "status": "captured"}],
                    "bl_target_dies": [{"op": "faction_standing_delta", "faction_id": "brooklyn_tower_lords", "delta": -2}],
                },
                "narration_cue_on_success": "clean exit",
                "narration_cue_on_failure": "",
            },
            "progress_track": {"ticks_filled": 0, "ticks_required": 10, "source": "ironsworn_vow_dangerous"},
            "scope": {"expected_scenes": 3, "expected_session_equivalents": 1.0},
        })
    return {
        "quests": quests,
        "backstory_ids": [quests[0]["id"], quests[1]["id"], quests[2]["id"], quests[3]["id"]],
    }


def _bridge_output(urgent_id: str, antagonist_id: str) -> Dict[str, Any]:
    prose = " ".join(["lorem ipsum"] * 800)  # ~1600 words
    scene = " ".join(["dolor sit amet"] * 60)  # ~180 words
    return {
        "bridge_prose": prose,
        "opening_scene": scene,
        "opening_scene_meta": {
            "primary_quest_id": urgent_id,
            "antagonist_id": antagonist_id,
            "hook_npc_id": "npc_akhil_rao",
            "location_id": "manhattan_fragment_clinic",
            "telegraph_bright_line_id": "bl_sweep",
        },
    }


class MockNarrator:
    def __init__(self) -> None:
        self._quest_output = _quest_output()
        self._urgent_id: str = ""

    def classifier(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return CLASSIFIER_OUTPUT

    def job_bundle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return _bundle_output()

    def quest_pool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._quest_output

    def bridge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        urgent = payload["urgent_quest"]
        self._urgent_id = urgent["id"]
        return _bridge_output(urgent["id"], urgent["central_conflict"]["proxy_antagonist_id"])


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------


class TestFullCreationFlow(unittest.TestCase):
    def test_six_scenes_produce_sheet_and_quests(self) -> None:
        inputs = FixedInputSource(
            texts={
                "name": "Abhishek Rao",
                "age": "30",
                "species": "baseline",
                "profession": "PGY-4 vascular surgery resident, NYU academic chief.",
                "personality": "diplomatic-but-direct, analytical, builds frameworks.",
                "npcs": "Akhil (sibling, med student), Jason (senior co-resident), Jessica (junior co-resident).",
                "pre_emergence_location": "pre_manhattan",
            },
            choices={
                "post-emergence location": 0,  # manhattan_fragment
                "job bundle": 1,  # second card
                "urgent quest": 0,  # first of the four non-backstory quests
            },
            multi={
                "subcategories": [0, 1],
                # Power offer is 3 from subcat A (indices 0-2) + 3 from subcat B (3-5);
                # must pick one from each band.
                "powers": [0, 3],
            },
        )
        narrator = MockNarrator()
        sz = SessionZero()
        result = sz.run(inputs, narrator, rng=random.Random(42))

        sheet = result["character_sheet"]
        qstate = result["quest_state"]

        self.assertEqual(sheet.name, "Abhishek Rao")
        self.assertEqual(sheet.age_at_onset, 30)
        self.assertEqual(sheet.tier, 3)
        self.assertEqual(sheet.tier_ceiling, 5)
        # Two powers with cast + rider rolled
        self.assertEqual(len(sheet.powers), 2)
        for p in sheet.powers:
            self.assertIn("cast_mode", p)
            self.assertIn("rider_slot", p)
        # Attributes: at least one attribute bumped above d6 (surgeon = Insight d10, Agility d8, …)
        attrs = sheet.attributes.to_dict()
        self.assertTrue(any(v > 6 for v in attrs.values()))
        # Skills from classifier applied
        self.assertGreaterEqual(sheet.skills.get("surgery", 0), 5)
        # NPCs materialized — classifier's 3 + bundle's 3 = 6 minimum
        self.assertGreaterEqual(len(sheet.relationships), 6)
        # Threats: bundle added at least one
        self.assertGreaterEqual(len(sheet.threats), 1)
        # Starting location from bundle
        self.assertTrue(sheet.location)

        # Quest state
        self.assertEqual(len(qstate.quests), 5)
        backgrounds = [q for q in qstate.quests if q.is_background]
        urgents = [q for q in qstate.quests if q.is_urgent]
        self.assertEqual(len(backgrounds), 4)
        self.assertEqual(len(urgents), 1)

        # Bridge prose + opening scene present
        self.assertIn("bridge_prose", result)
        self.assertTrue(result["bridge_prose"])
        self.assertTrue(result["opening_scene"])
        meta = result["opening_scene_meta"]
        self.assertEqual(meta["primary_quest_id"], urgents[0].id)


if __name__ == "__main__":
    unittest.main()
