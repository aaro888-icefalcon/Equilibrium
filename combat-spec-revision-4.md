# Emergence Combat Spec — Revision 4

**Status.** Authoritative combat system reference for the T3-T5 vertical slice. Supersedes combat-spec.md, revisions 1-3, and all intervening analysis documents as the primary implementation target. Integrates all cumulative design decisions.

**Precedence.** Setting bible > `interface-spec.md` > this document > all prior artifacts. Where this document extends the interface spec, extensions are flagged in §2 (Schema Reconciliation).

**Audience.** Claude Code (implementation), content spec author (power authoring), narrator integration. Self-contained.

---

## 1. Overview

### 1.1 Scope

Vertical slice: T3 (novice functional power user) through T5 (late-middle tier). Single-player character; solo play with potential narrative-introduced allies. Deterministic Python resolution with Claude as narrator over structured state.

### 1.2 Design register

Grounded simulation in the lineage of Berserk, Kenshi, McCarthy. Tactical commitment matters; every turn is a real choice. Pool economy creates resource pressure. Postures force defensive commitment. Powers manifest with costs and consequences.

### 1.3 Non-goals

- Party play (one PC; NPC allies are ephemeral)
- Multi-attack action trains (PF2e MAP is out of scope; Quick chain exists as narrow exception)
- Reactive interrupts / readied actions (removed to simplify turn flow)
- Instant-kill save-or-die effects outside Finishers (narrative weight preserved)
- Real-time action resolution

### 1.4 Core loop

Each combat turn: actor declares posture state (persistent from prior turn unless changed); resolves 1 Major action + 1 Minor action + any free actions; opponents' armed posture riders apply passive effects to incoming events. End of round: statuses tick; exposure advances on trigger events; momentum accumulates.

---

## 2. Schema Reconciliation

This section lists divergences from current `interface-spec.md` that Rev 4 requires. Flagged for interface-spec update during Implementation Migration.

| Interface-spec current | Rev 4 required | Change |
|------------------------|----------------|--------|
| `Action.verb` enum: `Attack, Power, Assess, Maneuver, Parley, Disengage, Finisher, Defend` | `Attack, Power, Power_Minor, Assess, Maneuver, Parley, Finisher, Posture_Change, Brace, Utility` | Remove `Disengage` (absorbed into Reposition), `Defend` (replaced by passive posture + posture riders). Add `Power_Minor` (Minor-action casts), `Brace` (pool recovery), `Posture_Change`, `Utility` |
| Power categories: 7 (seventh placeholder) | 6 broads (Somatic, Cognitive, Material, Kinetic, Spatial, Paradoxic) with 5 subs each | Consolidation per taxonomy work; resolves placeholder |
| `Power.effect.type`: 5 values | Expanded to 13 effect families | See §14 |
| Status list: 7 (bleeding, stunned, shaken, burning, exposed, marked, corrupted) | Same 7 retained | No change; use existing closed list |
| No posture field | Add `current_posture` to Combatant (parry, block, dodge, aggressive) | New field |
| No armed_posture_riders | Add list (max 2) to Combatant | New field |
| No hidden binary flag | Add to Combatant | New field |
| Single pool_max | Add `base_pool_max` and `effective_pool_max` (computed) | Effective = base - armed_posture_rider count |
| No brace_uses_remaining | Add to Combatant | New counter |
| Combatant `scene_mode_uses` not present | Add (set of mode slot ids used this scene) | For scene cost tracking |

All other existing interface-spec schemas are preserved. Rev 4 integrates with existing `Encounter Spec`, `Combat Outcome`, `Narrator Payload`, `Character Sheet` structures.

[CONTRADICTION: interface-spec category count. Recommend accepting 6-broad consolidation. If bible requires 7 categories, remap our broads onto the 7 with the 7th absorbing Paradoxic/Eldritch specialization.]

---

## 3. Attributes and Dice

### 3.1 Attributes

Six attributes (from Character Sheet): `strength`, `agility`, `perception`, `will`, `insight`, `might`. Die sizes: d4, d6, d8, d10, d12.

Default character creation: 1 d10, 2 d8, 2 d6, 1 d4 (standard array) or point-buy equivalent.

### 3.2 Resolution procedure

**Dual-die sum vs TN.** Each verb-sub-type specifies Primary + Secondary attribute. Actor rolls both dice, sums. Outcome tier determined by margin.

```
roll = Primary_die + Secondary_die + modifiers
outcome:
  roll < TN - 1      -> Fail
  roll == TN - 1     -> Fail (Marginal Fail)
  roll == TN         -> Marginal Success
  TN < roll < TN + 5 -> Full Success
  roll >= TN + 5     -> Crit
  (both dice show max value regardless of sum) -> Crit (auto)
```

**Fumble:** if both dice show 1, outcome is Fail and actor is *exposed* (applies status).

### 3.3 Target Numbers (TN)

Base TN 10 for most actions. Variance by verb sub-type:
- Quick attack: TN 11
- Ranged: TN 10 close / 10 medium / 13 far
- Parry posture: TN 10 opposed roll
- Dodge posture: TN 10 opposed roll, all-or-nothing

Modifiers: +1 for Marked target, +2 for positional advantage, +2 for setup, -2 for cover, etc. Cap at +5 / -5 total modifier.

### 3.4 Outcome-parasitic riders

Riders that trigger on verb outcomes scale by tier: Full delivers full effect; Marginal delivers half (rounded down); Fail delivers nothing; Crit adds bonus effect. Pool cost is paid regardless of outcome.

---

## 4. Action Economy

### 4.1 Per-turn allocation

Each turn:
- **1 Major action** (required; skip allowed but wasteful)
- **1 Minor action** (required if available; skip allowed)
- **Free actions** (any quantity; no roll): quick perception check, inventory glance, brief verbal, posture declaration
- **Passive state**: current posture held; armed posture riders applying effects

### 4.2 Verb catalog

| Verb | Action cost | Sub-types | Notes |
|------|-------------|-----------|-------|
| Attack | Major | heavy, quick, ranged, grapple | §5 |
| Power | Major | cast_1, cast_2, cast_3, capstone | §13-14 |
| Power_Minor | Minor | one per power optionally | §14 |
| Assess | Major | full | §11 |
| Brief Assess | Minor (Utility) | — | §11 |
| Finisher | Major | table entries | §12 |
| Maneuver | Minor | reposition, disrupt, conceal | §7 |
| Parley | Minor | demand, taunt, disorient, destabilize, negotiate | §8 |
| Posture_Change | Minor | to any valid posture | §6 |
| Utility | Minor | aid, brief assess, verbal shout, interact object | §11.2 |
| Brace | Minor | — | §16 |

---

## 5. Attacks (Major)

### 5.1 Sub-types

**Heavy.** Primary: strength. Secondary: might. TN 10. On Marginal: deal weapon damage. On Full: weapon damage + 2. On Crit: double weapon damage + 1 exposure to target. On Fail: self becomes *exposed* (whiffed commitment).

**Quick.** Primary: agility. Secondary: perception. TN 11. On Marginal: deal weapon damage (light). On Full: deal weapon damage + optionally chain a second Quick attack at -2 modifier (same turn, same or adjacent target). On Crit: weapon damage + 1 status application. Chain cap 2; no third attack.

**Ranged.** Primary: perception. Secondary: agility. TN 10 (close, ≤5m), 10 (medium, ≤15m), 13 (far, ≤30m). On Marginal: weapon damage. On Full: weapon damage. On Crit: weapon damage + targeted hit (ignore one step of cover). On Fail: miss; no self-expose except on Fumble.

**Grapple.** Primary: strength. Secondary: agility. Contested against target's strength + might. On Full: apply `grappled` binary flag (both combatants; neither can Reposition until resolved). On Crit: grappled + target takes 1 damage. On Fail: nothing happens; target may counter-grapple.

### 5.2 Whiff and Fumble

- Fail on Heavy: self *exposed* 1 round.
- Fumble (both dice 1): self *exposed* regardless of attack sub-type; attack still doesn't connect.

### 5.3 Damage application

Weapon damage determined by `might`+weapon tier (T3 baseline: d8; T5 baseline: d10). Damage reduces target's `condition_tracks.physical` by 1 per 4 damage dealt (or similar scaling per math envelope). Zero physical track = incapacitated.

### 5.4 Attack-adjacent riders

Strike riders attach to attacks per power authoring. One strike rider per attack by default; see §9.3 for combination.

---

## 6. Postures

### 6.1 The four postures

Declared at combat init; changed via Minor Posture_Change action.

| Posture | Defensive mechanic | Tactical fit |
|---------|--------------------|--------------| 
| **Parry** | Roll per+agi vs incoming attack TN; on Full, negate and counter-step (+1 to next own attack). Requires weapon drawn. | Melee skillful defender |
| **Block** | Flat damage reduction: incoming damage -= (might_die // 2). Always applies. | Durable frontliner |
| **Dodge** | Roll agi+ins vs incoming attack TN; on Full, fully negate. On Fail, full damage. | Evasive, all-or-nothing |
| **Aggressive** | No defense roll; incoming attacks resolve as attacker rolls vs TN 10 with no defender response. +1 to own attacks. Cannot arm defensive posture riders. | Offensive commitment |

### 6.2 Posture-rider compatibility

Each posture rider specifies compatible postures (1-3 of 4). Aggressive posture permits only offensively-keyed posture riders (authored rarely). Posture change during combat re-declares armed riders (may arm/disarm); current pool not lost (caps at new effective max only when naturally spent below).

### 6.3 No-posture edge case

A combatant may elect no posture (explicit declaration or stunned/incapacitated). Without a posture, no defense applied; all posture riders disarmed.

---

## 7. Maneuvers (Minor)

### 7.1 Sub-types

**Reposition.** Primary: agility. Secondary: might. TN 10. Self-focused movement up to move speed. On Full: move + gain positional advantage (+2 to your or declared ally's next attack on declared target this round). On Crit: Full + may move through one occupied square or break grapple. Absorbs what was previously Disengage: a Reposition from within melee range incurs no opportunity attack (there are no opportunity attacks in Rev 4; movement is freely resolvable as Reposition).

**Disrupt.** Primary: strength. Secondary: insight. TN 10. Enemy-focused. On Full: target -2 to next defense roll this round. On Crit: target *exposed* 1 round.

**Conceal.** Primary: agility. Secondary: insight. TN 10. Self-focused. On Full: caster gains `hidden` binary flag. Attackers targeting caster suffer -2 to attack roll. Broken on: caster's next attack, caster's next Parley, caster being directly struck, caster declaring Aggressive posture. On Crit: Full + caster's next attack this round treated as surprise (+2 modifier, ignore one step of cover).

### 7.2 Hidden flag mechanics

Not a status (not in closed 7-list). Parallel to `grappled`. Boolean; either true or false. Has no duration in rounds — persists until broken by listed triggers. AI profiles track hidden as targeting modifier (§21).

---

## 8. Parley (Minor)

### 8.1 Sub-types

**Demand.** Primary: will. Secondary: might. Target must be social-register creature (most humans, some creatures, no eldritch). TN 10. On Full: target complies with reasonable demand or refuses clearly; on Crit: complies with broader scope or provides ancillary intel.

**Taunt.** Primary: will. Secondary: insight. TN 10. On Full: target *shaken* 1 round + taunter becomes preferred target for opportunist/aggressive AI. On Crit: Full + target loses next Minor.

**Disorient.** Primary: insight. Secondary: perception. TN 10. On Full: target -2 to next Major action. On Crit: target forfeits next Major (uses it on self-correction).

**Destabilize.** Primary: insight. Secondary: will. TN 12. On Full: roll on Unpredictable Action table (authored per encounter context; generally: target changes AI profile temporarily, targets ally, or hesitates). On Crit: roll with +2 bonus on table.

**Negotiate.** Primary: insight. Secondary: will. TN 10. Only available if `parley_available` in Encounter Spec. On Full: combat may end via negotiated terms (dictated by Encounter Spec parley conditions). On Crit: better terms (fewer concessions required).

### 8.2 Register gating

Combat register `human`: all 5 parley sub-types available.
Combat register `creature`: demand, taunt, disorient available; destabilize sometimes; negotiate rarely.
Combat register `eldritch`: disorient sometimes; others rarely or never. Parley against eldritch is typically narratively scripted rather than roll-resolved.

### 8.3 Parley-adjacent riders

Parley riders attach per power authoring. See §9.

---

## 9. Rider System

### 9.1 Rider slots

Every power has 3 rider slots. Each slot authored as one of 6 rider types:

| Type | Verb augmented | Typical cost |
|------|----------------|--------------|
| strike | Attack | 1 pool |
| posture | (passive while armed) | 0 pool per trigger; -1 pool max per armed |
| maneuver | Maneuver | 1 pool |
| parley | Parley | 1 pool |
| assess | Assess / Brief Assess | 1 pool |
| finisher | Finisher | 1 pool |

No enforced slot-type-to-slot-name mapping. Author decides per-power which slots are which rider types.

### 9.2 Same-sub-type duplication rule

Within a single power, if two rider slots target the same sub-type (e.g., two strike riders on Heavy), they must cover DIFFERENT sub-types. No redundant targeting. Specialized distributions provide breadth, not stacking.

### 9.3 Rider combination

Two riders of the SAME type (both strike, both maneuver, both parley, both assess, both finisher) may combine on a single action. Pool cost: sum of individual costs + 1 combination tax. Full effects of both apply. No cascading (max 2 combined). Posture riders do not combine (they're always-on passives; combination is moot).

Example: strike rider A (1 pool: +1 fire damage + *burning* on Crit) + strike rider B (1 pool: ignore cover step) combined = 3 pool total for +1 fire damage + *burning* on Crit + ignore cover step on the attack.

### 9.4 Rider restrictions (sub-type scope)

Riders restrict to sub-types via the `restrictions` field. Library distribution:

**Strike riders:** ~50% restricted to 1 attack sub-type; ~30% to 2; ~20% to 3; 0% to all 4.
**Maneuver riders:** ~50% to 1; ~30% to 2; ~20% to 3 (all three).
**Parley riders:** ~40% to 1; ~40% to 2; ~20% to 3+.
**Finisher riders:** typically unrestricted (finishers rare enough that restriction adds no value).
**Assess riders:** typically apply to both Major Assess and Brief Assess unless author specifies.

### 9.5 Outcome-parasitic default

All riders default to outcome-parasitic: effects scale with the underlying verb's outcome tier (Full = full effect; Marginal = half; Fail = none, cost paid; Crit = bonus effect).

---

## 10. Posture Riders (special case: pure passives)

### 10.1 Core rules

- **Always-on while armed.** No triggers, no per-event pool costs.
- **Up to 2 armed simultaneously** (from different powers).
- **Effects stack.** Each armed rider applies independently.
- **Cost: -1 effective pool max per armed rider.** `effective_pool_max = base_pool_max - count_armed_posture_riders`.
- **Posture compatibility:** each rider specifies compatible postures (1-3 of 4). Aggressive-compatible riders are offensive passives (rare; ~5% of library).

### 10.2 Sub-categories

Nine sub-categories for posture rider authoring:

| Sub-category | Typical effect |
|--------------|----------------|
| reactive_defense | -1 damage on incoming attacks |
| reactive_offense | 1 counter-damage on each hit taken |
| reactive_status | Attacker gains small status on each hit |
| periodic | +1 hp regen per round, or status decay |
| aura_ally | Allies within 5m +1 to attack rolls |
| aura_enemy | Enemies within 5m -1 to attack rolls |
| awareness | Detect nearby movement; immune to surprise |
| anchor | Immune to forced movement; +2 vs Disrupt |
| amplify | +1 damage on own Crits |

### 10.3 Effect calibration

Each posture rider calibrated to provide approximately 1-2 pool worth of value per typical 4-round combat. Effects outside this range trigger authoring audit.

### 10.4 Mid-combat re-arming

Posture change (Minor) re-declares armed riders. New armed set recomputes effective max. If current pool exceeds new effective max, pool is preserved temporarily (not lost); caps at new max only when naturally spent below.

### 10.5 Narration integration

Posture rider triggers require narrative surfacing. Narrator Payload for incoming attacks includes passive effect applications (rider names + effect magnitudes) so narration can briefly acknowledge ("her hide turns the blow," "her stillness absorbs it").

---

## 11. Assess and Utility

### 11.1 Major Assess

Primary: perception. Secondary: insight. TN 10. On Full: reveal one tactical fact about target (armaments, resistances, AI profile, exposure level, known motive, or current intent). On Crit: Full + apply *marked* 1 round. Narrative: combatant pauses to read.

### 11.2 Utility (Minor)

Catch-all Minor actions:
- **Brief Assess:** reveal one surface fact about target; TN 13 (harder because rushed). Apply *marked* only on Crit.
- **Aid:** grant an ally +1 to their next roll this round (touch range).
- **Verbal shout:** apply or remove *shaken* from ally (no target roll; auto).
- **Interact object:** pick up, drop, manipulate non-combat object; use environmental feature.

Utility sub-types can be combined under a single Utility action if thematically compatible (narrator judgment; engine default: one per use).

### 11.3 Brief Assess vs full Assess

Brief Assess is the fast, shallow information-gather; full Assess is the deliberate tactical read. Choose based on action economy needs: full Assess costs Major; Brief is Minor.

---

## 12. Finisher (Major, gated)

### 12.1 Gating

Finisher available when:
- Target has *exposed* status OR exposure_track ≥ exposure_max
- Caster has ≥5 momentum
- Target register allows (humans and creatures yes; eldritch only when explicitly gated per encounter)

### 12.2 Cost

- 5 momentum (consumed)
- Optional: Finisher rider pool cost

### 12.3 Resolution

Primary+Secondary per attack sub-type used (Heavy str+might by default; can be authored per power finisher). TN 10. On Full: consult Finisher Table. On Crit: Full + table entry shifts one step better.

### 12.4 Finisher Table

| Outcome | Effect |
|---------|--------|
| Decisive blow | Target loses 1d4 physical track immediately; incapacitation at 0 |
| Crippling wound | Target gains persistent Harm (Tier 2) |
| Execution | Target immediately dies / reaches 0 track |
| Forced surrender | Target surrenders if parley_conditions allow |
| Narrative-driven | Custom per encounter (breakthrough trigger, unique outcome) |

Specific entries authored per encounter; default: "Decisive blow" on Full, "Execution" on Crit (humans), "Crippling wound" on Crit (creatures/eldritch survivability).

### 12.5 Post-finisher

Momentum zeroed. Target exposure_track cleared or irrelevant. Finisher is a narrative beat; combat may end if last enemy defeated.

---

## 13. Power Mode Slots

### 13.1 Slot structure

Each power has 8 mode slots:

1-3. **cast_1, cast_2, cast_3** — three cast modes (Major, optionally one Minor per §14.5)
4. **capstone** — pick 1 of 2 authored options at unlock
5-7. **rider slots** — three slots; each any of the 6 rider types per §9
8. **enhanced_rider** — pick 1 of 3 base riders to enhance at unlock

### 13.2 Starting unlocks (asymmetric by pair role)

- **Primary** power starts with: cast_1, cast_2, and the most offensive rider slot unlocked
- **Complement** power starts with: cast_1 and the two most supportive/defensive rider slots unlocked

If the primary has multiple strike riders (specialized distribution), the unlock is the first listed (author designates order). Complement's unlocks follow similar author-designation rule.

### 13.3 Progression unlocks

Additional modes unlock via mark spending (§19). Typical order: remaining rider slots → cast_3 → capstone → enhanced rider.

---

## 14. Cast Modes

### 14.1 Cost structure

Per Math envelope:
- Cast modes: 1-3 pool variable. Target distribution: 35% uniform (2-2-2), 25% ascending (1-2-3), 10% spike-focused (1-1-3), varied remainder.
- Capstones: 4-6 pool.
- Minor casts (§14.5): 1 pool fixed.

### 14.2 Effect families (13 total)

1. **Damage** — direct harm
2. **Status** — apply closed-list status
3. **Movement** — teleport, force-move, mobility
4. **Information** — reveal, sense, detect
5. **Control** — compel action, redirect
6. **Resource** — pool gain, pool drain, recovery
7. **Defense** — damage reduction, barrier
8. **Utility** — non-combat or niche
9. **Meta** — affect other powers/mechanics
10. **Cost-shifted** — effect paid in condition/corruption/heat
11. **Action-economy** — extra action, action denial, delay
12. **Stat-alteration** — attribute boost, derived stat change
13. **Terrain-alteration** — zone, obstacle, transformation, destruction

Each cast mode authored as 1-3 families. Within a power, 3 cast modes span ≥2 families and ≥2 targeting scopes.

### 14.3 Targeting scopes

- self (caster only)
- ally (one ally, touch or close)
- touched (touch-range combatant, caster or adjacent)
- enemy_single (one enemy in range)
- enemy_group (2-4 enemies in area)
- zone (area effect terrain)
- all_visible (all combatants in range)

### 14.4 Differentiation rules

Three cast modes within a power differ in ≥2 dimensions (scope, family, range, duration, cost, posture-sensitivity). Three identical-family casts rejected.

### 14.5 Minor casts

~20-30% of powers author one of their cast modes as a Minor action.

- Pool cost: 1 (fixed)
- Effect scale: ~60% of standard
- Short duration (1-2 rounds)
- Typical use: self-buff, brief utility, small status application, short teleport

Minor cast and Major action (including another cast) may both be performed on same turn if pool allows. Pool economy self-limits.

### 14.6 Scene cost

~5-8% of casts library-wide. Flag in mode schema. Cost: 1-2 pool + `scene_mode_uses` flag set. Cannot reuse mode until scene ends. For signature once-per-combat effects.

### 14.7 Persistence limit

Each power may have at most 1 cast mode that creates persistent (multi-round) effects. Prevents tracking overhead.

### 14.8 Posture interaction

Default: casts posture-agnostic (~85%). ~15% of casts author posture-sensitive mechanics (cast-in-Aggressive +1, or cast-requires-Parry-weapon-drawn).

### 14.9 Rider interaction with casts

Default: riders do not attach to cast modes. Exception: ~10% of powers may author one rider that also extends to the power's own casts (e.g., strike rider's damage bonus also applies to damage-dealing cast). Author-explicit per power.

### 14.10 Status application and exploitation

- 40-50% of casts apply at least one status (on Full or Crit).
- 20-30% of casts scale with target's existing status (setup-exploitation).
- 10-15% do both.

---

## 15. Capstones and Enhanced Riders

### 15.1 Capstones

Each power authored with 2 capstone options. Player picks 1 at capstone unlock. Not re-selectable.

Capstone design rules:
- Cost 4-6 pool (may include condition/corruption/scene cost as additional).
- Two options represent thematic divergence, not pure magnitude scale.
- Each option peaks a different playstyle within power's supported playstyle set.
- Viability path: conditional_no_roll, offensive_swing, or setup_dependent (per math §1.7).

### 15.2 Enhanced riders

Each power authors 3 enhanced variants (one per base rider slot). Player picks 1 at enhanced rider unlock. Not re-selectable.

Enhancement types:
1. **Magnitude** — bigger number
2. **New dimension** — add effect type (damage → damage + status)
3. **Broadening** — wider applicability (melee-only → all melee + thrown)
4. **Chaining** — effect cascades or persists

Authoring: ≥2 of 3 variants must be type 2 (new dimension) or 3 (broadening). Pure-magnitude-across-all rejected.

### 15.3 Combination-enabler enhanced riders

5-8 enhanced riders library-wide authored as combination-enablers:
- Allow the enhanced rider to combine with ONE specific other rider type
- Combined pool cost ≥ 2; combined effect capped
- Creates targeted late-game synergy

---

## 16. Pool Economy and Brace

### 16.1 Pool formula

```
base_pool_max = 3 + tier
effective_pool_max = base_pool_max - count_armed_posture_riders
```

At T3: base 6, effective 4-6.
At T5: base 8, effective 6-8.

### 16.2 Pool decay and refill

Pool spent as modes/riders are activated. No per-turn regen. Pool refills to effective max at end of combat.

### 16.3 Brace action

Minor action. Rules:
- Gain 1 pool (cannot exceed effective_pool_max)
- Cap 3 uses per combat
- No roll (auto-succeed)
- Not usable while *stunned* or at 0 physical track

Brace extends sustained combat. Tank builds (2 armed posture riders, effective max 4) can Brace 3x for effective pool 7 over combat.

### 16.4 Additional pool-adjacent costs

- **Corruption:** gained from Paradoxic/Eldritch/Sympathetic powers; 0-6 scale on Character Sheet. Permanent until narrative removal.
- **Condition damage to self:** some high-impact casts/capstones cost 1-2 track damage.
- **Heat:** gained from visible power use; faction-mapped; out-of-combat consequence.
- **Scene cost:** binary flag per mode; resets at scene end.

### 16.5 Cost distribution by broad

- Somatic: 10-30% of casts carry phy cost
- Kinetic: 10-15% carry phy cost
- Cognitive: 15-20% carry men cost
- Paradoxic: 20-30% carry corruption
- Material, Spatial: minimal self-cost; pool primary

---

## 17. Statuses and Binary Flags

### 17.1 Closed status list (7)

Per interface-spec.md §Constants:
- `bleeding` — lose 1 physical track per round
- `stunned` — skip next Major action
- `shaken` — -2 to Parley, -1 to attack rolls
- `burning` — take 1 damage per round; extinguishable via specific actions
- `exposed` — +2 to attacker's rolls against exposed target; prerequisite for Finisher
- `marked` — +2 to next attack against marked target
- `corrupted` — influences Paradoxic power interactions; possible compulsion triggers

Statuses are stackable to intensity 2 (duration refresh; some effects intensify at stack 2).

### 17.2 Binary flags

Parallel to statuses but not in closed list:
- `grappled` — cannot Reposition; resolved via contested Grapple rolls
- `hidden` — -2 to attackers targeting this combatant; broken by caster's offensive actions

Binary flags have no duration in rounds; persist until trigger conditions break them.

### 17.3 Status duration

Default: 1 round. Apply mechanism per rider/cast authoring. Extended by stack refresh.

---

## 18. Damage, Harm Pools, and Exposure

### 18.1 Damage types

Six damage types (one per broad, mapping roughly to interface-spec's 7 categories after consolidation):
- `somatic` (biological/vital)
- `cognitive` (mental/psychic)
- `material` (matter/energy — fire, cold, acid, etc.)
- `kinetic` (physical force)
- `spatial` (spatial distortion, dislocation)
- `paradoxic` (eldritch, temporal, sympathetic)

Affinity table (per Combatant): damage type → vulnerable/neutral/resistant/immune/absorb. Default: neutral.

### 18.2 Condition tracks

Per Character Sheet: `condition_tracks.physical`, `.mental`, `.social` (0-5 segments). Damage reduces segments. At 0: incapacitated (physical) / dominated/broken (mental) / outcast/defeated-socially (social).

Scaling: damage typically 1-4 per attack at T3. Finisher damage 1d4+ directly to tracks.

### 18.3 Exposure track

Per Combatant: `exposure_track` (0 to `exposure_max`; T3 default 3, T5 default 5).

Triggers that increment exposure:
- Being hit by Crit (+1)
- Being *exposed* status applied (jumps to max, enables Finisher immediately)
- Specific power effects (some capstones fill exposure)

At exposure_max: *exposed* status auto-applied; remains until combat end or cleared.

### 18.4 Harm

Persistent consequences from combat. Scale:
- Tier 1: scene-long wound
- Tier 2: persistent until treated
- Tier 3: permanent or fatal

Harm applied from Finisher outcomes, severe Crit events, or narrative adjudication.

---

## 19. Progression: XP, Marks, Tiers

### 19.1 XP events (7 types)

- Scene completion (1 XP)
- Goal achievement (2 XP)
- Costly choice (1 XP)
- Discovery of significant information (1 XP)
- Relationship pivot (1 XP)
- Near-fatal experience (2 XP)
- Breakthrough moment (5 XP + tier-up trigger)

### 19.2 Marks

Conversion: 5 XP = 1 Mark.

### 19.3 Mark spends

- Unlock one power mode: 1 mark
- Capstone unlock (select 1 of 2): 2 marks
- Enhanced rider unlock (select 1 of 3): 2 marks
- Cross-broad splice (unlock a mode from a sub outside your power's broad): 3 marks + narrative gate

### 19.4 Tier advancement

Dual-gate: narrative breakthrough + mark threshold.

- T3 → T4: breakthrough event + 4 marks
- T4 → T5: breakthrough event + 6 marks

Breakthrough events are narrative: character transformation moment (mortal peril, profound revelation, corruption cascade, etc.). GM/sim layer triggers breakthrough; player cannot force.

### 19.5 Expected cadence

- T3 covers ~20 scenes of play
- T4 covers ~25 scenes
- T5 vertical slice endpoint

---

## 20. AI Profiles

### 20.1 The five profiles

**Aggressive.** Targets nearest visible combatant regardless of vulnerability. Prefers attack over maneuver. Rarely parleys. Will not flee unless at 1 track remaining. Ignores hidden targets when other visible targets exist.

**Defensive.** Prefers Block posture; values survival over kills. Will fall back to cover/position. Uses Disrupt to deny attackers. Parleys when feasible.

**Tactical.** Assesses before engaging. Targets exposed, marked, or vulnerable combatants preferentially. Uses combination of Maneuver + Attack. Reads player posture and adapts. Will push for Finisher when enemy exposure high.

**Opportunist.** Avoids direct engagement; strikes at weakened targets. Prefers ranged or reach. Flees at moderate harm. Targets isolated combatants.

**Pack.** Operates in groups of 2+. Coordinates attacks (flanking bonuses). Each individual is weaker; strength in number. Targets marked combatants to leverage pack focus.

### 20.2 AI handling of new mechanics

- **Hidden targets**: aggressive/pack AI targets nearest visible, ignores hidden while visible targets exist; tactical AI may attempt detection if power/ability permits; opportunist AI avoids hidden targets entirely.
- **Posture reading**: tactical AI adapts attack type vs posture (e.g., heavy attack less effective vs parry → uses quick or ranged).
- **Conceal reciprocal**: some enemy templates can Conceal themselves (per template `abilities` field).
- **Brace reciprocal**: enemies don't typically Brace (simpler AI); exceptional templates may.

---

## 21. Combat Flow

### 21.1 Initiative

Roll per combatant: perception + insight, sort descending. Ties broken by agility die. Determined at combat start; persists through combat.

### 21.2 Round structure

Per round, in initiative order:

```pseudocode
for combatant in initiative_order:
    if combatant.condition_tracks.physical <= 0: skip
    if combatant.has_status("stunned"): consume_status(); skip Major
    
    # Posture remains from prior turn unless changed
    # Armed posture riders active; passive effects ongoing
    
    # Free actions (any)
    combatant.do_free_actions()
    
    # Minor action (optional)
    combatant.declare_minor()
    if minor == "brace": apply_brace()
    elif minor == "posture_change": apply_posture_change(); recompute_effective_max()
    elif minor in ["maneuver_subtype", "parley_subtype", "utility", "power_minor"]:
        resolve(minor)
    
    # Major action (required unless incapacitated)
    combatant.declare_major()
    resolve(major)
    
# End of round
for combatant in initiative_order:
    tick_statuses(combatant)
    apply_periodic_posture_rider_effects(combatant)
    advance_exposure_from_events(combatant)
    check_zone_effects(combatant)
    
# Check combat end conditions
if win_conditions_met: end_combat("victory")
elif loss_conditions_met: end_combat("defeat")
elif parley_accepted: end_combat("parley")
elif escape_achieved: end_combat("escape")
else: next_round()
```

### 21.3 Incoming attack resolution

```pseudocode
def resolve_attack(attacker, target, attack_sub_type):
    # 1. Roll attacker
    roll = attacker.primary_die + attacker.secondary_die + attacker_mods
    
    # 2. Apply hidden modifier
    if target.hidden: roll -= 2
    
    # 3. Determine TN
    tn = base_tn_for_subtype + target_mods
    if target.posture == "parry" or target.posture == "dodge":
        # Defender rolls opposed
        defender_roll = target.primary_die + target.secondary_die + target_mods
        if target.posture == "dodge" and defender_roll >= tn:
            return "miss"  # all-or-nothing
        if target.posture == "parry" and defender_roll >= tn:
            return "parried"  # negated + counter-step
    elif target.posture == "aggressive":
        pass  # no defense roll; attacker vs TN 10 flat
    # target.posture == "block": attack resolves normally, damage reduced
    
    # 4. Outcome
    outcome = determine_outcome(roll, tn)
    
    # 5. Apply passive posture rider effects (auto)
    for rider in target.armed_posture_riders:
        apply_posture_rider_passive(rider, attack_event)
    
    # 6. Compute damage
    damage = attacker.weapon_damage + attack_subtype_bonus
    if target.posture == "block": damage -= target.might_die // 2
    damage -= sum(posture_rider_reductions(target))
    damage = max(0, damage)
    
    # 7. Apply
    target.condition_tracks.physical -= damage_to_track_conversion(damage)
    
    # 8. Handle Crit, status, exposure updates
    if outcome == "crit": advance_exposure(target); apply_crit_effects(attacker, target)
    
    # 9. Strike rider application
    if attacker.declared_strike_rider:
        apply_strike_rider(attacker.declared_strike_rider, attack_event, outcome)
    
    return outcome
```

### 21.4 Scene structure and boundaries

Scene boundaries detected by:
- **Explicit narrative shift** — GM/sim declares new scene (location change, time skip, major transition)
- **Combat end** — combat resolution + narrative beat = scene end
- **Downtime transition** — explicit rest / between-encounter scene

On scene end:
- `scene_mode_uses` clears for all combatants
- Pool refills to effective max
- Brace uses reset to 3
- Temporary statuses expire unless marked persistent
- Harm tier 1 heals; tier 2+ persists

Scene boundaries surfaced via Narrator Payload `scene_type: "transition"` or similar.

---

## 22. Narrator Integration

### 22.1 Payload augmentation

Per Narrator Payload schema (interface-spec §Narrator Payload), combat turns emit payloads with `scene_type: "combat_turn"`. Rev 4 additions to `state_snapshot`:

- `current_postures` (all combatants): for posture reading
- `armed_posture_riders` (all combatants): for rider trigger narration
- `hidden_combatants`: which are hidden
- `declared_action`: the action being narrated
- `outcome`: Fail/Marginal/Full/Crit
- `damage_applied`: numeric
- `statuses_changed`: list of applied/removed
- `passive_effects_triggered`: list of posture rider effects that applied

### 22.2 Register directives

Narrator register per combat register (`human`, `creature`, `eldritch`):
- human: tactical, grounded, personal stakes
- creature: visceral, bodily, predator-prey
- eldritch: dread-tinged, sensory-wrong, resist over-explanation

Aggressive posture narration: commitment language, exposure
Parry/Block/Dodge narration: technique, resistance, evasion
Brace narration: centering, gathering, breath

### 22.3 Forbidden

Narrator must not:
- Invent damage not in payload
- Describe posture riders that aren't armed
- Describe statuses not in snapshot
- Resolve the eldritch "what is this really" question (per setting bible)
- Narrate outcomes not in `outcome` field

---

## 23. Design Decisions (cumulative log)

1. **Verb catalog finalized**: 10 verbs (Attack, Power, Power_Minor, Assess, Finisher, Maneuver, Parley, Posture_Change, Utility, Brace). Disengage and Defend removed.
2. **Four postures**: Parry, Block, Dodge, Aggressive.
3. **Aggressive locks defensive posture riders**, permits rare offensive passives.
4. **Three maneuver sub-types**: Reposition, Disrupt, Conceal. Conceal introduces `hidden` binary flag.
5. **Five parley sub-types**: demand, taunt, disorient, destabilize, negotiate.
6. **Eight power mode slots**: 3 cast + 1 capstone + 3 rider + 1 enhanced.
7. **Six rider types**: strike, posture, maneuver, parley, assess, finisher.
8. **Three rider slots per power; any type per slot**; "no same sub-type twice" rule.
9. **Posture riders are pure passives** with pool max cost and full stacking.
10. **Up to 2 armed posture riders** simultaneously.
11. **Effective pool max = base - armed posture rider count.**
12. **Base pool = 3 + tier.**
13. **Brace action** recovers 1 pool (cap 3 per combat).
14. **Cast cost variable 1-3 pool.**
15. **Minor casts** permitted for ~20-30% of powers.
16. **Scene cost** as cost type (~5-8% of library).
17. **13 effect families** for casts.
18. **Rider combination**: sum + 1 pool tax, same-type only.
19. **Status list: closed 7** (per interface-spec).
20. **Binary flags**: grappled, hidden.
21. **XP/Marks/Tiers**: 5 XP = 1 mark; dual-gate tier-up.
22. **6 broads × 5 subs** taxonomy (consolidated from interface-spec's 7 categories; flagged).

---

## 24. Flagged for Implementation

**Schema updates needed in `interface-spec.md`:**
1. Action.verb enum
2. Combatant additions (posture, armed_posture_riders, hidden, effective_pool_max, brace_uses_remaining, scene_mode_uses)
3. Power content schema: support for 8-slot mode structure, rider type enum, sub-category enum for posture riders, action_cost field on modes, scene_use flag
4. Effect type enum expansion (5 → 13)
5. Power categories: 7 → 6 (or map 6 onto 7 + resolve placeholder)

**Gaps for future spec work:**
- Scene boundary detection refinement (narrator/engine coordination)
- HEXACO → broad mapping (character-gen spec)
- Starting pool offer algorithm (character-gen spec)
- Encounter-scaling formulas (enemy balancing at T3-T5)
- Unpredictable Action table entries (per encounter authored)

**Authoring dependencies:**
- Power content authoring (see Authoring Guidelines Rev 3)
- Enemy template authoring (separate spec)
- Scene/encounter authoring (simulation spec)
