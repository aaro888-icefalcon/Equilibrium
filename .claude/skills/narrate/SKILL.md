---
name: narrate
description: Narration style guide for Emergence. Loads when generating prose from engine payloads, narrating scenes, combat, or character creation.
user-invocable: false
---

# Emergence Narration

## Register

Grounded simulation. Stoic. Tactile. Unsentimental. The narrator observes rather than interprets. Show through action, not interpretation. Prose is plain and load-bearing. Dialogue is terse. Powers are physical facts, not spectacle.

## Register Directives

- **standard**: Clear, grounded. Present tense for action, past for reflection.
- **eldritch**: Senses contradict. Time wrong. Language destabilizes gently.
- **intimate**: Close, personal. Quiet moments. Earned emotional weight.
- **action**: Terse, kinetic. Short sentences. Sensory impact.
- **quiet**: Understated. What is NOT said matters. Restraint.

## Response Types and Word Counts

Word counts vary by response type, NOT just scene_type:

| Response type | Words | When |
|---|---|---|
| Scene opener | 150-300 | New scene (step scene-open). Full frozen moment. |
| Scene continuation | 60-120 | Post-action beat (step scene-continue). Result + invitation. |
| Scene close | 40-80 | DQ resolved (step scene-close). Resolution + forward. |
| Exposition | 50-200 | Free action response. No roll, no time cost. |
| Combat turn | 25-60 | Per round narration |
| Character creation | 80-200 | Session zero beats |
| Preamble | 150-300 | Session start, recap + in media res |

## The Narration Pipeline (Declare-Determine-Describe)

The sim loop follows DDD: player declares intent → engine determines outcome → narrator describes result.

**Scene Opener** (Sensation → Information → Invitation):
1. **Sensation** -- lead with the sense that matters most. Specific nouns beat abstractions.
2. **Information** -- what the character infers. Seed hidden elements as foreshadowing.
3. **Invitation** -- end on what invites action. Do NOT list numbered choices.

**Scene Continuation** (Result → Complication → Invitation):
1. **Result** -- narrate the engine's outcome (the tier is law — do not soften).
2. **Complication** -- describe any engine-generated complications (PBTA-style GM moves).
3. **Invitation** -- updated scene state, what invites the next action.

**Scene Close** (Resolution → Forward):
1. **Resolution** -- answer the dramatic question.
2. **Forward** -- momentum to the next scene.

## Consequence Enforcement

The engine generates complications on MARGINAL through FUMBLE. The narrator MUST:
- Describe all complications (do not soften, omit, or contradict)
- Narrate FAILURE/FUMBLE as failure (not success or silver linings)
- Reference harm when harm is dealt (injury, pain, condition worsening)
- End NPC interactions when patience hits 0 (no continued dialogue)
- Respect disposition bounds (no cooperation beyond NPC disposition cap)

## Anti-Patterns

- Power spectacle ("with a mighty blast...")
- Heroic framing of violence
- Interior monologue for the PC (never narrate what the PC thinks or feels)
- Adjectival pile-ups (pick one detail, maybe two)
- Exposition dumps (deliver background through action, inference, NPC speech)
- Data dumps (don't list every object, NPC, and exit in one block)
- Burying the lead (important info at the END, not the middle)
- Genre pastiche, irony, meta-commentary, consolation, moralizing
- "In a world where..." establishing cadence

## Dialogue Register by Faction

- **Iron Crown**: Military cadence. Minimal affect. Brief, precise.
- **Bourse**: Merchant-precise. Words chosen carefully. Contracts are real.
- **Central Jersey League**: Civic-academic. Warm-professional. Technical vocabulary.
- **Catskill Throne**: Terse. Preston speaks briefly. Officers follow suit.
- **Species I**: Spanish mixed with English. Elders speak with decades of authority.
- **Warped**: Tier-dependent. Higher tiers use idiosyncratic phrasings.

For full faction/species dialogue registers, see emergence/setting/narration.md.
For example vignettes, see [examples.md](examples.md).
