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


# ---------------------------------------------------------------------------
# §4.2 Power
# ---------------------------------------------------------------------------

def resolve_power(
    actor_id: str,
    target_id: str,
    state: CombatState,
    rng: random.Random,
    power_category: str = "physical_kinetic",
    power_damage_die: int = 6,
    power_crit_rider: str = "",
    power_cost_phy: int = 0,
    power_cost_men: int = 0,
    power_cost_soc: int = 0,
    power_cost_corr: int = 0,
    power_tn_override: Optional[int] = None,
    is_mental_power: bool = False,
) -> VerbResult:
    """Resolve a Power verb per spec §4.2."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    # Attribute pair from category
    p_attr, s_attr = _POWER_ATTR_PAIRS.get(power_category, ("might", "insight"))
    p_die = _get_attr(actor, p_attr)
    s_die = _get_attr(actor, s_attr)

    # TN: mental powers use mental_defense; others use defense_value
    if is_mental_power or power_category in ("perceptual_mental",):
        tn = compute_mental_defense(target.will, 0)
    else:
        tn = compute_defense_value(target.agility, target.armor)
    if power_tn_override is not None:
        tn = power_tn_override

    atk_mod, _ = tier_gap_modifier(actor.tier, target.tier)
    mods = _build_modifiers(actor, target, state)
    mods.append(atk_mod)

    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Power",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )

    # Pay costs
    state.apply_damage(actor_id, power_cost_phy, "physical")
    state.apply_damage(actor_id, power_cost_men, "mental")
    state.apply_damage(actor_id, power_cost_soc, "social")
    actor.corruption += power_cost_corr

    damage_type_str = power_category
    track = _TRACK_FOR_DAMAGE_TYPE.get(damage_type_str, "physical")

    if tier in (SuccessTier.FUMBLE, SuccessTier.FAILURE):
        result.narrative_data["miss"] = True
        if tier == SuccessTier.FUMBLE:
            # Self-Burning if Matter/Energy power
            if power_category == "matter_energy":
                _apply_status(state, actor_id, StatusName.BURNING, 3, result)
            state.apply_damage(actor_id, 2, "physical")
            result.self_damage = 2

    elif tier == SuccessTier.PARTIAL_FAILURE:
        result.narrative_data["miss"] = True

    elif tier in (SuccessTier.MARGINAL, SuccessTier.FULL, SuccessTier.CRITICAL):
        base = power_damage_die
        if tier == SuccessTier.MARGINAL:
            base = max(1, base - 1)
        affinity = target.get_affinity(damage_type_str)
        dr = resolve_damage(
            base=base,
            attacker_tier=actor.tier,
            damage_type=DamageType(damage_type_str),
            target_affinity=affinity,
            is_crit=check.is_crit,
        )
        result.damage_dealt = dr.final
        result.damage_track = track
        state.apply_damage(target_id, dr.final, track)

        fill = compute_exposure_fill(dr.final, affinity)
        state.apply_exposure_fill(target_id, fill)
        result.exposure_delta[target_id] = fill

        if tier == SuccessTier.CRITICAL:
            state.clamp_momentum(actor_id, +1)
            result.momentum_delta[actor_id] = 1
            if power_crit_rider:
                _apply_status(state, target_id, power_crit_rider, 3, result)

    state.action_log.append({
        "round": state.round_number,
        "verb": "Power",
        "actor": actor_id,
        "target": target_id,
        "category": power_category,
        "tier": check.tier,
        "damage": result.damage_dealt,
    })
    return result


# ---------------------------------------------------------------------------
# §4.3 Assess
# ---------------------------------------------------------------------------

def resolve_assess(
    actor_id: str,
    target_id: str,
    state: CombatState,
    rng: random.Random,
    is_eldritch_target: bool = False,
    is_anomalous: bool = False,
) -> VerbResult:
    """Resolve an Assess verb per spec §4.3."""
    actor = state.combatants[actor_id]
    target = state.combatants.get(target_id)

    p_die = _get_attr(actor, "insight")
    s_die = _get_attr(actor, "perception")

    tn = 10
    if is_eldritch_target:
        tn = 13
    if is_anomalous:
        tn = 16

    mods = [state.status_engine.get_check_modifiers(actor_id, "Assess")]
    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Assess",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )

    truths_revealed = 0
    false_info = False
    next_attack_bonus = 0

    if tier == SuccessTier.CRITICAL:
        truths_revealed = 3
        next_attack_bonus = 2
        state.clamp_momentum(actor_id, +2)
        result.momentum_delta[actor_id] = 2
    elif tier == SuccessTier.FULL:
        truths_revealed = 2
        next_attack_bonus = 1
        state.clamp_momentum(actor_id, +1)
        result.momentum_delta[actor_id] = 1
    elif tier == SuccessTier.MARGINAL:
        truths_revealed = 1
    elif tier == SuccessTier.PARTIAL_FAILURE:
        truths_revealed = 1
        false_info = True
    elif tier == SuccessTier.FUMBLE:
        _apply_status(state, actor_id, StatusName.SHAKEN, 3, result)

    result.narrative_data.update({
        "truths_revealed": truths_revealed,
        "false_info": false_info,
        "next_attack_bonus": next_attack_bonus,
    })
    state.action_log.append({
        "round": state.round_number,
        "verb": "Assess",
        "actor": actor_id,
        "target": target_id,
        "tier": check.tier,
        "truths": truths_revealed,
    })
    return result


# ---------------------------------------------------------------------------
# §4.4 Maneuver
# ---------------------------------------------------------------------------

def resolve_maneuver(
    actor_id: str,
    state: CombatState,
    rng: random.Random,
    target_id: Optional[str] = None,
    maneuver_type: str = "reposition",  # "reposition", "grapple", "disarm", "trip"
    adjacent_enemies: int = 0,
) -> VerbResult:
    """Resolve a Maneuver verb per spec §4.4."""
    actor = state.combatants[actor_id]

    if maneuver_type in ("grapple", "disarm", "trip") and target_id:
        # Opposed check
        p_die = _get_attr(actor, "agility")
        s_die = _get_attr(actor, "strength")
        target = state.combatants[target_id]
        opp_p = _get_attr(target, "strength")
        opp_s = _get_attr(target, "agility")
        opp_check = roll_check(opp_p, opp_s, [], 0, rng)
        tn = opp_check.total
    else:
        p_die = _get_attr(actor, "agility")
        s_die = _get_attr(actor, "insight")
        tn = 10  # solo movement baseline

    mods = [state.status_engine.get_check_modifiers(actor_id, "Maneuver")]
    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Maneuver",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )

    if tier == SuccessTier.CRITICAL:
        result.narrative_data["effect"] = "full_plus_bonus"
        result.narrative_data["ally_attack_bonus"] = 1
    elif tier == SuccessTier.FULL:
        result.narrative_data["effect"] = "full"
    elif tier == SuccessTier.MARGINAL:
        result.narrative_data["effect"] = "partial"
        result.self_damage = 1
    elif tier in (SuccessTier.PARTIAL_FAILURE, SuccessTier.FAILURE):
        result.narrative_data["effect"] = "none"
        if tier == SuccessTier.FAILURE and adjacent_enemies > 0:
            result.narrative_data["opportunity_attack"] = True
    elif tier == SuccessTier.FUMBLE:
        result.narrative_data["effect"] = "none"
        result.narrative_data["self_prone"] = True

    state.action_log.append({
        "round": state.round_number,
        "verb": "Maneuver",
        "actor": actor_id,
        "type": maneuver_type,
        "tier": check.tier,
    })
    return result


# ---------------------------------------------------------------------------
# §4.5 Parley
# ---------------------------------------------------------------------------

def resolve_parley(
    actor_id: str,
    target_id: str,
    state: CombatState,
    rng: random.Random,
    parley_attr: str = "will",     # "will" (force) or "insight" (read)
    combat_register: str = "human",
) -> VerbResult:
    """Resolve a Parley verb per spec §4.5."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    p_die = _get_attr(actor, parley_attr)
    s_die = _get_attr(actor, "insight" if parley_attr == "will" else "perception")

    tn = compute_mental_defense(target.will, 0)

    mods = [state.status_engine.get_check_modifiers(actor_id, "Parley")]
    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Parley",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )

    if tier == SuccessTier.CRITICAL:
        result.narrative_data["terms"] = "accepted"
        result.narrative_data["group_cascade"] = True
        state.heat_deltas["general"] = state.heat_deltas.get("general", 0) - 1
        state.player_parleyed_recently = True
    elif tier == SuccessTier.FULL:
        result.narrative_data["terms"] = "willing"
        state.player_parleyed_recently = True
    elif tier == SuccessTier.MARGINAL:
        result.narrative_data["terms"] = "pause"
        state.player_parleyed_recently = True
    elif tier == SuccessTier.PARTIAL_FAILURE:
        result.narrative_data["terms"] = "none"
    elif tier == SuccessTier.FAILURE:
        state.clamp_momentum(actor_id, -1)
        result.momentum_delta[actor_id] = -1
        result.narrative_data["terms"] = "none"
    elif tier == SuccessTier.FUMBLE:
        result.self_damage = 1
        result.self_damage_track = "social"
        state.apply_damage(actor_id, 1, "social")
        _apply_status(state, actor_id, StatusName.SHAKEN, 3, result)
        result.narrative_data["terms"] = "none"

    state.action_log.append({
        "round": state.round_number,
        "verb": "Parley",
        "actor": actor_id,
        "target": target_id,
        "tier": check.tier,
        "terms": result.narrative_data.get("terms"),
    })
    return result


# ---------------------------------------------------------------------------
# §4.6 Disengage
# ---------------------------------------------------------------------------

def resolve_disengage(
    actor_id: str,
    state: CombatState,
    rng: random.Random,
    adjacent_enemies: int = 0,
) -> VerbResult:
    """Resolve a Disengage verb per spec §4.6."""
    actor = state.combatants[actor_id]

    p_die = _get_attr(actor, "agility")
    s_die = _get_attr(actor, "insight")

    # TN based on adjacent enemies
    if adjacent_enemies == 0:
        tn = 10
    elif adjacent_enemies == 1:
        tn = 13
    else:
        tn = 16

    mods = [state.status_engine.get_check_modifiers(actor_id, "Disengage")]
    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Disengage",
        actor_id=actor_id,
        target_id=None,
        check=check,
        success_tier=check.tier,
    )

    if tier == SuccessTier.CRITICAL:
        result.narrative_data["escape"] = "immediate"
        result.narrative_data["no_opp_attacks"] = True
    elif tier == SuccessTier.FULL:
        result.narrative_data["escape"] = "end_of_round"
        result.narrative_data["no_opp_attacks"] = True
    elif tier == SuccessTier.MARGINAL:
        result.narrative_data["escape"] = "end_of_round"
        result.narrative_data["opp_attack_first"] = True
    elif tier in (SuccessTier.PARTIAL_FAILURE, SuccessTier.FAILURE):
        result.narrative_data["escape"] = "failed"
        if adjacent_enemies > 0:
            result.narrative_data["opp_attacks"] = adjacent_enemies
    elif tier == SuccessTier.FUMBLE:
        result.narrative_data["escape"] = "failed"
        result.narrative_data["prone"] = True
        result.narrative_data["opp_attacks_bonus"] = 2

    state.action_log.append({
        "round": state.round_number,
        "verb": "Disengage",
        "actor": actor_id,
        "tier": check.tier,
        "escape": result.narrative_data.get("escape"),
    })
    return result


# ---------------------------------------------------------------------------
# §4.7 Finisher
# ---------------------------------------------------------------------------

def resolve_finisher(
    actor_id: str,
    target_id: str,
    state: CombatState,
    rng: random.Random,
    finisher_id: str = "fin_break_spine",
    momentum_cost: int = 5,
    p_attr: str = "might",
    s_attr: str = "strength",
    corruption_cost: int = 0,
) -> VerbResult:
    """Resolve a Finisher verb per spec §4.7."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    p_die = _get_attr(actor, p_attr)
    s_die = _get_attr(actor, s_attr)
    tn = 10  # Finisher TN is fixed at 10

    # Pay momentum cost
    state.clamp_momentum(actor_id, -momentum_cost)
    result_momentum = -momentum_cost

    # Pay corruption cost if applicable
    if corruption_cost > 0:
        actor.corruption += corruption_cost

    mods = [state.status_engine.get_check_modifiers(actor_id, "Finisher")]
    if state.status_engine.has_status(target_id, StatusName.MARKED):
        mods.append(2)

    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Finisher",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )
    result.momentum_delta[actor_id] = result_momentum

    if tier in (SuccessTier.FULL, SuccessTier.CRITICAL):
        result.narrative_data["effect"] = "full"
        result.narrative_data["finisher_id"] = finisher_id
        # Incapacitate or effect per finisher — engine applies full track fill
        state.apply_damage(target_id, 5, "physical")
        result.damage_dealt = 5
        target.active = False
    elif tier == SuccessTier.MARGINAL:
        result.narrative_data["effect"] = "partial"
        state.apply_damage(target_id, 3, "physical")
        result.damage_dealt = 3
    elif tier == SuccessTier.FUMBLE:
        # Exposed clears on fumble
        state.status_engine.remove_status(target_id, StatusName.EXPOSED)
        target.exposure = max(0, target.exposure_max - 1)
        result.narrative_data["effect"] = "fumble_miss"

    state.action_log.append({
        "round": state.round_number,
        "verb": "Finisher",
        "actor": actor_id,
        "target": target_id,
        "finisher_id": finisher_id,
        "tier": check.tier,
    })
    return result


# ---------------------------------------------------------------------------
# §4.8 Defend (reaction)
# ---------------------------------------------------------------------------

def resolve_defend(
    actor_id: str,
    incoming_actor_id: str,
    incoming_damage: int,
    incoming_tier: str,
    state: CombatState,
    rng: random.Random,
    incoming_status: str = "",
) -> VerbResult:
    """Resolve a Defend reaction per spec §4.8."""
    actor = state.combatants[actor_id]
    attacker = state.combatants.get(incoming_actor_id)

    p_die = _get_attr(actor, "agility")
    s_die = _get_attr(actor, "might")

    # Opposed: use attacker's total as TN (passed via incoming context)
    # For simplicity, use the actor's defense roll vs the incoming total
    tn = _get_attr(actor, "agility") + actor.armor  # approximate

    mods = [state.status_engine.get_check_modifiers(actor_id, "Defend")]
    check = roll_check(p_die, s_die, mods, tn, rng)
    tier = SuccessTier(check.tier)

    result = VerbResult(
        verb="Defend",
        actor_id=actor_id,
        target_id=incoming_actor_id,
        check=check,
        success_tier=check.tier,
    )

    if tier == SuccessTier.CRITICAL:
        result.narrative_data["damage_taken"] = 0
        result.narrative_data["free_attack"] = True
        state.clamp_momentum(actor_id, +1)
        result.momentum_delta[actor_id] = 1
    elif tier == SuccessTier.FULL:
        result.narrative_data["damage_taken"] = 0
    elif tier == SuccessTier.MARGINAL:
        reduced = max(0, incoming_damage - 2)
        result.narrative_data["damage_taken"] = reduced
        state.apply_damage(actor_id, reduced, "physical")
    elif tier == SuccessTier.PARTIAL_FAILURE:
        result.narrative_data["damage_taken"] = incoming_damage
        state.apply_damage(actor_id, incoming_damage, "physical")
    elif tier == SuccessTier.FAILURE:
        extra = incoming_damage + 1
        result.narrative_data["damage_taken"] = extra
        state.apply_damage(actor_id, extra, "physical")
        if attacker:
            state.clamp_momentum(incoming_actor_id, +1)
    elif tier == SuccessTier.FUMBLE:
        extra = incoming_damage + 2
        result.narrative_data["damage_taken"] = extra
        state.apply_damage(actor_id, extra, "physical")
        if incoming_status:
            _apply_status(state, actor_id, incoming_status, 3, result)

    state.action_log.append({
        "round": state.round_number,
        "verb": "Defend",
        "actor": actor_id,
        "attacker": incoming_actor_id,
        "tier": check.tier,
    })
    return result
