# Quest Design Guidelines

For narrators composing Quest JSON objects that the engine will validate.

A Quest is the unit of play. Exactly one active story, finishable, with a named
failure state the engine can check. Not a plot. A situation.

---

## The Angry Checklist

A Quest must pass all of these. The engine validator enforces most of them; the
rest are your responsibility.

1. **Concrete goal** — a verb-the-noun imperative sentence, ≤25 words.
2. **Externally verifiable done-state** — the engine can evaluate a predicate
   that answers "did the PC succeed?" without ambiguity.
3. **Player-facing** — the opening scene dramatizes the goal so the player can
   state it in their own words after reading.
4. **Achievable** — the goal is reachable through in-fiction PC action.
5. **At least one Bright Line** — a named non-death failure state the engine
   can check. Every Bright Line has a `telegraph_text` that the opening scene
   weaves in.
6. **Macrostructure** — a single variable trending toward a threshold, driven
   by named tick triggers. One variable per quest; if you need two, the quest
   is too big.
7. **Opposition with a plan** — the central_conflict names a proxy antagonist
   (an NPC id from the bundle). The antagonist's plan advances on clock ticks
   whether or not the PC acts.
8. **Stakes on both sides** — `resolution.world_deltas_on_success` and a
   `world_deltas_on_failure` branch for every Bright Line. Failure deltas
   should produce a new situation (threat, clock, lost standing), not a stall.

---

## Goal form: verb the noun

```
Extract Varin from the Corvid corridor before the Northbound sweep
Keep Old Meren's stall standing through market week
Identify the skimmer in the Brinker corridor before the cull
Disable the Iron Crown's supply caravan before it clears the tunnel
Deliver Weaver's testimony to the Accord Hall before the council rises
```

Not goals:

```
Help Varin                          ← state, not action
Survive the corridor                ← condition, not action
Deal with the Iron Crown            ← too vague, no done-state
Something about the skimmer         ← no verb, no noun
```

The heuristic: an outsider reading the goal must be able to sketch a finish
line in one sentence. If they'd need follow-up questions, the goal is soft.

---

## Bright Lines

A Bright Line is a named non-death failure state. Every quest has at least one;
most have two or three.

Each Bright Line object carries:

- `id` — unique within the quest (e.g. `bl_sweep_arrives`, `bl_varin_dies`)
- `description` — short prose stating the failure
- `check_condition` — a Predicate the engine evaluates each tick
- `telegraph_text` — how the opening scene cues this failure state in fiction

**The telegraph is non-optional.** If the player can't infer the failure state
from the opening scene, the line is hidden, and the player acts at random.
Angry's rule: *the player must know or be able to discover the failure state*.

**Canonical failure frames:**

- Time expires (macrostructure crosses threshold)
- Target dies or is captured
- PC captured or exiled
- Standing collapses below threshold
- Rival/threat reaches a milestone first
- PC's cover exposed

Keep check_conditions simple. Use the predicate DSL (see schema.py). Do not
invent new predicate types — if you need one, flag it for engine work.

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

**Rules:**

- `current` must start on the "good" side of `threshold` (decrement: `current >
  threshold`; increment: `current < threshold`). A quest that starts already
  failed fails validation.
- `tick_triggers` list only events that should advance this particular quest.
  A Ceremony quest that only advances when the astronomical window narrows
  should list a narrow trigger set, not `world_pulse`.
- Macrostructure is visible to the player. Narration must convey it — a bell,
  a horizon, a ledger line — never via meta-language (never say "your clock is
  at 3 segments").

---

## Proxy antagonist

Systemic antagonists (the Iron Crown, the Northbound sweep, the plague) need
a named NPC face. The proxy makes the opposition dramatizable — you can show
their plan, their patience, their moves.

The proxy is almost always drawn from the job bundle's NPCs (usually a rival
or threat). If the bundle has no candidate, the Quest generator should flag
it and add one, not invent one in isolation.

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

**Required:** every Bright Line must have a corresponding failure branch. An
empty list is allowed, but the key must exist — the validator enforces that
you considered each failure mode.

**Failure should generate follow-on situations.** A captured NPC is a new
quest seed. A lost standing is a new threat. A burned location is a clock
that now ticks. Use `{"op": "quest_seed", ...}` and `{"op": "threat_add", ...}`
to wire the downstream.

**Narration cues are optional** — if present, the resolution narrator reads
them as a guide, not a script.

---

## Scope

```json
"scope": {
  "expected_scenes": 3,
  "expected_session_equivalents": 1.0
}
```

- **1 scene / 0.2 sessions** — a minor quest; one decision, one outcome
- **3 scenes / 1 session** — default; a standard arc
- **5+ scenes / 2+ sessions** — a major thread; use sparingly

Scope is a budget, not a contract. Scenes can run short or long; the number
is a design intent for pacing purposes.

---

## Progress track

```json
"progress_track": {
  "ticks_filled": 0,
  "ticks_required": 10,
  "source": "ironsworn_vow_dangerous"
}
```

The progress track is the player-side engine: it fills as the PC makes moves
that advance the goal. Filling the track completes the quest; a Bright Line
firing ends it as failure. Different `source` values map to different tick
economies (dangerous, formidable, extreme).

---

## Concurrency

The save holds an unlimited number of concurrent quests. Writing one does not
require coordinating with the others, but be aware:

- Two quests sharing a proxy antagonist can play off each other; mark this in
  `central_conflict.nature` so the narrator knows.
- Two quests with overlapping macrostructure tick triggers will both advance
  on the same world pulse. That's fine — the world imposes pressure on all
  live threads simultaneously.

---

## Four-attempt rule

If the quest JSON you produce fails validation, the orchestrator returns the
error list and asks for a regeneration. You get three attempts. On the fourth,
the engine falls back to a template-driven quest built from the archetype
skeleton. Aim to pass on the first attempt by consulting the schema before you
write.
