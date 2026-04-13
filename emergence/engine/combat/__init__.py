"""Emergence combat engine — public API surface."""

from emergence.engine.combat.encounter_runner import EncounterRunner
from emergence.engine.combat.verbs import CombatState, CombatantRecord, VerbResult
from emergence.engine.combat.statuses import StatusEngine, StatusName, ActiveStatus
from emergence.engine.combat.ai import AiDecisionEngine, CombatantState, BattlefieldState
from emergence.engine.combat.resolution import roll_check, classify_result
from emergence.engine.combat.damage import resolve_damage, DamageType

__all__ = [
    "EncounterRunner",
    "CombatState",
    "CombatantRecord",
    "VerbResult",
    "StatusEngine",
    "StatusName",
    "ActiveStatus",
    "AiDecisionEngine",
    "CombatantState",
    "BattlefieldState",
    "roll_check",
    "classify_result",
    "resolve_damage",
    "DamageType",
]
