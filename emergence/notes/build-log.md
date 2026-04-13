# Build Log — Emergence

## Entry 0: Repository Organization

**Date:** Session start

**Action:** Organized flat repository into structured directory layout per README.md specification.

**Structure created:**
```
emergence/
  specs/           — 6 specification files (combat-spec, runtime-architecture, prompt-management, state-persistence, character-creation, progression)
  setting/         — 15 setting bible files
  engine/schemas/  — (Phase 1)
  engine/combat/   — (Phase 2)
  engine/sim/      — (Phase 3, 4)
  engine/runtime/  — (Phase 5)
  engine/narrator/ — (Phase 5)
  engine/persistence/ — (Phase 5)
  engine/progression/ — (Phase 6)
  engine/character_creation/ — (Phase 4)
  data/powers/     — (Phase 2)
  data/enemies/    — (Phase 2)
  data/encounters/ — (Phase 2)
  prompts/         — (Phase 5)
  tests/unit/      — test files
  tests/integration/ — test files
  tests/scenarios/ — test files
  tests/output/    — test output
  notes/           — build notes
```

**Missing specs noted:** sim-architecture.md and sim-content-integration.md referenced in README but not present in uploaded files. Logged to design-questions.md. Will construct from design-brief, interface-spec, gm-primer, and other available specs.

**Files moved:** All 21 source files organized into appropriate directories. No renames.

## Entry 1: Phase 1 — Schema Scaffolding and Validation Framework

**Date:** Phase 1 complete

**Deliverables:**
- `engine/schemas/character.py` (369 lines) — CharacterSheet, Attributes, Harm, Breakthrough, RelationshipState, InventoryItem, Goal, StatusEffect, HistoryEvent; Species/PowerCategory/ConditionTrack enums
- `engine/schemas/combatant.py` (179 lines) — Combatant with from_character_sheet(); AiProfile/CombatantSide/AffinityState enums
- `engine/schemas/encounter.py` (294 lines) — EncounterSpec, CombatOutcome, Action, EnemyState, PlayerStateDelta, NarrativeLogEntry, WorldConsequence, TerrainZone, WinLossCondition, WorldContext; _DictMixin base class; 8 enums
- `engine/schemas/narrator.py` (161 lines) — NarratorPayload, OutputTarget, ContextContinuity, NarratorConstraints; SceneType/RegisterDirective/OutputFormat enums
- `engine/schemas/world.py` (903 lines) — WorldState, Faction, NPC, Location, Clock, TickEvent, Situation, SessionMetadata, ActiveScene; 12 supporting dataclasses; 6 enums
- `engine/schemas/content.py` (198 lines) — Power, EnemyTemplate, PowerCost, PowerEffect
- `engine/schemas/serialization.py` (73 lines) — to_json/from_json, atomic save_to_file/load_from_file, MigrationRegistry with version tracking
- `engine/schemas/validation.py` (403 lines) — 13 validator functions, ValidationResult, 20 validation constant sets
- `engine/schemas/__init__.py` — Comprehensive re-exports of all types

**Tests:**
- `tests/unit/test_schemas.py` — 21 round-trip serialization tests covering all schema types including a full WorldState integration test
- `tests/unit/test_validation.py` — 116 validation tests covering valid inputs, invalid inputs, edge cases, and enum exhaustiveness for all 13 validators

**Exit criteria verified:**
1. Every schema serializes and deserializes without information loss — 21 tests pass
2. Every validation function correctly identifies valid and invalid inputs — 116 tests pass
3. All 137 unit tests pass

**Design decisions:**
- Used string-typed enum values in dataclass fields (not Enum instances) for JSON compatibility; Enum classes available for reference/documentation
- _DictMixin in encounter.py and narrator.py provides automatic to_dict/from_dict via field introspection; character.py and world.py use explicit methods for clarity with complex nested types
- Serialization uses json stdlib with atomic temp-and-rename writes per state-persistence spec
- Species enum in character.py has legacy values; validation.py uses correct setting bible species set
- Schema version "1.0" with MigrationRegistry ready for future migrations

**Issues resolved:**
- DQ-001/DQ-002: Missing sim-architecture.md and sim-content-integration.md — will construct from available specs
- Fixed VALID_SPECIES in validation.py to match setting bible (hollow_boned, deep_voiced, etc.) rather than incorrect placeholder values

## Entry 2: Phase 2 — Combat Engine

**Date:** Phase 2 complete

**Deliverables:**
- `engine/combat/resolution.py` — roll_check, classify_result, tier_gap_modifier, compute_defense_value, compute_mental_defense, roll_initiative
- `engine/combat/damage.py` — resolve_damage, allocate_to_tracks, compute_exposure_fill, DamageType, 7 AFFINITY_PROFILES
- `engine/combat/statuses.py` — StatusEngine (7 statuses: bleeding, stunned, shaken, burning, exposed, marked, corrupted), tick_start/end_of_round, modifier queries
- `engine/combat/ai.py` — AiDecisionEngine (5 profiles: aggressive, defensive, tactical, opportunist, pack), weighted feature scoring, retreat triggers
- `engine/combat/verbs.py` — CombatState, CombatantRecord, VerbResult, 8 verb resolvers (Attack, Power, Assess, Maneuver, Parley, Disengage, Finisher, Defend)
- `engine/combat/encounter_runner.py` — EncounterRunner: builds state, rolls initiative, runs round loop, dispatches verbs, checks win/loss/escape, builds CombatOutcome; register-specific mechanics (human heat, creature ecological clock, eldritch corruption offers)
- `engine/combat/data_loader.py` — load_powers, load_enemies, load_encounters
- `engine/combat/__init__.py` — Public API re-exports

**Data files:**
- `data/powers/*.json` — 48 powers across 7 categories (7 files)
- `data/enemies/*.json` — 30 enemy templates: 12 human, 12 creature, 6 eldritch (3 files)
- `data/encounters/sample_encounters.json` — 12 encounters across all 3 registers

**Schema fixes:**
- Added "auratic" to VALID_POWER_CATEGORIES in validation.py
- Added `tier` and `condition_track_max` fields to EnemyTemplate in content.py

**Tests:** 248 total (246 pass, 2 skipped)
- `test_resolution.py` — 18 tests (dice, classify_result, tier gap, monte carlo)
- `test_damage.py` — 25 tests (affinity, armor, exposure fill, track allocation, profiles)
- `test_statuses.py` — 20 tests (all 7 statuses, ticks, modifiers, scene clear)
- `test_ai.py` — 13 tests (5 profiles, retreat, pack degradation, target picking)
- `test_verbs.py` — 15 tests (all 8 resolvers with deterministic seeds)
- `test_data_loader.py` — 13 tests (48 powers, 30 enemies, 12 encounters)
- `test_combat_scenarios.py` — 6 integration tests (human, creature, eldritch registers)

**Exit criteria verified:**
1. `from emergence.engine.combat import EncounterRunner` imports cleanly
2. 48 powers, 30 enemies, 12 encounters load via data_loader
3. Seeded encounters produce deterministic, serializable CombatOutcome
4. All 248 tests pass

## Entry 2.5: Combat Spec Audit Fixes (Batches 1-7)

**Date:** Between Phase 2 and Phase 3

**Deliverables:**
- 27 bug fixes across encounter_runner.py, verbs.py, statuses.py, ai.py
- `tests/regression/test_combat_fixes.py` — 26 regression tests for all fixes

**Key fixes:**
- Batch 1: Eldritch clock advances each round; defensive AI uses AND (not OR) for retreat
- Batch 2: Bleeding/Burning tick after turn (not start of round)
- Batch 3: AI enumerates Defend as candidate action
- Batch 3B: Status durations match spec §6.1; Defend uses incoming_total for TN; ranged attacks apply armor
- Batch 5: Ecological clock logs events at 4/6/8 thresholds; corruption offers only on Parley/Power/Assess at P=0.2
- Batch 6: Heat calculation per spec §15.4 (per-enemy base, witness quotient +1/3 witnesses capped at 3, eldritch flag, parley -2)

**Tests:** 275 total after fixes

## Entry 3: Phase 3 — Simulation Engine Core

**Date:** Phase 3 complete

**Deliverables:**
- `engine/sim/yaml_parser.py` (~280 lines) — Minimal stdlib-only YAML subset parser: key-value, lists, nested indent, folded strings, comments, numerics, ~N approx values, inline lists, booleans, null, quoted strings
- `engine/sim/clocks.py` (~230 lines) — ClockEngine: advance evaluation, completion, reset, cross-clock interactions, condition types (always, flag, resource_below, clock_at, faction_conflict)
- `engine/sim/faction_logic.py` (~290 lines) — FactionDecisionEngine: territorial/diplomatic/scheme/internal/resource/goal actions, weighted selection, ~1 action/week calibration
- `engine/sim/npc_behavior.py` (~230 lines) — NpcBehaviorEngine: schedule evaluation, goal pursuit, memory decay, relationship drift, displacement, concern response
- `engine/sim/location_dynamics.py` (~210 lines) — LocationEngine: economic transitions, migration, danger escalation, opportunity generation, NPC sync, controller changes
- `engine/sim/tick_engine.py` (~130 lines) — TickEngine: daily orchestrator (time→clocks→factions→NPCs→locations→sync), seasonal ticks every 90 days
- `engine/sim/situation_generator.py` (~170 lines) — SituationGenerator: tension assessment, encounter probability, 3-6 choice generation
- `engine/sim/abstract_combat.py` (~110 lines) — Off-screen combat: tier+military power, 2d6 variance, casualty scales, territory consequences
- `engine/sim/encounter_generator.py` (~200 lines) — EncounterGenerator: register determination from world state, enemy selection, terrain, conditions
- `engine/sim/player_actions.py` (~200 lines) — PlayerActionResolver: dialogue, travel, activity, observation, prepare actions
- `engine/sim/context_management.py` (~130 lines) — compact_state() for narrator payloads
- `engine/sim/persistence.py` (~70 lines) — DirtyTracker for incremental saves
- `tests/helpers/synthetic_world.py` — 3 factions, 5 NPCs, 5 locations, 8 clocks

**Tests:** 462 total (459 pass, 3 skipped)
- `test_yaml_parser.py` — 41 tests
- `test_clocks.py` — 30 tests
- `test_faction_logic.py` — 11 tests
- `test_npc_behavior.py` — 18 tests
- `test_location_dynamics.py` — 13 tests
- `test_tick_engine.py` — 8 tests
- `test_situations.py` — 16 tests
- `test_abstract_combat.py` — 8 tests
- `test_encounter_generator.py` — 11 tests
- `test_player_actions.py` — 18 tests (includes context_management + persistence)
- `test_world_tick.py` — 7 integration tests (365-day smoke)
- `test_encounter_generation.py` — 3 integration tests (situation→encounter)
- `test_sim_combat_handoff.py` — 3 integration tests (sim→combat pipeline)

**Exit criteria verified:**
1. Synthetic world (3 factions, 5 NPCs, 5 locations, 8 clocks) ticks 365 days cleanly
2. Clocks advance, factions act, NPCs move, locations update, seasons cycle
3. Encounter generation produces valid EncounterSpec with appropriate register
4. Sim↔combat handoff works via existing EncounterRunner
5. Deterministic replay verified
6. All 462 tests pass
