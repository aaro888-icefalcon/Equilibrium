"""Posture rider system for the Emergence combat engine (Rev 4).

Posture riders are pure passives — always-on while armed. Max 2 armed
simultaneously. Each armed rider reduces effective_pool_max by 1.

9 sub-categories:
- reactive_defense: reduce incoming damage
- reactive_offense: counter damage on incoming attack
- reactive_status: apply status to attacker on incoming attack
- periodic: effect at end of each round
- aura_ally: buff allies in range
- aura_enemy: debuff enemies in range
- awareness: detection flags
- anchor: movement immunity
- amplify: damage bonus on crit

Uses only the Python standard library.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from emergence.engine.combat.pool import recalc_effective_pool_max
from emergence.engine.combat.postures import validate_posture_rider_compat


# ---------------------------------------------------------------------------
# Arm / disarm
# ---------------------------------------------------------------------------

def arm_rider(
    combatant: Any,
    power_id: str,
    rider_spec: Dict[str, Any],
    posture: Optional[str] = None,
) -> bool:
    """Arm a posture rider on a combatant. Returns True on success.

    Enforces: max 2 armed, posture compatibility.
    """
    armed = getattr(combatant, "armed_posture_riders", [])
    if len(armed) >= 2:
        return False

    posture = posture or getattr(combatant, "current_posture", "parry")
    sub_cat = rider_spec.get("sub_category", "")
    compat = rider_spec.get("compatible_postures", [])
    if not validate_posture_rider_compat(sub_cat, posture, compat):
        return False

    entry = {
        "power_id": power_id,
        "slot_id": rider_spec.get("slot_id", ""),
        "sub_category": sub_cat,
        "effect_parameters": rider_spec.get("effect_parameters", {}),
        "compatible_postures": compat,
    }
    armed.append(entry)
    combatant.armed_posture_riders = armed
    recalc_effective_pool_max(combatant)
    return True


def disarm_rider(combatant: Any, power_id: str, slot_id: str = "") -> bool:
    """Disarm a specific rider from a combatant. Returns True if found and removed."""
    armed = getattr(combatant, "armed_posture_riders", [])
    for i, r in enumerate(armed):
        if r["power_id"] == power_id and (not slot_id or r.get("slot_id") == slot_id):
            armed.pop(i)
            combatant.armed_posture_riders = armed
            recalc_effective_pool_max(combatant)
            return True
    return False


def disarm_all(combatant: Any) -> List[Dict[str, Any]]:
    """Disarm all riders. Returns list of disarmed rider entries."""
    armed = getattr(combatant, "armed_posture_riders", [])
    combatant.armed_posture_riders = []
    recalc_effective_pool_max(combatant)
    return armed


# ---------------------------------------------------------------------------
# Sub-category handlers
# ---------------------------------------------------------------------------

def apply_reactive_defense(rider_params: Dict[str, Any], incoming_damage: int) -> int:
    """Return damage reduction from a reactive_defense rider."""
    reduction = rider_params.get("damage_reduction", 1)
    return min(reduction, incoming_damage)


def apply_reactive_offense(rider_params: Dict[str, Any]) -> int:
    """Return counter damage dealt to attacker from reactive_offense rider."""
    return rider_params.get("counter_damage", 1)


def apply_reactive_status(rider_params: Dict[str, Any]) -> Optional[str]:
    """Return status name to apply to attacker, or None."""
    return rider_params.get("status_to_apply")


def apply_periodic(rider_params: Dict[str, Any], combatant: Any) -> Dict[str, Any]:
    """Apply periodic effect at end of round. Returns dict of effects applied."""
    effects = {}
    heal = rider_params.get("heal_physical", 0)
    if heal > 0:
        phy = getattr(combatant, "phy", 0)
        new_phy = max(0, phy - heal)
        combatant.phy = new_phy
        effects["healed_physical"] = phy - new_phy

    pool_regen = rider_params.get("pool_regen", 0)
    if pool_regen > 0:
        pool = getattr(combatant, "pool", 0)
        pool_max = getattr(combatant, "pool_max", 0)
        gain = min(pool_regen, pool_max - pool)
        combatant.pool = pool + gain
        effects["pool_regenerated"] = gain

    return effects


def apply_aura_ally(rider_params: Dict[str, Any], allies: List[Any]) -> List[Dict[str, Any]]:
    """Apply aura buff to allies. Returns list of effects."""
    effects = []
    buff = rider_params.get("ally_buff", {})
    for ally in allies:
        effects.append({"target": getattr(ally, "id", ""), "buff": buff})
    return effects


def apply_aura_enemy(rider_params: Dict[str, Any], enemies: List[Any]) -> List[Dict[str, Any]]:
    """Apply aura debuff to enemies. Returns list of effects."""
    effects = []
    debuff = rider_params.get("enemy_debuff", {})
    for enemy in enemies:
        effects.append({"target": getattr(enemy, "id", ""), "debuff": debuff})
    return effects


def apply_awareness(rider_params: Dict[str, Any]) -> Dict[str, Any]:
    """Return awareness detection flags."""
    return {
        "detect_hidden": rider_params.get("detect_hidden", False),
        "detect_range": rider_params.get("detect_range", 0),
    }


def apply_anchor(rider_params: Dict[str, Any]) -> Dict[str, Any]:
    """Return anchor (movement immunity) flags."""
    return {
        "immune_forced_movement": True,
        "disrupt_resistance": rider_params.get("disrupt_resistance", 2),
    }


def apply_amplify(rider_params: Dict[str, Any], is_crit: bool) -> int:
    """Return bonus damage from amplify rider (may be crit-conditional)."""
    if rider_params.get("crit_only", False) and not is_crit:
        return 0
    return rider_params.get("bonus_damage", 1)


# ---------------------------------------------------------------------------
# Aggregate application
# ---------------------------------------------------------------------------

def apply_incoming_attack_riders(
    combatant: Any,
    attack_event: Dict[str, Any],
) -> Dict[str, Any]:
    """Apply all armed passive riders to an incoming attack event.

    Returns aggregated effects dict.
    """
    armed = getattr(combatant, "armed_posture_riders", [])
    total_reduction = 0
    total_counter = 0
    statuses_to_apply: List[str] = []

    for rider in armed:
        sub = rider.get("sub_category", "")
        params = rider.get("effect_parameters", {})

        if sub == "reactive_defense":
            total_reduction += apply_reactive_defense(params, attack_event.get("damage", 0))
        elif sub == "reactive_offense":
            total_counter += apply_reactive_offense(params)
        elif sub == "reactive_status":
            status = apply_reactive_status(params)
            if status:
                statuses_to_apply.append(status)
        elif sub == "amplify":
            pass  # Amplify is for outgoing attacks, not incoming

    return {
        "damage_reduction": total_reduction,
        "counter_damage": total_counter,
        "statuses_to_apply_to_attacker": statuses_to_apply,
    }


def apply_end_of_round_riders(combatant: Any) -> List[Dict[str, Any]]:
    """Apply periodic riders at end of round. Returns list of effect dicts."""
    armed = getattr(combatant, "armed_posture_riders", [])
    effects = []

    for rider in armed:
        sub = rider.get("sub_category", "")
        params = rider.get("effect_parameters", {})

        if sub == "periodic":
            effect = apply_periodic(params, combatant)
            if effect:
                effects.append({"rider": rider.get("slot_id", ""), "effects": effect})

    return effects
