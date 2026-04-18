"""Quest lifecycle — init, tick, check_success, resolve.

All mutation of QuestState routes through these four functions. Narrator code
must never write to QuestState.quests[*] directly.

Contract:
    - init(state, quest_dict) -> quest_id
        Validates `quest_dict` against schema, appends to state.quests.
        Returns the new quest's id. Raises QuestValidationError on failure.

    - tick(state, event_type, magnitude=1, quest_id=None) -> List[TickReport]
        For each quest in state.quests whose tick_triggers include event_type
        (or for the specific quest_id), decrements/increments macrostructure
        by magnitude. If a bright_line fires after the tick, auto-calls
        resolve(success=False, bright_line_id=<that bl>). Returns a report
        per affected quest.

    - check_success(state, world, quest_id=None) -> List[CheckResult]
        Evaluates success_condition for each quest (or the named one) against
        the current world. If a quest's condition is satisfied, auto-calls
        resolve(success=True). Returns a report per evaluated quest.

    - resolve(state, world, quest_id, success, bright_line_id=None)
        Applies resolution deltas, moves the quest from state.quests to
        state.resolved or state.failed. Returns the DeltaResult.

Abandon is NOT supported. A quest ends only via success, bright-line fire,
or natural macrostructure expiry (which fires the designated bright_line).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.quests.deltas import (
    DeltaResult,
    WorldView,
    apply_deltas,
)
from emergence.engine.quests.schema import (
    BrightLine,
    Macrostructure,
    Predicate,
    Quest,
    QuestState,
    QuestValidationError,
    validate_quest,
    validate_predicate,
)


# ---------------------------------------------------------------------------
# Reports (return values)
# ---------------------------------------------------------------------------


@dataclass
class TickReport:
    quest_id: str
    variable_name: str
    before: float
    after: float
    direction: str
    bright_line_fired: Optional[str] = None
    resolved_as: Optional[str] = None  # "success" | "failure" | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "variable_name": self.variable_name,
            "before": self.before,
            "after": self.after,
            "direction": self.direction,
            "bright_line_fired": self.bright_line_fired,
            "resolved_as": self.resolved_as,
        }


@dataclass
class CheckResult:
    quest_id: str
    succeeded: bool
    resolved_as: Optional[str] = None  # "success" | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "succeeded": self.succeeded,
            "resolved_as": self.resolved_as,
        }


@dataclass
class ResolveReport:
    quest_id: str
    success: bool
    bright_line_id: Optional[str]
    delta_result: DeltaResult = field(default_factory=DeltaResult)
    narration_cue: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quest_id": self.quest_id,
            "success": self.success,
            "bright_line_id": self.bright_line_id,
            "delta_result": self.delta_result.to_dict(),
            "narration_cue": self.narration_cue,
        }


# ---------------------------------------------------------------------------
# CLI functions
# ---------------------------------------------------------------------------


def init(state: QuestState, quest_dict: Dict[str, Any]) -> str:
    """Validate and append a Quest to state.quests. Return its id.

    If `quest_dict["id"]` is missing or empty, a uuid4 is assigned.
    """
    if "id" not in quest_dict or not quest_dict["id"]:
        quest_dict = dict(quest_dict)
        quest_dict["id"] = f"q_{uuid.uuid4().hex[:10]}"
    quest = Quest.from_dict(quest_dict)
    errors = validate_quest(quest)
    if errors:
        raise QuestValidationError(errors)
    # Reject duplicate ids against active + resolved + failed.
    existing_ids = {q.id for q in state.quests} | {q.id for q in state.resolved} | {q.id for q in state.failed}
    if quest.id in existing_ids:
        raise QuestValidationError([f"id: duplicate {quest.id!r} already in state"])
    state.quests.append(quest)
    return quest.id


def tick(
    state: QuestState,
    event_type: str,
    magnitude: float = 1.0,
    quest_id: Optional[str] = None,
    world: Optional[WorldView] = None,
) -> List[TickReport]:
    """Advance macrostructures for eligible quests.

    If `quest_id` is None, every quest whose tick_triggers include event_type
    is affected. If `quest_id` is provided, only that quest is ticked (and
    still only if event_type is in its tick_triggers, unless event_type is
    the literal string "force").

    If a bright_line fires after tick, auto-resolves the quest as failure.
    """
    reports: List[TickReport] = []

    targets: List[Quest]
    if quest_id is not None:
        q = state.get(quest_id)
        targets = [q] if q is not None else []
    else:
        targets = list(state.quests)

    for q in targets:
        ms = q.macrostructure
        if quest_id is None and event_type not in ms.tick_triggers:
            continue
        if quest_id is not None and event_type != "force" and event_type not in ms.tick_triggers:
            continue

        before = ms.current
        if ms.direction == "decrement":
            ms.current = max(ms.current - magnitude, ms.threshold - 1)
        else:
            ms.current = min(ms.current + magnitude, ms.threshold + 1)

        report = TickReport(
            quest_id=q.id,
            variable_name=ms.variable_name,
            before=before,
            after=ms.current,
            direction=ms.direction,
        )

        # Check if any bright line fires after the tick.
        fired_bl = _first_fired_bright_line(q, world)
        if fired_bl is not None:
            report.bright_line_fired = fired_bl.id
            if world is not None:
                resolve_report = resolve(state, world, q.id, success=False, bright_line_id=fired_bl.id)
                report.resolved_as = "failure" if not resolve_report.success else "success"
        reports.append(report)

    return reports


def check_success(
    state: QuestState,
    world: WorldView,
    quest_id: Optional[str] = None,
) -> List[CheckResult]:
    """Evaluate success_condition for each quest; auto-resolve on success."""
    results: List[CheckResult] = []

    targets: List[Quest]
    if quest_id is not None:
        q = state.get(quest_id)
        targets = [q] if q is not None else []
    else:
        targets = list(state.quests)

    for q in targets:
        succeeded = evaluate_predicate(q.success_condition, q, world)
        result = CheckResult(quest_id=q.id, succeeded=succeeded)
        if succeeded:
            resolve_report = resolve(state, world, q.id, success=True)
            result.resolved_as = "success" if resolve_report.success else None
        results.append(result)

    return results


def resolve(
    state: QuestState,
    world: WorldView,
    quest_id: str,
    success: bool,
    bright_line_id: Optional[str] = None,
) -> ResolveReport:
    """Apply resolution deltas; move quest to resolved or failed."""
    q = state.get(quest_id)
    if q is None:
        raise KeyError(f"quest not in active set: {quest_id!r}")

    if success:
        deltas = q.resolution.world_deltas_on_success
        cue = q.resolution.narration_cue_on_success
    else:
        if bright_line_id is None:
            raise ValueError("bright_line_id required when success=False")
        deltas = q.resolution.world_deltas_on_failure.get(bright_line_id, [])
        cue = q.resolution.narration_cue_on_failure

    delta_result = apply_deltas(deltas, world)

    # Migrate the quest out of the active list.
    state.quests = [other for other in state.quests if other.id != q.id]
    if success:
        state.resolved.append(q)
    else:
        state.failed.append(q)

    return ResolveReport(
        quest_id=q.id,
        success=success,
        bright_line_id=bright_line_id,
        delta_result=delta_result,
        narration_cue=cue,
    )


def abandon_not_supported(*_args: Any, **_kwargs: Any) -> None:
    """Sentinel: quests cannot be abandoned. They end via success, bright
    line fire, or macrostructure expiry (which fires the designated
    bright_line). This function exists so that attempts to import an
    abandon verb surface as an explicit error rather than silent no-op.
    """
    raise NotImplementedError(
        "Quests cannot be abandoned. Failure is via bright line fire "
        "or macrostructure expiry."
    )


# ---------------------------------------------------------------------------
# Predicate evaluation
# ---------------------------------------------------------------------------


_NUMERIC_OP_FUNCS = {
    "<":  lambda a, b: a <  b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    ">=": lambda a, b: a >= b,
    ">":  lambda a, b: a >  b,
    "!=": lambda a, b: a != b,
}


def evaluate_predicate(
    predicate: Dict[str, Any],
    quest: Quest,
    world: Optional[WorldView],
) -> bool:
    """Evaluate a Predicate against the given quest + world.

    Returns False (rather than raising) if the predicate references missing
    entities — a quest cannot "succeed" because an NPC has been removed
    from the world. Structural errors in the predicate do raise.
    """
    errs = validate_predicate(predicate)
    if errs:
        raise ValueError("invalid predicate: " + "; ".join(errs))

    ptype = predicate["type"]

    if ptype == "and":
        return all(evaluate_predicate(p, quest, world) for p in predicate["predicates"])
    if ptype == "or":
        return any(evaluate_predicate(p, quest, world) for p in predicate["predicates"])
    if ptype == "not":
        return not evaluate_predicate(predicate["predicate"], quest, world)

    if ptype == "macrostructure":
        cmp_fn = _NUMERIC_OP_FUNCS[predicate["op"]]
        return cmp_fn(quest.macrostructure.current, predicate["value"])

    if ptype == "progress_full":
        return quest.progress_track.is_full()

    # Remaining predicates need a world.
    if world is None:
        return False

    if ptype == "npc_status":
        npc = world.get_npc(predicate["npc_id"])
        if npc is None:
            return False
        status = getattr(npc, "status", None)
        if status is None and isinstance(npc, dict):
            status = npc.get("status")
        return status == predicate["status"]

    if ptype == "pc_status":
        player = world.player()
        if player is None:
            return False
        # Player "status" is modeled as membership in `statuses` list or a
        # direct attribute. We accept either.
        direct = getattr(player, "status", None)
        if direct is not None and direct == predicate["status"]:
            return True
        statuses = getattr(player, "statuses", None) or []
        for s in statuses:
            name = getattr(s, "name", None) or (s.get("name") if isinstance(s, dict) else None)
            if name == predicate["status"]:
                return True
        return False

    if ptype == "pc_location":
        player = world.player()
        if player is None:
            return False
        return getattr(player, "location", "") == predicate["location_id"]

    if ptype == "pc_location_not":
        player = world.player()
        if player is None:
            return False
        return getattr(player, "location", "") != predicate["location_id"]

    if ptype == "faction_standing":
        faction = world.get_faction(predicate["faction_id"])
        # Faction "standing" may live on the faction or on player.relationships.
        # Prefer the player-relationship view (what the faction thinks of the PC).
        standing: Optional[float] = None
        player = world.player()
        if player is not None:
            rels = getattr(player, "relationships", None)
            if rels is not None:
                rel = rels.get(predicate["faction_id"])
                if rel is not None:
                    standing = getattr(rel, "standing", None)
                    if standing is None and isinstance(rel, dict):
                        standing = rel.get("standing")
        if standing is None and faction is not None:
            standing = getattr(faction, "standing", None)
            if standing is None and isinstance(faction, dict):
                standing = faction.get("standing")
        if standing is None:
            return False
        cmp_fn = _NUMERIC_OP_FUNCS[predicate["op"]]
        return cmp_fn(standing, predicate["value"])

    return False


def _first_fired_bright_line(quest: Quest, world: Optional[WorldView]) -> Optional[BrightLine]:
    """Return the first bright line whose check_condition evaluates True."""
    for bl in quest.bright_lines:
        try:
            if evaluate_predicate(bl.check_condition, quest, world):
                return bl
        except ValueError:
            continue
    return None
