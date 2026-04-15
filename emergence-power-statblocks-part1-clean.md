# Emergence Power Statblocks — Full Library

**Purpose.** Full 8-mode power specifications per Power Authoring Guidelines Rev 3 §4. This document feeds directly into Claude Code implementation and narrator reference. Each power has complete spec for all 8 mode slots: 3 cast modes, 3 rider slots, 1 capstone (authored of 2 options), 1 enhanced rider (authored of 3 variants).

**Precedence.** Setting bible → `interface-spec.md` → `combat-spec-revision-4.md` → `power-authoring-guidelines-revision-3.md` → `emergence-power-content-brief.md` → THIS document.

**Format per power:**
```
**Power Name** — pair_role | playstyles | register_gating
Identity: single sentence.

CAST_N | action | pool | additional_cost | scope | range | duration | families
  Effect: description.
  Parameters: structured values.
  Playstyles: list. Hook: combo note.

RIDER_X | type/sub_category | compatible_postures | pool | restrictions
  Effect: outcome-parasitic description with on_Full/on_Marginal/on_Crit.
  Playstyles. Combo: what this enables.

CAPSTONE (authored: OPTION_NAME) | pool | additional | scope
  Signal / Viability / Effect / Parameters / Playstyles.

ENHANCED_RIDER (authored: variant_type on rider_X) | pool
  Shift / Effect / Parameters / Combo.
```

**Cost notation:** `2p + 1phy + scene_use` = 2 pool + 1 physical track + once-per-combat.
**Scope values:** self | ally | touched | enemy_single | enemy_group | zone | all_visible.
**Range bands:** touch | close (≤5m) | medium (5-15m) | far (15-30m) | extreme (>30m).
**Posture tag:** R3 = compatible with Parry/Block/Dodge; R2 = two; R1 = one; A = Aggressive-keyed.

**Status IDs (closed set per interface-spec):** bleeding, stunned, shaken, burning, exposed, marked, corrupted.
**Binary flags:** grappled, hidden.
**Effect families:** damage, status, movement, information, control, resource, defense, utility, meta, cost-shifted, action-economy, stat-alteration, terrain-alteration.

---

# BROAD: SOMATIC

## Sub-category 4.1 — Vitality

---

**Regeneration** — Complement | Tank, Sustained Caster, Hybrid | Human, Creature
Identity: Self-heal physical wounds over rounds; ignore minor harm.

CAST_1 | Minor | 1p | — | self | — | scene | defense, resource
  Effect: passive regenerative state — heal 1 phy per 2 rounds while active.
  Parameters: phy_heal_rate=1, period=2r, duration=scene.
  Playstyles: Tank, Sustained. Hook: pairs with Blood Magic, Vital Drain (feed cost).

CAST_2 | Major | 2p | — | self | — | instant | defense
  Effect: spike heal — instantly recover 2 phy.
  Parameters: phy_heal=2, duration=instant.
  Playstyles: Tank, Hybrid. Hook: emergency recovery mid-combat.

CAST_3 | Major | 3p | — | self | — | instant | defense, resource
  Effect: purge and heal — remove 1 non-persistent status + heal 2 phy.
  Parameters: status_remove=1, phy_heal=2, excludes=[corrupted, exposed, marked], duration=instant.
  Playstyles: Tank, Sustained. Hook: Vitality cleanse for Paradoxic/Anomalous pairings.

RIDER_A | posture/periodic | R2 (Parry, Block) | 0p passive
  Effect: while posture active, heal 1 phy at end of round.
  Parameters: phy_heal=1, per_round=true, postures=[parry, block].
  Playstyles: Tank, Sustained. Combo: sustained_combat_presence.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from physical attacks while armed.
  Parameters: damage_reduction=1, damage_types=[physical].
  Playstyles: Tank. Combo: posture_stacking_defense.

RIDER_C | strike | restriction: Heavy attacks only | 1p (outcome-parasitic)
  Effect: on_Marginal target bleeding 1r; on_Full bleeding 2r; on_Crit bleeding 3r + self heals 1 phy.
  Playstyles: Brawler, Sustained. Combo: bleed_stack_sustain (with Fangs, Claws).

CAPSTONE (authored: RESURGENCE) | 6p + scene_use | — | self | instant | action-economy, defense
  Signal: "I do not fall."
  Viability: conditional_no_roll (triggers on 0 phy track).
  Effect: once per scene, when reduced to 0 phy track, immediately revive at 1 phy with pool restored to base_pool_max.
  Parameters: trigger=reduced_to_0_phy, revive_phy=1, pool_restore=true, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p passive
  Shift: reinforce.
  Effect: base passive periodic regen ALSO removes 1 non-persistent status per 2 rounds.
  Parameters: delta=+status_remove=1, same_period.
  Combo: null.

---

**Healing Touch** — Complement | Support/Buffer, Hybrid | Human
Identity: Restore ally flesh by physical contact.

CAST_1 | Minor | 1p | — | touched (ally) | touch | instant | defense
  Effect: touch-heal ally +1 phy.
  Parameters: target=ally, phy_heal=1.
  Playstyles: Support. Hook: reliable mid-combat recovery.

CAST_2 | Major | 2p | — | touched (ally) | touch | 2 rounds | defense
  Effect: sustained hands-on — ally recovers 3 phy over 2 rounds (1+2 split).
  Parameters: phy_heal=3, split=[1,2], requires_maintain_touch=true.
  Playstyles: Support. Hook: positions you as immobile healer.

CAST_3 | Major | 3p + 1phy (self) | touched (ally) | touch | instant | defense, resource
  Effect: cure harm — remove one Tier 1 harm from ally (per bible Harm system).
  Parameters: harm_tier_remove=1, phy_cost_self=1.
  Playstyles: Support. Hook: emergency stabilization or post-combat cleanup.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies within 5m heal 1 phy per 2 rounds while you maintain defensive posture.
  Parameters: range=5m, phy_heal=1, period=2r, posture_req=any_defensive.
  Playstyles: Support. Combo: group_sustain (with Rally Cry, Calming Aura).

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess reveals injury severity of target (phy remaining, active statuses).
  Playstyles: Support, Investigator. Combo: triage_enablement.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Negotiate +2 when target has been healed by you this scene or prior.
  Playstyles: Diplomat. Combo: healer_as_negotiator.

CAPSTONE (authored: LAY ON HANDS) | 5p + 2phy (self) + scene_use | — | ally | touch | instant | defense, resource
  Signal: "I will not let you die."
  Viability: conditional_no_roll (ally must be at 0 phy, still alive).
  Effect: once per scene, touch ally at 0 phy; restore to 1 phy immediately with all non-persistent status removed.
  Parameters: target_req=ally_at_0_phy, phy_restore=1, status_clear=all_non_persistent, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura range extends 5m→10m; also applies to self if no ally present.
  Parameters: range_delta=+5m, self_application=true.
  Combo: null.

---

**Iron Constitution** — Complement | Tank, Sustained Caster | Human, Creature
Identity: Ignore fatigue, hunger, minor toxins.

CAST_1 | Minor | 1p | — | self | — | instant | defense, resource
  Effect: shrug off — remove 1 non-persistent status.
  Parameters: status_remove=1, excludes=[corrupted, exposed, marked].
  Playstyles: Tank, Sustained. Hook: fast status response.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: scene endurance — immune to fatigue penalties; status durations halved.
  Parameters: fatigue_immune=true, status_duration_mult=0.5, duration=scene.
  Playstyles: Tank, Sustained. Hook: long-combat specialist.

CAST_3 | Major | 3p | — | self | — | instant | resource
  Effect: second wind — recover 3 pool (capped at effective_pool_max).
  Parameters: pool_recover=3, cap=effective_pool_max.
  Playstyles: Sustained. Hook: mid-combat replenish.

RIDER_A | posture/anchor | R3 | 0p passive
  Effect: immune to forced movement; +2 defense vs Disrupt.
  Parameters: forced_movement_immune=true, disrupt_defense=+2.
  Playstyles: Tank. Combo: frontline_immovable.

RIDER_B | posture/periodic | R2 (Parry, Block) | 0p passive
  Effect: +1 pool at end of round if current pool < effective_pool_max.
  Parameters: pool_gain=1, conditional=below_max.
  Playstyles: Sustained. Combo: pool_sustain.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 damage if self phy <3; on_Crit +2 damage if self phy <3.
  Playstyles: Brawler, Glass Cannon. Combo: desperation_damage.

CAPSTONE (authored: UNYIELDING) | 5p + 1phy + scene_use | — | self | — | scene | defense
  Signal: "I don't break."
  Viability: conditional_no_roll.
  Effect: scene: cannot be reduced below 1 phy track; damage that would reduce to 0 leaves at 1.
  Parameters: phy_floor=1, duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_B) | 0p
  Shift: reinforce.
  Effect: pool gain 1→2 per round while posture active.
  Parameters: delta=+1.
  Combo: null.

---

**Disease Immunity** — Complement | Support, Tank, utility | Human
Identity: Resist and cleanse pathogens, toxins, corruption.

CAST_1 | Minor | 1p | — | self | — | instant | defense
  Effect: self-cleanse — remove burning or bleeding on self.
  Parameters: status_remove=1, scope=[burning, bleeding].
  Playstyles: Tank. Hook: anti-DoT.

CAST_2 | Major | 2p | — | touched (ally) | touch | instant | defense
  Effect: ally touch-cleanse — remove 1 non-persistent status on ally.
  Parameters: target=ally, status_remove=1, excludes=[corrupted].
  Playstyles: Support. Hook: mid-combat support.

CAST_3 | Major | 2p | — | self | — | scene | defense
  Effect: scene resistance — immune to new bio/paradoxic status applications.
  Parameters: status_immune=[burning, bleeding, corrupted], duration=scene.
  Playstyles: Tank, Support. Hook: pre-combat prep vs known enemy type.

RIDER_A | posture/reactive_status | R3 | 0p passive
  Effect: status applications against you have durations halved (min 1r).
  Parameters: status_duration_mult=0.5, min_duration=1r.
  Playstyles: Tank. Combo: status_resilience.

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full reveals environmental toxic/corrupting effects within 5m.
  Playstyles: Investigator, Support. Combo: hazard_awareness.

RIDER_C | posture/periodic | R3 | 0p passive
  Effect: reduce corruption by 1 at scene end if defensive posture was active.
  Parameters: corruption_cleanse=1, timing=scene_end.
  Playstyles: Support. Combo: paradoxic_sustainer.

CAPSTONE (authored: PURGING FIRE) | 4p + 1phy + scene_use | — | all_visible_allies | medium | instant | defense
  Signal: "I bear the cure at my own cost."
  Viability: offensive_swing (cleanse sense).
  Effect: remove all non-persistent status from visible allies at 1 phy self cost.
  Parameters: target=all_visible_allies, status_clear=all_non_persistent, phy_cost_self=1, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 0p
  Shift: reinforce.
  Effect: scene-end cleansing also reduces 1 corruption on any ally in 5m.
  Parameters: ally_corruption_cleanse=1, range=5m.
  Combo: paradoxic_party_sustainer.

---

**Wound Memory** — Complement | Support, Investigator, Assassin | Human, Eldritch (weak)
Identity: Old scars become sensory organs; touch a wound to read its source.

CAST_1 | Minor | 1p | — | self | — | instant | information
  Effect: read-scar — reveal one fact about a specific wound on self (attacker type, time, circumstance).
  Parameters: info_reveal=1_fact, narrator_adjudicated=true.
  Playstyles: Investigator. Hook: pre-combat intel.

CAST_2 | Major | 2p | — | self | — | 1 round | defense, information
  Effect: prophet-pain — scar throbs warning; +2 defense rolls against the same type of attacker next round.
  Parameters: defense_bonus=+2_vs_matched_type, duration=1r.
  Playstyles: Support, Skirmisher. Hook: scene-specific preparation.

CAST_3 | Major | 3p + 1phy | self | — | instant | information
  Effect: deep resonance — re-live a prior combat moment; next Assess this combat auto-Full.
  Parameters: next_assess=auto_full, limit=per_combat.
  Playstyles: Investigator, Assassin. Hook: Assess→spike pairing.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full when attacked, Assess reveals attacker's type (register, broad class).
  Playstyles: Investigator. Combo: reactive_assess.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect sources of recent wounds on creatures within 10m.
  Parameters: range=10m, info_scope=wound_history.
  Playstyles: Investigator. Combo: social_intel.

RIDER_C | assess | restriction: Brief or Full Assess | 1p
  Effect: on_Full Parley/Assess against combat-scarred NPC +2.
  Playstyles: Diplomat. Combo: social_leverage.

CAPSTONE (authored: SCAR-ORACLE) | 4p + 1phy + scene_use | — | self | — | scene | information, defense
  Signal: "My body remembers what my mind forgets."
  Viability: setup_dependent (requires self phy <3).
  Effect: scene: while phy <3, attacks against you reveal attacker's next-round intent.
  Parameters: condition=self_phy_below_3, reveal=next_round_intent, limit=1/scene.
  Playstyles: Investigator, Glass Cannon.

ENHANCED_RIDER (authored: chaining on RIDER_B) | 0p
  Shift: branch.
  Effect: wound-source read reveals adjacent related wound (connect conspirators, chain violence).
  Parameters: secondary_reveal=1_connected.
  Combo: conspiracy_sight (with Pattern-Read, Psychometry).

---

**Coma Return** — Complement | Tank, scene-cost specialist | Human
Identity: Return from apparent death; narrative safety net.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense, resource
  Effect: near-death trance — stunned 1r, gain 2 pool.
  Parameters: self_status=stunned_1r, pool_gain=2.
  Playstyles: Sustained. Hook: risky resource generation.

CAST_2 | Major | 2p + scene_use | — | self | — | 1 round | defense, meta
  Effect: false death — appear dead 1r; attacks against you this round auto-miss.
  Parameters: attacks_auto_miss=true, duration=1r, limit=1/scene.
  Playstyles: Trickster, Tank. Hook: emergency defense.

CAST_3 | Major | 4p + 2phy + scene_use | — | self | — | instant | defense
  Effect: resurrection pulse — if at 0 phy, revive at 1 phy.
  Parameters: trigger=self_at_0_phy, phy_revive=1, limit=1/scene.
  Playstyles: Tank.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: once per scene, reduce a potentially fatal hit to leave you at 1 phy.
  Parameters: trigger=lethal_hit, outcome=floor_at_1_phy, limit=1/scene.
  Playstyles: Tank. Combo: safety_net_sustain.

RIDER_B | posture/periodic | R2 (Parry, Block) | 0p passive
  Effect: while at 0 phy track, gain 1 phy per 2 rounds.
  Parameters: conditional=phy_at_0, phy_gain=1, period=2r.
  Playstyles: Tank. Combo: rise_from_fall.

RIDER_C | strike | restriction: Heavy attacks | 1p
  Effect: on_Full attacks while self phy <2 +1 damage; on_Crit +2 damage + exposure.
  Playstyles: Glass Cannon, Brawler. Combo: desperation_fury.

CAPSTONE (authored: LAZARUS) | 5p + scene_use | — | self | — | scene | defense, meta
  Signal: "Death does not hold me."
  Viability: conditional_no_roll.
  Effect: scene: if reduced to 0 phy, auto-revive at 2 phy + 3 pool at round end.
  Parameters: trigger=self_at_0, revive_phy=2, pool_gain=3, timing=end_of_round, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 0p
  Shift: reinforce.
  Effect: reactive_defense floors at 2 phy instead of 1.
  Parameters: delta=phy_floor_2.
  Combo: null.

---

**Vital Drain** — Primary | Brawler, Sustained Caster, Assassin | Human, Creature
Identity: Touch-siphon life force; heal self by harming target.

CAST_1 | Major | 2p | — | enemy_single | touch | instant | damage, defense
  Effect: drain touch — 2 damage target, heal 1 phy self.
  Parameters: damage=2, phy_self_heal=1.
  Playstyles: Brawler, Sustained. Hook: primary sustain attack.

CAST_2 | Major | 3p | — | enemy_single | touch | 2 rounds | damage, defense
  Effect: grasping drain — grapple required: 3 damage over 2r, 2 phy self heal.
  Parameters: damage=3_over_2r, phy_self_heal=2, requires=grapple.
  Playstyles: Brawler. Hook: grapple-lock sustain.

CAST_3 | Major | 3p + scene_use | — | enemy_single | touch | instant | damage, status, defense
  Effect: wither touch — 4 damage + burning 2r + 2 phy self heal.
  Parameters: damage=4, status=burning_2r, phy_self_heal=2, limit=1/scene.
  Playstyles: Brawler. Hook: burst sustain spike.

RIDER_A | strike | restriction: grapple attacks only | 1p
  Effect: on_Full steal 1 phy (1 damage + 1 phy self heal); on_Crit steal 2 phy.
  Playstyles: Brawler, Sustained. Combo: grapple_sustain.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from attacks made within 5m (warmth drain).
  Parameters: damage_reduction=1, range=5m.
  Playstyles: Brawler. Combo: close_range_sustainer.

RIDER_C | posture/amplify | R3 | 0p passive
  Effect: own Crits heal 1 phy on damage-dealing attacks.
  Parameters: crit_heal=1, requires=damage_attack.
  Playstyles: Brawler, Assassin. Combo: crit_sustain.

CAPSTONE (authored: LIFETHIEF) | 6p + 1phy + scene_use | — | self | — | scene | defense, meta
  Signal: "I grow strong while they weaken."
  Viability: setup_dependent.
  Effect: scene: every attack you land heals 1 phy (capped at starting phy max).
  Parameters: per_attack_heal=1, cap=phy_max_starting, duration=scene, limit=1/scene.
  Playstyles: Brawler, Sustained.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 0p
  Shift: branch (toward dual-track sustain).
  Effect: Crits on damage-attacks heal 1 phy AND 1 men.
  Parameters: delta=+men_heal_1.
  Combo: dual_track_sustain (with Mental Blast).


## Sub-category 4.2 — Metamorphosis

---

**Shapeshifting** — Flex | Trickster, utility | Human, Creature (limited)
Identity: Assume another form — human or creature.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration, meta
  Effect: quick shift — assume common NPC type form (appearance only; stats retained).
  Parameters: duration=scene, scope=appearance_only.
  Playstyles: Trickster. Hook: narrative access, infiltration.

CAST_2 | Major | 2p | — | self | — | scene | stat-alteration
  Effect: creature form — beast form; swap one attribute die tier with another.
  Parameters: attribute_swap=1_tier, duration=scene.
  Playstyles: Trickster, Skirmisher. Hook: mobility/scouting tradeoff.

CAST_3 | Major | 3p + scene_use | — | self | — | scene | stat-alteration, meta
  Effect: duplicate — assume exact form of witnessed person.
  Parameters: duration=scene, requires=witnessed_target, limit=1/scene.
  Playstyles: Trickster. Hook: social infiltration.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: detect shapeshifters and illusions within 10m.
  Parameters: range=10m, detect=[shapeshift, illusion].
  Playstyles: Investigator, Trickster. Combo: counter-deception.

RIDER_B | parley | restriction: Negotiate, Demand | 1p
  Effect: on_Full +2 Parley when in form appropriate to target context.
  Playstyles: Diplomat, Trickster. Combo: disguise_social.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition ignores terrain appropriate to current form.
  Playstyles: Skirmisher. Combo: mobility_via_form.

CAPSTONE (authored: CHIMERA) | 5p + 1phy + scene_use | — | self | — | scene | stat-alteration, meta
  Signal: "I am many."
  Viability: setup_dependent.
  Effect: scene: swap freely between 2 pre-chosen forms as Minor action.
  Parameters: forms=2_chosen, swap_cost=minor, duration=scene, limit=1/scene.
  Playstyles: Trickster.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: detection also includes voice/scent/thermal signature reads.
  Parameters: additional_detect=[voice, scent, thermal].
  Combo: null.

---

**Mimicry** — Flex | Trickster, utility | Human
Identity: Observe and replicate another's physical form and skills.

CAST_1 | Minor | 1p | — | enemy_single | medium | scene | information, stat-alteration
  Effect: read-copy — Assess target, replicate one skill for scene.
  Parameters: requires_assess=true, skill_copy=1, duration=scene.
  Playstyles: Trickster. Hook: Assess synergy.

CAST_2 | Major | 3p | — | self | — | scene | stat-alteration
  Effect: full mimicry — replicate target's attribute profile loosely.
  Parameters: attribute_mimic=approximate, duration=scene.
  Playstyles: Trickster. Hook: anti-specialist counter.

CAST_3 | Major | 2p + scene_use | — | self | — | arc | stat-alteration, meta
  Effect: sustain-copy — maintain across 3 combats in arc.
  Parameters: duration=3_combats, limit=1/scene.
  Playstyles: Trickster. Hook: long-form narrative mimicry.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full after studying opponent, +2 to rolls vs them for scene.
  Playstyles: Investigator, Trickster. Combo: study_strike.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect other mimics/shapeshifters within 15m.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: counter-mimicry.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks against Assessed target +2; on_Crit +3 damage.
  Playstyles: Assassin, Trickster. Combo: assess_spike.

CAPSTONE (authored: MIRROR) | 5p + 1phy + scene_use | — | self | — | scene | stat-alteration, meta
  Signal: "I become you wholesale."
  Viability: setup_dependent (requires prior Assess).
  Effect: scene: adopt Assessed target's form, stats, up to 2 tactical tendencies.
  Parameters: requires=prior_assess, duration=scene, limit=1/scene.
  Playstyles: Trickster.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: studied opponent's posture choice revealed to you each round.
  Parameters: posture_reveal=continuous.
  Combo: tactical_dominance.

---

**Growth** — Primary | Tank, Brawler | Human, Creature
Identity: Increase size dramatically.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration
  Effect: half-grow — +1 might die tier for scene.
  Parameters: might_delta=+1_tier, duration=scene.
  Playstyles: Brawler. Hook: quick-boost melee.

CAST_2 | Major | 2p | — | self | — | scene | stat-alteration
  Effect: full grow — +2 phy, +2 damage Heavy, -1 agi.
  Parameters: phy_delta=+2, heavy_damage=+2, agi_delta=-1, duration=scene.
  Playstyles: Tank, Brawler. Hook: scene-long frontline.

CAST_3 | Major | 3p + 1phy | self | — | scene | stat-alteration
  Effect: gigantic — +4 phy, +3 damage Heavy, -2 agi, melee-only.
  Parameters: phy_delta=+4, heavy_damage=+3, agi_delta=-2, ranged_restricted=true.
  Playstyles: Tank. Hook: scene commit.

RIDER_A | strike | restriction: Heavy attacks only | 1p
  Effect: on_Full Heavy gains reach (hits 2 additional adjacent); on_Crit as Full + targets +1 damage.
  Playstyles: Brawler. Combo: cleave_variant.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: while grown, immune to forced movement; +2 vs Disrupt.
  Parameters: conditional=grown_state.
  Playstyles: Tank. Combo: frontline_immovable.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition creates difficult terrain in path behind for 1r.
  Playstyles: Tank, Area Denier. Combo: mobile_area_denial.

CAPSTONE (authored: COLOSSUS) | 5p + 2phy + scene_use | — | self | — | scene | stat-alteration, meta
  Signal: "I am the mountain come to fight."
  Viability: offensive_swing.
  Effect: scene: +4 phy, +3 damage melee, -2 agi, immune grapple, immune exposed.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Heavy reach to 3 adjacent; +1 damage to each.
  Combo: cleave_king.

---

**Shrinking** — Complement | Assassin, Skirmisher, Trickster | Human, Creature
Identity: Reduce size, gain concealment and agility.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration
  Effect: half-shrink — +1 agi, -1 might.
  Parameters: agi_delta=+1, might_delta=-1, duration=scene.
  Playstyles: Skirmisher. Hook: agility bump.

CAST_2 | Major | 2p | — | self | — | scene | stat-alteration, status
  Effect: shrink — hidden flag, +2 Conceal, -2 melee range.
  Parameters: flag=hidden_auto, conceal=+2, melee_reach=-2, duration=scene.
  Playstyles: Skirmisher, Assassin. Hook: stealth-mobile.

CAST_3 | Major | 3p + 1phy | self | — | scene | stat-alteration, status
  Effect: atomic — effectively hidden continuously, tiny-scale only.
  Parameters: flag=hidden_absolute, movement=tiny_only.
  Playstyles: Assassin, utility. Hook: infiltration.

RIDER_A | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal auto-Full while shrunk; hidden persists +1r.
  Playstyles: Assassin. Combo: stealth_king.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from attacks while shrunk.
  Parameters: conditional=shrunk_state.
  Playstyles: Skirmisher. Combo: defensive_shrink.

RIDER_C | strike | restriction: Quick, Grapple | 1p
  Effect: on_Full attacks from shrunk +1 damage; on_Crit target exposed 1r.
  Playstyles: Assassin. Combo: micro-strike.

CAPSTONE (authored: SUBATOMIC) | 5p + 1phy + scene_use | — | self | — | scene | stat-alteration, meta
  Signal: "I disappear into the space between."
  Viability: setup_dependent.
  Effect: scene: pass through barriers (non-living); hidden vs most senses; special interactions only.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin, utility.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Conceal benefit also applies to carried objects.
  Combo: null.

---

**Fluid Form** — Complement | Skirmisher, Tank, Trickster | Human, Creature
Identity: Become semi-liquid; shape mutable, mass unchanged.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: partial liquid — +2 Dodge rolls this round.
  Parameters: dodge_bonus=+2, duration=1r.
  Playstyles: Skirmisher. Hook: reactive spike.

CAST_2 | Major | 2p | — | self | — | scene | defense, stat-alteration
  Effect: liquid form — pass through gaps; -1 physical damage.
  Parameters: gap_passable=true, physical_reduction=1, duration=scene.
  Playstyles: Skirmisher, Tank. Hook: infiltration + defense.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, stat-alteration
  Effect: full liquid — ignore terrain, immune physical damage, -1 attack rolls.
  Parameters: terrain_ignore=true, physical_immune=true, attack_penalty=-1.
  Playstyles: Tank. Hook: defensive transformation.

RIDER_A | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: -2 physical damage (liquid shifts around impact).
  Parameters: physical_reduction=2.
  Playstyles: Tank. Combo: liquid_armor.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition passes through enemy squares without provoking.
  Playstyles: Skirmisher. Combo: mobility_bypass.

RIDER_C | strike | restriction: Quick attacks | 1p
  Effect: on_Full attack ignores -2 cover/armor step; on_Crit target bleeding 1r.
  Playstyles: Brawler. Combo: cover_bypass.

CAPSTONE (authored: TOTAL FLUIDITY) | 6p + 2phy + scene_use | — | self | — | scene | defense, meta
  Signal: "I am without edges to strike."
  Viability: setup_dependent.
  Effect: scene: immune to physical damage; specific types work; attacks -1.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: chaining on RIDER_A) | 0p
  Shift: reinforce.
  Effect: liquid armor persists 2r after scene ends.
  Combo: null.

---

**Adaptive Physiology** — Complement | Sustained Caster, Tank | Human, Creature (rare)
Identity: Develop resistance to recent threats.

CAST_1 | Minor | 1p | — | self | — | scene | defense
  Effect: adapt now — +2 defense vs last-attack type for scene.
  Parameters: bonus_vs_last_type=+2, duration=scene.
  Playstyles: Tank, Sustained. Hook: reactive defense-specific.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: broad adapt — after 3rd physical hit, -1 all physical damage.
  Parameters: trigger=3_hits, reduction=-1, duration=scene.
  Playstyles: Tank. Hook: long-combat.

CAST_3 | Major | 3p + scene_use | — | self | — | scene | defense
  Effect: total adapt — immunity to one chosen damage type.
  Parameters: damage_type_immune=chosen, duration=scene, limit=1/scene.
  Playstyles: Tank. Hook: scene-lock counter.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: after 1st hit from type, -2 damage from that type rest of scene.
  Parameters: trigger=first_hit, reduction=-2.
  Playstyles: Tank. Combo: evolving_defense.

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full when hit, reveal damage type (remember for scene).
  Playstyles: Investigator, Tank. Combo: type_identification.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect damage-dealing effects within 10m.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: hazard_awareness.

CAPSTONE (authored: DOOMSDAY) | 5p + 2phy + scene_use | — | self | — | scene | defense, meta
  Signal: "What strikes me, I become immune to."
  Viability: setup_dependent.
  Effect: scene: each round, +1 reduction vs most prevalent type received (escalating).
  Parameters: escalating=+1_per_round, duration=scene, limit=1/scene.
  Playstyles: Tank, Sustained.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: reactive_defense also applies to status (halved duration after 1st).
  Combo: null.

---

**Plant Integration** — Complement | Controller, Area Denier, Support | Human
Identity: Fuse with vegetation; draw sustenance or control.

CAST_1 | Minor | 1p | — | self | — | scene | defense, stat-alteration
  Effect: root-grip — in vegetation, immune to forced movement.
  Parameters: conditional=vegetation, duration=scene.
  Playstyles: Tank. Hook: terrain-locked defense.

CAST_2 | Major | 2p | — | enemy_single | medium | instant | damage
  Effect: vine-whip — melee 10m reach in vegetation: 2 damage.
  Parameters: damage=2, range=10m, terrain_req=vegetation.
  Playstyles: Controller. Hook: terrain-specific ranged.

CAST_3 | Major | 3p | — | zone (3m) | close | scene | defense, utility
  Effect: verdant zone — 3m plant-dense terrain; allies heal 1 phy per round within.
  Parameters: zone=3m, ally_heal=1_per_round, duration=scene.
  Playstyles: Support, Area Denier. Hook: area heal + setup.

RIDER_A | posture/periodic | R2 (Block, Dodge) | 0p passive
  Effect: in vegetation, heal 1 phy per 2r.
  Parameters: phy_heal=1, period=2r, terrain_req=vegetation.
  Playstyles: Sustained. Combo: terrain_sustain.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m in vegetation +1 attack rolls.
  Parameters: range=5m, attack_bonus=+1.
  Playstyles: Support. Combo: group_buff.

RIDER_C | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal via plant cover +2; natural hiding.
  Playstyles: Skirmisher. Combo: natural_cover.

CAPSTONE (authored: BECOME GROVE) | 5p + 2phy + scene_use | — | self | — | scene | defense, utility
  Signal: "I am the garden, and the garden fights."
  Viability: setup_dependent.
  Effect: scene: planted (no Reposition); -2 damage all incoming; 10m verdant zone heals allies 1 phy per 2r.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch.
  Effect: aura_ally also grants +1 damage rolls.
  Combo: group_offensive_buff.


## Sub-category 4.3 — Augmentation

---

**Super Strength (body)** — Primary | Brawler, Tank | Human
Identity: Lift, crush, strike with force far beyond human.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | damage
  Effect: burst-strength — next Heavy attack this round +2 damage.
  Parameters: next_heavy=+2, duration=1r.
  Playstyles: Brawler. Hook: setup spike.

CAST_2 | Major | 2p | — | self | — | scene | damage, stat-alteration
  Effect: sustained strength — +1 might die, +1 damage all melee.
  Parameters: might_delta=+1, melee_damage=+1, duration=scene.
  Playstyles: Brawler, Tank. Hook: scene-long buff.

CAST_3 | Major | 3p | — | self | — | scene | utility, stat-alteration
  Effect: monstrous lift — scene: lift capacity narrator-unlimited.
  Parameters: lift_unlimited=true, duration=scene.
  Playstyles: utility, Tank. Hook: environmental + narrative.

RIDER_A | strike | restriction: Heavy attacks only | 1p
  Effect: on_Full +1 damage; on_Crit +1 damage + target exposed 1r.
  Playstyles: Brawler. Combo: heavy_fury.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers landing hits take 1 counter-damage.
  Parameters: counter=1, range=melee.
  Playstyles: Tank, Brawler. Combo: punisher_counter.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition contact pushes enemy 2m.
  Parameters: push=2m.
  Playstyles: Brawler. Combo: mobile_push.

CAPSTONE (authored: UNBOUNDED) | 5p + 1phy + scene_use | — | self | — | scene | damage, stat-alteration
  Signal: "My strength has no ceiling."
  Viability: offensive_swing.
  Effect: scene: +2 damage all melee; grapple 2 enemies simultaneously; +1 might.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Heavy +2 damage on Full (was +1), +3 on Crit (was +2).
  Combo: null.

---

**Super Speed (body)** — Primary | Skirmisher, Hybrid, Brawler | Human
Identity: Move at multiplied rate; subjective time distortion.

CAST_1 | Minor | 1p | — | self | — | 1 round | action-economy
  Effect: speed burst — extra Reposition as free action this turn.
  Parameters: extra_reposition=1.
  Playstyles: Skirmisher. Hook: emergency mobility.

CAST_2 | Major | 2p | — | self | — | scene | stat-alteration, defense
  Effect: sustained speed — +1 agi, +1 defense rolls.
  Parameters: duration=scene.
  Playstyles: Skirmisher, Hybrid. Hook: mobility buff.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, action-economy
  Effect: blur state — enemies -2 attacks vs you; Quick chain cap raised to 3.
  Parameters: enemy_penalty=-2, quick_chain=3, duration=scene.
  Playstyles: Skirmisher. Hook: evasion + attack chain.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition passes through enemies; +1 next attack roll.
  Playstyles: Skirmisher. Combo: pass_and_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from ranged attacks.
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher. Combo: ranged_evasion.

RIDER_C | strike | restriction: Quick attacks only | 1p
  Effect: on_Full Quick chains to 1 additional adjacent target; on_Crit 2.
  Playstyles: Skirmisher. Combo: chain_offense.

CAPSTONE (authored: TIME KITES) | 6p + 2phy + scene_use | — | self | — | scene | action-economy, meta
  Signal: "I step between their heartbeats."
  Viability: offensive_swing.
  Effect: scene: 2 Major actions per round instead of 1.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: after Reposition, +1 defense rolls rest of round in addition to attack bonus.
  Combo: evasive_offense.

---

**Super Reflexes** — Complement | Skirmisher, Support, Tank | Human
Identity: React faster than physical thresholds allow.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: read attack — +2 next defense roll.
  Parameters: defense_bonus=+2, duration=next_defense.
  Playstyles: Skirmisher, Tank. Hook: reactive spike.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: combat flow — scene: +1 defense rolls; on Parry Full, free 1m counter-step.
  Parameters: defense_bonus=+1, counter_step=on_parry_full.
  Playstyles: Skirmisher, Tank. Hook: scene defense.

CAST_3 | Major | 3p + 1men | self | — | scene | defense, meta
  Effect: bullet time — Dodge ranged at any range (not just close).
  Parameters: dodge_range_extend=all.
  Playstyles: Skirmisher. Hook: ranged defense specialist.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: first attack per round -1 damage.
  Parameters: first_hit_reduction=1.
  Playstyles: Tank, Skirmisher. Combo: first-strike_defense.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: preview opponents' next-turn actions.
  Parameters: preview=next_turn.
  Playstyles: Investigator, Tank. Combo: informed_defense.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess as free action while in Parry/Dodge.
  Playstyles: Skirmisher. Combo: defense_intel.

CAPSTONE (authored: PRE-EMPTIVE) | 5p + 1men + scene_use | — | self | — | scene | meta, action-economy
  Signal: "I move before their intention becomes action."
  Viability: setup_dependent.
  Effect: scene: change posture as free action.
  Parameters: posture_change_free=true, duration=scene, limit=1/scene.
  Playstyles: Tank, Skirmisher.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: awareness also previews Parley and Disrupt actions.
  Combo: null.

---

**Enhanced Senses** — Complement | Support, Assassin (setup), Investigator | Human
Identity: Hearing, smell, sight beyond human thresholds.

CAST_1 | Minor | 1p | — | enemy_single | far | instant | information, status
  Effect: focus-sense — Assess at far range; auto-marked.
  Parameters: target_auto_mark=true, range=far, assess_auto_full=true.
  Playstyles: Assassin, Support. Hook: Assess+mark spike.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | information
  Effect: sense-scan — track one target's location continuously.
  Parameters: tracking=continuous, duration=scene.
  Playstyles: Investigator. Hook: persistent tracking.

CAST_3 | Major | 3p | — | all_visible | medium | scene | status, meta
  Effect: overwhelm — shaken on visible enemies in 10m.
  Parameters: enemies_in_10m_shaken=true, duration=scene.
  Playstyles: Area Denier, Support. Hook: area status.

RIDER_A | assess | restriction: all Assess types | 1p
  Effect: on_Full Brief Assess auto-succeeds; Full reveals 2 facts.
  Playstyles: Investigator. Combo: info_surge.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect hidden within 20m; auto-break Conceal on Full.
  Parameters: range=20m.
  Playstyles: Investigator, Assassin (counter). Combo: counter_stealth.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on marked +1 damage.
  Playstyles: Assassin, Support. Combo: mark_strike.

CAPSTONE (authored: SEE THROUGH) | 5p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "Nothing conceals itself from me."
  Viability: setup_dependent.
  Effect: scene: ignore all cover; hidden cannot apply within 20m.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator, Assassin (counter).

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess reveals target's intentions (narrator hints at next round).
  Combo: null.

---

**Hyper Agility** — Complement | Skirmisher, Trickster | Human
Identity: Impossible balance and acrobatic maneuvers.

CAST_1 | Minor | 1p | — | self | — | 1 round | stat-alteration, utility
  Effect: wall-run — traverse vertical surfaces this turn as flat ground.
  Parameters: vertical_traverse=true, duration=this_turn.
  Playstyles: Skirmisher. Hook: environmental navigation.

CAST_2 | Major | 2p | — | self | — | scene | stat-alteration
  Effect: scene agility — +1 agi, +1 Reposition rolls.
  Parameters: duration=scene.
  Playstyles: Skirmisher. Hook: mobility buff.

CAST_3 | Major | 3p | — | self | — | scene | defense
  Effect: impossible dodge — Dodge posture becomes +2 to Dodge rolls.
  Parameters: dodge_bonus=+2, duration=scene.
  Playstyles: Skirmisher. Hook: defensive spike.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition allows bonus Quick attack at -2 penalty.
  Playstyles: Skirmisher. Combo: mobile_strike.

RIDER_B | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: in Dodge, -1 damage from melee.
  Parameters: posture_req=dodge.
  Playstyles: Skirmisher. Combo: dodge_specialist.

RIDER_C | maneuver | restriction: Conceal via acrobatics | 1p
  Effect: on_Full Conceal via acrobatics +2; unusual hiding spots.
  Playstyles: Trickster, Assassin. Combo: acrobatic_hide.

CAPSTONE (authored: FREERUNNER) | 5p + 1phy + scene_use | — | self | — | scene | meta, utility
  Signal: "The world is my playground."
  Viability: setup_dependent.
  Effect: scene: no Reposition roll needed; auto-Full.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce.
  Effect: bonus Quick attack also applies +1 damage on Full.
  Combo: null.

---

**Iron Body** — Primary | Tank | Human, Creature
Identity: Skin resistant to piercing, impact, burns.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: harden — +2 damage reduction on next incoming.
  Parameters: next_reduction=+2.
  Playstyles: Tank. Hook: emergency.

CAST_2 | Major | 2p | — | self | — | scene | defense, stat-alteration
  Effect: skin of stone — -1 physical, -1 agi.
  Parameters: duration=scene.
  Playstyles: Tank. Hook: scene defense.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, stat-alteration
  Effect: steel flesh — -2 physical, -2 agi, immune bleeding.
  Parameters: duration=scene.
  Playstyles: Tank. Hook: heavy defense.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage all physical.
  Parameters: reduction=1.
  Playstyles: Tank. Combo: continuous_armor.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage (armor).
  Parameters: counter=1.
  Playstyles: Tank. Combo: punisher_armor.

RIDER_C | posture/anchor | R3 | 0p passive
  Effect: immune forced movement.
  Playstyles: Tank. Combo: immovable.

CAPSTONE (authored: DIAMOND FORM) | 6p + 2phy + scene_use | — | self | — | scene | defense, stat-alteration
  Signal: "I am not a man. I am the obstacle."
  Viability: setup_dependent.
  Effect: scene: -3 physical, -3 agi, immune non-persistent statuses.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 0p
  Shift: reinforce.
  Effect: reduction -1→-2.
  Combo: null.

---

**Lung Capacity** — Complement | Support, Tank (niche), utility | Human
Identity: Breath-adapted physiology.

CAST_1 | Minor | 1p | — | self | — | scene | defense, utility
  Effect: deep breath — immune air-denial scene.
  Parameters: duration=scene.
  Playstyles: Support, utility. Hook: environmental.

CAST_2 | Major | 2p | — | touched (ally) | touch | scene | defense, utility
  Effect: sustained respiration — ally in touch breathes freely.
  Parameters: target=ally.
  Playstyles: Support. Hook: team environmental.

CAST_3 | Major | 2p | — | self | — | scene | utility, support
  Effect: breath-of-iron — scene: channel exhale for +1 to one ally cast.
  Parameters: ally_cast_bonus=+1, limit=per_trigger.
  Playstyles: Support. Hook: team-boost.

RIDER_A | posture/periodic | R3 | 0p passive
  Effect: +1 pool per 2r if breathing.
  Parameters: period=2r.
  Playstyles: Sustained. Combo: pool_sustain.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect air quality, toxins, gas in 10m.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: hazard_detect.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full survey environment; reveal 1 environmental fact.
  Playstyles: Investigator, Support. Combo: environmental_intel.

CAPSTONE (authored: BOTTOMLESS BREATH) | 4p + 1phy + scene_use | — | self + allies_in_5m | close | scene | utility, defense
  Signal: "My breath keeps my people alive."
  Viability: setup_dependent.
  Effect: scene: self and 3 allies within 5m immune suffocation; +1 pool recovery over scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch.
  Effect: periodic pool gain also +1 phy per 4r.
  Combo: null.

---

## Sub-category 4.4 — Biochemistry

---

**Venom Injection** — Primary | Controller, Sustained Caster, Assassin | Human, Creature
Identity: Toxin via touch or bite.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | damage, status
  Effect: quick venom — melee: 1 damage + burning 1r.
  Parameters: damage=1, status=burning_1r.
  Playstyles: Controller. Hook: light setup.

CAST_2 | Major | 2p | — | enemy_single | touch | 2 rounds | damage, status
  Effect: venom strike — Heavy: +2 damage + bleeding 2r.
  Parameters: requires=heavy, damage=+2, status=bleeding_2r.
  Playstyles: Controller, Sustained. Hook: DoT setup.

CAST_3 | Major | 3p + 1phy | enemy_single | touch | 1 round | status, damage
  Effect: paralytic — save might+will TN 11 or stunned 1r.
  Parameters: save_tn=11, status=stunned_1r.
  Playstyles: Controller. Hook: disable spike.

RIDER_A | strike | restriction: melee attacks only | 1p
  Effect: on_Full +1 damage; on_Crit +1 damage + bleeding 1r.
  Playstyles: Assassin, Brawler. Combo: bleeding_stack.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 poison.
  Parameters: counter=1.
  Playstyles: Controller, Tank. Combo: defensive_poison.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on bleeding +1 damage; on_Crit +2.
  Playstyles: Assassin, Sustained. Combo: status_exploit.

CAPSTONE (authored: DEATH TOUCH) | 5p + 1phy + scene_use | — | enemy_single | touch | instant | damage, status
  Signal: "One touch is all it takes."
  Viability: offensive_swing.
  Effect: Heavy auto-applies exposed + bleeding 3r regardless of outcome.
  Parameters: requires=heavy, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce.
  Effect: poison resists cure — bleeding/burning from this rider immune to standard removal for 1r.
  Combo: persistent_DoT.

---

**Pheromone Control** — Complement | Controller, Diplomat, Support | Human, Creature
Identity: Chemical emission altering emotion and behavior.

CAST_1 | Minor | 1p | — | enemy_single (adjacent) | touch | 1 round | status, social
  Effect: calm wave — adjacent enemy -1 next attack.
  Parameters: penalty=-1_next_attack.
  Playstyles: Diplomat. Hook: reactive debuff.

CAST_2 | Major | 2p | — | enemy_group (5m) | close | 1 round | status, social
  Effect: mass influence — save will TN 11 or -1 attack/defense 1r.
  Parameters: save_tn=11.
  Playstyles: Controller, Diplomat. Hook: area debuff.

CAST_3 | Major | 3p + 1men | enemy_group (close) | close | 2 rounds | control, social
  Effect: charm cloud — save will TN 12 or refuse to attack you 2r.
  Parameters: save_tn=12.
  Playstyles: Controller, Diplomat. Hook: heavy control.

RIDER_A | parley | restriction: Negotiate, Demand | 1p
  Effect: on_Full +2 Parley at close range.
  Playstyles: Diplomat. Combo: close_social.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 attacks (distracting scent).
  Parameters: range=5m.
  Playstyles: Diplomat, Tank. Combo: aura_debuff.

RIDER_C | parley | restriction: Demand only | 1p
  Effect: on_Full Demand auto-applies shaken.
  Playstyles: Diplomat. Combo: social_status.

CAPSTONE (authored: SEDUCTION) | 5p + 1men + scene_use | — | enemy_single | close | scene | control, social
  Signal: "Your will is mine to claim."
  Viability: setup_dependent.
  Effect: save will TN 13 or temporary ally for scene.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller, Diplomat.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: branch.
  Effect: aura also affects creature-register (reduced, no Parley).
  Combo: null.

---

**Corrosive Secretion** — Primary | Brawler, Area Denier | Creature (primary), Human (rare)
Identity: Acid from skin or mouth.

CAST_1 | Major | 2p | — | enemy_single | close | 2 rounds | damage, status
  Effect: acid spit — ranged close: 3 damage + burning 2r.
  Parameters: damage=3, status=burning_2r.
  Playstyles: Brawler. Hook: ranged DoT.

CAST_2 | Major | 3p | — | zone (3m cone) | close | 1 round | damage, status, terrain
  Effect: acid spray — 3m cone: 2 damage + burning + cover -1 for scene.
  Parameters: damage=2, status=burning, cover_reduction=1.
  Playstyles: Area Denier, Brawler. Hook: multi-target + env.

CAST_3 | Major | 2p | — | enemy_single (grappled) | touch | scene | damage
  Effect: corrosive touch — grapple: 2 damage + armor -1 scene.
  Parameters: requires=grapple, damage=2.
  Playstyles: Brawler. Hook: grapple debuff.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee applies burning 1r; on_Crit 2r.
  Playstyles: Brawler. Combo: burning_stack.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 acid + weapon/armor -1 for 1r.
  Playstyles: Tank. Combo: defensive_corrosion.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves 2m acid pool (1 damage entry, 1r).
  Playstyles: Skirmisher, Area Denier. Combo: trail_of_acid.

CAPSTONE (authored: FLOOD THE GROUND) | 4p + 1phy + scene_use | — | zone (5m) | close | 3 rounds | damage, terrain
  Signal: "The ground itself hates them."
  Viability: offensive_swing.
  Effect: 5m area 3r: enemies entering or starting turn take 2 damage per round.
  Parameters: limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce.
  Effect: melee also -1 target's attacks next round.
  Combo: null.

---

**Sleep Touch** — Complement | Controller, Assassin (setup) | Human
Identity: Soporific contact.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | status
  Effect: drowsy touch — target -1 next action.
  Parameters: penalty=-1.
  Playstyles: Controller. Hook: setup.

CAST_2 | Major | 2p | — | enemy_single | touch | 1 round | status, control
  Effect: deep sleep — save will TN 11 or stunned 1r + -2 next recovery.
  Parameters: save_tn=11.
  Playstyles: Controller. Hook: hard control.

CAST_3 | Major | 3p + scene_use | — | enemy_single | touch | scene | control
  Effect: coma — save will TN 13 or narrative-unconscious.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene-ending.

RIDER_A | strike | restriction: grapple attacks | 1p
  Effect: on_Full grapple target's next action -1; on_Crit -2.
  Playstyles: Assassin. Combo: grapple_status.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 defense (lethargy).
  Parameters: range=5m.
  Playstyles: Controller, Assassin. Combo: aura_vulnerability.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full +2 Destabilize when target has been touched by you.
  Playstyles: Diplomat, Controller. Combo: social_setup.

CAPSTONE (authored: DREAMLESS) | 4p + 1men + scene_use | — | enemy_single | touch | 3 rounds | control, status
  Signal: "Let their rest be eternal."
  Viability: offensive_swing.
  Effect: Heavy: stunned 3r on Full + exposed after.
  Parameters: requires=heavy, limit=1/scene.
  Playstyles: Assassin, Controller.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: aura also affects creature-register (-1 defense).
  Combo: null.

---

**Blood Magic (self)** — Primary | Burst Caster, Glass Cannon | Human
Identity: Shed own blood for enhancement.

CAST_1 | Minor | 0p + 1phy | self | — | 1 round | resource, meta
  Effect: cut for power — next cast this round +2 effect scale.
  Parameters: next_cast_scale=+2.
  Playstyles: Burst. Hook: no-pool spike.

CAST_2 | Major | 2p + 1phy | self | — | instant | resource
  Effect: blood reserves — +3 pool temp (cap effective_pool_max+2, per_combat 1).
  Parameters: pool_gain=3, limit=1/combat.
  Playstyles: Burst, Sustained. Hook: resource spike.

CAST_3 | Major | 3p + 2phy | self | — | scene | resource, meta
  Effect: empowered sacrifice — next capstone -2 pool.
  Parameters: capstone_delta=-2, duration=scene.
  Playstyles: Burst. Hook: capstone enabler.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks at <3 phy +2 damage; on_Crit +3.
  Playstyles: Glass Cannon. Combo: desperation_damage.

RIDER_B | posture/amplify | R3 | 0p passive
  Effect: own Crits +1 damage while self bleeding.
  Parameters: conditional=bleeding.
  Playstyles: Burst, Brawler. Combo: bleed_fuel.

RIDER_C | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: counter-attackers (on Parry Full) gain bleeding 1r.
  Playstyles: Tank, Brawler. Combo: blood_contagion.

CAPSTONE (authored: BLOOD RITUAL) | 4p + 2phy + scene_use | — | self | — | 1 round | meta, resource
  Signal: "My blood pays the price; the universe listens."
  Viability: setup_dependent.
  Effect: next cast this round refunds any scene_use it normally consumes.
  Parameters: limit=1/scene.
  Playstyles: Burst.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Full +3 (was +2); Crit +4 (was +3).
  Combo: null.

---

**Metabolic Fire** — Primary | Brawler, Area Denier | Human, Creature
Identity: Biological combustion (physiological, not elemental).

CAST_1 | Minor | 1p | — | zone (3m cone) | close | 1 round | damage, status
  Effect: fire breath — 3m cone: 2 damage + burning 1r.
  Parameters: damage=2, status=burning_1r.
  Playstyles: Area Denier, Brawler. Hook: quick area.

CAST_2 | Major | 2p + 1phy | self | — | scene | damage, defense, stat-alteration
  Effect: blood heat — melee +1 fire damage; -1 from cold.
  Parameters: duration=scene.
  Playstyles: Brawler. Hook: thematic conversion.

CAST_3 | Major | 3p + 1phy | self | — | scene | damage, stat-alteration
  Effect: internal furnace — +2 all melee; on Crit exhale fire to adjacent (1 damage + burning 1r).
  Parameters: duration=scene.
  Playstyles: Brawler. Hook: scene-long buff.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee +1 fire; on_Crit +1 fire + burning 1r.
  Playstyles: Brawler. Combo: fire_melee.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 fire; on Crit burning 1r.
  Playstyles: Tank, Brawler. Combo: punisher_fire.

RIDER_C | posture/periodic | R3 | 0p passive
  Effect: heal 1 phy per 2r if burning applied by you this scene.
  Parameters: conditional=burning_applied.
  Playstyles: Sustained. Combo: fire_sustain.

CAPSTONE (authored: INNER FURNACE) | 5p + 2phy + scene_use | — | self | — | scene | damage, meta
  Signal: "The flame that lives inside cannot be stolen."
  Viability: offensive_swing.
  Effect: scene: melee ignores 1 reduction step; +1 fire melee.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: branch.
  Effect: strike rider also applies to ranged (breath-based).
  Combo: ranged_fire_brawler.

---

**Electrical Anatomy** — Primary | Skirmisher, Brawler | Human, Creature
Identity: Bio-generated electricity.

CAST_1 | Minor | 1p | — | enemy_single | touch | instant | damage, status
  Effect: shock touch — melee: 1 damage + 1 electric + stunned on Crit.
  Parameters: damage=1+1_electric.
  Playstyles: Brawler. Hook: status-tagged melee.

CAST_2 | Major | 2p | — | enemy_single | close | 1 round | damage, status
  Effect: arcing current — melee: 2 electric + stunned 1r on Crit.
  Parameters: damage=2_electric.
  Playstyles: Brawler. Hook: damage + status spike.

CAST_3 | Major | 3p + 1phy | self | — | scene | damage, stat-alteration
  Effect: body-charge — +1 electric damage all melee; maneuver rider trigger on Reposition.
  Parameters: duration=scene.
  Playstyles: Brawler, Skirmisher. Hook: scene buff.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee applies stunned 1r.
  Playstyles: Brawler. Combo: stun_melee.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 electric.
  Playstyles: Tank, Brawler. Combo: electric_counter.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition through conductive terrain (water, metal) ignores penalties.
  Playstyles: Skirmisher. Combo: conductor_mobility.

CAPSTONE (authored: LIGHTNING BODY) | 5p + 1phy + scene_use | — | self | — | scene | damage, defense
  Signal: "I am the storm made flesh."
  Viability: offensive_swing.
  Effect: scene: +2 electric melee; immune electric.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: stunned 2r (was 1r) on Crit.
  Combo: null.

---

## Sub-category 4.5 — Predation

---

**Claws / Bone Extension** — Primary | Brawler, Assassin | Human, Creature
Identity: Lethal appendages from body.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration, damage
  Effect: extend claws — melee +1 damage, bypass armor 1 step.
  Parameters: duration=scene.
  Playstyles: Brawler. Hook: weapon augment.

CAST_2 | Major | 2p | — | enemy_single | touch | 2 rounds | damage, status
  Effect: clawed rend — Heavy: +2 damage + bleeding 2r.
  Parameters: requires=heavy.
  Playstyles: Brawler. Hook: damage + DoT.

CAST_3 | Major | 3p | — | enemy_single | close | 3 rounds | damage, status
  Effect: bone spike — ranged close: 3 damage + bleeding 3r.
  Parameters: damage=3.
  Playstyles: Assassin, Brawler. Hook: ranged option.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee applies bleeding 1r on Crit.
  Playstyles: Brawler, Assassin. Combo: bleeding_stack.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage (claw counter).
  Playstyles: Tank, Brawler. Combo: defensive_claws.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on bleeding +1 damage; on_Crit +2.
  Playstyles: Brawler, Sustained. Combo: bleed_exploit.

CAPSTONE (authored: RED HARVEST) | 5p + 1phy + scene_use | — | enemy_group (3 adjacent) | close | 2 rounds | damage, status
  Signal: "The blade of my body reaps."
  Viability: offensive_swing.
  Effect: Heavy hits target + 2 adjacent; all take damage + bleeding 2r.
  Parameters: requires=heavy, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce.
  Effect: claws can parry ranged attacks (+1 to Parry vs ranged).
  Combo: null.

---

**Fangs / Bite** — Primary | Brawler, Assassin | Creature (primary), Human (rare)
Identity: Lethal bite with secondary effect.

CAST_1 | Minor | 1p | — | enemy_single (grappled) | touch | 1 round | damage, status
  Effect: bite — grapple: 1 damage + bleeding 1r.
  Parameters: requires=grapple.
  Playstyles: Brawler. Hook: grapple finisher.

CAST_2 | Major | 2p | — | enemy_single (grappled) | touch | 2 rounds | damage, status
  Effect: infected bite — grapple: 2 damage + bleeding 2r + 1 per round.
  Parameters: requires=grapple.
  Playstyles: Brawler, Assassin. Hook: DoT.

CAST_3 | Major | 3p + scene_use | — | enemy_single (grappled) | touch | instant | damage, status
  Effect: death bite — grapple: 4 damage + exposed.
  Parameters: requires=grapple, limit=1/scene.
  Playstyles: Assassin. Hook: finisher.

RIDER_A | strike | restriction: grapple attacks | 1p
  Effect: on_Full grapple applies bleeding 1r.
  Playstyles: Brawler. Combo: grapple_bleeding.

RIDER_B | posture/reactive_offense | R1 (Block) | 0p passive
  Effect: melee attackers in grapple take 1 damage + bleeding on Crit.
  Playstyles: Brawler, Tank. Combo: defensive_bite.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on bleeding +1 damage.
  Playstyles: Brawler, Assassin. Combo: bleed_exploit.

CAPSTONE (authored: FEEDING) | 5p + 1phy + scene_use | — | self | — | scene | defense, meta
  Signal: "Their pain is my strength."
  Viability: setup_dependent.
  Effect: scene: heal 1 phy each round any visible enemy is bleeding.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler, Sustained.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: bite also applies shaken on Crit.
  Combo: dual_status.

---

**Wings / Flight Biological** — Complement | Skirmisher, Artillery (setup) | Creature, Human (rare)
Identity: Flight by organic wings.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: glide — Reposition +5m distance.
  Parameters: duration=1r.
  Playstyles: Skirmisher. Hook: emergency.

CAST_2 | Major | 2p | — | self | — | scene | utility, stat-alteration
  Effect: sustained flight — vertical free, +1 ranged.
  Parameters: duration=scene.
  Playstyles: Skirmisher, Artillery. Hook: aerial.

CAST_3 | Major | 2p + 1phy | enemy_single | medium | instant | damage, status
  Effect: dive strike — Heavy from flight: +2 damage + exposed on Crit.
  Parameters: requires=[heavy, flying].
  Playstyles: Assassin, Brawler. Hook: alpha strike.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes vertical 3m; ignore difficult terrain.
  Playstyles: Skirmisher. Combo: terrain_free.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect movement 20m (aerial).
  Parameters: range=20m.
  Playstyles: Support. Combo: battlefield_awareness.

RIDER_C | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged from flight +1 damage.
  Playstyles: Artillery. Combo: aerial_ranged.

CAPSTONE (authored: STORM-WING) | 5p + 1phy + scene_use | — | self | — | scene | utility, damage
  Signal: "The sky is mine."
  Viability: offensive_swing.
  Effect: scene: permanent flight; Heavy dive applies exposed on Full; flyby doesn't break engagement.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Skirmisher, Assassin.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: branch.
  Effect: Reposition can carry ally in touch.
  Combo: team_flight.

---

**Tail / Prehensile Limb** — Complement | Skirmisher, Brawler | Creature
Identity: Extra limb for grip, balance, strike.

CAST_1 | Minor | 1p | — | enemy_single | touch | instant | utility
  Effect: extra grasp — second grapple with tail possible.
  Parameters: extra_grapple=1.
  Playstyles: Brawler. Hook: dual-grapple.

CAST_2 | Major | 2p | — | enemy_single | touch | instant | damage
  Effect: coiled strike — -1 damage, +2 to hit.
  Playstyles: Skirmisher. Hook: reliable hit.

CAST_3 | Major | 3p | — | zone (2m) | close | instant | damage, control
  Effect: sweeping tail — Disrupt + 1 damage all.
  Parameters: area=2m.
  Playstyles: Area Denier. Hook: AoE tempo.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee +1 grapple bonus + 1 damage.
  Playstyles: Brawler. Combo: grapple_strike.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: tail-anchored: immune forced movement.
  Playstyles: Tank. Combo: immovable_tail.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition, tail snap at passed enemy (1 damage).
  Playstyles: Skirmisher. Combo: mobile_strike.

CAPSTONE (authored: COILING BEAST) | 4p + 1phy + scene_use | — | self | — | scene | stat-alteration
  Signal: "Two hands and a third that never lets go."
  Viability: setup_dependent.
  Effect: scene: grapple 2 simultaneously with tail; tail grapples ignore engagement penalties.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: tail wields separate weapon (third attack possible).
  Combo: triple_attack.

---

**Horns / Gore** — Primary | Brawler, Area Denier | Creature, Human (rare)
Identity: Head-mounted piercing weapon.

CAST_1 | Minor | 1p | — | self | — | 1 round | damage
  Effect: lowered horns — next Heavy +1 damage.
  Parameters: next_heavy=+1.
  Playstyles: Brawler. Hook: setup.

CAST_2 | Major | 2p | — | enemy_single | close | instant | damage, status
  Effect: goring charge — Reposition + Heavy combined: 3 damage + exposed.
  Parameters: combines_actions=true.
  Playstyles: Brawler. Hook: charge.

CAST_3 | Major | 3p | — | zone (2m cone) | close | instant | damage
  Effect: sweeping horns — 2m cone: 2 damage all.
  Playstyles: Area Denier. Hook: AoE.

RIDER_A | strike | restriction: Heavy attacks (charging) | 1p
  Effect: on_Full Heavy after Reposition +1 damage.
  Playstyles: Brawler. Combo: charge_strike.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: horns lowered: immune forced movement.
  Playstyles: Tank. Combo: immovable_charger.

RIDER_C | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: frontal attackers take 1 damage.
  Parameters: direction=frontal.
  Playstyles: Tank. Combo: punisher_frontal.

CAPSTONE (authored: UNSTOPPABLE CHARGE) | 5p + 2phy + scene_use | — | enemy_group (path) | medium | instant | damage, utility
  Signal: "Nothing stops what has momentum."
  Viability: offensive_swing.
  Effect: charge 10m through enemies; each 2 damage; destroys cover.
  Parameters: range=10m, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Heavy after Reposition +2 damage (was +1).
  Combo: null.

---

**Tracking Musk / Scent-Sense** — Complement | Assassin (setup), Investigator | Creature, Human (rare)
Identity: Sense prey by scent across distance.

CAST_1 | Minor | 1p | — | enemy_single | far | scene | information, status
  Effect: catch scent — target's location known; target marked.
  Parameters: duration=scene.
  Playstyles: Assassin, Investigator. Hook: tracking.

CAST_2 | Major | 2p | — | enemy_single | extreme | scene | information
  Effect: track — follow one target via scent.
  Parameters: duration=scene.
  Playstyles: Investigator. Hook: scene intel.

CAST_3 | Major | 3p | — | zone (30m) | medium | scene | information
  Effect: hunt-sense — 30m zone: detect all living + rough state.
  Parameters: range=30m, duration=scene.
  Playstyles: Support, Investigator. Hook: recon.

RIDER_A | assess | restriction: all Assess | 1p
  Effect: on_Full Assess on tracked reveals recent actions.
  Playstyles: Investigator. Combo: historical_tracking.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect all within 20m even hidden.
  Parameters: range=20m.
  Playstyles: Investigator. Combo: counter_stealth.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full tracked target marked continuously scene.
  Playstyles: Assassin, Support. Combo: persistent_mark.

CAPSTONE (authored: PREDATOR'S NOSE) | 5p + 1phy + scene_use | — | all_visible | — | scene | information, status
  Signal: "Nothing escapes what hunts me."
  Viability: setup_dependent.
  Effect: scene: hidden in 20m auto-revealed; all visible enemies marked.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin, Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: branch.
  Effect: Assess reveals movement history last hour.
  Combo: narrative_investigation.

---

**Bestial Rage** — Primary | Brawler, Glass Cannon, Tank | Human, Creature
Identity: Enhanced combat state from emotional/pain trigger.

CAST_1 | Minor | 1p | — | self | — | scene | damage, stat-alteration
  Effect: enter rage — +1 melee damage, -1 defense, no retreat.
  Parameters: duration=scene.
  Playstyles: Brawler. Hook: trade-off.

CAST_2 | Major | 2p + 1phy | self | — | scene | damage, stat-alteration
  Effect: deep rage — +2 melee damage, +1 phy, -2 defense, cannot Parley.
  Parameters: duration=scene.
  Playstyles: Brawler, Tank. Hook: heavier commit.

CAST_3 | Major | 3p + 2phy | self | — | scene | damage, stat-alteration, meta
  Effect: berserker — +3 damage, +2 phy, cannot act non-combat.
  Parameters: duration=scene.
  Playstyles: Brawler, Glass Cannon. Hook: full commit.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full while exposed +1 damage.
  Playstyles: Glass Cannon. Combo: exposed_exploit.

RIDER_B | posture/amplify | R1 (Aggressive) | 0p passive
  Effect: own Crits heal 1 phy while Aggressive.
  Playstyles: Glass Cannon. Combo: rage_sustain.

RIDER_C | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: +1 reduction while at <3 phy.
  Playstyles: Glass Cannon, Tank. Combo: desperation_defense.

CAPSTONE (authored: RED MIST) | 5p + 2phy + scene_use | — | self | — | scene | damage, meta
  Signal: "I go where rage takes me, and return if I can."
  Viability: offensive_swing.
  Effect: scene: enter rage +2 damage melee; scene_use refunds if survive combat.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: while exposed +2 damage (was +1).
  Combo: null.


# BROAD: COGNITIVE

## Sub-category 4.6 — Telepathic

---

**Thought Reading** — Complement | Support, Artillery (setup) | Human (strong), Creature (weak)
Identity: Hear target's surface thoughts.

CAST_1 | Minor | 1p | — | enemy_single | close | instant | information
  Effect: quick read — glimpse current intent.
  Parameters: info_reveal=current_intent.
  Playstyles: Investigator, Support. Hook: Assess boost.

CAST_2 | Major | 2p | — | enemy_single | medium | 3 rounds | information
  Effect: deep read — know opponent's actions before they declare (3r).
  Parameters: duration=3r.
  Playstyles: Investigator. Hook: tactical dominance.

CAST_3 | Major | 3p | — | zone (5m) | close | instant | information
  Effect: mass surface — 5m area: all minds briefly revealed.
  Parameters: area=5m.
  Playstyles: Support, Investigator. Hook: area intel.

RIDER_A | assess | restriction: all Assess | 1p
  Effect: on_Full Assess on humanoid reveals intent and next action.
  Playstyles: Investigator. Combo: tactical_setup.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect hostile intent in 10m.
  Parameters: range=10m.
  Playstyles: Investigator, Tank. Combo: ambush_counter.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Parley after thought-read +2.
  Playstyles: Diplomat. Combo: informed_social.

CAPSTONE (authored: TELEPATH'S TRANCE) | 5p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "I listen where words fail."
  Viability: setup_dependent.
  Effect: scene: each round, know visible humanoid intent.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator, Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess also reveals 1 related target's connection to this one.
  Combo: null.

---

**Mental Speech** — Complement | Support/Buffer, Commander | Human
Identity: Silent mind-to-mind comm.

CAST_1 | Minor | 1p | — | touched (ally) | touch | 1 round | utility
  Effect: whisper — silent ally comm bypassing language.
  Parameters: duration=1r.
  Playstyles: Support. Hook: tactical coordination.

CAST_2 | Major | 2p | — | zone (30m) | far | scene | utility
  Effect: broadcast — allies in 30m share comm link.
  Parameters: range=30m, duration=scene.
  Playstyles: Support. Hook: team comm.

CAST_3 | Major | 3p + 1men | enemy_single | extreme | 1 round | utility, meta
  Effect: command-thought — force target hears you; bypass silence.
  Parameters: silence_immune=true.
  Playstyles: Controller. Hook: psychological pressure.

RIDER_A | parley | restriction: all Parley | 1p
  Effect: on_Full Parley works silently (no spoken requirement).
  Playstyles: Diplomat. Combo: silent_negotiation.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m share silent comm.
  Parameters: range=5m.
  Playstyles: Support. Combo: team_coordination.

RIDER_C | parley | restriction: Demand only | 1p
  Effect: on_Full +2 Demand vs target who heard your voice before.
  Playstyles: Diplomat. Combo: voice_memory.

CAPSTONE (authored: HIVE SPEECH) | 5p + 1men + scene_use | — | ally_group | medium | scene | utility, meta
  Signal: "We are one mind in many bodies."
  Viability: setup_dependent.
  Effect: scene: up to 4 allies share senses and thoughts seamlessly.
  Parameters: allies=4, duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch.
  Effect: aura also grants +1 Assess to all allies in range.
  Combo: team_tactics.

---

**Psychic Blast** — Primary | Artillery, Burst Caster | Human (strong), Creature (weak)
Identity: Directed mental attack.

CAST_1 | Major | 2p | — | enemy_single | medium | instant | damage
  Effect: focused blast — 3 mental damage.
  Parameters: damage=3_mental.
  Playstyles: Artillery, Burst. Hook: ranged single-target.

CAST_2 | Major | 3p + 1men | zone (5m) | close | 1 round | damage, status
  Effect: overwhelming pulse — 4 damage + stunned on Crit.
  Parameters: damage=4, area=5m.
  Playstyles: Artillery. Hook: spike + control.

CAST_3 | Major | 3p | enemy_group (3 targets) | medium | instant | damage
  Effect: cascading — 3 visible targets: 2 mental damage each.
  Parameters: damage=2_each, targets=3.
  Playstyles: Artillery. Hook: multi-target.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full psychic attacks apply shaken on Crit.
  Playstyles: Artillery. Combo: mental_status.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers in 5m take 1 mental.
  Parameters: counter=1_mental, range=5m.
  Playstyles: Tank. Combo: mental_counter.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full attack on marked +1 mental damage.
  Playstyles: Assassin (setup), Artillery. Combo: mark_spike.

CAPSTONE (authored: MIND CRUSH) | 5p + 1men + scene_use | — | enemy_single | medium | 2 rounds | damage, status
  Signal: "I break their minds to break them."
  Viability: offensive_swing.
  Effect: 6 mental damage + stunned 2r.
  Parameters: damage=6, limit=1/scene.
  Playstyles: Artillery, Burst.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: shaken on Full (was Crit); 2r on Crit.
  Combo: null.

---

**Memory Reading** — Complement | Support, Investigator | Human
Identity: Extract specific memories from target.

CAST_1 | Minor | 1p | — | enemy_single | touch | instant | information
  Effect: surface memory — target's last few minutes revealed.
  Parameters: info_scope=last_minutes.
  Playstyles: Investigator. Hook: quick intel.

CAST_2 | Major | 2p + 1men | enemy_single | touch | instant | information, status
  Effect: deep read — specific memory; shaken 1r on fail.
  Parameters: status_on_resist=shaken_1r.
  Playstyles: Investigator. Hook: specific intel.

CAST_3 | Major | 3p + 2men | enemy_single | touch | scene | information
  Effect: life flash — entire relevant life segment.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator. Hook: narrative investigation.

RIDER_A | assess | restriction: Brief or Full Assess | 1p
  Effect: on_Full Assess reveals one memory-relevant fact about target.
  Playstyles: Investigator. Combo: investigator_detect.

RIDER_B | parley | restriction: Negotiate only | 1p
  Effect: on_Full Negotiate with read target +2.
  Playstyles: Diplomat. Combo: informed_negotiation.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks after read apply shaken 1r.
  Playstyles: Assassin. Combo: mental_setup.

CAPSTONE (authored: MIND LIBRARY) | 4p + 1men + scene_use | — | enemy_group (3 targets) | medium | instant | information
  Signal: "Their secrets are already mine."
  Viability: setup_dependent.
  Effect: read 3 targets' specific memories.
  Parameters: targets=3, limit=1/scene.
  Playstyles: Investigator, Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess reveals target's emotional state and bias.
  Combo: null.

---

**Memory Editing** — Primary | Controller, Assassin (setup) | Human
Identity: Alter target's memory; change what they know.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | control, status
  Effect: mild blur — save will TN 11 or forget last minute.
  Parameters: save_tn=11.
  Playstyles: Controller. Hook: light control.

CAST_2 | Major | 3p + 1men | enemy_single | touch | scene | control, status
  Effect: erase — save will TN 12 or forget today; confused 1r.
  Parameters: save_tn=12, status=confused_1r.
  Playstyles: Controller. Hook: heavy control.

CAST_3 | Major | 4p + 2men + scene_use | enemy_single | touch | scene | control
  Effect: rewrite — save will TN 13 or memory replaced.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene-changing.

RIDER_A | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2 (memory edit pressure).
  Playstyles: Controller, Diplomat. Combo: social_manipulation.

RIDER_B | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks after edit apply exposed.
  Playstyles: Assassin. Combo: edit_exploit.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save will or confused 1r on first hostile action each round.
  Parameters: range=5m.
  Playstyles: Controller. Combo: confusion_aura.

CAPSTONE (authored: FALSE PAST) | 5p + 1men + 1 corruption + scene_use | — | enemy_single | touch | scene | control
  Signal: "I take away what they were."
  Viability: offensive_swing.
  Effect: target forgets you entirely for scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller, Assassin.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 0p
  Shift: branch.
  Effect: aura also reduces enemy Assess rolls by 1 in 5m.
  Combo: info_denial.

---

**Astral Projection** — Flex | Controller, utility | Human, Eldritch (rare)
Identity: Consciousness travels separate from body.

CAST_1 | Major | 2p | — | self | — | scene | utility, information
  Effect: scout — project to distant location for observation.
  Parameters: range=extended, duration=scene.
  Playstyles: Investigator, Support. Hook: reconnaissance.

CAST_2 | Major | 3p + 1men | self | — | 3 rounds | action-economy, damage
  Effect: combat projection — astral form acts independently at half stats (3r).
  Parameters: duration=3r.
  Playstyles: Artillery, Controller. Hook: duplicate self.

CAST_3 | Major | 4p + 1men + scene_use | self | — | scene | meta
  Effect: astral clash — duel in astral realm (bypass physical).
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: eldritch contest.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: detect astral presences in 20m.
  Parameters: range=20m.
  Playstyles: Investigator. Combo: spiritual_awareness.

RIDER_B | assess | restriction: Brief Assess | 1p
  Effect: on_Full astral-assess reveals hidden truths.
  Playstyles: Investigator. Combo: spirit_sight.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full astral-level Parley with spirits +2.
  Playstyles: Diplomat, utility. Combo: spirit_negotiation.

CAPSTONE (authored: ASTRAL GATE) | 5p + 1men + 1 corruption + scene_use | — | zone | — | scene | meta
  Signal: "I walk where the body cannot follow."
  Viability: setup_dependent.
  Effect: scene: passage between physical/astral realms; allies can follow.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: utility.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch.
  Effect: awareness includes emotional states of astral presences.
  Combo: null.

---

**Mind Network** — Complement | Support, Commander | Human
Identity: Link multiple minds into coordinated network.

CAST_1 | Minor | 1p | — | touched (2 allies) | touch | 2 rounds | utility
  Effect: quick link — 2 allies share senses 2r.
  Parameters: duration=2r.
  Playstyles: Support. Hook: team tactics.

CAST_2 | Major | 2p | — | ally_group (3) | close | scene | utility, meta
  Effect: network — 3 allies share senses and info.
  Parameters: duration=scene.
  Playstyles: Support. Hook: coordinated team.

CAST_3 | Major | 4p + scene_use | ally_group (5) | medium | scene | utility, meta
  Effect: hive — full group coordination (5 allies).
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support. Hook: commander mode.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 Assess.
  Parameters: range=5m.
  Playstyles: Support. Combo: team_intel.

RIDER_B | parley | restriction: Negotiate | 1p
  Effect: on_Full Parley with networked ally +2.
  Playstyles: Diplomat. Combo: shared_understanding.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full once per round, any networked ally can trigger free Assess.
  Playstyles: Support, Investigator. Combo: team_assess.

CAPSTONE (authored: COLLECTIVE MIND) | 5p + 1men + scene_use | — | ally_group (5) | medium | scene | utility, meta
  Signal: "We think as one."
  Viability: setup_dependent.
  Effect: scene: up to 5 allies act as one consciousness; each can use any networked ability once.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura range 5m→10m.
  Combo: null.

---

## Sub-category 4.7 — Perceptive

---

**Psychometry** — Complement | Investigator, Support (setup) | Human
Identity: Touch object, read its history.

CAST_1 | Minor | 1p | — | object | touch | instant | information
  Effect: quick read — last event involving object.
  Playstyles: Investigator. Hook: narrative intel.

CAST_2 | Major | 2p | — | object | touch | scene | information
  Effect: deep read — full history of object/owner.
  Playstyles: Investigator. Hook: deep intel.

CAST_3 | Major | 3p + 1men | zone | touch | scene | information
  Effect: scene-read — location history reconstruction.
  Parameters: duration=scene.
  Playstyles: Investigator, Support. Hook: reconstruction.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Brief Assess on object reveals 1 fact.
  Playstyles: Investigator. Combo: object_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect significant-use objects in 5m.
  Parameters: range=5m.
  Playstyles: Investigator. Combo: scene_scanning.

RIDER_C | assess | restriction: all Assess | 1p
  Effect: on_Full Assess on person wearing an item reveals item history.
  Playstyles: Investigator. Combo: person_via_object.

CAPSTONE (authored: SCENE-OMNISCIENT) | 4p + 1men + scene_use | — | zone | close | scene | information
  Signal: "The walls tell me everything."
  Viability: setup_dependent.
  Effect: scene: entire location's history accessible for narrative.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: Assess also triggers narrator-adjudicated hint about related objects.
  Combo: null.

---

**Remote Viewing** — Complement | Support, Artillery (setup) | Human
Identity: See distant place not physically present.

CAST_1 | Major | 2p | — | zone (far) | far | scene | information
  Effect: scry — observe location out-of-sight for scene.
  Parameters: duration=scene.
  Playstyles: Support, Investigator. Hook: recon.

CAST_2 | Major | 3p + 1men | zone (extreme) | extreme | 3 rounds | information, action-economy
  Effect: far-sight — 3r: target distant location; ally can act on your info.
  Parameters: duration=3r.
  Playstyles: Artillery (setup), Support. Hook: coord strike.

CAST_3 | Major | 4p + scene_use | zone (battlefield) | medium | scene | information, meta
  Effect: overwatch — entire battlefield from above for scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support, Commander. Hook: dominion.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess while scrying +1 to roll.
  Playstyles: Investigator. Combo: distant_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect scrying attempts against you.
  Playstyles: Investigator, Tank. Combo: counter-scry.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Parley with target scried +2.
  Playstyles: Diplomat, Investigator. Combo: informed_social.

CAPSTONE (authored: SCRIER THRONE) | 5p + 1men + scene_use | — | ally_group (all_visible) | — | scene | information, meta
  Signal: "I see, and my allies see through me."
  Viability: setup_dependent.
  Effect: scene: share viewed information with all allies continuously.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess reveals 2 facts at distance.
  Combo: null.

---

**Vision Modes** — Complement | Support, specialist | Human
Identity: See hidden wavelengths (thermal, x-ray, UV).

CAST_1 | Minor | 1p | — | self | — | 1 round | information
  Effect: x-ray flash — see through 1 obstacle this round.
  Parameters: duration=1r.
  Playstyles: Investigator. Hook: quick reveal.

CAST_2 | Major | 2p | — | self | — | scene | information, stat-alteration
  Effect: multi-spectrum — all wavelengths active scene.
  Parameters: duration=scene.
  Playstyles: Investigator, Support. Hook: persistent.

CAST_3 | Major | 2p | — | self | — | scene | information
  Effect: thermal — see through smoke/darkness; heat signatures.
  Parameters: duration=scene.
  Playstyles: Skirmisher, Investigator. Hook: concealment counter.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess reveals concealed items/weapons.
  Playstyles: Investigator. Combo: concealed_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect hidden via thermal in 15m.
  Parameters: range=15m.
  Playstyles: Assassin (counter), Investigator. Combo: thermal_detect.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full Brief Assess reveals target's equipment details.
  Playstyles: Investigator. Combo: tactical_equipment.

CAPSTONE (authored: TRUE VISION) | 5p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "Nothing hides from my eyes."
  Viability: setup_dependent.
  Effect: scene: no illusion or camouflage works within 20m.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator, Assassin (counter).

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: Assess also reveals structural weakness of armor/items.
  Combo: anti-armor.

---

**Tracking Sense** — Complement | Assassin, Investigator | Human
Identity: Sense specific target at distance.

CAST_1 | Minor | 1p | — | enemy_single | — | scene | information, status
  Effect: lock target — know rough location scene; target marked.
  Parameters: duration=scene.
  Playstyles: Assassin. Hook: tracking.

CAST_2 | Major | 2p | — | enemy_single | far | 3 rounds | information, status
  Effect: focused track — exact location/direction 3r.
  Parameters: duration=3r.
  Playstyles: Investigator, Assassin. Hook: pursuit.

CAST_3 | Major | 3p + 1phy | enemy_single | extreme | scene | information, status
  Effect: blood-bond — target marked continuously.
  Parameters: duration=scene.
  Playstyles: Assassin. Hook: scene-long hunt.

RIDER_A | assess | restriction: Brief or Full Assess | 1p
  Effect: on_Full Assess reveals full target profile if tracked.
  Playstyles: Investigator. Combo: deep_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: tracked target's actions real-time awareness.
  Playstyles: Investigator, Assassin. Combo: real_time.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on tracked +1 damage.
  Playstyles: Assassin. Combo: mark_strike.

CAPSTONE (authored: BLOODHOUND) | 5p + 1phy + scene_use | — | self | — | scene | information, meta
  Signal: "Nothing escapes my hunt."
  Viability: setup_dependent.
  Effect: scene: follow target through all terrain; target marked continuously.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: magnitude on RIDER_C) | 1p
  Shift: reinforce.
  Effect: on_Full +2 (was +1); on_Crit +3.
  Combo: null.

---

**Aura Sight** — Complement | Investigator, Support | Human, Eldritch
Identity: See emotional/power states around others.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | information
  Effect: quick-read — basic aura (emotion, health).
  Playstyles: Investigator. Hook: quick intel.

CAST_2 | Major | 2p | — | all_visible | medium | scene | information
  Effect: field read — all visible auras readable.
  Parameters: duration=scene.
  Playstyles: Investigator. Hook: scene intel.

CAST_3 | Major | 3p + 1men | enemy_single | medium | instant | information, meta
  Effect: deep-aura — target's supernatural nature revealed.
  Playstyles: Investigator. Hook: register identification.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Brief Assess reveals power category of target.
  Playstyles: Investigator. Combo: power_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect supernatural in 10m.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: eldritch_detect.

RIDER_C | parley | restriction: Negotiate, Demand | 1p
  Effect: on_Full Parley vs supernatural +2.
  Playstyles: Diplomat. Combo: supernatural_social.

CAPSTONE (authored: ALL-SEEING) | 5p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "No soul is hidden from me."
  Viability: setup_dependent.
  Effect: scene: all auras visible, powers named in narrator.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess also reveals target's corruption level (if any).
  Combo: null.

---

**Psychic Sonar** — Complement | Support, Skirmisher, Assassin (counter) | Human
Identity: 3D map via mental echolocation.

CAST_1 | Minor | 1p | — | zone (10m) | close | instant | information
  Effect: ping — reveal all entities in 10m.
  Playstyles: Investigator. Hook: reveal.

CAST_2 | Major | 2p | — | zone (20m) | medium | scene | information
  Effect: sustained — 20m continuous awareness.
  Parameters: range=20m, duration=scene.
  Playstyles: Support. Hook: persistent reveal.

CAST_3 | Major | 3p + 1men | structure | medium | scene | information, meta
  Effect: deep scan — map entire structure.
  Parameters: duration=scene.
  Playstyles: Investigator. Hook: reconnaissance.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: detect movement 15m through walls.
  Parameters: range=15m.
  Playstyles: Investigator, Assassin (counter). Combo: wall_awareness.

RIDER_B | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess in darkness normal (no penalty).
  Playstyles: Assassin (counter). Combo: dark_intel.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition through obscured at full speed.
  Playstyles: Skirmisher. Combo: dark_mobility.

CAPSTONE (authored: PERFECT SONAR) | 5p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "I see through darkness and walls alike."
  Viability: setup_dependent.
  Effect: scene: 30m omniscience (all entities and structures).
  Parameters: range=30m, duration=scene, limit=1/scene.
  Playstyles: Investigator, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch.
  Effect: awareness also detects intent (aggressive, cautious) of moving entities.
  Combo: tactical_intel.

---

**Reader-Glance** — Complement | Investigator, Support | Human
Identity: Analyze scene rapidly for non-obvious connections.

CAST_1 | Minor | 1p | — | zone | close | instant | information
  Effect: quick deduction — 1 tactical fact revealed.
  Playstyles: Investigator. Hook: setup.

CAST_2 | Major | 2p | — | enemy_group | medium | scene | information
  Effect: deep analysis — multiple strategic facts, weaknesses.
  Parameters: duration=scene.
  Playstyles: Investigator. Hook: scene intel.

CAST_3 | Major | 3p + 1men | ally_group | medium | scene | information, meta
  Effect: mastermind — scene: +2 to all allies' attacks via guidance.
  Parameters: duration=scene.
  Playstyles: Support, Commander. Hook: support spike.

RIDER_A | assess | restriction: Brief or Full Assess | 1p
  Effect: on_Full Assess reveals 2 facts instead of 1.
  Playstyles: Investigator. Combo: info_doubling.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect hidden motives in 10m.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: hidden_motive_detect.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Parley +1 from reading.
  Playstyles: Diplomat. Combo: read_social.

CAPSTONE (authored: SHERLOCK STATE) | 5p + 1men + scene_use | — | ally_group (all_visible) | — | scene | information, meta
  Signal: "I see patterns others cannot."
  Viability: setup_dependent.
  Effect: scene: all allies +1 to all rolls via your continuous guidance.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support, Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Assess reveals target's long-term goals (narrator).
  Combo: null.

---

## Sub-category 4.8 — Predictive

---

**Precognition** — Primary | Controller, Artillery | Human, Eldritch
Identity: Near-future glimpses aid combat decisions.

CAST_1 | Minor | 1p | — | self | — | 1 round | information, action-economy
  Effect: next-turn — know opponents' declared actions before declaring yourself.
  Parameters: duration=1r.
  Playstyles: Tank, Support. Hook: tactical dominance.

CAST_2 | Major | 2p | — | self | — | scene | defense, information
  Effect: short foresight — +1 all defense; redirect one attack.
  Parameters: redirect=1, duration=scene.
  Playstyles: Skirmisher, Tank. Hook: defensive spike.

CAST_3 | Major | 3p + 1men | self | — | scene | meta
  Effect: deep foresight — +2 initiative, +1 all rolls.
  Parameters: duration=scene.
  Playstyles: Controller. Hook: general enhancement.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: know opponents' posture choices this turn.
  Playstyles: Investigator, Tank. Combo: posture_anticipation.

RIDER_B | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess reveals next action of target.
  Playstyles: Investigator, Assassin. Combo: alpha_strike.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: reroll one defense roll per scene.
  Parameters: limit=1/scene.
  Playstyles: Tank, Skirmisher. Combo: foreseen_defense.

CAPSTONE (authored: TEMPORAL MASTERY) | 6p + 2men + 1 corruption + scene_use | — | self | — | scene | meta, action-economy
  Signal: "Time yields its secrets to me."
  Viability: offensive_swing.
  Effect: scene: always act first; 1 attack auto-Crit per scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Artillery, Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_C) | 0p
  Shift: reinforce.
  Effect: reroll applies to any roll (was defense only).
  Combo: null.

---

**Danger Sense** — Complement | Skirmisher, Support | Human
Identity: Warning of imminent harm.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: alert — +2 defense next round.
  Parameters: duration=1r.
  Playstyles: Tank, Skirmisher. Hook: reactive spike.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: sustained — +1 all defense; detect surprises.
  Parameters: duration=scene.
  Playstyles: Support, Tank. Hook: scene defense.

CAST_3 | Major | 3p + 1men | self | — | scene | defense, information
  Effect: battle-read — foresee all incoming for +2 defense.
  Parameters: duration=scene.
  Playstyles: Skirmisher. Hook: defensive dominance.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: first attack each round -1 damage.
  Playstyles: Tank, Skirmisher. Combo: first_strike_defense.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect ambushes and hidden threats.
  Playstyles: Investigator. Combo: counter-ambush.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full Brief Assess reveals incoming threat level.
  Playstyles: Support. Combo: threat_assessment.

CAPSTONE (authored: SIXTH SENSE) | 5p + 1men + scene_use | — | self | — | scene | defense, meta
  Signal: "I feel their strikes before they move."
  Viability: setup_dependent.
  Effect: scene: immune to surprise; 1 reroll per round.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank, Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch.
  Effect: awareness also warns of environmental hazards.
  Combo: hazard_avoidance.

---

**Tactical Overlay** — Complement | Support, Controller | Human
Identity: See opponent's patterns and predict tactics.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | information
  Effect: analyze — +2 next attack on target.
  Parameters: duration=1r.
  Playstyles: Assassin (setup), Support. Hook: spike.

CAST_2 | Major | 2p | — | enemy_group | medium | scene | information, status
  Effect: pattern read — +1 attacks on marked; detect tactics.
  Parameters: duration=scene.
  Playstyles: Support, Artillery. Hook: scene buff.

CAST_3 | Major | 3p + 1men | ally_group | medium | scene | information, meta
  Effect: master tactician — all allies +1 attack rolls.
  Parameters: duration=scene.
  Playstyles: Support, Commander. Hook: team buff.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess bonus +2 instead of +1.
  Playstyles: Investigator. Combo: assess_spike.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 attacks.
  Parameters: range=5m.
  Playstyles: Support. Combo: offensive_aura.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks after Assess auto-Full on Marginal (upgrade).
  Playstyles: Artillery, Assassin. Combo: setup_payoff.

CAPSTONE (authored: DEATHSTROKE MODE) | 5p + 1men + scene_use | — | enemy_group (visible_marked) | — | scene | information, damage
  Signal: "I see every opening."
  Viability: setup_dependent.
  Effect: scene: marked targets auto-Crit on Full attack rolls (upgrade).
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin, Artillery.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce.
  Effect: aura also grants allies +1 damage.
  Combo: total_offensive.

---

**Probability Glimpse** — Complement | Trickster, Support | Human, Eldritch
Identity: See likely outcome before committing.

CAST_1 | Minor | 1p | — | self | — | 1 round | meta
  Effect: reroll commit — reroll one failed die this round.
  Playstyles: Trickster. Hook: defensive reroll.

CAST_2 | Major | 2p | — | self | — | scene | meta
  Effect: double-read — one reroll per round.
  Parameters: duration=scene.
  Playstyles: Trickster, Support. Hook: scene rerolls.

CAST_3 | Major | 3p + 1men | self | — | scene | meta
  Effect: destiny glimpse — reroll any die scene.
  Parameters: duration=scene.
  Playstyles: Trickster. Hook: scene-long flex.

RIDER_A | posture/amplify | R3 | 0p passive
  Effect: own Crits reveal a future fact (narrator).
  Playstyles: Investigator, Trickster. Combo: crit_intel.

RIDER_B | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess reveals target's probability weakness.
  Playstyles: Investigator, Assassin. Combo: weakness_read.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks with reroll available +1 damage.
  Playstyles: Trickster. Combo: luck_strike.

CAPSTONE (authored: DESTINY'S EDGE) | 5p + 1men + 1 corruption + scene_use | — | self | — | scene | meta
  Signal: "I choose the outcome that serves me."
  Viability: setup_dependent.
  Effect: scene: +1 all rolls; 3 rerolls.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Trickster.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch.
  Effect: Crits also grant +1 pool (luck).
  Combo: crit_sustain.

---

**Lie Detection** — Complement | Investigator, Support | Human
Identity: Know falsehood from truth.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | information
  Effect: quick detection — 1 statement's truth revealed.
  Playstyles: Investigator. Hook: quick intel.

CAST_2 | Major | 2p | — | all_visible | close | scene | information
  Effect: sustained — all lies in scene known.
  Parameters: duration=scene.
  Playstyles: Investigator, Diplomat. Hook: scene intel.

CAST_3 | Major | 3p + 1men | enemy_single | medium | 1 round | information, status
  Effect: deep interrogation — Parley auto-reveals 1 hidden truth.
  Parameters: duration=1r.
  Playstyles: Investigator. Hook: extract.

RIDER_A | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2 when target is lying.
  Playstyles: Diplomat. Combo: lie_pressure.

RIDER_B | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess in Parley reveals true motive.
  Playstyles: Investigator. Combo: motive_read.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full +2 Negotiate vs known-liar.
  Playstyles: Diplomat. Combo: leverage_lying.

CAPSTONE (authored: INQUISITOR) | 4p + 1men + scene_use | — | enemy_group (3) | medium | scene | information
  Signal: "The truth will out."
  Viability: setup_dependent.
  Effect: extract 3 truths from targets scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator, Diplomat.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Destabilize +3 on Full (was +2); target also shaken 1r.
  Combo: null.

---

**Weakness Read** — Complement | Controller, Assassin | Human
Identity: Identify vulnerabilities in target.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | information
  Effect: vulnerability glimpse — Assess reveals one vulnerability.
  Playstyles: Assassin, Investigator. Hook: quick intel.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | information, meta
  Effect: comprehensive — track target weaknesses; +1 exploiting attacks.
  Parameters: duration=scene.
  Playstyles: Assassin. Hook: scene setup.

CAST_3 | Major | 3p + 1men | enemy_single | medium | scene | information, status
  Effect: primal — reveal target's fundamental weakness; exploit condition revealed.
  Parameters: duration=scene.
  Playstyles: Assassin. Hook: target-specific prep.

RIDER_A | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess reveals damage vulnerability (type).
  Playstyles: Investigator, Assassin. Combo: type_targeting.

RIDER_B | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks vs marked with known vulnerability +2 damage.
  Playstyles: Assassin. Combo: weakness_exploit.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full +2 Destabilize vs weakness-known target.
  Playstyles: Diplomat. Combo: social_weakness.

CAPSTONE (authored: EXECUTIONER) | 5p + 1men + scene_use | — | enemy_single | medium | scene | damage, meta
  Signal: "I know where to strike."
  Viability: setup_dependent.
  Effect: scene: attacks on known-weakness ignore all damage reduction.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: magnitude on RIDER_B) | 1p
  Shift: reinforce.
  Effect: +3 damage on Full (was +2); +4 on Crit.
  Combo: null.

---

**Doom Sense** — Complement | Tank, Survival | Human, Eldritch
Identity: Sense oncoming fatal events.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense, meta
  Effect: imminent warning — free Reposition or Posture change if doom imminent.
  Parameters: duration=1r.
  Playstyles: Tank, Skirmisher. Hook: reactive safety.

CAST_2 | Major | 2p | — | self | — | scene | information
  Effect: long-foresight — detect death-level threats in scene.
  Parameters: duration=scene.
  Playstyles: Investigator, Tank. Hook: intel.

CAST_3 | Major | 4p + scene_use | self | — | scene | defense, meta
  Effect: prevent doom — avoid 1 fatal outcome this scene.
  Parameters: limit=1/scene.
  Playstyles: Tank. Hook: fatal-dodge.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: first fatal-level attack per scene -50% damage.
  Parameters: limit=1/scene.
  Playstyles: Tank. Combo: safety_net.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect incoming lethal threats (narrator hints).
  Playstyles: Investigator, Tank. Combo: threat_prep.

RIDER_C | assess | restriction: Brief Assess | 1p
  Effect: on_Full Assess reveals lethal intent.
  Playstyles: Investigator. Combo: intent_detect.

CAPSTONE (authored: DEATH DODGER) | 5p + 1men + 1 corruption + scene_use | — | self | — | scene | defense, meta
  Signal: "Death has an appointment I have postponed."
  Viability: conditional_no_roll.
  Effect: once completely avoid a lethal outcome (0 damage instead).
  Parameters: limit=1/scene.
  Playstyles: Tank, Survival.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: reactive_defense also applies to fatal status effects (e.g., lethal exposed).
  Combo: null.

---

## Sub-category 4.9 — Dominant

---

**Mind Control** — Primary | Controller | Human
Identity: Override target will directly.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | 1 round | control
  Effect: brief compulsion — target does 1 Minor action of your choice.
  Parameters: duration=1r.
  Playstyles: Controller. Hook: minor control.

CAST_2 | Major | 3p + 1men | enemy_single | medium | 3 rounds | control
  Effect: domination — save will TN 12 or follow command 3r.
  Parameters: save_tn=12.
  Playstyles: Controller. Hook: medium control.

CAST_3 | Major | 5p + 2men + 1 corruption + scene_use | enemy_single | medium | scene | control, meta
  Effect: enslavement — save will TN 14 or target becomes ally scene.
  Parameters: save_tn=14, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene-ending.

RIDER_A | parley | restriction: Demand only | 1p
  Effect: on_Full Demand auto-succeeds if target failed will earlier.
  Playstyles: Diplomat, Controller. Combo: will_exploit.

RIDER_B | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attack after domination +1 damage.
  Playstyles: Assassin (setup). Combo: control_strike.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will saves.
  Parameters: range=5m.
  Playstyles: Controller. Combo: will_pressure.

CAPSTONE (authored: PUPPET MASTER) | 5p + 2men + 1 corruption + scene_use | — | enemy_group (3) | medium | scene | control
  Signal: "Their will is mine."
  Viability: offensive_swing.
  Effect: scene: dominate up to 3 targets (save will TN 13 each).
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: Demand also applies shaken 1r on Full.
  Combo: null.

---

**Compulsion** — Primary | Controller, Diplomat | Human
Identity: Force single specific action from target.

CAST_1 | Minor | 1p + 1men | enemy_single | close | 1 round | control
  Effect: force action — save will TN 11 or specific simple action.
  Parameters: save_tn=11.
  Playstyles: Controller. Hook: mild control.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 1 round | control
  Effect: sustained — save will TN 12 or follow command 1r.
  Playstyles: Controller. Hook: targeted control.

CAST_3 | Major | 3p + 2men + 1 corruption + scene_use | enemy_single | medium | 2 rounds | control
  Effect: absolute — save will TN 14 or cannot refuse 2r.
  Parameters: save_tn=14, duration=2r, limit=1/scene.
  Playstyles: Controller. Hook: heavy control.

RIDER_A | parley | restriction: Demand | 1p
  Effect: on_Full Demand compulsion-adjacent: forced truth.
  Playstyles: Diplomat. Combo: social_compulsion.

RIDER_B | parley | restriction: Destabilize only | 1p
  Effect: on_Full +2 Destabilize.
  Playstyles: Diplomat. Combo: pressure.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will.
  Playstyles: Controller. Combo: will_pressure.

CAPSTONE (authored: ABSOLUTE ORDER) | 4p + 2men + 1 corruption + scene_use | — | enemy_single | medium | scene | control
  Signal: "Obey without question."
  Viability: offensive_swing.
  Effect: save will TN 14 or follow orders scene.
  Parameters: save_tn=14, duration=scene, limit=1/scene.
  Playstyles: Controller, Diplomat.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 0p
  Shift: reinforce.
  Effect: aura also affects 2 willpower-related rolls per round (action cost reduced).
  Combo: null.

---

**Illusion** — Flex | Trickster, Controller | Human (stronger), Eldritch (weaker)
Identity: False sensation in target's senses.

CAST_1 | Minor | 1p | — | zone (small) | close | 1 round | meta
  Effect: simple illusion — small visible illusion; Minor action to disbelieve.
  Parameters: duration=1r.
  Playstyles: Trickster. Hook: distraction.

CAST_2 | Major | 2p | — | zone (medium) | medium | scene | meta
  Effect: complex — scene: sustained moderate complexity.
  Parameters: duration=scene.
  Playstyles: Trickster. Hook: sustained.

CAST_3 | Major | 3p + 1men | all_visible | medium | 3 rounds | meta, control
  Effect: mass — all visible save will TN 12 or perceive as real.
  Parameters: save_tn=12, duration=3r.
  Playstyles: Controller, Trickster. Hook: area illusion.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition creates illusion of staying (enemy targets original).
  Playstyles: Trickster, Skirmisher. Combo: escape_illusion.

RIDER_B | parley | restriction: Destabilize only | 1p
  Effect: on_Full +2 Destabilize via false info.
  Playstyles: Diplomat, Trickster. Combo: deception_pressure.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Assess against you.
  Parameters: range=5m.
  Playstyles: Trickster. Combo: assess_denial.

CAPSTONE (authored: REALITY HACK) | 5p + 2men + 1 corruption + scene_use | — | zone | close | 1 round | meta, control
  Signal: "The world bends to my lie."
  Viability: setup_dependent.
  Effect: one illusion affects physics briefly (narrator-adjudicated significant effect).
  Parameters: limit=1/scene.
  Playstyles: Trickster, Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 1p
  Shift: branch.
  Effect: Destabilize also shaken 1r on Full.
  Combo: null.

---

**Confusion** — Complement | Controller | Human
Identity: Scramble target's perception and decision-making.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | 1 round | status, control
  Effect: quick — save will TN 11 or -2 next action.
  Parameters: save_tn=11.
  Playstyles: Controller. Hook: light disable.

CAST_2 | Major | 2p | — | enemy_single | medium | 1 round | status, control
  Effect: deep — save will TN 12 or confused 1r.
  Parameters: save_tn=12.
  Playstyles: Controller. Hook: status.

CAST_3 | Major | 3p + 1men | zone (3m) | close | 1 round | status, control
  Effect: mass — 3m area: save will or confused 1r.
  Parameters: area=3m.
  Playstyles: Controller, Area Denier. Hook: area disable.

RIDER_A | parley | restriction: Destabilize only | 1p
  Effect: on_Full +2 Destabilize to confuse (narrative confusion).
  Playstyles: Diplomat. Combo: social_confusion.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 perception rolls.
  Playstyles: Controller. Combo: perception_denial.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on confused auto-Full on Marginal.
  Playstyles: Assassin, Brawler. Combo: confused_exploit.

CAPSTONE (authored: CHAOS TOUCH) | 4p + 1men + 1 corruption + scene_use | — | enemy_group (3) | medium | 2 rounds | status, control
  Signal: "I unravel their minds."
  Viability: offensive_swing.
  Effect: 3 targets confused 2r (save TN 13).
  Parameters: save_tn=13, duration=2r, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 1p
  Shift: reinforce.
  Effect: attack on confused also +1 damage.
  Combo: null.

---

**Hypnosis** — Complement | Controller, Diplomat | Human
Identity: Gradual submission via focused gaze.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | social
  Effect: subtle suggestion — target -1 to resist next Parley.
  Playstyles: Diplomat. Hook: social setup.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 2 rounds | status, social
  Effect: sustained trance — 2r: shaken and follows suggestions.
  Parameters: duration=2r.
  Playstyles: Controller, Diplomat. Hook: longer control.

CAST_3 | Major | 3p + 1men + scene_use | enemy_single | medium | scene | control, meta
  Effect: deep hypnosis — save will TN 13 or obeys suggestions 1 hour post-combat.
  Parameters: save_tn=13, duration=post_combat_1hr, limit=1/scene.
  Playstyles: Controller. Hook: narrative implant.

RIDER_A | parley | restriction: Negotiate, Demand | 1p
  Effect: on_Full all Parley vs hypnotized +1.
  Playstyles: Diplomat. Combo: social_mastery.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Parley resistance.
  Playstyles: Controller, Diplomat. Combo: social_pressure.

RIDER_C | parley | restriction: Demand | 1p
  Effect: on_Full Demand triggers hypnotic state on Full.
  Playstyles: Diplomat. Combo: voice_hypnosis.

CAPSTONE (authored: TRANCE MASTER) | 5p + 1men + 1 corruption + scene_use | — | enemy_single | medium | scene | social, control
  Signal: "They will do as I say. They always will."
  Viability: setup_dependent.
  Effect: scene: all Parley +2; one hypnotized target retains loyalty post-scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Diplomat, Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: all Parley +2 (was +1); hypnotized also -1 defense.
  Combo: null.

---

**Fear Induction** — Complement | Controller, Area Denier | Human, Creature
Identity: Impose fear on targets.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | status
  Effect: quick — shaken 1r.
  Playstyles: Controller. Hook: quick status.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 2 rounds | status, control
  Effect: terror — save will TN 12 or shaken 2r + -1 attacks.
  Parameters: save_tn=12, duration=2r.
  Playstyles: Controller. Hook: medium control.

CAST_3 | Major | 3p + 1men | zone (5m) | close | 1 round | status
  Effect: mass — 5m: save will TN 12 or shaken 1r.
  Parameters: area=5m.
  Playstyles: Area Denier, Controller. Hook: area status.

RIDER_A | parley | restriction: Demand | 1p
  Effect: on_Full Demand on shaken auto-Full.
  Playstyles: Diplomat. Combo: fear_leverage.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Parley resistance.
  Playstyles: Controller. Combo: social_pressure.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on shaken +1 damage.
  Playstyles: Assassin, Brawler. Combo: shaken_exploit.

CAPSTONE (authored: TERROR LORD) | 5p + 1men + 1 corruption + scene_use | — | all_visible | medium | scene | status, control
  Signal: "Fear is the shape I take."
  Viability: offensive_swing.
  Effect: scene: all visible save will TN 13 or shaken and cannot approach within 5m.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: magnitude on RIDER_C) | 1p
  Shift: reinforce.
  Effect: +2 damage on shaken (was +1).
  Combo: null.

---

**Possession** — Primary | Controller; rare | Human, Eldritch
Identity: Inhabit another's body temporarily.

CAST_1 | Major | 3p + 1men + 1 corruption | enemy_single | touch | 1 round | control, meta
  Effect: brief — save will TN 12; control target Minor next turn.
  Parameters: save_tn=12.
  Playstyles: Controller. Hook: micro-control.

CAST_2 | Major | 4p + 2men + 1 corruption + scene_use | enemy_single | touch | 2 rounds | control, meta
  Effect: sustained — save will TN 13; control 2r.
  Parameters: save_tn=13, duration=2r, limit=1/scene.
  Playstyles: Controller. Hook: heavy control.

CAST_3 | Major | 5p + 3men + 2 corruption + scene_use | enemy_single | touch | scene | control, meta
  Effect: body theft — save will TN 14; transfer to target for scene; original body vulnerable.
  Parameters: save_tn=14, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene-long.

RIDER_A | parley | restriction: Destabilize | 1p
  Effect: on_Full +2 Destabilize.
  Playstyles: Diplomat. Combo: possess_pressure.

RIDER_B | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks against possessed go to both (you and them).
  Playstyles: Assassin. Combo: dual_damage.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save or confused 1r per round.
  Playstyles: Controller. Combo: confusion_aura.

CAPSTONE (authored: PUPPET SOUL) | 5p + 2men + 2 corruption + scene_use | — | enemy_single | touch | scene | control
  Signal: "I wear them as a coat."
  Viability: offensive_swing.
  Effect: scene: one target possessed; operator functional.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch.
  Effect: Destabilize applied via possession also shaken 1r.
  Combo: null.

---

## Sub-category 4.10 — Auratic

---

**Fear Aura** — Complement | Area Denier, Controller | Human, Creature
Identity: Terror zone around you.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | status
  Effect: aura of dread — 3m: enemies -1 attacks 1r.
  Parameters: area=3m, duration=1r.
  Playstyles: Area Denier. Hook: quick debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | status
  Effect: chilling presence — 5m aura scene: save will TN 11 on entry or shaken 1r.
  Parameters: save_tn=11, area=5m, duration=scene.
  Playstyles: Area Denier, Controller. Hook: persistent zone.

CAST_3 | Major | 3p + 1men | all_visible | medium | scene | status, control
  Effect: total dread — all visible save will TN 13 or shaken + refuse approach.
  Parameters: save_tn=13, duration=scene.
  Playstyles: Controller, Area Denier. Hook: scene dominance.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 attacks.
  Parameters: range=5m.
  Playstyles: Area Denier. Combo: aura_debuff.

RIDER_B | parley | restriction: Demand | 1p
  Effect: on_Full Parley on shaken auto-Full.
  Playstyles: Diplomat. Combo: fear_leverage.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on shaken +1 damage.
  Playstyles: Assassin, Brawler. Combo: shaken_exploit.

CAPSTONE (authored: NIGHTMARE FIELD) | 5p + 1men + 1 corruption + scene_use | — | zone (10m) | medium | scene | status
  Signal: "They cannot breathe near me."
  Viability: setup_dependent.
  Effect: scene: 10m area continuous shaken; enemies in -2 attacks.
  Parameters: area=10m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura range 5m→8m; penalty -1 still.
  Combo: null.

---

**Awe Aura** — Complement | Support, Controller | Human
Identity: Project reverence that freezes action.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | social
  Effect: impressive — enemies in 3m -1 Parley next.
  Parameters: area=3m.
  Playstyles: Diplomat. Hook: Parley debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | control, social
  Effect: overwhelming — 5m aura: save will TN 12 or forfeit attack vs you 1r.
  Parameters: save_tn=12, area=5m, duration=scene.
  Playstyles: Controller, Diplomat. Hook: powerful zone.

CAST_3 | Major | 3p + 1men + scene_use | all_visible (10m) | medium | 1 round | control
  Effect: godly — area 10m: failures cannot act.
  Parameters: save_tn=13, duration=1r, limit=1/scene.
  Playstyles: Controller. Hook: scene-changing.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Parley resistance.
  Playstyles: Diplomat. Combo: social_dominance.

RIDER_B | parley | restriction: Demand | 1p
  Effect: on_Full Demand auto-Full on in-aura target.
  Playstyles: Diplomat. Combo: voice_authority.

RIDER_C | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 attacks (reverence).
  Playstyles: Support. Combo: team_buff.

CAPSTONE (authored: DIVINE PRESENCE) | 5p + 1men + 1 corruption + scene_use | — | all_visible | medium | 2 rounds | control, social
  Signal: "I am presence. They are shadows."
  Viability: setup_dependent.
  Effect: scene: visible enemies save TN 14 or kneel (no aggressive action).
  Parameters: save_tn=14, duration=2r, limit=1/scene.
  Playstyles: Controller, Diplomat.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 0p
  Shift: branch.
  Effect: aura_ally also grants +1 Parley.
  Combo: ally_support.

---

**Command Voice** — Primary | Controller, Diplomat | Human
Identity: Spoken imperative carries supernatural weight.

CAST_1 | Minor | 1p + 1men | enemy_single | close | 1 round | social, control
  Effect: single command — save will TN 11 or obey 1-word Minor next.
  Parameters: save_tn=11.
  Playstyles: Diplomat. Hook: micro-control.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 1 round | control, social
  Effect: voiced compulsion — save will TN 12 or follow phrase 1r.
  Parameters: save_tn=12.
  Playstyles: Controller, Diplomat. Hook: medium.

CAST_3 | Major | 4p + 2men + 1 corruption + scene_use | enemy_single | medium | 2 rounds | control, meta
  Effect: absolute voice — save will TN 14 or obey 5-word 2r.
  Parameters: save_tn=14, duration=2r, limit=1/scene.
  Playstyles: Controller. Hook: narrative dominance.

RIDER_A | parley | restriction: Demand | 1p
  Effect: on_Full Demand double effect when Command Voice active scene.
  Playstyles: Diplomat. Combo: voice_amplifier.

RIDER_B | parley | restriction: Disorient | 1p
  Effect: on_Full Disorient auto-Full if target heard Command.
  Playstyles: Diplomat. Combo: voice_chain.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will.
  Playstyles: Controller. Combo: will_pressure.

CAPSTONE (authored: WORD OF POWER) | 5p + 2men + 1 corruption + scene_use | — | enemy_single | medium | scene | control, meta
  Signal: "Speak, and reality obeys."
  Viability: offensive_swing.
  Effect: scene: one unbreakable command per combat (no save).
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller, Diplomat.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce.
  Effect: Demand triple effect (was double).
  Combo: null.

---

**Rally Cry** — Complement | Support/Buffer | Human
Identity: Inspire allies to greater effort.

CAST_1 | Minor | 1p | — | ally_group (5m) | close | 1 round | utility
  Effect: battle shout — allies in 5m +1 attack 1r.
  Parameters: area=5m, duration=1r.
  Playstyles: Support. Hook: quick buff.

CAST_2 | Major | 2p | — | ally_group (5m) | close | scene | utility, action-economy
  Effect: rally — allies in 5m +1 attack; one free action 1r.
  Parameters: duration=scene.
  Playstyles: Support. Hook: scene buff.

CAST_3 | Major | 3p + 1men + scene_use | ally_group (10m) | medium | 2 rounds | utility, status
  Effect: legendary — 10m: allies +2 attacks 2r; remove shaken.
  Parameters: area=10m, duration=2r, limit=1/scene.
  Playstyles: Support, Commander. Hook: group spike.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 attacks.
  Playstyles: Support. Combo: offensive_aura.

RIDER_B | parley | restriction: Negotiate | 1p
  Effect: on_Full Negotiate with ally-actions +2.
  Playstyles: Diplomat. Combo: coordination.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Crit ally-targeted status clearing (if any ally in 5m shaken/stunned).
  Playstyles: Support. Combo: group_cleanse.

CAPSTONE (authored: COMMANDER'S STRIKE) | 5p + 1men + scene_use | — | ally_group (all_visible) | — | scene | utility, meta
  Signal: "We rise, we strike, we endure."
  Viability: offensive_swing.
  Effect: scene: all allies +2 attacks; +1 damage.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support, Commander.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura range 5m→10m.
  Combo: null.

---

**Calming Aura** — Complement | Diplomat, Support | Human
Identity: Reduce hostility in zone.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | status, social
  Effect: calm presence — shaken/enraged enemies in 3m save will TN 11 or end condition.
  Parameters: save_tn=11.
  Playstyles: Diplomat. Hook: cleanse-zone.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | social, control
  Effect: pacification — hostile enemies save will TN 12 or lose 1 attack this turn.
  Parameters: save_tn=12, area=5m, duration=scene.
  Playstyles: Diplomat. Hook: scene debuff.

CAST_3 | Major | 3p + 1men + scene_use | zone (5m) | close | scene | control, meta
  Effect: truce — save will TN 13 or parley enabled (forced negotiation).
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller, Diplomat. Hook: narrative.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 hostile actions (first action each round).
  Playstyles: Diplomat. Combo: peace_zone.

RIDER_B | parley | restriction: Negotiate | 1p
  Effect: on_Full +2 Negotiate.
  Playstyles: Diplomat. Combo: social_mastery.

RIDER_C | parley | restriction: Destabilize | 1p
  Effect: on_Full +2 Parley vs calm-affected.
  Playstyles: Diplomat. Combo: calmed_leverage.

CAPSTONE (authored: SANCTUARY) | 4p + 1men + 1 corruption + scene_use | — | ally_group (5m) | close | scene | defense, social
  Signal: "This place will not be a battlefield."
  Viability: setup_dependent.
  Effect: scene: one area where allies cannot be attacked while within 5m.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Diplomat, Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura also +1 Negotiate vs in-aura targets.
  Combo: null.

---

**Despair Field** — Complement | Controller, Area Denier | Human, Eldritch
Identity: Remove hope from zone; paralyze will.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | status
  Effect: dampening — enemies in 3m -1 will rolls.
  Parameters: area=3m.
  Playstyles: Controller. Hook: will debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | status
  Effect: sustained despair — 5m: save will TN 12 or lose 1 Minor 1r.
  Parameters: save_tn=12, area=5m, duration=scene.
  Playstyles: Controller, Area Denier. Hook: action-economy.

CAST_3 | Major | 3p + 1men + scene_use | zone (10m) | medium | 2 rounds | status, control
  Effect: total — 10m: save will TN 13 or confused 2r.
  Parameters: save_tn=13, area=10m, duration=2r, limit=1/scene.
  Playstyles: Controller. Hook: heavy control.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will saves.
  Playstyles: Controller. Combo: will_denial.

RIDER_B | parley | restriction: Destabilize | 1p
  Effect: on_Full +2 Destabilize.
  Playstyles: Diplomat, Controller. Combo: social_despair.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on despair-affected (in aura) +1 damage.
  Playstyles: Assassin, Brawler. Combo: aura_exploit.

CAPSTONE (authored: HEART OF DARKNESS) | 5p + 1men + 1 corruption + scene_use | — | all_visible | medium | scene | status, control
  Signal: "Hope dies in my presence."
  Viability: offensive_swing.
  Effect: scene: all visible save will TN 13 or refuse to act on Full.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce.
  Effect: aura also -1 all defense rolls.
  Combo: null.

---

**Charismatic Draw** — Complement | Diplomat, Support | Human
Identity: Bystanders focus on you involuntarily.

CAST_1 | Minor | 1p | — | enemy_single (nearest) | close | 1 round | status, control
  Effect: magnetic — nearest enemy in 5m moves 2m toward you.
  Parameters: move_toward=2m.
  Playstyles: Diplomat. Hook: positioning.

CAST_2 | Major | 2p | — | zone (10m) | medium | scene | status
  Effect: crowd pull — enemies in 10m -1 to attack others.
  Parameters: area=10m, duration=scene.
  Playstyles: Diplomat, Tank. Hook: aggro.

CAST_3 | Major | 3p + 1men + scene_use | all_visible | medium | 1 round | control
  Effect: legendary pull — all visible save will TN 13 or move toward you.
  Parameters: save_tn=13, limit=1/scene.
  Playstyles: Controller, Diplomat. Hook: aggro dominance.

RIDER_A | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m save or move toward you each round.
  Playstyles: Diplomat, Tank. Combo: aggro_zone.

RIDER_B | parley | restriction: Demand | 1p
  Effect: on_Full Demand auto-Full on drawn enemies.
  Playstyles: Diplomat. Combo: drawn_social.

RIDER_C | parley | restriction: Disorient | 1p
  Effect: on_Full +2 Disorient on close ones (within 5m).
  Playstyles: Diplomat. Combo: close_pressure.

CAPSTONE (authored: CULT LEADER) | 5p + 1men + 2 corruption + scene_use | — | enemy_group (3) | medium | scene | social, control
  Signal: "They follow me, whether I will or no."
  Viability: setup_dependent.
  Effect: scene: 3 targets save will TN 13 or temporary allies.
  Parameters: save_tn=13, duration=scene, limit=1/scene.
  Playstyles: Controller, Diplomat.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch.
  Effect: aura also grants +1 to all own Parley rolls.
  Combo: social_amplifier.


# BROAD: MATERIAL

## Sub-category 4.11 — Elemental

---

**Pyrokinesis** — Primary | Artillery, Area Denier, Sustained Caster | Human, Creature
Identity: Generate and control fire.

CAST_1 | Major | 2p | — | enemy_single | far | instant | damage, status
  Effect: lance — far range: 3 fire damage + burning on Crit.
  Parameters: damage=3, status_on_crit=burning_1r.
  Playstyles: Artillery. Hook: ranged spike.

CAST_2 | Major | 3p | — | zone (3m) | medium | 1 round | damage, status
  Effect: bloom — 3m area: 2 fire + burning on Marginal+.
  Parameters: damage=2_all, status_on_marginal_plus=burning_1r.
  Playstyles: Area Denier. Hook: area DoT.

CAST_3 | Major | 2p | — | self | — | scene | damage, stat-alteration
  Effect: forge — weapon/hands +1 fire melee.
  Parameters: melee_fire=+1, duration=scene.
  Playstyles: Brawler, Hybrid. Hook: scene melee buff.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 fire damage; on_Crit burning 1r.
  Playstyles: Artillery, Brawler. Combo: fire_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 fire damage; -2 from matching element.
  Parameters: fire_reduction=1, matching_element=2.
  Playstyles: Tank. Combo: elemental_armor.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves burning trail 1r (1 fire to entries).
  Playstyles: Skirmisher, Area Denier. Combo: trail_of_fire.

CAPSTONE (authored: CONFLAGRATION) | 5p + 1phy + scene_use | — | all_visible (close) | close | 2 rounds | damage, terrain-alteration
  Signal: "I am the burning."
  Viability: offensive_swing.
  Effect: massive damage to close visible; zone burning 2r.
  Parameters: damage=4_all, area_zone=close_visible, duration=2r, limit=1/scene.
  Playstyles: Area Denier, Eradicator.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full +2 fire (was +1); Crit burning 2r.
  Combo: null.

---

**Cryokinesis** — Primary | Controller, Area Denier | Human
Identity: Generate cold and ice.

CAST_1 | Major | 2p | — | enemy_single | far | instant | damage, status
  Effect: freeze lance — 3 cold + save will or stunned 1r.
  Parameters: damage=3, save_tn=11, status_on_fail=stunned_1r.
  Playstyles: Controller, Artillery. Hook: damage + control.

CAST_2 | Major | 3p | — | zone (3m wall) | medium | 2 rounds | terrain-alteration, defense
  Effect: ice wall — 3m wall for 2r.
  Parameters: wall=3m, duration=2r.
  Playstyles: Area Denier, Tank. Hook: terrain control.

CAST_3 | Major | 2p | — | zone (5m) | close | scene | defense, terrain-alteration
  Effect: frost aura — 5m: allies -1 cold; enemies +1 difficult terrain.
  Parameters: ally_cold_reduction=1, enemy_difficult=true, duration=scene.
  Playstyles: Area Denier. Hook: scene terrain.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 cold; on_Crit stunned 1r.
  Playstyles: Controller. Combo: cold_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 cold damage; -2 matching.
  Parameters: cold_reduction=1.
  Playstyles: Tank. Combo: cold_armor.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves ice trail: difficult terrain 2r.
  Playstyles: Area Denier. Combo: trail_of_ice.

CAPSTONE (authored: ABSOLUTE ZERO) | 5p + 1phy + scene_use | — | enemy_single | medium | 2 rounds | damage, status
  Signal: "I freeze the world to stillness."
  Viability: offensive_swing.
  Effect: save or stunned 2r + 2 cold + exposed.
  Parameters: save_tn=14, status=stunned_2r_plus_exposed, damage=2_cold, limit=1/scene.
  Playstyles: Controller, Eradicator.

ENHANCED_RIDER (authored: new_dimension on RIDER_C) | 1p
  Shift: branch. Effect: ice trail also -1 enemy attack rolls in trail.
  Combo: null.

---

**Electrokinesis** — Primary | Artillery, Area Denier | Human
Identity: Generate electricity (material control, distinct from Electrical Anatomy).

CAST_1 | Minor | 1p | — | enemy_single | touch | instant | damage, status
  Effect: shock — melee: 1 electric + stunned on Crit.
  Parameters: damage=1_electric, status_on_crit=stunned_1r.
  Playstyles: Brawler. Hook: spike status.

CAST_2 | Major | 2p | — | enemy_single | medium | instant | damage
  Effect: lightning bolt — ranged: 3 electric + chain to adjacent (1 electric).
  Parameters: damage=3, chain_adjacent=1_electric.
  Playstyles: Artillery. Hook: chain damage.

CAST_3 | Major | 3p + 1phy | zone (5m) | medium | 1 round | damage, status
  Effect: thunderstorm — 5m: 2 electric + stunned on save-fail.
  Parameters: area=5m, damage=2_electric, save_tn=12, status_on_fail=stunned_1r.
  Playstyles: Area Denier. Hook: area control.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 electric; on_Crit stunned.
  Playstyles: Artillery. Combo: electric_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 electric.
  Parameters: counter=1.
  Playstyles: Tank. Combo: electric_counter.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition through conductive terrain free.
  Playstyles: Skirmisher. Combo: conductor_mobility.

CAPSTONE (authored: STORM LORD) | 5p + 1phy + scene_use | — | zone (10m) | medium | 1 round | damage, status
  Signal: "The sky is mine to call down."
  Viability: offensive_swing.
  Effect: 10m: electric all + stunned on save-fail.
  Parameters: area=10m, damage=2_electric, save_tn=13, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: chaining on RIDER_A) | 1p
  Shift: reinforce. Effect: strike also chains to adjacent (1 electric).
  Combo: null.

---

**Hydrokinesis** — Primary | Controller, Area Denier, utility | Human
Identity: Control water.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | damage, control
  Effect: water whip — melee 3m reach: 1 damage + disarm attempt.
  Parameters: damage=1, disarm_attempt=true.
  Playstyles: Controller. Hook: light disarm.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage, status
  Effect: water blade — ranged: 2 damage + bleeding on Crit.
  Parameters: damage=2, status_on_crit=bleeding_1r.
  Playstyles: Artillery. Hook: ranged spike.

CAST_3 | Major | 3p + 1phy | zone (5m line) | medium | instant | damage, movement
  Effect: tidal wave — 5m line: 2 damage + push 3m.
  Parameters: damage=2_all, push=3m.
  Playstyles: Area Denier. Hook: push + damage.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks +1 damage + disarm on Full.
  Playstyles: Controller. Combo: disarm_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 from impact/kinetic.
  Parameters: kinetic_reduction=1.
  Playstyles: Tank. Combo: kinetic_armor.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition through water at full speed.
  Playstyles: Skirmisher. Combo: water_mobility.

CAPSTONE (authored: TYPHOON) | 5p + 1phy + scene_use | — | zone (10m) | medium | 2 rounds | damage, terrain-alteration
  Signal: "The water rises to my will."
  Viability: offensive_swing.
  Effect: 10m: 2 damage + difficult 2r.
  Parameters: area=10m, damage=2_all, terrain=difficult, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: disarm also pulls weapon to your hand.
  Combo: weapon_steal.

---

**Geokinesis** — Primary | Tank, Area Denier | Human
Identity: Control earth and stone.

CAST_1 | Major | 2p | — | enemy_single | medium | instant | damage, status
  Effect: earth spike — close: 3 damage + bleeding.
  Parameters: damage=3, status=bleeding_1r.
  Playstyles: Brawler. Hook: damage spike.

CAST_2 | Major | 3p | — | zone (3m wall) | medium | 3 rounds | terrain-alteration
  Effect: stone wall — 3m wall 3r: cover + barrier.
  Parameters: wall=3m, duration=3r.
  Playstyles: Area Denier, Tank. Hook: terrain control.

CAST_3 | Major | 3p + 1phy | zone (5m) | medium | 1 round | damage, status, terrain-alteration
  Effect: earthquake — 5m: save agi or fall/exposed.
  Parameters: area=5m, save_tn=12, status_on_fail=exposed.
  Playstyles: Area Denier. Hook: area control.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee +1 damage; push 1m.
  Playstyles: Brawler. Combo: push_strike.

RIDER_B | posture/anchor | R3 | 0p passive
  Effect: immune to forced movement; +2 vs Disrupt.
  Parameters: immune=true, disrupt=+2.
  Playstyles: Tank. Combo: immovable.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition creates difficult terrain behind 1r.
  Playstyles: Tank, Area Denier. Combo: trail_terrain.

CAPSTONE (authored: EARTHSHAPER) | 5p + 1phy + scene_use | — | zone (10m wall) | medium | scene | terrain-alteration
  Signal: "The land obeys me."
  Viability: setup_dependent.
  Effect: massive 10m stone wall structure for scene.
  Parameters: wall=10m, duration=scene, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: anchor also reduces incoming damage by 1.
  Combo: dual_anchor.

---

**Aerokinesis** — Primary | Skirmisher, Controller | Human
Identity: Control wind.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | movement, control
  Effect: gust — push target 2m or knock back.
  Parameters: push=2m_or_knockback.
  Playstyles: Controller. Hook: positioning.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage, control
  Effect: wind blade — ranged: 2 damage + ignore 1 cover step.
  Parameters: damage=2, cover_ignore=1_step.
  Playstyles: Artillery. Hook: cover bypass.

CAST_3 | Major | 3p + 1phy | zone (5m) | medium | 1 round | damage, control, status
  Effect: tempest — 5m: save might or knocked back 3m, exposed.
  Parameters: area=5m, save_tn=12, knockback=3m, status_on_fail=exposed.
  Playstyles: Area Denier, Controller. Hook: area control.

RIDER_A | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged ignore 1 cover; +1 damage.
  Playstyles: Artillery. Combo: cover_strike.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes flight 5m.
  Playstyles: Skirmisher. Combo: aerial_mobility.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: incoming ranged -1 damage (deflection).
  Parameters: ranged_reduction=1.
  Playstyles: Tank. Combo: anti-ranged.

CAPSTONE (authored: STORM CALLER) | 5p + 1phy + scene_use | — | zone (10m) | medium | scene | control, terrain-alteration
  Signal: "The wind is mine to summon."
  Viability: setup_dependent.
  Effect: 10m: continuous winds push enemies (1m per round at start).
  Parameters: area=10m, push_per_round=1m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: ignore 2 cover steps (was 1).
  Combo: null.

---

**Magma-kinesis** — Primary | Area Denier, Eradicator | Human (rare), Eldritch (rare)
Identity: Molten rock hybrid.

CAST_1 | Major | 2p + 1phy | enemy_single | far | 2 rounds | damage, status
  Effect: magma lance — ranged: 4 damage + burning 2r.
  Parameters: damage=4, status=burning_2r.
  Playstyles: Artillery, Area Denier. Hook: spike DoT.

CAST_2 | Major | 3p + 1phy | zone (3m) | medium | 3 rounds | damage, terrain-alteration
  Effect: eruption — 3m: 3 fire + difficult 3r.
  Parameters: area=3m, damage=3_fire, terrain=difficult_3r.
  Playstyles: Area Denier. Hook: area + terrain.

CAST_3 | Major | 4p + 1phy + scene_use | zone (5m) | medium | scene | damage, terrain-alteration
  Effect: volcanic field — 5m: continuous fire + burning each round.
  Parameters: area=5m, per_round_damage=2_fire, status=burning, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Eradicator. Hook: scene zone.

RIDER_A | strike | restriction: melee/ranged | 1p
  Effect: on_Full +2 fire damage; on_Full burning 2r.
  Playstyles: Brawler, Artillery. Combo: fire_DoT_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers take 1 fire + burning 1r on Crit.
  Parameters: counter_fire=1.
  Playstyles: Tank. Combo: defensive_fire.

RIDER_C | posture/periodic | R3 | 0p passive
  Effect: heal 1 phy per 2r in fire (own zones).
  Parameters: phy_heal=1, period=2r, conditional=in_fire.
  Playstyles: Sustained. Combo: fire_sustain.

CAPSTONE (authored: VOLCANIC HEART) | 6p + 2phy + scene_use | — | zone (10m) | medium | scene | damage, terrain-alteration
  Signal: "The earth's blood is mine."
  Viability: offensive_swing.
  Effect: 10m: massive fire; burning 3r all entries.
  Parameters: area=10m, damage=3_fire, burning_3r=true, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Eradicator.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 0p
  Shift: branch. Effect: also heals allies in 5m (1 phy per 4r in fire).
  Combo: party_fire_sustain.

---

## Sub-category 4.12 — Transmutative

---

**Transmute Substance** — Flex | utility, Controller | Human (primary)
Identity: Change substance type/property.

CAST_1 | Minor | 1p | — | object (small) | touch | scene | utility
  Effect: minor transmute — small object substance changes (narrator-adjudicated).
  Parameters: scope=small_object, duration=scene.
  Playstyles: Trickster, utility. Hook: narrative + tactical.

CAST_2 | Major | 2p | — | enemy_single (weapon) | medium | 2 rounds | control
  Effect: combat transmute — target weapon brittle: -2 damage 2r.
  Parameters: target_weapon_damage=-2, duration=2r.
  Playstyles: Controller. Hook: anti-weapon.

CAST_3 | Major | 3p + 1pool | zone (3m) | close | scene | terrain-alteration
  Effect: environmental — 3m terrain: difficult or hazardous.
  Parameters: area=3m, terrain=difficult_or_hazardous, duration=scene.
  Playstyles: Area Denier. Hook: scene terrain.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks transmute target's armor: -1 scene.
  Playstyles: Controller. Combo: armor_decay.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect material composition of items in 5m.
  Parameters: range=5m.
  Playstyles: Investigator. Combo: material_intel.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition path may transmute (terrain shift).
  Playstyles: Skirmisher. Combo: terrain_walker.

CAPSTONE (authored: ALCHEMIST) | 5p + 1phy + scene_use | — | object (1 major) | medium | scene | utility, meta
  Signal: "Matter answers me."
  Viability: setup_dependent.
  Effect: one major transmutation (item, structure, terrain segment).
  Parameters: scope=major, duration=scene, limit=1/scene.
  Playstyles: utility, Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: armor decay also weakens defense rolls -1.
  Combo: dual_debuff.

---

**Matter Creation** — Complement | Support, Tank, utility | Human (primary)
Identity: Generate solid from nothing.

CAST_1 | Minor | 1p | — | self | — | scene | utility
  Effect: small creation — tool: +1 to relevant skill check.
  Parameters: skill_bonus=+1, duration=scene.
  Playstyles: utility, Support. Hook: contextual.

CAST_2 | Major | 2p | — | self | — | scene | damage, defense
  Effect: weapon conjure — temp weapon: +1 damage.
  Parameters: melee_damage=+1, duration=scene.
  Playstyles: Brawler. Hook: scene weapon.

CAST_3 | Major | 2p | — | zone (2m wall) | close | 2 rounds | terrain-alteration, defense
  Effect: barrier — 2m wall 2r.
  Parameters: wall=2m, duration=2r.
  Playstyles: Tank. Hook: tactical cover.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks with conjured weapon +1 damage.
  Playstyles: Brawler. Combo: conjure_strike.

RIDER_B | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: conjured armor: -1 damage.
  Parameters: reduction=1.
  Playstyles: Tank. Combo: conjure_armor.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess creates relevant tool (+1 to next action).
  Playstyles: utility. Combo: tool_setup.

CAPSTONE (authored: ARCHITECT) | 4p + 1phy + scene_use | — | zone (significant structure) | close | scene | utility, terrain-alteration
  Signal: "I make what is needed from air."
  Viability: setup_dependent.
  Effect: significant object/structure for scene.
  Parameters: scope=significant, duration=scene, limit=1/scene.
  Playstyles: utility, Support.

ENHANCED_RIDER (authored: broadening on RIDER_C) | 1p
  Shift: branch. Effect: tool also benefits ally in 5m.
  Combo: party_support.

---

**Solidify Energy** — Complement | Support, Controller | Human
Identity: Energy into shape.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: small construct — glowing shield: +2 defense 1r.
  Parameters: defense=+2, duration=1r.
  Playstyles: Tank. Hook: spike defense.

CAST_2 | Major | 2p | — | self | — | scene | damage, defense, utility
  Effect: construct — solid energy scene: tool/shield/small weapon.
  Parameters: scope=tool_shield_weapon, duration=scene.
  Playstyles: Hybrid. Hook: scene flex.

CAST_3 | Major | 4p + 1phy + scene_use | zone (large) | close | scene | terrain-alteration, defense
  Effect: arena-size — large: wall/cover.
  Parameters: scope=large_structure, duration=scene, limit=1/scene.
  Playstyles: Tank, Support. Hook: scene arena.

RIDER_A | posture/reactive_defense | R2 (Block, Parry) | 0p passive
  Effect: solidified armor: -1 damage in posture.
  Parameters: reduction=1.
  Playstyles: Tank. Combo: energy_armor.

RIDER_B | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks with energy weapon +1; on_Crit energy-bleeding.
  Playstyles: Brawler. Combo: energy_strike.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves energy trail (1 damage to passing).
  Playstyles: Skirmisher, Area Denier. Combo: trail_energy.

CAPSTONE (authored: LIGHT ARCHITECT) | 4p + 1phy + scene_use | — | zone (complex) | close | scene | utility, defense
  Signal: "Light becomes form at my command."
  Viability: setup_dependent.
  Effect: complex construct for scene.
  Parameters: scope=complex, duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch. Effect: armor also reflects 1 damage to attackers.
  Combo: reflect_armor.

---

**Weapon Conjure** — Complement | Brawler, Hybrid | Human
Identity: Summon armament.

CAST_1 | Minor | 1p | — | self | — | scene | damage, utility
  Effect: draw weapon — +1 damage; magical property.
  Parameters: melee_damage=+1, duration=scene.
  Playstyles: Brawler. Hook: scene weapon.

CAST_2 | Major | 2p | — | self | — | scene | utility, stat-alteration
  Effect: versatile — weapon shifts between melee/ranged each turn.
  Parameters: melee_or_ranged=true, duration=scene.
  Playstyles: Hybrid. Hook: scene flex.

CAST_3 | Major | 3p + 1phy | self | — | scene | damage, status
  Effect: absolute — +2 damage; special trait (element, status).
  Parameters: melee=+2, special_trait=true, duration=scene.
  Playstyles: Brawler. Hook: scene buff.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 damage; on_Crit element/status.
  Playstyles: Brawler. Combo: conjured_strike.

RIDER_B | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: weapon blocks 1 attack per round.
  Parameters: blocks_per_round=1.
  Playstyles: Tank. Combo: weapon_block.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition + attack combined (charge).
  Playstyles: Skirmisher, Brawler. Combo: charge_strike.

CAPSTONE (authored: LEGENDARY ARMS) | 4p + 1phy + scene_use | — | self | — | scene | damage, meta
  Signal: "My weapon writes itself."
  Viability: offensive_swing.
  Effect: +3 damage all attacks; unique effect (narrator-defined).
  Parameters: damage=+3, duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: strike also applies +1 to next ally attack on same target.
  Combo: party_setup.

---

**Armor Conjure** — Complement | Tank | Human
Identity: Generate protective layer.

CAST_1 | Minor | 1p | — | self | — | scene | defense
  Effect: quick armor — -1 physical damage.
  Parameters: physical_reduction=1, duration=scene.
  Playstyles: Tank. Hook: spike defense.

CAST_2 | Major | 2p | — | self | — | scene | defense, stat-alteration
  Effect: sustained — -2 physical, -1 agi.
  Parameters: physical_reduction=2, agi=-1, duration=scene.
  Playstyles: Tank. Hook: scene defense.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, stat-alteration
  Effect: absolute — -3 physical, +2 defense, -2 agi.
  Parameters: physical_reduction=3, defense=+2, agi=-2.
  Playstyles: Tank. Hook: heavy defense.

RIDER_A | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: -2 physical in posture.
  Parameters: physical_reduction=2.
  Playstyles: Tank. Combo: continuous_armor.

RIDER_B | posture/anchor | R3 | 0p passive
  Effect: immune to forced movement while armored.
  Parameters: immune=true.
  Playstyles: Tank. Combo: immovable.

RIDER_C | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers take 1 damage.
  Parameters: counter=1.
  Playstyles: Tank. Combo: punisher.

CAPSTONE (authored: LIVING FORTRESS) | 4p + 2phy + scene_use | — | self | — | scene | defense, meta
  Signal: "I am the wall."
  Viability: setup_dependent.
  Effect: scene: -4 physical; immune bleeding; +1 defense rolls.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: branch. Effect: extends to ally in 5m: -2 physical.
  Combo: ally_protect.

---

**Surface Reshape** — Complement | Skirmisher, utility | Human
Identity: Transform solid surfaces briefly.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: sculpted step — create foothold; Reposition +2 distance.
  Parameters: reposition=+2m.
  Playstyles: Skirmisher. Hook: mobility setup.

CAST_2 | Major | 2p | — | zone (3m) | close | scene | terrain-alteration
  Effect: terrain reshape — 3m terrain changes type.
  Parameters: area=3m, type_change=true, duration=scene.
  Playstyles: Area Denier, utility. Hook: scene terrain.

CAST_3 | Major | 3p + 1phy | zone (large) | close | scene | terrain-alteration, defense
  Effect: complex shape — significant barrier/trap.
  Parameters: scope=barrier_or_trap, duration=scene.
  Playstyles: Area Denier. Hook: complex setup.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition creates difficult terrain behind 1r.
  Playstyles: Skirmisher. Combo: trail_terrain.

RIDER_B | posture/anchor | R3 | 0p passive
  Effect: immune to Disrupt on reshaped ground.
  Parameters: disrupt_immune=true_on_reshaped.
  Playstyles: Tank. Combo: terrain_anchor.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks from sculpted +1 cover-ignore.
  Playstyles: Brawler. Combo: cover_break.

CAPSTONE (authored: GROUND SHAPER) | 4p + 1phy + scene_use | — | zone (massive) | medium | scene | terrain-alteration, meta
  Signal: "The earth obeys."
  Viability: setup_dependent.
  Effect: massive reshape (entire battlefield section).
  Parameters: scope=battlefield_section, duration=scene, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: chaining on RIDER_A) | 1p
  Shift: branch. Effect: trail also damages enemies 1r (1 damage).
  Combo: trail_damage.

---

**Disintegration** — Primary | Eradicator; rare | Human (rare)
Identity: Break molecular bonds.

CAST_1 | Major | 3p + 1phy | enemy_single | far | instant | damage, status
  Effect: rending ray — ranged: 5 damage + exposed; armor -1.
  Parameters: damage=5, status=exposed, armor_decay=-1.
  Playstyles: Eradicator. Hook: spike damage.

CAST_2 | Major | 4p + 1phy + scene_use | enemy_single | medium | instant | damage, status
  Effect: collapse — save will or exposed + 5 damage.
  Parameters: save_tn=14, status=exposed, damage=5, limit=1/scene.
  Playstyles: Eradicator. Hook: heavy spike.

CAST_3 | Major | 5p + 2phy + scene_use | enemy_single | medium | instant | damage, meta
  Effect: obliteration — save will or die-level reduction.
  Parameters: save_tn=15, effect_on_fail=phy_minus_4, limit=1/scene.
  Playstyles: Eradicator. Hook: scene-defining.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks ignore armor 1 step; +1 damage.
  Playstyles: Brawler, Eradicator. Combo: armor_break.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers take 2 damage (entropic reaction).
  Parameters: counter=2.
  Playstyles: Tank. Combo: heavy_punisher.

RIDER_C | strike | restriction: Finisher only | 1p
  Effect: on_Full Finisher auto-applies exposed.
  Playstyles: Assassin, Eradicator. Combo: finisher_exposed.

CAPSTONE (authored: ABSOLUTE ZERO) | 6p + 2phy + scene_use | — | enemy_single | medium | instant | damage, meta
  Signal: "I unmake what should not be."
  Viability: offensive_swing.
  Effect: target save will (TN 16) or removed from combat (narrative).
  Parameters: save_tn=16, removal=true, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: ignore armor 2 steps; +2 damage.
  Combo: null.


## Sub-category 4.13 — Radiant

---

**Light Projection** — Primary | Artillery, Support | Human
Identity: Generate and direct light.

CAST_1 | Minor | 1p | — | enemy_single | close | instant | damage, status
  Effect: flash — 1 damage + -1 attack rolls on target 1r.
  Parameters: damage=1, penalty=-1, duration=1r.
  Playstyles: Controller. Hook: spike debuff.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage
  Effect: radiant lance — 3 damage + blind on Crit (target -2 attacks 1r).
  Parameters: damage=3, crit_blind=-2_attacks_1r.
  Playstyles: Artillery. Hook: ranged spike.

CAST_3 | Major | 3p + 1phy | zone (5m cone) | medium | 1 round | damage, status
  Effect: solar flare — 5m cone: 2 damage + -1 attacks.
  Parameters: area=5m_cone, damage=2_all, penalty=-1, duration=1r.
  Playstyles: Area Denier, Artillery. Hook: area debuff.

RIDER_A | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged +1 damage; on_Crit target -1 attacks 1r.
  Playstyles: Artillery. Combo: light_strike.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 to attack rolls (illumination).
  Parameters: range=5m, attack=+1.
  Playstyles: Support. Combo: party_buff.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: illumination breaks hidden flag in 10m.
  Parameters: range=10m, hidden_break=true.
  Playstyles: Investigator. Combo: counter_stealth.

CAPSTONE (authored: SUN'S GAZE) | 5p + 1phy + scene_use | — | all_visible | medium | 2 rounds | damage, status
  Signal: "I am the light that judges."
  Viability: offensive_swing.
  Effect: visible enemies: 3 damage + exposed.
  Parameters: scope=all_visible, damage=3, status=exposed, limit=1/scene.
  Playstyles: Artillery.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also reveals hidden enemies in 10m.
  Combo: null.

---

**Darkness Projection** — Primary | Controller, Area Denier | Human, Eldritch (rare)
Identity: Create zones of darkness/void light.

CAST_1 | Minor | 1p | — | zone (3m) | close | scene | terrain-alteration, status
  Effect: dim — 3m: enemies -1 attack rolls (obscured).
  Parameters: area=3m, attack_penalty=-1, duration=scene.
  Playstyles: Area Denier. Hook: small zone debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | terrain-alteration
  Effect: smothering dark — 5m: hidden flag for self; enemies -2 Assess.
  Parameters: area=5m, self_hidden=true, assess_penalty=-2.
  Playstyles: Assassin, Area Denier. Hook: stealth zone.

CAST_3 | Major | 3p + 1men | zone (10m) | medium | scene | terrain-alteration, control
  Effect: total darkness — 10m: no vision; save will or shaken on entry.
  Parameters: area=10m, no_vision=true, save_tn=12, status_on_entry=shaken_1r.
  Playstyles: Controller. Hook: heavy zone.

RIDER_A | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal in dark auto-Full.
  Playstyles: Assassin. Combo: stealth_king.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: see through own darkness; detect in 10m.
  Parameters: self_see_dark=true, range=10m.
  Playstyles: Assassin. Combo: dark_vision.

RIDER_C | strike | restriction: Quick, ranged | 1p
  Effect: on_Full attacks from own darkness +1; target exposed on Crit.
  Playstyles: Assassin. Combo: dark_strike.

CAPSTONE (authored: NIGHT OMEN) | 5p + 1men + scene_use | — | zone (large) | medium | scene | terrain-alteration, meta
  Signal: "I bring the night that devours."
  Viability: setup_dependent.
  Effect: massive darkness field; scene.
  Parameters: area=large, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce. Effect: Conceal also applies to allies in 5m.
  Combo: party_stealth.

---

**Invisibility** — Complement | Assassin, Trickster | Human
Identity: Cease being seen.

CAST_1 | Minor | 1p | — | self | — | 1 round | status
  Effect: quick vanish — hidden flag 1r.
  Parameters: flag=hidden, duration=1r.
  Playstyles: Assassin. Hook: spike stealth.

CAST_2 | Major | 2p | — | self | — | scene | status, stat-alteration
  Effect: sustained — hidden flag auto; +2 Conceal; -2 enemy Assess vs you.
  Parameters: flag=hidden_auto, conceal=+2, enemy_assess=-2, duration=scene.
  Playstyles: Assassin, Trickster. Hook: scene stealth.

CAST_3 | Major | 3p + 1phy | self | — | scene | status, meta
  Effect: absolute — effectively invisible; attacks auto-Full (first strike).
  Parameters: invisible_absolute=true, first_attack_auto_full=true, duration=scene.
  Playstyles: Assassin. Hook: scene commit.

RIDER_A | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal auto-Full; hidden +1r.
  Playstyles: Assassin. Combo: stealth_king.

RIDER_B | strike | restriction: Quick attacks only | 1p
  Effect: on_Full attacks from invisible +1 damage; on_Crit target exposed + hidden breaks.
  Playstyles: Assassin. Combo: assassin_strike.

RIDER_C | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: -1 damage from attacks while hidden.
  Parameters: reduction=1, conditional=hidden.
  Playstyles: Skirmisher. Combo: invisible_defense.

CAPSTONE (authored: GHOST) | 5p + 1phy + scene_use | — | self | — | scene | status, meta
  Signal: "I walk unseen."
  Viability: setup_dependent.
  Effect: scene: hidden persistent; attacks from hidden auto-Crit first strike.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: hidden +2r (was +1r).
  Combo: null.

---

**Blinding Flash** — Complement | Controller, Support (counter) | Human
Identity: Instant bright burst.

CAST_1 | Minor | 1p | — | enemy_single | close | 1 round | status
  Effect: quick blind — target -2 attack rolls 1r.
  Parameters: attack_penalty=-2, duration=1r.
  Playstyles: Controller. Hook: spike debuff.

CAST_2 | Major | 2p | — | zone (3m) | close | 1 round | status
  Effect: area flash — 3m: save per or -2 attack rolls 1r.
  Parameters: area=3m, save_tn=12, penalty=-2, duration=1r.
  Playstyles: Controller. Hook: area debuff.

CAST_3 | Major | 3p + 1men | zone (5m) | close | 2 rounds | status, control
  Effect: permanent afterimage — 5m: save per or -1 attacks 2r + shaken.
  Parameters: area=5m, save_tn=12, penalty=-1, status=shaken.
  Playstyles: Controller. Hook: heavy area.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Crit blind 1r (-1 next attack).
  Playstyles: Controller, Assassin. Combo: blind_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Dodge) | 0p passive
  Effect: melee attackers -1 next attack (blind counter).
  Parameters: penalty=-1.
  Playstyles: Tank. Combo: defensive_blind.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect enemy using stealth/illusion in 5m.
  Parameters: range=5m.
  Playstyles: Investigator. Combo: anti-illusion.

CAPSTONE (authored: SUN BOMB) | 4p + 1phy + scene_use | — | zone (10m) | medium | 2 rounds | status, control
  Signal: "I shatter sight."
  Viability: offensive_swing.
  Effect: 10m: save or blind 2r (-2 attacks).
  Parameters: area=10m, save_tn=13, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Crit blind -2 (was -1).
  Combo: null.

---

**Illumination** — Complement | Support, Controller | Human
Identity: Long-term light source.

CAST_1 | Minor | 1p | — | zone (5m) | close | scene | utility
  Effect: bright torch — 5m lit area; hidden broken in zone.
  Parameters: area=5m, hidden_break=true, duration=scene.
  Playstyles: Support. Hook: anti-stealth utility.

CAST_2 | Major | 2p | — | zone (10m) | medium | scene | utility, support
  Effect: sustained — 10m lit; allies +1 perception.
  Parameters: area=10m, ally_perception=+1, duration=scene.
  Playstyles: Support. Hook: scene buff.

CAST_3 | Major | 3p + 1men | self | — | scene | utility, meta
  Effect: celestial beacon — you project; +2 Assess all visible.
  Parameters: assess_bonus=+2, duration=scene.
  Playstyles: Support, Investigator. Hook: scene support.

RIDER_A | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 Assess.
  Parameters: range=5m, assess=+1.
  Playstyles: Support. Combo: party_buff.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect hidden in 10m via illumination.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: counter_stealth.

RIDER_C | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess +1 in lit area.
  Playstyles: Investigator. Combo: assess_amplify.

CAPSTONE (authored: NORTH STAR) | 4p + 1men + scene_use | — | all_visible | medium | scene | meta, support
  Signal: "I am the light they cannot escape."
  Viability: setup_dependent.
  Effect: scene: no hidden flag possible within sight; allies +1 all rolls.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support, Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: aura also grants +1 defense.
  Combo: dual_buff.

---

**Shadow Construct** — Complement | Controller, Support | Human, Eldritch (rare)
Identity: Create shapes from darkness.

CAST_1 | Minor | 1p | — | zone (3m) | close | scene | terrain-alteration
  Effect: small shape — 3m: dim zone.
  Parameters: area=3m, obscure=true, duration=scene.
  Playstyles: Area Denier. Hook: small zone.

CAST_2 | Major | 2p | — | zone (5m structure) | close | scene | terrain-alteration, defense
  Effect: construct — 5m barrier; provides cover.
  Parameters: area=5m, cover_provided=true, duration=scene.
  Playstyles: Support. Hook: scene cover.

CAST_3 | Major | 3p + 1men | zone (large) | medium | scene | terrain-alteration, meta
  Effect: complex — significant shadow construct (scene).
  Parameters: scope=significant, duration=scene.
  Playstyles: Controller. Hook: scene dominance.

RIDER_A | posture/reactive_defense | R2 (Block, Dodge) | 0p passive
  Effect: shadow cloak: -1 ranged damage.
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher, Tank. Combo: ranged_defense.

RIDER_B | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal via shadow +2.
  Playstyles: Assassin. Combo: shadow_stealth.

RIDER_C | strike | restriction: Quick attacks only | 1p
  Effect: on_Full Quick from shadow +1 damage.
  Playstyles: Assassin. Combo: shadow_strike.

CAPSTONE (authored: NIGHTMARE ARCHITECT) | 5p + 1men + scene_use | — | zone (large) | medium | scene | terrain-alteration, meta
  Signal: "The dark remembers how to kill."
  Viability: setup_dependent.
  Effect: complex shadow construct attacks passersby (1 damage per round to enemies within).
  Parameters: scope=large, passive_damage=1, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 0p
  Shift: branch. Effect: shadow cloak also hidden flag in dark environments.
  Combo: environmental_stealth.

---

**Refraction Decoy** — Complement | Trickster, Skirmisher | Human
Identity: Create light doubles.

CAST_1 | Minor | 1p | — | self | — | 1 round | status, utility
  Effect: flash decoy — next attack vs you misses (attacks decoy).
  Parameters: auto_miss_next=true.
  Playstyles: Trickster, Skirmisher. Hook: spike defense.

CAST_2 | Major | 2p | — | self | — | scene | utility, defense
  Effect: sustained doubles — 2 decoys; enemies -2 Assess on you.
  Parameters: decoys=2, enemy_assess=-2, duration=scene.
  Playstyles: Trickster, Skirmisher. Hook: scene stealth.

CAST_3 | Major | 3p + 1men + scene_use | self | — | scene | utility, meta
  Effect: prismatic — 3 decoys; attacks 50% chance hit decoy; hidden.
  Parameters: decoys=3, auto_miss_chance=50%, hidden=true, duration=scene, limit=1/scene.
  Playstyles: Trickster. Hook: scene defense.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves decoy in position.
  Playstyles: Trickster, Skirmisher. Combo: misdirection.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from ranged (refraction deflects).
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher. Combo: ranged_defense.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2 (false info).
  Playstyles: Diplomat, Trickster. Combo: deception_parley.

CAPSTONE (authored: PRISM) | 5p + 1men + scene_use | — | self | — | scene | meta, defense
  Signal: "They will never know which is real."
  Viability: setup_dependent.
  Effect: scene: perpetual decoys; first attack each round auto-miss (hits decoy).
  Parameters: auto_miss_first=true, duration=scene, limit=1/scene.
  Playstyles: Trickster.

ENHANCED_RIDER (authored: chaining on RIDER_A) | 1p
  Shift: branch. Effect: decoy also taunts once (enemy attacks decoy instead of you).
  Combo: taunt_stealth.

---

## Sub-category 4.14 — Machinal

---

**Technopathy** — Primary | Controller, utility | Human
Identity: Communicate with and control technology.

CAST_1 | Minor | 1p | — | object (machine) | touch | instant | utility
  Effect: device query — one command sent to machine.
  Parameters: scope=simple_command.
  Playstyles: utility. Hook: tactical.

CAST_2 | Major | 2p | — | enemy_single (machine) | medium | 2 rounds | control
  Effect: override — save or machine obeys you 2r.
  Parameters: save_tn=12, duration=2r.
  Playstyles: Controller. Hook: tech control.

CAST_3 | Major | 3p + 1men + scene_use | zone (machines) | medium | scene | control
  Effect: network — all machines in 10m cooperate with you scene.
  Parameters: range=10m, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene dominance.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: detect machines in 20m; sense function.
  Parameters: range=20m.
  Playstyles: Investigator. Combo: tech_detect.

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess reveals machine state (damage, settings).
  Playstyles: Investigator. Combo: tech_intel.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on machines deal +2 damage.
  Playstyles: Brawler. Combo: anti-tech.

CAPSTONE (authored: MACHINE LORD) | 5p + 1men + scene_use | — | zone (all machines) | medium | scene | control, meta
  Signal: "The iron answers me."
  Viability: setup_dependent.
  Effect: scene: all visible machines obey (save TN 13).
  Parameters: scope=all_machines, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: branch. Effect: awareness also reveals weaknesses/exploits.
  Combo: tech_weakness_intel.

---

**Machine Empathy** — Complement | Support, utility | Human
Identity: Understand machines as thinking beings.

CAST_1 | Minor | 1p | — | object (machine) | touch | instant | information
  Effect: sense state — feel machine's condition.
  Parameters: info=machine_state.
  Playstyles: Investigator. Hook: intel.

CAST_2 | Major | 2p | — | object (machine) | touch | scene | utility, support
  Effect: attune — repair by touch; machine +1 effectiveness.
  Parameters: repair=minor, effectiveness=+1, duration=scene.
  Playstyles: Support, utility. Hook: scene boost.

CAST_3 | Major | 3p + 1men | object (machine) | touch | scene | information, meta
  Effect: deep-read — entire machine's history and creators.
  Parameters: info=complete_history, duration=scene.
  Playstyles: Investigator. Hook: narrative.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess reveals machine tactical info.
  Playstyles: Investigator. Combo: tech_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: sense hostile machines in 15m.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: anti-tech_awareness.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Negotiate with AI/sentient machines +2.
  Playstyles: Diplomat. Combo: ai_parley.

CAPSTONE (authored: METAL WHISPER) | 4p + 1men + scene_use | — | all_machines | medium | scene | meta, support
  Signal: "The machines know me as friend."
  Viability: setup_dependent.
  Effect: machines in 15m friendly or neutral; won't attack you.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support, Diplomat.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals how to disable machine.
  Combo: tech_sabotage_intel.

---

**EMP Pulse** — Primary | Area Denier, Controller | Human, Creature
Identity: Release electromagnetic pulse.

CAST_1 | Minor | 1p | — | enemy_single (machine) | close | instant | damage, status
  Effect: quick pulse — 2 damage vs machine; disable 1 Minor.
  Parameters: damage=2, minor_disable=1.
  Playstyles: Controller. Hook: anti-machine.

CAST_2 | Major | 2p | — | zone (3m) | close | 1 round | damage, control
  Effect: burst — 3m: 2 damage to machines; -2 their attacks 1r.
  Parameters: area=3m, machine_damage=2, penalty=-2.
  Playstyles: Area Denier, Controller. Hook: area anti-tech.

CAST_3 | Major | 3p + 1men + scene_use | zone (10m) | medium | 1 round | damage, control
  Effect: total pulse — 10m: all tech disabled 1r + 2 damage.
  Parameters: area=10m, disable=1r, damage=2, limit=1/scene.
  Playstyles: Area Denier. Hook: scene tech denial.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks against machine +1 damage; +2 Crit.
  Playstyles: Brawler. Combo: anti-tech_strike.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect active tech in 15m.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: tech_detect.

RIDER_C | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: machine attackers in 5m take 1 EMP damage.
  Parameters: counter=1_vs_machines.
  Playstyles: Tank. Combo: anti-machine_defense.

CAPSTONE (authored: TECH KILLER) | 5p + 1men + scene_use | — | zone (20m) | medium | scene | control, meta
  Signal: "Let their machines die."
  Viability: offensive_swing.
  Effect: 20m: all machines disabled for scene.
  Parameters: area=20m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: anti-machine strikes +2 damage (was +1).
  Combo: null.

---

**Signal Interception** — Complement | Support, Investigator | Human
Identity: Monitor communications.

CAST_1 | Minor | 1p | — | zone (signals) | — | instant | information
  Effect: quick scan — intercept one signal.
  Parameters: scope=1_signal.
  Playstyles: Investigator. Hook: intel.

CAST_2 | Major | 2p | — | zone (wide) | far | scene | information
  Effect: sustained — monitor all signals in scene.
  Parameters: scope=all_signals, duration=scene.
  Playstyles: Investigator, Support. Hook: scene intel.

CAST_3 | Major | 3p + 1men + scene_use | all_visible | medium | scene | information, control
  Effect: injection — intercept + inject false signals.
  Parameters: inject=true, duration=scene, limit=1/scene.
  Playstyles: Controller, Trickster. Hook: scene info-ops.

RIDER_A | assess | restriction: Brief or Full Assess | 1p
  Effect: on_Full Assess via signals reveals target comms.
  Playstyles: Investigator. Combo: comms_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect active comms in 30m; decode.
  Parameters: range=30m.
  Playstyles: Investigator. Combo: wide_awareness.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Parley using intercepted info +2.
  Playstyles: Diplomat. Combo: informed_negotiation.

CAPSTONE (authored: ALL-HEARING) | 4p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "I hear what they say in private."
  Viability: setup_dependent.
  Effect: scene: all comms in 60m monitored + decoded.
  Parameters: range=60m, duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Assess also reveals communication partners.
  Combo: network_intel.

---

**Camera Possession** — Complement | Investigator, utility | Human
Identity: See through electronic eyes.

CAST_1 | Minor | 1p | — | self (via camera) | far | instant | information
  Effect: brief view — see through one camera instantly.
  Parameters: scope=1_camera.
  Playstyles: Investigator. Hook: tactical scout.

CAST_2 | Major | 2p | — | self | — | scene | information
  Effect: sustained — switch between cameras scene.
  Parameters: camera_switching=true, duration=scene.
  Playstyles: Investigator, Support. Hook: scene scout.

CAST_3 | Major | 3p + 1men + scene_use | self | — | scene | information, meta
  Effect: network omniscient — all cameras in 50m accessible simultaneously.
  Parameters: range=50m, duration=scene, limit=1/scene.
  Playstyles: Investigator. Hook: scene dominance.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess via camera reveals target position/state.
  Playstyles: Investigator. Combo: remote_intel.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: aware of cameras in 30m.
  Parameters: range=30m.
  Playstyles: Investigator. Combo: camera_awareness.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2 via surveillance intel.
  Playstyles: Diplomat. Combo: blackmail_parley.

CAPSTONE (authored: OMNISCIENT) | 4p + 1men + scene_use | — | self | — | scene | information, meta
  Signal: "I see everything they see."
  Viability: setup_dependent.
  Effect: scene: all cameras functional; no angle hidden from you.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: camera Assess also reveals sound recording.
  Combo: audio_intel.

---

**Machine Animation** — Complement | Support, Controller | Human
Identity: Animate inert tech.

CAST_1 | Minor | 1p | — | object (small machine) | touch | 1 round | control
  Effect: brief animate — small machine acts 1r.
  Parameters: scope=small, duration=1r.
  Playstyles: Support. Hook: tactical.

CAST_2 | Major | 2p | — | object (medium) | medium | scene | control
  Effect: sustained — medium machine ally scene.
  Parameters: scope=medium, duration=scene.
  Playstyles: Support. Hook: scene ally.

CAST_3 | Major | 3p + 1men + scene_use | object (large) | medium | scene | control
  Effect: animate — large machine obeys scene.
  Parameters: scope=large, duration=scene, limit=1/scene.
  Playstyles: Support, Controller. Hook: scene dominance.

RIDER_A | assess | restriction: Brief Assess only | 1p
  Effect: on_Full animated machine gets +2 to next action.
  Playstyles: Support. Combo: machine_buff.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: animated machines in 5m +1 attacks.
  Parameters: range=5m, machine_attack=+1.
  Playstyles: Support. Combo: machine_support.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on targets of animated +1 damage.
  Playstyles: Brawler. Combo: coordinated_strike.

CAPSTONE (authored: IRON LEGION) | 5p + 2men + scene_use | — | zone (machines) | medium | scene | control, meta
  Signal: "Iron rises at my word."
  Viability: setup_dependent.
  Effect: scene: animate multiple machines (up to 3); act as unit.
  Parameters: machines=3, duration=scene, limit=1/scene.
  Playstyles: Support, Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch. Effect: aura also grants +1 damage.
  Combo: machine_damage_buff.

---

**Network Burst** — Primary | Area Denier, Controller | Human
Identity: Overload systems.

CAST_1 | Major | 2p | — | enemy_single | medium | 1 round | damage, status
  Effect: overload — save will or 2 mental damage + -2 attacks 1r.
  Parameters: save_tn=12, damage=2, penalty=-2.
  Playstyles: Controller. Hook: status debuff.

CAST_2 | Major | 3p + 1men | zone (5m) | medium | 2 rounds | damage, control
  Effect: mass burst — 5m: save or confused 2r.
  Parameters: area=5m, save_tn=13, status=confused_2r.
  Playstyles: Area Denier, Controller. Hook: area control.

CAST_3 | Major | 3p + 1men | self | — | scene | meta, support
  Effect: cognitive boost — +1 all rolls involving info.
  Parameters: info_bonus=+1, duration=scene.
  Playstyles: Support. Hook: scene utility.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks apply -1 attacks.
  Playstyles: Controller, Assassin. Combo: disruptive_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will saves.
  Parameters: range=5m.
  Playstyles: Controller. Combo: aura_will_break.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2.
  Playstyles: Diplomat. Combo: parley_burst.

CAPSTONE (authored: NETWORK COLLAPSE) | 5p + 1men + scene_use | — | zone (10m) | medium | scene | control
  Signal: "Their minds are a failing circuit."
  Viability: offensive_swing.
  Effect: 10m: save or confused scene.
  Parameters: area=10m, save_tn=14, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: branch. Effect: aura also affects machines (disable 1 Minor/r).
  Combo: dual_target.

---

## Sub-category 4.15 — Corrosive

---

**Decay Touch** — Primary | Brawler, Assassin (setup) | Human, Creature
Identity: Accelerate aging.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | damage, status
  Effect: decay — melee: 1 damage + -1 attacks 1r.
  Parameters: damage=1, penalty=-1.
  Playstyles: Controller. Hook: spike debuff.

CAST_2 | Major | 2p | — | enemy_single | touch | 2 rounds | damage, status
  Effect: rot — melee: 3 damage + bleeding 2r.
  Parameters: damage=3, status=bleeding_2r.
  Playstyles: Brawler. Hook: damage + DoT.

CAST_3 | Major | 3p + 1phy | enemy_single | touch | scene | damage, meta
  Effect: total decay — 4 damage + exposed + -1 attacks scene.
  Parameters: damage=4, status=exposed, penalty=-1.
  Playstyles: Brawler, Assassin. Hook: heavy debuff.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full +1 damage; on_Crit exposed.
  Playstyles: Brawler. Combo: decay_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage + armor -1 1r.
  Parameters: counter=1, armor_reduction=1r.
  Playstyles: Tank. Combo: decay_counter.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on decayed +1 damage.
  Playstyles: Assassin. Combo: decay_exploit.

CAPSTONE (authored: AGE OF DUST) | 5p + 1phy + scene_use | — | enemy_single | touch | scene | damage, meta
  Signal: "Their time runs out in my hands."
  Viability: offensive_swing.
  Effect: 5 damage + exposed scene + -2 all rolls.
  Parameters: damage=5, penalty=-2, duration=scene, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: strike damage +2 (was +1).
  Combo: null.

---

**Rust-maker** — Complement | Controller, utility | Human
Identity: Decay metal.

CAST_1 | Minor | 1p | — | object (metal) | touch | instant | control
  Effect: weaken — target's metal weapon/armor -1 damage/reduction 1 scene.
  Parameters: metal_degradation=-1.
  Playstyles: Controller. Hook: tactical debuff.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | control
  Effect: rust — armor -2 reduction; weapon -2 damage.
  Parameters: armor=-2, weapon=-2, duration=scene.
  Playstyles: Controller. Hook: heavy debuff.

CAST_3 | Major | 3p + 1phy | zone (metals) | close | scene | control, meta
  Effect: mass corrode — 5m: all metal degraded scene.
  Parameters: area=5m, metal_degradation=-2, duration=scene.
  Playstyles: Area Denier. Hook: scene anti-tech.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks bypass armor 1 step (rusted).
  Playstyles: Assassin. Combo: armor_bypass.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m with metal armor -1 reduction.
  Parameters: range=5m, penalty=-1.
  Playstyles: Controller. Combo: aura_armor_break.

RIDER_C | parley | restriction: Demand only | 1p
  Effect: on_Full Demand auto-Full vs armored enemies.
  Playstyles: Diplomat. Combo: armor_pressure.

CAPSTONE (authored: IRON ROTS) | 5p + 1phy + scene_use | — | all_visible | medium | scene | control, meta
  Signal: "Metal remembers it was rust."
  Viability: offensive_swing.
  Effect: visible metal armor destroyed; weapons -3 damage.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: bypass armor 2 steps.
  Combo: null.

---

**Rot** — Primary | Area Denier, Controller | Human, Creature
Identity: Decompose organic matter.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | damage, status
  Effect: rot zone — 3m: 1 damage to organic.
  Parameters: area=3m, damage=1_organic.
  Playstyles: Area Denier. Hook: small area.

CAST_2 | Major | 2p | — | enemy_single | medium | 2 rounds | damage, status
  Effect: rot flesh — 2 damage/r + bleeding 2r.
  Parameters: per_round=2, status=bleeding_2r.
  Playstyles: Controller. Hook: sustained DoT.

CAST_3 | Major | 3p + 1phy | zone (5m) | close | 3 rounds | damage, control
  Effect: mass rot — 5m: 2 damage/r to organics.
  Parameters: area=5m, per_round=2, duration=3r.
  Playstyles: Area Denier. Hook: area DoT.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full +1 damage to organic targets.
  Playstyles: Brawler. Combo: organic_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m at end of round: 1 rot damage.
  Parameters: range=5m, per_turn=1.
  Playstyles: Area Denier. Combo: aura_damage.

RIDER_C | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 rot damage.
  Parameters: counter=1.
  Playstyles: Tank. Combo: rot_counter.

CAPSTONE (authored: BLIGHT) | 5p + 1phy + scene_use | — | zone (10m) | medium | scene | damage, terrain-alteration
  Signal: "I am the end that eats all."
  Viability: offensive_swing.
  Effect: 10m: 2 rot/r organic; terrain contaminated scene.
  Parameters: area=10m, per_round=2, duration=scene, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also applies bleeding 1r.
  Combo: dual_DoT.

---

**Age Acceleration** — Complement | Controller, Assassin | Human
Identity: Age target.

CAST_1 | Minor | 1p + 1men | enemy_single | medium | 1 round | status
  Effect: brief — shaken + -1 attacks 1r.
  Parameters: status=shaken_1r, penalty=-1.
  Playstyles: Controller. Hook: spike debuff.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | damage, status
  Effect: sustained — 2 damage + -1 all rolls scene.
  Parameters: damage=2, penalty=-1, duration=scene.
  Playstyles: Controller, Assassin. Hook: scene debuff.

CAST_3 | Major | 3p + 1men + scene_use | enemy_single | medium | scene | damage, meta
  Effect: ancient — 4 damage + -2 all rolls + exposed scene.
  Parameters: damage=4, penalty=-2, status=exposed, limit=1/scene.
  Playstyles: Assassin. Hook: scene-defining.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks also -1 target attacks 1r.
  Playstyles: Controller. Combo: debuff_strike.

RIDER_B | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize +2 vs recently-aged.
  Playstyles: Diplomat. Combo: parley_break.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 will saves.
  Parameters: range=5m.
  Playstyles: Controller. Combo: aura_break.

CAPSTONE (authored: DECREPITUDE) | 5p + 1men + scene_use | — | enemy_single | medium | scene | control, meta
  Signal: "They feel every year at once."
  Viability: offensive_swing.
  Effect: target -2 all rolls + exposed scene.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Assassin.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 1p
  Shift: reinforce. Effect: Destabilize also halves pool.
  Combo: pool_pressure.

---

**Entropic Strike** — Primary | Brawler, Eradicator | Human, Creature
Identity: Attack that drains vitality/structure.

CAST_1 | Major | 2p | — | enemy_single | touch | 2 rounds | damage, status
  Effect: entropic blow — melee: 3 damage + -1 damage reduction 2r.
  Parameters: damage=3, armor_reduction=-1_2r.
  Playstyles: Brawler. Hook: anti-tank.

CAST_2 | Major | 3p + 1phy | enemy_single | touch | 3 rounds | damage, status
  Effect: entropy spread — 4 damage + bleeding 2r + exposed.
  Parameters: damage=4, status=bleeding_2r, bonus_status=exposed.
  Playstyles: Brawler. Hook: heavy status.

CAST_3 | Major | 4p + 1phy + scene_use | enemy_single | touch | scene | damage, meta
  Effect: decay strike — 5 damage + all target damage reduced -1 scene.
  Parameters: damage=5, target_damage_reduction=-1_scene, limit=1/scene.
  Playstyles: Eradicator. Hook: scene debuff.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee +1 damage; armor -1 1r.
  Playstyles: Brawler. Combo: armor_break_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage + armor -1 1r.
  Parameters: counter=1, armor_reduction=1r.
  Playstyles: Tank. Combo: defensive_entropy.

RIDER_C | strike | restriction: Finisher only | 1p
  Effect: on_Full Finisher auto-exposes.
  Playstyles: Assassin, Eradicator. Combo: finisher_exposed.

CAPSTONE (authored: ENTROPIC FURY) | 5p + 1phy + scene_use | — | enemy_single | touch | scene | damage, meta
  Signal: "Their structure is my rend."
  Viability: offensive_swing.
  Effect: 6 damage + armor destroyed + exposed scene.
  Parameters: damage=6, limit=1/scene.
  Playstyles: Brawler, Eradicator.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: strike damage +2; armor -2.
  Combo: null.

---

**Structural Erosion** — Complement | Controller, Area Denier | Human
Identity: Weaken structure integrity.

CAST_1 | Minor | 1p | — | object (structure) | touch | scene | utility
  Effect: weaken structure — target structure -2 durability scene.
  Parameters: durability=-2.
  Playstyles: utility. Hook: structural tactical.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | terrain-alteration
  Effect: area weaken — 5m structure: brittle; -1 cover.
  Parameters: area=5m, cover_reduction=-1.
  Playstyles: Area Denier. Hook: scene cover reduction.

CAST_3 | Major | 3p + 1phy + scene_use | zone (large) | medium | scene | terrain-alteration, meta
  Effect: collapse — major structure weakened; scene narrative potential.
  Parameters: scope=large, duration=scene, limit=1/scene.
  Playstyles: utility, Controller. Hook: scene narrative.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks from weakened terrain ignore 1 cover step.
  Playstyles: Brawler. Combo: cover_bypass.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect structural weaknesses in 10m.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: structural_intel.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition destroys 1 cover behind.
  Playstyles: Skirmisher. Combo: destructive_mobility.

CAPSTONE (authored: DEMOLITION) | 4p + 1phy + scene_use | — | zone (massive) | medium | scene | terrain-alteration, meta
  Signal: "Their walls do not hold."
  Viability: setup_dependent.
  Effect: significant structure collapse (narrator-adjudicated; major narrative).
  Parameters: scope=massive, duration=scene, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: branch. Effect: strike also deals +1 damage.
  Combo: cover_damage_strike.

---

**Energy Nullification** — Complement | Tank, Controller | Human (rare)
Identity: Disable energy effects.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | control
  Effect: dampen — target's next Power mode -2 effect.
  Parameters: next_power_effect=-2.
  Playstyles: Controller, Tank. Hook: spike counter.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | control
  Effect: null field — target's cast costs +1 pool scene.
  Parameters: cast_cost_penalty=+1, duration=scene.
  Playstyles: Controller. Hook: scene caster-counter.

CAST_3 | Major | 3p + 1men + scene_use | zone (5m) | close | scene | control, defense
  Effect: absolute — 5m: no Power modes function.
  Parameters: area=5m, powers_disabled=true, duration=scene, limit=1/scene.
  Playstyles: Controller, Tank. Hook: scene caster-lockdown.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks after target cast disrupt next cast.
  Playstyles: Controller. Combo: anti-caster_strike.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect active power effects in 15m.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: power_awareness.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from energy-based attacks.
  Parameters: energy_reduction=1.
  Playstyles: Tank. Combo: energy_armor.

CAPSTONE (authored: ANTI-MAGIC ZONE) | 5p + 1men + scene_use | — | zone (10m) | medium | scene | control, meta
  Signal: "Their power fails before me."
  Viability: setup_dependent.
  Effect: 10m: power costs +2 pool scene; some powers fail entirely.
  Parameters: area=10m, cost_penalty=+2, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_C) | 0p
  Shift: reinforce. Effect: energy reduction -2 (was -1).
  Combo: null.


# BROAD: KINETIC

## Sub-category 4.16 — Impact

---

**Force Strike** — Primary | Brawler, Area Denier | Human
Identity: Punch carrying enormous force.

CAST_1 | Major | 2p | — | enemy_single | close | instant | damage, movement
  Effect: thunderous blow — Heavy: 3 damage + push 2m.
  Parameters: damage=3, push=2m, requires=heavy.
  Playstyles: Brawler. Hook: damage + positioning.

CAST_2 | Major | 3p | — | enemy_single | medium | instant | damage, status
  Effect: force wave — ranged: 3 damage + exposed.
  Parameters: damage=3, status=exposed.
  Playstyles: Artillery, Brawler. Hook: ranged spike.

CAST_3 | Major | 3p + 1phy | zone (3m cone) | close | instant | damage, movement
  Effect: shockfront — 3m cone: 3 damage + push all 3m.
  Parameters: area=3m_cone, damage=3_all, push=3m_all.
  Playstyles: Area Denier, Brawler. Hook: area damage + push.

RIDER_A | strike | restriction: Heavy attacks only | 1p
  Effect: on_Full Heavy pushes target 2m; on_Crit target exposed + pushed 3m.
  Playstyles: Brawler. Combo: push_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 1 damage + pushed 1m.
  Parameters: counter=1, push=1m.
  Playstyles: Tank. Combo: punisher_push.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition impact pushes adjacent enemy 2m.
  Playstyles: Skirmisher. Combo: mobile_push.

CAPSTONE (authored: CRUSHING BLOW) | 5p + 1phy + scene_use | — | enemy_single | close | instant | damage, status
  Signal: "One hit, final."
  Viability: offensive_swing.
  Effect: Heavy: 6 damage + exposed + push 4m.
  Parameters: damage=6, status=exposed, push=4m, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: push distances +1m each.
  Combo: null.

---

**Shockwave Clap** — Complement | Area Denier, Controller | Human
Identity: Kinetic burst at close range.

CAST_1 | Minor | 1p | — | zone (3m) | close | instant | damage, status
  Effect: burst — 3m: 1 damage + push 1m.
  Parameters: area=3m, damage=1, push=1m.
  Playstyles: Area Denier. Hook: spike area.

CAST_2 | Major | 2p | — | zone (5m) | close | instant | damage, control
  Effect: blast — 5m: 2 damage + save agi or exposed.
  Parameters: area=5m, damage=2, save_tn=12, status_on_fail=exposed.
  Playstyles: Area Denier. Hook: area debuff.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | instant | damage, movement
  Effect: massive — 10m: 2 damage + push all 3m.
  Parameters: area=10m, damage=2_all, push=3m.
  Playstyles: Area Denier. Hook: big area control.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks push 1m; on_Crit push 2m + exposed.
  Playstyles: Controller. Combo: push_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers pushed 1m on hit.
  Parameters: push=1m.
  Playstyles: Tank. Combo: repulsor_counter.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt pushes target 2m.
  Playstyles: Area Denier, Controller. Combo: disrupt_push.

CAPSTONE (authored: THUNDER OUT) | 4p + 1phy + scene_use | — | zone (10m) | medium | instant | damage, movement
  Signal: "The world steps back when I strike."
  Viability: offensive_swing.
  Effect: 10m: 3 damage + knockback 5m + exposed.
  Parameters: area=10m, damage=3_all, knockback=5m, status=exposed, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Full push 2m, Crit push 4m.
  Combo: null.

---

**Crushing Grip** — Primary | Brawler | Human, Creature
Identity: Grapple with enormous force.

CAST_1 | Minor | 1p | — | enemy_single | touch | 1 round | damage
  Effect: quick grip — melee: 1 damage + grapple attempt +2.
  Parameters: damage=1, grapple_bonus=+2.
  Playstyles: Brawler. Hook: grapple setup.

CAST_2 | Major | 2p | — | enemy_single (grappled) | touch | 2 rounds | damage, status
  Effect: sustained crush — grapple: 2 damage/r + -1 target attacks.
  Parameters: per_round=2, penalty=-1, requires=grapple.
  Playstyles: Brawler. Hook: grapple-lock damage.

CAST_3 | Major | 3p + 1phy | enemy_single (grappled) | touch | instant | damage, status
  Effect: bone-crush — grapple: 5 damage + exposed + bleeding 2r.
  Parameters: damage=5, status=exposed_plus_bleeding_2r.
  Playstyles: Brawler. Hook: grapple spike.

RIDER_A | strike | restriction: grapple attacks | 1p
  Effect: on_Full +2 damage; on_Crit bleeding 2r.
  Playstyles: Brawler. Combo: grapple_crush.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: while grappling, immune to forced movement.
  Parameters: immune=true.
  Playstyles: Brawler, Tank. Combo: grapple_anchor.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition drags grappled target.
  Playstyles: Brawler. Combo: drag_strike.

CAPSTONE (authored: IRON HUG) | 5p + 1phy + scene_use | — | enemy_single (grappled) | touch | scene | damage, control
  Signal: "They cannot escape my grip."
  Viability: setup_dependent.
  Effect: scene: grappled target takes 2 damage/r; cannot escape.
  Parameters: per_round=2, escape_disabled=true, duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +3 (was +2); Crit bleeding 3r.
  Combo: null.

---

**Kinetic Charge Release** — Primary | Burst Caster, Brawler | Human
Identity: Store and unleash kinetic energy.

CAST_1 | Minor | 1p | — | self | — | 1 round | resource
  Effect: charge — store 1 kinetic; next Heavy +1 damage.
  Parameters: charge=1, next_heavy_bonus=+1.
  Playstyles: Burst. Hook: setup spike.

CAST_2 | Major | 2p | — | self | — | 2 rounds | resource, defense
  Effect: sustained charge — 2 charges over 2 rounds.
  Parameters: charges_per_round=1, duration=2r.
  Playstyles: Burst. Hook: medium buildup.

CAST_3 | Major | 3p + scene_use | — | enemy_single | close | instant | damage
  Effect: release — Heavy: 4 damage + 1 per stored charge.
  Parameters: damage=4_plus_charges, limit=1/scene.
  Playstyles: Burst. Hook: spike damage.

RIDER_A | strike | restriction: Heavy attacks | 1p
  Effect: on_Full Heavy +1 damage; on_Crit consume 1 charge for +2 damage.
  Playstyles: Brawler, Burst. Combo: charge_strike.

RIDER_B | posture/amplify | R3 | 0p passive
  Effect: own Crits build 1 charge.
  Parameters: crit_charge=1.
  Playstyles: Burst. Combo: crit_charge_build.

RIDER_C | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: successful Parry/Block builds 1 charge.
  Parameters: parry_charge=1.
  Playstyles: Tank. Combo: defensive_charge.

CAPSTONE (authored: KINETIC BOMB) | 5p + 2phy + scene_use | — | enemy_single | close | instant | damage, status
  Signal: "I save this rage for you."
  Viability: offensive_swing.
  Effect: release all stored: 2 damage per charge (capped at 10) + target exposed.
  Parameters: damage=2_per_charge_cap_10, status=exposed, limit=1/scene.
  Playstyles: Burst.

ENHANCED_RIDER (authored: chaining on RIDER_A) | 1p
  Shift: reinforce. Effect: consume charge on Full +1 damage (was only on Crit).
  Combo: null.

---

**Battering Ram** — Complement | Tank, Brawler | Human
Identity: Move through obstacles with force.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: charge setup — next Reposition + Heavy combines: +1 damage.
  Parameters: combined_reposition_heavy_bonus=+1.
  Playstyles: Brawler, Tank. Hook: charge setup.

CAST_2 | Major | 2p | — | enemy_single | close | instant | damage, status
  Effect: ram — Reposition + Heavy: 3 damage + push 2m.
  Parameters: damage=3, push=2m, requires=combined_actions.
  Playstyles: Brawler. Hook: charge attack.

CAST_3 | Major | 3p + 1phy | enemy_group (path) | medium | instant | damage, movement
  Effect: charge-line — Reposition 10m through enemies; 2 damage each.
  Parameters: range=10m, damage=2_per_target.
  Playstyles: Tank, Brawler. Hook: multi-target charge.

RIDER_A | strike | restriction: Heavy attacks (charge) | 1p
  Effect: on_Full charge attacks +1 damage + push 1m.
  Playstyles: Brawler. Combo: charge_push.

RIDER_B | posture/anchor | R3 | 0p passive
  Effect: while charged/charging, immune to forced movement.
  Parameters: immune=true.
  Playstyles: Tank. Combo: immovable_charger.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition destroys cover in path.
  Playstyles: Tank. Combo: destructive_mobility.

CAPSTONE (authored: JUGGERNAUT) | 5p + 2phy + scene_use | — | enemy_group (path) | medium | scene | damage, meta
  Signal: "Nothing in my path remains standing."
  Viability: offensive_swing.
  Effect: scene: Reposition destroys all cover; pass through enemies with 2 damage each.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: charge push 2m, Crit exposed.
  Combo: null.

---

**Sustained Crush** — Complement | Brawler (pressure) | Human, Creature
Identity: Continuous pressure.

CAST_1 | Minor | 1p | — | enemy_single (grappled) | touch | 1 round | damage
  Effect: maintain crush — grapple: 1 damage + -1 target attack 1r.
  Parameters: damage=1, penalty=-1.
  Playstyles: Brawler. Hook: sustained debuff.

CAST_2 | Major | 2p | — | enemy_single (grappled) | touch | 2 rounds | damage, status
  Effect: prolonged — grapple: 2 damage/r + bleeding 2r.
  Parameters: per_round=2, status=bleeding_2r.
  Playstyles: Brawler. Hook: sustained DoT.

CAST_3 | Major | 3p + 1phy | enemy_single (grappled) | touch | scene | damage, control
  Effect: total lockdown — grapple: 2 damage/r + target can't use Minor scene.
  Parameters: per_round=2, target_no_minor=true, duration=scene.
  Playstyles: Brawler, Controller. Hook: scene control.

RIDER_A | strike | restriction: grapple attacks | 1p
  Effect: on_Full grapple damage +1; on_Crit bleeding 1r.
  Playstyles: Brawler. Combo: grapple_damage.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: immune to forced movement while grappling.
  Parameters: immune=true.
  Playstyles: Brawler, Tank. Combo: grapple_anchor.

RIDER_C | posture/aura_enemy | R3 | 0p passive
  Effect: grappled target -1 defense.
  Parameters: target_defense=-1.
  Playstyles: Brawler, Assassin. Combo: grapple_vuln.

CAPSTONE (authored: PERPETUAL CRUSH) | 5p + 1phy + scene_use | — | enemy_single (grappled) | touch | scene | damage, control
  Signal: "Their bones ache in my grip."
  Viability: setup_dependent.
  Effect: scene: grappled target 3 damage/r + cannot act.
  Parameters: per_round=3, target_no_act=true, duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +2 (was +1), Crit bleeding 2r.
  Combo: null.

---

**Earth-Strike** — Primary | Area Denier, Brawler | Human
Identity: Punch ground, radiate kinetic.

CAST_1 | Minor | 1p | — | zone (3m) | close | instant | damage, status
  Effect: ground pound — 3m: 1 damage + -1 attack 1r.
  Parameters: area=3m, damage=1, penalty=-1.
  Playstyles: Area Denier, Brawler. Hook: spike area.

CAST_2 | Major | 2p | — | zone (5m) | close | 1 round | damage, control
  Effect: shockfront — 5m: 2 damage + save agi or exposed.
  Parameters: area=5m, damage=2, save_tn=12, status_on_fail=exposed.
  Playstyles: Area Denier. Hook: area debuff.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | 1 round | damage, movement
  Effect: seismic — 10m: 2 damage + push all 3m.
  Parameters: area=10m, damage=2, push=3m.
  Playstyles: Area Denier. Hook: big area control.

RIDER_A | strike | restriction: Heavy attacks | 1p
  Effect: on_Full Heavy also applies exposed in 2m radius.
  Playstyles: Area Denier, Brawler. Combo: aoe_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: attackers take 1 damage + exposed on Crit (shockwave).
  Parameters: counter=1, crit_exposed=true.
  Playstyles: Tank. Combo: shock_counter.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition creates difficult terrain 1r behind.
  Playstyles: Area Denier. Combo: trail_terrain.

CAPSTONE (authored: SEISMIC FIST) | 5p + 1phy + scene_use | — | zone (15m) | medium | instant | damage, movement
  Signal: "I make the earth tremble."
  Viability: offensive_swing.
  Effect: 15m: 3 damage + all knockback 3m + exposed.
  Parameters: area=15m, damage=3_all, knockback=3m, status=exposed, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: reinforce. Effect: AoE +1 damage to affected.
  Combo: null.

---

## Sub-category 4.17 — Velocity

---

**Super Speed** — Primary | Skirmisher, Hybrid, Brawler | Human
Identity: Sustained high movement; distinct from Super Speed (body) — kinetic control vs biological.

CAST_1 | Minor | 1p | — | self | — | 1 round | action-economy
  Effect: burst — extra Reposition this turn.
  Parameters: extra_reposition=1.
  Playstyles: Skirmisher. Hook: mobility.

CAST_2 | Major | 2p | — | self | — | scene | defense, stat-alteration
  Effect: scene speed — +1 agi, +1 defense.
  Parameters: agi=+1, defense=+1, duration=scene.
  Playstyles: Skirmisher, Hybrid. Hook: mobility buff.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, action-economy
  Effect: blur — enemies -2 attacks vs you; Quick chain cap 3.
  Parameters: enemy_attack=-2, quick_chain=3, duration=scene.
  Playstyles: Skirmisher. Hook: evasion+chain.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition passes through enemies; +1 next attack.
  Playstyles: Skirmisher. Combo: pass_and_strike.

RIDER_B | posture/reactive_defense | R3 | 0p passive
  Effect: -1 ranged damage.
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher. Combo: ranged_evasion.

RIDER_C | strike | restriction: Quick attacks | 1p
  Effect: on_Full Quick chains to 1; on_Crit 2.
  Playstyles: Skirmisher. Combo: chain_offense.

CAPSTONE (authored: VELOCITY MASTER) | 5p + 1phy + scene_use | — | self | — | scene | action-economy, meta
  Signal: "I outpace their reactions."
  Viability: offensive_swing.
  Effect: scene: 2 Major actions per round; always act first.
  Parameters: major_per_round=2, initiative_first=true, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Reposition +1 defense rest of round.
  Combo: evasive_offense.

---

**Burst Acceleration** — Complement | Assassin (mobility), Skirmisher | Human
Identity: Short bursts of extreme speed.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility, defense
  Effect: quick dash — +3m Reposition this turn.
  Parameters: reposition_delta=+3m.
  Playstyles: Skirmisher. Hook: emergency mobility.

CAST_2 | Major | 2p | — | self | — | 1 round | utility, stat-alteration
  Effect: sprint — +5m Reposition + free Assess.
  Parameters: reposition_delta=+5m, free_assess=true.
  Playstyles: Skirmisher, Investigator. Hook: mobility + intel.

CAST_3 | Major | 2p | — | self | — | 2 rounds | defense
  Effect: evade state — +2 defense rolls 2r.
  Parameters: defense=+2, duration=2r.
  Playstyles: Skirmisher. Hook: focused defense.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition +2m distance; +1 next attack.
  Playstyles: Skirmisher. Combo: burst_strike.

RIDER_B | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: while in Dodge, -1 melee damage.
  Parameters: melee_reduction=1, posture_req=dodge.
  Playstyles: Skirmisher. Combo: dodge_specialist.

RIDER_C | strike | restriction: Quick attacks | 1p
  Effect: on_Full Quick after Reposition +1 damage.
  Playstyles: Skirmisher, Assassin. Combo: charge_quick.

CAPSTONE (authored: BURST FORM) | 4p + 1phy + scene_use | — | self | — | scene | meta, defense
  Signal: "They cannot track me."
  Viability: setup_dependent.
  Effect: scene: +2 defense all; each Reposition +1 to next attack; Quick chain +1.
  Parameters: defense=+2, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: distance +3m, attack +2.
  Combo: null.

---

**Long Leap** — Complement | Skirmisher | Human
Identity: Cover great distance in jump.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: normal leap — Reposition +3m vertically or diagonal.
  Parameters: reposition=+3m.
  Playstyles: Skirmisher. Hook: mobility.

CAST_2 | Major | 2p | — | self | — | 1 round | utility, damage
  Effect: vault — 5m leap + attack at end: +1 damage.
  Parameters: range=5m, attack_bonus=+1.
  Playstyles: Skirmisher, Brawler. Hook: aerial charge.

CAST_3 | Major | 3p + 1phy | self | — | 1 round | damage, utility
  Effect: great leap — 10m + Heavy attack at end: +2 damage.
  Parameters: range=10m, heavy_bonus=+2.
  Playstyles: Brawler, Skirmisher. Hook: dive attack.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes vertical 3m.
  Playstyles: Skirmisher. Combo: terrain_mobility.

RIDER_B | strike | restriction: Heavy attacks (aerial) | 1p
  Effect: on_Full Heavy from height +1 damage; on_Crit exposed.
  Playstyles: Brawler. Combo: aerial_strike.

RIDER_C | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: -1 melee damage while airborne.
  Parameters: aerial_melee_reduction=1.
  Playstyles: Skirmisher. Combo: aerial_defense.

CAPSTONE (authored: SKYBOUND) | 4p + 1phy + scene_use | — | self | — | scene | utility, damage
  Signal: "The ground does not hold me."
  Viability: setup_dependent.
  Effect: scene: vertical movement free; Heavy attacks from height auto +2 damage.
  Parameters: vertical_free=true, heavy_bonus=+2, duration=scene, limit=1/scene.
  Playstyles: Skirmisher, Brawler.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 1p
  Shift: reinforce. Effect: damage +2, Crit bleeding 1r.
  Combo: null.

---

**Sustained Flight** — Complement | Artillery (setup), Skirmisher | Human
Identity: Extended aerial mobility.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: hover — lift from ground this turn.
  Parameters: hover=true, duration=1r.
  Playstyles: Skirmisher. Hook: tactical.

CAST_2 | Major | 2p | — | self | — | scene | utility, stat-alteration
  Effect: flight — vertical free; +1 ranged attacks scene.
  Parameters: vertical_free=true, ranged_bonus=+1, duration=scene.
  Playstyles: Artillery, Skirmisher. Hook: scene aerial.

CAST_3 | Major | 3p + 1phy | self | — | scene | meta, utility
  Effect: flight mastery — 3D combat; +2 defense from aerial; Quick chain cap 3.
  Parameters: defense_aerial=+2, quick_chain=3, duration=scene.
  Playstyles: Skirmisher. Hook: scene control.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition includes vertical 3m; ignore terrain.
  Playstyles: Skirmisher. Combo: free_mobility.

RIDER_B | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged from flight +1 damage.
  Playstyles: Artillery. Combo: aerial_ranged.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect movement in 20m while aerial.
  Parameters: range=20m.
  Playstyles: Support. Combo: battlefield_awareness.

CAPSTONE (authored: ETHEREAL WING) | 5p + 1phy + scene_use | — | self | — | scene | meta, utility
  Signal: "The sky is mine."
  Viability: offensive_swing.
  Effect: scene: aerial; +2 defense all; Heavy dive applies exposed.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Skirmisher, Artillery.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Reposition can carry ally.
  Combo: team_flight.

---

**Thrust Flight** — Primary | Artillery, Skirmisher | Human
Identity: Propel self as ranged attacker.

CAST_1 | Minor | 1p | — | enemy_single | close | instant | damage
  Effect: thrust charge — Reposition 5m + 1 damage.
  Parameters: reposition=5m, damage=1.
  Playstyles: Skirmisher. Hook: charge light.

CAST_2 | Major | 2p + 1phy | enemy_single | medium | instant | damage, status
  Effect: charge — Reposition 8m + Heavy: 3 damage + exposed.
  Parameters: reposition=8m, damage=3, status=exposed.
  Playstyles: Brawler, Skirmisher. Hook: aerial charge.

CAST_3 | Major | 3p + 1phy | enemy_single | medium | scene | damage, utility
  Effect: rocket form — scene: fly freely; +2 ranged damage.
  Parameters: ranged_damage=+2, duration=scene.
  Playstyles: Artillery. Hook: scene aerial buff.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition +3m vertical; +1 next attack.
  Playstyles: Skirmisher. Combo: mobile_strike.

RIDER_B | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged from thrust +1 damage.
  Playstyles: Artillery. Combo: aerial_ranged.

RIDER_C | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: -1 ranged damage (moving fast).
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher. Combo: evasive_flight.

CAPSTONE (authored: JETSTREAM) | 5p + 1phy + scene_use | — | self | — | scene | utility, damage
  Signal: "Speed becomes my weapon."
  Viability: offensive_swing.
  Effect: scene: flight; ranged +2 damage; enemies -2 attacks vs you.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Artillery, Skirmisher.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: vertical +5m, attack +2.
  Combo: null.

---

**Velocity Evasion** — Complement | Skirmisher, Trickster | Human
Identity: Dodge by speed alone.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: evade — next defense roll +2.
  Parameters: defense=+2, duration=next_defense.
  Playstyles: Skirmisher. Hook: spike defense.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: sustained — +1 all defense; first ranged attack auto-missed.
  Parameters: defense=+1, first_ranged_miss=true, duration=scene.
  Playstyles: Skirmisher. Hook: scene defense.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, meta
  Effect: phantom — +2 defense all; on Crit dodge, free counter Reposition.
  Parameters: defense=+2, crit_counter=true, duration=scene.
  Playstyles: Skirmisher. Hook: scene counter-dance.

RIDER_A | posture/reactive_defense | R1 (Dodge only) | 0p passive
  Effect: -1 damage from attacks; +1 Dodge rolls.
  Parameters: reduction=1, dodge=+1.
  Playstyles: Skirmisher. Combo: dodge_specialist.

RIDER_B | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition gives +2 next defense.
  Playstyles: Skirmisher. Combo: mobile_defense.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect incoming attacks; free Reposition once per scene when hit.
  Parameters: reposition_trigger=1.
  Playstyles: Skirmisher. Combo: defense_mobility.

CAPSTONE (authored: GHOST DANCE) | 5p + 1phy + scene_use | — | self | — | scene | defense, meta
  Signal: "They cannot touch what isn't there."
  Viability: setup_dependent.
  Effect: scene: first attack each round auto-missed.
  Parameters: first_miss_per_round=true, duration=scene, limit=1/scene.
  Playstyles: Skirmisher.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 0p
  Shift: reinforce. Effect: reduction -2 (was -1), Dodge +2 (was +1).
  Combo: null.

---

**Sprint Charge** — Primary | Brawler | Human
Identity: Headlong sprint into combat.

CAST_1 | Minor | 1p | — | self | — | 1 round | utility
  Effect: starting momentum — next charge +1 damage.
  Parameters: next_charge_bonus=+1.
  Playstyles: Brawler. Hook: setup spike.

CAST_2 | Major | 2p | — | enemy_single | medium | instant | damage, status
  Effect: charge — Reposition 8m + Heavy: 3 damage + exposed.
  Parameters: reposition=8m, damage=3, status=exposed.
  Playstyles: Brawler. Hook: charge.

CAST_3 | Major | 3p + 1phy | enemy_group (path) | medium | instant | damage, movement
  Effect: line charge — 10m through enemies; 2 damage each; exposed on path-end target.
  Parameters: range=10m, per_target=2, path_end_exposed=true.
  Playstyles: Brawler. Hook: multi-target.

RIDER_A | strike | restriction: Heavy attacks (charge) | 1p
  Effect: on_Full Heavy after Reposition +1 damage + push.
  Playstyles: Brawler. Combo: charge_push.

RIDER_B | posture/anchor | R2 (Block, Parry) | 0p passive
  Effect: immune to forced movement while charging.
  Parameters: immune=true.
  Playstyles: Tank, Brawler. Combo: immovable.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition through enemies (passes).
  Playstyles: Brawler. Combo: pass_strike.

CAPSTONE (authored: UNSTOPPABLE FORCE) | 5p + 2phy + scene_use | — | enemy_group (path) | medium | instant | damage, meta
  Signal: "Nothing slows me."
  Viability: offensive_swing.
  Effect: charge 15m through all; 3 damage each; exposed.
  Parameters: range=15m, per_target=3, status=exposed, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +2, push +1m.
  Combo: null.

---

## Sub-category 4.18 — Gravitic

---

**Gravity Crush** — Primary | Controller, Area Denier | Human, Eldritch (rare)
Identity: Increase gravity on target.

CAST_1 | Major | 2p | — | enemy_single | medium | 1 round | status, control
  Effect: weigh down — target -1 attack and -1 defense 1r.
  Parameters: penalty=-1_both, duration=1r.
  Playstyles: Controller. Hook: debuff.

CAST_2 | Major | 3p + 1men | enemy_single | medium | 2 rounds | damage, status
  Effect: crush — 2 damage + target cannot Reposition 2r.
  Parameters: damage=2, no_reposition=true, duration=2r.
  Playstyles: Controller. Hook: lockdown.

CAST_3 | Major | 4p + 1men + scene_use | zone (5m) | medium | scene | damage, terrain-alteration
  Effect: field — 5m: -1 movement and -1 damage per round.
  Parameters: area=5m, penalty=-1_movement_damage, duration=scene.
  Playstyles: Area Denier. Hook: scene zone.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt also exposed.
  Playstyles: Controller. Combo: disrupt_exposed.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Reposition distance.
  Parameters: range=5m, reposition=-1m.
  Playstyles: Controller, Tank. Combo: movement_restrict.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on gravity-crushed target +1 damage.
  Playstyles: Brawler. Combo: gravity_exploit.

CAPSTONE (authored: BLACK HOLE) | 5p + 1men + scene_use | — | zone (5m) | medium | scene | damage, meta
  Signal: "All bends toward me."
  Viability: offensive_swing.
  Effect: 5m: 2 damage per round; pull toward center 1m/r.
  Parameters: area=5m, per_round=2, pull=1m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Controller.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: Disrupt also -1 next attack.
  Combo: null.

---

**Anti-Gravity Lift** — Complement | Controller, Support | Human
Identity: Reduce/reverse gravity on target.

CAST_1 | Minor | 1p | — | object (small) | medium | scene | utility
  Effect: lift small — pick up object at distance.
  Parameters: scope=small, duration=scene.
  Playstyles: utility. Hook: tactical lift.

CAST_2 | Major | 2p | — | enemy_single | medium | 2 rounds | control
  Effect: levitate — target suspended; cannot attack 1r; -2 defense 2r.
  Parameters: suspended=1r, defense=-2_2r.
  Playstyles: Controller. Hook: lock + debuff.

CAST_3 | Major | 3p + 1men | ally_group | medium | scene | support, utility
  Effect: weightless — 3 allies in 5m: +2 Reposition distance scene.
  Parameters: allies=3, range=5m, reposition=+2m, duration=scene.
  Playstyles: Support. Hook: scene mobility buff.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition vertical +3m.
  Playstyles: Skirmisher. Combo: aerial_mobility.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +1 Reposition distance.
  Parameters: range=5m, reposition=+1m.
  Playstyles: Support. Combo: mobility_buff.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from melee (floating evasion).
  Parameters: melee_reduction=1.
  Playstyles: Skirmisher. Combo: aerial_defense.

CAPSTONE (authored: TRUE WEIGHTLESS) | 4p + 1men + scene_use | — | all_visible_allies | medium | scene | support, meta
  Signal: "Gravity forgets my people."
  Viability: setup_dependent.
  Effect: scene: all visible allies ignore gravity (+3m Reposition distance, vertical free).
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Reposition also allows ally carry.
  Combo: team_lift.

---

**Gravity Tether** — Complement | Controller | Human
Identity: Force between self and target.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | movement
  Effect: brief pull — pull target 2m toward you.
  Parameters: pull=2m.
  Playstyles: Controller. Hook: positioning.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 2 rounds | control, movement
  Effect: tethered — target follows you within 5m for 2r.
  Parameters: tether_range=5m, duration=2r.
  Playstyles: Controller. Hook: forced positioning.

CAST_3 | Major | 3p + 1men + scene_use | zone (5m) | medium | scene | control
  Effect: mass tether — 5m: enemies pulled toward you each round.
  Parameters: area=5m, pull_per_round=1m, duration=scene, limit=1/scene.
  Playstyles: Controller, Area Denier. Hook: scene pull.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt pulls target 2m toward you.
  Playstyles: Controller. Combo: pull_disrupt.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m can't Reposition away from you.
  Parameters: range=5m, retreat_blocked=true.
  Playstyles: Controller. Combo: sticky_aura.

RIDER_C | strike | restriction: melee attacks | 1p
  Effect: on_Full melee pulls target 1m closer.
  Playstyles: Brawler. Combo: pull_strike.

CAPSTONE (authored: BLACK HOLE WEAVE) | 5p + 1men + scene_use | — | enemy_group | medium | scene | control, movement
  Signal: "Distance does not save them."
  Viability: setup_dependent.
  Effect: scene: all enemies in 10m pulled toward you 2m/r.
  Parameters: area=10m, pull=2m, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also -1 attack rolls for retreating enemies.
  Combo: null.

---

**Radial Repel** — Primary | Area Denier, Tank | Human
Identity: Push outward from self.

CAST_1 | Minor | 1p | — | zone (3m) | close | instant | movement
  Effect: push — 3m: all enemies pushed 2m.
  Parameters: area=3m, push=2m.
  Playstyles: Area Denier. Hook: positioning.

CAST_2 | Major | 2p | — | zone (5m) | close | instant | damage, movement
  Effect: burst — 5m: 1 damage + push 3m.
  Parameters: area=5m, damage=1, push=3m.
  Playstyles: Area Denier. Hook: push + damage.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | instant | damage, control
  Effect: shockwave — 10m: 2 damage + save or exposed + knockback 4m.
  Parameters: area=10m, damage=2, save_tn=12, knockback=4m.
  Playstyles: Area Denier. Hook: big push.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt also pushes 2m.
  Playstyles: Controller. Combo: disrupt_push.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers pushed 1m.
  Parameters: push=1m.
  Playstyles: Tank. Combo: repulsor_defense.

RIDER_C | posture/anchor | R3 | 0p passive
  Effect: immune to forced movement.
  Parameters: immune=true.
  Playstyles: Tank. Combo: immovable.

CAPSTONE (authored: PULSE CORE) | 5p + 1phy + scene_use | — | zone (10m) | close | scene | control, movement
  Signal: "I push the world away."
  Viability: setup_dependent.
  Effect: scene: enemies in 10m repelled 1m at each round start.
  Parameters: area=10m, repel=1m, duration=scene, limit=1/scene.
  Playstyles: Area Denier, Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: push 3m (was 2m).
  Combo: null.

---

**Gravity Anchor** — Complement | Tank, Area Denier | Human
Identity: Self-anchor; increase personal gravity.

CAST_1 | Minor | 1p | — | self | — | scene | defense, stat-alteration
  Effect: anchor — immune to forced movement scene.
  Parameters: immune=true, duration=scene.
  Playstyles: Tank. Hook: scene anchor.

CAST_2 | Major | 2p | — | self | — | scene | defense
  Effect: rooted — +1 defense; enemies around you at -1 Reposition.
  Parameters: defense=+1, enemy_reposition=-1m, duration=scene.
  Playstyles: Tank, Controller. Hook: scene zone.

CAST_3 | Major | 3p + 1phy | self | — | scene | defense, control
  Effect: massive — +2 defense; enemies in 5m -1 attack.
  Parameters: defense=+2, enemy_attack=-1, duration=scene.
  Playstyles: Tank. Hook: scene powerhouse.

RIDER_A | posture/anchor | R3 | 0p passive
  Effect: immune to forced movement; +1 vs Disrupt.
  Parameters: immune=true, disrupt=+1.
  Playstyles: Tank. Combo: immovable.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Reposition distance.
  Parameters: range=5m, reposition=-1m.
  Playstyles: Tank. Combo: sticky_zone.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from push-based attacks.
  Parameters: push_reduction=1.
  Playstyles: Tank. Combo: anti-push.

CAPSTONE (authored: IMMOVABLE OBJECT) | 4p + 1phy + scene_use | — | self | — | scene | defense, meta
  Signal: "I cannot be moved."
  Viability: setup_dependent.
  Effect: scene: +3 defense; immune all forced movement; -2 all damage.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura range 10m (was 5m).
  Combo: null.

---

**Orbit Lock** — Complement | Controller, Area Denier | Human, Eldritch (rare)
Identity: Trap target in circular path.

CAST_1 | Minor | 1p | — | enemy_single | medium | 1 round | control
  Effect: brief circle — target can only Reposition in arc 1r.
  Parameters: arc_only=true, duration=1r.
  Playstyles: Controller. Hook: spike control.

CAST_2 | Major | 2p + 1men | enemy_single | medium | 2 rounds | control
  Effect: orbit trap — target locked in 5m orbit 2r.
  Parameters: orbit_range=5m, duration=2r.
  Playstyles: Controller. Hook: lock control.

CAST_3 | Major | 3p + 1men + scene_use | enemy_group (close) | medium | scene | control
  Effect: mass orbit — all in 5m locked orbit scene.
  Parameters: area=5m, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene lock.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt locks target's next Reposition direction.
  Playstyles: Controller. Combo: movement_restrict.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m cannot leave zone without will save (TN 11).
  Parameters: range=5m, save_tn=11.
  Playstyles: Controller, Tank. Combo: zone_lock.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks on orbit-locked +1 damage.
  Playstyles: Brawler. Combo: lock_exploit.

CAPSTONE (authored: BINDING ORBIT) | 5p + 1men + scene_use | — | enemy_single | medium | scene | control, meta
  Signal: "Their path is mine to set."
  Viability: setup_dependent.
  Effect: target locked in orbit scene; cannot approach you; -2 all rolls.
  Parameters: penalty=-2, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch. Effect: aura also pulls enemies 1m toward center each round.
  Combo: null.

---

**Mass Transfer** — Flex | Trickster, utility | Human
Identity: Shift perceived mass between objects/self.

CAST_1 | Minor | 1p | — | self | — | scene | stat-alteration
  Effect: weight shift — choose: +1 might or +1 agi for scene.
  Parameters: stat_swap=1_tier, duration=scene.
  Playstyles: Trickster. Hook: flex buff.

CAST_2 | Major | 2p | — | enemy_single | medium | scene | control
  Effect: mass drain — target -1 might; -1 damage scene.
  Parameters: target_might=-1, target_damage=-1, duration=scene.
  Playstyles: Controller. Hook: debuff.

CAST_3 | Major | 3p + 1men | object | medium | scene | utility, meta
  Effect: translocation — transfer mass between objects/self (narrator-adjudicated).
  Parameters: scope=significant, duration=scene.
  Playstyles: utility, Trickster. Hook: narrative.

RIDER_A | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition lighter (+2m); heavier (-1m).
  Playstyles: Trickster, Skirmisher. Combo: mass_mobility.

RIDER_B | posture/stat-alteration | R3 | 0p passive
  Effect: switch between +1 might / +1 agi once per round.
  Parameters: stat_swap=per_round.
  Playstyles: Trickster, Hybrid. Combo: flex_state.

RIDER_C | strike | restriction: all attack sub-types | 1p
  Effect: on_Full swap target's mass temporarily: -1 damage to them 1r.
  Playstyles: Trickster. Combo: debuff_strike.

CAPSTONE (authored: WEIGHT-MASTER) | 5p + 1men + scene_use | — | self + target | medium | scene | stat-alteration, meta
  Signal: "Mass is a choice."
  Viability: setup_dependent.
  Effect: scene: swap any stat with target; your stat +2, theirs -2.
  Parameters: stat_swap=+2_-2, duration=scene, limit=1/scene.
  Playstyles: Trickster.

ENHANCED_RIDER (authored: new_dimension on RIDER_B) | 0p
  Shift: branch. Effect: posture also grants +1 defense when lighter.
  Combo: dual_state.


## Sub-category 4.19 — Projective

---

**Telekinesis** — Flex | Controller, utility | Human
Identity: Move objects with mind.

CAST_1 | Minor | 1p | — | object (small) | medium | instant | utility, control
  Effect: pull/push small — move small object 5m.
  Parameters: scope=small, distance=5m.
  Playstyles: Controller, utility. Hook: tactical.

CAST_2 | Major | 2p | — | enemy_single | medium | instant | damage, movement
  Effect: TK strike — ranged: 2 damage + push 3m.
  Parameters: damage=2, push=3m.
  Playstyles: Controller. Hook: push spike.

CAST_3 | Major | 3p + 1men | zone (5m) | medium | scene | control, utility
  Effect: telekinetic zone — 5m: objects move; cover created or destroyed.
  Parameters: area=5m, duration=scene.
  Playstyles: Controller, Area Denier. Hook: scene zone.

RIDER_A | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged also pushes 1m.
  Playstyles: Controller. Combo: ranged_push.

RIDER_B | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt pushes 2m + exposed.
  Playstyles: Controller. Combo: disrupt_push.

RIDER_C | posture/reactive_defense | R3 | 0p passive
  Effect: -1 ranged damage (objects deflected).
  Parameters: ranged_reduction=1.
  Playstyles: Skirmisher. Combo: deflection.

CAPSTONE (authored: TK MASTERY) | 5p + 1men + scene_use | — | zone (10m) | medium | scene | meta, utility
  Signal: "All things answer me."
  Viability: setup_dependent.
  Effect: scene: move any object in 10m as free action; ranged +2 damage.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Controller, Artillery.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: push 2m (was 1m).
  Combo: null.

---

**Kinetic Throw** — Primary | Artillery, Controller | Human
Identity: Hurl objects with force.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | damage
  Effect: quick throw — improvised object: 2 damage.
  Parameters: damage=2.
  Playstyles: Artillery. Hook: ranged attack.

CAST_2 | Major | 2p | — | enemy_single | far | instant | damage, status
  Effect: heavy throw — thrown Heavy: 3 damage + bleeding on Crit.
  Parameters: damage=3, status_on_crit=bleeding_1r.
  Playstyles: Artillery, Brawler. Hook: ranged spike.

CAST_3 | Major | 3p + 1phy | enemy_group (line) | far | instant | damage, movement
  Effect: devastating throw — large object: 3 damage to line + push 3m.
  Parameters: damage=3_all_in_line, push=3m.
  Playstyles: Artillery. Hook: multi-target line.

RIDER_A | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged attacks with thrown item +1 damage.
  Playstyles: Artillery. Combo: thrown_strike.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: ranged attackers in 5m take 1 reflected damage.
  Parameters: counter=1.
  Playstyles: Tank. Combo: reflect_defense.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt via thrown object also -1 target next attack.
  Playstyles: Controller. Combo: ranged_disrupt.

CAPSTONE (authored: PROJECTILE STORM) | 5p + 1phy + scene_use | — | enemy_group (all_visible) | far | instant | damage
  Signal: "Every object in my hand is a weapon."
  Viability: offensive_swing.
  Effect: all visible enemies: 3 damage + bleeding on Crit.
  Parameters: scope=all_visible, damage=3_all, limit=1/scene.
  Playstyles: Artillery.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +2 (was +1); Crit bleeding 2r.
  Combo: null.

---

**Force Bolt** — Primary | Artillery | Human
Identity: Concussive blast of pure force.

CAST_1 | Major | 2p | — | enemy_single | far | instant | damage, movement
  Effect: concussive — 3 damage + push 1m.
  Parameters: damage=3, push=1m.
  Playstyles: Artillery. Hook: ranged spike.

CAST_2 | Major | 3p | — | zone (3m) | medium | instant | damage, status
  Effect: burst — 3m: 2 damage + exposed on Crit.
  Parameters: area=3m, damage=2_all, status_on_crit=exposed.
  Playstyles: Area Denier, Artillery. Hook: area attack.

CAST_3 | Major | 3p + 1phy | enemy_single | medium | instant | damage, status, movement
  Effect: heavy bolt — 4 damage + exposed + push 3m.
  Parameters: damage=4, status=exposed, push=3m.
  Playstyles: Artillery. Hook: spike all-in-one.

RIDER_A | strike | restriction: ranged attacks only | 1p
  Effect: on_Full ranged +1 damage; on_Crit push 2m.
  Playstyles: Artillery. Combo: push_ranged.

RIDER_B | posture/reactive_offense | R2 (Parry, Dodge) | 0p passive
  Effect: ranged attackers take 1 force damage.
  Parameters: counter=1.
  Playstyles: Tank. Combo: defensive_force.

RIDER_C | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt pushes 2m + exposed.
  Playstyles: Controller. Combo: ranged_disrupt.

CAPSTONE (authored: ANNIHILATOR) | 5p + 1phy + scene_use | — | zone (10m) | medium | instant | damage, status
  Signal: "I strike from nowhere."
  Viability: offensive_swing.
  Effect: 10m: 3 damage + exposed all.
  Parameters: area=10m, damage=3_all, status=exposed_all, limit=1/scene.
  Playstyles: Artillery.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +2 (was +1); push 3m on Crit.
  Combo: null.

---

**Force Barrier** — Complement | Tank, Support | Human
Identity: Project wall of force.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: quick barrier — +2 defense next incoming.
  Parameters: defense=+2, duration=next_incoming.
  Playstyles: Tank. Hook: spike defense.

CAST_2 | Major | 2p | — | zone (3m line) | close | 2 rounds | defense, terrain-alteration
  Effect: wall — 3m barrier line 2r; cover.
  Parameters: line=3m, duration=2r.
  Playstyles: Tank, Support. Hook: tactical cover.

CAST_3 | Major | 3p + 1phy | zone (5m dome) | close | scene | defense, terrain-alteration
  Effect: dome — 5m dome; -2 all damage within.
  Parameters: dome=5m, reduction=-2, duration=scene.
  Playstyles: Tank, Support. Hook: scene protection.

RIDER_A | posture/reactive_defense | R3 | 0p passive
  Effect: -1 damage from ranged.
  Parameters: ranged_reduction=1.
  Playstyles: Tank. Combo: ranged_armor.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m -1 damage from ranged.
  Parameters: range=5m, ranged_reduction=1.
  Playstyles: Support. Combo: party_shield.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition leaves barrier 1r.
  Playstyles: Skirmisher, Tank. Combo: trail_shield.

CAPSTONE (authored: AEGIS) | 5p + 1phy + scene_use | — | zone (10m dome) | close | scene | defense, meta
  Signal: "We stand, unbreaking."
  Viability: setup_dependent.
  Effect: scene: 10m dome; all allies within -3 damage.
  Parameters: area=10m, reduction=-3, duration=scene, limit=1/scene.
  Playstyles: Tank, Support.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: reduction -2 (was -1).
  Combo: null.

---

**Force Blade** — Primary | Brawler, Skirmisher | Human
Identity: Solid blade of kinetic force.

CAST_1 | Minor | 1p | — | self | — | scene | damage, stat-alteration
  Effect: quick blade — +1 melee damage scene.
  Parameters: melee=+1, duration=scene.
  Playstyles: Brawler. Hook: scene weapon.

CAST_2 | Major | 2p | — | enemy_single | close | instant | damage, status
  Effect: swung blade — Heavy: 3 damage + bleeding 1r.
  Parameters: damage=3, status=bleeding_1r.
  Playstyles: Brawler. Hook: melee spike.

CAST_3 | Major | 2p | — | self | — | scene | damage, defense
  Effect: sustained — scene: +2 melee; Parry bonus +1.
  Parameters: melee=+2, parry=+1, duration=scene.
  Playstyles: Brawler, Tank. Hook: scene dual.

RIDER_A | strike | restriction: melee attacks | 1p
  Effect: on_Full melee +1 damage; on_Crit bleeding 2r.
  Playstyles: Brawler. Combo: blade_strike.

RIDER_B | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: Parry bonus +1.
  Parameters: parry=+1.
  Playstyles: Tank, Brawler. Combo: blade_defense.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition + attack combined (+1 damage).
  Playstyles: Skirmisher. Combo: charge_strike.

CAPSTONE (authored: LEGENDARY BLADE) | 5p + 1phy + scene_use | — | self | — | scene | damage, meta
  Signal: "I carry the edge."
  Viability: offensive_swing.
  Effect: scene: +3 melee damage; Crits apply exposed.
  Parameters: melee=+3, crit_exposed=true, duration=scene, limit=1/scene.
  Playstyles: Brawler.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: damage +2; Crit bleeding 3r.
  Combo: null.

---

**Ranged Disarm** — Complement | Controller | Human
Identity: Strip weapons from enemy.

CAST_1 | Minor | 1p | — | enemy_single | medium | instant | control
  Effect: disarm — target save agi or loses weapon this round.
  Parameters: save_tn=11, weapon_lost=true.
  Playstyles: Controller. Hook: tactical disarm.

CAST_2 | Major | 2p | — | enemy_group (3) | medium | instant | control
  Effect: mass disarm — 3 targets save agi or lose weapons 1r.
  Parameters: save_tn=12, targets=3.
  Playstyles: Controller. Hook: area disarm.

CAST_3 | Major | 3p + 1phy + scene_use | zone (5m) | close | scene | control
  Effect: absolute — 5m: save or cannot use weapons scene.
  Parameters: area=5m, save_tn=13, weapons_disabled=true, duration=scene, limit=1/scene.
  Playstyles: Controller. Hook: scene denial.

RIDER_A | maneuver | restriction: Disrupt only | 1p
  Effect: on_Full Disrupt attempts disarm in addition.
  Playstyles: Controller. Combo: disrupt_disarm.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect armed enemies in 15m.
  Parameters: range=15m.
  Playstyles: Investigator. Combo: weapon_intel.

RIDER_C | strike | restriction: ranged attacks | 1p
  Effect: on_Full ranged may disarm target (save agi).
  Playstyles: Controller. Combo: ranged_disarm.

CAPSTONE (authored: WEAPON-STRIPPER) | 4p + 1phy + scene_use | — | enemy_group (visible) | medium | scene | control
  Signal: "What they wield becomes mine."
  Viability: setup_dependent.
  Effect: visible enemies save agi (TN 13) or weapons disarmed scene.
  Parameters: scope=all_visible, duration=scene, limit=1/scene.
  Playstyles: Controller.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 1p
  Shift: branch. Effect: Disrupt also can destroy disarmed weapon.
  Combo: weapon_destroy.

---

**Kinetic Redirect** — Complement | Tank, Support | Human
Identity: Send enemy attack back.

CAST_1 | Minor | 1p | — | self | — | 1 round | defense
  Effect: deflect — next incoming ranged reflected; 1 damage back to attacker.
  Parameters: next_ranged_reflect=1.
  Playstyles: Tank. Hook: spike counter.

CAST_2 | Major | 2p | — | self | — | scene | defense, counter
  Effect: sustained — ranged attacks 50% reflected scene.
  Parameters: ranged_reflect_chance=50%, duration=scene.
  Playstyles: Tank. Hook: scene ranged counter.

CAST_3 | Major | 3p + 1phy + scene_use | self | — | scene | defense, meta
  Effect: absolute — all ranged redirected to attacker.
  Parameters: ranged_reflect_chance=100%, duration=scene, limit=1/scene.
  Playstyles: Tank. Hook: scene redirect.

RIDER_A | posture/reactive_defense | R2 (Parry, Block) | 0p passive
  Effect: blocked/parried attacks reflect 1 damage.
  Parameters: reflect=1.
  Playstyles: Tank. Combo: parry_counter.

RIDER_B | posture/awareness | R3 | 0p passive
  Effect: detect incoming attacks; +1 defense vs them.
  Parameters: defense=+1.
  Playstyles: Tank. Combo: informed_defense.

RIDER_C | strike | restriction: Parry counter | 1p
  Effect: on_Full Parry counter-attack +1 damage.
  Playstyles: Tank, Brawler. Combo: counter_strike.

CAPSTONE (authored: MIRROR SOUL) | 5p + 1phy + scene_use | — | self | — | scene | defense, meta
  Signal: "What strikes me strikes back."
  Viability: setup_dependent.
  Effect: scene: all attacks have 50% reflection (melee + ranged); counter damage applies.
  Parameters: reflect_all=50%, duration=scene, limit=1/scene.
  Playstyles: Tank.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 0p
  Shift: reinforce. Effect: reflect damage +2 (was +1).
  Combo: null.

---

## Sub-category 4.20 — Sonic

---

**Sonic Scream** — Primary | Area Denier, Artillery | Human, Creature
Identity: Vocal attack at deafening volume.

CAST_1 | Major | 2p | — | zone (3m cone) | close | instant | damage, status
  Effect: scream — 3m cone: 2 damage + -1 attacks 1r.
  Parameters: area=3m_cone, damage=2, penalty=-1.
  Playstyles: Area Denier. Hook: area debuff.

CAST_2 | Major | 3p | — | zone (5m cone) | medium | instant | damage, control
  Effect: howl — 5m cone: 3 damage + save will or shaken.
  Parameters: area=5m_cone, damage=3, save_tn=12, status_on_fail=shaken.
  Playstyles: Area Denier, Controller. Hook: area spike.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | instant | damage, status
  Effect: banshee wail — 10m: 3 damage + exposed.
  Parameters: area=10m, damage=3, status=exposed.
  Playstyles: Area Denier, Eradicator. Hook: big area.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks also apply -1 attacks 1r.
  Playstyles: Area Denier. Combo: sonic_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Parley (deafened).
  Parameters: range=5m, parley=-1.
  Playstyles: Diplomat counter. Combo: deafening.

RIDER_C | parley | restriction: Taunt only | 1p
  Effect: on_Full Taunt via sonic +2.
  Playstyles: Diplomat. Combo: loud_taunt.

CAPSTONE (authored: VOICE OF RUIN) | 5p + 1phy + scene_use | — | zone (20m) | medium | instant | damage, control
  Signal: "My voice breaks stone."
  Viability: offensive_swing.
  Effect: 20m: 3 damage + exposed; destroys cover 1 step.
  Parameters: area=20m, damage=3, status=exposed, cover_reduction=1_step, limit=1/scene.
  Playstyles: Area Denier, Eradicator.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: penalty -2 (was -1).
  Combo: null.

---

**Vibration Wave** — Complement | Area Denier, Controller | Human
Identity: Control sonic vibrations.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | status
  Effect: mild vibration — 3m: -1 enemy attacks 1r.
  Parameters: area=3m, penalty=-1.
  Playstyles: Area Denier. Hook: spike area debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | 1 round | damage, status
  Effect: resonance — 5m: 2 damage + shaken on Crit.
  Parameters: area=5m, damage=2_all, status_on_crit=shaken.
  Playstyles: Area Denier. Hook: area damage.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | scene | control
  Effect: vibration field — 10m: -1 Assess; -1 defense rolls scene.
  Parameters: area=10m, assess_penalty=-1, defense_penalty=-1, duration=scene.
  Playstyles: Area Denier, Controller. Hook: scene debuff.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks apply -1 defense 1r.
  Playstyles: Controller. Combo: vibration_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 defense.
  Parameters: range=5m, defense=-1.
  Playstyles: Controller. Combo: defense_aura.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect structural weaknesses and hidden via vibration.
  Parameters: range=10m.
  Playstyles: Investigator. Combo: vibration_awareness.

CAPSTONE (authored: RESONANCE BREAK) | 4p + 1phy + scene_use | — | zone (10m) | medium | instant | damage, status
  Signal: "Every mass I strike rings with death."
  Viability: offensive_swing.
  Effect: 10m: 3 damage + exposed + cover destroyed 1 step.
  Parameters: area=10m, damage=3, status=exposed, cover_reduction=1, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: broadening on RIDER_B) | 0p
  Shift: reinforce. Effect: aura also -1 attack rolls.
  Combo: dual_debuff.

---

**Resonance Shatter** — Primary | Eradicator, Area Denier | Human, Creature
Identity: Match target's frequency and destroy.

CAST_1 | Major | 2p | — | enemy_single | medium | instant | damage, status
  Effect: resonate — 3 damage + bleeding 1r.
  Parameters: damage=3, status=bleeding_1r.
  Playstyles: Eradicator. Hook: spike DoT.

CAST_2 | Major | 3p + 1phy | enemy_single | medium | 2 rounds | damage, status
  Effect: sustained shatter — 4 damage + bleeding 2r + exposed.
  Parameters: damage=4, status=bleeding_2r, bonus=exposed.
  Playstyles: Eradicator. Hook: heavy DoT.

CAST_3 | Major | 4p + 1phy + scene_use | zone (5m) | medium | instant | damage, control
  Effect: mass — 5m: 3 damage + cover destroyed; structures collapse.
  Parameters: area=5m, damage=3_all, cover_destroyed=true, limit=1/scene.
  Playstyles: Eradicator. Hook: scene destruction.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks bypass 1 armor step; on_Crit exposed.
  Playstyles: Brawler, Eradicator. Combo: armor_break.

RIDER_B | posture/reactive_offense | R2 (Parry, Block) | 0p passive
  Effect: melee attackers take 2 damage; armor -1 1r.
  Parameters: counter=2, armor_reduction=1r.
  Playstyles: Tank. Combo: heavy_counter.

RIDER_C | posture/awareness | R3 | 0p passive
  Effect: detect structural resonance frequency of nearby (+1 damage vs found).
  Parameters: range=15m.
  Playstyles: Investigator. Combo: weakness_intel.

CAPSTONE (authored: SHATTER WORD) | 5p + 2phy + scene_use | — | enemy_group (visible) | medium | instant | damage, meta
  Signal: "I name their frequency and they break."
  Viability: offensive_swing.
  Effect: visible save will or 4 damage + exposed.
  Parameters: scope=all_visible, damage=4, status=exposed, save_tn=13, limit=1/scene.
  Playstyles: Eradicator.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: bypass 2 armor; +1 damage.
  Combo: null.

---

**Sound Dampening** — Complement | Support, Trickster | Human
Identity: Silence zones.

CAST_1 | Minor | 1p | — | zone (3m) | close | scene | utility
  Effect: dampen — 3m: -1 on attack rolls + Parley.
  Parameters: area=3m, attack_parley_penalty=-1, duration=scene.
  Playstyles: Controller, Support. Hook: zone debuff.

CAST_2 | Major | 2p | — | zone (5m) | close | scene | utility, control
  Effect: silence — 5m: no voice attacks; conceals sound-based.
  Parameters: area=5m, silence=true, duration=scene.
  Playstyles: Support. Hook: scene silence.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | scene | control, meta
  Effect: absolute — 10m: no sound; vocal casts fail.
  Parameters: area=10m, duration=scene.
  Playstyles: Controller. Hook: scene lockdown.

RIDER_A | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal auto-Full in dampened zone.
  Playstyles: Assassin. Combo: silent_conceal.

RIDER_B | posture/aura_ally | R3 | 0p passive
  Effect: allies in 5m +2 to Conceal rolls.
  Parameters: range=5m, conceal=+2.
  Playstyles: Support, Assassin. Combo: party_stealth.

RIDER_C | parley | restriction: Negotiate only | 1p
  Effect: on_Full Parley in silence +2 (no interruption).
  Playstyles: Diplomat. Combo: silence_parley.

CAPSTONE (authored: TOTAL SILENCE) | 4p + 1phy + scene_use | — | zone (15m) | medium | scene | meta, utility
  Signal: "Where I stand, there is quiet."
  Viability: setup_dependent.
  Effect: 15m: no sound; all vocal/sonic abilities fail; +2 Conceal for allies.
  Parameters: area=15m, duration=scene, limit=1/scene.
  Playstyles: Support.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: reinforce. Effect: conceal also grants +1 damage on first attack from stealth.
  Combo: stealth_strike.

---

**Concussive Thunderclap** — Primary | Area Denier | Human
Identity: Single deafening burst.

CAST_1 | Minor | 1p | — | zone (3m) | close | 1 round | status
  Effect: quick clap — 3m: shaken 1r.
  Parameters: area=3m, status=shaken_1r.
  Playstyles: Controller. Hook: spike status.

CAST_2 | Major | 2p | — | zone (5m) | close | 1 round | damage, control
  Effect: mass clap — 5m: 2 damage + save will or shaken.
  Parameters: area=5m, damage=2, save_tn=12, status_on_fail=shaken.
  Playstyles: Area Denier, Controller. Hook: area damage.

CAST_3 | Major | 3p + 1phy | zone (10m) | medium | instant | damage, status
  Effect: doomclap — 10m: 3 damage + exposed on Crit.
  Parameters: area=10m, damage=3, status_on_crit=exposed.
  Playstyles: Area Denier. Hook: big area.

RIDER_A | strike | restriction: all attack sub-types | 1p
  Effect: on_Full attacks apply -1 attacks 1r.
  Playstyles: Controller. Combo: stunned_strike.

RIDER_B | posture/aura_enemy | R3 | 0p passive
  Effect: enemies in 5m -1 Parley (deafened).
  Parameters: range=5m, parley=-1.
  Playstyles: Controller. Combo: deafening.

RIDER_C | parley | restriction: Taunt only | 1p
  Effect: on_Full Taunt via clap +2.
  Playstyles: Diplomat. Combo: loud_taunt.

CAPSTONE (authored: THUNDER LORD) | 4p + 1phy + scene_use | — | zone (15m) | medium | instant | damage, control
  Signal: "I speak like thunder."
  Viability: offensive_swing.
  Effect: 15m: 3 damage + shaken; cover -1.
  Parameters: area=15m, damage=3, status=shaken_all, cover_reduction=-1, limit=1/scene.
  Playstyles: Area Denier.

ENHANCED_RIDER (authored: magnitude on RIDER_A) | 1p
  Shift: reinforce. Effect: penalty -2 (was -1).
  Combo: null.

---

**Echolocation** — Complement | Support, Investigator, Skirmisher | Human, Creature
Identity: 3D navigation via sound.

CAST_1 | Minor | 1p | — | zone (10m) | close | instant | information
  Effect: brief scan — 10m: detect positions.
  Parameters: range=10m, scope=all_entities.
  Playstyles: Investigator, Skirmisher. Hook: rapid scan.

CAST_2 | Major | 2p | — | zone (20m) | medium | scene | information
  Effect: sustained — 20m map awareness.
  Parameters: range=20m, duration=scene.
  Playstyles: Investigator. Hook: scene tracking.

CAST_3 | Major | 3p + 1men | zone (30m structure) | medium | scene | information
  Effect: deep scan — full structural map.
  Parameters: scope=structure, duration=scene.
  Playstyles: Investigator, Support. Hook: navigation.

RIDER_A | posture/awareness | R3 | 0p passive
  Effect: detect movement in 15m through walls.
  Parameters: range=15m, walls_pass=true.
  Playstyles: Investigator. Combo: omniscient.

RIDER_B | assess | restriction: Brief Assess only | 1p
  Effect: on_Full Assess in darkness +2.
  Playstyles: Investigator, Skirmisher. Combo: anti-dark.

RIDER_C | maneuver | restriction: Reposition only | 1p
  Effect: on_Full Reposition in obscured terrain at full speed.
  Playstyles: Skirmisher. Combo: dark_navigator.

CAPSTONE (authored: PERFECT ECHO) | 5p + 1men + scene_use | — | zone (30m) | medium | scene | information, meta
  Signal: "Nothing hides from my ear."
  Viability: setup_dependent.
  Effect: 30m omniscient via sound.
  Parameters: range=30m, duration=scene, limit=1/scene.
  Playstyles: Investigator.

ENHANCED_RIDER (authored: broadening on RIDER_A) | 0p
  Shift: reinforce. Effect: awareness reveals intents.
  Combo: null.

---

**Vocal Mimicry** — Complement | Trickster, Diplomat | Human
Identity: Perfect voice replication.

CAST_1 | Minor | 1p | — | self | — | scene | utility
  Effect: voice copy — mimic one voice.
  Parameters: scope=1_voice, duration=scene.
  Playstyles: Trickster. Hook: deception.

CAST_2 | Major | 2p | — | self | — | scene | utility, social
  Effect: sustained — mimic multiple voices scene.
  Parameters: multiple=true, duration=scene.
  Playstyles: Trickster, Diplomat. Hook: scene deception.

CAST_3 | Major | 3p + 1men | all_visible | medium | scene | control, meta
  Effect: dominant — allies/enemies confuse identity.
  Parameters: confusion_scope=all_visible, duration=scene.
  Playstyles: Controller, Trickster. Hook: scene control.

RIDER_A | parley | restriction: all Parley types | 1p
  Effect: on_Full Parley impersonating known-voice +2.
  Playstyles: Diplomat, Trickster. Combo: voice_parley.

RIDER_B | maneuver | restriction: Conceal only | 1p
  Effect: on_Full Conceal via voice mimicry auto-Full (confuse pursuers).
  Playstyles: Trickster. Combo: vocal_stealth.

RIDER_C | parley | restriction: Destabilize only | 1p
  Effect: on_Full Destabilize via false voice identity +2.
  Playstyles: Diplomat, Trickster. Combo: identity_break.

CAPSTONE (authored: THOUSAND VOICES) | 4p + 1men + scene_use | — | self | — | scene | social, meta
  Signal: "Whose voice they hear, I choose."
  Viability: setup_dependent.
  Effect: scene: seamless voice swaps; +2 all Parley; others' Assess vs you -2.
  Parameters: duration=scene, limit=1/scene.
  Playstyles: Diplomat, Trickster.

ENHANCED_RIDER (authored: new_dimension on RIDER_A) | 1p
  Shift: branch. Effect: Parley also allows verbal commands to confuse target's next action.
  Combo: command_deception.


