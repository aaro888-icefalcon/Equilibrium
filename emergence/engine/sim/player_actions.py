"""Player action resolver — resolves player choices in situations.

Takes a SituationChoice selected by the player and resolves its effects:
state deltas, time cost, narration scene type, whether an encounter triggers.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Location,
    NPC,
    Situation,
    SituationChoice,
)


# ---------------------------------------------------------------------------
# ActionResult
# ---------------------------------------------------------------------------

@dataclass
class ActionResult:
    """Result of resolving a player action."""
    choice_id: str
    choice_type: str  # dialogue, travel, activity, observation, action
    narration_scene_type: str = "situation_description"
    time_cost_days: int = 0
    state_deltas: Dict[str, Any] = field(default_factory=dict)
    encounter_triggered: bool = False
    new_location: Optional[str] = None
    npc_interaction: Optional[Dict[str, Any]] = None
    narrative_hints: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# PlayerActionResolver
# ---------------------------------------------------------------------------

class PlayerActionResolver:
    """Resolves player choices within situations."""

    def resolve_action(
        self,
        choice: SituationChoice,
        situation: Situation,
        location: Location,
        npcs_present: List[NPC],
        player: Dict[str, Any],
        rng: random.Random,
    ) -> ActionResult:
        """Resolve a player's chosen action."""
        if choice.type == "dialogue":
            return self._resolve_dialogue(choice, npcs_present, rng)
        elif choice.type == "travel":
            return self._resolve_travel(choice, location, situation, rng)
        elif choice.type == "activity":
            return self._resolve_activity(choice, location, rng)
        elif choice.type == "observation":
            return self._resolve_observation(choice, location, npcs_present, rng)
        elif choice.type == "action":
            return self._resolve_action(choice, situation, rng)
        else:
            return ActionResult(
                choice_id=choice.id,
                choice_type=choice.type,
            )

    # ── Dialogue ──────────────────────────────────────────────────────

    def _resolve_dialogue(
        self,
        choice: SituationChoice,
        npcs_present: List[NPC],
        rng: random.Random,
    ) -> ActionResult:
        # Extract NPC id from choice id (format: talk_<npc_id>)
        npc_id = choice.id.replace("talk_", "")
        npc = None
        for n in npcs_present:
            if n.id == npc_id:
                npc = n
                break

        interaction = None
        hints: List[str] = []
        if npc:
            # NPC may share knowledge
            if npc.knowledge:
                topic = rng.choice(npc.knowledge)
                interaction = {
                    "npc_id": npc.id,
                    "npc_name": npc.display_name,
                    "shared_topic": topic.topic,
                    "shared_detail": topic.detail,
                }
                hints.append(f"{npc.display_name} shares information about {topic.topic}")
            else:
                interaction = {
                    "npc_id": npc.id,
                    "npc_name": npc.display_name,
                    "shared_topic": None,
                }
                hints.append(f"{npc.display_name} has nothing notable to share")

            # Relationship delta
            standing_delta = rng.choice([-1, 0, 0, 0, 1, 1])
            if standing_delta != 0:
                interaction["standing_delta"] = standing_delta

        return ActionResult(
            choice_id=choice.id,
            choice_type="dialogue",
            narration_scene_type="dialogue",
            time_cost_days=0,
            npc_interaction=interaction,
            narrative_hints=hints,
        )

    # ── Travel ────────────────────────────────────────────────────────

    def _resolve_travel(
        self,
        choice: SituationChoice,
        location: Location,
        situation: Situation,
        rng: random.Random,
    ) -> ActionResult:
        dest = choice.id.replace("travel_", "")

        # Find connection
        conn = None
        for c in location.connections:
            if c.to_location_id == dest:
                conn = c
                break

        # Travel time
        time_cost = 1  # default 1 day
        if conn and conn.travel_time:
            # Simple parse: "2d" → 2 days
            try:
                time_cost = int(conn.travel_time.replace("d", ""))
            except ValueError:
                time_cost = 1

        # Encounter check during travel
        encounter = False
        if conn and conn.hazards:
            encounter = rng.random() < 0.2
        elif rng.random() < situation.encounter_probability * 0.5:
            encounter = True

        return ActionResult(
            choice_id=choice.id,
            choice_type="travel",
            narration_scene_type="transition",
            time_cost_days=time_cost,
            new_location=dest,
            encounter_triggered=encounter,
            narrative_hints=[f"Traveling to {dest}"],
        )

    # ── Activity ──────────────────────────────────────────────────────

    def _resolve_activity(
        self,
        choice: SituationChoice,
        location: Location,
        rng: random.Random,
    ) -> ActionResult:
        activity = choice.id.replace("pursue_", "")

        # Activity outcomes
        success = rng.random() < 0.6
        deltas: Dict[str, Any] = {}
        hints: List[str] = []

        if success:
            deltas["resources_gained"] = {activity: rng.randint(1, 3)}
            hints.append(f"Successfully investigated {activity.replace('_', ' ')}")
            # Remove the opportunity
            if activity in location.opportunities:
                location.opportunities.remove(activity)
        else:
            hints.append(f"Investigation of {activity.replace('_', ' ')} yielded nothing")

        return ActionResult(
            choice_id=choice.id,
            choice_type="activity",
            narration_scene_type="situation_description",
            time_cost_days=1,
            state_deltas=deltas,
            narrative_hints=hints,
        )

    # ── Observation ───────────────────────────────────────────────────

    def _resolve_observation(
        self,
        choice: SituationChoice,
        location: Location,
        npcs_present: List[NPC],
        rng: random.Random,
    ) -> ActionResult:
        hints: List[str] = []

        # Reveal some information
        if location.dangers:
            hints.append(f"You notice: {', '.join(location.dangers)}")
        if location.opportunities:
            hints.append(f"Opportunities: {', '.join(location.opportunities)}")
        if npcs_present:
            hints.append(
                f"Present: {', '.join(n.display_name for n in npcs_present)}"
            )
        if not hints:
            hints.append("Nothing notable catches your attention")

        return ActionResult(
            choice_id=choice.id,
            choice_type="observation",
            narration_scene_type="situation_description",
            time_cost_days=0,
            narrative_hints=hints,
        )

    # ── Action (prepare, etc.) ────────────────────────────────────────

    def _resolve_action(
        self,
        choice: SituationChoice,
        situation: Situation,
        rng: random.Random,
    ) -> ActionResult:
        deltas: Dict[str, Any] = {}
        hints: List[str] = []

        if choice.id == "prepare":
            deltas["combat_bonus"] = rng.randint(1, 3)
            hints.append("You prepare for potential conflict")

        return ActionResult(
            choice_id=choice.id,
            choice_type="action",
            narration_scene_type="situation_description",
            time_cost_days=0,
            state_deltas=deltas,
            narrative_hints=hints,
        )
