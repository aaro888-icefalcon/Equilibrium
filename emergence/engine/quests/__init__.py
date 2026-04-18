"""Quest module — authoritative quest state and lifecycle.

Exports:
  - Quest, BrightLine, Macrostructure, Resolution, ProgressTrack, Scope,
    HookScene, CentralConflict, QuestState, Predicate
  - QuestValidationError, validate_quest
  - init, tick, check_success, resolve (CLI-facing)

All mutation of QuestState routes through quest.init / tick / check_success /
resolve. Narrator code must never write Quest fields directly.
"""

from emergence.engine.quests.schema import (
    BrightLine,
    CentralConflict,
    HookScene,
    Macrostructure,
    Predicate,
    ProgressTrack,
    Quest,
    QuestState,
    QuestValidationError,
    Resolution,
    Scope,
    validate_quest,
)
from emergence.engine.quests.quest import (
    abandon_not_supported,
    check_success,
    init,
    resolve,
    tick,
)

__all__ = [
    "BrightLine",
    "CentralConflict",
    "HookScene",
    "Macrostructure",
    "Predicate",
    "ProgressTrack",
    "Quest",
    "QuestState",
    "QuestValidationError",
    "Resolution",
    "Scope",
    "validate_quest",
    "init",
    "tick",
    "check_success",
    "resolve",
    "abandon_not_supported",
]
