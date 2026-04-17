"""Vignette scaffolds — the engine's request to the narrator.

A VignetteScaffold is built by YearOneVignetteScene.prepare() from the
CreationState and the vignette_index.  It carries every constraint the
narrator needs to produce a valid VignetteOutput:

  - the mechanical slot being bound,
  - the option_pool the narrator may pick from,
  - seed pools scoped to this vignette (from seed_pools.compute_seed_pools),
  - required minimums per seed type (per-choice, not per-vignette),
  - a summary of prior vignettes, so the narrator maintains continuity.

Scaffolds are read-only data; they never mutate state.
"""

from __future__ import annotations

import dataclasses
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.seed_pools import SeedPools


@dataclasses.dataclass
class SeedRequirement:
    """Per-choice minimums the narrator must meet for each seed type."""
    min_npcs: int = 0
    min_locations: int = 0
    min_factions: int = 0
    min_threats: int = 0
    min_vows: int = 0
    require_region_outcome: bool = False    # V2 only
    require_is_starting: bool = False       # V4 only
    min_goals_from_vows: int = 0            # V4 only (≥2)


@dataclasses.dataclass
class Option:
    """One cast_mode or rider slot option, as pulled from the power."""
    option_id: str
    display: str
    base_description: str       # the default description from the power def


@dataclasses.dataclass
class VignetteScaffold:
    """Everything the narrator needs to produce a VignetteOutput."""
    index: int                              # 1..4
    mechanical_slot: str                    # "primary_cast" | "primary_rider" | ...
    power_id: str                           # which of the player's two powers
    option_pool: List[Option]               # 3 options the narrator picks from
    time_period: str                        # "weeks after" | "autumn Y1" | ...
    region: Optional[str]                   # None before V2 locks it
    stakes_register: str                    # narrator register directive
    seed_pools: SeedPools
    required_seeds: SeedRequirement
    prior_vignette_summaries: List[str] = dataclasses.field(default_factory=list)
    forbidden: List[str] = dataclasses.field(default_factory=list)

    def option_ids(self) -> List[str]:
        return [o.option_id for o in self.option_pool]


_SLOT_TO_POWER_INDEX: Dict[str, int] = {
    "primary_cast": 0, "primary_rider": 0,
    "secondary_cast": 1, "secondary_rider": 1,
}


def _load_power_by_id(power_id: str) -> Optional[Dict[str, Any]]:
    """Scan the 6 powers_v2 JSON files and return the power dict for *power_id*."""
    import json
    import os
    base = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "powers_v2",
    ))
    if not os.path.isdir(base):
        return None
    for fname in sorted(os.listdir(base)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(base, fname), "r", encoding="utf-8") as f:
            powers = json.load(f)
        for p in powers:
            if p.get("id") == power_id:
                return p
    return None


def _pick_options(slots: List[Dict[str, Any]], rng, k: int = 3) -> List[Option]:
    """Pull *k* options from a power's cast_modes or rider_slots array."""
    chosen = list(slots[:k]) if len(slots) <= k else rng.sample(slots, k)
    return [
        Option(
            option_id=s.get("slot_id", ""),
            display=s.get("rider_type") or s.get("slot_id", ""),
            base_description=s.get("effect_description", ""),
        )
        for s in chosen
    ]


def _prior_summaries(state) -> List[str]:
    """Rebuild prior vignette summaries from state.history entries."""
    out: List[str] = []
    for entry in state.history:
        if entry.get("type") == "character_creation_vignette":
            desc = entry.get("description", "")
            if desc:
                out.append(desc)
    return out


def build_scaffold(state, vignette_index: int, rng) -> VignetteScaffold:
    """Build the scaffold for YearOneVignetteScene(vignette_index).

    Reads state.powers[0] or state.powers[1] based on the vignette's slot,
    loads the power's cast_modes / rider_slots from data/powers_v2/, picks
    3 options, fills seed pools via compute_seed_pools, and assembles the
    scaffold with the index's per-default metadata.
    """
    from emergence.engine.character_creation.seed_pools import compute_seed_pools

    if vignette_index not in PER_INDEX_DEFAULTS:
        raise ValueError(f"unknown vignette_index {vignette_index}")
    defaults = PER_INDEX_DEFAULTS[vignette_index]
    slot = defaults["mechanical_slot"]
    power_idx = _SLOT_TO_POWER_INDEX[slot]

    power_entry = state.powers[power_idx] if power_idx < len(state.powers) else {}
    power_id = power_entry.get("power_id") or power_entry.get("id") or ""
    power_data = _load_power_by_id(power_id) if power_id else None

    if power_data:
        source_slots = (
            power_data.get("cast_modes", []) if slot.endswith("_cast")
            else power_data.get("rider_slots", [])
        )
        option_pool = _pick_options(source_slots, rng, k=3)
    else:
        option_pool = []

    pools = compute_seed_pools(state, vignette_index)

    return VignetteScaffold(
        index=vignette_index,
        mechanical_slot=slot,
        power_id=power_id,
        option_pool=option_pool,
        time_period=defaults["time_period"],
        region=pools.region,
        stakes_register=defaults["stakes_register"],
        seed_pools=pools,
        required_seeds=defaults["required_seeds"],
        prior_vignette_summaries=_prior_summaries(state),
        forbidden=[
            "hit points", "experience points", "level up",
            "dice roll", "d20", "saving throw",
        ],
    )


# Per-index defaults used by the builder.
PER_INDEX_DEFAULTS: Dict[int, Dict[str, Any]] = {
    1: {
        "mechanical_slot": "primary_cast",
        "time_period": "weeks after the Onset",
        "stakes_register": "first use under threat",
        "required_seeds": SeedRequirement(min_npcs=1, min_locations=1, min_threats=1),
    },
    2: {
        "mechanical_slot": "primary_rider",
        "time_period": "autumn of Year One",
        "stakes_register": "departure or stay",
        "required_seeds": SeedRequirement(
            min_npcs=1, min_factions=1, min_threats=1,
            require_region_outcome=True,
        ),
    },
    3: {
        "mechanical_slot": "secondary_cast",
        "time_period": "winter of Year One",
        "stakes_register": "quiet discovery",
        "required_seeds": SeedRequirement(min_npcs=1, min_vows=1, min_threats=1),
    },
    4: {
        "mechanical_slot": "secondary_rider",
        "time_period": "spring of Year Two",
        "stakes_register": "commitment and ignition",
        "required_seeds": SeedRequirement(
            min_npcs=1, min_locations=1,
            require_is_starting=True,
            min_goals_from_vows=2,
        ),
    },
}
