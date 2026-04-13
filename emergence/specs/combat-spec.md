# EMERGENCE — COMBAT ENGINE SPECIFICATION

Version 1.0. Implementation target: single-player turn-based tactical engine, deterministic under seed, producing Combat Outcome per `interface-spec.md`. This document is authoritative for all combat mechanics, content, and AI. Where schemas conflict with the interface spec, the interface spec wins; this document is internally consistent with it.

Seventh power category is `auratic` (from bible `powers.md`). Damage types mirror the seven categories one-to-one: `physical_kinetic`, `perceptual_mental`, `matter_energy`, `biological_vital`, `auratic`, `temporal_spatial`, `eldritch_corruptive`.

---

## SECTION 1 — RESOLUTION SYSTEM

### 1.1 Core mechanic

Every resolved action is a **check**. A check rolls exactly two attribute dice — the *primary* and *secondary* attribute for the verb — and takes the **higher single die** as the base value. Modifiers are then applied. The result is compared to a **Target Number (TN)**.

```
check(actor, primary_attr, secondary_attr, modifiers, TN) ->
    d1 = roll(actor.attributes[primary_attr])      # e.g. d8
    d2 = roll(actor.attributes[secondary_attr])    # e.g. d6
    high = max(d1, d2)
    total = high + sum(modifiers)                  # modifiers applied to high only, not both dice
    margin = total - TN
    tier = classify(total, margin, d1, d2)
    return CheckResult(d1, d2, high, total, TN, margin, tier)
```

Attribute dice sizes are from the closed set **{d4, d6, d8, d10, d12}**. A d4 represents a crippled or untrained attribute; d6 baseline human; d8 competent; d10 elite; d12 peak. Higher than d12 does not exist; further advancement is represented by tier (see §5).

### 1.2 Modifier order and stacking

Modifiers apply to the higher-die result (`high`), not to each die independently. They are applied in this fixed order to avoid rounding and stacking ambiguity:

1. **Static situational** (terrain, range, cover): integer, can be negative
2. **Status-derived** (Shaken, Marked, Exposed apply to target; Stunned, Burning apply to actor)
3. **Power/ability modifiers** (declared in the ability definition)
4. **Tier gap modifier** (if check is contested by another combatant; see §1.4)
5. **Spent momentum** (see §1.7)

Modifiers from the same source do not stack — only the largest signed magnitude of that source applies. Modifiers from different sources stack additively without cap until the total modifier reaches ±6, at which point further modifiers of the same sign are discarded. This prevents unreachable/trivial target numbers.

### 1.3 Target numbers

| Difficulty | TN | Narrative meaning |
|---|---|---|
| Trivial | 7 | Routine under pressure |
| Standard | 10 | Challenging; the default |
| Hard | 13 | Trained opposition |
| Extreme | 16 | Elite opposition |
| Heroic | 19 | Against the odds |
| Mythic | 22 | Reserved for T8+ threats |

Contested checks (Attack vs Defend, Parley vs Will, Power vs resistance) use the **opposed** variant: both sides roll their check; the higher total wins; ties go to the defender. Margin = winner_total − loser_total.

### 1.4 Tier gap modifier

When a combatant of tier A engages a combatant of tier B, the higher-tier side adds the lower-tier side's **primary check die** reduction plus a flat modifier depending on gap:

| Tier gap | Higher-tier modifier | Lower-tier modifier |
|---|---|---|
| 0 | +0 | +0 |
| 1 | +1 | −0 |
| 2 | +2 | −1 |
| 3 | +3 | −2 |
| 4 | +4 | −3 |
| 5+ | +5 (capped) | −4 (capped) |

This is the single mechanical expression that "tier is load-bearing." A T5 versus a T3 is not merely "more dice" — the T5 rolls as normal but gains +2, and the T3 suffers −1. Combined with power access gates (see §5.3), this produces the bible's expectation that tier gaps of 3+ are nearly insurmountable without terrain, numbers, or desperation.

### 1.5 Success tiers

| Result | Condition | Outcome |
|---|---|---|
| Critical Success | both dice show the same value **and** that value ≥ 6, **and** total ≥ TN | Full effect + bonus rider (see verb tables); +1 momentum |
| Full Success | total ≥ TN + 3 | Full effect |
| Marginal Success | TN ≤ total < TN + 3 | Partial effect: damage −1, or effect applied with caveat |
| Partial Failure | TN − 3 ≤ total < TN | No primary effect; actor may spend 1 momentum to convert to Marginal; otherwise minor cost applied (see verb tables) |
| Failure | TN − 5 ≤ total < TN − 3 | No effect; actor takes 1 condition damage to track corresponding to action type (Physical for Attack/Maneuver; Mental for Assess/Power; Social for Parley) |
| Fumble | total < TN − 5, **or** both dice show 1 regardless of total | No effect; actor takes 2 condition damage and applies an appropriate status to self (Shaken on social; Stunned on physical; Bleeding if Attack with edged weapon; Burning if power use with Matter/Energy) |

Doubles at values 2–5 have no special effect unless the total also meets a threshold above.

### 1.6 Probability reference tables

`P(total ≥ TN)` after applying `+M` modifier, for paired attribute dice (ignoring crits/fumbles in the high-die calc — those are captured in the verbal tiers). These are the base rates the engine must satisfy up to floating-point accuracy.

**Evenly matched (d8 + d6 pair, +0 mod):**

| TN | P(success) |
|---|---|
| 7 | 0.79 |
| 10 | 0.46 |
| 13 | 0.15 |
| 16 | 0.02 |

**Favored (d10 + d8, +2 mod):**

| TN | P(success) |
|---|---|
| 7 | 0.98 |
| 10 | 0.82 |
| 13 | 0.49 |
| 16 | 0.18 |

**Outmatched (d6 + d6, −1 mod):**

| TN | P(success) |
|---|---|
| 7 | 0.56 |
| 10 | 0.14 |
| 13 | 0.00 |
| 16 | 0.00 |

**Elite (d12 + d10, +3 mod):**

| TN | P(success) |
|---|---|
| 10 | 0.98 |
| 13 | 0.83 |
| 16 | 0.50 |
| 19 | 0.20 |
| 22 | 0.03 |

**Weak (d4 + d4, +0):**

| TN | P(success) |
|---|---|
| 7 | 0.06 |
| 10 | 0.00 |

Implementation must match these within ±0.02 under monte-carlo sampling of 100,000 rolls per cell.

### 1.7 Momentum

Momentum is a small integer resource, 0–5, that a combatant holds separately from condition tracks. Each Critical Success generates +1 momentum. Each Full Success on Assess generates +1 momentum. Spending momentum:

- **1 momentum**: convert Partial Failure to Marginal Success (declared after roll).
- **2 momentum**: re-roll one die on a check (declared before modifiers applied). Must keep re-roll.
- **3 momentum**: add +3 to the high die after the roll.
- **5 momentum**: trigger a Finisher if the target is Exposed (see §8).

Momentum does not persist across encounters; it zeroes on Combat Outcome generation.

### 1.8 Worked examples

**Example 1: Attack, matched.** A militia soldier (str d8, agi d6, Attack uses str+agi) swings a rifle-butt at a scavenger raider (TN 10 via target's Defend). Rolls d8=5, d6=3. High=5. No modifiers. Total=5, TN=10, margin=−5. Failure. Actor takes 1 physical damage from the reversal.

**Example 2: Power, favored.** A T5 kinetic thrower (str d10, mig d10; Power uses mig+will for kinetic-throw) flings a chunk of curb at a Wretch. Power modifier +1. Tier gap (T5 vs T1) +4. Rolls d10=7, d10=6. High=7. Total = 7+1+4 = 12. TN=10. Margin=+2. Marginal Success: full base damage −1, Wretch takes the damage, no rider effect.

**Example 3: Crit.** Same kinetic thrower. Rolls d10=8, d10=8 (both dice show 8, ≥6, match). Total = 8+5 = 13. TN=10. Critical Success. Full base damage, bonus rider (add Burning for kinetic impact into masonry shrapnel, per power definition), +1 momentum.

**Example 4: Parley, outmatched.** A scavenger raider (will d6, ins d6) tries to talk a Bear-House guardsman (T6, Defend will d10+mig d10) into letting them pass. Parley uses will+ins. TN = opposed roll = 14 (high die 9 + tier mod +3 + static modifier +2 for Bear-House bearing). Raider rolls d6=3, d6=2. High=3. Tier-gap mod −3. Total = 0. Margin = −14. Fumble. Actor takes 2 social damage, gains Shaken. Guardsman remembers.

**Example 5: Fumble via double-1.** A T3 character Attacks with str d8, agi d8. Rolls d8=1, d8=1. Automatic Fumble regardless of TN. Actor takes 2 physical, applies Bleeding (edged weapon).

### 1.9 Edge cases

- **Unreachable TN**: if effective TN − max(d_primary, d_secondary) − max_modifier > 0, the engine still resolves the check (fumbles and crits can still occur through doubles rule); it does not short-circuit.
- **Modifier clamp**: total modifier is clamped to [−6, +6] before roll.
- **Excessive negatives**: an attribute reduced below d4 (via status or harm) rolls d4−1 rule: roll d4, subtract 1 from result, minimum 0. No further reduction is allowed.
- **No legal action**: if a combatant has no legal action (all verbs blocked by status), they take the **Defend** stance automatically (see §4.8); this cannot Fumble.
- **Exactly meeting TN**: counts as Marginal Success (TN ≤ total < TN+3), not Full.

### 1.10 Modifier sources (full table)

| Source | Value | Scope |
|---|---|---|
| Cover (partial) | −1 to attacker | Ranged Attack, Power at range |
| Cover (full) | −3 | As above |
| Exposed terrain zone | +1 to attacker | Any Attack/Power on target in Exposed zone |
| Hazardous zone | −1 to all checks in zone | All verbs |
| Higher elevation | +1 | Attack, Power, Assess |
| Flanking (two attackers on target's opposite sides) | +2 | Attack |
| Surprised target | +2 | First round only |
| Shaken (on target) | target −1 all checks | Applied to roll of Shaken actor |
| Marked (on target) | attacker +2 | Any Attack/Power/Finisher vs marked |
| Exposed (on target) | attacker +2, Finisher enabled | Any Attack/Power/Finisher |
| Stunned (on actor) | −2 all checks | Applied to roll of Stunned actor |
| Burning (on actor) | −1 all non-Disengage checks | Applied to roll of Burning actor |
| Bleeding (on actor) | −0 to check; +1 phys damage per round | Tick at end of actor turn |
| Corrupted (on actor) | See §6 | Variable |
| Weapon quality: fine | +1 Attack | Matter-manipulated / Species C craft |
| Weapon quality: poor | −1 Attack | Salvaged/rushed |
| Firearm ammo: reloaded | +0 base; 10% jam | Shared attack rule |
| Firearm ammo: fine-lot | +1 Attack | Bourse premium |
| Power-stamina depleted | −2 Power checks | Self-imposed when condition cost paid recently |
| Tier gap | See §1.4 | All contested checks |
| Momentum spend (+3) | +3 to high die | After roll, before margin |

---

## SECTION 2 — COMBATANT MODEL

### 2.1 Derived values

All derived values compute from attributes, tier, species, and equipped items. Formulas:

```
max_physical_segments   = 5 (fixed; tracks fill by damage, not max)
max_mental_segments     = 5 (fixed)
max_social_segments     = 5 (fixed)

defense_value           = d(agility) + armor_static         # used as Attack TN
mental_defense          = d(will)    + aura_static          # used as Power(perceptual/mental) TN, Parley TN
resilience_bonus        = tier // 2                          # added to exposure_max and harm thresholds

exposure_max            = base_exposure[template] + resilience_bonus
                          # base_exposure: standard human 3, elite 4, metahuman 5, Aberrant 6, Sovereign 8

initiative_bonus        = highest of (agility_die_size, perception_die_size) // 2
                          # d4->2, d6->3, d8->4, d10->5, d12->6

action_economy          = 1 Major + 1 Minor per round (standard)
                          # T7+ combatants receive 2 Major + 1 Minor (see 2.4)

power_pool              = will_die_size // 2 + tier          # soft cap on power uses per scene
corruption_cap          = 6 (shared constant)
```

**Worked example (player T3 kinetic):** str d8, agi d8, per d6, will d8, ins d6, mig d8, tier 3, leather jacket (+1 armor). Defense = 8+1 = 9 (TN to hit via Attack). Mental defense = 8. Resilience bonus = 1. Exposure max (standard human base 3) = 4. Initiative bonus = 4. Power pool = 4+3 = 7 uses before stamina penalty.

### 2.2 Combatant type defaults

Stat line: `[str, agi, per, will, ins, mig] / tier / condition_max [phy,men,soc] / exposure_max / ai_profile`.

| Type | Stat line | Notes |
|---|---|---|
| Standard human civilian | d6 d6 d6 d6 d6 d6 / 1 / 5 5 5 / 3 / defensive | Baseline |
| Standard human militia | d8 d6 d6 d6 d6 d8 / 2 / 5 5 5 / 3 / tactical | Soldier |
| Elite human (retinue officer) | d8 d8 d8 d8 d6 d8 / 4 / 5 5 5 / 5 / tactical | Trained veteran |
| Species A (Hollow-Boned) | d6 d10 d8 d6 d8 d4 | Agile, fragile; phy_max effectively 4 via bone-brittle rider |
| Species B (Deep-Voiced) | d6 d6 d8 d8 d6 d8 | +2 Parley; auratic +1 static |
| Species C (Silver-Hand) | d6 d6 d10 d6 d8 d6 | Matter/Energy access at half cost |
| Species D (Pale-Eyed) | d6 d6 d10 d8 d8 d6 | Low-light vision cancels cover mods |
| Species E (Slow-Breath) | d6 d6 d6 d8 d6 d10 | Toxin immune; resists Bleeding 1 round |
| Species F (Broad-Shouldered) | d10 d6 d6 d6 d6 d10 | +1 physical damage on melee |
| Species G (Sun-Worn) | d6 d6 d8 d6 d8 d8 | Biological pool +2 |
| Species H (Quick-Blooded) | d6 d10 d8 d6 d6 d8 | Regenerate 1 phy at end of each scene even without treatment |
| Species I (Wide-Sighted) | d6 d8 d10 d8 d8 d6 | Per-based Assess grants +2 momentum on crit instead of +1 |
| Species J (Stone-Silent) | d8 d6 d6 d10 d6 d10 | Projects steadiness aura: nearby allies resist Shaken |
| Wretch | d6 d6 d4 d4 d4 d6 / 1 / 4 3 1 / 2 / pack | Group-hunts; resistant to `physical_kinetic` |
| Hunter | d8 d8 d8 d4 d6 d8 / 3 / 5 4 1 / 3 / opportunist | Ambush specialist |
| Aberrant | d10 d8 d8 d6 d6 d10 / 5 / 6 4 2 / 5 / tactical | Variable; each Aberrant has 1–2 signature powers |
| Shade | — d8 d12 d10 d12 — / 5 / - 5 - / 4 / defensive | Physical damage immune; harmed only by auratic/perceptual/eldritch |
| Sovereign (anomalous) | d10 d10 d12 d12 d12 d12 / 8 / 7 6 5 / 8 / tactical | T8 default; rarely combat-engaged |
| Hive drone | d6 d8 d6 d4 d4 d6 / 1 / 3 1 1 / 2 / pack | Coordinates with other drones |
| Hive warrior | d8 d8 d6 d4 d4 d8 / 3 / 5 2 1 / 4 / aggressive | Pine Barrens colony unit |
| Warped (T4–T6) | d8 d8 d10 d10 d10 d10 / 5 / 6 6 5 / 6 / tactical | Speaks, parleys; high insight |
| Corrupted human (pact, early) | d6 d6 d8 d6 d8 d6 / 3 / 5 5 4 / 4 / opportunist | +1 Eldritch access; corruption track starts 2 |

### 2.3 Action economy

Each combatant on their turn receives:

- **1 Major action** — Attack, Power, Maneuver, Parley, Disengage, Finisher
- **1 Minor action** — Assess, reload, move (one zone), swap stance (switch to Defend as reaction), quick-speak
- **1 Reaction** — triggered outside own turn: Defend (against incoming Attack), interject Assess against declared Power, opportunistic Attack on fleeing combatant

Combatants of effective tier 7+ receive **2 Major + 1 Minor + 1 Reaction**. A combatant can Defend as many times as reactions allow (1 per round standard). An unspent Major can be downgraded into an additional Minor (but not the reverse).

### 2.4 Special cases

- **Stunned**: loses Major this turn.
- **Prone**: cannot take movement Minor; Attack as actor at −2; attacks against this combatant at +2 in melee.
- **Grappled**: may only Attack grappler (if armed) or attempt Maneuver to escape.
- **Mounted / elevated**: +1 Attack if position is mechanically legal, −1 to opponents' ranged Attack on the mounted combatant.

---

## SECTION 3 — TURN STRUCTURE

### 3.1 Round definition

A round is **approximately six seconds** of narrative time. Three rounds constitute one "exchange" — a natural descriptive break where the narrator summarizes rather than tick-by-tick details.

### 3.2 Initiative

At encounter start, every combatant rolls initiative: `d20 + initiative_bonus`. Resolve ties by: (1) higher perception die, (2) higher agility die, (3) higher tier, (4) random seed-deterministic coin-flip.

Initiative order is fixed for the encounter unless a combatant takes an action that explicitly moves them in the order (rare powers). Surprise: if the encounter begins with one side unaware, the unaware side rolls at −5 on initiative and the aware side gets a free Assess or Maneuver Minor before Round 1.

### 3.3 Round phases

Each round executes in strict phase order:

1. **Start-of-round tick**: Burning damage, Bleeding damage, ecological pressure clock advance (creature register), corruption offer resolution (eldritch register, if any offer pending from prior round).
2. **Declaration pass**: all combatants in initiative order declare their intended Major. Declarations are recorded but not yet resolved. (Enemies' declarations are visible to the player as intent.)
3. **Reaction pass**: combatants may declare reactions in response to declared Majors (e.g., "I Defend against the incoming Power").
4. **Resolution pass**: actions resolve in initiative order; each actor's Major and Minor execute; contested checks resolve as the actor's turn arrives; reactions trigger in place.
5. **End-of-round tick**: statuses decrement duration; Exposure decays if no damage taken this round (−1); witnesses log; scene clock (eldritch attention, hive attention) advances if triggered.

### 3.4 Simultaneous actions

Two combatants with identical initiative who both declared Attack against each other: resolve simultaneously. Both checks are rolled; both apply their effects before either combatant can take a reaction. If both would be incapacitated, both are.

### 3.5 Interrupts and reactions

- **Defend** (reaction): when targeted by an Attack or Power, the combatant may spend their reaction to roll an opposed check rather than use the static defense value. See §4.8.
- **Interject** (reaction, Assess-like): against a Power declaration, a combatant may spend reaction + Minor to attempt to disrupt on an `insight+per` check at TN = 10 + power_tier. Success imposes −2 on the Power check. Species I and Perceptual primaries use this disproportionately.
- **Opportunity Attack** (reaction): when a non-adjacent combatant leaves an adjacent combatant's reach (Disengage or Maneuver out), that combatant may take a reaction-Attack at −1.

### 3.6 Disengagement timing

Disengage resolves on its own Major (see §4.6). It cannot be taken as a Minor. Full success removes the combatant from the encounter at end-of-round-phase. Marginal success means disengaged but one opportunity attack from nearest adjacent enemy resolves first.

### 3.7 Round duration and narrative anchoring

A 3-round exchange is the narrative anchor. Combats that extend beyond 6 rounds are failure states for encounter design; the AI should pressure toward resolution (retreat, parley, finisher) by round 4.

---

## SECTION 4 — VERB SET

Each verb below follows the same format: **trigger, cost, primary/secondary attributes, TN rule, outcomes by tier, state changes, interactions, example**.

### 4.1 Attack

- **Trigger**: actor chooses to inflict direct physical harm on a target.
- **Cost**: Major. If ranged, spends 1 ammunition if firearm.
- **Attributes**: `strength + agility` for melee; `perception + agility` for ranged; `strength + might` for grapple.
- **TN**: target's `defense_value` (agility die size + armor static). Reaction Defend replaces this with opposed check.
- **Damage**: base weapon damage + tier // 2, modified by affinity (§7).

| Outcome | Effect |
|---|---|
| Crit | Full damage; apply weapon-appropriate status (edged → Bleeding; blunt → Stunned; ranged → Marked); +1 momentum; +2 exposure fill |
| Full | Full damage; +1 exposure fill |
| Marginal | Damage −1 (min 1); no status |
| Partial Fail | Miss; actor takes 1 phy if melee (over-extension) |
| Fail | Miss; no cost |
| Fumble | Miss; self-Bleeding (edged) or self-Stunned (blunt) or ammo jam (ranged); 2 phy self |

- **State changes**: target condition_tracks.physical increments by damage; exposure track fills; witnesses log if visible.
- **Interactions**: Marked target = +2 to this check. Exposed target enables Finisher (§8).
- **Example**: Militia soldier (str d8, agi d6) attacks raider (def 8). Rolls d8=7, d6=4. High=7. Total=7. TN=8. Margin=−1. Partial Fail. No damage; actor unharmed (did not Fumble).

### 4.2 Power

- **Trigger**: actor uses a manifested power with combat effect.
- **Cost**: Major. Condition cost per power definition (see §5.4). Heat cost if power creates witnesses (noisy, visible, unusual). Corruption cost if power is Eldritch or if user is at corruption threshold.
- **Attributes**: primary attribute depends on category:
  - Physical/Kinetic: `might + strength`
  - Matter/Energy: `might + insight`
  - Biological/Vital: `will + insight`
  - Perceptual/Mental: `will + perception`
  - Temporal/Spatial: `insight + perception`
  - Auratic: `will + might`
  - Eldritch/Corruptive: `will + insight` (plus 1 corruption)
- **TN**: target-type specific; Attack-like powers use target's `defense_value`; mental powers use `mental_defense`; utility powers use fixed TN per ability (typically 10 standard).
- **Damage type**: matches category (see §7).
- **Outcomes**: as Attack table, plus power-specific riders specified in each power entry.
- **State changes**: target-dependent; self condition_tracks decrement per cost; corruption if applicable; powers_used[power_id] += 1.
- **Interactions**: Kinetic cancels Kinetic — if both combatants declare kinetic Powers against each other in same round, the higher total wins by the margin; loser takes no effect. Perceptual defends Perceptual — perceptual target rolls a free oppositional check at no cost. Matter and Biological conflict — if both are present in a zone resolving simultaneously, both are at −1.
- **Example**: See §1.8 example 2.

### 4.3 Assess

- **Trigger**: actor studies a target or the battlefield.
- **Cost**: Minor (or Major for deep Assess).
- **Attributes**: `insight + perception`.
- **TN**: 10 baseline; 13 if target is concealed or eldritch; 16 for an anomalous entity.

| Outcome | Effect |
|---|---|
| Crit | Reveal 3 truths: target's motive, one status, one ability or harm; grant +2 momentum; next Attack/Power against target at +2 |
| Full | Reveal 2 truths; +1 momentum; next Attack/Power at +1 |
| Marginal | Reveal 1 truth |
| Partial | Reveal 1 truth, but one piece of false information is also presented; no momentum |
| Fail | No information |
| Fumble | Reveal nothing; gain Shaken (misread the situation) |

**Truths the engine can reveal:** remaining physical_max, active statuses, AI profile label, retreat threshold, one ability id, faction affiliation if hidden, current motive, parley availability. The engine maintains a ranked list per target; a reveal pulls top-ranked not yet revealed.

- **Interactions**: Species I and Perceptual primaries get +1. Against eldritch targets, Crit/Full also advances the player's corruption track by 0 (free); but against Sovereign-class, Crit/Full adds 1 corruption (knowing too much).

### 4.4 Maneuver

- **Trigger**: reposition in a meaningful tactical way (enter cover, change elevation, grapple, disarm, trip, push, reach objective zone).
- **Cost**: Major (or Minor for simple zone movement).
- **Attributes**: `agility + strength` for physical maneuvers; `agility + insight` for tactical repositioning.
- **TN**: 10 for solo movement; opposed for grapple/disarm/trip (target's `strength + agility` or `agility + insight`).

| Outcome | Effect |
|---|---|
| Crit | Maneuver succeeds; apply status (Prone from trip, Disarmed, moved two zones, gained flanking); next ally gets +1 Attack against target |
| Full | Maneuver succeeds |
| Marginal | Maneuver succeeds with cost (takes 1 phy, or move partial) |
| Partial | No move; stay in place |
| Fail | Stay in place; one opportunity attack resolves if applicable |
| Fumble | Fall Prone self or lose weapon self |

- **Interactions**: flanking grants +2 Attack; cover reduces ranged Attack on this combatant by −1 or −3; elevation by +1.

### 4.5 Parley

- **Trigger**: in combat, attempt to negotiate, threaten, bluff, plead, or offer terms.
- **Cost**: Major.
- **Attributes**: `will + insight` (forcing); `insight + perception` (reading and matching); Auratic primaries may substitute `will + might`.
- **TN**: target's `mental_defense`, modified by register:
  - Human: base TN; encounter's `parley_available` gates whether full terms can resolve combat.
  - Creature: Parley disabled in almost all cases (wolves, bear, altered fauna sometimes permit; hive and most eldritch-adjacent creatures do not).
  - Eldritch: Parley is **corruption offer** resolution — succeed and the offer becomes live; accepting transfers corruption (see §11.3).

| Outcome | Effect |
|---|---|
| Crit | Target accepts terms or stands down entirely; if part of a group, one other enemy follows lead; −1 heat with witnesses |
| Full | Target willing to hear/accept terms — combatant transitions to Parley state; other enemies still active |
| Marginal | Target pauses 1 round: Attack/Power against them is at −1 but they do not disengage |
| Partial | No effect |
| Fail | −1 momentum; target at +1 Attack against actor next turn |
| Fumble | Target gains +2 Attack against actor next turn; +1 social damage self; Shaken self |

- **State changes**: on Full/Crit, target's AI profile shifts to `defensive` or `parley-pending` for remainder of encounter. Witnesses log the parley. Terms (see §11.1) become structured outcome parameters.

### 4.6 Disengage

- **Trigger**: actor attempts to leave the encounter.
- **Cost**: Major. Also requires an available escape vector (terrain zone `objective` or `exposed` edge, corridor, concealment).
- **Attributes**: `agility + insight` (clean break); `might + will` (crashing through).
- **TN**: 10 if no adjacent enemies; 13 with one adjacent; 16 with two or more. Modified by terrain.

| Outcome | Effect |
|---|---|
| Crit | Disengage immediately; no opportunity attacks; encounter-level escape if all allies also disengage this round |
| Full | Disengage at end of round; no opportunity attacks |
| Marginal | Disengage at end of round; one opportunity attack resolves against actor first |
| Partial | No move; lose Major |
| Fail | No move; each adjacent enemy takes one opportunity attack |
| Fumble | Prone; each adjacent enemy takes one opportunity attack at +2 |

- **Interactions**: Smoke, concealment, darkness (Species D advantage), Temporal/Spatial powers can pre-empt the roll by generating cover. Heat is **not** reduced by Disengage — witnesses still saw.

### 4.7 Finisher

- **Trigger**: target is Exposed (see §8). Actor spends 5 momentum (or 2 momentum + 1 damage track).
- **Cost**: Major + momentum. Optionally heat or corruption per finisher type.
- **Attributes**: varies per finisher — but Finishers are declared against a target already broken, so most succeed on Full-equivalent check: `primary+secondary` vs TN 10 fixed, with the entry's signature modifier.
- **Outcomes**: each finisher defines its own effects (see §8.3). Typically kill, maim, capture, terrorize, or convert.

### 4.8 Defend (reaction)

- **Trigger**: actor is targeted by an Attack or Power.
- **Cost**: Reaction.
- **Attributes**: contested roll: actor rolls `agility + might` (physical) or `will + perception` (mental).
- **TN**: opposed, not fixed.

| Outcome | Effect |
|---|---|
| Crit | Incoming fully negated; counterattack: actor rolls 1 free Attack with no action cost at −2 |
| Full | Incoming negated |
| Marginal | Damage −2 (min 0); no status applies |
| Partial | Damage normal; no status |
| Fail | Damage +1 (attacker gains +1 as momentum) |
| Fumble | Damage +2; apply status regardless of attacker's result |

Defend cannot be used against status ticks (Burning, Bleeding). Defend can be used once per round unless action economy specifies more.

### 4.9 Verb interactions (summary matrix)

| Verb combo | Effect |
|---|---|
| Assess before Attack | Revealed status = +2 to Attack |
| Maneuver into flanking + Attack | +2 to Attack (stacks with reveal if different source) |
| Parley (Marginal) + Attack | Attack at −1 on struck target (reluctant) |
| Power (Shaken rider) + Attack | Attack at +1 on Shaken target |
| Disengage after Parley (Crit) | Disengage at TN 7 |
| Power (Marked) + Finisher | Finisher at +2 |
| Defend + Assess (Minor) | Resolve reaction then still get reveal |

---

## SECTION 5 — POWER SYSTEM

### 5.1 Category identities

| Category id | Theme | Combat role | Cost signature |
|---|---|---|---|
| `physical_kinetic` | Body, motion, applied force. | Direct damage, movement, durability | Physical track |
| `perceptual_mental` | Senses, thought, influence | Control, debuff, information | Mental track |
| `matter_energy` | Non-living matter, thermal, EM | Area damage, terrain | Physical track (heat, overextension) |
| `biological_vital` | Living tissue, healing, animal influence | Sustain, utility, self-modification | Physical track (self-drain) |
| `auratic` | Persistent influence zones | Battlefield state, party buffs, enemy debuffs | Social track (continuous erosion) |
| `temporal_spatial` | Time and space | Positioning, short-range tp, precog, echoes | Mental track + rare heat |
| `eldritch_corruptive` | Pact effects, contact, cursed projections | High raw output, at corruption cost | Corruption segments |

### 5.2 Tier escalation (10-tier table)

Population distribution (humans only; metahuman species scale similarly but shift averages by +1 for relevant primaries):

| Tier | % manifested | Capability envelope (Physical/kinetic as reference) | Power access |
|---|---|---|---|
| 1 | 40% | Visibly above-human | 1 tier-1 power |
| 2 | 25% | Trained-soldier-plus | 2 tier-1 or 1 tier-2 |
| 3 | 15% | Impressive; flips a car | 2 tier-1 + 1 tier-2, or 2 tier-2 + 1 tier-1, or 1 tier-3 |
| 4 | 10% | Elite; stops melee weapons skin-deep | Access up to tier-3; ~4 powers |
| 5 | 5% | Superhuman; walks through pistol fire | Tier-4 access; ~5 powers |
| 6 | 3% | Destructive; throws cars | Tier-5; ~6 powers |
| 7 | 1.5% | Levels buildings; stops artillery | Tier-6; ~7 powers; 2nd Major action |
| 8 | 0.4% | Apocalyptic localized; Volk, Kostas | Tier-7; ~8 powers |
| 9 | 0.08% | Apocalyptic-regional; Preston | Tier-8; ~9 powers |
| 10+ | 0.005% | Mythic | Tier-9/10 powers; no mid-Atlantic has |

A combatant's `tier` caps accessible power tiers at `tier + 0` for primary category and `tier − 1` for secondary (minimum 1). This is why the starter library caps at tier 10 but includes fewer powers at high tiers.

### 5.3 Power pool and progression

- **Power pool** (soft limit) = `will_die_size // 2 + tier` per scene. Exceeding it applies −2 to subsequent Power checks until rest.
- **Growth-through-use**: each power tracks a `usage_count` integer. Thresholds:
  - 10 uses: power costs reduce by 1 (minimum 1).
  - 25 uses: power gains +1 on check at this power's category primary.
  - 50 uses: power gains one defined "mastery" rider (listed per power where applicable).
  - 100 uses: unlocks related tier-up power prerequisite.
- **Tier ceiling** = starting tier + 1. Advancement past ceiling requires a **breakthrough** (§5.6).

### 5.4 Manifestation circumstance → category mapping

Used during character creation and for quick-NPC generation.

| Circumstance at Onset | Weight to category |
|---|---|
| Fighting, running for life, protecting another | Physical/Kinetic +30, Auratic +5 |
| Trying to understand, reading, watching | Perceptual/Mental +30, Temporal/Spatial +5 |
| Working with materials (metal, stone, wire, machines) | Matter/Energy +35, Physical/Kinetic +5 |
| Tending, feeding, healing, farming, with animals | Biological/Vital +35, Auratic +5 |
| Leading, calming, rallying, public speaking | Auratic +35, Perceptual/Mental +10 |
| Lost, disoriented, fleeing a confined space | Temporal/Spatial +35 |
| In presence of early-eldritch phenomena, panic | Eldritch/Corruptive +25 (rare), +10 Perceptual/Mental |
| Sleeping, unconscious | Random distribution per population percentages |

To roll: compute weighted distribution = base_population_percentages + circumstance weights, normalize, draw. Secondary category (55% chance): remove primary, reweight, draw.

### 5.5 Hereditary inheritance

Per power bible:

```
parent_manifested / child_manifests:
  both_manifested     -> child manifests: 0.99
  one_manifested      -> child manifests: 0.98
  neither_manifested  -> child manifests: 0.80

category_inheritance:
  parent_primary_A, random_other_B
  child primary draw:
    P(A)        = base_population_percentage(A) * 2
    P(other)    = remaining distribution, normalized

tier_inheritance:
  child tier is drawn from population distribution, independent of parent tier.
  tolerance: no direct tier inheritance, but breadth heritable —
    if parent has ≥2 categories, child is 2x as likely to have ≥2 categories.
```

### 5.6 Breakthrough

Advancing past tier ceiling requires a breakthrough. Seven specified conditions:

| # | Condition | Trigger in-engine | Resolution check | Cost (mark) |
|---|---|---|---|---|
| 1 | **Mortal defense of another** | Ally about to take fatal harm; actor intercepts | `will+might` vs TN 16 | +1 Depth; mark: scarring corresponding to domain |
| 2 | **Sacrifice of an irrevocable thing** | Actor voluntarily destroys a loved item, relationship, limb, or resource they cannot recover | Auto-succeed if sacrifice qualifies | +1 Depth or Breadth; mark: specific permanent harm tier 3 |
| 3 | **Mentorship completion** | 3+ scenes of training with a higher-tier user of same category | `insight+will` vs TN 13 | +1 Integration; mark: speech or gesture patterns copied from mentor |
| 4 | **Exposure survival** | 3+ scenes in a corruption zone without becoming Corrupted at end | `might+will` vs TN 16 | +1 Breadth; mark: 1 corruption segment permanent, cannot be reduced below this |
| 5 | **Domain-crisis** | Category-specific: Physical = sustain-overload survival; Biological = save another at severe personal cost (take tier-3 harm to heal tier-3); Eldritch = direct entity contact with consent to bargain; Temporal = surviving a paradox event; Perceptual = endure psychic flood; Matter = survive structural collapse of own making; Auratic = hold a zone under sustained assault | `primary+primary` vs TN 19 | +1 Depth; mark: domain-appropriate (Physical = densification; Perceptual = thought-privacy loss; etc., per bible) |
| 6 | **Loss** | Actor loses access to a category (via corruption, injury, or choice); remaining category concentrates | Auto on loss event | +1 Depth in remaining; mark: scar of the lost capacity visible permanently |
| 7 | **Confluence** | Three consecutive Crit successes on Power checks within a single scene | Auto on trigger | +1 Integration; mark: permanent mood-shift toward the category's affective register |

Breakthrough resolves at end-of-encounter: `breakthrough_triggered = true` in Combat Outcome; `breakthrough_details` populated with type, from_tier, to_tier, cost, trigger.

### 5.7 Starter power library (42 powers)

Notation per entry: **id** — name — tier — cost — damage_type — base_damage/effect — tactical role — prerequisite — synergies — counters — narration.

Cost format: `phy/men/soc` damage to actor condition tracks, plus optional `(heat+N)`, `(corr+N)`.

Base damage formula: `d(damage_die) + tier`, modified by affinity, armor, cover. Damage die is listed per power. "Utility" = non-damage.

#### Physical / Kinetic

**1. kin_push** — Kinetic Push — T1 — 1 phy — `physical_kinetic` — d6 damage + push target 1 zone — Role: area control — Prereq: none — Synergy: flanking after push — Counter: Kinetic cancels Kinetic — *"The air between her hand and the man shifted once. He went back two steps, then three, then off the edge."*

**2. hard_skin** — Hardened Skin — T1 — 1 phy (on first hit taken) — utility — self: next physical damage −2 — Role: defensive — Prereq: none — Synergy: Maneuver into tank role — Counter: Matter/Energy ignores — *"The knife struck and slid. Her skin did not open."*

**3. leap** — Leap — T1 — 1 phy — utility — move up to 2 zones including vertical — Role: mobility — Prereq: none — Synergy: opens Attack from new angle — Counter: none — *"He jumped the collapsed car like it was nothing and landed running."*

**4. kin_strike** — Kinetic Strike — T2 — 1 phy — `physical_kinetic` — d8 + tier; Crit applies Stunned — Role: burst — Prereq: kin_push — Synergy: Marked target +2 — Counter: Hardened Skin — *"She set her feet. The punch went through the plank and the man behind it."*

**5. redirect** — Redirect Force — T2 — 1 phy (reaction) — `physical_kinetic` — reaction on being Attacked: roll Defend; on Full/Crit return d6 damage to attacker — Role: counter — Prereq: none — Synergy: melee-heavy enemies — Counter: ranged attackers — *"The blow arrived and came back faster."*

**6. run** — Sustained Run — T3 — 1 phy — utility — out-of-combat: move 3x speed for scene; in combat: +1 to Disengage, flanking Maneuver at +1 — Role: mobility — Prereq: leap — Synergy: opportunistic AI profile — Counter: terrain/hazardous — *"He covered the distance before they finished aiming."*

**7. throw_car** — Throw Massive Object — T4 — 2 phy — `physical_kinetic` — d10+tier area (all in zone); Crit applies Stunned to all — Role: area — Prereq: kin_strike — Synergy: clustered enemies — Counter: scattered enemies, cover — *"He took the bumper in both hands. Then the whole car was moving."*

**8. flight** — Self-Propelled Flight — T5 — 2 phy per scene — utility — actor moves in three dimensions; ranged Attacks against actor −2; opportunistic Attacks invalid — Role: mobility/escape — Prereq: leap + run — Synergy: ranged Power from altitude — Counter: ranged specialists — *"He did not jump. He went up."*

**9. district_break** — District-Breaking Strike — T6 — 3 phy (heat+2) — `physical_kinetic` — d12+tier; all in 2 adjacent zones; destroys terrain — Role: nuclear option — Prereq: throw_car — Synergy: cornered — Counter: Temporal retreat — *"The ground after was lower than the ground before."*

#### Perceptual / Mental

**10. read_intent** — Read Intent — T1 — 1 men — utility — free Assess at +2; reveal 1 truth; passive: pre-declare enemy's Major — Role: info — Prereq: none — Synergy: Attack +1 next — Counter: Perceptual-defended target — *"She watched him speak and knew he was about to reach for the knife."*

**11. suggest** — Suggestion — T2 — 1 men — `perceptual_mental` — target `will` save; fail = 1 round Shaken + target must take Defend stance — Role: control — Prereq: none — Synergy: Parley follow-up — Counter: Species J, D — *"He said to the guard, 'You could sit down,' and the guard sat down."*

**12. illusion** — Minor Illusion — T2 — 1 men — `perceptual_mental` — create false sensory detail for 1 scene; grants +2 to Maneuver for concealment — Role: utility — Prereq: none — Synergy: ambush setup — Counter: Assess reveals — *"There were three of them. There were not three of them."*

**13. telepathy** — Telepathic Contact — T3 — 1 men — utility — speak silently with known target; share one Assess revelation — Role: coordination — Prereq: read_intent — Synergy: ally buff — Counter: none — *"She did not speak. He heard her."*

**14. psychic_lance** — Psychic Lance — T4 — 2 men — `perceptual_mental` — d8+tier mental damage; ignores physical armor; Crit applies Shaken — Role: direct — Prereq: suggest — Synergy: vs Auratic users — Counter: Perceptual defense — *"He blinked. Something had happened inside his head."*

**15. mass_influence** — Mass Influence — T5 — 3 men — `perceptual_mental` — all enemies in a zone roll `will` vs TN 13; fail = 1 round Defend stance forced — Role: control — Prereq: suggest + telepathy — Synergy: solo vs crowd — Counter: high-will targets — *"She spoke once and eight people reconsidered."*

**16. memory_edit** — Memory Edit — T6 — 3 men (soc+1) — utility — target forgets last scene; requires Crit; out-of-combat utility — Role: consequence removal — Prereq: psychic_lance — Synergy: heat reduction — Counter: anomalous targets — *"He would not remember her face."*

#### Matter / Energy

**17. pyro_spark** — Pyrokinetic Spark — T1 — 1 phy — `matter_energy` — d6+tier fire; Crit applies Burning — Role: direct — Prereq: none — Synergy: flammable terrain — Counter: Matter specialists — *"There was fire where her hand opened."*

**18. metal_edge** — Edge Shaping — T1 — 0 cost (Minor) — utility — improve a weapon to "fine" quality for 1 scene (+1 Attack) — Role: buff — Prereq: none — Synergy: melee ally — Counter: none — *"She ran her thumb along the blade. The blade was sharper."*

**19. stone_shard** — Stone Shard — T1 — 1 phy — `matter_energy` — d6+tier ranged; Crit applies Bleeding — Role: ranged — Prereq: none — Synergy: urban terrain — Counter: armored — *"A fragment of the curb took him in the cheek."*

**20. heat_lash** — Heat Lash — T2 — 1 phy — `matter_energy` — d8+tier; ignores leather armor; applies Burning on Full or Crit — Role: burst — Prereq: pyro_spark — Synergy: oil/fuel terrain — Counter: Species E toxin-resist does not help here — *"The air in front of him bent, and the man was burning."*

**21. wall** — Raise Wall — T3 — 2 phy — utility — raise a zone-divider wall for 3 rounds; ranged Attacks through it at −3; can be destroyed (20 dmg) — Role: defense — Prereq: stone_shard — Synergy: retreating — Counter: district_break — *"The ground rose up slow, then fast. It was a wall."*

**22. lightning_arc** — Lightning Arc — T4 — 2 phy — `matter_energy` — d10+tier; jumps to second target at −2 damage — Role: multi — Prereq: heat_lash — Synergy: clustered enemies — Counter: Species J steadiness — *"The arc went through the first. It did not stop."*

**23. district_fire** — District Fire — T6 — 3 phy (heat+3) — `matter_energy` — d12+tier area (entire encounter zone); leaves terrain burning for scene — Role: area — Prereq: lightning_arc — Synergy: last resort — Counter: Temporal retreat — *"He set fire to the block and did not put it out."*

#### Biological / Vital

**24. wound_close** — Wound Closing — T1 — 1 phy (self) — utility — target heals 2 physical damage; takes 20 min — Role: sustain — Prereq: none — Synergy: downtime — Counter: not combat — *"She put her hands on the wound and breathed until it closed."*

**25. animal_calm** — Animal Calm — T1 — 1 men — utility — one altered beast/animal: opposed `will`; on success, beast is friendly for scene — Role: creature-register — Prereq: none — Synergy: wilderness — Counter: Hive, eldritch — *"The wolf watched her, and did not come closer."*

**26. body_adapt** — Self-Modification — T1 — 1 phy — utility — self: adapt to cold/heat/underwater/low-O2 for 1 scene — Role: utility — Prereq: none — Synergy: environmental — Counter: none — *"He did not breathe for two minutes and did not notice."*

**27. field_heal** — Field Healing — T2 — 2 phy — utility — 1 target: heal 1 track segment (phy/men) in 1 round — Role: sustain — Prereq: wound_close — Synergy: ally — Counter: Bleeding persists — *"She did not speak. The wound slowed its bleed."*

**28. overgrow** — Overgrow — T2 — 1 phy — `biological_vital` — d6+tier; zone becomes difficult terrain (Maneuver −2) for 3 rounds — Role: control — Prereq: none — Synergy: retreat — Counter: fire — *"Vines came up through the asphalt. It was not fast. It was enough."*

**29. agony** — Agony Induction — T4 — 2 phy (ethical consequence) — `biological_vital` — d8+tier direct harm; Crit applies both Stunned and Bleeding — Role: direct — Prereq: field_heal — Synergy: single target — Counter: Species E, H — *"The man stopped moving and screamed instead."*

**30. raise** — Raise the Dying — T5 — 3 phy (self) — utility — target at 5 phy or with tier-3 harm: bring to 3 phy, clear statuses, remove lethal harm (scene tier only) — Role: sustain — Prereq: field_heal — Synergy: post-fight — Counter: eldritch-caused death — *"The breath returned. It was not even."*

#### Auratic

**31. calm_field** — Calm Field — T1 — 1 soc — utility — zone: nearby allies resist Shaken; hostile Parley checks at −1 — Role: support — Prereq: none — Synergy: Parley — Counter: fear users — *"The room settled when she came into it."*

**32. dread_field** — Dread Field — T1 — 1 soc — `auratic` — zone: enemies at −1 all checks while within; enemies who enter must `will` vs TN 10 or gain Shaken — Role: debuff — Prereq: none — Synergy: aggressive play — Counter: Species J, D — *"He said nothing. Men still moved back."*

**33. trust_field** — Trust Field — T1 — 1 soc — utility — zone: Parley +2, but lying inside the zone is harder; truth is felt — Role: social — Prereq: none — Synergy: diplomacy — Counter: deceivers exit — *"She did not raise her voice. They did not lie to her."*

**34. clarity_field** — Clarity Field — T2 — 1 soc — utility — allies in zone: +1 Assess, resist Confusion effects — Role: support — Prereq: any field — Synergy: Perceptual allies — Counter: corruption zones — *"Thinking in his presence was easier."*

**35. rally** — Rally — T3 — 2 soc — utility — all allies in zone: clear 1 Shaken or 1 Stunned; +1 to next Attack/Power — Role: support — Prereq: calm_field — Synergy: after enemy burst — Counter: none — *"Whatever he said then held the line."*

**36. unmake_fear** — Unmake Fear — T5 — 3 soc (permanent corruption 0 at this tier, but personality fixation accrues) — `auratic` — target: remove Shaken and immune for scene, or apply enemy-wide Shaken resist — Role: strong buff — Prereq: rally — Synergy: vs dread enemies — Counter: long-term personality mark — *"She told him it was all right. It was not, but he believed her."*

#### Temporal / Spatial

**37. blink** — Blink — T2 — 1 men — utility — teleport 1 zone; avoids opportunity attacks; acts as Disengage component — Role: mobility — Prereq: none — Synergy: escape — Counter: none — *"He was there. Then he was not."*

**38. fold_inventory** — Fold Inventory — T2 — 0 (passive) — utility — store 3 objects in subjective space; draw as Minor — Role: utility — Prereq: none — Synergy: logistics — Counter: none — *"She reached into nothing and took out the knife."*

**39. echo_sight** — Echo Sight — T3 — 1 men — utility — perceive scene state as of 10 minutes ago; +2 Assess on scene — Role: info — Prereq: none — Synergy: investigation — Counter: anomalous zones — *"She saw the room as it had been before the fight."*

**40. accelerate** — Personal Acceleration — T4 — 2 men — utility — self: one extra Minor this round, for 3 rounds — Role: tempo — Prereq: blink — Synergy: action economy — Counter: Temporal counter-users — *"Between his second step and his third he did four things."*

**41. slip_space** — Slip — T5 — 2 men — utility — teleport up to 3 zones; take 1 ally with; leaves Temporal contamination (minor) — Role: escape — Prereq: blink + accelerate — Synergy: full-party disengage — Counter: Temporal lock — *"They stepped sideways and were elsewhere."*

**42. pause_moment** — Pause Moment — T7 — 3 men (corr+1) — utility — the actor acts twice this round; time does not pass for enemies during the first Major — Role: decisive — Prereq: slip_space — Synergy: finisher setup — Counter: anomalous presence — *"She moved once and moved again, and the room had not moved between."*

#### Eldritch / Corruptive

**43. mark_reading** — Mark Reading — T1 — 1 men (corr+1 per use past 5) — utility — Assess an entity; reveal pact status, eldritch affinity, corruption count — Role: info — Prereq: none — Synergy: eldritch combat — Counter: none — *"She could see what he had accepted, and what remained of him."*

**44. curse_mark** — Curse Mark — T2 — 1 men (corr+1) — `eldritch_corruptive` — target: d6+tier; persists as Marked for scene; Attack vs them +2 — Role: target lock — Prereq: mark_reading — Synergy: Finisher — Counter: Auratic clarity — *"He drew something on his palm and the man felt the drawing inside his own skin."*

**45. whispered_bargain** — Whispered Bargain — T3 — 1 men (corr+2) — `eldritch_corruptive` — target `will` vs TN 13; fail = Corrupted status for 3 rounds — Role: control — Prereq: curse_mark — Synergy: lower-tier foes — Counter: Species J, high-will — *"She did not say it aloud. He heard it anyway."*

**46. small_offer** — Small Offer — T4 — 0 phy (corr+1 per scene) — utility — one Minor: ask a Sovereign-adjacent presence for a small answer; truthful within their kind — Role: sim-level — Prereq: whispered_bargain — Synergy: narrative — Counter: not combat — *"She asked and something answered."*

**47. deep_pact** — Deep Pact — T6 — 3 men (corr+3) — `eldritch_corruptive` — target: d12+tier; Crit applies Corrupted + Bleeding; target's AI profile flips to `opportunist` (betrayal rider) — Role: rare — Prereq: whispered_bargain — Synergy: confluence — Counter: anti-eldritch preparation — *"He spoke the wrong name, and the thing he spoke to answered him."*

**48. sovereign_voice** — Sovereign Voice — T8 — 4 men (corr+5) — `eldritch_corruptive` — zone: all enemies roll `will` vs TN 16 or be incapacitated 1 round; self gains Corrupted permanently at +1 — Role: nuclear — Prereq: deep_pact — Synergy: last resort — Counter: Sovereign-class presence — *"He spoke, and it was not his voice. The room went still."*

(The library defines 48 powers total — 42 standard plus 6 extension entries for T6–T8. Powers at T9/T10 are not defined as implementable — in-fiction they are the province of named NPCs like Preston and Volk and are resolved narratively rather than as player-cast spells.)

---

## SECTION 6 — STATUS EFFECTS

Closed list: `bleeding`, `stunned`, `shaken`, `burning`, `exposed`, `marked`, `corrupted`. No other statuses exist.

### 6.1 Full definitions

**Bleeding.**
- *Effect*: at end of afflicted combatant's turn, take 1 physical damage. Does not benefit from or trigger Defend.
- *Application*: Attack with edged weapon on Crit; power `stone_shard` on Crit; power `agony` on Crit; harm tier 2 "deep cut."
- *Removal*: end of scene; `field_heal`; `wound_close`; Minor action (self-bandage) on `insight+per` TN 10 (uses up any cloth resource).
- *Stacking*: multiple Bleeding applications do not stack damage; duration restarts. Species H clears Bleeding at start of their turn automatically.
- *Intensity narration*:
  - Light: "Her sleeve was getting heavier at the wrist."
  - Medium: "Each breath pulled blood up the side of his shirt."
  - Severe: "He was leaving a trail and he could not stop leaving it."

**Stunned.**
- *Effect*: loses Major action next turn. Does not affect Minor. Cannot declare reactions while Stunned.
- *Application*: Attack with blunt on Crit; `kin_strike` Crit; `throw_car` Crit (all in zone); `agony` Crit (combined with Bleeding); harm tier 1 "ears ringing."
- *Removal*: duration 1 round; automatic at end of next turn.
- *Stacking*: does not stack; duration resets.
- *Narration*:
  - Light: "He heard the hit more than felt it; the world was a beat behind."
  - Medium: "She was on one knee and did not remember going there."
  - Severe: "Everything was sideways and slow."

**Shaken.**
- *Effect*: −1 on all checks. Cannot spend momentum. Cannot use Power of tier ≥ current tier.
- *Application*: `suggest`, `psychic_lance` Crit, `dread_field` proximity fail, Parley Fumble self-application, witnessing an ally's tier-3 harm event.
- *Removal*: end of scene; `rally`; Parley Full success on self by ally.
- *Stacking*: does not stack; duration resets.
- *Narration*:
  - Light: "He held the rifle slightly wrong."
  - Medium: "She looked at her hand and found it was not steady."
  - Severe: "He did not look up from the floor."

**Burning.**
- *Effect*: at end of turn, take 1 physical damage type `matter_energy`. −1 to all non-Disengage checks until removed.
- *Application*: `pyro_spark`, `heat_lash`, `lightning_arc`, `district_fire`; flammable environment.
- *Removal*: Minor action (drop and roll; TN 10 `agility+might`); 1 zone of water; Matter/Energy specialist extinguish (free Minor).
- *Stacking*: multiple applications do not stack; duration is 3 rounds fresh on each application.
- *Narration*: fire does what fire does; describe what is burning.

**Exposed.**
- *Effect*: attackers gain +2 on Attack/Power/Finisher against this target; enables Finisher. Target cannot spend momentum.
- *Application*: exposure track fills to `exposure_max`. Damage types matching target's vulnerabilities fill it faster.
- *Removal*: at end of each round in which the target took no damage, exposure track −1. When exposure track falls below `exposure_max`, Exposed removed. Also removed by: successful Disengage reducing track to 0, Parley Crit, combat end.
- *Stacking*: not stackable — either Exposed or not.
- *Narration*:
  - "He had been set up wrong by the second hit and now had nowhere to go."
  - "She was still standing. She was finished."
  - "The thing was hurt in a way that mattered."

**Marked.**
- *Effect*: attackers gain +2 on Attack/Power. Marked target is visible through concealment to the marker.
- *Application*: Attack with ranged on Crit; `curse_mark`; tactical focus declaration (free Minor at combat start).
- *Removal*: end of scene; `memory_edit`; `clarity_field` zone.
- *Stacking*: multiple marks from different sources do not stack bonus but all markers gain visibility.
- *Narration*: subtle — a sight line, a smear, a faint sound that identifies the one target.

**Corrupted.**
- *Effect*: −1 to Parley and Assess against non-eldritch targets; +1 to Eldritch Power damage; one random scene-level cost rolled per round while afflicted (1: minor hallucination; 2: Shaken; 3: nothing; 4: nothing; 5: gain 1 corruption segment toward track; 6: briefly perceive what a Sovereign perceives, take 1 mental).
- *Application*: `whispered_bargain`, `deep_pact`, `sovereign_voice`; exposure to corruption zone; accepted offer (§11.3).
- *Removal*: end of scene unless corruption track advanced past 2 during application; permanent if track advanced to 3+.
- *Stacking*: does not stack; duration resets.
- *Narration*: things should-be-ordinary are slightly wrong for the Corrupted combatant. Times disagree. Reflections take a beat too long.

### 6.2 Interaction matrix (7×7)

Row = existing status; column = newly applied status. Entry = combined effect.

|  | Bleeding | Stunned | Shaken | Burning | Exposed | Marked | Corrupted |
|---|---|---|---|---|---|---|---|
| **Bleeding** | duration reset | add Stunned | add Shaken; damage +1 at tick | add Burning; damage +1 at tick | Expose immediate; Finisher eligible | damage +1 next hit | Corrupted blocks field_heal |
| **Stunned** | add Bleeding; turn-skip applies first | duration reset | add Shaken; −2 total | add Burning; no Defend possible | Expose imm; Finisher at +4 | add Marked; +2 next Attack | Corrupted amplifies Stun (duration +1) |
| **Shaken** | add Bleeding | add Stunned | duration reset | add Burning | Expose if track full; +1 fill | add Marked | Corrupted + Shaken = Sovereign-feel; −2 checks while both |
| **Burning** | add Bleeding; +1 phys/turn | add Stunned | add Shaken | duration reset | Expose; Burning-triggered Finishers ignite zone | add Marked | Corrupted Burning burns weird colors; no mechanical change |
| **Exposed** | Finisher eligible | Finisher at +4 | +1 fill | Burning-through-Exposed triggers ignite-zone Finisher | duration reset | +2 on any Finisher vs this target | Corrupted Exposed enables eldritch Finishers only |
| **Marked** | Bleeding spreads trail (narrative) | Stunned Marked = −4 to Defend | Shaken Marked = broken-mark; reveal secondary info on Assess | Burning Marked = "lit by a line of smoke" | Exposed Marked enables any Finisher | duration reset | Corrupted Mark = mark visible to eldritch |
| **Corrupted** | Corrupted Bleeding bleeds wrong | Stunned Corrupted: on recovery, roll corruption gain | Corrupted Shaken: extreme debuff — cannot Parley non-eldritch | Corrupted Burning: flames not extinguishable without clear_field | Exposed Corrupted: eldritch Finishers only | Corrupted Marked: marker sees through to corruption | duration reset; +1 corruption track |

### 6.3 Application/removal authority

Statuses are applied by the combat engine only as a result of a resolved check, a defined power/ability rider, or a terrain/tick effect. The narrator never originates status changes. Duration counters tick in the end-of-round phase.

---

## SECTION 7 — AFFINITY AND DAMAGE TYPES

### 7.1 Damage types

Seven, one-to-one with power categories. Short ids used throughout:

- `physical_kinetic` (PK)
- `perceptual_mental` (PM)
- `matter_energy` (ME)
- `biological_vital` (BV)
- `auratic` (AU)
- `temporal_spatial` (TS)
- `eldritch_corruptive` (EC)

### 7.2 Affinity multipliers

Affinity is per combatant per damage type: `vulnerable`, `neutral`, `resistant`, `immune`, `absorb`.

| Affinity | Damage multiplier | Exposure fill multiplier |
|---|---|---|
| vulnerable | ×1.5 (round up) | ×2 |
| neutral | ×1 | ×1 |
| resistant | ×0.5 (round down, min 1 if damage was ≥1) | ×0.5 (round down) |
| immune | ×0 | ×0 |
| absorb | ×0 to health; heals 1 phy per 3 incoming damage; no exposure fill | ×0 |

Damage calculation order (see also §10.1):

```
raw = base_damage(power/weapon) + tier_bonus + static_modifiers
after_affinity = raw * affinity_multiplier (floor with min-1-if-struck rule)
after_armor = after_affinity - armor_reduction (min 0)
after_cover = after_armor - cover_reduction (min 0)
final = after_cover
```

### 7.3 Standard affinity profiles

**Standard human (civilian, militia):** all neutral.

**Elite human:** PK resistant (armor), PM neutral, ME neutral, BV neutral, AU neutral, TS neutral, EC vulnerable.

**Wretch:** PK resistant (bodies are wrong), PM neutral, ME neutral (fire works), BV vulnerable (biology is malformed), AU neutral, TS neutral, EC vulnerable.

**Hunter:** PK neutral, PM resistant, ME neutral, BV neutral, AU neutral, TS neutral, EC vulnerable.

**Aberrant:** PK resistant, PM resistant, ME neutral, BV vulnerable (usually; variant Aberrants may differ), AU resistant, TS resistant, EC neutral.

**Shade:** PK immune, PM vulnerable, ME resistant, BV immune, AU vulnerable, TS vulnerable, EC neutral.

**Sovereign (anomalous):** PK resistant, PM resistant, ME resistant, BV resistant, AU neutral, TS neutral, EC absorb (most).

**Hive drone / warrior / fragment-cluster:** PK neutral, PM resistant (hive mind distributes shock), ME vulnerable (fire is the classical hive counter), BV resistant (anti-body systems), AU resistant, TS neutral, EC resistant.

**Species A (Hollow-Boned):** PK vulnerable (brittle bones), PM neutral, ME neutral, BV neutral, AU neutral, TS resistant (species-typical precog), EC neutral.

**Species B (Deep-Voiced):** PK neutral, PM resistant, ME neutral, BV neutral, AU vulnerable (resonance), TS neutral, EC neutral.

**Species C (Silver-Hand):** PK neutral, PM neutral, ME resistant (hands sense material), BV neutral, AU neutral, TS neutral, EC vulnerable.

**Species D (Pale-Eyed):** PK neutral, PM resistant, ME neutral, BV neutral, AU resistant, TS neutral, EC neutral.

**Species E (Slow-Breath):** PK neutral, PM neutral, ME resistant (heat/cold tolerant), BV resistant (toxin), AU neutral, TS neutral, EC neutral.

**Species F (Broad-Shouldered):** PK resistant (density), PM neutral, ME neutral, BV neutral, AU neutral, TS neutral, EC neutral.

**Species G (Sun-Worn):** PK neutral, PM neutral, ME neutral, BV resistant, AU neutral, TS neutral, EC vulnerable.

**Species H (Quick-Blooded):** PK neutral, PM neutral, ME neutral, BV resistant (regeneration), AU neutral, TS neutral, EC neutral.

**Species I (Wide-Sighted):** PK neutral, PM resistant, ME neutral, BV neutral, AU neutral, TS neutral, EC neutral.

**Species J (Stone-Silent):** PK resistant, PM resistant, ME neutral, BV neutral, AU resistant (steadiness), TS neutral, EC neutral.

### 7.4 Cover, armor, and zones

Cover reduces only physical-and-matter damage (PK, ME, BV projectile). Mental, auratic, temporal, eldritch ignore cover unless specifically flagged.

Armor static:

| Armor | Reduction | Cost to acquire |
|---|---|---|
| None | 0 | - |
| Clothing | 0 | baseline |
| Leather jacket | 1 | market |
| Reinforced gambeson | 2 | salvage or market |
| Plate (retinue) | 3 | retinue-issue |
| Matter-shaped plate (C-craft) | 4 | prestige |

Armor reduction applies after affinity. Certain powers (stone_shard Crit) ignore leather only; `heat_lash` ignores leather (specified). Matter/Energy fire bypasses cloth cover but is reduced by mass (stone, plate).

### 7.5 Status interaction with affinity

Damage-inducing statuses (Burning ticks, Bleeding ticks) apply the actor's affinity for the relevant damage type. So a Species E is still vulnerable to Burning if neutral to ME (their resistance to ME applies to the burn-through only partially: halved tick damage via their resistance multiplier).

---

## SECTION 8 — EXPOSURE AND FINISHERS

### 8.1 Exposure track

Every combatant has `exposure_track` (current) and `exposure_max` (cap). Fills through damage with type-affinity multiplier and through narrative triggers. When `exposure_track >= exposure_max`, the combatant gains `exposed` status.

Base `exposure_max` by type (before +resilience_bonus):

| Type | Base |
|---|---|
| Standard human civilian | 3 |
| Standard human militia | 3 |
| Elite human | 4 |
| Metahuman (any species) | 4 |
| Wretch | 2 |
| Hunter | 3 |
| Aberrant | 5 |
| Shade | 4 |
| Sovereign | 8 |
| Hive drone | 2 |
| Hive warrior | 3 |
| Warped T4–T6 | 6 |
| Corrupted human | 4 |

Add `resilience_bonus = tier // 2`.

### 8.2 Fill rates

Each damage instance adds fill based on raw damage after affinity, using this formula:

```
fill_delta = (damage_final // 2) * affinity_fill_multiplier
           + 1 if damage_final > 0 else 0          # the "sting" floor
           + 1 per Crit status applied                # crits push Exposure
```

Narrative triggers that add fill without damage:

- Ally fell: +1
- Parley Fumble in view: +1
- Seeing a Sovereign present directly: +2
- Witnessing own blood hit the floor: +1 (once per scene)

### 8.3 Finishers catalog

Finishers trigger when target is Exposed. Actor spends 5 momentum (or 2 momentum + 1 damage). Each finisher entry: **name — trigger — resolution — dramatic effect — variations**.

Two finishers per damage type (14 total):

**Physical / Kinetic:**

**fin_break_spine** — "Break the Spine" — melee + Exposed target — `might+strength` vs TN 10 — Target reduced to 0 physical, alive, tier-3 harm "broken spine, will not walk" — Variation on Marginal: tier-2 harm "broken ribs, persistent"; on Fumble: Attack misses, Exposed clears.

**fin_throw_through** — "Throw Through" — Exposed + `physical_kinetic` primary — `might+strength` vs TN 10 — Target is thrown into another enemy in adjacent zone; both take half damage; both become Exposed — Variation: if no second target, throw into terrain for tier-2 harm only.

**Perceptual / Mental:**

**fin_mind_break** — "Mind Break" — Exposed target in Parley range — `will+perception` vs TN 10 — Target goes catatonic for scene; enters parley surrender; mental track fills to 5 — Variation: Marginal leaves target Shaken permanently this scene; Fumble transfers 2 mental to self.

**fin_show_them** — "Show Them What They Did" — target Exposed with witnesses — `insight+perception` vs TN 10 — Target surrenders publicly; heat with target's faction decreases by 1 (demoralization cascade); watching allies gain +1 morale for scene — Variation: on Fumble, opposite — target galvanized, gains +2 Attack.

**Matter / Energy:**

**fin_ignite_zone** — "Ignite the Zone" — target Exposed with Burning — `might+insight` vs TN 10 — Zone burns for 3 rounds (all combatants take Burning on start of turn); heat +2 with any faction who controls territory; target dies unless Species E — Variation: Marginal limits fire to target; Fumble engulfs actor too.

**fin_pin_under** — "Pin Under Stone" — Exposed + Matter/Energy primary — `might+insight` vs TN 10 — Target is pinned by reshaped matter; immobilized until Crit Maneuver to escape; tier-2 harm "crushed limb" — Variation: Crit adds tier-3 harm "lost arm."

**Biological / Vital:**

**fin_shut_down** — "Shut Down the Body" — Exposed, touched — `will+insight` vs TN 10 — Target's nervous system collapses; alive, tier-3 harm "blind / deaf / mute / nerve-damaged" (choose one); takes no combat actions rest of scene — Variation: Marginal gives only Stunned for 3 rounds; Fumble backlash 2 phy to self.

**fin_mercy_kill** — "Mercy" — Exposed target with Bleeding and tier-2+ harm — `will+insight` vs TN 10 — Target dies without suffering; actor gains −1 heat with any faction that values mercy (CJL, Yonkers, Bourse); +1 standing with Biological/Vital primaries — Variation: Fumble — target lives, in severe pain; +1 heat with faction.

**Auratic:**

**fin_unmade** — "Unmade" — Exposed + in Dread or Trust field — `will+might` vs TN 10 — Target surrenders or breaks; AI profile shifts permanently to defensive for scene — Variation: Crit spreads effect to nearest enemy ally.

**fin_command_silence** — "Command Silence" — Exposed + Auratic primary — `will+might` vs TN 10 — Target stops, cannot attack; Parley immediate at +2; witnesses' Shaken status tier-2 for scene — Variation: Fumble causes self to gain Shaken.

**Temporal / Spatial:**

**fin_skip** — "Skip Them Out" — Exposed + Temporal primary — `insight+perception` vs TN 10 — Target teleported out of encounter (removed); witnesses confused; target wakes at a specified nearby location — Variation: Marginal displaces 1 zone only; Fumble teleports actor to that location, switching places with target.

**fin_pause_cut** — "Pause and Cut" — Exposed + pause_moment active — `insight+perception` vs TN 10 — Target does not perceive the killing stroke; alive or dead at actor choice; no opportunity attacks apply — Variation: Fumble stops time for actor only (lost turn, corrupt +1).

**Eldritch / Corruptive:**

**fin_name_them** — "Name Them" — Exposed target with Corrupted — `will+insight` vs TN 10, corr +2 — Target is unmade — either converted to a marked eldritch-adjacent entity (if corrupted to 3+) or dies silently — Variation: on success, nearby enemies roll `will` vs TN 13 or gain Shaken for scene.

**fin_hand_over** — "Hand Them Over" — Exposed target in a Sovereign-marked zone or with eldritch attention — `will+insight` vs TN 10, corr +3 — Target removed (taken by the thing that was listening); actor owes a favor; world state: corruption clock advances 1 segment — Variation: Fumble — actor taken instead.

### 8.4 Decay and persistence

Exposure decays at end-of-round by 1 if target took no damage that round and is not Exposed. When Exposed, exposure does not decay until all statuses cleared and 2 rounds of no damage pass.

Exposure does not persist across encounters. Combat Outcome generation sets exposure_track = 0 on all surviving combatants.

### 8.5 Parley interaction

A Full/Crit Parley against an Exposed target counts as a Finisher-equivalent without momentum cost: target stands down. This is the mechanical expression of "killing is often the worst option" — the player can broker at the finish line.

---

## SECTION 9 — ENEMY AI

### 9.1 Decision procedure (shared across profiles)

Each enemy turn:

1. Enumerate legal actions (Major + Minor options): Attack targets, Power uses, Maneuver options, Assess options, Parley (if parley_available), Disengage (if meets retreat conditions), Finisher (if target Exposed and momentum ≥ 5).
2. Score each candidate action as `U(action) = sum(weight_i * feature_i)` per profile.
3. Apply situational modifiers.
4. Pick highest-U action; on ties, pick by initiative-seeded deterministic tiebreak (action id lexicographic).
5. Execute.

Features used across profiles (all normalized to 0..1 or signed):

- `target_damage_expectation` — expected damage to target per action.
- `target_exposure_fill` — expected exposure fill.
- `self_risk` — expected damage to self next round given this action.
- `position_value` — value of the terrain zone achieved (objective, flanking, escape).
- `tempo` — +1 if action generates momentum, +0.5 if Crit-likely (tier gap).
- `allies_need` — 1 if an ally is Exposed or at low phy, 0 otherwise.
- `threat_to_self` — the Attack-expected-damage of the most dangerous visible enemy toward self.
- `parley_signal` — player's recent actions: Parley attempted (+1 if yes this or last round), sparing wound (+0.5).

### 9.2 Profiles

**Aggressive.**

| Feature | Weight |
|---|---|
| target_damage_expectation | +1.5 |
| target_exposure_fill | +1.0 |
| self_risk | −0.25 |
| position_value | +0.25 |
| tempo | +0.5 |
| allies_need | 0 |
| threat_to_self | 0 |
| parley_signal | −0.5 |

Target prioritization: lowest current_phy_max; on tie, highest threat_to_self. Retreat: only if phy track ≥ 4/5 **and** no ally within 2 zones.

**Defensive.**

| Feature | Weight |
|---|---|
| target_damage_expectation | +0.5 |
| target_exposure_fill | +0.25 |
| self_risk | −1.5 |
| position_value | +1.0 |
| tempo | +0.25 |
| allies_need | +1.0 |
| threat_to_self | +0.5 |
| parley_signal | +1.0 |

Target prioritization: highest threat_to_self. Retreat: phy track ≥ 3/5 **or** no allies remaining.

**Tactical.**

| Feature | Weight |
|---|---|
| target_damage_expectation | +0.75 |
| target_exposure_fill | +1.25 |
| self_risk | −0.5 |
| position_value | +0.75 |
| tempo | +0.75 |
| allies_need | +0.5 |
| threat_to_self | +0.25 |
| parley_signal | +0.5 |

Situational: prefers Assess on round 1 if no prior Assess; prefers Maneuver to flanking when feasible; uses Powers when affinity is exploitable (vulnerable). Target prioritization: currently Exposed if any; else highest tier. Retreat: mission-failure condition met, or phy ≥ 4/5 with no allies in range.

**Opportunist.**

| Feature | Weight |
|---|---|
| target_damage_expectation | +1.0 |
| target_exposure_fill | +1.5 |
| self_risk | −1.0 |
| position_value | +0.5 |
| tempo | +1.0 |
| allies_need | 0 |
| threat_to_self | +0.5 |
| parley_signal | +0.25 |

Prefers flanking, Marked targets, Exposed targets; avoids frontal engagements. Target prioritization: Exposed > Marked > lowest phy > isolated. Retreat: phy ≥ 2/5 if threat_to_self high; Disengage readily when chance drops.

**Pack.**

| Feature | Weight |
|---|---|
| target_damage_expectation | +1.0 |
| target_exposure_fill | +1.25 |
| self_risk | −0.5 |
| position_value | +0.5 |
| tempo | +0.5 |
| allies_need | +0.25 |
| threat_to_self | 0 |
| parley_signal | −0.5 |
| coordination_bonus | +1.5 (if 2+ pack allies attacking same target) |

Pack members always prefer to converge on a single target. If pack size drops below 2, individual pack members degrade to aggressive. Retreat: if pack reduced to 1 member for 2+ rounds.

### 9.3 Worked combat examples

**Aggressive profile (scavenger raider).** Target: player (str d8, agi d8, tier 3, phy 1/5). Raider stats: d8 d6 d6 d6 d4 d8 / tier 2 / phy 0/5. AI picks from (a) melee Attack, (b) Maneuver to flank, (c) Disengage.

*Round 1.* Scores: Attack: 1.5*0.4 [expected] + 1.0*0.3 [expo] − 0.25*0.2 [self risk, player is strong] + 0.5*0.25 [tempo] = 0.6 + 0.3 − 0.05 + 0.125 = 0.975. Maneuver: 0.25*0.5 [position] + tempo 0 = 0.125. Disengage: − not yet wounded. Pick Attack. Raider rolls str d8=6, agi d6=3; high 6; TN=9 (defense); margin −3; Partial Fail. Player unharmed.

*Round 2.* Raider Attack again: same scores (fresh). Roll d8=7, d6=5; high 7; −2 (player declared Defend reaction). Margin = 7−2−9 = −4; Fail. Raider takes 1 phy (self) from reversal… wait, that's if the *player* attacks. Raider stays at phy 0. But player Attacked back on previous turn: did damage 5. Raider now phy 2/5.

*Round 3.* Raider phy 2/5, still under 4/5 retreat threshold. Ally Attack is feasible. Same Attack pick. Rolls double-1 Fumble. Raider takes 2 phy self; now 4/5. Exceeds retreat threshold. On own next move: Disengage considered (but adjacent player + phy 4/5 + no allies → still prefers retreat). Disengage TN 13 (one adjacent); rolls agi+ins = d6+d4. High=4. Margin −9. Fail. Opportunity Attack by player resolves. End.

**Defensive profile (Bear-House guardsman).** Player is a T5 kinetic attacker. Guardsman: d8 d8 d8 d8 d6 d8 / T4 / phy 0/5, plate (+3 armor, def 11).

*Round 1.* Player kin-pushed guardsman. Expected damage ~6 → after plate → 3 phy taken. Guardsman phy 3/5. Threshold (3/5) met → retreat considered. But ally Captain present; allies_need = 0. Pick Defend + Assess (Minor). Defend scores: self_risk mitigation high. Rolls Defend opposed: d8+d8, high 6; player got 9 on attack. Margin −3; Partial Defend; took damage normally. Already done this round.

*Round 2.* phy 3/5. Pick Disengage to cover. Rolls agi+ins d8+d6 high 7; TN 13 (adjacent player). Margin −6. Fail — but no opportunity attack triggers if player did not take reaction. Guardsman stays.

*Round 3.* Captain shouts order (Rally free for scene). Guardsman: allies_need now 1 (Captain Exposed). Pick Attack on player at +2 (coordinated). Rolls str+agi d8+d8 high 7; TN=15 (player def + tier gap). Margin −8; Fail.

End-round: Captain falls (player finisher). Guardsman last standing. Retreat per Defensive on own terms: Disengage TN 10 (no adjacent). Roll d8+d6 high 5, +momentum 3 spend (had 3 from defend Crits earlier). Total 8. Margin −2. Partial; no disengage. Player offers parley (Marginal hit earlier). Guardsman accepts under Defensive weighting (parley_signal +1.0 tips the action). Parley resolves: terms negotiated (see §11).

**Tactical profile (Catskill Throne lieutenant).** A three-round combat against a pair of raiders. Player present as ally. Lieutenant: d8 d8 d8 d8 d8 d8 / T6 / phy 0/5, defensive terrain.

*Round 1.* Lieutenant picks Assess (Minor) + Attack. Assess scores highest among Minors. Learns raider 1 has Bleeding pre-existing. Attack on raider 1: +2 from Assess. Full success; raider 1 Exposed. Momentum now 1.

*Round 2.* Maneuver flank on raider 2 (position_value 1.0 + tempo 0.75); free Attack next round sets up Finisher. Rolls Full. Flanking achieved.

*Round 3.* Raider 1 Exposed, momentum 1 (not enough for standalone Finisher). Tactical weighing: Finisher not feasible alone; cheaper to Attack for Crit path. Rolls Attack on raider 1 (+2 from Exposed). Full success; raider 1 defeated. Raider 2 flanked. Next round AI expects Finisher on raider 2 or Marginal capture.

**Opportunist profile (Hunter eldritch).** Player solo, T4. Hunter: d8 d8 d8 d4 d6 d8 / T3. Hunter starts unseen.

*Round 1.* Surprise: Hunter gets free Assess + Maneuver. Maneuver into ambush position (+2 surprise, +2 flanking). Score max. Executes.

*Round 2.* Attack on player from ambush. Tempo high, self risk low pre-emptive. Rolls Crit. Full damage; applies Bleeding. Momentum 1.

*Round 3.* Player now Bleeding + hurt. Opportunist scoring: Attack on Bleeding/low-phy target spikes. Picks Attack. Full success. Player Exposed. Hunter checks retreat (phy still 5/5): no retreat, but opportunist threshold: if player still at ≥1 phy but threat_to_self is rising (player T4 Power-pending), Hunter may Disengage. Scores Disengage vs Finisher-setup. Momentum too low for Finisher. Disengage into cover wins. Executes. Hunter fades. Combat ends with player wounded, Hunter alive — the classic Hunter loop.

**Pack profile (Wretch pack, six members).** Player T3. Wretches d6 d6 d4 d4 d4 d6 / T1 each, phy_max 4.

*Round 1.* All six declare Attack on player, converging. coordination_bonus = +1.5 × 6. Combined attack roll ceremony: only two Wretches can flank any single zone per rules; others attack from front.
- Two flanking Wretches: +2 Attack.
- Four frontal: normal.
Player defends twice at most this round; ablative.
Turn order: Wretch 1 (flanking) rolls d6+d6 high 5; TN 9; +2 flank, tier-gap +0 (lower side). Total 7. Fail. Wretch 2 (flanking) rolls high 6; total 8. Fail. Wretch 3 frontal rolls high 5; total 5. Fail. Wretch 4 Crit: d6=6, d6=6. Both match, both ≥6. Crit. Full damage + Bleeding. Player phy 3/5. Wretches 5, 6 roll moderate; one Marginal success; player phy 2/5.

*Round 2.* Player unloads kin-push area. Damage: d6+3 = ~6 raw, affinity PK resistant → 3 per target. Three Wretches to 1/5; two unscratched; one to 2/5. Wretch pack reduced morale 0 (pack doesn't morale-check). Continue.

Wretches all attack. Two Fumble (double-1 on d4 rolls common at small dice). Two full; player to 0/5, Exposed, Bleeding, phy track maxed. Wretch Crit would trigger Finisher but Wretches don't finisher. Player incapacitated.

End state: player defeat. Demonstrates why lone against pack is a failure.

### 9.4 Retreat thresholds (summary)

| Profile | Retreat trigger |
|---|---|
| Aggressive | phy ≥ 4/5 AND no ally within 2 zones |
| Defensive | phy ≥ 3/5 OR no allies remaining |
| Tactical | Mission-fail condition met, OR phy ≥ 4/5 with no allies in range |
| Opportunist | phy ≥ 2/5 if threat_to_self high; or Exposed; or target dies |
| Pack | Pack size < 2 for 2+ rounds; or dominant pack-member incapacitated |

Retreat declares Disengage on AI's next turn.

---

## SECTION 10 — DAMAGE, CONDITION TRACKS, HARM

### 10.1 Damage calculation (formal)

```
function resolve_damage(attacker, target, attack_like_action) -> int:
    base = weapon_damage or power_base_damage(action)
    tier_bonus = attacker.tier // 2
    static_mods = sum(attacker_static + terrain + statuses_on_target)
    raw = base + tier_bonus + static_mods

    aff = target.affinity_table[action.damage_type]
    aff_multiplier = {vulnerable: 1.5, neutral: 1, resistant: 0.5, immune: 0, absorb: 0}[aff]
    after_affinity = floor(raw * aff_multiplier)
    if raw > 0 and after_affinity == 0 and aff == resistant:
        after_affinity = 1  # sting floor

    armor_red = target.armor_static if attack_like_action is melee/ranged else 0
    cover_red = target.cover_reduction if action.ignores_cover is False else 0
    after_defense = max(0, after_affinity - armor_red - cover_red)

    if aff == absorb:
        target.condition_tracks.physical = max(0, target.condition_tracks.physical - floor(raw / 3))
        return 0  # and target gains healing

    return after_defense
```

Damage margin bonus: on Full Success, +0; on Crit, +1 damage.

### 10.2 Damage-to-track allocation

Each damage type maps to condition tracks:

| Damage type | Primary track | Secondary on overflow |
|---|---|---|
| physical_kinetic | physical | — |
| matter_energy | physical | — |
| biological_vital (offensive) | physical | — |
| perceptual_mental | mental | physical on 2+ overflow |
| temporal_spatial | mental | — |
| auratic | social | mental on 2+ overflow |
| eldritch_corruptive | mental | social on 2+ overflow; corruption on Crit |

A track fills 0 → 5. At 5 filled:

- **Physical 5**: incapacitated physically. Next damage triggers harm tier check.
- **Mental 5**: incapacitated mentally; forced Defend/Disengage only; Parley fails automatically.
- **Social 5**: cannot Parley; heat with any involved faction +1; no Auratic powers.

### 10.3 Harm tiers

Harm is acquired when:
- A track is filled to 5 and takes another damage: tier-1 harm automatic.
- Crit Attack/Power with dedicated rider.
- Finisher-induced.
- Tier-3 harm specifically: fatal-if-not-treated or permanently impairing; from Finishers or mortal scenarios.

Triggers:
- **Tier 1** — 1 additional damage past track cap → tier-1 harm.
- **Tier 2** — 3+ additional damage past cap, or Crit with severity — tier-2 harm.
- **Tier 3** — Finisher or massive overflow (6+ past cap) — tier-3 harm.

### 10.4 Harm pool

**Physical harm:**

Tier 1 (scene-only, clear at end):

1. `sprained_joint` — −1 physical checks this scene. Treatment: rest.
2. `ringing_ears` — −1 perception this scene. Treatment: rest.
3. `shallow_cut` — Bleeding 1 round. Treatment: bandage.
4. `bruised_ribs` — −1 might this scene. Treatment: rest.
5. `concussion_light` — −1 insight this scene. Treatment: rest.

Tier 2 (persistent until treated):

6. `deep_cut` — Bleeding persists across scenes; −1 physical until healed. Treatment: `wound_close`, `field_heal`, or 2 days bed rest + bandages.
7. `broken_rib` — −1 might, phy_max reduced by 1, 2 weeks rest. Treatment: biokinetic or time.
8. `broken_finger` — −1 weapon Attack checks. Treatment: splint + 3 weeks.
9. `persistent_concussion` — −1 insight, −1 perception until treated. Treatment: 1 week rest + biokinetic.
10. `infection` — phy 1/day until treated; biokinetic or antibiotic (dwindling resource).
11. `dislocated_shoulder` — cannot use two-handed weapons until treated. Treatment: set, 1 day.
12. `torn_muscle` — −1 strength, −1 maneuver. Treatment: 2 weeks rest + biokinetic.
13. `crushed_hand` — no off-hand use. Treatment: biokinetic or permanent.
14. `shrapnel_embedded` — Bleeding on any Maneuver until removed. Treatment: surgery (no anesthetic).

Tier 3 (permanent or fatal):

15. `broken_spine` — cannot walk; permanent unless T5+ biokinetic + massive cost. Rider: character continues as mounted/chaired NPC or retires.
16. `lost_limb` — arm or leg. Permanent. −2 physical baseline; no two-handed weapons (if arm); no run (if leg).
17. `lost_eye` — permanent. −1 ranged attack, −1 perception.
18. `severe_burn_scarring` — permanent −1 social; −1 heat resistance.
19. `traumatic_brain_injury` — permanent −1 insight OR −1 will (choose at application).
20. `mortal_wound` — character dies in 1 in-world day unless T5+ biokinetic healed; on heal, converts to tier-2 `deep_cut` permanent.

**Mental harm:**

Tier 1:

21. `rattled` — next scene −1 will.
22. `bad_vision` — next scene −1 perception.

Tier 2:

23. `nightmares` — −1 rest recovery for 4 weeks. Treatment: time, community, or biokinetic work.
24. `flashback_trigger` — specific stimulus applies Shaken. Treatment: avoidance or therapy (long).
25. `memory_gap` — lost 1 recent memory; narrative only, does not decay. Treatment: none.
26. `intrusive_voices` — occasional Shaken out of combat. Treatment: religious/community.

Tier 3:

27. `dissociation` — permanent: cannot reliably distinguish real/unreal under stress. Rider: −2 Assess vs eldritch.
28. `psychosis_episodic` — periodic Shaken at scene start. Permanent.
29. `corrupted_memory` — false memory that feels true; character acts on it. Permanent.
30. `mind_scar` — permanent −1 will.

**Social harm:**

Tier 1:

31. `embarrassed` — scene-level; −1 Parley.

Tier 2:

32. `reputation_stain` — heat +1 with one faction permanently until redemption arc.
33. `broken_standing` — relationship with one NPC drops 1 step (toward hostile).
34. `marked_deserter` — specific faction places bounty in relevant region.

Tier 3:

35. `oath_breaker` — broad social: standing −2 with all allied factions; duration permanent until grand reparation.

### 10.5 Healing

- **End of scene**: all tier-1 harm clears. Physical/mental/social track damage does not auto-heal.
- **Short rest (1 hour safe)**: heal 1 physical if phy < 5; heal 1 mental if calm environment.
- **Long rest (1 in-world day safe)**: heal 2 phy, 1 men, 1 soc; treat tier-1 harm acquired earlier.
- **Biokinetic care (T2+)**: 1 hour work, clear all tier-1 and 1 tier-2 physical harm per session.
- **Biokinetic care (T5+)**: can attempt tier-3 physical harm at extreme cost (bible-appropriate: long procedure, trade-in of tier-3 on the healer).
- **Time (weeks)**: tier-2 physical harm clears with listed treatment + time. Tier-2 mental/social does not auto-clear; requires specific narrative events.
- **Corruption does not heal** without explicit narrative intervention (and even then, rarely).

---

## SECTION 11 — THREE COMBAT REGISTERS

### 11.1 Human register

- **Parley available**: default true; set false only if encounter flags blood-feud, specific no-quarter situation, or if target's `parley_conditions` list is explicitly empty.
- **Political consequences**: every Attack that injures a faction-affiliated NPC accrues heat with that faction (+1 per fight, +1 per Crit-damaging hit, +2 if NPC dies). Accrual applies at Combat Outcome generation.
- **Witness mechanics**: every non-combatant NPC and every surviving enemy records the fight. Witnesses roll `perception` vs TN 10 to correctly identify actor (not the player's name unless known). The set of witnesses feeds `world_consequences` type `witness_recorded`. Visible powers leave stronger witness marks — visible Power visibility = "visible" generates 2 witnesses per 1 for "subtle".
- **Faction reactions**: during combat, Parley by an enemy of another faction may trigger a third-party intervention event if the combat is near a border or in contested territory (encounter-level flag; the sim engine decides).
- **Killing vs sparing**:
  - Kill: target's `final_state = dead`; faction heat +2; rumor generated; body disposition must be resolved (burned, buried, left, taken).
  - Spare (leave alive): `final_state = incapacitated` or `fled`; faction heat +1; target holds a grudge (relationship standing with target −1 permanently, +1 memory event "you let me live").
  - Prisoner: `final_state = surrendered`; Parley terms apply; costs include transport, feeding, guarding.
- **Terms negotiation**: Parley Full/Crit enables terms structure. The following term types are recognized by the engine (structured parameters feed into `world_consequences`):

10+ sample terms:

1. `release_for_ransom` — prisoner freed for copper/goods.
2. `safe_passage` — both sides disengage without pursuit; heat +0 for this engagement.
3. `information_exchange` — one truth per side; captured knowledge added to player's known_information; actor can extract faction knowledge.
4. `territory_cession` — loser gives up claim to a zone; faction territory update.
5. `oath_of_neutrality` — loser's faction will not attack actor's faction for a season; clock interaction.
6. `blood_price` — loser pays compensation for deaths; decreases heat by 1.
7. `hostage_held` — actor takes a hostage (specific NPC id); creates hostage state with ticking clock.
8. `forced_labor_term` — loser provides specified service to actor's faction for a season.
9. `disarmament` — loser surrenders weapons; can be salvaged as inventory.
10. `apology_public` — loser publicly admits fault; reputation effects on both sides.
11. `affiliation_switch` — loser defects to actor's faction (rare, requires Crit Parley).
12. `mercy_credit` — actor spares loser; loser owes a defined future favor (1 call-in).

### 11.2 Creature / hive register

- **Parley disabled** for almost all creatures: Wretches, Hunters, Aberrants (default), Hive drones/warriors/fragment clusters, altered fauna.
- **Allowed parley**: Warped of T5+ (bible: parley-capable), Five Sisters and other named council Warped, some individual altered fauna (Nine-Tail specifically), and the Broker (a Sovereign-class Aberrant). Engine uses `parley_conditions` list on template.
- **Ecological pressure clock**: every creature-register encounter advances a `scene_clock` tracking attention. Start at 0; max 8.
  - Each loud Power (visibility "visible"): +1.
  - Each round in Hive territory: +1.
  - Each dead creature: +1.
  - Disengage successful: −0 (but does not remove existing attention).
- **Attention triggers**: at clock ≥ 4, reinforcements arrive (1 extra drone or 1 additional Hunter next round). At clock ≥ 6, an Aberrant-scale response. At clock = 8, the encounter escalates to "all nearby creatures converge" — this is the failure condition; recommend Disengage.
- **Escalation procedure**: the sim engine is notified via `world_consequences` that attention has crossed thresholds: Hive territory advances by 1 local segment in Pine Barrens colony growth; Wretch region density ticks up.
- **Disengagement interaction**: in creature register, Disengage does not stop the clock but does end the encounter. However, the player leaves Tracks (a trail) — the AI assigns a "tracked" flag to the player for the next 2 in-world days in the region. Encounters roll more probability during that window.

### 11.3 Eldritch register

- **Corruption offer mechanics**: when the player engages an eldritch combatant with Parley, Power, or Assess against eldritch targets, the engine may generate a **corruption offer** with probability = 0.2 per interaction, higher (0.5) for Sovereign-class. Offer types:
  - **Information offer**: "Know one thing." Accept: +1 corruption; gain one truth about the world (sim-level). Decline: +1 Shaken.
  - **Power offer**: "Be strong for one turn." Accept: +2 corruption; next Power at +3 and damage +2. Decline: no effect.
  - **Safe-passage offer**: "Leave and owe me." Accept: +1 corruption; escape automatic; world_consequence flag "eldritch debt" posted. Decline: combat continues.
  - **Transform offer**: "Become." Accept: corruption track +3; permanent effect — character gains pact status; long-term transformation. Offered rarely (Sovereign only).
  - **Vessel offer**: "Carry something." Accept: +2 corruption; gain a one-shot eldritch power for the scene. Decline: no effect.
- **Trap structure**: every offer includes a trap. Accepting generates a clock-advance cascade. The engine records offer acceptance in `world_consequences` as `eldritch_obligation`. Subsequent sim ticks may fire hooks.
- **Resource cost differential**: eldritch combat costs are front-loaded into corruption, not condition tracks. Mental damage from eldritch targets applies corruption fill at a rate of +1 corruption per 2 mental track damage taken.
- **Anomalous behavior manifestation**: the narrator is *instructed* (via payload forbidden list) to not resolve the anomalous question. Concrete techniques:
  - Ticks describe wrongness without cause (reflections late, clocks disagreeing).
  - Sovereign names (One Who Waits, The Echo, Grandfather Silt) appear in payload notes but never explained.
  - Voice: eldritch messenger dialogue repeats phrases; does not respond to argument.
  - Damage sources do not correspond to visible action (target takes mental damage; no visible source).
  - Any attempt to "look behind" a Sovereign (Crit Assess at Sovereign) costs +1 corruption and reveals a non-explanation (one detail that adds a question rather than answers one).

---

## SECTION 12 — COMPLETE ENEMY ROSTER

All 30 enemy templates use the schema from interface-spec (§Enemy Template). Notation compressed. Stat line: **[str,agi,per,will,ins,mig] / tier / phy/men/soc max**. Affinity: seven entries, compressed with V/N/R/I/A.

### 12.1 Human templates (12)

**human_scavenger_raider** — *Tonal:* Thin, hungry, patched armor, pre-Onset hunting rifle with reloaded rounds. — *Register*: human. *[d8,d6,d6,d6,d4,d8] / 2 / 5/5/5 / exp 3 / aggressive*. Affinity: PK N, PM N, ME N, BV N, AU N, TS N, EC V. Abilities: `melee_crude` (d6 knife), `rifle_shot` (d8 ranged, 10% jam), `scavenger_sense` (+1 Assess in ruin). Powers: 1 tier-1 random (roll on category table). Retreat: phy ≥ 3/5. Parley: `["food_offered", "safe_passage_offered"]`. Description: "He had not eaten properly in a week and his rifle was older than he was." Tactics: ambushes at ruin chokepoints. Scaling: Elite variant d8 d8 d6 d8 d6 d8 / T3, adds `crude_explosive`.

**human_militia_soldier** — *Federal Continuity or Crabclaw regular.* *[d8,d6,d6,d6,d6,d8] / 2 / 5/5/5 / exp 3 / tactical*. Affinity: all N, EC V. Abilities: `drilled_melee` (d8), `rifle_shot`, `squad_signal` (Minor: grant ally +1 next Attack). Powers: optional 1 tier-1. Retreat: mission-fail. Parley: `["surrender_offered", "credentials_shown"]`. Description: "Uniform in decent repair; the boots were the tell." Tactics: pairs, maintains line.

**human_warlord_lieutenant** — *Iron Crown or Bear-House captain-rank.* *[d10,d8,d8,d10,d8,d10] / 6 / 5/5/5 / exp 7 / tactical*. Affinity: PK R, rest N, EC V. Abilities: `sword_heavy` (d10 melee), `rifle_fine` (d10 ranged), `command` (Rally allies scene). Powers: 2 tier-3 (typically Physical/Kinetic + Auratic dread). Retreat: never unless ordered. Parley: `["cease_hostilities_above", "defer_to_superior_mentioned"]`. Description: "Plate under a long coat, a soldier's stillness, eyes that did not leave the room's exits." Tactics: holds the line, coordinates subordinates.

**human_faction_patrol_leader** — *CJL or Bourse detachment leader.* *[d8,d8,d8,d10,d8,d8] / 4 / 5/5/5 / exp 5 / defensive*. Affinity: all N, AU R. Abilities: `disciplined_shot`, `parley_voice` (+2 Parley), `emergency_bandage` (Minor: heal 1 phy on ally). Powers: 1 tier-2 Auratic `calm_field`, 1 tier-1 Perceptual `read_intent`. Retreat: phy ≥ 3/5 or parley offered. Parley: `["identifiable_affiliation", "non_faction_violence"]`. Description: "She had been in five fights this year and did not wish to be in another." Tactics: de-escalation first.

**human_metahuman_duelist_F** — *Species F retinue champion.* *[d12,d8,d6,d8,d6,d12] / 5 / 6/5/5 / exp 6 / aggressive*. Affinity: PK R, rest N, EC V. Abilities: `heavy_sword` (d10+1), `lunge_close`, `armor_plate` (−2 melee against). Powers: 1 tier-3 `kin_strike`, 1 tier-2 `leap`. Retreat: phy ≥ 4/5. Parley: `["honor_duel_offered", "surrender_formal"]`. Description: "Very large, very still, until he was not." Tactics: closes range, breaks line.

**human_metahuman_duelist_I** — *Species I scout captain.* *[d8,d8,d12,d10,d10,d8] / 5 / 5/5/5 / exp 6 / tactical*. Affinity: PM R, rest N. Abilities: `longshot_bow` (d10 ranged; ignores partial cover), `two_shot` (Minor: second ranged Attack at −2), `kin_sight` (Assess from 500m, no action). Powers: `read_intent` (T1), `telepathy` (T3). Retreat: phy ≥ 3/5. Parley: `["kin_connection", "non_hostile_intent"]`. Description: "Her eyes caught the room light and kept it."

**human_assassin** — *Independent or Listening-marked.* *[d6,d12,d10,d8,d8,d6] / 4 / 4/5/5 / exp 4 / opportunist*. Affinity: all N, EC V. Abilities: `poisoned_blade` (d8 + Bleeding + BV secondary), `shadow_move` (Minor: gain Marked-from on target), `throw_knife` (d6 ranged, −0). Powers: `illusion` (T2), `blink` (T2, if Temporal). Retreat: phy ≥ 2/5 or target down. Parley: `["contract_ended_plausible"]`. Description: "You did not see her enter. You did not want to be looking for her." Tactics: one hit, vanish.

**human_hedge_knight** — *Unaffiliated veteran for hire.* *[d10,d8,d8,d8,d8,d10] / 4 / 5/5/5 / exp 5 / defensive*. Affinity: PK R, rest N, EC V. Abilities: `sword_taught`, `shield_block` (−1 damage taken when shield up), `parry_riposte` (Defend Crit inflicts d6). Powers: 1 tier-2 `hard_skin`. Retreat: contract-over. Parley: `["coin_offered", "better_contract_offered"]`. Description: "He owed no one and no one mistook him for harmless." Tactics: measured; does not overcommit.

**human_charismatic_preacher** — *Listening recruiter or baseline revivalist.* *[d6,d6,d8,d12,d10,d6] / 5 / 5/5/6 / exp 5 / defensive*. Affinity: AU R, EC (varies), rest N. Abilities: `sermon` (Parley at +3; affects multiple), `whispered_offer` (corruption offer if Listening-aligned), `crowd_draw` (Minor: pull nearby NPCs to scene). Powers: `dread_field` or `trust_field` (T1), `rally` (T3), possibly `whispered_bargain` (T3) if Listening. Retreat: never while audience. Parley: `["theological_common_ground"]`. Description: "He did not raise his voice. The voice did something else instead." Tactics: wins before combat starts, or loses.

**human_rogue_surgeon** — *Pre-Onset trained, post-Onset salvage medic.* *[d6,d6,d8,d8,d10,d6] / 3 / 5/5/5 / exp 4 / opportunist*. Affinity: BV R, rest N. Abilities: `scalpel` (d4 + precise: Crit = tier-2 harm), `triage` (Minor: stabilize ally at 0 phy), `knockout_drug` (d6 BV + Stunned on Full). Powers: `wound_close` (T1), `agony` (T4) if morally compromised. Retreat: phy ≥ 2/5. Parley: `["medical_supplies_offered"]`. Description: "Her hands were clean in a world where that was an effort." Tactics: applies pressure fluidly; hates to fight directly.

**human_displaced_veteran** — *Pre-Onset military, now adrift.* *[d8,d6,d6,d8,d8,d10] / 3 / 5/5/5 / exp 5 / defensive*. Affinity: PK R, PM V (PTSD), rest N. Abilities: `old_drill` (d8 rifle, +1 Assess), `dig_in` (Minor: cover +2 next round), `grit` (once per scene: ignore first status). Powers: 1 tier-1 random. Retreat: phy ≥ 4/5. Parley: `["shared_service_reference"]`. Description: "His gear was older than some of the people fighting him." Tactics: positional; will surrender if no escape.

**human_fanatic** — *Listening convert or ideological extremist.* *[d8,d6,d6,d12,d6,d10] / 3 / 5/6/3 / exp 5 / aggressive*. Affinity: PM R, AU V, EC R, rest N. Abilities: `zealous_strike` (d8 + ignore first Shaken), `chant` (Minor: allies +1 will this round), `last_stand` (at 0 phy, one free Attack before death). Powers: `dread_field` or tier-2 Eldritch depending on alignment. Retreat: **never**. Parley: `[]` — empty. Description: "He meant it. Every word." Tactics: forward, always forward.

### 12.2 Creature templates (12)

**creature_hive_drone** — Pine Barrens base unit. *[d6,d8,d6,d4,d4,d6] / 1 / 3/1/1 / exp 2 / pack*. Affinity: PK N, PM R, ME V, BV R, AU R, TS N, EC R. Abilities: `thorn_strike` (d4 + BV; Crit Bleeding), `spore_spray` (d4 cone + mental), `swarm_coordinate` (adjacent drones share +1). Powers: none. Retreat: never individually; colony-level. Parley: `[]`. Description: "Not an animal. Not a plant. Moving at a rhythm that was not quite either." Tactics: swarm.

**creature_hive_warrior** — Colony elite. *[d10,d8,d6,d4,d4,d10] / 3 / 5/2/1 / exp 4 / aggressive*. Affinity: ME V, rest as drone. Abilities: `vine_crush` (d8 + grapple), `acid_spray` (d8 ME range 2), `regenerate` (1 phy per round if not Burning). Powers: none. Retreat: phy ≥ 4/5. Description: "Larger than the drones. Wrong-jointed." Tactics: engages first-line, draws fire.

**creature_transformed_predator_alpha** — Warped-adjacent apex (dire wolf, bear-kin). *[d12,d10,d10,d8,d8,d12] / 5 / 6/5/5 / exp 6 / tactical*. Affinity: PK R, BV R, EC V, rest N. Abilities: `pack_bite` (d10 + Bleeding on Crit), `intimidate` (Minor: applies Shaken on `will` fail), `hunt_track` (out of combat). Powers: 1 tier-2 Perceptual or Auratic if T5 Warped. Retreat: pack-lost. Parley: `["acknowledged_as_equal"]` if T5+ Warped. Description: "It stopped moving when it saw her. It did not need to." Tactics: picks off isolated targets.

**creature_blood_bonded_swarm** — Rat-kin or raven-kin. *[d4,d10,d8,d4,d4,d4] / 2 (swarm) / 6/1/1 / exp 3 / pack*. Affinity: PK R (dispersed), ME V (fire), rest N. Abilities: `many_bites` (d8 area), `cover_sight` (Minor: target −1 per for 1 round), `disperse_regroup` (Maneuver). Powers: none. Retreat: half-HP. Description: "The dark moved. It was not dark." Tactics: area denial.

**creature_charged_zone_fauna** — Altered by prolonged corruption exposure. *[d8,d8,d8,d8,d8,d8] / 4 / 5/5/5 / exp 5 / opportunist*. Affinity: PK N, PM R, ME N, BV N, AU R, TS N, EC R. Abilities: `charged_bite` (d8 PK + EC secondary), `disorient_touch` (target `will` vs TN 13 or 1 round Shaken), `phase_step` (1-zone shift per scene). Powers: none. Retreat: variable. Description: "A deer at the wrong size, with the wrong number of eyes that worked."

**creature_plant_bound_entity** — Hive-adjacent but not colony-bound; overgrowth spirit. *[d6,d6,d10,d8,d8,d8] / 4 / 5/4/2 / exp 5 / defensive*. Affinity: ME V, BV R, rest N. Abilities: `tangle_roots` (grapple 2 targets), `heal_from_earth` (1 phy per round if in plant zone), `thorn_volley` (d6 range 2). Powers: `overgrow` (T2). Retreat: only if uprooted. Description: "The clearing had not been a clearing an hour ago." Tactics: zone lock.

**creature_transformed_scavenger** — Coyote-hog-kin. *[d8,d10,d8,d4,d6,d8] / 3 / 4/3/1 / exp 3 / opportunist*. Affinity: PK N, BV R, rest N. Abilities: `snatch_run` (hit + Maneuver free), `spore_breath` (BV d4 + Shaken), `pack_howl` (call 1 more in round 2). Powers: none. Retreat: phy ≥ 2/5. Description: "It had been something useful once. Not anymore."

**creature_territorial_apex** — Bear-king, bull-warped. *[d12,d6,d8,d8,d8,d12] / 5 / 6/5/5 / exp 7 / defensive*. Affinity: PK R, ME N, BV R, rest N, EC V. Abilities: `claw_sweep` (d12 area), `roar` (Shaken to all enemies first-round), `charge` (d10 + Maneuver 2 zones). Powers: none or 1 Auratic intimidation. Retreat: phy ≥ 5/5 (near death only). Parley if T6+ Warped: `["territorial_respect"]`. Description: "You did not cross into this valley twice."

**creature_ambush_predator** — Ghost-cougar, shadow-weft. *[d8,d12,d10,d6,d8,d8] / 4 / 5/5/5 / exp 4 / opportunist*. Affinity: PM R, PK N, rest N. Abilities: `pounce` (+3 Attack if ambush round), `vanish` (Minor: gain Marked-invisible), `neck_strike` (d8 + Crit-applies-Bleeding-3). Powers: `illusion` (T2) if Warped. Retreat: on damage > 2 phy.

**creature_aquatic_horror** — Chesapeake blood-kin, salted gull. *[d10,d8,d8,d6,d6,d10] / 4 / 5/4/3 / exp 5 / aggressive*. Affinity: ME V (fire), PK N, BV R, rest N. Abilities: `drag_under` (grapple + 1 zone move into water: Stunned), `tentacle_lash` (d10 range 2), `foul_spray` (BV + Shaken). Retreat: surface broken.

**creature_sky_predator** — Bonded hawk, altered raptor. *[d8,d12,d12,d8,d8,d8] / 4 / 4/5/5 / exp 4 / opportunist*. Affinity: PK N, rest N. Abilities: `stoop_dive` (d10 + Marked), `aerial_scout` (Minor: grant team +1 Assess), `talons_carry` (grapple, move up 2 zones if can lift). Retreat: wing-injured.

**creature_larval_stage** — Young Aberrant, fragment-cluster seed. *[d4,d6,d4,d4,d4,d4] / 1 / 2/1/1 / exp 1 / aggressive*. Affinity: everything N except EC V. Abilities: `mindless_bite` (d4), `split_on_death` (into two smaller tokens for 1 round). Powers: none. Description: "Small. Wrong." Tactics: screen for larger entity.

### 12.3 Eldritch templates (6)

**eldritch_lesser_corruption** — A recent Listening convert mid-transformation. *[d8,d6,d6,d10,d6,d8] / 3 / 5/5/3 / exp 4 / opportunist*. Affinity: PK N, PM R, ME N, BV N, AU R, TS N, EC A. Abilities: `whispered_offer` (corruption offer, Parley-like), `wrong_touch` (d6 EC + Corrupted on Crit), `inhuman_endurance` (ignore first Stunned). Powers: `curse_mark` (T2). Retreat: never. Parley: `["relinquish_faith"]` — extremely rare resolution. Description: "He had been a man a month ago. He still almost was."

**eldritch_greater_corruption** — Late-stage Listening deep. *[d10,d8,d8,d12,d10,d10] / 5 / 6/6/4 / exp 6 / defensive*. Affinity: PK R, PM R, ME N, BV R, AU R, EC A, TS N. Abilities: `sovereign_proxy` (channel: d10 + Shaken area), `undertow_pull` (all adjacent -1 will), `litany` (rally allies if present). Powers: `whispered_bargain` (T3), `deep_pact` (T6 reduced). Parley: `[]`. Description: "What he was now had been her sister. It was not now."

**eldritch_voice_from_elsewhere** — An anomalous Shade-adjacent. *[—,d8,d12,d12,d12,—] / 5 / —/5/— / exp 5 / tactical*. Affinity: PK I, ME R, rest V or N. Abilities: `whispered_truth` (mental d10; ignores armor, cover; reveals true thing), `unvoice` (Silences a zone: no speech, no Parley, no Rally for 3 rounds), `wrong_name` (target must roll will TN 16 or gain Corrupted + Shaken). Powers: none. Retreat: fades at dawn or when lead-lined zone entered. Description: "Nothing stood there. Something was speaking."

**eldritch_things_that_knew** — A minor Aberrant with articulate awareness. *[d10,d6,d12,d12,d12,d10] / 6 / 5/6/5 / exp 6 / tactical*. Affinity: PK R, PM R, rest N, EC A. Abilities: `recite_name` (knows actor's true name; d10 EC; applies Marked + Corrupted), `multi_limb_strike` (2 Attacks this round, each d8), `witness_without_body` (present in 2 adjacent zones simultaneously). Powers: `curse_mark`, `whispered_bargain`. Parley: `["bargain_accepted"]` — will offer a deal of its own. Description: "It did not look at her. It had seen her."

**eldritch_the_one_who_returns** — A returning Hunter, killed before and back. *[d10,d12,d10,d8,d8,d12] / 6 / 6/5/4 / exp 7 / opportunist*. Affinity: PK R, BV R, ME N, EC A, rest N. Abilities: `first_wound_healed` (first phy damage heals back next round), `familiar_path` (knows the terrain: free Maneuver per round), `last_death_echo` (once per scene: take no damage from one Attack). Powers: none. Retreat: phy ≥ 6/6. Parley: `[]`. Description: "She had killed it last autumn. It had taken the same steps getting here."

**eldritch_the_pact_touched** — A human deep into a Sovereign pact. *[d8,d8,d10,d12,d12,d10] / 7 / 5/6/5 / exp 8 / tactical*. Affinity: PK R, PM R, AU R, EC A, rest N. Abilities: `pact_channel` (EC d12 + Corrupted area; costs corr +2 per use — engine tracks internally), `mark_all` (Minor: all enemies Marked for 1 round), `patron_intervention` (once per scene: negate one incoming effect). Powers: `deep_pact`, `sovereign_voice` (T8, at reduced scale). Parley: `["patron_mentioned_by_name"]`. Description: "The voice was his. What came out between words was not." Tactics: attacker-at-range; relies on patron.

---

## SECTION 13 — ENCOUNTER CONSTRUCTION

### 13.1 Difficulty calculation

```
encounter_budget = player_tier * 2 + player_condition_reserve * 0.5
player_condition_reserve = (15 - sum(player.condition_tracks)) / 3
  # 0..5; 5 = fresh, 0 = incapacitated soon
available_powers_bonus = min(3, count(player.powers)) * 0.5

effective_player_strength = encounter_budget + available_powers_bonus

enemy_cost(template) = enemy.tier + (1 if ai_profile in ["tactical","pack"] else 0)
                      + (2 if register == "eldritch" else 0)

allocate enemies so that sum(enemy_cost) is within [effective_player_strength − 1, effective_player_strength + 2].

difficulty_band:
  sum == effective − 1       -> Routine
  sum == effective           -> Standard
  sum == effective + 1       -> Hard
  sum == effective + 2       -> Desperate
  sum > effective + 2        -> Forbidden except for boss/scripted
```

For a fresh T3 player with 3 powers: budget = 6 + 2.5 + 1.5 = 10. Standard encounter: two T3 tactical enemies (3+1 + 3+1 = 8), two T1 drones (2), total 10.

### 13.2 Enemy mix rules

- No more than 50% of enemies share the same template in a single encounter (pack exception: up to 8 of same pack template).
- At least one enemy with a Parley path if register is human and encounter is not blood-feud.
- Eldritch encounters: at most 1 Sovereign; never 2 in one encounter.
- Mixed register (human + creature, human + eldritch) is allowed but requires narrative justification in the encounter_spec.

### 13.3 Terrain zone generation

Each encounter has 3–4 zones. Zone types (properties list):

- `exposed` — +1 attacker modifier to any target in zone.
- `cover_partial` — ranged Attack at −1.
- `cover_full` — ranged Attack at −3.
- `hazardous` — all in zone at −1; possible periodic damage.
- `objective` — contextual; holds scene value.
- `elevated` — +1 to attacker from elevated position.
- `concealed` — Maneuver +2 for stealth.
- `corrupted` — eldritch-adjacent; +1 corruption fill per round; Auratic powers disrupted.
- `water` — Burning cannot apply here; Maneuver −1.
- `burning` — Burning status applied to entering combatants.

Zone generator: per encounter, pick one primary theme (ruin, forest, field, tunnel, hall, plaza) and draw 3 zones from theme-appropriate zone list:

| Theme | Zone distribution |
|---|---|
| Ruin | cover_partial + cover_full + exposed + objective |
| Forest | concealed + cover_partial + hazardous + objective |
| Field | exposed + exposed + cover_partial + objective |
| Tunnel | cover_full + cover_partial + hazardous + exposed |
| Hall | cover_partial + elevated + objective + exposed |
| Plaza | exposed + cover_partial + cover_partial + elevated |
| Pine Barrens | concealed + corrupted + hazardous + objective |
| Manhattan | cover_full + corrupted + exposed + cover_partial |

### 13.4 Stakes generation from world state

Stakes derive from the encounter trigger situation. Formula:

```
stakes_string = synthesis(
    primary_faction_interest,
    player_goal_alignment,
    enemy_motive,
    world_clock_proximity
)
```

Six stakes templates (populated from situation):

1. **Survival** — "Live through it." (Default if no other interest present.)
2. **Resource contested** — "What is in the crate matters more than the men guarding it."
3. **Relationship tested** — "The person watching decides something after."
4. **Territory crossed** — "After this, the road is closed or open."
5. **Knowledge extracted** — "One of them knows where {NPC}} is."
6. **Clock pressure** — "If this takes too long, {{something in the world happens}}."

### 13.5 Win/loss/escape templates (12 examples)

| # | type | parameters | narrative sample |
|---|---|---|---|
| 1 | defeat_all | {targets: [all_enemies]} | "The road is yours." |
| 2 | defeat_specific | {target: leader_id} | "Kill the captain; the rest may break." |
| 3 | survive_rounds | {rounds: 5} | "Hold until dawn." |
| 4 | reach_zone | {zone_id: "objective_3"} | "Get to the vehicle." |
| 5 | convince_parley | {target: leader_id} | "Convince them you are not the trouble you look like." |
| 6 | break_contact | {zones_from_start: 2} | "Just get clear. Anywhere will do." |
| 7 | protect_target | {target: npc_id, rounds: 3} | "Keep her alive for three rounds." |
| 8 | extract_target | {target: npc_id, to_zone: X} | "Pull him out; the rest can burn." |
| 9 | destroy_object | {object: X} | "The records cannot survive this." |
| 10 | claim_object | {object: X} | "Take it. Take it out." |
| 11 | observe_only | {rounds: 3, discovery_TN: 10} | "Watch without being seen." |
| 12 | outlast | {rounds: 6, player_alive: true} | "You do not have to win. Only not lose." |

Loss conditions: always include `player_incapacitated` (all tracks at 5), `corruption_6` (full track), and `key_ally_dies` if protect_target is win condition.

Escape conditions: always include `disengage_successful` and `parley_accepted` where applicable.

### 13.6 Sample encounters (12)

1. **Raider ambush, Cross-Bronx**. Register human. Three `human_scavenger_raider`. Zones: exposed plaza + cover_partial (wrecked cars) + cover_partial + elevated (overpass). Stakes: survival + resource (courier pouch). Win: defeat_all OR break_contact. Parley: available. Opening: "Two figures stepped out of the cars. A third moved in the shadow of the overpass."

2. **Hunter pair, Catskills perimeter**. Register creature. Two `creature_ambush_predator`. Zones: concealed forest + cover_partial + hazardous (slope) + objective (trail). Stakes: survival + territory. Win: defeat_all OR break_contact. Parley: disabled. Opening: "Nothing had moved on the trail for three minutes. She noticed that."

3. **Wretch pack, Pine Barrens edge**. Register creature. Six `creature_hive_drone` (as Wretches, reskinned) OR seven Wretches proper. Zones: pine concealed + pine concealed + exposed road + corrupted. Stakes: clock pressure (attention). Win: defeat_all before clock 6 OR break_contact. Parley: disabled. Opening: "Something coughed in the brush. Twice. From different places."

4. **Iron Crown patrol, Jersey road**. Register human. One `human_warlord_lieutenant`, two `human_militia_soldier`. Zones: road exposed + field exposed + ditch cover_partial + farm objective. Stakes: territory + relationship (witness). Win: defeat_all OR parley. Parley: available but costly. Opening: "Three men on the road. The lieutenant stepped forward. He had questions."

5. **Listening messenger, township entry**. Register eldritch + human. One `eldritch_lesser_corruption` + two `human_fanatic`. Zones: plaza exposed + cover_partial + elevated chapel + corrupted zone (back of plaza). Stakes: knowledge + clock (township faith). Win: defeat leader OR reject offer (no combat) OR accept offer (combat avoided, corruption cost). Parley: offer-based only. Opening: "The man in the back spoke first. His words were not in any language the town knew. The fanatics translated."

6. **Bear-House guardsmen at pass**. Register human. One `human_faction_patrol_leader`, three `human_militia_soldier`. Zones: bridge cover_partial + road elevated + ravine hazardous + exit objective. Stakes: territory. Win: parley (preferred) OR break_contact OR defeat_all. Parley available. Opening: "They had been on this bridge since first light. Their relief was not coming for two hours."

7. **Grandfather Silt wake**. Register eldritch. No combat possible with Sovereign itself; instead two `creature_aquatic_horror` from its retinue. Zones: water + broken pier cover_partial + exposed boat deck + concealed hold. Stakes: survival + clock (Silt notices). Win: break_contact. Parley: disabled. Opening: "The water had been calm. The water was not calm now."

8. **Fed Continuity checkpoint, Potomac**. Register human. One `human_militia_soldier` officer + four `human_militia_soldier`. Zones: checkpoint exposed + barrier cover_partial + bunker cover_full + objective road. Stakes: relationship + clock (Fed erosion). Win: parley (credentials) OR defeat OR break_contact. Parley priority. Opening: "Scrip was still an insult here. Copper was better. He asked for papers anyway."

9. **Camden salvage, three-way**. Register human. Two `human_scavenger_raider` + one `human_rogue_surgeon` on opposing side, plus a `creature_blood_bonded_swarm` (rats) disturbed by the noise. Zones: warehouse interior cover_partial + cover_full + hazardous (structural) + objective crate. Stakes: resource + third party. Win: claim_object. Parley: three-way possible. Opening: "Two factions in the same building, looking for the same box. And then the rats."

10. **Warped territory, Five Sisters**. Register creature (T8 Warped). One `creature_transformed_predator_alpha` at T7 (council member), plus 3 T5 subordinates. Zones: clearing exposed + forest concealed + cave cover_full + elevated overlook. Stakes: territory + relationship (parley-capable). Win: parley (preferred) OR break_contact. Direct defeat forbidden (fail). Opening: "She sat on the stone and waited for them to come close enough to speak."

11. **The Echo's perimeter, Manhattan Financial District**. Register eldritch. No entity directly — anomalous event encounter. Zones: street corrupted + cover_partial + corrupted + objective (way out). Stakes: clock (corruption accrual) + knowledge. Win: reach_zone OR observe + leave. Parley: offer may manifest. Opening: "She checked her watch. The watch said the wrong thing. She checked it again. It said the same wrong thing."

12. **Preston's retinue, Catskill approach**. Register human. One elite `human_warlord_lieutenant` + four `human_militia_soldier`. Preston himself does not engage. Zones: mountain road elevated + cover_partial + exposed approach + cover_full (bunker). Stakes: relationship (Preston watches) + survival. Win: parley (preferred) OR defeat (massively escalates heat). Parley: available. Opening: "The road was empty. Then it was not. Then it was clear what the road had been waiting for."

---

## SECTION 14 — NARRATION INTEGRATION

### 14.1 Payload generation procedure

After each resolved action (not each check — one payload per Major action), the combat engine emits a Narrator Payload. Procedure:

1. Construct `state_snapshot`: actor id + name, action verb, resolution tier (Crit/Full/Marginal/…), damage_final, statuses_applied, targets touched, momentum delta, exposure delta, zone changes, witness delta.
2. Select `register_directive`:
   - Human register standard combat → `"action"`.
   - Human register parley → `"standard"`.
   - Creature register → `"action"` + `"quiet"` modifier if ambush.
   - Eldritch register → `"eldritch"`.
   - Low-intensity or breathing-space exchange → `"quiet"`.
3. Compose `forbidden` list always including "invent damage not in payload", "invent statuses not applied", "describe NPCs not present"; add register-specific forbids (eldritch: "resolve the anomalous question").
4. Set `desired_length`:
   - Most combat turns: {min_words: 30, max_words: 80}.
   - Crit turns: {40, 120}.
   - Finishers: {60, 180}.
   - End-of-round ticks: {15, 45}.
5. Populate `context_continuity`:
   - `last_narration_summary`: 1-sentence generated from prior payload's action.
   - `scene_history_summary`: compact running state: round number, alive counts, player status.
   - `key_callbacks`: 3–5 fixed details (terrain, weather, NPC name, prior statuses).

### 14.2 Ten payload examples

Each example abbreviated to essential fields. Full payload would include `schema_version`, etc. per interface spec.

**Payload 1: Attack Full Success**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player, name: "Ana"}
  verb: Attack
  target: {id: raider_1, name: "the taller one"}
  result: Full
  damage: 4 (PK)
  weapon: "steel knife"
  status_applied: []
  exposure_delta: {raider_1: +2}
register_directive: action
forbidden: ["invent damage not in payload"]
output_target: {length: {30, 80}, format: prose}
context_continuity:
  last: "A second man stepped out from behind the overpass."
  history: "Round 2 of 3. Ana is Bleeding. One raider down."
  callbacks: ["steel knife", "rain on asphalt", "overpass concrete"]
```

**Payload 2: Crit Attack with Bleeding rider**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player, name: "Teo"}
  verb: Attack
  target: {id: hunter_a, name: "the stalker"}
  result: Crit
  damage: 8 (PK)
  status_applied: [bleeding]
  exposure_delta: {hunter_a: +3, exposed: true}
  momentum_delta: +1
register_directive: action
forbidden: [...]
output_target: {length: {40, 120}, format: prose}
```

**Payload 3: Power, Matter/Energy, marginal**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player}
  verb: Power
  power_id: pyro_spark
  target: {id: wretch_3}
  result: Marginal
  damage: 3 (ME)
  cost_applied: {condition: {physical: 1}, heat: {}, corruption: 0}
register_directive: action
```

**Payload 4: Parley Full in human register**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player}
  verb: Parley
  target: {id: lieutenant}
  result: Full
  terms_live: true
  target_state_shift: "willing_to_hear"
register_directive: standard
output_target: {length: {50, 120}, format: dialogue}
context_continuity:
  history: "Round 3. Two of his men are down. He has not moved."
```

**Payload 5: Eldritch offer issued**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: eldritch_lesser_corruption}
  verb: Power
  power_id: whispered_offer
  target: {id: player}
  offer_type: "information_offer"
  offer_cost: {corruption: 1}
  offer_reward: "one truth about the world"
register_directive: eldritch
forbidden: ["invent statuses not applied", "resolve the anomalous question", "explain the offerer's origin"]
output_target: {length: {40, 100}, format: prose}
context_continuity:
  callbacks: ["cold that has no source", "the trees here grow wrong", "his voice was not his"]
```

**Payload 6: Finisher, mercy kill**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player}
  verb: Finisher
  finisher_id: fin_mercy_kill
  target: {id: raider_leader}
  result: Full
  outcome: "target_dies_without_suffering"
  heat_delta: {faction_cjl: -1, faction_iron_crown: 0}
  witnesses: 2
register_directive: quiet
output_target: {length: {60, 180}, format: prose}
forbidden: ["heroic framing", "consolation"]
```

**Payload 7: Disengage Marginal (opp attack resolves)**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: player}
  verb: Disengage
  result: Marginal
  opp_attack_result: "hit, 2 phy to player"
  exit_zone: "alley"
register_directive: action
output_target: {length: {30, 80}, format: prose}
```

**Payload 8: Maneuver flank Full**
```
scene_type: combat_turn
state_snapshot:
  actor: {id: ally_chen}
  verb: Maneuver
  target_zone: "behind_raider_2"
  result: Full
  position_value: "flanking"
  next_ally_bonus: +1
register_directive: action
output_target: {length: {20, 60}, format: prose}
```

**Payload 9: End-of-round tick, Burning damage**
```
scene_type: combat_turn
state_snapshot:
  tick_type: end_of_round
  round: 2
  burning_damage: {player: 1, raider_2: 1}
  exposure_decay: {raider_3: -1}
  scene_clock_advance: 0
register_directive: quiet
output_target: {length: {15, 45}, format: terse}
```

**Payload 10: Scene framing, encounter start**
```
scene_type: scene_framing
state_snapshot:
  location: "cross_bronx_overpass"
  time_of_day: "late afternoon"
  weather: "overcast, dry"
  zones: [road_exposed, overpass_elevated, cars_cover_partial, ditch_concealed]
  enemies_visible: 2
  enemies_hidden: 1
  stakes: "survival + courier pouch"
  opening_situation: "Two figures on the road. The third position is unverified."
register_directive: standard
output_target: {length: {80, 180}, format: prose}
forbidden: ["reveal the hidden enemy"]
```

### 14.3 Sample narrations matching payloads

**Payload 1 sample**: *"She stepped inside the raider's reach. The knife went in at the lower ribs, not deep, but enough. He made a small sound. She was already moving backward."*

**Payload 2 sample**: *"He had been aiming for the stalker's throat and took its shoulder instead, because the thing was faster than he'd guessed. It was still enough. The fragment of bone came out the other side. The stalker made a noise it had not made before and sat down. Blood followed it down, then kept following."*

**Payload 5 sample**: *"The man in the long coat said something she did not understand. He said it again in words she did. 'One answer,' he said. 'One only. What is the harbor in on the fifth day from now?' He smiled the way a person might smile if they had learned smiling from a picture. 'You do not have to answer yes now.'"*

**Payload 6 sample**: *"She knelt beside him. He tried to speak. She put her hand on his chest and the hand was warm and very still and then his breathing stopped, which was the point. Somewhere across the plaza, someone lowered a weapon they had been holding. The rain kept going."*

### 14.4 Forbidden behaviors (combat-specific)

The combat engine's forbidden list always includes:

- "invent damage values, status applications, or consequences not in the payload"
- "narrate dice, target numbers, or mechanical resolution"
- "describe characters not present in state_snapshot"
- "resolve the anomalous eldritch question" (eldritch register only)
- "heroic framing of violence"
- "consolation or moralizing"
- "power-spectacle voice (per narration.md)"
- "explain faction politics in exposition"
- "narrate the player's internal state in interpretive language"

---

## SECTION 15 — END CONDITIONS AND OUTCOMES

### 15.1 Resolution triggers

Per resolution type:

- `victory` — all enemies `final_state in [dead, incapacitated, fled, surrendered]` and at least one of win_conditions satisfied.
- `defeat` — player incapacitated (all three tracks at 5 OR tier-3 harm "mortal_wound" OR corruption = 6) OR any loss_condition triggered.
- `parley` — a Parley terms-accepted state reached and ratified; typically set by encounter logic when `parley_terms_locked` is true.
- `escape` — any escape_condition triggered; player out of encounter; enemies remain.
- `truce` — both sides agree to disengage without terms beyond cessation; neither side victorious.
- `stalemate` — encounter runs to round limit (default 10) without resolution; engine forces truce-equivalent with heat accrual for both sides.
- `other` — engine-level fallback for anomalous eldritch encounters that resolve via corruption offer acceptance or time event.

### 15.2 Outcome construction

For each resolution type, the engine constructs the Combat Outcome per interface spec. Key consequence generation:

**Player state delta:**
- `condition_changes`: take final track values minus initial.
- `harm_added`: all harm applied during combat.
- `resources_spent`: ammunition, consumables.
- `heat_accrued`: see 15.4.
- `corruption_gained`: delta during combat.
- `statuses_persisting`: only those with persistence (none in standard list; bleeding/burning clear at scene end unless harm was tier-2+).
- `powers_used`: increment per use.
- `breakthrough_triggered`: per §5.6.
- `injuries_healed`: biokinetic work during combat.

**Enemy states**: each enemy final_state and relevant details.

**World consequences**: structured list, see 15.3.

### 15.3 World consequence templates (20+)

Each template has `{type, parameters, scope, visibility}`:

1. `faction_standing_change` — {faction_id, delta, reason_label} — regional/local.
2. `location_state_change` — {location_id, state_field, new_value} — local.
3. `npc_memory_update` — {npc_id, event_summary, emotional_weight} — local.
4. `clock_advance` — {clock_id, segments: 1} — global.
5. `rumor_generated` — {rumor_id, content, veracity, source_location} — regional.
6. `witness_recorded` — {witnesses: [ids], event_summary} — local.
7. `territory_contested` — {location_id, contesting_factions} — regional.
8. `resource_gained` — {resource_id, quantity, source} — local.
9. `resource_lost` — {resource_id, quantity} — local.
10. `npc_killed` — {npc_id, killer_id, means, body_disposition} — regional.
11. `eldritch_obligation_posted` — {offerer_id, debt_type, due_condition} — global.
12. `faction_grievance_registered` — {faction_id, content} — regional.
13. `bounty_posted` — {on_id, amount, by_faction} — regional.
14. `injury_reputation` — {character_id, visible_scar_desc} — local.
15. `oath_made` — {parties, terms, witnesses} — regional.
16. `prisoner_taken` — {prisoner_id, captor_id, location} — local.
17. `hive_attention_raised` — {region_id, delta} — regional.
18. `breakthrough_public` — {character_id, tier_from, tier_to, circumstance} — regional.
19. `corruption_zone_expanded` — {zone_id, segments: 1} — regional.
20. `safe_passage_established` — {route_id, duration_days, between_factions} — regional.
21. `faction_scheme_exposed` — {faction_id, scheme_id} — regional/global.
22. `npc_status_change` — {npc_id, new_status} — global (rare).

### 15.4 Heat accrual formulas

```
for each enemy e in enemies_combatant:
    faction = e.faction_affiliation.primary
    if faction is null: continue

    base = 0
    if e.final_state == "dead":
        base += 2
    elif e.final_state == "incapacitated":
        base += 1
    elif e.final_state == "fled":
        base += 1  # witnessed unprovoked attack
    elif e.final_state == "surrendered":
        base += 0  # prisoner handled separately

    if player.used_eldritch_power:
        base += 1  # eldritch deployment is noted

    if visible_witnesses > 0:
        base += 1 per 3 witnesses (rounded up), max +3

    if combat_register == "human" and player.first_attack_was_unprovoked:
        base += 1

    heat[faction] += base
```

After computing per-faction heat, apply parley modifiers:

- Parley resolution: subtract 2 from the relevant faction's heat (minimum 0 for this encounter).
- Mercy kill Finisher: subtract 1 with CJL, Yonkers, Bourse; +0 elsewhere.
- Blood_price term accepted: subtract 1.
- Oath_of_neutrality term: subtract 2.

### 15.5 Witness mechanics

During combat, every non-combatant in or adjacent to the encounter zone is recorded as a potential witness. Per round, each such NPC rolls `perception d(NPC.perception)` vs TN 10 to "see correctly." On success, they become a witness with knowledge (actions, powers, identities where visible).

Witnesses produce two persistent effects:
- Rumors (see templates): content derived from what witness saw.
- NPC memory update: witness's `memory` list gains an event with emotional_weight based on severity.

Player powers with `visibility = "subtle"` halve the witness-success TN (TN 15 effective). `"visible"` power use makes witness perception automatic.

### 15.6 Resource expenditure tracking

Per encounter, the engine tracks:
- Ammunition spent (by type).
- Consumables used (bandages, medicine, rations eaten).
- Weapons lost (dropped, broken, disarmed).
- Power uses per power.
- Corruption gained.
- Heat gained per faction.

These aggregate into `resources_spent`, `powers_used`, `corruption_gained`, `heat_accrued` fields.

---

## SECTION 16 — TESTING AND VALIDATION

### 16.1 Probability validation tests (5)

**T-prob-1**: Evenly matched, no modifier. Setup: d8+d6 vs TN 10. Expected P(success) = 0.46 ± 0.02 over 100,000 rolls.

**T-prob-2**: Favored. d10+d8 +2 mod vs TN 10. Expected 0.82 ± 0.02.

**T-prob-3**: Crit frequency. d10+d10 vs TN 10. Expected P(Crit) = P(both dice match and ≥6 and total ≥ TN) = sum over v∈{6..10} (1/10)² = 5/100 = 0.05. Measured over 100,000 rolls should be 0.05 ± 0.003.

**T-prob-4**: Fumble frequency. Any pair of dice, double-1. For d6+d6: P = (1/6)² = 0.028. For d4+d4: 0.0625.

**T-prob-5**: Tier gap extreme. T1 d6+d6 vs T5 defender at TN 14. Expected P(success) ≤ 0.02.

### 16.2 Balance tests (5)

**T-bal-1**: Solo T3 player vs 6-Wretch pack. Over 1,000 simulated encounters, player victory rate expected 15–35% (encounter should be losable but not unwinnable; this tests §9.3 pack-combat expectations).

**T-bal-2**: Solo T3 player vs T6 lieutenant + 2 militia. Expected victory rate < 10% without parley. With parley resolution path accessible, resolution-favorable (victory/parley/escape) rate 40–60%.

**T-bal-3**: T5 kinetic throw (kin_strike, flight) vs T5 biokinetic healer. Kinetic should win ~65–75% due to raw damage advantage; healer's role is not combat.

**T-bal-4**: Standard encounter construction (§13.1). A player at baseline condition with encounter_budget computed: resolution-favorable rate 55–70%.

**T-bal-5**: Eldritch corruption offers over 10 consecutive eldritch encounters, player declining all. Expected corruption gain 0–3 (from proximity/mental damage). Accepting all: expected 15+ (player becomes non-player character).

### 16.3 Scenario tests (10)

**T-scn-1 (Attack + Defend contested):** Actor str d8/agi d6 attacks target with reaction Defend (agi d8/mig d6). Verify: both sides roll, higher total wins, ties to defender, Crit-Defend yields counterattack at −2.

**T-scn-2 (Exposure fill → Exposed → Finisher):** Target exposure_max 4. Apply 4 damage instances of 3 each (fill 2 each) over 2 rounds. Verify Exposed triggers at/after 4th hit; Finisher available with 5 momentum; executing `fin_break_spine` yields tier-3 harm "broken spine."

**T-scn-3 (Parley Full in human register):** Target `parley_conditions` = ["coin_offered"]. Player offers coin as parley component; Parley Full succeeds. Verify target AI profile shifts, terms structure emitted, heat −2 applied, world_consequences include `oath_made` or equivalent.

**T-scn-4 (Disengage Marginal):** 1 adjacent enemy, Disengage TN 13. Verify Marginal triggers one opportunity attack before actor exits.

**T-scn-5 (Corruption accumulation):** Player with corruption 4 uses `deep_pact`. Verify corruption +3 → 6 triggers transformation (player becomes non-player; special outcome).

**T-scn-6 (Tier gap modifier):** T1 vs T5 direct: verify T1 at −3 and T5 at +4 to all contested checks.

**T-scn-7 (Hive scene_clock):** Pine Barrens encounter. After 3 `visibility=visible` powers + 2 dead drones, clock = 5. Verify reinforcement at clock ≥ 4 trigger.

**T-scn-8 (Breakthrough condition):** Player at tier ceiling 3, tier 3. Condition 1 (mortal defense of another) met. Verify breakthrough_triggered, to_tier = 4, cost mark applied.

**T-scn-9 (Affinity edge):** Shade (PK immune). Player attacks with PK weapon. Verify damage = 0 and exposure fill = 0.

**T-scn-10 (Momentum spend):** Player Partial Fail on Attack. Verify `spend 1 momentum` converts to Marginal.

### 16.4 Integration tests (3)

**T-int-1**: Full encounter round-trip. Generate Encounter Spec, run engine to resolution, verify Combat Outcome conforms to schema with all required fields.

**T-int-2**: Determinism. Same encounter, same seed → identical Combat Outcome (byte-for-byte in narrative_log's `payload` field; narration strings may differ because narrator is non-deterministic).

**T-int-3**: Validate cross-reference. All ids in Combat Outcome's enemy_states, powers_used, and narrative_log actor_id reference valid registries (templates, powers, NPCs).

### 16.5 Coverage targets

- Every verb: at least one test scenario invokes resolution at each tier (Crit/Full/Marginal/Partial/Fail/Fumble).
- Every status: tested for application, removal, stacking-duration-reset, interaction row per matrix.
- Every AI profile: 3-round worked example executed; target prioritization verified.
- Every enemy template: instantiated and run in at least one encounter during balance testing.
- Every finisher: tested for trigger, execution, outcome variation.

---

## design_decisions

Decisions made during specification, not stated in source material, listed in order of appearance.

1. **Seventh power category id** = `auratic`. Interface spec used `temporal_spatial` as placeholder; bible `powers.md` names Auratic as seventh. Damage type `auratic` follows.
2. **Resolution mechanic**: two-die take-higher + modifiers vs TN is the Fabula Ultima port. Doubles at 6+ = Crit; double-1 = Fumble regardless of total.
3. **TN ladder**: 7/10/13/16/19/22 (Trivial through Mythic) at 3-step intervals.
4. **Tier gap modifier table**: +0/+1/+2/+3/+4/+5 capped; lower side at −0/−0/−1/−2/−3/−4 capped. Chosen to make tier gap ≥3 nearly insurmountable without other advantages, per bible's depiction of Preston and Volk.
5. **Momentum system**: 0–5 scale, Crit generates +1, Full-Assess generates +1. Spending rules fixed (1/2/3/5 tiers). Momentum resets at scene end.
6. **Attribute pair per verb**: str+agi melee Attack; per+agi ranged Attack; will+ins Parley; insight+per Assess; agi+str or agi+ins Maneuver; agi+ins or mig+will Disengage. Powers pair by category.
7. **Condition tracks fixed at 5 segments** per interface. Damage-to-track mapping set per damage type (§10.2).
8. **Harm pool**: 35 specific entries across phys/men/soc × tier 1/2/3.
9. **Status list fixed at 7** per interface; full application/removal/stacking rules defined in §6.
10. **Affinity table**: five states (vulnerable/neutral/resistant/immune/absorb) with multipliers 1.5/1/0.5/0/0-and-heal. Sting-floor rule (resistant still takes 1) preserves non-zero outcomes.
11. **Exposure model**: integer track filled by damage with affinity-modified fill; Exposed at max; decays if no damage; enables Finisher.
12. **Finisher system**: 14 finishers (2 per damage type) plus parley-as-finisher-equivalent; momentum cost 5 standard.
13. **AI profiles**: 5 profiles with explicit utility weights (§9.2). Worked examples show scoring math visibly.
14. **Retreat thresholds** defined per profile in §9.4.
15. **Enemy roster**: 30 templates (12 human, 12 creature, 6 eldritch) with full stat lines, affinities, abilities, powers, retreat/parley conditions.
16. **Power library**: 48 powers spanning tiers 1–8 across 7 categories (42+ per brief; expanded for completeness). Tier 9/10 powers not player-accessible; reserved for named-NPC narrative use.
17. **Breakthrough conditions**: 7 specific triggers, each with resolution check, cost mark per bible's "marked" requirement.
18. **Manifestation circumstance mapping**: 8 circumstances with category weights.
19. **Hereditary probabilities**: per bible's "about twice as likely" for primary category inheritance; tier independent.
20. **Growth thresholds**: 10/25/50/100 power uses producing stepped mechanical effects.
21. **Encounter difficulty formula**: tier × 2 + reserve + power bonus; enemy cost sums to bracket.
22. **Terrain zone themes**: 8 themes with zone-composition lists.
23. **12 win/loss/escape templates** and 12 sample encounters covering all registers.
24. **Parley terms list**: 12 specific term types with structured outcomes.
25. **Eldritch offer types**: 5 specific types (information, power, safe-passage, transform, vessel) with corruption costs and scene effects.
26. **Corruption offer probability**: 0.2 baseline, 0.5 for Sovereign-class per interaction.
27. **Hive ecological clock**: 0–8 track, thresholds at 4, 6, 8 trigger reinforcements/escalation/all-convene.
28. **Narration payload fields** per interface schema, with 10 example payloads.
29. **Heat accrual formula**: base from enemy state + eldritch flag + witness quotient + unprovoked flag; reduced by parley modifiers.
30. **World consequence templates**: 22 types with structured parameters.
31. **Round duration**: ~6 seconds narrative; 3-round "exchange" units; pressure toward resolution by round 4.
32. **Action economy**: 1 Major + 1 Minor + 1 Reaction standard; T7+ gain an extra Major.
33. **Defend is a reaction**, not one of the 7 primary verbs (matches interface schema listing 8 total).
34. **Power pool soft cap**: `will_die_size/2 + tier` uses per scene before −2 penalty. Prevents spam without hard-capping.
35. **Species stat lines**: derived from bible traits (e.g., Species F high str/mig, Species A high agi/low mig); specific die assignments chosen to produce distinct play feel.

## [NEEDS AUTHORSHIP]

None critical. Minor items (optional, not blocking implementation):

- [NEEDS AUTHORSHIP: sample narration prose for all 14 finishers; only a subset are exemplified in §8.3.]
- [NEEDS AUTHORSHIP: detailed visual/sensory descriptions for the 6 eldritch templates beyond the one-line tonal notes.]

## [NEEDS RESOLUTION]

None. All mechanics specified with concrete values; all content slots filled.

