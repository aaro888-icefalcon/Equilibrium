# V1 Category-Name Vestiges — Audit & Restructure Plan

**Last audit:** after CP-G push on branch `claude/emergence-game-setup-6ECgI`.

## Scope Note

Session-zero powers-catalog migration is complete. The V1 category names (`physical_kinetic`, `perceptual_mental`, `matter_energy`, `biological_vital`, `auratic`, `temporal_spatial`, `eldritch_corruptive`) still appear in **combat, progression, sim, schemas**, and **enemy data** — not as catalog references, but as content identifiers used as tags in damage types, breakthrough rules, NPC weighting, and enemy affinity tables.

## Target Shape Question

The V2 catalog at `emergence/data/powers_v2/*.json` has:

- **6 broad categories**: `kinetic`, `material`, `paradoxic`, `spatial`, `somatic`, `cognitive`
- **5 sub-categories each** (30 total family groups): see table below
- **200 powers** distributed across them

| broad      | sub-categories                                        |
|------------|-------------------------------------------------------|
| kinetic    | gravitic, impact, projective, sonic, velocity         |
| material   | corrosive, elemental, machinal, radiant, transmutative|
| paradoxic  | anomalous, divinatory, probabilistic, sympathetic, temporal |
| somatic    | augmentation, biochemistry, metamorphosis, predation, vitality |
| spatial    | gateway, phasing, reach, territorial, translative     |
| cognitive  | auratic, dominant, perceptive, predictive, telepathic |

User directive referenced "36 v2 categories". The actual current V2 shape is **30 sub-categories** (6 × 5). "36" would require either (a) adding a 6th sub-category per broad, or (b) using a different taxonomy. **Need to resolve this before downstream code is reshaped, because every reference below needs a target taxonomy to migrate to.**

---

## Live-Code Vestige Inventory

### Combat

- `emergence/engine/combat/damage.py:42-51` — `DAMAGE_TYPE_MAP_V1_TO_V2` keys on all 7 V1 category names. **Purpose:** coerces V1 damage-type strings to V2 broads. **Action after taxonomy choice:** delete map; rewrite call sites to produce V2 broads directly; if sub-category damage matters, extend to the new sub-category axis.
- `emergence/engine/combat/damage.py:246` — docstring comment says "physical_kinetic melee/ranged" (armor-applicable). **Action:** rename to "kinetic melee/ranged".
- `emergence/engine/combat/statuses.py:101,120,129` — status effects emit `damage_type` tags with V1 names (`eldritch_corruptive`, `matter_energy`, `physical_kinetic`). **Action:** remap to V2 broad (`paradoxic`, `material`, `kinetic` respectively). Then audit every consumer of `damage_type` in combat resolution.
- `emergence/engine/combat/statblock_parser.py:34-35` — "auratic" appears as a V2 sub-category (cognitive/auratic) in a parser table. **Legitimate V2 use, not vestige.** Leave.

### Progression

- `emergence/engine/progression/breakthrough.py:60-68` — `MARK_POOLS` keyed by all 7 V1 category names; mark-id prefixes hard-coded: `P*` for physical_kinetic, `M*` for perceptual_mental, `E*` for matter_energy, `B*` for biological_vital, `A*` for auratic, `T*` for temporal_spatial, `X*` for eldritch_corruptive. **Action:** re-author `MARK_POOLS` around V2 broads (K/C/M/P/S/Sp mark prefixes or similar). Decide whether marks live at broad level or sub-category level (30 pools vs. 6).
- `emergence/engine/progression/breakthrough.py:211` — default `primary_cat` falls back to `"physical_kinetic"`. **Action:** change default to `"kinetic"`.
- `emergence/engine/progression/breakthrough.py:245` — string literal `"biased to eldritch_corruptive"` in side-effect log. **Action:** swap to `"paradoxic"`.
- `emergence/engine/progression/corruption.py:30` — literal string `"eldritch_corruptive cost -1"` in a corruption-mark description. **Action:** swap to `"paradoxic cost -1"`.

### Sim / NPC

- `emergence/engine/sim/npc_generator.py:112-118` — power-category weights dict (`_BASE_CATEGORY_WEIGHTS` or similar) keyed on a mix of V1 and abbreviated names: `physical`, `perceptual`, `matter_energy`, `biological`, `auratic`, `temporal_spatial`, `eldritch`. **Action:** rekey to the 6 V2 broads and retune weights.
- `emergence/engine/sim/content_loader.py:146-147` — a keyword list containing V1 category tokens (`matter`, `energy`, `biological`, `vital`, `auratic`, `temporal`, `spatial`, `eldritch`). **Purpose:** probably content-tag indexing. **Action:** audit what reads this list; retarget to V2 broads + sub-categories.

### Schemas

- `emergence/engine/schemas/validation.py:29-32` — `VALID_POWER_CATEGORIES_V1` set kept for save-file migration validation. **Action:** delete once no save files reference V1 categories, or rename to `VALID_POWER_CATEGORIES_LEGACY` and bump save-schema version. Also add `VALID_POWER_CATEGORIES_V2` + `VALID_SUB_CATEGORIES_V2` alongside.

### Character-Creation Tagging

- `emergence/engine/character_creation/scenario_pool.py:81-82,90` — `"auratic"` appears in `REACTION_KEYWORDS` tag lists. **Legitimate V2 sub-category use** (cognitive/auratic). Leave.

---

## Test-File Vestiges

These tests construct fake characters with V1 `primary_category` strings and `damage_type` affinities. They still pass because the code paths they exercise use V1 keys internally. When the code is restructured, each of these needs to be updated in lockstep:

- `emergence/tests/unit/test_breakthrough.py:22,46,58,133,188,247`
- `emergence/tests/unit/test_family.py:16,64`
- `emergence/tests/unit/test_schemas.py:48,49,99,244,318,321,387`
- `emergence/tests/unit/test_npc_generator.py:37-38`
- `emergence/tests/integration/test_progression.py:26,43,52,53,58,95,128`
- `emergence/tests/scenarios/test_long_game.py:31,86,87,186,213`

---

## Enemy Data

- `emergence/data/enemies/human.json`, `creature.json`, `eldritch.json` — every enemy entry has an `affinity_table` dict keyed on all 7 V1 category names (e.g., `{"physical_kinetic": "neutral", ..., "eldritch_corruptive": "vulnerable"}`). **Action:** bulk rewrite to 6 V2 broads. If sub-category resistance is meaningful, expand to 30 or 36 keys; otherwise collapse to 6.

---

## Recommended Restructure Sequence

Before any of this runs, answer: **do we target 30 sub-categories (current V2 data shape) or 36 (6 × 6)?** The answer determines whether `paradoxic` (and each other broad) gets a 6th sub-category added, whether enemy affinity tables stay at broad level or expand, and how `MARK_POOLS` is authored.

Assuming **30 V2 sub-categories** (current data), the safe order is:

1. **schemas/validation.py** — add V2 validators alongside V1; keep V1 as `LEGACY` for save compat.
2. **combat/damage.py + statuses.py** — retarget `damage_type` values to V2 broads; delete `DAMAGE_TYPE_MAP_V1_TO_V2`.
3. **data/enemies/*.json** — rewrite every `affinity_table` to 6 V2 broads (with a one-off transform script).
4. **progression/breakthrough.py + corruption.py** — rekey `MARK_POOLS` to V2 broads (decide pool granularity), retarget strings.
5. **sim/npc_generator.py + sim/content_loader.py** — rekey category weights and content-tag lists.
6. **tests** (all files above) — update fixtures to V2 keys.
7. **delete** `VALID_POWER_CATEGORIES_V1` / `LEGACY` once save migration is done.

Each of the above is independently committable. Full surface ≈ 9 engine files + 3 JSON files + 6 test files.

## What This Is Not

Not part of this audit (leave alone, already V2-correct): scenarios.py, scenario_pool.py (the `"auratic"` uses are V2 sub-category), data/powers_v2/*.json, statblock_parser.py (its `"auratic"` is also V2 sub-cat).
