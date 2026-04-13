"""Data loaders for combat content: powers, enemy templates, encounters.

Reads JSON files from the data/ directory tree and returns typed objects
using the schema classes from engine.schemas.content and engine.schemas.encounter.
"""

import json
import os
from typing import Dict, List

from emergence.engine.schemas.content import Power, EnemyTemplate
from emergence.engine.schemas.encounter import EncounterSpec


def load_powers(directory: str) -> Dict[str, Power]:
    """Load all power JSON files from *directory* and return {id: Power}."""
    powers: Dict[str, Power] = {}
    if not os.path.isdir(directory):
        return powers
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        with open(path, "r") as f:
            entries = json.load(f)
        for entry in entries:
            p = Power.from_dict(entry)
            powers[p.id] = p
    return powers


def load_enemies(directory: str) -> Dict[str, EnemyTemplate]:
    """Load all enemy template JSON files from *directory* and return {id: EnemyTemplate}."""
    enemies: Dict[str, EnemyTemplate] = {}
    if not os.path.isdir(directory):
        return enemies
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(directory, fname)
        with open(path, "r") as f:
            entries = json.load(f)
        for entry in entries:
            e = EnemyTemplate.from_dict(entry)
            enemies[e.id] = e
    return enemies


def load_encounters(path: str) -> List[EncounterSpec]:
    """Load encounter specs from a single JSON file at *path*.

    Returns a list of EncounterSpec objects.
    """
    if not os.path.isfile(path):
        return []
    with open(path, "r") as f:
        entries = json.load(f)
    return [EncounterSpec.from_dict(entry) for entry in entries]
