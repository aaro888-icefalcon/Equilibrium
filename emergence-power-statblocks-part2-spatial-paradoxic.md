# Emergence Power Statblocks — Part 2: Spatial & Paradoxic

**Scope.** This file contains full 8-mode statblocks for the Spatial (30 powers) and Paradoxic (30 powers) broads, completing the 200-power library begun in `emergence-power-statblocks.md` (Somatic, Cognitive, Material, Kinetic — 140 powers, contains internal duplication that will be cleaned in a final audit pass).

**Authority.** Rev 3 §4 schema-compliant. Formatting matches Part 1.

**Format per power:**
```
**Power Name** — pair_role | playstyles | register_gating
Identity: one sentence.

CAST_N | action | pool | additional_cost | scope | range | duration | families
  Effect / Parameters / Playstyles / Hook.

RIDER_X | type/sub_category | compat | pool | restrictions
  Effect outcome-parasitic / Playstyles / Combo.

CAPSTONE (authored: OPTION) | cost | scope | range | duration | families
  Signal / Viability / Effect / Parameters / Playstyles.

ENHANCED_RIDER (authored: variant on rider_X) | cost
  Shift / Effect / Combo.
```

**Posture tags:** R3 = Parry/Block/Dodge compatible; R2 = two; R1 = one; A = Aggressive-keyed.

---

# BROAD: SPATIAL

Spatial powers manipulate location, distance, and boundaries. Register gating: predominantly Human; Creature access limited (atavistic short-range phasing/teleports); Eldritch strong in Translative, Phasing, and Gateway subcategories.


## Sub-category 4.21 — Translative (6 powers)

---

**Teleportation** — Primary | Skirmisher, Assassin | Human, Eldritch
Identity: Instantaneously move across distance.

CAST_1 | Minor | 2p | — | self | medium | instant | movement
  Effect: short hop — teleport up to 10m to seen location.
  Parameters: distance=10m, line_of_sight=required.
  Playstyles: Skirmisher. Hook: reactive mobility.

CAST_2 | Major | 3p | — | self | far | instant | movement, action-economy
  Effect: combat teleport — teleport 25m; gain +1 to next attack roll this turn.
  Parameters: distance=25m, next_attack=+1.
  Playstyles: Skirmisher, Assassin. Hook: repositioning strike.

CAST_3 | Major | 4p + 1phy + scene_use | self + touched_ally | far | instant | movement, meta
  Effect: group blink — teleport self + 1 touched ally 25m.
  Parameters: distance=25m, ally_carry=1, limit=1/scene.
  Playstyles: Support, Skirmisher. Hook: rescue extraction.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition becomes teleport (ignore terrain, break engagement).
  Playstyles: Skirmisher. Combo: engagement_break.

RIDER_B | posture/reactive_defense | R1 (Dodge) | 0p passive
  Effect: once per round in Dodge posture, a hit that would land instead misses (blink-avoid).
  Parameters: auto_miss=1_per_round, posture=dodge.
  Playstyles: Skirmisher. Combo: dodge_blink.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks gain +1 damage after teleport this round; on_Crit target exposed.
  Playstyles: Assassin. Combo: blink_strike.

CAPSTONE (authored: STEPPED PATHS) | 5p + 1phy + scene_use | — | self | extreme | scene | movement, meta
  Signal: "Distance is advisory."
  Viability: setup_dependent.
  Effect: scene: teleport up to 15m as Minor action each round; always available.
  Parameters: distance=15m, cost=minor, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 1p
  Shift: reinforce.
  Effect: Crit after teleport also applies exposed 2r and denies target Reposition next turn.
  Combo: assassin_lock.

---

**Blink Step** — Complement | Skirmisher, Defense | Human
Identity: Short repeated micro-teleports.

CAST_1 | Minor | 1p | — | self | close | instant | movement
  Effect: blink — teleport 3m any direction.
  Parameters: distance=3m.
  Playstyles: Skirmisher. Hook: reactive step.

CAST_2 | Minor | 1p | — | self | close | 1 round | movement, defense
  Effect: flickering step — +2 defense this round via positional jitter; can't be grappled.
  Parameters: defense=+2, grapple_immune=true, duration=1r.
  Playstyles: Skirmisher. Hook: engagement defense.

CAST_3 | Major | 3p | — | self | medium | 2 rounds | movement, defense
  Effect: scattered — 2r: can blink 3m as free action up to twice per round; -1 enemy attacks.
  Parameters: free_blinks=2_per_round, enemy_attack=-1, duration=2r.
  Playstyles: Skirmisher. Hook: scene mobility spike.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes one 3m blink (ignore line-of-sight for destination).
  Playstyles: Skirmisher. Combo: terrain_ignore_mobility.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: first melee attack per round against you suffers -2 to hit (jitter).
  Parameters: first_melee_penalty=-2.
  Playstyles: Skirmisher. Combo: evasion_first.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt can be made at 3m range via blink-step (effectively melee Disrupt).
  Playstyles: Skirmisher. Combo: blink_disrupt.

CAPSTONE (authored: INSTANT AWAY) | 5p + 1phy + scene_use | — | self | — | scene | movement, action-economy
  Signal: "I am never where they think."
  Viability: setup_dependent.
  Effect: scene: blink 3m as free action once per round; any attack that would hit can be negated by spending 1 pool (blink-avoid).
  Parameters: free_blink=1_per_round, avoid_cost=1p, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: jitter penalty now applies to ranged as well as melee first-attack.
  Combo: universal_first_defense.

---

**Group Teleport** — Complement | Support, utility | Human
Identity: Transport allies across distance.

CAST_1 | Major | 2p | — | self + touched_ally | medium | instant | movement
  Effect: shared hop — self + 1 touched ally teleport 10m.
  Parameters: distance=10m, allies=1, requires=touch.
  Playstyles: Support. Hook: two-person extraction.

CAST_2 | Major | 3p | — | ally_group (3 adjacent) | medium | instant | movement
  Effect: party shift — up to 3 adjacent allies teleport 15m.
  Parameters: distance=15m, allies=3, adjacent=required.
  Playstyles: Support. Hook: team reposition.

CAST_3 | Major | 4p + 1phy + scene_use | ally_group (5) | far | instant | movement, meta
  Effect: mass evacuation — 5 allies teleport up to 30m.
  Parameters: distance=30m, allies=5, limit=1/scene.
  Playstyles: Support. Hook: emergency team extract.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition carries 1 adjacent ally (both move together).
  Playstyles: Support, Skirmisher. Combo: drag_ally.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m gain +1 to Reposition rolls.
  Parameters: range=5m, reposition=+1.
  Playstyles: Support. Combo: party_mobility.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess for party — reveal hostile positions; allies gain +1 to next defense.
  Playstyles: Support. Combo: tactical_intel_setup.

CAPSTONE (authored: COLLECTIVE JUMP) | 5p + 1phy + scene_use | — | ally_group (visible) | extreme | instant | movement, meta
  Signal: "We leave together or not at all."
  Viability: setup_dependent.
  Effect: all visible allies teleport together up to 50m to a location you've seen.
  Parameters: allies=all_visible, distance=50m, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward combat extraction).
  Effect: Reposition+ally ability now also gives that ally +1 to their next action.
  Combo: rescue_strike.

---

**Return Anchor** — Complement | utility, Skirmisher | Human
Identity: Set a point; return to it instantly.

CAST_1 | Minor | 1p | — | self | — | scene | utility, meta
  Effect: set anchor — designate current location as anchor for scene.
  Parameters: anchor_set=true, duration=scene.
  Playstyles: utility, Skirmisher. Hook: setup.

CAST_2 | Major | 2p | — | self | extreme | instant | movement
  Effect: return — teleport to anchor from any distance.
  Parameters: distance=unlimited_to_anchor, requires_anchor=true.
  Playstyles: Skirmisher. Hook: safe retreat.

CAST_3 | Major | 3p + 1phy + scene_use | self + touched_ally | extreme | instant | movement
  Effect: pull-return — return to anchor with 1 touched ally.
  Parameters: ally_carry=1, requires_anchor=true, limit=1/scene.
  Playstyles: Support, Skirmisher. Hook: rescue return.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: know hostile presence within 20m of your anchor at all times.
  Parameters: range=20m_around_anchor, detect=hostile.
  Playstyles: Investigator. Combo: anchor_intel.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition can occur toward anchor at double distance.
  Playstyles: Skirmisher. Combo: anchor_mobility.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess anchor area (even if not visible) reveals one fact about current state there.
  Playstyles: Investigator. Combo: distant_intel.

CAPSTONE (authored: PERSISTENT ANCHOR) | 4p + 1phy + scene_use | — | self | — | arc | meta, utility
  Signal: "The thread from me to home never breaks."
  Viability: setup_dependent.
  Effect: anchor persists across scenes within an arc; return available as Minor action (once per combat).
  Parameters: duration=arc, return_cost=minor, per_combat=1, limit=1/scene_to_set.
  Playstyles: utility, Skirmisher.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 1p
  Shift: branch (toward combat use).
  Effect: Reposition toward anchor also gains +1 to next attack if anchor is behind enemy line.
  Combo: flanking_mobility.

---

**Long Teleport** — Complement | utility, narrative | Human, Eldritch (rare)
Identity: Travel far in single jump.

CAST_1 | Major | 3p + 1phy | self | extreme | instant | movement
  Effect: long jump — teleport up to 100m (line-of-sight or known location).
  Parameters: distance=100m, requires=known_or_visible.
  Playstyles: utility. Hook: out-of-combat traversal, scene relocation.

CAST_2 | Major | 4p + 2phy + scene_use | self | off-map | instant | movement, meta
  Effect: city-hop — teleport to a known location within the same city/region (narrator-adjudicated).
  Parameters: scope=known_city_location, limit=1/scene.
  Playstyles: utility, narrative. Hook: narrative travel.

CAST_3 | Major | 5p + 2phy + scene_use | self + ally_group (3) | extreme | instant | movement, meta
  Effect: group long jump — 3 allies teleport up to 100m.
  Parameters: distance=100m, allies=3, limit=1/scene.
  Playstyles: Support. Hook: party relocation.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess scouts a remote location (reveal tactical layout).
  Playstyles: Investigator. Combo: pre-travel_scout.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition gains +5m distance if terrain permits line-of-sight.
  Playstyles: Skirmisher. Combo: extended_mobility.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect space-distorting effects (other teleporters, gateways) within 30m.
  Parameters: range=30m, detect=spatial_distortion.
  Playstyles: Investigator. Combo: counter_spatial.

CAPSTONE (authored: WORLD-STEPPER) | 5p + 2phy + scene_use | — | self | unlimited | instant | movement, meta
  Signal: "No place on earth is far from me."
  Viability: setup_dependent (location must be known/previously visited).
  Effect: teleport to any known location on continental scale; 2 phy cost.
  Parameters: scope=any_known_location, limit=1/scene.
  Playstyles: utility, narrative.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward intel).
  Effect: scout Assess also reveals hostile count and approximate strength.
  Combo: recon_mastery.

---

**Random Teleport** — Complement | Trickster, Glass Cannon | Human, Eldritch
Identity: Uncontrolled or partially uncontrolled jump.

CAST_1 | Minor | 1p | — | self | medium | instant | movement, meta
  Effect: chaotic blink — teleport 3-10m in random direction (narrator roll).
  Parameters: distance=3d8_meters, direction=random.
  Playstyles: Trickster. Hook: unpredictable evasion (works against high-intel enemies).

CAST_2 | Major | 2p | — | self | far | instant | movement, defense
  Effect: panic jump — teleport 15m in random safe direction; +2 to defense this round.
  Parameters: distance=15m, direction=narrator_safe, defense=+2_this_round.
  Playstyles: Glass Cannon, Skirmisher. Hook: emergency escape.

CAST_3 | Major | 3p + 1phy | self | extreme | instant | movement, meta
  Effect: fate-jump — teleport to narratively significant location (narrator chooses; low-to-high risk).
  Parameters: scope=narrator_significant, risk=variable.
  Playstyles: Trickster, narrative. Hook: narrative wildcard.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: when hit by a damaging attack, 25% chance to blink 3m randomly (damage reduced by half on trigger).
  Parameters: trigger_chance=25%, damage_reduction_on_trigger=50%.
  Playstyles: Skirmisher, Glass Cannon. Combo: panic_defense.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes 50% chance of bonus 3m random blink.
  Playstyles: Trickster. Combo: erratic_mobility.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Crit attacks trigger a random 3m blink to self post-attack.
  Playstyles: Trickster. Combo: hit_and_run_chaos.

CAPSTONE (authored: ROULETTE) | 4p + 1phy + scene_use | — | self | scene | scene | meta, defense
  Signal: "Even I don't know where I'll be."
  Viability: conditional_no_roll (triggers on each hit received).
  Effect: scene: each time you're hit, 50% chance to teleport 5m in random safe direction and the damage that triggered blink is negated.
  Parameters: trigger=each_hit, chance=50%, blink=5m, duration=scene, limit=1/scene.
  Playstyles: Trickster, Glass Cannon.

ENHANCED_RIDER (authored: chaining on RIDER_C) | 1p
  Shift: branch (toward sustained chaos).
  Effect: Crit-triggered blink also applies *confused* (via scrambling their expectations) to the target they just struck.
  Combo: chaos_strike_status.

---

## Sub-category 4.22 — Phasing (6 powers)

---

**Intangibility** — Primary | Tank, Skirmisher | Human, Eldritch
Identity: Become partly insubstantial; pass through solids.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: partial phase — -2 physical damage this round; can pass through one thin barrier.
  Parameters: physical_reduction=-2, barrier_pass=1_thin, duration=1r.
  Playstyles: Tank, Skirmisher. Hook: reactive defense.

CAST_2 | Major | 2p | — | self | — | scene | defense, stat-alteration
  Effect: ghost-state — scene: -1 all physical damage; pass through solids by spending 1p per barrier; can't attack while fully phased.
  Parameters: physical_reduction=-1, barrier_pass_cost=1p, attack_while_phased=false, duration=scene.
  Playstyles: Tank, utility. Hook: scene defense + infiltration.

CAST_3 | Major | 3p + 1phy + scene_use | self | — | scene | defense, meta
  Effect: selective phase — scene: once per round, negate one incoming attack entirely (phase through the damage).
  Parameters: damage_negate=1_per_round, duration=scene, limit=1/scene.
  Playstyles: Tank. Hook: heavy defensive toggle.

RIDER_A | posture/reactive_defense | R2 (Parry, Dodge) | 0p passive
  Effect: -1 physical damage while posture is active.
  Parameters: physical_reduction=-1.
  Playstyles: Tank. Combo: continuous_phase_armor.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition passes through walls/barriers (up to 1m thickness).
  Playstyles: Skirmisher, utility. Combo: barrier_mobility.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks ignore -2 cover/armor step.
  Playstyles: Assassin, Brawler. Combo: cover_ignore_strike.

CAPSTONE (authored: TRUE GHOST) | 5p + 2phy + scene_use | — | self | — | scene | defense, meta
  Signal: "They strike only air."
  Viability: setup_dependent.
  Effect: scene: immune to physical damage; can attack with half effect (treat attacks as applying half damage/effects); -2 agi.
  Parameters: physical_immune=true, attack_scale=0.5, agi_delta=-2, duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: reactive_defense now also reduces energy damage by -1 (not just physical).
  Combo: universal_phase_armor.

---

**Dimensional Step** — Complement | Skirmisher, utility | Human, Eldritch
Identity: Step through adjacent dimensional layer briefly.

CAST_1 | Minor | 1p | — | self | close | instant | movement
  Effect: side-step — move 5m in any direction, ignoring terrain and line-of-sight.
  Parameters: distance=5m, ignore=terrain_and_sight.
  Playstyles: Skirmisher. Hook: unobstructed movement.

CAST_2 | Major | 2p | — | self | close | 1 round | defense, movement
  Effect: out-of-phase — 1 round: cannot be targeted by attacks; cannot attack.
  Parameters: untargetable=true, attack_disabled=true, duration=1r.
  Playstyles: Skirmisher, Tank. Hook: emergency invulnerability.

CAST_3 | Major | 3p + 1phy | self | medium | instant | movement, meta
  Effect: side-slip strike — step 10m to position + next attack +2 and exposes target.
  Parameters: distance=10m, next_attack=+2, target_exposed=true.
  Playstyles: Assassin, Skirmisher. Hook: positional strike.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition can ignore one major obstacle (wall, pit, enemy line).
  Playstyles: Skirmisher. Combo: obstacle_bypass.

RIDER_B | posture/reactive_defense | R1 (Dodge) | 0p passive
  Effect: while in Dodge, ranged attacks miss on a 4+ on 2d6 (side-slip).
  Parameters: miss_chance=2_in_3, posture=dodge, scope=ranged.
  Playstyles: Skirmisher. Combo: ranged_evade.

RIDER_C | strike | restriction: Quick attacks only | 1p
  Effect: on_Full Quick attacks are preceded by a 3m side-step (attacker's choice of direction).
  Playstyles: Skirmisher, Assassin. Combo: side_step_strike.

CAPSTONE (authored: PHASE WALKER) | 5p + 1phy + scene_use | — | self | — | scene | movement, meta
  Signal: "Between becomes my home."
  Viability: setup_dependent.
  Effect: scene: can side-step 5m as free action once per round; immune to attacks-of-opportunity.
  Parameters: free_side_step=1_per_round, aoo_immune=true, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 1p
  Shift: branch (toward assassin combo).
  Effect: side-step Quick attack also applies *bleeding* 1r on Crit.
  Combo: assassin_bleed.

---

**Through-Walls** — Complement | utility, Assassin | Human
Identity: Pass through walls specifically.

CAST_1 | Major | 2p | — | self | touch | instant | movement, utility
  Effect: ghost walk — pass through up to 1m of solid wall.
  Parameters: wall_thickness=1m.
  Playstyles: utility. Hook: infiltration.

CAST_2 | Major | 3p + 1phy | self + touched_ally | touch | instant | movement, utility
  Effect: shared phase — self + 1 touched ally pass through 1m of wall.
  Parameters: wall_thickness=1m, ally_carry=1.
  Playstyles: Support, Skirmisher. Hook: team breach.

CAST_3 | Major | 3p | — | enemy_single | close | 1 round | control, status
  Effect: phase-lock — target partially stuck in a wall 1r: *stunned* 1r + *exposed*.
  Parameters: status=stunned_1r_plus_exposed, requires=adjacent_wall.
  Playstyles: Controller, Assassin. Hook: terrain-dependent control.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition can pass through one wall ≤1m thick.
  Playstyles: Skirmisher, Assassin. Combo: wall_flank.

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess through walls reveals what's on the other side.
  Playstyles: Investigator. Combo: breach_intel.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks made after wall-traversal ignore -2 cover step.
  Playstyles: Assassin. Combo: breach_strike.

CAPSTONE (authored: OMNIPHASE) | 5p + 2phy + scene_use | — | self | — | scene | movement, meta
  Signal: "Walls are rumors."
  Viability: setup_dependent.
  Effect: scene: pass through any wall as Minor action; allies in 5m may do the same (costs them 1p each).
  Parameters: scope=any_wall, ally_option_cost=1p, duration=scene, limit=1/scene.
  Playstyles: utility, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 1p
  Shift: branch (toward coordinated breach).
  Effect: Assess-through-wall also grants the Assessor's ally +1 to next attack at that location.
  Combo: coord_breach.

---

**Air-Walk** — Complement | Skirmisher, utility | Human
Identity: Walk on air as if floor.

CAST_1 | Minor | 1p | — | self | — | scene | movement, stat-alteration
  Effect: stepping air — scene: treat air as floor for vertical movement (up to 10m elevation).
  Parameters: max_elevation=10m, duration=scene.
  Playstyles: Skirmisher. Hook: aerial mobility.

CAST_2 | Major | 2p | — | self | — | scene | movement, defense
  Effect: hover — scene: can stay at any elevation; +1 to ranged defense (aerial mobility).
  Parameters: hover=true, ranged_defense=+1, duration=scene.
  Playstyles: Skirmisher, Artillery. Hook: aerial combat.

CAST_3 | Major | 3p + 1phy + scene_use | self + ally (touched) | touch | scene | movement, meta
  Effect: sky-path — self + 1 ally can air-walk scene.
  Parameters: allies=1, duration=scene, limit=1/scene.
  Playstyles: Support. Hook: team aerial.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition can include vertical movement up to 5m.
  Playstyles: Skirmisher. Combo: aerial_reposition.

RIDER_B | posture/reactive_defense | R1 (Dodge) | 0p passive
  Effect: while airborne and in Dodge, +1 defense against melee.
  Parameters: melee_defense=+1_when_airborne, posture=dodge.
  Playstyles: Skirmisher. Combo: aerial_evade.

RIDER_C | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged attacks from airborne position gain +1 damage.
  Playstyles: Artillery. Combo: aerial_artillery.

CAPSTONE (authored: SKY-LORD) | 4p + 1phy + scene_use | — | self | — | scene | movement, meta
  Signal: "The ground is optional."
  Viability: setup_dependent.
  Effect: scene: permanent air-walk; dive attacks (Heavy from high position) gain +2 damage; enemies -1 to hit airborne you.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 1p
  Shift: reinforce.
  Effect: aerial ranged also ignores 1 step of cover.
  Combo: aerial_cover_strike.

---

**Phasing Strike** — Primary | Assassin, Brawler | Human, Eldritch
Identity: Attacks pass through armor via phase.

CAST_1 | Minor | 1p | — | self | — | 1 round | damage, stat-alteration
  Effect: phase-sharpen — next melee attack ignores 1 step of armor/cover; +1 damage.
  Parameters: armor_ignore=1_step, damage=+1, duration=next_attack.
  Playstyles: Assassin, Brawler. Hook: setup strike.

CAST_2 | Major | 2p | — | enemy_single | close | instant | damage, status
  Effect: phase rend — Heavy attack: ignore all armor; 3 damage + *bleeding* 2r.
  Parameters: armor_ignore=full, damage=3, status=bleeding_2r, requires=heavy.
  Playstyles: Assassin. Hook: anti-armor spike.

CAST_3 | Major | 3p + 1phy | enemy_single | close | instant | damage, meta
  Effect: organ-strike — Heavy: save fortitude (TN 12) or +3 damage + *exposed*.
  Parameters: save_tn=12, damage_on_fail=+3, status_on_fail=exposed, requires=heavy.
  Playstyles: Assassin. Hook: lethal setup.

RIDER_A | strike | restriction: Quick, Heavy | 1p
  Effect: on_Full ignore 1 step of armor/cover; on_Crit ignore 2 steps + *bleeding* 1r.
  Playstyles: Assassin, Brawler. Combo: armor_bypass_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: counter-attacks (Parry Full) ignore 1 step of armor.
  Parameters: counter_armor_ignore=1_step.
  Playstyles: Tank, Brawler. Combo: phase_parry.

RIDER_C | strike | restriction: Finisher only | 1p
  Effect: on_Full Finisher ignores all armor.
  Playstyles: Assassin. Combo: finisher_phase.

CAPSTONE (authored: GHOST BLADE) | 5p + 1phy + scene_use | — | enemy_single | close | instant | damage, meta
  Signal: "Their armor protects nothing."
  Viability: offensive_swing.
  Effect: Heavy attack: ignore all armor + 4 damage + *bleeding* 3r + *exposed*.
  Parameters: damage=4, status=bleeding_3r_plus_exposed, requires=heavy, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: on_Full +1 damage (in addition to armor ignore); on_Crit +2 damage.
  Combo: null.

---

**Reverse Phase** — Complement | Controller, Anti-teleporter | Human (rare), Eldritch
Identity: Lock target's phase/teleport capability.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | 1 round | control
  Effect: anchor — target cannot teleport or phase for 1 round.
  Parameters: teleport_block=true, phase_block=true, duration=1r.
  Playstyles: Controller. Hook: counter-mobility.

CAST_2 | Major | 2p | — | zone (5m) | close | 2 rounds | control, terrain-alteration
  Effect: anchor zone — 5m area: no teleport/phase in or out for 2r.
  Parameters: area=5m, teleport_block=true, phase_block=true, duration=2r.
  Playstyles: Controller, Area Denier. Hook: area denial of mobility.

CAST_3 | Major | 3p + 1men + scene_use | all_visible | medium | scene | control, meta
  Effect: realm-lock — all visible enemies cannot teleport or phase for scene.
  Parameters: scope=all_visible_enemies, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene counter.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m cannot teleport or phase.
  Parameters: range=5m, spatial_block=true.
  Playstyles: Controller. Combo: aura_anti-spatial.

RIDER_B | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt cancels target's active spatial effect (phase, teleport-in-progress).
  Playstyles: Controller. Combo: spatial_disrupt.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect spatial effects (phasing, teleport, portals) within 30m.
  Parameters: range=30m, detect=spatial_effects.
  Playstyles: Investigator. Combo: counter-spatial_awareness.

CAPSTONE (authored: GROUNDED REALITY) | 5p + 1men + scene_use | — | zone (15m) | medium | scene | control, meta
  Signal: "Here, only legs carry you."
  Viability: setup_dependent.
  Effect: 15m zone scene: no teleport, phase, portal, or dimensional travel in or out.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch (toward full spatial shutdown).
  Effect: aura also prevents *all* Spatial broad powers (Reach, Gateway, Territorial effects) for enemies in range.
  Combo: total_spatial_denial.

---

## Sub-category 4.23 — Gateway (6 powers)

---

**Portal Creation** — Primary | utility, Controller, Skirmisher | Human, Eldritch
Identity: Create paired spatial portals.

CAST_1 | Major | 2p | — | zone (2m portal) | medium | 2 rounds | movement, utility
  Effect: short portal — two linked 2m portals up to 15m apart; passage through is free for anyone.
  Parameters: distance=15m, portal_size=2m, duration=2r.
  Playstyles: utility, Controller. Hook: battlefield mobility.

CAST_2 | Major | 3p + 1phy | zone (3m portal) | far | 3 rounds | movement, meta
  Effect: combat portal — linked 3m portals up to 30m apart; your allies may use without cost.
  Parameters: distance=30m, portal_size=3m, ally_pass_free=true, duration=3r.
  Playstyles: Support, Controller. Hook: team repositioning.

CAST_3 | Major | 4p + 1phy + scene_use | zone (5m portal) | extreme | scene | movement, meta
  Effect: scene portal — linked 5m portals at any distance for scene.
  Parameters: distance=unlimited_within_scene, portal_size=5m, duration=scene, limit=1/scene.
  Playstyles: utility, Controller. Hook: scene logistics.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition may deploy a brief 1-round portal to current destination.
  Parameters: portal_deploy=true, duration=1r.
  Playstyles: Support, Skirmisher. Combo: mobility_portal.

RIDER_B | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged attacks may originate from an active portal (from either endpoint).
  Playstyles: Artillery, Assassin. Combo: portal_shot.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect active portals or dimensional rifts within 30m.
  Parameters: range=30m, detect=portals.
  Playstyles: Investigator. Combo: portal_awareness.

CAPSTONE (authored: GATE MASTER) | 5p + 2phy + scene_use | — | zone (multiple) | extreme | scene | meta, utility
  Signal: "The world is a hallway I walk."
  Viability: setup_dependent.
  Effect: scene: maintain up to 3 paired portals simultaneously across the battlefield; pass through is Minor action.
  Parameters: portal_pairs=3, duration=scene, limit=1/scene.
  Playstyles: Controller, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 1p
  Shift: branch (toward ambush).
  Effect: portal-shot attacks also grant +2 to next Assess on the target (reading through the portal).
  Combo: portal_recon_strike.

---

**Dimensional Rift** — Primary | Controller, Area Denier | Human (rare), Eldritch
Identity: Tear in space; unstable portal or damaging rift.

CAST_1 | Major | 2p + 1men | zone (2m) | medium | instant | damage, status
  Effect: small tear — 2m rift: 3 damage to enemies in area + *exposed*.
  Parameters: area=2m, damage=3, status=exposed.
  Playstyles: Controller. Hook: AoE with secondary effect.

CAST_2 | Major | 3p + 1men | zone (5m) | medium | 2 rounds | damage, terrain-alteration
  Effect: unstable zone — 5m: 2 damage per round to all within; difficult terrain.
  Parameters: area=5m, per_round_damage=2, terrain=difficult, duration=2r.
  Playstyles: Area Denier. Hook: persistent hazard.

CAST_3 | Major | 4p + 2men + scene_use | enemy_single | medium | instant | damage, meta
  Effect: targeted rift — enemy save will (TN 13) or 5 damage + briefly displaced (Reposition 5m, narrator's choice of direction).
  Parameters: save_tn=13, damage=5, displacement=5m, limit=1/scene.
  Playstyles: Controller. Hook: displacement spike.

RIDER_A | strike | restriction: Power, Power_Minor | 1p
  Effect: on_Full rift-strikes deal +1 damage; on_Crit target briefly displaced (2m forced movement).
  Playstyles: Controller, Artillery. Combo: rift_displacement.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m take 1 damage per 2 rounds (rift leakage).
  Parameters: range=5m, damage=1, period=2r.
  Playstyles: Area Denier. Combo: rift_aura.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt applies *exposed* via local rift tear.
  Playstyles: Controller. Combo: disrupt_tear.

CAPSTONE (authored: WORLD WOUND) | 5p + 2men + scene_use | — | zone (10m) | medium | scene | damage, terrain-alteration
  Signal: "I open the world and let it bleed."
  Viability: offensive_swing.
  Effect: 10m rift-zone scene: 2 damage per round to enemies; terrain difficult; enemies save will (TN 12) each round or *shaken*.
  Parameters: area=10m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Full +2 damage (was +1); Crit displacement 4m (was 2m).
  Combo: null.

---

**Linked Portals** — Complement | Support, Trickster | Human
Identity: Set multiple anchor points; move between them.

CAST_1 | Minor | 1p | — | self | — | scene | utility
  Effect: set link point — designate current location as one of up to 3 linked points for scene.
  Parameters: link_points_max=3, duration=scene.
  Playstyles: utility. Hook: pre-positioning.

CAST_2 | Major | 2p | — | self | scene | instant | movement
  Effect: jump to link — teleport to any of your currently-set link points.
  Parameters: distance=to_link_point, requires=set_link.
  Playstyles: Skirmisher, Support. Hook: tactical repositioning.

CAST_3 | Major | 3p + 1phy + scene_use | ally_group (3) | medium | instant | movement, meta
  Effect: relay — 3 allies teleport to distinct link points (your choice).
  Parameters: allies=3, destinations=chosen_link_points, limit=1/scene.
  Playstyles: Support. Hook: team distribution.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition automatically sets a new link point at destination.
  Playstyles: utility. Combo: mobility_linking.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense hostile presence within 10m of any active link point.
  Parameters: range=10m_per_link.
  Playstyles: Investigator. Combo: perimeter_awareness.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess from one link point reveals state of another link point area.
  Playstyles: Investigator. Combo: distant_intel.

CAPSTONE (authored: WEB OF WAYS) | 4p + 1phy + scene_use | — | self | — | scene | meta, utility
  Signal: "The world becomes my map."
  Viability: setup_dependent.
  Effect: scene: up to 5 link points simultaneously; teleport between them as Minor action.
  Parameters: links_max=5, teleport_cost=minor, duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: awareness radius extends 15m per link point; also includes emotional state of detected hostiles.
  Combo: emotional_awareness.

---

**Summoning Path** — Complement | Support, Commander | Human, Eldritch
Identity: Open portal for allies to arrive.

CAST_1 | Major | 2p | — | zone (2m) | close | 1 round | utility, meta
  Effect: call ally — known ally within 100m can step through portal to you (1 ally).
  Parameters: ally_distance_max=100m, allies=1, requires_known=true.
  Playstyles: Support. Hook: reinforcement.

CAST_2 | Major | 3p + 1phy | zone (3m) | close | 2 rounds | utility, meta
  Effect: party summon — 3 known allies within 500m arrive through portal over 2r.
  Parameters: allies=3, distance_max=500m, duration=2r.
  Playstyles: Support, Commander. Hook: combat reinforcement.

CAST_3 | Major | 4p + 2phy + scene_use | zone (5m) | close | instant | meta, support
  Effect: emergency summon — any known living ally within any distance arrives immediately.
  Parameters: allies=1, distance=unlimited_within_known_contacts, limit=1/scene.
  Playstyles: Support, narrative. Hook: scene-changing reinforcement.

RIDER_A | parley | restriction: Negotiate only | 1p
  Effect: on_Full Negotiate via portal to distant ally — coordinate cross-scene actions.
  Playstyles: Diplomat, narrative. Combo: cross-scene_coord.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: summoned allies in 5m have +1 to defense on their arrival round.
  Parameters: range=5m, arrival_defense=+1.
  Playstyles: Support. Combo: safe_arrival.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess reveals condition and location of a known ally.
  Playstyles: Investigator, Support. Combo: ally_intel.

CAPSTONE (authored: RALLY CALL) | 5p + 2phy + scene_use | — | zone (5m) | close | scene | meta, support
  Signal: "We do not fight alone."
  Viability: setup_dependent (requires known allies exist to summon).
  Effect: scene: up to 3 known allies arrive via portal throughout scene (narrator adjudicates timing/ally-availability).
  Parameters: allies_max=3, duration=scene, limit=1/scene.
  Playstyles: Commander, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 1p
  Shift: branch (toward strategic coordination).
  Effect: Assess also transmits a brief message to the ally (one-way).
  Combo: tactical_coord.

---

**Delayed Portal** — Complement | Trickster, utility | Human, Eldritch
Identity: Set a portal to activate later.

CAST_1 | Minor | 1p | — | zone (2m) | close | scene | meta, utility
  Effect: set fuse — mark location; portal becomes available after 2 rounds.
  Parameters: activation_delay=2r, duration=scene.
  Playstyles: Trickster, utility. Hook: setup.

CAST_2 | Major | 2p | — | zone (3m) | close | scene | meta, movement
  Effect: timed gate — portal opens automatically in 3 rounds for 1 round; pairs to your current location.
  Parameters: auto_open=3r_delay, open_duration=1r, duration=scene.
  Playstyles: Trickster, utility. Hook: pre-setup escape.

CAST_3 | Major | 3p + 1phy + scene_use | zone (multiple) | medium | scene | meta, utility
  Effect: portal bomb — set 3 timed portals; each opens at round of your choice for 1r; any location you've been to in scene.
  Parameters: portals=3, each_duration=1r, duration=scene, limit=1/scene.
  Playstyles: Trickster. Hook: scene traps.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition also sets a delayed portal at departure location (2r delay, 1r duration).
  Playstyles: Trickster, Skirmisher. Combo: escape_route_setup.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense the remaining time and location of your delayed portals.
  Parameters: self_awareness=portal_state.
  Playstyles: utility. Combo: self_coordination.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks trigger one of your delayed portals to open immediately at current location.
  Playstyles: Trickster. Combo: attack_portal_combo.

CAPSTONE (authored: PORTAL TRAP) | 4p + 1phy + scene_use | — | enemy_single | medium | instant | control, meta
  Signal: "You stepped where I planned."
  Viability: offensive_swing.
  Effect: enemy in marked location save will (TN 13) or is pulled through portal to a location of your choice; *stunned* 1r.
  Parameters: save_tn=13, status=stunned_1r, limit=1/scene.
  Playstyles: Controller, Trickster.

ENHANCED_RIDER (authored: chaining on RIDER_C) | 1p
  Shift: branch (toward trickster combat).
  Effect: Full attack trigger also teleports you 3m in any direction via the portal.
  Combo: trick_escape_strike.

---

**Targeted Portal** — Complement | Assassin, Controller | Human, Eldritch
Identity: Direct a portal to send someone specific.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | instant | control
  Effect: short redirect — target save might (TN 11) or is moved 3m in any direction.
  Parameters: save_tn=11, displacement=3m.
  Playstyles: Controller. Hook: positioning control.

CAST_2 | Major | 2p + 1men | enemy_single | medium | instant | control
  Effect: forced jump — target save will (TN 12) or is teleported 5m to a location you designate (within range).
  Parameters: save_tn=12, displacement=5m_chosen.
  Playstyles: Controller. Hook: hard positional control.

CAST_3 | Major | 3p + 1men + scene_use | enemy_single | medium | instant | control, meta
  Effect: banishment — target save will (TN 14) or is teleported 20m (narrator designates safe-distance direction); next round they lose 1 Minor action re-engaging.
  Parameters: save_tn=14, displacement=20m, minor_lost=1, limit=1/scene.
  Playstyles: Controller. Hook: heavy disruption.

RIDER_A | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize also applies 2m forced movement (threaten to send target through portal).
  Playstyles: Controller. Combo: displacement_parley.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m who Reposition save will (TN 11) or your portal-forced destination applies (1m adjustment).
  Parameters: range=5m, save_tn=11, adjustment=1m.
  Playstyles: Controller. Combo: aura_positioning.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks may apply 1m displacement; on_Crit 3m displacement.
  Playstyles: Controller. Combo: strike_displacement.

CAPSTONE (authored: BANISHER) | 5p + 2men + scene_use | — | enemy_single | medium | instant | control, meta
  Signal: "Be elsewhere."
  Viability: offensive_swing.
  Effect: target save will (TN 15) or is teleported out of combat entirely (removed for scene; returns at scene end if applicable); on fail save, *exposed* instead.
  Parameters: save_tn=15, effect_on_fail=scene_removal, effect_on_marginal=exposed, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward diplomat).
  Effect: Destabilize-displacement also applies *shaken* (fear of being sent away).
  Combo: shaken_displacement.

---

## Sub-category 4.24 — Reach (6 powers)

---

**Tensile Extend** — Complement | Brawler, Skirmisher | Human, Creature
Identity: Limbs stretch long distances.

CAST_1 | Minor | 1p | — | self | — | 1 round | stat-alteration, damage
  Effect: reach — next melee attack has 5m range (vs normal touch).
  Parameters: melee_range=5m, duration=next_attack.
  Playstyles: Brawler, Skirmisher. Hook: extended engagement.

CAST_2 | Major | 2p | — | enemy_single | medium | instant | damage, movement
  Effect: whip strike — 10m melee: 2 damage + pull target 3m toward you.
  Parameters: range=10m, damage=2, pull=3m.
  Playstyles: Brawler, Controller. Hook: engagement pull.

CAST_3 | Major | 3p | — | self | — | scene | stat-alteration
  Effect: sustained extend — scene: melee range is 5m; can grapple at 5m.
  Parameters: melee_range=5m, grapple_range=5m, duration=scene.
  Playstyles: Brawler. Hook: scene reach buff.

RIDER_A | strike | restriction: melee attacks only | 1p
  Effect: on_Full melee attacks gain +2m range; on_Crit pull target 2m.
  Playstyles: Brawler. Combo: reach_pull_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers at 5m range take 1 counter-damage (whip-counter).
  Parameters: counter=1, range=5m.
  Playstyles: Tank, Brawler. Combo: extended_counter.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes a tensile-pull of up to 1 adjacent-at-distance enemy 2m.
  Playstyles: Controller. Combo: mobile_pull.

CAPSTONE (authored: ELASTIC WAR) | 5p + 1phy + scene_use | — | self | — | scene | stat-alteration, damage
  Signal: "My reach is my answer."
  Viability: setup_dependent.
  Effect: scene: melee range is 10m; can grapple at 10m; +1 damage on all melee.
  Parameters: melee_range=10m, melee_damage=+1, duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Full +3m range (was +2m); Crit pull 3m (was 2m).
  Combo: null.

---

**Spatial Fold** — Complement | Skirmisher, utility | Human
Identity: Compress distance between two points.

CAST_1 | Minor | 1p | — | self | medium | 1 round | movement
  Effect: close the gap — next Reposition halves distance penalty (terrain counts as half).
  Parameters: terrain_mult=0.5, duration=next_reposition.
  Playstyles: Skirmisher. Hook: terrain bypass.

CAST_2 | Major | 2p | — | self + ally | medium | instant | movement, meta
  Effect: pull ally — teleport 1 touched ally to you from up to 15m.
  Parameters: ally_pull=true, distance=15m.
  Playstyles: Support, Skirmisher. Hook: rescue.

CAST_3 | Major | 3p + 1phy | zone (10m line) | medium | 2 rounds | terrain-alteration, movement
  Effect: folded corridor — 10m line becomes effectively 2m of movement for allies; 10m for enemies.
  Parameters: ally_movement_mult=0.2, enemy_movement_mult=1.0, duration=2r.
  Playstyles: Support, Area Denier. Hook: asymmetric terrain.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition effectively halves distance (moves 2× normal).
  Playstyles: Skirmisher. Combo: mobility_double.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m treat their Reposition distance as +2m.
  Parameters: range=5m, ally_reposition=+2m.
  Playstyles: Support. Combo: party_mobility.

RIDER_C | strike | restriction: melee attacks | 1p
  Effect: on_Full melee attacks from "outside normal reach" (up to 5m) land as melee.
  Playstyles: Brawler. Combo: fold_strike.

CAPSTONE (authored: COMPRESSED GEOGRAPHY) | 4p + 1phy + scene_use | — | zone (20m) | medium | scene | terrain-alteration, meta
  Signal: "Distance is a convention."
  Viability: setup_dependent.
  Effect: 20m area scene: movement costs halved for you and allies; doubled for enemies.
  Parameters: ally_mult=0.5, enemy_mult=2.0, duration=scene, limit=1/scene.
  Playstyles: Support, Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward combat advantage).
  Effect: doubled Reposition also grants +1 to next attack roll.
  Combo: fold_and_strike.

---

**Long Reach Strike** — Primary | Artillery, Brawler | Human
Identity: Attack someone far away with melee-style reach.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | damage
  Effect: arcing strike — 10m ranged attack: 2 damage (counts as melee for effect purposes).
  Parameters: range=10m, damage=2, type=melee_via_reach.
  Playstyles: Brawler, Artillery. Hook: melee-at-range.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage, status
  Effect: piercing reach — Heavy attack at 20m: 3 damage + *exposed*.
  Parameters: range=20m, damage=3, status=exposed, requires=heavy.
  Playstyles: Brawler, Artillery. Hook: long-range heavy.

CAST_3 | Major | 3p + 1phy | zone (line 15m) | medium | instant | damage
  Effect: sweeping reach — line of 15m: 2 damage to each enemy in line.
  Parameters: line_length=15m, damage=2_each.
  Playstyles: Area Denier, Brawler. Hook: line AoE.

RIDER_A | strike | restriction: melee attacks, treated as reach | 1p
  Effect: on_Full melee attacks may have 5m reach; on_Crit +1 damage.
  Playstyles: Brawler. Combo: reach_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: enemies at 5m range take 1 counter-damage on attacking you.
  Parameters: counter=1, range=5m.
  Playstyles: Tank. Combo: reach_counter.

RIDER_C | strike | restriction: Heavy attacks only | 1p
  Effect: on_Full Heavy attacks at up to 10m deal +1 damage (reach heavy).
  Playstyles: Brawler. Combo: long_heavy.

CAPSTONE (authored: WORLD STRIKE) | 5p + 1phy + scene_use | — | enemy_single | extreme | instant | damage, status
  Signal: "Nowhere is far enough."
  Viability: offensive_swing.
  Effect: Heavy attack at 30m: 5 damage + *exposed* + *bleeding* 2r.
  Parameters: range=30m, damage=5, status=exposed_plus_bleeding_2r, requires=heavy, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: reach attacks also treat cover as 1 step less effective.
  Combo: reach_cover_break.

---

**Extended Sight** — Complement | Investigator, Artillery (setup) | Human
Identity: See far beyond normal sight.

CAST_1 | Minor | 1p | — | self | — | scene | information
  Effect: long view — see details at up to 100m as if 10m.
  Parameters: effective_sight_range=100m, duration=scene.
  Playstyles: Investigator. Hook: scouting.

CAST_2 | Major | 2p | — | enemy_single | extreme | scene | information, support
  Effect: targeted vision — continuously observe one target at any distance.
  Parameters: continuous_observation=true, duration=scene.
  Playstyles: Investigator, Artillery. Hook: persistent surveillance.

CAST_3 | Major | 3p + 1men | zone (wide) | extreme | scene | information, meta
  Effect: field of view — grant self +1 to ranged attacks and Assess vs targets within 50m (wide awareness).
  Parameters: ranged_attack_bonus=+1, assess_bonus=+1, range=50m, duration=scene.
  Playstyles: Artillery, Investigator. Hook: scene support.

RIDER_A | assess | restriction: all Assess types | 1p
  Effect: on_Full Assess range extended to up to 50m; reveals 1 additional fact.
  Playstyles: Investigator. Combo: deep_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect movement within 30m regardless of intervening light or obstruction (line-of-sight through walls not required but not ignored either — see silhouettes).
  Parameters: range=30m, detect=movement.
  Playstyles: Investigator. Combo: perimeter_watch.

RIDER_C | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged attacks ignore 1 step of cover (clear long sight).
  Playstyles: Artillery. Combo: long_shot_clear.

CAPSTONE (authored: EAGLE EYE) | 4p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "I see what's coming before they do."
  Viability: setup_dependent.
  Effect: scene: all ranged attacks +2; Assess can target anything within 100m; detect hidden at any range.
  Parameters: ranged=+2, assess_range=100m, hidden_detect=any, duration=scene, limit=1/scene.
  Playstyles: Artillery, Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess also reveals target's current phy track state (approximation).
  Combo: tactical_targeting.

---

**Force at Distance** — Complement | Artillery, Controller | Human
Identity: Apply physical force through space.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | movement
  Effect: nudge — push target 2m in any direction.
  Parameters: push=2m.
  Playstyles: Controller. Hook: positioning.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage, movement
  Effect: ranged push — 3 damage + push 3m.
  Parameters: damage=3, push=3m.
  Playstyles: Controller, Artillery. Hook: damage + positioning.

CAST_3 | Major | 3p + 1phy | zone (cone 5m) | medium | instant | damage, movement
  Effect: wave force — 5m cone: 2 damage + all pushed 3m away from you.
  Parameters: area=5m_cone, damage=2_each, push=3m_away.
  Playstyles: Area Denier, Controller. Hook: area displacement.

RIDER_A | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged attacks also push 1m; on_Crit push 3m.
  Playstyles: Controller, Artillery. Combo: ranged_displacement.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: ranged attackers who hit you are pushed back 1m.
  Parameters: push_on_ranged_hit=1m.
  Playstyles: Tank. Combo: reactive_push.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt at ranged applies 2m push to target.
  Playstyles: Controller. Combo: ranged_disrupt.

CAPSTONE (authored: TELEKINETIC MASTERY) | 5p + 1phy + scene_use | — | zone (10m) | medium | scene | control, meta
  Signal: "Their bodies are mine to arrange."
  Viability: setup_dependent.
  Effect: scene: once per round, move any enemy within 10m up to 5m in any direction (save agi TN 12 to resist).
  Parameters: per_round_move=5m, save_tn=12, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward combined control).
  Effect: ranged attack push also applies *exposed* on Crit.
  Combo: push_and_expose.

---

**Projected Presence** — Complement | Support, Diplomat | Human
Identity: Project image/voice to distant location for communication.

CAST_1 | Minor | 1p | — | self | far | scene | utility
  Effect: voice projection — speak to distant location with clarity (no need to raise voice).
  Parameters: voice_range=far, duration=scene.
  Playstyles: Support, Diplomat. Hook: communication.

CAST_2 | Major | 2p | — | self | extreme | scene | utility, support
  Effect: image projection — visible and audible avatar at a distant known location; ally (through avatar).
  Parameters: avatar=true, range=extreme_known_location, duration=scene.
  Playstyles: Support, Diplomat. Hook: distant presence.

CAST_3 | Major | 3p + 1men + scene_use | self | unlimited | scene | meta, support
  Effect: two-place — appear simultaneously at two locations (narrator-adjudicated; one avatar is real-weight, one is insubstantial for combat).
  Parameters: locations=2, duration=scene, limit=1/scene.
  Playstyles: narrative, Support. Hook: scene meta.

RIDER_A | parley | restriction: all Parley types | 1p
  Effect: on_Full Parley at far range functions as if at close range (no range penalty).
  Playstyles: Diplomat. Combo: distant_parley.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m gain +1 to Parley checks (your presence reinforces their words).
  Parameters: range=5m, parley=+1.
  Playstyles: Support, Diplomat. Combo: amplified_ally.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess through projected presence reveals ally's condition at distance.
  Playstyles: Investigator, Support. Combo: distant_intel.

CAPSTONE (authored: OMNIPRESENCE) | 4p + 1men + scene_use | — | self | extreme | scene | meta, utility
  Signal: "I am where I need to be."
  Viability: setup_dependent.
  Effect: scene: project image + voice + presence to 3 distant known locations simultaneously; all allies in 5m of any projection gain +1 rolls.
  Parameters: projections=3, ally_bonus=+1, duration=scene, limit=1/scene.
  Playstyles: Support, Commander.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward command).
  Effect: distant Parley also allows you to grant +1 to one ally's action at that location.
  Combo: remote_command.

---

## Sub-category 4.25 — Territorial (6 powers)

---

**Zone Anchor** — Complement | Tank, Controller | Human
Identity: Establish area where you're dominant.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration, meta
  Effect: my ground — within 5m of current position, +1 defense for scene.
  Parameters: defense=+1, radius_from_self=5m, duration=scene.
  Playstyles: Tank. Hook: positional defense.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | terrain-alteration, defense
  Effect: territorial ground — 5m zone: +1 defense for you; enemies in zone -1 attack.
  Parameters: area=5m, self_defense=+1, enemy_attack_penalty=-1, duration=scene.
  Playstyles: Tank, Controller. Hook: scene defensive zone.

CAST_3 | Major | 3p + 1phy + scene_use | zone (10m) | close | scene | terrain-alteration, meta
  Effect: absolute territory — 10m zone: +2 defense self; +1 defense allies; -1 enemy attacks; enemies save will on entry (TN 11) or *shaken*.
  Parameters: area=10m, self_defense=+2, ally_defense=+1, enemy_attack_penalty=-1, entry_shaken=true, duration=scene, limit=1/scene.
  Playstyles: Tank, Controller. Hook: scene dominance.

RIDER_A | posture/anchor | R3 | 0p passive
  Effect: while in your territorial zone, immune to forced movement.
  Parameters: immune_in_zone=forced_movement.
  Playstyles: Tank. Combo: zone_immovable.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers in your zone take 1 counter-damage on successful attacks against you.
  Parameters: counter=1.
  Playstyles: Tank. Combo: zone_counter.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks against enemies in your zone deal +1 damage.
  Playstyles: Brawler, Tank. Combo: zone_advantage.

CAPSTONE (authored: SACRED GROUND) | 4p + 2phy + scene_use | — | zone (15m) | medium | scene | meta, defense
  Signal: "This ground is mine."
  Viability: setup_dependent.
  Effect: 15m zone scene: +2 defense self; +2 defense allies; -2 enemy attacks; enemies cannot Reposition out of zone.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Tank, Controller.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: counter-damage also applies *bleeding* on Crit.
  Combo: zone_punisher.

---

**Target Pin** — Primary | Controller, Assassin | Human
Identity: Lock target in place.

CAST_1 | Minor | 1p + 1men | enemy_single | close | 1 round | control
  Effect: stick — target save agi (TN 11) or cannot Reposition next turn.
  Parameters: save_tn=11, reposition_disabled=1r.
  Playstyles: Controller. Hook: tactical lock.

CAST_2 | Major | 2p | — | enemy_single | medium | 2 rounds | control, status
  Effect: pin — save agi (TN 12) or *grappled* + cannot Reposition 2r.
  Parameters: save_tn=12, flag=grappled, reposition_disabled=2r.
  Playstyles: Controller, Assassin. Hook: hard lock.

CAST_3 | Major | 3p + 1men + scene_use | enemy_group (5m) | close | 1 round | control
  Effect: mass pin — 5m: all save agi (TN 12) or cannot Reposition this round.
  Parameters: area=5m, save_tn=12, reposition_disabled=1r, limit=1/scene.
  Playstyles: Controller, Area Denier. Hook: area lockdown.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks also apply reposition-disabled 1r; on_Crit target *exposed*.
  Playstyles: Assassin, Controller. Combo: strike_lock.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m Reposition distance reduced by 2m.
  Parameters: range=5m, reposition_delta=-2m.
  Playstyles: Controller. Combo: aura_slow.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt also applies reposition-disabled 1r.
  Playstyles: Controller. Combo: disrupt_lock.

CAPSTONE (authored: CAGE) | 5p + 1men + scene_use | — | enemy_single | medium | scene | control, meta
  Signal: "You stay."
  Viability: offensive_swing.
  Effect: enemy save will (TN 14) or cannot Reposition, teleport, or phase for scene; each round they spend 1 action attempting to break free (TN 12).
  Parameters: save_tn=14, full_mobility_block=true, break_attempt_tn=12, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Full also applies *exposed*; Crit applies *exposed* + reposition-disabled 2r.
  Combo: null.

---

**Space Seal** — Complement | Area Denier, Controller | Human, Eldritch
Identity: Close an area off from outside.

CAST_1 | Major | 2p | — | zone (3m entry) | close | 2 rounds | control, terrain-alteration
  Effect: seal doorway — 3m opening sealed 2r: enemies save might (TN 12) to pass.
  Parameters: width=3m, save_tn=12, duration=2r.
  Playstyles: Area Denier. Hook: choke point control.

CAST_2 | Major | 3p + 1men | zone (5m) | close | scene | control, meta
  Effect: encircle — 5m area scene: entering or leaving costs a Major action + save (TN 12).
  Parameters: area=5m, save_tn=12, action_cost=major, duration=scene.
  Playstyles: Area Denier, Controller. Hook: scene zone control.

CAST_3 | Major | 4p + 1men + scene_use | zone (10m) | medium | scene | control, meta
  Effect: total seal — 10m area scene: absolute barrier; no entry/exit except through you (narrator-adjudicated).
  Parameters: area=10m, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene dominance.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt against entering/leaving target applies *stunned* 1r.
  Playstyles: Controller. Combo: threshold_control.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies attempting to enter or leave 5m around you save will (TN 11) or spend Major action.
  Parameters: range=5m, save_tn=11, action_tax=major.
  Playstyles: Controller. Combo: aura_threshold.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect any breach or crossing attempt of your sealed area.
  Parameters: scope=all_your_sealed_zones.
  Playstyles: Investigator. Combo: perimeter_awareness.

CAPSTONE (authored: SIEGE LINE) | 5p + 1men + scene_use | — | zone (20m) | medium | scene | meta, control
  Signal: "Inside or outside — choose now."
  Viability: setup_dependent.
  Effect: 20m area scene: complete boundary; entry/exit only via your explicit permission.
  Parameters: area=20m, absolute=true, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch (toward dual control).
  Effect: Disrupt also applies *marked* (enemies crossing are tagged for ally attention).
  Combo: threshold_mark.

---

**Territorial Field** — Primary | Support, Tank | Human
Identity: Zone providing benefit to you and allies.

CAST_1 | Minor | 1p | — | zone (3m) | close | 2 rounds | support
  Effect: small boost — 3m area: allies +1 to next attack roll.
  Parameters: area=3m, ally_attack=+1_next, duration=2r.
  Playstyles: Support. Hook: mini-buff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | support, defense
  Effect: rallying ground — 5m zone scene: allies +1 attack, +1 defense.
  Parameters: area=5m, ally_attack=+1, ally_defense=+1, duration=scene.
  Playstyles: Support. Hook: scene buff zone.

CAST_3 | Major | 3p + 1phy + scene_use | zone (10m) | close | scene | support, meta
  Effect: stronghold — 10m zone: allies +2 attack, +2 defense, 1 phy regen per 3r; enemies -1 to rolls in zone.
  Parameters: area=10m, ally_combat=+2, ally_regen=1_per_3r, enemy_penalty=-1, duration=scene, limit=1/scene.
  Playstyles: Support. Hook: scene dominance.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 defense.
  Parameters: range=5m, defense=+1.
  Playstyles: Support. Combo: continuous_support.

RIDER_B | parley | restriction: Negotiate only | 1p
  Effect: on_Full Negotiate from within your zone +2.
  Playstyles: Diplomat, Support. Combo: zone_diplomacy.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks from within your zone +1 damage; on_Crit apply *marked*.
  Playstyles: Brawler. Combo: zone_strike.

CAPSTONE (authored: BASTION) | 5p + 1phy + scene_use | — | zone (15m) | medium | scene | support, meta
  Signal: "Here, we are strong."
  Viability: setup_dependent.
  Effect: 15m zone scene: allies +2 all rolls; 1 phy regen per 2r; enemies save will (TN 12) on entry or *shaken*.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Support, Commander.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura also applies +1 to ally Parley rolls.
  Combo: triple_ally_buff.

---

**Boundary Definition** — Complement | utility, Controller | Human, Eldritch
Identity: Define an edge; things across the edge treat each other as hostile or beyond reach.

CAST_1 | Minor | 1p | — | zone (line 5m) | close | 2 rounds | terrain-alteration
  Effect: short boundary — 5m line: crossing provokes Attack-of-Opportunity from you (1 free attack).
  Parameters: line=5m, aoo=1_per_cross, duration=2r.
  Playstyles: Controller. Hook: positional control.

CAST_2 | Major | 2p | — | zone (line 10m) | medium | scene | control, terrain-alteration
  Effect: line of command — 10m line scene: crossings impose save will (TN 12) or cross becomes Major-action-costly.
  Parameters: line=10m, save_tn=12, action_cost=major, duration=scene.
  Playstyles: Controller, utility. Hook: scene control.

CAST_3 | Major | 3p + 1men + scene_use | zone (circle 10m) | close | scene | meta, control
  Effect: quarantine circle — 10m circle scene: no projectile or ranged attack can cross; no Gateway effects cross.
  Parameters: area=10m, ranged_block=true, gateway_block=true, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene anti-ranged.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies crossing into 5m save will (TN 11) or lose 1 Minor action.
  Parameters: range=5m, save_tn=11, minor_lost=1.
  Playstyles: Controller. Combo: boundary_aura.

RIDER_B | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt when enemy crosses your boundary auto-Full.
  Playstyles: Controller. Combo: boundary_disrupt.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess tracks all boundary-crossings in current scene.
  Playstyles: Investigator. Combo: boundary_intel.

CAPSTONE (authored: LAW OF LINES) | 4p + 1men + scene_use | — | zone (multiple lines) | medium | scene | meta, control
  Signal: "Cross, and answer for it."
  Viability: setup_dependent.
  Effect: scene: maintain up to 3 boundary lines simultaneously; each applies its own effect.
  Parameters: lines=3, duration=scene, limit=1/scene.
  Playstyles: Controller, utility.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch (toward dual-effect boundary).
  Effect: aura also applies *marked* to any enemy who crosses.
  Combo: boundary_marked.

---

**Space Compression** — Complement | Controller, Assassin (setup) | Human, Eldritch (rare)
Identity: Bring distant things close together / make near things far.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | 1 round | control, status
  Effect: squish — enemy save agi (TN 11) or treat all distance in area as 2× for them (double movement cost).
  Parameters: save_tn=11, distance_mult=2.0_for_target, duration=1r.
  Playstyles: Controller. Hook: mobility debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | 2 rounds | terrain-alteration, control
  Effect: compressed zone — 5m area 2r: you and allies move at half cost; enemies at double.
  Parameters: area=5m, ally_mult=0.5, enemy_mult=2.0, duration=2r.
  Playstyles: Controller, Support. Hook: asymmetric terrain.

CAST_3 | Major | 3p + 1men + scene_use | zone (10m) | medium | scene | meta, terrain-alteration
  Effect: total distortion — 10m zone scene: asymmetric compression; enemies suffer 3× distance cost.
  Parameters: area=10m, enemy_mult=3.0, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene terrain control.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition costs half distance in compressed zones.
  Playstyles: Skirmisher. Combo: compressed_mobility.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m have Reposition distance reduced by 1m.
  Parameters: range=5m, reposition_delta=-1m.
  Playstyles: Controller. Combo: aura_slow.

RIDER_C | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged attacks at enemies in compressed terrain +1 damage (easier to track).
  Playstyles: Artillery. Combo: compressed_target.

CAPSTONE (authored: FOLDED WORLD) | 5p + 1men + scene_use | — | zone (15m) | medium | scene | meta, terrain-alteration
  Signal: "Their legs betray them."
  Viability: setup_dependent.
  Effect: 15m zone scene: enemies move at 3× cost; you and allies at 0.5×; all ally ranged attacks +1 damage against zone enemies.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: compressed-zone Reposition also grants +1 to next attack.
  Combo: fold_advantage_strike.


---

# BROAD: PARADOXIC

Paradoxic powers bend reality's rules. Cast modes typically carry `+N corruption` as additional cost. Register gating: Human primary; Eldritch register sources Anomalous sub-category; Creature access rare.

## Sub-category 4.26 — Temporal (6 powers)

---

**Time Stop** — Primary | Burst Caster, meta | Human, Eldritch (rare)
Identity: Halt local time briefly.

CAST_1 | Major | 3p + 1 corruption | self | — | 1 round | meta, action-economy
  Effect: instant stop — take 1 additional Major action this turn.
  Parameters: extra_major=1, duration=this_turn.
  Playstyles: Burst. Hook: spike economy.

CAST_2 | Major | 5p + 2 corruption + scene_use | self | — | 1 round | meta, action-economy
  Effect: extended — 2 extra Majors this turn.
  Parameters: extra_majors=2, limit=1/scene.
  Playstyles: Burst. Hook: scene-defining economy.

CAST_3 | Major | 4p + 2 corruption | zone | medium | 1 round | meta, control
  Effect: slowed time — enemies' speed halved 1r; you + allies normal.
  Parameters: enemy_speed_mult=0.5, duration=1r.
  Playstyles: Controller, Skirmisher. Hook: tempo shift.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks during Time Stop +2 damage.
  Playstyles: Burst, Assassin. Combo: stop_strike.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition during stopped time doubles distance.
  Playstyles: Skirmisher. Combo: stop_mobility.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess during stop auto-Full + reveals 2 facts.
  Playstyles: Investigator. Combo: stop_intel.

CAPSTONE (authored: FROZEN MOMENT) | 6p + 3 corruption + scene_use | — | self | — | scene | meta, action-economy
  Signal: "A heartbeat becomes my hour."
  Viability: offensive_swing.
  Effect: once per scene, take three full turns in a row (effectively 3× economy for one round).
  Parameters: extra_turns=2, limit=1/scene.
  Playstyles: Burst.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full +3 damage (was +2); Crit auto-applies *exposed*.
  Combo: null.

---

**Time Slow** — Complement | Controller, Area Denier | Human
Identity: Slow time in area.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | 1 round | control
  Effect: slow one — save will (TN 11) or -2 next action.
  Parameters: save_tn=11, penalty=-2.
  Playstyles: Controller. Hook: spike debuff.

CAST_2 | Major | 2p + 1 corruption | zone (5m) | medium | 2 rounds | control, terrain-alteration
  Effect: slowed zone — 5m: enemies -1 all rolls 2r.
  Parameters: area=5m, all_rolls=-1, duration=2r.
  Playstyles: Controller, Area Denier. Hook: area tempo.

CAST_3 | Major | 3p + 2 corruption + scene_use | zone (10m) | medium | scene | control, meta
  Effect: deep slow — 10m scene: enemies get 1 Major per 2 rounds.
  Parameters: area=10m, major_frequency=0.5, limit=1/scene.
  Playstyles: Controller. Hook: scene dominance.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks vs slowed +1 damage; on_Crit target loses 1 Minor next round.
  Playstyles: Assassin. Combo: slow_exploit.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m Reposition -1m.
  Parameters: range=5m, reposition=-1m.
  Playstyles: Controller. Combo: aura_slow.

RIDER_C | maneuver | Disrupt only | 1p
  Effect: on_Full Disrupt also applies -1 to target's next action.
  Playstyles: Controller. Combo: disrupt_slow.

CAPSTONE (authored: MOLASSES) | 5p + 2 corruption + scene_use | — | zone (15m) | medium | scene | control, meta
  Signal: "Their moments stretch into hours."
  Viability: offensive_swing.
  Effect: 15m scene: enemies all actions -2; skip every other round.
  Parameters: area=15m, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also -1 enemy attack rolls.
  Combo: dual_aura_slow.

---

**Time Speed Ally** — Complement | Support, Commander | Human
Identity: Speed ally's time.

CAST_1 | Minor | 1p + 1 corruption | ally | medium | 1 round | support
  Effect: quick-pulse — ally +1 next roll.
  Parameters: next_roll=+1.
  Playstyles: Support. Hook: small buff.

CAST_2 | Major | 2p + 1 corruption | ally | medium | 2 rounds | action-economy
  Effect: sustained — ally extra Minor per round 2r.
  Parameters: extra_minor=1_per_round, duration=2r.
  Playstyles: Support. Hook: economy buff.

CAST_3 | Major | 3p + 2 corruption + scene_use | ally | medium | 1 round | action-economy, meta
  Effect: spike — ally takes two Majors this round.
  Parameters: extra_major=1, limit=1/scene.
  Playstyles: Support. Hook: spike.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 Reposition.
  Parameters: range=5m, reposition=+1m.
  Playstyles: Support. Combo: party_mobility.

RIDER_B | assess | Brief | 1p
  Effect: on_Full pick an ally to act first next round (reorder initiative).
  Playstyles: Commander. Combo: tempo_control.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full +1 to ally's next action.
  Playstyles: Diplomat. Combo: coord_support.

CAPSTONE (authored: HASTEN) | 4p + 2 corruption + scene_use | — | ally_group (3) | medium | scene | support, action-economy
  Signal: "Move faster than they can track."
  Viability: setup_dependent.
  Effect: scene: 3 allies each +1 Minor per round, +1 attack, +1 defense.
  Parameters: allies=3, limit=1/scene.
  Playstyles: Commander.

ENHANCED_RIDER (new_dimension on RIDER_A) | 0p
  Shift: reinforce. Effect: aura also +1 ally defense rolls.
  Combo: dual_aura_support.

---

**Small Rewind** — Complement | Burst, meta | Human, Eldritch (rare)
Identity: Reverse small events.

CAST_1 | Minor | 1p + 1 corruption | self | — | instant | meta
  Effect: reroll one die (your own failed roll).
  Parameters: reroll=1.
  Playstyles: Burst, Trickster. Hook: spike meta.

CAST_2 | Major | 2p + 1 corruption | ally | medium | instant | meta
  Effect: ally reroll — ally within medium rerolls one die.
  Parameters: reroll=1_ally.
  Playstyles: Support, Burst. Hook: party meta.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | instant | meta, defense
  Effect: rewind action — undo one thing that happened to you this turn.
  Parameters: undo=1_effect, limit=1/scene.
  Playstyles: Tank, Burst. Hook: emergency undo.

RIDER_A | posture/amplify | R3 | 0p passive
  Effect: own Crits grant 1 reroll for rest of round.
  Parameters: reroll_grant=1_on_crit.
  Playstyles: Burst. Combo: crit_meta.

RIDER_B | assess | Brief | 1p
  Effect: on_Full Assess grants 1 reroll to ally.
  Playstyles: Support. Combo: assess_meta.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks with reroll-available +1 damage.
  Playstyles: Burst, Assassin. Combo: meta_strike.

CAPSTONE (authored: SECOND CHANCE) | 5p + 2 corruption + scene_use | — | self | — | scene | meta
  Signal: "That roll didn't happen."
  Viability: setup_dependent.
  Effect: scene: 3 rerolls available (you or ally); Crits grant bonus rerolls.
  Parameters: rerolls=3, limit=1/scene.
  Playstyles: Trickster, Support.

ENHANCED_RIDER (broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: Crits also grant 1 reroll for ally.
  Combo: party_meta_chain.

---

**Future Glimpse** — Complement | Investigator, Controller | Human, Eldritch
Identity: See moments ahead.

CAST_1 | Minor | 1p | — | self | — | 1 round | information
  Effect: next-turn — know enemies' declared actions before you declare.
  Parameters: preview=all_enemy_actions, duration=1r.
  Playstyles: Controller. Hook: info dominance.

CAST_2 | Major | 2p + 1 corruption | self | — | scene | information, meta
  Effect: sustained — scene: once per round see one enemy's intended action.
  Parameters: per_round_preview=1, duration=scene.
  Playstyles: Controller, Investigator. Hook: scene intel.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | scene | information, meta
  Effect: deep glimpse — see outcome of chosen action before committing; may change based on glimpse.
  Parameters: outcome_preview=1_per_round, limit=1/scene.
  Playstyles: Trickster. Hook: ultimate info.

RIDER_A | assess | Brief | 1p
  Effect: on_Full reveals target's next-round action.
  Playstyles: Investigator. Combo: action_preview.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: know which enemy will attack you next before they declare.
  Parameters: preview=attacker_target.
  Playstyles: Tank, Investigator. Combo: defensive_intel.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks vs previewed enemies +1 damage.
  Playstyles: Assassin. Combo: preview_strike.

CAPSTONE (authored: PROPHETIC) | 5p + 2 corruption + scene_use | — | self | — | scene | information, meta
  Signal: "I have already seen this moment."
  Viability: setup_dependent.
  Effect: scene: at round start, see all enemies' declared actions before committing your own.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: awareness also reveals attacker's weapon/power.
  Combo: null.

---

**Time Loop Target** — Primary | Controller, meta | Human (rare), Eldritch
Identity: Trap target in repeating moment.

CAST_1 | Major | 3p + 1 corruption | enemy_single | medium | 1 round | control, meta
  Effect: brief loop — save will (TN 12) or repeat last action (half effect).
  Parameters: save_tn=12, effect=repeat_half.
  Playstyles: Controller. Hook: action repeat.

CAST_2 | Major | 4p + 2 corruption | enemy_single | medium | 2 rounds | control
  Effect: sustained — save will (TN 13) or repeat same action 2r.
  Parameters: save_tn=13, duration=2r.
  Playstyles: Controller. Hook: heavy lockdown.

CAST_3 | Major | 5p + 3 corruption + scene_use | enemy_single | medium | scene | control, meta
  Effect: eternal moment — save will (TN 15) or stasis scene (removed from combat).
  Parameters: save_tn=15, stasis=true, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene-removal.

RIDER_A | parley | Destabilize only | 1p
  Effect: on_Full Destabilize vs looped target auto-Full.
  Playstyles: Controller. Combo: loop_parley.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save will (TN 11) or repeat previous Minor.
  Parameters: range=5m, save_tn=11.
  Playstyles: Controller. Combo: aura_loop.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks vs looped targets +2 damage.
  Playstyles: Assassin. Combo: loop_strike.

CAPSTONE (authored: STASIS PRISON) | 5p + 3 corruption + scene_use | — | enemy_single | medium | scene | meta, control
  Signal: "Live this moment forever."
  Viability: offensive_swing.
  Effect: save will (TN 16) or stasis; on any save-fail, *corrupted* applied if target survives.
  Parameters: save_tn=16, corruption_on_survival=1, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Destabilize vs looped also applies *corrupted*.
  Combo: loop_corruption_combo.

---

## Sub-category 4.27 — Probabilistic (6 powers)

---

**Luck Field** — Complement | Support, Trickster | Human
Identity: Influence probabilistic outcomes.

CAST_1 | Minor | 1p | — | self | — | 1 round | meta
  Effect: small luck — +1 next roll.
  Parameters: next_roll=+1.
  Playstyles: Support. Hook: small buff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | meta, support
  Effect: aura of luck — 5m: allies +1 all rolls, enemies -1 all rolls.
  Parameters: area=5m, ally=+1, enemy=-1, duration=scene.
  Playstyles: Support. Hook: scene asymmetric meta.

CAST_3 | Major | 3p + 1 corruption | self | — | scene | meta, action-economy
  Effect: personal surge — scene: reroll one failed die per round.
  Parameters: rerolls=1_per_round, duration=scene.
  Playstyles: Trickster. Hook: scene meta spike.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 defense.
  Parameters: range=5m, defense=+1.
  Playstyles: Support. Combo: luck_defense.

RIDER_B | posture/amplify | R3 | 0p passive
  Effect: own Crits grant 1 reroll to ally in 5m.
  Parameters: ally_reroll_on_crit=1.
  Playstyles: Support. Combo: crit_chain.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks in your luck-field +1 damage.
  Playstyles: Burst. Combo: luck_strike.

CAPSTONE (authored: FORTUNE FAVORS) | 4p + 2 corruption + scene_use | — | ally_group (visible) | medium | scene | meta, support
  Signal: "The world smiles on us."
  Viability: setup_dependent.
  Effect: scene: all visible allies +1 all rolls; 2 rerolls per scene.
  Parameters: ally=+1, rerolls=2, limit=1/scene.
  Playstyles: Support, Trickster.

ENHANCED_RIDER (broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: aura also +1 ally attack rolls.
  Combo: dual_aura.

---

**Force Max Roll** — Complement | Burst, Eradicator | Human (rare)
Identity: Compel successful roll.

CAST_1 | Minor | 1p + 1 corruption | self | — | instant | meta
  Effect: compelled — one of your rolls this round treated as max.
  Parameters: max_result=1_roll.
  Playstyles: Burst, Trickster. Hook: guaranteed success.

CAST_2 | Major | 2p + 1 corruption | ally | medium | instant | meta, support
  Effect: ally compel — ally's roll this round is max.
  Parameters: ally_max=1.
  Playstyles: Support. Hook: party guarantee.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | scene | meta
  Effect: scene compel — once per scene, force any roll (yours or ally's) to max.
  Parameters: max_any=1, limit=1/scene.
  Playstyles: Trickster. Hook: scene guarantee.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks auto-max (if rolled lower).
  Playstyles: Burst. Combo: auto-max_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: one defense roll per scene auto-max.
  Parameters: max_defense=1_per_scene.
  Playstyles: Tank. Combo: guaranteed_defense.

RIDER_C | parley | Demand only | 1p
  Effect: on_Full Demand treated as max outcome.
  Playstyles: Diplomat. Combo: max_demand.

CAPSTONE (authored: DESTINY'S HAND) | 5p + 2 corruption + scene_use | — | self | — | scene | meta, action-economy
  Signal: "The universe aligns for me."
  Viability: setup_dependent.
  Effect: scene: once per round, force any roll to max.
  Parameters: per_round_max=1, limit=1/scene.
  Playstyles: Trickster, Burst.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: max-roll attack also applies *exposed* + *bleeding* 1r.
  Combo: dominant_strike.

---

**Force Min Roll** — Complement | Controller | Human (rare)
Identity: Compel target's roll to min.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | 1 round | meta, control
  Effect: force low — save will (TN 11) or one roll this turn min.
  Parameters: save_tn=11, min=1_roll.
  Playstyles: Controller. Hook: spike counter.

CAST_2 | Major | 2p + 1 corruption | enemy_single | medium | 1 round | control
  Effect: sustained curse — save will (TN 12) or all rolls this round min.
  Parameters: save_tn=12, duration=1r.
  Playstyles: Controller. Hook: heavy debuff.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_single | medium | scene | meta, control
  Effect: cursed — save will (TN 13) or all rolls min for scene.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene curse.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks force target's next defense roll to min.
  Playstyles: Assassin. Combo: min_defense_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 all rolls.
  Parameters: range=5m, all_rolls=-1.
  Playstyles: Controller. Combo: aura_curse.

RIDER_C | maneuver | Disrupt only | 1p
  Effect: on_Full Disrupt target's next attack roll is min.
  Playstyles: Controller. Combo: disrupt_curse.

CAPSTONE (authored: CURSE OF FAILURE) | 5p + 2 corruption + scene_use | — | enemy_single | medium | scene | meta, control
  Signal: "Every path leads to ruin."
  Viability: offensive_swing.
  Effect: save will (TN 15) or all rolls min scene; rolls against them max.
  Parameters: save_tn=15, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: strike also forces target's next attack roll to min.
  Combo: null.

---

**Hex** — Complement | Controller, Sustained | Human
Identity: Persistent bad luck.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | 2 rounds | status
  Effect: minor hex — -1 all rolls 2r.
  Parameters: all_rolls=-1, duration=2r.
  Playstyles: Controller. Hook: DoT-status.

CAST_2 | Major | 2p + 1 corruption | enemy_single | medium | scene | status, control
  Effect: curse — save will (TN 12) or -2 all rolls scene.
  Parameters: save_tn=12, penalty=-2, duration=scene.
  Playstyles: Controller. Hook: scene debuff.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_group (3) | medium | scene | control
  Effect: mass hex — 3 save will (TN 12) or -1 all rolls scene.
  Parameters: targets=3, save_tn=12, limit=1/scene.
  Playstyles: Controller. Hook: area curse.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 to one chosen roll type (attack/defense/parley).
  Parameters: range=5m, penalty=-1_chosen_type.
  Playstyles: Controller. Combo: aura_hex.

RIDER_B | parley | Destabilize only | 1p
  Effect: on_Full Destabilize vs hexed +2.
  Playstyles: Controller. Combo: hex_parley.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks on hexed +1 damage.
  Playstyles: Assassin. Combo: hex_exploit.

CAPSTONE (authored: DEEP CURSE) | 5p + 2 corruption + scene_use | — | enemy_single | medium | scene | meta, control
  Signal: "Their luck has run dry."
  Viability: setup_dependent.
  Effect: scene: target -3 all rolls; auto-fails saves on casts against them.
  Parameters: all_rolls=-3, save_auto_fail=true, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: aura applies -1 to ALL roll types (not just one).
  Combo: total_aura_hex.

---

**Tip the Balance** — Complement | Trickster, Support | Human
Identity: Shift probabilities subtly without forcing outcomes.

CAST_1 | Minor | 1p | — | self | — | 1 round | meta
  Effect: nudge — +2 to next roll (cost: next FAILED roll after this takes -2).
  Parameters: next_roll=+2, delayed_penalty=-2_on_next_fail.
  Playstyles: Trickster. Hook: reward/risk.

CAST_2 | Major | 2p + 1 corruption | self or ally | medium | scene | meta
  Effect: skewed scales — scene: pick one roll type (attack/defense/parley); +1 to it, -1 to others.
  Parameters: chosen_type=+1, others=-1, duration=scene.
  Playstyles: Support. Hook: targeted commitment.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_single or ally | medium | scene | meta, support
  Effect: heavy tip — target (ally or enemy): ally gets +2 all rolls, enemy gets -2 all rolls, scene. Corruption builds.
  Parameters: target_bonus_or_penalty=+2/-2, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: asymmetric scene.

RIDER_A | posture/amplify | R3 | 0p passive
  Effect: own Crits also trigger +1 to next ally roll in 5m.
  Parameters: ally_bonus_on_crit=+1.
  Playstyles: Support. Combo: crit_shift.

RIDER_B | assess | Brief | 1p
  Effect: on_Full Assess shifts a target's next roll by ±1 (your choice).
  Playstyles: Controller. Combo: assess_tip.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks shift target's next defense -1.
  Playstyles: Assassin. Combo: strike_tip.

CAPSTONE (authored: THE SCALES) | 5p + 2 corruption + scene_use | — | scene | medium | scene | meta
  Signal: "The world bends slightly, for me."
  Viability: setup_dependent.
  Effect: scene: you and allies +1 all rolls; enemies -1 all rolls.
  Parameters: ally=+1, enemy=-1, duration=scene, limit=1/scene.
  Playstyles: Support, Trickster.

ENHANCED_RIDER (new_dimension on RIDER_A) | 0p
  Shift: branch. Effect: Crit also triggers -1 to next enemy roll within 5m.
  Combo: dual_tip.

---

**Chance Exchange** — Complement | Trickster, Support | Human, Eldritch
Identity: Swap outcomes with another.

CAST_1 | Minor | 1p + 1 corruption | self + ally | medium | instant | meta, support
  Effect: swap rolls — take an ally's recent roll result as your own (ally keeps original for tracking); their new roll is your previous result.
  Parameters: swap=1_roll_with_ally.
  Playstyles: Support, Trickster. Hook: situational meta.

CAST_2 | Major | 2p + 1 corruption | self + enemy | medium | instant | meta, control
  Effect: steal outcome — exchange your failed roll for an enemy's successful roll. They now have your fail; you have their success.
  Parameters: swap_with_enemy=1_roll, requires=enemy_success_and_self_fail_same_round.
  Playstyles: Trickster. Hook: reactive steal.

CAST_3 | Major | 3p + 2 corruption + scene_use | self + ally_group (3) | medium | scene | meta, support
  Effect: shared fortune — scene: once per round, an ally may take your next roll as their own (and vice versa).
  Parameters: swap_per_round=1, duration=scene, limit=1/scene.
  Playstyles: Support. Hook: scene coordination.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m can spend 1p to swap one die roll with you per scene.
  Parameters: range=5m, swap=1_per_scene_ally_initiated.
  Playstyles: Support. Combo: reciprocal_meta.

RIDER_B | assess | Brief | 1p
  Effect: on_Full Assess reveals a target's recent roll outcomes (setup for swap).
  Playstyles: Investigator. Combo: swap_setup.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Negotiate opens narrative "exchange" (fortune-based deals).
  Playstyles: Diplomat, narrative. Combo: narrative_exchange.

CAPSTONE (authored: WEAVER OF FORTUNES) | 5p + 2 corruption + scene_use | — | scene | medium | scene | meta
  Signal: "I trade fates like coin."
  Viability: setup_dependent.
  Effect: scene: once per round, force an exchange between any two creatures' next rolls (including enemy↔ally).
  Parameters: per_round_exchange=1, limit=1/scene.
  Playstyles: Trickster, Controller.

ENHANCED_RIDER (new_dimension on RIDER_A) | 0p
  Shift: branch. Effect: swap also transfers one status effect (ally's burning→enemy).
  Combo: status_exchange.

---

## Sub-category 4.28 — Sympathetic (6 powers)

---

**Doll Binding** — Primary | Controller, Assassin | Human, Eldritch
Identity: Effigy binds target; harm the doll, harm the target.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | scene | meta
  Effect: create link — craft rudimentary effigy; target linked for scene (requires component: hair, blood, or equivalent — narrator-adjudicated).
  Parameters: link_duration=scene, requires=component.
  Playstyles: Controller, Assassin. Hook: setup for strikes.

CAST_2 | Major | 2p + 1 corruption | linked_enemy | extreme | instant | damage
  Effect: pierce the doll — 3 damage to linked target at any distance.
  Parameters: damage=3, range=unlimited_if_linked, requires=prior_link.
  Playstyles: Assassin. Hook: spike-ranged damage.

CAST_3 | Major | 4p + 2 corruption + scene_use | linked_enemy | extreme | 2 rounds | damage, status
  Effect: torment — target save will (TN 13) or 4 damage + *bleeding* 2r + *shaken*.
  Parameters: save_tn=13, damage=4, status=bleeding_2r_plus_shaken, requires=link, limit=1/scene.
  Playstyles: Assassin. Hook: scene spike.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks on linked target ignore 1 step of armor; on_Crit apply *exposed*.
  Playstyles: Assassin. Combo: link_strike.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: continuously know linked target's state (phy remaining, statuses, location).
  Parameters: scope=linked_targets.
  Playstyles: Investigator. Combo: link_intel.

RIDER_C | parley | Demand only | 1p
  Effect: on_Full Demand against linked target +3.
  Playstyles: Diplomat, Controller. Combo: link_parley.

CAPSTONE (authored: EFFIGY MASTER) | 5p + 2 corruption + scene_use | — | linked_enemies (up to 3) | extreme | scene | meta, damage
  Signal: "Each thread I pull, they twist."
  Viability: setup_dependent.
  Effect: scene: maintain up to 3 links; can harm each as Minor action (2 damage each per use, once per round).
  Parameters: max_links=3, per_round_harm=2_each, duration=scene, limit=1/scene.
  Playstyles: Controller, Assassin.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full ignores 2 steps armor; Crit also *bleeding* 2r.
  Combo: null.

---

**True Name Invocation** — Primary | Controller, Diplomat | Human, Eldritch
Identity: Speak target's true name; powerful binding.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | 1 round | meta, control
  Effect: name-speak — save will (TN 12) or -2 to actions vs you this round (known name disrupts).
  Parameters: save_tn=12, penalty=-2, requires=known_true_name.
  Playstyles: Controller. Hook: setup control.

CAST_2 | Major | 2p + 1 corruption | enemy_single | medium | scene | control
  Effect: named pressure — save will (TN 13) or cannot directly target you with harmful action scene.
  Parameters: save_tn=13, no_direct_harm_you=true, duration=scene.
  Playstyles: Controller, Diplomat. Hook: scene protection.

CAST_3 | Major | 4p + 2 corruption + scene_use | enemy_single | medium | scene | control, meta
  Effect: binding — save will (TN 14) or forced to take one Minor action per round as you direct (narrator-adjudicated scope).
  Parameters: save_tn=14, minor_dictation=1_per_round, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene control.

RIDER_A | parley | Demand only | 1p
  Effect: on_Full Demand on name-known target auto-Full.
  Playstyles: Diplomat. Combo: name_demand.

RIDER_B | assess | Brief or Full | 1p
  Effect: on_Full Assess may reveal target's true name (narrator-adjudicated based on context).
  Playstyles: Investigator. Combo: name_intel.

RIDER_C | parley | Destabilize only | 1p
  Effect: on_Full Destabilize vs name-known +2.
  Playstyles: Controller. Combo: name_break.

CAPSTONE (authored: NAMING CHAIN) | 5p + 2 corruption + scene_use | — | enemy_single | medium | scene | meta, control
  Signal: "I know what you are."
  Viability: setup_dependent (requires true name).
  Effect: scene: named target -3 vs you; you may dictate their one Minor action per round; they are *marked* and *shaken* continuously.
  Parameters: save_tn=15, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: Demand also applies *corrupted* on success.
  Combo: corruption_demand.

---

**Blood Tracking / Targeting** — Complement | Assassin, Investigator | Human, Eldritch
Identity: Small sympathetic link via blood or tissue.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | touch | scene | information, status
  Effect: blood-lock — target *marked* for scene; you always know their location.
  Parameters: status=marked, location_tracking=true, duration=scene.
  Playstyles: Assassin, Investigator. Hook: persistent tracking.

CAST_2 | Major | 2p + 1 corruption | enemy_single | extreme | instant | damage
  Effect: distant pierce — 2 damage to blood-linked target at any range.
  Parameters: damage=2, range=unlimited_if_linked, requires=blood_link.
  Playstyles: Assassin. Hook: ranged strike.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_single | extreme | scene | meta, information
  Effect: deep track — scene: linked target visible to you at all times; you know their rolls before they commit.
  Parameters: roll_preview=true, duration=scene, limit=1/scene.
  Playstyles: Investigator, Assassin. Hook: scene dominance.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks on blood-linked +1 damage; on_Crit ignore 1 armor step.
  Playstyles: Assassin. Combo: linked_strike.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: always know location and rough state of blood-linked targets.
  Parameters: scope=linked.
  Playstyles: Investigator. Combo: linked_awareness.

RIDER_C | maneuver | Conceal only | 1p
  Effect: on_Full Conceal vs blood-linked target auto-Full (you know where they're looking).
  Playstyles: Assassin. Combo: linked_stealth.

CAPSTONE (authored: RED HUNTER) | 5p + 2 corruption + scene_use | — | enemy_single (blood-linked) | extreme | scene | meta, damage
  Signal: "Your blood still speaks to mine."
  Viability: setup_dependent.
  Effect: scene: linked target takes 1 damage per round anywhere; all your attacks on them +2.
  Parameters: per_round_damage=1, attack_bonus=+2, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: linked attacks also apply *bleeding* 1r.
  Combo: bleed_link.

---

**Oath Binding** — Complement | Diplomat, Controller | Human, Eldritch
Identity: Sworn oath creates reality-backed obligation.

CAST_1 | Minor | 1p + 1 corruption | willing_target | medium | scene | meta, support
  Effect: swear — willing target takes a binding oath; if they break it, they take 2 damage + *exposed*.
  Parameters: break_penalty=2_damage_plus_exposed, requires=willing, duration=scene.
  Playstyles: Diplomat. Hook: narrative pressure.

CAST_2 | Major | 2p + 1 corruption | enemy_or_ally | medium | scene | meta, control
  Effect: forced oath — save will (TN 12) or bound by oath of your choice scene; break penalty 3 damage + *bleeding* 2r.
  Parameters: save_tn=12, break_penalty=3_plus_bleeding_2r, duration=scene.
  Playstyles: Controller, Diplomat. Hook: binding control.

CAST_3 | Major | 4p + 2 corruption + scene_use | enemy_single | medium | arc | meta, narrative
  Effect: deep vow — save will (TN 14) or bound by oath for entire arc (narrator-adjudicated); break penalty 5 damage + *corrupted*.
  Parameters: save_tn=14, duration=arc, limit=1/scene.
  Playstyles: Controller, narrative. Hook: arc-defining.

RIDER_A | parley | Negotiate only | 1p
  Effect: on_Full Negotiate results in oath-binding (target accepts terms or refuses — both have weight).
  Playstyles: Diplomat. Combo: parley_oath.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect oath-breakers and those bound by your oaths within 30m.
  Parameters: range=30m.
  Playstyles: Investigator, Diplomat. Combo: oath_awareness.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks on oath-breakers +2 damage.
  Playstyles: Diplomat, Assassin. Combo: breaker_strike.

CAPSTONE (authored: PACT LORD) | 5p + 2 corruption + scene_use | — | scene | medium | arc | meta, narrative
  Signal: "By my word, it is done."
  Viability: setup_dependent.
  Effect: scene: up to 3 active oaths; each break deals 4 damage + *corrupted*.
  Parameters: oaths_max=3, break_penalty=4_plus_corrupted, duration=arc, limit=1/scene.
  Playstyles: Diplomat, Controller.

ENHANCED_RIDER (broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: Parley also forces oath-awareness on observers (everyone knows).
  Combo: public_oath.

---

**Shared Pain Link** — Complement | Tank, Sustained | Human, Eldritch
Identity: Link pain between self and target (or ally).

CAST_1 | Minor | 1p + 1 corruption | enemy_single | medium | 2 rounds | meta, defense
  Effect: short link — damage you take for 2r splits half to target (save will TN 11 to prevent).
  Parameters: damage_share_mult=0.5, save_tn=11, duration=2r.
  Playstyles: Tank. Hook: damage redirection.

CAST_2 | Major | 2p + 1 corruption | ally | medium | scene | meta, defense
  Effect: ally bond — scene: you and ally share damage 50/50 (can't reduce below 1 on either side per hit).
  Parameters: split=50/50, floor=1, duration=scene.
  Playstyles: Tank, Support. Hook: team tank.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_single | medium | scene | meta, damage
  Effect: pain vow — scene: any damage you take, target takes 1.5× that amount.
  Parameters: target_damage_mult=1.5, duration=scene, limit=1/scene.
  Playstyles: Glass Cannon. Hook: scene spike.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: damage you take share 1 to nearest linked creature (if any).
  Parameters: share=1_damage, scope=linked.
  Playstyles: Tank. Combo: damage_share.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: linked allies in 5m -1 damage (your pain absorbs).
  Parameters: range=5m, ally_reduction=1.
  Playstyles: Support, Tank. Combo: ally_protection.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks on linked enemy take 1 from you as sympathetic.
  Playstyles: Glass Cannon. Combo: link_sacrifice.

CAPSTONE (authored: MARTYR'S LINK) | 5p + 2 corruption + scene_use | — | ally_group (3) | medium | scene | meta, defense
  Signal: "Their pain is mine to bear."
  Viability: setup_dependent.
  Effect: scene: 3 allies linked; all damage to any splits 40% to you, 60% among others.
  Parameters: allies=3, self_share=40%, duration=scene, limit=1/scene.
  Playstyles: Tank, Support.

ENHANCED_RIDER (new_dimension on RIDER_B) | 0p
  Shift: branch. Effect: aura also heals linked allies 1 phy per 2r if you have taken damage.
  Combo: martyr_heal.

---

**Sacrifice Exchange** — Primary | Burst, Glass Cannon | Human, Eldritch
Identity: Offer self for amplified effect.

CAST_1 | Minor | 1p + 1phy + 1 corruption | self | — | 1 round | meta
  Effect: bleed for power — next cast this round +2 effect scale (damage, range, duration).
  Parameters: next_cast_scale=+2, duration=1r.
  Playstyles: Burst. Hook: no-pool spike.

CAST_2 | Major | 2p + 2phy + 1 corruption | self or ally | medium | instant | meta, support
  Effect: greater sacrifice — ally gains +3 to next action OR you recover 4 pool.
  Parameters: choice=ally_bonus_or_self_pool, value=+3_or_4p.
  Playstyles: Support, Burst. Hook: spike.

CAST_3 | Major | 3p + 3phy + 2 corruption + scene_use | self | — | instant | meta
  Effect: the final price — next cast is free of all costs (including scene_use).
  Parameters: next_cast_cost=0, limit=1/scene.
  Playstyles: Burst. Hook: capstone enabler.

RIDER_A | strike | all attack sub-types | 1p
  Effect: on_Full attacks at <3 phy +2 damage; on_Crit +3.
  Playstyles: Glass Cannon. Combo: desperation_damage.

RIDER_B | posture/amplify | R3 | 0p passive
  Effect: own Crits heal 1 phy if self was below 3 phy at Crit.
  Parameters: crit_heal_if_low=1.
  Playstyles: Glass Cannon. Combo: sacrifice_sustain.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Parley where offering self-harm as "sacrifice" auto-Full.
  Playstyles: Diplomat, narrative. Combo: sacrifice_parley.

CAPSTONE (authored: THE OFFERING) | 4p + 3phy + 2 corruption + scene_use | — | self | — | 1 round | meta, resource
  Signal: "My blood, for all."
  Viability: setup_dependent.
  Effect: this round: self drops to 1 phy; all allies recover 2 phy + full pool.
  Parameters: self_reduce_to=1_phy, ally_heal=2_phy_plus_full_pool, limit=1/scene.
  Playstyles: Support, Glass Cannon.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full +3 damage (was +2); Crit +4.
  Combo: null.

---

## Sub-category 4.29 — Anomalous (6 powers)

---

**Wrong Touch** — Primary | Assassin, Eradicator | Eldritch (primary), Human (rare, corruption heavy)
Identity: Contact that violates basic reality.

CAST_1 | Minor | 1p + 1 corruption | enemy_single | touch | 1 round | damage, status
  Effect: incongruent — melee touch: 2 damage + save will (TN 11) or *shaken* 1r.
  Parameters: damage=2, save_tn=11, status=shaken_1r.
  Playstyles: Assassin, Controller. Hook: light corruption setup.

CAST_2 | Major | 2p + 2 corruption | enemy_single | touch | 2 rounds | damage, status
  Effect: wrong wound — Heavy: 4 damage + *corrupted* 2r.
  Parameters: damage=4, status=corrupted_2r, requires=heavy.
  Playstyles: Assassin. Hook: corruption spike.

CAST_3 | Major | 4p + 3 corruption + scene_use | enemy_single | touch | instant | damage, meta
  Effect: abyssal touch — Heavy: 5 damage + *corrupted* 3r + *exposed* + save will (TN 13) or phy track permanently reduced by 1 for this scene.
  Parameters: damage=5, phy_track_reduction=1, requires=heavy, limit=1/scene.
  Playstyles: Eradicator. Hook: catastrophic spike.

RIDER_A | strike | melee attacks | 1p
  Effect: on_Full melee applies *corrupted* 1r; on_Crit *corrupted* 2r + *bleeding*.
  Playstyles: Assassin, Eradicator. Combo: corruption_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage + save will (TN 11) or *shaken*.
  Parameters: counter=1, shaken_on_fail=true.
  Playstyles: Tank. Combo: wrong_counter.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 3m save will (TN 11) each round or *shaken* (exposure to wrongness).
  Parameters: range=3m, per_round_save=true.
  Playstyles: Controller. Combo: aura_wrong.

CAPSTONE (authored: REALITY WOUND) | 5p + 3 corruption + scene_use | — | enemy_single | touch | 3 rounds | damage, meta
  Signal: "Your reality fails at my touch."
  Viability: offensive_swing.
  Effect: Heavy: 6 damage + *corrupted* 3r + phy track reduced 1 for scene + save will (TN 14) or *shaken* for scene.
  Parameters: damage=6, requires=heavy, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full *corrupted* 2r; Crit *corrupted* 3r + *bleeding* 2r.
  Combo: null.

---

**Reality Wound** — Primary | Eradicator, Area Denier | Eldritch
Identity: Tear localized reality.

CAST_1 | Major | 2p + 2 corruption | zone (2m) | close | instant | damage, status
  Effect: rift — 2m area: 3 damage + save will (TN 12) or *corrupted*.
  Parameters: area=2m, damage=3, save_tn=12, status=corrupted.
  Playstyles: Area Denier, Eradicator. Hook: area corruption.

CAST_2 | Major | 3p + 2 corruption | zone (5m) | medium | 2 rounds | damage, terrain-alteration
  Effect: unstable reality — 5m 2r: 2 damage per round to all; terrain *corrupted* (narrator-adjudicated effects).
  Parameters: area=5m, per_round=2, duration=2r.
  Playstyles: Area Denier. Hook: persistent zone.

CAST_3 | Major | 5p + 3 corruption + scene_use | zone (10m) | medium | scene | damage, meta
  Effect: wound in the world — 10m scene: 2 damage per round, *shaken* per round save (TN 12), terrain *corrupted*; includes you if you enter.
  Parameters: area=10m, per_round=2, duration=scene, includes_self=true, limit=1/scene.
  Playstyles: Eradicator. Hook: scene-defining.

RIDER_A | strike | Power, Power_Minor | 1p
  Effect: on_Full rift-strikes apply *corrupted* 1r; on_Crit *corrupted* 2r + *bleeding*.
  Playstyles: Area Denier. Combo: corruption_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m take 1 damage per 2r (reality leakage).
  Parameters: range=5m, damage=1, period=2r.
  Playstyles: Area Denier. Combo: aura_wound.

RIDER_C | maneuver | Disrupt only | 1p
  Effect: on_Full Disrupt applies *corrupted* via local reality tear.
  Playstyles: Controller. Combo: disrupt_wound.

CAPSTONE (authored: THE WOUND) | 6p + 3 corruption + scene_use | — | zone (15m) | medium | scene | damage, meta
  Signal: "I tear the world open here."
  Viability: offensive_swing.
  Effect: 15m scene: 3 damage per round; all save will (TN 13) or *corrupted* each round; terrain permanently *corrupted* (narrative).
  Parameters: area=15m, per_round=3, duration=scene, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: rift-strikes also apply *shaken* in addition to *corrupted*.
  Combo: dual_status.

---

**Impossible Geometry** — Complement | Controller, Area Denier | Eldritch, Human (rare)
Identity: Folds space in ways it should not fold.

CAST_1 | Minor | 1p + 1 corruption | zone (small) | close | 2 rounds | terrain-alteration
  Effect: small distortion — 3m area 2r: enemies save will (TN 11) or lose 1 Minor (confused by geometry).
  Parameters: area=3m, save_tn=11, minor_lost=1, duration=2r.
  Playstyles: Controller. Hook: tempo debuff.

CAST_2 | Major | 2p + 2 corruption | zone (5m) | medium | scene | terrain-alteration, control
  Effect: non-Euclidean — 5m scene: enemies Reposition cost doubled; allies cost halved.
  Parameters: area=5m, enemy_mult=2.0, ally_mult=0.5, duration=scene.
  Playstyles: Controller, Area Denier. Hook: scene asymmetric terrain.

CAST_3 | Major | 4p + 3 corruption + scene_use | zone (10m) | medium | scene | meta, terrain-alteration
  Effect: wrong space — 10m scene: narrator-adjudicated reality distortions; enemies save will each round (TN 12) or *confused*.
  Parameters: area=10m, per_round_save=true, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene disorientation.

RIDER_A | maneuver | Reposition only | 1p
  Effect: on_Full Reposition through distorted terrain costs no pool (normally 1p if through difficult).
  Playstyles: Skirmisher. Combo: distortion_mobility.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: you are unaffected by distorted-geometry penalties in your zones.
  Parameters: self_immune_in_own_zones=true.
  Playstyles: utility. Combo: author_immune.

RIDER_C | assess | Brief Assess only | 1p
  Effect: on_Full Assess in distorted zone reveals 2 facts (enemies are confused).
  Playstyles: Investigator. Combo: distortion_intel.

CAPSTONE (authored: IMPOSSIBLE LAND) | 5p + 3 corruption + scene_use | — | zone (15m) | medium | scene | meta, terrain-alteration
  Signal: "Geometry obeys me; it makes sense to no one else."
  Viability: setup_dependent.
  Effect: 15m scene: enemies save will (TN 14) on entry or *confused* scene; movement costs tripled; you + allies free.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: free Reposition also grants +1 to next attack.
  Combo: distorted_strike.

---

**Unspeakable Name** — Primary | Controller, Eradicator | Eldritch (primary), Human (rare)
Identity: Utter name that should not be spoken.

CAST_1 | Minor | 1p + 2 corruption | enemy_single | close | 1 round | status
  Effect: whisper the name — save will (TN 12) or *shaken* + *corrupted* 1r.
  Parameters: save_tn=12, status=shaken_1r_plus_corrupted_1r.
  Playstyles: Controller. Hook: dual status.

CAST_2 | Major | 3p + 2 corruption | enemy_group (5m) | close | 1 round | status, control
  Effect: speak aloud — 5m: save will (TN 13) or *shaken* 2r + *corrupted* 1r.
  Parameters: area=5m, save_tn=13, status=shaken_2r_plus_corrupted, duration=1r.
  Playstyles: Controller, Area Denier. Hook: area corruption.

CAST_3 | Major | 5p + 4 corruption + scene_use | all_visible | medium | 1 round | meta, control
  Effect: proclaim — all visible enemies save will (TN 14) or phy track reduced by 1 + *corrupted* + *shaken* scene. Self: take 2 corruption regardless.
  Parameters: save_tn=14, phy_reduction=1, status_on_fail=corrupted_plus_shaken, self_cost=2_corruption, limit=1/scene.
  Playstyles: Eradicator. Hook: scene apocalypse.

RIDER_A | parley | Destabilize only | 1p
  Effect: on_Full Destabilize also applies *corrupted*.
  Playstyles: Controller. Combo: corruption_parley.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save will (TN 11) each round or -1 all rolls (echoes of name).
  Parameters: range=5m, per_round_save=true.
  Playstyles: Controller. Combo: aura_unspeakable.

RIDER_C | strike | all attack sub-types | 1p
  Effect: on_Full attacks on *corrupted* targets +2 damage; on_Crit *exposed*.
  Playstyles: Assassin, Eradicator. Combo: corruption_exploit.

CAPSTONE (authored: THE UNMAKING NAME) | 6p + 4 corruption + scene_use | — | all_visible | medium | scene | meta, control
  Signal: "This is what you are, unspoken, unravelling."
  Viability: offensive_swing.
  Effect: all visible save will (TN 15) or *corrupted* scene + -2 all rolls + -1 phy; self 3 corruption.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (new_dimension on RIDER_B) | 0p
  Shift: branch. Effect: aura also applies 1 damage per round to creature-register enemies (they hear the name more acutely).
  Combo: creature_bane.

---

**Call the Depth** — Primary | Area Denier, Eradicator | Eldritch
Identity: Summon fragment of deep reality.

CAST_1 | Major | 2p + 2 corruption | zone (3m) | close | 2 rounds | damage, status
  Effect: shallow call — 3m 2r: 2 damage per round + save will (TN 12) or *corrupted*.
  Parameters: area=3m, per_round=2, save_tn=12, duration=2r.
  Playstyles: Area Denier. Hook: zone corruption.

CAST_2 | Major | 4p + 3 corruption | zone (5m) | medium | scene | damage, meta
  Effect: deep call — 5m scene: unspeakable entity-shadow presence; 3 damage per round; save will (TN 13) or *shaken* + *corrupted*.
  Parameters: area=5m, per_round=3, duration=scene.
  Playstyles: Eradicator, Area Denier. Hook: scene presence.

CAST_3 | Major | 5p + 4 corruption + scene_use | zone (10m) | medium | scene | meta, damage
  Effect: abyssal manifestation — 10m scene: eldritch entity briefly manifests; 4 damage per round; save will (TN 14) or phy track -1 + *corrupted*; self takes 2 additional corruption.
  Parameters: area=10m, per_round=4, self_extra_corruption=2, duration=scene, limit=1/scene.
  Playstyles: Eradicator. Hook: scene apocalypse.

RIDER_A | strike | Power, Power_Minor | 1p
  Effect: on_Full depth-attacks apply *corrupted*; on_Crit *corrupted* 2r + *bleeding*.
  Playstyles: Area Denier. Combo: depth_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save will (TN 11) each round or *shaken*.
  Parameters: range=5m, per_round_save=true.
  Playstyles: Controller. Combo: depth_aura.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect entities from beyond reality within 30m (eldritch, extraplanar).
  Parameters: range=30m, detect=extraplanar.
  Playstyles: Investigator. Combo: anti-eldritch.

CAPSTONE (authored: THE DEEP ANSWERS) | 6p + 4 corruption + scene_use | — | zone (15m) | medium | scene | meta, damage
  Signal: "I opened the door. Now it sees."
  Viability: offensive_swing.
  Effect: 15m scene: 5 damage per round; all in zone save will (TN 14) each round or *shaken* + *corrupted*; scene ends with +2 self corruption regardless.
  Parameters: area=15m, per_round=5, duration=scene, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full *corrupted* 2r; Crit *corrupted* 3r + *exposed*.
  Combo: null.

---

**Wound That Speaks** — Complement | Support, Controller | Eldritch, Human (corruption heavy)
Identity: Corruption speaks, gives intel, demands payment.

CAST_1 | Minor | 1p + 1 corruption | self | — | scene | information
  Effect: the wound speaks — ask one question of the corruption; receive cryptic but true answer (narrator-adjudicated).
  Parameters: info=1_answer, duration=scene.
  Playstyles: Investigator, narrative. Hook: narrative intel.

CAST_2 | Major | 2p + 1 corruption | self | — | scene | information, support
  Effect: deeper conversation — scene: free Assess per round; auto-Full if question directed through wound.
  Parameters: free_assess_per_round=1, duration=scene.
  Playstyles: Investigator. Hook: scene intel.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | scene | information, meta
  Effect: the wound speaks and answers — scene: know all enemies' intentions; ally +1 all rolls from intelligence. Self gains 1 corruption at scene end.
  Parameters: all_intentions_known=true, ally_bonus=+1, duration=scene, limit=1/scene.
  Playstyles: Investigator, Support. Hook: scene dominance.

RIDER_A | assess | all Assess types | 1p
  Effect: on_Full Assess reveals 2 facts instead of 1 (the wound fills in gaps).
  Playstyles: Investigator. Combo: wound_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: aware of corruption-carrying creatures within 20m (other *corrupted* status holders, eldritch).
  Parameters: range=20m, detect=corrupted.
  Playstyles: Investigator. Combo: corruption_awareness.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Parley via wound (cryptic speaker) +2; if target is also *corrupted*, auto-Full.
  Playstyles: Diplomat. Combo: corrupted_parley.

CAPSTONE (authored: THE ORACLE WOUND) | 4p + 2 corruption + scene_use | — | self | — | scene | meta, information
  Signal: "It speaks. I listen. I become."
  Viability: setup_dependent.
  Effect: scene: 3 questions answered; +2 all Assess rolls; ally in 5m gets 1 reroll per round. Self: 2 corruption at scene end.
  Parameters: questions=3, duration=scene, limit=1/scene.
  Playstyles: Investigator, Support.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals target's one hidden fear.
  Combo: psychological_intel.

---

## Sub-category 4.30 — Divinatory (6 powers)

---

**Revelation** — Complement | Investigator, narrative | Human, Eldritch
Identity: Sudden knowledge of hidden truth.

CAST_1 | Minor | 1p + 1 corruption | self | — | instant | information
  Effect: flash — reveal 1 hidden truth about current situation (narrator-adjudicated).
  Parameters: info=1_hidden_truth.
  Playstyles: Investigator, narrative. Hook: narrative intel.

CAST_2 | Major | 2p + 1 corruption | self | — | instant | information, meta
  Effect: deep revelation — reveal a truth with tactical weight (enemy weakness, hidden threat, ally capability).
  Parameters: info=1_tactical_truth.
  Playstyles: Investigator. Hook: tactical intel.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | scene | information, meta
  Effect: cascading truth — scene: 3 revelations spaced throughout; ally +1 all rolls from intel.
  Parameters: revelations=3, ally_bonus=+1, duration=scene, limit=1/scene.
  Playstyles: Investigator, Support. Hook: scene intel.

RIDER_A | assess | Brief or Full | 1p
  Effect: on_Full Assess reveals hidden truth; on_Crit reveals 2 hidden truths.
  Playstyles: Investigator. Combo: deep_assess.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: once per scene, when you would be surprised or deceived, you are not (and know who is deceiving).
  Parameters: auto_detect_deception=1_per_scene.
  Playstyles: Investigator, Tank. Combo: anti-deception.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Negotiate uses revealed truth as leverage; +2 to success.
  Playstyles: Diplomat. Combo: truth_leverage.

CAPSTONE (authored: ORACULAR) | 4p + 2 corruption + scene_use | — | self | — | scene | information, meta
  Signal: "I see what is hidden."
  Viability: setup_dependent.
  Effect: scene: 1 revelation per round; all Assess rolls +2; immune to deception.
  Parameters: per_round_revelation=1, assess_bonus=+2, duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: Assess also reveals target's hidden resource state (pool, phy track).
  Combo: resource_intel.

---

**Omen Reading** — Complement | Investigator, narrative | Human
Identity: Read portents; predict likely futures.

CAST_1 | Minor | 1p | — | self | — | scene | information
  Effect: omen — 1 narrative future hint (narrator-adjudicated, intentionally vague).
  Parameters: info=1_narrative_hint.
  Playstyles: narrative, Investigator. Hook: setup.

CAST_2 | Major | 2p | — | self | — | scene | information, meta
  Effect: specific omen — 1 concrete prediction about next scene (narrator binds next scene to it).
  Parameters: info=1_concrete_prediction, duration=arc.
  Playstyles: narrative. Hook: arc-shaping.

CAST_3 | Major | 3p + 1 corruption + scene_use | self | — | scene | information, meta
  Effect: deep omen — reveal 3 possible futures; narrator offers choice among them for next scene.
  Parameters: futures=3, choice=true, limit=1/scene.
  Playstyles: narrative, Controller. Hook: arc control.

RIDER_A | assess | Brief Assess | 1p
  Effect: on_Full Assess also reveals target's probable future action (next 1-2 rounds).
  Playstyles: Investigator. Combo: future_action.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense approaching events (narrator warns you of imminent significant changes).
  Parameters: scope=scene_significance.
  Playstyles: narrative. Combo: narrative_warning.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Negotiate using omen-knowledge +2.
  Playstyles: Diplomat. Combo: prophetic_parley.

CAPSTONE (authored: THE READER) | 4p + 1 corruption + scene_use | — | arc | — | arc | meta, narrative
  Signal: "I know what is coming."
  Viability: setup_dependent.
  Effect: arc: 1 omen per scene; narrator offers choice of narrative direction at each scene start.
  Parameters: per_scene_omen=1, duration=arc, limit=1/scene.
  Playstyles: narrative.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals target's intended arc-long ambition (deep intel).
  Combo: arc_intel.

---

**Listening Ear** — Complement | Investigator | Human
Identity: Hear distant conversations or thoughts.

CAST_1 | Minor | 1p | — | enemy_group | far | scene | information
  Effect: eavesdrop — hear conversations up to 50m away.
  Parameters: range=50m, info=audible_conversations, duration=scene.
  Playstyles: Investigator. Hook: passive intel.

CAST_2 | Major | 2p + 1 corruption | enemy_single | extreme | scene | information
  Effect: continuous listen — target of choice: hear all they say or silently think scene.
  Parameters: target_read=true, duration=scene.
  Playstyles: Investigator. Hook: deep intel.

CAST_3 | Major | 3p + 1 corruption + scene_use | all_visible | medium | scene | information, meta
  Effect: hive listen — all visible enemies: hear their thoughts/plans; +2 to all Assess on them.
  Parameters: scope=all_visible, assess_bonus=+2, duration=scene, limit=1/scene.
  Playstyles: Investigator, Support. Hook: scene dominance.

RIDER_A | assess | all Assess types | 1p
  Effect: on_Full Assess on listened-to target reveals their plans for next round.
  Playstyles: Investigator. Combo: plan_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: hear all conversations within 15m regardless of obstruction.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: area_listen.

RIDER_C | parley | Disorient only | 1p
  Effect: on_Full Disorient using overheard info auto-Full.
  Playstyles: Diplomat. Combo: overheard_disorient.

CAPSTONE (authored: OMNISCIENT EAR) | 4p + 1 corruption + scene_use | — | scene | extreme | scene | information, meta
  Signal: "Every word, every thought, I hear."
  Viability: setup_dependent.
  Effect: scene: all conversations and surface thoughts in 30m audible; Assess on any target auto-Full.
  Parameters: range=30m, duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals target's ally chain-of-command (who they report to).
  Combo: hierarchy_intel.

---

**Truth-Pressure** — Complement | Controller, Diplomat | Human
Identity: Force target to speak truth or suffer penalty.

CAST_1 | Minor | 1p | — | enemy_single | close | 1 round | social
  Effect: truth fog — target save will (TN 11) or must speak truth next 1r.
  Parameters: save_tn=11, truth_forced=1r.
  Playstyles: Diplomat. Hook: social leverage.

CAST_2 | Major | 2p + 1 corruption | enemy_single | medium | scene | social, control
  Effect: compelled — save will (TN 12) or must answer one question truthfully.
  Parameters: save_tn=12, truth_answer=1, duration=scene.
  Playstyles: Diplomat, Controller. Hook: investigation.

CAST_3 | Major | 3p + 2 corruption + scene_use | enemy_single | medium | scene | social, meta
  Effect: ultimate truth — save will (TN 14) or scene: cannot lie, forced to answer any direct question truthfully.
  Parameters: save_tn=14, no_lies=true, duration=scene, limit=1/scene.
  Playstyles: Diplomat. Hook: scene interrogation.

RIDER_A | parley | Demand only | 1p
  Effect: on_Full Demand + truth-force yields truthful reply.
  Playstyles: Diplomat. Combo: forced_truth.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will saves when speaking.
  Parameters: range=5m, will=-1.
  Playstyles: Diplomat. Combo: aura_truth.

RIDER_C | assess | Brief | 1p
  Effect: on_Full Assess detects lies in conversation within 10m.
  Playstyles: Investigator. Combo: lie_detection.

CAPSTONE (authored: THE INQUISITOR) | 5p + 2 corruption + scene_use | — | enemy_single | medium | scene | social, meta
  Signal: "Speak truly or suffer."
  Viability: offensive_swing.
  Effect: scene: target save will (TN 15) or cannot lie, auto-answers direct questions, *bleeding* 1r if they attempt deception.
  Parameters: save_tn=15, duration=scene, limit=1/scene.
  Playstyles: Diplomat, Controller.

ENHANCED_RIDER (broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also -1 to target's Parley resistance.
  Combo: dual_aura_pressure.

---

**Fate-Reveal** — Complement | narrative | Human, Eldritch
Identity: Reveal something's narrative purpose or destiny.

CAST_1 | Minor | 1p + 1 corruption | object_or_enemy | medium | instant | information, narrative
  Effect: small fate — reveal 1 narrative fact about target (purpose, role, hidden connection).
  Parameters: info=1_narrative_fact.
  Playstyles: narrative, Investigator. Hook: arc revelation.

CAST_2 | Major | 2p + 1 corruption | object_or_enemy | medium | scene | information, narrative
  Effect: deep fate — scene: track target's role; reveal future significance.
  Parameters: info=role_and_future, duration=scene.
  Playstyles: narrative, Controller. Hook: arc control.

CAST_3 | Major | 4p + 2 corruption + scene_use | scene | — | arc | narrative, meta
  Effect: the reading — narrator reveals arc-significance of one chosen target or object; binding narrative consequence.
  Parameters: scope=arc_revelation, binding=true, limit=1/scene.
  Playstyles: narrative. Hook: arc-defining.

RIDER_A | assess | all Assess types | 1p
  Effect: on_Full Assess reveals target's narrative significance.
  Playstyles: Investigator. Combo: narrative_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense narratively-important objects or persons within 30m.
  Parameters: range=30m, detect=narrative_significance.
  Playstyles: narrative. Combo: fate_sense.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Negotiate using fate-knowledge +2.
  Playstyles: Diplomat. Combo: fate_parley.

CAPSTONE (authored: FATE-BREAKER) | 5p + 2 corruption + scene_use | — | arc | medium | arc | narrative, meta
  Signal: "Your destiny serves me now."
  Viability: setup_dependent.
  Effect: arc: alter one fate (narrator allows narrative redirection); target gains *corrupted* permanently.
  Parameters: fate_alter=1, duration=arc, limit=1/scene.
  Playstyles: narrative, Controller.

ENHANCED_RIDER (new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals target's connection to current arc's primary antagonist.
  Combo: enemy_intel.

---

**Pattern-Read** — Complement | Investigator, Support | Human
Identity: See patterns, chains, conspiracies.

CAST_1 | Minor | 1p | — | self | — | scene | information
  Effect: pattern flash — reveal 1 pattern in recent events (narrator-adjudicated).
  Parameters: info=1_pattern.
  Playstyles: Investigator. Hook: intel.

CAST_2 | Major | 2p + 1 corruption | self | — | scene | information, meta
  Effect: connect dots — 3 facts connect; reveal underlying chain.
  Parameters: info=chain_of_3_facts, duration=scene.
  Playstyles: Investigator. Hook: deep intel.

CAST_3 | Major | 3p + 2 corruption + scene_use | self | — | arc | information, meta
  Effect: the great pattern — scene: reveal the arc-level pattern driving current events.
  Parameters: info=arc_pattern, duration=arc, limit=1/scene.
  Playstyles: narrative, Investigator. Hook: arc-shaping.

RIDER_A | assess | all Assess types | 1p
  Effect: on_Full Assess connects target to 1 other known entity (conspiracy, relationship).
  Playstyles: Investigator. Combo: connection_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense when patterns are being manipulated or hidden (detect pattern-hiders).
  Parameters: detect=pattern_manipulation.
  Playstyles: Investigator. Combo: counter-conspiracy.

RIDER_C | parley | Negotiate only | 1p
  Effect: on_Full Negotiate using pattern-intel +2.
  Playstyles: Diplomat. Combo: pattern_leverage.

CAPSTONE (authored: WEB-READER) | 4p + 2 corruption + scene_use | — | scene | — | arc | information, meta
  Signal: "I see every thread, every weaver."
  Viability: setup_dependent.
  Effect: arc: each scene reveals one arc-significant pattern; +2 all Assess rolls related to current arc.
  Parameters: per_scene_pattern=1, arc_assess_bonus=+2, duration=arc, limit=1/scene.
  Playstyles: Investigator, narrative.

ENHANCED_RIDER (chaining on RIDER_A) | 1p
  Shift: branch. Effect: connection-revealed also applies +1 to ally's next Parley with anyone in the chain.
  Combo: conspiracy_leverage.

