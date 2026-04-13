# Emergence -- Technical Handoff

This document is the comprehensive technical reference for the Emergence codebase. It covers architecture, module inventory, key classes and functions, test coverage, known issues, and how to extend the game.

---

## Architecture Overview

Emergence is a CLI tactical RPG built in Python 3.10+ using only the standard library. The architecture has seven layers, built in sequence:

```
Layer 7: Progression    — Power marks, skills, relationships, aging, corruption
Layer 6: Runtime        — Entry point, session loop, mode dispatch, input handling
Layer 5: Narrator       — Prompt templates, payload construction, narration queue
Layer 4: Persistence    — Save/load, migration, multi-character management
Layer 3: Content        — YAML loader, initial world state, character creation
Layer 2: Simulation     — Tick engine, factions, NPCs, locations, clocks, situations
Layer 1: Combat         — Turn-based encounters, powers, enemies, AI, registers
Layer 0: Schemas        — Dataclasses, validation, serialization
```

Each layer depends only on layers below it. The runtime (Layer 6) orchestrates everything.

### Directory Structure

```
emergence/
  __main__.py              — CLI entry point (170 lines)
  PLAY.md                  — Player-facing instructions
  HANDOFF.md               — This document
  README.md                — Build orchestration notes

  engine/
    schemas/               — Data structures (8 files, ~2,600 lines)
      character.py         — CharacterSheet, Attributes, Harm, Species enum
      combatant.py         — Combatant, AiProfile enum
      encounter.py         — EncounterSpec, CombatOutcome, Action, 8 enums
      narrator.py          — NarratorPayload, SceneType enum
      world.py             — WorldState, Faction, NPC, Location, Clock, Situation
      content.py           — Power, EnemyTemplate
      serialization.py     — JSON helpers, MigrationRegistry
      validation.py        — 13 validators, ValidationResult

    combat/                — Combat engine (7 files, ~3,000 lines)
      resolution.py        — Dice, checks, tier gaps, defense values
      damage.py            — Damage resolution, track allocation, affinities
      statuses.py          — 7 status effects with tick/modifier system
      ai.py                — 5 AI profiles, target selection, retreat
      verbs.py             — 8 combat verbs (Attack through Defend)
      encounter_runner.py  — Full encounter orchestration
      data_loader.py       — Load powers/enemies/encounters from JSON

    sim/                   — Simulation engine (16 files, ~4,500 lines)
      yaml_parser.py       — Stdlib-only YAML subset parser
      clocks.py            — Macro clock advancement
      faction_logic.py     — Faction decision system
      npc_behavior.py      — NPC schedules, goals, memory
      location_dynamics.py — Economic transitions, migration, danger
      tick_engine.py       — Daily/seasonal tick orchestrator
      situation_generator.py — Player-facing situation builder
      abstract_combat.py   — Off-screen faction/NPC combat
      encounter_generator.py — EncounterSpec from situation
      player_actions.py    — Resolve player choices
      context_management.py — Compact state for narrator
      persistence.py       — Dirty-flag tracker
      content_loader.py    — YAML setting bible loader
      initial_state.py     — T+1 world state builder
      npc_generator.py     — Procedural NPC generation

    character_creation/    — Session Zero (5 files, ~1,855 lines)
      session_zero.py      — 10-scene orchestrator, InputSource protocol
      scenes.py            — Scenes 0-4 (pre-onset)
      manifestation.py     — Scene 5 (power manifestation)
      year_one.py          — Scenes 6-9 (year one)
      character_factory.py — Accumulate deltas, finalize CharacterSheet

    narrator/              — Narration system (4 files, ~430 lines)
      queue.py             — NarrationChannel protocol, Mock + File queues
      payloads.py          — 8 payload builders
      prompts.py           — Prompt templates + format_prompt
      validation.py        — Length bounds, forbidden patterns

    persistence/           — Save system (4 files, ~550 lines)
      save.py              — Atomic writes, leaves-first, throttle
      load.py              — 5-state classification, LoadResult
      migration.py         — SaveMigrator with dry-run
      multi_character.py   — Archive, list, switch characters

    progression/           — Character advancement (10 files, ~1,900 lines)
      tactical.py          — Power use tracking, strengthening marks
      breakthrough.py      — 8 trigger conditions, 24 marks, resolution
      skills.py            — 32 skills, 10 proficiency levels, synergies
      relationships.py     — Standing, trust, state machine, decay
      factions.py          — Faction standing, reach, heat
      resources.py         — 7 resource types, decay, upkeep
      aging.py             — Age categories, degradation, death roll
      family.py            — Fertility, children, descendant creation
      corruption.py        — 0-6 scale, transformation, reversal
      arcs.py              — Narrative arc detection

    runtime/               — Game loop (5 files, ~840 lines)
      main.py              — GameState, launch sequence, session loop
      configuration.py     — GameConfig dataclass
      error_handling.py    — Exception hierarchy, crash_shutdown
      input_handler.py     — Meta commands, choices, freeform input
      modes.py             — Mode transition table, ModeManager

  data/
    powers/                — 48 powers across 7 JSON files
    enemies/               — 30 enemies across 3 JSON files
    encounters/            — 12 sample encounters (1 JSON file)

  prompts/                 — 8 narrator prompt template files (.md)

  specs/                   — 6 game specification documents
  setting/                 — 15 setting bible files (YAML + Markdown)
  notes/                   — Build log, deferred items, design questions

  tests/
    unit/                  — 36 test files
    integration/           — 12 test files
    regression/            — 1 test file (combat fixes)
    scenarios/             — 1 test file (long game)
    helpers/               — Synthetic world factory
```

**Total: 58 engine files (~14,900 lines), 50 test files (~9,900 lines), 11 data files, 8 prompt files.**

---

## Module Reference -- Schemas

### `engine/schemas/character.py` (369 lines)

Core character data model. Everything about a player or NPC character lives here.

- **CharacterSheet** -- Full character: name, age, species, tier, attributes, powers, condition tracks, inventory, goals, relationships, history. All fields are plain dicts/lists for JSON serialization.
- **Attributes** -- 6 die-sized attributes (strength, agility, will, insight, perception, might). Die sizes: 4, 6, 8, 10, 12.
- **Harm** -- Physical/mental harm with tier and description.
- **Breakthrough** -- Records a tier advancement event.
- **Species enum** -- 11 species from setting bible (human, hollow_boned, deep_voiced, etc.).
- **PowerCategory enum** -- 7 categories (physical_kinetic through eldritch_corruptive).

### `engine/schemas/world.py` (903 lines)

The largest schema file. Defines all world-state entities.

- **WorldState** -- Top-level container: current_day, season, schema_version, metadata.
- **Faction** -- 22 fields: territory, population, power_profile, economic_base, goals, schemes, relationships, standing modifiers.
- **NPC** -- Manifest (powers), knowledge, memory, relationships, schedule, goals, location.
- **Location** -- Type, connections, economic_state, danger_level, controller, ambient_conditions.
- **Clock** -- Name, segments, current_segment, advance conditions, completion effects.
- **TickEvent** -- Typed event from daily/seasonal ticks with visibility level.
- **Situation** -- Player-facing moment: description, tension, choices, encounter probability.
- **SessionMetadata** / **ActiveScene** -- Runtime session tracking.

### `engine/schemas/encounter.py` (294 lines)

Combat interface types. Shared between sim (generates specs) and combat (consumes specs, produces outcomes).

- **EncounterSpec** -- Defines an encounter: enemies, terrain zones, register, win/loss conditions, world context.
- **CombatOutcome** -- Result: resolution, rounds, player state delta, enemy states, narrative log, world consequences.
- **Action** -- Single combat action record.
- **CombatRegister enum** -- human, creature, eldritch.

### `engine/schemas/validation.py` (402 lines)

13 validators (one per schema type) returning `ValidationResult(valid, errors)`. Checks field types, ranges, enum membership, cross-references.

### `engine/schemas/serialization.py` (81 lines)

- **to_json/from_json** -- Dict serialization with type dispatch.
- **save_to_file/load_from_file** -- Atomic temp-and-rename file I/O.
- **MigrationRegistry** -- Version tracking and migration function registry.

---

## Module Reference -- Combat Engine

### `engine/combat/resolution.py` (372 lines)

Dice and check resolution per combat spec Section 1.

- **roll_check(die_size, modifier, difficulty, rng)** -- Core resolution: roll d(die_size), add modifier, compare to difficulty. Returns CheckResult with success tier (critical/full/partial/miss/fumble).
- **tier_gap_modifier(attacker_tier, defender_tier)** -- +/-2 per tier difference.
- **compute_defense_value / compute_mental_defense** -- Derive defense from attributes.
- **roll_initiative** -- d10 + perception + modifier for turn order.

### `engine/combat/damage.py` (469 lines)

Damage calculation and track allocation.

- **resolve_damage(source, target, base_damage, damage_type, affinity_profile)** -- Full damage pipeline: base + tier bonus, affinity multiplier, armor reduction, track allocation.
- **allocate_to_tracks(damage, target)** -- Distributes across physical/mental/social tracks.
- **compute_exposure_fill** -- Fills exposure meter toward Exposed status.
- **7 AFFINITY_PROFILES** -- Damage type interactions per power category.

### `engine/combat/statuses.py` (215 lines)

Seven combat statuses: Bleeding, Stunned, Shaken, Burning, Exposed, Marked, Corrupted.

- **StatusEngine** -- Manages active statuses per combatant. Provides tick_start_of_round (Stunned skip), tick_end_of_turn (Bleeding/Burning damage), tick_end_of_round (duration decay), and modifier queries.

### `engine/combat/ai.py` (405 lines)

Enemy decision-making with 5 profiles.

- **AiDecisionEngine** -- Selects major+minor action per turn. Profiles: aggressive (damage focus), defensive (survive), tactical (status exploitation), opportunist (finisher seeking), pack (coordinated swarm).
- Retreat triggers per profile. Pack degradation when allies fall.

### `engine/combat/verbs.py` (881 lines)

Eight combat action resolvers. The largest combat file.

- **CombatState** -- Tracks zones, combatants, initiative, action log, scene clocks.
- **CombatantRecord** -- Per-combatant state: health, statuses, momentum, position.
- **resolve_attack/power/assess/maneuver/parley/disengage/finisher/defend** -- Each returns VerbResult with damage, status changes, movement, narrative text.

### `engine/combat/encounter_runner.py` (610 lines)

Top-level combat orchestrator.

- **EncounterRunner.run(spec, player_record, rng) -> CombatOutcome** -- Builds CombatState from EncounterSpec, rolls initiative, runs round loop (max 12), dispatches verb resolution, checks win/loss/escape each round, builds final CombatOutcome.
- Register-specific mechanics: human heat accrual (per-enemy + witnesses), creature ecological clock (reinforcements at 4/6/8), eldritch attention clock (corruption offers on Parley/Power/Assess at 20%).

### `engine/combat/data_loader.py` (58 lines)

- **load_powers/load_enemies/load_encounters** -- Reads JSON data files from `data/` directory. 48 powers, 30 enemies, 12 encounters.

---

## Module Reference -- Simulation Engine

### `engine/sim/yaml_parser.py` (338 lines)

Stdlib-only YAML subset parser. Handles: key-value pairs, lists, nested indentation, `>` folded strings, `#` comments, numeric types, `~N` approximate values, inline lists, booleans, null, quoted strings. Does **not** handle anchors, tags, or flow mappings.

### `engine/sim/tick_engine.py` (156 lines)

Central simulation orchestrator.

- **TickEngine.run_daily_tick(world, factions, npcs, locations, clocks, player, rng)** -- Advances time by 1 day, then runs: clocks -> factions -> NPCs -> locations -> sync. Returns list of TickEvents.
- **run_seasonal_tick()** -- Heavier processing at 90-day boundaries (economic shifts, population changes, clock resets).

### `engine/sim/clocks.py` (273 lines)

Macro clock advancement per setting bible clocks.yaml.

- **ClockEngine** -- Evaluates advance conditions (always, flag, resource_below, clock_at, faction_conflict), applies completion effects, handles reset and cross-clock interactions.

### `engine/sim/faction_logic.py` (443 lines)

Faction decision-making. ~1 significant action per week per faction.

- **FactionDecisionEngine.evaluate_faction_tick(faction, world, factions, rng)** -- Weighted selection among: territorial (expansion/defense), diplomatic (alliance/rivalry), scheme advancement, internal tension, resource acquisition, goal pursuit. Returns TickEvents.

### `engine/sim/npc_behavior.py` (287 lines)

NPC daily behavior simulation.

- **NpcBehaviorEngine.evaluate_npc_tick(npc, world, rng)** -- Schedule evaluation (day/night/special), goal pursuit (active goal + progress check), memory decay (older memories fade), relationship drift, displacement (flee danger), concern response.

### `engine/sim/location_dynamics.py` (285 lines)

Location state evolution.

- **LocationEngine.evaluate_location_tick(location, world, rng)** -- Economic state transitions (thriving->stable->declining->collapsed), population migration (toward safety/prosperity), danger escalation, opportunity generation, NPC presence sync, controller changes from faction actions.

### `engine/sim/situation_generator.py` (223 lines)

Generates player-facing moments of tension.

- **SituationGenerator.generate_situation(world, player, location, npcs_present, recent_events, rng)** -- Assesses tension from clocks, NPC conflicts, dangers, heat. Generates 3-6 choices. Calculates encounter probability from threat level.

### `engine/sim/abstract_combat.py` (116 lines)

Off-screen combat between factions/NPCs (not involving the player).

- **resolve_abstract_combat(attacker, defender, context, rng)** -- Tier comparison + military power + 2d6 variance. Returns winner, casualty scale, territory consequences.

### `engine/sim/encounter_generator.py` (259 lines)

Bridges situations to tactical combat.

- **EncounterGenerator.generate_encounter(situation, world, player, rng) -> EncounterSpec** -- Determines register (human/creature/eldritch) from world context, selects appropriate enemies, builds terrain zones, sets win/loss conditions.

### `engine/sim/player_actions.py` (253 lines)

Resolves player choices from situations.

- **PlayerActionResolver.resolve_action(choice, situation, world, player, rng) -> ActionResult** -- Action types: dialogue, travel, activity, observation, prepare. ActionResult carries state deltas, narration scene type, time cost, whether an encounter is triggered.

### `engine/sim/context_management.py` (161 lines)

- **compact_state(world, player, max_tokens)** -- Prioritizes current location, present NPCs, active tensions, recent events. Used to build narrator payloads without overwhelming context.

### `engine/sim/persistence.py` (61 lines)

- **DirtyTracker** -- Tracks which entities have changed since last save. Enables incremental saves.

### `engine/sim/content_loader.py` (437 lines)

Loads the setting bible YAML files into schema objects.

- **ContentLoader** -- `load_factions()`, `load_npcs()`, `load_locations()`, `load_clocks()`, `load_constants()`, `load_timeline()`. Handles informal YAML values: `~N` -> int, `"very high"` -> 9, `"T9 Physical/kinetic"` -> NpcManifest, faction parenthetical qualifiers.

### `engine/sim/initial_state.py` (165 lines)

- **build_initial_world(content_loader)** -- Assembles T+1 year world state from all bible content. Wires bidirectional faction relationships, syncs NPC locations, validates cross-references.

### `engine/sim/npc_generator.py` (303 lines)

Procedural NPC generation for session zero and runtime.

- **generate_npc(archetype, constraints, rng)** -- 60-name pool, 11 species with mid-Atlantic population weights (81% human), tier pyramid (T1-T10), 7 domain fractions, personality traits, voice templates.
- **generate_npc_batch(count, constraints, rng)** -- Batch generation with name uniqueness.

---

## Module Reference -- Character Creation

### `engine/character_creation/session_zero.py` (188 lines)

Orchestrates 10-scene character creation.

- **InputSource protocol** -- `get_text(prompt) -> str`, `get_choice(prompt, choices) -> int`. Allows test and live implementations.
- **NarratorSink protocol** -- `narrate(text)`. Abstracts output.
- **FixedInputSource** -- Deterministic inputs for testing.
- **SessionZero.run(input, narrator, rng, world) -> CharacterSheet** -- Iterates 10 scenes, passes deltas to CharacterFactory, finalizes sheet.

### `engine/character_creation/scenes.py` (561 lines)

Scenes 0-4 (pre-onset).

- **OpeningScene** -- Name + age (16-65).
- **OccupationScene** -- 12 occupations with attribute/skill/resource/heat deltas.
- **RelationshipScene** -- 6 archetypes (spouse, parent, child, sibling, friend, mentor) with NPC generation and status-based goals.
- **LocationScene** -- 8 regions x 8 circumstances. Region determines starting faction; circumstance affects power manifestation.
- **ConcernScene** -- 8 pre-onset concerns with goals and optional secondary NPCs.

### `engine/character_creation/manifestation.py` (258 lines)

Scene 5 -- power manifestation.

- **ManifestationScene** -- Circumstance-weighted category draw (7 categories with 8 circumstance tilt profiles), session-zero tier pyramid (T1:50%, T2:30%, T3:15%, T4:5%), background modifiers, secondary category at 55% probability. 36 starter power templates across 6 categories.

### `engine/character_creation/year_one.py` (535 lines)

Scenes 6-9 (year one after the Onset).

- **FirstWeeksScene** -- 4 survival strategies, companion NPC generation, eldritch corruption check.
- **FactionEncounterScene** -- 8 region-to-faction mappings, 4 response types (accept/negotiate/refuse/play).
- **CriticalIncidentScene** -- 3 incident branches (Hungry Thing / Reckoning / Loss) selected by character state, 4 options each.
- **SettlingScene** -- 5 lifestyle options (species-filtered), starting inventory, final goal.

### `engine/character_creation/character_factory.py` (313 lines)

- **CreationState** -- Accumulates deltas across 10 scenes: attribute bonuses, skill grants, resource additions, NPC references, goals, narrative tags.
- **CharacterFactory** -- `apply_scene_result()` merges deltas. `finalize()` snaps die sizes, validates, produces CharacterSheet.

---

## Module Reference -- Runtime

### `engine/runtime/main.py` (381 lines)

The central game loop.

- **GameState** -- Mutable container for all runtime state: world, player, factions, npcs, locations, clocks, metadata, session_id, rng, current_mode, narrator_mode, autosave_interval.
- **LaunchLock** -- File-based lock preventing concurrent sessions. Stale after 1 hour.
- **launch(args, save_root, force_new)** -- 11-step sequence: parse -> config -> save root -> lock -> classify save -> dispatch (fresh/resume/corrupt) -> session loop -> shutdown -> release.
- **main_session_loop(state)** -- Mode dispatch loop. Calls `_run_session_zero`, `_run_framing`, `_run_sim_cycle`, `_run_combat`, or handles `GAME_OVER`.
- **_maybe_autosave(state)** -- Saves every `autosave_interval` seconds (default 600).
- **_clean_shutdown(state)** -- Final save + lock release.

### `engine/runtime/modes.py` (134 lines)

Mode transition enforcement.

- **TRANSITION_TABLE** -- SESSION_ZERO->{FRAMING}, FRAMING->{SIM}, SIM->{COMBAT, FRAMING, GAME_OVER}, COMBAT->{SIM, GAME_OVER}, GAME_OVER->{SESSION_ZERO}.
- **ModeManager** -- Registers handlers, validates transitions, tracks history. `run_cycle()` delegates to current handler and auto-transitions.
- **ModeHandler protocol** -- `enter(state)`, `run_cycle(state) -> next_mode`, `exit(state)`.

### `engine/runtime/input_handler.py` (117 lines)

- **InputHandler.parse_input(raw, num_choices) -> Intent** -- Recognizes `/save`, `/quit`, `/status`, `/help`, `/inventory`, `/map`, `/character`, `/history`. Parses numeric (1-N) or letter (a-z) choices. Falls back to freeform text.
- **Intent** -- is_meta_command, meta_command, meta_args, target_choice, freeform_text.

### `engine/runtime/configuration.py` (82 lines)

- **GameConfig** -- 12 fields: save_root, log_level, seed, autosave_interval, narrator_mode, etc.
- **load_config/save_config** -- Simple key=value file format.

### `engine/runtime/error_handling.py` (127 lines)

- **Exception hierarchy** -- EmergenceError -> RecoverableError (exit 1), FatalError (exit 2), SaveIntegrityError (exit 3), NarratorProtocolError (exit 4), EngineInternalError (exit 5).
- **crash_shutdown(error, state)** -- Emergency save attempt before exit.

---

## Module Reference -- Narrator

### `engine/narrator/queue.py` (84 lines)

- **NarrationChannel protocol** -- `emit(payload) -> str`. Abstracts narrator communication.
- **MockNarrationQueue** -- Returns `"[NARRATION: {scene_type}]"` immediately. Used in testing and mock mode.
- **FileNarrationQueue** -- Writes JSONL to queue file, prints `===NARRATION_PAYLOAD===` marker, blocks for response `===NARRATION_COMPLETE===`. Sequence tracking via `narration_seq.txt`.

### `engine/narrator/payloads.py` (155 lines)

8 payload builders, each returning a NarratorPayload dict:

- `build_combat_turn_payload` -- Round-by-round combat narration.
- `build_scene_framing_payload` -- New scene/location setup.
- `build_situation_payload` -- Player-facing choice moment.
- `build_dialogue_payload` -- NPC conversation.
- `build_character_creation_payload` -- Session zero beats.
- `build_transition_payload` -- Time/location transitions.
- `build_death_payload` -- Character death narration.
- `build_time_skip_payload` -- Extended time passage.

### `engine/narrator/prompts.py` (122 lines)

- **PROMPT_TEMPLATES** -- 8 prompt templates keyed by scene type.
- **get_prompt(scene_type)** -- Retrieves template.
- **format_prompt(template, payload)** -- Substitutes payload fields into template.

### `engine/narrator/validation.py` (73 lines)

- **validate_narration(text, payload)** -- Checks length bounds per scene type, forbidden patterns (out-of-character references, meta-gaming), payload constraint compliance.

---

## Module Reference -- Persistence

### `engine/persistence/save.py` (100 lines)

- **SaveManager(save_root)** -- `full_save()`: writes entities in leaves-first order (player, factions, npcs, locations, clocks, metadata), then world.json last as save-complete marker. Atomic temp-and-rename writes. 5-second throttle between saves.
- `lightweight_save()` -- Saves combat_state.json only, for round-by-round persistence.

### `engine/persistence/load.py` (168 lines)

- **LoadManager(save_root)** -- `classify()` returns FRESH/PARTIAL/VALID/CORRUPT/VERSION_MISMATCH. `load_save()` returns LoadResult with world, player, factions, npcs, locations, clocks, errors.

### `engine/persistence/migration.py` (155 lines)

- **SaveMigrator(save_root)** -- `needs_migration()`, `get_save_version()`, `migrate(dry_run)`. Applies registered migration functions in version order with atomic file rewrites.

### `engine/persistence/multi_character.py` (126 lines)

- **MultiCharacterManager(save_root)** -- `archive_character(reason)` moves to `player/archive/{name}_{timestamp}/`. `list_characters()` returns archived character metadata. `switch_character(archive_id)` archives current, restores target.

---

## Module Reference -- Progression

### `engine/progression/tactical.py` (134 lines)

Power strengthening through use.

- **TacticalProgression(character)** -- `log_power_use(power_id, category)` increments counters. `check_strengthening()` awards marks at thresholds: 25 (mark 1), 75 (mark 2), 200 (mark 3), 500 (mark 4), 1200 (mark 5). At tier ceiling, mark 5 threshold doubles to 2400. Category bonuses at 100/400/1000/2500 total uses.

### `engine/progression/breakthrough.py` (394 lines)

Tier advancement events.

- **BreakthroughEngine** -- `check_triggers(character, world, event, rng)` evaluates 8 conditions: near_death, mentorship (90+ days), eldritch_exposure (3+ days), substance, ritual (3+ participants), npc_death (standing >= 2), sustained_crisis (14+ days), sacrifice (5-year cooldown).
- `resolve_breakthrough(character, trigger, rng)` -- Rolls against condition-specific DC. On success: tier +1, mark selection by type (depth=same category, breadth=adjacent, integration=universal).
- **24 breakthrough marks** -- P1-P4 (physical), M1-M4 (mental), E1-E4 (energy), B1-B4 (biological), A1-A4 (auratic), T1-T4 (temporal), X1-X4 (eldritch, all add corruption), U1-U3 (universal).

### `engine/progression/skills.py` (152 lines)

Use-based skill advancement.

- **SkillProgression(character)** -- 32 skills in 7 clusters (combat, movement, social, knowledge, craft, survival, special). Thresholds: 5/20/60/150/350/750/1500/3000/7000/15000 for proficiency 1-10.
- **9 synergy pairs** -- e.g., first_aid 4 -> surgery +1, literacy 4 -> history/bureaucracy/languages +1.
- **5 prerequisite rules** -- e.g., surgery >= 3 requires first_aid >= 4.
- **resolve_skill_check(character, skill, attribute, dc, rng)** -- 1d(attribute) + proficiency + synergy bonus, -2 if untrained.

### `engine/progression/relationships.py` (182 lines)

NPC relationship dynamics.

- **RelationshipProgression(character)** -- Standing -3..+3, trust 0-5. State machine: neutral -> cordial -> warm -> trusted -> loyal (positive path); cold -> antagonist -> blood_feud (negative path).
- `apply_betrayal()` -- Standing = -3, locked for 60 days.
- `apply_absence_decay()` -- 40% chance per month for positive standings, 30% drift toward 0 for negative.
- `handle_npc_death()` -- Lock permanently, mental damage (1 at standing 2, 2 at standing 3).

### `engine/progression/factions.py` (118 lines)

Faction standing, reach, and heat tracking.

- **FactionProgression(character)** -- Standing -3..+3, reach 0-5, heat (decayable vs permanent).
- `apply_yearly_decay(rng)` -- 50% chance standing drifts toward 0, reach -1 per 3 years inactive, heat -1/year (respects permanent floor).

### `engine/progression/resources.py` (115 lines)

Resource management with decay.

- **ResourceProgression(character)** -- 7 types. Wealth decay rates: cu 0%, scrip 5%/year, crown_chits 10%/year, grain 10%/month, pharma 3%/year, trade_goods 5%/year.
- `apply_follower_upkeep()` -- Retainer 150 cu/month, retinue 300 cu/month.
- `apply_holding_upkeep()` -- Residence/workshop 30 cu, fortified 80 cu, stronghold 130 cu.

### `engine/progression/aging.py` (223 lines)

Character aging and mortality.

- **AgingEngine** -- 7 age categories: young (<30), mature (30-39), aging (40-49), old (50-59), very_old (60-69), ancient (70-79), elder (80+).
- Attribute degradation at 40 (str/agi -1 die), 50 (str/agi/per -1, phys_max -1), 60 (same).
- **Death roll at 60+** -- 1d20 + modifiers vs DC 8. Modifiers: physical track damage, harm, corruption > 2, age > 60, species, medical care, stress.

### `engine/progression/family.py` (178 lines)

Family and lineage.

- **FamilyEngine** -- Fertility by age bracket (16-25: 8%, 25-35: 6%, 35-45: 3%, 45-55: 1%, 55+: 0%). Child manifestation: 15% annual chance ages 12-18.
- `create_descendant(parent, world, rng)` -- Picks oldest manifested child, inherits 50% resources, significant relationships (|standing| >= 2, not dead), lineage tracking.

### `engine/progression/corruption.py` (219 lines)

Corruption scale and consequences.

- **CorruptionEngine** -- Scale 0-6. Segment 1-2: cosmetic effects. Segment 3-4: mechanical (skill penalties, faction standing caps). Segment 5: aging halted, faction_standing_cap = 1, monthly will check vs DC 12. Segment 6: transformation (character becomes NPC, sheet locked).
- `attempt_reversal()` -- Segments 1-2: fully reversible. 3-4: max -1 per 5 years. 5: only patron_release or counter_bargain. 6: irreversible.

### `engine/progression/arcs.py` (188 lines)

Narrative arc detection for significant moments.

- **ArcTracker.check_arc_progress(character, world)** -- Detects: goal completion (100%) and 75% milestones, relationship climax (loyal, blood_feud), relationship loss (NPC death), faction allegiance (+3) and enmity (-3), corruption visibility (segment 3), corruption transformation (segment 6), tier milestones.

---

## Test Coverage

**898 tests total (895 pass, 3 skipped).**

### Unit Tests (36 files, ~640 tests)

| File | Tests | Covers |
|------|-------|--------|
| test_schemas | 21 | Round-trip serialization for all schema types |
| test_validation | 116 | All 13 validators, valid/invalid/edge cases |
| test_resolution | 18 | Dice, checks, tier gaps, Monte Carlo |
| test_damage | 25 | Affinities, armor, exposure, track allocation |
| test_statuses | 20 | All 7 statuses, ticks, modifiers |
| test_ai | 13 | 5 AI profiles, retreat, pack degradation |
| test_verbs | 15 | All 8 combat verbs |
| test_data_loader | 13 | 48 powers, 30 enemies, 12 encounters |
| test_yaml_parser | 41 | All YAML features |
| test_clocks | 30 | Advance, completion, reset, interactions |
| test_faction_logic | 11 | All faction action types |
| test_npc_behavior | 18 | Schedule, goals, memory, relationships |
| test_location_dynamics | 13 | Economics, migration, danger |
| test_tick_engine | 8 | Daily/seasonal ticks |
| test_situations | 16 | Tension, choices, encounter probability |
| test_abstract_combat | 8 | Tier advantage, determinism |
| test_encounter_generator | 11 | Register selection, enemy matching |
| test_player_actions | 18 | All action types + context + persistence |
| test_npc_generator | 22 | Species/tier distribution, constraints |
| test_session_zero_scenes | 26 | Scenes 0-4, eligibility, deltas |
| test_manifestation | 11 | Category/tier rolls, circumstance tilts |
| test_year_one | 20 | Scenes 6-9, incident type selection |
| test_runtime_config | 19 | Config load/save, defaults |
| test_narrator | 21 | Queue, payloads, prompts, validation |
| test_input_handler | 24 | Meta commands, choices, freeform |
| test_modes | 17 | Transitions, forbidden paths, history |
| test_tactical_progression | 15 | Marks, thresholds, ceiling |
| test_breakthrough | 28 | 8 triggers, resolution, marks |
| test_skills | 14 | Proficiency, prerequisites, synergies |
| test_relationships | 20 | Standing, trust, states, betrayal, decay |
| test_faction_progression | 10 | Standing, reach, heat, decay |
| test_resources | 13 | Add, spend, decay, upkeep |
| test_aging | 14 | Categories, degradation, death roll |
| test_family | 10 | Birth, manifestation, descendant |
| test_corruption | 15 | Segments, effects, reversal |
| test_arcs | 12 | Goals, relationships, factions, corruption, tier |

### Integration Tests (12 files, ~140 tests)

| File | Tests | Covers |
|------|-------|--------|
| test_combat_scenarios | 6 | Human/creature/eldritch register encounters |
| test_world_tick | 7 | 365-day simulation smoke test |
| test_encounter_generation | 3 | Situation -> encounter pipeline |
| test_sim_combat_handoff | 3 | Sim -> combat -> sim round-trip |
| test_content_loading | 27 | All bible content loads + cross-references |
| test_initial_state | 12 | T+1 world state + 30-day tick |
| test_session_zero | 15 | 5 seeds -> 5 varied characters |
| test_content_sim_integration | 3 | Bible -> sim -> combat pipeline |
| test_save_load | 28 | Save/load/migration/multi-character |
| test_full_session | 18 | End-to-end, CLI commands, round-trip |
| test_mode_transitions | 12 | All valid paths, forbidden paths |
| test_progression | 6 | Combat marks, standings, persistence |

### Regression Tests (1 file, 26 tests)

| File | Tests | Covers |
|------|-------|--------|
| test_combat_fixes | 26 | All 27 Phase 2.5 combat spec audit fixes |

### Scenario Tests (1 file, 4 tests)

| File | Tests | Covers |
|------|-------|--------|
| test_long_game | 4 | 5-year simulation, aging to death, descendant, serialization |

### Running Tests

```bash
# All tests
python -m unittest discover -s emergence/tests -v

# Specific test file
python -m unittest emergence.tests.unit.test_tactical_progression -v

# Specific test category
python -m unittest discover -s emergence/tests/unit -v
python -m unittest discover -s emergence/tests/integration -v
python -m unittest discover -s emergence/tests/scenarios -v
```

---

## Known Issues

No critical bugs are known. The 3 skipped tests are placeholder tests for features that require live narrator integration (not available in mock mode).

### Design Questions Resolved

- **DQ-001: Missing sim-architecture.md** -- The README references this spec but it was not provided. The simulation engine was constructed from design-brief.md, interface-spec.md, gm-primer.md, and cross-references in other specs.
- **DQ-002: Missing sim-content-integration.md** -- Also referenced but not provided. Content integration was built from the setting bible files directly.

### Deferred Items

No items were deferred. All specified mechanics were implemented.

### Limitations

- **Narrator integration** -- The narrator queue protocol is implemented but the live narrator (Claude generating prose) is not wired into the session loop. Mock mode returns placeholder text. The FileNarrationQueue protocol is ready for integration.
- **CLI polish** -- The `play` subcommand works in mock mode (FixedInputSource). Live stdin input works but has minimal formatting/color.
- **Power data** -- 48 powers are implemented from the combat spec. The setting bible describes additional powers that are not yet in the data files.
- **Balance tuning** -- Progression thresholds, encounter difficulty, and economic values are implemented per spec but have not been play-tested at scale beyond the automated 5-year smoke test.

---

## Extension Guide

### Adding a New Power

1. Add the power definition to the appropriate JSON file in `data/powers/{category}.json`. Fields: id, name, tier_min, tier_max, damage_type, base_damage, cost, effects, description.
2. If the power introduces a new mechanic, add a verb handler case in `engine/combat/verbs.py:resolve_power()`.
3. Add a starter template entry in `engine/character_creation/manifestation.py:STARTER_POWERS` if it should be available during session zero.
4. Add a test in `tests/unit/test_data_loader.py` to verify it loads.

### Adding a New Enemy

1. Add the template to `data/enemies/{register}.json`. Fields: id, name, tier, attributes, powers, ai_profile, condition_track_max, affinities, description.
2. If using a new AI profile, add it in `engine/combat/ai.py`.
3. Add a sample encounter using the enemy in `data/encounters/sample_encounters.json`.

### Adding a New Faction

1. Add the faction to `setting/factions.yaml`.
2. Add a content_loader mapping in `engine/sim/content_loader.py:load_factions()` if the faction uses non-standard YAML formatting.
3. Add the faction ID to `engine/sim/initial_state.py:build_initial_world()` relationship wiring.
4. Add region-to-faction mapping in `engine/character_creation/year_one.py:REGION_FACTIONS` if the faction controls a region.

### Adding a New NPC

1. Add to `setting/npcs.yaml` with domain, concern, location, faction, and manifest fields.
2. The content loader will pick it up automatically if the format matches existing entries.
3. Add cross-reference tests in `tests/integration/test_content_loading.py`.

### Adding a New Location

1. Add to `setting/locations.yaml` with type, connections, economic_state, controller, and ambient fields.
2. Add to the region mapping in `engine/character_creation/scenes.py:REGION_LOCATIONS` if it should be a session zero option.
3. Verify cross-references in `tests/integration/test_initial_state.py`.

### Adding a New Progression Mechanic

1. Create a new module in `engine/progression/`.
2. Follow the pattern: class takes `character` dict, modifies it in place, stores state in well-named character dict keys.
3. Ensure all state is JSON-serializable (plain dicts, lists, numbers, strings).
4. Add yearly/monthly decay if applicable.
5. Wire into `engine/runtime/main.py:_run_sim_cycle()` for tick integration.
6. Add unit tests in `tests/unit/` and integration tests in `tests/integration/test_progression.py`.

### Adding a New Session Zero Scene

1. Create a Scene subclass in the appropriate file (`scenes.py` for pre-onset, `year_one.py` for post-onset).
2. Implement `narrate()`, `choices()`, and `apply(state, choice, rng)`.
3. Add the scene to the scene list in `engine/character_creation/session_zero.py:SessionZero.SCENES`.
4. Add test cases in `tests/unit/test_session_zero_scenes.py` or `tests/unit/test_year_one.py`.

### Adding a New Combat Verb

1. Add a `resolve_{verb}` function in `engine/combat/verbs.py` following the existing pattern (takes CombatState, actor, target/zone, rng; returns VerbResult).
2. Add the verb to `engine/combat/encounter_runner.py:_dispatch_verb()`.
3. Add AI consideration in `engine/combat/ai.py:_enumerate_actions()`.
4. Add the verb name to `engine/schemas/encounter.py:CombatVerb` enum.
5. Add tests in `tests/unit/test_verbs.py`.

---

## Key Design Patterns

### All State is Plain Dicts

Character sheets, world state, faction data -- everything is stored as plain Python dicts with string keys and JSON-serializable values. This makes save/load trivial and avoids dataclass serialization complexity. Schema dataclasses exist for documentation and validation but the runtime passes dicts.

### Protocol-Based Abstraction

I/O boundaries use Python protocols (structural typing): `InputSource`, `NarratorSink`, `NarrationChannel`, `ModeHandler`. This allows test doubles (FixedInputSource, MockNarrationQueue) without inheritance hierarchies.

### Deterministic Replay

All randomness flows through injected `random.Random` instances. Pass the same seed, get the same game. This is critical for testing and debugging.

### Atomic File I/O

All saves use temp-file-and-rename: write to `{path}.tmp`, then `os.replace()` to the final path. This prevents corrupt saves from crashes mid-write.

### Leaves-First Save Order

When saving, entity files (player, factions, npcs, locations, clocks) are written before `world.json`. On load, the presence of `world.json` is the "save complete" marker. A save missing `world.json` is classified as PARTIAL and can be recovered.

---

## Build History

| Phase | Tests | Key Deliverables |
|-------|-------|-----------------|
| 0 | -- | Repository organization |
| 1 | 137 | 8 schema files, validation framework |
| 2 | 248 | Combat engine, 48 powers, 30 enemies, 12 encounters |
| 2.5 | 275 | 27 combat spec audit fixes, 26 regression tests |
| 3 | 462 | 16 simulation engine modules, 365-day smoke test |
| 4 | 598 | Content loader, character creation (10 scenes), NPC generator |
| 5 | 737 | Runtime, narrator, persistence, CLI entry point |
| 6 | 898 | 10 progression modules, 5-year extended smoke test |
| 7 | 898 | PLAY.md, HANDOFF.md, final polish |

Full build history with per-phase details is in `notes/build-log.md`.

