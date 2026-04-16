"""PBTA-style complication generator for simulation resolution.

Draws from Apocalypse World MC moves, AW threat moves, Dungeon World GM moves,
and DW danger moves. The engine picks complications based on:
- Outcome tier (MARGINAL = success with cost, worse tiers = harder consequences)
- Severity weighting (harm more common at lower tiers)
- Applicability (moves must be contextually relevant to fire)

Key principle: worse outcome → worse complication. Engine picks, not narrator.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Complication:
    """A GM move triggered by a check result."""
    move_id: str                # e.g. "reveal_unwelcome_truth"
    severity: str               # soft, medium, hard, severe
    category: str               # core, faction, hostile, environmental, landscape
    description: str            # Human-readable description
    mechanical_effects: List[Dict[str, Any]] = field(default_factory=list)
    narrative_seed: str = ""    # Hint for narrator

    def to_dict(self) -> Dict[str, Any]:
        return {
            "move_id": self.move_id,
            "severity": self.severity,
            "category": self.category,
            "description": self.description,
            "mechanical_effects": self.mechanical_effects,
            "narrative_seed": self.narrative_seed,
        }


@dataclass
class ComplicationContext:
    """World state relevant to complication selection and parameterization."""
    # Location context
    location_id: str = ""
    location_display: str = ""
    location_dangers: List[str] = field(default_factory=list)
    location_threat_types: List[str] = field(default_factory=list)  # e.g., "faction", "landscape"

    # NPC context
    npcs_present: List[Dict[str, Any]] = field(default_factory=list)  # slim views: id, name, disposition, goals, knowledge
    hostile_npcs: List[Dict[str, Any]] = field(default_factory=list)

    # Player context
    player_resources: Dict[str, int] = field(default_factory=dict)    # CU, supplies, etc.
    player_inventory: List[Dict[str, Any]] = field(default_factory=list)
    player_condition_tracks: Dict[str, int] = field(default_factory=dict)  # physical/mental/social
    player_allies: List[Dict[str, Any]] = field(default_factory=list)
    player_goals: List[Dict[str, Any]] = field(default_factory=list)

    # World/narrative context
    hidden_elements: List[Dict[str, Any]] = field(default_factory=list)
    active_clocks: List[Dict[str, Any]] = field(default_factory=list)
    faction_tensions: List[Dict[str, Any]] = field(default_factory=list)
    recent_tick_events: List[Dict[str, Any]] = field(default_factory=list)

    # Action context (what triggered the complication)
    action_type: str = ""
    action_target: Optional[str] = None


# ---------------------------------------------------------------------------
# Severity weighting by outcome tier
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS: Dict[str, Dict[str, int]] = {
    "marginal":         {"soft": 60, "medium": 30, "hard": 10, "severe": 0},
    "partial_failure":  {"soft": 20, "medium": 40, "hard": 30, "severe": 10},
    "failure":          {"soft": 5,  "medium": 20, "hard": 50, "severe": 25},
    "fumble":           {"soft": 0,  "medium": 10, "hard": 40, "severe": 50},
}


# ---------------------------------------------------------------------------
# Core moves (always available when applicable)
# ---------------------------------------------------------------------------

CORE_MOVES: List[Dict[str, Any]] = [
    # Soft moves — foreshadow, information, setup
    {
        "id": "reveal_unwelcome_truth",
        "severity": "soft",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.hidden_elements) or bool(ctx.npcs_present),
    },
    {
        "id": "show_approaching_threat",
        "severity": "soft",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.active_clocks) or bool(ctx.location_dangers),
    },
    {
        "id": "announce_offscreen_badness",
        "severity": "soft",
        "category": "core",
        "applicable": lambda ctx: True,  # Always available
    },
    {
        "id": "tell_consequences_and_ask",
        "severity": "soft",
        "category": "core",
        "applicable": lambda ctx: True,
    },
    # Medium moves — real cost, recoverable
    {
        "id": "use_up_resources",
        "severity": "medium",
        "category": "core",
        "applicable": lambda ctx: (
            bool(ctx.player_inventory)
            or any(v > 0 for v in ctx.player_resources.values())
            or any(v > 1 for v in ctx.player_condition_tracks.values())
        ),
    },
    {
        "id": "time_passes",
        "severity": "medium",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.active_clocks) or True,
    },
    {
        "id": "make_them_buy",
        "severity": "medium",
        "category": "core",
        "applicable": lambda ctx: True,
    },
    {
        "id": "turn_move_back",
        "severity": "medium",
        "category": "core",
        "applicable": lambda ctx: True,
    },
    # Hard moves — material consequence
    {
        "id": "take_stuff",
        "severity": "hard",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.player_inventory),
    },
    {
        "id": "put_in_spot",
        "severity": "hard",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.player_allies) or bool(ctx.player_goals),
    },
    {
        "id": "deal_harm",
        "severity": "hard",
        "category": "core",
        "applicable": lambda ctx: True,
    },
    {
        "id": "separate_them",
        "severity": "hard",
        "category": "core",
        "applicable": lambda ctx: (
            bool(ctx.player_allies) or bool(ctx.location_dangers)
        ),
    },
    {
        "id": "npc_makes_move",
        "severity": "hard",
        "category": "core",
        "applicable": lambda ctx: any(
            npc.get("has_goals") for npc in ctx.npcs_present
        ),
    },
    # Severe moves — situation-changing
    {
        "id": "capture_seize",
        "severity": "severe",
        "category": "core",
        "applicable": lambda ctx: bool(ctx.hostile_npcs) or bool(ctx.location_dangers),
    },
    {
        "id": "force_new_dq",
        "severity": "severe",
        "category": "core",
        "applicable": lambda ctx: True,
    },
]


# ---------------------------------------------------------------------------
# Threat-contextual moves (added when threat type active at location)
# ---------------------------------------------------------------------------

FACTION_MOVES: List[Dict[str, Any]] = [
    {"id": "claim_jurisdiction", "severity": "medium", "category": "faction",
     "applicable": lambda ctx: "faction" in ctx.location_threat_types},
    {"id": "pressure_allies", "severity": "hard", "category": "faction",
     "applicable": lambda ctx: "faction" in ctx.location_threat_types and bool(ctx.player_allies)},
    {"id": "demand_concession", "severity": "medium", "category": "faction",
     "applicable": lambda ctx: "faction" in ctx.location_threat_types},
    {"id": "study_weakness", "severity": "soft", "category": "faction",
     "applicable": lambda ctx: "faction" in ctx.location_threat_types},
]

HOSTILE_INDIVIDUAL_MOVES: List[Dict[str, Any]] = [
    {"id": "attack_vulnerable_moment", "severity": "hard", "category": "hostile",
     "applicable": lambda ctx: bool(ctx.hostile_npcs)},
    {"id": "offer_with_strings", "severity": "medium", "category": "hostile",
     "applicable": lambda ctx: bool(ctx.hostile_npcs)},
    {"id": "display_obsession", "severity": "soft", "category": "hostile",
     "applicable": lambda ctx: bool(ctx.hostile_npcs)},
]

ENVIRONMENTAL_MOVES: List[Dict[str, Any]] = [
    {"id": "corrupt_damage", "severity": "hard", "category": "environmental",
     "applicable": lambda ctx: "environmental" in ctx.location_threat_types},
    {"id": "lingering_effect", "severity": "medium", "category": "environmental",
     "applicable": lambda ctx: "environmental" in ctx.location_threat_types},
    {"id": "neglect_obligations", "severity": "soft", "category": "environmental",
     "applicable": lambda ctx: "environmental" in ctx.location_threat_types},
]

LANDSCAPE_MOVES: List[Dict[str, Any]] = [
    {"id": "bar_the_way", "severity": "medium", "category": "landscape",
     "applicable": lambda ctx: "landscape" in ctx.location_threat_types},
    {"id": "shift_rearrange", "severity": "medium", "category": "landscape",
     "applicable": lambda ctx: "landscape" in ctx.location_threat_types},
    {"id": "present_guardian", "severity": "hard", "category": "landscape",
     "applicable": lambda ctx: "landscape" in ctx.location_threat_types},
    {"id": "disgorge_something", "severity": "severe", "category": "landscape",
     "applicable": lambda ctx: "landscape" in ctx.location_threat_types},
]


def _all_moves() -> List[Dict[str, Any]]:
    """Combine all move pools."""
    return (
        CORE_MOVES
        + FACTION_MOVES
        + HOSTILE_INDIVIDUAL_MOVES
        + ENVIRONMENTAL_MOVES
        + LANDSCAPE_MOVES
    )


# ---------------------------------------------------------------------------
# Selection logic
# ---------------------------------------------------------------------------

def _filter_applicable(context: ComplicationContext) -> List[Dict[str, Any]]:
    """Return all moves whose applicability conditions are met."""
    return [m for m in _all_moves() if m["applicable"](context)]


def _weighted_select(
    applicable: List[Dict[str, Any]],
    outcome_tier: str,
    rng: random.Random,
) -> Optional[Dict[str, Any]]:
    """Select one move from applicable pool, weighted by severity for tier."""
    tier_key = outcome_tier.lower()
    weights_map = SEVERITY_WEIGHTS.get(tier_key)
    if not weights_map:
        return None

    # Build weighted pool
    pool: List[tuple] = []  # (move, weight)
    for move in applicable:
        sev = move["severity"]
        w = weights_map.get(sev, 0)
        if w > 0:
            pool.append((move, w))

    if not pool:
        return None

    # Weighted random selection
    total = sum(w for _, w in pool)
    r = rng.uniform(0, total)
    upto = 0
    for move, w in pool:
        upto += w
        if r <= upto:
            return move
    return pool[-1][0]  # Fallback


# ---------------------------------------------------------------------------
# Parameterization — fills specific details from game state
# ---------------------------------------------------------------------------

def _param_reveal_unwelcome_truth(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    if ctx.hidden_elements:
        elem = rng.choice(ctx.hidden_elements)
        content = elem.get("content", "something you didn't want to know")
        desc = f"You learn an unwelcome truth: {content}"
        effects = [{"type": "information_revealed", "source": elem.get("source_type", "unknown")}]
    elif ctx.npcs_present:
        npc = rng.choice(ctx.npcs_present)
        desc = f"You learn something uncomfortable about {npc.get('name', 'them')}"
        effects = [{"type": "npc_info_revealed", "npc_id": npc.get("id", "")}]
    else:
        desc = "A truth surfaces that complicates matters."
        effects = []
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="reveal",
    )


def _param_show_approaching_threat(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    if ctx.active_clocks:
        clock = rng.choice(ctx.active_clocks)
        name = clock.get("name", "something")
        desc = f"Signs of approaching threat: {name} draws nearer."
        effects = [{"type": "clock_foreshadow", "clock_id": clock.get("id", ""), "segments": 1}]
    elif ctx.location_dangers:
        danger = rng.choice(ctx.location_dangers)
        desc = f"The {danger} is getting worse."
        effects = [{"type": "danger_escalation", "danger": danger}]
    else:
        desc = "Something approaches — you can feel it."
        effects = []
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="foreshadow",
    )


def _param_announce_offscreen_badness(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    if ctx.recent_tick_events:
        ev = rng.choice(ctx.recent_tick_events)
        desc = f"Word reaches you: {ev.get('description', 'something happened elsewhere')}"
        effects = [{"type": "event_surfaced", "event_id": ev.get("id", "")}]
    else:
        desc = "News of trouble from another region filters through."
        effects = [{"type": "ambient_badness"}]
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="offscreen",
    )


def _param_use_up_resources(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    # Pick a resource to deplete
    if ctx.player_inventory:
        item = rng.choice(ctx.player_inventory)
        name = item.get("name", "something")
        desc = f"Your {name} is damaged or depleted."
        effects = [{"type": "resource_lost", "resource": item.get("id", ""), "amount": 1}]
    elif any(v > 0 for v in ctx.player_resources.values()):
        keys = [k for k, v in ctx.player_resources.items() if v > 0]
        key = rng.choice(keys)
        desc = f"You expend {key}."
        effects = [{"type": "resource_lost", "resource": key, "amount": 1}]
    else:
        desc = "You use up effort, energy, or goodwill."
        effects = [{"type": "cost_abstract"}]
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="resource_cost",
    )


def _param_deal_harm(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    # Pick condition track based on action type
    if ctx.action_type == "social":
        track = "social"
    elif ctx.action_type in ("investigate", "wait", "exposition"):
        track = "mental"
    else:
        track = "physical"

    current = ctx.player_condition_tracks.get(track, 5)
    amount = 1 if current > 1 else 0

    desc = f"You take {track} harm."
    effects = [{"type": "harm_dealt", "track": track, "amount": amount}]
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="harm",
    )


def _param_npc_makes_move(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    npcs_with_goals = [n for n in ctx.npcs_present if n.get("has_goals")]
    if not npcs_with_goals:
        return _param_generic(move, ctx, rng)

    npc = rng.choice(npcs_with_goals)
    name = npc.get("name", "someone")
    desc = f"{name} acts on their own agenda, complicating your situation."
    effects = [
        {"type": "npc_action", "npc_id": npc.get("id", ""),
         "action": "pursue_goal"}
    ]
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="npc_action",
    )


def _param_time_passes(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    desc = "This took longer than expected. Time slips."
    effects = [{"type": "time_cost", "extra_hours": 3}]
    if ctx.active_clocks:
        clock = rng.choice(ctx.active_clocks)
        effects.append({"type": "clock_advance", "clock_id": clock.get("id", ""), "segments": 1})
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=effects,
        narrative_seed="time_cost",
    )


def _param_generic(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    """Fallback parameterizer for moves without specific handlers."""
    generic_descs = {
        "tell_consequences_and_ask": "The path forward is clear — and so is its cost.",
        "make_them_buy": "You can have what you want, but it will cost you.",
        "turn_move_back": "Your approach has created a new problem.",
        "take_stuff": "Something valuable is lost or taken.",
        "put_in_spot": "Someone you care about is now exposed.",
        "separate_them": "You're cut off from something you were counting on.",
        "capture_seize": "Something is seized from you — by force or circumstance.",
        "force_new_dq": "The situation escalates beyond what you planned for.",
        # Faction
        "claim_jurisdiction": "A faction claims authority over what you're doing.",
        "pressure_allies": "A faction leans on someone close to you.",
        "demand_concession": "A faction demands something in return.",
        "study_weakness": "Someone is watching you carefully — looking for leverage.",
        # Hostile individual
        "attack_vulnerable_moment": "An enemy strikes when you're exposed.",
        "offer_with_strings": "An offer arrives — tempting, but with hidden costs.",
        "display_obsession": "Someone's obsession manifests in an uncomfortable way.",
        # Environmental
        "corrupt_damage": "The environment leaves its mark on something you valued.",
        "lingering_effect": "The place has left a lingering effect on you.",
        "neglect_obligations": "Something important has been neglected while you were focused here.",
        # Landscape
        "bar_the_way": "A path forward is barred.",
        "shift_rearrange": "The space itself has changed around you.",
        "present_guardian": "A guardian or warden stands in your path.",
        "disgorge_something": "The place vomits forth something unexpected.",
    }
    desc = generic_descs.get(move["id"], "Something complicates your situation.")
    return Complication(
        move_id=move["id"], severity=move["severity"], category=move["category"],
        description=desc, mechanical_effects=[],
        narrative_seed=move["id"],
    )


_PARAMETERIZERS: Dict[str, Callable] = {
    "reveal_unwelcome_truth": _param_reveal_unwelcome_truth,
    "show_approaching_threat": _param_show_approaching_threat,
    "announce_offscreen_badness": _param_announce_offscreen_badness,
    "use_up_resources": _param_use_up_resources,
    "deal_harm": _param_deal_harm,
    "npc_makes_move": _param_npc_makes_move,
    "time_passes": _param_time_passes,
}


def _parameterize(
    move: Dict, ctx: ComplicationContext, rng: random.Random
) -> Complication:
    """Fill in specific details from game state for a selected move."""
    fn = _PARAMETERIZERS.get(move["id"], _param_generic)
    return fn(move, ctx, rng)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_complications(
    outcome_tier: str,
    context: ComplicationContext,
    rng: random.Random,
) -> List[Complication]:
    """Generate complications for a given outcome tier.

    Rules:
    - CRITICAL / FULL: 0 complications
    - MARGINAL: 1 complication (success with cost — the PBTA 7-9 band)
    - PARTIAL_FAILURE: 1 complication
    - FAILURE: 1 complication (harder)
    - FUMBLE: 2 complications (severe)
    """
    tier_key = outcome_tier.lower()
    if tier_key not in SEVERITY_WEIGHTS:
        return []

    num_complications = 2 if tier_key == "fumble" else 1

    applicable = _filter_applicable(context)
    if not applicable:
        return []

    complications: List[Complication] = []
    for _ in range(num_complications):
        move = _weighted_select(applicable, tier_key, rng)
        if move is None:
            break
        complications.append(_parameterize(move, context, rng))

    return complications
