"""Tick engine — daily/seasonal simulation orchestrator.

Each daily tick runs in order:
1. Advance time
2. Tick clocks
3. Tick factions
4. Tick NPCs
5. Tick locations
6. Sync NPC presence
7. Collect and return all events

Seasonal ticks (every 90 days) run heavier processing:
faction rebalancing, economic recalculation, etc.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Clock,
    Faction,
    Location,
    NPC,
    TickEvent,
    WorldState,
)
from emergence.engine.sim.clocks import ClockEngine
from emergence.engine.sim.faction_logic import FactionDecisionEngine
from emergence.engine.sim.npc_behavior import NpcBehaviorEngine
from emergence.engine.sim.location_dynamics import LocationEngine


# ---------------------------------------------------------------------------
# TickEngine
# ---------------------------------------------------------------------------

class TickEngine:
    """Orchestrates daily and seasonal world ticks."""

    def __init__(self) -> None:
        self.clock_engine = ClockEngine()
        self.faction_engine = FactionDecisionEngine()
        self.npc_engine = NpcBehaviorEngine()
        self.location_engine = LocationEngine()

    def run_daily_tick(
        self,
        world: WorldState,
        factions: Dict[str, Faction],
        npcs: Dict[str, NPC],
        locations: Dict[str, Location],
        clocks: Dict[str, Clock],
        player: Optional[Dict[str, Any]],
        rng: random.Random,
    ) -> List[TickEvent]:
        """Run one daily tick. Returns all events produced."""
        events: List[TickEvent] = []

        # 1. Advance time
        day_count = world.current_time.get("day_count", 0) + 1
        world.current_time["day_count"] = day_count
        year = day_count // 365
        day_in_year = day_count % 365
        month = day_in_year // 30
        day = day_in_year % 30
        tick_ts = f"T+{year + 1}y {month}m {day}d"
        world.current_time["in_world_date"] = tick_ts
        world.current_time["year"] = year + 1

        # Build world_state context for sub-engines
        world_state: Dict[str, Any] = {
            "day_count": day_count,
            "tick_timestamp": tick_ts,
            "factions": {fid: f for fid, f in factions.items()},
            "clocks": clocks,
            "player": player,
        }

        # 2. Tick clocks
        clock_events = self.clock_engine.tick_clocks(
            clocks, world_state, rng, tick_ts
        )
        events.extend(clock_events)

        # 3. Tick factions
        for faction_id, faction in factions.items():
            faction_events = self.faction_engine.evaluate_faction_tick(
                faction, world_state, factions, rng, tick_ts
            )
            events.extend(faction_events)

        # 4. Tick NPCs
        for npc_id, npc in npcs.items():
            npc_events = self.npc_engine.evaluate_npc_tick(
                npc, world_state, rng, tick_ts
            )
            events.extend(npc_events)

        # 5. Tick locations
        for loc_id, loc in locations.items():
            loc_events = self.location_engine.evaluate_location_tick(
                loc, world_state, rng, tick_ts
            )
            events.extend(loc_events)

        # 6. Sync NPC presence
        self.location_engine.sync_npc_presence(locations, npcs)

        # 7. Check for seasonal tick
        if day_count > 0 and day_count % 90 == 0:
            seasonal_events = self.run_seasonal_tick(
                world, factions, npcs, locations, clocks, rng, tick_ts
            )
            events.extend(seasonal_events)

        return events

    def run_seasonal_tick(
        self,
        world: WorldState,
        factions: Dict[str, Faction],
        npcs: Dict[str, NPC],
        locations: Dict[str, Location],
        clocks: Dict[str, Clock],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Run heavier seasonal processing (every ~90 days).

        Currently handles:
        - Season cycling
        - Faction resource rebalancing
        """
        events: List[TickEvent] = []

        # Cycle seasons
        seasons = ["spring", "summer", "autumn", "winter"]
        day_count = world.current_time.get("day_count", 0)
        season_idx = (day_count // 90) % 4
        new_season = seasons[season_idx]

        for loc in locations.values():
            loc.ambient.season = new_season

        events.append(TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="environment",
            entity_id="world",
            event_type="season_change",
            details={"season": new_season},
            visibility="global",
        ))

        return events
