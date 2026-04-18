"""Job bundle scene — narrator generates 5 cards from the picked location,
player picks 1.

Flow:
  1. Engine reads the picked post-emergence location from CreationState
  2. Engine loads that location's archetype pool from job_archetypes.json
  3. Engine builds a narrator_payload carrying the archetypes + character
  4. Narrator (Claude) returns a bundle_output JSON with 5 cards
  5. Engine validates the 5 cards against the bundle schema
  6. Player picks 1 card; engine applies it to CreationState
"""

from __future__ import annotations

import json
import os
import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.location_scene import get_location


JOB_ARCHETYPES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "job_archetypes.json",
)

BUNDLE_CARDS_REQUIRED = 5
VALID_NPC_ROLES = frozenset(["ally", "contact", "rival", "patron"])


class BundleValidationError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Bundle output invalid:\n  - " + "\n  - ".join(errors))


class JobBundleScene:
    scene_id: str = "job_bundle"
    register: str = "standard"

    def __init__(self) -> None:
        self._archetype_cache: Optional[Dict[str, List[Dict[str, Any]]]] = None

    # ------------------------------------------------------------------
    # Archetype loading
    # ------------------------------------------------------------------

    def _load_archetypes(self) -> Dict[str, List[Dict[str, Any]]]:
        if self._archetype_cache is not None:
            return self._archetype_cache
        with open(JOB_ARCHETYPES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._archetype_cache = data.get("locations", {})
        return self._archetype_cache

    def archetypes_for(self, location_id: str) -> List[Dict[str, Any]]:
        return list(self._load_archetypes().get(location_id, []))

    # ------------------------------------------------------------------
    # Phase 1: prepare payload for narrator
    # ------------------------------------------------------------------

    def build_narrator_payload(self, state: CreationState) -> Dict[str, Any]:
        location_id = state.scene_choices.get("post_emergence_location") or state.starting_location
        if not location_id:
            raise RuntimeError("post-emergence location not yet picked")
        location = get_location(location_id)
        archetypes = self.archetypes_for(location_id)

        # Compact character summary for the narrator prompt.
        char_summary = {
            "name": state.name,
            "age_at_onset": state.age_at_onset,
            "species": state.species,
            "pre_emergence_location": state.region,
            "self_description": state.self_description,
            "attributes": {
                name: 6 + state.attribute_deltas.get(name, 0)
                for name in ("strength", "agility", "perception", "will", "insight", "might")
            },
            "skills": dict(state.skills),
            "powers": [
                {
                    "power_id": p.get("power_id"),
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "sub_category": p.get("sub_category"),
                }
                for p in state.powers
            ],
            "npcs": list(state.generated_npcs),
        }

        return {
            "task": "job_bundle_generate_v1",
            "guidelines_doc": "emergence/docs/job_bundle_guidelines.md",
            "post_emergence_location": location,
            "archetype_pool": archetypes,
            "character": char_summary,
            "cards_required": BUNDLE_CARDS_REQUIRED,
            "schema_hint": {
                "cards": [
                    {
                        "job_id": "str",
                        "title": "str",
                        "daily_loop": "str",
                        "skill_tilts": {"<skill>": "int 0-2"},
                        "factions": {
                            "positive": [{"faction_id": "str", "standing": "int", "role": "str"}],
                            "negative": [{"faction_id": "str", "standing": "int", "reason": "str"}]
                        },
                        "npcs": [{
                            "npc_id": "str", "name": "str", "role": "ally|contact|rival|patron",
                            "relation": "str",
                            "bond": {"trust": "int -3..3", "loyalty": "int -3..3", "tension": "int 0..3"},
                            "hook": "str"
                        }],
                        "threats": [{"archetype": "str", "hook": "str"}],
                        "starting_location": "str",
                        "opening_vignette_seed": "str"
                    }
                ]
            },
        }

    # ------------------------------------------------------------------
    # Phase 2: validate bundle output
    # ------------------------------------------------------------------

    @staticmethod
    def validate_bundle_output(payload: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        if not isinstance(payload, dict):
            return ["root: must be dict"]
        cards = payload.get("cards")
        if not isinstance(cards, list):
            return ["cards: required list"]
        if len(cards) != BUNDLE_CARDS_REQUIRED:
            errors.append(f"cards: must contain exactly {BUNDLE_CARDS_REQUIRED} cards (got {len(cards)})")
        seen_ids: set = set()
        for i, card in enumerate(cards):
            prefix = f"cards[{i}]"
            if not isinstance(card, dict):
                errors.append(f"{prefix}: must be dict")
                continue
            jid = card.get("job_id")
            if not jid:
                errors.append(f"{prefix}.job_id: required")
            elif jid in seen_ids:
                errors.append(f"{prefix}.job_id: duplicate {jid!r}")
            else:
                seen_ids.add(jid)
            for key in ("title", "daily_loop", "starting_location", "opening_vignette_seed"):
                if not card.get(key):
                    errors.append(f"{prefix}.{key}: required")
            if not isinstance(card.get("skill_tilts"), dict):
                errors.append(f"{prefix}.skill_tilts: required dict")
            factions = card.get("factions")
            if not isinstance(factions, dict):
                errors.append(f"{prefix}.factions: required dict")
            else:
                if not isinstance(factions.get("positive"), list) or not factions["positive"]:
                    errors.append(f"{prefix}.factions.positive: required non-empty list")
                if not isinstance(factions.get("negative"), list):
                    errors.append(f"{prefix}.factions.negative: required list")
            npcs = card.get("npcs")
            if not isinstance(npcs, list) or len(npcs) < 3:
                errors.append(f"{prefix}.npcs: required list of 3+ entries")
            else:
                for j, npc in enumerate(npcs):
                    nprefix = f"{prefix}.npcs[{j}]"
                    if not isinstance(npc, dict):
                        errors.append(f"{nprefix}: must be dict")
                        continue
                    if not npc.get("name"):
                        errors.append(f"{nprefix}.name: required")
                    if npc.get("role") not in VALID_NPC_ROLES:
                        errors.append(f"{nprefix}.role: must be one of {sorted(VALID_NPC_ROLES)}")
            threats = card.get("threats")
            if not isinstance(threats, list) or not threats:
                errors.append(f"{prefix}.threats: required non-empty list")
        return errors

    # ------------------------------------------------------------------
    # Phase 3: accept + pick
    # ------------------------------------------------------------------

    def store_bundle_output(
        self,
        bundle_output: Dict[str, Any],
        state: CreationState,
    ) -> CreationState:
        errors = self.validate_bundle_output(bundle_output)
        if errors:
            raise BundleValidationError(errors)
        state.scene_choices["job_bundle_cards"] = list(bundle_output.get("cards", []))
        return state

    def apply_pick(
        self,
        pick_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        cards = state.scene_choices.get("job_bundle_cards") or []
        if not cards:
            raise RuntimeError("no bundle cards stored; call store_bundle_output first")
        if pick_index < 0 or pick_index >= len(cards):
            raise ValueError("pick index out of range")
        card = cards[pick_index]

        # Apply card deltas via the factory.
        factions_pos = card.get("factions", {}).get("positive", [])
        factions_neg = card.get("factions", {}).get("negative", [])
        faction_standing = {}
        for f in factions_pos:
            faction_standing[f["faction_id"]] = faction_standing.get(f["faction_id"], 0) + int(f.get("standing", 1))
        for f in factions_neg:
            faction_standing[f["faction_id"]] = faction_standing.get(f["faction_id"], 0) + int(f.get("standing", -1))

        generated_npcs: List[Dict[str, Any]] = []
        for npc in card.get("npcs", []):
            npc_id = npc.get("npc_id") or _stable_npc_id(npc.get("name", ""), npc.get("role", "ally"))
            bond = npc.get("bond", {}) or {}
            generated_npcs.append({
                "npc_id": npc_id,
                "display_name": npc.get("name", ""),
                "scene_id": "job_bundle",
                "role": npc.get("role", "ally"),
                "standing": int(bond.get("loyalty", 0)),
                "trust": max(0, int(bond.get("trust", 0))),
                "relation": npc.get("relation", ""),
                "hooks": [npc.get("hook", "")] if npc.get("hook") else [],
            })

        threats = []
        for i, t in enumerate(card.get("threats", [])):
            arch = t.get("archetype", "named_rival_human")
            name = t.get("name") or arch.replace("_", " ").title()
            threats.append({
                "npc_id": t.get("npc_id") or f"threat_{card.get('job_id','')}_{arch}_{i}",
                "archetype": arch,
                "name": name,
                "standing": -2,
                "source": f"job_bundle:{card.get('job_id','')}",
                "summary": t.get("hook", ""),
            })

        scene_result = {
            "skills": dict(card.get("skill_tilts") or {}),
            "faction_standing": faction_standing,
            "generated_npcs": generated_npcs,
            "threats": threats,
            "starting_location": card.get("starting_location", state.starting_location),
            "narrative_tag": f"job:{card.get('job_id','')}",
        }
        state = factory.apply_scene_result(self.scene_id, scene_result, state, rng)
        state.starting_location = card.get("starting_location", state.starting_location)
        state.scene_choices["job_pick"] = card
        return state

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def phase(self, state: CreationState) -> str:
        if not state.scene_choices.get("job_bundle_cards"):
            return "awaiting_narrator"
        if not state.scene_choices.get("job_pick"):
            return "awaiting_player_pick"
        return "complete"


def _stable_npc_id(name: str, role: str) -> str:
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_") or "unnamed"
    return f"npc_job_{role}_{base}"
