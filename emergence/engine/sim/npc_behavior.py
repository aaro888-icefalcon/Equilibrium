"""NPC behavior engine — evaluates NPC actions each daily tick.

Each tick an NPC may:
- Follow their schedule (time-of-day based location)
- Pursue active goals
- Update relationships (drift, events)
- Decay old memories
- Change status (alive, displaced, missing)
- Move to a new location based on goals/schedule/events
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    NPC,
    NpcMemory,
    NpcRelationshipState,
    TickEvent,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Daily probability of an NPC taking a notable action
_ACTION_PROBABILITY = 1.0 / 5.0  # ~once every 5 days

# Memory decay: emotional_weight decreases by decay_rate per tick
_MIN_EMOTIONAL_WEIGHT = 0

# Relationship drift: standings drift toward 0 slowly
_RELATIONSHIP_DRIFT_PROB = 0.02  # ~once per 50 days


# ---------------------------------------------------------------------------
# NpcBehaviorEngine
# ---------------------------------------------------------------------------

class NpcBehaviorEngine:
    """Evaluates NPC behavior each tick and produces TickEvents."""

    def evaluate_npc_tick(
        self,
        npc: NPC,
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Run one tick for an NPC. Returns events."""
        if npc.status != "alive":
            return []

        events: List[TickEvent] = []

        # 1. Memory decay (always runs)
        self._decay_memories(npc)

        # 2. Relationship drift (low probability)
        events.extend(self._drift_relationships(npc, rng, tick_timestamp))

        # 3. Schedule evaluation — move if needed
        schedule_event = self._evaluate_schedule(npc, world_state, tick_timestamp)
        if schedule_event:
            events.append(schedule_event)

        # 4. Notable action (goal pursuit, concern response)
        if rng.random() < _ACTION_PROBABILITY:
            action_events = self._take_action(npc, world_state, rng, tick_timestamp)
            events.extend(action_events)

        return events

    # ── Memory ────────────────────────────────────────────────────────

    def _decay_memories(self, npc: NPC) -> None:
        """Decay emotional weight of all memories. Remove forgotten ones."""
        surviving: List[NpcMemory] = []
        for mem in npc.memory:
            mem.emotional_weight = max(
                _MIN_EMOTIONAL_WEIGHT,
                mem.emotional_weight - mem.decay_rate,
            )
            # Keep memories with any emotional weight
            if mem.emotional_weight > 0:
                surviving.append(mem)
        npc.memory = surviving

    # ── Relationships ─────────────────────────────────────────────────

    def _drift_relationships(
        self,
        npc: NPC,
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Slowly drift relationship standings toward 0."""
        events: List[TickEvent] = []
        for entity_id, rel in npc.relationships.items():
            if abs(rel.standing) >= 2 and rng.random() < _RELATIONSHIP_DRIFT_PROB:
                old = rel.standing
                if rel.standing > 0:
                    rel.standing -= 1
                elif rel.standing < 0:
                    rel.standing += 1
                events.append(TickEvent(
                    tick_timestamp=tick_timestamp,
                    entity_type="npc",
                    entity_id=npc.id,
                    event_type="relationship_drift",
                    details={
                        "target": entity_id,
                        "old_standing": old,
                        "new_standing": rel.standing,
                    },
                ))
        return events

    # ── Schedule ──────────────────────────────────────────────────────

    def _evaluate_schedule(
        self,
        npc: NPC,
        world_state: Dict[str, Any],
        tick_timestamp: str,
    ) -> Optional[TickEvent]:
        """Check if NPC should move based on their schedule."""
        if not npc.schedule:
            return None

        # Schedule format: {"default": "location_id", "patrol": ["loc1", "loc2"], ...}
        default_loc = npc.schedule.get("default", "")
        patrol_route = npc.schedule.get("patrol", [])

        if patrol_route:
            # Cycle through patrol locations based on day
            day = world_state.get("day_count", 0)
            target = patrol_route[day % len(patrol_route)]
        elif default_loc:
            target = default_loc
        else:
            return None

        if target != npc.location:
            old_location = npc.location
            npc.location = target
            return TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="npc",
                entity_id=npc.id,
                event_type="npc_movement",
                details={
                    "from": old_location,
                    "to": target,
                    "reason": "schedule",
                },
            )
        return None

    # ── Actions ───────────────────────────────────────────────────────

    def _take_action(
        self,
        npc: NPC,
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """NPC pursues a goal or responds to a concern."""
        events: List[TickEvent] = []

        # Prioritize concerns
        if npc.current_concerns:
            concern = rng.choice(npc.current_concerns)
            resolved = rng.random() < 0.2
            if resolved:
                npc.current_concerns.remove(concern)
            events.append(TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="npc",
                entity_id=npc.id,
                event_type="concern_addressed",
                details={
                    "concern": concern,
                    "resolved": resolved,
                },
            ))
            return events

        # Otherwise pursue goals
        if npc.goals:
            goal = rng.choice(npc.goals)
            progress = rng.randint(0, 2)
            old_progress = goal.get("progress", 0)
            goal["progress"] = min(10, old_progress + progress)
            completed = goal["progress"] >= 10

            events.append(TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="npc",
                entity_id=npc.id,
                event_type="goal_pursuit",
                details={
                    "goal": goal.get("description", goal.get("id", "unknown")),
                    "progress": goal["progress"],
                    "delta": progress,
                    "completed": completed,
                },
            ))
            return events

        # Idle — do nothing notable
        return events

    # ── Status transitions ────────────────────────────────────────────

    def displace_npc(
        self,
        npc: NPC,
        new_location: str,
        reason: str,
        tick_timestamp: str,
    ) -> TickEvent:
        """Force-move an NPC (e.g., due to faction conflict or disaster)."""
        old_location = npc.location
        npc.location = new_location
        npc.status = "displaced"
        npc.current_concerns.append(f"displaced from {old_location}")
        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="npc",
            entity_id=npc.id,
            event_type="npc_displaced",
            details={
                "from": old_location,
                "to": new_location,
                "reason": reason,
            },
        )

    def add_memory(
        self,
        npc: NPC,
        event: str,
        date: str,
        emotional_weight: int = 5,
        decay_rate: float = 0.1,
    ) -> None:
        """Add a new memory to an NPC."""
        npc.memory.append(NpcMemory(
            date=date,
            event=event,
            emotional_weight=emotional_weight,
            decay_rate=decay_rate,
        ))

    def update_relationship(
        self,
        npc: NPC,
        target_id: str,
        standing_delta: int,
        reason: str,
        tick_timestamp: str,
    ) -> TickEvent:
        """Adjust an NPC's relationship standing with another entity."""
        if target_id not in npc.relationships:
            npc.relationships[target_id] = NpcRelationshipState()
        rel = npc.relationships[target_id]
        old = rel.standing
        rel.standing = max(-3, min(3, rel.standing + standing_delta))
        rel.history.append({"reason": reason, "delta": standing_delta, "date": tick_timestamp})

        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="npc",
            entity_id=npc.id,
            event_type="relationship_change",
            details={
                "target": target_id,
                "old_standing": old,
                "new_standing": rel.standing,
                "reason": reason,
            },
        )
