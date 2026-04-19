# Character Creation Beat Prompt

> Prepended with the canonical voice preamble. Register-aware: the payload's `register_directive` drives cadence.

Register: {register_directive}
Scene: {scene_id}
Framing: {framing_text}
Choices: {choices}

## Structure

Canonical rhythm at the register directed by the payload.

- **ROLL block** ONLY if the beat actually rolls (session-zero scenes 2/5/7).
- **UI box** ONLY for choice-surface beats.
- `"intimate"` register: slower cadence, shorter paragraphs. Bold restricted to named entities only.
- `"action"` register: full canonical rhythm including fragments, em dashes, scene-capping aphorism.

## Length

80-200 words. Present the scene framing as prose, then the choices exactly as listed.

## Constraints

- Do not add choices beyond those listed. Do not editorialize or rank the choices.

## Self-audit

Run the ten checks in the preamble's `<self_audit>` block. Cap total revisions at 2.
