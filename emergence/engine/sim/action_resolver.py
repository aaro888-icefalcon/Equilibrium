"""Dice-backed action resolver for simulation mode.

Replaces the hardcoded RNG in player_actions.py with the dual-die system
from combat/resolution.py. Implements the Declare-Determine-Describe pipeline:

1. Player declares intent + approach (ActionDeclaration)
2. Engine determines outcome via three-gate check + dice roll
3. Engine returns ActionResolution with outcomes and consequences pre-applied

All actions resolve as risky/standard (no Position/Effect yet).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from emergence.engine.combat.resolution import (
    CheckResult,
    SuccessTier,
    roll_check,
)
from emergence.engine.schemas.world import (
    Location,
    NPC,
    Clock,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ActionDeclaration:
    """Player's declared action, classified by narrator."""
    action_type: str            # social, physical, investigate, travel, medical, craft, wait, exposition
    approach: str               # persuade, force, observe, etc.
    target_id: Optional[str] = None   # NPC or object ID
    skill_id: Optional[str] = None    # Optional skill to use
    free_text: str = ""               # Player's original declaration


@dataclass
class ActionResolution:
    """Full result of resolving an action."""
    declaration: ActionDeclaration
    gate_result: str = ""               # "rolled", "auto_success", "auto_fail", "no_roll"
    check_result: Optional[Dict[str, Any]] = None  # Serialized CheckResult
    outcome_tier: str = ""              # SuccessTier value if rolled
    tn: int = 0
    primary_die: int = 0
    secondary_die: int = 0
    modifiers: List[Dict[str, Any]] = field(default_factory=list)
    complications: List[Dict[str, Any]] = field(default_factory=list)
    state_deltas: Dict[str, Any] = field(default_factory=dict)
    narrative_hints: List[str] = field(default_factory=list)
    npc_interaction: Optional[Dict[str, Any]] = None
    time_cost_days: int = 0
    new_location: Optional[str] = None
    encounter_triggered: bool = False
    scene_state_changes: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "declaration": {
                "action_type": self.declaration.action_type,
                "approach": self.declaration.approach,
                "target_id": self.declaration.target_id,
                "skill_id": self.declaration.skill_id,
                "free_text": self.declaration.free_text,
            },
            "gate_result": self.gate_result,
            "outcome_tier": self.outcome_tier,
            "tn": self.tn,
            "primary_die": self.primary_die,
            "secondary_die": self.secondary_die,
            "modifiers": self.modifiers,
            "complications": self.complications,
            "state_deltas": self.state_deltas,
            "narrative_hints": self.narrative_hints,
            "time_cost_days": self.time_cost_days,
            "new_location": self.new_location,
            "encounter_triggered": self.encounter_triggered,
            "scene_state_changes": self.scene_state_changes,
        }
        if self.check_result:
            d["check_result"] = self.check_result
        if self.npc_interaction:
            d["npc_interaction"] = self.npc_interaction
        return d


# ---------------------------------------------------------------------------
# Approach → attribute pair mapping
# ---------------------------------------------------------------------------

APPROACH_ATTRIBUTES: Dict[str, Tuple[str, str]] = {
    # Social
    "persuade": ("will", "insight"),
    "intimidate": ("will", "might"),
    "deceive": ("insight", "agility"),
    "reason": ("insight", "will"),
    # Physical
    "force": ("strength", "might"),
    "stealth": ("agility", "perception"),
    "speed": ("agility", "strength"),
    "endurance": ("strength", "will"),
    # Investigate
    "observe": ("perception", "insight"),
    "search": ("perception", "agility"),
    "analyze": ("insight", "will"),
    "ask_around": ("insight", "perception"),
    # Travel
    "direct": ("agility", "strength"),
    "cautious": ("perception", "agility"),
    "fast": ("agility", "strength"),
    # Medical
    "treat": ("insight", "perception"),
    "diagnose": ("insight", "will"),
    "stabilize": ("insight", "agility"),
    # Craft
    "build": ("insight", "strength"),
    "repair": ("perception", "strength"),
    "improvise": ("insight", "agility"),
}

# Default attribute pairs by action type (fallback if approach not in table)
ACTION_TYPE_DEFAULTS: Dict[str, Tuple[str, str]] = {
    "social": ("will", "insight"),
    "physical": ("strength", "agility"),
    "investigate": ("perception", "insight"),
    "travel": ("agility", "strength"),
    "medical": ("insight", "perception"),
    "craft": ("insight", "strength"),
}

# Skill proficiency → TN modifier
_PROF_TO_TN_MOD = [
    (1, 3, -1),
    (4, 6, -2),
    (7, 9, -3),
    (10, 10, -4),
]


# ---------------------------------------------------------------------------
# TN calculation
# ---------------------------------------------------------------------------

def _skill_proficiency(skill_uses: int) -> int:
    """Convert skill use count to proficiency level (0-10)."""
    thresholds = [5, 20, 60, 150, 350, 750, 1500, 3000, 7000, 15000]
    level = 0
    for t in thresholds:
        if skill_uses >= t:
            level += 1
        else:
            break
    return level


def _proficiency_tn_mod(proficiency: int) -> int:
    """Convert proficiency level to TN modifier."""
    for low, high, mod in _PROF_TO_TN_MOD:
        if low <= proficiency <= high:
            return mod
    if proficiency >= 10:
        return -4
    return 0


def calculate_tn(
    base: int = 10,
    npc_disposition: Optional[int] = None,
    skill_uses: int = 0,
    location_danger_count: int = 0,
) -> int:
    """Calculate target number for an action.

    Args:
        base: Base TN (default 10 = STANDARD).
        npc_disposition: NPC disposition (-3 to +3). Each point below 0 adds +1.
        skill_uses: Player's skill use count for the relevant skill.
        location_danger_count: Number of active dangers at location.

    Returns:
        Clamped TN in [7, 22].
    """
    tn = base

    # NPC disposition modifier: below 0 makes it harder
    if npc_disposition is not None and npc_disposition < 0:
        tn += abs(npc_disposition)

    # Skill proficiency reduces TN
    prof = _skill_proficiency(skill_uses)
    tn += _proficiency_tn_mod(prof)  # Negative, so reduces TN

    # Location danger adds difficulty
    if location_danger_count > 0:
        tn += min(location_danger_count, 2)

    return max(7, min(22, tn))


# ---------------------------------------------------------------------------
# Three-gate check
# ---------------------------------------------------------------------------

def three_gate_check(
    primary_die: int,
    secondary_die: int,
    total_modifier: int,
    tn: int,
    has_failure_cost: bool,
) -> str:
    """Determine whether to roll dice or auto-resolve.

    Three gates:
    1. Can succeed? (max possible roll >= TN)
    2. Can fail? (min possible roll < TN)
    3. Cost to failure? (some consequence exists for failing)

    Returns:
        "auto_fail", "auto_success", or "roll"
    """
    clamped_mod = max(-6, min(6, total_modifier))
    max_possible = primary_die + secondary_die + clamped_mod
    min_possible = 2 + clamped_mod  # Both dice roll 1

    if max_possible < tn:
        return "auto_fail"
    if min_possible >= tn:
        return "auto_success"
    if not has_failure_cost:
        return "auto_success"  # Succeeds but may cost time
    return "roll"


# ---------------------------------------------------------------------------
# Failure cost assessment
# ---------------------------------------------------------------------------

def _has_failure_cost(
    declaration: ActionDeclaration,
    location: Location,
    npcs_present: List[NPC],
) -> bool:
    """Determine if failing this action has a real cost."""
    # Social actions against NPCs always have cost (patience, standing)
    if declaration.action_type == "social" and declaration.target_id:
        return True
    # Travel always has cost (time, potential encounter)
    if declaration.action_type == "travel":
        return True
    # Physical actions in dangerous locations have cost
    if declaration.action_type == "physical" and location.dangers:
        return True
    # Investigation has cost if there's time pressure or hostiles
    if declaration.action_type == "investigate" and (
        location.dangers or any(
            getattr(n, "standing_with_player_default", 0) <= -1
            for n in npcs_present
        )
    ):
        return True
    # Medical always has cost (patient's condition)
    if declaration.action_type == "medical":
        return True
    # Default: no cost (auto-succeed with time)
    return False


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------

def resolve_action(
    declaration: ActionDeclaration,
    player: Dict[str, Any],
    location: Location,
    npcs_present: List[NPC],
    clocks: Dict[str, Clock],
    rng: random.Random,
) -> ActionResolution:
    """Main resolution pipeline.

    1. Map approach → attribute pair → player die sizes
    2. Compute TN from context
    3. Run three-gate check
    4. If "roll": call roll_check()
    5. Compute complications (stub for now — Phase 1b)
    6. Return ActionResolution
    """
    resolution = ActionResolution(declaration=declaration)

    # Handle no-roll action types
    if declaration.action_type == "wait":
        resolution.gate_result = "no_roll"
        resolution.outcome_tier = "FULL"
        resolution.time_cost_days = 1
        resolution.narrative_hints = ["Time passes."]
        return resolution

    if declaration.action_type == "exposition":
        resolution.gate_result = "no_roll"
        resolution.outcome_tier = "FULL"
        resolution.time_cost_days = 0
        # Gather exposition info (expanded in Phase 1c)
        resolution.narrative_hints = _gather_exposition(
            declaration, location, npcs_present
        )
        return resolution

    # 1. Map approach → attribute pair
    attr_pair = APPROACH_ATTRIBUTES.get(
        declaration.approach,
        ACTION_TYPE_DEFAULTS.get(declaration.action_type, ("will", "insight")),
    )
    primary_attr, secondary_attr = attr_pair

    attributes = player.get("attributes", {})
    primary_die = attributes.get(primary_attr, 6)
    secondary_die = attributes.get(secondary_attr, 6)

    resolution.primary_die = primary_die
    resolution.secondary_die = secondary_die

    # 2. Compute TN
    npc_disposition = None
    target_npc = None
    if declaration.target_id:
        for npc in npcs_present:
            if npc.id == declaration.target_id:
                target_npc = npc
                npc_disposition = npc.standing_with_player_default
                break

    skill_uses = 0
    if declaration.skill_id:
        skills = player.get("skills", {})
        skill_uses = skills.get(declaration.skill_id, 0)

    tn = calculate_tn(
        base=10,
        npc_disposition=npc_disposition,
        skill_uses=skill_uses,
        location_danger_count=len(location.dangers),
    )
    resolution.tn = tn

    # Collect modifiers (for audit trail)
    mods_list: List[int] = []
    mod_details: List[Dict[str, Any]] = []

    # Skill synergy bonus (from skills.py)
    if declaration.skill_id and skill_uses > 0:
        prof = _skill_proficiency(skill_uses)
        if prof > 0:
            mod_details.append({
                "source": f"skill:{declaration.skill_id}",
                "proficiency": prof,
                "tn_effect": _proficiency_tn_mod(prof),
            })

    resolution.modifiers = mod_details

    # 3. Three-gate check
    has_cost = _has_failure_cost(declaration, location, npcs_present)
    gate = three_gate_check(
        primary_die, secondary_die,
        sum(mods_list), tn, has_cost,
    )
    resolution.gate_result = gate

    if gate == "auto_fail":
        resolution.outcome_tier = SuccessTier.FAILURE.value
        resolution.narrative_hints = ["This action cannot succeed."]
        resolution.time_cost_days = 0
        return resolution

    if gate == "auto_success":
        resolution.outcome_tier = SuccessTier.FULL.value
        resolution.narrative_hints = ["This is straightforward."]
        # Auto-success with time cost if no failure cost existed
        if not has_cost:
            resolution.time_cost_days = 1
        return resolution

    # 4. Roll dice
    check = roll_check(
        primary_die=primary_die,
        secondary_die=secondary_die,
        modifiers=mods_list,
        tn=tn,
        rng=rng,
    )
    resolution.outcome_tier = check.tier
    resolution.check_result = {
        "d1": check.d1,
        "d2": check.d2,
        "total": check.total,
        "tn": check.tn,
        "margin": check.margin,
        "tier": check.tier,
        "is_crit": check.is_crit,
        "is_fumble": check.is_fumble,
    }

    # 5. Apply outcome-specific effects
    _apply_outcome_effects(resolution, declaration, target_npc, location, rng)

    # 6. Generate complications (stub — replaced in Phase 1b)
    resolution.complications = _generate_complications_stub(
        resolution.outcome_tier, rng
    )

    return resolution


# ---------------------------------------------------------------------------
# Outcome effect application
# ---------------------------------------------------------------------------

def _apply_outcome_effects(
    resolution: ActionResolution,
    declaration: ActionDeclaration,
    target_npc: Optional[NPC],
    location: Location,
    rng: random.Random,
) -> None:
    """Apply outcome-specific effects based on tier and action type."""
    tier = resolution.outcome_tier

    # Travel
    if declaration.action_type == "travel":
        if tier in (SuccessTier.CRITICAL.value, SuccessTier.FULL.value,
                    SuccessTier.MARGINAL.value):
            # Find connection for destination
            dest = declaration.target_id
            if dest:
                resolution.new_location = dest
                resolution.time_cost_days = 1
                # Check for encounter during travel
                if tier == SuccessTier.MARGINAL.value:
                    resolution.encounter_triggered = rng.random() < 0.15
                resolution.narrative_hints.append(f"Traveling to {dest}.")
        else:
            resolution.time_cost_days = 1
            resolution.narrative_hints.append("Travel impeded.")

    # Social
    elif declaration.action_type == "social" and target_npc:
        npc_name = target_npc.display_name
        if tier == SuccessTier.CRITICAL.value:
            resolution.narrative_hints.append(
                f"{npc_name} responds very favorably."
            )
        elif tier == SuccessTier.FULL.value:
            resolution.narrative_hints.append(
                f"{npc_name} agrees to your request."
            )
        elif tier == SuccessTier.MARGINAL.value:
            resolution.narrative_hints.append(
                f"{npc_name} partially agrees, but at a cost."
            )
        elif tier == SuccessTier.PARTIAL_FAILURE.value:
            resolution.narrative_hints.append(
                f"{npc_name} is not convinced."
            )
        elif tier == SuccessTier.FAILURE.value:
            resolution.narrative_hints.append(
                f"{npc_name} refuses."
            )
        elif tier == SuccessTier.FUMBLE.value:
            resolution.narrative_hints.append(
                f"{npc_name} reacts badly."
            )

    # Investigation / observation
    elif declaration.action_type == "investigate":
        if tier in (SuccessTier.CRITICAL.value, SuccessTier.FULL.value):
            resolution.narrative_hints.append("Investigation succeeds.")
            if location.dangers:
                resolution.narrative_hints.append(
                    f"Dangers noticed: {', '.join(location.dangers[:2])}"
                )
        elif tier == SuccessTier.MARGINAL.value:
            resolution.narrative_hints.append("Partial information gained.")
        else:
            resolution.narrative_hints.append("Investigation yields nothing.")

    # Medical
    elif declaration.action_type == "medical":
        if tier in (SuccessTier.CRITICAL.value, SuccessTier.FULL.value):
            resolution.narrative_hints.append("Treatment succeeds.")
        elif tier == SuccessTier.MARGINAL.value:
            resolution.narrative_hints.append("Treatment partially effective.")
        else:
            resolution.narrative_hints.append("Treatment fails.")

    # Physical / craft
    else:
        if tier in (SuccessTier.CRITICAL.value, SuccessTier.FULL.value):
            resolution.narrative_hints.append("Action succeeds.")
        elif tier == SuccessTier.MARGINAL.value:
            resolution.narrative_hints.append("Action succeeds, barely.")
        else:
            resolution.narrative_hints.append("Action fails.")


# ---------------------------------------------------------------------------
# Exposition helper
# ---------------------------------------------------------------------------

def _gather_exposition(
    declaration: ActionDeclaration,
    location: Location,
    npcs_present: List[NPC],
) -> List[str]:
    """Gather exposition information (expanded in Phase 1c)."""
    hints: List[str] = []

    # Location details
    if location.dangers:
        hints.append(f"Known dangers: {', '.join(location.dangers)}")
    if location.opportunities:
        hints.append(f"Opportunities: {', '.join(location.opportunities)}")
    if location.description:
        hints.append(f"Location: {location.description}")

    # NPC info
    for npc in npcs_present:
        if npc.knowledge:
            for k in npc.knowledge[:2]:
                hints.append(f"{npc.display_name} knows about: {k.topic}")

    if not hints:
        hints.append("Nothing notable to report.")

    return hints


# ---------------------------------------------------------------------------
# Complication stub (replaced by Phase 1b)
# ---------------------------------------------------------------------------

def _generate_complications_stub(
    outcome_tier: str, rng: random.Random
) -> List[Dict[str, Any]]:
    """Stub complication generator. Returns empty list.

    Will be replaced by the full PBTA-style complication generator
    in Phase 1b (complications.py).
    """
    return []
