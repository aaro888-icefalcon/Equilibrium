"""Posture system for the Emergence combat engine (Rev 4).

Four postures define defensive behavior:
- PARRY: roll per+agi vs attacker total; Full negates + counter-step.
- BLOCK: flat damage reduction = might // 2.
- DODGE: roll agi+ins vs attacker total; Full negates, Fail = full damage.
- AGGRESSIVE: no defense roll; attacker hits at TN 10 flat.

Uses only the Python standard library.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from emergence.engine.combat.resolution import roll_check, SuccessTier


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PARRY = "parry"
BLOCK = "block"
DODGE = "dodge"
AGGRESSIVE = "aggressive"

ALL_POSTURES = frozenset({PARRY, BLOCK, DODGE, AGGRESSIVE})

# Postures that allow defensive rolls
DEFENSIVE_POSTURES = frozenset({PARRY, BLOCK, DODGE})


# ---------------------------------------------------------------------------
# Posture defense resolution
# ---------------------------------------------------------------------------

def resolve_posture_defense(
    target: Any,
    posture: str,
    attacker_total: int,
    rng: random.Random,
) -> Dict[str, Any]:
    """Resolve posture-based defense against an incoming attack.

    Args:
        target: CombatantRecord (or duck-typed object with attribute fields).
        posture: Current posture string.
        attacker_total: The attacker's roll total to beat.
        rng: Deterministic random source.

    Returns:
        Dict with keys:
            negated (bool): True if the attack is fully negated.
            damage_reduction (int): Flat damage reduction to apply.
            counter_bonus (int): Bonus to next attack from counter-step.
            defender_roll (Optional[dict]): Roll details if a roll was made.
    """
    if posture == AGGRESSIVE:
        return {
            "negated": False,
            "damage_reduction": 0,
            "counter_bonus": 0,
            "defender_roll": None,
        }

    if posture == BLOCK:
        might = getattr(target, "might", 6)
        reduction = might // 2
        return {
            "negated": False,
            "damage_reduction": reduction,
            "counter_bonus": 0,
            "defender_roll": None,
        }

    if posture == PARRY:
        # Roll perception + agility vs attacker_total as TN
        per = getattr(target, "perception", 6)
        agi = getattr(target, "agility", 6)
        result = roll_check(per, agi, [], attacker_total, rng)
        tier = SuccessTier(result.tier)
        if tier in (SuccessTier.CRITICAL, SuccessTier.FULL):
            return {
                "negated": True,
                "damage_reduction": 0,
                "counter_bonus": 1,
                "defender_roll": {"d1": result.d1, "d2": result.d2, "total": result.total, "tier": result.tier},
            }
        elif tier == SuccessTier.MARGINAL:
            return {
                "negated": True,
                "damage_reduction": 0,
                "counter_bonus": 0,
                "defender_roll": {"d1": result.d1, "d2": result.d2, "total": result.total, "tier": result.tier},
            }
        else:
            return {
                "negated": False,
                "damage_reduction": 0,
                "counter_bonus": 0,
                "defender_roll": {"d1": result.d1, "d2": result.d2, "total": result.total, "tier": result.tier},
            }

    if posture == DODGE:
        # Roll agility + insight vs attacker_total as TN
        agi = getattr(target, "agility", 6)
        ins = getattr(target, "insight", 6)
        result = roll_check(agi, ins, [], attacker_total, rng)
        tier = SuccessTier(result.tier)
        if tier in (SuccessTier.CRITICAL, SuccessTier.FULL, SuccessTier.MARGINAL):
            return {
                "negated": True,
                "damage_reduction": 0,
                "counter_bonus": 0,
                "defender_roll": {"d1": result.d1, "d2": result.d2, "total": result.total, "tier": result.tier},
            }
        else:
            return {
                "negated": False,
                "damage_reduction": 0,
                "counter_bonus": 0,
                "defender_roll": {"d1": result.d1, "d2": result.d2, "total": result.total, "tier": result.tier},
            }

    # Unknown posture — treat as aggressive (no defense)
    return {
        "negated": False,
        "damage_reduction": 0,
        "counter_bonus": 0,
        "defender_roll": None,
    }


def get_attacker_tn_modifier(target_posture: str) -> int:
    """Return TN modifier for attacking a target in the given posture.

    Aggressive targets are easier to hit: attacker gets -1 to TN (easier).
    """
    if target_posture == AGGRESSIVE:
        return -1
    return 0


def change_posture(combatant: Any, new_posture: str) -> str:
    """Change a combatant's posture. Returns the old posture."""
    if new_posture not in ALL_POSTURES:
        raise ValueError(f"Invalid posture: {new_posture}")
    old = getattr(combatant, "current_posture", PARRY)
    combatant.current_posture = new_posture
    return old


def validate_posture_rider_compat(rider_sub_category: str, posture: str,
                                   compatible_postures: List[str]) -> bool:
    """Check if a posture rider is compatible with the current posture.

    If compatible_postures is empty, the rider is compatible with all postures.
    Defensive riders are never compatible with Aggressive posture.
    """
    if posture == AGGRESSIVE and rider_sub_category in (
        "reactive_defense", "reactive_offense", "reactive_status"
    ):
        return False
    if compatible_postures and posture not in compatible_postures:
        return False
    return True
