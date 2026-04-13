"""World State schemas for the Emergence game engine.

Defines all dataclasses needed to represent the living world: factions, NPCs,
locations, clocks, tick events, situations, and the top-level world state.
Uses only the Python standard library.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FactionType(str, Enum):
    NOBLE_HOUSE = "noble_house"
    WARLORD_HOLDING = "warlord_holding"
    MERCHANT_GUILD = "merchant_guild"
    RELIGIOUS_ORDER = "religious_order"
    METAHUMAN_POLITY = "metahuman_polity"
    SURVIVOR_COMMUNE = "survivor_commune"


class LocationType(str, Enum):
    CITY = "city"
    TOWN = "town"
    FORTRESS = "fortress"
    RUIN = "ruin"
    WILDERNESS_ZONE = "wilderness_zone"
    FACTION_HOLDING = "faction_holding"
    NATURAL_FEATURE = "natural_feature"
    CHARGED_ZONE = "charged_zone"


class EconomicState(str, Enum):
    THRIVING = "thriving"
    SUFFICIENT = "sufficient"
    STRAINED = "strained"
    FAILING = "failing"
    ABANDONED = "abandoned"


class NpcStatus(str, Enum):
    ALIVE = "alive"
    DEAD = "dead"
    MISSING = "missing"
    TRANSFORMED = "transformed"
    DISPLACED = "displaced"


class TickVisibility(str, Enum):
    WORLD = "world"
    REGIONAL = "regional"
    LOCAL = "local"
    HIDDEN = "hidden"


class ChoiceType(str, Enum):
    DIALOGUE = "dialogue"
    ACTION = "action"
    OBSERVATION = "observation"
    TRAVEL = "travel"
    ACTIVITY = "activity"


# ---------------------------------------------------------------------------
# Faction supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class FactionTerritory:
    """Geographic holdings of a faction."""

    primary_region: str = ""
    secondary_holdings: List[str] = field(default_factory=list)
    contested_zones: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionTerritory":
        return cls(
            primary_region=data.get("primary_region", ""),
            secondary_holdings=data.get("secondary_holdings", []),
            contested_zones=data.get("contested_zones", []),
        )


@dataclass
class FactionPopulation:
    """Demographics of a faction."""

    total: int = 0
    military_capacity: int = 0
    powered_fraction: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionPopulation":
        return cls(
            total=data.get("total", 0),
            military_capacity=data.get("military_capacity", 0),
            powered_fraction=data.get("powered_fraction", 0.0),
        )


@dataclass
class FactionPowerProfile:
    """Power distribution profile within a faction."""

    dominant_categories: List[str] = field(default_factory=list)
    typical_tier_range: List[int] = field(default_factory=lambda: [1, 3])
    standout_individuals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionPowerProfile":
        return cls(
            dominant_categories=data.get("dominant_categories", []),
            typical_tier_range=data.get("typical_tier_range", [1, 3]),
            standout_individuals=data.get("standout_individuals", []),
        )


@dataclass
class FactionEconomicBase:
    """Economic foundations of a faction."""

    primary_resources: List[str] = field(default_factory=list)
    trade_relationships: List[Dict[str, Any]] = field(default_factory=list)
    currency_dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionEconomicBase":
        return cls(
            primary_resources=data.get("primary_resources", []),
            trade_relationships=data.get("trade_relationships", []),
            currency_dependencies=data.get("currency_dependencies", []),
        )


@dataclass
class FactionGoal:
    """A strategic goal pursued by a faction."""

    id: str
    description: str
    weight: float = 1.0
    progress: int = 0  # 0-10

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionGoal":
        return cls(
            id=data["id"],
            description=data["description"],
            weight=data.get("weight", 1.0),
            progress=data.get("progress", 0),
        )


@dataclass
class FactionScheme:
    """An active scheme or plot being executed by a faction."""

    id: str
    description: str
    target: str
    progress: int = 0
    expected_completion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionScheme":
        return cls(
            id=data["id"],
            description=data["description"],
            target=data["target"],
            progress=data.get("progress", 0),
            expected_completion=data.get("expected_completion", ""),
        )


@dataclass
class FactionRelationship:
    """A faction's relationship with another faction."""

    disposition: int = 0  # -3 to +3
    history: List[Dict[str, Any]] = field(default_factory=list)
    active_agreements: List[str] = field(default_factory=list)
    active_grievances: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactionRelationship":
        return cls(
            disposition=data.get("disposition", 0),
            history=data.get("history", []),
            active_agreements=data.get("active_agreements", []),
            active_grievances=data.get("active_grievances", []),
        )


# ---------------------------------------------------------------------------
# Faction
# ---------------------------------------------------------------------------

@dataclass
class Faction:
    """A major faction in the world."""

    id: str = ""
    schema_version: str = "1.0"
    display_name: str = ""
    type: str = "survivor_commune"
    current_leader: Dict[str, Any] = field(default_factory=dict)
    territory: FactionTerritory = field(default_factory=FactionTerritory)
    population: FactionPopulation = field(default_factory=FactionPopulation)
    power_profile: FactionPowerProfile = field(default_factory=FactionPowerProfile)
    economic_base: FactionEconomicBase = field(default_factory=FactionEconomicBase)
    goals: List[FactionGoal] = field(default_factory=list)
    current_schemes: List[FactionScheme] = field(default_factory=list)
    internal_tensions: List[Dict[str, Any]] = field(default_factory=list)
    external_relationships: Dict[str, FactionRelationship] = field(
        default_factory=dict
    )  # faction_id -> relationship
    standing_with_player_default: int = 0  # -3 to +3
    known_information: List[str] = field(default_factory=list)
    secret_information: List[str] = field(default_factory=list)
    narrative_voice: str = ""
    last_tick_actions: List[Dict[str, Any]] = field(default_factory=list)
    resources: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "display_name": self.display_name,
            "type": self.type,
            "current_leader": dict(self.current_leader),
            "territory": self.territory.to_dict(),
            "population": self.population.to_dict(),
            "power_profile": self.power_profile.to_dict(),
            "economic_base": self.economic_base.to_dict(),
            "goals": [g.to_dict() for g in self.goals],
            "current_schemes": [s.to_dict() for s in self.current_schemes],
            "internal_tensions": list(self.internal_tensions),
            "external_relationships": {
                k: v.to_dict() for k, v in self.external_relationships.items()
            },
            "standing_with_player_default": self.standing_with_player_default,
            "known_information": list(self.known_information),
            "secret_information": list(self.secret_information),
            "narrative_voice": self.narrative_voice,
            "last_tick_actions": list(self.last_tick_actions),
            "resources": dict(self.resources),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Faction":
        return cls(
            id=data.get("id", ""),
            schema_version=data.get("schema_version", "1.0"),
            display_name=data.get("display_name", ""),
            type=data.get("type", "survivor_commune"),
            current_leader=data.get("current_leader", {}),
            territory=FactionTerritory.from_dict(data["territory"])
            if "territory" in data
            else FactionTerritory(),
            population=FactionPopulation.from_dict(data["population"])
            if "population" in data
            else FactionPopulation(),
            power_profile=FactionPowerProfile.from_dict(data["power_profile"])
            if "power_profile" in data
            else FactionPowerProfile(),
            economic_base=FactionEconomicBase.from_dict(data["economic_base"])
            if "economic_base" in data
            else FactionEconomicBase(),
            goals=[
                FactionGoal.from_dict(g) for g in data.get("goals", [])
            ],
            current_schemes=[
                FactionScheme.from_dict(s)
                for s in data.get("current_schemes", [])
            ],
            internal_tensions=data.get("internal_tensions", []),
            external_relationships={
                k: FactionRelationship.from_dict(v)
                for k, v in data.get("external_relationships", {}).items()
            },
            standing_with_player_default=data.get(
                "standing_with_player_default", 0
            ),
            known_information=data.get("known_information", []),
            secret_information=data.get("secret_information", []),
            narrative_voice=data.get("narrative_voice", ""),
            last_tick_actions=data.get("last_tick_actions", []),
            resources=data.get("resources", {}),
        )


# ---------------------------------------------------------------------------
# NPC supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NpcManifest:
    """Power manifestation details for an NPC."""

    category: str = ""
    tier: int = 1
    specific_abilities: List[str] = field(default_factory=list)
    circumstance_of_manifestation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NpcManifest":
        return cls(
            category=data.get("category", ""),
            tier=data.get("tier", 1),
            specific_abilities=data.get("specific_abilities", []),
            circumstance_of_manifestation=data.get(
                "circumstance_of_manifestation", ""
            ),
        )


@dataclass
class NpcKnowledge:
    """A piece of knowledge held by an NPC."""

    topic: str
    detail: str
    will_share_if: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NpcKnowledge":
        return cls(
            topic=data["topic"],
            detail=data["detail"],
            will_share_if=data.get("will_share_if", []),
        )


@dataclass
class NpcMemory:
    """A memory that may decay over time."""

    date: str
    event: str
    emotional_weight: int = 5  # 0-10
    decay_rate: float = 0.1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NpcMemory":
        return cls(
            date=data["date"],
            event=data["event"],
            emotional_weight=data.get("emotional_weight", 5),
            decay_rate=data.get("decay_rate", 0.1),
        )


@dataclass
class NpcRelationshipState:
    """Tracks an NPC's relationship with another entity."""

    standing: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    current_state: str = "neutral"
    trust: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NpcRelationshipState":
        return cls(
            standing=data.get("standing", 0),
            history=data.get("history", []),
            current_state=data.get("current_state", "neutral"),
            trust=data.get("trust", 0),
        )


# ---------------------------------------------------------------------------
# NPC
# ---------------------------------------------------------------------------

@dataclass
class NPC:
    """A non-player character in the world."""

    id: str = ""
    schema_version: str = "1.0"
    display_name: str = ""
    faction_affiliation: Dict[str, Any] = field(
        default_factory=lambda: {"primary": None, "secondary": []}
    )
    location: str = ""
    schedule: Dict[str, Any] = field(default_factory=dict)
    species: str = "human"
    age: int = 30
    manifestation: NpcManifest = field(default_factory=NpcManifest)
    role: str = ""
    goals: List[Dict[str, Any]] = field(default_factory=list)
    relationships: Dict[str, NpcRelationshipState] = field(default_factory=dict)
    resources: List[Dict[str, Any]] = field(default_factory=list)
    knowledge: List[NpcKnowledge] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    current_concerns: List[str] = field(default_factory=list)
    memory: List[NpcMemory] = field(default_factory=list)
    standing_with_player_default: int = 0
    what_they_want_from_player: str = ""
    voice: str = ""
    hooks: List[str] = field(default_factory=list)
    status: str = "alive"  # alive, dead, missing, transformed, displaced

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "display_name": self.display_name,
            "faction_affiliation": dict(self.faction_affiliation),
            "location": self.location,
            "schedule": dict(self.schedule),
            "species": self.species,
            "age": self.age,
            "manifestation": self.manifestation.to_dict(),
            "role": self.role,
            "goals": list(self.goals),
            "relationships": {
                k: v.to_dict() for k, v in self.relationships.items()
            },
            "resources": list(self.resources),
            "knowledge": [k.to_dict() for k in self.knowledge],
            "personality_traits": list(self.personality_traits),
            "current_concerns": list(self.current_concerns),
            "memory": [m.to_dict() for m in self.memory],
            "standing_with_player_default": self.standing_with_player_default,
            "what_they_want_from_player": self.what_they_want_from_player,
            "voice": self.voice,
            "hooks": list(self.hooks),
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        return cls(
            id=data.get("id", ""),
            schema_version=data.get("schema_version", "1.0"),
            display_name=data.get("display_name", ""),
            faction_affiliation=data.get(
                "faction_affiliation", {"primary": None, "secondary": []}
            ),
            location=data.get("location", ""),
            schedule=data.get("schedule", {}),
            species=data.get("species", "human"),
            age=data.get("age", 30),
            manifestation=NpcManifest.from_dict(data["manifestation"])
            if "manifestation" in data
            else NpcManifest(),
            role=data.get("role", ""),
            goals=data.get("goals", []),
            relationships={
                k: NpcRelationshipState.from_dict(v)
                for k, v in data.get("relationships", {}).items()
            },
            resources=data.get("resources", []),
            knowledge=[
                NpcKnowledge.from_dict(k) for k in data.get("knowledge", [])
            ],
            personality_traits=data.get("personality_traits", []),
            current_concerns=data.get("current_concerns", []),
            memory=[
                NpcMemory.from_dict(m) for m in data.get("memory", [])
            ],
            standing_with_player_default=data.get(
                "standing_with_player_default", 0
            ),
            what_they_want_from_player=data.get(
                "what_they_want_from_player", ""
            ),
            voice=data.get("voice", ""),
            hooks=data.get("hooks", []),
            status=data.get("status", "alive"),
        )


# ---------------------------------------------------------------------------
# Location supporting dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LocationConnection:
    """A connection from one location to another."""

    to_location_id: str
    travel_mode: str = "foot"
    travel_time: str = ""
    hazards: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LocationConnection":
        return cls(
            to_location_id=data["to_location_id"],
            travel_mode=data.get("travel_mode", "foot"),
            travel_time=data.get("travel_time", ""),
            hazards=data.get("hazards", []),
        )


@dataclass
class AmbientConditions:
    """Environmental conditions at a location."""

    weather: str = "clear"
    time_of_day: str = "morning"
    season: str = "spring"
    threat_level: int = 0  # 0-5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AmbientConditions":
        return cls(
            weather=data.get("weather", "clear"),
            time_of_day=data.get("time_of_day", "morning"),
            season=data.get("season", "spring"),
            threat_level=data.get("threat_level", 0),
        )


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

@dataclass
class Location:
    """A named place in the world."""

    id: str = ""
    schema_version: str = "1.0"
    display_name: str = ""
    type: str = "town"
    region: str = ""
    coordinates: Dict[str, Any] = field(default_factory=dict)
    controller: Optional[str] = None  # faction_id, "contested", "unclaimed"
    population: int = 0
    defensive_capacity: int = 0  # 0-10
    economic_state: str = "sufficient"
    resources: List[Dict[str, Any]] = field(default_factory=list)
    notable_features: List[str] = field(default_factory=list)
    connections: List[LocationConnection] = field(default_factory=list)
    current_events: List[str] = field(default_factory=list)
    dangers: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    description: str = ""
    npcs_present: List[str] = field(default_factory=list)
    ambient: AmbientConditions = field(default_factory=AmbientConditions)
    history: List[Dict[str, Any]] = field(default_factory=list)
    last_tick_updates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "display_name": self.display_name,
            "type": self.type,
            "region": self.region,
            "coordinates": dict(self.coordinates),
            "controller": self.controller,
            "population": self.population,
            "defensive_capacity": self.defensive_capacity,
            "economic_state": self.economic_state,
            "resources": list(self.resources),
            "notable_features": list(self.notable_features),
            "connections": [c.to_dict() for c in self.connections],
            "current_events": list(self.current_events),
            "dangers": list(self.dangers),
            "opportunities": list(self.opportunities),
            "description": self.description,
            "npcs_present": list(self.npcs_present),
            "ambient": self.ambient.to_dict(),
            "history": list(self.history),
            "last_tick_updates": list(self.last_tick_updates),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(
            id=data.get("id", ""),
            schema_version=data.get("schema_version", "1.0"),
            display_name=data.get("display_name", ""),
            type=data.get("type", "town"),
            region=data.get("region", ""),
            coordinates=data.get("coordinates", {}),
            controller=data.get("controller"),
            population=data.get("population", 0),
            defensive_capacity=data.get("defensive_capacity", 0),
            economic_state=data.get("economic_state", "sufficient"),
            resources=data.get("resources", []),
            notable_features=data.get("notable_features", []),
            connections=[
                LocationConnection.from_dict(c)
                for c in data.get("connections", [])
            ],
            current_events=data.get("current_events", []),
            dangers=data.get("dangers", []),
            opportunities=data.get("opportunities", []),
            description=data.get("description", ""),
            npcs_present=data.get("npcs_present", []),
            ambient=AmbientConditions.from_dict(data["ambient"])
            if "ambient" in data
            else AmbientConditions(),
            history=data.get("history", []),
            last_tick_updates=data.get("last_tick_updates", []),
        )


# ---------------------------------------------------------------------------
# Clock
# ---------------------------------------------------------------------------

@dataclass
class Clock:
    """A progress clock tracking an impending event or process."""

    id: str = ""
    schema_version: str = "1.0"
    display_name: str = ""
    current_segment: int = 0
    total_segments: int = 8
    advance_conditions: List[Dict[str, Any]] = field(default_factory=list)
    advance_rate: Dict[str, Any] = field(default_factory=dict)
    completion_consequences: List[Dict[str, Any]] = field(default_factory=list)
    reset_conditions: List[Dict[str, Any]] = field(default_factory=list)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    narrative_description: str = ""
    last_advancement: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Clock":
        return cls(
            id=data.get("id", ""),
            schema_version=data.get("schema_version", "1.0"),
            display_name=data.get("display_name", ""),
            current_segment=data.get("current_segment", 0),
            total_segments=data.get("total_segments", 8),
            advance_conditions=data.get("advance_conditions", []),
            advance_rate=data.get("advance_rate", {}),
            completion_consequences=data.get("completion_consequences", []),
            reset_conditions=data.get("reset_conditions", []),
            interactions=data.get("interactions", []),
            narrative_description=data.get("narrative_description", ""),
            last_advancement=data.get("last_advancement", {}),
        )


# ---------------------------------------------------------------------------
# Tick Event
# ---------------------------------------------------------------------------

@dataclass
class TickEvent:
    """A single event produced during a world tick."""

    tick_timestamp: str
    entity_type: str  # faction, npc, location, clock, threat, environment
    entity_id: str
    event_type: str
    details: Dict[str, Any] = field(default_factory=dict)
    consequences: List[Dict[str, Any]] = field(default_factory=list)
    visibility: str = "local"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickEvent":
        return cls(
            tick_timestamp=data["tick_timestamp"],
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            event_type=data["event_type"],
            details=data.get("details", {}),
            consequences=data.get("consequences", []),
            visibility=data.get("visibility", "local"),
        )


# ---------------------------------------------------------------------------
# Situation
# ---------------------------------------------------------------------------

@dataclass
class SituationChoice:
    """A choice available to the player within a situation."""

    id: str
    description: str
    type: str  # dialogue, action, observation, travel, activity
    consequences_hint: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SituationChoice":
        return cls(
            id=data["id"],
            description=data["description"],
            type=data["type"],
            consequences_hint=data.get("consequences_hint"),
        )


@dataclass
class Situation:
    """A snapshot of the player's current narrative context."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    location: str = ""
    timestamp: str = ""
    present_npcs: List[str] = field(default_factory=list)
    ambient: Dict[str, Any] = field(default_factory=dict)
    recent_events: List[str] = field(default_factory=list)
    tension: str = ""
    player_choices: List[SituationChoice] = field(default_factory=list)
    could_happen_next: List[str] = field(default_factory=list)
    encounter_probability: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schema_version": self.schema_version,
            "location": self.location,
            "timestamp": self.timestamp,
            "present_npcs": list(self.present_npcs),
            "ambient": dict(self.ambient),
            "recent_events": list(self.recent_events),
            "tension": self.tension,
            "player_choices": [c.to_dict() for c in self.player_choices],
            "could_happen_next": list(self.could_happen_next),
            "encounter_probability": self.encounter_probability,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Situation":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            schema_version=data.get("schema_version", "1.0"),
            location=data.get("location", ""),
            timestamp=data.get("timestamp", ""),
            present_npcs=data.get("present_npcs", []),
            ambient=data.get("ambient", {}),
            recent_events=data.get("recent_events", []),
            tension=data.get("tension", ""),
            player_choices=[
                SituationChoice.from_dict(c)
                for c in data.get("player_choices", [])
            ],
            could_happen_next=data.get("could_happen_next", []),
            encounter_probability=data.get("encounter_probability", 0.0),
        )


# ---------------------------------------------------------------------------
# World State
# ---------------------------------------------------------------------------

@dataclass
class SessionMetadata:
    """Metadata about the current play session."""

    session_count: int = 0
    total_playtime_real_seconds: int = 0
    last_save: str = ""
    character_lifetime_years: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionMetadata":
        return cls(
            session_count=data.get("session_count", 0),
            total_playtime_real_seconds=data.get(
                "total_playtime_real_seconds", 0
            ),
            last_save=data.get("last_save", ""),
            character_lifetime_years=data.get("character_lifetime_years", 0.0),
        )


@dataclass
class ActiveScene:
    """The currently active scene or mode."""

    type: str = "sim_mode"  # sim_mode, combat_mode, framing, session_zero
    scene_id: str = ""
    state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ActiveScene":
        return cls(
            type=data.get("type", "sim_mode"),
            scene_id=data.get("scene_id", ""),
            state=data.get("state", {}),
        )


@dataclass
class WorldState:
    """Top-level container for the entire world state."""

    schema_version: str = "1.0"
    current_time: Dict[str, Any] = field(
        default_factory=lambda: {
            "in_world_date": "T+1y 0m 0d",
            "onset_date_real": "2025-01-01",
            "year": 1,
        }
    )
    active_scene: Optional[ActiveScene] = None
    session_metadata: SessionMetadata = field(default_factory=SessionMetadata)
    worldline_id: str = "lordly_equilibrium"
    active_player_character: str = ""
    past_characters: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "current_time": dict(self.current_time),
            "active_scene": self.active_scene.to_dict()
            if self.active_scene is not None
            else None,
            "session_metadata": self.session_metadata.to_dict(),
            "worldline_id": self.worldline_id,
            "active_player_character": self.active_player_character,
            "past_characters": list(self.past_characters),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        return cls(
            schema_version=data.get("schema_version", "1.0"),
            current_time=data.get(
                "current_time",
                {
                    "in_world_date": "T+1y 0m 0d",
                    "onset_date_real": "2025-01-01",
                    "year": 1,
                },
            ),
            active_scene=ActiveScene.from_dict(data["active_scene"])
            if data.get("active_scene") is not None
            else None,
            session_metadata=SessionMetadata.from_dict(
                data["session_metadata"]
            )
            if "session_metadata" in data
            else SessionMetadata(),
            worldline_id=data.get("worldline_id", "lordly_equilibrium"),
            active_player_character=data.get("active_player_character", ""),
            past_characters=data.get("past_characters", []),
        )
