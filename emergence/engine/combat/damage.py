"""Damage calculation, affinity resolution, and track allocation for Emergence.

Implements the full damage pipeline: raw computation, affinity scaling, armor
and cover reduction, track allocation with overflow, exposure fill, and harm
tier determination.  Uses only the Python standard library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from emergence.engine.schemas.combatant import AffinityState
from emergence.engine.schemas.character import ConditionTrack


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DamageType(str, Enum):
    """Seven damage types, one-to-one with power categories."""
    PHYSICAL_KINETIC = "physical_kinetic"
    PERCEPTUAL_MENTAL = "perceptual_mental"
    MATTER_ENERGY = "matter_energy"
    BIOLOGICAL_VITAL = "biological_vital"
    AURATIC = "auratic"
    TEMPORAL_SPATIAL = "temporal_spatial"
    ELDRITCH_CORRUPTIVE = "eldritch_corruptive"


# Short aliases used in profile definitions.
PK = DamageType.PHYSICAL_KINETIC
PM = DamageType.PERCEPTUAL_MENTAL
ME = DamageType.MATTER_ENERGY
BV = DamageType.BIOLOGICAL_VITAL
AU = DamageType.AURATIC
TS = DamageType.TEMPORAL_SPATIAL
EC = DamageType.ELDRITCH_CORRUPTIVE


# ---------------------------------------------------------------------------
# Armor table
# ---------------------------------------------------------------------------

ARMOR_TABLE: Dict[str, int] = {
    "none": 0,
    "clothing": 0,
    "leather": 1,
    "gambeson": 2,
    "plate": 3,
    "c-craft plate": 4,
}


# ---------------------------------------------------------------------------
# Affinity profiles
# ---------------------------------------------------------------------------

def _neutral_profile() -> Dict[str, str]:
    """Return a profile where every damage type is neutral."""
    return {dt.value: AffinityState.NEUTRAL.value for dt in DamageType}


def _profile(**overrides: str) -> Dict[str, str]:
    """Build an affinity profile starting from all-neutral, then applying overrides."""
    base = _neutral_profile()
    base.update(overrides)
    return base


AFFINITY_PROFILES: Dict[str, Dict[str, str]] = {
    "standard_human": _neutral_profile(),

    "elite_human": _profile(
        physical_kinetic=AffinityState.RESISTANT.value,
        eldritch_corruptive=AffinityState.VULNERABLE.value,
    ),

    "wretch": _profile(
        physical_kinetic=AffinityState.RESISTANT.value,
        biological_vital=AffinityState.VULNERABLE.value,
        eldritch_corruptive=AffinityState.VULNERABLE.value,
    ),

    "hunter": _profile(
        perceptual_mental=AffinityState.RESISTANT.value,
        eldritch_corruptive=AffinityState.VULNERABLE.value,
    ),

    "aberrant": _profile(
        physical_kinetic=AffinityState.RESISTANT.value,
        perceptual_mental=AffinityState.RESISTANT.value,
        biological_vital=AffinityState.VULNERABLE.value,
        auratic=AffinityState.RESISTANT.value,
        temporal_spatial=AffinityState.RESISTANT.value,
    ),

    "shade": _profile(
        physical_kinetic=AffinityState.IMMUNE.value,
        perceptual_mental=AffinityState.VULNERABLE.value,
        matter_energy=AffinityState.RESISTANT.value,
        biological_vital=AffinityState.IMMUNE.value,
        auratic=AffinityState.VULNERABLE.value,
        temporal_spatial=AffinityState.VULNERABLE.value,
    ),

    "sovereign": _profile(
        physical_kinetic=AffinityState.RESISTANT.value,
        perceptual_mental=AffinityState.RESISTANT.value,
        matter_energy=AffinityState.RESISTANT.value,
        biological_vital=AffinityState.RESISTANT.value,
        eldritch_corruptive=AffinityState.ABSORB.value,
    ),

    "hive_drone": _profile(
        perceptual_mental=AffinityState.RESISTANT.value,
        matter_energy=AffinityState.VULNERABLE.value,
        biological_vital=AffinityState.RESISTANT.value,
        auratic=AffinityState.RESISTANT.value,
        eldritch_corruptive=AffinityState.RESISTANT.value,
    ),
}


# ---------------------------------------------------------------------------
# Track routing tables
# ---------------------------------------------------------------------------

# Maps damage type -> (primary_track, overflow_track_or_None, overflow_threshold)
# overflow_threshold: how many points past track cap before overflow spills.
# None means no overflow routing.

_TRACK_ROUTING: Dict[DamageType, Tuple[str, str | None, int]] = {
    PK: ("physical", None, 0),
    ME: ("physical", None, 0),
    BV: ("physical", None, 0),
    PM: ("mental", "physical", 2),
    TS: ("mental", None, 0),
    AU: ("social", "mental", 2),
    EC: ("mental", "social", 2),
}

TRACK_MAX = 5


# ---------------------------------------------------------------------------
# Damage result dataclass
# ---------------------------------------------------------------------------

@dataclass
class DamageResult:
    """Complete output of a single damage resolution."""
    raw: int
    after_affinity: int
    after_armor: int
    after_cover: int
    final: int
    damage_type: str
    track_allocation: Dict[str, int]
    exposure_fill: int
    harm_tier: int  # 0 = no harm event, 1/2/3
    absorbed: int   # HP healed via absorb


# ---------------------------------------------------------------------------
# Core pipeline helpers
# ---------------------------------------------------------------------------

def _tier_bonus(attacker_tier: int) -> int:
    """Tier bonus = attacker_tier // 2."""
    return attacker_tier // 2


def _affinity_damage(raw: int, affinity: AffinityState) -> int:
    """Apply affinity multiplier to raw damage.

    Returns the damage value after affinity scaling (before armor/cover).
    Does NOT handle absorb healing -- caller checks for that.
    """
    if affinity == AffinityState.VULNERABLE:
        return math.ceil(raw * 1.5)
    if affinity == AffinityState.NEUTRAL:
        return raw
    if affinity == AffinityState.RESISTANT:
        result = math.floor(raw * 0.5)
        if raw > 0 and result == 0:
            result = 1  # sting floor
        return result
    # IMMUNE or ABSORB
    return 0


def _affinity_fill_multiplier(affinity: AffinityState) -> float:
    """Return the exposure fill multiplier for a given affinity."""
    if affinity == AffinityState.VULNERABLE:
        return 2.0
    if affinity == AffinityState.NEUTRAL:
        return 1.0
    if affinity == AffinityState.RESISTANT:
        return 0.5
    # IMMUNE or ABSORB
    return 0.0


def _absorb_healing(raw: int) -> int:
    """Absorb: heal 1 physical per 3 incoming raw damage."""
    return raw // 3


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resolve_damage(
    base: int,
    attacker_tier: int,
    damage_type: DamageType | str,
    target_affinity: AffinityState | str,
    armor: int = 0,
    cover: int = 0,
    is_crit: bool = False,
    static_mods: int = 0,
) -> DamageResult:
    """Run the full damage calculation pipeline and return a DamageResult.

    Parameters
    ----------
    base:
        Base damage value from the attack/power.
    attacker_tier:
        Attacker's tier (used for tier bonus = tier // 2).
    damage_type:
        One of the seven DamageType values (enum or string).
    target_affinity:
        The target's affinity state for this damage type.
    armor:
        Armor reduction value (applied only for physical_kinetic melee/ranged).
    cover:
        Cover reduction value (applied only for PK, ME, BV projectile attacks).
    is_crit:
        Whether the attack is a critical hit (+1 damage bonus).
    static_mods:
        Sum of all static damage modifiers (buffs, debuffs, etc.).

    Returns
    -------
    DamageResult with all pipeline stages populated.
    """
    # Normalise enum inputs.
    if isinstance(damage_type, str):
        damage_type = DamageType(damage_type)
    if isinstance(target_affinity, str):
        target_affinity = AffinityState(target_affinity)

    # -- raw --
    raw = base + _tier_bonus(attacker_tier) + static_mods
    if is_crit:
        raw += 1

    # -- affinity --
    absorbed = 0
    if target_affinity == AffinityState.ABSORB:
        after_affinity = 0
        absorbed = _absorb_healing(raw)
    else:
        after_affinity = _affinity_damage(raw, target_affinity)

    # -- armor (only for melee/ranged physical_kinetic) --
    after_armor = max(0, after_affinity - armor)

    # -- cover (only for PK, ME, BV projectile) --
    after_cover = max(0, after_armor - cover)

    final = after_cover

    # -- exposure fill --
    exposure_fill = compute_exposure_fill(
        final,
        target_affinity,
        crit_statuses_applied=1 if is_crit else 0,
    )

    # -- track allocation (using zero current tracks for standalone calc) --
    # resolve_damage returns the *amount* to apply; actual track state is
    # handled by the caller via allocate_to_tracks.
    track_allocation: Dict[str, int] = {}
    harm_tier = 0

    if final > 0:
        primary_track, _, _ = _TRACK_ROUTING[damage_type]
        track_allocation[primary_track] = final

    return DamageResult(
        raw=raw,
        after_affinity=after_affinity,
        after_armor=after_armor,
        after_cover=after_cover,
        final=final,
        damage_type=damage_type.value,
        track_allocation=track_allocation,
        exposure_fill=exposure_fill,
        harm_tier=harm_tier,
        absorbed=absorbed,
    )


def allocate_to_tracks(
    damage: int,
    damage_type: DamageType | str,
    current_tracks: Dict[str, int],
    is_crit: bool = False,
) -> Dict[str, object]:
    """Allocate damage to condition tracks, handling overflow and harm tiers.

    Parameters
    ----------
    damage:
        Final damage to allocate (after affinity, armor, cover).
    damage_type:
        The damage type, determining which track(s) receive damage.
    current_tracks:
        Current condition track values, e.g. {"physical": 2, "mental": 0, "social": 1}.
        This dict is NOT mutated; the result contains deltas.
    is_crit:
        Whether this was a critical hit (relevant for EC corruption).

    Returns
    -------
    A dict with:
        "track_changes": Dict[str, int]  -- amount added to each track
        "harm_events": List[Dict]        -- list of harm tier events triggered
        "corruption": int                -- corruption points gained (EC crit only)
        "new_tracks": Dict[str, int]     -- resulting track values after allocation
    """
    if isinstance(damage_type, str):
        damage_type = DamageType(damage_type)

    primary_track, overflow_track, overflow_threshold = _TRACK_ROUTING[damage_type]

    tracks = dict(current_tracks)
    track_changes: Dict[str, int] = {}
    harm_events: List[Dict[str, object]] = []
    corruption = 0

    if damage <= 0:
        return {
            "track_changes": track_changes,
            "harm_events": harm_events,
            "corruption": corruption,
            "new_tracks": tracks,
        }

    # Apply damage to primary track.
    current_primary = tracks.get(primary_track, 0)
    new_primary = current_primary + damage
    primary_applied = min(damage, TRACK_MAX - current_primary)
    primary_applied = max(0, primary_applied)  # can't apply negative
    overflow_amount = max(0, new_primary - TRACK_MAX)

    tracks[primary_track] = min(new_primary, TRACK_MAX)
    track_changes[primary_track] = tracks[primary_track] - current_primary

    # Determine harm tier from overflow past track cap.
    if overflow_amount > 0:
        harm_tier = _compute_harm_tier(overflow_amount)
        harm_events.append({
            "tier": harm_tier,
            "track": primary_track,
            "overflow": overflow_amount,
        })

    # Overflow routing to secondary track.
    if overflow_track is not None and overflow_amount >= overflow_threshold and overflow_amount > 0:
        overflow_to_apply = overflow_amount
        current_secondary = tracks.get(overflow_track, 0)
        new_secondary = current_secondary + overflow_to_apply
        secondary_overflow = max(0, new_secondary - TRACK_MAX)

        tracks[overflow_track] = min(new_secondary, TRACK_MAX)
        secondary_change = tracks[overflow_track] - current_secondary
        if secondary_change > 0:
            track_changes[overflow_track] = secondary_change

        if secondary_overflow > 0:
            sec_harm = _compute_harm_tier(secondary_overflow)
            harm_events.append({
                "tier": sec_harm,
                "track": overflow_track,
                "overflow": secondary_overflow,
            })

    # Eldritch_corruptive: corruption on crit.
    if damage_type == EC and is_crit:
        corruption = 1

    return {
        "track_changes": track_changes,
        "harm_events": harm_events,
        "corruption": corruption,
        "new_tracks": tracks,
    }


def compute_exposure_fill(
    damage_final: int,
    affinity: AffinityState | str,
    crit_statuses_applied: int = 0,
) -> int:
    """Compute how much the exposure track advances from a single hit.

    Parameters
    ----------
    damage_final:
        Final damage after the full pipeline.
    affinity:
        The target's affinity state for this damage type.
    crit_statuses_applied:
        Number of crit-related statuses that were applied (each adds +1).

    Returns
    -------
    Total exposure fill (non-negative integer).
    """
    if isinstance(affinity, str):
        affinity = AffinityState(affinity)

    fill_mult = _affinity_fill_multiplier(affinity)

    # Immune and absorb yield zero fill regardless.
    if fill_mult == 0.0:
        return 0

    # Base fill: half of final damage, scaled by affinity fill multiplier.
    base_fill = damage_final // 2
    scaled_fill = base_fill * fill_mult

    # For resistant (0.5x), round down.
    fill = math.floor(scaled_fill)

    # Sting floor: at least 1 if any damage was dealt.
    sting = 1 if damage_final > 0 else 0

    # Crit push.
    crit_push = crit_statuses_applied

    return fill + sting + crit_push


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_harm_tier(overflow: int) -> int:
    """Determine harm tier from the amount of damage past track cap (5).

    Tier 1: 1 additional damage past cap
    Tier 2: 3+ additional damage past cap
    Tier 3: 6+ overflow (or Finisher, handled externally)
    """
    if overflow >= 6:
        return 3
    if overflow >= 3:
        return 2
    if overflow >= 1:
        return 1
    return 0
