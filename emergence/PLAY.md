# Emergence -- How to Play

A solo AI-narrated tactical RPG and life simulation set one year after the Onset -- a catastrophic event that killed most of humanity and left survivors with supernatural abilities.

---

## Requirements

- Python 3.10 or later (tested on 3.11)
- No external dependencies -- stdlib only

---

## Quick Start

```bash
# From the repository root:
python -m emergence play
```

This launches a new session. If no save exists, you enter Session Zero (character creation). If a save exists, play resumes where you left off.

---

## Subcommands

| Command | Description |
|---------|-------------|
| `play` | Start or resume a session (default) |
| `new` | Create a new character (enters Session Zero) |
| `list` | List saves and archived characters |
| `inspect` | Validate and report on save state |
| `migrate` | Run save migrations to latest schema |
| `help` | Print usage |

### Examples

```bash
python -m emergence play                   # Resume or start new
python -m emergence new                    # Force new character
python -m emergence list                   # Show all characters
python -m emergence inspect                # Validate save files
python -m emergence migrate                # Upgrade old saves
```

---

## Global Options

| Option | Default | Description |
|--------|---------|-------------|
| `--save-root PATH` | `./saves/default` | Save directory (or set `EMERGENCE_SAVE_ROOT` env var) |
| `--config PATH` | `./config/emergence.toml` | Config file path (or set `EMERGENCE_CONFIG` env var) |
| `--log-level LEVEL` | `info` | Logging: `debug`, `info`, `warn`, `error` |
| `--log-file PATH` | `{save-root}/logs/runtime.log` | Log file destination |
| `--no-color` | off | Suppress ANSI color output |
| `--seed N` | random | Override RNG seed for deterministic replay |
| `--dry-run` | off | Validate and print launch plan without modifying save |

### Play Options

| Option | Description |
|--------|-------------|
| `--character NAME` | Switch to a specific archived character |
| `--resume` | Force resume from existing save |
| `--skip-session-zero` | Dev/testing: skip character creation, use template |

---

## Session Zero -- Character Creation

When you start a new game, you go through Session Zero: a 10-scene guided character creation that builds your character through narrative choices. Each choice shapes who your character was before the Onset and who they are becoming after it.

### The Ten Scenes

**Pre-Onset (Scenes 0-4)**

| Scene | What Happens | What You Choose |
|-------|-------------|-----------------|
| 0. Opening | Set the frame | Your name and age at the Onset (16-65) |
| 1. Occupation | What you did before | One of 12 occupations (soldier, doctor, farmer, etc.) |
| 2. Relationships | Who matters to you | A key relationship (spouse, parent, child, sibling, friend, mentor) and their fate |
| 3. Location | Where you were | One of 8 regions and your circumstance during the Onset |
| 4. Concern | What weighed on you | One of 8 pre-Onset concerns (money, family illness, legal trouble, etc.) |

**Manifestation (Scene 5)**

Your powers manifest. The category (physical kinetic, perceptual mental, matter energy, biological vital, auratic, temporal spatial, or eldritch corruptive) is weighted by your circumstances. Your tier (T1-T4) is rolled with modifiers from your background. You pick your starting power(s).

**Year One (Scenes 6-9)**

| Scene | What Happens | What You Choose |
|-------|-------------|-----------------|
| 6. First Weeks | Surviving the aftermath | How you spent the first three weeks |
| 7. Faction Encounter | The local power finds you | How you responded to the faction controlling your area |
| 8. Critical Incident | Something breaks | A defining crisis -- type depends on your corruption, heat, and prior choices |
| 9. Settling In | Finding your place | Where and how you're living one year after the Onset |

Every choice grants attributes, skills, resources, relationships, and narrative hooks. No two characters play the same.

---

## Game Modes

Play cycles through four modes:

### Framing

A scene-setting narration establishes where you are, who is present, and what tensions are active. This transitions you into the main simulation.

### Simulation

The core gameplay loop. The world advances day by day. Factions maneuver, NPCs pursue their goals, locations change, and macro clocks tick forward. You are presented with situations -- moments of tension or opportunity -- and choose how to respond.

Choices include dialogue, travel, activities, and observation. Some choices trigger combat encounters.

### Combat

Turn-based tactical encounters. You and your enemies trade actions across terrain zones. Each round you choose a major action (Attack, Power, Maneuver, Parley, Disengage, Finisher, Defend) and a minor action (Assess or quick maneuver).

**Key concepts:**
- **Condition tracks** -- Physical, mental, and social damage accumulate. Getting incapacitated ends the fight.
- **Status effects** -- Exposed, Marked, Shaken, Stunned, Bleeding, Burning, Corrupted. Each changes what you can do and what can be done to you.
- **Momentum** -- Build it through successful actions. At 5+ momentum against an Exposed enemy, you can attempt a Finisher.
- **Registers** -- Combat behaves differently depending on who you fight: humans (heat and witnesses), creatures (ecological clock and escalation), or eldritch entities (attention clock and corruption).
- **Heat** -- Violence has consequences. Killing earns more heat than incapacitating. Witnesses multiply it. Parley reduces it. Heat follows you into the simulation.

After combat resolves (victory, defeat, escape, or parley), you return to the simulation with consequences applied.

### Game Over

When your character dies (combat, aging, corruption transformation), you may continue as a descendant if one exists, or start fresh.

---

## In-Game Commands

During play, type these at any prompt:

| Command | Shortcut | Description |
|---------|----------|-------------|
| `/help` | | Show available commands |
| `/save` | | Save current game state |
| `/quit` | `/exit` | Save and exit |
| `/status` | | Display character and world status |
| `/character` | `/char` | Show your character sheet |
| `/inventory` | `/inv` | Show your inventory and resources |
| `/map` | | Show your current location and region |
| `/history` | | Show recent events |

### Making Choices

When presented with numbered choices, enter the number (1, 2, 3...) or the corresponding letter (a, b, c...). When prompted for freeform input (like your character's name), just type normally.

---

## Progression

Your character grows through play, not through menus.

### Power Strengthening

Using your powers in combat earns strengthening marks at thresholds (25, 75, 200, 500, 1200 uses). Each mark makes the power more effective. At your tier ceiling, the final threshold doubles.

### Breakthroughs

Extraordinary circumstances can trigger a breakthrough -- a permanent tier increase. Eight possible triggers exist: near-death experience, sustained mentorship, eldritch exposure, substance use, group ritual, traumatic loss, prolonged crisis, and personal sacrifice. Breakthroughs are rare, consequential, and come with recovery periods.

### Skills

32 skills across 7 clusters improve through use. Thresholds: 5, 20, 60, 150, 350, 750, 1500, 3000, 7000, 15000 uses for 10 proficiency levels. Some skills have prerequisites (surgery requires first aid proficiency 4+) and synergies (literacy boosts history and languages).

### Relationships

NPCs have standing (-3 to +3) and trust (0 to 5) with you. Relationships evolve through interaction: neutral becomes warm becomes trusted becomes loyal. Betrayal locks standing at -3 for 60 days. Absence causes decay. NPC death is permanent and hits hard.

### Factions

Faction standing (-3 to +3), reach (0 to 5), and heat track your relationship with the 22 factions. Standing decays over time without reinforcement. Heat has a permanent floor.

### Resources

Seven resource types: currency units (cu), scrip, crown chits, grain, pharmaceuticals, trade goods, and ammunition. Some decay over time (grain rots, scrip inflates). Followers and holdings require upkeep.

### Aging

Characters age. Attributes degrade at decade boundaries (40, 50, 60). Past 60, an annual death check runs. Life expectancy in this world is 42 years. High corruption and poor health make death more likely.

### Family

Characters can have partners and children. Children may manifest powers between ages 12-18. When your character dies, you can continue as a manifested descendant who inherits half your resources, significant relationships, and your lineage.

### Corruption

Using eldritch powers, bargaining with entities, or exposure to the wrong things accumulates corruption on a 0-6 scale. Low corruption is cosmetic. Moderate corruption has mechanical effects. High corruption (5) halts aging but caps faction standing and imposes will checks. Corruption 6 is transformation -- your character is gone. Reversal is possible at low levels, difficult at moderate levels, and impossible at 6.

---

## Save Management

The game auto-saves every 10 minutes. Use `/save` for manual saves. Save files are stored in the save root directory (default: `./saves/default/`).

**Save structure:**
```
saves/default/
  world.json           # World state (written last -- marks save as complete)
  player/
    character.json     # Active character
    archive/           # Archived characters
  factions.json
  npcs.json
  locations.json
  clocks.json
  metadata.json
```

### Multiple Characters

One world can hold multiple characters. When a character dies or you switch, the previous character is archived. Use `python -m emergence play --character NAME` to switch.

### Save Classification

| State | Meaning |
|-------|---------|
| FRESH | No save data -- new game |
| VALID | Clean save -- resumable |
| PARTIAL | Interrupted save -- recoverable |
| CORRUPT | Damaged save data |
| VERSION_MISMATCH | Save from different schema version -- run `migrate` |

---

## Tips

- **Explore your powers.** Using them earns strengthening marks. Varied use across your category unlocks category bonuses.
- **Build relationships.** Loyal NPCs offer real advantages. Betrayed ones become permanent enemies.
- **Watch your heat.** Every faction tracks what you do. Violence escalates. Parley de-escalates. Witnesses multiply consequences.
- **Manage corruption carefully.** Small amounts are cosmetic. The scale from 3 onward is increasingly hard to reverse. 6 is permanent.
- **Plan for mortality.** Your character will die. A prepared descendant inherits your legacy. An unprepared death means starting over.
- **Save before risky choices.** Autosave helps, but manual `/save` before a dangerous encounter is wise.
- **Pay attention to clocks.** The world's macro clocks drive major events. When a clock completes, things change permanently.

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Clean exit |
| 1 | General error |
| 2 | Fatal error |
| 3 | Save integrity error |
| 4 | Narrator protocol error |
| 5 | Engine internal error |

---

## Troubleshooting

**"Launch lock exists"** -- Another session is running, or a previous session crashed. Lock files older than 1 hour are automatically treated as stale. Delete `saves/default/.lock` if you're sure no other session is active.

**"Save integrity error"** -- Run `python -m emergence inspect` to diagnose. If corrupt, you may need to restore from a backup or start fresh.

**"Version mismatch"** -- Run `python -m emergence migrate` to upgrade your save to the current schema version. Use `--dry-run` first to preview changes.
