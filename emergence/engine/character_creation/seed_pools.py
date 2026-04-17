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

def _compute_v1(state: CreationState) -> SeedPools:
    """V1 stub — filled in 1.2.b."""
    raise NotImplementedError("v1 compute — wired in 1.2.b")


def _compute_v2(state: CreationState) -> SeedPools:
    """V2 stub — filled in 1.2.c."""
    raise NotImplementedError("v2 compute — wired in 1.2.c")


def _compute_v3(state: CreationState) -> SeedPools:
    """V3 stub — filled in 1.2.d."""
    raise NotImplementedError("v3 compute — wired in 1.2.d")


def _compute_v4(state: CreationState) -> SeedPools:
    """V4 stub — filled in 1.2.e."""
    raise NotImplementedError("v4 compute — wired in 1.2.e")
