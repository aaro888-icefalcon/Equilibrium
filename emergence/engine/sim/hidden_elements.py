"""Hidden elements — unrevealed information available for narration and complications.

Populates a pool of "things the narrator knows but the player hasn't seen yet"
from:
- NPC knowledge entries where will_share_if conditions aren't met
- Location dangers and opportunities the player hasn't observed
- Recent tick events with visibility != "player_seen"
- Clocks approaching completion (ratio >= 0.5)
- Faction current schemes

Used by:
1. Narrator — seed as foreshadowing / atmospheric texture
2. Complication generator — draw from pool when "reveal_unwelcome_truth"
   or "announce_offscreen_badness" fires
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Location,
    NPC,
    Clock,
    TickEvent,
)


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class HiddenElement:
    """An unrevealed piece of information."""
    source_type: str            # npc_knowledge, location_danger, tick_event, clock_state, world_state
    source_id: str              # ID of the source entity
    content: str                # Human-readable detail
    priority: int = 3           # 1-5, higher = more important
    tags: List[str] = field(default_factory=list)  # For matching to complications

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "content": self.content,
            "priority": self.priority,
            "tags": self.tags,
        }


# ---------------------------------------------------------------------------
# Gathering functions
# ---------------------------------------------------------------------------

def _gather_npc_knowledge(npcs: List[NPC]) -> List[HiddenElement]:
    """Pull NPC knowledge entries that the player hasn't heard yet."""
    elements: List[HiddenElement] = []
    for npc in npcs:
        for k in getattr(npc, "knowledge", []):
            # Skip if no content
            if not getattr(k, "detail", ""):
                continue
            # Priority: higher for NPCs with higher standing (they have more reason to share)
            priority = 3
            standing = getattr(npc, "standing_with_player_default", 0)
            if standing >= 2:
                priority = 4
            elif standing <= -1:
                priority = 2  # Hostile NPCs' secrets are more valuable but less accessible

            elements.append(HiddenElement(
                source_type="npc_knowledge",
                source_id=npc.id,
                content=f"{npc.display_name} knows: {k.detail}",
                priority=priority,
                tags=["npc_secret", k.topic],
            ))
    return elements


def _gather_location_info(location: Location) -> List[HiddenElement]:
    """Pull location dangers and opportunities not yet observed."""
    elements: List[HiddenElement] = []

    for danger in getattr(location, "dangers", []):
        elements.append(HiddenElement(
            source_type="location_danger",
            source_id=location.id,
            content=f"Danger at {location.display_name}: {danger}",
            priority=4,
            tags=["danger", "location"],
        ))

    for opp in getattr(location, "opportunities", []):
        elements.append(HiddenElement(
            source_type="location_opportunity",
            source_id=location.id,
            content=f"Opportunity at {location.display_name}: {opp}",
            priority=3,
            tags=["opportunity", "location"],
        ))

    # Current events at location
    for event in getattr(location, "current_events", []):
        elements.append(HiddenElement(
            source_type="location_event",
            source_id=location.id,
            content=f"At {location.display_name}: {event}",
            priority=3,
            tags=["event", "location"],
        ))

    return elements


def _gather_tick_events(events: List[TickEvent]) -> List[HiddenElement]:
    """Pull recent tick events the player may not have encountered."""
    elements: List[HiddenElement] = []
    for ev in events[-10:]:  # Last 10 events
        visibility = getattr(ev, "visibility", "local")
        if visibility == "global":
            priority = 4
        elif visibility == "local":
            priority = 3
        else:
            priority = 2

        details = getattr(ev, "details", {})
        if isinstance(details, dict):
            display = details.get("display_name") or details.get("description", "")
        else:
            display = str(details)

        if not display:
            continue

        elements.append(HiddenElement(
            source_type="tick_event",
            source_id=getattr(ev, "entity_id", ""),
            content=f"Elsewhere: {display}",
            priority=priority,
            tags=[getattr(ev, "event_type", ""), "world_event"],
        ))
    return elements


def _gather_clock_states(clocks: Dict[str, Clock]) -> List[HiddenElement]:
    """Pull clocks approaching completion."""
    elements: List[HiddenElement] = []
    for clock_id, clock in clocks.items():
        if clock.total_segments <= 0:
            continue
        ratio = clock.current_segment / clock.total_segments
        if ratio >= 0.5:
            display = getattr(clock, "display_name", clock_id)
            priority = 5 if ratio >= 0.75 else 4
            elements.append(HiddenElement(
                source_type="clock_state",
                source_id=clock_id,
                content=(
                    f"{display} is "
                    f"{clock.current_segment}/{clock.total_segments} "
                    "complete."
                ),
                priority=priority,
                tags=["clock", "approaching"],
            ))
    return elements


def _gather_faction_schemes(factions: Dict[str, Any]) -> List[HiddenElement]:
    """Pull faction schemes and secret information."""
    elements: List[HiddenElement] = []
    for faction_id, faction in factions.items():
        # Faction might be a dict or an object
        if isinstance(faction, dict):
            schemes = faction.get("current_schemes", [])
            name = faction.get("display_name", faction_id)
        else:
            schemes = getattr(faction, "current_schemes", [])
            name = getattr(faction, "display_name", faction_id)

        for scheme in schemes[:2]:  # Top 2 schemes per faction
            if isinstance(scheme, dict):
                desc = scheme.get("description", "")
            else:
                desc = str(scheme)
            if not desc:
                continue
            elements.append(HiddenElement(
                source_type="faction_scheme",
                source_id=faction_id,
                content=f"{name} is pursuing: {desc}",
                priority=3,
                tags=["faction", "scheme"],
            ))
    return elements


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def gather_hidden_elements(
    location: Location,
    npcs_present: List[NPC],
    recent_events: List[TickEvent],
    clocks: Dict[str, Clock],
    factions: Optional[Dict[str, Any]] = None,
    player: Optional[Dict[str, Any]] = None,
) -> List[HiddenElement]:
    """Gather hidden elements from all sources.

    Returns list sorted by priority (highest first).
    """
    elements: List[HiddenElement] = []

    elements.extend(_gather_npc_knowledge(npcs_present))
    elements.extend(_gather_location_info(location))
    elements.extend(_gather_tick_events(recent_events))
    elements.extend(_gather_clock_states(clocks))

    if factions:
        elements.extend(_gather_faction_schemes(factions))

    # Sort by priority descending
    elements.sort(key=lambda e: e.priority, reverse=True)

    return elements
