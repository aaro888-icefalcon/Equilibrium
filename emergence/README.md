# Emergence

A solo AI-narrated tactical RPG and life simulation set one year after the Onset -- a catastrophic event that killed most of humanity and left survivors with supernatural abilities.

## Current State

**All 7 build phases complete. 898 tests passing (895 pass, 3 skipped).**

| Phase | Description | Tests |
|-------|-------------|-------|
| 1 | Schema scaffolding + validation | 137 |
| 2 | Combat engine (48 powers, 30 enemies) | 275 |
| 3 | Simulation engine (tick, factions, NPCs, clocks) | 462 |
| 4 | Content integration + character creation | 598 |
| 5 | Runtime, narrator, persistence | 737 |
| 6 | Progression (10 systems) + extended smoke test | 898 |
| 7 | Documentation + polish | 898 |

## Quick Start

```bash
python -m emergence play        # Start or resume
python -m emergence new         # New character
python -m emergence list        # List saves
python -m emergence --help      # All options
```

Requires Python 3.10+. No external dependencies.

## Documentation

- **[PLAY.md](PLAY.md)** -- Player-facing instructions, commands, and tips
- **[HANDOFF.md](HANDOFF.md)** -- Technical architecture, module reference, extension guide
- **[notes/build-log.md](notes/build-log.md)** -- Complete build history

## Running Tests

```bash
python -m unittest discover -s emergence/tests -v
```

---

# Build Orchestration (Original Prompt)

You are Codex. You will build a complete, playable, AAA-quality vertical slice of Emergence — a solo AI-narrated tactical RPG and life simulation set in a post-collapse Earth where most of humanity manifested supernatural abilities one year ago.

The user is not actively supervising. You are working autonomously across an extended session. Your job is to be a rigorous, restrained, agentic implementer who follows the specifications precisely while iterating, testing, integrating, and refining your own work.

You have a flat collection of specifications and content files. Your first action is to organize them. Then you build, in iterative phases, with explicit testing and integration verification at each phase. The end result is a polished CLI-based game with rigorous game systems, deep simulation, and consistent narration.

## Your operating principles

1. The specifications are complete game designs. They contain every mechanic, formula, ability, enemy, encounter, and procedure you need. You do not need to make game design decisions. Your job is faithful, rigorous implementation. If you find yourself wanting to make a design decision, stop — re-read the relevant specification, find the answer there.

2. Build iteratively, not monolithically. Each phase produces a working artifact that gets tested before the next phase begins. Each phase is followed by an integration test that verifies the new code works with everything built before it.

3. Test everything. Every module gets unit tests. Every integration point gets integration tests. Every game system gets scenario tests. The build log records test results at every phase.

4. Iterate on quality. After implementing a phase, you do an explicit refinement pass on your own work. You identify weaknesses, gaps, and rough edges. You fix them. You do this before declaring the phase complete.

5. Integrate continuously. The combat engine, simulation engine, runtime, and content layers must work together. After each phase, you verify that the new work integrates cleanly with prior phases. Integration failures are bugs to fix immediately, not deferrals.

6. Document continuously. Every module has a clear docstring. Every non-trivial procedure has inline comments. The build log records what you did and why. The handoff document at the end is comprehensive enough that the user can understand and modify the code.

7. Stay within the specifications. If a specification is silent on something you encounter, log it to notes/design-questions.md and use the most defensible interpretation. Do not invent new mechanics, content, or systems beyond what specifications direct.

8. The setting bible is authoritative for world content. Powers, factions, NPCs, locations, history come from the bible. Implementation details come from the specifications. You do not reinvent content.

## Your first action: organize the repository

The files you received are flat. Read README.md, design-brief.md, and interface-spec.md first. Then read the eight specification files. Then read the setting bible files. After reading, organize the repository into this structure:

```
emergence/
  README.md
  design-brief.md
  interface-spec.md
  PLAY.md (you create at the end)
  HANDOFF.md (you create at the end)
  specs/
    combat-spec.md
    sim-architecture.md
    sim-content-integration.md
    runtime-architecture.md
    prompt-management.md
    state-persistence.md
    character-creation.md
    progression.md
  setting/
    [all 15 setting bible files: constants.yaml, clocks.yaml, trajectory.md,
     factions.yaml, npcs.yaml, locations.yaml, species.md, powers.md,
     eldritch.md, timeline.yaml, timeline_narrative.md, narration.md,
     geography.md, primer.md, gm-primer.md]
  engine/
    schemas/        (Phase 1)
    combat/         (Phase 2)
    sim/            (Phase 3, 4)
    runtime/        (Phase 5)
    narrator/       (Phase 5)
    persistence/    (Phase 5)
    progression/    (Phase 6)
  data/
    powers/         (Phase 2 — power library from spec)
    enemies/        (Phase 2 — enemy templates from spec)
    encounters/     (Phase 2 — sample encounters from spec)
  prompts/          (Phase 5 — narrator prompt templates)
  tests/
    unit/
    integration/
    scenarios/
    output/
  notes/
    build-log.md
    deferred.md
    design-questions.md
    integration-issues.md
  runtime/          (created by game at runtime)
  saves/            (created by game at runtime)
```

Move uploaded files into appropriate directories. Do not rename. Create empty notes files with headers. After organization, write the first build log entry confirming structure and proceed to Phase 1.

## Build phases

Each phase has a goal, deliverables, exit criteria, integration requirements, and an explicit refinement pass.

### Phase 1 — Schema scaffolding and validation framework

**Goal:** Implement all interface schemas as Python dataclasses with serialization, validation, and round-trip testing.

**Build:**

- `engine/schemas/character.py` — Character Sheet dataclass with full field set per interface-spec.md
- `engine/schemas/combatant.py` — Combatant dataclass extending Character
- `engine/schemas/encounter.py` — Encounter Spec, Combat Outcome, Action dataclasses
- `engine/schemas/narrator.py` — Narrator Payload dataclass
- `engine/schemas/world.py` — World State, Faction, NPC, Location, Clock, Tick Event, Situation dataclasses
- `engine/schemas/content.py` — Power, Enemy Template, Status, Affinity dataclasses
- `engine/schemas/serialization.py` — JSON serialization helpers, schema versioning, migration framework
- `engine/schemas/validation.py` — Validation functions for each schema
- `tests/unit/test_schemas.py` — Round-trip serialization tests for every schema
- `tests/unit/test_validation.py` — Validation tests including failure cases

**Exit criteria:**

- Every schema serializes and deserializes without information loss
- Every validation function correctly identifies valid and invalid inputs
- All unit tests pass

**Integration verification:**

- All schemas can be instantiated together without import conflicts
- Serialization of a complete world state (all entity types) round-trips cleanly

**Refinement pass:**

After exit criteria met, review the schemas for clarity, consistency, and ergonomic use. Improve naming, add helper methods that will be needed in later phases, ensure all field types are precisely specified.

**Build log entry:** files created, line counts, test results, refinements made.

### Phase 2 — Combat engine implementation

**Goal:** Implement the complete combat engine per combat-spec.md, with all powers, enemies, statuses, affinities, exposure, AI, and narration payload generation.

**Build:**

- `engine/combat/resolution.py` — Attribute die resolution per spec Section 1
- `engine/combat/turn_loop.py` — Turn structure and verb resolution per Sections 3-4
- `engine/combat/statuses.py` — All seven statuses per Section 6
- `engine/combat/affinities.py` — Affinity system per Section 7
- `engine/combat/exposure.py` — Exposure mechanic per Section 8
- `engine/combat/enemy_ai.py` — All five AI profiles per Section 9
- `engine/combat/damage.py` — Damage and harm system per Section 10
- `engine/combat/registers.py` — Three combat register modifications per Section 11
- `engine/combat/encounter_runner.py` — Top-level combat loop, encounter execution, outcome generation
- `engine/combat/narrator_payload.py` — Combat narration payload construction per Section 14
- `data/powers/*.json` — All powers from spec Section 5 (42+ powers)
- `data/enemies/*.json` — All enemy templates from spec Section 12 (30+ enemies)
- `data/encounters/*.json` — Sample encounters from spec Section 13 (12+ encounters)
- `tests/unit/test_resolution.py` — Resolution math tests with probability validation per spec Section 16
- `tests/unit/test_statuses.py` — All status interactions per spec interaction matrix
- `tests/unit/test_powers.py` — Each power's mechanical effect verified
- `tests/unit/test_enemies.py` — Each enemy's stats and behavior verified
- `tests/integration/test_combat_scenarios.py` — All 15 test scenarios from spec Section 16
- `tests/scenarios/test_full_combats.py` — Complete combats across all three registers

**Exit criteria:**

- All powers from spec implemented and tested
- All enemy templates from spec implemented and tested
- All 15 test scenarios pass with expected outcomes
- Probability validation tests confirm resolution math matches spec targets
- Sample combats run to completion in all three registers

**Integration verification:**

- Combat engine reads encounter specs conforming to schemas from Phase 1
- Combat engine produces combat outcomes conforming to schemas from Phase 1
- Combat narration payloads conform to schemas from Phase 1
- Engine handles malformed inputs gracefully

**Refinement pass:**

Run extensive playtesting (you simulate as both player and engine):
- Run 50 simulated combats with varied builds and encounters
- Identify any combat that feels broken (drags, ends instantly, has no real choices, has dominant strategy)
- Fix identified issues
- Document any encountered gaps in spec coverage to notes/design-questions.md

**Build log entry:** complete report.

### Phase 3 — Simulation engine core

**Goal:** Implement the complete simulation engine per sim-architecture.md, including tick engine, faction logic, NPC behavior, location dynamics, clocks, situation generator, abstract combat, and persistence.

**Build:**

- `engine/sim/tick_engine.py` — World tick and local tick procedures per spec Section 1
- `engine/sim/faction_logic.py` — Complete faction decision system per spec Section 2
- `engine/sim/npc_behavior.py` — NPC schedules, goals, relationships, memory per Section 3
- `engine/sim/location_dynamics.py` — Location updates per Section 4
- `engine/sim/clocks.py` — Macro clock advancement per Section 5
- `engine/sim/situation_generator.py` — Situation generation per Section 6
- `engine/sim/abstract_combat.py` — Off-screen combat resolution per Section 7
- `engine/sim/persistence.py` — State serialization per Section 8
- `engine/sim/context_management.py` — State compaction per Section 9
- `engine/sim/player_actions.py` — Action resolution per Section 10
- `engine/sim/encounter_generator.py` — Encounter spec construction per Section 11
- `tests/unit/test_tick_engine.py` — Tick procedures
- `tests/unit/test_faction_decisions.py` — Faction decision logic with worked examples from spec
- `tests/unit/test_npc_behavior.py` — NPC behavior verified
- `tests/unit/test_clocks.py` — Clock advancement and interactions
- `tests/unit/test_situations.py` — Situation generation
- `tests/unit/test_abstract_combat.py` — Abstract combat outcomes
- `tests/integration/test_world_tick.py` — Full world tick with synthetic content
- `tests/integration/test_encounter_generation.py` — Encounter generation across registers

**Exit criteria:**

- All sim engine modules implemented per spec
- Synthetic test content (3 factions, 5 NPCs, 5 locations, all 8 clocks) ticks cleanly through 365 simulated days
- Encounter generation produces valid encounter specs across all three registers
- All unit and integration tests pass

**Integration verification:**

- Sim engine produces encounter specs that the combat engine from Phase 2 can run
- Combat outcomes from Phase 2's engine are correctly ingested by the sim engine
- The full handoff cycle (sim generates encounter → combat resolves → sim ingests outcome) works end to end with synthetic content

**Refinement pass:**

Run 30 days of simulated time with synthetic content, watching for:
- Faction decisions that don't make sense
- NPC behavior that seems disconnected from goals
- Clocks advancing too fast or too slow
- Situations that lack tension or specificity

Fix identified issues. Document gaps.

**Build log entry:** complete.

### Phase 4 — Content integration and character creation

**Goal:** Load the setting bible content into the simulation per sim-content-integration.md. Implement session zero per character-creation.md.

**Build:**

- `engine/sim/content_loader.py` — Loaders for factions, NPCs, locations, timeline, clocks
- `engine/sim/initial_state.py` — T+1 initial world state construction per sim-content-integration spec Section 7
- `engine/sim/npc_generator.py` — Unnamed NPC generation per spec Section 3
- `engine/character_creation/session_zero.py` — Complete session zero flow per character-creation spec
- `engine/character_creation/scenes.py` — Each session zero scene as specified
- `engine/character_creation/manifestation.py` — Manifestation mechanic per spec Section 4
- `engine/character_creation/year_one.py` — Year 1 scenes per spec Section 5
- `engine/character_creation/character_factory.py` — Character sheet construction per Section 7
- `tests/integration/test_content_loading.py` — All bible content loads cleanly
- `tests/integration/test_initial_state.py` — T+1 state matches spec
- `tests/integration/test_session_zero.py` — Multiple complete session zero runs producing varied characters
- `tests/integration/test_character_validity.py` — Generated characters conform to schemas

**Exit criteria:**

- All 22 factions from bible load correctly
- All 50 NPCs from bible load correctly
- All locations from bible load correctly
- T+1 initial world state matches spec
- Session zero produces complete, valid character sheets
- Multiple session zero runs produce noticeably different characters

**Integration verification:**

- Loaded world state can be ticked by the Phase 3 sim engine without errors
- Generated characters can be placed in the world and the sim handles them
- Generated characters can enter combat via the Phase 2 engine and complete encounters

**Refinement pass:**

- Run 5 complete session zero playthroughs with different choices
- Verify character variation
- Identify any session zero scenes that feel mechanical, generic, or off-tone
- Improve narration and choice presentation in those scenes
- Verify the loaded world feels grounded when ticked

**Build log entry:** complete.

### Phase 5 — Runtime integration and narrator

**Goal:** Wire all subsystems into a complete runtime per runtime-architecture.md, prompt-management.md, and state-persistence.md. Implement the narrator queue pattern.

**Build:**

- `engine/runtime/main.py` — Entry point and main session loop per runtime-architecture Section 1-2
- `engine/runtime/modes.py` — All mode handling per Section 3
- `engine/runtime/input_handler.py` — Structured and freeform input parsing per Section 5
- `engine/runtime/error_handling.py` — Error categories and recovery per Section 6
- `engine/runtime/configuration.py` — Configuration system per Section 8
- `engine/narrator/queue.py` — Narration queue per prompt-management Section 5
- `engine/narrator/prompts.py` — Complete prompt library per prompt-management Section 2
- `engine/narrator/validation.py` — Narration validation per Section 7
- `engine/narrator/payloads.py` — Payload construction helpers
- `engine/persistence/save.py` — Save procedure per state-persistence Section 1-2
- `engine/persistence/load.py` — Load procedure per Section 3
- `engine/persistence/migration.py` — Migration framework per Section 4
- `engine/persistence/multi_character.py` — Multi-character world handling per Section 5
- `prompts/*.md` — All narrator prompt templates as files
- `tests/integration/test_full_session.py` — Complete session from launch through save
- `tests/integration/test_save_load.py` — Save and load round-trip tests
- `tests/integration/test_mode_transitions.py` — All mode transitions work cleanly

**Exit criteria:**

- A full session runs from launch through character creation, into sim mode, triggers an encounter, runs combat, returns to sim, saves, and exits cleanly
- The save can be loaded and play resumes correctly
- All mode transitions work
- Narrator produces grounded prose for all scene types
- Error handling catches and recovers from injected failures

**Integration verification:**

- The complete stack works end to end without crashes
- Combat outcomes are properly persisted in saves
- Sim state changes are properly persisted in saves
- A character created in one session can be loaded and continued in another

**Refinement pass:**

- Run 5 complete sessions from launch to save, each with different player choices
- Identify any rough edges in mode transitions, input parsing, narration quality, save behavior
- Fix identified issues
- Verify narration stays in register across all scene types

**Build log entry:** complete.

### Phase 6 — Progression and end-to-end smoke test

**Goal:** Implement progression mechanics per progression.md. Run extended smoke testing to verify the game holds together over decades of in-world time.

**Build:**

- `engine/progression/tactical.py` — Tactical progression per progression spec Section 1
- `engine/progression/breakthrough.py` — Breakthrough mechanics per Section 2
- `engine/progression/skills.py` — Skill progression per Section 3
- `engine/progression/relationships.py` — Relationship progression per Section 4
- `engine/progression/factions.py` — Faction standing progression per Section 5
- `engine/progression/resources.py` — Resource progression per Section 6
- `engine/progression/aging.py` — Aging procedures per Section 7
- `engine/progression/family.py` — Family and lineage per Section 8
- `engine/progression/corruption.py` — Corruption mechanics per Section 9
- `engine/progression/arcs.py` — Narrative arc tracking per Section 10
- `tests/integration/test_progression.py` — Progression mechanics verified
- `tests/scenarios/test_long_game.py` — Extended play scenarios

**Exit criteria:**

- All progression mechanics implemented and tested
- A character can play for 30 simulated minutes of real time without breaking
- Multiple sessions across the same character work
- Character aging works
- Character death from old age works
- Continuation as descendant works

**Integration verification:**

- Progression integrates with combat (powers strengthen through combat use)
- Progression integrates with sim (relationships develop through sim play)
- Progression state persists across sessions

**Refinement pass:**

- Run a long-form simulated game: one character through 5 in-world years of play
- Document the experience in detail
- Identify any progression that feels arbitrary, broken, or meaningless
- Fix identified issues

**Build log entry:** complete.

### Phase 7 — Polish, documentation, and handoff

**Goal:** Final polish pass, comprehensive documentation, and handoff materials.

**Build:**

- `PLAY.md` — Complete player-facing instructions for running and playing the game
- `HANDOFF.md` — Comprehensive technical handoff covering architecture, what works, what's known-broken, what's deferred, where to look for what
- README updates with current state of the build
- Final pass on all engine code: docstrings, comments, consistency
- Final pass on tests: coverage gaps addressed
- Final entry in `notes/build-log.md` summarizing the entire build

**Exit criteria:**

- PLAY.md is complete and accurate
- HANDOFF.md is comprehensive
- All known issues documented
- The game runs cleanly when launched per PLAY.md instructions

## Discipline rules (re-read between every phase)

- Phase exit criteria are non-negotiable. If you cannot meet them, stop and write a failure report. Do not paper over.
- The refinement pass is mandatory at every phase. It is not optional.
- If you find yourself wanting to make a design decision, the design exists in a specification — find it. If it genuinely is not there, log to design-questions.md and use the most defensible interpretation.
- Defer additions you'd like to make to deferred.md. Do not implement them.
- After every phase, append to build-log.md: files created, line counts, test results, refinements made, integration verifications, deferrals, design questions raised.
- Standard library only. No pip installs.
- Narration is produced by you (Codex) reading prompts and generating prose during the build process for testing, and during runtime for play. No external API calls.
- Test continuously. Integrate continuously. Refine continuously.

## How to handle stuck states

If you encounter a situation where you cannot proceed:

1. Determine whether this is a specification gap (the spec doesn't say what to do) or an implementation problem (you can't figure out how to do what the spec says).

2. For specification gaps: log to design-questions.md, choose the most defensible interpretation consistent with the design brief, document your choice in the build log, and proceed.

3. For implementation problems: try at least three different approaches before declaring a stuck state. Document each attempt in integration-issues.md. If still stuck, write a detailed failure report to build-log.md including what you tried, what failed, and what specifically you need to proceed.

4. Never silently fail. Never paper over. Visible failure is required.

## Success criterion

The user can run `python -m emergence.runtime.main` (or equivalent entry point per your runtime architecture spec), go through session zero, play the game, save, quit, resume later. The game feels like the setting. Combat is tactical and varied. The sim produces specific grounded situations. The narrator stays in register. State persists correctly. Multiple characters in the same world inherit each other's effects.

The vertical slice should provide at least 5 hours of compelling play before the seams show.

## Begin

Start by reading design-brief.md and interface-spec.md fully. Then read all eight specification documents fully. Then read the setting bible files. Then organize the repository per Phase 1 instructions. Then proceed through phases in order, with refinement and integration verification at each phase boundary.

Do not begin Phase 1 implementation until you have read all specifications and confirmed the repository organization in build-log.md.

Re-read these discipline rules between every phase.
