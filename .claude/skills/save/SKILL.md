---
name: save
description: Save the current Emergence game state
disable-model-invocation: true
allowed-tools: Bash(python3 -m emergence *)
---

Save the current Emergence game.

Run: `python3 -m emergence --save-root ./saves/default step save`

Confirm to the player when the save is complete, including the current character name and mode.
