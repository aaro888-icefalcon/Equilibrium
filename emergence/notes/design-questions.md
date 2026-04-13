# Design Questions — Emergence

## DQ-001: Missing sim-architecture.md

The README references `sim-architecture.md` with 11 sections (tick engine, faction logic, NPC behavior, location dynamics, clocks, situation generator, abstract combat, persistence, context management, player actions, encounter generator). This file was not provided.

**Resolution:** Will construct simulation engine implementation from design-brief.md (simulation layer description), interface-spec.md (World State, Faction, NPC, Location, Clock, Tick Event, Situation schemas), gm-primer.md (detailed world simulation guidance), and other specs that reference sim behavior. Key sections of the design brief describe tick-based simulation, faction decision-making, NPC schedules/goals/memory, and situation generation.

## DQ-002: Missing sim-content-integration.md

The README references `sim-content-integration.md` with at least 7 sections covering content loading and T+1 initial world state. This file was not provided.

**Resolution:** Will construct content integration from the setting bible files (factions.yaml, npcs.yaml, locations.yaml, clocks.yaml, timeline.yaml, constants.yaml) and the interface spec schemas. T+1 world state construction will follow the worldline described in trajectory.md and the constants in constants.yaml.
