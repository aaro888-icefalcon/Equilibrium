# Power Authoring Guidelines — Revision 3

**Purpose.** Binding authoring framework for the content spec author to stat up every power in `superpower-taxonomy-full.md` (200 powers). Integrates all cumulative decisions. Readable from-zero; `combat-spec-revision-4.md` is the companion mechanics reference.

**Precedence.** Setting bible > `interface-spec.md` > `combat-spec-revision-4.md` > this document > any prior authoring artifact.

**Scope.** Vertical slice target: T3-T5 tier, 60-100 powers authored from the 200-power taxonomy. Remaining powers stubbed or deferred.

---

## 1. Framing

### 1.1 What this document does

Defines the authoring process and constraints for power content. Any power authored must pass the audit procedures herein before inclusion in the library. The library's aggregate distribution must meet coverage targets specified here.

### 1.2 What this document doesn't do

- Does not define mechanics (see Rev 4)
- Does not define schemas (see `interface-spec.md`)
- Does not list the 200 powers (see `superpower-taxonomy-full.md`)
- Does not implement (Claude Code's job)

### 1.3 Core design principle

Power combat is not about picking the "right" power — it's about picking the right kit. Kit is the 2-power starting combo. Every combo must produce a coherent playstyle with identifiable strengths, weaknesses, and tactical loop. Individual powers are authored *so that their combinations work*, not as isolated units.

---

## 2. Playstyle Taxonomy

### 2.1 The 12 playstyles

Every kit (2-power combo) lands on 1-2 of these.

| # | Playstyle | Offensive profile | Defensive profile | Core loop |
|---|-----------|-------------------|-------------------|-----------|
| 1 | Melee Brawler | Heavy + grapple | Block posture; durable | Close distance, sustained pressure, tank hits |
| 2 | Skirmisher | Quick strikes + mobility | Dodge posture; phase | Hit-and-run, disengage, re-engage on favorable terms |
| 3 | Artillery | Ranged + area cast | Block/dodge from cover | Establish position, deliver damage across range |
| 4 | Controller | Status + save-or-suck | Ally-positioning-dependent | Debuff key enemies, enable next turn |
| 5 | Area Denier | AOE + zone control | Territorial anchor | Shape battlefield, force enemy concessions |
| 6 | Burst Caster | Big-cost high-damage casts | Posture rider between | Store pool, unleash, recover, repeat |
| 7 | Sustained Caster | Low-cost cast spam | Multiple defensive riders | Steady mid-damage, long-fight endurance |
| 8 | Tank/Juggernaut | Moderate melee | 2 armed posture riders | Draw focus, absorb, wear down |
| 9 | Support/Buffer | Ally-enabling, rare direct damage | Ally-adjacent for auras | Set up ally, exploit combo windows |
| 10 | Trickster | Unpredictable, variable-effect riders | Stance-shifting, illusion | Surprise play, probability manipulation |
| 11 | Assassin | High single-target burst with setup | Conceal + phase | Setup + spike, disappear |
| 12 | Hybrid | Attack AND cast within same turn | Flexible | Multi-tool — adapt to scene |

### 2.2 Diplomat emphasis (within Controller)

Previous analyses surfaced "Diplomat" as a potential 13th playstyle. Rev 3 decision: fold it into Controller with a Diplomat emphasis. Controllers using primarily parley riders (vs primarily status-application riders) express as Diplomats. Same playstyle category; different sub-expression.

### 2.3 Coverage requirement

Each of the 12 playstyles must be achievable via ≥3 distinct 2-power combos. Library audit verifies this before slice release.

### 2.4 Evolution paths

Player's character playstyle evolves T3 → T5 via:
- **Deepening** — unlock more modes in existing powers
- **Branching** — unlock complement's locked modes that reveal new capabilities
- **Peaking** — capstone commitment (2 options per capstone)
- **Grafting** — T5+ cross-broad splice (3 marks + narrative gate)

Authoring implication: each power's full 8-mode set should support multiple playstyle destinations.

---

## 3. Combo Identity Rules

### 3.1 Five identity rules (binding)

For any 2-power combo to be playable:

1. **Combined offensive profile clear.** Melee / ranged / caster / mixed — not all equally.
2. **Combined defensive profile clear.** One dominant posture for typical play.
3. **Mobility present.** Either a maneuver rider, a movement-oriented cast, or a mobility-class power (Spatial, Kinetic/Velocity, Somatic with flight).
4. **Setup/control present.** At least one mode applies a combat status or reveals information.
5. **Resource profile sustainable.** 4-round pool spend ≤ base pool + 2 (allowing for Brace and rider combinations).

### 3.2 Six cross-power interaction surfaces

Combo depth emerges from these surfaces. Library authoring must support all six with stated coverage:

**Surface 1: Status Exploitation Chain.**
Power A applies status → Power B's rider exploits it. Target library: ≥60% of powers apply a status somewhere; ≥50% have a mode or rider that checks for status.

**Surface 2: Setup → Spike.**
Power A creates setup → Power B's cast scales with it. Target library: ≥25% of powers have a setup-scaling cast mode.

**Surface 3: Defensive Counter-Attack.**
Power A's posture rider applies reactive effect → Power B's strike rider extends. Target library: each register (human/creature/eldritch) has ≥1-2 powers with counter-adjacent posture riders.

**Surface 4: Position-Shared Benefit.**
Power A repositions ally/self → Power B's mode benefits from adjacency/positioning. Target library: ≥15% of powers have adjacency-sensitive modes.

**Surface 5: Resource Trade.**
Power A costs condition/corruption/heat → Power B mitigates or exploits that cost. Target library: Paradoxic broad has ≥3 corruption-generating powers; ≥2 powers in other broads interact with corruption.

**Surface 6: Assess Synergy.**
Power A reveals info → Power B's mode uses revealed info. Target library: ≥10 powers include information-revealing cast or rider; ≥20 powers scale with information possession.

### 3.3 Three failure modes (binding rejection criteria)

Any power or combo exhibiting these is rejected and re-authored:

- **Redundant kit:** both powers do the same thing; no interaction surface possible.
- **Incoherent kit:** powers too disparate; no gameplay loop emerges.
- **Dead weight:** one power is always-optimal vs the other; the other's modes decay unused.

---

## 4. Per-Power Authoring Template

### 4.1 Eight mode slots

Each power has exactly 8 mode slots. Schema per Rev 4 §13:

1. **cast_1** — Major cast mode
2. **cast_2** — Major cast mode (or Minor, if authored)
3. **cast_3** — Major cast mode
4. **capstone** — 2 authored options; player picks 1 at unlock
5. **rider slot A** — any of 6 rider types
6. **rider slot B** — any of 6 rider types
7. **rider slot C** — any of 6 rider types
8. **enhanced_rider** — 3 variants authored (one per base rider); player picks 1 at unlock

### 4.2 Cast mode template

```yaml
cast_mode:
  slot_id: cast_1 | cast_2 | cast_3
  action_cost: major | minor
  pool_cost: 1-3 (regular); 4-6 (capstone); ≥1 with scene_use
  additional_cost:
    condition: phy | men | social (optional; typically 1)
    corruption: integer (typically 1, only for Paradoxic)
    heat: {faction_id: value} (if visible)
    scene_use: bool (default false)
  targeting_scope: self | ally | touched | enemy_single | enemy_group | zone | all_visible
  range_band: touch | close | medium | far | extreme
  duration: instant | 1_round | 2_3_rounds | scene | persistent
  effect_families: list of 1-3 of 13 families
  effect_description: one sentence
  effect_parameters: structured data (damage amount, status id, save TN, area, etc.)
  posture_sensitive: bool (default false; if true, specify compatible postures)
  supports_playstyle: list of 1-3 of 12 playstyles
  interaction_hook: brief note on what combos with this mode
  narrative_register: brief description for narrator integration
```

### 4.3 Cast mode authoring rules

**Rule 1 — Differentiation.** Within a power, 3 cast modes differ in ≥2 dimensions: scope, family, range, duration, cost, posture-sensitivity.

**Rule 2 — Family coverage.** 3 modes span ≥2 effect families.

**Rule 3 — Scope coverage.** 3 modes span ≥2 targeting scopes.

**Rule 4 — At least one reliable mode.** One of the 3 must be achievable-on-setup reliable (not pure high-stakes).

**Rule 5 — Persistence limit.** At most 1 persistent-duration cast per power.

**Rule 6 — Minor cast opt-in.** ~20-30% of powers author one cast mode as Minor (action_cost: minor, pool_cost: 1, effect scale ~60%).

**Rule 7 — Scene cost opt-in.** ~5-8% of cast modes library-wide carry scene_use.

**Rule 8 — Cost distribution within power.** Target mix: 35% uniform (2-2-2), 25% ascending (1-2-3), 10% spike-focused (1-1-3), varied remainder.

### 4.4 Rider template

```yaml
rider:
  slot_id: rider_a | rider_b | rider_c
  rider_type: strike | posture | maneuver | parley | assess | finisher
  sub_category: (only for posture riders)
  pool_cost: 1 (typical); 0 (posture riders — cost paid via effective pool max reduction)
  restrictions:
    attack_sub_types: list (for strike)
    maneuver_sub_types: list (for maneuver)
    parley_sub_types: list (for parley)
    postures: list (for posture)
  outcome_parasitic: bool (default true — scales with verb outcome)
  effect_description: one sentence
  effect_parameters:
    on_full: structured effect
    on_marginal: half effect (default) or authored
    on_crit: bonus effect
  supports_playstyle: list
  combo_enable: string or null — describes what combo surface this enables
```

### 4.5 Rider authoring rules

**Rule 1 — Dimension orthogonality.** 3 rider slots within a power affect different dimensions (damage, status, movement, defense, economy). Three damage riders is thin.

**Rule 2 — No same sub-type duplication.** Within one power, two riders targeting same sub-type rejected. Specialized distributions (e.g., 2 strike) must cover different sub-types.

**Rule 3 — Default restriction scope:**
- Strike: ~50% to 1 attack sub-type; ~30% to 2; ~20% to 3; 0% to 4.
- Maneuver: ~50% to 1; ~30% to 2; ~20% to 3 (all three).
- Parley: ~40% to 1; ~40% to 2; ~20% to 3+.

**Rule 4 — Outcome-parasitic default.** Effect scales with underlying verb outcome.

**Rule 5 — Posture riders as pure passives.** No triggers, no per-event pool cost. Cost paid via effective pool max reduction (-1 per armed).

**Rule 6 — Posture rider calibration.** Each posture rider provides ~1-2 pool worth of value per typical 4-round combat. Effects outside this range trigger audit.

**Rule 7 — Posture compatibility.** ~30% of posture riders compatible with all 3 defensive postures; ~45% with 2; ~25% with 1; ~5% Aggressive-keyed (offensive passives only).

### 4.6 Capstone template

```yaml
capstone:
  option_id: option_a | option_b
  pool_cost: 4-6
  additional_cost:
    condition: 1-3 phy typical
    corruption: 0-2 typical (only Paradoxic)
    scene_use: usually true for capstones
  character_signal: one-line description of what choosing this says
  viability_path: conditional_no_roll | offensive_swing | setup_dependent
  supports_playstyle: list of 1-2 playstyles (tighter than cast; capstone is a commitment)
  effect_description: one sentence
  effect_parameters: structured
```

### 4.7 Capstone authoring rules

**Rule 1 — Divergence.** 2 options represent thematic divergence, not linear "more damage." Each is a different answer to "what is this power at its peak?"

**Rule 2 — Playstyle peaks.** Option A and Option B peak *different* playstyles within the power's supported set.

**Rule 3 — Viability.** Each option takes one of three viability paths (no-roll / offensive swing / setup-dependent).

**Rule 4 — Character signal.** One-line description surfaces the choice weight at unlock.

### 4.8 Enhanced rider template

```yaml
enhanced_rider:
  enhancement_for: rider_a | rider_b | rider_c
  enhancement_type: magnitude | new_dimension | broadening | chaining
  playstyle_shift: reinforce | branch (does it deepen base playstyle or branch to new?)
  pool_cost: same as base rider
  effect_description: one sentence
  effect_parameters: delta from base
  combo_enable: string or null (if this enables a specific rider combination pair)
```

### 4.9 Enhanced rider authoring rules

**Rule 1 — Type distribution.** Across 3 variants, ≥2 must be type 2 (new_dimension) or 3 (broadening). All-magnitude rejected.

**Rule 2 — Playstyle shift tagged.** Specify whether enhancement reinforces or branches.

**Rule 3 — Combination enablers.** 5-8 enhanced riders library-wide authored as combination-enablers (combo_enable field non-null).

---

## 5. Library-Wide Distribution Targets

### 5.1 Rider type distribution (library-wide)

| Rider type | % of slots | ~count at 100 powers |
|-----------|-----------|---------------------|
| strike | 45% | 135 |
| posture | 28% | 84 |
| maneuver | 12% | 36 |
| parley | 9% | 27 |
| assess | 4% | 12 |
| finisher | 2% | 6 |

### 5.2 Per-power rider distribution patterns

| Pattern | Description | % of library |
|---------|-------------|--------------|
| Standard 1-1-1 | 1 strike + 1 posture + 1 maneuver | 55% |
| Offense-specialized | 2 strike + 1 posture | 15% |
| Defense-specialized | 1 strike + 2 posture | 10% |
| Mobility-specialized | 1 posture + 2 maneuver | 5% |
| Parley-shifted | 2 parley + 1 posture | 7% |
| Assess-shifted | 1 strike + 1 posture + 1 assess | 4% |
| Mixed exotic | 1 strike + 1 parley + 1 assess | 3% |
| Extreme specialist | 3 of one type | 1% |

### 5.3 Per-broad rider gravity

| Broad | Strike | Posture | Maneuver | Parley | Assess | Finisher |
|-------|--------|---------|----------|--------|--------|----------|
| Somatic | ~55% | ~35% | ~10% | — | — | — |
| Cognitive | ~25% | ~20% | ~5% | ~30% | ~15% | ~5% |
| Material | ~60% | ~30% | ~10% | — | — | — |
| Kinetic | ~50% | ~20% | ~25% | ~5% | — | — |
| Spatial | ~30% | ~20% | ~45% | — | ~5% | — |
| Paradoxic | ~30% | ~15% | ~15% | ~15% | ~15% | ~10% |

### 5.4 Posture rider sub-category distribution

| Sub-category | % of posture riders |
|--------------|---------------------|
| reactive_defense | 50% |
| reactive_offense | 15% |
| reactive_status | 10% |
| periodic | 10% |
| aura_ally | 5% |
| aura_enemy | 5% |
| awareness | 2% |
| anchor | 2% |
| amplify | 1% |

### 5.5 Cast cost distribution within a power

| Pattern | Distribution |
|---------|--------------|
| Uniform (2-2-2) | 35% |
| Ascending (1-2-3) | 25% |
| Descending (3-2-1) | 5% |
| Spike-focused (1-1-3) | 10% |
| Balanced-heavy (2-2-3) | 10% |
| Light-balanced (1-2-2) | 10% |
| Other | 5% |

### 5.6 Per-broad cast cost associations

| Broad | Typical self-cost |
|-------|-------------------|
| Somatic | 10-30% of casts: 1 phy damage |
| Kinetic | 10-15% of casts: 1 phy damage |
| Cognitive | 15-20%: 1 men damage |
| Material | Minimal self-cost; pool only |
| Spatial | Minimal self-cost; pool only |
| Paradoxic | 20-30%: 1 corruption |

### 5.7 Other distribution targets

- **Minor casts**: 20-30% of powers have one Minor-action cast
- **Scene cost casts**: 5-8% of casts library-wide
- **Posture-sensitive casts**: 15% of casts
- **Rider-on-cast extensions**: ~10% of powers
- **Persistent-duration casts**: max 1 per power (library-wide average: 30-40% of powers have one)

---

## 6. Playstyle Coverage Matrix

Each playstyle requires ≥3 combos. Target sample mappings (content spec author will expand):

| Playstyle | Combo 1 | Combo 2 | Combo 3 |
|-----------|---------|---------|---------|
| Melee Brawler | Claws + Regeneration | Fangs + Iron Skin | Pyrokinesis/Forge + Somatic Augmentation |
| Skirmisher | Super Speed + Blink Step | Wings + Phase | Kinetic Burst + Dodge Enhancement |
| Artillery | Pyrokinesis + Tremor Sense | Telekinesis + Precognition | Force Lance + Aura Sight |
| Controller | Mind Control + Dread Field | Compulsion + Command Voice | Psychometry + Taunt Aura |
| Area Denier | Pyrokinesis + Zone Anchor | Territorial + Elemental | Cryokinesis + Gravity Well |
| Burst Caster | Force Bolt + Flesh Knit | Psychic Lance + Vitality | Time Slow + Burst Damage |
| Sustained Caster | Electrokinesis + Pressure Read | Photonic + Endurance | Cold-touch + Awareness |
| Tank/Juggernaut | Iron Body + Armor Conjure | Regeneration + Anchor | Somatic/Vitality + Material/Transmutative |
| Support/Buffer | Rally Cry + Healing Touch | Aura of Protection + Shared Sight | Boons + Pact Empowerment |
| Trickster | Luck Field + Illusion | Probability Shift + Mirror Self | Unpredictable + Feint Master |
| Assassin | Invisibility + Time Slow | Shadow Step + Blink | Somatic/Predation + Cognitive/Perceptive |
| Hybrid | Force Strike + Telekinesis | Kinetic/Impact + Material/Elemental | Multi-family specialists |

---

## 7. Authoring Process

### 7.1 Per-power authoring steps

For each power authored:

**Step 1: Identify from taxonomy.**
Locate the power in `superpower-taxonomy-full.md`. Confirm broad, sub, and thematic register.

**Step 2: Determine broad + sub.**
Map broad to attribute pool per `gm-primer.md` domain mapping. Note: Somatic → biological_vital (phy); Cognitive → perceptual_mental (men); etc.

**Step 3: Assign pair role.**
Primary or complement. Primaries typically offensive-oriented; complements supportive/defensive. Some powers work well as either (mark as flex).

**Step 4: Select attributes.**
2 primary options + 2 secondary options per the broad's natural dice. Attribute pairing determines feel.

**Step 5: Identify supported playstyles.**
List 3-4 playstyles this power supports across its full mode set. Cast modes and riders will emphasize these.

**Step 6: Draft 3 cast modes.**
Apply cast mode template (§4.2) and rules (§4.3). Ensure differentiation, coverage, reliable mode present.

**Step 7: Draft 3 riders.**
Apply rider template (§4.4) and rules (§4.5). Determine rider type per slot. Respect no-same-sub-type rule.

**Step 8: Draft 2 capstone options.**
Apply capstone template (§4.6) and rules (§4.7). Two options diverge thematically.

**Step 9: Draft 3 enhanced rider variants.**
Apply enhanced rider template (§4.8) and rules (§4.9). At least 2 are dimension-expanding.

**Step 10: Tag every mode.**
`supports_playstyle` list per mode. `interaction_hook` for casts. `combo_enable` for riders.

**Step 11: Per-power audit.**
Run audit checklist (§8.1).

**Step 12: Commit to library registry.**

### 7.2 Authoring order across library

Given 60-100 power vertical slice target, author in passes:

**Pass 1 (30 powers):** one primary + one complement per sub-category × 15 sub-categories = 30 powers. Establishes baseline coverage.

**Pass 2 (30 powers):** fill distribution gaps; add specialists; build out strong broads (Cognitive, Material).

**Pass 3 (10-40 powers):** gap-fill to targets. Verify combos land correctly. Audit library-wide.

**Checkpoint audits:** after each pass, run library-wide audit (§8.3).

---

## 8. Audit Procedures

### 8.1 Per-power audit checklist

Before committing a power to registry, verify:

- [ ] Power id and taxonomy location documented
- [ ] Pair role assigned (primary / complement / flex)
- [ ] Attributes assigned per broad
- [ ] Supports_playstyle list (3-4 playstyles across full mode set)
- [ ] 3 cast modes pass differentiation (≥2 dimensions different)
- [ ] 3 cast modes pass coverage (≥2 families, ≥2 scopes)
- [ ] At least 1 reliable cast mode
- [ ] ≤1 persistent cast mode
- [ ] Cost-effect scaling within envelope (Rev 4 §14.1)
- [ ] 3 riders pass dimension orthogonality
- [ ] No same-sub-type duplication within power
- [ ] Rider restriction distribution reasonable
- [ ] 2 capstone options diverge thematically, peak different playstyles
- [ ] 3 enhanced rider variants; ≥2 type 2/3
- [ ] Every mode tagged with supports_playstyle
- [ ] Interaction hooks noted for casts
- [ ] Combo_enable noted for riders (null if none)
- [ ] Narrative register note for narrator

### 8.2 Per-combo audit (archetype-pair sampling)

Test 3 sample combos per 8×8 archetype pair matrix = 192 audits minimum.

For each combo:
- [ ] Offensive profile identified (melee / ranged / caster / mixed)
- [ ] Defensive profile identified (dominant posture)
- [ ] Mobility option present
- [ ] Setup/control option present
- [ ] 4-round pool spend ≤ base pool + 2
- [ ] ≥1 cross-power interaction surface active
- [ ] Playstyle identified from the 12
- [ ] No failure mode (redundant / incoherent / dead weight)

Failed combos trigger power-level or library-level revision.

### 8.3 Library-wide audit

After each authoring pass, verify against targets:

- [ ] Rider distribution within ±3% of target per type
- [ ] Per-broad distribution within expected ranges
- [ ] Posture rider sub-categories within ±3% of target
- [ ] 12 playstyles each achievable via ≥3 combos
- [ ] 8 archetypes each supported by ≥8 powers
- [ ] 6 cross-power interaction surfaces each active in ≥10 combos
- [ ] Combo failure rate ≤5% of plausible combos
- [ ] Minor casts: 20-30% of powers
- [ ] Scene cost casts: 5-8%
- [ ] Enhanced rider combination-enablers: 5-8 total

Any criterion failed triggers additional authoring or revision before slice release.

---

## 9. Worked Exemplars

### 9.1 Exemplar 1: Pyrokinesis + Tremor Sense (Artillery)

**Pyrokinesis** (Material/Elemental, primary role)

| Slot | Content |
|------|---------|
| cast_1 "Lance" | Major, 2 pool; ranged enemy_single, far; damage + *burning* on Crit |
| cast_2 "Bloom" | Major, 3 pool; ranged enemy_group, medium (3-tile area); damage + *burning* on Marginal+ |
| cast_3 "Forge" | Major, 2 pool; self scope, touch; weapon-enhance for scene (+1 damage) |
| capstone option A "Conflagration" | Major, 5 pool + 1 phy + scene_use; enemy_group all-visible close; massive damage; zone persists 2r |
| capstone option B "Crucible" | Major, 4 pool + 1 phy + 1 corruption; self; temporary Aggressive posture with +2 attack for 3r |
| rider_a strike | +1 fire damage; *burning* on Crit; applies to heavy+quick+grapple |
| rider_b posture (reactive_defense) | -1 incoming fire damage; -2 from matching-element attacks; compatible with Parry, Block |
| rider_c maneuver | Reposition leaves 1m trail of burning for 1r (environmental *burning* application) |
| enhanced_rider option 1 (type: broadening) | Strike rider now works on ranged attacks; fire damage includes ranged |
| enhanced_rider option 2 (type: new_dimension) | Posture rider adds counter-damage: attackers take 1 fire damage per hit |
| enhanced_rider option 3 (type: chaining) | Maneuver rider's fire trail extends to 2r and persists 2 rounds |

**Supports playstyles:** Artillery, Area Denier, Sustained Caster

**Tremor Sense** (Cognitive/Perceptive, complement role)

| Slot | Content |
|------|---------|
| cast_1 "Tremor" | Major, 2 pool; zone, medium (20m radius); reveal all movement + *marked* applied to detected, 3r duration |
| cast_2 "Pulse" | Major, 2 pool; enemy_single, medium; *marked* 1r + foreknowledge (reveal next action) |
| cast_3 "Ripple" | Minor (!), 1 pool; self, touch; next attack ignores one step of cover |
| capstone option A "Earth-Read" | Major, 4 pool + scene_use; zone all_visible; reveals all combatants, their intents, weakness |
| capstone option B "Harmonic" | Major, 5 pool + 1 men; self; all your rolls +2 this scene |
| rider_a strike | Attacks on detected-via-Tremor targets ignore cover step |
| rider_b posture (awareness) | Detect nearby movement (10m); immune to surprise; compatible with all 3 defensive postures |
| rider_c maneuver | Reposition grants +2 to next ally/self attack on declared target |
| enhanced_rider option 1 (type: broadening) | Awareness extends to 20m |
| enhanced_rider option 2 (type: new_dimension) | Maneuver rider's bonus persists 2 rounds |
| enhanced_rider option 3 (type: chaining) | Reposition also applies *marked* to target on Full |

**Supports playstyles:** Artillery, Assassin, Controller (Investigator emphasis)

**Combo identity at T3:**

Primary Pyrokinesis unlocked: cast_1, cast_2, strike (rider_a).
Complement Tremor Sense unlocked: cast_1, posture (rider_b), maneuver (rider_c).

6 modes active. Playstyle: **Artillery** with awareness passive. Pool 6 (no armed posture rider initially; player may choose to arm Tremor Sense's posture rider at combat init → pool 5).

**Typical 4-round combat:**
- Turn 1: Posture = Block. Arm Tremor Sense's posture rider (awareness). Effective pool 5. Cast Tremor (2). Pool 3.
- Turn 2: Quick attack + strike rider on marked target (1). Pool 2.
- Turn 3: Cast Bloom (3). Pool -1 → problem. Actually: Brace (Minor, +1 to 3), then Cast Bloom. Pool 0.
- Turn 4: Attack + no rider. Or Brace, attack + strike. Pool 0.

Pool management tight. Shows trade-off of arming posture rider (awareness value vs -1 pool).

**Audit results:**
- Offensive profile: ranged-focused ✓
- Defensive profile: Block with awareness ✓
- Mobility: Reposition (base + rider) ✓
- Setup/control: Tremor (info + *marked*) ✓
- Pool ≤ base + 2: 7 vs 8 (ok with Brace) ✓
- 4 of 6 interaction surfaces active ✓
- Artillery playstyle clear ✓
- No failure mode ✓

Combo valid.

### 9.2 Exemplar 2: Dread Field + Command Voice (Controller, Diplomat)

**Dread Field** (Cognitive/Auratic, primary role)

| Slot | Content |
|------|---------|
| cast_1 "Aura" | Major, 2 pool; enemy_group, close (5m); all in range must save vs will+ins, fail → *shaken* 1r |
| cast_2 "Fix" | Major, 2 pool; enemy_single, medium; auto-effect on Full, target *shaken* 2r |
| cast_3 "Recognition" | Major, 2 pool + 1 men; self, scene duration; in scenes with 3+ enemies, +2 to all Parley rolls |
| capstone option A "Terror" | Major, 5 pool + scene_use; enemy_group all_visible; all enemies *shaken* 3r + must check to act (50% forfeit Major) |
| capstone option B "Dread-Binding" | Major, 4 pool + 1 men; enemy_single; target *shaken* scene + compelled to answer one demand truthfully |
| rider_a parley (parley rider) | On Full Parley (any sub-type): target also becomes *shaken* 1r |
| rider_b posture (aura_enemy) | Enemies within 5m suffer -1 to attack rolls; compatible with all 3 defensive postures |
| rider_c strike | Attacks on *shaken* targets: +2 damage |
| enhanced_rider option 1 (type: broadening) | Parley rider works on Disorient and Destabilize too |
| enhanced_rider option 2 (type: new_dimension) | Posture rider also applies *shaken* 1r to enemies who attack you |
| enhanced_rider option 3 (type: chaining) | Strike rider damage cascades: on Full hit against shaken target, nearby enemies also *shaken* 1r |

**Supports playstyles:** Controller (Diplomat emphasis), Area Denier, Support/Buffer

**Command Voice** (Cognitive/Dominant, complement role)

| Slot | Content |
|------|---------|
| cast_1 "Order" | Major, 2 pool; enemy_single, medium; target must save will+ins, fail → compelled to move 3m or drop weapon |
| cast_2 "Focus" | Minor (!), 1 pool; ally, close; ally's next action +2 roll |
| cast_3 "Silence" | Major, 3 pool + 1 men; enemy_single, medium; target *stunned* 1r on Full (high TN 13) |
| capstone option A "Imperator" | Major, 6 pool + scene_use; enemy_single; dominate for 3r (AI profile becomes ally) |
| capstone option B "Rallying Cry" | Major, 4 pool; ally all_visible; all allies +1 to attack/defense for 3r |
| rider_a parley (parley rider) | Demand gains +2 effect: on Full, target complies with larger-scope requests |
| rider_b posture (aura_ally) | Allies within 5m gain +1 to attack rolls; compatible with Parry, Block |
| rider_c posture (awareness) | Know intent of all visible combatants next turn; compatible with Parry, Block, Dodge |

**Supports playstyles:** Controller, Support/Buffer, Diplomat (Controller emphasis)

**Combo identity:**

Playstyle: **Controller** with **Diplomat emphasis**. Heavy parley + status application. Limited direct damage.

Combat loop: Aura cast (applies *shaken* group) → Demand (boosted by parley rider) → Attack on *shaken* enemies (boosted by strike rider) → repeat.

Pool management: 2 powers × 3 modes × 2 pool average = ~12 pool budget, pool 6. Player must alternate high-impact turns with setup turns. Brace augments.

4 of 6 interaction surfaces active (status exploitation dominant).

**Playstyle evolution:**

T3: Controller. Both cast_1s + parley riders.
T4: unlock Command Voice cast_2 (Focus, Minor cast) → plays more like Support.
T5: capstone unlock — Dread Field's "Terror" pushes Area Denier; or Command Voice's "Imperator" pushes pure Controller. Player choice.

### 9.3 Exemplar 3: Shadow Step + Blink (Assassin)

**Shadow Step** (Material/Radiant, primary role; some subs bridge Material/Spatial)

| Slot | Content |
|------|---------|
| cast_1 "Cloak" | Minor (!), 1 pool; self, 1r; *hidden* via Cloaking (breaks as hidden normally) |
| cast_2 "Shade" | Major, 2 pool; self, 2r; +2 to Conceal rolls this combat; enemies -1 to attack rolls against you |
| cast_3 "Phantom Strike" | Major, 3 pool; enemy_single, close; attack with +2 mod if caster hidden or target marked; damage +3 |
| capstone option A "Dissolve" | Major, 5 pool + 1 men; self, scene; near-invisible; hidden persists through parley; -3 to attack rolls against you |
| capstone option B "Shadow-Slay" | Major, 5 pool + scene_use; enemy_single; reveals caster + executes attack at +4 mod; on Crit enables Finisher immediately |
| rider_a strike | Attacks from hidden: +2 damage, +1 exposure to target; works on heavy + quick + ranged |
| rider_b posture (awareness) | Detect all hidden combatants (friend/foe) within 15m; compatible with all defensive |
| rider_c maneuver | Conceal grants +2 on the hiding roll + if successful, leave a decoy in current position for 1r |

**Blink** (Spatial/Translative, complement role)

| Slot | Content |
|------|---------|
| cast_1 "Step" | Minor (!), 1 pool; self, instant; teleport up to 5m |
| cast_2 "Trace" | Major, 2 pool; self, 3r; next 3 repositions are teleports (no ground traversal) |
| cast_3 "Return" | Major, 3 pool; self; teleport to previously occupied position, gain +2 to next attack from ambush |
| capstone option A "Riftwalk" | Major, 5 pool + scene_use; self, scene; each Minor action can include a 5m teleport (free movement) |
| capstone option B "Void-Step" | Major, 4 pool + 1 corruption; self; teleport 15m + apply *exposed* to one enemy on arrival |
| rider_a maneuver | Reposition becomes teleport; ignore terrain |
| rider_b posture (amplify own) | On own Crit, gain +3m of free teleport this turn; compatible with all |
| rider_c strike | Attacks after teleport in the same turn: +1 damage |

**Combo identity:**

Playstyle: **Assassin**. Conceal + teleport + burst damage from ambush.

Classic turn: Cast Cloak (Minor) → *hidden* → Blink (Step Minor alternately) in to range → attack with strike rider + phantom strike → *hidden* broken, but damage delivered.

High single-target burst; very fragile (no ward stack, low pool for sustained defense). Assassin playstyle explicit and mechanically supported.

Interaction surfaces: 5 of 6 active (position-shared, setup→spike, status exploitation, assess synergy, resource trade at T5 via corruption).

---

## 10. Content Authoring Plan (action items)

### 10.1 Vertical slice target

Author 60-100 powers from `superpower-taxonomy-full.md`. Remaining powers stubbed for post-slice expansion.

### 10.2 Prioritization

- **Primary-role powers first.** Offense drives combat more than support; prioritize 1 primary per sub-category.
- **Complement-role second.** After primary baseline, fill complement roster to enable combos.
- **Archetype coverage.** 8 archetypes (striker, controller, juggernaut, eradicator, shaper, weaver, healer, trickster) each supported by ≥8 powers.
- **Broad coverage.** ≥10 powers per broad for the slice.

### 10.3 Authoring schedule (suggested)

- Pass 1 (30 powers): primaries + key complements per sub-category
- Pass 2 (30 powers): specialists, exotic-rider powers, playstyle gaps
- Pass 3 (10-40 powers): library-wide audit gaps

Checkpoint audits between passes.

### 10.4 Session budget

Rough estimate: 2-3 hours per fully-authored power (8 modes + tagging + audit). At 60 powers: ~120-180 hours. Batchable across sessions.

Sample-first strategy: author 20 powers fully, validate playstyle emergence via combos, then batch-author remainder with confidence.

---

## 11. Appendix: Glossary

**Broads (6):** Somatic, Cognitive, Material, Kinetic, Spatial, Paradoxic.

**Sub-categories per broad (5 each):** see `superpower-taxonomy-full.md` for full list.

**Archetypes (8):** striker, controller, juggernaut, eradicator, shaper, weaver, healer, trickster.

**Playstyles (12):** Melee Brawler, Skirmisher, Artillery, Controller, Area Denier, Burst Caster, Sustained Caster, Tank/Juggernaut, Support/Buffer, Trickster, Assassin, Hybrid.

**Rider types (6):** strike, posture, maneuver, parley, assess, finisher.

**Posture rider sub-categories (9):** reactive_defense, reactive_offense, reactive_status, periodic, aura_ally, aura_enemy, awareness, anchor, amplify.

**Effect families (13):** damage, status, movement, information, control, resource, defense, utility, meta, cost_shifted, action_economy, stat_alteration, terrain_alteration.

**Postures (4):** parry, block, dodge, aggressive.

**Maneuver sub-types (3):** reposition, disrupt, conceal.

**Parley sub-types (5):** demand, taunt, disorient, destabilize, negotiate.

**Attack sub-types (4):** heavy, quick, ranged, grapple.

**Statuses (closed 7):** bleeding, stunned, shaken, burning, exposed, marked, corrupted.

**Binary flags (2):** grappled, hidden.

**Scopes (7):** self, ally, touched, enemy_single, enemy_group, zone, all_visible.

**Range bands (5):** touch, close, medium, far, extreme.

**Durations (5):** instant, 1_round, 2_3_rounds, scene, persistent.

---

## 12. Ready to Author

Content spec author may now begin authoring powers from `superpower-taxonomy-full.md`, one at a time, using the templates in §4 and the authoring process in §7. After every ~30 powers, run the library-wide audit in §8.3. Adjust subsequent authoring to close distribution gaps.

Flag any mechanical ambiguity to Rev 4 (§Flagged for Implementation) or this document (§Open Questions) for resolution before the slice closes.
