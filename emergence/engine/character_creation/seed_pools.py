"""Seed pool computation for Year One vignettes.

Given a CreationState and a vignette index (1..4), returns the NPC archetypes,
factions, locations, threats, and vow packages in reach for that vignette.
Implements the accumulating-state filter described in the v4 spec:

  V1 (weeks after Onset):    region unlocked; pools are NYC-default unless bio
                             strongly implies outer-borough.
  V2 (autumn Y1, region-lock): three outcomes — stay_nyc, displaced_to,
                             traveled_to (traveled_to only if V1 surfaced a
                             named NPC with non-local origin; otherwise
                             replaced with a second displaced variant).
  V3 (winter Y1):            filtered by now-locked region; excludes archetypes
                             already consumed by V1/V2 unless `recurrable`.
  V4 (spring Y2):            filtered by region; must include ≥1 named
                             antagonist and ≥1 startable location candidate.

No new content tables.  Reuses REGIONS, REGION_FACTIONS, FACTION_DEMANDS,
VOW_PACKAGES, SURVIVAL_POOL, and the threat archetype registry.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.character_factory import CreationState


@dataclasses.dataclass
class SeedPools:
    """Options in reach for one vignette."""

    vignette_index: int
    region: Optional[str]                      # locked region if known, else None
    npc_archetypes: List[str]                  # archetype ids (for generate_npc)
    factions: List[Dict[str, Any]]             # [{id, name, demand_data}]
    locations: List[Dict[str, Any]]            # [{id, name, region, startable}]
    threats: List[str]                         # threat archetype ids
    vow_packages: List[Dict[str, Any]]         # entries from VOW_PACKAGES
    region_outcomes: Optional[List[str]]       # V2 only; else None
    notes: List[str] = dataclasses.field(default_factory=list)


def compute_seed_pools(
    state: CreationState,
    vignette_index: int,
) -> SeedPools:
    """Return the SeedPools scoped to *vignette_index* for this *state*.

    vignette_index ∈ {1, 2, 3, 4} — the YearOneVignetteScene index, not the
    overall scene index (scenes 2-5 correspond to vignettes 1-4).
    """
    if vignette_index not in {1, 2, 3, 4}:
        raise ValueError(f"vignette_index must be 1..4, got {vignette_index}")

    # Branch by index; each branch fills a SeedPools and returns it.
    if vignette_index == 1:
        return _compute_v1(state)
    if vignette_index == 2:
        return _compute_v2(state)
    if vignette_index == 3:
        return _compute_v3(state)
    return _compute_v4(state)


# Branch implementations follow in subsequent commits.

_V1_NPC_ARCHETYPES = [
    "survivor", "rival", "companion", "dependent",
    "medic", "scavenger", "informant", "enforcer",
]

_V1_NYC_LOCATIONS = [
    {"id": "loc-manhattan-midtown",
     "name": "Manhattan midtown",
     "region": "New York City",
     "startable": False},
    {"id": "loc-brooklyn-tower-districts",
     "name": "Brooklyn tower districts",
     "region": "New York City",
     "startable": False},
]

_V1_NYC_FACTIONS = ["tower-lords", "queens-commonage"]


def _compute_v1(state: CreationState) -> SeedPools:
    """V1: weeks after Onset. NYC-default pools. No prior vignette state.

    Region is not yet locked — V2 decides. V1 presents threats that will
    shape the reaction_tag signal heading into V2; the vignette's picks
    seed NPCs, one threat, and one location in Manhattan or Brooklyn.
    """
    from emergence.engine.character_creation.scenarios import (
        REGION_FACTIONS, FACTION_DEMANDS, VOW_PACKAGES,
    )
    from emergence.engine.character_creation.threats import list_archetype_ids

    # NYC-default factions: tower-lords (primary) + queens-commonage (if seeded).
    factions: List[Dict[str, Any]] = []
    nyc_rep = REGION_FACTIONS.get("New York City", {"id": "tower-lords", "name": "Tower Lords of Brooklyn"})
    factions.append({
        "id": nyc_rep["id"],
        "name": nyc_rep["name"],
        "demand_data": FACTION_DEMANDS.get(nyc_rep["id"], {}),
    })

    # Threats: all archetypes eligible at V1 (no prior exclusions).
    threat_ids = list(list_archetype_ids())

    # Vow packages are seeded at V3+; V1 surfaces none for commitment.
    # However the narrator may reference VOW_PACKAGES motifs for flavor,
    # so we return the list so the scaffold can quote from it.
    vows = [dict(v) for v in VOW_PACKAGES]

    return SeedPools(
        vignette_index=1,
        region="New York City",
        npc_archetypes=list(_V1_NPC_ARCHETYPES),
        factions=factions,
        locations=[dict(loc) for loc in _V1_NYC_LOCATIONS],
        threats=threat_ids,
        vow_packages=vows,
        region_outcomes=None,
        notes=["V1: NYC default, no region lock yet, all threat archetypes eligible"],
    )


def _compute_v2(state: CreationState) -> SeedPools:
    """V2 stub — filled in 1.2.c."""
    raise NotImplementedError("v2 compute — wired in 1.2.c")


def _compute_v3(state: CreationState) -> SeedPools:
    """V3 stub — filled in 1.2.d."""
    raise NotImplementedError("v3 compute — wired in 1.2.d")


def _compute_v4(state: CreationState) -> SeedPools:
    """V4 stub — filled in 1.2.e."""
    raise NotImplementedError("v4 compute — wired in 1.2.e")
