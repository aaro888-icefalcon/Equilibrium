---
name: new-game
description: Start a new Emergence game with a fresh character
disable-model-invocation: true
allowed-tools: Bash(python3 -m emergence *)
---

Start a new Emergence game. $ARGUMENTS

1. Check if a save already exists: `python3 -m emergence --save-root ./saves/default step status`
2. If a save exists, warn the player that starting a new game will overwrite it. Ask for confirmation.
3. If confirmed (or no save exists): `python3 -m emergence --save-root ./saves/default step init --force`
4. Begin Session Zero using the /play skill flow.
