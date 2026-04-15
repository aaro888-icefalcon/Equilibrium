"""Context management — compact world state for narrator payloads.

Produces a prioritized summary of world state that fits within token
budgets for narrator prompts. Prioritizes: current location, present
NPCs, active tensions, recent events.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Clock,
    Faction,
    Location,
    NPC,
    TickEvent,
    WorldState,
)


# ---------------------------------------------------------------------------
# Compaction
# ---------------------------------------------------------------------------

def compact_state(
    world: WorldState,
    player: Dict[str, Any],
    current_location: Location,
    npcs_present: List[NPC],
    factions: Dict[str, Faction],
    clocks: Dict[str, Clock],
    recent_events: List[TickEvent],
    max_items: int = 50,
) -> Dict[str, Any]:
    """Compact world state into a narrator-friendly dict.

    Prioritizes information closest to the player:
    1. Current location details
    2. Present NPCs (names, moods, relationships to player)
    3. Active tensions and dangers
    4. Recent significant events
    5. Relevant clock states
    6. Faction summaries
    """
    result: Dict[str, Any] = {}
    items = 0

    # 1. Time context
    result["time"] = {
        "date": world.current_time.get("in_world_date", ""),
        "season": current_location.ambient.season,
        "time_of_day": current_location.ambient.time_of_day,
    }
    items += 1

    # 2. Current location
    result["location"] = {
        "id": current_location.id,
        "name": current_location.display_name,
        "type": current_location.type,
        "controller": current_location.controller,
        "economic_state": current_location.economic_state,
        "threat_level": current_location.ambient.threat_level,
        "dangers": current_location.dangers[:3],
        "opportunities": current_location.opportunities[:3],
        "weather": current_location.ambient.weather,
    }
    items += 1

    # 3. Present NPCs
    npc_summaries: List[Dict[str, Any]] = []
    for npc in npcs_present[:5]:  # Cap at 5
        if items >= max_items:
            break
        summary: Dict[str, Any] = {
            "id": npc.id,
            "name": npc.display_name,
            "role": npc.role,
            "personality": npc.personality_traits[:3],
            "concerns": npc.current_concerns[:2],
        }
        # Player relationship
        player_rel = npc.relationships.get("player")
        if player_rel:
            summary["standing_with_player"] = player_rel.standing
            summary["relationship_state"] = player_rel.current_state
        else:
            summary["standing_with_player"] = npc.standing_with_player_default
        npc_summaries.append(summary)
        items += 1
    result["npcs_present"] = npc_summaries

    # 4. Recent events (most recent first)
    event_summaries: List[Dict[str, Any]] = []
    for event in reversed(recent_events[-10:]):
        if items >= max_items:
            break
        event_summaries.append({
            "type": event.event_type,
            "entity": event.entity_id,
            "details_summary": _summarize_details(event.details),
        })
        items += 1
    result["recent_events"] = event_summaries

    # 5. Relevant clocks (high progress only)
    clock_summaries: List[Dict[str, Any]] = []
    for clock_id, clock in clocks.items():
        if items >= max_items:
            break
        ratio = clock.current_segment / clock.total_segments if clock.total_segments > 0 else 0
        if ratio >= 0.5:  # Only show clocks past halfway
            clock_summaries.append({
                "name": clock.display_name,
                "progress": f"{clock.current_segment}/{clock.total_segments}",
                "urgency": "critical" if ratio >= 0.75 else "building",
            })
            items += 1
    result["active_clocks"] = clock_summaries

    # 6. Faction context (only factions relevant to current location)
    faction_summaries: List[Dict[str, Any]] = []
    relevant_factions = set()
    if current_location.controller:
        relevant_factions.add(current_location.controller)
    for npc in npcs_present:
        primary = npc.faction_affiliation.get("primary")
        if primary:
            relevant_factions.add(primary)

    for fid in relevant_factions:
        if items >= max_items:
            break
        faction = factions.get(fid)
        if faction:
            faction_summaries.append({
                "id": faction.id,
                "name": faction.display_name,
                "type": faction.type,
                "stance": faction.standing_with_player_default,
            })
            items += 1
    result["relevant_factions"] = faction_summaries

    # 7. Player summary
    result["player"] = {
        "heat": player.get("heat", {}).get("current", 0) if isinstance(player.get("heat"), dict) else player.get("heat", 0),
        "corruption": player.get("corruption", 0),
        "location": current_location.id,
    }

    return result


def _summarize_details(details: Dict[str, Any]) -> str:
    """One-line summary of event details."""
    parts: List[str] = []
    for key, val in list(details.items())[:3]:
        parts.append(f"{key}={val}")
    return ", ".join(parts) if parts else "no details"
