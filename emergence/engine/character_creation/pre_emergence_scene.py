"""Pre-emergence scene — text elicitation + classifier apply.

Flow:
  1. Player supplies: name, age, species, profession, personality, npcs, location
  2. Engine bundles the text into a narrator_payload (for Claude)
  3. Narrator (Claude) reads the bundle and returns a classifier JSON payload
  4. Engine validates the JSON against classifier_contract and applies to state

Three-state scene:
  - "awaiting_text":  needs the player's text inputs
  - "awaiting_narrator": text captured; waiting for Claude's classifier output
  - "complete":       classifier applied; ready to advance
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.classifier_contract import (
    ClassifierValidationError,
    to_scene_result,
    validate_classifier_output,
)


# Mid-Atlantic pre-Onset locations. These are original cities/districts the
# PC plausibly lived in before the Onset. Post-Onset settlement is picked
# separately in location_scene.py.
PRE_EMERGENCE_LOCATIONS: List[Dict[str, str]] = [
    {"id": "pre_manhattan", "display_name": "Manhattan (NYC)"},
    {"id": "pre_brooklyn", "display_name": "Brooklyn (NYC)"},
    {"id": "pre_queens", "display_name": "Queens (NYC)"},
    {"id": "pre_bronx", "display_name": "The Bronx (NYC)"},
    {"id": "pre_staten_island", "display_name": "Staten Island (NYC)"},
    {"id": "pre_jersey_city", "display_name": "Jersey City (NJ)"},
    {"id": "pre_newark", "display_name": "Newark (NJ)"},
    {"id": "pre_princeton", "display_name": "Princeton (NJ)"},
    {"id": "pre_new_brunswick", "display_name": "New Brunswick (NJ)"},
    {"id": "pre_philadelphia", "display_name": "Philadelphia (PA)"},
    {"id": "pre_allentown", "display_name": "Allentown / Lehigh Valley (PA)"},
    {"id": "pre_pittsburgh_area", "display_name": "Western PA"},
    {"id": "pre_baltimore", "display_name": "Baltimore (MD)"},
    {"id": "pre_annapolis", "display_name": "Annapolis (MD)"},
    {"id": "pre_dc", "display_name": "Washington, DC"},
    {"id": "pre_arlington", "display_name": "Arlington / Northern Virginia"},
    {"id": "pre_wilmington", "display_name": "Wilmington (DE)"},
    {"id": "pre_delmarva", "display_name": "Delmarva Peninsula"},
]

PRE_EMERGENCE_LOCATION_IDS = frozenset(loc["id"] for loc in PRE_EMERGENCE_LOCATIONS)

VALID_SPECIES = frozenset([
    "baseline", "a_hollow_boned", "b_deep_voiced", "c_silver_hand",
    "d_pale_eyed", "e_slow_breath", "f_iron_lung", "g_stone_footed",
    "h_glass_skinned", "i_ember_marked",
])


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


class PreEmergenceScene:
    """Elicits pre-Onset biography text + receives classifier JSON.

    Two-phase apply:
      - apply_text() captures the raw text inputs
      - apply_classifier() validates and applies the narrator's classifier JSON
    """

    scene_id: str = "pre_emergence"
    register: str = "intimate"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Before the Onset. Before the engines stopped on Seventh Avenue, "
            "before the helicopter came in wrong, before you knew what the pressure "
            "under your sternum would mean. Tell us who you were."
        )

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        return [
            {"key": "name", "prompt": "Your name."},
            {"key": "age", "prompt": "Your age on the day of the Onset (16-65)."},
            {"key": "species", "prompt": (
                "Species. 'baseline' for an ordinary human, or one of: "
                "a_hollow_boned, b_deep_voiced, c_silver_hand, d_pale_eyed, "
                "e_slow_breath, f_iron_lung, g_stone_footed, h_glass_skinned, "
                "i_ember_marked."
            )},
            {"key": "profession", "prompt": (
                "Your profession and what it looked like day-to-day. "
                "Describe the work as if someone who'd never done it needed to understand it."
            )},
            {"key": "personality", "prompt": (
                "Your temperament, interests, habits. How do you decide things? "
                "Where do you drop the ball? What do you care about?"
            )},
            {"key": "npcs", "prompt": (
                "The people in your life. Family, friends, coworkers. Names where you have them. "
                "Describe each briefly — who they are, how close, any tension."
            )},
            {"key": "pre_emergence_location", "prompt": (
                "Where you lived before the Onset. Pick one id from: "
                + ", ".join(loc["id"] for loc in PRE_EMERGENCE_LOCATIONS)
            )},
        ]

    # ------------------------------------------------------------------
    # Phase 1: text capture
    # ------------------------------------------------------------------

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Capture raw text inputs. Validation of classifier output is separate."""
        name = (text_inputs.get("name") or "").strip()
        if not name:
            raise ValueError("name is required")

        try:
            age = int(text_inputs.get("age", "25"))
        except ValueError:
            raise ValueError("age must be an integer")
        age = max(16, min(65, age))

        species = (text_inputs.get("species") or "baseline").strip().lower()
        if species not in VALID_SPECIES:
            species = "baseline"

        location = (text_inputs.get("pre_emergence_location") or "").strip().lower()
        if location not in PRE_EMERGENCE_LOCATION_IDS:
            raise ValueError(
                f"pre_emergence_location must be one of: "
                f"{', '.join(sorted(PRE_EMERGENCE_LOCATION_IDS))}"
            )

        profession = (text_inputs.get("profession") or "").strip()
        personality = (text_inputs.get("personality") or "").strip()
        npcs_text = (text_inputs.get("npcs") or "").strip()

        # Pack into self_description for the classifier payload.
        self_description = _pack_self_description(profession, personality, npcs_text)

        # Hold raw text in scene_choices so the narrator payload can draw it
        # without re-prompting, then advance to the classifier phase.
        state.scene_choices["pre_emergence_raw"] = {
            "name": name,
            "age": age,
            "species": species,
            "profession": profession,
            "personality": personality,
            "npcs_text": npcs_text,
            "pre_emergence_location": location,
        }
        state.name = name
        state.age_at_onset = age
        state.species = species
        state.self_description = self_description
        state.region = location

        return state

    # ------------------------------------------------------------------
    # Phase 2: narrator classifier payload in, apply
    # ------------------------------------------------------------------

    def build_narrator_payload(self, state: CreationState) -> Dict[str, Any]:
        """Return the payload the narrator uses to compose the classifier JSON."""
        raw = state.scene_choices.get("pre_emergence_raw", {})
        return {
            "classifier_task": "pre_emergence_v1",
            "guidelines_doc": "emergence/docs/classifier_guidelines.md",
            "name": raw.get("name", ""),
            "age": raw.get("age", 25),
            "species": raw.get("species", "baseline"),
            "profession": raw.get("profession", ""),
            "personality": raw.get("personality", ""),
            "npcs_text": raw.get("npcs_text", ""),
            "pre_emergence_location": raw.get("pre_emergence_location", ""),
            "schema_hint": {
                "attributes": {"<name>": "int in {4,6,8,10}", "rationale": "str"},
                "skills": {"<canonical_skill>": "int 0-6", "rationale": "str"},
                "npcs": [{
                    "name": "str", "relation": "str", "role": "str",
                    "bond": {"trust": "int -3..3", "loyalty": "int -3..3", "tension": "int 0..3"},
                    "distance": "str", "notes": "str",
                }],
                "history_seeds": "list (optional)",
                "inventory_seeds": "list (optional)",
            },
        }

    def apply_classifier(
        self,
        classifier_output: Dict[str, Any],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Validate and apply the narrator's classifier JSON to state."""
        errors = validate_classifier_output(classifier_output)
        if errors:
            raise ClassifierValidationError(errors)

        raw = state.scene_choices.get("pre_emergence_raw", {})
        scene_result = to_scene_result(
            classifier_output,
            name=state.name,
            age_at_onset=state.age_at_onset,
            species=state.species,
            self_description=state.self_description,
            pre_emergence_location=raw.get("pre_emergence_location", ""),
        )

        state = factory.apply_scene_result(self.scene_id, scene_result, state, rng)
        state.scene_choices["pre_emergence_classifier"] = dict(classifier_output)
        return state

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def phase(self, state: CreationState) -> str:
        """Return 'awaiting_text' | 'awaiting_narrator' | 'complete'."""
        if "pre_emergence_raw" not in state.scene_choices:
            return "awaiting_text"
        if "pre_emergence_classifier" not in state.scene_choices:
            return "awaiting_narrator"
        return "complete"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pack_self_description(profession: str, personality: str, npcs: str) -> str:
    parts: List[str] = []
    if profession:
        parts.append(f"[Profession] {profession}")
    if personality:
        parts.append(f"[Personality] {personality}")
    if npcs:
        parts.append(f"[People] {npcs}")
    return "\n\n".join(parts)
