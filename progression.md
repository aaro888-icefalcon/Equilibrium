# progression.md

Specification for character development across the in-world decades of an Emergence campaign. Covers tactical (combat capability), life (skills, relationships, resources), aging, family, corruption, and narrative arcs. All schemas conform to `interface-spec.md`. All references to combat resolution defer to `combat-spec.md`.

---

## SECTION 1 — TACTICAL PROGRESSION

### 1.1 Power use counters

Each power on `Character Sheet.powers` carries a runtime-tracked `use_count` integer, persisted as a sibling map `Character Sheet.power_use_counts: {power_id: integer}`.

A use is logged when:

- Combat: any `Action` with `verb == "Power"` or `verb == "Finisher"` referencing that `power_id` (combat engine increments after action resolves, regardless of success).
- Sim: an activity outcome that explicitly invokes the power (sim engine increments per the activity's `power_invocations` field).
- Passive uses (e.g., always-on perceptual sweep, species baselines used in narration) do **not** count toward strengthening — only deliberate, costed uses.

`power_use_counts[power_id]` is monotonic; no decay.

### 1.2 Strengthening thresholds

A power gains a **strengthening mark** at fixed use-count thresholds. Each mark is a mechanical change (cost reduction, range/duration extension, or new minor effect option). Marks are per-power and accumulate independently. Marks 1–5 within tier; mark 5 is the tier ceiling for that power.

| Mark | Use count | Mechanical effect |
|---|---|---|
| 1 | 25 | -1 condition cost on the cheaper track this power taxes |
| 2 | 75 | one new option appears in the power's effect parameters (per-power; defined in registry) |
| 3 | 200 | -1 corruption cost on uses that would otherwise inflict corruption (floor 0) |
| 4 | 500 | range / duration / area extended one step (per power-type table) |
| 5 | 1,200 | power's effective tier rises by 1 for purposes of opposed checks (does not raise character tier) |

Use rates calibrate to the bible's "10–20 years of practice within a tier." A retinue user logging ~150 power uses per year reaches mark 4 in ~3 years and mark 5 in ~8 years; a passive user reaches mark 1 in years.

### 1.3 Tier ceiling effects

Character tier is global; strengthening is per-power. The character's `tier` and `tier_ceiling` (`interface-spec.md`) bound advancement:

- A character with `tier < tier_ceiling` may add power marks freely as above.
- At `tier == tier_ceiling`, mark 5 on **any** power becomes hard to reach: the use-count threshold for that power's mark 5 is raised to 2,400 (doubled) to represent diminishing returns within strata.
- Tier ceiling lifts only via breakthrough (Section 2) or, exceptionally, via mentorship (Section 2.7 increases ceiling without raising tier).
- `tier == 10` is the maximum; no tier can exceed 10. Tier 10 requires multiple breakthroughs. No mid-Atlantic individual has reached T10.

### 1.4 Cross-power growth in category

When a character logs use on multiple powers in the same `power_category`, a category-wide bonus accumulates separately as `Character Sheet.category_use_counts: {category_id: integer}` (sum of all in-category power uses).

| Category bonus mark | Sum threshold | Effect |
|---|---|---|
| 1 | 100 | one new tier-1 power in the same category becomes available to learn (player picks from registry; learning ritual = sim activity, 7 in-world days, no breakthrough required) |
| 2 | 400 | as above, but a tier-2 power if `tier >= 2`; otherwise a second tier-1 |
| 3 | 1,000 | the character may **integrate** two of their existing in-category powers into a single combined verb (combat engine treats as one Power action with both effect tags); see combat-spec |
| 4 | 2,500 | tier_ceiling +1 (one-time per category; capped so that cumulative cross-category ceiling-raises never exceed +3 from this source) |

The mark-1 unlock is the primary pathway for "breadth within domain" — a Physical/kinetic specialist who logs many uses can develop a second kinetic verb without a breakthrough.

### 1.5 Storage

Power use counts and category use counts are persisted in `player/character.json` alongside core fields. Strengthening marks themselves are persisted as `Character Sheet.power_marks: {power_id: integer}` (0–5 per power). Recomputation from use counts is an idempotent operation; the runtime may recompute on load to detect drift.

---

## SECTION 2 — BREAKTHROUGH MECHANICS

A **breakthrough** raises `tier` by exactly 1 and writes a `breakthrough` record to `Character Sheet.breakthroughs[]`. Each breakthrough requires a triggering **condition**, a **resolution** procedure, and applies a **mark** as cost.

### 2.1 Breakthrough conditions

Eight defined conditions. Each has a trigger (when it can fire), resolution procedure (how it resolves), and breakthrough type (Depth / Breadth / Integration per `powers.md`).

```
1. NEAR-DEATH BREAKTHROUGH
   Trigger: combat-spec resolution would result in player death (fatal harm tier 3 added,
            condition_tracks.physical full, no rescue) AND tier < tier_ceiling.
   Resolution: roll 1d10 + (tier) vs DC 12 + (current tier). On pass, breakthrough fires
            in lieu of death. Player survives with new tier, harm tier 2 persistent
            ("the wound that should have killed me"), and one breakthrough mark.
   Type: Depth (default), or Integration if character has 3+ powers active in the encounter.

2. MENTORSHIP BREAKTHROUGH
   Trigger: ≥ 90 in-world days of sustained training under a mentor of tier >= player.tier + 2,
            within same primary category, with `Mentorship` activity logged.
   Resolution: at end of training period, will check vs DC 7 + (player.tier - 1).
            On pass, breakthrough fires with type Integration.
   Cooldown: a mentor may catalyze only one breakthrough per student per lifetime.

3. ELDRITCH EXPOSURE BREAKTHROUGH
   Trigger: sustained presence in an eldritch-charged location (≥ 3 cumulative in-world
            days within a `location.type == "charged_zone"` of eldritch character)
            OR direct contact-bargain with an anomalous eldritch entity.
   Resolution: breakthrough fires automatically (no roll). Type: Breadth (new domain
            appears, biased toward eldritch_corruptive); if player rejects new domain,
            type Depth in primary category.
   Cost: corruption +1 unconditional, +1 additional if Breadth.

4. SUBSTANCE BREAKTHROUGH
   Trigger: ingestion of a specific catalyst substance (registered substances: pre-Onset
            pharmaceutical-grade psychedelics; biokinetic-cultivated visionary brews from
            the Pine Barrens periphery; certain Catskill mushrooms with eldritch-adjacent
            character) AND will check vs DC 10 to retain coherent intent through the
            episode.
   Resolution: on pass, tier +1 type Breadth or Integration (player picks).
            On fail, no breakthrough; corruption +1; harm tier 2 ("the time I went
            somewhere and came back wrong").
   Cooldown: any single substance may catalyze only once per lifetime.

5. RITUAL BREAKTHROUGH
   Trigger: completion of a multi-participant ritual (≥ 3 manifesters; ≥ 1 of whom
            is tier >= player.tier + 1; ≥ 1 in-world day duration; specific rite
            documented in `data/rituals/`).
   Resolution: insight check vs DC 9 + (player.tier - 1). On pass, breakthrough
            fires; type matches the ritual's specified output (registered rituals
            specify Depth / Breadth / Integration).
   Cost: typically a relationship debt to the participants (each participant gains
            standing +1 with player; player owes a service per the ritual contract).

6. TRAUMATIC LOSS BREAKTHROUGH
   Trigger: death or transformation of an NPC at `relationships[npc_id].standing >= 2`
            within the past 30 in-world days, AND will check vs DC 8 + (current tier).
   Resolution: on pass, breakthrough fires type Depth. On fail, condition_tracks.mental
            +1, no breakthrough.
   Once-per-loss: each NPC loss may trigger only once.

7. SUSTAINED CRISIS BREAKTHROUGH
   Trigger: condition_tracks at any track ≥ 3 sustained for ≥ 14 in-world days while
            the character actively engages threats (not in shelter / recovery).
   Resolution: at end of sustained period, will + might check vs DC 11. On pass,
            breakthrough type Depth; on fail, condition_tracks at affected track
            stays elevated and harm tier 2 added.
   Cost: ageing acceleration (+1 effective age category — see Section 7).

8. SACRIFICE BREAKTHROUGH
   Trigger: voluntary, irrevocable surrender of a specific resource of weight —
            a relationship (standing >= 2) cut to standing -3, a holding burned,
            a power deliberately suppressed (mark resets to 0), a body part lost.
   Resolution: breakthrough fires automatically on completed sacrifice. Type Depth
            or Breadth (player picks at moment of sacrifice).
   Frequency: up to once per 5 in-world years per character.
```

### 2.2 Breakthrough resolution procedure

When a trigger fires, the runtime emits a `Narrator Payload` with `scene_type: "scene_framing"` and a special `state_snapshot.breakthrough_pending` field. After the narration beat, the runtime:

```
1. Apply tier += 1 (capped at 10).
2. Append to breakthroughs[]:
   {
     date: current_time,
     from_tier: prior tier,
     to_tier: new tier,
     cost: <selected mark from 2.3>,
     trigger: <condition id>
   }
3. Update tier_ceiling: max(current ceiling, new tier).
4. Apply selected mark (Section 2.3) — modify attributes, statuses, or relationships
   per mark definition.
5. Apply type-specific bonus:
   - Depth: one of the character's existing powers in the primary category gains
     +1 mark immediately (free strengthening).
   - Breadth: one new power becomes available in a category not previously held,
     player picks tier-1 or tier-2 power from registry filtered by tier <= new tier.
     Update power_category_secondary if was null.
   - Integration: one new combined-verb becomes available (combat-spec mechanic);
     no new power_id added but a `Character Sheet.integrations[]` entry is.
6. Add a history record (category "breakthrough").
7. Log a Recovery Period (Section 2.4).
```

### 2.3 Breakthrough marks catalog (24 marks)

Marks are drawn from a category-aware pool when breakthrough fires. The runtime presents the player with **3 mark options** drawn from the appropriate sub-pool; the player picks one. Marks are permanent.

**Physical marks (apply on Physical breakthroughs or any breakthrough where category dominant is physical_kinetic):**

```
P1. Densification — strength +1 die size; agility -1 die size; visible musculature change.
P2. Weight gain — strength unchanged; condition_tracks.physical max +1; flexibility lost (skills requiring agility +1 difficulty).
P3. Hand callus — melee unarmed counts as tier-1 weapon permanently; permanent visible deformation.
P4. Eye scarring — perception +1 die; cosmetic disfigurement; social interactions with strangers carry +1 difficulty until trust established.
```

**Perceptual / Mental marks:**

```
M1. Thought-bleed — perception +1; will -1; others' thoughts intermittently audible (status: "marked" applied recurrently in crowds).
M2. Sleep loss — perception +1; condition_tracks.mental max -1; the character requires less sleep but cannot rest deeply.
M3. False memory — insight +1; player periodically presented with one false memory per in-world year, indistinguishable from real until contradicted by external fact.
M4. Affect flatness — will +1; social-track interactions with NPCs at standing >= 2 reduce trust faster (Section 4).
```

**Matter / Energy marks:**

```
E1. Mineralization — strength +1; condition_tracks.physical max +1; corruption +1 (Kostas-trajectory); skin partly stone-flecked.
E2. Heat tolerance — resistance to "burning" status increased one step; cold sensitivity (status "shaken" applied in below-freezing conditions).
E3. Electromagnetic sensitivity — perception +1 in non-storm conditions; "shaken" or "stunned" status risk in proximity to functioning electrical sources (Peekskill area).
E4. Discoloration — visible silver, copper, or rust-tone skin discoloration, growing with use; commerce difficulty +1 in strange territory.
```

**Biological / Vital marks:**

```
B1. Plant resonance — agriculture skill +2; biokinetic abilities cost -1; presence wilts or flourishes plants in radius (visible mark, social signaling).
B2. Self-drain — biological_vital powers cost -1 normally but +2 condition cost when healing others; visible aging acceleration cosmetic.
B3. Sense overload — perception +1 die; condition_tracks.mental max -1; in any crowded location (>20 NPCs) status "shaken" applied at scene start.
B4. Body-shift — strength +1 OR agility +1 (player picks at mark time); subtle physiological reorganization; must re-tailor clothing.
```

**Auratic marks:**

```
A1. Field fixation — auratic powers' radius +50%; player's own personality drifts toward field's affect (trust-field user becomes incapable of natural skepticism; calm-field user incapable of urgency); will checks at +1 difficulty against the affect's opposite.
A2. Lonely zone — auratic effect strengthens; NPC trust ceiling reduces by 1 in any relationship started after this mark.
A3. Aural mark — audible humming or subsonic at edge of perception; stealth -2; intimidation +1.
A4. Permanent presence — even when leaving a location, residual effect persists for 1 in-world week (Section 8 of `powers.md` re: "auratic-charged zones").
```

**Temporal / Spatial marks:**

```
T1. Time-slip — temporal powers cost -1; player intermittently misplaces a few seconds (small narrative beats, no mechanical cost beyond confusion).
T2. Folded inventory — gain a "folded space" inventory slot of 1 cubic foot capacity, accessible only by character.
T3. Position uncertainty — perception +1; navigation skills suffer +1 difficulty in unfamiliar terrain.
T4. Echo — character occasionally appears doubled in others' peripheral vision; intimidation +1; stealth -1.
```

**Eldritch / Corruptive marks (always include corruption +1 in addition to any other mark):**

```
X1. Marked tongue — corruption +1; eldritch_corruptive cost -2; conversation with baseline humans difficulty +1.
X2. Patron-bond — corruption +1; relationship entry generated/strengthened with an eldritch entity NPC; standing ambiguous, trust unmeasured.
X3. Visible transformation — corruption +1; one cosmetic change (eye color shift, skin pattern, hand alteration); visibility "visible".
X4. Dream-bleed — corruption +1; dreams shared with proximate sleepers; perception +1 in dream-state; mental track degrades +1 over years of use.
```

**Universal marks (offered for any breakthrough type):**

```
U1. Lost fear (Preston-trajectory, very rare — only offered for the third+ Depth breakthrough)
    — will +2; condition_tracks.mental max +1; intimidation +2; social-track standings with NPCs at tier < player capped at +1 (cannot be loyal/loved).
U2. Aging acceleration — current_age effective +5 years for purposes of Section 7 aging.
U3. Limp / scar / chronic ache — persistent harm tier 2 acquired during trigger event becomes tier 3 (permanent); attribute -1 in one of {strength, agility} (player picks).
```

The runtime selects three marks for player choice as follows:

```
- Always offer U1/U2/U3 candidates if their conditions are met.
- Offer 2-3 category-specific marks matched to the dominant category of the breakthrough.
- Eldritch marks are mandatory if the breakthrough trigger was condition 3 (Eldritch
  Exposure) or condition 4 (Substance) on a fail-recovery.
- Universal U1 (Lost fear) is only offered when this is the player's 3rd+ Depth breakthrough.
```

### 2.4 Recovery period

After breakthrough:

- Condition tracks all set to current value or 3, whichever is higher (the breakthrough taxes the body).
- Status "exposed" applied for 7 in-world days (the character is reactive, vulnerable).
- During recovery: power use is allowed but every use costs +1 condition damage to the relevant track.
- Recovery ends after 7 days; any unhealed harm from the trigger event remains.
- During recovery, no further breakthroughs may trigger; triggers met during recovery are deferred (state held until recovery ends, then re-evaluated).

---

## SECTION 3 — SKILL PROGRESSION

### 3.1 Skill catalog (32 skills)

Skills are referenced by string id and stored as `Character Sheet.skills: {skill_id: integer 0–10}`. Default is 0 (untrained). Resolution per `combat-spec.md` skill check procedure (1d6+stat vs target opposed by enemy stat or DC).

```
COMBAT
1.  firearms          — pre-Onset small arms; resolves ranged Attack actions
2.  melee             — knives, clubs, improvised; resolves melee Attack actions
3.  brawling          — unarmed; subset of melee but distinct progression
4.  thrown            — knives, rocks, javelins
5.  tactics           — pre-encounter assessment; reads terrain_zones for advantages

PHYSICAL / SURVIVAL
6.  stealth           — moving unseen; reduces opposed perception checks
7.  urban_movement    — climbing, parkour, ruin-crossing
8.  wilderness        — overland travel, tracking, foraging
9.  weather_read      — anticipating conditions; modifies travel time
10. animal_handling   — horses, dogs, livestock, biokinetic-altered fauna
11. swimming          — open water, harbor, river

CRAFT / TECHNICAL
12. craft             — fine work; matter-manipulator-adjacent; clothmaking, leatherwork
13. basic_repair      — improvised repair of mechanical items
14. scavenging        — efficient retrieval from ruins
15. agriculture       — biokinetic-supported farming
16. cooking           — turning raw food into preserved or cookable form

MEDICAL
17. first_aid         — wound care without biokinetic capacity
18. surgery           — invasive intervention; benefits from a biokinetic assist
19. pharmacology      — pre-Onset pharmaceuticals, biokinetic-cultivated remedies
20. field_medicine    — combination of first_aid + pharmacology in austere conditions

SOCIAL
21. negotiation       — commercial and political bargaining
22. intimidation      — coercion through threat
23. command           — leading subordinates in combat or sim
24. instruction       — teaching skills to others
25. streetwise        — navigating informal economies, gangs, criminal networks

KNOWLEDGE
26. literacy          — reading and writing (28% baseline regional rate; valuable)
27. languages         — non-English regional languages (Spanish, Portuguese, Russian, Korean, etc.)
28. history           — pre-Onset and post-Onset historical knowledge
29. regional_geography — knowledge of mid-Atlantic locations, routes, factions
30. bureaucracy       — interfacing with institutions; primarily Fed Continuity / Bourse

OTHER
31. perception_check  — generic alertness; supplements perception attribute
32. faction_etiquette — knowledge of how to approach specific factions
```

### 3.2 Use tracking and strengthening thresholds

Each skill carries `Character Sheet.skill_uses: {skill_id: integer}`, incremented when the skill is invoked in a check (success or fail). Skill proficiency increases at fixed thresholds:

| Proficiency reaches | Cumulative uses required | Notes |
|---|---|---|
| 1 (untrained → novice) | 5 | first use of an untrained skill is +2 difficulty (improv) |
| 2 | 20 | |
| 3 | 60 | |
| 4 | 150 | |
| 5 | 350 | requires either an instructor (skill 6+) or a relevant breakthrough |
| 6 | 750 | requires deliberate study with an instructor (sim activity) for 90 in-world days at this skill |
| 7 | 1,500 | as 6, plus the character must have used the skill in a high-stakes context (combat/critical incident) at least 10 times since reaching 6 |
| 8 | 3,000 | mentor must be skill 9+ |
| 9 | 7,000 | regional-level expertise; named role typical |
| 10 | 15,000 | preeminent in the mid-Atlantic; one or two practitioners per skill at this level |

Progression slows by design — proficiency 4 is achievable in ~3 years of regular practice; 6 is a decade of deliberate work; 8+ is a lifetime.

### 3.3 Skill check resolution

Per `combat-spec.md`, skill checks resolve as: roll `1d6 + skill_proficiency + relevant_attribute_die_step` vs. target DC or opposed roll. Opposed checks are skill+attr vs. opposing skill+attr. (Attribute die step here means: d4=0, d6=1, d8=2, d10=3, d12=4.)

For sim-side skill checks (e.g., scavenging in a ruin), the sim engine resolves directly.

### 3.4 Cross-skill synergies and prerequisites

```
SYNERGIES (the second skill gains a passive +1 to its proficiency at relevant checks
            when the prerequisite is at the threshold listed):

- first_aid 4   →  surgery +1
- agriculture 4 →  cooking +1
- streetwise 4  →  negotiation +1
- tactics 4     →  command +1
- literacy 4    →  history +1, bureaucracy +1, languages +1 (each)
- wilderness 4  →  weather_read +1, animal_handling +1
- urban_movement 4 → stealth +1
- melee 4       →  brawling +1
- firearms 4    →  thrown +1

PREREQUISITES (skill cannot be raised above floor without prerequisite):

- surgery >= 3 requires first_aid >= 4
- field_medicine >= 4 requires first_aid >= 4 AND pharmacology >= 3
- command >= 3 requires tactics >= 3 OR command-related occupation tag from Session Zero
- bureaucracy >= 5 requires literacy >= 5
- pharmacology >= 5 requires literacy >= 4 (recipes are written)
- faction_etiquette per-faction maximum is capped at floor(player_standing_with_faction + 5) — antagonized factions become opaque
```

Synergies and prerequisites computed at every skill-up event; runtime warns player when a planned check is gated.

---

## SECTION 4 — RELATIONSHIP PROGRESSION

### 4.1 Standing and trust evolution

Per `interface-spec.md`: `standing` is integer -3..+3 (player's view), `trust` is integer 0..5 (NPC's trust of player). `current_state` is a string label. Both standing and trust evolve through events.

Standing changes are visible to the player; trust changes are tracked but not always shown (the NPC may say one thing and feel another).

### 4.2 Relationship-changing events catalog

Each event has a magnitude in standing and trust deltas, applied to the affected NPC's `Character Sheet.relationships[npc_id]` entry and mirrored in the NPC's `relationships[player_id]`.

```
EVENT                                             standing  trust
1.  Player saves NPC's life                          +1      +2
2.  Player gives NPC a gift (>50 cu value)           +1       0
3.  Player gives NPC information NPC needed          +0      +1
4.  Player keeps a promise to NPC                    +0      +1
5.  Player breaks a promise to NPC                   -1      -2
6.  Player betrays NPC to a third party              -3      -3
7.  Player allows NPC to be harmed (witness)         -1      -1
8.  Player takes a wound for NPC                     +1      +2
9.  Player shares vulnerability (mental track > 2)   +0      +1
10. Player remembers NPC's significant event          0      +1
11. Player forgets NPC's significant event           -0      -1   (small)
12. Player publicly defends NPC                      +1      +1
13. Player publicly criticizes NPC                   -1      -1
14. Player and NPC are in combat together (won)      +0      +1
15. Player and NPC are in combat together (lost)     -0      +0   (shared loss can deepen later via 16)
16. Player and NPC survive harrowing event           +1      +1
17. Player kills someone NPC loved                   -3      -3
18. Player kills someone NPC hated (and NPC knows)   +1      +1
19. Player has child with NPC                        +2      +2  (locks current_state to "co-parent")
20. NPC's faction acts against player                -0      -1  (NPC is conflicted; magnitude rises if NPC was complicit)
21. Time alone together (sim activity, 1+ days)      +0      +1
22. Romantic moment (sim activity, requires standing >= 1) +1 +1; updates current_state to "lovers" if was non-romantic
23. Sex (requires standing >= 1, lover state)        +0      +1; corruption check if eldritch_corruptive primary
24. Player hides truth NPC asked about               -0      -1  (only if discovered)
25. NPC asks player for help, player refuses         -1      -1
26. NPC asks for help, player gives at cost          +1      +2
27. Player drinks/eats/breaks bread with NPC         +0      +0  (no shift; ritual significance flagged)
28. Player teaches NPC a skill                       +0      +1
29. Player learns from NPC                           +0      +1
30. NPC's death witnessed by player                  +0      +0  (no further shift; locks current_state to "deceased_known")
31. Player corruption increases by ≥ 2 in NPC's presence -1  -1 (NPC sees something change)
32. Player breakthrough witnessed by NPC             +0      +1 (deeper bond through shared crisis)
```

Standing and trust are clamped to [-3, +3] and [0, 5] respectively. `current_state` is updated by specific events (19, 22, 30) or by reaching standing thresholds.

### 4.3 Deepening procedure (`current_state` transitions)

`current_state` transitions are both event-driven and threshold-driven.

```
Threshold-driven (apply when both conditions hold for ≥ 14 in-world days):
- standing >= 1, trust >= 2  →  "cordial" if no other state set
- standing >= 2, trust >= 3  →  "warm" / "friend" (player chooses if multiple options apply)
- standing >= 3, trust >= 4  →  "loyal" / "loved" / "sworn" (player chooses)
- standing <= -1, trust <= 1 →  "cold"
- standing <= -2, trust <= 1 →  "antagonist"
- standing <= -3, trust <= 0 →  "blood feud" / "enemy"

Event-driven (override threshold-driven at event resolution):
- event 19           →  "co-parent" (irrevocable)
- event 22           →  "lovers"
- event 30           →  "deceased_known"
- event 6 betrayal   →  "betrayed" (special; persists even if standing later rises)
- character marriage (sim activity, requires both at standing >= 2 lovers) → "spouse"
```

### 4.4 Breaking procedure

A relationship breaks (transitions to negative state) under any of:

```
- Event 6 (betrayal): immediate transition to "betrayed", standing locked at -3 for 60 in-world days minimum.
- Event 17 (killed someone they loved): immediate "blood feud", standing -3 permanent unless event-resolved.
- Event 5 (broken promise) repeated 3 times within 1 in-world year: transition to "estranged".
- Sustained absence with no contact >= 2 in-world years: standing decays toward 0 (Section 4.5).
- NPC's faction switches to player-hostile: standing modifier of -1 applied unless player specifically counters.
```

Resolution paths from broken state:

```
- "betrayed" → "estranged": requires event 1, 8, or 26 + ≥ 90 in-world days passage.
- "blood feud" → "estranged": requires event 8 directed at NPC + an explicit reconciliation activity (sim).
- "estranged" → "cold": passive time + no negative events for 6 months.
- "cold" → "neutral": standing returns to 0 via event 4 or 21.
```

### 4.5 Continuity through absence

When player is not in NPC's location and no events fire involving them, the relationship state evolves on tick:

```
Per in-world month of absence:
- If standing > 0: standing decays by 0 with probability 0.6, by 1 with probability 0.4. (Bonds erode unless reinforced.)
- If standing < 0: standing decays toward 0 by 0 (prob 0.7) or +1 (prob 0.3). (Old grievances soften.)
- If standing == 0: no change.
- Trust does not decay; it is sticky.
- NPC's memory of player accumulates: each in-world year of absence adds an entry "did not return for [N] years" to NPC's memory (interface-spec NPC.memory).
- After 5 in-world years of absence, current_state becomes "long-absent"; on player's return, standing displays unchanged but NPC's first-meeting reaction reflects the absence (narrator beat).
```

NPC may move location on their own ticks (sim engine). On player return, NPC may not be where left; NPC may have died, transformed, joined a faction, married, had children, etc. All such changes are surfaced to the player on first re-encounter via a `Narrator Payload` summary.

### 4.6 Death of significant NPCs

When an NPC at `relationships[npc_id].standing >= 2` dies:

1. NPC.status set to "dead"; NPC.location set to "deceased".
2. Player's `relationships[npc_id].current_state` set to "deceased_known" (if player witnessed or learned) or "deceased_unknown" (if player has not yet been told).
3. Standing locked (no further changes).
4. `Character Sheet.history` entry generated, category "personal".
5. `condition_tracks.mental` += 1 if standing was 2; += 2 if standing was 3.
6. Goal tied to NPC, if any: pressure += 2 and re-categorized as "honor" or "avenge" depending on cause of death (player picks at the moment narration delivers the news).
7. Trigger evaluation of breakthrough condition 6 (Traumatic Loss).
8. NPC's `resources` may pass to player per inheritance procedure (Section 8.5) if NPC was kin or sworn.

If death is "transformed" rather than dead: same procedure but `current_state` set to "transformed_known"; the transformed NPC may persist as a non-player entity in NPC files, with eldritch or corrupted character; relationship tracking continues but with a strange register.

---

## SECTION 5 — FACTION STANDING

### 5.1 Player faction standing model

Per design_decisions in character-creation.md: faction standing from the player's perspective is read at runtime from `factions/{faction_id}.json` external_relationships entry for the player. For runtime efficiency, this spec **adds a mirror field** to `Character Sheet`:

```
Character Sheet.faction_standing: {faction_id: {standing: integer -3..+3, reach: integer 0..5}}
```

`standing` mirrors the faction's view; `reach` is a separate measure of how widely the player is known within the faction (0 = invisible, 5 = named figure). Mirror is updated on every faction-standing event; cross-validation against faction file required on save load.

### 5.2 Standing-change events catalog

Applied to `Character Sheet.faction_standing[faction_id]` and `factions/{faction_id}.json.external_relationships[player_id]`.

```
EVENT                                                  standing  reach
1.  Completed contract / paid mission for faction         +1     +1
2.  Refused contract                                       0     +0
3.  Betrayed contract terms                               -2     +1
4.  Killed faction member (witnessed/known)               -2     +2
5.  Killed faction enemy (faction knew)                   +1     +1
6.  Saved faction member's life                           +1     +1
7.  Defended faction territory (combat)                   +1     +1
8.  Took faction territory                                -2     +2
9.  Donated significant resources (>500 cu value)         +1     +1
10. Took faction property (theft, witnessed)              -2     +1
11. Married into faction (requires NPC of faction at standing >= 3, sim activity) +2 +1
12. Had child with faction member                         +1     +1
13. Sworn oath to faction (formal)                        +2     +2
14. Broke oath to faction                                 -3     +1
15. Spoke publicly for / against faction                  ±1     +1 (sign per content)
16. Aided faction's rival (faction knew)                  -1     +1
17. Aided faction's ally (faction knew)                   +1     +1
18. Trained with faction                                   0     +1
19. Successfully petitioned faction leadership            +1     +1
20. Failed petition                                        0     +1
21. Caught corrupting / corrupted within faction territory -1     +1
22. Earned a faction-specific honor (per content)         +2     +1
23. Arrested or held by faction                           -1     +1
24. Escaped from faction custody                          -2     +2
25. Provided intelligence to faction                       +1     +1
26. Spy uncovered                                         -3     +2
27. Faction leader meets player personally (positive)     +0     +1
28. Faction leader meets player personally (negative)     -1     +1
29. Player receives a named title from faction            +1     +1
30. Player publicly humiliated within faction territory   -1     +1
```

### 5.3 Reputation accumulation

`reach` accumulates with each event. Higher reach unlocks faction-internal opportunities and risks.

| Reach | Threshold effect |
|---|---|
| 0 | invisible — faction does not know player exists |
| 1 | local awareness — at most one local officer of the faction recognizes the name |
| 2 | regional awareness — faction in player's region knows the name |
| 3 | faction-wide — leadership has heard of player |
| 4 | named figure — faction leadership knows the player personally; player may petition directly |
| 5 | a name — songs, stories, legends; player is a fact in the faction's internal narrative |

### 5.4 Standing decay over time

Standing is **less sticky** than relationship standing because factions are institutions and forget faster than individuals.

```
Per in-world year:
- If |standing| >= 2: drift toward sign by 0 (prob 0.5) or by 1 toward zero (prob 0.5).
- If |standing| == 1: same as above.
- Decay halts entirely if any event in the past year affected this faction.
- Reach: if no event in 3 years, reach decays by 1; floor 0. Names are forgotten faster
  than acts.
- Heat (separate from standing, per interface-spec): decays by 1 per in-world year if
  no triggering event; unless heat was earned via event 26 (spy uncovered) or 14 (broken
  oath), in which case heat does not decay.
```

### 5.5 Threshold effects

```
Standing  Effects
-3        formally hostile; faction territory entry triggers combat encounter rolls
-2        hostile; entry tolerated only with escort; surveillance flagged
-1        cold; merchants overcharge; service slow; petition rejected
 0        neutral; standard rates and treatment
+1        cordial; minor preferential treatment; small contracts offered
+2        warm; access to faction-internal services (training, lodging, intelligence)
+3        loyal/sworn; included in faction strategic planning; titles available

Reach    Effects
 0       no faction interaction triggered by player presence
 1       local situations (Sim) may include faction NPC arriving
 2       faction-themed missions surface in sim's situation generator
 3       faction leaders' major moves involve player as participant or pawn
 4       player may initiate scenes with faction leader
 5       player's actions become faction internal politics
```

---

## SECTION 6 — RESOURCE PROGRESSION

### 6.1 Resource categories

Stored in `Character Sheet.resources: {resource_name: integer}`. Seven categories.

```
1. TERRITORY     — physical land or location holdings
                   keys: territory_holdings (count), territory_size_total (acres)
2. HOLDINGS      — buildings, fortifications, fixed infrastructure
                   keys: holding_residence, holding_workshop, holding_fortified_position,
                         holding_warehouse, holding_estate, holding_stronghold
3. WEALTH        — currencies and tradeable stores
                   keys: cu (Bourse copper), scrip (Fed Continuity, depreciating),
                         crown_chits (Iron Crown, regional only), grain_stores (units),
                         pre_onset_pharma (units, very valuable), trade_goods (general)
4. FOLLOWERS     — people who answer to the player
                   keys: retainers (count), retinue (count, combat-capable),
                         apprentices (count), dependents (non-combatant)
5. INFLUENCE     — political and social capital not in faction_standing
                   keys: bourse_credit_line (cu equivalent),
                         contacts_thin / contacts_solid / contacts_deep,
                         titles_held (list), debts_owed_to_player (list),
                         debts_owed_by_player (list)
6. KNOWLEDGE     — information assets
                   keys: maps_held, manuscripts_held, scrolls_eldritch (corruption-risk),
                         intelligence_packets (each tied to a faction or location),
                         craft_secrets
7. EQUIPMENT     — categorized inventory
                   keys: weapons_quality (count by tier), armor_quality, tools,
                         transport (horses, carts, boats), comms_devices_pre_onset
```

`inventory` field (per `interface-spec.md`) holds individual item records; `resources` holds category-level aggregates.

### 6.2 Acquisition procedures

Each resource type acquires through specific activities. Sim engine validates eligibility; combat outcomes deliver some.

```
TERRITORY
  - Granted by faction (faction.standing >= 3, formal grant): acquisition is a sim activity
    "petition for grant" that takes 30+ in-world days; 50% success at standing 3, 80% at standing 4 mirror, etc.
  - Conquered: combat outcome with `world_consequences.type == "territory_contested"`
    that resolves in player favor; requires combat strength sufficient + holding capacity.
  - Inherited: per Section 8 inheritance.
  - Purchased: rare; requires wealth ≥ 5,000 cu and seller eligibility.

HOLDINGS
  - Built: sim activity "construction" of variable duration (workshop: 90 days, residence: 60 days, stronghold: 365 days+); requires followers (laborers) and resources (stone, wood, iron).
  - Acquired with territory: most territory grants include existing holdings.
  - Captured: combat outcome.

WEALTH
  - Wages from contracts (Section 5 events; per-faction rates per gm-primer.md).
  - Trade: sim activity using negotiation skill + region price differentials.
  - Salvage: sim activity in ruins; uses scavenging skill.
  - Inheritance: per Section 8.
  - Loot: combat outcome `resources_spent` field (negative spent = gained).

FOLLOWERS
  - Hire: requires wealth (retainer 150 cu/mo standard; retinue 300+; apprentices unpaid stipend).
  - Recruit: requires reputation (reach >= 2 with relevant faction or local).
  - Sworn: a follower at standing >= 3 with player who takes oath; permanent absent break.
  - Inherit: per Section 8.

INFLUENCE
  - Earn through events (debts owed); accumulate through faction service.
  - Bourse credit line: granted at standing >= 2 with bourse + reach >= 2.
  - Titles: granted by factions (event 29 in 5.2).
  - Debts owed to player: tracked individually, redeemable.

KNOWLEDGE
  - Purchased from Bourse / specialists.
  - Captured in salvage.
  - Granted by NPCs at standing >= 2 + literacy >= 4.
  - Researched: sim activity in library (Princeton, Rutgers, Bourse Library).

EQUIPMENT
  - Crafted (craft skill).
  - Purchased.
  - Captured (combat outcome).
```

### 6.3 Maintenance / upkeep procedures

Resources without maintenance decay. Decay applied per in-world tick (default monthly).

```
TERRITORY
  - Requires followers (≥ 1 retainer per 100 acres) and wealth (15 cu per acre per year).
  - Underfunded territory: per month deficit, lose acres equal to (deficit / 50 cu).
  - Unowned by faction: subject to raid / encroachment events on sim ticks.

HOLDINGS
  - Each holding: 30 cu/month upkeep base; +50 cu if fortified; +100 cu if stronghold.
  - Underfunded: holding degrades — workshop loses craft bonus; residence becomes uninhabitable; stronghold becomes ruin (after 24 months underfunded).

WEALTH
  - Currencies decay differently:
      cu: stable.
      scrip: -5%/year (Fed Continuity erosion clock); -20%/year if Erosion clock fires.
      crown_chits: -10%/year; -100% (worthless) if Iron Crown collapses.
      grain_stores: -10%/month spoilage unless biokinetic-preserved (-2%/month).
      pre_onset_pharma: -3%/year (stockpile aging per gm-primer); zero by ~T+5 to T+8.

FOLLOWERS
  - Wages required monthly per follower type.
  - Underfunded: morale event roll on tick; loyalty -1 standing per missed month; followers leave at standing 0.
  - Casualties: combat outcomes may kill followers; recruitment is the only restoration.

INFLUENCE
  - Bourse credit line: revoked if standing with Bourse drops below 1.
  - Debts owed: aging — 1 in 10 chance per year of being uncollectible.
  - Titles: held until removed by faction (faction-internal political tick may strip).

KNOWLEDGE
  - Manuscripts decay: -5% chance per year of becoming unreadable in non-archival storage.
  - Held in a Bourse vault or Princeton library: 0 decay.

EQUIPMENT
  - Weapons: -5% quality per year of use; -2% if maintained.
  - Armor: -3% per year combat use; -1% storage.
  - Tools: degrade with use; basic_repair check restores.
  - Transport: horses age (Section 7 applies — no, simpler: 12-year working life).
```

### 6.4 Conversion procedures

```
Wealth ↔ Wealth (currency exchange):
  - Bourse fee 5%; 10% in faction territories not aligned with Bourse.
  - Cross-currency rates per gm-primer Quick-Reference.

Wealth → Holdings/Territory: see Acquisition.
Wealth → Followers: hiring above.
Wealth → Knowledge: purchase from libraries / Bourse.
Wealth → Equipment: purchase or contract crafting.
Knowledge → Wealth: sale to Bourse / Fed Continuity / faction (variable rates).
Equipment → Wealth: sale; standard 50% of crafted-cost recovery.
Followers → Influence: every 5 retainers for 12 months adds 1 to local reach.
Influence (debts) → Wealth or Knowledge or Equipment: at NPC discretion.
Territory → Wealth: lease income (5–20 cu/acre/year depending on land quality); slow.
Territory → Followers: peasants on territory may be levied (one-time) into temporary retainers.
```

### 6.5 Loss conditions

```
- Combat defeat in territory: contested status applied; weeks/months to resolve.
- NPC betrayal (event 6): may transfer holdings or wealth to NPC if NPC was steward.
- Faction action (faction.standing very low + event in 5.2): expropriation possible.
- Eldritch encroachment: territory near Pine Barrens / charged zones may shrink (sim tick).
- Player death: see Section 8 inheritance.
- Currency collapse: scrip / chits / etc. zero out on faction collapse.
- Disaster: sim ticks may trigger location-affecting events (fire, plague, raid).
```

---

## SECTION 7 — AGING

### 7.1 Aging timeline (baseline humans)

`Character Sheet.current_age` advances with `World State.current_time`. Each in-world year increments by 1 on the player's birthday (deterministic offset from onset date).

Aging effects apply at decade transitions (entering 30s, 40s, 50s, 60s, 70s, 80s). Effects are cumulative; they apply on the first tick of the relevant year.

```
20s (16-29)   — Baseline. No decrements. +1 to one attribute (player picks) at age 25 if not already maxed (representing physical maturity).
30s (30-39)   — No decrements yet, but slower recovery. condition_tracks recovery slowed: 1 extra in-world day per harm tier when healing without biokinetic. Skill use thresholds for new skills (untrained → novice) +20% (harder to learn fresh things).
40s (40-49)   — Strength -1 die size. Agility -1 die size. Recovery +50% slower than 20s baseline. New skill acquisition: no learning of skill from untrained without instruction (instructor required). Insight may +1 die at age 45 if not maxed.
50s (50-59)   — Strength -1 (cumulative -2), agility -1 (cumulative -2). Perception -1 die. Condition_tracks.physical max -1. Authority opens: titles, command roles, mentorship slots become more accessible. Insight +1 if not maxed at age 55.
60s (60-69)   — Strength -1 (cumulative -3, floor d4), agility -1 (cumulative -3, floor d4), perception -1 (cumulative -2). Condition_tracks.physical max -1 (cumulative -2). Will may +1 (lifetime experience). Combat encounters: fatigue accumulates faster. Death roll begins (Section 7.4).
70s (70-79)   — All physical attributes at floor (d4 minimum). Condition_tracks.physical max 3. Power use: any deliberate use causes condition tax +1. Death roll intensifies.
80s+ (80+)   — Each year requires a death roll regardless of activity. Player who survives is exceptional.
```

Attribute floors: `d4`. Below d4, the attribute is considered functionally lost (rolled as automatic 1).

### 7.2 Variation for species

Species modify the aging timeline:

```
Species A (Hollow-Boned)  — fragility accelerates: 50s decrements apply at 40; 60s at 50.
Species B (Deep-Voiced)   — baseline aging.
Species C (Silver-Hand)   — hand mineralization (cumulative with mark E1) accelerates physical decline; -1 strength per decade additional from 40s.
Species D (Pale-Eyed)     — baseline aging; perception decline halved.
Species E (Slow-Breath)   — aging slowed: decade transitions apply at +5 years (40s effects at 45, etc.); life expectancy +10 years.
Species F (Broad-Shouldered) — baseline aging; condition_tracks.physical max retained at 6 through 60s.
Species G (Sun-Worn)      — cosmetic acceleration noted from 25 (greying); mechanical aging baseline.
Species H (Quick-Blooded) — baseline aging accelerated by -5 years (decrements at 25/35/45/55/65 etc.); short-lived; offset by faster recovery throughout life.
Species I (Wide-Sighted)  — perception decline halved; otherwise baseline.
Species J (Stone-Silent)  — strength decline halved; will +1 from 50s.
```

### 7.3 Variation for corruption

Corruption interacts with aging:

```
- Corruption 1-2: no aging modifier.
- Corruption 3-4: aging decade transitions apply at +5 years (slowed) for physical decrements.
                   — corrupted bodies physically degrade differently; some are preserved.
- Corruption 5: aging halts mechanically for physical attributes; mental/social tracks may shift independently. The character's "current_age" still increments for narrative purposes; physical body does not match age.
- Corruption 6: see Section 9.5.
```

### 7.4 Capability transitions

```
Authority (opens with age):
- Eligibility for "captain" role appointments: 30+
- Eligibility for "councillor" or "elder" roles: 50+
- Eligibility for "lord" or "named successor" roles: 40+ baseline; species varies
- Title-holding becomes social anchor in the 50s; relationship trust ceiling +1 with NPCs ≥ 35 once player passes 50.

Physical activities (close with age):
- Combat front-line participation: harder past 50 (encounters generate retreat options preferentially)
- Travel speed: -10% per decade past 30 in overland speed
- Sustained labor: condition cost +1 per scene past 50
- Pregnancy: viability declines after 35 (Section 8)
```

### 7.5 Death by old age

Each year past age 60, a death roll on player's birthday tick:

```
Roll 1d20.
Modifiers:
  - Physical track current value: -1 per filled segment
  - Persistent harm tier 3: -2 each
  - Corruption: -1 per segment above 2
  - Age above 60: -1 per 5 years above
  - Species E, J: +2
  - Species C, H: -1 (shortened lifespan trajectory)
  - condition_tracks.mental at 4-5: -1
  - Resources: lodging_paid present, biokinetic care contracted: +2
  - Yonkers Compact resident or aligned: +1
  - Lifestyle: high-stress (combat in past year, refugee status): -1
DC 8.
Pass: another year.
Fail: death sequence triggered.
```

#### 7.5.1 Soft warnings

The runtime issues narrator beats as the death roll approaches risk:

```
- 18 months before estimated death (when DC margin <= 3): narrator beat featuring NPC concern, mirror, unusual tiredness.
- 6 months before estimated death: narrator beat — "the work is harder than it was."
- On the failed roll: full death sequence (Section 7.5.2).
```

These beats are derived from running the death roll silently each tick and forecasting near-failures.

#### 7.5.2 Death scene

A `Narrator Payload` with `scene_type: "death_narration"` and `register: "quiet"`. The scene is fixed-form:

```
- Present-moment narration of the dying. Brief. Concrete. Setting depicted.
- One conscious choice offered: "what do you want to say"; player free-text 1-300 chars
  delivered to whichever NPC is present (highest standing + present + alive).
- NPC response narrated.
- Final beat: closing image. Specific. Sensory.
- Character status set to "dead". Player Sheet locked from further modification.
- Inheritance procedure (Section 8.5) triggered.
- Continuation prompt offered: "play a descendant?" (Section 8.4).
```

Death from combat or violence has its own narration path per `combat-spec.md`; this section governs death from age and attrition.

---

## SECTION 8 — FAMILY AND LINEAGE

### 8.1 Reproduction mechanics

Reproduction is a sim activity, not a combat outcome. Eligibility:

- Player and partner NPC both alive, present in same location for sustained period.
- Both manifested OR both unmanifested (cross-pairings standard 80/20 baseline / metahuman per `powers.md`).
- Sim activity "trying for a child" requires standing ≥ 2 mutual.
- Per attempt month: 25% conception baseline, modified by:
  - Player age 16-30: no modifier; 31-35: -5%; 36-40: -15%; 41-45: -25%; 46+: requires biokinetic intervention.
  - Partner same modifiers.
  - Health (condition_tracks.physical < 2 either party): no modifier; > 2: -10% per segment over.
  - Corruption ≥ 3 either party: -50% additional.
  - Cross-species pairing: 5% baseline (per bible); offspring viability separate roll.
- Pregnancy: 9 in-world months for human; species variations [NEEDS AUTHORSHIP].
- Childbirth: medical event. With biokinetic: routine. Without: per gm-primer "childbirth kills women at rates not seen in the region for a century" — 5% maternal mortality without biokinetic; 0.5% with.

### 8.2 What determines outcomes

For each conception, on viable pregnancy:

```
Step 1: Species determination.
  - Human + Human            → Human always.
  - Human + Metahuman X      → Human 80%, Metahuman X 20%.
  - Metahuman X + Metahuman X → Metahuman X always.
  - Metahuman X + Metahuman Y → 5% viable; if viable, picks parent species at coin flip.

Step 2: Manifestation determination at puberty (puberty = age 12-14 random).
  - Both parents manifested:    99% manifestation rate.
  - One parent manifested:      98%.
  - Neither parent manifested:  80%.

Step 3: Category inheritance (if manifested).
  - Population baseline modified: parent's primary category 2x more likely than chance.
  - If both parents have same primary category: 4x more likely.
  - Tier inheritance: parental tier irrelevant — child tier rolled per pyramid (Section 4.2.3 of character-creation.md).
  - Profile breadth inheritance: if both parents narrow-specialist (single category), child likely narrow (P(narrow) = 0.7); if both multi-domain, child likely multi (0.7); mixed parents, child 0.5.
```

### 8.3 Lineage tracking across generations

Each child generates an NPC file with:

- `parents: [player_id, partner_id]`
- `birth_date: <in-world>`
- `birth_location: <location_id>`
- Full NPC schema fields, populated as they age (initially infant: minimal entries; expand on tick milestones at age 5, 12, 18).

Player's `relationships[child_id]` tracks them like any other relationship; standing default +3, current_state "parent_of" (cannot be reduced below +1 by ordinary events).

Multi-generation tracking: when player dies, descendants persist as NPCs with `parents` field maintained. Lineage reconstruction is a graph traversal of NPC files via `parents` field. Lineage is queryable but not displayed unless requested.

### 8.4 Continuation as descendant procedure

On player death (Section 7.5 or combat), the runtime offers continuation:

```
1. Identify candidate continuation characters from `player.relationships` and saved NPCs:
   - Player's children, age >= 16 at time of death.
   - Player's apprentices (followers tagged as apprentices).
   - Player's named-successor NPC (if explicitly designated via sim activity "designate heir").
   - Sworn followers at standing ≥ 3.
2. Present candidates with brief summaries.
3. Player may also select "no continuation; new character" (full Session Zero rerun).
4. On selection of continuation:
   - Selected NPC promoted to player character.
   - Their NPC file converted to character.json schema.
   - Their attributes, powers, tier, relationships, location, current_age all preserved.
   - World State.active_player_character updated.
   - World State.past_characters appended with old player id.
   - Inheritance applied (Section 8.5).
   - Memory of predecessor: new player gains a one-time "inherited memory" entry summarizing the predecessor's life-shape — this is narrative continuity.
```

In-world time continues — the new character starts from their current age in their current life situation; the world has continued ticking through the death scene.

### 8.5 Inheritance: resources, relationships, faction standings, knowledge

Inheritance procedure on player death:

```
RESOURCES
  - If continuation character chosen: 60% of player's wealth resources transfer; 100%
    of any titled holdings (territory, holdings) for which the continuation character
    is the named successor; otherwise holdings revert to factions or are contested.
  - Specific items in inventory transfer at 100%.
  - Followers: each follower rolls morale (will check vs DC 7 + standing-with-player);
    pass = transfers loyalty to continuation character at standing -1; fail = leaves.
  - Currency held: 100% transfers (carried).

RELATIONSHIPS
  - Continuation character keeps own relationships (which already included player as relationship to other NPCs).
  - Inherits view of player's significant relationships at standing 0 or +1 (per existing relationship type with continuation):
      Player's spouse: continuation already has parent/step-parent relationship if child of pairing; standing inherited.
      Player's allies and oathsworn: standing 0 by default with continuation; one-time grace event "your predecessor's friend" boosts standing +1.
      Player's enemies: standing -1 inherited; "your predecessor's enemy" carries weight.

FACTION STANDINGS
  - Continuation inherits 50% of player's standing values rounded toward zero.
  - Reach inherits at 50% (rounded down).
  - Heat inherits at 100% if standing was negative (institutional grudges persist) or 50% if neutral/positive.
  - Titles: do not inherit by default; specific titles tagged "hereditary" do.

KNOWLEDGE
  - Manuscripts and scrolls in physical inventory transfer fully.
  - Skill proficiencies do NOT transfer (continuation has their own).
  - Goals do not transfer (continuation has their own); but a "Goal: continue what was started" may be offered as a one-time choice based on predecessor's highest-pressure unresolved Goal.
```

If no continuation chosen: world continues, player's holdings revert to factions per faction logic, surviving relationships continue as NPCs, world.active_player_character updated to the new Session Zero character.

---

## SECTION 9 — CORRUPTION

### 9.1 Sources catalog

Corruption accumulates on `Character Sheet.corruption` (0–6 per `interface-spec.md`). Sources:

```
A. POWER USE (per use):
   1. Eldritch_corruptive primary power use: +0.05 per use (tracked as float internally,
      ceiling integer applied at thresholds; 20 uses = +1).
   2. Other category power use under stress: condition tax overflow; corruption +1 for every
      4 uses past mark 5 thresholds.

B. EXPOSURE (per scene/period):
   3. Scene in eldritch-charged location: +1 corruption per 3 cumulative days.
   4. Exposure to anomalous eldritch entity (combat or sustained presence): +1 per encounter.
   5. Exposure to corrupted NPCs at standing >= 2: +1 per in-world year if NPC corruption >= 4.
   6. Witness of horror beyond normal limits (specific event types): +1 per event.

C. ACTIONS:
   7. Taking eldritch bargain (mark X2 path): +1 immediate.
   8. Substance breakthrough fail: +1 (Section 2.1 condition 4).
   9. Killing NPC at standing >= 3: +1 immediate.
   10. Kinslaying (relative or sworn): +2 immediate.
   11. Cannibalism: +1 per occurrence.
   12. Taking life of an entity that asked for parley with intent to deceive parley terms: +1.

D. BREAKTHROUGH MARKS:
   13. Mark E1 (Mineralization): +1.
   14. Marks X1-X4: +1 each.
   15. Mark U1 (Lost fear): +1.

E. MEDICAL / SUBSTANCE:
   16. Use of pre-Onset psychoactives outside ritual context: +1 per period of dependency
      (1+ in-world month of regular use).
   17. Eldritch-cultivated substances regular use: +1 per month.

F. RELATIONSHIPS:
   18. Sustained relationship at standing >= 2 with eldritch-aligned NPC (current_state
      "patron_or_predator"): +1 per in-world year.
```

### 9.2 Threshold meanings (segments 0-6)

Per `interface-spec.md`:

- 0: baseline
- 1-2: touched
- 3-4: changed
- 5: transforming
- 6: transformed (becomes non-player entity)

### 9.3 Specific marks at each threshold

Each segment's first time crossing produces a permanent mark; subsequent re-crossing does not duplicate. Marks persist even if corruption is later reduced.

```
Segment 1 — TOUCHED (cosmetic, slight)
  Choose one (player picks at first crossing):
  - Eyes shift color faintly.
  - Skin shows a faint pattern (silvery, vein-like, or geometric).
  - Voice carries a subtle resonance (perception checks against player +1 difficulty).
  - Sleep shortens; less rest needed; dreams more vivid.
  Mechanical: none; signaling only.

Segment 2 — TOUCHED (perceptible)
  Choose one:
  - Auratic minor effect: NPCs feel uneasy (no opinion shift, but NPCs note the discomfort).
  - One sense slightly enhanced (+1 to perception checks of one type).
  - Hands feel cold or warm to others on contact.
  Mechanical: minor; one-off.

Segment 3 — CHANGED (visible)
  Choose one:
  - Visible physical alteration (scaled patch, eye change, hair change): commerce difficulty +1 in unfamiliar territory.
  - Behavioral compulsion (specific situational): one tic, narrative-only.
  - Power_category_primary cost reduction in eldritch_corruptive: -1 (free corruption discount).
  Mechanical: small; visibility "subtle" → "visible".

Segment 4 — CHANGED (significant)
  Choose one:
  - Persistent harm tier 2 acquired: a slow physiological wrongness (limbs wrong-jointed; skin thickened).
  - Relationship trust ceiling -1 with non-corrupted NPCs.
  - One new tier-1 power in eldritch_corruptive offered (player may decline).
  Mechanical: larger; visibility "visible".

Segment 5 — TRANSFORMING (severe)
  All apply:
  - Visible transformation (no longer fully passing as baseline human): NPCs respond differently; some flee.
  - Persistent harm tier 2 (unhealable through ordinary means).
  - Aging halts mechanically (Section 7.3).
  - One forced sim-tick check per in-world month: will check vs DC 12. Fail = corruption +1, accelerating toward 6.
  - Faction standings cap at 1 except with eldritch-aligned factions.

Segment 6 — TRANSFORMED
  Triggered: see Section 9.5.
```

### 9.4 Reversibility per segment

Per gm-primer / bible: "Whether corruption from heavy power use can be reversed... has not been reversed in any observed case. But the cases are few." Mechanically:

```
Segments 1-2: REVERSIBLE.
  - Sustained absence from corruption sources for ≥ 2 in-world years → corruption -1.
  - Biokinetic intervention (Yonkers Three Judges or equivalent T6+ biokinetic) once: corruption -1.
  - Sacrifice breakthrough used for cleansing: corruption -1.
  - Maximum -1 from each source above; effects can stack to clear segments 1-2 fully.

Segments 3-4: PARTIALLY REVERSIBLE.
  - Same procedures as above but each yields at most 1 segment reduction over 5 in-world years.
  - Marks remain even when corruption integer reduces (a "changed" character whose
    corruption returns to 2 still has the segment 3 cosmetic mark).

Segment 5: NEAR-IRREVERSIBLE.
  - Only sustained eldritch-equivalent intervention (mark X3 patron's voluntary release;
    successful counter-bargain) may reduce; rare and costly.
  - Reduction at most -1, requires sim activity of 1+ in-world year of dedicated work.

Segment 6: TRANSFORMATION (irreversible).
  - Per Section 9.5.
```

### 9.5 Maximum corruption procedure (transformation)

When `corruption == 6` is reached:

```
1. Runtime emits Narrator Payload scene_type: "death_narration" with register: "eldritch".
   The scene is the character's transformation, narrated as inevitability.
2. The character is converted to NPC schema:
   - status: "transformed"
   - species: "corrupted" (per interface-spec NPC species options)
   - Faction standing: all factions set to -2 minimum (humans cannot trust this person).
   - manifestation: tier preserved; category may shift to eldritch_corruptive primary
     (if not already); secondary preserved.
   - All relationships' current_state updated to "transformed_known" or "transformed_unknown"
     per visibility.
3. Character's `Character Sheet` is locked (read-only); preserved in player/character.json
   for historical reference.
4. Inheritance procedure (Section 8.5) triggers — same as death.
5. The transformed entity persists in the world as a new NPC. The NPC's behavior is
   driven by NPC tick logic; their goals carried over from the player's last Goal set,
   reinterpreted through the eldritch register. Future encounters may surface them.
6. Continuation prompt offered.
```

The transformed character is not "dead" in the technical sense — they continue in the world as something else. The boundary between transformation and death is the player's loss of control, not the cessation of being.

---

## SECTION 10 — NARRATIVE ARCS

### 10.1 Arc types catalog

Narrative arcs are persistent, multi-session story structures that the sim engine surfaces situations against. They are similar to but distinct from Goals: a Goal is a pressure (single line); an arc is a structure (state machine).

Arcs are stored as `Character Sheet.arcs: [arc_object]`. Each arc:

```
{
  id: string,
  type: string (from catalog below),
  title: string,
  initiated_at: in-world date,
  state: string (per arc's state machine),
  state_data: object (arc-specific),
  parties: list of {id: string (npc_id or faction_id), role: string},
  pressure: integer 0-5 (rate at which sim surfaces relevant situations),
  resolution: string or null,
  resolved_at: string or null
}
```

Arc type catalog (15 types):

```
1.  faction_leadership       — player rises within a faction toward leadership
2.  territorial_consolidation — player builds territory and integrates holdings
3.  family_building           — player establishes / extends a household and lineage
4.  vendetta                  — player pursues revenge for specific harm
5.  eldritch_investigation    — player investigates an anomalous entity / phenomenon
6.  breakthrough_quest        — player seeks specific breakthrough condition
7.  succession_crisis         — player participates in or precipitates a power transition
8.  trade_empire              — player builds commercial network across regions
9.  refugee_protection        — player shelters and defends a vulnerable group
10. apprenticeship            — player learns from a specific mentor toward proficiency
11. romance                   — player builds toward a specific romantic outcome
12. cultural_revival          — player works to preserve / rebuild pre-Onset knowledge
13. heresy_or_cult            — player follows or builds a religious / ideological structure
14. monster_hunt              — player tracks and confronts a specific eldritch / Warped entity
15. final_journey             — player approaches end-of-life with specific business
```

### 10.2 Arc state machines

Each arc type has a state machine. Common states:

```
INITIATED → ENGAGED → ESCALATING → CLIMAX → RESOLVED
                                       ↓
                                   SUSPENDED (player walks away; can re-enter)
                                   ABANDONED (3 in-world years without action)
                                   FAILED (specific failure condition met)
```

Per-arc-type state machines (selected examples; full machines in `data/arcs/{arc_type}.json`):

```
faction_leadership:
  INITIATED      — player joined faction, reach >= 1
  ENGAGED        — player at standing >= 2, reach >= 2
  ESCALATING     — player named officer / titled
  CLIMAX         — leadership challenge or succession event imminent
  RESOLVED-WIN   — player is faction leader or recognized successor
  RESOLVED-LOSS  — challenger superseded player; player exiled or demoted
  ABANDONED      — player departed faction (standing -1 for 1 year)

vendetta:
  INITIATED      — target identified
  ENGAGED        — player has taken first action toward target
  ESCALATING     — player has caused harm to target's network
  CLIMAX         — player and target in same location with combat option
  RESOLVED-WIN   — target dead, transformed, or conceded
  RESOLVED-LOSS  — player killed by target's faction; vendetta passes to descendant
  RESOLVED-PEACE — player and target enter formal truce (rare; Goal pressure 0)
  SUSPENDED      — player away from target's region for 1+ years

eldritch_investigation:
  INITIATED      — player has knowledge of phenomenon
  ENGAGED        — player has investigated at site or witness
  ESCALATING     — player has engaged corrupted source (corruption ≥ 1 from arc)
  CLIMAX         — player faces direct contact / decision with the entity
  RESOLVED-WIN   — anomaly understood (in-character, not metaphysically resolved)
                   OR contained
  RESOLVED-LOSS  — corruption ≥ 5 or character transformed
  ABANDONED      — player departs; arc dormant; phenomenon continues

[remaining arc state machines per data/arcs/]
```

### 10.3 Progression mechanics

Arcs progress through:

- **Player actions** that advance specific state transitions per the arc's machine.
- **Sim ticks** that may advance arcs the player is not actively pursuing (factions move; targets move; opportunities arrive or pass).
- **Pressure**: each arc's `pressure` integer (0-5) controls how often the sim's situation generator surfaces situations relevant to this arc:
  - Pressure 0: dormant; no situations surfaced.
  - Pressure 1: ~1 situation per in-world season.
  - Pressure 2: ~1 per month.
  - Pressure 3: ~2 per month.
  - Pressure 4: ~weekly.
  - Pressure 5: dominant; most situations relate to this arc.

Pressure derives from arc state (CLIMAX = pressure 4-5) and from player intent (player-set "focus" command raises one arc's pressure +1).

### 10.4 Resolution

An arc resolves when a state transition reaches a RESOLVED-* state. On resolution:

```
1. Arc.resolved_at set to current time.
2. Arc.state set to terminal state.
3. History record generated, category appropriate.
4. Resource / relationship / faction-standing consequences applied per resolution type
   (defined in data/arcs/{arc_type}.json).
5. Goals tied to this arc removed or updated.
6. New arcs may be generated (Section 10.5).
7. The arc remains in Character Sheet.arcs[] permanently as historical record.
```

### 10.5 Generation of new arcs from play

Arcs may be generated by:

```
A. Session Zero: each Goal at pressure >= 2 generates an associated arc at pressure
   matching the Goal.

B. Critical events: combat outcomes, faction events, NPC deaths, breakthroughs may
   each trigger arc generation per defined templates. Examples:
   - First combat killing of a faction member at standing -2: generates "vendetta" arc
     against that faction (or specific commander).
   - Breakthrough Mark X2 (patron-bond): generates "eldritch_investigation" arc.
   - Player marriage (event 11/19): generates "family_building" arc.
   - Player title gained (faction event 22 or 29): generates "faction_leadership" arc.

C. NPC offers: an NPC with relationship standing >= 2 may offer the player an arc
   ("I need help with this thing"). Player may accept (arc generated) or decline.

D. Resolution chain: completing one arc may generate a follow-up arc per
   data/arcs/{arc_type}.json continuation rules. (E.g., succession_crisis RESOLVED-WIN
   generates faction_leadership arc.)

E. Player command: at any sim mode beat, player may declare an explicit arc by
   describing intent (free-text, runtime maps to arc_type via heuristic or asks
   clarifying question). This is the player-driven path for non-emergent arcs.
```

Arcs generated at runtime are written to `Character Sheet.arcs[]` and persisted on next save. Arc cap: no hard limit on count, but **only 4 arcs can be at pressure ≥ 2 simultaneously** — if a new arc would push the count above 4, the lowest-pressure existing arc is reduced by 1 (its pressure being demoted, not the arc being abandoned). Sim operations that involve pressure-weighted situation selection use only pressure ≥ 1 arcs.

### 10.6 Arc archive

Arcs in RESOLVED, ABANDONED, or FAILED states remain in the character sheet for narrative continuity. Reference NPCs, locations, and consequences may surface in future situations as callbacks. The narrator may reference past arcs in `context_continuity.key_callbacks` field of Narrator Payloads when scene relevance triggers.

---

## design_decisions

1. **Power use thresholds at 25/75/200/500/1200** chosen to pace mark-1 within months of regular use, mark-5 within ~8 years for active users — calibrated to bible's "10–20 years of practice within a tier."
2. **Cross-power category use unlocks (Section 1.4)** added to give "breadth-within-domain" a non-breakthrough path; bible mentions multi-domain users gradually developing capacities, but most growth requires breakthroughs. Marks 1 and 2 of category use formalize the gradual path.
3. **Eight breakthrough conditions** chosen (instead of the seven the spec asks for) to fully cover the bible's named catalysts (life-threat, sacrifice, mentorship, exposure, domain-crisis, loss, plus added near-death and ritual). Substance and ritual are added as distinct categories the bible implies (substance: psychedelic / drug onset cases; ritual: cultic and contractual practices in Pine Barrens / Throne).
4. **24 breakthrough marks** total (4 per category × 6 categories + 3 universal). Marks chosen to cover physical, mental, behavioral, and relational change types per spec requirement.
5. **Recovery period of 7 in-world days** with elevated condition tracks and "exposed" status — short enough to be playable, long enough to feel as a cost.
6. **Skill catalog: 32 skills** organized in 7 clusters. Coverage is deliberately broad, including non-combat (literacy, languages, agriculture, animal_handling) so non-combat play is mechanically dense.
7. **Skill use thresholds (5/20/60/150/350/750/1500/3000/7000/15000)** scale from "novice in a session" to "preeminent in a generation". Threshold inflation past 5 enforces deliberateness of advanced skill mastery.
8. **Skill prerequisites and synergies** explicitly tabled to make build planning legible.
9. **Faction standing mirror field added to Character Sheet** (Section 5.1): resolves the [NEEDS RESOLUTION] from character-creation.md Section 7.4. Mirror is updated on event; cross-validation against faction file required on save load. This is necessary to give the narrator faction context within the context budget.
10. **Resource categories: 7** matching the spec request. Maintenance/decay rates based on bible (scrip erosion, pharma stockpile aging) where given; provisional where not.
11. **Aging timeline by decade**: explicit attribute decrements at 30s/40s/50s/60s/70s/80s. Floors at d4. Death roll begins at 60. Calibrated against bible life expectancy table (regional avg 42; sovereign 62).
12. **Species aging variations** per species bible characteristics: Slow-Breath +10 years, Quick-Blooded -5, Silver-Hand strength accelerates (mineralization), etc.
13. **Death by old age** is a yearly probabilistic roll with modifiers; soft warnings at -3 margin and -1 margin give the player time to settle affairs.
14. **Continuation as descendant** is a soft option, not forced. Players who prefer fresh starts can decline and run a new Session Zero. The world continues either way.
15. **Inheritance: 60% of wealth, 100% of titled holdings (if named successor), 50% of standing/reach, 100% of negative heat**. Calibrated so descendants have meaningful continuity but are not freely inheriting position; faction realities and world ticks intervene.
16. **Corruption thresholds (1-2/3-4/5/6) marks** tied to bible's "touched / changed / transforming / transformed" per interface-spec.
17. **Corruption reversibility scale** mirrors bible's "has not been reversed in any observed case" — segments 1-2 reversible, 3-4 partial, 5 near-irreversible, 6 transformation. Reversal paths exist but are costly.
18. **Transformation at 6 is conversion, not death** — character continues in the world as a non-player entity. This preserves the bible's eldritch-population dynamics and produces narrative consequence rather than hard end.
19. **Arc cap: 4 arcs at pressure ≥ 2 simultaneously** — bounds the situation generator's load and forces the player to choose what their character is actively about, mirroring how lives have a few dominant pressures at any time.

## [NEEDS RESOLUTION]

- **[NEEDS RESOLUTION: power registry per-power mark-2 effects]** Section 1.2 mark 2 says "one new option appears in the power's effect parameters (per-power; defined in registry)" — every power needs its mark-2 effect defined in the registry data files.
- **[NEEDS RESOLUTION: registered substances list]** Section 2.1 condition 4 references "data/substances/" — the catalog of substance catalysts must be authored, including their categories, prerequisites, and resolution modifiers.
- **[NEEDS RESOLUTION: registered rituals list]** Section 2.1 condition 5 references "data/rituals/" — ritual specifications including participants, duration, type, and contract terms.
- **[NEEDS RESOLUTION: combat-spec.md skill check formula]** Section 3.3 references combat-spec for skill resolution; formula must match what combat-spec specifies. Provisional formula given.
- **[NEEDS RESOLUTION: integration combined-verb mechanics]** Section 1.4 mark 3 references combat-spec's combined-verb mechanic; specification must be aligned with combat-spec.
- **[NEEDS AUTHORSHIP: arc state machine data files]** Section 10.2 sketches selected arc state machines; full state machines for all 15 arc types must be authored in `data/arcs/`.
- **[NEEDS AUTHORSHIP: per-faction first-encounter table]** referenced from character-creation.md Section 5.2; authoring dependency.
- **[NEEDS AUTHORSHIP: pregnancy and species-variation childbirth]** Section 8.1 — species variations on pregnancy duration and complications not in bible.
- **[NEEDS AUTHORSHIP: title hereditary tags]** Section 8.5 specifies titles tagged "hereditary" inherit; the catalog of which titles are hereditary requires faction-by-faction authoring.
- **[CONTRADICTION: combat-spec.md does not yet exist as a sibling spec]** This document references combat-spec.md repeatedly. If combat-spec is a separate forthcoming document, alignment is pending; if it does not exist, the resolution rules in this document and character-creation.md become provisional pending its production.
