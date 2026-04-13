"""Verb resolvers for the Emergence combat engine.

Implements resolution functions for all 8 combat verbs per combat-spec.md
Sections 3–4.  Each resolver takes mutable CombatState and returns a VerbResult.
All randomness flows through the injected random.Random instance.

Uses only the Python standard library.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.combat.resolution import (
    CheckResult,
    SuccessTier,
    roll_check,
    roll_die,
    tier_gap_modifier,
    compute_defense_value,
    compute_mental_defense,
)
from emergence.engine.combat.damage import (
    DamageType,
    resolve_damage,
    compute_exposure_fill,
    AFFINITY_PROFILES,
)
from emergence.engine.combat.statuses import StatusEngine, StatusName, ActiveStatus


# ---------------------------------------------------------------------------
# CombatState — mutable encounter state
# ---------------------------------------------------------------------------

@dataclass
class CombatantRecord:
    """Live state of one combatant during an encounter."""
    id: str
    side: str                       # "player", "enemy", "ally"
    tier: int = 1
    # Attribute die sizes
    strength: int = 6
    agility: int = 6
    perception: int = 6
    will: int = 6
    insight: int = 6
    might: int = 6
    # Condition tracks (0 = fresh, max = incapacitated)
    phy: int = 0
    men: int = 0
    soc: int = 0
    phy_max: int = 5
    men_max: int = 5
    soc_max: int = 5
    armor: int = 0                  # static armor reduction
    # Affinities: damage_type -> affinity string ("neutral", "resistant", etc.)
    affinities: Dict[str, str] = field(default_factory=dict)
    # Exposure
    exposure: int = 0
    exposure_max: int = 3
    # Momentum (0-5)
    momentum: int = 0
    # Powers available
    powers: List[str] = field(default_factory=list)
    # AI profile (for enemies)
    ai_profile: str = "aggressive"
    # Corruption track
    corruption: int = 0
    # Whether this combatant is still active
    active: bool = True

    def get_affinity(self, damage_type: str) -> str:
        return self.affinities.get(damage_type, "neutral")

    def is_exposed(self) -> bool:
        return self.exposure >= self.exposure_max

    def is_incapacitated(self) -> bool:
        return self.phy >= self.phy_max or not self.active


@dataclass
class CombatState:
    """Mutable state for an in-progress encounter."""
    combatants: Dict[str, CombatantRecord] = field(default_factory=dict)
    zones: List[dict] = field(default_factory=list)
    round_number: int = 1
    initiative_order: List[str] = field(default_factory=list)
    status_engine: StatusEngine = field(default_factory=StatusEngine)
    scene_clocks: Dict[str, int] = field(default_factory=dict)
    action_log: List[dict] = field(default_factory=list)
    combat_register: str = "human"
    # Witness and heat tracking (human register)
    witnesses: List[str] = field(default_factory=list)
    heat_deltas: Dict[str, int] = field(default_factory=dict)
    # Pack convergence target
    pack_target_id: Optional[str] = None
    # Player parleyed recently (for AI parley_signal)
    player_parleyed_recently: bool = False

    def get_enemies_of(self, side: str) -> List[CombatantRecord]:
        return [c for c in self.combatants.values()
                if c.side != side and c.active and not c.is_incapacitated()]

    def apply_exposure_fill(self, target_id: str, fill: int) -> None:
        c = self.combatants.get(target_id)
        if not c:
            return
        c.exposure = min(c.exposure + fill, c.exposure_max + 5)
        # Check if newly Exposed
        if c.is_exposed() and not self.status_engine.has_status(target_id, StatusName.EXPOSED):
            self.status_engine.apply_status(target_id, ActiveStatus(
                name=StatusName.EXPOSED,
                duration=-1,
                source="exposure_track",
                applied_round=self.round_number,
            ))

    def apply_damage(self, target_id: str, damage: int, track: str = "physical") -> None:
        c = self.combatants.get(target_id)
        if not c:
            return
        if track == "physical":
            c.phy = min(c.phy + damage, c.phy_max + 3)
        elif track == "mental":
            c.men = min(c.men + damage, c.men_max + 3)
        elif track == "social":
            c.soc = min(c.soc + damage, c.soc_max + 3)

    def clamp_momentum(self, cid: str, delta: int) -> None:
        c = self.combatants.get(cid)
        if not c:
            return
        c.momentum = max(0, min(5, c.momentum + delta))


# ---------------------------------------------------------------------------
# VerbResult
# ---------------------------------------------------------------------------

@dataclass
class VerbResult:
    """Result of resolving a single combat verb."""
    verb: str
    actor_id: str
    target_id: Optional[str]
    check: Optional[CheckResult]
    success_tier: str           # SuccessTier value string
    damage_dealt: int = 0
    damage_track: str = "physical"
    statuses_applied: List[Tuple[str, str]] = field(default_factory=list)  # (target_id, status)
    exposure_delta: Dict[str, int] = field(default_factory=dict)           # target_id -> fill
    momentum_delta: Dict[str, int] = field(default_factory=dict)           # cid -> delta
    narrative_data: Dict[str, Any] = field(default_factory=dict)
    self_damage: int = 0
    self_damage_track: str = "physical"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TRACK_FOR_DAMAGE_TYPE: Dict[str, str] = {
    "physical_kinetic": "physical",
    "matter_energy": "physical",
    "biological_vital": "physical",
    "perceptual_mental": "mental",
    "temporal_spatial": "mental",
    "auratic": "social",
    "eldritch_corruptive": "mental",
}

_POWER_ATTR_PAIRS: Dict[str, Tuple[str, str]] = {
    "physical_kinetic":   ("might", "strength"),
    "matter_energy":      ("might", "insight"),
    "biological_vital":   ("will", "insight"),
    "perceptual_mental":  ("will", "perception"),
    "temporal_spatial":   ("insight", "perception"),
    "auratic":            ("will", "might"),
    "eldritch_corruptive": ("will", "insight"),
}


def _get_attr(c: CombatantRecord, attr: str) -> int:
    return getattr(c, attr, 6)


def _apply_status(state: CombatState, target_id: str, status_name: str,
                  duration: int, result: VerbResult) -> None:
    state.status_engine.apply_status(target_id, ActiveStatus(
        name=status_name,
        duration=duration,
        source=result.actor_id,
        applied_round=state.round_number,
    ))
    result.statuses_applied.append((target_id, status_name))


def _build_modifiers(actor: CombatantRecord, target: Optional[CombatantRecord],
                     state: CombatState) -> List[int]:
    """Collect check modifiers from statuses on both sides."""
    mods: List[int] = []
    # Actor status modifiers
    mods.append(state.status_engine.get_check_modifiers(actor.id, "Attack"))
    # Attack bonus vs target statuses
    if target:
        mods.append(state.status_engine.get_attack_bonus_vs(target.id))
    return mods


# ---------------------------------------------------------------------------
# §4.1 Attack
# ---------------------------------------------------------------------------

def resolve_attack(
    actor_id: str,
    target_id: str,
    state: CombatState,
    rng: random.Random,
    weapon_type: str = "melee",   # "melee", "ranged", "grapple"
    weapon_damage_base: int = 6,
    weapon_status_rider: str = "",  # "bleeding", "stunned", ""
) -> VerbResult:
    """Resolve an Attack verb per spec §4.1."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    # Attribute pair
    if weapon_type == "ranged":
        p_attr, s_attr = "perception", "agility"
    elif weapon_type == "grapple":
        p_attr, s_attr = "strength", "might"
    else:
        p_attr, s_attr = "strength", "agility"

    p_die = _get_attr(actor, p_attr)
    s_die = _get_attr(actor, s_attr)

    # TN = target's defense_value
    tn = compute_defense_value(target.agility, target.armor)

    # Tier gap modifier (attacker perspective)
    atk_mod, _ = tier_gap_modifier(actor.tier, target.tier)

    mods = _build_modifiers(actor, target, state)
    mods.append(atk_mod)

    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Attack",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )

    if tier == SuccessTier.FUMBLE:
        # Self-damage + self-status
        result.self_damage = 2
        if weapon_status_rider == "bleeding":
            _apply_status(state, actor_id, StatusName.BLEEDING, 3, result)
        elif weapon_status_rider == "blunt":
            _apply_status(state, actor_id, StatusName.STUNNED, 1, result)
        result.narrative_data["fumble"] = True

    elif tier == SuccessTier.FAILURE:
        # Melee: actor takes 1 phy from over-extension
        if weapon_type == "melee":
            result.self_damage = 1
        result.narrative_data["miss"] = True

    elif tier == SuccessTier.PARTIAL_FAILURE:
        result.narrative_data["miss"] = True

    elif tier in (SuccessTier.MARGINAL, SuccessTier.FULL, SuccessTier.CRITICAL):
        # Compute damage
        affinity = target.get_affinity("physical_kinetic")
        base = weapon_damage_base
        if tier == SuccessTier.MARGINAL:
            base = max(1, base - 1)
        dr = resolve_damage(
            base=base,
            attacker_tier=actor.tier,
            damage_type=DamageType.PHYSICAL_KINETIC,
            target_affinity=affinity,
            armor=target.armor if weapon_type != "ranged" else 0,
            is_crit=check.is_crit,
        )
        result.damage_dealt = dr.final
        result.damage_track = "physical"
        state.apply_damage(target_id, dr.final, "physical")

        # Exposure fill
        fill = compute_exposure_fill(dr.final, affinity)
        if tier == SuccessTier.CRITICAL:
            fill += 1  # crit status rider adds to exposure
        state.apply_exposure_fill(target_id, fill)
        result.exposure_delta[target_id] = fill

        # Momentum
        if tier == SuccessTier.CRITICAL:
            state.clamp_momentum(actor_id, +1)
            result.momentum_delta[actor_id] = 1
            # Crit weapon rider
            if weapon_status_rider:
                rider = weapon_status_rider
                if rider == "bleeding":
                    _apply_status(state, target_id, StatusName.BLEEDING, 3, result)
                elif rider in ("stunned", "blunt"):
                    _apply_status(state, target_id, StatusName.STUNNED, 1, result)
                elif rider == "marked":
                    _apply_status(state, target_id, StatusName.MARKED, -1, result)

    state.action_log.append({
        "round": state.round_number,
        "verb": "Attack",
        "actor": actor_id,
        "target": target_id,
        "tier": check.tier,
        "damage": result.damage_dealt,
    })
    return result
