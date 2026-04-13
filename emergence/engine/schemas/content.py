"""Content schemas for the Emergence game engine.

Defines dataclasses for powers, enemy templates, and related game content
that populate the world.  Uses only the Python standard library.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


# ---------------------------------------------------------------------------
# Power supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class PowerCost:
    """Resource cost incurred when a power is used."""

    condition: Dict[str, int] = field(default_factory=dict)  # track -> damage
    heat: Dict[str, int] = field(default_factory=dict)  # faction -> heat
    corruption: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PowerCost":
        return cls(
            condition=data.get("condition", {}),
            heat=data.get("heat", {}),
            corruption=data.get("corruption", 0),
        )


@dataclass
class PowerEffect:
    """Mechanical effect produced by a power."""

    type: str  # damage, status, utility, movement, combined
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PowerEffect":
        return cls(
            type=data["type"],
            parameters=data.get("parameters", {}),
        )


# ---------------------------------------------------------------------------
# Power
# ---------------------------------------------------------------------------

@dataclass
class Power:
    """A manifestation power available to characters."""

    id: str
    schema_version: str = "1.0"
    name: str = ""
    category: str = ""  # power category
    tier: int = 1  # minimum tier to manifest
    cost: PowerCost = field(default_factory=PowerCost)
    effect: PowerEffect = field(default_factory=lambda: PowerEffect(type="damage"))
    damage_type: str = ""  # matches power category
    description: str = ""
    prerequisite: Optional[str] = None
    usage_scope: str = "both"  # combat, sim, both
    visibility: str = "visible"  # visible, subtle, variable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "name": self.name,
            "category": self.category,
            "tier": self.tier,
            "cost": self.cost.to_dict(),
            "effect": self.effect.to_dict(),
            "damage_type": self.damage_type,
            "description": self.description,
            "prerequisite": self.prerequisite,
            "usage_scope": self.usage_scope,
            "visibility": self.visibility,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Power":
        return cls(
            id=data["id"],
            schema_version=data.get("schema_version", "1.0"),
            name=data.get("name", ""),
            category=data.get("category", ""),
            tier=data.get("tier", 1),
            cost=PowerCost.from_dict(data["cost"])
            if "cost" in data
            else PowerCost(),
            effect=PowerEffect.from_dict(data["effect"])
            if "effect" in data
            else PowerEffect(type="damage"),
            damage_type=data.get("damage_type", ""),
            description=data.get("description", ""),
            prerequisite=data.get("prerequisite"),
            usage_scope=data.get("usage_scope", "both"),
            visibility=data.get("visibility", "visible"),
        )


# ---------------------------------------------------------------------------
# Enemy Template
# ---------------------------------------------------------------------------

@dataclass
class EnemyTemplate:
    """A reusable template for generating enemy combatants."""

    id: str
    schema_version: str = "1.0"
    display_name: str = ""
    register: str = "human"  # human, creature, eldritch
    attribute_defaults: Dict[str, int] = field(
        default_factory=lambda: {
            "strength": 6,
            "agility": 6,
            "perception": 6,
            "will": 6,
            "insight": 6,
            "might": 6,
        }
    )
    condition_track_defaults: Dict[str, int] = field(
        default_factory=lambda: {"physical": 0, "mental": 0, "social": 0}
    )
    affinity_table: Dict[str, str] = field(default_factory=dict)
    ai_profile: str = "aggressive"
    exposure_max: int = 6
    abilities: List[str] = field(default_factory=list)
    powers: List[str] = field(default_factory=list)
    retreat_conditions: List[str] = field(default_factory=list)
    parley_conditions: List[str] = field(default_factory=list)
    description: str = ""
    tactics_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "display_name": self.display_name,
            "register": self.register,
            "attribute_defaults": dict(self.attribute_defaults),
            "condition_track_defaults": dict(self.condition_track_defaults),
            "affinity_table": dict(self.affinity_table),
            "ai_profile": self.ai_profile,
            "exposure_max": self.exposure_max,
            "abilities": list(self.abilities),
            "powers": list(self.powers),
            "retreat_conditions": list(self.retreat_conditions),
            "parley_conditions": list(self.parley_conditions),
            "description": self.description,
            "tactics_note": self.tactics_note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnemyTemplate":
        return cls(
            id=data["id"],
            schema_version=data.get("schema_version", "1.0"),
            display_name=data.get("display_name", ""),
            register=data.get("register", "human"),
            attribute_defaults=data.get(
                "attribute_defaults",
                {
                    "strength": 6,
                    "agility": 6,
                    "perception": 6,
                    "will": 6,
                    "insight": 6,
                    "might": 6,
                },
            ),
            condition_track_defaults=data.get(
                "condition_track_defaults",
                {"physical": 0, "mental": 0, "social": 0},
            ),
            affinity_table=data.get("affinity_table", {}),
            ai_profile=data.get("ai_profile", "aggressive"),
            exposure_max=data.get("exposure_max", 6),
            abilities=data.get("abilities", []),
            powers=data.get("powers", []),
            retreat_conditions=data.get("retreat_conditions", []),
            parley_conditions=data.get("parley_conditions", []),
            description=data.get("description", ""),
            tactics_note=data.get("tactics_note", ""),
        )
