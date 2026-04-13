# Runtime Architecture Specification

This document specifies the runtime layer of Emergence: the entry point, session loop, mode handling, file tree, input handling, error handling, dependencies, and configuration. The runtime coordinates the sim engine, the combat engine, the narrator (Claude at runtime reading payloads), and persistence. It does not itself contain game logic or produce prose.

The runtime is a Python program executed by `python3 -m emergence` from within a Claude Code session. Claude Code sees the stdout/stdin stream of the program and, by design, pauses to read narrator payloads and emit prose into the chat stream between engine steps. The runtime writes structured payloads to a known queue file; Claude reads the queue; Claude emits prose and a marker indicating the payload was consumed; the runtime proceeds.

---

## Section 1 — Entry Point and Launch

### 1.1 Command-line entry

The entry point is `emergence.__main__`, invoked as:

```
python3 -m emergence [SUBCOMMAND] [OPTIONS]
```

**Subcommands:**

| Subcommand | Purpose |
|---|---|
| `play` | Default. Start or resume a session in the default save slot. |
| `new` | Force creation of a new character in the active world. |
| `list` | List saves and characters. Print and exit. |
| `inspect` | Print validation report for a save directory. Print and exit. |
| `migrate` | Run migrations on a save directory without launching. Print and exit. |
| `help` | Print usage and exit. |

**Global options (apply to all subcommands):**

| Option | Type | Default | Effect |
|---|---|---|---|
| `--save-root PATH` | string | `$EMERGENCE_SAVE_ROOT` or `./saves/default` | Save directory to operate on. |
| `--config PATH` | string | `$EMERGENCE_CONFIG` or `./config/emergence.toml` | Config file path. |
| `--log-level LEVEL` | enum | `info` | One of `debug|info|warn|error`. |
| `--log-file PATH` | string | `{save_root}/logs/runtime.log` | Log destination. |
| `--no-color` | flag | false | Suppress ANSI color in stdout. |
| `--seed INT` | int | read from world | Override RNG seed for this session. Records override in session log. |
| `--dry-run` | flag | false | Validate and print launch plan. Do not mutate save. |

**`play` options:**

| Option | Type | Default | Effect |
|---|---|---|---|
| `--character ID` | string | active character in world | Switch active character in this world. |
| `--resume` | flag | auto | Force resume rather than create/select. |
| `--skip-session-zero` | flag | false | For dev/testing only. Spawns a character with a fixed template. |

**`new` options:**

| Option | Type | Default | Effect |
|---|---|---|---|
| `--world PATH` | string | `--save-root` value | World to place the new character in. |
| `--template ID` | string | `null` | Use a named character template instead of full session zero. |

**Exit codes:**

- `0`: clean exit after session or successful print-and-exit subcommand.
- `1`: user-facing error (bad args, bad config).
- `2`: environment error (missing Python version, missing directories not creatable).
- `3`: save integrity error (schema violation, corrupt file unrecoverable).
- `4`: engine internal error (bug; stack trace in log).
- `5`: narrator protocol error (queue discipline violation).

### 1.2 Launch sequence

The launch sequence is a strict ordered pipeline. Each step validates preconditions and either advances or halts with a classified error.

```
LAUNCH_SEQUENCE:
  step 1:  parse_cli_arguments()
  step 2:  check_python_version()        # 3.10+ required
  step 3:  load_config(config_path)      # see §8
  step 4:  validate_config()
  step 5:  ensure_save_root_exists(save_root)  # create if missing
  step 6:  acquire_launch_lock(save_root)      # see §1.6
  step 7:  inspect_save_contents(save_root)
             -> classification: FRESH | PARTIAL | VALID | CORRUPT | VERSION_MISMATCH
  step 8:  dispatch_by_classification()
             -> FRESH         -> first_run_experience()
             -> PARTIAL       -> repair_or_abort()
             -> VALID         -> resume_or_new_character_experience()
             -> CORRUPT       -> corruption_recovery()
             -> VERSION_MISMATCH -> run_migrations() then re-inspect
  step 9:  enter_main_session_loop()
  step 10: clean_shutdown() on normal return; crash_shutdown() on exception
  step 11: release_launch_lock()
```

### 1.3 Save classification

`inspect_save_contents` examines the directory according to the Save schema in `interface-spec.md §Save` and returns one of:

- **FRESH**: `save_root` does not exist, or contains only empty subdirectories, or contains only the `logs/` directory.
- **PARTIAL**: `world.json` is missing but some other files are present. Indicates an aborted session zero or a manual edit in progress.
- **VALID**: `world.json` exists, schema versions match or are older (migrable), all referenced ids resolve. At least one `player/character.json` is present *or* `world.json.past_characters` is non-empty *and* world is valid without an active character (between-characters state).
- **CORRUPT**: `world.json` exists but fails parse, fails schema validation, or references entities whose files are missing beyond migration recovery.
- **VERSION_MISMATCH**: `world.json` parses, but schema_version is newer than this engine supports (newer save than runtime).

### 1.4 First-run experience

On FRESH classification:

1. Print the one-paragraph setting hook (from config, template `hooks.first_run`).
2. Offer three launch options as menu choices: `[1] Begin new life (session zero)`, `[2] Run a quick tutorial fight`, `[3] Exit`.
3. On `1`:
   - Create the save skeleton: write `world.json` with `schema_version`, `current_time.in_world_date = "T+1y 0m 0d"`, `year = 1`, `worldline_id = "lordly_equilibrium"`, `active_player_character = null`, `past_characters = []`, `active_scene = null`, `session_metadata` initialized.
   - Copy the seed world content (factions, npcs, locations, clocks) from `data/worldseed/lordly_equilibrium/` into the save directory verbatim. This materializes the Lordly Equilibrium state into the save so future ticks write to the save, not the seed.
   - Initialize `history/`, `rumors/rumors.json`, `session_log/` as empty structures.
   - Enter `session_zero_mode` (§3.1).
4. On `2`: enter a sandbox combat scene with a pregenerated character. No save is mutated. Exits cleanly to menu.
5. On `3`: clean exit.

### 1.5 Resume / multi-character / new-character experience

On VALID classification with `active_player_character != null`:

1. Compute `resume_summary`:
   - Character name, species, current age, location, in-world date, last-save timestamp, a one-sentence state summary drawn from `session_metadata.last_resume_summary` if present.
2. Offer: `[1] Resume {character.name}`, `[2] Switch character`, `[3] New character in this world`, `[4] World status`, `[5] Exit`.
3. `[1]` -> load full state (§3 of state-persistence.md), enter whichever mode `world.active_scene.type` indicates, or sim mode if `active_scene` is null.
4. `[2]` -> list all ids in `past_characters` plus active; selection swaps `active_player_character`; persist world.json; resume.
5. `[3]` -> archive current character (see state-persistence §5), set `active_player_character = null`, enter session zero.
6. `[4]` -> print faction standings, clock states, regional summary, and return to menu.
7. `[5]` -> clean exit.

On VALID classification with `active_player_character == null` and `past_characters` non-empty: skip directly to `[3]` (create new character in inhabited world).

### 1.6 Launch lock

A single file `{save_root}/.lock` holds the PID and ISO timestamp of the owning process. On launch:

- If `.lock` does not exist, create it atomically (O_CREAT|O_EXCL).
- If it exists and its PID is live and the process name is the emergence runtime, abort with "save in use by PID {n}".
- If the PID is dead (or not a live emergence process), warn "recovering stale lock from {timestamp}", remove, and recreate.

The lock is released on any clean or crash exit (atexit handler + signal handler for SIGTERM/SIGINT).

---

## Section 2 — Main Session Loop

### 2.1 Top-level control flow

```
main_session_loop(state):
  initialize_session(state)
  while not state.session_should_end:
    mode = state.world.active_scene.type or "sim_mode"
    try:
      next_mode, mode_result = run_mode(mode, state)
    except RecoverableError as e:
      handle_recoverable(e, state)
      continue
    except FatalError as e:
      crash_shutdown(e, state)
      raise
    apply_mode_transition(state, next_mode, mode_result)
    maybe_autosave(state)
  terminate_session(state)
```

### 2.2 Session initialization

```
initialize_session(state):
  state.session_id = generate_session_id()   # timestamp + random suffix
  state.session_start_real = now()
  state.rng = seeded_rng(state.world.rng_seed)
  state.narration_queue = open_queue(save_root / "runtime" / "narration_queue.jsonl")
  state.input_channel = stdin_line_reader()
  log_event("session_start", {session_id, character_id, in_world_date})
  emit_framing_payload(
    scene_type="scene_framing",
    trigger="session_resume" or "session_start",
    register="standard"
  )
  wait_for_narration()
  write_session_log_entry("session_open")
```

### 2.3 Mode dispatch

`run_mode(mode, state)` is a dispatch to the mode handler (§3). Each handler returns a tuple `(next_mode_name, mode_result)`. `next_mode_name` is one of: `sim_mode`, `combat_mode`, `framing`, `transition`, `session_zero`, `end`. `mode_result` is a mode-specific dict recorded in the session log.

### 2.4 Save points

Saves occur at each of the following moments (see state-persistence §1 for full enumeration):

1. Immediately after mode transitions from combat_mode, session_zero, or framing.
2. After a sim tick that advances `current_time` by one or more in-world days.
3. Before entering combat_mode (pre-combat snapshot for rollback-on-crash support).
4. On explicit `save` meta-command.
5. On graceful shutdown.
6. On autosave interval (configurable; default every 10 minutes real time while in sim_mode).

### 2.5 Termination procedure

```
terminate_session(state):
  flush_narration_queue()
  write_session_log_entry("session_close", summary=generate_session_summary(state))
  update_session_metadata(
    session_count += 1,
    total_playtime_real_seconds += real_elapsed,
    last_save = iso_now(),
    character_lifetime_years = recompute_from_history(state.character)
  )
  save_all(state)                    # full save per state-persistence §2
  emit_end_of_session_framing(state) # optional closing narration
  release_launch_lock()
  log_event("session_end")
  close_logs()
  return exit_code = 0
```

### 2.6 Crash recovery

Uncaught exceptions route to `crash_shutdown`:

```
crash_shutdown(exception, state):
  log_exception(exception, with_full_traceback=True)
  write_session_log_entry("session_crash", exception_class, message, last_save_ts)
  attempt_emergency_save(state)
    -> best-effort: write state.draft/ snapshot, mark world.json.active_scene.unsafe_shutdown=True
  release_launch_lock()
  print_user_facing_crash_message(exception)
  exit(4)
```

On the next launch, `inspect_save_contents` detects `active_scene.unsafe_shutdown == True` and routes to `crash_recovery_dialog`:

- `[1] Resume from last autosave (recommended)`: restore from `{save_root}/` (ignore `.draft/`).
- `[2] Attempt to recover in-flight scene from draft`: copy `.draft/` over `{save_root}/`, clear unsafe_shutdown flag.
- `[3] Abandon character (archive and start over)`.

Option `[2]` is offered only if `.draft/` exists and passes a reduced validation pass.

---

## Section 3 — Mode Handling

Five modes exist: `session_zero`, `sim_mode`, `combat_mode`, `framing`, `transition`. Each is a handler with a defined entry, loop, exit, and allowed transitions.

Universal rule: *no mode modifies state outside its authorizing engine's scope* (see interface-spec §Modification Authority). Mode handlers route input and invoke engines; they do not write state fields directly.

### 3.1 session_zero

**Purpose.** Author a playable character through scenes, not a form (per design brief). Produces a `Character Sheet` conforming to schema.

**Entry.**
- Precondition: `world.active_player_character == null`.
- Load `data/session_zero/beats.json`: an ordered list of creation beats.
- Initialize `creation_state = {sheet_partial: {}, beat_index: 0, choices_recorded: {}}`.

**Beats.** Eight required beats in order:

1. `origin_context` — what the character was doing the moment of Onset.
2. `what_was_lost` — who or what did not survive.
3. `manifestation_moment` — the discovery of power (produces `power_category_primary`, initial power id, circumstance_of_manifestation text).
4. `first_year_summary` — what the last twelve months have been.
5. `body_and_mark` — attributes, species (baseline human or one of the ten metahuman species per species.md), a physical detail.
6. `relationships_residue` — one or two surviving connections (populates initial entries in `relationships` and a matching stub NPC if the referent does not already exist in the world).
7. `entanglement_and_goals` — 1-3 goals and 1 faction entanglement.
8. `starting_position` — location id from locations.yaml, immediate situation.

**Beat loop.**

```
for beat in beats:
  emit_payload(scene_type="character_creation_beat", beat=beat.id,
               state_snapshot=creation_state, register=beat.register)
  wait_for_narration()                    # Claude writes the beat's scene
  present_choices(beat.choice_menu)       # engine-side structured menu
  selection = read_choice_or_freeform()
  update = beat.apply(selection, creation_state, rng)
  creation_state.apply(update)
  record_choice(beat.id, selection)
  write_draft_character(creation_state)   # incremental save to .draft/
finalize_character(creation_state)
validate_character_sheet(sheet)
world.active_player_character = sheet.id
append_to_past_characters_on_death_only   # not now
save_all()
transition_to: framing (scene_framing at starting_position)
```

**Transitions.**
- Normal completion -> `framing`.
- Player types `restart` during session zero -> reset `creation_state`, re-enter from beat 0.
- Player types `quit` during session zero -> abandon draft, set `active_player_character = null`, clean exit.

**Forbidden.** Narrator never proposes mechanical stats. Engine computes all mechanical fields from beat selections deterministically.

### 3.2 sim_mode

**Purpose.** The sim layer — travel, activities, conversation, scavenging, rest. The place where the character lives. Default mode between framed scenes.

**Entry.**
- Precondition: world has valid active character; location id resolves.
- Load current location, npcs_present, ambient conditions.
- Compute a `Situation` (per interface-spec §Situation) via sim engine `generate_situation(world, character)`.

**Sim loop.** Each iteration is one *situation cycle*:

```
while mode == sim_mode:
  situation = sim_engine.generate_situation(world, character)
  emit_payload(
    scene_type="situation_description",
    state_snapshot=compact_situation_snapshot(situation, character),
    register=infer_register(situation),           # §3.2.1
    context_continuity=continuity_state,
  )
  wait_for_narration()

  present_choices(situation.player_choices + universal_sim_verbs)
  raw_input = read_player_input()
  intent = parse_input(raw_input, situation)      # §5

  if intent.is_meta_command:
    handle_meta(intent)
    continue
  if intent.is_mode_command and intent.target == "quit":
    break_to_terminate()
  if intent.target_choice is None:
    emit_payload(scene_type="transition",
                 directive="clarify input", forbidden=["invent outcome"])
    continue

  resolution = sim_engine.resolve_choice(intent, situation, world, character, rng)
  #   resolution is one of:
  #   - SimOutcome(state_deltas, narration_payload)
  #   - DialogueOutcome(npc_id, dialogue_state) -> transitions to dialogue sub-loop
  #   - EncounterTriggered(encounter_spec)      -> transitions to combat_mode
  #   - ActivityStarted(activity_state)          -> stays in sim_mode with extended activity
  #   - TravelStarted(route, etd)                -> stays in sim_mode; time advances

  apply_state_deltas(resolution.state_deltas, world, character)
  emit_payload(scene_type=resolution.narration_scene_type,
               state_snapshot=resolution.narration_snapshot,
               register=resolution.register)
  wait_for_narration()

  advance_time(resolution.time_cost, world)       # may trigger sim ticks
  maybe_run_sim_ticks(world, character)           # §3.2.2
  maybe_autosave()

  if resolution is EncounterTriggered:
    return ("combat_mode", resolution.encounter_spec)
  if resolution.forces_framing:
    return ("framing", resolution.frame_spec)
```

#### 3.2.1 Register inference

Register is chosen deterministically from situation features:

| Feature | Register |
|---|---|
| eldritch taxonomy present in location or npc set | `eldritch` |
| combat imminent (encounter_probability ≥ 0.6) | `action` |
| intimate/private social context flagged | `intimate` |
| night, wilderness, solo | `quiet` |
| default | `standard` |

The engine chooses the register; the narrator honors it. The narrator never escalates register beyond what is directed.

#### 3.2.2 Sim tick triggers within sim_mode

Ticks run when `current_time` crosses a tick boundary. Two boundaries exist:

- **Daily tick**: every in-world day boundary crossed.
- **Seasonal tick**: every in-world season boundary (four per year).

Each tick invokes the sim engine's tick routine, which emits Tick Events (per interface-spec). Events with `visibility in {"local","regional"}` touching the character's current location or current relationships generate `transition` narration payloads; `world`-visibility events are logged and may surface later as rumor. `hidden` events are logged only.

**Tick backlog.** If time advances more than a single tick (e.g., a multi-day travel), run ticks in order, cap at config `sim.max_ticks_per_advance` (default 30), and summarize remainder as a single `time_skip` narration. This prevents narration flood on long travel.

**Transitions.**
- To `combat_mode` via `EncounterTriggered`.
- To `framing` when entering a new location for the first time that session, or when a scripted framing trigger fires.
- To `end` via `quit` meta-command.
- To `session_zero` only on character death resolution (see §3.4 exit).

### 3.3 framing

**Purpose.** A short scene that establishes context on a major transition: entering a new location, returning after a long absence, a new day's first scene, resuming a session. Narration-only; no mechanical choices.

**Entry.** Triggered by sim_mode, session startup, or explicit `sim_engine.request_framing(trigger_reason)`.

**Loop.**

```
frame_payload = build_framing_payload(
  scene_type="scene_framing",
  trigger_reason=trigger,
  state_snapshot=compact_location_and_character_snapshot(),
  register=infer_register(location),
  desired_length=(80, 180),
)
emit_payload(frame_payload)
wait_for_narration()
return ("sim_mode", None)
```

**Exit.** Always returns to `sim_mode`. Framing never loops on itself.

**Forbidden.** Framing payloads never present choices. Framing narration must not invent consequences; it only sets the stage.

### 3.4 combat_mode

**Purpose.** The tactical subsystem as defined in combat-spec (not authored here). The runtime's job is to hand off the encounter, drive the combat loop, and receive a Combat Outcome.

**Entry.**
- Input: `EncounterSpec` from sim.
- Validate: all ids resolve, player sheet conforms, encounter schema_version matches.
- Create `{save_root}/runtime/combat_snapshot.json` — pre-combat copy of character.json and relevant world state, for rollback on combat-engine crash.
- Set `world.active_scene = {type: "combat_mode", scene_id: encounter.id, state: {round: 0}}`.
- Emit `scene_framing` payload with combat register (one of `human|creature|eldritch` per `encounter.combat_register`) — opening situation narration only. Player does not yet act.

**Loop.** Delegated to combat engine via `combat_engine.run(encounter_spec, input_channel, narration_channel) -> CombatOutcome`. The combat engine is a subroutine; the runtime's responsibility during combat is only:

- Provide a narration channel that uses `emit_payload` with `scene_type="combat_turn"`.
- Provide an input channel that accepts player declarations.
- Advance `world.active_scene.state.round` as turns complete.
- Autosave at end of each round (lightweight: write only active_scene, not full world tick).

Detailed combat procedure is out of scope for this document. The runtime is agnostic to combat internals as long as the outcome conforms.

**Exit.**

```
outcome = combat_engine.run(spec, ...)
validate_combat_outcome(outcome, against=spec)
sim_engine.ingest_combat_outcome(outcome, world, character)
#   applies player_state_delta, enemy_states, world_consequences
emit_payload(scene_type="transition",
             state_snapshot=post_combat_snapshot,
             register="quiet")
wait_for_narration()
world.active_scene = null
delete combat_snapshot.json
if character.is_dead:
  return ("end", DeathOutcome(outcome))
  # main loop triggers death_narration then session termination
return ("sim_mode", None)
```

**Death handling.** If any post-ingest invariant fails the "character alive" predicate (condition_track.physical >= 5 with lethal tier-3 harm, or explicit death flag in outcome, or corruption >= 6), route to `death_narration`:

```
emit_payload(scene_type="death_narration",
             state_snapshot=final_character_snapshot,
             register="quiet",
             forbidden=["consolation", "moralizing", "future framing"])
wait_for_narration()
archive_character(character)      # see state-persistence §5
world.active_player_character = null
terminate_session()
```

### 3.5 transition

**Purpose.** A short narrative bridge between situations that does not warrant a full framing or scene. Used for small time elapses, minor state changes, and the "after the dust settles" beat after significant resolutions.

Transition is not a mode the main loop persists in; it is a narration payload type emitted from within other modes. It does not have a loop. When narration completes, the emitting mode resumes.

No explicit transitions in/out are required because `transition` is not a mode-level state.

### 3.6 Mode transition matrix

| From → To | session_zero | sim_mode | combat_mode | framing | end |
|---|---|---|---|---|---|
| session_zero | loop | on completion | — | — | on quit |
| sim_mode | on death-then-new | loop | on encounter | on location-change | on quit |
| combat_mode | — | on outcome (alive) | loop | on escape-to-new-location | on death |
| framing | — | always after framing | — | — | on quit |

Dashes indicate forbidden transitions. Attempting a forbidden transition is an engine internal error.

---

## Section 4 — File Structure

The project directory has four top-level concerns: engine code, content data, runtime state (saves + logs), and configuration. Everything is plain files; no database.

```
emergence/
├── emergence/                   # Python package — engine code
│   ├── __init__.py
│   ├── __main__.py              # entry point; parses CLI, calls launch
│   ├── launch.py                # launch sequence from §1.2
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── session_loop.py      # main session loop from §2
│   │   ├── modes/
│   │   │   ├── __init__.py
│   │   │   ├── session_zero.py  # §3.1
│   │   │   ├── sim.py           # §3.2
│   │   │   ├── combat.py        # §3.4 runtime wrapper around combat engine
│   │   │   ├── framing.py       # §3.3
│   │   │   └── transition.py    # §3.5 helper
│   │   ├── input.py             # §5 input handling
│   │   ├── output.py            # stdout printing, color, formatting
│   │   ├── errors.py            # §6 error classes and handlers
│   │   ├── config.py            # §8 config loading and validation
│   │   ├── locks.py             # launch lock from §1.6
│   │   └── narration_queue.py   # queue writer/reader per prompt-mgmt.md §5
│   ├── sim/
│   │   ├── __init__.py
│   │   ├── engine.py            # sim engine public API
│   │   ├── situation.py         # Situation generation
│   │   ├── ticks.py             # tick routines
│   │   ├── activities.py        # scavenge, rest, travel, etc.
│   │   └── outcomes.py          # SimOutcome, EncounterTriggered, etc.
│   ├── combat/
│   │   ├── __init__.py
│   │   ├── engine.py            # combat engine entry point
│   │   └── (combat internals — specified in combat-spec, not here)
│   ├── world/
│   │   ├── __init__.py
│   │   ├── character.py         # Character Sheet model + validation
│   │   ├── faction.py
│   │   ├── npc.py
│   │   ├── location.py
│   │   ├── clock.py
│   │   └── registry.py          # id lookup across entities
│   ├── content/
│   │   ├── __init__.py
│   │   ├── loader.py            # loads data/ into registries
│   │   ├── powers.py
│   │   ├── enemies.py
│   │   └── session_zero.py
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── save.py              # save procedures per state-persistence §2
│   │   ├── load.py              # load procedures per state-persistence §3
│   │   ├── atomic.py            # atomic file write helpers
│   │   ├── journal.py           # state-persistence §7
│   │   └── migrations/
│   │       ├── __init__.py
│   │       ├── registry.py      # version registry
│   │       └── v1_0_to_v1_1.py  # one file per migration step
│   ├── narrator/
│   │   ├── __init__.py
│   │   ├── payload.py           # Narrator Payload construction
│   │   ├── compaction.py        # state snapshot compaction per scene_type
│   │   ├── continuity.py        # last_narration_summary bookkeeping
│   │   └── validation.py        # post-narration checks per prompt-mgmt §7
│   └── util/
│       ├── __init__.py
│       ├── rng.py               # seeded RNG wrapper
│       ├── time.py              # in-world time math
│       ├── ids.py               # id generation and validation
│       └── text.py              # text utilities (word count, etc.)
├── data/                        # content data — read-only at runtime
│   ├── worldseed/
│   │   └── lordly_equilibrium/
│   │       ├── world.json
│   │       ├── factions/
│   │       ├── npcs/
│   │       ├── locations/
│   │       ├── clocks/
│   │       └── history/
│   ├── powers/
│   │   └── {power_id}.json
│   ├── enemies/
│   │   └── {template_id}.json
│   ├── session_zero/
│   │   └── beats.json
│   ├── bible/                   # authoritative setting text, reference only
│   │   ├── primer.md
│   │   ├── geography.md
│   │   ├── species.md
│   │   ├── powers.md
│   │   ├── eldritch.md
│   │   ├── narration.md
│   │   └── (others)
│   └── prompts/
│       └── {scene_type}.txt     # prompt templates per prompt-mgmt §2
├── saves/                       # runtime state — mutable
│   └── default/                 # a single save root; more may exist
│       ├── world.json
│       ├── player/
│       │   ├── character.json
│       │   └── journal.json
│       ├── factions/{id}.json
│       ├── npcs/{id}.json
│       ├── locations/{id}.json
│       ├── clocks/{id}.json
│       ├── history/{era}.json
│       ├── rumors/rumors.json
│       ├── archived_characters/{id}/   # state-persistence §5
│       │   └── character.json
│       ├── session_log/
│       │   └── {session_id}.json
│       ├── logs/
│       │   └── runtime.log
│       ├── runtime/
│       │   ├── narration_queue.jsonl
│       │   └── combat_snapshot.json    # only during combat
│       ├── .draft/                      # only during session_zero or crash recovery
│       ├── .lock
│       └── .version                    # text file with engine version last written
├── config/
│   └── emergence.toml
├── tests/                       # developer-only
│   └── …
├── README.md
└── requirements.txt             # empty or comment-only; stdlib only
```

### 4.1 Directory boundary rules

- `emergence/` contains code only. No data files. Never mutated at runtime.
- `data/` contains content, read-only at runtime. The runtime may read; it may not write. Seeding a new world *copies* from `data/worldseed/` into `saves/{save_root}/`.
- `saves/` is the only tree the runtime writes to during play, with the exception of logs.
- `config/` contains the config file. The runtime reads. It writes only when the user issues an explicit config-change command (not specified as in-game; future work).
- `.draft/`, `.lock`, `runtime/` inside a save are engine-managed; the player is not expected to edit them and the engine treats manual edits as potential corruption.

### 4.2 What belongs where — contested cases

- **Player journal**: `saves/{root}/player/journal.json`. Readable by the player in-game (§5 meta-command). Auto-populated by the engine.
- **Rumors**: `saves/{root}/rumors/rumors.json`. World-level; shared across characters in the same world.
- **Per-character history**: lives inside `character.json.history`. The top-level `history/` directory is for *world* history: faction events, era summaries, regional developments. Not for character personal history.
- **Prompts**: `data/prompts/` — the runtime reads these at narrator-payload time. They are content (tone, structure) rather than code.
- **Setting bible files**: `data/bible/` — the runtime does not parse these. They are reference for the narrator (Claude) and are surfaced via targeted references in payloads, not bulk-loaded.

---

## Section 5 — Input Handling

Player input arrives via stdin. The runtime supports three input modes, layered: structured menu choice, meta-command, freeform verb.

### 5.1 Parsing pipeline

```
parse_input(raw: str, context: Situation | None) -> Intent:
  text = raw.strip()
  if text == "":
    return Intent(kind="noop")
  if text.startswith("/"):
    return parse_meta_command(text[1:])
  if re.match(r"^\d+$", text) and context and context.player_choices:
    idx = int(text) - 1
    if 0 <= idx < len(context.player_choices):
      return Intent(kind="choice", target_choice=context.player_choices[idx])
    return Intent(kind="error", reason="invalid_choice_index")
  return parse_freeform(text, context)
```

### 5.2 Structured choice

When `context.player_choices` is non-empty, the runtime prints them numbered `1..n`. The player types `1`, `2`, etc. The first match wins. A matching choice resolves to `Intent(kind="choice", target_choice=choice_obj)`.

### 5.3 Meta-commands

Meta-commands begin with `/` and are handled by the runtime, not the sim or combat engine. They never advance in-world time. Available at any time except mid-combat-turn:

| Command | Effect |
|---|---|
| `/save` | Force autosave. Prints "saved at {path}". |
| `/quit` or `/exit` | Initiate clean shutdown. Confirm if unsaved. |
| `/help` | Print command list and current context hints. |
| `/sheet` | Print character sheet summary. Uses a structured printer, not narration. |
| `/powers` | Print powers list with short descriptions. |
| `/inventory` or `/inv` | Print inventory. |
| `/journal` | Print the journal index with entry ids; `/journal {id}` prints an entry. |
| `/time` | Print `current_time.in_world_date`, age, season, location. |
| `/location` or `/where` | Print current location display_name, controller, threat level, npcs present. |
| `/relationships` or `/rel` | Print relationship standings. |
| `/clocks` | Print macro clocks visible to the player (known + rumored). Hidden clocks omitted. |
| `/standings` or `/heat` | Print current heat by faction. |
| `/goals` | Print active goals with progress. |
| `/history` | Print last 20 character history events. |
| `/config` | Print the current effective config. Read-only in v1. |
| `/log {n}` | Reprint the last n narration entries from the session log. Default n=3. |
| `/verbose` | Toggle verbose output (echoes engine events). |
| `/debug` | Print a diagnostic snapshot (only when log-level=debug). |

Unknown `/command` prints `unknown command, try /help`.

### 5.4 Freeform parsing

For freeform input, the runtime uses rule-based intent recognition. The parser is deterministic; there is no LLM call to parse input.

**Procedure:**

```
parse_freeform(text, context):
  lower = text.lower().strip().rstrip(".!?")
  tokens = lower.split()
  first = tokens[0] if tokens else ""
  # 1. synonym lookup
  verb = VERB_SYNONYMS.get(first, None)
  # 2. match against context choices by keyword overlap
  if context and context.player_choices:
    for choice in context.player_choices:
      if keyword_match(lower, choice):
        return Intent(kind="choice", target_choice=choice)
  # 3. verb dispatch
  if verb:
    return build_verb_intent(verb, tokens, context)
  # 4. fallback: look for object-only mention
  obj = find_object_in_context(tokens, context)
  if obj:
    return Intent(kind="examine", target=obj)
  # 5. nothing matched
  return Intent(kind="unclear", raw=text)
```

**Verb synonym table (canonical forms and synonyms):**

| Canonical | Synonyms |
|---|---|
| travel | go, walk, move, head, leave, depart |
| examine | look, inspect, check, study, observe, see |
| attack | attack, strike, hit, fight, kill, engage |
| talk | talk, speak, say, ask, tell, greet |
| rest | rest, wait, pause, sit |
| sleep | sleep, camp, bunk |
| scavenge | scavenge, search, loot, gather, forage |
| hide | hide, conceal, duck, crouch |
| flee | flee, run, escape, retreat |
| use | use, activate, invoke, cast |
| take | take, grab, pick up, pocket |
| drop | drop, discard, leave behind |
| give | give, offer, hand |
| trade | trade, barter, sell, buy |
| help | help, aid, assist |
| threaten | threaten, menace, warn |
| parley | parley, negotiate, talk down, terms |

**Intent resolution.** Each verb maps to a handler that either:

- Resolves to one of the current `player_choices` (e.g., `travel` matches a travel choice).
- Generates a new `Intent` of kind matching an activity (e.g., `scavenge` with no choice present but a valid scavenge context).
- Returns `Intent(kind="unclear", raw=text)` if the verb is valid but context forbids it here (e.g., `flee` outside of combat or a chase).

**Unclear intents** result in a narrator-less clarification prompt printed by the runtime directly (e.g., `can you be more specific? available actions are listed above.`). No narration payload is emitted. This is the fallback procedure.

### 5.5 Input validation

- Maximum raw length: 500 characters. Longer inputs are rejected with `input too long`.
- Control characters (other than newline and tab) are stripped silently.
- Leading `/` triggers meta parser even if the command is invalid, preventing accidental freeform commands like `/stop`.
- During combat turns, only: numbered menu choices, `/help`, `/sheet`, `/save`, `/quit`, and the canonical combat verbs supplied by the combat engine are accepted. Freeform parsing is narrower in combat.

---

## Section 6 — Error Handling

Errors are classified at source and handled by category. Silent swallowing is forbidden; visible failure is required (per interface-spec non-negotiable properties).

### 6.1 Error categories

| Category | Exception class | Recoverable? | Response |
|---|---|---|---|
| Schema violation | `SchemaError` | no (requires fix) | Halt current operation; log; offer rollback |
| State corruption | `CorruptionError` | sometimes | Attempt recovery from last save; else offer abandon |
| Narrator protocol failure | `NarratorProtocolError` | yes | Retry once; then fall back to template; then accept with warning |
| Engine internal error | `EngineBugError` | no | Crash shutdown; preserve state |
| IO failure | `IOFailureError` | yes | Retry up to 3 times with backoff; then escalate |
| User input error | `InputError` | yes | Print user message; re-prompt |
| Tick invariant violation | `TickInvariantError` | no | Crash; preserve pre-tick state |
| Migration failure | `MigrationError` | no | Halt at launch; preserve save untouched |

### 6.2 Response procedures

**Schema violation (SchemaError).** Raised by `validate_*` functions.

```
handle_schema_error(e, state):
  log("schema_violation", entity=e.entity, field=e.field, value=e.value,
      expected=e.expected)
  write_diagnostic({save_root}/logs/schema_error_{ts}.json, ...)
  if e.entity is a in-memory draft (mid-session):
    rollback_to_last_save()
    notify_user("State change rejected due to schema violation; rolled back to last save.")
    return resume
  else (persisted file):
    raise FatalError  # stops session; user must intervene
```

**State corruption (CorruptionError).** Detected by load or mid-session invariant check.

```
handle_corruption(e, state):
  log("corruption", file=e.file, detail=e.detail)
  if e.recoverable_from_backup and latest_backup_exists():
    offer_user(["restore backup", "continue anyway", "abandon"])
  else:
    offer_user(["abandon character", "exit and inspect"])
```

**Narrator protocol failure.** See §6.3.

**Engine internal error (EngineBugError).** Any unexpected exception in engine code that isn't one of the above.

```
handle_engine_bug(e, state):
  log_exception(e, full_traceback=True)
  crash_shutdown(e, state)    # see §2.6
```

**IO failure.** Disk full, permission denied, transient read error.

```
with_retry(n=3, backoff_seconds=[0.1, 0.5, 2.0]):
  op()
else:
  notify_user("Disk error: {detail}. Your session is still live but I can't save right now. Try /save later.")
  set_save_degraded_flag()
```

**User input error.** Invalid choice index, malformed command, unparseable input with no freeform fallback match.

```
print_user_message("{guidance}")
re_prompt()
# no state mutation, no narration payload
```

**Tick invariant violation.** A sim tick produced state that fails a post-tick invariant (e.g., faction territory overlap exceeds cap, npc in two locations).

```
log("tick_invariant_violation", ...)
rollback_to_pre_tick_snapshot()
raise FatalError  # do not proceed with corrupt tick
```

### 6.3 Narrator protocol failure

"Narrator protocol failure" means the narration queue output is absent, malformed, violates length limits egregiously, or echoes the payload verbatim.

```
handle_narrator_protocol_failure(payload, response, error):
  log_narrator_failure(payload, response, error)
  if retries < max_retries (default 1):
    emit_payload(augmented_payload_with_reminder)
    retries += 1
    return retry
  # fall back
  fallback = generate_template_narration(payload)
  print(fallback)
  log("narrator_fallback_used", scene_type=payload.scene_type)
  continue_with_fallback_as_narration
```

Template fallbacks are stored in `data/prompts/{scene_type}.fallback.txt` and are minimal, neutral prose keyed to payload fields.

### 6.4 Logging and diagnostics

- Main log: `{save_root}/logs/runtime.log`, rotating at 10 MB, keep last 5.
- Level set by `--log-level` or config.
- Each log line: ISO timestamp, level, module, event, structured fields (JSON-extended).
- Crash diagnostics: on fatal error, dump `{save_root}/logs/crash_{ts}/` with: traceback, last 20 log lines, snapshot of `active_scene`, in-memory state digest.
- Schema violations: separate file per incident at `logs/schema_error_{ts}.json` for easy triage.

### 6.5 Graceful degradation

The runtime prefers visible degradation to silent success. Degradation flags:

- `save_degraded`: IO errors prevent saves. In-game HUD prints `[SAVE DEGRADED]` on status queries.
- `narration_degraded`: narration fallbacks in use. Prints `[NARRATION DEGRADED]` in debug/verbose mode.
- `tick_degraded`: a non-fatal tick produced warnings. Next session status mentions it.

Any flag set at session close produces a final warning message asking the player to inspect the log.

### 6.6 User-facing error messages

Tone: plain, factual, no jargon where avoidable. Examples:

- `Can't save: disk is full. Free some space and try /save again.`
- `That choice isn't available right now.`
- `Something went wrong with the last narration. Continuing with a simpler description.`
- `This save was made with a newer version of the game. Upgrade or start a new save.`
- `The game crashed. Your progress up to the last save has been preserved at {path}. A crash report is at {path}.`

---

## Section 7 — Dependencies

- **Python 3.10 or newer.** Minimum 3.10. Uses structural pattern matching. Validated at launch step 2.
- **Standard library only.** No `pip install`. No external packages. All dependencies are modules shipped with CPython.
- **Required modules:** `json`, `os`, `sys`, `pathlib`, `dataclasses`, `enum`, `typing`, `datetime`, `random`, `hashlib`, `shutil`, `tomllib` (3.11+) or `configparser` fallback for 3.10, `logging`, `signal`, `atexit`, `argparse`, `textwrap`, `re`, `itertools`, `collections`, `uuid`.
- **No network.** No outbound HTTP. No `requests`, no `urllib` usage during play. The runtime runs air-gapped.
- **No model calls from Python.** The narrator is Claude at runtime (Claude Code), reading the queue. Python does not make API calls.

### 7.1 TOML handling

If Python >= 3.11, use `tomllib`. If 3.10, fall back to a minimal TOML-subset parser implemented with `configparser` (flat key = value, section-free) or reject with a clear message asking for 3.11+. Implementer choice; record in design_decisions.

### 7.2 Environment validation at launch

Validates at step 2 of launch sequence:

```
check_python_version():
  if sys.version_info < (3, 10):
    print("Emergence requires Python 3.10 or newer. Found {v}.")
    exit(2)
check_stdlib_modules():
  for m in REQUIRED_MODULES:
    try: __import__(m)
    except ImportError:
      print("Python install missing module {m}. Reinstall Python or check PYTHONPATH.")
      exit(2)
check_filesystem_writable(save_root):
  try: touch_test_file
  except: exit(2)
check_terminal():
  if not sys.stdin.isatty() and not dry_run:
    warn("stdin is not a TTY; input may not work as expected")
```

---

## Section 8 — Configuration

### 8.1 File and format

- Location: `./config/emergence.toml` by default; override via `--config` or `$EMERGENCE_CONFIG`.
- Format: TOML.
- Hierarchy: global defaults -> global config file -> per-save `{save_root}/config.toml` (optional) -> CLI flags. Later overrides earlier.

### 8.2 Complete option table

All options with type, default, valid range, effect.

**[runtime]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `autosave_interval_seconds` | int | 600 | 60-3600 | Real-time interval between sim-mode autosaves. 0 disables. |
| `autosave_on_tick` | bool | true | — | Save after any tick that advances time. |
| `max_draft_age_days` | int | 30 | 1-365 | Drafts older than this are cleaned on launch. |
| `confirm_on_quit` | bool | true | — | Prompt confirmation if unsaved changes exist. |
| `session_log_retention` | int | 100 | 10-10000 | Max session logs kept per save. |

**[sim]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `max_ticks_per_advance` | int | 30 | 1-365 | Cap on consecutive ticks in a single time advance. |
| `default_travel_speed_km_per_day` | int | 35 | 10-200 | Default for on-foot travel. Overridable by power/species. |
| `situation_generation_attempts` | int | 5 | 1-20 | Max attempts to draw a non-degenerate situation. |
| `encounter_probability_cap` | float | 0.95 | 0.0-1.0 | Hard cap on per-situation encounter probability. |
| `daily_tick_enabled` | bool | true | — | Disable to freeze world (debug). |

**[combat]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `round_autosave` | bool | true | — | Save at end of each combat round. |
| `max_rounds_per_encounter` | int | 30 | 3-200 | Hard cap; encounter auto-resolves via stalemate at cap. |

**[narrator]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `queue_path` | string | `runtime/narration_queue.jsonl` | path | Relative to save root. |
| `timeout_seconds` | int | 120 | 10-3600 | Max wait for narration before failure. |
| `retry_on_failure` | int | 1 | 0-3 | Narrator retry count. |
| `word_count_tolerance` | float | 0.35 | 0.0-1.0 | Tolerance for over/under on desired_length. |
| `log_narrations` | bool | true | — | Log all emitted narrations to session_log. |

**[input]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `max_input_length` | int | 500 | 50-5000 | Reject longer lines. |
| `enable_freeform` | bool | true | — | If false, only numbered choices and /commands. |

**[display]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `color` | bool | true | — | ANSI color. `--no-color` overrides. |
| `width` | int | 96 | 40-200 | Wrap width for printing. |
| `echo_engine_events` | bool | false | — | Print structured engine events; noisy. |

**[logging]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `level` | enum | `info` | debug|info|warn|error | Log verbosity. |
| `max_file_size_mb` | int | 10 | 1-1000 | Rotation threshold. |
| `backup_count` | int | 5 | 0-50 | Rotated files kept. |

**[paths]**

| Key | Type | Default | Valid | Effect |
|---|---|---|---|---|
| `data_root` | string | `./data` | path | Content root. |
| `saves_root` | string | `./saves` | path | Default saves directory (for `list` subcommand). |

### 8.3 Per-character vs global configuration

- `runtime.*`, `logging.*`, `display.*`, `input.*`, `paths.*` are global.
- `sim.*`, `combat.*`, `narrator.*` may be overridden per-save by `{save_root}/config.toml`.
- Overriding `sim.daily_tick_enabled` or `narrator.retry_on_failure` per-character is allowed and useful for debug saves.

### 8.4 Validation at launch

```
validate_config(cfg):
  for key, spec in CONFIG_SCHEMA.items():
    if key not in cfg and spec.required:
      raise ConfigError(key, "missing")
    v = cfg.get(key, spec.default)
    if not spec.type_match(v):
      raise ConfigError(key, "wrong type")
    if not spec.range_ok(v):
      raise ConfigError(key, "out of range")
  cfg = apply_defaults(cfg)
  return cfg
```

Unknown keys produce a warning but do not halt launch. Typos are easy; graceful-enough handling helps iteration.

---

## Design Decisions

- **Narrator coupling.** The narrator is Claude reading payloads from a JSONL queue; the Python runtime does not make API calls. This is the mandated architecture per design brief. All "wait_for_narration" steps block the runtime until Claude writes a completion marker to the queue. See prompt-management.md §5 for queue protocol.
- **Subcommand model chosen over top-level flags.** Subcommands (`play`, `new`, `list`, `inspect`, `migrate`) give cleaner separation than overloaded flags; `play` is the default so casual invocation remains `python -m emergence`.
- **Single save root per invocation.** Multi-save management is through `--save-root` and the `list` subcommand; no in-engine save-slot selection UI in v1.
- **Launch lock uses PID file, not fcntl.** Cross-platform; simple; adequate for single-user solo RPG.
- **Meta-commands use `/` prefix.** Distinct from freeform verbs; familiar from chat/IRC conventions; avoids ambiguity with in-world actions.
- **Combat_mode does not narrate autonomously.** The combat engine emits `combat_turn` payloads through the same queue, but the mode handler is a thin wrapper; combat internals are out of scope here.
- **Autosave on tick, not on every mutation.** Every-mutation saves would thrash the disk during sim bursts; end-of-tick granularity matches the natural game boundary.
- **`.draft/` used for both session zero and crash recovery.** Single staging directory; classification distinguishes purposes via presence of `draft_purpose.txt`.
- **Freeform parsing is deterministic and rule-based.** No model-based NLU; keeps input reproducible and debuggable, matches "resolution is deterministic" principle.
- **TOML version split.** Require 3.11+ for native `tomllib` and document this; no fallback parser in v1. Recorded as soft constraint: if shipping to 3.10 is required later, add minimal parser. Per §7.1.
- **Sim tick backlog cap.** 30 ticks max per advance; remainder summarized as time_skip. Prevents narration flood on long journeys without losing world progression (ticks still run; narration is just summarized).

## [NEEDS RESOLUTION]

- [NEEDS RESOLUTION: exact session zero beat text and choice menus — out of scope for this doc; belongs in content authoring pass]
- [NEEDS RESOLUTION: combat_mode internal procedure — deferred to combat-spec.md]
- [NEEDS RESOLUTION: exact tick cadence for seasonal tick (calendar-based vs. elapsed-time-based) — sim-spec.md decision]
- [NEEDS RESOLUTION: universal sim verbs list (rest, scavenge, etc.) must be defined concretely by sim-spec; runtime uses whatever sim-engine provides]
