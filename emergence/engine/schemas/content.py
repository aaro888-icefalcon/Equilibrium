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
# Power V2 — Rev 4 schema (8 mode slots)
# ---------------------------------------------------------------------------

@dataclass
class CastMode:
    """A single cast mode within a PowerV2 (3 per power, plus capstones)."""

    slot_id: str = ""
    action_cost: str = "major"  # major or minor
    pool_cost: int = 1
    additional_cost: Dict[str, Any] = field(default_factory=dict)  # condition, corruption, heat, scene_use
    effect_families: List[str] = field(default_factory=list)  # from EffectFamily enum
    targeting_scope: str = "enemy_single"  # self, ally, touched, enemy_single, enemy_group, zone, all_visible
    range_band: str = "close"  # touch, close, medium, far, extreme
    duration: str = "instant"  # instant, 1_round, 2_3_rounds, scene, persistent
    effect_description: str = ""
    effect_parameters: Dict[str, Any] = field(default_factory=dict)
    posture_sensitive: bool = False
    playstyles: List[str] = field(default_factory=list)
    hook: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CastMode":
        return cls(**{k: data[k] for k in data if k in {f.name for f in cls.__dataclass_fields__.values()}})


@dataclass
class RiderSpec:
    """A rider slot within a PowerV2 (3 per power)."""

    slot_id: str = ""
    rider_type: str = "strike"  # from RiderType enum
    sub_category: str = ""  # for posture riders: reactive_defense, reactive_offense, etc.
    pool_cost: int = 0  # 0 for posture riders (passive)
    restrictions: Dict[str, Any] = field(default_factory=dict)
    compatible_postures: List[str] = field(default_factory=list)
    effect_description: str = ""
    effect_parameters: Dict[str, Any] = field(default_factory=dict)
    playstyles: List[str] = field(default_factory=list)
    combo_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiderSpec":
        return cls(**{k: data[k] for k in data if k in {f.name for f in cls.__dataclass_fields__.values()}})


@dataclass
class CapstoneOption:
    """A capstone option within a PowerV2 (2 per power, player picks 1)."""

    name: str = ""
    pool_cost: int = 3
    additional_cost: Dict[str, Any] = field(default_factory=dict)
    targeting_scope: str = "enemy_single"
    range_band: str = "close"
    duration: str = "scene"
    effect_description: str = ""
    effect_parameters: Dict[str, Any] = field(default_factory=dict)
    effect_families: List[str] = field(default_factory=list)
    signal: str = ""  # <=8 word character-voice framing
    viability: str = ""
    playstyles: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapstoneOption":
        return cls(**{k: data[k] for k in data if k in {f.name for f in cls.__dataclass_fields__.values()}})


@dataclass
class EnhancedRiderOption:
    """An enhanced rider option within a PowerV2 (3 per power, player picks 1)."""

    variant_name: str = ""
    base_rider_slot: str = ""  # which rider slot this enhances
    enhancement_type: str = ""
    pool_cost: int = 0
    shift: str = ""
    effect_description: str = ""
    effect_parameters: Dict[str, Any] = field(default_factory=dict)
    combo_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EnhancedRiderOption":
        return cls(**{k: data[k] for k in data if k in {f.name for f in cls.__dataclass_fields__.values()}})


@dataclass
class PowerV2:
    """A Rev 4 power with 8 mode slots."""

    id: str = ""
    schema_version: str = "2.0"
    name: str = ""
    category: str = ""  # 6-broad: somatic, cognitive, material, kinetic, spatial, paradoxic
    sub_category: str = ""  # e.g., vitality, telepathic, elemental, impact, translative, temporal
    pair_role: str = ""  # Primary, Complement, Flex
    register_gating: List[str] = field(default_factory=lambda: ["human", "creature", "eldritch"])
    playstyles: List[str] = field(default_factory=list)
    identity: str = ""
    description: str = ""
    tier: int = 1

    # 3 cast modes
    cast_modes: List[CastMode] = field(default_factory=lambda: [CastMode(), CastMode(), CastMode()])
    # 2 capstone options (player picks 1 at unlock)
    capstone_options: List[CapstoneOption] = field(default_factory=lambda: [CapstoneOption(), CapstoneOption()])
    # 3 rider slots
    rider_slots: List[RiderSpec] = field(default_factory=lambda: [RiderSpec(), RiderSpec(), RiderSpec()])
    # 3 enhanced rider options (player picks 1 at unlock)
    enhanced_rider_options: List[EnhancedRiderOption] = field(
        default_factory=lambda: [EnhancedRiderOption(), EnhancedRiderOption(), EnhancedRiderOption()]
    )

    prerequisite: Optional[str] = None
    usage_scope: str = "both"  # combat, sim, both
    visibility: str = "visible"  # visible, subtle, variable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "name": self.name,
            "category": self.category,
            "sub_category": self.sub_category,
            "pair_role": self.pair_role,
            "register_gating": list(self.register_gating),
            "playstyles": list(self.playstyles),
            "identity": self.identity,
            "description": self.description,
            "tier": self.tier,
            "cast_modes": [c.to_dict() for c in self.cast_modes],
            "capstone_options": [c.to_dict() for c in self.capstone_options],
            "rider_slots": [r.to_dict() for r in self.rider_slots],
            "enhanced_rider_options": [e.to_dict() for e in self.enhanced_rider_options],
            "prerequisite": self.prerequisite,
            "usage_scope": self.usage_scope,
            "visibility": self.visibility,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PowerV2":
        return cls(
            id=data.get("id", ""),
            schema_version=data.get("schema_version", "2.0"),
            name=data.get("name", ""),
            category=data.get("category", ""),
            sub_category=data.get("sub_category", ""),
            pair_role=data.get("pair_role", ""),
            register_gating=data.get("register_gating", ["human", "creature", "eldritch"]),
            playstyles=data.get("playstyles", []),
            identity=data.get("identity", ""),
            description=data.get("description", ""),
            tier=data.get("tier", 1),
            cast_modes=[CastMode.from_dict(c) for c in data.get("cast_modes", [{}, {}, {}])],
            capstone_options=[CapstoneOption.from_dict(c) for c in data.get("capstone_options", [{}, {}])],
            rider_slots=[RiderSpec.from_dict(r) for r in data.get("rider_slots", [{}, {}, {}])],
            enhanced_rider_options=[
                EnhancedRiderOption.from_dict(e) for e in data.get("enhanced_rider_options", [{}, {}, {}])
            ],
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
    tier: int = 1
    condition_track_max: Dict[str, int] = field(
        default_factory=lambda: {"physical": 5, "mental": 5, "social": 5}
    )
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
            "tier": self.tier,
            "attribute_defaults": dict(self.attribute_defaults),
            "condition_track_defaults": dict(self.condition_track_defaults),
            "condition_track_max": dict(self.condition_track_max),
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
            tier=data.get("tier", 1),
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
            condition_track_max=data.get(
                "condition_track_max",
                {"physical": 5, "mental": 5, "social": 5},
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
