# Quest Design Guidelines

For narrators composing Quest JSON objects the engine validates.

A Quest is the unit of play: one story, finishable, with a named failure
state the engine can check. Not a plot. A situation.

---

## What the engine expects

Generate, in a single bundled response:

- **8 Quest JSON objects** (see schema below).
- **`backstory_ids`** — list of 4 quest ids flagged as backstory.
- **`backstory_prose`** — a ~1200-1800-word narration of the PC's year
  since the Onset that weaves the four backstory quests into lived
  history. The player reads this **alongside** the four urgent-quest
  options and makes the urgent pick with the backstory fresh in mind.

Split by role:

- **4 backstory quests** (narrator-flagged): establish what the PC has
  been doing for the past year. These are the quests you narrate through
  `backstory_prose`.
- **4 urgent-offer quests** (remaining): the player picks one. This quest
  opens active play.

The **urgent quest must be physically dangerous**. All four urgent-offer
quests must pass urgent-quest validation so any of them can be picked.

### Backstory prose rules

- Word count: 1200-1800 (soft slack 300).
- Weave the four backstory quests in as remembered seasons, not
  blow-by-blow summaries. Show texture: weather, sleep, rooms, people.
- Reference the job bundle's `post_onset_goal` explicitly. Where
  `goal_conflicts_with_job` is true, show the friction in fiction (not
  as a bullet list).
- Do **not** preview the urgent quest. The urgent options are a separate
  field the player reads immediately after. Describing any of them here
  pre-decides the choice.
- Follow the positive-voice style directives in
  `emergence/setting/narration_style.md`. No meta-language, no numbered
  choices, no AI-assistant voice.

---

## Quest schema (required fields)

Every quest passes `validate_quest`. Missing or malformed fields return
errors for a regen attempt (up to 3 attempts total).

### Core fields

- **`id`** — unique string across the 8 quests.
- **`archetype`** — one of the registered quest archetypes.
- **`goal`** — verb-the-noun imperative sentence, ≤ 25 words.
- **`hook_scene`** — `{established_on_turn, inciting_event}`.
- **`central_conflict`** — `{nature, proxy_antagonist_id}` where the
  antagonist id is a named NPC from the job bundle.
- **`bright_lines`** — list of named non-death failure states (see below).
- **`macrostructure`** — one variable trending toward a threshold.
- **`success_condition`** — a Predicate the engine evaluates.
- **`resolution`** — success deltas plus a failure branch for every
  bright line.
- **`progress_track`** — `{ticks_filled, ticks_required, source}`.
- **`scope`** — `{expected_scenes, expected_session_equivalents}`.

### Required new fields (Phase G schema extension)

- **`conflict_mode`** — one of: `combat`, `social`, `investigation`,
  `escape`, `heist`. See mode definitions below.
- **`physical_danger`** — `{armed_opposition: bool, expected_combat_scenes: int}`.
- **`hook_npcs`** — list of NPC ids this quest introduces into the player's
  relationship roster. Must be drawn from the job bundle's generated NPCs.

---

## Conflict modes

Every quest declares exactly one conflict_mode.

### `combat`

Armed opposition is the core obstacle. The PC is expected to fight,
threaten, or kill their way through one or more scenes.

Example goal: *Repel the Iron Crown patrol breaking the blockade at
Burlington before dawn.*

### `escape`

The PC is being hunted, pursued, cornered, or must exfiltrate under
pressure. Armed opposition is present and closing.

Example goal: *Extract Varin from the Corvid corridor before the
Northbound sweep.*

### `social`

Conversation, negotiation, and standing are the load-bearing obstacles.
Violence is possible but not central.

Example goal: *Broker the truce between the Three Judges and the Bear-House
before the next council.*

### `investigation`

The PC is finding something hidden: a culprit, a mechanism, a location.
Clues and deductions are the load-bearing work.

Example goal: *Identify the skimmer draining the Bourse copper ledgers
before the quarterly audit.*

### `heist`

A multi-step plan with setup, infiltration, extraction. Planning and
stealth dominate; violence is a fallback.

Example goal: *Steal the Iron Crown's grain ledgers from the Newark
customs house during the Tuesday audit cycle.*

---

## Urgent-quest rules (strictly enforced)

The urgent-quest must satisfy **all** of these. The engine validator
simulates `is_urgent=True` on each of the four urgent-offer quests and
rejects the quest-output if any of them would fail:

1. **`conflict_mode` is `combat` or `escape`.** Urgent quests are
   physically dangerous by design.
2. **`physical_danger.armed_opposition = true`.**
3. **`physical_danger.expected_combat_scenes >= 1`.**
4. **Goal opens with a tactical verb** from:
   `extract, disable, intercept, breach, hunt, rescue, destroy, ambush,
   sabotage, capture, free, kill, eliminate, repel, escort, defend, guard,
   smuggle, steal, evacuate, assassinate, burn, stop`
5. **Proxy antagonist comes from a combat-capable threat** in the job
   bundle. Combat-capable threat archetypes:
   `knife_scavenger_survivor, warped_predator_personal,
   warped_predator_intelligent, wretch_swarm, named_rival_human,
   faction_assassin_contract, raider_band_reaper, raider_band_chain_king,
   iron_crown_notice, volk_informant, preston_notice, doctor_pale_target,
   cult_listening_incursion, hive_tendril_breach`.

---

## Backstory-set rules

The four backstory quests together must span **≥ 3 distinct
`conflict_mode` values**. This keeps the PC's past year textured and
avoids a four-quest stack of nothing but `social` drama.

Good distribution examples:
- combat, social, investigation, heist
- escape, social, investigation, combat
- combat, social, heist, investigation

Backstory quests are not required to use tactical verbs or armed
opposition. They can be meditative, diplomatic, or investigative.

---

## Bright lines

A Bright Line is a named non-death failure state. Every quest has ≥ 1.

Each bright-line object carries:
- `id` — unique within the quest.
- `description` — short prose stating the failure.
- `check_condition` — Predicate evaluated each tick.
- `telegraph_text` — how the opening scene cues this failure in fiction.

The telegraph is not optional. The opening scene must let the player
infer the failure state from prose alone.

---

## Macrostructure

One variable. One direction. Engine-evaluable.

```json
{
  "variable_name": "hours_until_sweep",
  "current": 5,
  "threshold": 0,
  "direction": "decrement",
  "tick_triggers": ["world_pulse", "travel_segment", "rest_action", "scene_close"]
}
```

- `current` starts on the good side of `threshold`.
- `tick_triggers` list the events that should advance this quest.
- Narration conveys the macrostructure through in-fiction cues (a bell, a
  horizon, a ledger line). No meta-language.

---

## Resolution structure

```json
"resolution": {
  "world_deltas_on_success": [ {"op": "...", ...} ],
  "world_deltas_on_failure": {
    "<bright_line_id>": [ {"op": "...", ...} ],
    ...
  },
  "narration_cue_on_success": "one-line hint for the resolution narrator",
  "narration_cue_on_failure": "one-line hint"
}
```

Every bright line must have a corresponding failure branch key (list may
be empty, but the key must exist). Failure branches should generate
follow-on situations: a captured NPC becomes a rescue quest seed; a
burned location becomes a clock that now ticks.

---

## Hook NPCs

Each quest declares `hook_npcs: [npc_id, ...]` — NPCs the quest introduces
to the player's relationship roster. Draw these from the job bundle's
`npcs` list. The bridge scene uses this list to know which NPCs to
introduce in the prose.

Backstory quests typically hook 1-2 NPCs each; the urgent quest may hook
more if its opening scene requires multiple named faces.

---

## Scope

```json
"scope": {
  "expected_scenes": 3,
  "expected_session_equivalents": 1.0
}
```

Typical ranges:
- 1 scene / 0.2 sessions — minor quest; one decision, one outcome.
- 3 scenes / 1 session — default; standard arc.
- 5+ scenes / 2+ sessions — major thread; use sparingly.

---

## Goal form: verb the noun

Urgent-quest goals open with a tactical verb. Backstory goals may use
any imperative verb.

### Urgent (tactical):

```
Extract Varin from the Corvid corridor before the Northbound sweep
Disable the Iron Crown supply caravan before it clears the tunnel
Repel the Reaper's scouts from the Fordham checkpoint
Hunt the Warped predator stalking the Cold Spring trail
Escort Councilor Veldt to the Accord Hall before the session rises
```

### Backstory (any imperative):

```
Broker the grain accord between Edison and the Commonage last autumn
Identify the clinic embezzler before the Bourse audit
Negotiate the truce that ended the 34th Street fire
```

### Not goals:

```
Help Varin                          ← state, not action
Survive the corridor                ← condition, not action
Deal with the Iron Crown            ← too vague, no done-state
Something about the skimmer         ← no verb, no noun
```

---

## Four-attempt rule

If the quest JSON fails validation, the orchestrator returns the error
list and asks for regeneration (up to 3 regen attempts). On the fourth
failure, the engine falls back to a template-driven quest built from the
archetype skeleton. Aim to pass on the first attempt.
