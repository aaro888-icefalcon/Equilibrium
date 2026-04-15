"""Pool mechanics for the Emergence combat engine (Rev 4).

Pool fuels power casts and rider combinations.
- base_pool_max = 3 + tier
- effective_pool_max = base_pool_max - armed_posture_rider_count
- Brace: minor action, +1 pool, cap 3 uses per combat

Uses only the Python standard library.
"""

from __future__ import annotations

from typing import Any


def compute_base_pool_max(tier: int) -> int:
    """Base pool max = 3 + tier."""
    return 3 + tier


def compute_effective_pool_max(base: int, armed_count: int) -> int:
    """Effective pool max = base - number of armed posture riders."""
    return max(0, base - armed_count)


def init_pool(combatant: Any) -> None:
    """Initialize pool fields on a combatant at combat start."""
    tier = getattr(combatant, "tier", 1)
    armed = getattr(combatant, "armed_posture_riders", [])
    combatant.base_pool_max = compute_base_pool_max(tier)
    combatant.pool_max = compute_effective_pool_max(combatant.base_pool_max, len(armed))
    combatant.pool = combatant.pool_max
    combatant.brace_uses = 3


def recalc_effective_pool_max(combatant: Any) -> None:
    """Recalculate effective pool max after arming/disarming riders."""
    armed = getattr(combatant, "armed_posture_riders", [])
    combatant.pool_max = compute_effective_pool_max(combatant.base_pool_max, len(armed))
    # If current pool exceeds new max, cap it
    if combatant.pool > combatant.pool_max:
        combatant.pool = combatant.pool_max


def can_spend_pool(combatant: Any, amount: int) -> bool:
    """Check if combatant can spend the given pool amount."""
    return getattr(combatant, "pool", 0) >= amount


def spend_pool(combatant: Any, amount: int) -> bool:
    """Deduct pool if possible. Returns True on success."""
    if not can_spend_pool(combatant, amount):
        return False
    combatant.pool -= amount
    return True


def resolve_brace(combatant: Any) -> bool:
    """Resolve a Brace minor action: +1 pool, cap 3 uses per combat.

    Returns True if brace succeeded, False if rejected.
    Rejection reasons: no uses left, already at effective max, incapacitated.
    """
    brace_uses = getattr(combatant, "brace_uses", 0)
    if brace_uses <= 0:
        return False

    pool = getattr(combatant, "pool", 0)
    pool_max = getattr(combatant, "pool_max", 0)
    if pool >= pool_max:
        return False

    # Check not incapacitated
    phy = getattr(combatant, "phy", 0)
    phy_max = getattr(combatant, "phy_max", 5)
    if phy >= phy_max:
        return False

    combatant.pool = min(pool + 1, pool_max)
    combatant.brace_uses = brace_uses - 1
    return True


def refill_pool(combatant: Any) -> None:
    """Refill pool to effective max (used at scene boundary)."""
    combatant.pool = getattr(combatant, "pool_max", 0)
    combatant.brace_uses = 3
