# Emergence Combat System Migration Guide

**Audience.** Claude Code instance continuing Emergence implementation. You have previously built a combat system and CLI against an earlier spec revision (pre-Rev 4). This guide tells you what changed and the order to adapt.

**Primary reference.** `combat-spec-revision-4.md` is the new authoritative reference. When in doubt about a mechanic, check Rev 4.

**Scope.** Adapt existing precursor code to match Rev 4. Preserve what still applies; modify or replace what diverged. Run regression tests at each checkpoint.

---

## 1. Summary of Changes

### 1.1 Verb catalog

**Removed:**
- `Disengage` → absorbed into Reposition maneuver
- `Defend` → replaced by passive posture + posture riders

**Added:**
- `Power_Minor` → minor-action cast (new; ~20-30% of powers have one)
- `Brace` → pool recovery minor action
- `Posture_Change` → explicit posture transition (was implicit in Defend)
- `Utility` → catch-all minor (was partially implicit)

**Retained:**
- `Attack`, `Power` (renamed Power_Major internally), `Assess`, `Maneuver`, `Parley`, `Finisher`

### 1.2 Postures (new concept)

Previously: stances (parry, block, dodge) per Rev 3.
Now: postures (Parry, Block, Dodge, Aggressive) per Rev 4.

Rename throughout: stance → posture. Add Aggressive as 4th option.

### 1.3 Posture riders (previously "ward riders")

Previously: ward riders triggered per incoming attack, 1 pool per trigger.
Now: posture riders are **pure passives** — always on while armed; no per-trigger cost; **-1 effective pool max per armed**.

Up to 2 armed simultaneously. Effects stack.

### 1.4 New binary flag

`hidden` — parallel to `grappled`. Added by Conceal maneuver. Breaks on caster's attack/parley/being hit directly/declaring Aggressive.

### 1.5 New maneuver sub-type

`conceal` joins `reposition` and `disrupt`. Adds `hidden` flag.

### 1.6 Rider system changes

- 3 rider slots per power, but each slot can be any of 6 rider types (strike, posture, maneuver, parley, assess, finisher).
- "No same sub-type twice" rule within a power.
- Rider combination permitted: sum + 1 pool tax, same-type only, max 2 combined.

### 1.7 Pool mechanics

- `base_pool_max = 3 + tier`
- `effective_pool_max = base_pool_max - count(armed_posture_riders)`
- No per-turn regen.
- Brace action: Minor, +1 pool, cap 3 per combat.

### 1.8 Cast mode changes

- Variable cost 1-3 pool within a power.
- Some casts can be Minor action (new).
- Scene cost flag (once-per-combat).
- 13 effect families (expanded from 5).

### 1.9 Other additions

- Capstone unlock: pick 1 of 2 authored options.
- Enhanced rider unlock: pick 1 of 3 base riders to enhance.
- 8 mode slots per power.
- Dual-gate tier-up (narrative + marks).

---

## 2. Schema Migration

### 2.1 `interface-spec.md` updates required

Your first task: update `interface-spec.md` itself. It's authoritative; Rev 4 flags specific changes.

**Action schema:**
```
# Replace verb enum
verb: Attack | Power | Power_Minor | Assess | Finisher | 
      Maneuver | Parley | Posture_Change | Brace | Utility
```

**Combatant schema — additions:**
```
current_posture: "parry" | "block" | "dodge" | "aggressive"
armed_posture_riders: list of {power_id, slot_id, sub_category}  # max 2
hidden: boolean  # default false
base_pool_max: int  # = 3 + tier
effective_pool_max: int  # computed = base - len(armed_posture_riders)
current_pool: int
brace_uses_remaining: int  # resets to 3 at combat start
scene_mode_uses: set of {power_id, slot_id}  # resets at scene end
```

**Character Sheet — additions:**
Same pool-related fields propagate to Character Sheet for persistent tracking between combats (`scene_mode_uses` persists within a scene).

**Power content schema — extensive changes:**

```
# Replace mode structure. Each power has exactly 8 mode slots:
modes:
  cast_1: ModeSpec  # Major cast (or Minor if authored as such)
  cast_2: ModeSpec
  cast_3: ModeSpec
  capstone_options: list of 2 ModeSpec  # player picks 1 at unlock
  rider_slots: list of 3 RiderSpec
  enhanced_rider_options: list of 3 EnhancedRiderSpec  # player picks 1 at unlock

ModeSpec (for cast):
  slot_id: string
  action_cost: "major" | "minor"
  pool_cost: int (1-6)
  additional_cost: {condition?, corruption?, heat?, scene_use?}
  effect_families: list of (damage | status | movement | information | 
    control | resource | defense | utility | meta | cost_shifted |
    action_economy | stat_alteration | terrain_alteration)
  targeting_scope: self | ally | touched | enemy_single | enemy_group | zone | all_visible
  range_band: touch | close | medium | far | extreme
  duration: instant | 1_round | 2_3_rounds | scene | persistent
  effect_description: string
  effect_parameters: structured per family
  posture_sensitive: bool (default false)
  supports_playstyle: list of playstyle tags
  
RiderSpec:
  slot_id: string
  rider_type: strike | posture | maneuver | parley | assess | finisher
  sub_category: only for posture riders (reactive_defense | reactive_offense | 
    reactive_status | periodic | aura_ally | aura_enemy | awareness | anchor | amplify)
  pool_cost: int (0 for posture riders)
  restrictions: 
    attack_sub_types: list (for strike)
    maneuver_sub_types: list (for maneuver)
    parley_sub_types: list (for parley)
    postures: list (for posture)
  effect_description: string
  effect_parameters: structured
  playstyle_fit: list
  combo_enable: string or null
```

**Power category field:**
- Update enum to consolidated 6-broad list: `somatic | cognitive | material | kinetic | spatial | paradoxic`
- OR: keep 7 categories per current spec and map broads onto them (document the mapping)

Recommendation: take the consolidation (6 broads); it matches content authoring work.

**Damage type enum:**
Update to match broads: `somatic | cognitive | material | kinetic | spatial | paradoxic` (one per broad).

**Status list:** no change (closed 7 retained).

### 2.2 Schema version bumps

All modified schemas bump `schema_version`. Current: "1.0". Post-Rev 4: "2.0".

Write migration functions per schema:
- Old Action (v1.0) → new Action (v2.0): verb remap (Defend → error/reject; Disengage → Maneuver+sub_type reposition with disengage flag authored out)
- Old Combatant (v1.0) → new (v2.0): add posture fields defaulting to "parry"; initialize armed_posture_riders empty
- Old Power (v1.0) → new (v2.0): more complex — may require re-authoring since mode structure changed

For old saves, if Power data is pre-Rev 4: migration cannot preserve mode structure losslessly. Recommend: fresh-start expected for vertical slice; old saves from pre-Rev 4 implementations invalidated.

### 2.3 Constants file (`constants.yaml`)

Add entries for new constants:
- `postures`: [parry, block, dodge, aggressive]
- `rider_types`: [strike, posture, maneuver, parley, assess, finisher]
- `posture_rider_sub_categories`: [reactive_defense, reactive_offense, ...]
- `effect_families`: [damage, status, ..., terrain_alteration]  # 13 values
- `maneuver_sub_types`: [reposition, disrupt, conceal]
- `binary_flags`: [grappled, hidden]
- `brace_max_uses_per_combat`: 3

---

## 3. Engine Module Changes

### 3.1 New or modified modules

**`postures.py`** (new or rewrite):
- Define 4 postures with their defensive mechanics.
- Aggressive special rules (no defense roll; no defensive posture riders).
- Posture change handler (Minor action).
- Posture compatibility check for rider arming.

**`posture_riders.py`** (new — replaces ward_riders module if one exists):
- Pure passive application logic.
- 9 sub-category handlers.
- Stacking logic (effects apply independently).
- Effective pool max recalculation trigger.
- Mid-combat re-arming with pool-preservation logic.

**`pool.py`** (modify):
- Base pool max formula (3 + tier).
- Effective max calculation (subtract armed count).
- Pool spend validation (check effective max).
- Brace handler (+1, cap 3, not exceeding effective max).

**`maneuvers.py`** (modify):
- Add Conceal handler: roll, TN 10, apply hidden flag on Full.
- Hidden flag toggle on specific events (attack/parley/hit/Aggressive).
- Remove Disengage (replace with Reposition flag if needed for narrative).

**`cast_modes.py`** (modify):
- Support Minor action casts (action_cost field).
- Scene cost checking (lookup in combatant's scene_mode_uses).
- 13 effect family dispatch.
- Variable cost handling (1-3 pool).

**`rider_combination.py`** (new):
- Combination resolution: check same-type constraint, calculate sum + 1 cost, apply both effects.
- Validation: two riders must both be declared in the same action's declaration phase.

**`attack.py`** (modify):
- Update TNs per attack sub-type.
- Handle Aggressive-posture incoming attack resolution (no defender roll).
- Apply passive posture rider effects on incoming attack.
- Apply hidden modifier (-2) to attacker rolls against hidden target.

**`statuses.py`** (modify if needed):
- No change to closed 7-list. 
- Ensure `corrupted` status present (was in spec; may or may not be implemented).
- Add handler for binary flag `hidden`.

**`finisher.py`** (verify):
- 5 momentum cost + target *exposed* gate.
- Finisher Table authored per encounter.
- Finisher riders (new rider type) apply per authoring.

**`ai_profiles.py`** (modify):
- Add hidden-target handling per profile.
- Posture-reading for tactical AI.
- Conceal-capable enemy template handling.

**`scene.py`** (new or modify):
- Scene boundary detection.
- Scene-end: reset `scene_mode_uses`, refill pool, reset brace uses, expire scene-duration statuses.

**`narrator_integration.py`** (modify):
- Augment state_snapshot with new fields (postures, armed_posture_riders, hidden, declared_action, etc.).
- Register directive for 4 postures, Brace, Conceal.

### 3.2 Removed modules / replaced behavior

- Ward trigger logic (per-attack pool decision) → replaced by posture_riders pure-passive application
- Defend action → replaced by posture mechanics
- Disengage as distinct verb → absorbed into Maneuver/Reposition

---

## 4. CLI Changes

CLI surface may need new commands or command modifications. Depending on your prior CLI design:

**New commands:**
- `conceal` → issue Conceal maneuver
- `brace` → issue Brace action
- `change-posture <posture>` → Posture Change Minor
- `cast-minor <power> <cast_slot>` → Minor-action cast
- `combine-riders <power1> <rider1> <power2> <rider2>` → declare combination (applied with next applicable verb)

**Modified commands:**
- `attack` → add rider declaration option (can now declare 1 or 2 riders at sum+1 cost)
- `maneuver <subtype>` → support new `conceal` subtype
- Old `defend` command → remove, replace with `change-posture` if transitional behavior needed

**Combat init flow:**
- Posture declaration (prompt for 1 of 4)
- Posture rider arming prompt (0, 1, or 2 riders, posture-compatible)
- Brace counter set to 3
- Scene-mode-uses cleared if new scene

### 4.1 State display

When showing player state, now include:
- Current posture
- Armed posture riders (name and brief effect)
- Effective pool max and current pool
- Brace uses remaining
- Hidden flag status
- Active statuses and binary flags

---

## 5. Testing Strategy

### 5.1 Schema migration tests

Write round-trip tests for each schema change:
- Serialize current-version object
- Deserialize
- Verify field equality

For v1.0 → v2.0 migration:
- Pre-Rev 4 Combatant → migrated Combatant → verify posture defaults, armed_posture_riders empty, hidden false
- Pre-Rev 4 Action.verb "Defend" → migration reject (invalid; no clean mapping)
- Pre-Rev 4 Action.verb "Disengage" → migration maps to Maneuver with reposition sub_type + disengage narrative flag

### 5.2 Math validation tests

**Pool max test:**
- Combatant with tier 3, 0 armed posture riders → effective_pool_max = 6 ✓
- Combatant with tier 3, 1 armed → effective_pool_max = 5 ✓
- Combatant with tier 5, 2 armed → effective_pool_max = 6 ✓

**Brace test:**
- Combatant at pool 2, effective max 5. Brace → pool 3. Brace → pool 4. Brace → pool 5. Brace attempt → rejected (cap 3 uses). 
- Combatant at pool 5, effective max 5. Brace → rejected or no-op (at max).

**Posture rider stacking test:**
- 2 armed posture riders, both `reactive_defense` with -1 damage reduction. Incoming attack 6 damage → applied damage is 6 - 2 = 4.
- 2 armed, one `reactive_defense` (-1) + one `reactive_offense` (1 counter). Incoming attack 6 damage, hits → target takes 5 damage; attacker takes 1 damage.

**Aggressive posture test:**
- Combatant in Aggressive posture. Armed posture riders: verify none defensively-keyed are active.
- Attacker vs Aggressive target: roll vs TN 10 flat (no defender roll); on hit, full damage applied (no reduction from ward — but reduction from `reactive_defense` posture riders applies only if armed, which they shouldn't be in Aggressive).

**Rider combination test:**
- Power A strike rider cost 1, effect +fire damage.
- Power B strike rider cost 1, effect +status.
- Combined on one Heavy attack: pool cost 3 (1+1+1 tax). Both effects apply.
- Attempted combination of strike + maneuver rider: rejected (different types).
- Attempted 3-rider combo: rejected (max 2).

### 5.3 Regression tests

For each prior combat scenario your precursor handles, verify:
- Same outcome for same inputs (where mechanics unchanged)
- Updated outcome for changed mechanics (where Rev 4 differs from precursor)

Document diffs explicitly in test output.

### 5.4 Integration tests

- Full round-trip: Encounter Spec → combat resolution → Combat Outcome → Simulation ingest.
- Narrator payload: verify new fields present and correct for combat_turn payloads.
- Save/load: combat mid-encounter, save, load, resume — state preserved.

---

## 6. Migration Order (recommended)

Execute in this order to resolve dependencies cleanly:

1. **Update `interface-spec.md`** with Rev 4 schema changes. Bump schema_version to 2.0. This is the authoritative change.

2. **Update `constants.yaml`** with new enums and values.

3. **Update type definitions / enums in code** (posture, rider_type, maneuver_sub_type, etc.). Compilation should break in predictable places.

4. **Implement `pool.py` changes** (effective max calculation, Brace). Enables most downstream testing.

5. **Implement `postures.py`** (4 postures, change handler, compatibility).

6. **Implement `posture_riders.py`** (pure passive application, stacking, sub-categories). Remove old ward trigger logic.

7. **Implement `maneuvers.py` updates** (add Conceal; remove Disengage as separate verb).

8. **Implement `attack.py` updates** (Aggressive posture handling, hidden modifier, posture rider passive application).

9. **Implement `cast_modes.py` updates** (Minor cast support, scene cost, expanded effect families).

10. **Implement `rider_combination.py`** (new module).

11. **Implement `scene.py`** (boundary detection, reset logic).

12. **Update `ai_profiles.py`** (hidden handling, posture reading, new mechanics awareness).

13. **Update `narrator_integration.py`** (augmented payloads).

14. **Update CLI** (new commands, modified commands, state display).

15. **Write schema migration functions** for any existing persisted data.

16. **Run regression tests**. Fix regressions.

17. **Run new-mechanic tests** (math validation, integration).

18. **Manual playtest** if possible: run a sample T3 combat through all new mechanics (Conceal, Brace, posture change, rider combination, armed posture riders).

---

## 7. Open Questions for Claude Code

These require your judgment; decisions not specified in Rev 4:

1. **CLI command naming** — specific invocation strings. Match your existing conventions.
2. **Save file handling for pre-Rev 4 saves** — offer migration-best-effort OR require fresh characters for Rev 4? Recommend: require fresh characters (precursor was experimental).
3. **Error handling for invalid state transitions** — e.g., declaring posture rider that requires Parry while in Aggressive. Graceful rejection with clear message.
4. **Logging verbosity** — how much mechanic detail to log per turn. Recommend: full resolution trace in debug mode; summary in normal.
5. **Narrator payload delivery** — sync or async. Depends on existing architecture.

---

## 8. Risks and Mitigations

**Risk: Posture rider balance.** Effects calibrated to ~1 pool worth per combat. Over/under may emerge in play. Mitigation: expose calibration notes in authoring guidelines; adjust per power after playtest.

**Risk: Rider combination economy.** Sum + 1 pool tax may be too cheap or too expensive in practice. Mitigation: flag for playtest observation; may tighten to sum + 2 if spike turns trivialize.

**Risk: Conceal + AI interaction.** Hidden target targeting logic may behave unexpectedly with certain enemy templates. Mitigation: robust AI profile tests; explicit handling per profile.

**Risk: Scene boundary detection ambiguity.** Current spec is permissive. Mitigation: log scene boundary events for review; refine heuristic after observation.

**Risk: Schema migration complexity.** Old saves may not migrate cleanly. Mitigation: recommend fresh starts for Rev 4; preserve old saves for reference.

---

## 9. Success Criteria

Migration is complete when:
- ✓ All schemas at v2.0 with corresponding migration functions
- ✓ All new verbs functional (Brace, Conceal, Posture_Change, Power_Minor, Utility)
- ✓ Removed verbs absent (Defend, Disengage)
- ✓ 4 postures functional with distinct mechanics
- ✓ Posture riders apply passive effects; pool max reduction correct
- ✓ Rider combination resolvable
- ✓ Scene cost tracks correctly
- ✓ All regression tests pass or deltas documented
- ✓ New-mechanic tests all pass
- ✓ Manual playtest runs a full T3 combat cleanly

Upon completion, flag readiness to begin Power content authoring per the Authoring Guidelines Rev 3 document.
