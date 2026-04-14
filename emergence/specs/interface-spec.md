# Emergence Interface Specification

This document defines the schemas that all subsystems of Emergence must share. It is the contract between the combat engine, the simulation engine, the runtime layer, the narrator, and persistence. Specifications must implement these schemas exactly. Implementations must conform.

Schemas are JSON-compatible structures described in prose with typed field lists. Every persisted entity must support lossless round-trip through serialize/deserialize. Every schema includes a `schema_version` field for future migration.

---

## Core Schemas

### Character Sheet

Represents a player character. Persisted in `player/character.json`.

**Fields:**

- `id` (string, unique): stable identifier
- `schema_version` (string): e.g., "1.0"
- `name` (string): character's name
- `species` (string): either `"human"` or a metahuman species id from the setting's species registry
- `age_at_onset` (integer): character's age at T=0
- `current_age` (integer): character's current age in years
- `attributes` (object): character's base attributes
  - `strength` (integer, die size: one of 4, 6, 8, 10, 12)
  - `agility` (integer, die size)
  - `perception` (integer, die size)
  - `will` (integer, die size)
  - `insight` (integer, die size)
  - `might` (integer, die size)
- `condition_tracks` (object): damage tracks, segments filled out of five
  - `physical` (integer, 0-5)
  - `mental` (integer, 0-5)
  - `social` (integer, 0-5)
- `harm` (list of objects): persistent consequences
  - `tier` (integer, 1-3): 1 = scene, 2 = persistent until treated, 3 = permanent or fatal
  - `description` (string): what the harm is
  - `persistent` (boolean): whether the harm carries across scenes
  - `source` (string): what caused the harm
  - `date_acquired` (string): in-world date
- `powers` (list of strings): power ids from the power registry
- `power_category_primary` (string): one of seven power category ids
- `power_category_secondary` (string or null)
- `tier` (integer, 1-10): character's current power tier
- `tier_ceiling` (integer, 1-10): maximum tier reachable without breakthrough
- `breakthroughs` (list of objects): record of tier advancements
  - `date` (string, in-world)
  - `from_tier` (integer)
  - `to_tier` (integer)
  - `cost` (string): what the breakthrough marked the character with
  - `trigger` (string): what caused it
- `heat` (object): faction id mapped to integer heat level
- `corruption` (integer, 0-6): corruption segments filled
- `relationships` (object): npc id mapped to relationship state
  - `standing` (integer, -3 to +3): -3 hostile, 0 neutral, +3 loyal/loved
  - `history` (list of event records): significant interactions
  - `current_state` (string): e.g., "estranged", "collaborators", "lovers", "blood feud"
  - `trust` (integer, 0-5): how much the NPC trusts the character
- `inventory` (list of item objects)
  - `id` (string)
  - `name` (string)
  - `description` (string)
  - `quantity` (integer)
  - `mechanical_effect` (string or null): any game-mechanical properties
- `location` (string): location id where character currently is
- `history` (list of significant event records)
  - `date` (string, in-world)
  - `category` (string): e.g., "combat", "political", "personal", "discovery"
  - `description` (string)
  - `consequences` (list): structured effects applied
- `statuses` (list of objects): active status effects
  - `name` (string): one of the closed status list
  - `duration` (integer or string): remaining duration or condition
  - `source` (string): what applied it
- `skills` (object): skill id mapped to proficiency (integer, 0-10)
- `resources` (object): resource name mapped to quantity (for holdings, wealth, followers, etc.)
- `goals` (list of objects): character's active narrative goals
  - `id` (string)
  - `description` (string)
  - `progress` (integer, 0-10)
  - `pressure` (integer, 0-5): how much this goal pushes the character
- `session_zero_choices` (object): record of choices made in character creation, for reference

### Combatant

Extends Character Sheet for non-player combatants. Not persisted in the save directly; generated per encounter. Same fields as Character Sheet plus:

**Additional fields:**

- `side` (string): one of `"enemy"`, `"ally"`, `"neutral"`
- `ai_profile` (string): one of `"aggressive"`, `"defensive"`, `"tactical"`, `"opportunist"`, `"pack"`
- `exposure_track` (integer): current exposure fill
- `exposure_max` (integer): maximum exposure before Exposed status applies
- `affinity_table` (object): damage_type id mapped to one of `"vulnerable"`, `"neutral"`, `"resistant"`, `"immune"`, `"absorb"`
- `abilities` (list of strings): ability ids available in combat
- `template_id` (string): references the enemy template registry
- `retreat_conditions` (list of strings): conditions under which this combatant tries to flee
- `parley_conditions` (list of strings): conditions under which this combatant will accept terms
- `motive` (string): what this combatant wants from the encounter
- `threat_assessment` (object): how the combatant perceives other combatants' threat levels

---

### Encounter Spec

Generated by the simulation engine, consumed by the combat engine. Represents a combat encounter about to begin.

**Fields:**

- `id` (string, unique per encounter): stable identifier
- `schema_version` (string)
- `generated_at` (string): in-world timestamp
- `location` (string): location id
- `player` (Character Sheet object): full, not reference
- `enemies` (list of Combatant objects)
- `allies` (list of Combatant objects, optional): if the player has combat allies
- `terrain_zones` (list of zone objects, optional, 3-4 expected when present)
  - `id` (string)
  - `name` (string)
  - `properties` (list of strings): e.g., `"exposed"`, `"cover"`, `"hazardous"`, `"objective"`
  - `description` (string): sensory texture
- `stakes` (string): what is contested in this encounter
- `win_conditions` (list of condition objects): what counts as player victory
- `loss_conditions` (list of condition objects): what counts as player defeat
- `escape_conditions` (list of condition objects): how the player can disengage
- `parley_available` (boolean): whether negotiated outcomes are possible in this encounter
- `world_context` (object): compact summary of relevant world state
  - `faction_situation` (string): brief faction context
  - `recent_events` (list of strings): relevant recent history
  - `heat_levels` (object): player's current heat with relevant factions
  - `clock_states` (object): relevant macro clock states
  - `scene_clock` (integer or null): if a scene-level pressure clock is running (e.g., hive attention)
- `combat_register` (string): one of `"human"`, `"creature"`, `"eldritch"`
- `opening_situation` (string): the setup the narrator describes as combat begins

**Condition object** (used in win/loss/escape conditions):

- `type` (string): e.g., `"defeat_all"`, `"defeat_specific"`, `"survive_rounds"`, `"reach_zone"`, `"convince_parley"`, `"break_contact"`, `"protect_target"`
- `parameters` (object): type-specific parameters

---

### Combat Outcome

Returned by the combat engine, ingested by the simulation engine. Represents the result of a completed encounter.

**Fields:**

- `encounter_id` (string): references the originating Encounter Spec
- `schema_version` (string)
- `resolution` (string): one of `"victory"`, `"defeat"`, `"parley"`, `"escape"`, `"truce"`, `"stalemate"`, `"other"`
- `rounds_elapsed` (integer)
- `player_state_delta` (object): changes to apply to the player's Character Sheet
  - `condition_changes` (object): track name mapped to delta
  - `harm_added` (list of Harm objects)
  - `resources_spent` (object): resource mapped to delta
  - `heat_accrued` (object): faction id mapped to delta
  - `corruption_gained` (integer)
  - `statuses_persisting` (list of status objects): statuses carrying past the encounter
  - `powers_used` (object): power id mapped to usage count for progression tracking
  - `breakthrough_triggered` (boolean)
  - `breakthrough_details` (object or null): if breakthrough occurred, details
  - `skill_usage` (object): skill id mapped to usage for progression
  - `injuries_healed` (list): any injuries resolved during combat
- `enemy_states` (list of objects): final state of each enemy
  - `enemy_id` (string)
  - `final_state` (string): one of `"alive"`, `"dead"`, `"fled"`, `"surrendered"`, `"incapacitated"`, `"transformed"`
  - `relevant_details` (object): e.g., parley terms accepted, knowledge revealed, death cause
  - `body_disposition` (string or null): for dead combatants, what happened to the body
- `narrative_log` (list of turn records)
  - `turn` (integer)
  - `actor_id` (string)
  - `action` (Action object)
  - `payload` (object): structured data for narration
  - `narration` (string): the prose produced by the narrator
- `world_consequences` (list of structured state change records)
  - `type` (string): e.g., `"faction_standing_change"`, `"location_state_change"`, `"npc_memory_update"`, `"clock_advance"`, `"rumor_generated"`, `"witness_recorded"`, `"territory_contested"`
  - `parameters` (object): type-specific data
  - `scope` (string): one of `"local"`, `"regional"`, `"global"`
  - `visibility` (string): one of `"known"`, `"rumored"`, `"hidden"`

---

### Action

Internal to the combat engine. Represents a single combat action taken by any combatant.

**Fields:**

- `actor_id` (string)
- `verb` (string): one of `"Attack"`, `"Power"`, `"Assess"`, `"Maneuver"`, `"Parley"`, `"Disengage"`, `"Finisher"`, `"Defend"`
- `target_id` (string or null)
- `power_id` (string or null): if verb is Power or Finisher
- `target_zone` (string or null): if zones are active
- `modifiers` (object): situational modifiers
- `declared_at_round` (integer)

---

### Narrator Payload

Produced by engines, consumed by the narrator (Claude at runtime). Triggers prose generation.

**Fields:**

- `schema_version` (string)
- `scene_type` (string): one of `"combat_turn"`, `"scene_framing"`, `"situation_description"`, `"dialogue"`, `"transition"`, `"character_creation_beat"`, `"time_skip"`, `"death_narration"`
- `state_snapshot` (object): compact, only what the narrator needs for this moment
- `register_directive` (string): references the narration style guide, e.g., `"standard"`, `"eldritch"`, `"intimate"`, `"action"`, `"quiet"`
- `output_target` (object):
  - `desired_length` (object): `{min_words: int, max_words: int}`
  - `format` (string): one of `"prose"`, `"dialogue"`, `"mixed"`, `"terse"`
- `forbidden` (list of strings): things the narrator must not do (e.g., `"invent damage not in payload"`, `"describe characters not present"`, `"resolve the anomalous eldritch question"`)
- `context_continuity` (object):
  - `last_narration_summary` (string): one-sentence summary of the previous narration
  - `scene_history_summary` (string): compact summary of the current scene so far
  - `key_callbacks` (list of strings): specific details from earlier in the scene to maintain continuity

---

## Simulation Schemas

### Faction

Persisted in `factions/{faction_id}.json`.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `display_name` (string)
- `type` (string): e.g., `"noble_house"`, `"warlord_holding"`, `"merchant_guild"`, `"religious_order"`, `"metahuman_polity"`, `"survivor_commune"`
- `current_leader` (object): npc id and brief context
- `territory` (object):
  - `primary_region` (string)
  - `secondary_holdings` (list of location ids)
  - `contested_zones` (list of location ids)
- `population` (object):
  - `total` (integer)
  - `military_capacity` (integer)
  - `powered_fraction` (float)
- `power_profile` (object):
  - `dominant_categories` (list of power category ids)
  - `typical_tier_range` (tuple of two integers)
  - `standout_individuals` (list of npc ids)
- `economic_base` (object):
  - `primary_resources` (list of strings)
  - `trade_relationships` (list of faction ids with relationship type)
  - `currency_dependencies` (list of strings)
- `goals` (list of goal objects, ranked)
  - `id` (string)
  - `description` (string)
  - `weight` (float): importance in decision-making
  - `progress` (integer, 0-10)
- `current_schemes` (list of scheme objects)
  - `id` (string)
  - `description` (string)
  - `target` (string): target id or description
  - `progress` (integer, 0-10)
  - `expected_completion` (string): in-world date estimate
- `internal_tensions` (list of tension objects)
- `external_relationships` (object): faction id mapped to relationship object
  - `disposition` (integer, -3 to +3)
  - `history` (list of event references)
  - `active_agreements` (list of strings)
  - `active_grievances` (list of strings)
- `standing_with_player_default` (integer, -3 to +3)
- `known_information` (list of strings): what everyone knows
- `secret_information` (list of strings): GM-only, tagged
- `narrative_voice` (string): single paragraph describing how this faction feels
- `last_tick_actions` (list): actions taken in the most recent tick
- `resources` (object): for tick-level resource tracking

### NPC

Persisted in `npcs/{npc_id}.json`.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `display_name` (string)
- `faction_affiliation` (object):
  - `primary` (string or null): faction id
  - `secondary` (list of faction ids)
- `location` (string): current location id
- `schedule` (object): location transitions by time of day or day of week
- `species` (string): `"human"`, species id, `"corrupted"`, or other
- `age` (integer)
- `manifestation` (object):
  - `category` (string): power category id
  - `tier` (integer, 1-10)
  - `specific_abilities` (list of power ids)
  - `circumstance_of_manifestation` (string)
- `role` (string): public-facing function
- `goals` (list of goal objects, ranked)
- `relationships` (object): npc/player id mapped to relationship state
- `resources` (list of resource objects): possessions, leverage, knowledge
- `knowledge` (list of knowledge objects): information this NPC has
  - `topic` (string)
  - `detail` (string)
  - `will_share_if` (list of conditions)
- `personality_traits` (list of strings)
- `current_concerns` (list of strings)
- `memory` (list of memory objects): significant events this NPC remembers
  - `date` (string)
  - `event` (string)
  - `emotional_weight` (integer, 0-10)
  - `decay_rate` (float): how fast this memory fades
- `standing_with_player_default` (integer, -3 to +3)
- `what_they_want_from_the_player` (string): default; shifts with play
- `voice` (string): paragraph on speech patterns, manner, specificity
- `hooks` (list of strings): ways this NPC might enter play
- `status` (string): one of `"alive"`, `"dead"`, `"missing"`, `"transformed"`, `"displaced"`

### Location

Persisted in `locations/{location_id}.json`.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `display_name` (string)
- `type` (string): e.g., `"city"`, `"town"`, `"fortress"`, `"ruin"`, `"wilderness_zone"`, `"faction_holding"`, `"natural_feature"`, `"charged_zone"`
- `region` (string)
- `coordinates` (object): approximate, relative to real-world geography
- `controller` (string or null): faction id, or `"contested"`, or `"unclaimed"`
- `population` (integer)
- `defensive_capacity` (integer, 0-10)
- `economic_state` (string): one of `"thriving"`, `"sufficient"`, `"strained"`, `"failing"`, `"abandoned"`
- `resources` (list of resource objects): what can be scavenged, traded, extracted
- `notable_features` (list of strings): landmarks, unique structures, specific dangers
- `connections` (list of connection objects)
  - `to_location_id` (string)
  - `travel_mode` (string)
  - `travel_time` (string): e.g., "half a day on foot"
  - `hazards` (list of strings)
- `current_events` (list of strings): what's happening here now
- `dangers` (list of strings): what might kill a visitor
- `opportunities` (list of strings): what a visitor might want
- `description` (string): two paragraphs of sensory texture
- `npcs_present` (list of npc ids)
- `ambient_conditions` (object):
  - `weather` (string)
  - `time_of_day` (string)
  - `season` (string)
  - `threat_level` (integer, 0-5)
- `history` (list of event references): significant events that happened here
- `last_tick_updates` (list): state changes from the most recent tick

### Clock

Persisted in `clocks/{clock_id}.json`. Represents a macro-level world pressure tracker.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `display_name` (string)
- `current_segment` (integer): segments filled
- `total_segments` (integer)
- `advance_conditions` (list of condition objects): triggers that fill segments
- `advance_rate` (object): baseline segments per in-world year with modifiers
- `completion_consequences` (list of consequence objects): what happens when clock fills
- `reset_conditions` (list of condition objects): what rolls the clock back
- `interactions` (list of objects): how this clock affects or is affected by other clocks
- `narrative_description` (string): paragraph on what this clock represents
- `last_advancement` (object): most recent segment fill with cause

### Tick Event

Internal to sim engine. Emitted during world ticks for logging and downstream processing.

**Fields:**

- `tick_timestamp` (string): in-world date
- `entity_type` (string): one of `"faction"`, `"npc"`, `"location"`, `"clock"`, `"threat"`, `"environment"`
- `entity_id` (string)
- `event_type` (string)
- `details` (object)
- `consequences` (list of state change records)
- `visibility` (string): `"world"`, `"regional"`, `"local"`, `"hidden"`

### Situation

Produced by the sim's situation generator, consumed by the narrator when the player enters a location or takes an action.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `location` (string): location id
- `timestamp` (string): in-world date and time
- `present_npcs` (list of npc ids)
- `ambient` (object): weather, time of day, season, specific sensory details
- `recent_events` (list of strings): what has happened here recently that matters
- `tension` (string): what is at stake in this moment
- `player_choices` (list of choice objects): available actions
  - `id` (string)
  - `description` (string)
  - `type` (string): e.g., `"dialogue"`, `"action"`, `"observation"`, `"travel"`, `"activity"`
  - `consequences_hint` (string or null): optional hint about likely outcome
- `could_happen_next` (list of strings): potential developments
- `encounter_probability` (float, 0-1): likelihood this situation will trigger combat based on player choices

---

## Runtime Schemas

### World State

Persisted in `world.json` at save root.

**Fields:**

- `schema_version` (string)
- `current_time` (object):
  - `in_world_date` (string): e.g., "T+1y 3m 14d"
  - `onset_date_real` (string): real-world calendar reference for T=0
  - `year` (integer): years since onset
- `active_scene` (object or null): current scene if mid-session
  - `type` (string): `"sim_mode"`, `"combat_mode"`, `"framing"`, `"session_zero"`
  - `scene_id` (string)
  - `state` (object): scene-specific state
- `session_metadata` (object):
  - `session_count` (integer)
  - `total_playtime_real_seconds` (integer)
  - `last_save` (string): ISO timestamp
  - `character_lifetime_years` (float): in-world years played on current character
- `worldline_id` (string): references the simulation worldline
- `active_player_character` (string): character id
- `past_characters` (list of character ids): previous characters in this world

### Save

The full save directory structure.

```
save_root/
  world.json
  player/
    character.json
    journal.json  (optional player-accessible event log)
  factions/
    {faction_id}.json
  npcs/
    {npc_id}.json
  locations/
    {location_id}.json
  clocks/
    {clock_id}.json
  history/
    {era_id}.json
  rumors/
    rumors.json
  session_log/
    {session_id}.json  (one per completed session, for continuity reference)
```

Every file includes a `schema_version`. Corrupt files are handled by the load procedure (report and recover where possible; fail gracefully if unrecoverable).

---

## Content Schemas

### Power

Referenced by id from character sheets and narration payloads. Defined in `data/powers/{power_id}.json` or an equivalent registry.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `name` (string)
- `category` (string): one of seven power category ids
- `tier` (integer, 1-10): minimum tier to manifest this power
- `cost` (object):
  - `condition` (object): track name mapped to damage
  - `heat` (object): faction id mapped to heat gain
  - `corruption` (integer): corruption gain
- `damage_type` (string): one of seven damage type ids matching categories
- `effect` (object):
  - `type` (string): one of `"damage"`, `"status"`, `"utility"`, `"movement"`, `"combined"`
  - `parameters` (object): type-specific
- `description` (string): narrative description
- `prerequisite` (string or null): power id that must be manifested first
- `usage_scope` (string): one of `"combat"`, `"sim"`, `"both"`
- `visibility` (string): one of `"visible"`, `"subtle"`, `"variable"`

### Enemy Template

Referenced by id in encounter generation. Defined in `data/enemies/{template_id}.json`.

**Fields:**

- `id` (string)
- `schema_version` (string)
- `display_name` (string)
- `register` (string): one of `"human"`, `"creature"`, `"eldritch"`
- `attribute_defaults` (object): attribute name to die size
- `condition_track_defaults` (object)
- `affinity_table` (object)
- `ai_profile` (string)
- `exposure_max` (integer)
- `abilities` (list of ability ids)
- `powers` (list of power ids, if applicable)
- `retreat_conditions` (list of strings)
- `parley_conditions` (list of strings)
- `description` (string): sensory texture for narration
- `tactics_note` (string): brief note on how this enemy fights

---

## Schema Versioning and Migration

All persisted files and all schema-bearing runtime objects include a `schema_version` field. Initial version is `"1.0"`. Schema changes require a migration function that accepts an older-version object and produces a current-version object. Migration functions live in a dedicated module and run automatically on load.

When a file's version is newer than the running code supports, the load procedure fails with a clear error. When a file's version is older, migration runs automatically. Migration must not lose information; if information would be lost, migration fails and the file is preserved unchanged for manual inspection.

---

## Modification Authority

The engines have explicit authority over specific fields. Violations are bugs.

**Combat engine modifies:**
- Character sheet: `condition_tracks`, `harm`, `statuses`, `powers_used` counters during combat
- Combatant objects: all fields during their combat lifecycle
- Produces Combat Outcome

**Simulation engine modifies:**
- Character sheet: `location`, `relationships`, `heat`, `inventory` (non-combat), `history`, `resources`, `skills` via activity outcomes
- Faction, NPC, Location, Clock entities: all fields via tick logic
- Emits Tick Events
- Produces Encounter Specs and Situations

**Character creation modifies:**
- Character sheet: entire object during session zero only

**Runtime modifies:**
- World State: `current_time`, `active_scene`, `session_metadata`
- Coordinates handoffs between subsystems
- Routes narrator payloads and collects narration

**Narrator (Claude at runtime) modifies:**
- Nothing. The narrator reads payloads and produces prose. All state changes originate from engines.

No engine reaches across these boundaries. Cross-boundary state changes happen only through the defined handoff objects (Encounter Spec, Combat Outcome, Tick Event, Situation).

---

## Integration Points

1. **Sim to Combat:** Sim generates Encounter Spec from world state, hands to Combat Engine.
2. **Combat to Sim:** Combat Engine returns Combat Outcome; Sim ingests and applies `world_consequences`.
3. **Engine to Narrator:** Either engine emits Narrator Payload; Runtime routes to narrator; narration returned as string and attached to payload for logging.
4. **Runtime to Engine:** Runtime routes player input to active engine based on current mode.
5. **Runtime to Persistence:** Runtime triggers save; all entities serialize per schemas; directory structure created atomically.
6. **Persistence to Runtime:** Runtime loads on resume; all entities deserialize with migration if needed; validation before play resumes.

---

## Constants

Certain values are referenced across subsystems and must be consistent.

**Power categories (seven):**
- `physical_kinetic`
- `perceptual_mental`
- `matter_energy`
- `biological_vital`
- `temporal_spatial`
- `eldritch_corruptive`
- (seventh category to be resolved in content; use `temporal_spatial` as placeholder if needed during build)

**Damage types:** match power category ids one-to-one.

**Status effects (closed list of seven):**
- `bleeding`
- `stunned`
- `shaken`
- `burning`
- `exposed`
- `marked`
- `corrupted`

**AI profiles (five):**
- `aggressive`
- `defensive`
- `tactical`
- `opportunist`
- `pack`

**Combat registers (three):**
- `human`
- `creature`
- `eldritch`

**Relationship standing (seven values):**
- `-3` hostile
- `-2` antagonistic
- `-1` cold
- `0` neutral
- `1` cordial
- `2` warm
- `3` loyal

**Corruption thresholds:**
- `0` baseline
- `1-2` touched
- `3-4` changed
- `5` transforming
- `6` transformed (character becomes non-player entity)

**Harm tiers:**
- `1` scene (clears at encounter end)
- `2` persistent (clears when treated)
- `3` permanent (never fully clears; may be fatal)

---

## Validation Requirements

On every state change, engines must verify:

- Schemas conform to specified field types and value ranges
- Cross-reference ids exist in the relevant registries (faction, npc, location, power, status)
- Modifications stay within the authorizing engine's scope
- Schema versions match current code
- Required fields are present

Validation failures are reported to the runtime, logged, and halt further state changes until resolved. Silent fallback is forbidden; visible failure is required.

---

## Non-Negotiable Properties

These properties must hold for any conforming implementation:

1. **Deterministic resolution:** Given identical state and identical seed, the combat engine produces identical outcomes. Given identical state, the sim engine produces identical tick results. Narration is the only non-deterministic layer.

2. **State/narration separation:** The narrator never originates state changes. The engines never produce prose. Payloads are the only currency between them.

3. **Persistence completeness:** Any state that affects gameplay must persist. Round-trip through save/load must preserve game-relevant behavior exactly.

4. **Schema conformance:** Every object passed between subsystems conforms to its specified schema. Schema violations are bugs.

5. **Modification authority:** No engine modifies data outside its authorized scope.

6. **Context budget discipline:** Narrator payloads contain only what's needed for the current scene. Bulk state stays in files, not in context.

Specifications that contradict these properties are invalid. Implementations that violate these properties are broken.
