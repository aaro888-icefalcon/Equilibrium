# character-creation.md

Specification for Session Zero in Emergence. Produces a complete, validated `Character Sheet` per `interface-spec.md`. Game-time start is T+1y (summer solstice following Onset). All scenes run as `scene_type: "character_creation_beat"` payloads in the runtime.

---

## SECTION 1 — SESSION ZERO COMPLETE FLOW

### 1.1 Scene count and order

Session Zero is **ten scenes** in fixed order. No scene is skippable except where noted. Every scene mutates `Character Sheet.session_zero_choices` and one or more sheet fields per the Game Start Setup table (Section 7).

| # | Scene | Mutates | Pacing |
|---|---|---|---|
| 0 | Opening Framing | name, age_at_onset, seed | 1–2 min |
| 1 | Pre-Onset Occupation | attributes, skills, resources, faction default heat | 3–4 min |
| 2 | Pre-Onset Relationships | relationships (1–3 NPCs), one Goal | 3–4 min |
| 3 | Pre-Onset Location & Circumstance | starting region, location bias for manifestation | 2–3 min |
| 4 | Pre-Onset Immediate Concern | one Goal, one personal stake NPC | 2–3 min |
| 5 | Manifestation Moment | power_category_primary, secondary, tier, powers, one breakthrough record, one harm or status | 4–5 min |
| 6 | Year One — First Weeks | condition_tracks deltas, harm, skills, resources | 2–3 min |
| 7 | Year One — First Encounter With a Faction | heat, one relationship, faction standing entries | 3–4 min |
| 8 | Year One — Critical Incident | breakthrough OR persistent harm OR corruption; relationship change | 3–4 min |
| 9 | Year One — Settling Into A Place | location, inventory, one Goal, post-creation validation | 2–3 min |

Real-time target **22–35 minutes** at default narrator length. The runtime enforces a soft cap: if total elapsed real time exceeds 45 minutes, scene 7+ choice sets present a flagged "fast path" first option that fixes likely-default consequences and proceeds.

### 1.2 Save points

`Character Sheet` and `World State.active_scene` are persisted **after every scene** to `save_root/player/character.json` with `active_scene.type = "session_zero"` and `active_scene.scene_id = "sz_{n}"`. Resume reads `active_scene` and re-enters the next scene.

### 1.3 Narrator register

All scene narration uses `register_directive: "standard"` except Scene 5 (manifestation), which uses `"intimate"` for the inward-turning beat and `"action"` for any externalized manifestation incident, and Scene 8, which uses `"action"` or `"eldritch"` per critical incident type. `forbidden` includes `"invent_powers_not_in_payload"`, `"resolve_anomalous_eldritch_question"`, `"narrate_outcomes_player_did_not_choose"`.

---

## SECTION 2 — OPENING FRAMING

### 2.1 Narrator framing prose template

The opening narration is fixed prose, parameterized only by chosen name and chosen age. The narrator generates from this template with no embellishment beyond the variables.

> The Onset was a year ago this season. You were [AGE] years old then. You are [AGE+1] now.
>
> Most of the people you knew are dead. The ones who lived live differently. The world that existed before — the trains, the lights, the calls placed and answered, the certainty that tomorrow would resemble today — is gone, and the gone-ness is the air everyone now breathes. Some days you forget what the air used to be like. Some days you do not.
>
> You are a person in a smaller, harder world. You can do things now that no one could do before. So can almost everyone left alive.
>
> Tell me your name.
>
> Tell me how old you were on the day everything stopped.

### 2.2 First choice — name and age

Two free-text inputs, validated:

- `name`: 1–60 characters, any Unicode letters / spaces / hyphens / apostrophes. No control characters. Default if blank: random pick from a name pool drawn from setting NPCs (e.g., "Marisol Reyes", "Theo Blackwell", "Anya Sokolova").
- `age_at_onset`: integer 16–65. Below 16 or above 65 is rejected with the prompt "the campaign begins one year after the Onset; choose an age you were on that day, between sixteen and sixty-five."

`current_age = age_at_onset + 1` is computed and stored.

### 2.3 Random seed

A random seed is generated at session start and stored in `session_zero_choices.seed` (uint64). This seed governs all randomized outcomes inside Session Zero, including manifestation tier roll, power selection within category, and any "random" branches in critical incidents. Identical seed + identical choices = identical character. Surfaced in the post-creation summary so the player can record it for replay.

### 2.4 How the opening choices establish pre-onset scene

`age_at_onset` is referenced by Scene 1 (occupation eligibility — see filter rules), Scene 2 (relationship offerings shift between "parents" / "children" / "spouse" depending on age), and Section 7 aging baseline. The name appears in subsequent scene narration. The seed is locked.

---

## SECTION 3 — PRE-ONSET IDENTITY SCENES

Every pre-onset scene follows this structure:

- **Narrator framing**: 60–120 word prose template, parameterized.
- **Choice set**: 4–8 options, each with a one-line description shown to the player.
- **Per-choice consequences**: structured deltas applied on selection.
- **Stored in `session_zero_choices`** under the scene's key.

Mechanical consequences use the attribute die-size scale `{4, 6, 8, 10, 12}`. Attributes default to d6 for all six (`strength`, `agility`, `perception`, `will`, `insight`, `might`) before scene 1. Scenes raise some, leave others alone. **Maximum any attribute reaches via Session Zero alone is d10**; d12 requires breakthroughs.

> **Attribute meanings (locked here for cross-spec consistency):**
> `strength` — applied muscular force. `agility` — speed, balance, fine motor. `perception` — senses and quick read of environment. `will` — resolve under stress, mental resistance. `insight` — judgment, social read, comprehension. `might` — power potency; the die used for power-output checks.

### 3.1 Scene 1 — Occupation

#### Narrator framing

> Before the Onset you had a life and a job. The job is gone now in any form that matters, but the habits of it are still in your hands and in how you think.
>
> What did you do?

#### Choice set

Twelve options. Each option lists `display`, `attribute_deltas` (added to defaults), `starting_skills` (skill_id → integer proficiency, 1–4), `resources` (resource → quantity), `default_heat_modifiers` (faction_id → delta), `narrative_tag`, and `notes`.

```
1. Federal employee (DOD civilian, clerk, analyst, engineer)
   - perception +2, insight +2 (d8 each)
   - skills: bureaucracy 3, firearms 1, regional_geography 2, literacy 4
   - resources: scrip_sentiment 1
   - heat: fed-continuity -1 (lower starting suspicion)
   - tag: "former federal"

2. Police / first responder / EMT
   - strength +2, will +2 (d8 each)
   - skills: firearms 3, melee 2, first_aid 3, intimidation 2, urban_movement 2
   - resources: side_arm_pre_onset 1
   - heat: iron-crown +1 (recognized as ex-authority)
   - tag: "former badge"

3. Soldier or veteran (US military, enlisted or officer)
   - strength +2, will +2, perception +1 (d8/d8/d6+)
   - skills: firearms 4, melee 2, tactics 2, command 1, field_medicine 2
   - heat: catskill-throne -1 (Preston's recruiters notice veterans)
   - tag: "veteran"

4. Doctor, nurse, or paramedic
   - insight +2, perception +1 (d8/d8)
   - skills: first_aid 4, surgery 2, pharmacology 3, literacy 4
   - resources: medical_kit_partial 1
   - heat: yonkers-compact -2 (healers welcome)
   - tag: "medical"

5. Farmer or agricultural worker
   - strength +2, will +1 (d8/d6+)
   - skills: agriculture 4, animal_handling 3, weather_read 2, basic_repair 2
   - heat: delmarva-harvest-lords -1, central-jersey-league -1
   - tag: "of the land"

6. Tradesperson (electrician, plumber, mechanic, carpenter, machinist)
   - agility +2, insight +1 (d8/d6+)
   - skills: craft 3, basic_repair 4, scavenging 2
   - resources: tools_pre_onset 1
   - heat: flushing-edison-cluster -1 (skilled hands respected)
   - tag: "skilled hands"

7. Office worker (white-collar professional)
   - insight +2 (d8)
   - skills: bureaucracy 2, literacy 4, negotiation 2
   - resources: contacts_thin 1
   - tag: "former office"

8. Service worker (retail, food service, hospitality, driver)
   - agility +1, perception +2 (d6+/d8)
   - skills: streetwise 3, negotiation 2, urban_movement 2, languages 1
   - tag: "service"

9. Educator or academic (teacher, professor, librarian)
   - insight +2, will +1 (d8/d6+)
   - skills: literacy 4, history 3, languages 2, instruction 3
   - heat: central-jersey-league -1 (Rutgers-Princeton sphere)
   - tag: "educator"

10. Criminal (thief, dealer, smuggler, fence — petty to organized)
    - agility +2, perception +1 (d8/d6+)
    - skills: streetwise 4, stealth 3, melee 2, intimidation 2, scavenging 2
    - heat: iron-crown -1 (criminal networks have continuity), philadelphia-bourse +1
    - tag: "underside"

11. Student (college or graduate program)
    - insight +1, perception +1 (d6+/d6+)
    - skills: literacy 4, languages 1, instruction 1
    - resources: youth 1
    - tag: "student"
    - eligibility: age_at_onset 16–28

12. Manual laborer / construction / dockworker / warehouse
    - strength +2, will +1 (d8/d6+)
    - skills: melee 2, basic_repair 2, scavenging 3, urban_movement 2
    - heat: south-philly-holding -1 (recognized type)
    - tag: "muscle"
```

Eligibility filter: option 11 hidden if `age_at_onset > 28`. All others always available.

`session_zero_choices.occupation` stores the selected option index and the full resolved deltas (for audit and replay).

### 3.2 Scene 2 — Relationships

#### Narrator framing

> You did not live alone before, even if you lived alone. People had a claim on you. You had a claim on them.
>
> Tell me about the one person who mattered most.

#### Choice set

Six relationship-archetype options. Each generates one named NPC (saved to `npcs/{generated_id}.json`) and one entry in `Character Sheet.relationships`. Each option also offers a follow-up: `status_at_game_start` ∈ {`alive_present`, `alive_separated`, `dead`, `transformed`, `missing`}.

```
1. Spouse / partner / lover
   - eligibility: age_at_onset >= 18
   - generates: NPC age within ±10 years of player
   - relationship.standing: +3 if alive_present/alive_separated; +2 if missing; remains +3 historical if dead
   - relationship.current_state: "spouse" / "estranged_spouse" / "widowed" / "transformed" / "missing"
   - generates Goal: id "find_them" (if missing) / "honor_their_memory" (if dead) / "rebuild_with_them" (if alive_present) / "reach_them" (if alive_separated) / "release_them" (if transformed). pressure: 3
   - attribute: will +1 if dead/missing/transformed (grief-hardened)

2. Parent (mother or father, player chooses)
   - eligibility: age_at_onset 16–55
   - generates: NPC age player_age + 18 to + 40
   - standing: +2 baseline, modifiable by status
   - current_state per status
   - if alive: skills inherit one — player picks one parent skill from a 4-option pool keyed to parent's implied occupation
   - generates Goal: see status; pressure 2
   - attribute: insight +1 (parental teaching residue)

3. Child (one or more; player names eldest)
   - eligibility: age_at_onset 22–65
   - generates 1–3 NPCs as chosen; ages 0–25 capped by player age
   - standing: +3 unconditional
   - current_state: "parent_of"
   - generates Goal: "keep_them_alive" (alive) / "find_them" (missing) / "avenge_them" (dead) / "stay_with_them" (transformed). pressure: 5 (highest)
   - attribute: will +1, perception +1
   - resource: dependents N

4. Sibling
   - generates: NPC similar age
   - standing: +2 baseline
   - current_state per status; status options include "estranged_pre_onset" with standing 0
   - generates Goal at pressure 2
   - skills: streetwise +1 (shared upbringing)

5. Closest friend
   - generates: NPC similar age
   - standing: +2
   - current_state per status; option "fell_out" with standing -1
   - generates Goal pressure 2
   - skills: one of {negotiation, streetwise, instruction} +1 (player picks)

6. Mentor or boss
   - generates: NPC older, profession-aligned with Scene 1 occupation
   - standing: +1 if respect, -1 if resentment (player chooses)
   - current_state per status
   - generates Goal: "honor_their_lesson" / "surpass_them" / "find_what_they_left_behind" pressure 1
   - resource: contacts_thin +1
   - attribute: insight +1

OPTIONAL FOLLOW-UP (free-text, skippable): one secondary relationship.
   - same generation procedure, single NPC, standing +1 to +2, no Goal generated.
   - capped at one to keep scope bounded.
```

NPC generation procedure (deterministic given seed):

1. Pick gender per setting demographic baseline (sex ratio 79:100 male:female post-Onset in adults; for parents/spouse the player explicitly chooses).
2. Generate name from the setting name pool (ethnicity weighted by player's Scene 3 region selection, defaulted before then to mid-Atlantic baseline).
3. Set `species` = "human" by default; if player has not yet chosen species (Section 6 runs interleaved with Scene 1, see below), defer.
4. Set `age` per archetype rules above.
5. Roll manifestation per the same circumstance-mapping table used for player Scene 5 (see 4.2), simplified: NPCs roll one category and a tier from the population pyramid (T1 40 / T2 25 / T3 15 / T4 10 / T5 5 / T6 3 / T7 1.5 / T8 0.4 / T9 0.08 / T10+ 0.005, normalized).
6. Set `status` per `status_at_game_start` choice.
7. Write `voice` and `personality_traits` from a small archetype table (3 trait-slots filled from the archetype's pool).
8. Persist.

`session_zero_choices.relationships` stores choices made.

### 3.3 Scene 3 — Pre-Onset Location and Circumstance

#### Narrator framing

> When the Onset hit, you were somewhere specific. Doing something specific. The where and the what of that hour shaped what happened next.
>
> Where were you? What were you doing?

#### Choice set

Two-stage: pick a region, then pick a circumstance within that region.

**Stage A — Region (eight options).** Each sets `pre_onset_region`, biases `starting_location` for game start (Section 7), and adjusts NPC ethnic generation defaults retroactively if Scene 2 NPCs were generated as defaults.

```
1. New York City (Manhattan, Brooklyn, Queens, Bronx, Staten Island)
2. Northern New Jersey (Newark, Jersey City, Paterson, Bayonne)
3. Hudson Valley (Yonkers, Peekskill, White Plains, Catskills)
4. Central New Jersey (Princeton, New Brunswick, Trenton, the corridor)
5. Philadelphia and inner suburbs
6. Lehigh Valley / Bucks County
7. Baltimore / DC corridor
8. Delmarva Peninsula / Chesapeake shore
```

**Stage B — Circumstance (eight options, generic across regions).** This is the input to Section 4's circumstance-to-category mapping. Each circumstance carries the **base category-distribution** that Section 4 applies.

```
A. At work, indoors, alone or near-alone
B. At work, outdoors, with people
C. Commuting (car, bus, subway, bicycle, on foot)
D. At home with family
E. At a public place (store, restaurant, park, gym, school, church)
F. Asleep
G. In motion: exercising, athletic activity, fighting, fleeing
H. In a crisis: medical, emotional, witnessing violence, being attacked
```

Stage B sets `session_zero_choices.onset_circumstance` for use in Scene 5.

### 3.4 Scene 4 — Pre-Onset Immediate Concern

#### Narrator framing

> Everyone carried something into that day that did not survive it. A worry. A debt. A diagnosis. A fight you hadn't finished. Something you were going to do that week.
>
> What was yours?

#### Choice set

Eight options. Generates a personal-stake Goal (or modifies an existing one) and may generate one additional NPC.

```
1. Money trouble (debt, loss of job, eviction)
   - Goal: "rebuild_what_was_lost", pressure 2
   - resources: -- (no starting wealth boost)
   - attribute: will +1

2. A sick or dying family member
   - generates NPC if not already present (parent/sibling, dying or recently dead)
   - Goal: "honor_them" or "save_someone_else_from_this", pressure 3
   - skills: first_aid +1

3. A romantic crisis (breakup, affair, custody fight)
   - generates Goal: "settle_the_account", pressure 2
   - if a spouse/partner exists from Scene 2, modifies their standing -1 to 0
   - attribute: insight +1

4. A legal problem (case pending, recently arrested, recently released)
   - heat: fed-continuity +1 OR iron-crown -1 (player picks: fugitive vs. recognized)
   - skills: streetwise +1
   - Goal: "stay_free", pressure 2

5. A new job, move, or major life change about to happen
   - Goal: "still_become_who_I_was_going_to_be", pressure 1
   - resources: contacts_thin +1
   - attribute: insight +1

6. A child on the way (yours or a partner's)
   - eligibility: a partner exists from Scene 2 (alive)
   - generates child NPC, age 1 at game start (born T+0.25y)
   - relationships entry: standing +3, current_state "infant_dependent"
   - Goal: "keep_them_alive", pressure 5 (overrides if duplicate)
   - resource: dependents +1
   - attribute: will +1

7. A grudge or open enemy
   - generates one NPC at standing -2, current_state "enemy"
   - Goal: "settle_with_them", pressure 2
   - skills: intimidation +1
   - status_at_game_start choice: same set as Scene 2

8. Nothing in particular — life was steady
   - no Goal generated
   - resources: stability 1
   - attribute: will +1, insight +1
   - tag: "from a quiet life"
```

If choice 6 conflicts (no partner), present a fallback narration: "There was no one carrying it but you" — generates child NPC anyway with status `infant_dependent` and a Goal "keep_them_alive" pressure 5; flags the player as solo parent.

`session_zero_choices.immediate_concern` stores the selection.

---

## SECTION 4 — MANIFESTATION MOMENT

### 4.1 Narrator framing

Run as a two-beat scene. Beat 1 is internal (`register: "intimate"`); Beat 2 is external (`register: "intimate"` if circumstance was passive, `"action"` if active).

**Beat 1 framing template:**

> [TIME-OF-DAY descriptor for the chosen circumstance]. [SENSORY DETAIL keyed to circumstance]. And then —
>
> Something inside you opened, or closed, or turned. The word for it would come later, and the word would not be right. What you felt was not pain. What you felt was that you had been carrying something all your life without knowing it, and now you knew.

**Beat 2 framing template** (one of three based on circumstance category):

- *Passive circumstances (A, D, E, F):*
  > Around you, the lights died. The hum that had always been the floor of the world stopped humming. People started to scream, somewhere. You stood up. You felt your hands.
- *Mobile circumstances (B, C, G):*
  > The world fell. [SPECIFIC FAILURE: the engine, the elevator, the lights, the train, the music, the signal]. People around you went down with it. You did not. You knew, in the way you knew which way was up, that something in you had not gone down with the rest.
- *Crisis circumstances (H):*
  > The thing that was already happening kept happening, and the world's collapse arrived inside it. [SPECIFIC: the man who was already going to hit you, the bleeding that would not stop, the engine you were already driving fast]. You did not have time to be afraid the way the others were. You were already inside it.

### 4.2 Manifestation mechanic

Manifestation is **circumstance-conditioned weighted draw + tier roll + power selection**. Three sub-procedures, in order.

#### 4.2.1 Circumstance → category distribution

The player's Scene 3 Stage-B circumstance (A–H) determines a probability distribution over the seven power categories. Distributions sum to 1.0. The seven category ids (per `interface-spec.md`):

`physical_kinetic`, `perceptual_mental`, `matter_energy`, `biological_vital`, `auratic`, `temporal_spatial`, `eldritch_corruptive`.

Population baseline (from `powers.md`): physical_kinetic .28, perceptual_mental .15, matter_energy .14, biological_vital .14, auratic .12, temporal_spatial .09, eldritch_corruptive .015 (residual normalized).

Per-circumstance tilt (multiplicative weights, then renormalized):

| Code | Circumstance | physical | perceptual | matter | biological | auratic | temporal | eldritch |
|---|---|---|---|---|---|---|---|---|
| A | At work indoors alone | 1.0 | 1.4 | 1.2 | 0.9 | 1.0 | 1.1 | 1.0 |
| B | At work outdoors with people | 1.3 | 0.9 | 1.1 | 1.2 | 1.0 | 0.8 | 0.9 |
| C | Commuting | 1.4 | 1.0 | 0.9 | 0.8 | 0.8 | 1.4 | 0.9 |
| D | At home with family | 0.9 | 1.2 | 0.9 | 1.4 | 1.4 | 0.8 | 0.9 |
| E | At a public place | 1.0 | 1.3 | 0.9 | 1.0 | 1.3 | 0.9 | 1.0 |
| F | Asleep | 0.7 | 1.6 | 0.8 | 1.1 | 1.1 | 1.4 | 1.2 |
| G | In motion / exertion / combat | 1.8 | 0.9 | 1.0 | 1.0 | 0.9 | 1.0 | 0.7 |
| H | In crisis | 1.4 | 1.2 | 1.0 | 1.2 | 1.0 | 0.8 | 1.2 |

#### 4.2.2 Specific circumstance → category mapping table (30 entries)

The player's Scene 3 selection is one of eight categories, but the *narrative* circumstance can be more specific. The runtime asks one follow-up free-text or a short-list. The specific circumstance is matched against this table; on match, a category bias of **+0.5 added to that category's weight** before renormalization. Unmatched specifics fall through to the base table.

```
Specific circumstance               → bias category
1.  driving a car                   → physical_kinetic
2.  riding a subway                 → temporal_spatial
3.  on a bicycle                    → physical_kinetic
4.  on a plane (in flight)          → temporal_spatial   (if survived: see Critical Incident)
5.  walking up stairs               → physical_kinetic
6.  in an elevator                  → temporal_spatial
7.  at a hospital, treating patient → biological_vital
8.  at a hospital, as patient       → biological_vital
9.  at a school, teaching           → perceptual_mental
10. at a school, learning           → perceptual_mental
11. on a job site, lifting          → physical_kinetic
12. on a job site, machining        → matter_energy
13. cooking at home                 → biological_vital
14. holding a child                 → auratic
15. in bed with a partner           → auratic
16. asleep, dreaming                → perceptual_mental
17. in argument with someone        → perceptual_mental
18. in physical fight               → physical_kinetic
19. fleeing a threat                → temporal_spatial
20. delivering a baby               → biological_vital
21. attending a funeral             → auratic
22. at a religious service          → auratic
23. in a museum or library          → perceptual_mental
24. in a fire or burning building   → matter_energy
25. underwater (swimming, drowning) → biological_vital
26. in extreme cold                 → matter_energy
27. doing precision work (jewelry, surgery, engraving) → matter_energy
28. comforting someone in grief     → auratic
29. high on drugs or drunk          → eldritch_corruptive
30. witnessing a death              → perceptual_mental
```

[NEEDS AUTHORSHIP: bible does not specify whether substance-altered states correlate with eldritch onset. Decision held in design_decisions.]

#### 4.2.3 Tier roll

After category is selected, draw `tier` from a Session-Zero–restricted pyramid:

```
T1: 0.50, T2: 0.30, T3: 0.15, T4: 0.05
T5+ unavailable from session zero except through Critical Incident path (Scene 8) — see 4.2.5.
```

Modifiers to the tier roll:

- Circumstance H (in crisis): +0.10 to T3 weight, +0.05 to T4, taken from T1.
- Circumstance F (asleep): -0.05 from T3/T4, added to T1 (sleeping manifestations are usually low-tier).
- Pre-onset occupation `tag: "veteran"` or `"former badge"`: +0.05 T3, taken from T1 (combat-prepared bodies push tier).
- Pre-onset immediate concern choice 6 (child on way) or 7 (grudge): +0.03 T2/T3 (stake correlates).

All modifiers applied additively; result clamped to non-negative; renormalize.

Tier-ceiling (`tier_ceiling`) is set to current `tier + 2` at session zero close. (Most characters never reach ceiling without breakthroughs; ceiling represents practice headroom within current tier strata.)

#### 4.2.4 Specific power selection within determined category

Each category has a registry of starting powers in `data/powers/` keyed by `power_id` and `tier_minimum`. Session Zero selection procedure:

1. Filter category registry for powers with `tier_minimum <= drawn_tier`.
2. Partition into **starter set** (tier_minimum <= 2, generic, broadly applicable) and **specialty set** (tier_minimum 3+).
3. Present player with 4 options drawn deterministically from the seed: 2 from starter set, 2 from specialty set if drawn_tier >= 3 (else 4 from starter set).
4. Player picks one. This becomes `powers[0]`, the **anchor power**.
5. Roll secondary category presence: 55% chance (matches population baseline). If secondary present, run identical procedure on the secondary's distribution: secondary is the second-highest weight from 4.2.1 with biological_vital and auratic given +0.1 each as natural co-occurrences. Player picks 1 power from secondary, tier_minimum <= max(1, drawn_tier - 2). This is `powers[1]`, the **secondary power**.
6. `power_category_primary` = drawn category. `power_category_secondary` = drawn secondary or null.

Player agency: choice of power within the four offered, choice of secondary acceptance (player may decline secondary roll for narrow-specialist build; this raises tier_ceiling +1 to compensate).

Determined elements: category (driven by circumstance), tier (rolled), specialty option set (seeded).

#### 4.2.5 Critical Incident tier escalation (forward reference)

Year One Scene 8 may produce an in-scene breakthrough lifting tier by exactly 1, capped at T5 from Session Zero. See Section 5.4 for triggers.

### 4.3 Manifestation scene narration template

After mechanical resolution, narrator produces a **closing beat** template:

> What you found in your hands [or your eyes, or your throat, or the air around you, or the spaces between thoughts] was [POWER NAME, in plain language — not its mechanical effect, what it felt like]. You did not have a word for it. The word for it would come from other people, in the months that followed, and the word would never be quite right.
>
> [If tier 1–2:] It was a small thing. Most people, you would learn, had something small. You were not unusual.
>
> [If tier 3:] It was not small. Other people you would meet would notice it, when you used it, in ways that you did not yet know to manage.
>
> [If tier 4–5:] It was not small. You knew immediately that it was not small. The hour of the Onset was full of people learning whether the thing they had become was the kind of thing other people would let live near them. You learned, in that hour, that you were one of those people.

`forbidden` for this beat: `"name_the_mechanical_effect"`, `"narrate_advanced_use"`, `"foreshadow_breakthrough"`.

### 4.4 Player agency vs. determined elements (summary)

| Element | Source | Player chooses? |
|---|---|---|
| Category | Circumstance + roll | No (consequence of Scene 3) |
| Tier | Roll modified by background | No (rolled) |
| Specific anchor power | 4-option presentation | Yes |
| Secondary presence | 55% roll | No, but may decline (narrow build) |
| Secondary category | Weights | No |
| Specific secondary power | 4-option presentation | Yes |
| Felt experience text | Template + power | No (narrator generates) |

---

## SECTION 5 — YEAR ONE COLLAPSE SCENES

Four scenes covering the year between Onset and game start. Each scene runs after manifestation and consumes prior choices.

### 5.1 Scene 6 — First Weeks

#### Narrator framing

> The first three weeks were the worst of them. The dead lay where they had fallen. The food in refrigerators went bad. The people who had not died of the Onset itself died of what the Onset did to the world. You did what you did to keep going.
>
> What did you do?

#### Choice set (4 options)

```
1. Stayed in place. Defended what you had.
   - +1 will, +1 perception
   - skills: melee +1, basic_repair +1, stealth +1
   - condition_tracks.physical -1 segment recovered (you hardened up)
   - resources: shelter_pre_established 1
   - history record: "held position through first weeks"

2. Moved. Found people. Joined a group.
   - +1 insight, +1 agility
   - skills: negotiation +1, urban_movement +1, streetwise +1
   - relationships: generates 1 NPC, standing +1, current_state "first_weeks_companion", status options apply
   - history record: "moved in the first weeks; found people"

3. Helped. Treated wounded, brought water, dug graves.
   - +1 will
   - skills: first_aid +2, instruction +1
   - resources: reputation_local 1 (helps with sim activities later)
   - heat: yonkers-compact -1, central-jersey-league -1 (good word travels)
   - condition_tracks.mental +1 (you saw too much)
   - history record: "spent the first weeks helping"

4. Took. Used what was in you to take what others had.
   - +1 strength, +1 will
   - skills: intimidation +2, melee +1, scavenging +2
   - resources: scavenged_goods 2, scrip_pre_onset 1
   - heat: fed-continuity +1, iron-crown -1 (you're useful, they remember)
   - condition_tracks.social +1 (people remember)
   - corruption +1 if eldritch_corruptive primary, else 0
   - history record: "took what was needed in the first weeks"
```

`narration register: "standard"`. Length 100-180 words. After narration, the chosen consequences are applied.

### 5.2 Scene 7 — First Encounter With a Faction

#### Narrator framing

Generated dynamically based on `pre_onset_region` (Scene 3) — each region has a default first-faction encounter set. This scene has 4 choice options that are *region-aware* but *consistent in mechanical structure*.

> Months passed. The biggest thing left in your part of the world had a name. You met it, in the form of a person who spoke for it.
>
> [REGION-SPECIFIC FRAMING — 60–120 words: who the speaker is, what they want, where you met them. Examples: a Bourse factor offering courier work; a Throne recruiter testing your kinetic capacity; a CJL township councillor inviting you to an Accord meeting; an Iron Crown captain demanding your power's catalogued; a kin elder of Species I asking which side you'll stand on.]
>
> They want something from you. You want something back, or you don't.

The faction met is determined by region:

```
Region                       → primary faction encounter
NYC                          → Tower Lord OR Queens Commonage (player picks; 50/50 default)
Northern NJ                  → Iron Crown
Hudson Valley                → Catskill Throne (recruiter)
Central NJ                   → Central Jersey League
Philadelphia                 → Philadelphia Bourse
Lehigh Valley / Bucks        → Lehigh Principalities OR Quick-Blooded enclave
Baltimore / DC               → Fed Continuity OR Crabclaw (player picks)
Delmarva                     → Delmarva Harvest Lord
```

#### Choice set (4 options)

```
1. Accept their terms. Take the offered position.
   - faction.standing +1 (warm) with that faction
   - heat: -1 with that faction (enrolled, not suspect)
   - resources: faction-specific (Bourse: scrip & contract; Throne: training & barracks; CJL: stipend & lodging; etc.) — see lookup table
   - skills: faction-specific +1 (Bourse: negotiation; Throne: tactics; CJL: agriculture; Iron Crown: intimidation; Bourse alt: literacy; etc.)
   - history record: "joined [FACTION]"
   - consequences: locks one Goal "advance_within_FACTION" pressure 2 if not already at faction
   - faction's RIVALS: heat +1

2. Negotiate. Take a partial offer; keep some independence.
   - faction.standing +1 (cordial)
   - heat: 0 with that faction
   - resources: small payment, half-contract, conditional pass
   - skills: negotiation +1
   - history record: "negotiated terms with [FACTION]"

3. Refuse. Walk away.
   - faction.standing -1 (cold) but not hostile
   - heat: +1 with that faction
   - resources: --
   - skills: will +1 boost (held line)
   - attribute: will +1
   - history record: "refused [FACTION]"

4. Take the meeting and use it. Leverage it for something else.
   - faction.standing -1 (suspicious)
   - heat: +1 with that faction
   - resources: information 1, contacts_thin 1
   - skills: streetwise +1, negotiation +1
   - condition_tracks.social +1 (you played them)
   - history record: "took the meeting and worked the angles"
```

The faction-specific stipend, contract, and skill table is in the runtime data files (`data/sessionzero/faction_first_encounter.json`). Each faction lookup must include: `payment_resource`, `payment_quantity`, `skill_offered`, `inventory_offered` (1-3 items), `narration_hooks`.

### 5.3 Scene 8 — Critical Incident

This scene is mandatory and is the **third critical incident** counter — incidents 1 and 2 are folded into Scenes 6 and 7's outcome richness; Scene 8 is the explicit headline event.

#### Narrator framing

The runtime selects one of three critical-incident templates based on accumulated state. Selection rule: pick the highest-pressure unmet condition.

| Trigger condition | Incident |
|---|---|
| corruption >= 1 OR power_category_primary == eldritch_corruptive | A. The Hungry Thing |
| heat with any faction >= 2 OR Scene 7 choice 4 | B. The Reckoning |
| Default (no high-pressure trigger) | C. The Loss |

If multiple trigger, runtime breaks tie in order A > B > C.

#### Incident A — The Hungry Thing

> Something in your part of the world started to notice you. What it was, you could not have said. It came once, and you were ready for it the second time.

**Choice set (4 options):**
```
1. Faced it directly. Won at cost.
   - corruption +1
   - persistent harm: tier 2, "marked by the encounter", source "eldritch_proximity"
   - tier potentially +1 IF circumstance permits Depth breakthrough (insight check vs DC 8 against will die; if pass: tier +1, breakthrough record added with cost "carries the marked silence"); else tier unchanged
   - skill: will +1
   - heat: the-listening +1 OR pine-barrens-region awareness flagged

2. Hid. Stayed hidden. Survived without being seen.
   - skills: stealth +2, perception +1
   - condition_tracks.mental +1
   - status added: "shaken" (clears after 30 in-world days)
   - resources: information 1 about eldritch presence
   - no breakthrough

3. Bargained.
   - corruption +2
   - powers: gain a tier-1 eldritch_corruptive utility power as supplemental (added to powers[2])
   - relationships: generates an "entity contact" NPC, standing 0, current_state "patron_or_predator", status alive
   - history record: "made a bargain in the first year"

4. Lost someone to it.
   - relationships: one existing NPC's status set to "dead" or "transformed" (player picks which NPC); standing locked; Goal generated/strengthened pressure +2
   - skill: will +2
   - condition_tracks.mental +1
   - persistent harm: tier 2, "the night they were taken", clears only with specific narrative resolution
```

#### Incident B — The Reckoning

> The faction you crossed had a long memory. They came for you. You were ready, or you weren't.

**Choice set (4 options):**
```
1. Fought through it.
   - heat: +2 with the faction
   - persistent harm: tier 2, "wound from the reckoning", source "[FACTION]_combat"
   - tier potentially +1 IF will check vs DC 8 passes (Depth breakthrough through life-threat)
   - skill: melee +1, firearms +1
   - resources: salvaged from the encounter (small)
   - relationships: generates "one of theirs you killed" — entry only as NPC memory event

2. Ran. Lost everything you couldn't carry.
   - resources: --75% of all material resources (round down)
   - heat: 0 with the faction (gave up; not worth pursuing further)
   - skills: urban_movement +2, stealth +1
   - location bias: shifts starting region to adjacent (away from the faction's seat)
   - history record: "ran in the first year; lost everything"

3. Surrendered. Took the terms.
   - faction.standing -2 (antagonistic) becomes -1 (cold) with debt
   - resources: stripped (-50% of wealth resources)
   - inventory: marked or branded item (visible faction sign)
   - status: "marked" persistent until faction debt cleared
   - heat: -1 (debt acknowledged)
   - skills: --

4. Talked through it. Owed someone for it.
   - faction.standing 0
   - relationships: generates one NPC of the faction as "owed_to", standing +1, trust 1, current_state "owed"
   - resources: --
   - Goal generated: "settle_the_debt" pressure 3
```

#### Incident C — The Loss

> The first year took the people you loved at a rate no one alive had been ready for. Yours came in the spring, or the winter, or one ordinary Tuesday afternoon. You were there, or you weren't.

**Choice set (4 options):**
```
1. You were there. You couldn't stop it.
   - one existing NPC: status set to "dead" (player picks)
   - condition_tracks.mental +2
   - persistent harm: tier 2, "the day they died", source "loss"
   - skills: first_aid +1 (you tried)
   - Goal modified: pressure +2 to associated Goal
   - history record: "lost [NPC] in [SEASON]"

2. You weren't. You found out later.
   - one existing NPC: status set to "dead" (player picks)
   - condition_tracks.mental +1
   - skill: will +1
   - Goal modified: pressure +1
   - history record: "learned of [NPC]'s death after the fact"

3. You found them transformed.
   - one existing NPC: status set to "transformed" (player picks)
   - condition_tracks.mental +2, condition_tracks.social +1
   - relationships entry: standing kept, current_state "transformed_known_to_player"
   - corruption +1
   - Goal generated/modified: pressure +2

4. You held on to them. They lived.
   - all NPCs from Scenes 2 and 4 with status "alive_present" remain so
   - skill: first_aid +1, will +1
   - resources: dependents +1 in effect (you carried them through)
   - condition_tracks.physical +1 (the work cost you)
   - heat: catskill-throne +1 IF Hudson Valley region (Throne notices stable households)
   - tier potentially +1 IF biological_vital primary AND will check vs DC 9 (Sacrifice breakthrough — saving others at cost)
```

### 5.4 Scene 9 — Settling Into a Place

#### Narrator framing

> A year after the Onset, you were somewhere. Not where you had been. Not yet anywhere you would call home. But somewhere.
>
> Where did the year leave you?

#### Choice set (5 options)

Choices set `starting_location` (Section 7) and produce a small inventory + one final Goal.

```
1. In a town. Working.
   - location: regional capital appropriate to pre_onset_region (e.g., Yonkers; Trenton; Philadelphia; Edison; Allentown; DC; Easton)
   - inventory: working clothes, basic tool kit, 15 cu, lodging contract (1 month)
   - Goal: "build_a_life_here" pressure 2
   - resources: lodging_paid 1

2. On a road. Moving between places.
   - location: a major travel hub appropriate to region (e.g., Bourse caravan staging; Throne tributary post; CJL township market)
   - inventory: travel kit, 25 cu, weapon (region-appropriate), bedroll
   - Goal: "see_what's_left" pressure 1
   - skills: urban_movement +1, weather_read +1
   - resources: contacts_thin +1

3. In a faction's service. Quartered.
   - location: faction seat (uses Scene 7's faction if accepted; else nearest faction-aligned location)
   - inventory: faction kit (uniform, weapon, identification), 20 cu, barracks bed
   - Goal: "advance_within_faction" pressure 2
   - heat: -1 with faction
   - faction.standing +1

4. Hidden. Off the map.
   - location: a low-population zone appropriate to region (Pine Barrens edge; Catskill backcountry; Delmarva marsh; abandoned suburb)
   - inventory: cache (food 14 days, weapon, basic gear), 5 cu
   - Goal: "stay_invisible" pressure 3
   - skills: stealth +2, scavenging +1
   - heat: -2 across all factions (no one is looking)

5. Among your people.
   - eligibility: species != "human" OR Species I region OR cluster region
   - location: a kin or cluster concentration appropriate to species
   - inventory: kin gift, 10 cu, recognition token
   - Goal: "represent_or_protect_your_people" pressure 3
   - relationships: generates 1 kin elder NPC, standing +2, current_state "kin_elder"
   - faction.standing +2 with own community
```

After narration of choice 5, the runtime triggers post-creation validation (Section 9).

### 5.5 Themes coverage map

| Theme | Scene |
|---|---|
| First weeks survival | 6 |
| Faction encounters | 7 |
| Relationship preservation | 8 (esp. C), 9 |
| Skill development | 6, 7, 8 |
| Resource accumulation | 7, 9 |
| Heat generation | 7, 8 (esp. B) |
| Harm accumulation | 8 |
| Power use | 8 (breakthroughs) |
| Critical incident 1 | 6 (option 4 if taken) |
| Critical incident 2 | 7 (any path) |
| Critical incident 3 | 8 (mandatory) |

---

## SECTION 6 — METAHUMAN CHARACTER CREATION

### 6.1 Species selection procedure

Species selection runs as **Scene 1.5** — interleaved between Scene 1 (occupation) and Scene 2 (relationships). The runtime presents species options *after* the player has chosen occupation, because some species are filtered by region (which is set in Scene 3) and some by background. To preserve simple flow, the runtime asks once at Scene 1.5 for species commitment, then revalidates at Scene 3 against region eligibility (rejecting incompatible region+species combinations with a re-prompt).

**Narrator framing for Scene 1.5:**

> The Onset did not end the same way for everyone. About one in ten woke up not quite human anymore. They changed in patterns. Ten patterns. Most of those people are not in this part of the world.
>
> Are you one of them?

#### Choice set (11 options)

```
0. Human (baseline). Default.
1. Species A — Hollow-Boned        (mid-Atlantic minimal; NPC-likely diaspora)
2. Species B — Deep-Voiced         (mid-Atlantic minimal)
3. Species C — Silver-Hand         (cluster: Flushing/Sunset Park/Edison)
4. Species D — Pale-Eyed           (mid-Atlantic minimal; outer Brooklyn enclave)
5. Species E — Slow-Breath         (mid-Atlantic minimal; rural diaspora)
6. Species F — Broad-Shouldered    (mid-Atlantic minimal; retinue diaspora)
7. Species G — Sun-Worn            (cluster: central NJ + Lehigh)
8. Species H — Quick-Blooded       (cluster: North NJ + Bucks + outer Queens)
9. Species I — Wide-Sighted        (cluster: western Philadelphia + DC corridor)
10. Species J — Stone-Silent       (mid-Atlantic minimal; mediator diaspora)
```

Default is option 0. Setting bible mid-Atlantic share: ~19% metahuman. Session Zero presentation does not weight by population — players choose freely among the eleven, but choosing a non-cluster species in a region that does not match generates a "diaspora individual" framing rather than a "kin-network member" framing.

### 6.2 Per-species creation modifications

Each species option applies the following modifications (applied **on top of** Scene 1 occupation deltas, not in place of them):

```
SPECIES A — Hollow-Boned
- agility +2 (caps current die at d10), perception +1
- strength -2 (subtract from base; floor d4), might unaffected
- skill: weather_read +1
- baseline ability: micro-precognition (auto-applied perceptual_mental tier-1 power "danger sense")
- condition_tracks: physical max 5 (unchanged) but starting persistent tag "fragile bones" — physical harm tier 2 from blunt force escalates to tier 3 if untreated within 1 in-world week
- region availability: any (diaspora individual)
- narration tag: "lean and quick, lighter than they should be"

SPECIES B — Deep-Voiced
- will +1, insight +1
- baseline ability: auto-applied auratic tier-1 "carrying voice" (low-intensity persuasion / long-range audibility)
- condition_tracks unchanged
- region availability: any (diaspora individual; Queens / Jersey City / Philadelphia suburb / DC)
- narration tag: "broader through the chest, voice that fills the room"

SPECIES C — Silver-Hand
- insight +1, agility +1
- baseline ability: auto-applied matter_energy tier-1 "shaping touch" (matter-reshaping by contact, non-combat scope)
- starting_skills: craft +2, basic_repair +1
- inventory: "silvered palm sheath" (cosmetic; 1 cu value)
- region availability: NYC (Flushing/Sunset Park) or Northern NJ (Edison) cluster preferred; diaspora elsewhere
- narration tag: "the silver shows at the wrists when the sleeves move"

SPECIES D — Pale-Eyed
- perception +2
- baseline ability: auto-applied perceptual_mental tier-1 "low-light sight" + minor intent-read
- region availability: any (diaspora; outer Brooklyn enclave concentration)
- narration tag: "eyes that catch light wrong"

SPECIES E — Slow-Breath
- will +1, condition_tracks.physical max 6 (one extra segment)
- baseline ability: reduced caloric needs (resource: rations consumed at 60% rate); breath-hold; toxin tolerance (resistance to "burning" status, +2 to resist mechanically)
- region availability: any (diaspora)
- narration tag: "still in a way other people aren't"

SPECIES F — Broad-Shouldered
- strength +2, condition_tracks.physical max 6
- height/weight visibly above baseline
- baseline ability: physical durability (one harm tier 1 absorbed per scene without effect)
- region availability: any (diaspora; retinue concentration)
- narration tag: "large enough to be the largest in any room"

SPECIES G — Sun-Worn
- insight +1, will +1
- baseline ability: auto-applied biological_vital tier-1 "plant sense" (agricultural diagnosis at touch)
- starting_skills: agriculture +2
- visibly weathered earlier than baseline (greying by mid-20s)
- region availability: Central NJ or Lehigh cluster preferred; diaspora elsewhere
- narration tag: "weathered face, the look of someone who's worked in sun"

SPECIES H — Quick-Blooded
- agility +1, condition_tracks.physical regenerates 1 segment per scene transition (not per round)
- baseline ability: rapid healing (tier 1 harm clears in one scene; tier 2 in 3 scenes; tier 3 unchanged)
- starting_skills: urban_movement +1
- region availability: North NJ (Paterson/Passaic) or Bucks County or outer Queens cluster preferred; diaspora elsewhere
- narration tag: "smaller than baseline, faster than baseline, warmer to the touch"

SPECIES I — Wide-Sighted
- perception +2
- baseline ability: enhanced vision (low-light + near-UV); long-range species-recognition
- starting_skills: languages +1 (Spanish baseline)
- region availability: Philadelphia or DC corridor cluster preferred; diaspora elsewhere
- relationships: if cluster region, generates 1 additional kin NPC at standing +1, current_state "kin_recognized"
- narration tag: "the eyes — large, often colored in ways baseline eyes are not"

SPECIES J — Stone-Silent
- strength +1, will +2, condition_tracks.physical max 6
- height notably above baseline
- baseline ability: auto-applied auratic tier-1 "steadiness zone" (3-5m radius reduces panic in nearby NPCs)
- region availability: any (diaspora; mediator concentration)
- narration tag: "tall, still, the tension easing around them"
```

Mechanical note: species **baseline abilities** are added to `powers` as power_id entries (e.g., `power_species_a_microprecog`) and recorded as `species_baseline: true` in the power's metadata. They count for narrative purposes but do not consume the Section 4 power-selection slots. Player still rolls/selects manifestation per Section 4 in addition to species baseline.

### 6.3 Species-specific scenes

Two species-specific scenelets insert when applicable. Both run between Scene 7 and Scene 8.

**Cluster scenelet (triggers if species in {C, G, H, I} AND pre_onset_region is cluster region):**

> Your community had its own meetings, its own quarrels, its own rules for what its people did when the world ended. You went to the meetings, or you didn't.

Choice set (3 options):
```
1. Went to the meetings. Took your place.
   - relationships: +1 cluster_elder NPC standing +1
   - faction.standing +1 with cluster faction (twelve-hands / lehigh-principalities / quick-blooded-network / species-i-diaspora)
   - Goal: "represent_your_kin" pressure 2

2. Stayed apart. Did your own work.
   - faction.standing -1 with cluster faction
   - skills: relevant cluster craft +1 (C: craft / G: agriculture / H: stealth / I: streetwise)
   - resources: independent_reputation 1

3. Worked within the cluster but kept your own ledger.
   - faction.standing 0 with cluster faction
   - skills: negotiation +1
   - resources: cluster_contacts 1
```

**Diaspora scenelet (triggers if species != human AND not in cluster region):**

> There were a few of you, scattered. You found each other or you didn't. The community in your part of the world was thin or it was not there at all.

Choice set (3 options):
```
1. Found the others. Built a small thing together.
   - relationships: +1 diaspora_companion NPC standing +1
   - resources: small_community_tie 1

2. Did not look for them. Went on alone.
   - skill: will +1
   - tag: "diaspora_isolated"

3. Found them and walked away from them.
   - relationships: +1 diaspora_companion NPC standing -1, current_state "estranged_kin"
   - history record: "left the diaspora community in [REGION]"
```

### 6.4 Mechanical implications summary

| Sheet field | Species impact mechanism |
|---|---|
| `attributes` | per-species deltas, may exceed baseline d10 cap |
| `condition_tracks.physical` | per-species max change (E, F, J get max 6) |
| `powers` | species baseline ability added |
| `relationships` | cluster scenelet may add kin NPC |
| `skills` | per-species starting_skill additions |
| `species` | set to species id |
| `inventory` | species-specific items (C only by default) |
| Faction `heat` | cluster-faction scenelet outcome |
| Goal | cluster scenelet may add kin Goal |

---

## SECTION 7 — GAME START SETUP

### 7.1 Character sheet construction procedure

After Scene 9 closes, the runtime constructs the final `Character Sheet` per `interface-spec.md` schema by mapping session zero choices to fields. Procedure:

```
1.  schema_version = "1.0"
2.  id = generate_uuid()
3.  name = session_zero_choices.name
4.  species = session_zero_choices.species (default "human")
5.  age_at_onset = session_zero_choices.age_at_onset
6.  current_age = age_at_onset + 1
7.  attributes = base_d6_all_six
        + occupation.attribute_deltas
        + species.attribute_deltas
        + scene_6_deltas + scene_7_deltas + scene_8_deltas + scene_9_deltas
        clamp each to {d4, d6, d8, d10, d12} (rounded down to nearest valid die size)
8.  condition_tracks = { physical: 0, mental: 0, social: 0 }
        with maxes set by species (default 5)
        plus any track increments accumulated in Year One scenes (scene 6/7/8 deltas)
9.  harm = list of harm objects accumulated through scenes
10. powers = anchor + secondary (Section 4) + species baseline + any incident additions
11. power_category_primary = manifestation result
12. power_category_secondary = manifestation result or null
13. tier = manifestation tier + any incident breakthrough modifiers
14. tier_ceiling = tier + 2 (or +3 if narrow-specialist declined secondary)
15. breakthroughs = any records added in Scene 8
16. heat = aggregate of all heat deltas, faction_id → integer (clamp -3..+5)
17. corruption = sum of all corruption deltas (clamp 0..6)
18. relationships = aggregate of all relationship entries
        each with standing, history (init with session zero events), current_state, trust = 1 default
19. inventory = aggregate of all inventory grants (Section 5 + 6)
20. location = derived from Scene 9 choice → location_id lookup table
21. history = aggregate history records from Scenes 6–9 (3–6 entries typical)
22. statuses = any persistent statuses applied
23. skills = aggregate of all skill grants, capped at 4 from session zero alone (further growth requires play)
24. resources = aggregate of resource grants
25. goals = aggregate of all goals generated; if more than 4 exist, sort by pressure desc and keep top 4 (others moved to "deferred" key in session_zero_choices)
26. session_zero_choices = full record of every selection
```

### 7.2 Starting location determination

Lookup table `data/sessionzero/starting_locations.json` maps `(pre_onset_region, scene_9_choice)` to a `location_id` from `locations.yaml`. Example mappings (full table written by content authoring):

```
(NYC, in_a_town)            → location-yonkers-market-quarter
(NYC, on_a_road)            → location-george-washington-bridge-camp
(NYC, faction_service)      → location-mount-tremper OR location-port-newark per Scene 7 faction
(NYC, hidden)               → location-staten-marshes
(NYC, among_your_people)    → location-flushing-cluster-square (if species C)
(Hudson Valley, in_a_town)  → location-yonkers-healing-hall-quarter
(Hudson Valley, faction)    → location-mount-tremper or location-peekskill-bear-house
(Central NJ, in_a_town)     → location-new-brunswick-market
(Central NJ, faction)       → location-rutgers-princeton-corridor
(Philadelphia, in_a_town)   → location-philadelphia-bourse-quarter
(Philadelphia, faction)     → location-bourse-trading-floor
(Philadelphia, among_your_people) → location-pg-county-corridor (if species I)
(Lehigh, in_a_town)         → location-allentown
(DC, in_a_town)             → location-dc-mall-perimeter
(DC, faction)               → location-pentagon-quartered
(Delmarva, in_a_town)       → location-easton
(Delmarva, on_a_road)       → location-eastern-shore-trade-route
... [NEEDS AUTHORSHIP: full table requires every region × every Scene 9 choice]
```

### 7.3 Starting relationship loading from NPC registry

Procedure:

1. For each generated NPC in session zero, write a file `npcs/{generated_id}.json` per `interface-spec.md` NPC schema.
2. Each NPC's `relationships` includes a back-reference to the player character: `{player_id: {standing: <player's standing toward them>, trust: <NPC's trust toward player>, history: [<initial event>], current_state: <as set>}}`.
3. Each NPC's `location` set to `player.location` for present NPCs; `"unknown"` for missing; `"deceased"` for dead; `"transformed"` for transformed.
4. Each NPC's `memory` initialized with one entry summarizing their relationship origin (Scene 2 or Scene 4 backstory).
5. Each NPC's `what_they_want_from_the_player` derived from current_state (e.g., `"spouse, alive_separated"` → `"to be reunited"`; `"enemy"` → `"to settle the account"`).

### 7.4 Starting faction standings from Year 1 choices

For each faction id with a non-default heat or standing from session zero:

1. Locate `factions/{faction_id}.json`.
2. Set `faction.external_relationships[player_id] = { disposition: <derived from heat>, history: [<session zero event>], active_agreements: [], active_grievances: [<if heat > 0>] }`.
3. Player sheet's `heat[faction_id]` = the integer accumulated.
4. Faction-relationship standing scale (player's view of the faction, separate from heat):
   - heat <= -1, scene_7_choice in {accept, negotiate}: `standing 1` (cordial)
   - heat 0, scene_7 in {refused, leveraged}: `standing 0` (neutral)
   - heat >= +2: `standing -1` (cold), or -2 if Scene 8 Incident B with that faction
   - faction.standing_with_player = mirror of player's standing unless specifically modified

`Character Sheet` does not natively store player→faction standing as a field; it lives in faction-side `external_relationships`. The player's relationship view is read at runtime. (`Character Sheet.heat` is the only player-side faction tracking field.) [NEEDS RESOLUTION: progression.md Section 5 may need to add a `Character Sheet.faction_standing` mirror; flagged.]

### 7.5 Starting resource inventory

`Character Sheet.resources` and `Character Sheet.inventory` are populated as the union of all grants. Default starting inventory baseline (every character regardless of choices):

```
- clothing (1, no mechanical effect)
- knife or equivalent edge tool (1, mechanical: melee tier-1 weapon)
- waterskin or canteen (1, no mechanical effect)
- 5 cu (Bourse copper) baseline carried
```

All grants from Scene 7 and Scene 9 add to this baseline. `resources` is a separate dictionary for non-physical accumulables: `{ contacts_thin: int, scrip_pre_onset: int, lodging_paid: int, dependents: int, ...}`.

### 7.6 Starting condition state including persistent harm and active statuses

Apply at construction:

- Persistent harm from Scene 8: any `tier 2` harm record is added to `harm[]` with `persistent: true`.
- Persistent statuses: any status with non-temporary `duration` (e.g., "marked", "shaken") added to `statuses[]`.
- Condition tracks: integer values from accumulated deltas. Tracks above 3 trigger a starting-state warning (player begins under significant pressure); above 4 require validation review.

---

## SECTION 8 — VARIATION AND REPLAYABILITY

### 8.1 Variation procedure for repeated plays

The runtime supports two replay modes:

**A. Fresh seed.** New random seed; same or different choice path. Different draws for tier and power options yield different builds even from identical choice sequence.

**B. Locked seed.** Player provides a previous run's seed. With identical choices, identical result; with different choices and same seed, divergence point identifiable.

The `session_zero_choices` object includes `seed`, `mode` (`"fresh"` or `"locked"`), and a `divergence_log` for locked-seed runs that took different paths than the previous one (logged for the player's interest).

### 8.2 Random seed handling

- Seed generated as `uint64` from `os.urandom(8)` at character creation start.
- All random draws inside session zero use a `random.Random(seed)` instance, advanced deterministically.
- Order of draws is fixed: name pool (if defaulted), NPC generation (Scene 2), NPC manifestation rolls, Scene 5 tier roll, Scene 5 secondary-presence roll, Scene 5 power-option selection (anchor and secondary), Critical Incident DC checks, any scenelet rolls.
- Deterministic ordering is enforced by the runtime; engines must not introduce additional draws during Session Zero outside this sequence.

### 8.3 Optional secret choices for non-standard playthroughs

Three optional flags accessible only via explicit player input (text command at Scene 0, e.g., "let me see the optional choices") — not menu-presented:

```
1. "I did not manifest." (Baseline-human path; ~5% of population)
   - skips Scene 5 manifestation
   - power_category_primary = null, power_category_secondary = null, tier = 0, powers = []
   - attributes: +1 to two attributes player picks (compensation)
   - heat: -2 across powered factions (overlooked)
   - flag: unmanifested = true
   - viable but markedly harder; warned to player in framing

2. "I manifested into something that scares me."
   - forces eldritch_corruptive primary at Scene 5 (overrides circumstance)
   - corruption +1 starting
   - tier roll uses crisis modifier even if circumstance was passive
   - flag: corrupt_start = true

3. "I was older than I should have been on Onset day."
   - allows age_at_onset 66–80
   - attribute caps at d8 baseline (one d10 maximum)
   - flag: elder_start = true
   - life expectancy substantially reduced (Section 7 of progression.md)
```

### 8.4 Variation envelope

Across all combinations, the design target is **noticeably different play for the first decade** of in-world time:

- Different starting region → different first-encountered factions, different threat profile, different travel options.
- Different occupation → different baseline skill profile, different default heat with at least one faction.
- Different relationships → different Goals, different NPC presences, different return-to-someone hooks.
- Different manifestation category → different tactical verbs in combat, different corruption profile, different societal signaling.
- Different Scene 7 choice → different faction relationships, different starting inventory.
- Different Scene 8 incident → different breakthrough record (or none), different persistent harm, different ledger of debts and losses.
- Different Scene 9 location → different geography of the first year of play.

Sufficient combinatorial range (12 occupations × 8 regions × 8 circumstances × 11 species × 4 Scene 7 choices × 3 critical incidents × 4 incident outcomes × 5 Scene 9 choices ≈ 4 million distinct paths) ensures replay-meaningful variation; orthogonality of choice axes ensures variation is felt, not just numeric.

---

## SECTION 9 — POST-CREATION VALIDATION

### 9.1 Schema validation

After construction (Section 7.1), run `validate_character_sheet(sheet)` which checks every field against the schema in `interface-spec.md`:

```
- All required fields present (id, schema_version, name, species, attributes, ...)
- All values within allowed ranges (attribute die sizes ∈ {4,6,8,10,12}; condition_tracks 0..max; harm tier 1..3; tier 1..10; corruption 0..6; standing -3..+3)
- All cross-references resolve (each power_id in powers exists in registry; each faction_id in heat exists; each npc_id in relationships exists as a saved file)
- No duplicate ids
- schema_version matches current
```

Failure halts creation and presents a structured error (which field, expected vs. actual). No silent fallback.

### 9.2 Internal consistency checks

Beyond schema:

```
- power_category_primary appears in powers[].category for at least one power
- if power_category_secondary != null, appears in powers[].category for at least one power
- tier_ceiling >= tier
- breakthroughs[].to_tier matches the tier that resulted (chain consistency)
- relationship.history references at least one event (no orphaned relationships)
- goals length <= 4 active
- harm[] entries with persistent: true for tier >= 2; tier 1 entries flagged for cleanup
- if species != "human", species_baseline power present in powers[]
- if unmanifested flag, powers == [] and tier == 0 and categories == null
- if corrupt_start, corruption >= 1 and primary == eldritch_corruptive
- inventory contains baseline items (knife, clothing, waterskin)
- starting location_id resolves to an existing location file
```

Inconsistency halts creation with a structured error.

### 9.3 Recovery if validation fails

Three failure modes and responses:

```
A. Missing data (a Scene's deltas were not recorded).
   Recovery: re-run the most recent affected Scene from saved state.

B. Out-of-range value (e.g., attribute computation overshot d12).
   Recovery: clamp to nearest legal value, log a warning to session_log,
   note adjustment to player ("your attribute was clamped to the legal maximum").

C. Cross-reference broken (e.g., npc_id listed in relationships but file not written).
   Recovery: regenerate missing file from session_zero_choices.relationships record;
   if regeneration fails, abort creation and roll back to last save point.
```

The runtime persists `session_zero_choices` complete enough that a full re-run is always possible. Validation never silently "fixes" data; every adjustment is logged and surfaced.

### 9.4 Validation summary surfaced to player

After successful validation, present a one-screen summary:

```
Character: [NAME], age [CURRENT_AGE]
Species: [SPECIES]
Power: [PRIMARY_CATEGORY], tier [TIER] — anchor: [POWER NAME] / secondary: [POWER NAME or "none"]
Background: [OCCUPATION TAG]
Started in: [REGION]; living in: [LOCATION]
With them: [LIST OF NPCs WITH STATUS]
Carrying: [GOAL DESCRIPTIONS, sorted by pressure]
Marked by: [PERSISTENT HARM / CORRUPTION / STATUS — if any]
Begin?
```

Player confirms; runtime sets `World State.active_scene = null` and `World State.current_time = "T+1y"`; sim engine takes over.

---

## design_decisions

1. **Ten scenes** chosen over a smaller count because the design brief calls for character creation as play, not a form. Each scene is short (2–4 minutes) so total stays inside the 22–35 minute target.
2. **Auratic** is the seventh power category id, per `powers.md`. The interface-spec placeholder `temporal_spatial` for the seventh slot is overridden to `auratic`. All references throughout this spec use seven category ids: physical_kinetic, perceptual_mental, matter_energy, biological_vital, auratic, temporal_spatial, eldritch_corruptive.
3. **Attribute meanings** (`might` vs. `strength`) locked here in 3.0 because the interface schema names them but does not define them. `might` = power-output die, used by combat and progression specs.
4. **Session Zero tier cap T4** (T5 only via Critical Incident breakthrough). This preserves the bible's statement that Preston's three rapid breakthroughs are exceptional; ordinary characters do not start at high tier.
5. **Tier ceiling = tier + 2** at start. Practice within tier reaches ceiling over years; further growth requires breakthrough. Calibrated to the bible's "10–20 years of practice within a tier."
6. **Substance-altered states bias to eldritch_corruptive** in 4.2.2 (entry 29). Bible does not address this; provisional decision to give the eldritch category a non-trivial entry path other than Scene 8. Flagged as authorship.
7. **Species selection at Scene 1.5** (between occupation and relationships) so species-typical adjustments apply before relationship NPCs are generated (NPC ethnic generation needs region; species region biases region defaults).
8. **NPC generation deterministic from seed** — every NPC field can be reconstructed from `(seed, generation_index)`. Necessary for save reliability and replay.
9. **Character Sheet does not natively mirror faction standing**; player faction view is read from faction files at runtime. Flagged in 7.4; progression.md may add a mirror field if a clean lookup proves friction.
10. **Critical incident gating** is the only way to hit T5 in Session Zero, and only one of three incident types (A or B) routes to it. This keeps high-tier starts rare and earned.
11. **Scene 9 choice 5 (Among your people)** is the only choice gated by species; all other Scene 9 choices remain open regardless. This keeps the metahuman-character path mechanically distinct without reducing baseline-human choice space.
12. **Inventory baseline** (knife, clothing, waterskin, 5 cu) given to every character regardless of choices, ensuring no character begins with literally nothing. Aligns with the bible's "every peasant is a small wizard" — even a stripped character has hands and a kit.
13. **Validation is hard-fail**, not silent-fix. The interface spec's "silent fallback is forbidden" rule is honored.
14. **Optional secret choices** are text-command-gated (not menu) so they do not pollute the default Session Zero presentation, but exist for replayers who want non-standard starts.

## [NEEDS RESOLUTION]

- **[NEEDS RESOLUTION: starting_locations table]** Section 7.2 sketches the lookup but every (region × Scene 9 choice) pair must be authored against the location registry. ~40 entries.
- **[NEEDS RESOLUTION: faction_first_encounter table]** Section 5.2 sketches the lookup; full data file requires `payment_resource`, `payment_quantity`, `skill_offered`, `inventory_offered`, `narration_hooks` per faction option. ~10 factions × 4 fields each.
- **[NEEDS RESOLUTION: power registry coverage]** Sections 4.2.4 and 6.2 reference `data/powers/` and `power_id`s like `power_species_a_microprecog`; the full power registry must exist for selection to work. Not in scope of this spec; flagged as content-authoring dependency.
- **[NEEDS RESOLUTION: character sheet faction-standing mirror]** Section 7.4 leaves the player's view of factions to runtime lookup of faction files. If lookup proves expensive in the narrator-context budget, progression.md may add a mirror field; this affects both specs.
- **[NEEDS AUTHORSHIP: substance-altered states / eldritch correlation]** Section 4.2.2 entry 29 is provisional; bible does not explicitly correlate intoxication with eldritch onset.
- **[NEEDS AUTHORSHIP: skill catalog]** This document references skill_ids (firearms, melee, first_aid, surgery, agriculture, craft, basic_repair, scavenging, streetwise, urban_movement, stealth, intimidation, negotiation, command, tactics, bureaucracy, literacy, regional_geography, history, languages, instruction, weather_read, animal_handling, pharmacology, field_medicine, perception_check). The full 30+ skill catalog is in progression.md Section 3.
- **[NEEDS AUTHORSHIP: NPC name pool]** Section 2.2 references a "name pool" weighted by region; content authoring required.
- **[NEEDS AUTHORSHIP: scene 8 critical incident location/NPC parameterization]** Each incident template needs region-flavored parameterization in narration.
