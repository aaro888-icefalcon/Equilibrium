"""Location scene — post-Onset settlement pick.

The player picks where they ended up one year after the Onset. This binds
the job bundle generation (each location has its own archetype pool).
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)


# Canonical post-Onset settlements in the Mid-Atlantic. Keep ids stable —
# they key into job_archetypes.json.
POST_EMERGENCE_LOCATIONS: List[Dict[str, str]] = [
    {
        "id": "manhattan_fragment",
        "display_name": "Manhattan Fragment",
        "summary": "The reduced Manhattan — roughly 250k survivors, a spine of habitable avenues between dead districts. The Echo in Lower Manhattan. The fashion institute crater.",
    },
    {
        "id": "brooklyn_tower_lords",
        "display_name": "Brooklyn (Tower Lords)",
        "summary": "Plural warlords across the borough's high-rises, ruling vertically. Salvage economy, constant low-grade feuding.",
    },
    {
        "id": "queens_commonage",
        "display_name": "Queens Commonage",
        "summary": "A perceptual-coordinated agricultural commune, 480k. Crop surpluses buy them influence across the region.",
    },
    {
        "id": "staten_citadel",
        "display_name": "Staten Citadel",
        "summary": "Chen's temporal-spatial harbor fortress. Tolls salvage routes. Quiet, well-defended, strange.",
    },
    {
        "id": "iron_crown_newark",
        "display_name": "Iron Crown (Newark)",
        "summary": "Volk's warlord polity, 740k. Deep-water port, disciplined enforcers, bureaucratic violence.",
    },
    {
        "id": "yonkers_compact",
        "display_name": "Yonkers Compact",
        "summary": "Biokinetic governing commune — the Three Judges. 340k. Stability through ritual and severity.",
    },
    {
        "id": "peekskill_bear_house",
        "display_name": "Peekskill (Bear-House)",
        "summary": "Matter-energy warlord holding. The reactor, the fabrication yards. 420k. Technically rich, politically brittle.",
    },
    {
        "id": "catskill_throne",
        "display_name": "Catskill Throne (periphery)",
        "summary": "Preston's mountain passes. 180k direct subjects. Living in the Throne's shadow means watching the skyline.",
    },
    {
        "id": "princeton_accord",
        "display_name": "Princeton Accord Hall",
        "summary": "A council-governed township. Old university infrastructure repurposed. Bureaucratic, scholarly, cautious.",
    },
    {
        "id": "central_jersey_league",
        "display_name": "Central Jersey League",
        "summary": "15-township federation, 780k. Agricultural, defensible, pluralistic — and slow to act.",
    },
    {
        "id": "philadelphia_bourse",
        "display_name": "Philadelphia Bourse",
        "summary": "Mercantile consortium, 2.52M metro. Copper-currency economy, sprawling civic life, entrenched rivalries.",
    },
    {
        "id": "south_philly_holding",
        "display_name": "South Philly Holding",
        "summary": "Dreng's enforcer fiefdom, 180k. Navy Yard and the rail spurs. Violent, loyal, proud.",
    },
    {
        "id": "crabclaw_baltimore",
        "display_name": "Crabclaw Confederation (Baltimore)",
        "summary": "Three-lord fishery-and-trade federation, 440k. The harbor as currency.",
    },
    {
        "id": "delmarva_harvest",
        "display_name": "Delmarva Harvest Lords (Easton)",
        "summary": "Six biokinetic lords, 1.15M. Food exporter for the region. Internal tensions recurrent.",
    },
    {
        "id": "lehigh_principalities",
        "display_name": "Lehigh Principalities (Allentown)",
        "summary": "12 coal lords, 990k. Species G agricultural integration. Cold winters, long contracts.",
    },
    {
        "id": "fed_continuity_dc",
        "display_name": "Federal Continuity Command (DC)",
        "summary": "Residual state authority, 1.9M. Pentagon intact. Paperwork, denial, uniforms.",
    },
    {
        "id": "flushing_edison_c_cluster",
        "display_name": "Flushing / Edison (Silver-Hand Cluster)",
        "summary": "Species C craft specialists, 178k. The Twelve Hands council. Artisan economies.",
    },
    {
        "id": "pine_barrens_batsto",
        "display_name": "Pine Barrens (Batsto / The Listening)",
        "summary": "Eldritch cult core, ~35k and growing. Ong's Hat scattered perimeter. The woods themselves are unreliable.",
    },
]

POST_EMERGENCE_LOCATION_IDS = frozenset(loc["id"] for loc in POST_EMERGENCE_LOCATIONS)


class LocationScene:
    scene_id: str = "location"
    register: str = "standard"

    def get_framing(self, state: CreationState) -> str:
        return (
            "One year after the Onset, the map is smaller and louder. "
            "Pick where you ended up — the settlement that took you in, the "
            "work that keeps you fed, the roofs and walls you mostly trust."
        )

    def get_choices(self, state: CreationState) -> List[Dict[str, str]]:
        return [dict(loc) for loc in POST_EMERGENCE_LOCATIONS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        if choice_index < 0 or choice_index >= len(POST_EMERGENCE_LOCATIONS):
            raise ValueError("location pick index out of range")
        chosen = POST_EMERGENCE_LOCATIONS[choice_index]
        scene_result = {
            "location": chosen["id"],
            "starting_location": chosen["id"],
        }
        state = factory.apply_scene_result(self.scene_id, scene_result, state, rng)
        # starting_location propagates through scene_result via `location`;
        # also set the typed field explicitly.
        state.starting_location = chosen["id"]
        state.scene_choices["post_emergence_location"] = chosen["id"]
        return state

    def phase(self, state: CreationState) -> str:
        if state.scene_choices.get("post_emergence_location"):
            return "complete"
        return "pending"


def get_location(location_id: str) -> Dict[str, str]:
    for loc in POST_EMERGENCE_LOCATIONS:
        if loc["id"] == location_id:
            return dict(loc)
    raise KeyError(f"unknown post-emergence location: {location_id!r}")
