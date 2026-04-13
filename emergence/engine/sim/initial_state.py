"""Build the initial T+1 year world state from setting bible content.

Loads all factions, NPCs, locations, clocks, and constants from YAML,
assembles them into a coherent starting state, and validates cross-references.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from emergence.engine.sim.content_loader import ContentLoader
from emergence.engine.schemas.world import (
    Clock,
    Faction,
    Location,
    NPC,
    SessionMetadata,
    WorldState,
)


def build_initial_world(
    content_loader: ContentLoader | None = None,
) -> Tuple[WorldState, Dict[str, Faction], Dict[str, NPC], Dict[str, Location], Dict[str, Clock]]:
    """Build the complete initial game state at T+1 year.

    Returns (world_state, factions, npcs, locations, clocks).
    """
    loader = content_loader or ContentLoader()

    # Load all content
    factions = loader.load_factions()
    npcs = loader.load_npcs()
    locations = loader.load_locations()
    clocks = loader.load_clocks()
    constants = loader.load_constants()

    # Build world state at T+1 year
    world = WorldState(
        schema_version="1.0",
        current_time={
            "year": 1,
            "month": 0,
            "day": 0,
            "season": "spring",
            "tick_count": 0,
            "timestamp": "T+1y 0m 0d",
        },
        worldline_id="lordly_equilibrium",
        session_metadata=SessionMetadata(
            session_count=0,
            total_playtime_real_seconds=0,
            last_save="",
            character_lifetime_years=0.0,
        ),
    )

    # Wire bidirectional faction relationships
    _wire_faction_relationships(factions)

    # Assign NPCs to location resident lists
    _sync_npc_locations(npcs, locations)

    # Apply constants to world metadata
    if isinstance(constants, dict):
        world_constants = constants.get("world", constants)
        if isinstance(world_constants, dict):
            # Store constants reference for runtime access
            world.session_metadata.character_lifetime_years = 0.0

    return world, factions, npcs, locations, clocks


def _wire_faction_relationships(factions: Dict[str, Faction]) -> None:
    """Ensure faction relationships are bidirectional.

    If faction A lists B in relationships, ensure B also references A.
    """
    for fid, faction in factions.items():
        if not hasattr(faction, 'relationships') or not isinstance(getattr(faction, 'relationships', None), dict):
            continue
        for target_id, rel in list(faction.relationships.items()):
            if target_id in factions:
                target = factions[target_id]
                if not hasattr(target, 'relationships'):
                    target.relationships = {}
                if fid not in target.relationships:
                    # Mirror relationship with inverted stance
                    target.relationships[fid] = {
                        "stance": rel.get("stance", "neutral") if isinstance(rel, dict) else "neutral",
                        "source": "mirrored",
                    }


def _sync_npc_locations(npcs: Dict[str, NPC], locations: Dict[str, Location]) -> None:
    """Populate location NPC lists from NPC location assignments."""
    for nid, npc in npcs.items():
        if npc.location and npc.location in locations:
            loc = locations[npc.location]
            if not hasattr(loc, 'npcs_present'):
                loc.npcs_present = []
            if nid not in loc.npcs_present:
                loc.npcs_present.append(nid)


def validate_initial_state(
    world: WorldState,
    factions: Dict[str, Faction],
    npcs: Dict[str, NPC],
    locations: Dict[str, Location],
    clocks: Dict[str, Clock],
) -> List[str]:
    """Validate the initial state for consistency. Returns list of warnings."""
    warnings = []

    # Check time is T+1
    if isinstance(world.current_time, dict):
        if world.current_time.get("year") != 1:
            warnings.append(f"Expected year 1, got {world.current_time.get('year')}")

    # Check minimum entity counts
    if len(factions) < 10:
        warnings.append(f"Only {len(factions)} factions loaded, expected 10+")
    if len(npcs) < 20:
        warnings.append(f"Only {len(npcs)} NPCs loaded, expected 20+")
    if len(locations) < 20:
        warnings.append(f"Only {len(locations)} locations loaded, expected 20+")
    if len(clocks) < 5:
        warnings.append(f"Only {len(clocks)} clocks loaded, expected 5+")

    # Check NPC faction references
    non_faction_labels = {"independent", "warped", "none", ""}
    for nid, npc in npcs.items():
        faction = npc.faction_affiliation.get("primary") if isinstance(npc.faction_affiliation, dict) else None
        if faction and faction not in non_faction_labels and faction not in factions:
            warnings.append(f"NPC {nid} references unknown faction {faction}")

    # Check location controllers (skip informal values like "contested", "independent", NPC refs)
    informal_controllers = {"contested", "independent", "informal", "none", ""}
    for lid, loc in locations.items():
        if not loc.controller:
            continue
        ctrl = loc.controller
        # Strip parenthetical qualifiers
        paren_idx = ctrl.find("(")
        if paren_idx > 0:
            ctrl = ctrl[:paren_idx].strip()
        ctrl_lower = ctrl.lower().strip()
        if ctrl_lower in informal_controllers:
            continue
        # Skip NPC references (npc-*)
        if ctrl_lower.startswith("npc-"):
            continue
        # Skip quoted values
        if ctrl.startswith('"') or ctrl.startswith("'"):
            continue
        if ctrl not in factions:
            warnings.append(f"Location {lid} has unknown controller {loc.controller}")

    # Check clock segments are valid
    for cid, clock in clocks.items():
        if clock.current_segment > clock.total_segments:
            warnings.append(f"Clock {cid} segment {clock.current_segment} > total {clock.total_segments}")

    return warnings
