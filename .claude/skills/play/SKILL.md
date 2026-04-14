---
name: play
description: Start or resume an Emergence game session. Use when the player wants to play the game.
disable-model-invocation: true
allowed-tools: Bash(python3 -m emergence *)
---

Start or resume an Emergence game session. $ARGUMENTS

## Steps

1. Check game state:
   ```
   python3 -m emergence --save-root ./saves/default step status
   ```

2. **If FRESH (no save):**
   - Initialize the world: `python3 -m emergence --save-root ./saves/default step init`
   - Begin Session Zero (character creation) — see below

3. **If VALID with SESSION_ZERO mode:**
   - Read `session_zero_scene` from status to find current scene
   - Continue from that scene

4. **If VALID with SIM mode:**
   - Run a tick: `python3 -m emergence --save-root ./saves/default step tick`
   - Generate situation: `python3 -m emergence --save-root ./saves/default step situation`
   - Narrate the scene from the `narrator_payload`
   - Present choices to the player
   - Wait for input, then resolve: `python3 -m emergence --save-root ./saves/default step resolve --choice-id <id>`

5. **If VALID with COMBAT mode:**
   - Present available verbs and targets
   - Wait for player choice
   - Process round: `python3 -m emergence --save-root ./saves/default step combat-round --verb <verb> --target <target>`

## Session Zero Flow

For each scene 0 through 9:
1. Get scene: `python3 -m emergence --save-root ./saves/default step scene --index N`
2. Read the `narrator_payload` and `framing_text`. Narrate it to the player.
3. If `needs_text_input` is true, ask for text (name, age for scene 0).
4. Present `choices` as numbered options if any exist.
5. Apply: `python3 -m emergence --save-root ./saves/default step scene-apply --index N --input-choice C` or `--input-text key=value`
6. Proceed to next scene.

After all 10 scenes:
- Finalize: `python3 -m emergence --save-root ./saves/default step scene-finalize`
- Narrate the character summary as an in-world reflection
- Save: `python3 -m emergence --save-root ./saves/default step save`
- Begin the simulation loop (step 4 above)

## Narration Rules

- Read the `register_directive` and `scene_type` from each payload
- Generate prose that is grounded, tactile, and unsentimental
- NEVER invent details not in the payload
- NEVER use meta-gaming language
- NEVER speak for the player character
