"""Threat archetype registry.

Threat archetypes are forces (NPCs or factions) that press on the character
with unfinished business.  Each archetype binds a display flavor, pressure
bounds, an escalation hook, and a pointer into the combat enemy template
catalog (for MediaResScene's encounter handoff).

The registry is loaded lazily from data/threats/threat_archetypes.json and
cached for the process lifetime.
"""

from __future__ import annotations

import dataclasses
import json
import os
from typing import Dict, List, Optional, Tuple


@dataclasses.dataclass(frozen=True)
class ThreatArchetype:
    """One row in the threat archetype registry."""

    id: str
    display_name: str
    pressure_default: int
    pressure_range: Tuple[int, int]
    escalation_hook: str
    encounter_template: str
    resolution_conditions: List[str]
    register_flavor: str
    recurrable: bool


_REGISTRY: Optional[Dict[str, ThreatArchetype]] = None


def _registry_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(
        os.path.join(here, "..", "..", "data", "threats", "threat_archetypes.json")
    )


def _load_registry() -> Dict[str, ThreatArchetype]:
    path = _registry_path()
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    out: Dict[str, ThreatArchetype] = {}
    for archetype_id, row in raw.items():
        pr = row.get("pressure_range", [1, 5])
        out[archetype_id] = ThreatArchetype(
            id=row.get("id", archetype_id),
            display_name=row.get("display_name", archetype_id),
            pressure_default=int(row.get("pressure_default", 2)),
            pressure_range=(int(pr[0]), int(pr[1])),
            escalation_hook=row.get("escalation_hook", ""),
            encounter_template=row.get("encounter_template", ""),
            resolution_conditions=list(row.get("resolution_conditions", [])),
            register_flavor=row.get("register_flavor", ""),
            recurrable=bool(row.get("recurrable", False)),
        )
    return out


def get_threat_registry() -> Dict[str, ThreatArchetype]:
    """Return the archetype registry, loading once per process."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _load_registry()
    return _REGISTRY


def get_archetype(archetype_id: str) -> Optional[ThreatArchetype]:
    """Look up one archetype by id.  Returns None if unknown."""
    return get_threat_registry().get(archetype_id)


def list_archetype_ids() -> List[str]:
    """Return all archetype ids in registration order."""
    return list(get_threat_registry().keys())


def clamp_pressure(archetype_id: str, pressure: int) -> int:
    """Clamp *pressure* to the archetype's declared range."""
    arc = get_archetype(archetype_id)
    if not arc:
        return max(1, min(5, pressure))
    lo, hi = arc.pressure_range
    return max(lo, min(hi, pressure))
