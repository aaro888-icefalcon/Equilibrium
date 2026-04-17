"""Character Sheet schema for the Emergence game engine.

Defines all dataclasses needed to represent a full player or NPC character,
including attributes, harm, powers, relationships, inventory, and history.
Uses only the Python standard library.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Species(str, Enum):
    HUMAN = "human"
    EMERGENT = "emergent"
    CHIMERA = "chimera"
    REVENANT = "revenant"
    PARAGON = "paragon"
    ABERRANT = "aberrant"


class PowerCategory(str, Enum):
    SOMATIC = "somatic"
    COGNITIVE = "cognitive"
    MATERIAL = "material"
    KINETIC = "kinetic"
    SPATIAL = "spatial"
    PARADOXIC = "paradoxic"


class ConditionTrack(str, Enum):
    PHYSICAL = "physical"
    MENTAL = "mental"
    SOCIAL = "social"


# ---------------------------------------------------------------------------
# Supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Attributes:
    """Core attributes expressed as die sizes (4, 6, 8, 10, or 12)."""

    strength: int = 6
    agility: int = 6
    perception: int = 6
    will: int = 6
    insight: int = 6
    might: int = 6

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Attributes":
        return cls(
            strength=data.get("strength", 6),
            agility=data.get("agility", 6),
            perception=data.get("perception", 6),
            will=data.get("will", 6),
            insight=data.get("insight", 6),
            might=data.get("might", 6),
        )


@dataclass
class Harm:
    """A single harm entry on a character's condition monitor."""

    tier: int  # 1=scene, 2=persistent, 3=permanent/fatal
    description: str
    persistent: bool
    source: str
    date_acquired: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Harm":
        return cls(
            tier=data["tier"],
            description=data["description"],
            persistent=data["persistent"],
            source=data["source"],
            date_acquired=data["date_acquired"],
        )


@dataclass
class Breakthrough:
    """Records a tier advancement event."""

    date: str
    from_tier: int
    to_tier: int
    cost: str
    trigger: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Breakthrough":
        return cls(
            date=data["date"],
            from_tier=data["from_tier"],
            to_tier=data["to_tier"],
            cost=data["cost"],
            trigger=data["trigger"],
        )


@dataclass
class RelationshipState:
    """Tracks a relationship with another character or faction."""

    standing: int = 0  # -3 to +3
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_state: str = "neutral"
    trust: int = 0  # 0 to 5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipState":
        return cls(
            standing=data.get("standing", 0),
            history=data.get("history", []),
            current_state=data.get("current_state", "neutral"),
            trust=data.get("trust", 0),
        )


@dataclass
class InventoryItem:
    """A single item carried by the character."""

    id: str
    name: str
    description: str
    quantity: int = 1
    mechanical_effect: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InventoryItem":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            quantity=data.get("quantity", 1),
            mechanical_effect=data.get("mechanical_effect"),
        )


@dataclass
class Goal:
    """An active character goal with progress and pressure meters."""

    id: str
    description: str
    progress: int = 0  # 0-10
    pressure: int = 0  # 0-5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        return cls(
            id=data["id"],
            description=data["description"],
            progress=data.get("progress", 0),
            pressure=data.get("pressure", 0),
        )


@dataclass
class StatusEffect:
    """An active status condition on the character.

    Valid names: bleeding, stunned, shaken, burning, exposed, marked, corrupted.
    """

    name: str
    duration: int  # remaining duration in rounds/scenes
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusEffect":
        return cls(
            name=data["name"],
            duration=data["duration"],
            source=data["source"],
        )


@dataclass
class HistoryEvent:
    """A narrative event recorded in the character's history."""

    date: str
    category: str  # combat, political, personal, discovery
    description: str
    consequences: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEvent":
        return cls(
            date=data["date"],
            category=data["category"],
            description=data["description"],
            consequences=data.get("consequences", []),
        )


# ---------------------------------------------------------------------------
# Main CharacterSheet
# ---------------------------------------------------------------------------

@dataclass
class CharacterSheet:
    """Full character sheet for a player character or NPC."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    name: str = ""
    species: str = "human"
    age_at_onset: int = 25
    current_age: int = 26

    # Core mechanics
    attributes: Attributes = field(default_factory=Attributes)
    condition_tracks: Dict[str, int] = field(
        default_factory=lambda: {"physical": 0, "mental": 0, "social": 0}
    )
    harm: List[Harm] = field(default_factory=list)

    # Powers
    powers: List[str] = field(default_factory=list)
    power_category_primary: str = ""
    power_category_secondary: Optional[str] = None

    # Tier / advancement
    tier: int = 1  # 1-10
    tier_ceiling: int = 3  # 1-10
    breakthroughs: List[Breakthrough] = field(default_factory=list)

    # Heat and corruption
    heat: Dict[str, int] = field(default_factory=dict)
    corruption: int = 0  # 0-6

    # Social
    relationships: Dict[str, RelationshipState] = field(default_factory=dict)

    # Inventory / location
    inventory: List[InventoryItem] = field(default_factory=list)
    location: str = ""

    # Narrative
    history: List[HistoryEvent] = field(default_factory=list)
    statuses: List[StatusEffect] = field(default_factory=list)

    # Skills, resources, goals
    skills: Dict[str, int] = field(default_factory=dict)
    resources: Dict[str, int] = field(default_factory=dict)
    goals: List[Goal] = field(default_factory=list)

    # Session zero
    session_zero_choices: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "name": self.name,
            "species": self.species,
            "age_at_onset": self.age_at_onset,
            "current_age": self.current_age,
            "attributes": self.attributes.to_dict(),
            "condition_tracks": dict(self.condition_tracks),
            "harm": [h.to_dict() for h in self.harm],
            "powers": list(self.powers),
            "power_category_primary": self.power_category_primary,
            "power_category_secondary": self.power_category_secondary,
            "tier": self.tier,
            "tier_ceiling": self.tier_ceiling,
            "breakthroughs": [b.to_dict() for b in self.breakthroughs],
            "heat": dict(self.heat),
            "corruption": self.corruption,
            "relationships": {
                k: v.to_dict() for k, v in self.relationships.items()
            },
            "inventory": [i.to_dict() for i in self.inventory],
            "location": self.location,
            "history": [h.to_dict() for h in self.history],
            "statuses": [s.to_dict() for s in self.statuses],
            "skills": dict(self.skills),
            "resources": dict(self.resources),
            "goals": [g.to_dict() for g in self.goals],
            "session_zero_choices": dict(self.session_zero_choices),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterSheet":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            schema_version=data.get("schema_version", "1.0"),
            name=data.get("name", ""),
            species=data.get("species", "human"),
            age_at_onset=data.get("age_at_onset", 25),
            current_age=data.get("current_age", 26),
            attributes=Attributes.from_dict(data["attributes"])
            if "attributes" in data
            else Attributes(),
            condition_tracks=data.get(
                "condition_tracks",
                {"physical": 0, "mental": 0, "social": 0},
            ),
            harm=[Harm.from_dict(h) for h in data.get("harm", [])],
            powers=data.get("powers", []),
            power_category_primary=data.get("power_category_primary", ""),
            power_category_secondary=data.get("power_category_secondary"),
            tier=data.get("tier", 1),
            tier_ceiling=data.get("tier_ceiling", 3),
            breakthroughs=[
                Breakthrough.from_dict(b) for b in data.get("breakthroughs", [])
            ],
            heat=data.get("heat", {}),
            corruption=data.get("corruption", 0),
            relationships={
                k: RelationshipState.from_dict(v)
                for k, v in data.get("relationships", {}).items()
            },
            inventory=[
                InventoryItem.from_dict(i) for i in data.get("inventory", [])
            ],
            location=data.get("location", ""),
            history=[
                HistoryEvent.from_dict(h) for h in data.get("history", [])
            ],
            statuses=[
                StatusEffect.from_dict(s) for s in data.get("statuses", [])
            ],
            skills=data.get("skills", {}),
            resources=data.get("resources", {}),
            goals=[Goal.from_dict(g) for g in data.get("goals", [])],
            session_zero_choices=data.get("session_zero_choices", {}),
        )
