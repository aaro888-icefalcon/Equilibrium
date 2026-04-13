"""Clock advancement engine — evaluates and advances macro clocks each tick.

Clocks are progress counters (0..total_segments) that track impending events.
Each daily tick, the engine evaluates whether a clock should advance based on
its advance_conditions matched against current world state. When a clock
completes (current_segment == total_segments), its completion_consequences
fire. Some clocks can reset under certain conditions. Clocks can interact
with each other (e.g., one clock advancing accelerates another).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import Clock, TickEvent


# ---------------------------------------------------------------------------
# Condition evaluator
# ---------------------------------------------------------------------------

def _evaluate_condition(condition: Dict[str, Any], world_state: Dict[str, Any]) -> bool:
    """Check if a single advance condition is met.

    Conditions are dicts with at least a 'type' key. Supported types:
    - faction_conflict: true if factions in condition['factions'] have
      standing < condition.get('threshold', -1)
    - resource_below: true if resource at condition['resource'] is below
      condition['threshold']
    - clock_at: true if another clock at condition['clock_id'] has
      current_segment >= condition['segment']
    - always: always true (unconditional advance)
    - flag: true if a flag in world_state['flags'] matches
    """
    ctype = condition.get("type", "")

    if ctype == "always":
        return True

    if ctype == "faction_conflict":
        factions = world_state.get("factions", {})
        target_ids = condition.get("factions", [])
        threshold = condition.get("threshold", -1)
        for fid in target_ids:
            faction = factions.get(fid, {})
            relations = faction.get("relations", {})
            for other_id in target_ids:
                if other_id == fid:
                    continue
                if relations.get(other_id, 0) <= threshold:
                    return True
        return False

    if ctype == "resource_below":
        resources = world_state.get("resources", {})
        resource_key = condition.get("resource", "")
        threshold = condition.get("threshold", 0)
        return resources.get(resource_key, 0) < threshold

    if ctype == "clock_at":
        clocks = world_state.get("clocks", {})
        target_id = condition.get("clock_id", "")
        segment_min = condition.get("segment", 0)
        target_clock = clocks.get(target_id)
        if target_clock is None:
            return False
        seg = target_clock.current_segment if isinstance(target_clock, Clock) else target_clock.get("current_segment", 0)
        return seg >= segment_min

    if ctype == "flag":
        flags = world_state.get("flags", set())
        return condition.get("flag", "") in flags

    # Unknown condition type — don't advance
    return False


# ---------------------------------------------------------------------------
# ClockEngine
# ---------------------------------------------------------------------------

class ClockEngine:
    """Evaluates and advances macro clocks during world ticks."""

    def evaluate_advance(
        self,
        clock: Clock,
        world_state: Dict[str, Any],
        rng: random.Random,
    ) -> bool:
        """Determine whether a clock should advance this tick.

        A clock advances if:
        1. It is not already complete (current_segment < total_segments).
        2. At least one advance_condition is satisfied.
        3. The advance_rate probability check passes (default 1.0 = always).
        """
        if clock.current_segment >= clock.total_segments:
            return False

        if not clock.advance_conditions:
            return False

        # Check if any condition is met
        any_met = any(
            _evaluate_condition(cond, world_state)
            for cond in clock.advance_conditions
        )
        if not any_met:
            return False

        # Probability gate from advance_rate
        prob = clock.advance_rate.get("probability", 1.0)
        return rng.random() < prob

    def advance(
        self,
        clock: Clock,
        world_state: Dict[str, Any],
        tick_timestamp: str,
    ) -> TickEvent:
        """Advance a clock by one segment. Returns a TickEvent."""
        clock.current_segment = min(
            clock.current_segment + 1, clock.total_segments
        )
        clock.last_advancement = {"timestamp": tick_timestamp}

        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="clock",
            entity_id=clock.id,
            event_type="clock_advance",
            details={
                "segment": clock.current_segment,
                "total": clock.total_segments,
                "display_name": clock.display_name,
            },
        )

    def check_completion(self, clock: Clock) -> bool:
        """Return True if the clock has reached its final segment."""
        return clock.current_segment >= clock.total_segments

    def apply_completion(
        self,
        clock: Clock,
        world_state: Dict[str, Any],
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Fire completion consequences. Returns TickEvents describing effects."""
        if not self.check_completion(clock):
            return []

        events: List[TickEvent] = []
        for consequence in clock.completion_consequences:
            events.append(TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="clock",
                entity_id=clock.id,
                event_type="clock_completion",
                details={
                    "consequence": consequence,
                    "display_name": clock.display_name,
                },
                visibility=consequence.get("visibility", "global"),
            ))
        return events

    def check_reset(
        self,
        clock: Clock,
        world_state: Dict[str, Any],
    ) -> bool:
        """Check if a clock's reset conditions are met."""
        if not clock.reset_conditions:
            return False
        return any(
            _evaluate_condition(cond, world_state)
            for cond in clock.reset_conditions
        )

    def reset(
        self,
        clock: Clock,
        tick_timestamp: str,
        reset_to: int = 0,
    ) -> TickEvent:
        """Reset a clock to a given segment (default 0)."""
        old_segment = clock.current_segment
        clock.current_segment = reset_to
        return TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="clock",
            entity_id=clock.id,
            event_type="clock_reset",
            details={
                "from_segment": old_segment,
                "to_segment": reset_to,
                "display_name": clock.display_name,
            },
        )

    def check_interactions(
        self,
        clock: Clock,
        all_clocks: Dict[str, Clock],
        world_state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check if this clock's state triggers interactions with other clocks.

        Returns a list of interaction dicts describing effects on other clocks.
        Interaction format: {target_clock_id, effect_type, ...}
        """
        triggered: List[Dict[str, Any]] = []
        for interaction in clock.interactions:
            target_id = interaction.get("target_clock_id", "")
            if target_id not in all_clocks:
                continue
            trigger_segment = interaction.get("trigger_at_segment", 0)
            if clock.current_segment >= trigger_segment:
                triggered.append(interaction)
        return triggered

    def tick_clocks(
        self,
        clocks: Dict[str, Clock],
        world_state: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Run a full clock tick: evaluate, advance, check completion/reset/interactions.

        This is the main entry point called by the tick engine each day.
        """
        # Put clocks into world_state for cross-clock condition evaluation
        world_state["clocks"] = clocks
        events: List[TickEvent] = []

        for clock_id, clock in clocks.items():
            # Skip already-complete clocks unless they can reset
            if self.check_completion(clock):
                if self.check_reset(clock, world_state):
                    events.append(self.reset(clock, tick_timestamp))
                continue

            # Evaluate and advance
            if self.evaluate_advance(clock, world_state, rng):
                events.append(self.advance(clock, world_state, tick_timestamp))

                # Check completion after advance
                if self.check_completion(clock):
                    events.extend(
                        self.apply_completion(clock, world_state, tick_timestamp)
                    )

        # Cross-clock interactions (second pass)
        for clock_id, clock in clocks.items():
            interactions = self.check_interactions(clock, clocks, world_state)
            for interaction in interactions:
                target_id = interaction.get("target_clock_id", "")
                target = clocks.get(target_id)
                if target is None:
                    continue
                effect = interaction.get("effect_type", "")
                if effect == "accelerate" and target.current_segment < target.total_segments:
                    # Accelerate: advance the target clock by 1 extra
                    prob = interaction.get("probability", 0.5)
                    if rng.random() < prob:
                        events.append(self.advance(target, world_state, tick_timestamp))

        return events
