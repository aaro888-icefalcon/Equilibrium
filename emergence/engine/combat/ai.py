"""Enemy AI decision engine for Emergence combat.

Implements 5 AI profiles: aggressive, defensive, tactical, opportunist, pack.
Each profile uses weighted feature scoring to choose actions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class AiProfileType(str, Enum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    TACTICAL = "tactical"
    OPPORTUNIST = "opportunist"
    PACK = "pack"


# Feature weight tables per profile
AI_WEIGHTS: Dict[str, Dict[str, float]] = {
    "aggressive": {
        "target_damage_expectation": 1.5,
        "target_exposure_fill": 1.0,
        "self_risk": -0.25,
        "position_value": 0.25,
        "tempo": 0.5,
        "allies_need": 0.0,
        "threat_to_self": 0.0,
        "parley_signal": -0.5,
    },
    "defensive": {
        "target_damage_expectation": 0.5,
        "target_exposure_fill": 0.25,
        "self_risk": -1.5,
        "position_value": 1.0,
        "tempo": 0.25,
        "allies_need": 1.0,
        "threat_to_self": 0.5,
        "parley_signal": 1.0,
    },
    "tactical": {
        "target_damage_expectation": 0.75,
        "target_exposure_fill": 1.25,
        "self_risk": -0.5,
        "position_value": 0.75,
        "tempo": 0.75,
        "allies_need": 0.5,
        "threat_to_self": 0.25,
        "parley_signal": 0.5,
    },
    "opportunist": {
        "target_damage_expectation": 1.0,
        "target_exposure_fill": 1.5,
        "self_risk": -1.0,
        "position_value": 0.5,
        "tempo": 1.0,
        "allies_need": 0.0,
        "threat_to_self": 0.5,
        "parley_signal": 0.25,
    },
    "pack": {
        "target_damage_expectation": 1.0,
        "target_exposure_fill": 1.25,
        "self_risk": -0.5,
        "position_value": 0.5,
        "tempo": 0.5,
        "allies_need": 0.25,
        "threat_to_self": 0.0,
        "parley_signal": -0.5,
        "coordination_bonus": 1.5,
    },
}

# Retreat thresholds per profile
RETREAT_THRESHOLDS: Dict[str, Dict[str, object]] = {
    "aggressive": {"phy_threshold": 4, "require_no_ally": True},
    "defensive": {"phy_threshold": 3, "or_no_allies": True},
    "tactical": {"phy_threshold": 4, "require_no_ally": True, "mission_fail": True},
    "opportunist": {"phy_threshold": 2, "threat_sensitive": True},
    "pack": {"min_pack_size": 2, "rounds_alone": 2},
}


@dataclass
class CombatAction:
    """A candidate action for AI evaluation."""
    action_type: str   # Rev 4: Attack, Power, Power_Minor, Assess, Maneuver, Parley, Finisher, Brace, Posture_Change, Utility
    target_id: Optional[str] = None
    power_id: Optional[str] = None
    zone_id: Optional[str] = None
    is_major: bool = True
    sub_type: Optional[str] = None  # Rev 4: attack/maneuver/parley sub-type

    @property
    def sort_key(self) -> str:
        return f"{self.action_type}_{self.target_id or ''}_{self.power_id or ''}"


@dataclass
class CombatantState:
    """Minimal combatant state for AI decisions."""
    id: str
    side: str             # enemy, ally, neutral
    ai_profile: str
    tier: int
    phy_current: int      # current physical track damage (0=fresh, 5=incap)
    phy_max: int = 5
    men_current: int = 0
    soc_current: int = 0
    zone_id: str = ""
    is_exposed: bool = False
    is_marked: bool = False
    is_shaken: bool = False
    is_stunned: bool = False
    is_bleeding: bool = False
    momentum: int = 0
    powers: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    retreat_conditions: List[str] = field(default_factory=list)
    parley_conditions: List[str] = field(default_factory=list)
    # Rev 4 additions
    hidden: bool = False
    current_posture: str = "parry"
    pool: int = 0
    pool_max: int = 6
    armed_rider_count: int = 0


@dataclass
class BattlefieldState:
    """Snapshot of combat state for AI decisions."""
    combatants: Dict[str, CombatantState] = field(default_factory=dict)
    zones: List[dict] = field(default_factory=list)
    round_number: int = 1
    player_parleyed_recently: bool = False
    pack_target_id: Optional[str] = None  # convergence target for pack AI


class AiDecisionEngine:
    """Chooses actions for AI-controlled combatants."""

    def choose_action(self, actor: CombatantState, state: BattlefieldState) -> CombatAction:
        """Choose the best Major action for this actor."""
        profile = actor.ai_profile

        # Check retreat first (disengage absorbed into reposition maneuver)
        if self.should_retreat(actor, state):
            return CombatAction(action_type="Maneuver", sub_type="reposition")

        candidates = self._enumerate_major_actions(actor, state)
        if not candidates:
            return CombatAction(action_type="Attack", sub_type="heavy")

        scored = [(self._score_action(actor, a, state), a.sort_key, a) for a in candidates]
        scored.sort(key=lambda x: (-x[0], x[1]))  # highest score, then lexicographic tie
        return scored[0][2]

    def choose_minor(self, actor: CombatantState, state: BattlefieldState) -> Optional[CombatAction]:
        """Choose best Minor action (Rev 4: Brace, Assess, Maneuver, etc.)."""
        profile = actor.ai_profile

        # Defensive/tactical: Brace if pool < pool_max and uses remain
        if profile in ("defensive", "tactical") and actor.pool < actor.pool_max:
            return CombatAction(action_type="Brace", is_major=False)

        # Tactical prefers Brief Assess on round 1
        if profile == "tactical" and state.round_number == 1:
            target = self.pick_target(actor, state)
            if target:
                return CombatAction(action_type="Utility", target_id=target, is_major=False, sub_type="brief_assess")

        # Opportunist: try Conceal if not hidden
        if profile == "opportunist" and not actor.hidden:
            return CombatAction(action_type="Maneuver", is_major=False, sub_type="conceal")

        # Default: Brief Assess highest-threat enemy
        target = self.pick_target(actor, state)
        if target:
            return CombatAction(action_type="Utility", target_id=target, is_major=False, sub_type="brief_assess")

        # Fallback: Brace if pool isn't full
        if actor.pool < actor.pool_max:
            return CombatAction(action_type="Brace", is_major=False)
        return None

    def should_retreat(self, actor: CombatantState, state: BattlefieldState) -> bool:
        """Check retreat conditions per profile."""
        profile = actor.ai_profile
        thresh = RETREAT_THRESHOLDS.get(profile, {})

        if profile == "aggressive":
            phy_thresh = thresh.get("phy_threshold", 4)
            has_ally = self._has_nearby_ally(actor, state)
            return actor.phy_current >= phy_thresh and not has_ally

        elif profile == "defensive":
            phy_thresh = thresh.get("phy_threshold", 3)
            has_allies = self._count_allies(actor, state) > 0
            return actor.phy_current >= phy_thresh and not has_allies

        elif profile == "tactical":
            phy_thresh = thresh.get("phy_threshold", 4)
            has_ally = self._has_nearby_ally(actor, state)
            return actor.phy_current >= phy_thresh and not has_ally

        elif profile == "opportunist":
            phy_thresh = thresh.get("phy_threshold", 2)
            threat = self._highest_threat(actor, state)
            return actor.phy_current >= phy_thresh and threat > 0.5

        elif profile == "pack":
            pack_count = self._count_pack_allies(actor, state)
            return pack_count < 2

        return False

    def pick_target(self, actor: CombatantState, state: BattlefieldState) -> Optional[str]:
        """Pick best target per profile's priority rules."""
        enemies = self._get_enemies(actor, state)
        if not enemies:
            return None

        profile = actor.ai_profile

        if profile == "aggressive":
            # Lowest phy; on tie highest threat
            enemies.sort(key=lambda e: (-(5 - e.phy_current), -e.tier))
            return enemies[0].id

        elif profile == "defensive":
            # Highest threat to self
            enemies.sort(key=lambda e: -e.tier)
            return enemies[0].id

        elif profile == "tactical":
            # Exposed first, then highest tier
            exposed = [e for e in enemies if e.is_exposed]
            if exposed:
                return exposed[0].id
            enemies.sort(key=lambda e: -e.tier)
            return enemies[0].id

        elif profile == "opportunist":
            # Exposed > Marked > lowest phy > isolated
            exposed = [e for e in enemies if e.is_exposed]
            if exposed:
                return exposed[0].id
            marked = [e for e in enemies if e.is_marked]
            if marked:
                return marked[0].id
            enemies.sort(key=lambda e: -(5 - e.phy_current))
            return enemies[0].id

        elif profile == "pack":
            # Converge on single target
            if state.pack_target_id and state.pack_target_id in state.combatants:
                target = state.combatants[state.pack_target_id]
                if target.phy_current < 5:
                    return state.pack_target_id
            # Pick lowest phy
            enemies.sort(key=lambda e: -(5 - e.phy_current))
            return enemies[0].id

        return enemies[0].id if enemies else None

    # ── internal helpers ─────────────────────────────────────────────

    def _enumerate_major_actions(
        self, actor: CombatantState, state: BattlefieldState
    ) -> List[CombatAction]:
        """List all legal Major actions."""
        actions: List[CombatAction] = []
        enemies = self._get_enemies(actor, state)

        for e in enemies:
            actions.append(CombatAction(action_type="Attack", target_id=e.id))

        for pid in actor.powers:
            for e in enemies:
                actions.append(CombatAction(action_type="Power", target_id=e.id, power_id=pid))

        # Rev 4: Maneuver sub-types
        actions.append(CombatAction(action_type="Maneuver", sub_type="reposition"))
        actions.append(CombatAction(action_type="Maneuver", sub_type="disrupt"))

        if actor.parley_conditions:
            for e in enemies:
                actions.append(CombatAction(action_type="Parley", target_id=e.id, sub_type="demand"))
                actions.append(CombatAction(action_type="Parley", target_id=e.id, sub_type="taunt"))

        # Finisher if target exposed and momentum >= 5
        for e in enemies:
            if e.is_exposed and actor.momentum >= 5:
                actions.append(CombatAction(action_type="Finisher", target_id=e.id))

        return actions

    def _score_action(
        self, actor: CombatantState, action: CombatAction, state: BattlefieldState
    ) -> float:
        """Score a candidate action using the profile's weight table."""
        profile = actor.ai_profile
        # Pack degrades to aggressive if fewer than 2 allies
        if profile == "pack" and self._count_pack_allies(actor, state) < 2:
            profile = "aggressive"

        weights = AI_WEIGHTS.get(profile, AI_WEIGHTS["aggressive"])
        features = self._compute_features(actor, action, state)
        score = sum(weights.get(k, 0.0) * v for k, v in features.items())
        return score

    def _compute_features(
        self, actor: CombatantState, action: CombatAction, state: BattlefieldState
    ) -> Dict[str, float]:
        """Compute feature vector for a candidate action."""
        f: Dict[str, float] = {
            "target_damage_expectation": 0.0,
            "target_exposure_fill": 0.0,
            "self_risk": 0.0,
            "position_value": 0.0,
            "tempo": 0.0,
            "allies_need": 0.0,
            "threat_to_self": 0.0,
            "parley_signal": 0.0,
            "coordination_bonus": 0.0,
        }

        target = state.combatants.get(action.target_id or "", None)

        if action.action_type == "Attack" and target:
            # Estimate damage relative to d8 baseline
            f["target_damage_expectation"] = min(1.0, actor.tier * 0.15 + 0.3)
            f["target_exposure_fill"] = 0.3
            if target.is_exposed:
                f["target_damage_expectation"] += 0.2
            if target.is_marked:
                f["target_damage_expectation"] += 0.15
            f["self_risk"] = 0.2 if target.tier >= actor.tier else 0.1
            f["tempo"] = 0.25

        elif action.action_type == "Power" and target:
            f["target_damage_expectation"] = min(1.0, actor.tier * 0.2 + 0.2)
            f["target_exposure_fill"] = 0.4
            f["self_risk"] = 0.15
            f["tempo"] = 0.3

        elif action.action_type == "Assess":
            f["position_value"] = 0.4
            f["tempo"] = 0.5
            f["self_risk"] = 0.0

        elif action.action_type == "Maneuver":
            f["position_value"] = 0.6
            f["self_risk"] = 0.1

        elif action.action_type == "Parley":
            f["parley_signal"] = 1.0 if state.player_parleyed_recently else 0.3
            f["self_risk"] = 0.0

        elif action.action_type == "Finisher" and target:
            f["target_damage_expectation"] = 1.0
            f["target_exposure_fill"] = 1.0
            f["tempo"] = 1.0

        # Allies need: check if any ally is exposed or low
        allies = [c for c in state.combatants.values()
                  if c.side == actor.side and c.id != actor.id]
        if any(a.is_exposed or a.phy_current >= 4 for a in allies):
            f["allies_need"] = 1.0

        # Threat to self
        enemies = self._get_enemies(actor, state)
        if enemies:
            max_threat = max(e.tier for e in enemies)
            f["threat_to_self"] = min(1.0, max_threat / 10.0)

        # Pack coordination bonus
        if actor.ai_profile == "pack" and action.target_id:
            pack_on_same = sum(
                1 for c in state.combatants.values()
                if c.side == actor.side and c.id != actor.id
                and c.ai_profile == "pack"
            )
            if pack_on_same >= 2:
                f["coordination_bonus"] = 1.0

        return f

    def _get_enemies(self, actor: CombatantState, state: BattlefieldState) -> List[CombatantState]:
        return [
            c for c in state.combatants.values()
            if c.side != actor.side and c.phy_current < 5
        ]

    def _has_nearby_ally(self, actor: CombatantState, state: BattlefieldState) -> bool:
        return self._count_allies(actor, state) > 0

    def _count_allies(self, actor: CombatantState, state: BattlefieldState) -> int:
        return sum(
            1 for c in state.combatants.values()
            if c.side == actor.side and c.id != actor.id and c.phy_current < 5
        )

    def _count_pack_allies(self, actor: CombatantState, state: BattlefieldState) -> int:
        return sum(
            1 for c in state.combatants.values()
            if c.side == actor.side and c.id != actor.id
            and c.ai_profile == "pack" and c.phy_current < 5
        )

    def _highest_threat(self, actor: CombatantState, state: BattlefieldState) -> float:
        enemies = self._get_enemies(actor, state)
        if not enemies:
            return 0.0
        return max(e.tier for e in enemies) / 10.0
