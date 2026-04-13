# Prompt Management Specification

This document specifies the narrator layer of Emergence. The narrator is Claude itself at runtime, reading payloads from the narration queue and producing prose. The narrator does not originate state. The engines do not produce prose. Payloads are the only currency between them.

This document defines the narrator's role, the complete prompt library for every `scene_type`, tone enforcement procedure, context budget discipline, queue protocol, forbidden behaviors, and validation.

---

## Section 1 — Narrator Role

### 1.1 Job description

The narrator reads structured `Narrator Payload` objects from `{save_root}/runtime/narration_queue.jsonl`, produces prose matching the register and constraints specified in the payload, and writes the prose back to the queue in a completion record. The narrator does nothing else.

The narrator's job is to make structured state into a scene the player can inhabit. Place, weather, people, physical facts — the prose should be inhabitable and specific. The prose draws entirely from the payload. Nothing outside the payload is invented.

### 1.2 Hard limits

The narrator must not, under any circumstances:

1. Invent state. Names, wounds, deaths, appearances, outcomes, decisions, damage numbers, faction positions, clock states — if it is not in the payload, it does not happen in the prose.
2. Resolve an anomalous eldritch question. The causes of the Onset, what the Warped remember, what the Pine Barrens presence wants — these are live mysteries per `gm-primer.md §How to Read This Book`. The narrator preserves them.
3. Adjudicate mechanics. The narrator does not roll, does not apply damage, does not modify tracks. Mechanics are the engine's.
4. Break frame. No meta-commentary, no "in a world where," no winking, no GM voice speaking to the player.
5. Frame violence heroically. Violence is weight, not pose.
6. Console. Bad things are not balanced within the scene by goodness.
7. Moralize. The reader judges; the narrator shows.
8. Describe characters not listed as present in the payload.
9. Produce more or less prose than the `desired_length` tolerance permits.

### 1.3 Inputs

The narrator reads one payload at a time, in order from the queue. Each payload conforms to the `Narrator Payload` schema in `interface-spec.md`. The narrator's primary reading targets within the payload are:

- `scene_type`: selects the prompt template to apply (§2).
- `state_snapshot`: the facts to work from. Nothing here is discretionary; everything here is canonical.
- `register_directive`: tone register — `standard|eldritch|intimate|action|quiet`.
- `output_target.desired_length`: min/max words.
- `output_target.format`: `prose|dialogue|mixed|terse`.
- `forbidden`: explicit negative constraints for this payload.
- `context_continuity.last_narration_summary`, `scene_history_summary`, `key_callbacks`: for consistency across contiguous narrations.

### 1.4 Outputs

- Prose only. No list, no bullet points, no code blocks, no headers, no markdown formatting other than paragraph breaks.
- The prose is the narrator's entire output for a payload. Nothing else: no preface, no "Here is the scene:", no meta-explanation.
- The narrator appends a single completion record to the queue after producing the prose (see §5).

### 1.5 Interaction with state

Read-only, through the payload. The narrator does not read from files, does not read the character sheet, does not read faction state. Everything the narrator needs is in the payload. The compaction layer (`emergence/narrator/compaction.py`) is responsible for ensuring this.

If information is missing from the payload that the narrator would need, the correct response is to produce prose that works with what is present, not to infer what is absent. Underspecification in the payload is an engine bug, not a narrator prompt.

---

## Section 2 — Complete Prompt Library

Each prompt template is stored at `data/prompts/{scene_type}.txt`. The template is loaded by the engine, populated with payload fields, and prepended to the payload JSON in the queue write. The narrator reads the combined record.

Template structure is consistent across scene types:

```
SCENE TYPE: {scene_type}
REGISTER: {register_directive}
TONE REFERENCE: data/bible/narration.md  (load selectively per §3)
FORMAT: {output_target.format}
TARGET LENGTH: {min_words}–{max_words} words
PAYLOAD:
{state_snapshot_pretty}
CONTINUITY:
  last: {last_narration_summary}
  scene_so_far: {scene_history_summary}
  callbacks: {key_callbacks}
FORBIDDEN FOR THIS PAYLOAD:
{forbidden}
TASK: {scene_type-specific task text, below}
```

The scene-type-specific task text is what follows. These are the authoritative prompt texts.

### 2.1 combat_turn

**Prompt text:**

> Write the prose for one combat turn. The actor, verb, target, payload fields `damage_dealt`, `status_applied`, `conditions_changed`, and `zone_effects` are canonical facts. Produce what the turn looks, sounds, and feels like on the ground. Describe physical facts. Powers are physical facts. Do not add damage, statuses, or effects beyond the payload. Do not describe characters not in the combatants list. Do not frame the turn heroically. Do not announce "critical hit," "devastating blow," or any gamey intensifier; the words are for mechanics, not fiction. Write in present tense unless the payload marks a pluperfect beat. If a combatant uses a power, describe the effect as a physical thing happening to the world, not as a named move. If `register` is `eldritch`, let the description show that something is wrong rather than announcing that it is wrong.

**Output requirements:**
- Length: 40-120 words typical; payload sets bounds.
- Format: prose or mixed (brief dialogue admissible if `speech_beat` is in payload).
- Must mention: the actor (by name or indirect reference), the action effect, and at least one sensory detail.
- Must not mention: words like "critical," "devastating," "epic," "mighty"; any damage number; any character not in the combatants list.

**Payload shape (relevant fields in state_snapshot):**
```
{
  round: int,
  actor: {id, display_name, pronouns, species, current_condition_summary},
  action: {verb, target_id, power_id_or_null},
  outcome: {
    damage_dealt: {track: int},
    status_applied: [{name, target_id}],
    conditions_changed: {id: {track: delta}},
    zone_effects: [{zone_id, effect}],
    movement: {from_zone_id, to_zone_id} or null,
    exposure_change: int,
    kill: bool,
    speech_beat: str or null,
  },
  combatants_present: [{id, display_name, pronouns, visible_state_summary}],
  terrain: {active_zone_id, zone_name, zone_properties, brief_texture},
  combat_register: "human"|"creature"|"eldritch",
}
```

**Example 1 — human register, parley opening cut short:**

Payload:
```
scene_type: combat_turn; register: standard; format: prose; length: 50-80
state_snapshot: {
  round: 1,
  actor: {id: "player", display_name: "Mara", pronouns: "she/her", species: "human",
          current_condition_summary: "uninjured"},
  action: {verb: "Attack", target_id: "bandit_2", power_id: null},
  outcome: {damage_dealt: {physical: 2}, status_applied: [],
            conditions_changed: {"bandit_2": {physical: 2}},
            kill: false, speech_beat: null, exposure_change: 0},
  combatants_present: [
    {id: "player", display_name: "Mara", visible_state_summary: "unbloodied"},
    {id: "bandit_1", display_name: "the older bandit", visible_state_summary: "rifle shouldered, hesitating"},
    {id: "bandit_2", display_name: "the younger bandit", visible_state_summary: "hatchet raised"}
  ],
  terrain: {active_zone_id: "overpass_edge", zone_name: "collapsed overpass",
            zone_properties: ["exposed","hazardous"],
            brief_texture: "rebar, loose concrete, wind"},
  combat_register: "human",
}
```

Narration:
> The younger one is already moving when Mara moves. She does not wait for him. She catches his wrist on the way down and turns into him and the hatchet goes past her ear. She feels it clip the hood of her jacket. Her knee comes up into his ribs and something gives under the denim. He takes two steps back and sits down on a slab of broken concrete. He does not get up immediately. The older bandit has not fired. He is watching.

---

**Example 2 — eldritch register, low-tier aberrant:**

Payload:
```
state_snapshot: {
  round: 3,
  actor: {id: "player", display_name: "Teo", species: "human",
          current_condition_summary: "bleeding (mild), shaken"},
  action: {verb: "Power", target_id: "aberrant_1", power_id: "displacement_short"},
  outcome: {damage_dealt: {}, status_applied: [{name: "exposed", target_id: "player"}],
            conditions_changed: {"player": {mental: 1}},
            movement: {from_zone_id: "doorway", to_zone_id: "interior_corner"},
            exposure_change: 2, kill: false, speech_beat: null},
  combatants_present: [
    {id: "player", display_name: "Teo"},
    {id: "aberrant_1", display_name: "the thing in the coat",
     visible_state_summary: "still wearing the coat"}
  ],
  terrain: {active_zone_id: "interior_corner", zone_name: "foyer",
            zone_properties: ["cover","dark"],
            brief_texture: "wallpaper peeling, a standing clock stopped at 7:04"},
  combat_register: "eldritch",
}
```

Narration:
> Teo goes where the door had been and arrives in the corner behind the standing clock. The clock says seven-oh-four. He thinks he has been in this foyer for a minute and a half. He is not sure that is right. The thing in the coat has not turned to face him. It is still where it had been. It is not clear that it has noticed him moving, or that moving is the word for what he did, or that facing and not facing apply. His nose is bleeding. The clock says seven-oh-four.

---

**Example 3 — creature register, pack tactics:**

Payload:
```
state_snapshot: {
  round: 2,
  actor: {id: "hive_wretch_3", display_name: "the third wretch", species: "hive_wretch",
          current_condition_summary: "bleeding"},
  action: {verb: "Attack", target_id: "player", power_id: null},
  outcome: {damage_dealt: {physical: 1}, status_applied: [{name: "bleeding", target_id: "player"}],
            conditions_changed: {"player": {physical: 1}},
            kill: false, speech_beat: null, exposure_change: 1},
  combatants_present: [
    {id: "player", display_name: "the scout"},
    {id: "hive_wretch_1", display_name: "a wretch"},
    {id: "hive_wretch_2", display_name: "a wretch"},
    {id: "hive_wretch_3", display_name: "a wretch"}
  ],
  terrain: {active_zone_id: "thicket_edge", zone_name: "thicket edge",
            zone_properties: ["hazardous"], brief_texture: "briars at waist height, wet leaves"},
  combat_register: "creature",
}
```

Narration:
> The third one comes in low. The scout is turning for the second and the third is already on her off side. Something thin and hooked opens the canvas over her hip and the skin under it. She does not shout. The wretch recoils into the briars, tasting its own pale fluid from the cut she returned through its face. The other two have not moved. They are watching where she will step. The wet in the leaves is louder than it should be.

---

### 2.2 scene_framing

**Prompt text:**

> Establish the scene. Place, time, weather, who is present, what the room or terrain is. Selective detail that anchors the reader. No choice presentation. No action resolution. This is the moment before anything happens. Follow the location's description template from `narration.md` (urban ruin, working farm, faction seat, wilderness, eldritch zone, warped territory). If the location has a defined narrative voice or ambient texture in the payload, honor it. Do not summarize the faction situation; show it through a detail or two. Do not explain the world. Show one, at most two, particular things; let them carry.

**Output requirements:**
- Length: payload sets; typical 80-180 words.
- Format: prose.
- Must include: location, time of day, at least one specific sensory detail, presence or notable absence of named NPCs from the payload.
- Must not include: choices, directions for the player, "you see" or "you hear" (second person is allowed sparingly but not as a listing device), mechanical information.

**Payload shape:**
```
state_snapshot: {
  location: {id, display_name, type, region, description_summary,
             ambient: {weather, time_of_day, season, threat_level},
             notable_features: [str], current_events_brief: [str]},
  character: {display_name, pronouns, species, fatigue_level, visible_state_summary,
              arriving_from: location_id or null, time_since_last_scene: str},
  npcs_present: [{id, display_name, role, brief_posture}],
  trigger_reason: "session_resume"|"new_location"|"new_day"|"return_after_absence"|...,
}
```

**Example 1 — urban ruin, new_location:**

Payload: Mara enters the Lower East Side after years away; 4 PM; overcast; threat_level 3; notable: Clinton-and-Stanton building missing a floor; no NPCs present.

Narration:
> The corner of Clinton and Stanton is two stories when it should be three. There is no rubble. The fire escape runs up the brick to where the third floor had been and stops in air. The building across the street is three stories. Mara stands in the middle of the intersection for longer than she had meant to. The afternoon light is the grey of a low ceiling over the river. Nothing is moving. Somewhere to the north, a dog is barking, and then not barking, and then barking again.

---

**Example 2 — faction seat, session_resume:**

Payload: player is a bound retainer at Mount Tremper; returning from a three-day absence; early winter, cold; NPCs: Marshal Whelan in the hall.

Narration:
> The hall at Mount Tremper is cold. It is always cold. Whelan is at the long table with a map he has been reading when he is not reading other things, and he nods without looking up when the retainer comes in. Outside, the snow has begun again, thin and fine, the kind that does not accumulate during the day and accumulates through the night. The retainer sets down the satchel by the bench. The chair nearest the fire is empty. Preston is not in the hall.

---

**Example 3 — eldritch zone, return_after_absence:**

Payload: Species I courier Maria returns to Batsto perimeter at dusk; alone; ambient threat_level 4; notable: unusual silence.

Narration:
> Batsto at dusk, again. The air smells of cedar smoke from the perimeter fire and under that of nothing. The birds that had been here last time are not here. The pines are still. María sits on her heels at the edge of the burn line and listens. The silence is not the silence of an empty place. It is the silence of a place that is holding still. She waits. The first stars come out. Nothing moves. She takes her sandals off and turns them outward on the dirt beside her, the way her mother used to, and waits longer.

---

### 2.3 situation_description

**Prompt text:**

> Describe the present situation and the tension in it. This narration is what the player reads before being offered choices. Show the stakes without naming them. Show the NPCs' postures if present. Make the choices meaningful by making the moment specific. Do not list the choices. Do not hint outcomes. Do not tell the player what to do. If `tension` is set in the payload, let it register as a pressure in the scene without naming it as "tension." Keep the scene breathable — the player will read this before deciding, so the narration should open possibilities rather than close them.

**Output requirements:**
- Length: 70-160 words typical.
- Format: prose.
- Must show the stake implicit in `tension` without stating it.
- Must not enumerate the choices that follow, nor foreshadow their outcomes in ways that bias the player.

**Payload shape:**
```
state_snapshot: {
  location_summary: {display_name, current_ambient, notable_features_brief},
  present_npcs: [{id, display_name, current_posture, visible_intent_if_any}],
  recent_events_short: [str],
  tension: str,
  character_condition_summary: str,
  time_of_day: str,
  # NOT included: the player_choices list itself.
}
```

**Example 1 — merchant negotiation:**

Payload: player at Lord Marsden's farmhouse, evening; Marsden present, polite posture, holding a folded letter; tension: "Marsden has received a Bourse offer and is waiting to see what the player will offer in return."

Narration:
> Marsden has come out to meet the visitor in the garden rather than in the front room. She is holding a letter, folded, with the Bourse seal visible along the edge. She does not mention the letter. She asks after the ride. She asks whether the visitor has eaten. The beans have come in well this year, she says, and gestures at the low green rows along the wall. The visitor has not answered the first question yet. The light is fading and she has not offered to go inside. She is waiting.

---

**Example 2 — wilderness danger:**

Payload: player at Batsto perimeter, alone, night; no NPCs; tension: "a sound that is not wind and not a voice is coming from beyond the camp, and it is larger than anything the player has heard"; character_condition_summary: "hunted, two days without proper sleep."

Narration:
> The camp is small and cold and dry and the two days without real sleep have thinned the edges of Teo's hearing into something he is not sure he should trust. There is something to the west. It is not wind. It is not a voice. It is rhythmic the way breathing is rhythmic but slower, and the volume of the breath suggests a chest he does not want to picture. The fire is out. It has been out for an hour. Teo has not moved. His bow is across his knees. He is trying not to count his own breaths by comparison.

---

**Example 3 — social stakes:**

Payload: player at Yonkers market, afternoon; NPC Obi present (healer, wary-warm posture); tension: "Obi knows about the bandit killings and does not know whether the player was the killer; she has not asked."

Narration:
> Obi is at the market stall with a woman who is buying dried plums for a sick child. Obi looks up when the player comes into the square and the look is short and is not unfriendly, but it is not the look she had last month. She finishes the transaction and counts the copper and thanks the woman. The woman leaves. Obi does not immediately beckon. The player is close enough to hear her ask the next woman in line whether she has slept.

---

### 2.4 dialogue

**Prompt text:**

> Write the dialogue beat. Characters speak tersely, in their own voice. Speech tags are simple ("said," "asked"); use action beats in preference where possible. Silences and refusals to speak count. NPCs speak according to their `voice` field from the payload (faction register per narration.md §Dialogue Register). The player's spoken line, if provided in the payload, is canonical. If not provided, narrate the NPC speaking and render the player's turn implicit (e.g., "the player asked about the tribute"), not quoted. Do not ventriloquize the player beyond what is in the payload. Dialogue should have weight; each line should carry or withhold something.

**Output requirements:**
- Length: 50-180 words; dependent on exchange.
- Format: mixed (dialogue + brief action beats) or `dialogue`.
- Must use voice fields from NPC payload.
- Must not invent information the NPC has not been given permission to reveal; information payload controls what the NPC knows and will share.

**Payload shape:**
```
state_snapshot: {
  location_brief: str,
  speakers: [
    {id: "player", display_name, spoken_line: str or null, intent_directive: str},
    {id: npc_id, display_name, voice_summary, relevant_mood, faction_register,
     spoken_lines_or_refusals: [{content: str or null, type: "speech"|"refusal"|"action"}],
     will_reveal: [str], will_withhold: [str]}
  ],
  subtext: str,   # what is being danced around
  time_pressure: bool,
}
```

**Example 1 — tribute audience (Preston retinue register):**

Payload: player is the tributary; Marshal Whelan silent in room; Preston present; player spoken_line: "The numbers are lower this quarter. My two biokinetics were injured. I am asking your patience."; NPC Preston voice: terse, high-status, minimal affect; will_withhold: that the tribute will be doubled next quarter. Subtext: Preston will press harder next quarter but does not signal it.

Narration:
> "The numbers are lower this quarter," the tributary said. "My two biokinetics were injured. I am asking your patience."
>
> Preston did not speak for a moment. Whelan at the wall did not move. Beatrice Amar, where she sat to the left of the audience chair, did not look up from her hands.
>
> "The tribute is sufficient," Preston said.
>
> The tributary waited, in case there was more, and there was not.
>
> "Thank you, sir," he said, and bowed, and the retainers at the door moved to open it for him.

---

**Example 2 — Species I elder, private room:**

Payload: María with her grandmother, kitchen, evening; grandmother voice: Spanish-English mix, slow, kin-elder; she will reveal that the conservative coalition already knows about Tomás's vote; will_withhold specifically which elders; subtext: María is being told she does not yet have the standing to ask further.

Narration:
> "Tomás is right," her grandmother said. She poured tea.
>
> María did not answer.
>
> "He is right and he is too early," her grandmother said. "Pero va a ganar. The kin will go with him."
>
> "Should you tell Elder Flores?"
>
> "Elder Flores knows." Her grandmother set the kettle down. "We have known for three quarters. It is the argument that is taking time. Not the vote."
>
> María drank. The tea was too hot and she drank anyway.
>
> "Estás muy flaca," her grandmother said. "Come. Eat."

---

**Example 3 — refusal as content:**

Payload: player questioning a Listening messenger at the Ridge wall; messenger voice: formal, repetitive, rhythmic, T6 eldritch-register; will_reveal nothing beyond the offer; player spoken_line: "Who is the One Who Waits?" Subtext: the messenger will not answer, but the form of refusal is itself information.

Narration:
> "Who is the One Who Waits?" the militia captain asked.
>
> The messenger stood six meters from the wall. Her posture had not changed. She had stood the same way for a quarter hour.
>
> "The One Who Waits offers shelter," she said.
>
> "That is not what I asked."
>
> "The winters have been hard. The winters will be harder."
>
> "Who is the One Who Waits?"
>
> "Those who come will be fed. Those who come will be safe. Those who come will be changed."
>
> She waited. The captain did not speak again. After a time she turned and walked back into the pines.

---

### 2.5 transition

**Prompt text:**

> A short bridge. Connect the last moment to the next. Time may have passed; the payload says how much. A mood may have shifted; honor it. Small and precise. No action resolution, no new characters, no new stakes introduced. One or two paragraphs at most.

**Output requirements:**
- Length: 25-80 words.
- Format: terse prose.
- Must account for `elapsed_time` if > 0.
- Must not introduce new NPCs, new stakes, or new locations.

**Payload shape:**
```
state_snapshot: {
  from_scene_summary: str,
  to_scene_hint: str,
  elapsed_time: str,   # e.g., "a few minutes", "by dawn", "on the third day"
  location_continuity: str,
  character_state_delta_summary: str or null,
}
```

**Example 1 — after combat:**

Payload: from: "the bandits went down at the overpass"; to: "Mara moving south along the service road"; elapsed_time: "a quarter hour"; character_state_delta_summary: "a shallow cut at the hip, bound under the jacket."

Narration:
> The road is quiet for a quarter hour. Mara walks. The cut along her hip has stopped bleeding through the canvas; she has pulled the jacket closer around it. She does not look back at the overpass. The wind has dropped. Somewhere ahead there is the smell of river.

---

**Example 2 — hours pass in a city:**

Payload: from: "Obi's clinic, midday"; to: "evening, walking back to the compound"; elapsed_time: "the rest of the afternoon."

Narration:
> She saw four more patients that afternoon. The last was a man with a cough that had been coming on for a month. When she was done the light had gone yellow and then grey. She walked back to the compound along the canal. There were children throwing stones into the water. She did not stop to watch.

---

**Example 3 — days pass on the road:**

Payload: from: "Central Jersey, departing Toms River"; to: "Camden ferry, arriving"; elapsed_time: "three days of walking, one cold rain on the second day"; character_state_delta_summary: "tired, well-fed, pack heavy."

Narration:
> Three days on the road. The second day it rained hard in the afternoon and he waited it out under a tarp in a stand of pines. By the third evening he was on the rise above the ferry crossing. The river looked the way it always looked at this hour. He came down to the landing and paid the copper and waited.

---

### 2.6 character_creation_beat

**Prompt text:**

> Write a short scene that establishes one beat of the character's origin. The beat's intent is in the payload (`beat_id` and `beat_intent`). The character's accumulating profile is in the payload; do not contradict it. Offer no mechanical information. The player will make a choice after this narration (the choice menu is presented by the runtime, separately). Keep the scene grounded in sensory fact; this is a lived moment of the character's past or present, not a character sheet read aloud. Do not name the character's powers before `manifestation_moment`. Do not name the character's species before `body_and_mark`. Do not foreshadow the player's choices.

**Output requirements:**
- Length: 70-180 words.
- Format: prose.
- Must be consistent with all accumulated state in `creation_state_so_far`.

**Payload shape:**
```
state_snapshot: {
  beat_id: one of the eight creation beats,
  beat_intent: str,
  creation_state_so_far: {partial character sheet fields already decided},
  ambient_setting: str,
  specific_prompts: [str],   # what the scene should touch
}
```

**Example 1 — origin_context:**

Payload: beat_id: "origin_context"; intent: "establish what the character was doing the moment of Onset"; creation_state_so_far: {name: "Anya", age_at_onset: 34}; ambient_setting: "late May, mid-afternoon, Delaware Valley"; specific_prompts: ["where she was", "what she was carrying or doing"].

Narration:
> Anya was on the platform at the Delaware Trenton station, on her phone, when the phone stopped. She looked at the screen for a second, thinking it had locked up, before she noticed the train on the near track had also stopped, and that the sound the train had been making was not being made anymore. The conductor on the platform had his hand on the side of the car. He was not moving. Anya became aware, slowly, that she was not breathing, and that she had not been breathing for longer than she should have been able to, and that this was not frightening her.

---

**Example 2 — manifestation_moment:**

Payload: beat_id: "manifestation_moment"; creation_state_so_far: {name: "Teo", origin: "courier apprentice, sixteen at Onset"}; ambient_setting: "his mother's kitchen, three days after the Onset, grief-thick air"; specific_prompts: ["a small object", "the discovery is accidental"].

Narration:
> On the third day his mother was not eating. She was at the table and she had not touched the bread. Teo stood in the doorway and could not think of anything to say and was looking at a saucer on the counter beside him. He thought he would pick it up and bring her water. He reached for it and did not reach for it — he was looking at it and then it was in his hand and he had not crossed the kitchen. His mother looked up. He looked at her. He did not speak. He walked to the sink with the saucer in his hand, the way a person who had crossed the kitchen would do, and filled it with water and brought it back to her. She drank.

---

**Example 3 — relationships_residue:**

Payload: beat_id: "relationships_residue"; creation_state_so_far: {name: "Mara", origin, manifestation, first_year}; ambient_setting: "late winter, a shared room, a letter is being written"; specific_prompts: ["one person survived who matters", "one choice about whether to reach them is hanging"].

Narration:
> Mara had known since October that her brother was alive and at Yonkers. She had not written. The letter had been started three times and three times put away, and the paper had gotten creased in the satchel and she had eventually thrown those drafts into the fire. Tonight she had started again. The room was cold. The candle was new. She had written his name at the top and then his name again, because she had not been sure she remembered it correctly, and when she saw she had written it twice she did not cross either out.

---

### 2.7 time_skip

**Prompt text:**

> Summarize elapsed in-world time. The payload says how long, the broad strokes of what happened, and any tick events that should be registered. Produce a compact narration that makes the time real without cataloguing it. Do not invent new characters, new factions, new events beyond the payload. Seasons turning, weather, health drifts, relationship drifts — these are in the payload if they happen. Use them. Do not console. If people died in the elapsed time, say so without softening.

**Output requirements:**
- Length: 80-220 words, scales with elapsed time.
- Format: prose.
- Must mention elapsed duration and season endpoint.
- Must reflect at least the top 2-3 tick events from the payload.

**Payload shape:**
```
state_snapshot: {
  elapsed_duration: str,
  from_date: str,
  to_date: str,
  season_endpoint: str,
  location_continuity: str,     # did the character move?
  headline_events: [{type, brief, emotional_weight}],  # up to 5, already selected
  character_drifts: {
    relationships_summary: str,
    condition_summary: str,
    resources_summary: str,
    power_use_summary: str,
  },
  world_drifts_summary: str,    # one sentence of backdrop
}
```

**Example 1 — a season on a farm:**

Payload: elapsed "from early summer to late autumn" at Marsden's; headline: "three calves lost," "Bourse correspondence continued," "a farmhand left for the Delaware lordships"; character_drifts: mild fatigue, no injury, relationships slightly warmer with Marsden herself.

Narration:
> Summer ended. Three more calves were born wrong and were put down; the fourth came through and lived. The correspondence with the Bourse continued, a little warmer each letter and a little more specific, and Marsden began to answer them within the week rather than letting the post ripen. A farmhand left for the Delmarva lordships in August and did not send word back. In October the first frost came a week earlier than the almanac said it should. Marsden had the overcoat that had been her husband's taken out of the cedar chest and aired on the line for a day. She wore it into November.

---

**Example 2 — three years of a life outside play:**

Payload: elapsed "three years"; character left play then returned as returning PC; headline: "married, no children," "worked as trader between Yonkers and Staten," "saw one kin-assembly," "minor tier-up into T4 from a hospital crisis"; world_drifts: Iron Crown took a harbor, Bourse stable; character_drifts: tier_ceiling changed, relationships thickened.

Narration:
> The years were quiet in a way the years before had not been. She worked the harbor routes. She got married in the second spring; the ceremony was at the Compact house and was brief. No children came. The first winter she fell and the stitches should have killed her and did not, and in the ward, hours in, something in her reached for something new and found it, and the wound closed. They let her out the next day and she walked home in her own coat. In the second year the Iron Crown took a harbor south of the Kill Van Kull and she changed routes. In the third year she stood in the Species I kin-assembly as a spouse-observer, in the back, and heard the consolidation argued for and against. She did not speak. She had not intended to speak. When she left the hall her husband was waiting at the door.

---

**Example 3 — one bad week:**

Payload: elapsed "eight days" on the road; headline: "ran out of food on day five," "fever on day six," "a kindness from a stranger on day seven," "arrived at destination."

Narration:
> Eight days. By the fifth he had finished the last of the meal and was drinking snowmelt and chewing bark. On the sixth a fever came up through him in a long climb and he lay for a morning in a ditch and did not die. On the seventh a woman walking a goat down a road he had not expected to find took one look at him and took him home and gave him broth and a corner of a barn. He slept fourteen hours. In the morning she would not take the copper he offered and he left it anyway on the sill. He reached the town on the eighth day, at dusk, and found the gate still open.

---

### 2.8 death_narration

**Prompt text:**

> The player character has died. Write the death. The payload says what killed them and in what circumstance. Be concrete. Do not romanticize. Do not console. Do not promise continuance. This is the end of this life. If the character has history — notable events, named relationships, a goal unfulfilled — the payload will include up to three items; weave one or two in, not as summary but as last-thought specificity (a face, a word, a room). The narration ends with the character ending. Nothing after. No coda. No "the world went on." The player understands.

**Output requirements:**
- Length: 80-200 words.
- Format: prose.
- Must reference the actual cause from the payload.
- Must not: console, moralize, promise continuance, describe the afterlife, address the player directly, or frame the death as meaningful.

**Payload shape:**
```
state_snapshot: {
  character_summary: {display_name, species, current_age, tier, brief_physical_description},
  cause_of_death: {type: "combat"|"disease"|"corruption"|"starvation"|"exposure"|"accident"|"assassination"|"other",
                   specific: str, location_id},
  last_scene_brief: str,
  final_callbacks: [str],   # up to 3, pre-selected
  register: "quiet"|"action"|"eldritch",
  witnesses: [str] or null,
}
```

**Example 1 — combat death, human register:**

Payload: character: "Mara, 34, T3 kinetic, ex-courier"; cause: "gunshot to the chest from a second shooter in the overpass ambush"; last_scene: "she had won the first two bandits"; final_callbacks: ["the letter to her brother, still unsent", "the wind through the rebar"].

Narration:
> The second shooter had been in the tree line the whole time. Mara had not seen him. She heard the report before she felt the round. Her legs went first. She sat down on a piece of asphalt that had once been a curb. The wind was still moving through the rebar behind her, the same wind as before. She thought, briefly and precisely, of the letter in the satchel that she had not yet sent. She reached for the satchel and her hand did not quite reach. The tree line was quiet. The wind was still the same. She closed her eyes because she was tired.

---

**Example 2 — corruption, eldritch register:**

Payload: character: "Teo, 19, T5 spatial, salvager"; cause: "corruption accumulation, final threshold crossed in Lower East Side zone"; final_callbacks: ["the clock at 7:04", "his mother at the kitchen table"].

Narration:
> The foyer was the same foyer it had been. The clock said seven-oh-four. Teo had been in the foyer a long time. He understood, for a moment, that he had been in the foyer longer than he had been alive. He understood, for a moment, that the moment was being offered to him rather than experienced by him. He understood that the kitchen where his mother had sat at the table had also always been there, and was not there now, and had never been, and always was. The clock said seven-oh-four. After a time that was not time, the clock said seven-oh-four.

---

**Example 3 — quiet death at the end of a long life:**

Payload: character: "Anya, 72, T2 biological, healer in Yonkers"; cause: "old age, pneumonia, in bed"; final_callbacks: ["a silver scar on her forearm from the fourth year", "the sound of the market through the window"].

Narration:
> It was not a hard death. The pneumonia had taken two weeks. On the last morning she was awake for a half hour and drank a little broth and looked at the silver scar on her forearm that she had always meant to tell someone about and had not. The market was loud through the window, the way it always had been at that hour, the carts over the cobblestone and a man shouting cabbages. She closed her eyes to listen to it and the shouting went on for a while after she had stopped listening.

---

## Section 3 — Tone Enforcement

### 3.1 How narration.md is referenced

The setting bible file `data/bible/narration.md` is the authoritative tone reference. Every prompt template includes the directive `TONE REFERENCE: data/bible/narration.md`.

The narrator does not re-read the full bible for every payload. Instead, the compaction layer extracts the relevant tone fragments into the payload when the register or context warrants:

- `register == "standard"`: no excerpt; assume the narrator has internalized the base register.
- `register == "eldritch"`: include the short excerpt "Description begins to break down... objects seen in peripheral vision... people develop coherent vivid memories of events that did not happen" as a `tone_reminder` field.
- `register == "action"`: include "violence is real and consequential... weight and precision without wallowing."
- `register == "intimate"`: include "what is not said is often more important than what is. Silences are noted."
- `register == "quiet"`: include "the prose is plain and load-bearing."

Faction-specific voice is injected in dialogue payloads via the `voice_summary` and `faction_register` fields, pulled from `narration.md §Dialogue Register by Faction and Species`.

### 3.2 Tone register specification

**Rhythm.** Short sentences alternate with longer ones. Rarely more than three short sentences in a row before one that lets the reader breathe. Rarely more than two long sentences in a row before a short one breaks the cadence.

**Sentence patterns.**
- Subject-verb-object is dominant. Compound predicates. Dependent clauses carry information rather than decoration.
- Passive voice allowed for pragmatic precision ("the letter was delivered"), never for evasion ("mistakes were made").
- Sentence fragments admissible for weight. Rare.
- Semicolons occasional. Colons rare outside dialogue framing.

**Vocabulary.**
- Nouns and verbs outweigh adjectives and adverbs at least 2:1 by rough count.
- Concrete over abstract. `rebar`, not `detritus`. `hip`, not `flank`. `cold`, not `frigid`.
- Register-appropriate technical vocabulary where characters have it: `biokinetic`, `T4`, `Bourse copper`, `tribute`. Do not over-explain.
- Eldritch register may bend grammar for specific effect (a repetition, a tense that does not agree) — only when something wrong is being conveyed, never as ornament.

**Sensory priorities.** Physical sensation first: weight, temperature, wetness, texture, sound, smell. Sight is present but not privileged the way prose default tends to privilege it. Interiority is shown through physical detail, not stated.

**What is described.** The one or two specific things that do the work. A scar. A clock. The wind. The cut through the canvas. A silence where there should be birdsong.

**What is omitted.** Backstory unless it is acting in the scene. Emotional labels unless the character says them. Explanation of setting rules. What the reader can assemble from detail.

**Voice consistency.** Across scenes, the narrator sounds like the same narrator. Observational, spare, unsentimental.

**Voice variation.** Dialogue honors character voices per narration.md. NPC thought is not ventriloquized; what NPCs know is inferred by the reader from what they do and say.

### 3.3 Anti-patterns (complete list)

Each anti-pattern is a failure mode the narrator must avoid. Each has a recognizable signature and a corrective principle.

**1. Power-spectacle.** Describing power use as impressive.
- *Bad*: "With a mighty kinetic blast, Preston sent the Wretches flying."
- *Good*: "Preston killed three of them and did not move from where he stood."
- *Fix*: Power is a physical fact. Describe the effect; do not adorn it.

**2. Heroic framing.** Framing violence or victory as noble.
- *Bad*: "Mara rose to meet the threat, undaunted."
- *Good*: "Mara caught his wrist."
- *Fix*: The character does the thing. The narrator does not applaud.

**3. Adjectival pile-up.** More than two adjectives on a noun.
- *Bad*: "the ancient, ruined, crumbling, blood-soaked cathedral."
- *Good*: "the cathedral." Or, if distinction matters: "the bombed cathedral."
- *Fix*: Pick one adjective. Sometimes pick none.

**4. Comic-book pacing.** Action beats that escalate without earning it.
- *Bad*: "Then, with shocking speed, she spun and unleashed—"
- *Good*: "She was already moving."
- *Fix*: Pace is tempo, not volume.

**5. Genre pastiche.** Prose that belongs in a different register.
- *Bad*: "In a world where the dead walked and the gods were silent, one woman..."
- *Good*: "It was the third winter."
- *Fix*: If the sentence sounds like it belongs in a different kind of fiction, it does.

**6. Consolation.** Balancing a bad thing with a good thing within the same scene.
- *Bad*: After a death, "but in her sacrifice, something was preserved."
- *Good*: After a death, stop.
- *Fix*: Don't balance. Don't soften.

**7. Moralizing.** Narrator passing judgment.
- *Bad*: "Volk's cruelty was unimaginable."
- *Good*: "Volk took the man's hand off at the wrist and handed it to the clerk to log."
- *Fix*: Show the act. Let the reader conclude.

**8. Sentimentality.** Decorative emotional description.
- *Bad*: "She gazed at the sunset, thinking of all she had lost."
- *Good*: "The sun went down. She stayed in the garden past the light."
- *Fix*: Character action carries the weight.

**9. Irony / meta-commentary.** Winking at the reader.
- *Bad*: "Of course, in this new world, such luxuries were a thing of the past."
- *Good*: Omit. The world is real to the characters.
- *Fix*: No distance between narrator and world.

**10. Exposition dump.** Narrator explaining background.
- *Bad*: "The Federal Continuity Command, the largest organized polity in the region, had been..."
- *Good*: "Scrip was trading at twelve to the copper at the Camden ferry that week, and someone had written the rate on the post in chalk."
- *Fix*: Show status through detail.

**11. "In a world where."** Establishing cadence of commercial fiction.
- *Fix*: Begin in the scene.

**12. Over-explanation of mechanics.** Narrator reifying game rules.
- *Bad*: "Her condition track dropped as she took the blow."
- *Good*: "She took the blow and sat down hard."
- *Fix*: Mechanics are not in the fiction.

**13. Damage/status invention.** Narrator adding effects not in payload.
- *Fix*: If the payload does not say the enemy is bleeding, the enemy is not bleeding.

**14. Character invention.** Narrator adding named or distinct NPCs not in payload.
- *Fix*: Only the combatants_present / npcs_present in the payload exist in the scene.

**15. Resolving the anomalous question.** Narrator explaining eldritch or Warped origins.
- *Fix*: Describe what is wrong. Do not explain why.

**16. Breaking the fourth wall.** Narrator addressing the player as player.
- *Fix*: Second-person "you" may appear sparingly as narrator reference to PC. Never as meta reference to the person at the keyboard.

**17. Comic mechanical naming.** Power names spoken in prose.
- *Bad*: "She activated her Kinetic Burst."
- *Good*: "The wall went out."
- *Fix*: Powers in the fiction are the effects. Names are for mechanics.

**18. Scene-end summation.** Narrator closing a scene with a thesis statement.
- *Bad*: "It had been a long day, but she had survived."
- *Good*: End on the last concrete detail.
- *Fix*: No summary. Stop.

**19. Adjective as judgment.** An adjective that labels rather than describes.
- *Bad*: "the sinister figure."
- *Good*: "the figure. It was waiting."
- *Fix*: Adjectives are for facts, not labels.

**20. Anachronism from before.** References to pre-Onset systems still operating.
- *Bad*: "She checked her phone."
- *Good*: Phones do not work. Do not check phones.
- *Fix*: Setting constraints are always live.

### 3.4 Quality checks for register drift

After narration is produced, validation (§7) runs:

- **Adjective density check**: if adjectives > 15% of words, flag.
- **"mighty/epic/devastating" blacklist check**: any blacklisted word flags.
- **Heroic framing keyword check**: `triumph`, `vanquish`, `rise up`, `undaunted`, `stood tall`, `unleashed`, `heroic`, `noble`, `valor` flag.
- **Exposition signature check**: sentences beginning `The {faction} was` or `In this world` flag.
- **Power-name check**: if a known power_id appears in the prose, flag.
- **Second-person frequency check**: `you`/`your` > N per 100 words where payload format is not explicitly second-person, flag.

Flags do not fail the narration by themselves (any one could be a false positive). Two or more flags trigger the retry path (§7).

---

## Section 4 — Context Budget

### 4.1 Token targets per prompt type

Soft targets for total prompt+payload size (in tokens; approximate):

| scene_type | prompt+payload | narration output |
|---|---|---|
| combat_turn | ≤ 800 | 60-200 |
| scene_framing | ≤ 600 | 120-260 |
| situation_description | ≤ 700 | 100-220 |
| dialogue | ≤ 900 | 80-260 |
| transition | ≤ 400 | 40-120 |
| character_creation_beat | ≤ 700 | 100-250 |
| time_skip | ≤ 900 | 120-320 |
| death_narration | ≤ 600 | 120-280 |

If a payload's `state_snapshot` exceeds the prompt budget, compaction kicks in (§4.2).

### 4.2 Compaction procedures per scene_type

Compaction is implemented in `emergence/narrator/compaction.py`. Each scene_type has a compactor that reduces world state to the minimal payload the narrator needs.

**General rules applied to all compactions:**
- Convert lists of >5 items to top-N-by-relevance summaries. Relevance is defined per-field.
- Convert full NPC objects to `{id, display_name, role, current_posture, voice_summary}` projection.
- Convert faction objects to `{display_name, one_sentence_current_situation}`.
- Convert full location objects to `{display_name, type, ambient, notable_features_brief, description_summary}`.
- Dates as "T+1y 3m 14d" canonical; no wall-clock timestamps in narrator payloads.

**Per-scene compaction:**

- **combat_turn**: include only the current round, the actor, and all combatants with `visible_state_summary` (not full sheets). Terrain: current zone only, not all zones. Actor action: canonical Action object (verb, target, power_id). Payload does not include win/loss conditions; the narrator does not need them.
- **scene_framing**: include the location (with ambient and up to 3 notable_features), the character's `arriving_from` if different, npcs_present projected to posture. Exclude faction politics, clocks, inventory.
- **situation_description**: include tension, present npcs projected, recent_events_short (up to 3), time_of_day, character_condition_summary. Exclude full relationship ledger, exclude choice list.
- **dialogue**: include speakers with voice_summary and will_reveal/will_withhold lists, subtext one sentence. Exclude faction overview, exclude mechanics.
- **transition**: the smallest payload. From-scene and to-scene brief, elapsed_time, one-sentence state delta. Nothing else.
- **character_creation_beat**: the beat_intent, the creation_state_so_far (small by design), a few specific_prompts. Exclude world state entirely.
- **time_skip**: a precomputed `headline_events` list (capped at 5, top-weighted by `emotional_weight * scope_weight`), character drifts summarized, one-sentence world drift. The full tick log is NOT included.
- **death_narration**: character summary, cause_of_death, a precomputed `final_callbacks` list of up to 3 items drawn from character history (selected by weight).

### 4.3 Continuity passing

`context_continuity` is populated for every payload within a scene continuum.

- **`last_narration_summary`**: a ≤20-word summary of the immediately preceding narration. Generated by a summarizer routine (`narrator/continuity.summarize_last`). The summarizer is simple: take the last 1-2 sentences of the prior narration, reduce by removing modifiers, cap at 20 words. Heuristic; not perfect; adequate.
- **`scene_history_summary`**: a ≤60-word summary of the scene so far. Accumulated across payloads: after each narration, `update_scene_history(new_narration)` appends a one-sentence synopsis to the scene_history buffer. When the buffer exceeds 60 words, the oldest sentences are compressed.
- **`key_callbacks`**: up to 5 specific items the narrator should be able to reference (a detail mentioned earlier, an NPC name already introduced, a clock tick). Populated from scene-specific rules: e.g., combat scenes callback named combatants, scene_framing callbacks items that situational_description will want to reference.

Scene continuity resets on mode transitions except combat->transition immediately after outcome (the transition narration may callback to combat).

### 4.4 Long-session handling

Long sessions accumulate session_log entries and scene_history state.

- Scene history is scene-scoped, not session-scoped. Entering a new location or new framing resets scene_history.
- Session-level continuity (e.g., "it is late afternoon, and it has been a long day") is carried in the character's `fatigue_level` and `current_condition_summary`, not in scene_history.
- The session log grows as a JSONL; it is not fed to the narrator. It is for player review and post-mortem.
- If scene_history compaction cannot keep the payload under budget after 10 narrations in a scene, force a `scene_framing` refresh on the next narration to reset state.

---

## Section 5 — Narration Queue

The narration queue is the communication channel between the Python runtime (producer) and the narrator (Claude reading this chat, as consumer).

### 5.1 Queue file format

`{save_root}/runtime/narration_queue.jsonl` — append-only JSON Lines.

Three record types:

**PAYLOAD record:**
```json
{"type":"payload","seq":N,"ts":"ISO","scene_type":"...",
 "payload":{<full Narrator Payload schema>}}
```

**NARRATION record (written by narrator after reading a PAYLOAD):**
```json
{"type":"narration","seq":N,"ts":"ISO","for_seq":N,
 "prose":"<the prose>",
 "word_count":int,
 "flags":[...]}
```

**PROTOCOL record (for errors, sync, protocol-level messages):**
```json
{"type":"protocol","seq":N,"ts":"ISO","event":"fallback|retry|validation_failure|resync","detail":{...}}
```

### 5.2 Write procedure (runtime)

```
emit_payload(payload):
  seq = next_seq()
  record = {"type":"payload", "seq":seq, "ts":now_iso(),
            "scene_type":payload.scene_type, "payload":payload.as_dict()}
  atomic_append(queue_path, json.dumps(record) + "\n")
  return seq

wait_for_narration(seq, timeout=config.narrator.timeout_seconds):
  deadline = now() + timeout
  while now() < deadline:
    narration = scan_queue_for_response(seq)
    if narration: return narration
    sleep(poll_interval)   # default 0.5s
  raise NarratorProtocolError("timeout", seq=seq)
```

Atomic append: open in append mode, write, flush, fsync. Lines are complete or absent; never partial.

### 5.3 Read procedure (narrator)

The narrator reads the queue. Conceptually:

```
loop:
  find next PAYLOAD record with no matching NARRATION
  apply the prompt template for scene_type
  produce prose per §2 prompt text
  run self-check per §3.3 anti-patterns
  write NARRATION record for that seq
```

In Claude Code, this manifests as: Claude reads the stdout stream, sees the payload (which Python has printed alongside writing to the file), writes the prose into the chat, and a companion handler writes the NARRATION record back to the queue. Exact plumbing is implementation-side; the contract is the queue file and the seq/for_seq correspondence.

### 5.4 Synchronization

- The queue is single-producer (runtime), single-consumer (narrator). No locking required; append-only discipline suffices.
- `seq` is a monotonically increasing integer per save, persisted in `{save_root}/runtime/narration_seq.txt`.
- If the queue file is absent on session start, it is created empty.
- On session start, the runtime reads the tail of the queue to find the highest existing seq and continues from seq+1.

### 5.5 Error handling

- **Timeout on narration**: after config timeout, write a PROTOCOL record (`event:"timeout"`) and invoke narrator fallback (per §7 and runtime §6.3).
- **Out-of-order narration**: narration for a seq earlier than expected is logged and discarded (already handled).
- **Duplicate narration**: second narration for the same seq is logged and discarded.
- **Malformed narration record**: parse error triggers PROTOCOL record (`event:"validation_failure"`) and retry path.
- **Queue file corruption** (truncated line, malformed JSON): runtime rebuilds queue tail from last known good line; logs the corruption; continues.

---

## Section 6 — Forbidden Behaviors

Enumerated list of what the narrator must never do. Each has examples. Violations trigger validation failure (§7).

1. **Mechanics invention.** Inventing damage, track changes, status effects, hit/miss outcomes. *Bad*: "the blow scraped against her armor for minor damage." *Good*: "the blade slid along the canvas of her jacket."

2. **Damage/status invention beyond payload.** Including effects not in `outcome.damage_dealt` or `outcome.status_applied`. If the payload says `bleeding` applied to the target, the target is bleeding. If not, they are not.

3. **Character invention.** Introducing named or distinct characters not listed in `combatants_present`, `present_npcs`, `speakers`. An unnamed "figure" at a distance is acceptable only if the payload's terrain or context supports it.

4. **Resolving anomalous eldritch questions.** Explaining what the Pine Barrens presence is, what the Warped remember, what caused the Onset, what the Echo wants. These are live mysteries; preserve them. Describe what is wrong. Do not explain why.

5. **Breaking the fourth wall.** "As you read this," "dear reader," "the GM," "the system," "your character," addressed as player-outside-character. Forbidden entirely.

6. **Genre pastiche.** Prose that reads as superhero origin, grimdark parody, post-apoc adventure, comic-book caption, fantasy pastiche. *Bad*: "The world had become a crucible, and only the strong would survive." *Good*: delete; start a new sentence with a physical fact.

7. **Comic-book pacing.** Escalation cadence without earned beats. "Then, in a flash—" "Suddenly—" "With blinding speed—". Forbidden as cadence tools.

8. **Spectacle prioritization.** Framing power use or combat as impressive to watch. Powers are physical facts. Combat is friction. Witness is rare and not performed for the reader.

9. **Sentimentality.** Lingering on emotional beats, describing emotions as emotions, implying the reader should feel a particular way.

10. **Over-explanation.** Narrator explaining setting rules, mechanics, relationships, histories in expository paragraphs. If the reader needs to know it, show it.

11. **Consolation.** Balancing loss with gain in the same scene. Affirming meaning. Reassuring the reader.

12. **Moralizing.** Narrator judging characters. "Cruel," "noble," "righteous," "wicked" — as narrator labels, forbidden. As character-observed perception from a specified POV, sometimes permissible (e.g., a character who considers an enemy wicked may think of them as wicked within their thought, but the narrator still does not validate it).

13. **Naming powers in fiction.** Using `power_id` or formal power names ("Kinetic Burst," "Displacement Short") in the prose. The effect is described. The name is for mechanics.

14. **Anachronism from the Before.** Working cars, cell phones, radio, television, aircraft. Reloaded firearms work; heavier weapons do not. Electricity exists only at Peekskill; respect this.

15. **Ventriloquizing the player.** Speaking for the PC beyond what the payload provides. If the payload does not include a spoken_line for the player, the player does not speak directly in the narration; the narrator may indirect ("the courier asked about the weather") but does not invent a quote.

16. **Ventriloquizing NPCs.** Putting words in NPC mouths that are outside their `will_reveal` / `will_withhold` / `voice_summary` bounds.

17. **Scene closure that thesis-statements.** "It was the end of an era." "She had become something new." Final sentences must end on concrete detail, not summary.

18. **Adjective pile-up.** More than two modifiers on a noun.

19. **Second-person drift.** Using "you" as narrator default voice outside direct invocation.

20. **Markdown or structural formatting.** No headers, no bullets, no code blocks, no lists. Prose only, with paragraph breaks.

21. **Prefacing or meta-voice.** "Here is the scene:" "This scene takes place in..." "The following is the narration:" Forbidden. The narration begins with the scene.

22. **Mathematical specificity.** Exact numbers, percentages, timers from mechanical state. "She had three segments of condition remaining" — never. "She was hurt" — if the payload supports it.

---

## Section 7 — Narration Validation

After each narration, before accepting it as the scene's prose, the runtime runs validation in `emergence/narrator/validation.py`.

### 7.1 Verification procedure

```
validate(narration: str, payload: NarratorPayload) -> ValidationResult:
  flags = []
  flags += length_check(narration, payload.output_target.desired_length)
  flags += pattern_check(narration)                # §7.2
  flags += content_check(narration, payload)        # §7.3
  flags += register_check(narration, payload.register_directive)

  severity = classify(flags)
  return ValidationResult(
    flags=flags,
    severity=severity,   # "pass"|"warn"|"retry"|"fallback"
    decision=decide(severity)
  )
```

### 7.2 Pattern checks

- **Length check**: word_count within `desired_length.min_words * (1 - tol)` to `max_words * (1 + tol)` where `tol = config.narrator.word_count_tolerance`. Outside: `retry` flag.
- **Blacklist word check**: `mighty|epic|devastating|triumph|vanquish|undaunted|valor|blinding speed|suddenly|in a flash|unleashed|...`: presence adds `warn` flag.
- **Pacing phrase check**: `then, suddenly`, `with shocking`, `in an instant`: presence adds `warn`.
- **Formatting check**: any `#`, `*`, `-` at line start, triple backticks, or bullet markers: `retry` flag.
- **Prefacing check**: narration begins with "Here", "The following", "This", "In this scene": `retry` flag.
- **Second-person density**: `you/your` words > 4% of total (outside explicit intimate register): `warn`.
- **Power-name check**: any `power_id` or formal name from the payload's `powers` list appears verbatim in prose: `warn`.

### 7.3 Content checks

- **Character-presence check**: every quoted speaker must be in payload's speakers/npcs/combatants. Additions: `retry`.
- **Damage/status conformance**: if narration mentions a named status ("bleeding," "stunned," "shaken," "burning," "exposed," "marked," "corrupted") for a target, that status must be in `outcome.status_applied` for that target. Extra: `retry`.
- **Fact-anchor check**: at least one concrete sensory noun (from a curated list of ~200: weather, textures, specific objects) appears. Absence: `warn`.
- **Eldritch-resolution check**: if register is not `eldritch`, narration should not introduce explicit eldritch content; if register is `eldritch`, narration should not *explain* (heuristic: no sentence of the form "because X is Y" regarding eldritch entities). Violation: `retry`.

### 7.4 Register check

Register-specific pattern expectations:
- `standard`: no strong anti-patterns; passes by default.
- `eldritch`: at least one "wrong" marker (unexpected concrete anomaly) present. Absence: `warn`.
- `action`: average sentence length ≤ 14 words. Exceeding: `warn`.
- `intimate`: word count within tight bounds, dialogue fraction ≥ 30% if format is mixed. Out-of-spec: `warn`.
- `quiet`: long-sentence fraction (sentences > 18 words) ≤ 30%. Exceeding: `warn`.

### 7.5 Severity and decision

```
severity(flags):
  if any flag is kind=retry:
    return "retry"
  if count(warn_flags) >= 2:
    return "retry"
  if count(warn_flags) == 1:
    return "warn"
  return "pass"

decide(severity):
  if severity == "pass":   accept
  if severity == "warn":   accept_with_log
  if severity == "retry":
    if retries_remaining > 0: regenerate with augmented prompt
    else: fallback
  fallback: template narration
```

### 7.6 Failure response — regenerate

On retry, the runtime emits an augmented payload with:
- The original payload intact.
- An additional `narrator_correction` field listing the flags that fired, in neutral language ("length exceeded max by 40 words", "status 'bleeding' in prose but not in outcome").
- An incremented `retry_count` field.

The narrator re-reads and re-produces. Retry limit defaults to 1 (configurable).

### 7.7 Failure response — fallback

If retries exhaust, a template-generated narration is produced from `data/prompts/{scene_type}.fallback.txt`. Templates are minimal:

- **combat_turn.fallback**: "`{actor_name} {verb_description} {target_description_or_empty}. {sensory_texture_from_zone}.`"
- **scene_framing.fallback**: "`{character_name} {arrives_or_is_at} {location_name}. {ambient_sentence}. {notable_feature_sentence_if_any}.`"
- **situation_description.fallback**: "`{location_brief}. {npcs_present_brief}. {tension_rephrased_neutral}.`"
- **dialogue.fallback**: quote-by-quote replay of spoken_lines_or_refusals fields, joined by `{speaker} said,`.
- **transition.fallback**: "`{elapsed_time_phrase}. {character_state_delta_summary_or_empty}.`"
- **character_creation_beat.fallback**: "`{beat_intent_rephrased}. ({prompt_authorship_hint})`"
- **time_skip.fallback**: one sentence per headline_event, concatenated.
- **death_narration.fallback**: "`{character_name} died. {cause_of_death.specific}.`"

Fallback narrations are logged with `narration_degraded` flag on the session. The player may see the quality drop; the session continues.

### 7.8 Accept-with-warning

Severity `warn` records the warning in the session log but accepts the narration. Too many warnings across a session (threshold: 5 per session) elevates the session's narration state to `degraded` and surfaces a notice at session close.

---

## Design Decisions

- **Narrator is Claude at runtime.** No API call from Python. The queue file is the contract. This is mandated by the design brief and constrains all decisions in this doc.
- **Prompt templates are files in `data/prompts/`.** This lets content be iterated without code changes; engine loads at launch and caches.
- **Compaction is the engine's responsibility, not the narrator's.** Narrators cannot be trusted to filter large payloads; compactors in `emergence/narrator/compaction.py` enforce the context budget before the payload is ever written.
- **Three continuity fields, not full scene history.** `last_narration_summary`, `scene_history_summary`, `key_callbacks` are the only continuity hooks; the narrator does not see the full queue history. This matches the context budget discipline.
- **Pattern-and-content validation, not model-based validation.** The validator is rule-based regex and string matching, deterministic, fast, debuggable. No second model call.
- **Retry budget of 1 by default.** Two-phase retry + fallback caps narrator time without losing scenes.
- **Eight scene_types, no more.** The eight defined here cover the surface area; any new scene type would require an engine change, which we do not design around at build-one.
- **Power names forbidden in prose.** Enforces the "powers are physical facts" principle and prevents the narrator from drifting into comic-book cadence.
- **Death narration has its own scene_type with strict forbiddens.** Death is the end of a life; the narrator's job there is hardest and most regulated.
- **Closed status list in validation (seven).** Matches interface-spec. Prevents status drift from the narrator side.
- **Session log narration copies are for player review, not for re-feeding.** Keeping the narrator context strictly payload-bounded prevents drift across long sessions.
- **Fallbacks are intentionally plain.** They should feel like a drop in quality so the player and the developer notice; they should not feel like ordinary narration.

## [NEEDS RESOLUTION]

- [NEEDS RESOLUTION: curated concrete-noun list for fact-anchor check — content authoring task]
- [NEEDS RESOLUTION: tone_reminder excerpts beyond the five registers here — pull from bible as needed]
- [NEEDS RESOLUTION: exact word-count tolerances may need tuning once sample narrations are tested in-flight]
- [NEEDS RESOLUTION: whether the chat transport actually writes narration records to the queue file or whether a shim observes the chat stream and writes on Claude's behalf — implementation-side, out of spec scope]
