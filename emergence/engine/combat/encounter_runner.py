"""Encounter runner for the Emergence combat engine.

Orchestrates an EncounterSpec into a CombatOutcome by running the full
turn loop per combat-spec.md Section 3.  All randomness flows through
an injected random.Random instance for deterministic replay.

Uses only the Python standard library.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.schemas.encounter import (
    CombatOutcome,
    EncounterSpec,
    Action,
    EnemyState,
    WorldConsequence,
)
from emergence.engine.combat.verbs import (
    CombatState,
    CombatantRecord,
    VerbResult,
    resolve_attack,
    resolve_power,
    resolve_assess,
    resolve_maneuver,
    resolve_parley,
    resolve_disengage,
    resolve_finisher,
    resolve_defend,
)
from emergence.engine.combat.statuses import StatusEngine, StatusName, ActiveStatus
from emergence.engine.combat.ai import AiDecisionEngine, CombatantState, BattlefieldState
from emergence.engine.combat.damage import AFFINITY_PROFILES


# ---------------------------------------------------------------------------
# Max rounds safeguard (spec §3.7: >6 rounds = design failure)
# ---------------------------------------------------------------------------
MAX_ROUNDS = 12


class EncounterRunner:
    """Runs a single encounter from spec to outcome."""

    def __init__(self) -> None:
        self._ai = AiDecisionEngine()

    # -----------------------------------------------------------------------
    # Public entry point
    # -----------------------------------------------------------------------

    def run(
        self,
        spec: EncounterSpec,
        player_record: CombatantRecord,
        rng: random.Random,
    ) -> CombatOutcome:
        """Execute the encounter and return a CombatOutcome.

        Args:
            spec:           The EncounterSpec describing enemies, zones, conditions.
            player_record:  Pre-built CombatantRecord for the player.
            rng:            Deterministic random source.

        Returns:
            A populated CombatOutcome.
        """
        state = self._build_state(spec, player_record)
        initiative_order = self._roll_initiative(state, rng)
        state.initiative_order = initiative_order

        outcome = self._run_loop(state, spec, rng)
        return outcome

    # -----------------------------------------------------------------------
    # State construction
    # -----------------------------------------------------------------------

    def _build_state(
        self, spec: EncounterSpec, player_record: CombatantRecord
    ) -> CombatState:
        """Assemble CombatState from EncounterSpec and player record."""
        state = CombatState(
            zones=spec.terrain_zones if spec.terrain_zones else [],
            combat_register=spec.combat_register,
        )

        # Add player
        player_record.side = "player"
        state.combatants[player_record.id] = player_record

        # Add enemies from spec
        for enemy_entry in spec.enemies:
            rec = self._enemy_entry_to_record(enemy_entry)
            state.combatants[rec.id] = rec

        # Ecological clock for creature register
        if spec.combat_register == "creature":
            state.scene_clocks["ecological"] = 0
        # Eldritch attention clock
        if spec.combat_register == "eldritch":
            state.scene_clocks["eldritch_attention"] = 0

        return state

    def _enemy_entry_to_record(self, entry: Dict[str, Any]) -> CombatantRecord:
        """Convert a spec enemy entry dict into a CombatantRecord."""
        instance_id = entry.get("instance_id", entry.get("template_id", "enemy"))
        tier = entry.get("tier", 1)
        attrs = entry.get("attribute_defaults", {})
        ct_max = entry.get("condition_track_max", {"physical": 5, "mental": 5, "social": 5})
        affinity_table = entry.get("affinity_table", {})
        ai_profile = entry.get("ai_profile", "aggressive")
        exposure_max = entry.get("exposure_max", 3)

        return CombatantRecord(
            id=instance_id,
            side="enemy",
            tier=tier,
            strength=attrs.get("strength", 6),
            agility=attrs.get("agility", 6),
            perception=attrs.get("perception", 6),
            will=attrs.get("will", 6),
            insight=attrs.get("insight", 6),
            might=attrs.get("might", 6),
            phy_max=ct_max.get("physical", 5),
            men_max=ct_max.get("mental", 5),
            soc_max=ct_max.get("social", 5),
            affinities=affinity_table,
            ai_profile=ai_profile,
            exposure_max=exposure_max,
            powers=entry.get("powers", []),
        )

    # -----------------------------------------------------------------------
    # Initiative
    # -----------------------------------------------------------------------

    def _roll_initiative(
        self, state: CombatState, rng: random.Random
    ) -> List[str]:
        """Roll initiative for all combatants; return ordered list of ids."""
        rolls: List[Tuple[str, int, int]] = []
        for cid, c in state.combatants.items():
            bonus = max(c.agility, c.perception) // 2
            roll = rng.randint(1, 20) + bonus
            tiebreak = rng.randint(1, 10)
            rolls.append((cid, roll, tiebreak))
        rolls.sort(key=lambda x: (x[1], x[2]), reverse=True)
        return [cid for cid, _, _ in rolls]

    # -----------------------------------------------------------------------
    # Main round loop
    # -----------------------------------------------------------------------

    def _run_loop(
        self,
        state: CombatState,
        spec: EncounterSpec,
        rng: random.Random,
    ) -> CombatOutcome:
        """Execute rounds until a win/loss/escape condition is met."""
        resolution = "stalemate"
        rounds_completed = 0

        for round_num in range(1, MAX_ROUNDS + 1):
            state.round_number = round_num

            # Phase 1: start-of-round tick
            self._tick_start(state, rng)

            # Phase 2-4: each combatant acts in initiative order
            for cid in list(state.initiative_order):
                c = state.combatants.get(cid)
                if not c or not c.active or c.is_incapacitated():
                    continue
                can_major, can_minor = state.status_engine.can_act(cid)
                if c.side == "player":
                    self._player_turn(cid, state, rng, can_major, can_minor)
                else:
                    self._enemy_turn(cid, state, rng, can_major, can_minor)

            # Phase 5: end-of-round tick
            self._tick_end(state)

            rounds_completed = round_num

            # Check win/loss/escape
            result = self._check_conditions(state, spec, round_num)
            if result:
                resolution = result
                break

        return self._build_outcome(state, spec, resolution, rounds_completed)

    # -----------------------------------------------------------------------
    # Start/end of round ticks
    # -----------------------------------------------------------------------

    def _tick_start(self, state: CombatState, rng: random.Random) -> None:
        """Apply start-of-round status ticks to all combatants."""
        for cid, c in list(state.combatants.items()):
            if not c.active:
                continue
            effects = state.status_engine.tick_start_of_round(cid, rng)
            for eff in effects:
                if eff["type"] == "damage":
                    track = eff.get("track", "physical")
                    state.apply_damage(cid, eff["amount"], track)
                elif eff["type"] == "apply_status":
                    state.status_engine.apply_status(cid, ActiveStatus(
                        name=eff["status"],
                        duration=2,
                        source="corrupted",
                        applied_round=state.round_number,
                    ))

    def _tick_end(self, state: CombatState) -> None:
        """Decrement status durations; decay exposure; advance clocks."""
        for cid, c in list(state.combatants.items()):
            if not c.active:
                continue
            state.status_engine.tick_end_of_round(cid)
            # Exposure decay: if no damage taken this round, decay by 1
            # (simplified: check if no damage-dealing actions targeted this cid in log)
            round_log = [e for e in state.action_log
                         if e.get("round") == state.round_number
                         and e.get("target") == cid
                         and e.get("damage", 0) > 0]
            if not round_log and c.exposure > 0:
                c.exposure = max(0, c.exposure - 1)
                if c.exposure < c.exposure_max:
                    state.status_engine.remove_status(cid, StatusName.EXPOSED)

        # Advance register clocks
        if state.combat_register == "creature":
            # Each round in creature territory: +1 clock
            state.scene_clocks["ecological"] = state.scene_clocks.get("ecological", 0) + 1
        elif state.combat_register == "eldritch":
            state.scene_clocks["eldritch_attention"] = state.scene_clocks.get("eldritch_attention", 0)
