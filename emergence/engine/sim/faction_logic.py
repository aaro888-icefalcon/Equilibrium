"""Faction decision engine — evaluates faction actions each daily tick.

Each tick, a faction may take one significant action from:
- Territorial: expand, patrol, fortify, contest
- Diplomatic: shift relations, propose treaty, break agreement
- Scheme: advance active schemes
- Internal: manage tensions, purge dissent, recruit
- Resource: trade, requisition, hoard

Calibrated for ~1 significant action per week per faction to avoid
excessive state churn.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Faction,
    FactionGoal,
    FactionRelationship,
    FactionScheme,
    TickEvent,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Base daily probability of a faction taking a significant action (~1/week)
_ACTION_PROBABILITY = 1.0 / 7.0

# Disposition shift thresholds
_DISPOSITION_MIN = -3
_DISPOSITION_MAX = 3


# ---------------------------------------------------------------------------
# FactionDecisionEngine
# ---------------------------------------------------------------------------

class FactionDecisionEngine:
    """Evaluates faction behavior each tick and produces TickEvents."""

    def evaluate_faction_tick(
        self,
        faction: Faction,
        world_state: Dict[str, Any],
        all_factions: Dict[str, Faction],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Run one tick for a faction. Returns list of events (usually 0-1)."""
        # Roll for whether this faction acts today
        if rng.random() >= _ACTION_PROBABILITY:
            return []

        # Gather priorities
        candidates = self._gather_candidates(faction, world_state, all_factions, rng)
        if not candidates:
            return []

        # Weight and pick
        chosen = self._pick_action(candidates, rng)
        events = self._execute_action(
            faction, chosen, world_state, all_factions, rng, tick_timestamp
        )

        # Record last action
        faction.last_tick_actions = [e.to_dict() for e in events]
        return events

    # ── Candidate gathering ──────────────────────────────────────────

    def _gather_candidates(
        self,
        faction: Faction,
        world_state: Dict[str, Any],
        all_factions: Dict[str, Faction],
        rng: random.Random,
    ) -> List[Dict[str, Any]]:
        """Build list of candidate actions with weights."""
        candidates: List[Dict[str, Any]] = []

        # Territorial actions
        if faction.territory.contested_zones:
            candidates.append({
                "type": "territorial",
                "subtype": "contest",
                "weight": 2.0,
                "zone": rng.choice(faction.territory.contested_zones),
            })
        if faction.resources.get("military", 0) > 50:
            candidates.append({
                "type": "territorial",
                "subtype": "patrol",
                "weight": 1.0,
            })

        # Diplomatic actions
        for other_id, rel in faction.external_relationships.items():
            if other_id not in all_factions:
                continue
            if rel.disposition <= -2 and rel.active_grievances:
                candidates.append({
                    "type": "diplomatic",
                    "subtype": "escalate",
                    "weight": 1.5,
                    "target": other_id,
                })
            elif rel.disposition >= 1 and not rel.active_agreements:
                candidates.append({
                    "type": "diplomatic",
                    "subtype": "propose_treaty",
                    "weight": 1.0,
                    "target": other_id,
                })
            # Natural disposition drift toward 0
            if abs(rel.disposition) >= 2:
                candidates.append({
                    "type": "diplomatic",
                    "subtype": "drift",
                    "weight": 0.5,
                    "target": other_id,
                })

        # Scheme advancement
        for scheme in faction.current_schemes:
            if scheme.progress < 10:
                candidates.append({
                    "type": "scheme",
                    "subtype": "advance",
                    "weight": 1.5,
                    "scheme_id": scheme.id,
                })

        # Internal tensions
        if faction.internal_tensions:
            candidates.append({
                "type": "internal",
                "subtype": "manage_tension",
                "weight": 1.5,
                "tension": faction.internal_tensions[0],
            })

        # Resource actions (always a low-weight fallback)
        candidates.append({
            "type": "resource",
            "subtype": "gather",
            "weight": 0.5,
        })

        # Goal pursuit
        for goal in faction.goals:
            if goal.progress < 10:
                candidates.append({
                    "type": "goal",
                    "subtype": "pursue",
                    "weight": goal.weight,
                    "goal_id": goal.id,
                })

        return candidates

    def _pick_action(
        self,
        candidates: List[Dict[str, Any]],
        rng: random.Random,
    ) -> Dict[str, Any]:
        """Weighted random selection from candidates."""
        weights = [c["weight"] for c in candidates]
        total = sum(weights)
        roll = rng.random() * total
        cumulative = 0.0
        for candidate in candidates:
            cumulative += candidate["weight"]
            if roll <= cumulative:
                return candidate
        return candidates[-1]

    # ── Action execution ─────────────────────────────────────────────

    def _execute_action(
        self,
        faction: Faction,
        action: Dict[str, Any],
        world_state: Dict[str, Any],
        all_factions: Dict[str, Faction],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        """Execute a chosen action and return TickEvents."""
        action_type = action["type"]
        subtype = action["subtype"]

        if action_type == "territorial":
            return self._do_territorial(faction, action, rng, tick_timestamp)
        elif action_type == "diplomatic":
            return self._do_diplomatic(
                faction, action, all_factions, rng, tick_timestamp
            )
        elif action_type == "scheme":
            return self._do_scheme(faction, action, rng, tick_timestamp)
        elif action_type == "internal":
            return self._do_internal(faction, action, rng, tick_timestamp)
        elif action_type == "resource":
            return self._do_resource(faction, action, rng, tick_timestamp)
        elif action_type == "goal":
            return self._do_goal(faction, action, rng, tick_timestamp)

        return []

    def _do_territorial(
        self,
        faction: Faction,
        action: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        subtype = action["subtype"]
        if subtype == "contest":
            zone = action.get("zone", "unknown")
            success = rng.random() < 0.4
            if success:
                if zone in faction.territory.contested_zones:
                    faction.territory.contested_zones.remove(zone)
                if zone not in faction.territory.secondary_holdings:
                    faction.territory.secondary_holdings.append(zone)
            return [TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="faction",
                entity_id=faction.id,
                event_type="territorial_contest",
                details={
                    "zone": zone,
                    "success": success,
                    "subtype": subtype,
                },
            )]
        elif subtype == "patrol":
            return [TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="faction",
                entity_id=faction.id,
                event_type="territorial_patrol",
                details={"subtype": subtype},
            )]
        return []

    def _do_diplomatic(
        self,
        faction: Faction,
        action: Dict[str, Any],
        all_factions: Dict[str, Faction],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        target_id = action.get("target", "")
        subtype = action["subtype"]
        rel = faction.external_relationships.get(target_id)
        if rel is None:
            return []

        if subtype == "escalate":
            shift = -1
            new_disp = max(_DISPOSITION_MIN, rel.disposition + shift)
            rel.disposition = new_disp
            # Mirror on target
            other = all_factions.get(target_id)
            if other and faction.id in other.external_relationships:
                other_rel = other.external_relationships[faction.id]
                other_rel.disposition = max(
                    _DISPOSITION_MIN, other_rel.disposition + shift
                )
            return [TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="faction",
                entity_id=faction.id,
                event_type="diplomatic_escalation",
                details={
                    "target": target_id,
                    "new_disposition": new_disp,
                },
                visibility="regional",
            )]

        elif subtype == "propose_treaty":
            # 50/50 acceptance
            accepted = rng.random() < 0.5
            if accepted:
                treaty = f"treaty_{faction.id}_{target_id}"
                rel.active_agreements.append(treaty)
                other = all_factions.get(target_id)
                if other and faction.id in other.external_relationships:
                    other.external_relationships[faction.id].active_agreements.append(treaty)
            return [TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="faction",
                entity_id=faction.id,
                event_type="diplomatic_treaty_proposal",
                details={
                    "target": target_id,
                    "accepted": accepted,
                },
                visibility="regional",
            )]

        elif subtype == "drift":
            # Drift one step toward 0
            if rel.disposition > 0:
                rel.disposition -= 1
            elif rel.disposition < 0:
                rel.disposition += 1
            return [TickEvent(
                tick_timestamp=tick_timestamp,
                entity_type="faction",
                entity_id=faction.id,
                event_type="diplomatic_drift",
                details={
                    "target": target_id,
                    "new_disposition": rel.disposition,
                },
            )]

        return []

    def _do_scheme(
        self,
        faction: Faction,
        action: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        scheme_id = action.get("scheme_id", "")
        scheme = None
        for s in faction.current_schemes:
            if s.id == scheme_id:
                scheme = s
                break
        if scheme is None:
            return []

        progress_delta = rng.randint(1, 3)
        scheme.progress = min(10, scheme.progress + progress_delta)
        completed = scheme.progress >= 10

        return [TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="faction",
            entity_id=faction.id,
            event_type="scheme_advance" if not completed else "scheme_complete",
            details={
                "scheme_id": scheme_id,
                "progress": scheme.progress,
                "delta": progress_delta,
                "completed": completed,
            },
        )]

    def _do_internal(
        self,
        faction: Faction,
        action: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        tension = action.get("tension", {})
        resolved = rng.random() < 0.3
        if resolved and tension in faction.internal_tensions:
            faction.internal_tensions.remove(tension)

        return [TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="faction",
            entity_id=faction.id,
            event_type="internal_tension_managed",
            details={
                "tension": tension,
                "resolved": resolved,
            },
        )]

    def _do_resource(
        self,
        faction: Faction,
        action: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        # Gather a random amount of a primary resource
        resources = faction.economic_base.primary_resources
        if resources:
            resource = rng.choice(resources)
        else:
            resource = "supplies"
        amount = rng.randint(5, 20)
        faction.resources[resource] = faction.resources.get(resource, 0) + amount

        return [TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="faction",
            entity_id=faction.id,
            event_type="resource_gathered",
            details={
                "resource": resource,
                "amount": amount,
                "new_total": faction.resources[resource],
            },
        )]

    def _do_goal(
        self,
        faction: Faction,
        action: Dict[str, Any],
        rng: random.Random,
        tick_timestamp: str,
    ) -> List[TickEvent]:
        goal_id = action.get("goal_id", "")
        goal = None
        for g in faction.goals:
            if g.id == goal_id:
                goal = g
                break
        if goal is None:
            return []

        delta = rng.randint(0, 2)
        goal.progress = min(10, goal.progress + delta)

        return [TickEvent(
            tick_timestamp=tick_timestamp,
            entity_type="faction",
            entity_id=faction.id,
            event_type="goal_progress",
            details={
                "goal_id": goal_id,
                "progress": goal.progress,
                "delta": delta,
            },
        )]
