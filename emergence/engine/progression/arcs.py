"""Narrative arc tracker — monitors goal progress, relationship climax,
faction shifts, and personal transformation moments.

Generates narrator payloads for significant milestones.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ArcEvent:
    """A significant narrative event detected by the arc tracker."""

    def __init__(
        self,
        arc_type: str,
        description: str,
        scene_type: str = "scene_framing",
        data: Dict[str, Any] | None = None,
    ) -> None:
        self.arc_type = arc_type
        self.description = description
        self.scene_type = scene_type
        self.data = data or {}


class ArcTracker:
    """Tracks narrative arcs and detects significant moments."""

    def check_arc_progress(
        self,
        character: Dict[str, Any],
        world: Dict[str, Any],
    ) -> List[ArcEvent]:
        """Check all arcs for significant progress. Returns events."""
        events = []

        events.extend(self._check_goals(character))
        events.extend(self._check_relationship_climax(character))
        events.extend(self._check_faction_shifts(character))
        events.extend(self._check_transformation(character))
        events.extend(self._check_tier_milestones(character))

        return events

    def _check_goals(self, character: Dict[str, Any]) -> List[ArcEvent]:
        """Check goal progress milestones."""
        events = []
        goals = character.get("goals", [])

        for goal in goals:
            if isinstance(goal, dict):
                progress = goal.get("progress", 0)
                status = goal.get("status", "active")
                goal_name = goal.get("description", "unknown goal")

                if status == "active" and progress >= 100:
                    goal["status"] = "completed"
                    events.append(ArcEvent(
                        "goal_completed",
                        f"Goal achieved: {goal_name}",
                        scene_type="scene_framing",
                        data={"goal": goal_name},
                    ))
                elif status == "active" and progress >= 75 and not goal.get("milestone_75"):
                    goal["milestone_75"] = True
                    events.append(ArcEvent(
                        "goal_milestone",
                        f"Goal nearly complete: {goal_name}",
                        data={"goal": goal_name, "progress": progress},
                    ))

        return events

    def _check_relationship_climax(self, character: Dict[str, Any]) -> List[ArcEvent]:
        """Detect relationship climax moments."""
        events = []
        relationships = character.get("relationships", {})

        for npc_id, rel in relationships.items():
            state = rel.get("state", "neutral")
            prev_state = rel.get("prev_state", "neutral")

            if state != prev_state:
                # State transition detected
                if state == "loyal" and prev_state != "loyal":
                    events.append(ArcEvent(
                        "relationship_climax",
                        f"Deep bond formed with {npc_id}",
                        scene_type="dialogue",
                        data={"npc_id": npc_id, "new_state": state},
                    ))
                elif state == "blood_feud" and prev_state != "blood_feud":
                    events.append(ArcEvent(
                        "relationship_climax",
                        f"Blood feud declared with {npc_id}",
                        scene_type="scene_framing",
                        data={"npc_id": npc_id, "new_state": state},
                    ))
                elif state == "dead":
                    events.append(ArcEvent(
                        "relationship_loss",
                        f"{npc_id} has died",
                        scene_type="death_narration",
                        data={"npc_id": npc_id},
                    ))

                rel["prev_state"] = state

        return events

    def _check_faction_shifts(self, character: Dict[str, Any]) -> List[ArcEvent]:
        """Detect significant faction standing changes."""
        events = []
        factions = character.get("faction_standings", {})

        for fac_id, fac in factions.items():
            standing = fac.get("standing", 0)
            prev_standing = fac.get("prev_standing")

            if prev_standing is not None and standing != prev_standing:
                if standing == 3 and prev_standing < 3:
                    events.append(ArcEvent(
                        "faction_milestone",
                        f"Sworn allegiance with {fac_id}",
                        data={"faction_id": fac_id, "standing": standing},
                    ))
                elif standing == -3 and prev_standing > -3:
                    events.append(ArcEvent(
                        "faction_milestone",
                        f"Declared enemy of {fac_id}",
                        data={"faction_id": fac_id, "standing": standing},
                    ))

            fac["prev_standing"] = standing

        return events

    def _check_transformation(self, character: Dict[str, Any]) -> List[ArcEvent]:
        """Detect corruption transformation milestones."""
        events = []
        corruption = character.get("corruption", 0)
        prev_corruption_segment = character.get("prev_corruption_segment", 0)
        current_segment = int(corruption)

        if current_segment > prev_corruption_segment:
            if current_segment == 3:
                events.append(ArcEvent(
                    "corruption_milestone",
                    "The change is now visible to others",
                    scene_type="scene_framing",
                    data={"corruption": current_segment},
                ))
            elif current_segment == 5:
                events.append(ArcEvent(
                    "corruption_milestone",
                    "Transformation accelerates — the old self fades",
                    scene_type="scene_framing",
                    data={"corruption": current_segment},
                ))
            elif current_segment == 6:
                events.append(ArcEvent(
                    "corruption_transformation",
                    "Transformation complete",
                    scene_type="death_narration",
                    data={"corruption": current_segment},
                ))

        character["prev_corruption_segment"] = current_segment
        return events

    def _check_tier_milestones(self, character: Dict[str, Any]) -> List[ArcEvent]:
        """Detect tier advancement milestones."""
        events = []
        tier = character.get("tier", 1)
        prev_tier = character.get("prev_tier")

        if prev_tier is not None and tier > prev_tier:
            events.append(ArcEvent(
                "tier_milestone",
                f"Breakthrough — tier {tier} reached",
                scene_type="scene_framing",
                data={"tier": tier, "prev_tier": prev_tier},
            ))

        character["prev_tier"] = tier
        return events
