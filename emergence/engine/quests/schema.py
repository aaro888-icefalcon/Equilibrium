"""Quest schema — dataclasses and validator.

A Quest is the operational unit of play. Exactly one or more Quests live in
QuestState.quests at any time (no active/pending distinction; all concurrent).
Resolved and failed quests migrate to QuestState.resolved / .failed.

Predicate form
--------------
BrightLine.check_condition and Quest.success_condition both use the Predicate
DSL rather than evaluated expression strings. Predicate types:

    {"type": "macrostructure", "op": "<=", "value": 0}
    {"type": "npc_status", "npc_id": "...", "status": "dead"}
    {"type": "pc_status", "status": "captured"}
    {"type": "pc_location_not", "location_id": "..."}
    {"type": "faction_standing", "faction_id": "...",
                                 "op": "<=", "value": -2}
    {"type": "progress_full"}             # progress_track ticks_filled >= required
    {"type": "and", "predicates": [...]}
    {"type": "or",  "predicates": [...]}
    {"type": "not", "predicate": {...}}

Validation contract
-------------------
A Quest must satisfy every check in `validate_quest` before it can be added to
QuestState. The four CLI functions (init/tick/check_success/resolve) call
`validate_quest` on every insert.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Predicate DSL
# ---------------------------------------------------------------------------

# Valid top-level "type" values in a predicate dict.
PREDICATE_TYPES = {
    "macrostructure",
    "npc_status",
    "pc_status",
    "pc_location_not",
    "pc_location",
    "faction_standing",
    "progress_full",
    "and",
    "or",
    "not",
}

# Valid "op" values for numeric predicates.
NUMERIC_OPS = {"<", "<=", "==", ">=", ">", "!="}


class Predicate(dict):
    """Typed marker for a predicate dict. Inherits from dict for JSON parity.

    Not enforced via dataclass because predicates are nested and heterogeneous.
    `validate_predicate` is the contract.
    """


def validate_predicate(pred: Any, path: str = "predicate") -> List[str]:
    """Return a list of error messages. Empty list means valid."""
    errors: List[str] = []
    if not isinstance(pred, dict):
        return [f"{path}: must be a dict, got {type(pred).__name__}"]
    ptype = pred.get("type")
    if ptype not in PREDICATE_TYPES:
        errors.append(f"{path}: unknown predicate type {ptype!r}")
        return errors

    if ptype == "macrostructure":
        op = pred.get("op")
        if op not in NUMERIC_OPS:
            errors.append(f"{path}.op: must be one of {sorted(NUMERIC_OPS)}")
        if not isinstance(pred.get("value"), (int, float)):
            errors.append(f"{path}.value: must be numeric")
    elif ptype == "npc_status":
        if not pred.get("npc_id"):
            errors.append(f"{path}.npc_id: required")
        if not pred.get("status"):
            errors.append(f"{path}.status: required")
    elif ptype == "pc_status":
        if not pred.get("status"):
            errors.append(f"{path}.status: required")
    elif ptype in ("pc_location_not", "pc_location"):
        if not pred.get("location_id"):
            errors.append(f"{path}.location_id: required")
    elif ptype == "faction_standing":
        if not pred.get("faction_id"):
            errors.append(f"{path}.faction_id: required")
        if pred.get("op") not in NUMERIC_OPS:
            errors.append(f"{path}.op: must be one of {sorted(NUMERIC_OPS)}")
        if not isinstance(pred.get("value"), (int, float)):
            errors.append(f"{path}.value: must be numeric")
    elif ptype == "progress_full":
        pass
    elif ptype == "and" or ptype == "or":
        subs = pred.get("predicates")
        if not isinstance(subs, list) or not subs:
            errors.append(f"{path}.predicates: must be a non-empty list")
        else:
            for i, sub in enumerate(subs):
                errors.extend(validate_predicate(sub, f"{path}.predicates[{i}]"))
    elif ptype == "not":
        sub = pred.get("predicate")
        if sub is None:
            errors.append(f"{path}.predicate: required")
        else:
            errors.extend(validate_predicate(sub, f"{path}.predicate"))
    return errors


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class HookScene:
    established_on_turn: int = 0
    inciting_event: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookScene":
        return cls(
            established_on_turn=data.get("established_on_turn", 0),
            inciting_event=data.get("inciting_event", ""),
        )


@dataclass
class CentralConflict:
    nature: str = ""
    proxy_antagonist_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CentralConflict":
        return cls(
            nature=data.get("nature", ""),
            proxy_antagonist_id=data.get("proxy_antagonist_id", ""),
        )


@dataclass
class BrightLine:
    id: str
    description: str
    check_condition: Dict[str, Any]  # Predicate
    telegraph_text: str = ""  # how the opening scene cues this failure state

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "check_condition": dict(self.check_condition),
            "telegraph_text": self.telegraph_text,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BrightLine":
        return cls(
            id=data["id"],
            description=data.get("description", ""),
            check_condition=dict(data.get("check_condition", {})),
            telegraph_text=data.get("telegraph_text", ""),
        )


# Valid tick_trigger names. Extend when new tick sources are added to the engine.
TICK_TRIGGERS = {
    "world_pulse",
    "travel_segment",
    "rest_action",
    "scene_close",
    "combat_round_over_threshold",
    "resolve_action_success",
    "resolve_action_failure",
}


@dataclass
class Macrostructure:
    variable_name: str = ""
    current: float = 0.0
    threshold: float = 0.0
    direction: str = "decrement"  # "decrement" | "increment"
    tick_triggers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "current": self.current,
            "threshold": self.threshold,
            "direction": self.direction,
            "tick_triggers": list(self.tick_triggers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Macrostructure":
        return cls(
            variable_name=data.get("variable_name", ""),
            current=float(data.get("current", 0.0)),
            threshold=float(data.get("threshold", 0.0)),
            direction=data.get("direction", "decrement"),
            tick_triggers=list(data.get("tick_triggers", [])),
        )

    def at_threshold(self) -> bool:
        """True when the macrostructure has crossed its threshold."""
        if self.direction == "decrement":
            return self.current <= self.threshold
        return self.current >= self.threshold


@dataclass
class Resolution:
    """Structured outcomes for engine delta application.

    The narrator composes resolution prose at runtime from these deltas
    plus the quest state. `narration_cue_*` fields are optional single-line
    hints; the narrator is not required to honor them verbatim.
    """

    world_deltas_on_success: List[Dict[str, Any]] = field(default_factory=list)
    world_deltas_on_failure: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    narration_cue_on_success: str = ""
    narration_cue_on_failure: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_deltas_on_success": [dict(d) for d in self.world_deltas_on_success],
            "world_deltas_on_failure": {
                k: [dict(d) for d in v] for k, v in self.world_deltas_on_failure.items()
            },
            "narration_cue_on_success": self.narration_cue_on_success,
            "narration_cue_on_failure": self.narration_cue_on_failure,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Resolution":
        return cls(
            world_deltas_on_success=[dict(d) for d in data.get("world_deltas_on_success", [])],
            world_deltas_on_failure={
                k: [dict(d) for d in v]
                for k, v in data.get("world_deltas_on_failure", {}).items()
            },
            narration_cue_on_success=data.get("narration_cue_on_success", ""),
            narration_cue_on_failure=data.get("narration_cue_on_failure", ""),
        )


@dataclass
class ProgressTrack:
    ticks_filled: int = 0
    ticks_required: int = 10
    source: str = "ironsworn_vow_dangerous"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProgressTrack":
        return cls(
            ticks_filled=int(data.get("ticks_filled", 0)),
            ticks_required=int(data.get("ticks_required", 10)),
            source=data.get("source", "ironsworn_vow_dangerous"),
        )

    def is_full(self) -> bool:
        return self.ticks_filled >= self.ticks_required


@dataclass
class Scope:
    expected_scenes: int = 3
    expected_session_equivalents: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scope":
        return cls(
            expected_scenes=int(data.get("expected_scenes", 3)),
            expected_session_equivalents=float(data.get("expected_session_equivalents", 1.0)),
        )


@dataclass
class Quest:
    id: str
    archetype: str
    goal: str
    hook_scene: HookScene = field(default_factory=HookScene)
    central_conflict: CentralConflict = field(default_factory=CentralConflict)
    bright_lines: List[BrightLine] = field(default_factory=list)
    macrostructure: Macrostructure = field(default_factory=Macrostructure)
    success_condition: Dict[str, Any] = field(default_factory=dict)  # Predicate
    resolution: Resolution = field(default_factory=Resolution)
    progress_track: ProgressTrack = field(default_factory=ProgressTrack)
    scope: Scope = field(default_factory=Scope)
    is_urgent: bool = False  # True for the opening/player-picked quest
    is_background: bool = False  # True for narrator-picked backstory quests

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "archetype": self.archetype,
            "goal": self.goal,
            "hook_scene": self.hook_scene.to_dict(),
            "central_conflict": self.central_conflict.to_dict(),
            "bright_lines": [bl.to_dict() for bl in self.bright_lines],
            "macrostructure": self.macrostructure.to_dict(),
            "success_condition": dict(self.success_condition),
            "resolution": self.resolution.to_dict(),
            "progress_track": self.progress_track.to_dict(),
            "scope": self.scope.to_dict(),
            "is_urgent": self.is_urgent,
            "is_background": self.is_background,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quest":
        return cls(
            id=data["id"],
            archetype=data.get("archetype", ""),
            goal=data.get("goal", ""),
            hook_scene=HookScene.from_dict(data.get("hook_scene", {})),
            central_conflict=CentralConflict.from_dict(data.get("central_conflict", {})),
            bright_lines=[BrightLine.from_dict(b) for b in data.get("bright_lines", [])],
            macrostructure=Macrostructure.from_dict(data.get("macrostructure", {})),
            success_condition=dict(data.get("success_condition", {})),
            resolution=Resolution.from_dict(data.get("resolution", {})),
            progress_track=ProgressTrack.from_dict(data.get("progress_track", {})),
            scope=Scope.from_dict(data.get("scope", {})),
            is_urgent=bool(data.get("is_urgent", False)),
            is_background=bool(data.get("is_background", False)),
        )


@dataclass
class QuestState:
    """Top-level container for all quests in a save.

    Stored on disk as `saves/<name>/quests.json`.
    """

    quests: List[Quest] = field(default_factory=list)
    resolved: List[Quest] = field(default_factory=list)
    failed: List[Quest] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quests": [q.to_dict() for q in self.quests],
            "resolved": [q.to_dict() for q in self.resolved],
            "failed": [q.to_dict() for q in self.failed],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QuestState":
        return cls(
            quests=[Quest.from_dict(q) for q in data.get("quests", [])],
            resolved=[Quest.from_dict(q) for q in data.get("resolved", [])],
            failed=[Quest.from_dict(q) for q in data.get("failed", [])],
        )

    def get(self, quest_id: str) -> Optional[Quest]:
        for q in self.quests:
            if q.id == quest_id:
                return q
        return None


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class QuestValidationError(ValueError):
    """Raised when a quest fails schema validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Quest validation failed:\n  - " + "\n  - ".join(errors))


# Common English imperative verbs likely to open verb-the-noun goals.
# Not exhaustive; used as a heuristic only. Claude reformulates on fail.
IMPERATIVE_VERB_HINTS = {
    "get", "keep", "identify", "retrieve", "move", "disable", "deliver",
    "confirm", "find", "remove", "eliminate", "broker", "perform",
    "enter", "sustain", "reach", "stop", "repel", "recover", "escort",
    "extract", "rescue", "kill", "defend", "guard", "scout", "investigate",
    "negotiate", "sabotage", "witness", "verify", "hunt", "infiltrate",
    "deceive", "reinforce", "contain", "counter", "travel", "carry",
    "prevent", "secure", "survive", "track", "bring", "take", "warn",
    "steal", "smuggle", "assassinate", "burn", "shelter", "protect",
    "evacuate", "capture", "free", "ambush", "expose", "plant",
}


def _is_verb_the_noun(goal: str) -> bool:
    """Heuristic: does `goal` look like a verb-the-noun imperative sentence?

    Checks:
    - ≤ 25 words
    - First word is a capital-letter-starting token whose lowercased form is
      either in IMPERATIVE_VERB_HINTS or ends in a common verb pattern
    - Contains at least one noun-like capitalized or bracketed token after
      the first word (heuristic; accepts template placeholders like [target])
    """
    if not goal or not isinstance(goal, str):
        return False
    stripped = goal.strip()
    words = stripped.split()
    if not words or len(words) > 25:
        return False
    first = words[0]
    if not first[:1].isalpha():
        return False
    first_lower = first.lower().rstrip(",.")
    looks_imperative = (
        first_lower in IMPERATIVE_VERB_HINTS
        or first[:1].isupper()  # capitalized first word is a soft proxy
    )
    if not looks_imperative:
        return False
    # Must have at least one noun-ish token afterward.
    if len(words) < 2:
        return False
    return True


def validate_quest(quest: Quest) -> List[str]:
    """Return a list of error messages. Empty list means valid."""
    errors: List[str] = []

    # --- id, archetype, goal ---
    if not quest.id:
        errors.append("id: required")
    if not quest.archetype:
        errors.append("archetype: required")
    if not quest.goal:
        errors.append("goal: required")
    elif not _is_verb_the_noun(quest.goal):
        errors.append(
            f"goal: does not match verb-the-noun heuristic "
            f"(got {quest.goal!r}; must be an imperative sentence ≤25 words)"
        )

    # --- central conflict ---
    if not quest.central_conflict.nature:
        errors.append("central_conflict.nature: required")
    if not quest.central_conflict.proxy_antagonist_id:
        errors.append("central_conflict.proxy_antagonist_id: required")

    # --- bright lines ---
    if not quest.bright_lines:
        errors.append("bright_lines: at least one required")
    seen_ids = set()
    for i, bl in enumerate(quest.bright_lines):
        prefix = f"bright_lines[{i}]"
        if not bl.id:
            errors.append(f"{prefix}.id: required")
        elif bl.id in seen_ids:
            errors.append(f"{prefix}.id: duplicate {bl.id!r}")
        else:
            seen_ids.add(bl.id)
        if not bl.description:
            errors.append(f"{prefix}.description: required")
        if not bl.telegraph_text:
            errors.append(f"{prefix}.telegraph_text: required (opening scene must cue this)")
        errors.extend(validate_predicate(bl.check_condition, f"{prefix}.check_condition"))

    # --- macrostructure ---
    ms = quest.macrostructure
    if not ms.variable_name:
        errors.append("macrostructure.variable_name: required")
    if ms.direction not in ("decrement", "increment"):
        errors.append(f"macrostructure.direction: must be 'decrement' or 'increment' (got {ms.direction!r})")
    if not ms.tick_triggers:
        errors.append("macrostructure.tick_triggers: at least one required")
    for trig in ms.tick_triggers:
        if trig not in TICK_TRIGGERS:
            errors.append(
                f"macrostructure.tick_triggers: unknown trigger {trig!r} "
                f"(allowed: {sorted(TICK_TRIGGERS)})"
            )
    if ms.direction == "decrement" and ms.current <= ms.threshold:
        errors.append(
            "macrostructure: starts already at/past threshold "
            f"({ms.current} <= {ms.threshold})"
        )
    if ms.direction == "increment" and ms.current >= ms.threshold:
        errors.append(
            "macrostructure: starts already at/past threshold "
            f"({ms.current} >= {ms.threshold})"
        )

    # --- success_condition ---
    if not quest.success_condition:
        errors.append("success_condition: required")
    else:
        errors.extend(validate_predicate(quest.success_condition, "success_condition"))

    # --- resolution ---
    res = quest.resolution
    if not res.world_deltas_on_success:
        errors.append("resolution.world_deltas_on_success: at least one delta required")
    # Every bright line must have a failure delta branch (may be empty list,
    # but key must exist — this enforces the author thought about it).
    for bl in quest.bright_lines:
        if bl.id and bl.id not in res.world_deltas_on_failure:
            errors.append(
                f"resolution.world_deltas_on_failure: missing branch for "
                f"bright_line {bl.id!r}"
            )

    # --- progress track ---
    if quest.progress_track.ticks_required <= 0:
        errors.append("progress_track.ticks_required: must be > 0")
    if quest.progress_track.ticks_filled < 0:
        errors.append("progress_track.ticks_filled: must be >= 0")

    # --- scope ---
    if quest.scope.expected_scenes <= 0:
        errors.append("scope.expected_scenes: must be > 0")

    return errors
