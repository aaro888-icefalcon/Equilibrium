"""Combat resolution system for the Emergence tactical RPG engine.

Implements core dice/check mechanics: attribute die rolls, modifier stacking,
success tier classification, tier gap modifiers, derived combat values, and
initiative ordering.  All randomness flows through an injected random.Random
instance so that results are fully deterministic under a given seed.

Uses only the Python standard library.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Sequence, Tuple

from emergence.engine.schemas import Combatant


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_DIE_SIZES = frozenset({4, 6, 8, 10, 12})

MODIFIER_CLAMP_MIN = -6
MODIFIER_CLAMP_MAX = 6

MOMENTUM_MIN = 0
MOMENTUM_MAX = 5


class Difficulty(Enum):
    """Named target-number presets."""
    TRIVIAL = 7
    STANDARD = 10
    HARD = 13
    EXTREME = 16
    HEROIC = 19
    MYTHIC = 22


TARGET_NUMBERS: Dict[str, int] = {d.name: d.value for d in Difficulty}


# ---------------------------------------------------------------------------
# Tier gap table
# ---------------------------------------------------------------------------

# Indexed by abs(gap); values are (higher_tier_mod, lower_tier_mod).
_TIER_GAP_TABLE: List[Tuple[int, int]] = [
    (0, 0),    # gap 0
    (1, 0),    # gap 1
    (2, -1),   # gap 2
    (3, -2),   # gap 3
    (4, -3),   # gap 4
    (5, -4),   # gap 5+
]


# ---------------------------------------------------------------------------
# SuccessTier enum
# ---------------------------------------------------------------------------

class SuccessTier(str, Enum):
    """Ordered result bands for a check."""
    CRITICAL = "critical"
    FULL = "full"
    MARGINAL = "marginal"
    PARTIAL_FAILURE = "partial_failure"
    FAILURE = "failure"
    FUMBLE = "fumble"


# ---------------------------------------------------------------------------
# CheckResult dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CheckResult:
    """Immutable result of a resolved check (Rev 4: dual-die sum).

    Attributes:
        d1:        Raw value of the first (primary attribute) die.
        d2:        Raw value of the second (secondary attribute) die.
        high:      max(d1, d2) -- kept for backward compat, but total now uses sum.
        total:     d1 + d2 + clamped modifiers.
        tn:        Target Number the check was rolled against.
        margin:    total - tn.
        tier:      The classified SuccessTier value (as a string for
                   serialization convenience).
        is_crit:   True if the result qualifies as a Critical Success.
        is_fumble: True if the result qualifies as a Fumble.
    """
    d1: int
    d2: int
    high: int
    total: int
    tn: int
    margin: int
    tier: str
    is_crit: bool
    is_fumble: bool


# ---------------------------------------------------------------------------
# Die rolling
# ---------------------------------------------------------------------------

def roll_die(size: int, rng: random.Random) -> int:
    """Roll a single die of the given *size* and return the result.

    *size* must be one of {4, 6, 8, 10, 12}.  If a size below 4 is passed
    (representing an attribute reduced below d4), the d4-1 rule applies:
    roll a d4, subtract 1, minimum 0.

    Args:
        size: Die face count (e.g. 4, 6, 8, 10, 12) or a value < 4 to
              trigger the degraded-die rule.
        rng:  A ``random.Random`` instance used for deterministic rolls.

    Returns:
        Integer result in [0, size] (0 only possible under the d4-1 rule).
    """
    if size < 4:
        # Attribute reduced below d4: roll d4, subtract 1, minimum 0.
        return max(rng.randint(1, 4) - 1, 0)
    if size not in VALID_DIE_SIZES:
        raise ValueError(
            f"Invalid die size {size}; must be one of {sorted(VALID_DIE_SIZES)} "
            f"or < 4 for the degraded-die rule."
        )
    return rng.randint(1, size)


# ---------------------------------------------------------------------------
# Success-tier classification
# ---------------------------------------------------------------------------

def classify_result(d1: int, d2: int, total: int, tn: int,
                    die1_max: int = 0, die2_max: int = 0) -> SuccessTier:
    """Classify a resolved check into a :class:`SuccessTier` (Rev 4).

    The classification rules (applied in priority order):

    1. **Fumble** -- both dice show 1 (regardless of total).
    2. **Auto-Critical** -- both dice show their max face value.
    3. **Critical** -- total >= TN + 5.
    4. **Full Success** -- TN < total < TN + 5 (i.e., TN+1 to TN+4).
    5. **Marginal** -- total == TN.
    6. **Partial Failure** -- total == TN - 1.
    7. **Failure** -- total < TN - 1.

    Note: double-1 fumble takes priority over everything.
    Auto-critical (both max) takes priority over band classification.
    """
    # Priority 1: double-ones is always a fumble.
    if d1 == 1 and d2 == 1:
        return SuccessTier.FUMBLE

    # Priority 2: both dice at max face value → auto-critical.
    if die1_max > 0 and die2_max > 0 and d1 == die1_max and d2 == die2_max:
        return SuccessTier.CRITICAL

    # Standard band classification per Rev 4 §3.2.
    if total >= tn + 5:
        return SuccessTier.CRITICAL
    if total > tn:
        return SuccessTier.FULL
    if total == tn:
        return SuccessTier.MARGINAL
    if total == tn - 1:
        return SuccessTier.PARTIAL_FAILURE
    return SuccessTier.FAILURE


# ---------------------------------------------------------------------------
# Core check resolution
# ---------------------------------------------------------------------------

def roll_check(
    primary_die: int,
    secondary_die: int,
    modifiers: Sequence[int],
    tn: int,
    rng: random.Random,
) -> CheckResult:
    """Roll a full check and return a :class:`CheckResult` (Rev 4: dual-die sum).

    Mechanics:
        1. Roll both attribute dice.
        2. Sum both dice: ``dice_sum = d1 + d2``.
        3. Sum all *modifiers* and clamp the total modifier to [-6, +6].
        4. ``total = dice_sum + clamped_modifier``.
        5. Classify the result into a success tier.

    Args:
        primary_die:   Die size for the primary attribute (e.g. 8 for d8).
        secondary_die: Die size for the secondary attribute.
        modifiers:     Sequence of signed integers applied to dice sum.
        tn:            Target Number.
        rng:           Deterministic random source.

    Returns:
        A fully populated :class:`CheckResult`.
    """
    d1 = roll_die(primary_die, rng)
    d2 = roll_die(secondary_die, rng)
    high = max(d1, d2)  # kept for backward compat

    # Clamp total modifier.
    raw_mod = sum(modifiers)
    clamped_mod = max(MODIFIER_CLAMP_MIN, min(MODIFIER_CLAMP_MAX, raw_mod))

    # Rev 4: total = d1 + d2 + mods (was: max(d1,d2) + mods)
    total = d1 + d2 + clamped_mod
    margin = total - tn
    tier = classify_result(d1, d2, total, tn,
                           die1_max=primary_die, die2_max=secondary_die)

    return CheckResult(
        d1=d1,
        d2=d2,
        high=high,
        total=total,
        tn=tn,
        margin=margin,
        tier=tier.value,
        is_crit=(tier is SuccessTier.CRITICAL),
        is_fumble=(tier is SuccessTier.FUMBLE),
    )


# ---------------------------------------------------------------------------
# Tier gap modifier
# ---------------------------------------------------------------------------

def tier_gap_modifier(attacker_tier: int, defender_tier: int) -> Tuple[int, int]:
    """Compute tier-gap modifiers for attacker and defender.

    Args:
        attacker_tier: Tier of the acting combatant.
        defender_tier: Tier of the opposing combatant.

    Returns:
        ``(attacker_mod, defender_mod)`` -- signed integers to include in
        each side's modifier list.  The higher-tier combatant receives a
        positive bonus; the lower-tier combatant receives zero or a
        negative penalty.

    Examples:
        >>> tier_gap_modifier(5, 3)
        (2, -1)
        >>> tier_gap_modifier(3, 5)
        (-1, 2)
        >>> tier_gap_modifier(4, 4)
        (0, 0)
    """
    gap = abs(attacker_tier - defender_tier)
    # Clamp to table range (5+ collapses to index 5).
    idx = min(gap, len(_TIER_GAP_TABLE) - 1)
    higher_mod, lower_mod = _TIER_GAP_TABLE[idx]

    if gap == 0:
        return (0, 0)
    if attacker_tier > defender_tier:
        return (higher_mod, lower_mod)
    # attacker_tier < defender_tier
    return (lower_mod, higher_mod)


# ---------------------------------------------------------------------------
# Derived combat values
# ---------------------------------------------------------------------------

def compute_defense_value(agility_die_size: int, armor_static: int) -> int:
    """Compute physical defense value (used as Attack TN).

    Formula: ``agility_die_size + armor_static``.
    """
    return agility_die_size + armor_static


def compute_mental_defense(will_die_size: int, aura_static: int) -> int:
    """Compute mental defense value (used as Power/Parley TN).

    Formula: ``will_die_size + aura_static``.
    """
    return will_die_size + aura_static


def compute_initiative_bonus(agility_die_size: int, perception_die_size: int) -> int:
    """Compute initiative bonus.

    Formula: ``max(agility_die_size, perception_die_size) // 2``.

    Results: d4->2, d6->3, d8->4, d10->5, d12->6.
    """
    return max(agility_die_size, perception_die_size) // 2


def compute_power_pool(will_die_size: int, tier: int) -> int:
    """Compute power-use pool for the scene.

    Formula: ``will_die_size // 2 + tier``.
    """
    return will_die_size // 2 + tier


def compute_resilience_bonus(tier: int) -> int:
    """Compute resilience bonus (added to exposure_max and harm thresholds).

    Formula: ``tier // 2``.
    """
    return tier // 2


def compute_exposure_max(base_exposure: int, tier: int) -> int:
    """Compute maximum exposure from a template base and the combatant's tier.

    Formula: ``base_exposure + resilience_bonus(tier)``.
    """
    return base_exposure + compute_resilience_bonus(tier)


# ---------------------------------------------------------------------------
# Initiative
# ---------------------------------------------------------------------------

def _combatant_initiative_bonus(combatant: Combatant) -> int:
    """Extract the initiative bonus from a :class:`Combatant`."""
    return compute_initiative_bonus(
        combatant.attributes.agility,
        combatant.attributes.perception,
    )


def roll_initiative(
    combatant_list: Sequence[Combatant],
    rng: random.Random,
) -> List[Tuple[Combatant, int]]:
    """Roll initiative for every combatant and return a sorted order.

    Each combatant rolls a d10 and adds their initiative bonus.  The
    returned list is sorted **descending** by roll value.  Ties are broken
    by higher initiative bonus, then by a secondary d10 tiebreaker roll
    (higher goes first).

    Args:
        combatant_list: Sequence of :class:`Combatant` instances.
        rng:            Deterministic random source.

    Returns:
        A list of ``(combatant, total_roll)`` tuples sorted from highest
        initiative to lowest.
    """
    entries: List[Tuple[Combatant, int, int, int]] = []
    for combatant in combatant_list:
        bonus = _combatant_initiative_bonus(combatant)
        roll = rng.randint(1, 10)
        total = roll + bonus
        # Pre-roll a tiebreaker so it is deterministic under the same seed.
        tiebreaker = rng.randint(1, 10)
        entries.append((combatant, total, bonus, tiebreaker))

    # Sort descending by total, then by bonus (higher is better), then by
    # tiebreaker roll.
    entries.sort(key=lambda e: (e[1], e[2], e[3]), reverse=True)

    return [(combatant, total) for combatant, total, _bonus, _tb in entries]
