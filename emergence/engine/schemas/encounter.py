"""Encounter engine schemas: EncounterSpec, CombatOutcome, Action, and supporting types."""

from dataclasses import dataclass, field, fields, asdict
from typing import Optional, List, Dict, Any, Type, TypeVar
from enum import Enum
import uuid

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class CombatRegister(str, Enum):
    HUMAN = "human"
    CREATURE = "creature"
    ELDRITCH = "eldritch"


class CombatResolution(str, Enum):
    VICTORY = "victory"
    DEFEAT = "defeat"
    PARLEY = "parley"
    ESCAPE = "escape"
    TRUCE = "truce"
    STALEMATE = "stalemate"
    OTHER = "other"


class CombatVerb(str, Enum):
    ATTACK = "Attack"
    POWER = "Power"
    ASSESS = "Assess"
    MANEUVER = "Maneuver"
    PARLEY = "Parley"
    DISENGAGE = "Disengage"
    FINISHER = "Finisher"
    DEFEND = "Defend"


class ConditionType(str, Enum):
    DEFEAT_ALL = "defeat_all"
    DEFEAT_SPECIFIC = "defeat_specific"
    SURVIVE_ROUNDS = "survive_rounds"
    REACH_ZONE = "reach_zone"
    CONVINCE_PARLEY = "convince_parley"
    BREAK_CONTACT = "break_contact"
    PROTECT_TARGET = "protect_target"


class EnemyFinalState(str, Enum):
    ALIVE = "alive"
    DEAD = "dead"
    FLED = "fled"
    SURRENDERED = "surrendered"
    INCAPACITATED = "incapacitated"
    TRANSFORMED = "transformed"


class ConsequenceType(str, Enum):
    FACTION_STANDING_CHANGE = "faction_standing_change"
    LOCATION_STATE_CHANGE = "location_state_change"
    NPC_MEMORY_UPDATE = "npc_memory_update"
    CLOCK_ADVANCE = "clock_advance"
    RUMOR_GENERATED = "rumor_generated"
    WITNESS_RECORDED = "witness_recorded"
    TERRITORY_CONTESTED = "territory_contested"


class ConsequenceScope(str, Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    GLOBAL = "global"


class ConsequenceVisibility(str, Enum):
    KNOWN = "known"
    RUMORED = "rumored"
    HIDDEN = "hidden"


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

    # Optional[X] is Union[X, None]
    if origin is type(None):
        return val
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
    if origin is type(None):
        return val
    # Python typing.Union
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
            # else: let default_factory / default handle it
        return cls(**kwargs)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TerrainZone(_DictMixin):
    """A zone within the encounter terrain."""
    id: str
    name: str
    properties: List[str]  # exposed, cover, hazardous, objective
    description: str


@dataclass
class WinLossCondition(_DictMixin):
    """A single win, loss, or escape condition."""
    type: str  # from ConditionType enum
    parameters: Dict = field(default_factory=dict)


@dataclass
class WorldContext(_DictMixin):
    """Broader world state fed into the encounter."""
    faction_situation: str = ""
    recent_events: List[str] = field(default_factory=list)
    heat_levels: Dict[str, int] = field(default_factory=dict)
    clock_states: Dict[str, int] = field(default_factory=dict)
    scene_clock: Optional[int] = None


@dataclass
class EncounterSpec(_DictMixin):
    """Full specification for generating and running an encounter."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    generated_at: str = ""
    location: str = ""
    player: Dict = field(default_factory=dict)  # Full CharacterSheet as dict
    enemies: List[Dict] = field(default_factory=list)  # List of Combatant dicts
    allies: List[Dict] = field(default_factory=list)
    terrain_zones: List[TerrainZone] = field(default_factory=list)
    stakes: str = ""
    win_conditions: List[WinLossCondition] = field(default_factory=list)
    loss_conditions: List[WinLossCondition] = field(default_factory=list)
    escape_conditions: List[WinLossCondition] = field(default_factory=list)
    parley_available: bool = False
    world_context: WorldContext = field(default_factory=WorldContext)
    combat_register: str = "human"
    opening_situation: str = ""


@dataclass
class Action(_DictMixin):
    """A single combat action declaration."""
    actor_id: str
    verb: str  # from CombatVerb
    target_id: Optional[str] = None
    power_id: Optional[str] = None
    target_zone: Optional[str] = None
    modifiers: Dict = field(default_factory=dict)
    declared_at_round: int = 0


@dataclass
class EnemyState(_DictMixin):
    """Post-combat state of an individual enemy."""
    enemy_id: str
    final_state: str  # from EnemyFinalState
    relevant_details: Dict = field(default_factory=dict)
    body_disposition: Optional[str] = None


@dataclass
class PlayerStateDelta(_DictMixin):
    """Changes to the player resulting from the encounter."""
    condition_changes: Dict[str, int] = field(default_factory=dict)
    harm_added: List[Dict] = field(default_factory=list)
    resources_spent: Dict[str, int] = field(default_factory=dict)
    heat_accrued: Dict[str, int] = field(default_factory=dict)
    corruption_gained: int = 0
    statuses_persisting: List[Dict] = field(default_factory=list)
    powers_used: Dict[str, int] = field(default_factory=dict)
    breakthrough_triggered: bool = False
    breakthrough_details: Optional[Dict] = None
    skill_usage: Dict[str, int] = field(default_factory=dict)
    injuries_healed: List[Dict] = field(default_factory=list)


@dataclass
class NarrativeLogEntry(_DictMixin):
    """A single entry in the combat narrative log."""
    turn: int
    actor_id: str
    action: Dict  # Action as dict
    payload: Dict
    narration: str = ""


@dataclass
class WorldConsequence(_DictMixin):
    """A consequence that ripples out into the broader world."""
    type: str  # from ConsequenceType
    parameters: Dict = field(default_factory=dict)
    scope: str = "local"
    visibility: str = "known"


@dataclass
class CombatOutcome(_DictMixin):
    """Complete result of a resolved encounter."""
    encounter_id: str
    schema_version: str = "1.0"
    resolution: str = "victory"  # from CombatResolution
    rounds_elapsed: int = 0
    player_state_delta: PlayerStateDelta = field(default_factory=PlayerStateDelta)
    enemy_states: List[EnemyState] = field(default_factory=list)
    narrative_log: List[NarrativeLogEntry] = field(default_factory=list)
    world_consequences: List[WorldConsequence] = field(default_factory=list)
