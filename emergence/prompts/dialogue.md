# Dialogue Prompt

> Prepended with the canonical voice preamble. Canonical prose wraps quoted NPC dialogue. Mechanism lives in the optional negotiation ROLL block.

Register: {register_directive}
NPC: {npc_name}. Voice style: {npc_voice}.
Topic: {topic}. Standing with player: {standing}.
Player options: {player_options}

## Structure

- **Physical-detail anchor** — one sentence before or immediately after the quote (armor heat, masked breath, the heat radiating from his armor, the way his eyes track your shoulders not the pouch).
- Quoted NPC line in the NPC's voice style exactly.
- If payload has `opposed: true`, emit inline ROLL block:

  ```
  **ROLL: Negotiation**
  `Result: T vs DC D` (**TIER**)
  ```

- Respect the NPC's disposition cap — no cooperation beyond the payload-declared bound.
- Close on a negative-definition pivot when the NPC's stance changes (`"It's not a greeting. It's a **measurement**."` template).
- UI box after the NPC reply ONLY if `options_changed: true`.

## Length

30-140 words.

## Constraints

- Match the NPC's voice style exactly. Do not invent intent or information not in the payload. Do not speak for the player character.

## Self-audit

Run the ten checks in the preamble's `<self_audit>` block. Cap total revisions at 2.
