"""Situation generator — creates player-facing situations from world state.

A Situation represents the current narrative snapshot: where the player is,
who's around, what's happening, what choices are available, and how likely
an encounter is. The generator builds this from current world state.
"""

from __future__ import annotations

import random
import uuid
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Location,
    NPC,
    Situation,
    SituationChoice,
    Clock,
    TickEvent,
)


# ---------------------------------------------------------------------------
# Tension assessment
# ---------------------------------------------------------------------------

_TENSION_LEVELS = ["calm", "uneasy", "tense", "volatile", "critical"]


def _assess_tension(
    location: Location,
    npcs_present: List[NPC],
    recent_events: List[TickEvent],
    clocks: Dict[str, Clock],
) -> str:
    """Assess the tension level at a location."""
    score = 0

    # Threat level contributes directly
    score += location.ambient.threat_level

    # Dangers
    score += len(location.dangers)

    # NPC conflicts (NPCs with negative standings toward each other)
    for npc in npcs_present:
        for other in npcs_present:
            if npc.id == other.id:
                continue
            rel = npc.relationships.get(other.id)
            if rel and rel.standing <= -2:
                score += 1

    # Recent violent/dramatic events
    for event in recent_events[-10:]:
        if event.event_type in (
            "territorial_contest", "diplomatic_escalation",
            "npc_displaced", "danger_escalation",
        ):
            score += 1

    # Clocks near completion
    for clock in clocks.values():
        if clock.total_segments > 0:
            ratio = clock.current_segment / clock.total_segments
            if ratio >= 0.75:
                score += 1

    # Map score to tension level
    if score <= 1:
        return "calm"
    elif score <= 3:
        return "uneasy"
    elif score <= 5:
        return "tense"
    elif score <= 8:
        return "volatile"
    else:
        return "critical"


# ---------------------------------------------------------------------------
# Encounter probability
# ---------------------------------------------------------------------------

def _encounter_probability(
    location: Location,
    tension: str,
    player_heat: int = 0,
) -> float:
    """Calculate probability of a combat encounter."""
    base = {
        "calm": 0.02,
        "uneasy": 0.08,
        "tense": 0.15,
        "volatile": 0.25,
        "critical": 0.40,
    }.get(tension, 0.05)

    # Heat increases encounter chance
    heat_bonus = min(0.2, player_heat * 0.03)

    # Location threat level bonus
    threat_bonus = location.ambient.threat_level * 0.03

    return min(0.8, base + heat_bonus + threat_bonus)


# ---------------------------------------------------------------------------
# Choice generation
# ---------------------------------------------------------------------------

def _generate_choices(
    location: Location,
    npcs_present: List[NPC],
    tension: str,
    rng: random.Random,
) -> List[SituationChoice]:
    """Generate 3-6 player choices based on context."""
    choices: List[SituationChoice] = []

    # Always offer observation
    choices.append(SituationChoice(
        id="observe",
        description="Take stock of your surroundings",
        type="observation",
    ))

    # Talk to present NPCs
    for npc in npcs_present[:2]:  # Cap at 2 dialogue choices
        choices.append(SituationChoice(
            id=f"talk_{npc.id}",
            description=f"Speak with {npc.display_name}",
            type="dialogue",
            consequences_hint=None,
        ))

    # Travel options from connections
    for conn in location.connections[:2]:  # Cap at 2 travel choices
        choices.append(SituationChoice(
            id=f"travel_{conn.to_location_id}",
            description=f"Travel to {conn.to_location_id}",
            type="travel",
            consequences_hint="This will advance time" if conn.hazards else None,
        ))

    # Opportunity-based actions
    for opp in location.opportunities[:1]:
        choices.append(SituationChoice(
            id=f"pursue_{opp}",
            description=f"Investigate: {opp.replace('_', ' ')}",
            type="activity",
        ))

    # In tense situations, offer defensive actions
    if tension in ("tense", "volatile", "critical"):
        choices.append(SituationChoice(
            id="prepare",
            description="Prepare for trouble",
            type="action",
            consequences_hint="May reduce encounter difficulty",
        ))

    # Cap at 6
    return choices[:6]


# ---------------------------------------------------------------------------
# SituationGenerator
# ---------------------------------------------------------------------------

class SituationGenerator:
    """Generates Situation objects from current world state."""

    def generate_situation(
        self,
        world_state: Dict[str, Any],
        player: Dict[str, Any],
        location: Location,
        npcs_present: List[NPC],
        recent_events: List[TickEvent],
        clocks: Dict[str, Clock],
        rng: random.Random,
    ) -> Situation:
        """Build a Situation from current state."""
        tick_ts = world_state.get("tick_timestamp", "")
        heat_raw = player.get("heat", 0)
        if isinstance(heat_raw, dict):
            # Support multiple heat dict formats:
            #   {"current": N, "faction_modifiers": {...}}  (character factory)
            #   {"total": N}  (combat outcome)
            #   {"total": N, "permanent": N, "decayable": N}  (merged)
            player_heat = heat_raw.get("current", heat_raw.get("total", 0))
            if not isinstance(player_heat, (int, float)):
                player_heat = 0
        else:
            player_heat = heat_raw

        # Assess tension
        tension = _assess_tension(location, npcs_present, recent_events, clocks)

        # Encounter probability
        enc_prob = _encounter_probability(location, tension, player_heat)

        # Generate choices
        choices = _generate_choices(location, npcs_present, tension, rng)

        # Recent event summaries
        event_summaries = [
            f"{e.entity_type}:{e.event_type}" for e in recent_events[-5:]
        ]

        # What could happen next
        could_happen: List[str] = []
        if enc_prob > 0.15:
            could_happen.append("combat_encounter")
        if any(npc.current_concerns for npc in npcs_present):
            could_happen.append("npc_request")
        if location.dangers:
            could_happen.append("environmental_hazard")

        return Situation(
            location=location.id,
            timestamp=tick_ts,
            present_npcs=[npc.id for npc in npcs_present],
            ambient=location.ambient.to_dict(),
            recent_events=event_summaries,
            tension=tension,
            player_choices=choices,
            could_happen_next=could_happen,
            encounter_probability=enc_prob,
        )
