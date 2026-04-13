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

## Entry 4: Phase 4 — Content Integration and Character Creation

**Date:** Phase 4 complete

**Deliverables:**
- `engine/sim/content_loader.py` (~425 lines) — ContentLoader: loads factions.yaml, npcs.yaml, locations.yaml, clocks.yaml, constants.yaml, timeline.yaml. Handles informal values (~N, "very high", "T9 Physical/kinetic", "neutral-transactional", parenthetical faction qualifiers)
- `engine/sim/initial_state.py` (~150 lines) — build_initial_world(): assembles T+1 year state from all bible content. Wires bidirectional faction relationships, syncs NPC locations. validate_initial_state() checks cross-references
- `engine/sim/npc_generator.py` (~250 lines) — Procedural NPC generation: 30+30 name pool, 11 species with mid-Atlantic population weights (81% human, 19% metahuman), tier pyramid (T1-T10), 7 domain fractions, personality traits, voice templates. Batch generation with uniqueness enforcement
- `engine/character_creation/character_factory.py` (~230 lines) — CreationState dataclass (accumulates 10 scenes of deltas), CharacterFactory (applies scene results, finalizes to CharacterSheet with die-size snapping)
- `engine/character_creation/session_zero.py` (~190 lines) — SessionZero orchestrator with InputSource/NarratorSink protocols. FixedInputSource + MockNarratorSink for testing
- `engine/character_creation/scenes.py` (~420 lines) — Scenes 0-4: Opening (name+age), Occupation (12 options per spec §3.1), Relationships (6 archetypes with NPC generation), Location (8 regions × 8 circumstances), Concern (8 options)
- `engine/character_creation/manifestation.py` (~240 lines) — Scene 5: circumstance-weighted category draw (8 tilts × 7 categories), session-zero tier pyramid (T1-T4), background modifiers, secondary category (55%), 42 starter power templates
- `engine/character_creation/year_one.py` (~340 lines) — Scenes 6-9: First Weeks (4 options), Faction Encounter (8 region→faction mappings, 4 response types), Critical Incident (3 branches × 4 options, state-driven selection), Settling (5 options, species-filtered)

**Tests:** 598 total (595 pass, 3 skipped)
- `test_content_loading.py` — 27 integration tests (all bible content loads, cross-references validate)
- `test_initial_state.py` — 12 integration tests (world state, validation, 30-day tick)
- `test_npc_generator.py` — 22 unit tests (species/tier distribution, constraints, determinism)
- `test_session_zero_scenes.py` — 26 unit tests (scenes 0-4, eligibility, deltas, full sequence)
- `test_manifestation.py` — 11 unit tests (category/tier rolls, circumstance tilts, powers)
- `test_year_one.py` — 20 unit tests (scenes 6-9, incident type selection, faction encounters)
- `test_session_zero.py` — 15 integration tests (5 seeds → 5 characters, choices recorded, attributes valid)
- `test_content_sim_integration.py` — 3 integration tests (bible→sim→combat pipeline)

**Exit criteria verified:**
1. All 22 factions, 64 NPCs, 40+ locations, 8+ clocks load from YAML
2. Cross-references validate within tolerance (NPC factions, NPC locations)
3. 5 session zeros produce varied characters (different categories, tiers)
4. Generated characters enter combat engine successfully
5. Full bible world ticks 30 days without errors
6. All 598 tests pass

## Entry 5: Phase 5 — Runtime Integration and Narrator

**Date:** Phase 5 complete

**Deliverables:**
- `engine/runtime/configuration.py` (~85 lines) — GameConfig dataclass (12 fields), load_config/save_config from key=value files
- `engine/runtime/error_handling.py` (~115 lines) — Exception hierarchy: EmergenceError → RecoverableError(1), FatalError(2), SaveIntegrityError(3), NarratorProtocolError(4), EngineInternalError(5). crash_shutdown() with emergency save
- `engine/runtime/input_handler.py` (~100 lines) — InputHandler: parses meta commands (/save, /quit, /status, /help, /inventory, /map, /character, /history), numeric/letter choices, freeform text → Intent
- `engine/runtime/modes.py` (~130 lines) — ModeManager with TRANSITION_TABLE: SESSION_ZERO→FRAMING→SIM↔COMBAT, GAME_OVER→SESSION_ZERO. StubModeHandler for testing
- `engine/runtime/main.py` (~300 lines) — GameState dataclass, 11-step launch sequence, main_session_loop, mode dispatch (session_zero, framing, sim, combat, game_over), LaunchLock, autosave, clean/crash shutdown
- `emergence/__main__.py` (~170 lines) — CLI entry point: play/new/list/inspect/migrate/help subcommands, --save-root, --config, --log-level, --seed, --dry-run, --no-color
- `engine/narrator/queue.py` (~90 lines) — NarrationChannel protocol, MockNarrationQueue (immediate), FileNarrationQueue (JSONL + seq)
- `engine/narrator/payloads.py` (~150 lines) — 8 payload builders: combat_turn, scene_framing, situation, dialogue, character_creation, transition, death, time_skip
- `engine/narrator/prompts.py` (~120 lines) — PROMPT_TEMPLATES dict (8 templates), get_prompt(), format_prompt()
- `engine/narrator/validation.py` (~70 lines) — validate_narration(): length bounds per scene type, forbidden patterns, payload constraints
- `engine/persistence/save.py` (~95 lines) — SaveManager: atomic writes (temp-and-rename), leaves-first (entities before world.json as save-complete marker), 5s throttle, lightweight_save for combat rounds
- `engine/persistence/load.py` (~140 lines) — LoadManager: classify() (FRESH/PARTIAL/VALID/CORRUPT/VERSION_MISMATCH), load_save() → LoadResult
- `engine/persistence/migration.py` (~130 lines) — SaveMigrator: needs_migration(), get_save_version(), migrate(dry_run) with atomic file rewrite
- `engine/persistence/multi_character.py` (~120 lines) — MultiCharacterManager: archive_character(), list_characters(), switch_character()
- `prompts/*.md` — 8 prompt template reference files

**Tests:** 737 total (734 pass, 3 skipped)
- `test_runtime_config.py` — 19 unit tests (config load/save, defaults, overrides)
- `test_narrator.py` — 21 unit tests (queue, payloads, prompts, validation)
- `test_input_handler.py` — 24 unit tests (meta commands, choices, freeform, aliases)
- `test_modes.py` — 17 unit tests (transitions, forbidden paths, history, run_cycle)
- `test_save_load.py` — 28 integration tests (save/load/migration/multi-character)
- `test_full_session.py` — 18 integration tests (end-to-end, CLI commands, save round-trip)
- `test_mode_transitions.py` — 12 integration tests (all valid paths, sim↔combat, forbidden)

**Exit criteria verified:**
1. Full session: launch → session zero → sim → save → quit works in mock mode
2. Save/load round-trip preserves all state (world, player, factions, NPCs, locations, clocks)
3. All 5 save classifications detected correctly (FRESH, PARTIAL, VALID, CORRUPT, VERSION_MISMATCH)
4. Mode transitions enforce valid paths, reject forbidden transitions
5. CLI subcommands (play, list, inspect, migrate, help) all functional
6. Character archival and multi-character switch works
7. All 737 tests pass

## Entry 6: Phase 6 — Progression and Extended Smoke Test

**Date:** Phase 6 complete

**Deliverables:**
- `engine/progression/tactical.py` (~120 lines) — TacticalProgression: power use tracking, strengthening marks at 25/75/200/500/1200 (doubled at tier ceiling), category bonuses at 100/400/1000/2500
- `engine/progression/breakthrough.py` (~300 lines) — BreakthroughEngine: 8 trigger conditions (near-death, mentorship, eldritch exposure, substance, ritual, traumatic loss, sustained crisis, sacrifice), resolution with tier increment and mark selection. 24 breakthrough marks (P1-P4, M1-M4, E1-E4, B1-B4, A1-A4, T1-T4, X1-X4, U1-U3) with specific mechanical effects
- `engine/progression/skills.py` (~180 lines) — SkillProgression: 32 skills in 7 clusters, thresholds (5/20/60/150/350/750/1500/3000/7000/15000), 9 synergy pairs, 5 prerequisite rules, skill checks with untrained penalty
- `engine/progression/relationships.py` (~180 lines) — RelationshipProgression: standing -3..+3, trust 0-5, state machine (neutral→cordial→warm→loyal, cold→antagonist→blood_feud), betrayal lock (60 days), absence decay (40%/month positive, 30%/month negative drift), NPC death handling
- `engine/progression/factions.py` (~120 lines) — FactionProgression: standing -3..+3, reach 0-5, heat (permanent vs decayable), yearly decay (50% standing, 1/3yr reach, 1/yr heat)
- `engine/progression/resources.py` (~130 lines) — ResourceProgression: 7 types, 6 wealth sub-types with per-type decay rates (cu stable, scrip -5%/yr, grain -10%/mo), follower/holding upkeep
- `engine/progression/aging.py` (~180 lines) — AgingEngine: 7 age categories, attribute degradation at 40/50/60, death roll past 60 (1d20 + modifiers vs DC 8), species variations, medical care bonus
- `engine/progression/family.py` (~170 lines) — FamilyEngine: fertility by age, child manifestation during puberty, descendant creation with resource/relationship inheritance, lineage tracking
- `engine/progression/corruption.py` (~190 lines) — CorruptionEngine: 0-6 scale, segment-specific effects, transformation at 6 (character becomes NPC), monthly will check at 5, reversibility rules (1-2 full, 3-4 partial, 5 near-irreversible, 6 irreversible), source tracking
- `engine/progression/arcs.py` (~160 lines) — ArcTracker: goal completion/milestones, relationship climax (loyal, blood feud, death), faction allegiance/enmity, corruption visibility/transformation, tier advancement

**Tests:** 898 total (895 pass, 3 skipped)
- `test_tactical_progression.py` — 15 unit tests (marks, thresholds, ceiling, category)
- `test_breakthrough.py` — 28 unit tests (8 triggers, resolution, application, mark catalog)
- `test_skills.py` — 14 unit tests (proficiency, prerequisites, synergies, checks)
- `test_relationships.py` — 20 unit tests (standing, trust, states, betrayal, decay, death)
- `test_faction_progression.py` — 10 unit tests (standing, reach, heat, decay)
- `test_resources.py` — 13 unit tests (add, spend, decay, upkeep)
- `test_aging.py` — 14 unit tests (categories, degradation, death roll)
- `test_family.py` — 10 unit tests (birth, aging, manifestation, descendant, inheritance)
- `test_corruption.py` — 15 unit tests (segments, effects, will check, reversal)
- `test_arcs.py` — 12 unit tests (goals, relationships, factions, corruption, tier)
- `test_long_game.py` — 4 scenario tests (5-year sim, aging to death, descendant, serialization)
- `test_progression.py` — 6 integration tests (combat marks, standing, save/load persistence)

**Exit criteria verified:**
1. All progression mechanics work: power marks, skills, relationships, factions, resources
2. 5-year simulated game runs without crashes or schema violations
3. Aging → death → descendant continuation works
4. Multiple sessions on same character work (progression persists through save/load)
5. All progression state is JSON-serializable and round-trips correctly
6. All 898 tests pass
