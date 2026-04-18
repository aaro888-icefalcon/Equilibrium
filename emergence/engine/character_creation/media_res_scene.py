"""MediaResScene — scene 5 of v4, handoff to combat.

Filled in Phase 4.  This stub allows scenes_v4 to assemble without
importing a missing symbol; prepare returns without side effects and
get_scenario_code returns a placeholder.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)


class MediaResScene:
    """Combat-handoff scene.  Reads finalized CharacterSheet + world state,
    builds an EncounterSpec, emits opening prose + spec for EncounterRunner.
    Fully wired in Phase 4.1.
    """

    scene_id = "sz_v4_media_res"
    register = "action"

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        return None

    def get_framing(self, state: CreationState) -> str:
        return "Media res — combat handoff (Phase 4 stub)."

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        return {
            "scene_intent": "Hand off to combat with an EncounterSpec.",
            "stub": True,
            "note": "Phase 4.1 fills this in.",
            "starting_location": state.starting_location,
            "threats_ranked_by_pressure": sorted(
                state.threats,
                key=lambda t: -int(t.get("pressure") or 0),
            ),
        }

    def get_choices(self, state: CreationState) -> List[str]:
        return []

    def needs_text_input(self) -> bool:
        return False

    def apply(self, choice_index, state, factory, rng):
        return state

    def is_complete(self, state: CreationState) -> bool:
        return True
