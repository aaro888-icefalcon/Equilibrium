"""YearOneVignetteScene — scenes 1-4 of the v4 arc (vignettes V1-V4).

Each instance binds one mechanical slot:
  V1 -> primary_cast
  V2 -> primary_rider + region lock
  V3 -> secondary_cast
  V4 -> secondary_rider + starting location lock

The scene is narrator-driven.  prepare() builds a VignetteScaffold from
state; get_scenario_code() serializes it plus the rendered prompt; the
CLI's --output-json arg feeds the narrator's response into
apply_vignette_output(), which validates against the scaffold and
applies the picked VignetteChoice via apply_vignette_choice.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.scaffolds import (
    VignetteScaffold, build_scaffold,
)
from emergence.engine.character_creation.vignette_prompts import render_prompt
from emergence.engine.character_creation.vignette_contract import (
    VignetteOutput, validate_vignette_output, apply_vignette_choice,
)


class YearOneVignetteScene:
    """Wraps one of the four Year One vignettes."""

    register = "standard"

    def __init__(self, vignette_index: int) -> None:
        if vignette_index not in (1, 2, 3, 4):
            raise ValueError(f"vignette_index must be 1..4, got {vignette_index}")
        self.vignette_index = vignette_index
        self.scene_id = f"sz_v4_vignette_{vignette_index}"
        self._scaffold: VignetteScaffold | None = None
        self._prompt: str = ""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._scaffold = build_scaffold(state, self.vignette_index, rng)
        self._prompt = render_prompt(self._scaffold, reaction_tags=list(state.reaction_tags))

    def get_framing(self, state: CreationState) -> str:
        # The narrator produces prose; we expose a short orientation so
        # CLI consumers have something to display before the VignetteOutput
        # is authored.
        if not self._scaffold:
            return ""
        return (
            f"Vignette {self._scaffold.index} — "
            f"{self._scaffold.time_period}.  Register: "
            f"{self._scaffold.stakes_register}.  Narrator: author a "
            f"VignetteOutput JSON per the prompt."
        )

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        if not self._scaffold:
            return {}
        sc = self._scaffold
        return {
            "scene_intent": (
                f"Year One vignette {sc.index}: bind {sc.mechanical_slot} "
                f"and seed NPCs/location/threat/vow."
            ),
            "beat_target_words": [400, 600],
            "vignette_index": sc.index,
            "mechanical_slot": sc.mechanical_slot,
            "power_id": sc.power_id,
            "option_pool": [
                {"option_id": o.option_id, "display": o.display,
                 "base_description": o.base_description}
                for o in sc.option_pool
            ],
            "time_period": sc.time_period,
            "region": sc.region,
            "stakes_register": sc.stakes_register,
            "seed_pools": {
                "npc_archetypes": sc.seed_pools.npc_archetypes,
                "factions": sc.seed_pools.factions,
                "locations": sc.seed_pools.locations,
                "threats": sc.seed_pools.threats,
                "vow_packages": sc.seed_pools.vow_packages,
                "region_outcomes": sc.seed_pools.region_outcomes,
            },
            "required_seeds": {
                "min_npcs": sc.required_seeds.min_npcs,
                "min_locations": sc.required_seeds.min_locations,
                "min_factions": sc.required_seeds.min_factions,
                "min_threats": sc.required_seeds.min_threats,
                "min_vows": sc.required_seeds.min_vows,
                "require_region_outcome": sc.required_seeds.require_region_outcome,
                "require_is_starting": sc.required_seeds.require_is_starting,
                "min_goals_from_vows": sc.required_seeds.min_goals_from_vows,
            },
            "prior_vignette_summaries": sc.prior_vignette_summaries,
            "forbidden": sc.forbidden,
            "narrator_prompt": self._prompt,
            "invitation": (
                "Narrator: author one VignetteOutput JSON with 3 choices.  "
                "The CLI consumes it via --output-json."
            ),
        }

    def get_choices(self, state: CreationState) -> List[str]:
        # Scenes without a VignetteOutput expose the option_ids as
        # placeholder choices so the step-scene-apply CLI can show the
        # player what the narrator's shape will be.
        if not self._scaffold:
            return []
        return [o.option_id for o in self._scaffold.option_pool]

    # ------------------------------------------------------------------
    # Apply — the narrator's output drives state.
    # ------------------------------------------------------------------

    def apply_vignette_output(
        self,
        raw_json: str,
        pick_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> Dict[str, Any]:
        """Parse + validate + apply.  Returns a structured result dict."""
        if not self._scaffold:
            return {"status": "error", "message": "scaffold not prepared"}

        try:
            output = VignetteOutput.from_json(raw_json)
        except ValueError as e:
            return {"status": "error",
                    "message": f"VignetteOutput parse failed: {e}"}

        violations = validate_vignette_output(output, self._scaffold, state)
        if violations:
            return {"status": "error",
                    "message": "VignetteOutput failed validation",
                    "violations": violations}

        pick_idx = min(max(0, pick_index), len(output.choices) - 1)
        chosen = output.choices[pick_idx]

        # V2: if region_outcome is set, apply region lock here.
        if chosen.seed_bundle.region_outcome:
            region = _resolve_region_from_outcome(
                chosen.seed_bundle.region_outcome,
                chosen.seed_bundle.locations,
            )
            if region:
                state.region = region

        state = apply_vignette_choice(chosen, self.scene_id, state, factory, rng)

        return {
            "status": "ok",
            "state": state,
            "picked_choice": pick_idx,
            "picked_option_id": chosen.mechanical_binding.option_id,
        }

    def apply(self, choice_index, state, factory, rng):
        # Dead path — vignette scenes require --output-json.  Returns
        # state unchanged so callers don't crash.
        return state

    def is_complete(self, state: CreationState) -> bool:
        # Scene advances when the slot was bound (mechanical_binding
        # written via bundle_to_choice_data).  We detect via the history
        # entry with type=character_creation_vignette.
        for h in reversed(state.history):
            if (h.get("type") == "character_creation_vignette"
                    and self.scene_id in (h.get("description") or "") or True):
                # Simplified: the pending_ack flag set after apply is the
                # signal.  Clear means the scene is fully resolved.
                pass
        return state.pending_ack or False


def _resolve_region_from_outcome(
    outcome: str,
    locations: List[Any],
) -> str:
    """Given a V2 region_outcome and the picked choice's locations,
    resolve the new locked region.
    """
    if outcome == "stay_nyc":
        return "New York City"
    # For displaced_to / traveled_to, pull region from first location entry.
    for loc in locations:
        spec = getattr(loc, "spec", None)
        lid = getattr(loc, "id", None)
        if spec and spec.get("region"):
            return spec["region"]
        if lid:
            from emergence.engine.character_creation.seed_pools import _REGION_LOCATIONS
            for region, locs in _REGION_LOCATIONS.items():
                if any(l.get("id") == lid for l in locs):
                    return region
    return ""
