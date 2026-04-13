# Workflow State — Emergence Build

## Current Phase: COMPLETE — All 7 Phases Done

## Phase 7 Progress — COMPLETE

| Step | Description | Status |
|------|-------------|--------|
| 7.1 | PLAY.md | done |
| 7.2 | HANDOFF.md | done |
| 7.3 | README Update + Docstrings | done |
| 7.4 | Test Coverage + Final Build Log | done |

## Phase 6 Progress — COMPLETE

| Step | Description | Status |
|------|-------------|--------|
| 6.1 | Tactical Progression | done |
| 6.2 | Breakthrough Mechanics | done |
| 6.3 | Skills + Relationships | done |
| 6.4 | Factions + Resources | done |
| 6.5 | Aging + Family + Corruption | done |
| 6.6 | Narrative Arcs | done |
| 6.7 | Extended Smoke Test | done |
| 6.8 | Build Log Update | done |

## Phase 5 Progress — COMPLETE

| Step | Description | Status |
|------|-------------|--------|
| 5.1 | Configuration + Error Handling | done |
| 5.2 | Narrator Queue + Payloads | done |
| 5.3 | Persistence Layer | done |
| 5.4 | Input Handler + Mode System | done |
| 5.5 | Entry Point + Session Loop | done |
| 5.6 | Full Session Integration | done |
| 5.7 | Refinement + Build Log | done |

## Phase 4 Progress — COMPLETE

| Step | Description | Status |
|------|-------------|--------|
| 4.1 | Content Loader | done |
| 4.2 | Initial World State | done |
| 4.3 | NPC Generator | done |
| 4.4 | Character Creation Core | done |
| 4.5 | Scenes 0-4 (Pre-Onset) | done |
| 4.6 | Scenes 5-9 (Manifestation + Year One) | done |
| 4.7 | Session Zero Integration | done |
| 4.8 | Refinement + Build Log | done |

## Phase 3 Progress — COMPLETE

| Step | Description | Status |
|------|-------------|--------|
| 3.1 | YAML Parser + Sim Skeleton | done |
| 3.2 | Clock System | done |
| 3.3 | Faction Logic | done |
| 3.4 | NPC Behavior | done |
| 3.5 | Location Dynamics | done |
| 3.6 | Tick Engine + Situation Generator | done |
| 3.7 | Abstract Combat + Encounter Generator | done |
| 3.8 | Player Actions + Context Management + Persistence | done |
| 3.9 | Integration — 365-Day Smoke + Handoff | done |
| 3.10 | Refinement + Build Log | done |

## Completed Phases

- Phase 0: Repository organization
- Phase 1: Schema scaffolding (137 tests)
- Phase 2: Combat engine (248 tests, 48 powers, 30 enemies, 12 encounters)
- Phase 2.5: Combat spec audit fixes (275 tests after fixes)
- Phase 3: Simulation engine core (462 tests — 11 engine files, 10 test files, 1 helper)
- Phase 4: Content integration + character creation (598 tests — 8 engine files, 8 test files)
- Phase 5: Runtime integration + narrator (737 tests — 14 engine files, 7 test files, 8 prompt files)
- Phase 6: Progression + extended smoke test (898 tests — 10 engine files, 12 test files)
- Phase 7: Polish, documentation, and handoff (PLAY.md, HANDOFF.md, README update, docstrings, final build log)

## Test Summary

- Total: 898 tests (895 pass, 3 skipped)
- Phase 1 tests: test_schemas (21), test_validation (116)
- Phase 2 tests: test_resolution (18), test_damage (25), test_statuses (20), test_ai (13), test_verbs (15), test_data_loader (13), test_combat_scenarios (6), test_combat_fixes (26)
- Phase 3 tests: test_yaml_parser (41), test_clocks (30), test_faction_logic (11), test_npc_behavior (18), test_location_dynamics (13), test_tick_engine (8), test_situations (16), test_abstract_combat (8), test_encounter_generator (11), test_player_actions (18), test_world_tick (7), test_encounter_generation (3), test_sim_combat_handoff (3)
- Phase 4 tests: test_content_loading (27), test_initial_state (12), test_npc_generator (22), test_session_zero_scenes (26), test_manifestation (11), test_year_one (20), test_session_zero (15), test_content_sim_integration (3)
- Phase 5 tests: test_runtime_config (19), test_narrator (21), test_input_handler (24), test_modes (17), test_save_load (28), test_full_session (18), test_mode_transitions (12)
- Phase 6 tests: test_tactical_progression (15), test_breakthrough (28), test_skills (14), test_relationships (20), test_faction_progression (10), test_resources (13), test_aging (14), test_family (10), test_corruption (15), test_arcs (12), test_long_game (4), test_progression (6)

## Runtime Modules

| Module | Purpose |
|--------|---------|
| configuration | GameConfig dataclass + load/save |
| error_handling | Exception hierarchy (5 exit codes) + crash_shutdown |
| input_handler | Meta commands, choices, freeform → Intent |
| modes | ModeManager with transition table |
| main | Launch sequence (11 steps), session loop, mode dispatch |

## Narrator Modules

| Module | Purpose |
|--------|---------|
| queue | NarrationChannel protocol, Mock + File queues |
| payloads | 8 payload builders for all scene types |
| prompts | Prompt templates + format_prompt |
| validation | Length bounds, forbidden patterns |

## Persistence Modules

| Module | Purpose |
|--------|---------|
| save | Atomic writes, leaves-first, throttle |
| load | 5-state classification, LoadResult |
| migration | SaveMigrator with dry-run |
| multi_character | Archive, list, switch characters |

## Sim Engine Modules

| Module | Purpose |
|--------|---------|
| yaml_parser | Stdlib-only YAML subset parser |
| clocks | Macro clock advancement engine |
| faction_logic | Faction decision system (~1 action/week) |
| npc_behavior | NPC schedule, goals, memory, relationships |
| location_dynamics | Economic transitions, migration, danger, opportunities |
| tick_engine | Daily/seasonal tick orchestrator |
| situation_generator | Player-facing situation builder |
| abstract_combat | Off-screen faction/NPC combat |
| encounter_generator | EncounterSpec builder from situation |
| player_actions | Resolve player choices |
| context_management | Compact state for narrator |
| persistence | Dirty-flag tracker |

## Character Creation Modules

| Module | Purpose |
|--------|---------|
| content_loader | Loads setting bible YAML into schema objects |
| initial_state | Builds T+1 world state from loaded content |
| npc_generator | Procedural NPC generation with species/tier distributions |
| character_factory | Accumulates scene deltas, finalizes CharacterSheet |
| session_zero | 10-scene orchestrator with InputSource/NarratorSink protocols |
| scenes | Pre-onset scenes 0-4 (opening, occupation, relationships, location, concern) |
| manifestation | Scene 5: circumstance-weighted power category and tier rolls |
| year_one | Scenes 6-9 (first weeks, faction encounter, critical incident, settling) |

## Progression Modules

| Module | Purpose |
|--------|---------|
| tactical | Power use tracking, strengthening marks (5 thresholds) |
| breakthrough | 8 trigger conditions, resolution, 24 marks |
| skills | 32 skills, 10 proficiency levels, synergies, prerequisites |
| relationships | Standing -3..+3, trust 0-5, state machine, decay |
| factions | Faction standing/reach/heat, yearly decay |
| resources | 7 types, wealth decay, follower/holding upkeep |
| aging | 7 age categories, attribute degradation, death roll |
| family | Fertility, child manifestation, descendant creation |
| corruption | 0-6 scale, segment effects, transformation, reversal |
| arcs | Goal/relationship/faction/corruption/tier milestones |

## Last Commit Context

Phase 6 complete. All progression mechanics implemented and tested. 898 tests passing. Extended smoke test: 5-year simulation, aging to death + descendant continuation.
