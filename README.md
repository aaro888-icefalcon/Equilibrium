# Emergence

A solo AI-narrated tactical RPG and life simulation set one year after the Onset -- a catastrophic event that killed most of humanity and left survivors with supernatural abilities.

## Overview

Emergence is a complete game engine built in Python 3.10+ with no external dependencies. The engine handles all mechanics (combat, simulation, progression, persistence) while Codex acts as the narrator, transforming structured game payloads into grounded, tactile prose.

The game runs inside a Codex session. Type `/play` to start.

## Requirements

- Python 3.10 or later
- Codex (CLI, IDE, desktop, or web)
- No pip install needed -- stdlib only

## Quick Start

1. Open this repository in Codex
2. Type `/play` to start or resume a game
3. Follow the narrator's lead

## Project Structure

```
emergence/
  __main__.py          CLI entry point
  PLAY.md              Player-facing instructions
  HANDOFF.md           Technical reference
  engine/              Game engine (~15K lines)
    schemas/           Data structures and validation
    combat/            Turn-based combat system
    sim/               World simulation engine
    character_creation/ Session zero (10-scene character creation)
    narrator/          Payload builders and prompt templates
    persistence/       Save/load system
    progression/       Character advancement systems
    runtime/           Game loop and step CLI
  data/                Powers, enemies, encounters (JSON)
  setting/             World bible (YAML + Markdown)
  specs/               Design specifications
  tests/               898 tests (unit, integration, regression, scenario)
```

## Documentation

- [How to Play](emergence/PLAY.md) -- player-facing guide
- [Technical Handoff](emergence/HANDOFF.md) -- architecture and module reference
- [Design Brief](emergence/specs/design-brief.md) -- game design philosophy

## Testing

```bash
python3 -m pytest emergence/tests/ -q
```
