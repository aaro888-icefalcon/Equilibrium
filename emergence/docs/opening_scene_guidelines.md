# Opening Scene Guidelines (Media Res)

For the narrator authoring the opening scene of Session Zero — the scene that
drops the player into their urgent quest after the bridge narrative ends.

---

## The three-questions test

After reading the opening scene, the player must be able to state — in their
own words, without being told mechanically — three things:

1. **What am I trying to do?** (the goal)
2. **What happens if I fail?** (the primary Bright Line)
3. **What's running out?** (the macrostructure)

If a reader can't answer all three from your prose, the scene is a setup,
not a hook. Rewrite.

---

## Structure

The opening scene is a **frozen tableau** at the moment the quest becomes
active. Follow Sensation → Information → Invitation:

1. **Sensation** (40-70 words). Lead with the sense that matters most for this
   moment. Specific nouns, not abstractions.
2. **Information** (60-120 words). What the PC infers. Seed the goal, the
   Bright Line telegraph, the macrostructure indicator. Name the proxy
   antagonist or their proxy (a watcher, a messenger, a distant fire).
3. **Invitation** (30-60 words). End on what invites action. Not a numbered
   list of choices. A decision point that the player can answer in their own
   words.

**Total: 150-300 words.** Tight envelope.

---

## Required elements (engine-validated)

The opening-scene payload must reference, by id or by name where relevant:

- `primary_quest_id` — the urgent quest being dramatized
- `antagonist_id` — the proxy antagonist (NPC or faction)
- `hook_npc_id` — the NPC whose fate anchors the PC's stake (may be the
  antagonist or the target; always in frame)
- `location_id` — where the scene is
- `telegraph_bright_line_id` — which Bright Line the scene telegraphs
  (usually the one most immediately threatening)

If any of these are missing, the validator returns the scene for rewrite.

---

## Dramatizing each quest element

### The goal

Make the goal object (or its proxy) palpable. Varin, not "the target." The
sealed packet, not "the cargo." The player should see, hear, or be holding
the thing they're trying to deliver / protect / retrieve.

### The Bright Line

The telegraph_text is your handle. Weave it into the scene — a distant bell,
a ledger line closing, a rival's caravan visible at the horizon. The player
must see the thing that will end them if they stall.

### The macrostructure

Show the clock, don't say it. A bell tower. The tide. A shift change. A
patrol cycle. A watch fire that will burn out. The player should sense the
time pressure as environmental fact, not as a narrator aside.

### The antagonist

The proxy antagonist appears in frame or just off-stage. A name, a sigil, a
voice. Not the full agenda — that comes from play. But the player must
understand *someone is pushing back on this*.

### The hook

Why this PC, not any PC? The hook is the personal stake — usually an NPC
from the pre-emergence or job bundle whose welfare rides on this quest. They
should be in view or invoked directly.

---

## The invitation

The scene ends on an open question. Not "what do you do?" — too lazy. A
specific moment of choice that the player can answer by declaring intent.

Examples:

> *Varin's hand closes around yours. The bell down the avenue rings the half-hour.*

> *The packet sits on the counter between you. Across the room, Volk's man has
> not moved, has not looked at you, has not stopped smiling.*

> *The map folds closed under your fingers. Outside, someone is tuning a horse.*

---

## Background quest name-dropping

The bridge narrative that ends in the opening scene should reference the four
background quests by the pressures they apply to the PC — not by name, not
as a checklist. A line about a debt still unpaid. A note the player left
themselves about a rumor they have not run down. A letter on the table that
they have not yet opened.

The player doesn't need to hold all four in working memory. But they should
know these pressures exist so that when they come to the surface later in
play, the reveal has weight.

---

## Register and voice

Register comes from the quest's `hook_scene.inciting_event` and the PC's
pre-emergence classifier output. For Emergence specifically:

- No meta-gaming language (never: hit points, XP, level up, dice roll, d20)
- No AI-assistant voice
- Violence has weight; powers are physical facts, not spectacle
- Never speak for the PC's interior — describe what they see, what they
  hear, what they notice

See `emergence/setting/narration.md` for the full style guide.

---

## What to avoid

- **Numbered choice lists.** Players declare freely.
- **Softened Bright Lines.** If the telegraph is a distant bell, don't also
  write "but the bell hasn't rung yet and might not." Let the tension stand.
- **Exposition dumps.** The bridge narrative did the summary; the scene is
  the present moment.
- **Introducing new quests mid-scene.** All five quests were fixed by the
  time the opening scene runs. A new hook surfacing in frame is fine; a new
  quest binding is not.
- **Off-screen resolution.** The scene must leave the quest unresolved. The
  invitation is for the player's first move, not a foregone conclusion.
