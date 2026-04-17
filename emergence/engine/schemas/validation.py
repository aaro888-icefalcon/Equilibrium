"""Validation functions for all Emergence schemas.

Each validator returns a ValidationResult indicating success or failure,
with a list of error messages describing any issues found.
Uses only the Python standard library.
"""

from dataclasses import dataclass, field
from typing import List, Any

from emergence.engine.schemas.character import CharacterSheet
from emergence.engine.schemas.combatant import Combatant
from emergence.engine.schemas.encounter import EncounterSpec, CombatOutcome, Action
from emergence.engine.schemas.narrator import NarratorPayload
from emergence.engine.schemas.world import WorldState, Faction, NPC, Location, Clock
from emergence.engine.schemas.content import Power, EnemyTemplate


VALID_DIE_SIZES = {4, 6, 8, 10, 12}
VALID_SPECIES = {
    "human", "hollow_boned", "deep_voiced", "silver_hand", "pale_eyed",
    "slow_breath", "broad_shouldered", "sun_worn", "quick_blooded",
    "wide_sighted", "stone_silent", "corrupted",
}
VALID_POWER_CATEGORIES = {
    "somatic", "cognitive", "material", "kinetic", "spatial", "paradoxic",
}
# V2 sub-categories: 5 per broad, 30 total. Matches powers_v2/*.json.
VALID_POWER_SUB_CATEGORIES = {
    # kinetic
    "gravitic", "impact", "projective", "sonic", "velocity",
    # material
    "corrosive", "elemental", "machinal", "radiant", "transmutative",
    # paradoxic
    "anomalous", "divinatory", "probabilistic", "sympathetic", "temporal",
    # somatic
    "augmentation", "biochemistry", "metamorphosis", "predation", "vitality",
    # spatial
    "gateway", "phasing", "reach", "territorial", "translative",
    # cognitive
    "auratic", "dominant", "perceptive", "predictive", "telepathic",
}
VALID_CONDITION_TRACKS = {"physical", "mental", "social"}
VALID_STATUS_NAMES = {
    "bleeding", "stunned", "shaken", "burning", "exposed", "marked", "corrupted",
}
VALID_COMBATANT_SIDES = {"enemy", "ally", "neutral"}
VALID_AI_PROFILES = {"aggressive", "defensive", "tactical", "opportunist", "pack"}
VALID_COMBAT_REGISTERS = {"human", "creature", "eldritch"}
VALID_COMBAT_VERBS = {
    "Attack", "Power", "Power_Minor", "Assess", "Maneuver", "Parley",
    "Finisher", "Brace", "Posture_Change", "Utility",
}
VALID_EFFECT_FAMILIES = {
    "damage", "status", "movement", "information", "control", "resource",
    "defense", "utility", "meta", "cost_shifted", "action_economy",
    "stat_alteration", "terrain_alteration",
}
VALID_POSTURES = {"parry", "block", "dodge", "aggressive"}
VALID_RIDER_TYPES = {"strike", "posture", "maneuver", "parley", "assess", "finisher"}
VALID_ATTACK_SUB_TYPES = {"heavy", "quick", "ranged", "grapple"}
VALID_MANEUVER_SUB_TYPES = {"reposition", "disrupt", "conceal"}
VALID_PARLEY_SUB_TYPES = {"demand", "taunt", "disorient", "destabilize", "negotiate"}
VALID_RESOLUTIONS = {
    "victory", "defeat", "parley", "escape", "truce", "stalemate", "other",
}
VALID_SCENE_TYPES = {
    "combat_turn", "scene_framing", "situation_description", "dialogue",
    "transition", "character_creation_beat", "time_skip", "death_narration",
}
VALID_REGISTER_DIRECTIVES = {"standard", "eldritch", "intimate", "action", "quiet"}
VALID_OUTPUT_FORMATS = {"prose", "dialogue", "mixed", "terse"}
VALID_FACTION_TYPES = {
    "noble_house", "warlord_holding", "merchant_guild",
    "religious_order", "metahuman_polity", "survivor_commune",
}
VALID_LOCATION_TYPES = {
    "city", "town", "fortress", "ruin", "wilderness_zone",
    "faction_holding", "natural_feature", "charged_zone",
}
VALID_ECONOMIC_STATES = {"thriving", "sufficient", "strained", "failing", "abandoned"}
VALID_NPC_STATUSES = {"alive", "dead", "missing", "transformed", "displaced"}
VALID_ENEMY_FINAL_STATES = {
    "alive", "dead", "fled", "surrendered", "incapacitated", "transformed",
}
VALID_POWER_EFFECT_TYPES = {"damage", "status", "utility", "movement", "combined"}
VALID_USAGE_SCOPES = {"combat", "sim", "both"}
VALID_VISIBILITY = {"visible", "subtle", "variable"}


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.errors.append(msg)


# ---------------------------------------------------------------------------
# Character validation
# ---------------------------------------------------------------------------

def validate_character_sheet(c: CharacterSheet) -> ValidationResult:
    """Validate a CharacterSheet instance."""
    r = ValidationResult()

    if not c.name or not c.name.strip():
        r.add_error("name must be a non-empty string")

    if c.species and c.species not in VALID_SPECIES:
        r.add_error(f"species '{c.species}' is not valid; expected one of {sorted(VALID_SPECIES)}")

    # Attributes must be valid die sizes
    for attr_name in ("strength", "agility", "perception", "will", "insight", "might"):
        val = getattr(c.attributes, attr_name)
        if val not in VALID_DIE_SIZES:
            r.add_error(f"attribute '{attr_name}' has value {val}; must be one of {sorted(VALID_DIE_SIZES)}")

    # Tier bounds
    if not (1 <= c.tier <= 10):
        r.add_error(f"tier {c.tier} out of range 1-10")
    if not (1 <= c.tier_ceiling <= 10):
        r.add_error(f"tier_ceiling {c.tier_ceiling} out of range 1-10")
    if c.tier > c.tier_ceiling:
        r.add_error(f"tier ({c.tier}) exceeds tier_ceiling ({c.tier_ceiling})")

    # Corruption
    if not (0 <= c.corruption <= 6):
        r.add_error(f"corruption {c.corruption} out of range 0-6")

    # Condition tracks
    for track_name, val in c.condition_tracks.items():
        if track_name not in VALID_CONDITION_TRACKS:
            r.add_error(f"unknown condition track '{track_name}'")
        if not isinstance(val, int) or val < 0:
            r.add_error(f"condition track '{track_name}' value {val} must be a non-negative integer")

    # Statuses
    for s in c.statuses:
        if s.name not in VALID_STATUS_NAMES:
            r.add_error(f"status name '{s.name}' is not valid; expected one of {sorted(VALID_STATUS_NAMES)}")

    # Power categories
    if c.power_category_primary and c.power_category_primary not in VALID_POWER_CATEGORIES:
        r.add_error(f"power_category_primary '{c.power_category_primary}' is not valid")
    if c.power_category_secondary and c.power_category_secondary not in VALID_POWER_CATEGORIES:
        r.add_error(f"power_category_secondary '{c.power_category_secondary}' is not valid")

    # Harm tiers
    for h in c.harm:
        if h.tier not in (1, 2, 3):
            r.add_error(f"harm tier {h.tier} must be 1, 2, or 3")

    # Goals
    for g in c.goals:
        if not (0 <= g.progress <= 10):
            r.add_error(f"goal '{g.id}' progress {g.progress} out of range 0-10")
        if not (0 <= g.pressure <= 5):
            r.add_error(f"goal '{g.id}' pressure {g.pressure} out of range 0-5")

    # Relationships standing
    for key, rel in c.relationships.items():
        if not (-3 <= rel.standing <= 3):
            r.add_error(f"relationship '{key}' standing {rel.standing} out of range -3 to +3")
        if not (0 <= rel.trust <= 5):
            r.add_error(f"relationship '{key}' trust {rel.trust} out of range 0-5")

    return r


# ---------------------------------------------------------------------------
# Combatant validation
# ---------------------------------------------------------------------------

def validate_combatant(c: Combatant) -> ValidationResult:
    """Validate a Combatant instance."""
    r = ValidationResult()

    if not c.id:
        r.add_error("id must be non-empty")
    if not c.name:
        r.add_error("name must be non-empty")
    if c.side not in VALID_COMBATANT_SIDES:
        r.add_error(f"side '{c.side}' must be one of {sorted(VALID_COMBATANT_SIDES)}")
    if c.ai_profile not in VALID_AI_PROFILES:
        r.add_error(f"ai_profile '{c.ai_profile}' must be one of {sorted(VALID_AI_PROFILES)}")
    if c.exposure_track < 0:
        r.add_error(f"exposure_track {c.exposure_track} must be non-negative")
    if c.exposure_max < 1:
        r.add_error(f"exposure_max {c.exposure_max} must be at least 1")
    if c.exposure_track > c.exposure_max:
        r.add_error(f"exposure_track ({c.exposure_track}) exceeds exposure_max ({c.exposure_max})")

    for attr_name in ("strength", "agility", "perception", "will", "insight", "might"):
        val = getattr(c.attributes, attr_name)
        if val not in VALID_DIE_SIZES:
            r.add_error(f"attribute '{attr_name}' has value {val}; must be one of {sorted(VALID_DIE_SIZES)}")

    if not (0 <= c.corruption <= 6):
        r.add_error(f"corruption {c.corruption} out of range 0-6")

    return r


# ---------------------------------------------------------------------------
# Encounter validation
# ---------------------------------------------------------------------------

def validate_encounter_spec(e: EncounterSpec) -> ValidationResult:
    """Validate an EncounterSpec instance."""
    r = ValidationResult()

    if not e.id:
        r.add_error("id must be non-empty")
    if e.combat_register not in VALID_COMBAT_REGISTERS:
        r.add_error(f"combat_register '{e.combat_register}' must be one of {sorted(VALID_COMBAT_REGISTERS)}")
    if not e.enemies:
        r.add_error("enemies list must not be empty")
    if not e.location:
        r.add_error("location must be non-empty")

    return r


def validate_combat_outcome(o: CombatOutcome) -> ValidationResult:
    """Validate a CombatOutcome instance."""
    r = ValidationResult()

    if not o.encounter_id:
        r.add_error("encounter_id must be non-empty")
    if o.resolution not in VALID_RESOLUTIONS:
        r.add_error(f"resolution '{o.resolution}' must be one of {sorted(VALID_RESOLUTIONS)}")
    if o.rounds_elapsed < 0:
        r.add_error(f"rounds_elapsed {o.rounds_elapsed} must be non-negative")

    return r


def validate_action(a: Action) -> ValidationResult:
    """Validate an Action instance."""
    r = ValidationResult()

    if not a.actor_id:
        r.add_error("actor_id must be non-empty")
    if a.verb not in VALID_COMBAT_VERBS:
        r.add_error(f"verb '{a.verb}' must be one of {sorted(VALID_COMBAT_VERBS)}")
    if a.declared_at_round < 0:
        r.add_error(f"declared_at_round {a.declared_at_round} must be non-negative")

    return r


# ---------------------------------------------------------------------------
# Narrator validation
# ---------------------------------------------------------------------------

def validate_narrator_payload(p: NarratorPayload) -> ValidationResult:
    """Validate a NarratorPayload instance."""
    r = ValidationResult()

    if p.scene_type not in VALID_SCENE_TYPES:
        r.add_error(f"scene_type '{p.scene_type}' must be one of {sorted(VALID_SCENE_TYPES)}")
    if p.register_directive not in VALID_REGISTER_DIRECTIVES:
        r.add_error(f"register_directive '{p.register_directive}' must be one of {sorted(VALID_REGISTER_DIRECTIVES)}")
    if p.output_target.format not in VALID_OUTPUT_FORMATS:
        r.add_error(f"output_target.format '{p.output_target.format}' must be one of {sorted(VALID_OUTPUT_FORMATS)}")

    length = p.output_target.desired_length
    if "min_words" in length and "max_words" in length:
        if length["min_words"] > length["max_words"]:
            r.add_error("output_target.desired_length min_words exceeds max_words")
        if length["min_words"] < 0:
            r.add_error("output_target.desired_length min_words must be non-negative")

    return r


# ---------------------------------------------------------------------------
# World schema validation
# ---------------------------------------------------------------------------

def validate_faction(f: Faction) -> ValidationResult:
    """Validate a Faction instance."""
    r = ValidationResult()

    if not f.id:
        r.add_error("id must be non-empty")
    if not f.display_name:
        r.add_error("display_name must be non-empty")
    if f.type not in VALID_FACTION_TYPES:
        r.add_error(f"type '{f.type}' must be one of {sorted(VALID_FACTION_TYPES)}")
    if not (-3 <= f.standing_with_player_default <= 3):
        r.add_error(f"standing_with_player_default {f.standing_with_player_default} out of range -3 to +3")
    if f.population.total < 0:
        r.add_error(f"population.total {f.population.total} must be non-negative")
    if f.population.military_capacity < 0:
        r.add_error(f"population.military_capacity must be non-negative")
    if not (0.0 <= f.population.powered_fraction <= 1.0):
        r.add_error(f"population.powered_fraction {f.population.powered_fraction} out of range 0.0-1.0")

    return r


def validate_npc(n: NPC) -> ValidationResult:
    """Validate an NPC instance."""
    r = ValidationResult()

    if not n.id:
        r.add_error("id must be non-empty")
    if not n.display_name:
        r.add_error("display_name must be non-empty")
    if n.species not in VALID_SPECIES:
        r.add_error(f"species '{n.species}' must be one of {sorted(VALID_SPECIES)}")
    if n.status not in VALID_NPC_STATUSES:
        r.add_error(f"status '{n.status}' must be one of {sorted(VALID_NPC_STATUSES)}")
    if n.age < 0:
        r.add_error(f"age {n.age} must be non-negative")

    return r


def validate_location(loc: Location) -> ValidationResult:
    """Validate a Location instance."""
    r = ValidationResult()

    if not loc.id:
        r.add_error("id must be non-empty")
    if not loc.display_name:
        r.add_error("display_name must be non-empty")
    if loc.type not in VALID_LOCATION_TYPES:
        r.add_error(f"type '{loc.type}' must be one of {sorted(VALID_LOCATION_TYPES)}")
    if loc.economic_state not in VALID_ECONOMIC_STATES:
        r.add_error(f"economic_state '{loc.economic_state}' must be one of {sorted(VALID_ECONOMIC_STATES)}")
    if not (0 <= loc.defensive_capacity <= 10):
        r.add_error(f"defensive_capacity {loc.defensive_capacity} out of range 0-10")
    if loc.population < 0:
        r.add_error(f"population {loc.population} must be non-negative")

    return r


def validate_clock(c: Clock) -> ValidationResult:
    """Validate a Clock instance."""
    r = ValidationResult()

    if not c.id:
        r.add_error("id must be non-empty")
    if not c.display_name:
        r.add_error("display_name must be non-empty")
    if c.total_segments < 1:
        r.add_error(f"total_segments {c.total_segments} must be at least 1")
    if c.current_segment < 0:
        r.add_error(f"current_segment {c.current_segment} must be non-negative")
    if c.current_segment > c.total_segments:
        r.add_error(f"current_segment ({c.current_segment}) exceeds total_segments ({c.total_segments})")

    return r


def validate_world_state(ws: WorldState) -> ValidationResult:
    """Validate a WorldState instance."""
    r = ValidationResult()

    if not ws.schema_version:
        r.add_error("schema_version must be non-empty")
    if "in_world_date" not in ws.current_time:
        r.add_error("current_time must include 'in_world_date'")
    if "year" not in ws.current_time:
        r.add_error("current_time must include 'year'")
    if ws.current_time.get("year", 0) < 0:
        r.add_error("current_time.year must be non-negative")

    return r


# ---------------------------------------------------------------------------
# Content validation
# ---------------------------------------------------------------------------

def validate_power(p: Power) -> ValidationResult:
    """Validate a Power instance."""
    r = ValidationResult()

    if not p.id:
        r.add_error("id must be non-empty")
    if not p.name:
        r.add_error("name must be non-empty")
    if p.category and p.category not in VALID_POWER_CATEGORIES:
        r.add_error(f"category '{p.category}' must be one of {sorted(VALID_POWER_CATEGORIES)}")
    if not (1 <= p.tier <= 10):
        r.add_error(f"tier {p.tier} out of range 1-10")
    if p.effect.type not in VALID_POWER_EFFECT_TYPES:
        r.add_error(f"effect.type '{p.effect.type}' must be one of {sorted(VALID_POWER_EFFECT_TYPES)}")
    if p.usage_scope not in VALID_USAGE_SCOPES:
        r.add_error(f"usage_scope '{p.usage_scope}' must be one of {sorted(VALID_USAGE_SCOPES)}")
    if p.cost.corruption < 0:
        r.add_error(f"cost.corruption {p.cost.corruption} must be non-negative")

    return r


def validate_enemy_template(et: EnemyTemplate) -> ValidationResult:
    """Validate an EnemyTemplate instance."""
    r = ValidationResult()

    if not et.id:
        r.add_error("id must be non-empty")
    if not et.display_name:
        r.add_error("display_name must be non-empty")
    if et.register not in VALID_COMBAT_REGISTERS:
        r.add_error(f"register '{et.register}' must be one of {sorted(VALID_COMBAT_REGISTERS)}")
    if et.ai_profile not in VALID_AI_PROFILES:
        r.add_error(f"ai_profile '{et.ai_profile}' must be one of {sorted(VALID_AI_PROFILES)}")
    if et.exposure_max < 1:
        r.add_error(f"exposure_max {et.exposure_max} must be at least 1")

    # Validate attribute defaults
    for attr_name in ("strength", "agility", "perception", "will", "insight", "might"):
        val = et.attribute_defaults.get(attr_name, 6)
        if val not in VALID_DIE_SIZES:
            r.add_error(f"attribute_defaults.{attr_name} has value {val}; must be one of {sorted(VALID_DIE_SIZES)}")

    return r
