"""Unit tests for the quest module."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pytest

from emergence.engine.quests import (
    Quest,
    QuestState,
    QuestValidationError,
    check_success,
    init,
    resolve,
    tick,
    validate_quest,
)
from emergence.engine.quests.archetypes import (
    ARCHETYPES,
    get_archetype,
    list_archetypes,
)
from emergence.engine.quests.deltas import apply_deltas, validate_delta


# ---------------------------------------------------------------------------
# Fakes for WorldView
# ---------------------------------------------------------------------------


@dataclass
class FakePlayer:
    condition_tracks: Dict[str, int] = field(default_factory=lambda: {"physical": 0, "mental": 0, "social": 0})
    heat: Dict[str, int] = field(default_factory=dict)
    corruption: int = 0
    inventory: List[Any] = field(default_factory=list)
    location: str = "start"
    statuses: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, Any] = field(default_factory=dict)
    threats: List[Dict[str, Any]] = field(default_factory=list)
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class FakeNPC:
    id: str
    status: str = "alive"


@dataclass
class FakeFaction:
    id: str
    standing: int = 0


@dataclass
class FakeClock:
    id: str
    current_segment: int = 0


class FakeWorld:
    def __init__(self) -> None:
        self._player = FakePlayer()
        self._npcs: Dict[str, FakeNPC] = {}
        self._factions: Dict[str, FakeFaction] = {}
        self._clocks: Dict[str, FakeClock] = {}
        self.quest_seeds: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []

    def add_npc(self, npc_id: str, status: str = "alive") -> None:
        self._npcs[npc_id] = FakeNPC(id=npc_id, status=status)

    def add_faction(self, faction_id: str, standing: int = 0) -> None:
        self._factions[faction_id] = FakeFaction(id=faction_id, standing=standing)

    def add_clock(self, clock_id: str, current: int = 0) -> None:
        self._clocks[clock_id] = FakeClock(id=clock_id, current_segment=current)

    # WorldView protocol
    def player(self) -> FakePlayer:
        return self._player

    def get_faction(self, faction_id: str) -> Optional[FakeFaction]:
        return self._factions.get(faction_id)

    def get_npc(self, npc_id: str) -> Optional[FakeNPC]:
        return self._npcs.get(npc_id)

    def get_clock(self, clock_id: str) -> Optional[FakeClock]:
        return self._clocks.get(clock_id)

    def add_quest_seed(self, archetype: str, seed: Dict[str, Any]) -> None:
        self.quest_seeds.append({"archetype": archetype, "seed": seed})

    def add_history_event(self, event: Dict[str, Any]) -> None:
        self.history.append(event)


# ---------------------------------------------------------------------------
# Quest fixture
# ---------------------------------------------------------------------------


def _valid_quest_dict(quest_id: str = "q_test_1", **overrides: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "id": quest_id,
        "archetype": "extraction",
        "goal": "Extract Varin from the Corvid corridor before the sweep",
        "hook_scene": {
            "established_on_turn": 0,
            "inciting_event": "Varin's signal cuts three klicks from drop",
        },
        "central_conflict": {
            "nature": "Time-critical extraction under hostile jurisdiction",
            "proxy_antagonist_id": "npc_sweep_lead",
        },
        "bright_lines": [
            {
                "id": "bl_sweep_arrives",
                "description": "Northbound sweep reaches extraction zone before PC clears",
                "check_condition": {"type": "macrostructure", "op": "<=", "value": 0},
                "telegraph_text": "the distant bell marking shift change; three hours of light",
            },
            {
                "id": "bl_varin_dies",
                "description": "Target dies before extraction",
                "check_condition": {
                    "type": "npc_status",
                    "npc_id": "npc_varin",
                    "status": "dead",
                },
                "telegraph_text": "Varin's injury visible and worsening",
            },
        ],
        "macrostructure": {
            "variable_name": "hours_until_sweep",
            "current": 5,
            "threshold": 0,
            "direction": "decrement",
            "tick_triggers": ["world_pulse", "travel_segment", "rest_action", "scene_close"],
        },
        "success_condition": {
            "type": "and",
            "predicates": [
                {"type": "npc_status", "npc_id": "npc_varin", "status": "extracted"},
                {"type": "pc_location_not", "location_id": "corvid_corridor"},
            ],
        },
        "resolution": {
            "world_deltas_on_success": [
                {"op": "faction_standing_delta", "faction_id": "bear_house", "delta": 1},
            ],
            "world_deltas_on_failure": {
                "bl_sweep_arrives": [
                    {"op": "npc_status_set", "npc_id": "npc_varin", "status": "captured"},
                ],
                "bl_varin_dies": [
                    {"op": "faction_standing_delta", "faction_id": "bear_house", "delta": -2},
                ],
            },
            "narration_cue_on_success": "clean exit; Varin walks out on her own feet",
            "narration_cue_on_failure": "",
        },
        "progress_track": {"ticks_filled": 0, "ticks_required": 10, "source": "ironsworn_vow_dangerous"},
        "scope": {"expected_scenes": 3, "expected_session_equivalents": 1.0},
        "is_urgent": True,
        "conflict_mode": "combat",
        "physical_danger": {"armed_opposition": True, "expected_combat_scenes": 2},
        "hook_npcs": ["npc_varin"],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_valid_quest_passes(self) -> None:
        q = Quest.from_dict(_valid_quest_dict())
        assert validate_quest(q) == []

    def test_missing_goal(self) -> None:
        q = Quest.from_dict(_valid_quest_dict(goal=""))
        errs = validate_quest(q)
        assert any("goal" in e for e in errs)

    def test_non_imperative_goal(self) -> None:
        q = Quest.from_dict(_valid_quest_dict(goal=""))
        errs = validate_quest(q)
        assert errs  # empty goal always fails

    def test_too_long_goal(self) -> None:
        long = "Get " + " ".join(f"word{i}" for i in range(30))
        q = Quest.from_dict(_valid_quest_dict(goal=long))
        errs = validate_quest(q)
        assert any("verb-the-noun" in e for e in errs)

    def test_no_bright_lines_fails(self) -> None:
        d = _valid_quest_dict()
        d["bright_lines"] = []
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("bright_lines" in e for e in errs)

    def test_duplicate_bright_line_ids(self) -> None:
        d = _valid_quest_dict()
        d["bright_lines"][1]["id"] = d["bright_lines"][0]["id"]
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("duplicate" in e for e in errs)

    def test_bright_line_missing_telegraph(self) -> None:
        d = _valid_quest_dict()
        d["bright_lines"][0]["telegraph_text"] = ""
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("telegraph_text" in e for e in errs)

    def test_invalid_tick_trigger(self) -> None:
        d = _valid_quest_dict()
        d["macrostructure"]["tick_triggers"] = ["not_a_real_trigger"]
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("tick_triggers" in e for e in errs)

    def test_macrostructure_starts_past_threshold(self) -> None:
        d = _valid_quest_dict()
        d["macrostructure"]["current"] = 0  # decrement, threshold 0 → already at
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("threshold" in e for e in errs)

    def test_missing_failure_branch_for_bright_line(self) -> None:
        d = _valid_quest_dict()
        del d["resolution"]["world_deltas_on_failure"]["bl_varin_dies"]
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("bl_varin_dies" in e for e in errs)

    def test_no_success_deltas(self) -> None:
        d = _valid_quest_dict()
        d["resolution"]["world_deltas_on_success"] = []
        q = Quest.from_dict(d)
        errs = validate_quest(q)
        assert any("world_deltas_on_success" in e for e in errs)


# ---------------------------------------------------------------------------
# Archetypes
# ---------------------------------------------------------------------------


class TestArchetypes:
    def test_eighteen_archetypes(self) -> None:
        assert len(ARCHETYPES) == 18

    def test_all_archetypes_have_unique_ids(self) -> None:
        ids = [a.id for a in ARCHETYPES]
        assert len(ids) == len(set(ids))

    def test_get_archetype_found(self) -> None:
        a = get_archetype("extraction")
        assert a.id == "extraction"
        assert a.goal_template.startswith("Get ")

    def test_get_archetype_missing(self) -> None:
        with pytest.raises(KeyError):
            get_archetype("no_such_archetype")

    def test_list_archetypes_json_safe(self) -> None:
        import json
        # If any archetype isn't JSON-serializable, this will raise.
        json.dumps(list_archetypes())

    def test_all_archetypes_have_at_least_one_bright_line_template(self) -> None:
        for a in ARCHETYPES:
            assert a.bright_line_templates, f"{a.id} has no bright_line_templates"

    def test_all_archetypes_specify_direction(self) -> None:
        for a in ARCHETYPES:
            assert a.macrostructure_direction in ("decrement", "increment")


# ---------------------------------------------------------------------------
# Delta validation & application
# ---------------------------------------------------------------------------


class TestDeltas:
    def test_unknown_op_rejected(self) -> None:
        errs = validate_delta({"op": "do_something_bad"})
        assert errs

    def test_faction_standing_delta_requires_fields(self) -> None:
        errs = validate_delta({"op": "faction_standing_delta"})
        assert errs

    def test_apply_faction_standing_delta(self) -> None:
        world = FakeWorld()
        world.add_faction("bear_house", standing=0)
        world._player.relationships["bear_house"] = type("R", (), {"standing": 0, "trust": 0})()
        result = apply_deltas([{"op": "faction_standing_delta", "faction_id": "bear_house", "delta": 2}], world)
        assert len(result.applied) == 1
        assert world._factions["bear_house"].standing == 2

    def test_apply_npc_status_set(self) -> None:
        world = FakeWorld()
        world.add_npc("npc_varin", status="alive")
        result = apply_deltas([{"op": "npc_status_set", "npc_id": "npc_varin", "status": "extracted"}], world)
        assert len(result.applied) == 1
        assert world._npcs["npc_varin"].status == "extracted"

    def test_apply_missing_npc_skips(self) -> None:
        world = FakeWorld()
        result = apply_deltas([{"op": "npc_status_set", "npc_id": "ghost", "status": "dead"}], world)
        assert len(result.applied) == 0
        assert len(result.skipped) == 1

    def test_apply_threat_add(self) -> None:
        world = FakeWorld()
        result = apply_deltas([{"op": "threat_add", "threat": {"id": "t1", "name": "Sweep Captain"}}], world)
        assert len(result.applied) == 1
        assert world._player.threats[0]["id"] == "t1"

    def test_apply_quest_seed_forwarded(self) -> None:
        world = FakeWorld()
        result = apply_deltas([{"op": "quest_seed", "archetype": "hunt", "seed": {"target": "x"}}], world)
        assert len(result.applied) == 1
        assert world.quest_seeds[0]["archetype"] == "hunt"


# ---------------------------------------------------------------------------
# Lifecycle: init / tick / check_success / resolve
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_init_appends_and_validates(self) -> None:
        state = QuestState()
        qid = init(state, _valid_quest_dict())
        assert qid == "q_test_1"
        assert len(state.quests) == 1

    def test_init_rejects_invalid(self) -> None:
        state = QuestState()
        bad = _valid_quest_dict(goal="")
        with pytest.raises(QuestValidationError):
            init(state, bad)

    def test_init_assigns_id_when_missing(self) -> None:
        state = QuestState()
        d = _valid_quest_dict()
        del d["id"]
        qid = init(state, d)
        assert qid.startswith("q_")
        assert len(state.quests) == 1

    def test_init_rejects_duplicate_id(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict(quest_id="q_same"))
        with pytest.raises(QuestValidationError):
            init(state, _valid_quest_dict(quest_id="q_same"))

    def test_tick_decrements_only_eligible(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict(quest_id="q_with_pulse"))
        # Second quest without world_pulse in triggers
        d2 = _valid_quest_dict(quest_id="q_without_pulse")
        d2["macrostructure"]["tick_triggers"] = ["scene_close"]
        init(state, d2)

        reports = tick(state, "world_pulse", magnitude=1)
        # Only the first quest should have ticked
        ticked_ids = [r.quest_id for r in reports]
        assert "q_with_pulse" in ticked_ids
        assert "q_without_pulse" not in ticked_ids

    def test_tick_fires_bright_line_and_auto_resolves(self) -> None:
        state = QuestState()
        d = _valid_quest_dict()
        d["macrostructure"]["current"] = 1
        init(state, d)
        world = FakeWorld()
        world.add_faction("bear_house", standing=0)

        reports = tick(state, "world_pulse", magnitude=2, world=world)

        assert len(reports) == 1
        assert reports[0].bright_line_fired == "bl_sweep_arrives"
        assert reports[0].resolved_as == "failure"
        assert len(state.quests) == 0
        assert len(state.failed) == 1

    def test_check_success_resolves_quest(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict())

        world = FakeWorld()
        world.add_faction("bear_house", standing=0)
        world.add_npc("npc_varin", status="extracted")
        world._player.location = "safe_house"

        results = check_success(state, world)

        assert len(results) == 1
        assert results[0].succeeded is True
        assert results[0].resolved_as == "success"
        assert len(state.resolved) == 1
        assert len(state.quests) == 0

    def test_resolve_applies_success_deltas(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict())
        world = FakeWorld()
        world.add_faction("bear_house", standing=0)

        report = resolve(state, world, "q_test_1", success=True)

        assert report.success is True
        assert len(report.delta_result.applied) == 1
        assert world._factions["bear_house"].standing == 1
        assert state.quests == []
        assert len(state.resolved) == 1

    def test_resolve_failure_uses_bright_line_branch(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict())
        world = FakeWorld()
        world.add_npc("npc_varin", status="alive")
        world.add_faction("bear_house", standing=0)

        report = resolve(state, world, "q_test_1", success=False, bright_line_id="bl_sweep_arrives")

        assert report.success is False
        assert world._npcs["npc_varin"].status == "captured"

    def test_resolve_requires_bright_line_on_failure(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict())
        world = FakeWorld()
        with pytest.raises(ValueError):
            resolve(state, world, "q_test_1", success=False)

    def test_resolve_unknown_quest_raises(self) -> None:
        state = QuestState()
        world = FakeWorld()
        with pytest.raises(KeyError):
            resolve(state, world, "no_such_quest", success=True)

    def test_serialize_round_trip(self) -> None:
        state = QuestState()
        init(state, _valid_quest_dict())
        restored = QuestState.from_dict(state.to_dict())
        assert len(restored.quests) == 1
        assert restored.quests[0].goal == state.quests[0].goal


# ---------------------------------------------------------------------------
# Predicate evaluation edge cases
# ---------------------------------------------------------------------------


class TestPredicates:
    def _quest(self) -> Quest:
        return Quest.from_dict(_valid_quest_dict())

    def test_and_both_true(self) -> None:
        from emergence.engine.quests.quest import evaluate_predicate
        q = self._quest()
        world = FakeWorld()
        world.add_npc("npc_varin", status="extracted")
        world._player.location = "safe_house"
        assert evaluate_predicate(q.success_condition, q, world) is True

    def test_and_one_false(self) -> None:
        from emergence.engine.quests.quest import evaluate_predicate
        q = self._quest()
        world = FakeWorld()
        world.add_npc("npc_varin", status="alive")
        world._player.location = "safe_house"
        assert evaluate_predicate(q.success_condition, q, world) is False

    def test_missing_npc_returns_false(self) -> None:
        from emergence.engine.quests.quest import evaluate_predicate
        q = self._quest()
        world = FakeWorld()
        assert evaluate_predicate(q.success_condition, q, world) is False

    def test_macrostructure_predicate(self) -> None:
        from emergence.engine.quests.quest import evaluate_predicate
        q = self._quest()
        q.macrostructure.current = 0
        pred = {"type": "macrostructure", "op": "<=", "value": 0}
        assert evaluate_predicate(pred, q, None) is True

    def test_not_predicate(self) -> None:
        from emergence.engine.quests.quest import evaluate_predicate
        q = self._quest()
        pred = {"type": "not", "predicate": {"type": "progress_full"}}
        assert evaluate_predicate(pred, q, None) is True  # track is empty
        q.progress_track.ticks_filled = 99
        assert evaluate_predicate(pred, q, None) is False
