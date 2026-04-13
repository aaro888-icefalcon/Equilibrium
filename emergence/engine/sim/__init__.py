"""Emergence simulation engine — world tick, factions, NPCs, locations, clocks.

Phase 3 modules:
- yaml_parser: Minimal stdlib-only YAML subset parser
- clocks: Macro clock advancement engine
- faction_logic: Faction decision system
- npc_behavior: NPC schedule, goals, relationships, memory
- location_dynamics: Location economic/population/danger updates
- tick_engine: Daily/seasonal tick orchestrator
- situation_generator: Generate player-facing situations
- abstract_combat: Off-screen combat resolution
- encounter_generator: Build EncounterSpec from situation
- player_actions: Resolve player choices in situations
- context_management: Compact world state for narrator payloads
- persistence: Dirty-flag tracking for incremental saves
"""
