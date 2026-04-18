"""Persistence helpers for CreationState and QuestState during session zero.

Both live under the save root while creation is in progress:
    save_root/session_zero_state.json   — CreationState (dict form)
    save_root/quests.json                — QuestState (dict form)

On finalize, CreationState's sheet is written to save_root/player/character.json
via the existing LoadManager / SaveManager, and CreationState may be retained
or cleared. QuestState persists into sim play.
"""

from __future__ import annotations

import dataclasses
import json
import os
from typing import Any, Dict

from emergence.engine.character_creation.character_factory import CreationState
from emergence.engine.quests.schema import QuestState


_CREATION_FILE = "session_zero_state.json"
_QUESTS_FILE = "quests.json"


# ---------------------------------------------------------------------------
# CreationState
# ---------------------------------------------------------------------------


def load_creation_state(save_root: str) -> CreationState:
    path = os.path.join(save_root, _CREATION_FILE)
    if not os.path.exists(path):
        return CreationState()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _creation_from_dict(data)


def save_creation_state(save_root: str, state: CreationState) -> None:
    path = os.path.join(save_root, _CREATION_FILE)
    os.makedirs(save_root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_creation_to_dict(state), f, indent=2, default=str)


def clear_creation_state(save_root: str) -> None:
    path = os.path.join(save_root, _CREATION_FILE)
    if os.path.exists(path):
        os.remove(path)


def _creation_to_dict(state: CreationState) -> Dict[str, Any]:
    return dataclasses.asdict(state)


def _creation_from_dict(data: Dict[str, Any]) -> CreationState:
    # Build a CreationState with all supplied fields; unknown keys are ignored.
    field_names = {f.name for f in dataclasses.fields(CreationState)}
    filtered = {k: v for k, v in data.items() if k in field_names}
    return CreationState(**filtered)


# ---------------------------------------------------------------------------
# QuestState
# ---------------------------------------------------------------------------


def load_quest_state(save_root: str) -> QuestState:
    path = os.path.join(save_root, _QUESTS_FILE)
    if not os.path.exists(path):
        return QuestState()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return QuestState.from_dict(data)


def save_quest_state(save_root: str, quest_state: QuestState) -> None:
    path = os.path.join(save_root, _QUESTS_FILE)
    os.makedirs(save_root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(quest_state.to_dict(), f, indent=2, default=str)


def clear_quest_state(save_root: str) -> None:
    path = os.path.join(save_root, _QUESTS_FILE)
    if os.path.exists(path):
        os.remove(path)
