"""MediaResScene — scene 5 of v4, handoff to combat.

Reads finalized state (or CreationState as a fallback) and builds an
EncounterSpec directly.  The EncounterSpec is emitted as part of the
scenario_code so the CLI can hand it to step combat-start.

Threat selection: highest-pressure threat archetype with a known
encounter_template wins.  Fallback: synthesize a human-register
scavenger encounter at state.starting_location.
"""

from __future__ import annotations

import random as _random
import uuid
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.threats import get_archetype
from emergence.engine.schemas.encounter import (
    EncounterSpec, TerrainZone, WinLossCondition, WorldContext,
)


# Map threat archetype encounter_template values to combat register.
_TEMPLATE_REGISTER: Dict[str, str] = {
    "human_scavenger_raider": "human",
    "iron_crown_squad": "human",
    "assassin_strike_team": "human",
    "rival_duel_human": "human",
    "debt_collection": "human",
    "former_ally_strike": "human",
    "family_situation_social": "human",
    "warped_predator": "creature",
    "infected_host": "creature",
    "eldritch_fragment": "eldritch",
}


_TEMPLATE_ENEMY: Dict[str, Dict[str, Any]] = {
    "human_scavenger_raider": {"template_id": "scavenger", "tier": 1, "ai_profile": "defensive"},
    "iron_crown_squad": {"template_id": "militia_soldier", "tier": 2, "ai_profile": "methodical"},
    "assassin_strike_team": {"template_id": "bounty_hunter", "tier": 4, "ai_profile": "predatory"},
    "rival_duel_human": {"template_id": "raider_enforcer", "tier": 3, "ai_profile": "aggressive"},
    "debt_collection": {"template_id": "raider_scout", "tier": 2, "ai_profile": "aggressive"},
    "former_ally_strike": {"template_id": "raider_enforcer", "tier": 3, "ai_profile": "aggressive"},
    "family_situation_social": {"template_id": "raider_scout", "tier": 2, "ai_profile": "aggressive"},
    "warped_predator": {"template_id": "mutant_stalker", "tier": 3, "ai_profile": "ambush"},
    "infected_host": {"template_id": "feral_hound", "tier": 1, "ai_profile": "pack_tactics"},
    "eldritch_fragment": {"template_id": "void_touched", "tier": 3, "ai_profile": "chaotic"},
}


_DEFAULT_TERRAIN: List[Dict[str, Any]] = [
    {"id": "approach", "name": "the approach", "properties": ["exposed"],
     "description": "Open ground, no cover."},
    {"id": "cover", "name": "scattered cover", "properties": ["cover"],
     "description": "Vehicles, debris, low walls."},
    {"id": "objective", "name": "contested point", "properties": ["objective"],
     "description": "The thing worth fighting over."},
]


class MediaResScene:
    """Combat-handoff scene.  No picks, no text input."""

    scene_id = "sz_v4_media_res"
    register = "action"

    def __init__(self) -> None:
        self._encounter_spec: Optional[EncounterSpec] = None
        self._triggering_threat: Optional[Dict[str, Any]] = None
        self._fallback_used: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._triggering_threat = self._select_threat(state)
        self._fallback_used = self._triggering_threat is None
        self._encounter_spec = self._build_encounter_spec(state, rng)

    def get_framing(self, state: CreationState) -> str:
        if self._triggering_threat:
            who = self._triggering_threat.get("name", "they")
            return (
                f"Spring of year two.  {who} comes for you at "
                f"{state.starting_location or 'your door'}.  The "
                f"conversation ends.  Something else begins."
            )
        return (
            f"Spring of year two.  Strangers at "
            f"{state.starting_location or 'your door'}, uninvited, "
            f"armed, unhurried."
        )

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        threat = self._triggering_threat or {}
        secondaries = self._secondary_threats(state, exclude=threat.get("name"))
        return {
            "scene_intent": (
                "Media res: ignition combat.  EncounterSpec is built "
                "from the highest-pressure threat (or a scavenger "
                "ambush fallback) and handed to step combat-start."
            ),
            "stakes_register": "action",
            "beat_target_words": [200, 400],
            "triggering_threat": threat,
            "secondary_threats": secondaries,
            "starting_location": state.starting_location,
            "fallback_used": self._fallback_used,
            "encounter_spec": self._encounter_spec.to_dict() if self._encounter_spec else None,
            "invitation": (
                "Narrator opens combat in media res: 200-400 words of "
                "action-register prose pulling in the triggering threat, "
                "the starting location, and 1-2 secondary threats as "
                "world context.  Then hand off to step combat-start."
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

    # ------------------------------------------------------------------
    # Threat selection
    # ------------------------------------------------------------------

    def _select_threat(self, state: CreationState) -> Optional[Dict[str, Any]]:
        """Pick the highest-pressure threat with a known encounter_template."""
        candidates = []
        for t in state.threats:
            aid = t.get("archetype", "")
            arc = get_archetype(aid) if aid else None
            if arc and arc.encounter_template in _TEMPLATE_REGISTER:
                candidates.append((int(t.get("pressure") or 0), t))
        if not candidates:
            return None
        candidates.sort(key=lambda pair: -pair[0])
        return candidates[0][1]

    def _secondary_threats(
        self,
        state: CreationState,
        exclude: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        out = []
        for t in state.threats:
            if exclude and t.get("name") == exclude:
                continue
            out.append({"name": t.get("name", ""),
                        "pressure": t.get("pressure", 0),
                        "archetype": t.get("archetype", "")})
            if len(out) >= 2:
                break
        return out

    # ------------------------------------------------------------------
    # EncounterSpec builder
    # ------------------------------------------------------------------

    def _build_encounter_spec(
        self,
        state: CreationState,
        rng: _random.Random,
    ) -> EncounterSpec:
        threat = self._triggering_threat
        if threat and threat.get("archetype"):
            aid = threat["archetype"]
            arc = get_archetype(aid)
            tmpl = arc.encounter_template if arc else ""
            register = _TEMPLATE_REGISTER.get(tmpl, "human")
            enemy = dict(_TEMPLATE_ENEMY.get(tmpl,
                                              {"template_id": "scavenger", "tier": 1,
                                               "ai_profile": "defensive"}))
        else:
            # Fallback scavenger ambush.
            register = "human"
            enemy = {"template_id": "scavenger", "tier": 1, "ai_profile": "defensive"}

        enemy["instance_id"] = f"enemy_{uuid.uuid4().hex[:8]}"

        player_dict = {
            "name": state.name,
            "tier": state.tier,
            "powers": list(state.powers),
            "skills": dict(state.skills),
            "starting_location": state.starting_location,
        }

        terrain = [TerrainZone(**z) for z in _DEFAULT_TERRAIN]

        win = [WinLossCondition(type="defeat_all", parameters={})]
        loss = [WinLossCondition(type="player_down", parameters={})]
        escape = [WinLossCondition(type="break_contact",
                                    parameters={"distance": "out_of_sight"})]

        world_ctx = WorldContext(
            recent_events=[h.get("description", "") for h in state.history[-3:]],
            heat_levels={f: int(v) for f, v in state.heat_deltas.items()},
            clock_states={},
        )

        opening = (
            f"{(threat or {}).get('name', 'A stranger')} steps into view.  "
            f"{state.starting_location or 'The ground you hold'} "
            f"becomes the place this has to be settled.  No speech now; "
            f"just the shape of it."
        )

        return EncounterSpec(
            id=str(uuid.uuid4()),
            location=state.starting_location or "loc-manhattan-midtown",
            player=player_dict,
            enemies=[enemy],
            terrain_zones=terrain,
            stakes="Survival.  " + (threat.get("summary", "") if threat else ""),
            win_conditions=win,
            loss_conditions=loss,
            escape_conditions=escape,
            parley_available=(register == "human"),
            world_context=world_ctx,
            combat_register=register,
            opening_situation=opening,
        )
