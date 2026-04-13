"""Location dynamics engine — evaluates location changes each daily tick.

Each tick, a location may experience:
- Economic transitions (sufficient → strained → crisis → collapsed)
- Population shifts (migration in/out based on conditions)
- Controller changes (faction takeover, abandonment)
- Danger escalation/de-escalation
- Opportunity generation
- NPC presence synchronization
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import Location, NPC, TickEvent


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ECONOMIC_STATES = ["thriving", "sufficient", "strained", "crisis", "collapsed"]

# Daily probability of economic state change
_ECONOMIC_SHIFT_PROB = 0.02  # ~once per 50 days

# Daily probability of danger escalation
_DANGER_ESCALATION_PROB = 0.03

# Daily probability of new opportunity
_OPPORTUNITY_GENERATION_PROB = 0.02

# Population change per migration event
_MIGRATION_AMOUNT_RANGE = (5, 50)


# ---------------------------------------------------------------------------
# LocationEngine
# ---------------------------------------------------------------------------

class LocationEngine:
    """Evaluates location dynamics each tick and produces TickEvents."""

    def evaluate_location_tick(
        self,
        location: Location,
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Run one tick for a location. Returns events."""
        events: List[TickEvent] = []

        # 1. Economic state transitions
        econ_event = self._evaluate_economic_shift(location, world_state, rng, tick_timestamp)
        if econ_event:
            events.append(econ_event)

        # 2. Population migration
        pop_event = self._evaluate_migration(location, world_state, rng, tick_timestamp)
        if pop_event:
            events.append(pop_event)

        # 3. Danger escalation/de-escalation
        danger_event = self._evaluate_danger(location, rng, tick_timestamp)
        if danger_event:
            events.append(danger_event)

        # 4. Opportunity generation
        opp_event = self._evaluate_opportunities(location, rng, tick_timestamp)
        if opp_event:
            events.append(opp_event)

        # Store last updates
        location.last_tick_updates = [e.to_dict() for e in events]
        return events

    # ── Economic ──────────────────────────────────────────────────────

    def _evaluate_economic_shift(
        self,
        location: Location,
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> Optional[TickEvent]:
        if rng.random() >= _ECONOMIC_SHIFT_PROB:
            return None

        idx = _ECONOMIC_STATES.index(location.economic_state) if location.economic_state in _ECONOMIC_STATES else 1

        # Determine direction: worsen if dangers present or no controller,
        # improve if controller present and no dangers
        if location.dangers or location.controller is None:
            direction = 1  # worsen
        elif location.controller and not location.dangers:
            direction = -1  # improve
        else:
            direction = rng.choice([-1, 1])

        new_idx = max(0, min(len(_ECONOMIC_STATES) - 1, idx + direction))
        if new_idx == idx:
            return None

        old_state = location.economic_state
        location.economic_state = _ECONOMIC_STATES[new_idx]

        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="location",
            entity_id=location.id,
            event_type="economic_shift",
            details={
                "from": old_state,
                "to": location.economic_state,
                "direction": "worsened" if direction > 0 else "improved",
            },
            visibility="regional",
        )

    # ── Migration ─────────────────────────────────────────────────────

    def _evaluate_migration(
        self,
        location: Location,
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> Optional[TickEvent]:
        # Migration triggered by economic state
        if location.economic_state in ("crisis", "collapsed"):
            # People leave
            if location.population > 0 and rng.random() < 0.1:
                amount = min(
                    location.population,
                    rng.randint(*_MIGRATION_AMOUNT_RANGE)
                )
                location.population -= amount
                return TickEvent(
                    tick_timestamp=tick_timestamp,
                    entity_type="location",
                    entity_id=location.id,
                    event_type="population_exodus",
                    details={
                        "amount": amount,
                        "new_population": location.population,
                        "reason": location.economic_state,
                    },
                )
        elif location.economic_state in ("thriving", "sufficient"):
            # People arrive
            if rng.random() < 0.03:
                amount = rng.randint(*_MIGRATION_AMOUNT_RANGE)
                location.population += amount
                return TickEvent(
                    tick_timestamp=tick_timestamp,
                    entity_type="location",
                    entity_id=location.id,
                    event_type="population_influx",
                    details={
                        "amount": amount,
                        "new_population": location.population,
                    },
                )
        return None

    # ── Danger ────────────────────────────────────────────────────────

    def _evaluate_danger(
        self,
        location: Location,
        rng: random.Random,
        tick_timestamp: str,
    ) -> Optional[TickEvent]:
        if rng.random() >= _DANGER_ESCALATION_PROB:
            return None

        # Escalate: add a new danger or increase threat level
        if location.ambient.threat_level < 5 and (location.dangers or rng.random() < 0.3):
            location.ambient.threat_level += 1
            return TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="location",
                entity_id=location.id,
                event_type="danger_escalation",
                details={
                    "new_threat_level": location.ambient.threat_level,
                    "dangers": list(location.dangers),
                },
            )
        elif location.ambient.threat_level > 0 and not location.dangers:
            # De-escalate
            location.ambient.threat_level -= 1
            return TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="location",
                entity_id=location.id,
                event_type="danger_deescalation",
                details={
                    "new_threat_level": location.ambient.threat_level,
                },
            )
        return None

    # ── Opportunities ─────────────────────────────────────────────────

    _OPPORTUNITY_TYPES = [
        "salvage_cache", "trade_caravan", "information_broker",
        "medical_supplies", "refugee_group", "faction_contact",
        "abandoned_tech", "safe_passage",
    ]

    def _evaluate_opportunities(
        self,
        location: Location,
        rng: random.Random,
        tick_timestamp: str,
    ) -> Optional[TickEvent]:
        if rng.random() >= _OPPORTUNITY_GENERATION_PROB:
            return None

        # Cap opportunities at 3 per location
        if len(location.opportunities) >= 3:
            return None

        opportunity = rng.choice(self._OPPORTUNITY_TYPES)
        location.opportunities.append(opportunity)

        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="location",
            entity_id=location.id,
            event_type="opportunity_appeared",
            details={"opportunity": opportunity},
        )

    # ── NPC sync ──────────────────────────────────────────────────────

    def sync_npc_presence(
        self,
        locations: Dict[str, Location],
        npcs: Dict[str, NPC],
    ) -> None:
        """Update each location's npcs_present based on NPC locations."""
        # Clear all presence lists
        for loc in locations.values():
            loc.npcs_present = []
        # Repopulate
        for npc in npcs.values():
            if npc.status == "alive" and npc.location in locations:
                locations[npc.location].npcs_present.append(npc.id)

    # ── Controller change ─────────────────────────────────────────────

    def change_controller(
        self,
        location: Location,
        new_controller: Optional[str],
        reason: str,
        tick_timestamp: str,
    ) -> TickEvent:
        """Change a location's controlling faction."""
        old = location.controller
        location.controller = new_controller
        location.history.append({
            "date": tick_timestamp,
            "event": "controller_change",
            "from": old,
            "to": new_controller,
            "reason": reason,
        })
        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="location",
            entity_id=location.id,
            event_type="controller_change",
            details={
                "from": old,
                "to": new_controller,
                "reason": reason,
            },
            visibility="global",
        )
