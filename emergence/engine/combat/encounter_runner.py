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
            state.scene_clocks["eldritch_attention"] = state.scene_clocks.get("eldritch_attention", 0) + 1

    # -----------------------------------------------------------------------
    # State conversion for AI
    # -----------------------------------------------------------------------

    def _to_battlefield_state(self, state: CombatState) -> BattlefieldState:
        """Convert CombatState into a BattlefieldState snapshot for the AI."""
        combatants: Dict[str, CombatantState] = {}
        for cid, c in state.combatants.items():
            combatants[cid] = CombatantState(
                id=cid,
                side=c.side,
                ai_profile=c.ai_profile,
                tier=c.tier,
                phy_current=c.phy,
                phy_max=c.phy_max,
                men_current=c.men,
                soc_current=c.soc,
                is_exposed=state.status_engine.has_status(cid, StatusName.EXPOSED),
                is_marked=state.status_engine.has_status(cid, StatusName.MARKED),
                is_shaken=state.status_engine.has_status(cid, StatusName.SHAKEN),
                is_stunned=state.status_engine.has_status(cid, StatusName.STUNNED),
                is_bleeding=state.status_engine.has_status(cid, StatusName.BLEEDING),
                momentum=c.momentum,
                powers=list(c.powers),
            )
        return BattlefieldState(
            combatants=combatants,
            zones=state.zones,
            round_number=state.round_number,
            player_parleyed_recently=state.player_parleyed_recently,
            pack_target_id=state.pack_target_id,
        )

    # -----------------------------------------------------------------------
    # Action dispatch
    # -----------------------------------------------------------------------

    def _dispatch_action(
        self,
        actor_id: str,
        verb: str,
        target_id: Optional[str],
        power_id: Optional[str],
        state: CombatState,
        rng: random.Random,
    ) -> VerbResult:
        """Route a verb string to the correct resolver and log the result."""
        if verb == "Attack":
            result = resolve_attack(actor_id, target_id or "", state, rng)
        elif verb == "Power":
            result = resolve_power(actor_id, target_id or "", state, rng)
        elif verb == "Assess":
            result = resolve_assess(actor_id, target_id or "", state, rng)
        elif verb == "Maneuver":
            result = resolve_maneuver(actor_id, state, rng, target_id=target_id)
        elif verb == "Parley":
            result = resolve_parley(actor_id, target_id or "", state, rng)
        elif verb == "Disengage":
            result = resolve_disengage(actor_id, state, rng)
        elif verb == "Finisher":
            result = resolve_finisher(actor_id, target_id or "", state, rng)
        elif verb == "Defend":
            result = resolve_defend(actor_id, "", 0, "full", state, rng)
        else:
            result = VerbResult(
                verb=verb, actor_id=actor_id, target_id=target_id,
                check=None, success_tier="full",
            )

        # Log to action_log
        state.action_log.append({
            "round": state.round_number,
            "actor": actor_id,
            "verb": verb,
            "target": target_id,
            "damage": result.damage_dealt,
            "tier": result.success_tier,
        })

        # Register-specific side effects
        self._apply_register_mechanics(actor_id, result, state, rng)

        return result

    # -----------------------------------------------------------------------
    # Player turn
    # -----------------------------------------------------------------------

    def _player_turn(
        self,
        cid: str,
        state: CombatState,
        rng: random.Random,
        can_major: bool,
        can_minor: bool,
    ) -> None:
        """Execute the player's turn with a simple auto-strategy."""
        enemies = state.get_enemies_of("player")
        if not enemies:
            return

        # Minor action: Assess first enemy
        if can_minor:
            self._dispatch_action(cid, "Assess", enemies[0].id, None, state, rng)

        if not can_major:
            return

        # Check for Finisher opportunity
        player = state.combatants[cid]
        for e in enemies:
            if (state.status_engine.has_status(e.id, StatusName.EXPOSED)
                    and player.momentum >= 5):
                self._dispatch_action(cid, "Finisher", e.id, None, state, rng)
                return

        # Default: Attack first enemy
        self._dispatch_action(cid, "Attack", enemies[0].id, None, state, rng)

    # -----------------------------------------------------------------------
    # Enemy turn
    # -----------------------------------------------------------------------

    def _enemy_turn(
        self,
        cid: str,
        state: CombatState,
        rng: random.Random,
        can_major: bool,
        can_minor: bool,
    ) -> None:
        """Execute an enemy's turn using the AI decision engine."""
        bf_state = self._to_battlefield_state(state)
        actor = bf_state.combatants.get(cid)
        if not actor:
            return

        # Minor action
        if can_minor:
            minor = self._ai.choose_minor(actor, bf_state)
            if minor:
                self._dispatch_action(
                    cid, minor.action_type, minor.target_id,
                    minor.power_id, state, rng,
                )

        # Major action
        if can_major:
            action = self._ai.choose_action(actor, bf_state)
            self._dispatch_action(
                cid, action.action_type, action.target_id,
                action.power_id, state, rng,
            )

    # -----------------------------------------------------------------------
    # Win / loss / escape checks
    # -----------------------------------------------------------------------

    def _check_conditions(
        self,
        state: CombatState,
        spec: EncounterSpec,
        round_num: int,
    ) -> Optional[str]:
        """Evaluate terminal conditions. Returns resolution string or None."""
        # Defeat: player incapacitated
        for c in state.combatants.values():
            if c.side == "player" and c.is_incapacitated():
                return "defeat"

        # Victory: all enemies down
        enemies_alive = [
            c for c in state.combatants.values()
            if c.side == "enemy" and c.active and not c.is_incapacitated()
        ]
        if not enemies_alive:
            return "victory"

        # Escape: player successfully disengaged this round
        disengage_log = [
            e for e in state.action_log
            if e.get("round") == round_num
            and e.get("verb") == "Disengage"
            and e.get("actor") in [
                cid for cid, c in state.combatants.items() if c.side == "player"
            ]
            and e.get("tier") in ("critical", "full")
        ]
        if disengage_log:
            return "escape"

        # Spec win conditions
        for wc in spec.win_conditions:
            wc_type = wc.type if hasattr(wc, "type") else wc.get("type", "")
            wc_params = wc.parameters if hasattr(wc, "parameters") else wc.get("parameters", {})
            if wc_type == "survive_rounds":
                target_rounds = wc_params.get("rounds", 99)
                if round_num >= target_rounds:
                    return "victory"
            elif wc_type == "convince_parley":
                parley_ok = [
                    e for e in state.action_log
                    if e.get("verb") == "Parley"
                    and e.get("tier") in ("critical", "full")
                ]
                if parley_ok:
                    return "parley"

        return None

    # -----------------------------------------------------------------------
    # Outcome builder
    # -----------------------------------------------------------------------

    def _build_outcome(
        self,
        state: CombatState,
        spec: EncounterSpec,
        resolution: str,
        rounds_completed: int,
    ) -> CombatOutcome:
        """Assemble a CombatOutcome from final state."""
        from emergence.engine.schemas.encounter import (
            PlayerStateDelta,
            NarrativeLogEntry,
        )

        # Player state delta
        player = None
        for c in state.combatants.values():
            if c.side == "player":
                player = c
                break

        player_delta = PlayerStateDelta(
            condition_changes={
                "physical": player.phy if player else 0,
                "mental": player.men if player else 0,
                "social": player.soc if player else 0,
            },
            heat_accrued=dict(state.heat_deltas),
            corruption_gained=player.corruption if player else 0,
        )

        # Enemy states
        enemy_states: List[EnemyState] = []
        for cid, c in state.combatants.items():
            if c.side == "enemy":
                if c.is_incapacitated():
                    final = "incapacitated"
                elif not c.active:
                    final = "fled"
                else:
                    final = "alive"
                enemy_states.append(EnemyState(
                    enemy_id=cid, final_state=final,
                ))

        # Narrative log
        narrative: List[NarrativeLogEntry] = []
        for entry in state.action_log:
            narrative.append(NarrativeLogEntry(
                turn=entry.get("round", 0),
                actor_id=entry.get("actor", ""),
                action=entry,
                payload={"damage": entry.get("damage", 0), "tier": entry.get("tier", "")},
            ))

        # World consequences
        consequences: List[WorldConsequence] = []
        if state.combat_register == "human" and state.witnesses:
            consequences.append(WorldConsequence(
                type="witness_recorded",
                parameters={"witnesses": list(state.witnesses)},
                scope="local",
            ))
        eco_clock = state.scene_clocks.get("ecological", 0)
        if state.combat_register == "creature" and eco_clock >= 6:
            consequences.append(WorldConsequence(
                type="clock_advance",
                parameters={"clock": "ecological", "value": eco_clock},
            ))

        return CombatOutcome(
            encounter_id=spec.id,
            resolution=resolution,
            rounds_elapsed=rounds_completed,
            player_state_delta=player_delta,
            enemy_states=enemy_states,
            narrative_log=narrative,
            world_consequences=consequences,
        )

    # -----------------------------------------------------------------------
    # Register-specific mechanics
    # -----------------------------------------------------------------------

    def _apply_register_mechanics(
        self,
        actor_id: str,
        result: VerbResult,
        state: CombatState,
        rng: random.Random,
    ) -> None:
        """Apply register-specific side effects after an action resolves."""
        # --- Human register: heat tracking ---
        if state.combat_register == "human":
            target = state.combatants.get(result.target_id or "")
            if target and target.side == "enemy" and target.is_incapacitated():
                state.heat_deltas["kill"] = state.heat_deltas.get("kill", 0) + 1
            if result.verb == "Parley" and result.success_tier in ("critical", "full"):
                state.heat_deltas["spare"] = state.heat_deltas.get("spare", 0) + 1

        # --- Eldritch register: attention + corruption offers ---
        if state.combat_register == "eldritch":
            actor = state.combatants.get(actor_id)
            if actor and actor.side == "enemy":
                attn = state.scene_clocks.get("eldritch_attention", 0) + 1
                state.scene_clocks["eldritch_attention"] = attn
                if attn >= 3 and rng.random() < 0.33:
                    # Corruption offer: apply corrupted to player
                    for cid, c in state.combatants.items():
                        if c.side == "player":
                            state.status_engine.apply_status(cid, ActiveStatus(
                                name=StatusName.CORRUPTED,
                                duration=2,
                                source="eldritch_attention",
                                applied_round=state.round_number,
                            ))
                            break
