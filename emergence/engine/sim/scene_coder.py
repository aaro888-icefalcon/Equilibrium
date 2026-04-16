"""AngryGM-style scene coder — replaces the rigid choice menu.

A scene has:
- Dramatic question (yes/no)
- Source of conflict
- Scene type (action / social / exploration / decision / transition)
- NPCs with social stat blocks
- Yes/no outcomes (what happens either way)
- Transition hint (what follows)
- Hidden elements (for narrator seeding and complication parameterization)

The narrator uses the scene code to generate prose. No numbered choices —
the player declares what they want to do freely.

Three scene phases:
- opener: 150-300 words, full establishing beat (sensation → info → invitation)
- continuation: 60-120 words, result + invitation after resolve-action
- close: 40-80 words, resolution + forward momentum
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.schemas.world import (
    Clock,
    Location,
    NPC,
    SocialBlock,
    TickEvent,
)
from emergence.engine.sim.hidden_elements import (
    HiddenElement,
    gather_hidden_elements,
)
from emergence.engine.sim.social import ensure_social_block


# ---------------------------------------------------------------------------
# Scene code dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NpcSceneView:
    """Slim NPC view for the narrator, including social stat block."""
    id: str
    display_name: str
    role: str
    voice: str
    social_block: Dict[str, Any]         # SocialBlock serialized
    knowledge_topics: List[str]
    hooks: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "role": self.role,
            "voice": self.voice,
            "social_block": self.social_block,
            "knowledge_topics": self.knowledge_topics,
            "hooks": self.hooks,
        }


@dataclass
class SceneCode:
    """Complete scene specification replacing Situation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    scene_type: str = "exploration"       # action / social / exploration / decision / transition
    scene_phase: str = "opener"           # opener / continuation / close

    # Dramatic frame
    dramatic_question: str = ""
    source_of_conflict: str = ""
    yes_outcome: str = ""
    no_outcome: str = ""
    transition_hint: str = ""

    # Location
    location_id: str = ""
    location_display: str = ""
    tension: str = "calm"

    # NPCs
    npcs: List[Dict[str, Any]] = field(default_factory=list)    # NpcSceneView dicts

    # Narrative context
    hidden_elements: List[Dict[str, Any]] = field(default_factory=list)
    environmental_detail: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    relevant_player_goals: List[str] = field(default_factory=list)
    available_approaches: List[str] = field(default_factory=list)

    # Mechanical state
    encounter_probability: float = 0.0
    scene_continues: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scene_type": self.scene_type,
            "scene_phase": self.scene_phase,
            "dramatic_question": self.dramatic_question,
            "source_of_conflict": self.source_of_conflict,
            "yes_outcome": self.yes_outcome,
            "no_outcome": self.no_outcome,
            "transition_hint": self.transition_hint,
            "location_id": self.location_id,
            "location_display": self.location_display,
            "tension": self.tension,
            "npcs": list(self.npcs),
            "hidden_elements": list(self.hidden_elements),
            "environmental_detail": list(self.environmental_detail),
            "constraints": list(self.constraints),
            "relevant_player_goals": list(self.relevant_player_goals),
            "available_approaches": list(self.available_approaches),
            "encounter_probability": self.encounter_probability,
            "scene_continues": self.scene_continues,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SceneCode":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            scene_type=data.get("scene_type", "exploration"),
            scene_phase=data.get("scene_phase", "opener"),
            dramatic_question=data.get("dramatic_question", ""),
            source_of_conflict=data.get("source_of_conflict", ""),
            yes_outcome=data.get("yes_outcome", ""),
            no_outcome=data.get("no_outcome", ""),
            transition_hint=data.get("transition_hint", ""),
            location_id=data.get("location_id", ""),
            location_display=data.get("location_display", ""),
            tension=data.get("tension", "calm"),
            npcs=data.get("npcs", []),
            hidden_elements=data.get("hidden_elements", []),
            environmental_detail=data.get("environmental_detail", []),
            constraints=data.get("constraints", []),
            relevant_player_goals=data.get("relevant_player_goals", []),
            available_approaches=data.get("available_approaches", []),
            encounter_probability=data.get("encounter_probability", 0.0),
            scene_continues=data.get("scene_continues", True),
        )


# ---------------------------------------------------------------------------
# Scene type inference
# ---------------------------------------------------------------------------

def infer_scene_type(
    npcs_present: List[NPC],
    tension: str,
    player_goals: List[Dict[str, Any]],
    location: Location,
    recent_events: List[TickEvent],
) -> str:
    """Infer scene type from context.

    Priority:
    - Hostile NPCs (disp <= -2) + high tension → action
    - NPCs with what_they_want_from_player → social
    - Unexplored opportunities + low tension → exploration
    - High-pressure goals + relevant context → decision
    - Player just traveled (recent travel event) → transition
    - Fallback: exploration
    """
    # Action: hostile NPCs present with high tension
    hostile_present = any(
        getattr(n, "standing_with_player_default", 0) <= -2
        for n in npcs_present
    )
    if hostile_present and tension in ("tense", "volatile", "critical"):
        return "action"

    # Social: NPCs who want something from the player
    social_interest = any(
        getattr(n, "what_they_want_from_player", "")
        for n in npcs_present
    )
    if social_interest:
        return "social"

    # Decision: high-pressure goals
    high_pressure = any(
        g.get("pressure", 0) >= 3 for g in player_goals
    )
    if high_pressure and len(player_goals) >= 2:
        return "decision"

    # Exploration: unexplored opportunities
    if location.opportunities:
        return "exploration"

    return "exploration"


# ---------------------------------------------------------------------------
# Dramatic question derivation
# ---------------------------------------------------------------------------

def derive_dramatic_question(
    scene_type: str,
    npcs_present: List[NPC],
    player_goals: List[Dict[str, Any]],
    location: Location,
    player: Dict[str, Any],
) -> Tuple[str, str]:
    """Derive dramatic question and source of conflict.

    Returns (question, conflict).

    Priority:
    1. Player goal intersecting with present NPC → DQ from goal
    2. NPC what_they_want_from_player + player presence → DQ from NPC want
    3. Active obligation at location → DQ from obligation
    4. Location tension → DQ from threat
    5. Fallback: "Can Shake pass through safely?"
    """
    player_name = player.get("name", "the player").split()[0]  # First name

    # Priority 1: Player goal + NPC intersection
    for goal in player_goals:
        goal_desc = goal.get("description", "")
        goal_id = goal.get("id", "")
        for npc in npcs_present:
            # Rough heuristic: goal references NPC name or ID
            if (npc.display_name.lower() in goal_desc.lower()
                    or npc.id in goal_id):
                question = f"Can {player_name} {goal_desc.lower()}?"
                conflict = (
                    getattr(npc, "what_they_want_from_player", "")
                    or f"{npc.display_name} has their own agenda"
                )
                return (question, conflict)

    # Priority 2: NPC want
    for npc in npcs_present:
        want = getattr(npc, "what_they_want_from_player", "")
        if want:
            question = (
                f"Will {player_name} give {npc.display_name} what they want?"
            )
            conflict = want
            return (question, conflict)

    # Priority 3: Active obligation (inferred from current_events)
    for event in getattr(location, "current_events", []):
        if any(kw in event.lower() for kw in ("review", "summons", "meeting", "audit")):
            question = f"Can {player_name} handle this obligation?"
            conflict = event
            return (question, conflict)

    # Priority 4: Tension from dangers
    if location.dangers:
        danger_list = ", ".join(location.dangers[:2])
        question = f"Can {player_name} navigate {location.display_name} safely?"
        conflict = danger_list
        return (question, conflict)

    # Priority 5: Fallback
    question = f"What will {player_name} find at {location.display_name}?"
    conflict = "Uncertainty"
    return (question, conflict)


def derive_yes_no_outcomes(
    question: str, conflict: str, scene_type: str
) -> Tuple[str, str]:
    """Generate yes/no outcome summaries for the scene code.

    These are hints for the narrator — they indicate what a 'resolved yes'
    or 'resolved no' scene close should describe.
    """
    if scene_type == "social":
        yes = "Agreement reached, disposition improves, new options open."
        no = "Request refused, disposition drops, alternatives force themselves."
    elif scene_type == "action":
        yes = "Threat overcome. Danger passes. Resources likely spent."
        no = "Overwhelmed. Harm taken. Situation worsens."
    elif scene_type == "decision":
        yes = "Decision made, path committed, other options closed."
        no = "Decision forced by circumstance or delay, worse option taken."
    elif scene_type == "transition":
        yes = "Travel safe. Arrival at destination. Time advances."
        no = "Incident en route. Time lost. Resources spent."
    else:  # exploration
        yes = "Information gained. Opportunity identified. Path forward clearer."
        no = "Nothing found. Time lost. Something noticed you."
    return (yes, no)


# ---------------------------------------------------------------------------
# Available approaches
# ---------------------------------------------------------------------------

def _approaches_for_scene(
    scene_type: str, npcs_present: List[NPC]
) -> List[str]:
    """Suggest approaches relevant to the scene type."""
    has_npcs = bool(npcs_present)
    hostile = any(
        getattr(n, "standing_with_player_default", 0) <= -1
        for n in npcs_present
    )

    if scene_type == "social" and has_npcs:
        if hostile:
            return ["persuade", "intimidate", "reason", "deceive", "wait"]
        return ["persuade", "reason", "deceive", "intimidate", "wait"]
    if scene_type == "action":
        return ["force", "speed", "stealth", "endurance", "wait"]
    if scene_type == "exploration":
        return ["observe", "search", "analyze", "ask_around", "wait"]
    if scene_type == "decision":
        return ["analyze", "reason", "wait"]
    if scene_type == "transition":
        return ["direct", "cautious", "fast"]
    return ["observe", "wait"]


# ---------------------------------------------------------------------------
# Tension assessment (ported from situation_generator)
# ---------------------------------------------------------------------------

def _assess_tension(
    location: Location,
    npcs_present: List[NPC],
    recent_events: List[TickEvent],
    clocks: Dict[str, Clock],
) -> str:
    """Compute tension level (calm/uneasy/tense/volatile/critical)."""
    score = location.ambient.threat_level + len(location.dangers)

    for npc in npcs_present:
        if getattr(npc, "standing_with_player_default", 0) <= -2:
            score += 1

    for event in recent_events[-10:]:
        ev_type = getattr(event, "event_type", "")
        if ev_type in (
            "territorial_contest", "diplomatic_escalation",
            "npc_displaced", "danger_escalation",
        ):
            score += 1

    for clock in clocks.values():
        if clock.total_segments > 0:
            ratio = clock.current_segment / clock.total_segments
            if ratio >= 0.75:
                score += 1

    if score <= 1: return "calm"
    if score <= 3: return "uneasy"
    if score <= 5: return "tense"
    if score <= 8: return "volatile"
    return "critical"


def _encounter_probability(tension: str, player_heat: int = 0) -> float:
    base = {"calm": 0.02, "uneasy": 0.08, "tense": 0.15,
            "volatile": 0.25, "critical": 0.40}.get(tension, 0.05)
    return min(0.8, base + min(0.2, player_heat * 0.03))


# ---------------------------------------------------------------------------
# NPC scene view builder
# ---------------------------------------------------------------------------

def _build_npc_view(npc: NPC) -> NpcSceneView:
    """Build an NpcSceneView with social block lazily seeded."""
    block = ensure_social_block(npc)
    topics = [getattr(k, "topic", "") for k in getattr(npc, "knowledge", [])[:3]]
    return NpcSceneView(
        id=npc.id,
        display_name=npc.display_name,
        role=getattr(npc, "role", ""),
        voice=getattr(npc, "voice", ""),
        social_block=block.to_dict(),
        knowledge_topics=[t for t in topics if t],
        hooks=list(getattr(npc, "hooks", [])),
    )


# ---------------------------------------------------------------------------
# Main entry point: generate_scene
# ---------------------------------------------------------------------------

class SceneCodeGenerator:
    """Generates SceneCode objects from current world state."""

    def generate_scene(
        self,
        world_state: Dict[str, Any],
        player: Dict[str, Any],
        location: Location,
        npcs_present: List[NPC],
        recent_events: List[TickEvent],
        clocks: Dict[str, Clock],
        factions: Optional[Dict[str, Any]] = None,
        rng: Optional[random.Random] = None,
    ) -> SceneCode:
        """Build a complete scene code from world state."""
        rng = rng or random.Random()

        # Tension and encounter probability
        tension = _assess_tension(location, npcs_present, recent_events, clocks)
        heat_raw = player.get("heat", 0)
        heat = heat_raw.get("current", 0) if isinstance(heat_raw, dict) else heat_raw
        enc_prob = _encounter_probability(tension, heat)

        # Scene type
        player_goals = list(player.get("goals", []))
        scene_type = infer_scene_type(
            npcs_present, tension, player_goals, location, recent_events,
        )

        # Dramatic question + source of conflict
        dq, conflict = derive_dramatic_question(
            scene_type, npcs_present, player_goals, location, player,
        )

        # Yes/no outcomes
        yes_outcome, no_outcome = derive_yes_no_outcomes(dq, conflict, scene_type)

        # NPC scene views
        npc_views = [_build_npc_view(n) for n in npcs_present]

        # Hidden elements
        hidden = gather_hidden_elements(
            location=location,
            npcs_present=npcs_present,
            recent_events=recent_events,
            clocks=clocks,
            factions=factions,
        )

        # Environmental detail — lead with what the player sees
        env_detail = []
        if location.description:
            env_detail.append(location.description)
        if location.current_events:
            env_detail.extend(
                f"Current event: {e}" for e in location.current_events[:3]
            )

        # Constraints from location tension and NPC presence
        constraints: List[str] = []
        if tension in ("tense", "volatile", "critical"):
            constraints.append(f"Tension: {tension}")
        for npc in npcs_present:
            want = getattr(npc, "what_they_want_from_player", "")
            if want:
                constraints.append(f"{npc.display_name} wants: {want}")

        # Relevant player goals (those with pressure > 0)
        relevant_goals = [
            g.get("description", "")
            for g in player_goals
            if g.get("pressure", 0) > 0
        ][:3]

        # Available approaches (suggestions)
        approaches = _approaches_for_scene(scene_type, npcs_present)

        # Transition hint (brief guess at what follows)
        transition_hint = (
            "After resolution: new scene based on outcome and NPC reactions."
        )

        return SceneCode(
            scene_type=scene_type,
            scene_phase="opener",
            dramatic_question=dq,
            source_of_conflict=conflict,
            yes_outcome=yes_outcome,
            no_outcome=no_outcome,
            transition_hint=transition_hint,
            location_id=location.id,
            location_display=getattr(location, "display_name", location.id),
            tension=tension,
            npcs=[v.to_dict() for v in npc_views],
            hidden_elements=[h.to_dict() for h in hidden],
            environmental_detail=env_detail,
            constraints=constraints,
            relevant_player_goals=relevant_goals,
            available_approaches=approaches,
            encounter_probability=enc_prob,
            scene_continues=True,
        )


# ---------------------------------------------------------------------------
# Scene continuation logic
# ---------------------------------------------------------------------------

def check_scene_continues(
    scene: SceneCode, resolution_payload: Dict[str, Any]
) -> Tuple[bool, str]:
    """Check if the scene should continue after a resolve-action.

    Returns (continues, reason).

    Scene ends when:
    - interaction_ended (patience hit 0)
    - outcome was severe (major state change)
    - player chose to leave (travel action succeeded)
    """
    scene_state = resolution_payload.get("scene_state_changes", {})

    # Hard stop: patience exhausted
    if scene_state.get("interaction_ended"):
        return (False, "NPC patience exhausted — interaction forced to end.")

    # Travel away = scene ends
    if resolution_payload.get("new_location"):
        return (False, "Player traveled to a new location.")

    # Force new DQ complication = scene ends
    for comp in resolution_payload.get("complications", []):
        if comp.get("move_id") in ("force_new_dq", "capture_seize"):
            return (False, f"Complication forced scene end: {comp.get('move_id')}")

    # Severe outcome with major state change
    outcome_tier = resolution_payload.get("outcome_tier", "")
    if outcome_tier == "fumble":
        return (False, "Fumble triggered scene close.")

    return (True, "")
