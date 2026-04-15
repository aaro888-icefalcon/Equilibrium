# Combat Migration + Power Library — Micro-Commit Plan

## Guiding Principles
- Each commit touches ≤3 engine files + their tests
- Tests run after every commit; no red-to-red transitions
- One-liner status before and after each step
- No silent work >30 seconds — externalize reasoning to scratch notes

## Baseline
- 911 tests pass (3 skipped)
- Branch: claude/combat-migration-power-library-Z45WO

---

## Phase A: Schema Foundation (4 commits)

### A1: Add new enums and constants
- Files: `schemas/encounter.py`, `schemas/combatant.py`
- Add: CombatVerb enum update (remove Defend/Disengage, add Power_Minor/Brace/Posture_Change/Utility)
- Add: PostureType enum (parry, block, dodge, aggressive)
- Add: RiderType enum (strike, posture, maneuver, parley, assess, finisher)
- Add: ManeuverSubType enum (reposition, disrupt, conceal)
- Add: BinaryFlag enum (grappled, hidden)
- Add: PowerBroad enum (somatic, cognitive, material, kinetic, spatial, paradoxic)
- Add: EffectFamily enum (13 values)
- Test: Fix any tests referencing old Defend/Disengage verbs — keep backward-compat alias temporarily
- Run tests → must pass

### A2: Extend Combatant schema with new fields
- Files: `schemas/combatant.py`
- Add fields: current_posture, armed_posture_riders, hidden, base_pool_max, effective_pool_max, current_pool, brace_uses_remaining, scene_mode_uses
- Defaults: posture=parry, armed=[], hidden=False, pool=3+tier, brace=3, scene_modes=set()
- Test: Update test_schemas round-trip tests for new Combatant fields
- Run tests → must pass

### A3: New power content schema (ModeSpec, RiderSpec)
- Files: `schemas/content.py`
- Add: ModeSpec dataclass (slot_id, action_cost, pool_cost, additional_cost, effect_families, targeting, range, duration, effect_desc, effect_params, posture_sensitive, playstyles)
- Add: RiderSpec dataclass (slot_id, rider_type, sub_category, pool_cost, restrictions, effect_desc, effect_params, playstyle_fit, combo_enable)
- Add: PowerV2 structure with 8 mode slots (3 casts, 2 capstone options, 3 riders, 3 enhanced rider options)
- Test: Round-trip serialization of new types
- Run tests → must pass

### A4: Schema version bump + migration stubs
- Files: `schemas/serialization.py`, `persistence/migration.py`
- Bump schema_version to "2.0"
- Add migration function stubs: v1_to_v2 for Combatant (add defaults), Action (remap verbs)
- Test: Migration function unit tests
- Run tests → must pass

---

## Phase B: Pool + Posture Mechanics (3 commits)

### B1: Pool module
- Files: NEW `combat/pool.py`
- Functions: compute_base_pool_max(tier), compute_effective_pool_max(base, armed_count), spend_pool(combatant, cost), refill_pool(combatant), brace(combatant)
- Test: NEW `tests/unit/test_pool.py` — tier calcs, brace cap, effective max with armed riders
- Run tests → must pass

### B2: Posture module
- Files: NEW `combat/postures.py`
- Functions: get_posture_defense(posture), change_posture(combatant, new_posture), validate_posture_rider_compat(posture, rider), aggressive_defense_override()
- Test: NEW `tests/unit/test_postures.py` — 4 postures, aggressive no-defense-roll, compat checks
- Run tests → must pass

### B3: Wire pool + posture into CombatState
- Files: `combat/verbs.py` (CombatState/CombatantRecord)
- Add pool fields and posture to CombatantRecord init
- Ensure existing verb resolvers don't break with new fields
- Test: Existing test_verbs must still pass
- Run tests → must pass

---

## Phase C: Verb Changes (4 commits)

### C1: Remove Defend verb, add Posture_Change
- Files: `combat/verbs.py`, `combat/encounter_runner.py`
- Remove resolve_defend; add resolve_posture_change (minor action, switches posture)
- Update _dispatch_verb
- Test: Fix tests referencing Defend; add test for Posture_Change
- Run tests → must pass

### C2: Remove Disengage, update Maneuver with Conceal
- Files: `combat/verbs.py`
- Remove resolve_disengage; add conceal sub-type to resolve_maneuver
- Conceal: roll vs TN 10, Full → hidden=True
- Hidden breaks on: attack, parley, being hit, declaring Aggressive
- Test: Add conceal tests; fix disengage references
- Run tests → must pass

### C3: Add Brace verb
- Files: `combat/verbs.py`, `combat/encounter_runner.py`
- resolve_brace: minor action, +1 pool, cap 3 uses per combat, can't exceed effective max
- Wire into _dispatch_verb
- Test: Add brace tests (cap, effective max ceiling)
- Run tests → must pass

### C4: Add Power_Minor + Utility verbs
- Files: `combat/verbs.py`, `combat/encounter_runner.py`
- resolve_power_minor: like resolve_power but checks action_cost=="minor"
- resolve_utility: catch-all minor with narrative effect
- Test: Add Power_Minor and Utility tests
- Run tests → must pass

---

## Phase D: Rider + Attack Updates (3 commits)

### D1: Posture rider module
- Files: NEW `combat/posture_riders.py`
- Functions: arm_rider(combatant, power_id, slot_id), disarm_rider(combatant, idx), apply_passive_effects(combatant, event), recalc_effective_pool_max(combatant)
- 9 sub-category handlers (stubs initially, flesh out key ones: reactive_defense, reactive_offense, periodic)
- Test: NEW `tests/unit/test_posture_riders.py` — arm/disarm, pool recalc, stacking
- Run tests → must pass

### D2: Rider combination module
- Files: NEW `combat/rider_combination.py`
- Functions: validate_combination(rider1, rider2), resolve_combination(rider1, rider2, action, combatant)
- Rules: same-type only, max 2, cost = sum + 1 pool tax
- Test: NEW `tests/unit/test_rider_combination.py` — valid/invalid combos, cost calc
- Run tests → must pass

### D3: Update attack resolution for postures + hidden
- Files: `combat/verbs.py` (resolve_attack section), `combat/damage.py`
- Aggressive posture: no defender roll, TN 10 flat
- Hidden modifier: -2 to attacker rolls against hidden target
- Apply passive posture rider effects on incoming attack
- Test: Update test_verbs attack tests, add aggressive + hidden cases
- Run tests → must pass

---

## Phase E: Power Library (3 commits)

### E1: Power statblock parser
- Files: NEW `engine/sim/power_parser.py`
- Parse markdown statblocks from emergence-power-statblocks-part1-clean.md and part2
- Output: list of PowerV2 dicts
- Test: NEW `tests/unit/test_power_parser.py` — parse sample powers, verify field extraction
- Run tests → must pass

### E2: Generate power JSON files (6 broads)
- Files: Script run to generate `data/powers_v2/*.json`
- 6 files: somatic.json, cognitive.json, material.json, kinetic.json, spatial.json, paradoxic.json
- Each power has full 8-mode structure
- Test: data_loader v2 loads all 200 powers, validates schemas
- Run tests → must pass

### E3: Update data_loader for v2 powers
- Files: `combat/data_loader.py`
- Add load_powers_v2() alongside existing load_powers()
- Validate each power against PowerV2 schema
- Test: Update test_data_loader for v2 format
- Run tests → must pass

---

## Phase F: Integration (3 commits)

### F1: Update AI profiles for new mechanics
- Files: `combat/ai.py`
- Add hidden-target handling per profile
- Add posture-reading for tactical AI
- Add Brace/Conceal to AI action enumeration
- Test: Update test_ai with posture + hidden scenarios
- Run tests → must pass

### F2: Update encounter runner for new flow
- Files: `combat/encounter_runner.py`
- Combat init: posture declaration, rider arming, pool init, brace counter
- Round flow: support new verbs, hidden flag management, scene mode tracking
- Scene boundary: reset scene_mode_uses, refill pool, reset brace
- Test: Update test_combat_scenarios
- Run tests → must pass

### F3: Update narrator payloads + CLI
- Files: `narrator/payloads.py`, `runtime/step_cli.py`
- Augment combat_turn payload with posture, armed riders, hidden, pool state
- Update step_cli combat-round to present new verb options
- Test: Update test_narrator, test_step_cli
- Run tests → must pass

---

## Phase G: Regression + Polish (2 commits)

### G1: Fix any remaining test failures
- Files: various
- Run full suite, fix any broken tests from cascade effects
- Run tests → ALL must pass

### G2: Update schema migration + constants
- Files: `setting/constants.yaml`, `persistence/migration.py`
- Add all new constants (postures, rider_types, effect_families, etc.)
- Finalize v1→v2 migration functions
- Test: Migration round-trip tests
- Run tests → ALL must pass
- Push to remote

---

## Total: ~22 commits across 7 phases
## Estimated new/modified files: ~15 engine files, ~10 test files
## Target: 200 powers loaded, all Rev 4 mechanics functional, all tests green
