# Migration scope note — after CP-D

V1 catalog deletion is complete:
- emergence/data/powers/*.json removed
- load_powers() removed from data_loader.py
- T3_POWER_CATALOG / _STARTER_POWERS / _V1_TO_V2_CATEGORY / CATEGORY_MAP_V1_TO_V2 removed
- manifestation.py, scenes.py, year_one.py removed
- _make_v1_scenes removed from runtime/main.py

Remaining V1 category-name references in engine code are NOT catalog
references. They are content identifiers used as internal tags:

- combat/statuses.py:101,129 — uses "eldritch_corruptive"/"physical_kinetic"
  as damage_type tag values on status-effect payloads
- combat/damage.py:44 — DAMAGE_TYPE_MAP_V1_TO_V2 is its own V1->V2 coercion
  for damage types (separate from the category migration we just deleted)
- schemas/validation.py:29 — VALID_POWER_CATEGORIES_V1 is kept as a migration
  validator for old save files
- progression/breakthrough.py — breakthrough rules keyed on V1 category names
- progression/corruption.py — corruption-mark rules keyed on V1 category names
- sim/npc_generator.py — likely similar (not inspected in depth)

Deleting these requires a coordinated rewrite of:
  combat (damage, statuses), progression (breakthrough, corruption),
  sim/npc_generator, schemas/validation, plus 7 test files
  (test_progression, test_long_game, test_breakthrough, test_family,
   test_npc_generator, test_scenarios_v2, test_schemas).

That is a separate migration. The user's directive was scoped to the
powers catalog, which is done.

Next step after CP-D: ask the user whether to continue into bucket-2.
