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


_V2_DISPLACED_LOCATIONS = [
    {"id": "loc-port-newark-compound", "name": "Port Newark compound",
     "region": "Northern New Jersey", "startable": False},
    {"id": "loc-kingston-hv", "name": "Kingston, Hudson Valley",
     "region": "Hudson Valley", "startable": False},
    {"id": "loc-rutgers-campus", "name": "Rutgers campus, Central Jersey",
     "region": "Central New Jersey", "startable": False},
]

_V2_TRAVELED_LOCATIONS = [
    {"id": "loc-philadelphia-bourse-floor", "name": "Philadelphia Bourse floor",
     "region": "Philadelphia", "startable": False},
    {"id": "loc-lehigh-allentown", "name": "Allentown, Lehigh Valley",
     "region": "Lehigh Valley", "startable": False},
    {"id": "loc-delmarva-granary", "name": "Delmarva granary",
     "region": "Delmarva", "startable": False},
]


def _v1_surfaced_non_local(state: CreationState) -> bool:
    """Heuristic: did V1 produce an NPC or history entry pointing outside NYC?"""
    for npc in state.generated_npcs:
        loc = (npc.get("location") or "").lower()
        if loc and not loc.startswith("loc-manhattan") and not loc.startswith("loc-brooklyn"):
            return True
    for entry in state.history:
        desc = (entry.get("description") or "").lower()
        if any(k in desc for k in ("jersey", "philadelphia", "hudson", "lehigh", "delmarva")):
            return True
    return False


def _compute_v2(state: CreationState) -> SeedPools:
    """V2: autumn Y1.  The region-lock vignette.

    Three region_outcomes — stay_nyc, displaced_to, traveled_to — unless V1
    did not surface a non-local NPC or travel hook; then traveled_to is
    substituted with a second displaced_to option.  The narrator offers
    three distinct choices, each binding a different region outcome; the
    validator enforces either the {stay, displaced, traveled} set or the
    {stay, displaced, displaced} set.
    """
    from emergence.engine.character_creation.scenarios import (
        REGION_FACTIONS, FACTION_DEMANDS, VOW_PACKAGES,
    )
    from emergence.engine.character_creation.threats import (
        get_archetype, list_archetype_ids,
    )

    travel_enabled = _v1_surfaced_non_local(state)

    # Locations: one stay, one displaced, one travel (or second displaced).
    locations: List[Dict[str, Any]] = list(_V1_NYC_LOCATIONS[:1])  # stay candidate
    locations.extend(_V2_DISPLACED_LOCATIONS[:1])                   # displaced candidate
    if travel_enabled:
        locations.extend(_V2_TRAVELED_LOCATIONS[:1])
    else:
        locations.extend(_V2_DISPLACED_LOCATIONS[1:2])              # second displaced

    # Factions: NYC + the displaced/traveled target regions.
    factions: List[Dict[str, Any]] = []
    seen_fids = set()
    for loc in locations:
        rep = REGION_FACTIONS.get(loc["region"])
        if rep and rep["id"] not in seen_fids:
            factions.append({
                "id": rep["id"],
                "name": rep["name"],
                "demand_data": FACTION_DEMANDS.get(rep["id"], {}),
            })
            seen_fids.add(rep["id"])

    # Threats: exclude archetypes already consumed by V1 unless recurrable.
    consumed = {t.get("archetype", "") for t in state.threats if t.get("archetype")}
    threat_ids: List[str] = []
    for aid in list_archetype_ids():
        if aid not in consumed:
            threat_ids.append(aid)
            continue
        arc = get_archetype(aid)
        if arc and arc.recurrable:
            threat_ids.append(aid)

    region_outcomes = ["stay_nyc", "displaced_to"]
    region_outcomes.append("traveled_to" if travel_enabled else "displaced_to")

    vows = [dict(v) for v in VOW_PACKAGES]

    return SeedPools(
        vignette_index=2,
        region=None,  # not yet locked; V2's pick locks it
        npc_archetypes=["faction_contact", "ally", "rival", "dependent", "informant"],
        factions=factions,
        locations=locations,
        threats=threat_ids,
        vow_packages=vows,
        region_outcomes=region_outcomes,
        notes=[
            "V2: region-lock vignette",
            f"traveled_to {'enabled' if travel_enabled else 'substituted with second displaced_to'}",
        ],
    )


_REGION_LOCATIONS: Dict[str, List[Dict[str, Any]]] = {
    "New York City": [
        {"id": "loc-manhattan-midtown", "name": "Manhattan midtown", "region": "New York City", "startable": True},
        {"id": "loc-brooklyn-tower-districts", "name": "Brooklyn tower districts", "region": "New York City", "startable": True},
    ],
    "Northern New Jersey": [
        {"id": "loc-port-newark-compound", "name": "Port Newark compound", "region": "Northern New Jersey", "startable": True},
    ],
    "Hudson Valley": [
        {"id": "loc-kingston-hv", "name": "Kingston, Hudson Valley", "region": "Hudson Valley", "startable": True},
    ],
    "Central New Jersey": [
        {"id": "loc-rutgers-campus", "name": "Rutgers campus, Central Jersey", "region": "Central New Jersey", "startable": True},
    ],
    "Philadelphia": [
        {"id": "loc-philadelphia-bourse-floor", "name": "Philadelphia Bourse floor", "region": "Philadelphia", "startable": True},
    ],
    "Lehigh Valley": [
        {"id": "loc-lehigh-allentown", "name": "Allentown, Lehigh Valley", "region": "Lehigh Valley", "startable": True},
    ],
    "Delmarva": [
        {"id": "loc-delmarva-granary", "name": "Delmarva granary", "region": "Delmarva", "startable": True},
    ],
}


def _filter_threats_by_consumption(
    state: CreationState,
) -> List[str]:
    """Return threat archetypes whose consumed-ness allows re-use.

    An archetype is eligible if (a) not yet in state.threats, OR (b)
    already in state.threats but its `recurrable` flag is True.
    """
    from emergence.engine.character_creation.threats import (
        get_archetype, list_archetype_ids,
    )
    consumed = {t.get("archetype", "") for t in state.threats if t.get("archetype")}
    out: List[str] = []
    for aid in list_archetype_ids():
        if aid not in consumed:
            out.append(aid)
            continue
        arc = get_archetype(aid)
        if arc and arc.recurrable:
            out.append(aid)
    return out


def _compute_v3(state: CreationState) -> SeedPools:
    """V3: winter Y1.  Region is now locked (from V2).

    Pools are filtered to the locked region.  Threats exclude anything
    consumed in V1/V2 unless `recurrable`.  At least one vow seed is
    surfaced (the first-pick-worthy package) since V3 is where the
    narrator plants the commitment that will ripen at V4.
    """
    from emergence.engine.character_creation.scenarios import (
        REGION_FACTIONS, FACTION_DEMANDS, VOW_PACKAGES,
    )

    region = state.region or "New York City"
    locations = list(_REGION_LOCATIONS.get(region, _V1_NYC_LOCATIONS))

    rep = REGION_FACTIONS.get(region)
    factions: List[Dict[str, Any]] = []
    if rep:
        factions.append({
            "id": rep["id"],
            "name": rep["name"],
            "demand_data": FACTION_DEMANDS.get(rep["id"], {}),
        })

    threat_ids = _filter_threats_by_consumption(state)

    vows = [dict(v) for v in VOW_PACKAGES]  # all packages eligible; narrator picks

    return SeedPools(
        vignette_index=3,
        region=region,
        npc_archetypes=["mentor", "ally", "rival", "dependent", "informant", "medic"],
        factions=factions,
        locations=locations,
        threats=threat_ids,
        vow_packages=vows,
        region_outcomes=None,
        notes=[
            f"V3: region locked to {region}",
            f"{len(threat_ids)} threat archetypes eligible after V1/V2 filter",
        ],
    )


def _compute_v4(state: CreationState) -> SeedPools:
    """V4: spring Y2.  Starting-location vignette.

    Must include at least one named antagonist and at least one startable
    location candidate.  Vow packages are presented so the narrator can
    surface the commitment planted in V3; at least 2 are required so the
    player's pick can bind ≥2 goals.
    """
    from emergence.engine.character_creation.scenarios import (
        REGION_FACTIONS, FACTION_DEMANDS, VOW_PACKAGES,
    )

    region = state.region or "New York City"

    # All locations in the region are startable candidates in V4.
    locations = list(_REGION_LOCATIONS.get(region, _V1_NYC_LOCATIONS))
    for loc in locations:
        loc["startable"] = True

    rep = REGION_FACTIONS.get(region)
    factions: List[Dict[str, Any]] = []
    if rep:
        factions.append({
            "id": rep["id"],
            "name": rep["name"],
            "demand_data": FACTION_DEMANDS.get(rep["id"], {}),
        })

    threat_ids = _filter_threats_by_consumption(state)

    # Named-antagonist archetypes: require at least one to be eligible so
    # the narrator can surface a named enemy.  Prefer recurrable +
    # human/social options over anomalous ones for ignition usability.
    named_antagonist_candidates = [
        aid for aid in ("named_rival_human", "faction_assassin_contract",
                        "knife_scavenger_survivor", "ruined_former_ally",
                        "iron_crown_notice")
        if aid in threat_ids
    ]
    if not named_antagonist_candidates:
        # fallback: force the default named_rival_human into the pool
        threat_ids.append("named_rival_human")
        named_antagonist_candidates = ["named_rival_human"]

    vows = [dict(v) for v in VOW_PACKAGES]

    return SeedPools(
        vignette_index=4,
        region=region,
        npc_archetypes=[
            "named_antagonist", "ally", "rival", "dependent",
            "mentor", "informant", "medic", "faction_contact",
        ],
        factions=factions,
        locations=locations,
        threats=threat_ids,
        vow_packages=vows,
        region_outcomes=None,
        notes=[
            f"V4: region {region}, starting-location lock",
            f"named antagonist candidates: {named_antagonist_candidates}",
            f"{len(locations)} startable location(s)",
            f"{len(vows)} vow packages (>=2 required for commit)",
        ],
    )
