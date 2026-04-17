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
