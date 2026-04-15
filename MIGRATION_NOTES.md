# Emergence Combat Migration Notes — Rev 4

## Status: IN PROGRESS

---

## 1. What Changed

### Verb Catalog
- Removed: `Defend` (replaced by posture mechanics), `Disengage` (absorbed into Reposition maneuver)
- Added: `Power_Minor`, `Brace`, `Posture_Change`, `Utility`
- Modified: `Attack` (4 sub-types), `Maneuver` (3 sub-types incl. Conceal), `Parley` (5 sub-types)

### Dice Resolution
- Old: take-higher-of-two-dice + modifiers
- New: dual-die sum + modifiers (d1 + d2 + mods vs TN)
- New outcome bands: Fumble (both=1), Failure (<TN-1), Partial Failure (TN-1), Marginal (TN), Full (TN+1 to TN+4), Critical (>=TN+5 or both=max)

### Posture System (new)
- 4 postures: Parry (counter), Block (damage reduction), Dodge (all-or-nothing), Aggressive (no defense)
- Replaces old Defend verb entirely

### Pool Mechanics (new)
- base_pool_max = 3 + tier
- effective_pool_max = base - armed_posture_rider_count
- Brace action: +1 pool, cap 3 uses per combat
- Pool fuels casts and rider combinations

### Power Schema
- Old: flat Power with single effect
- New: PowerV2 with 8 mode slots (3 casts, 2 capstone options, 3 riders, 3 enhanced rider options)
- 200 powers across 6 broads (was 48 across 7 categories)

### Category Consolidation
- Old 7 categories → New 6 broads (see mapping below)

### Action Economy
- Each turn: 1 Minor + 1 Major (was: 1 action)
- Minor: Brace, Posture_Change, Maneuver, Parley, Power_Minor, Utility
- Major: Attack, Power, Assess, Finisher

### Binary Flags (new)
- `hidden`: gained via Conceal maneuver, breaks on attack/parley/hit/Aggressive
- `grappled`: gained via Grapple attack sub-type

### Posture Riders (new)
- Pure passives, always-on while armed (max 2)
- 9 sub-categories: reactive_defense, reactive_offense, reactive_status, periodic, aura_ally, aura_enemy, awareness, anchor, amplify
- Each armed rider reduces effective_pool_max by 1

### Rider Combination (new)
- Combine 2 same-type riders on one action
- Cost: sum of individual costs + 1 pool tax

---

## 2. What Was Preserved

- Save/load architecture (persistence layer unchanged)
- Setting bible files and content loader
- Narrator queue protocol (FileNarrationQueue, MockNarrationQueue)
- 7 closed status list (bleeding, stunned, shaken, burning, exposed, marked, corrupted)
- 5 AI profiles structure (aggressive, defensive, tactical, opportunist, pack)
- Character creation (session zero, 10 scenes)
- Simulation engine (tick, factions, NPCs, locations, clocks)
- Progression mechanics (all 10 modules)
- Runtime/CLI architecture

---

## 3. Category Mapping (v1 → v2)

| Old Category (v1) | New Broad (v2) |
|--------------------|----------------|
| physical_kinetic | kinetic |
| perceptual_mental | cognitive |
| matter_energy | material |
| biological_vital | somatic |
| temporal_spatial | spatial |
| eldritch_corruptive | paradoxic |
| auratic | cognitive (merged) |

---

## 4. Schema Version

- Old: 1.0
- New: 2.0
- Old saves: Invalidated. Fresh characters required for Rev 4.

---

## 5. [NEEDS TUNING]

*(Populated during implementation)*

---

## 6. [AMBIGUOUS]

*(Populated during statblock parsing)*

---

## 7. Recommendations for Playtest

- Paradoxic capstone damage values (may be too swingy)
- Time Stop action-economy abuse potential
- Mind Control chains (duration stacking)
- Rider combination cost (sum+1 may be too cheap for spike turns)
- Posture rider balance (~1 pool value per 4-round combat target)
