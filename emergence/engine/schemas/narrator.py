"""Narrator payload schema for the Emergence engine."""

from dataclasses import dataclass, field, fields
from typing import Optional, List, Dict, Any, Type, TypeVar
from enum import Enum

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SceneType(str, Enum):
    COMBAT_TURN = "combat_turn"
    SCENE_FRAMING = "scene_framing"
    SITUATION_DESCRIPTION = "situation_description"
    DIALOGUE = "dialogue"
    TRANSITION = "transition"
    CHARACTER_CREATION_BEAT = "character_creation_beat"
    TIME_SKIP = "time_skip"
    DEATH_NARRATION = "death_narration"


class RegisterDirective(str, Enum):
    STANDARD = "standard"
    ELDRITCH = "eldritch"
    INTIMATE = "intimate"
    ACTION = "action"
    QUIET = "quiet"


class OutputFormat(str, Enum):
    PROSE = "prose"
    DIALOGUE = "dialogue"
    MIXED = "mixed"
    TERSE = "terse"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_dataclass_instance(obj: Any) -> bool:
    return hasattr(type(obj), "__dataclass_fields__")


def _is_dataclass_type(cls: Any) -> bool:
    return hasattr(cls, "__dataclass_fields__")


def _to_dict_value(val: Any) -> Any:
    """Recursively convert a value for serialisation."""
    if _is_dataclass_instance(val):
        return val.to_dict()
    if isinstance(val, list):
        return [_to_dict_value(v) for v in val]
    if isinstance(val, dict):
        return {k: _to_dict_value(v) for k, v in val.items()}
    if isinstance(val, Enum):
        return val.value
    return val


def _from_dict_value(val: Any, field_type: Any) -> Any:
    """Recursively reconstruct a value from a plain dict/list."""
    origin = getattr(field_type, "__origin__", None)
    args = getattr(field_type, "__args__", ())

    if origin is list or origin is List:
        inner = args[0] if args else Any
        if isinstance(val, list):
            return [_from_dict_value(v, inner) for v in val]
        return val
    if origin is dict or origin is Dict:
        k_type = args[0] if args else Any
        v_type = args[1] if len(args) > 1 else Any
        if isinstance(val, dict):
            return {_from_dict_value(k, k_type): _from_dict_value(v, v_type) for k, v in val.items()}
        return val

    # Handle Optional (Union with None)
    import typing
    if origin is getattr(typing, "Union", None):
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1:
            if val is None:
                return None
            return _from_dict_value(val, non_none[0])
        return val

    # Concrete dataclass type
    if _is_dataclass_type(field_type) and isinstance(val, dict):
        return field_type.from_dict(val)

    return val


def _get_type_hints(cls: type) -> Dict[str, Any]:
    """Return resolved type hints for *cls*, falling back gracefully."""
    import typing
    try:
        return typing.get_type_hints(cls)
    except Exception:
        return {f.name: f.type for f in fields(cls)}


class _DictMixin:
    """Mixin providing to_dict / from_dict on any dataclass."""

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for f in fields(self):  # type: ignore[arg-type]
            result[f.name] = _to_dict_value(getattr(self, f.name))
        return result

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        hints = _get_type_hints(cls)
        kwargs: Dict[str, Any] = {}
        for f in fields(cls):  # type: ignore[arg-type]
            if f.name in data:
                kwargs[f.name] = _from_dict_value(data[f.name], hints.get(f.name, Any))
        return cls(**kwargs)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class OutputTarget(_DictMixin):
    """Desired output shape for the narrator."""
    desired_length: Dict[str, int] = field(default_factory=lambda: {"min_words": 80, "max_words": 180})
    format: str = "prose"


@dataclass
class ContextContinuity(_DictMixin):
    """Continuity context carried between narration calls."""
    last_narration_summary: str = ""
    scene_history_summary: str = ""
    key_callbacks: List[str] = field(default_factory=list)


@dataclass
class NarratorConstraints(_DictMixin):
    """Hard constraints the narrator must respect."""
    forbidden: List[str] = field(default_factory=list)


@dataclass
class NarratorPayload(_DictMixin):
    """Complete payload sent to the narrator for a single narration beat."""
    schema_version: str = "1.0"
    scene_type: str = "scene_framing"
    state_snapshot: Dict = field(default_factory=dict)
    register_directive: str = "standard"
    output_target: OutputTarget = field(default_factory=lambda: OutputTarget(desired_length={"min_words": 80, "max_words": 180}))
    constraints: NarratorConstraints = field(default_factory=NarratorConstraints)
    context_continuity: ContextContinuity = field(default_factory=ContextContinuity)
