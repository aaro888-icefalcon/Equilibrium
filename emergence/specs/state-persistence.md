# State Persistence Specification

This document specifies how Emergence saves, loads, migrates, and manages state across sessions and characters. It conforms to the Save schema in `interface-spec.md §Save` and supports the runtime architecture in `runtime-architecture.md`.

State is a set of files on disk. No database. Saves are atomic per-file and idempotent. Round-trip through save/load must preserve game-relevant behavior exactly (interface-spec non-negotiable property 3).

---

## Section 1 — Save Triggers

Saves are triggered automatically at specific moments and manually by the player. Each trigger has an explicit precondition, scope, and behavior. Unless noted, every trigger produces a *full save* (§2).

### 1.1 Automatic triggers

| Trigger | Condition | Scope | Behavior |
|---|---|---|---|
| **scene_transition_autosave** | Any mode transition: session_zero→framing, framing→sim, sim→combat, combat→sim, any→end | Full save | After the transition is applied, before the new mode's entry procedure begins. |
| **mode_change_autosave** | Same as scene_transition but collapsed to the mode granularity. Redundant with above; consolidated: one save per mode boundary. | Full | — |
| **major_state_event_autosave** | A defined major-event emission from sim engine: NPC death, faction war declaration, faction takeover, clock complete, breakthrough, character death, character marriage, character birth. | Full | Save immediately after the event is applied. |
| **time_elapsed_autosave** | At least one in-world day has passed since the last save, AND at least one sim tick has run. | Full | Save at end of the tick that crosses the day boundary. |
| **combat_round_autosave** | End of each combat round, if `combat.round_autosave=true`. | Lightweight — only world.json, character.json, and combat snapshot. Faction/npc/location files unchanged during combat and not rewritten. | Fast save; not a full rewrite. |
| **real_time_autosave** | Every `runtime.autosave_interval_seconds` real seconds in sim_mode, if enabled (default 600). | Full | Background save at interval. |
| **pre_combat_snapshot** | Entry to combat_mode. | Snapshot to `{save_root}/runtime/combat_snapshot.json`. | Rollback support; not part of the rotation. |
| **on_graceful_shutdown** | Runtime receives quit/SIGTERM/normal exit. | Full | Final save with updated session_metadata. |
| **on_crash** | Uncaught exception. | Best-effort emergency save to `.draft/`. | Crash recovery per runtime §2.6. |

### 1.2 Manual triggers

| Trigger | Command | Scope |
|---|---|---|
| **player_save_command** | `/save` | Full save. Prints confirmation "saved at {timestamp} to {path}". |
| **player_quit_with_save** | `/quit` with confirmation | Full save, then shutdown. |

### 1.3 Non-saving transitions

Some events explicitly do NOT save, to avoid thrashing:

- Every freeform input that does not change state.
- Every narrator payload emission (unless it follows a state change).
- Every tick that produces only `hidden`-visibility events.
- Dialogue sub-loop exchanges that do not modify relationships.

### 1.4 Save throttling

To prevent excessive writes on rapid transitions (e.g., a sim-combat-sim toggle in quick succession), the save layer throttles:

- Minimum 5 real seconds between two full saves; second full save within the window is coalesced with the first pending.
- Manual `/save` bypasses throttling.
- Tick-boundary and combat-round saves bypass throttling.

### 1.5 Save ordering invariant

Saves are serialized: a save completes before the next save begins. The runtime uses an in-process save queue; concurrent save requests queue rather than race.

---

## Section 2 — Save Format

### 2.1 Directory layout (reference)

Per `interface-spec.md §Save` with runtime additions:

```
{save_root}/
├── world.json                       # World State schema
├── player/
│   ├── character.json               # Character Sheet schema
│   └── journal.json                 # §7
├── factions/
│   └── {faction_id}.json            # Faction schema
├── npcs/
│   └── {npc_id}.json                # NPC schema
├── locations/
│   └── {location_id}.json           # Location schema
├── clocks/
│   └── {clock_id}.json              # Clock schema
├── history/
│   └── {era_id}.json                # World-history eras, see §5.3
├── rumors/
│   └── rumors.json                  # all active rumors
├── archived_characters/
│   └── {character_id}/              # §5
│       ├── character.json
│       ├── epitaph.json             # death summary + final journal snapshot
│       └── journal.json
├── session_log/
│   └── {session_id}.json            # one per session
├── logs/
│   └── runtime.log                  # rotated
├── runtime/
│   ├── narration_queue.jsonl        # see prompt-mgmt §5
│   ├── narration_seq.txt
│   └── combat_snapshot.json         # only during combat
├── .draft/                          # only during session_zero or crash recovery
│   └── (mirrors top-level layout)
├── .lock                            # launch lock file
└── .version                         # engine version that last wrote this save
```

### 2.2 File-by-file specification

**`world.json`** — World State schema.
- Always present in a VALID save.
- Represents session-spanning world state: current_time, active_scene, session_metadata, worldline_id, active_player_character, past_characters, rng_seed.
- Additional runtime fields:
  - `rng_seed` (int): seeded on world creation; persists.
  - `engine_version` (string): last engine version that wrote this file.
  - `save_degraded_flag` (bool): set if last session had IO errors.
  - `narration_degraded_flag` (bool): set if narration fallbacks occurred this session.

**`player/character.json`** — Character Sheet schema.
- Present if `world.active_player_character != null`.
- All fields per interface-spec §Character Sheet.
- On character death: archived to `archived_characters/{id}/character.json`; this file is removed or emptied (see §5).

**`player/journal.json`** — see §7.

**`factions/{faction_id}.json`** — Faction schema. One file per faction in world. Total count ~15-30.

**`npcs/{npc_id}.json`** — NPC schema. One file per named NPC in world. Named-NPC count bounded (<1000); throwaway encounter mobs are not persisted as NPCs.

**`locations/{location_id}.json`** — Location schema. One per location. Region and point-location granularity.

**`clocks/{clock_id}.json`** — Clock schema. The ten macro clocks plus any scene or regional clocks.

**`history/{era_id}.json`** — shared chronology of world events, grouped by era. Era ids are sequential ("era_001" etc.) and a new era file is created when the current era exceeds 200 events or a major world event (full clock, war resolution) designates a new era.

**`rumors/rumors.json`** — a single object: `{"rumors":[{id, text, source, scope, visibility, confidence, first_heard, last_spread, subjects}], "schema_version": "1.0"}`. World-level; shared across characters.

**`archived_characters/{character_id}/`** — see §5.

**`session_log/{session_id}.json`** — per-session chronological record:
- session_id, start_ts, end_ts (null until close), character_id, starting_location
- events: ordered list of structured entries (mode transitions, major state events, choices made, narrations emitted with payload summary).
- summary: at session close, a generated summary sentence for use in `last_resume_summary`.

**`logs/`** — operational logs. Rotated. Not part of gameplay state; safe to delete.

**`runtime/`** — runtime-only; regenerable. Safe to delete when not in an active session.

**`.version`** — plain text: `engine_version_string\nschema_version_string\n`.

**`.lock`** — PID file.

### 2.3 Atomicity procedure

All file writes use a temp-and-rename pattern for per-file atomicity:

```
atomic_write(path, content_bytes):
  tmp = path + ".tmp." + random_suffix()
  with open(tmp, "wb") as f:
    f.write(content_bytes)
    f.flush()
    fsync(f)
  os.replace(tmp, path)      # atomic on POSIX; effectively so on Windows
  fsync(dir_of(path))         # best-effort directory fsync
```

A full save is multiple atomic writes; there is no transaction across files. To approximate cross-file atomicity:

- Writes are ordered: leaves first, then aggregates, then `world.json` last. `world.json` is the anchor; if `world.json` is updated, all referenced state was written before it.
- If a crash occurs mid-save, `world.json` may still reference the last consistent state (because it was written last) or the save may be partially new (fresh leaves, stale world.json). Either is recoverable.
- Per-file `.tmp` artifacts are cleaned on next load.

### 2.4 Rollback support

Three rollback layers:

1. **Pre-combat snapshot**: `{save_root}/runtime/combat_snapshot.json` saved at combat entry. On combat engine crash mid-encounter, the snapshot is restored before the next session resumes.
2. **`.draft/` directory**: used during session_zero (draft character) and crash recovery. A successful commit replaces live with draft; a crash during session_zero leaves the draft and the load procedure can offer to resume or discard.
3. **Rotated backups** (optional, config-gated): every Nth save (default 10) copies `world.json` to `{save_root}/backups/world.{ts}.json`. Retention capped at `runtime.backup_retention` (default 5). Disabled by default in v1 to avoid bloat.

### 2.5 Full save procedure

```
full_save(state):
  set_save_in_progress()
  acquire_save_lock()
  try:
    update_session_metadata(state)
    bump_rng_seed_persistence_if_needed()

    # leaves first
    for npc in state.dirty_npcs:
      atomic_write_json(npcs/{id}.json, npc.as_dict())
    for faction in state.dirty_factions:
      atomic_write_json(factions/{id}.json, faction.as_dict())
    for location in state.dirty_locations:
      atomic_write_json(locations/{id}.json, location.as_dict())
    for clock in state.dirty_clocks:
      atomic_write_json(clocks/{id}.json, clock.as_dict())
    if state.history_dirty:
      atomic_write_json(history/{era_id}.json, era.as_dict())
    if state.rumors_dirty:
      atomic_write_json(rumors/rumors.json, rumors.as_dict())
    if state.journal_dirty:
      atomic_write_json(player/journal.json, journal.as_dict())

    # player
    if state.character_dirty:
      atomic_write_json(player/character.json, character.as_dict())

    # session log (append-like)
    atomic_write_json(session_log/{session_id}.json, session_log.as_dict())

    # anchor last
    atomic_write_json(world.json, world_state.as_dict())

    clear_dirty_flags(state)
    write_version_marker()
    log("save_complete", files_written=count, duration=elapsed)
  finally:
    release_save_lock()
    clear_save_in_progress()
```

Dirty-flag tracking: the sim engine and character modification paths set dirty flags on entities they modify. Full save consults these; unchanged entities are not rewritten. First-ever save or corrupted state forces full write of all entities.

### 2.6 Lightweight save (combat round)

During combat, a lightweight save writes only:
- `world.json` (with updated `active_scene.state.round`)
- `player/character.json` (updated condition_tracks, statuses, harm)
- `runtime/combat_snapshot.json` is NOT updated per round (it is the pre-combat baseline).

This avoids rewriting faction/npc/location files that cannot change during combat.

---

## Section 3 — Load Procedure

### 3.1 Step-by-step algorithm

```
load_save(save_root) -> LoadResult:
  1. preflight:
       - save_root exists, is a directory
       - .lock is not held by another process
       - clean up stale .tmp files older than 5 minutes
  2. read_version:
       - parse .version file
       - determine engine_version_written, schema_version_written
  3. classify:
       - per runtime §1.3
       - one of FRESH, PARTIAL, VALID, CORRUPT, VERSION_MISMATCH
  4. if classification == FRESH: return FreshResult()
  5. if classification == VERSION_MISMATCH:
       if schema_version_written > current_schema_version: fail with FutureSaveError
       else (older): dispatch to migrations (§4)
  6. load_world:
       - parse world.json
       - validate against World State schema
       - migrate if needed
  7. load_entities:
       - for each file under factions/, npcs/, locations/, clocks/:
           parse, validate, migrate if needed
           populate in-memory registry
  8. load_player:
       - if world.active_player_character:
           parse player/character.json
           validate against Character Sheet schema
           migrate if needed
  9. load_collections:
       - history/*.json -> world history log
       - rumors/rumors.json -> rumor registry
       - player/journal.json -> journal
  10. cross_reference_validation:
       - every faction.territory.* location_id exists in locations registry
       - every npc.location exists
       - every character.location exists
       - every character.relationships key resolves to an NPC id
       - every faction.leader resolves
       - every scheme.target resolves
       - any orphan reference: log as warning; attempt repair (§3.4)
  11. reconstruct_runtime_state:
       - seed RNG from world.rng_seed + session-entropy
       - open narration queue
       - load session_seq
  12. classify_post_load:
       - if world.active_scene.type == "combat_mode" and combat_snapshot.json exists:
           offer recovery dialog (continue from snapshot | resume in sim from post-combat)
       - if world.active_scene.unsafe_shutdown:
           offer crash recovery (runtime §2.6)
  13. return VALIDResult(state, warnings)
```

### 3.2 Validation pass

Full schema validation runs in step 6-9 for every loaded entity:

- Field types match schema.
- Required fields present.
- Enum values within allowed sets (AI profiles, combat registers, relationship standing range, corruption range, harm tiers, status names, etc.).
- schema_version field present.
- Cross-references (step 10) resolve.

Validation failures in VALID-classified saves halt load and route to CORRUPT handling. Validation warnings (recoverable via repair) log and continue.

### 3.3 Migration handling

If any loaded file's `schema_version < current_schema_version`:

1. Look up the migration chain (§4).
2. Apply migrations in order: 1.0 -> 1.1 -> 1.2 -> current.
3. After all migrations, rewrite the file atomically with the new schema_version.
4. Emit a `migrated` log entry.

If a file's `schema_version > current_schema_version`:

1. Halt load.
2. Print user-facing error: "This save was made with a newer version of the game (schema {v}). Upgrade or start a new save."
3. Exit with code 3.

### 3.4 Error recovery

**Corrupt file (single).** A parse error or schema violation in a single entity file:

- If the entity has a backup in `{save_root}/backups/`, offer restoration.
- Else: attempt regeneration from `data/worldseed/` if the entity id is a seeded entity (faction_id, location_id, clock_id that exists in the worldseed). NPCs specific to a save cannot be regenerated; their loss is reported.
- Missing NPC referenced by character.relationships: degrade the relationship to a placeholder record `{status: "lost_to_corruption", original_id: id, standing: 0}` and log.

**Corrupt world.json.** Fatal. Try backups. If no backup, abort with CorruptionError; user must inspect.

**Corrupt character.json.** Fatal for that character but not for the world. Offer archive and start new character in the world.

**Missing referenced file.** If a referenced file is missing but a regeneration source exists (worldseed), regenerate. Else mark the reference as orphan, log, allow load to proceed with degraded state.

**Version conflict (future version).** Halt. Preserve save unchanged.

### 3.5 Post-load settlement

After a successful load:

- `session_metadata.session_count` is NOT yet incremented (incremented at session close).
- `session_metadata.last_load_ts` is set to now.
- If `save_degraded_flag` or `narration_degraded_flag` is set from a previous session, surface a message to the player.
- If any migrations ran, the save is rewritten with new schema_version values.

---

## Section 4 — Migration Framework

### 4.1 Function pattern

Each migration is a pure function:

```
def migrate_{entity}_v{from}_to_v{to}(obj: dict) -> dict:
    """
    Migrate {entity} from schema_version {from} to {to}.
    Pure: does not touch disk, does not mutate input.
    Returns a new dict with schema_version = {to}.
    """
    new = deepcopy(obj)
    # field transformations
    new["schema_version"] = "{to}"
    return new
```

Each migration function:
- Lives in `emergence/persistence/migrations/v{from}_to_v{to}.py`.
- Exports a dict `MIGRATIONS`: `{entity_name: migration_function}`.
- May migrate one, several, or all entity types present in that schema transition.
- Is tested with round-trip tests on known-good older saves (§4.4).

### 4.2 Version registry and migration chain

`emergence/persistence/migrations/registry.py` holds:

```
SCHEMA_VERSIONS_IN_ORDER = ["1.0", "1.1", "1.2", ...]
CURRENT_VERSION = "1.0"   # at build-one

MIGRATION_CHAIN = {
  ("1.0", "1.1"): module_v1_0_to_v1_1,
  ("1.1", "1.2"): module_v1_1_to_v1_2,
  ...
}
```

The loader computes the path from an entity's `schema_version` to CURRENT_VERSION and applies migrations in sequence:

```
migrate_to_current(obj, entity_type):
  v = obj["schema_version"]
  while v != CURRENT_VERSION:
    next_v = next_version_after(v)
    migrator = MIGRATION_CHAIN[(v, next_v)].MIGRATIONS.get(entity_type)
    if migrator is None:
      # no-op migration: just bump version
      obj = {**obj, "schema_version": next_v}
    else:
      obj = migrator(obj)
    v = next_v
  return obj
```

### 4.3 Migration template

Reference template for a migration file:

```
# v{X}_to_v{Y}.py
"""
Migration from schema {X} to schema {Y}.
Changes:
  - Character: added field `breakthroughs` with default [].
  - NPC: renamed `trust_level` to `standing_with_player_default`.
"""

def migrate_character_{X}_to_{Y}(obj):
    new = dict(obj)
    new["breakthroughs"] = new.get("breakthroughs", [])
    new["schema_version"] = "{Y}"
    return new

def migrate_npc_{X}_to_{Y}(obj):
    new = dict(obj)
    if "trust_level" in new:
        new["standing_with_player_default"] = new.pop("trust_level")
    new["schema_version"] = "{Y}"
    return new

MIGRATIONS = {
    "character": migrate_character_{X}_to_{Y},
    "npc": migrate_npc_{X}_to_{Y},
}
```

### 4.4 Testing requirements

For each migration, a developer test fixture lives in `tests/fixtures/migrations/{from}_to_{to}/`:

- `input/` with sample pre-migration entity files (one per entity type being migrated).
- `expected/` with post-migration files.
- Test runs each migrator and diffs output against expected.

Migration tests must demonstrate:

- Round-trip: migrate_forward(obj) then validate against new schema; never lose information.
- Idempotence: running migrator on already-migrated object is a no-op (or rejected with clear error).
- Multi-step: a v1.0 save migrates cleanly through v1.1 to v1.2.

### 4.5 Failure handling

If a migration function raises:

- Log full traceback.
- Preserve the original file untouched on disk (the migration function is pure; partial migrations do not write to disk until the full chain succeeds).
- Halt load with MigrationError.
- User message: "Save could not be upgraded from schema {from}. Original save preserved. See log for details."
- Exit code 3.

If migration completes but validation of the migrated object fails:

- Same handling: original preserved, load halted, error surfaced.

Migration must not lose information. If a migration would discard a field that is not demonstrably replaceable, the migration must fail and preserve the file (per interface-spec §Schema Versioning).

---

## Section 5 — Multi-Character World

### 5.1 Shared vs character-specific state

**Shared world state (persists across characters):**

- `world.json` minus `active_player_character` and `active_scene`
- All `factions/*.json`
- All `locations/*.json`
- All `clocks/*.json`
- All `history/*.json`
- `rumors/rumors.json`
- All `npcs/*.json` except those marked `origin: "player_relation"` (relatives, lovers, etc. seeded by a specific character's session zero)

**Character-specific state:**

- `player/character.json`
- `player/journal.json`
- NPCs with `origin: "player_relation"` where `relation_of: {character_id}` — these live at `archived_characters/{character_id}/relations/{npc_id}.json` after archival.

**Session state (not character-specific but session-scoped):**

- `session_log/*.json`
- `runtime/*`

### 5.2 Inheritance of altered world by new characters

When a new character is created in a world that has seen previous play:

- The world state is exactly what the previous character left it.
- All factions have their current standings, clock states, territories.
- All locations have their current controllers, populations, states.
- NPCs the previous character interacted with *remember* those interactions in their own `memory` field. The previous character appears by name in NPC memories as a dead person, a departed person, or a present person depending on their final status. A new character encountering these NPCs may hear about the former PC as rumor.
- Rumors about the previous character's actions remain in `rumors.json`, decaying per normal rumor rules.
- The previous character's faction heat is zeroed on the new character (heat is personal). Faction standings for the new character default to `faction.standing_with_player_default`.
- The new character's session zero has access to choose their starting location from all locations the world knows about, not just seed locations.

### 5.3 Character history archive

On character death (or explicit archive):

```
archive_character(character_id):
  mkdir archived_characters/{character_id}/
  move player/character.json -> archived_characters/{character_id}/character.json
  move player/journal.json -> archived_characters/{character_id}/journal.json
  create archived_characters/{character_id}/epitaph.json:
    {
      character_id, name, species, birth_in_world_date, death_in_world_date,
      current_age_at_death, cause_of_death,
      final_location, final_tier, final_relationships_summary,
      final_goals_status: [goal_id: "completed"|"abandoned"|"in_progress"],
      total_session_count, lifetime_years, lifetime_real_seconds,
      notable_history: top-N events by weight,
      final_journal_snapshot: last 50 journal entries
    }
  gather NPC records with origin.relation_of == character_id:
    for each: move npcs/{id}.json -> archived_characters/{character_id}/relations/{id}.json
  world.active_player_character = null
  world.past_characters.append(character_id)
```

Archived characters are read-only; their state does not change. The world continues to remember them via NPC memories and rumors (not archives).

### 5.4 Multi-character discovery

- The `list` subcommand of the runtime (§1 of runtime-architecture) enumerates both the current character and archived characters, showing birth/death dates, lifetime length, cause of death, and a one-line epitaph.
- The player may start any number of new characters in the same world, serially.
- Two characters cannot be active simultaneously in the same world.

### 5.5 World resets

A "new world" is implemented by creating a new save_root from worldseed. The `new` subcommand with `--world PATH` where PATH does not exist creates a new world at that path. World reset is not an in-game action; it is a file operation.

---

## Section 6 — Time-Skip Handling

### 6.1 Game does not advance when not played

In-world time is `world.current_time`. It advances only when the runtime explicitly advances it. The real-world clock is not coupled to in-world time. A player who does not play for three months returns to a world that has not moved.

`session_metadata.last_save` is real-time for bookkeeping; it does not influence in-world time.

### 6.2 Resume procedure

On session resume:

- Load state as §3.
- In-world time is exactly `world.current_time` from last save.
- The opening framing narration (scene_type `scene_framing`, trigger `session_resume`) references the elapsed real time only if the player requests it (via `/time` which prints both); the in-world fiction treats the resume as continuous.
- The framing payload's `time_since_last_scene` is the in-world time gap since the last scene, which for a resume is typically "moments later" or "after a night's sleep" depending on what the previous session's last scene was.

### 6.3 Optional time-skip command

A player may explicitly elapse in-world time via `/skip {duration}`:

- `/skip 1d`, `/skip 1w`, `/skip 1m`, `/skip 3m`, `/skip 6m`, `/skip 1y` accepted durations (config-capped).
- Precondition: character is in a safe location (threat_level ≤ 2) and has no active scene.
- Behavior:
  1. Runtime computes the number of ticks corresponding to the duration.
  2. Runs the tick loop for that many ticks with the player in a `skipping` context flag — activities default to rest/shelter; no encounters trigger unless a faction-driven event specifically seeks out the character.
  3. Character accumulates the expected drifts: age advances, relationships drift per NPC memory decay, resources are consumed per daily rate, heat decays at baseline rate, injuries heal on tier-1 and tier-2 schedules, powers are not practiced so power_use counters do not increment.
  4. A single `time_skip` narration payload is emitted summarizing the elapsed period.
  5. A new `scene_framing` narration establishes the current moment.
- Cap per skip call: 1 in-world year. Beyond this, multiple calls are required (by design, to make long skips deliberate).
- Config: `sim.time_skip_enabled` (default true), `sim.time_skip_max_duration_days` (default 365).

### 6.4 Time accounting

Every save writes updated `session_metadata`:
- `total_playtime_real_seconds += real_elapsed_this_session`
- `character_lifetime_years = (world.current_time minus character.birth_date) / 365.25` recomputed

The player can see both via `/time`:
- "In-world: {current_time}. Character is {current_age}, {lifetime_years} years since manifestation."
- "Real-world time played: {playtime_formatted}. Sessions: {session_count}."

---

## Section 7 — Journal and History

### 7.1 Journal overview

The journal at `player/journal.json` is the player's in-game memory aid. It is auto-populated by the engine from significant events, viewable via the `/journal` meta-command, and part of the character's persisted state (travels with the character into the archive on death).

The journal is distinct from:
- `character.history` (mechanical log of events with structured consequences, used by the engine).
- `session_log/*.json` (operational session records, not in-fiction).

The journal is the player's prose-y, readable record.

### 7.2 Format

```json
{
  "schema_version": "1.0",
  "character_id": "...",
  "entries": [
    {
      "id": "journal_00042",
      "in_world_date": "T+2y 1m 14d",
      "real_ts": "2025-10-04T19:14:00Z",
      "category": "encounter|travel|relationship|faction|discovery|death|breakthrough|personal",
      "title": "Short title (<= 60 chars)",
      "body": "One paragraph of prose, 30-120 words, written from the character's perspective as journal prose.",
      "tags": ["location:{id}", "npc:{id}", "faction:{id}", ...],
      "auto_generated": true,
      "source_event_id": "history entry id or null"
    }
  ],
  "entry_count": 42,
  "last_updated": "..."
}
```

### 7.3 Auto-population

The engine produces journal entries from the `history` field of the character and select world events. Triggers:

| Event | Journal category |
|---|---|
| Arrival at a new location for the first time | travel |
| Significant NPC interaction (relationship standing change, first meeting, death) | relationship |
| Major combat outcome (victory or notable defeat) | encounter |
| Breakthrough (tier advancement) | breakthrough |
| Goal progress change | personal |
| Faction heat threshold crossed | faction |
| Major world event affecting character (faction takeover in current region, clock completion) | faction |
| Discovery of major location feature or secret | discovery |
| Character death | death (final entry) |

Journal prose is produced by the narrator as a dedicated payload type `journal_entry` (not in the primary scene_type list; it is a narration sub-type emitted out-of-band and not subject to the scene flow). Per-entry budget: 30-120 words, first-person register of the character where appropriate.

*[This journal_entry narration sub-type is a deliberate extension of the narrator system; it uses the same queue mechanism as primary scene types but does not advance scene state.]*

### 7.4 Presentation

The `/journal` command prints an index:

```
Journal — 42 entries
Most recent:
  journal_00042  T+2y 1m 14d  breakthrough  "The third time"
  journal_00041  T+2y 1m 13d  encounter     "The overpass"
  journal_00040  T+2y 1m 10d  travel        "Arriving in Yonkers"
  …
Type /journal {id} for full entry, or /journal {category} to filter.
```

Filters:
- `/journal recent [N]` — last N entries (default 10).
- `/journal travel` — all entries in category.
- `/journal npc:{id}` — entries tagged with an NPC.
- `/journal search {keyword}` — simple substring match across body and title.

Full entry printing includes in-world date, title, body, and tags.

### 7.5 Retention

- Journal entries are permanent. The journal does not automatically prune.
- Soft limit: 1000 entries; at 1000, the oldest 50 are compressed into a single summary entry titled "Before {date}", preserving the rest.
- On character death, the journal is archived alongside the character and is readable via `list` subcommand inspection.

### 7.6 Player-authored entries

Out of scope for v1. [NEEDS RESOLUTION: whether to allow `/journal write {text}` player-authored entries in a later pass.]

---

## Design Decisions

- **Per-file atomicity, no cross-file transactions.** Ordered writes (leaves -> anchor) approximate consistency; full ACID is unnecessary for single-user solo play and would complicate the runtime without clear benefit.
- **`world.json` is the anchor.** Written last; load routes consistency assumptions through it. If a save crashed mid-write, a stale world.json + fresh leaves degrades to a recoverable warning rather than corruption.
- **Dirty flags for incremental saves.** Keeps full-save cost manageable even with dozens of faction/NPC/location files. Unchanged entities skip writes.
- **Combat round saves are lightweight.** Writing faction files between rounds would be wasteful; combat cannot change them.
- **No backup rotation by default.** Shipping with complexity off; optional via config. Crashes are handled by `.draft/` and pre-combat snapshot; backups are belt-and-suspenders.
- **Migrations are pure functions, tested with fixtures.** No in-place mutation; failed migrations preserve originals; chain is linear and deterministic.
- **Shared world, per-character personal state.** The world persists across characters because the design brief demands it (world advances whether the player plays or not; factions remember; new characters inherit the altered world). Personal relationships and journal are character-scoped.
- **In-world time does not advance while not played.** The player has limited hours; coupling real-time to in-world time would make absences punishing without narrative benefit. `/skip` provides explicit long-skip capability.
- **Journal is auto-populated, player-readable, character-persistent.** Gives the player a readable record of their life without manual bookkeeping, satisfies the "life lived across decades" fantasy by making that life reviewable.
- **`archived_characters/` archive pattern.** Archives are read-only; archival is a one-way move; past characters surface through world memory (NPC memories, rumors, history) rather than through live pointers.
- **Journal narrations use the narration queue too.** Same contract, same discipline; avoids a second narrator path. Tagged as out-of-band in the queue so scene continuity is not disturbed.

## [NEEDS RESOLUTION]

- [NEEDS RESOLUTION: precise tick backlog behavior during `/skip` vs. normal play — sim-spec should specify. This doc assumes ticks run but events of scope `local` affecting character default to neutral outcomes during skip.]
- [NEEDS RESOLUTION: rumor decay algorithm is not specified here — sim-spec responsibility.]
- [NEEDS RESOLUTION: whether `archived_characters/` should be world-shared or per-save-root — this spec places them per-save-root, which is the simplest reading.]
- [NEEDS RESOLUTION: player-authored journal entries: whether v1 supports `/journal write {text}`. Current doc defers.]
- [NEEDS RESOLUTION: journal_entry narration sub-type — extends the eight primary scene_types; prompt-management.md does not define it as a primary type. Either add it there, or keep it a simple templated non-narrator entry. Current doc assumes narrator-produced with light prompting.]
