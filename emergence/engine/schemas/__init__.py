"""Emergence engine schemas — dataclasses for all game state."""
from emergence.engine.schemas.character import (
    CharacterSheet, Attributes, Harm, Breakthrough, RelationshipState,
    InventoryItem, Goal, StatusEffect, HistoryEvent,
    PowerCategory, ConditionTrack,
)
from emergence.engine.schemas.combatant import (
    Combatant, AiProfile, CombatantSide, AffinityState,
)
from emergence.engine.schemas.encounter import (
    EncounterSpec, CombatOutcome, Action, TerrainZone, WinLossCondition,
    WorldContext, EnemyState, PlayerStateDelta, NarrativeLogEntry,
    WorldConsequence, CombatRegister, CombatResolution, CombatVerb,
    ConditionType, EnemyFinalState, ConsequenceType,
)
from emergence.engine.schemas.narrator import (
    NarratorPayload, OutputTarget, ContextContinuity, NarratorConstraints,
    SceneType, RegisterDirective, OutputFormat,
)
from emergence.engine.schemas.world import (
    WorldState, Faction, NPC, Location, Clock, TickEvent, Situation,
    SessionMetadata, ActiveScene, FactionTerritory, FactionPopulation,
    FactionPowerProfile, FactionEconomicBase, FactionGoal, FactionScheme,
    FactionRelationship, NpcManifest, NpcKnowledge, NpcMemory,
    NpcRelationshipState, LocationConnection, AmbientConditions,
    SituationChoice,
)
from emergence.engine.schemas.content import (
    Power, EnemyTemplate, PowerCost, PowerEffect,
)
from emergence.engine.schemas.serialization import (
    to_json, from_json, save_to_file, load_from_file,
    CURRENT_SCHEMA_VERSION, migration_registry,
)
from emergence.engine.schemas.validation import (
    validate_character_sheet, validate_combatant, validate_encounter_spec,
    validate_combat_outcome, validate_action, validate_narrator_payload,
    validate_faction, validate_npc, validate_location, validate_clock,
    validate_world_state, validate_power, validate_enemy_template,
    ValidationResult,
)
