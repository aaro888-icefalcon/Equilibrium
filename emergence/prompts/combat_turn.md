# Combat Turn Prompt

> Prepended with the canonical voice preamble (`emergence/prompts/canonical_voice.md`). Voice lives in prose; mechanism lives in the ROLL block and the UI box. Keep them flush, never collapsed.

Register: {register_directive}
Round {round}: {actor} uses {action_type}.
Result: {action_result}
Damage dealt: {damage_dealt}. Status applied: {status_applied}.
Enemies remaining: {enemies_remaining}.
Player condition: {player_condition}

## Structure (emit in order)

1. **Prose beat** — 2-4 short declaratives, paratactic/right-branching. At least one fragment paragraph (`"Opportunity."` / `"Thud. Thud."` / `"Time."`). One precise-technical-noun + pulp-verb adjacency (`"the blade bites deep"`, `"driving toward the pulsing target"`). One medical/mechanical/military simile permitted. Em dash for appositive specification of the enemy's anatomy/armor.
2. **ROLL block:**

   ```
   **ROLL: <ACTION>**
   **Dice:** d1 + d2 = sum
   **Modifiers:** +X (LABEL) ...
   **Total:** T vs DC D (tag)
   **Result:** **TIER**
   ```

3. **Italic damage line:** `*Damage dealt: X | Damage taken: Y*`
4. **Consequence prose** — 1-2 sentences, closing on a compressed aphoristic single-line paragraph.
5. **ASCII UI box** — HP/SP/options flush against prose.

## Length

40-120 words including ROLL block and UI box.

## Mechanism channel

Dice, DC, damage numbers, HP/SP live ONLY inside the ROLL block or UI box. Never in prose.

## Self-audit

Run the ten checks in the preamble's `<self_audit>` block, then the `<recognizability_test>`. Quote your shortest and longest sentence to a scratch line if rhythm variance is ambiguous; delete before emitting. Cap total revisions at 2 — emit on the second pass regardless.
