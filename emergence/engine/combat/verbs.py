"""Verb resolvers for the Emergence combat engine.

Implements resolution functions for combat verbs per combat-spec.md
Sections 3–4.  Each resolver takes mutable CombatState and returns a VerbResult.
Rev 4 adds Brace, Posture_Change, Utility, and Power_Minor minor-action verbs.
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
    # Rev 4: Posture system
    current_posture: str = "parry"      # parry, block, dodge, aggressive
    # Rev 4: Armed posture riders (max 2)
    armed_posture_riders: List[Dict[str, Any]] = field(default_factory=list)
    # Rev 4: Binary flags
    hidden: bool = False
    grappled: bool = False
    # Rev 4: Pool mechanics
    pool: int = 0                       # current pool
    pool_max: int = 6                   # effective pool max (base - armed count)
    base_pool_max: int = 6              # 3 + tier
    brace_uses: int = 3                 # resets to 3 at combat start
    # Rev 4: Scene mode tracking
    scene_mode_uses: List[str] = field(default_factory=list)

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
    "kinetic": "physical",
    "material": "physical",
    "somatic": "physical",
    "cognitive": "mental",
    "spatial": "mental",
    "paradoxic": "mental",
}

_POWER_ATTR_PAIRS: Dict[str, Tuple[str, str]] = {
    "somatic":   ("might", "will"),
    "cognitive":  ("will", "perception"),
    "material":   ("might", "insight"),
    "kinetic":    ("might", "strength"),
    "spatial":    ("insight", "perception"),
    "paradoxic":  ("will", "insight"),
}

# Rev 4: Attack sub-type attribute pairs and TNs
_ATTACK_SUB_TYPE_CONFIG: Dict[str, Dict[str, Any]] = {
    "heavy":   {"attrs": ("strength", "might"), "tn": 10, "fail_effect": "self_exposed"},
    "quick":   {"attrs": ("agility", "perception"), "tn": 11, "fail_effect": None},
    "ranged":  {"attrs": ("perception", "agility"), "tn": 10, "fail_effect": None},
    "grapple": {"attrs": ("strength", "agility"), "tn": 10, "fail_effect": None, "contested": True},
}

# Rev 4: Parley sub-type attribute pairs and TNs
_PARLEY_SUB_TYPE_CONFIG: Dict[str, Dict[str, Any]] = {
    "demand":      {"attrs": ("will", "might"), "tn": 10},
    "taunt":       {"attrs": ("will", "insight"), "tn": 10},
    "disorient":   {"attrs": ("insight", "perception"), "tn": 10},
    "destabilize": {"attrs": ("insight", "will"), "tn": 12},
    "negotiate":   {"attrs": ("insight", "will"), "tn": 10},
}

# Rev 4: Maneuver sub-type attribute pairs and TNs
_MANEUVER_SUB_TYPE_CONFIG: Dict[str, Dict[str, Any]] = {
    "reposition": {"attrs": ("agility", "might"), "tn": 10},
    "disrupt":    {"attrs": ("strength", "insight"), "tn": 10},
    "conceal":    {"attrs": ("agility", "insight"), "tn": 10},
}


_STATUS_DURATIONS: Dict[str, int] = {
    StatusName.BLEEDING: -1,   # end of scene
    StatusName.STUNNED: 1,     # 1 round
    StatusName.SHAKEN: 3,      # 3 rounds
    StatusName.BURNING: 3,     # 3 rounds
    StatusName.CORRUPTED: 3,   # 3 rounds (permanent if corruption >= 3)
    StatusName.MARKED: -1,     # end of scene
    StatusName.EXPOSED: -1,    # until exposure decays
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
    attack_sub_type: str = "heavy",
) -> VerbResult:
    """Resolve an Attack verb per spec §4.1."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    # Rev 4: Look up attribute pair and TN from sub-type config
    sub_cfg = _ATTACK_SUB_TYPE_CONFIG.get(attack_sub_type, _ATTACK_SUB_TYPE_CONFIG["heavy"])
    p_attr, s_attr = sub_cfg["attrs"]

    p_die = _get_attr(actor, p_attr)
    s_die = _get_attr(actor, s_attr)

    # TN = target's defense_value
    tn = compute_defense_value(target.agility, target.armor)

    # Tier gap modifier (attacker perspective)
    atk_mod, _ = tier_gap_modifier(actor.tier, target.tier)

    mods = _build_modifiers(actor, target, state)
    mods.append(atk_mod)

    # Rev 4: Hidden target penalty
    if target.hidden:
        mods.append(-2)

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
        affinity = target.get_affinity("kinetic")
        base = weapon_damage_base
        if tier == SuccessTier.MARGINAL:
            base = max(1, base - 1)
        dr = resolve_damage(
            base=base,
            attacker_tier=actor.tier,
            damage_type=DamageType.KINETIC,
            target_affinity=affinity,
            armor=target.armor,  # armor applies to melee AND ranged per §10.1
            is_crit=check.is_crit,
        )
        result.damage_dealt = dr.final
        result.damage_track = "physical"
        state.apply_damage(target_id, dr.final, "physical")

        # TODO: Rev 4 posture defense integration — apply target posture
        # damage reduction here once posture wiring is complete.

        # Exposure fill
        fill = compute_exposure_fill(
            dr.final, affinity,
            crit_statuses_applied=1 if check.is_crit else 0,
        )
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
                    _apply_status(state, target_id, StatusName.BLEEDING, -1, result)
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
    power_category: str = "kinetic",
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
    if is_mental_power or power_category in ("cognitive",):
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
            if power_category == "material":
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

        fill = compute_exposure_fill(
            dr.final, affinity,
            crit_statuses_applied=1 if check.is_crit else 0,
        )
        state.apply_exposure_fill(target_id, fill)
        result.exposure_delta[target_id] = fill

        if tier == SuccessTier.CRITICAL:
            state.clamp_momentum(actor_id, +1)
            result.momentum_delta[actor_id] = 1
            if power_crit_rider:
                dur = _STATUS_DURATIONS.get(power_crit_rider, 3)
                _apply_status(state, target_id, power_crit_rider, dur, result)

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
    sub_type: str = "reposition",
) -> VerbResult:
    """Resolve a Maneuver verb per spec §4.4."""
    actor = state.combatants[actor_id]

    # Rev 4: Look up attribute pair and TN from sub-type config
    sub_cfg = _MANEUVER_SUB_TYPE_CONFIG.get(sub_type, _MANEUVER_SUB_TYPE_CONFIG["reposition"])

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
        p_attr, s_attr = sub_cfg["attrs"]
        p_die = _get_attr(actor, p_attr)
        s_die = _get_attr(actor, s_attr)
        tn = sub_cfg["tn"]

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

    # Rev 4: Sub-type specific outcomes
    if sub_type == "conceal":
        if tier in (SuccessTier.FULL, SuccessTier.CRITICAL):
            actor.hidden = True
            result.narrative_data["effect"] = "hidden"
            if tier == SuccessTier.CRITICAL:
                result.narrative_data["ally_attack_bonus"] = 1
        elif tier == SuccessTier.MARGINAL:
            result.narrative_data["effect"] = "partial"
            result.self_damage = 1
        elif tier in (SuccessTier.PARTIAL_FAILURE, SuccessTier.FAILURE):
            result.narrative_data["effect"] = "none"
        elif tier == SuccessTier.FUMBLE:
            result.narrative_data["effect"] = "none"
            result.narrative_data["self_prone"] = True
    elif sub_type == "disrupt" and target_id:
        target = state.combatants[target_id]
        if tier in (SuccessTier.FULL, SuccessTier.CRITICAL):
            result.narrative_data["effect"] = "disrupted"
            state.clamp_momentum(target_id, -1)
            result.momentum_delta[target_id] = -1
            if tier == SuccessTier.CRITICAL:
                result.narrative_data["ally_attack_bonus"] = 1
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
    else:
        # Default reposition behavior
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
        "sub_type": sub_type,
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
    sub_type: str = "demand",
) -> VerbResult:
    """Resolve a Parley verb per spec §4.5."""
    actor = state.combatants[actor_id]
    target = state.combatants[target_id]

    # Rev 4: Look up attribute pair from sub-type config
    sub_cfg = _PARLEY_SUB_TYPE_CONFIG.get(sub_type, _PARLEY_SUB_TYPE_CONFIG["demand"])
    p_attr, s_attr = sub_cfg["attrs"]
    p_die = _get_attr(actor, p_attr)
    s_die = _get_attr(actor, s_attr)

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
# §5.1 Brace (minor action)
# ---------------------------------------------------------------------------

def resolve_brace(actor_id: str, state: CombatState, rng: random.Random) -> VerbResult:
    """Resolve Brace minor action: +1 pool, cap 3 uses."""
    from emergence.engine.combat.pool import resolve_brace as _pool_brace
    actor = state.combatants[actor_id]
    success = _pool_brace(actor)
    result = VerbResult(
        verb="Brace",
        actor_id=actor_id,
        target_id=None,
        check=None,
        success_tier="full" if success else "failure",
    )
    result.narrative_data["pool_gained"] = 1 if success else 0
    result.narrative_data["pool_after"] = actor.pool
    result.narrative_data["brace_uses_left"] = actor.brace_uses
    state.action_log.append({
        "round": state.round_number,
        "verb": "Brace",
        "actor": actor_id,
        "success": success,
    })
    return result


# ---------------------------------------------------------------------------
# §5.2 Posture_Change (minor action)
# ---------------------------------------------------------------------------

def resolve_posture_change(
    actor_id: str,
    new_posture: str,
    state: CombatState,
    rng: random.Random,
) -> VerbResult:
    """Resolve Posture_Change minor action."""
    from emergence.engine.combat.postures import change_posture, validate_posture_rider_compat
    from emergence.engine.combat.pool import recalc_effective_pool_max
    actor = state.combatants[actor_id]
    old_posture = change_posture(actor, new_posture)
    # Disarm incompatible riders
    disarmed = []
    remaining = []
    for rider in actor.armed_posture_riders:
        sub = rider.get("sub_category", "")
        compat = rider.get("compatible_postures", [])
        if validate_posture_rider_compat(sub, new_posture, compat):
            remaining.append(rider)
        else:
            disarmed.append(rider)
    actor.armed_posture_riders = remaining
    recalc_effective_pool_max(actor)
    # Hidden breaks on Aggressive
    if new_posture == "aggressive" and actor.hidden:
        actor.hidden = False
    result = VerbResult(
        verb="Posture_Change",
        actor_id=actor_id,
        target_id=None,
        check=None,
        success_tier="full",
    )
    result.narrative_data["old_posture"] = old_posture
    result.narrative_data["new_posture"] = new_posture
    result.narrative_data["disarmed_riders"] = disarmed
    state.action_log.append({
        "round": state.round_number,
        "verb": "Posture_Change",
        "actor": actor_id,
        "posture": new_posture,
    })
    return result


# ---------------------------------------------------------------------------
# §5.3 Utility (minor action)
# ---------------------------------------------------------------------------

def resolve_utility(
    actor_id: str,
    utility_type: str,
    state: CombatState,
    rng: random.Random,
    target_id: Optional[str] = None,
) -> VerbResult:
    """Resolve Utility minor action."""
    actor = state.combatants[actor_id]
    result = VerbResult(
        verb="Utility",
        actor_id=actor_id,
        target_id=target_id,
        check=None,
        success_tier="full",
    )
    if utility_type == "brief_assess":
        p_die = _get_attr(actor, "perception")
        s_die = _get_attr(actor, "insight")
        mods = [state.status_engine.get_check_modifiers(actor_id, "Assess")]
        check = roll_check(p_die, s_die, mods, 13, rng)
        tier = SuccessTier(check.tier)
        result.check = check
        result.success_tier = check.tier
        if tier in (SuccessTier.CRITICAL, SuccessTier.FULL, SuccessTier.MARGINAL):
            result.narrative_data["facts_revealed"] = 1
        if tier == SuccessTier.CRITICAL and target_id:
            _apply_status(state, target_id, StatusName.MARKED, -1, result)
    elif utility_type == "aid" and target_id:
        result.narrative_data["ally_bonus"] = 1
    elif utility_type == "verbal_shout" and target_id:
        if state.status_engine.has_status(target_id, StatusName.SHAKEN):
            state.status_engine.remove_status(target_id, StatusName.SHAKEN)
            result.narrative_data["removed_shaken"] = True
    elif utility_type == "interact_object":
        result.narrative_data["interacted"] = True
    state.action_log.append({
        "round": state.round_number,
        "verb": "Utility",
        "actor": actor_id,
        "type": utility_type,
    })
    return result


# ---------------------------------------------------------------------------
# §5.4 Power_Minor (minor action)
# ---------------------------------------------------------------------------

def resolve_power_minor(
    actor_id: str,
    target_id: str,
    power_id: str,
    cast_slot: str,
    state: CombatState,
    rng: random.Random,
    power_category: str = "somatic",
) -> VerbResult:
    """Resolve Power_Minor: minor-action cast, pool cost 1, reduced effect."""
    from emergence.engine.combat.pool import can_spend_pool, spend_pool
    actor = state.combatants[actor_id]
    target = state.combatants.get(target_id)
    # Check scene cost
    scene_key = f"{power_id}:{cast_slot}"
    if scene_key in actor.scene_mode_uses:
        return VerbResult(
            verb="Power_Minor",
            actor_id=actor_id,
            target_id=target_id,
            check=None,
            success_tier="failure",
            narrative_data={"reason": "scene_cost_spent"},
        )
    # Pool cost = 1 for minor casts
    if not can_spend_pool(actor, 1):
        return VerbResult(
            verb="Power_Minor",
            actor_id=actor_id,
            target_id=target_id,
            check=None,
            success_tier="failure",
            narrative_data={"reason": "insufficient_pool"},
        )
    spend_pool(actor, 1)
    # Roll
    attr_pair = _POWER_ATTR_PAIRS.get(power_category, ("will", "insight"))
    p_die = _get_attr(actor, attr_pair[0])
    s_die = _get_attr(actor, attr_pair[1])
    mods = _build_modifiers(actor, target, state)
    check = roll_check(p_die, s_die, mods, 10, rng)
    tier = SuccessTier(check.tier)
    result = VerbResult(
        verb="Power_Minor",
        actor_id=actor_id,
        target_id=target_id,
        check=check,
        success_tier=check.tier,
    )
    result.narrative_data["power_id"] = power_id
    result.narrative_data["cast_slot"] = cast_slot
    result.narrative_data["pool_spent"] = 1
    result.narrative_data["pool_after"] = actor.pool
    # Minor casts deal ~60% damage of standard
    if tier in (SuccessTier.CRITICAL, SuccessTier.FULL) and target_id:
        dmg = max(1, 2)  # base minor damage
        track = _TRACK_FOR_DAMAGE_TYPE.get(power_category, "physical")
        state.apply_damage(target_id, dmg, track)
        result.damage_dealt = dmg
        result.damage_track = track
    state.action_log.append({
        "round": state.round_number,
        "verb": "Power_Minor",
        "actor": actor_id,
        "target": target_id,
        "power": power_id,
    })
    return result
