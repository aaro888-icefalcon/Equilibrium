"""Unit coverage for the behavior introduced by the playtest revision plan.

Tests the contracts the revision guarantees, complementing the existing
quest / sampler / flow tests:

1. Urgent quest must be tactical (combat/escape mode, armed opposition,
   tactical verb, >=1 combat scene).
2. Backstory set must span >= 3 distinct conflict modes.
3. Job bundle must carry >= 1 combat-capable threat per card.
4. Bridge scene requires hooked_npcs and mentioned_factions.
5. step about returns the primer preface.
"""

from __future__ import annotations

import unittest

from emergence.engine.character_creation.bridge_scene import BridgeScene
from emergence.engine.character_creation.job_bundle_scene import JobBundleScene
from emergence.engine.quests.schema import (
    Quest,
    CONFLICT_MODES,
    TACTICAL_VERBS,
    URGENT_CONFLICT_MODES,
    validate_quest,
    validate_quest_set,
)
from emergence.engine.runtime.step_cli import _build_about_preface


def _valid_urgent_dict(quest_id: str = "q_u") -> dict:
    """Minimal urgent-quest dict that passes validation."""
    return {
        "id": quest_id,
        "archetype": "extraction",
        "goal": "Extract the hostage before the patrol clears the tunnel",
        "hook_scene": {"established_on_turn": 0, "inciting_event": "Signal cuts."},
        "central_conflict": {"nature": "time-critical extraction",
                             "proxy_antagonist_id": "npc_patrol_lead"},
        "bright_lines": [{
            "id": "bl_patrol",
            "description": "patrol clears tunnel",
            "check_condition": {"type": "macrostructure", "op": "<=", "value": 0},
            "telegraph_text": "distant engines",
        }],
        "macrostructure": {
            "variable_name": "minutes_until_patrol", "current": 5, "threshold": 0,
            "direction": "decrement", "tick_triggers": ["scene_close"],
        },
        "success_condition": {"type": "npc_status", "npc_id": "npc_hostage",
                              "status": "extracted"},
        "resolution": {
            "world_deltas_on_success": [
                {"op": "faction_standing_delta", "faction_id": "bear_house", "delta": 1}
            ],
            "world_deltas_on_failure": {"bl_patrol": []},
            "narration_cue_on_success": "",
            "narration_cue_on_failure": "",
        },
        "progress_track": {"ticks_filled": 0, "ticks_required": 10,
                           "source": "ironsworn_vow_dangerous"},
        "scope": {"expected_scenes": 3, "expected_session_equivalents": 1.0},
        "is_urgent": True,
        "conflict_mode": "combat",
        "physical_danger": {"armed_opposition": True, "expected_combat_scenes": 1},
        "hook_npcs": ["npc_hostage"],
    }


class TestUrgentQuestRules(unittest.TestCase):
    def test_conflict_modes_contain_expected_set(self) -> None:
        self.assertEqual(
            CONFLICT_MODES, {"combat", "social", "investigation", "escape", "heist"}
        )
        self.assertEqual(URGENT_CONFLICT_MODES, {"combat", "escape"})

    def test_tactical_verbs_include_key_entries(self) -> None:
        for v in ("extract", "disable", "intercept", "breach", "hunt", "rescue"):
            self.assertIn(v, TACTICAL_VERBS)

    def test_urgent_with_social_mode_fails(self) -> None:
        d = _valid_urgent_dict()
        d["conflict_mode"] = "social"
        errors = validate_quest(Quest.from_dict(d))
        self.assertTrue(any("URGENT_CONFLICT_MODES" in e or "conflict_mode" in e for e in errors))

    def test_urgent_without_armed_opposition_fails(self) -> None:
        d = _valid_urgent_dict()
        d["physical_danger"]["armed_opposition"] = False
        errors = validate_quest(Quest.from_dict(d))
        self.assertTrue(any("armed_opposition" in e for e in errors))

    def test_urgent_with_zero_combat_scenes_fails(self) -> None:
        d = _valid_urgent_dict()
        d["physical_danger"]["expected_combat_scenes"] = 0
        errors = validate_quest(Quest.from_dict(d))
        self.assertTrue(any("expected_combat_scenes" in e for e in errors))

    def test_urgent_with_non_tactical_verb_fails(self) -> None:
        d = _valid_urgent_dict()
        d["goal"] = "Negotiate a truce with the Iron Crown sergeant"
        errors = validate_quest(Quest.from_dict(d))
        self.assertTrue(any("TACTICAL_VERBS" in e for e in errors))

    def test_backstory_quest_with_social_mode_allowed(self) -> None:
        d = _valid_urgent_dict()
        d["is_urgent"] = False
        d["is_background"] = True
        d["conflict_mode"] = "social"
        d["goal"] = "Broker the accord before the council rises"
        d["physical_danger"] = {"armed_opposition": False, "expected_combat_scenes": 0}
        self.assertEqual(validate_quest(Quest.from_dict(d)), [])

    def test_valid_urgent_passes(self) -> None:
        self.assertEqual(validate_quest(Quest.from_dict(_valid_urgent_dict())), [])


class TestBackstoryModeDiversity(unittest.TestCase):
    def _bg(self, mode: str) -> Quest:
        return Quest(
            id=f"bg_{mode}", archetype="x", goal="Broker the accord", is_background=True,
            conflict_mode=mode,
        )

    def test_three_modes_passes(self) -> None:
        urgent = Quest(id="u", archetype="x", goal="Extract the packet", is_urgent=True)
        quests = [self._bg("social"), self._bg("investigation"),
                  self._bg("combat"), self._bg("combat"), urgent]
        errors = validate_quest_set(quests)
        self.assertEqual([e for e in errors if "conflict_modes" in e], [])

    def test_two_modes_fails(self) -> None:
        urgent = Quest(id="u", archetype="x", goal="Extract the packet", is_urgent=True)
        quests = [self._bg("social"), self._bg("social"),
                  self._bg("social"), self._bg("combat"), urgent]
        errors = validate_quest_set(quests)
        self.assertTrue(any("conflict_modes" in e for e in errors))


class TestBundleCombatThreatConstraint(unittest.TestCase):
    def _card(self, threat_archetypes, conflicts: bool = True) -> dict:
        return {
            "job_id": "j1", "title": "T", "daily_loop": "loop",
            "post_onset_goal": "Find my sister in the north.",
            "goal_conflicts_with_job": conflicts,
            "goal_conflict_note": (
                "The job keeps me south while she's north." if conflicts else ""
            ),
            "skill_tilts": {"surgery": 1},
            "factions": {"positive": [{"faction_id": "f1", "standing": 1}],
                         "negative": []},
            "npcs": [
                {"name": "A", "role": "ally"},
                {"name": "B", "role": "contact"},
                {"name": "C", "role": "rival"},
            ],
            "threats": [{"archetype": a, "hook": "x"} for a in threat_archetypes],
            "starting_location": "loc", "opening_vignette_seed": "seed",
        }

    def _wrap(self, cards) -> dict:
        return {"cards": cards}

    def test_all_non_combat_threats_fails(self) -> None:
        payload = self._wrap([self._card(["debt_holder"])] * 5)
        for i in range(5):
            payload["cards"][i]["job_id"] = f"j{i}"
        errors = JobBundleScene.validate_bundle_output(payload)
        self.assertTrue(any("combat-capable" in e for e in errors))

    def test_at_least_one_combat_threat_passes(self) -> None:
        payload = self._wrap([self._card(["named_rival_human", "debt_holder"])] * 5)
        for i in range(5):
            payload["cards"][i]["job_id"] = f"j{i}"
        errors = JobBundleScene.validate_bundle_output(payload)
        self.assertFalse(any("combat-capable" in e for e in errors))

    def test_fewer_than_two_goal_conflicts_fails(self) -> None:
        cards = [self._card(["named_rival_human"], conflicts=False) for _ in range(5)]
        # Mark just one card as conflicting; need at least two.
        cards[0]["goal_conflicts_with_job"] = True
        cards[0]["goal_conflict_note"] = "tension between goal and job"
        for i in range(5):
            cards[i]["job_id"] = f"j{i}"
        errors = JobBundleScene.validate_bundle_output(self._wrap(cards))
        self.assertTrue(any("goal_conflicts_with_job" in e for e in errors))

    def test_two_goal_conflicts_passes(self) -> None:
        cards = [self._card(["named_rival_human"], conflicts=False) for _ in range(5)]
        for i in (0, 3):
            cards[i]["goal_conflicts_with_job"] = True
            cards[i]["goal_conflict_note"] = "tension between goal and job"
        for i in range(5):
            cards[i]["job_id"] = f"j{i}"
        errors = JobBundleScene.validate_bundle_output(self._wrap(cards))
        self.assertFalse(any("goal_conflicts_with_job" in e for e in errors))


class TestBridgeHookedNpcs(unittest.TestCase):
    def _quest(self) -> Quest:
        return Quest.from_dict({
            "id": "u", "archetype": "x", "goal": "Extract the packet",
            "central_conflict": {"nature": "n", "proxy_antagonist_id": "npc_a"},
            "bright_lines": [{"id": "bl", "description": "d",
                              "check_condition": {"type": "macrostructure", "op": "<=", "value": 0},
                              "telegraph_text": "t"}],
            "macrostructure": {"variable_name": "v", "current": 5, "threshold": 0,
                               "direction": "decrement", "tick_triggers": ["scene_close"]},
            "success_condition": {"type": "progress_full"},
            "resolution": {
                "world_deltas_on_success": [{"op": "faction_standing_delta",
                                             "faction_id": "f", "delta": 1}],
                "world_deltas_on_failure": {"bl": []},
            },
            "is_urgent": True, "conflict_mode": "combat",
            "physical_danger": {"armed_opposition": True, "expected_combat_scenes": 1},
        })

    def _payload(self, **overrides) -> dict:
        p = {
            "opening_scene": " ".join(["ipsum"] * 200),
            "opening_scene_meta": {
                "primary_quest_id": "u", "antagonist_id": "npc_a",
                "hook_npc_id": "npc_b", "location_id": "loc",
                "telegraph_bright_line_id": "bl",
            },
            "hooked_npcs": [
                {"npc_id": "npc_a", "relation": "rival", "introduced_in": "bridge_present_day"},
                {"npc_id": "npc_b", "relation": "coworker", "introduced_in": "bridge_present_day"},
            ],
            "mentioned_factions": ["brooklyn_tower_lords"],
        }
        p.update(overrides)
        return p

    def test_missing_hooked_npcs_fails(self) -> None:
        p = self._payload()
        del p["hooked_npcs"]
        errors = BridgeScene.validate_bridge_output(p, self._quest(), {"npc_a", "npc_b"})
        self.assertTrue(any("hooked_npcs" in e for e in errors))

    def test_hooked_npc_not_in_bundle_fails(self) -> None:
        p = self._payload()
        p["hooked_npcs"][0]["npc_id"] = "npc_nonexistent"
        errors = BridgeScene.validate_bridge_output(p, self._quest(), {"npc_a", "npc_b"})
        self.assertTrue(any("not in bundle_npc_ids" in e for e in errors))

    def test_missing_mentioned_factions_fails(self) -> None:
        p = self._payload()
        del p["mentioned_factions"]
        errors = BridgeScene.validate_bridge_output(p, self._quest(), {"npc_a", "npc_b"})
        self.assertTrue(any("mentioned_factions" in e for e in errors))

    def test_valid_payload_passes(self) -> None:
        errors = BridgeScene.validate_bridge_output(
            self._payload(), self._quest(), {"npc_a", "npc_b"}
        )
        self.assertEqual(errors, [])


class TestAboutPreface(unittest.TestCase):
    def test_preface_includes_about_banner(self) -> None:
        preface = _build_about_preface()
        self.assertIn("ABOUT EMERGENCE", preface)

    def test_preface_includes_how_to_play(self) -> None:
        preface = _build_about_preface()
        self.assertIn("How to play:", preface)

    def test_preface_mentions_combat_risk(self) -> None:
        preface = _build_about_preface()
        self.assertIn("combat", preface.lower())


if __name__ == "__main__":
    unittest.main()
