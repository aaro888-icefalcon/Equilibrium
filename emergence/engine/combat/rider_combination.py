"""Rider combination system for the Emergence combat engine (Rev 4).

Combines 2 same-type riders on one action.
Cost = sum of individual costs + 1 pool tax.
Both effects apply parasitically on the action's outcome tier.

Constraints:
- Both riders must be the same type (both strike, both maneuver, etc.)
- Posture riders cannot be combined (they're pure passives)
- Maximum 2 riders per combination
- Pool tax is always +1 on top of the sum of individual costs

Uses only the Python standard library.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


def validate_combination(
    rider_a: Dict[str, Any],
    rider_b: Dict[str, Any],
) -> Tuple[bool, str]:
    """Validate that two riders can be combined.

    Returns (valid, reason_string).
    """
    type_a = rider_a.get("rider_type", "")
    type_b = rider_b.get("rider_type", "")

    if type_a != type_b:
        return False, f"Type mismatch: {type_a} vs {type_b}"

    if type_a == "posture":
        return False, "Posture riders cannot be combined (pure passives)"

    # Check not from same power (different-power requirement)
    power_a = rider_a.get("power_id", "")
    power_b = rider_b.get("power_id", "")
    slot_a = rider_a.get("slot_id", "")
    slot_b = rider_b.get("slot_id", "")
    if power_a == power_b and slot_a == slot_b:
        return False, "Cannot combine a rider with itself"

    return True, "ok"


def compute_combination_cost(
    rider_a: Dict[str, Any],
    rider_b: Dict[str, Any],
) -> int:
    """Compute total pool cost for combining two riders: sum + 1 tax."""
    cost_a = rider_a.get("pool_cost", 0)
    cost_b = rider_b.get("pool_cost", 0)
    return cost_a + cost_b + 1


def resolve_combined_riders(
    rider_a: Dict[str, Any],
    rider_b: Dict[str, Any],
    verb_result: Any,
    success_tier: str,
) -> Dict[str, Any]:
    """Apply both riders' effects parasitically on the action's outcome.

    Returns dict with combined effects.
    """
    effects_a = _apply_rider_effect(rider_a, success_tier)
    effects_b = _apply_rider_effect(rider_b, success_tier)

    return {
        "rider_a": {
            "power_id": rider_a.get("power_id", ""),
            "slot_id": rider_a.get("slot_id", ""),
            "effects": effects_a,
        },
        "rider_b": {
            "power_id": rider_b.get("power_id", ""),
            "slot_id": rider_b.get("slot_id", ""),
            "effects": effects_b,
        },
        "total_cost": compute_combination_cost(rider_a, rider_b),
    }


def _apply_rider_effect(rider: Dict[str, Any], success_tier: str) -> Dict[str, Any]:
    """Apply a single rider's effect based on the success tier."""
    params = rider.get("effect_parameters", {})
    rider_type = rider.get("rider_type", "")

    # Riders only apply on success (marginal or better)
    if success_tier in ("failure", "fumble", "partial_failure"):
        return {"applied": False, "reason": "action_failed"}

    effects: Dict[str, Any] = {"applied": True}

    if rider_type == "strike":
        effects["bonus_damage"] = params.get("bonus_damage", 1)
        effects["bonus_status"] = params.get("status_on_crit") if success_tier == "critical" else None
    elif rider_type == "maneuver":
        effects["bonus_movement"] = params.get("bonus_movement", 0)
        effects["bonus_effect"] = params.get("bonus_effect", "")
    elif rider_type == "parley":
        effects["bonus_social"] = params.get("bonus_social", 0)
        effects["bonus_effect"] = params.get("bonus_effect", "")
    elif rider_type == "assess":
        effects["bonus_info"] = params.get("bonus_info", 1)
    elif rider_type == "finisher":
        effects["bonus_damage"] = params.get("bonus_damage", 2)

    return effects
