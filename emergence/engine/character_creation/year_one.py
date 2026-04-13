"""Year One scenes (6-9) for session zero character creation.

Scene 6: First Weeks
Scene 7: First Encounter With a Faction
Scene 8: Critical Incident (The Hungry Thing / The Reckoning / The Loss)
Scene 9: Settling Into a Place
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation.session_zero import Scene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.sim.npc_generator import generate_npc


# ---------------------------------------------------------------------------
# Scene 6 — First Weeks
# ---------------------------------------------------------------------------

_FIRST_WEEKS = [
    {
        "display": "Stayed in place. Defended what you had.",
        "attribute_deltas": {"will": 1, "perception": 1},
        "skills": {"melee": 1, "basic_repair": 1, "stealth": 1},
        "resources": {"shelter_pre_established": 1},
    },
    {
        "display": "Moved. Found people. Joined a group.",
        "attribute_deltas": {"insight": 1, "agility": 1},
        "skills": {"negotiation": 1, "urban_movement": 1, "streetwise": 1},
        "generate_companion": True,
    },
    {
        "display": "Helped. Treated wounded, brought water, dug graves.",
        "attribute_deltas": {"will": 1},
        "skills": {"first_aid": 2, "instruction": 1},
        "resources": {"reputation_local": 1},
        "heat": {"yonkers-compact": -1, "central-jersey-league": -1},
    },
    {
        "display": "Took. Used what was in you to take what others had.",
        "attribute_deltas": {"strength": 1, "will": 1},
        "skills": {"intimidation": 2, "melee": 1, "scavenging": 2},
        "resources": {"scavenged_goods": 2, "scrip_pre_onset": 1},
        "heat": {"fed-continuity": 1, "iron-crown": -1},
        "corruption_if_eldritch": True,
    },
]


class FirstWeeksScene(Scene):
    scene_id = "sz_6"

    def get_framing(self, state: CreationState) -> str:
        return (
            "The first three weeks were the worst of them. The dead lay "
            "where they had fallen. The food in refrigerators went bad. "
            "You did what you did to keep going.\n\n"
            "What did you do?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [fw["display"] for fw in _FIRST_WEEKS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(_FIRST_WEEKS) - 1)
        fw = _FIRST_WEEKS[idx]

        result: Dict[str, Any] = {
            "attribute_deltas": fw.get("attribute_deltas", {}),
            "skills": fw.get("skills", {}),
            "resources": fw.get("resources", {}),
            "heat": fw.get("heat", {}),
        }

        # Companion NPC
        if fw.get("generate_companion"):
            npc = generate_npc(archetype="companion", rng=rng)
            result["relationship"] = {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": 1,
                "current_state": "first_weeks_companion",
                "archetype": "companion",
            }

        # Corruption if eldritch primary
        if fw.get("corruption_if_eldritch") and state.power_category_primary == "eldritch_corruptive":
            result["corruption"] = 1

        result["history"] = [{
            "timestamp": "T+0.1y",
            "description": f"First weeks: {fw['display']}",
            "type": "session_zero",
        }]

        return factory.apply_scene_result(self.scene_id, result, state, rng)


# ---------------------------------------------------------------------------
# Scene 7 — First Faction Encounter
# ---------------------------------------------------------------------------

_REGION_TO_FACTION = {
    "New York City": "tower-lords",
    "Northern New Jersey": "iron-crown",
    "Hudson Valley": "catskill-throne",
    "Central New Jersey": "central-jersey-league",
    "Philadelphia and inner suburbs": "philadelphia-bourse",
    "Lehigh Valley / Bucks County": "lehigh-principalities",
    "Baltimore / DC corridor": "fed-continuity",
    "Delmarva Peninsula / Chesapeake shore": "delmarva-harvest-lords",
}

_FACTION_ENCOUNTER_CHOICES = [
    {
        "display": "Accept their terms. Take the offered position.",
        "faction_standing": 1,
        "heat_self": -1,
        "heat_rivals": 1,
        "skills": {},  # faction-specific
        "narrative_tag": "joined faction",
    },
    {
        "display": "Negotiate. Take a partial offer; keep some independence.",
        "faction_standing": 1,
        "heat_self": 0,
        "skills": {"negotiation": 1},
        "narrative_tag": "negotiated with faction",
    },
    {
        "display": "Refuse. Walk away.",
        "faction_standing": -1,
        "heat_self": 1,
        "attribute_deltas": {"will": 1},
        "narrative_tag": "refused faction",
    },
    {
        "display": "Take the meeting and use it. Leverage it for something else.",
        "faction_standing": -1,
        "heat_self": 1,
        "resources": {"information": 1, "contacts_thin": 1},
        "skills": {"streetwise": 1, "negotiation": 1},
        "narrative_tag": "played faction",
    },
]

# Faction-specific skill bonuses
_FACTION_SKILL_BONUS = {
    "tower-lords": "intimidation",
    "iron-crown": "intimidation",
    "catskill-throne": "tactics",
    "central-jersey-league": "agriculture",
    "philadelphia-bourse": "negotiation",
    "lehigh-principalities": "craft",
    "fed-continuity": "bureaucracy",
    "delmarva-harvest-lords": "agriculture",
}


class FactionEncounterScene(Scene):
    scene_id = "sz_7"

    def get_framing(self, state: CreationState) -> str:
        faction = _REGION_TO_FACTION.get(state.region, "a local faction")
        return (
            "Months passed. The biggest thing left in your part of the "
            f"world had a name. You met {faction}, in the form of a "
            "person who spoke for it.\n\n"
            "They want something from you. You want something back, or you don't."
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [c["display"] for c in _FACTION_ENCOUNTER_CHOICES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(_FACTION_ENCOUNTER_CHOICES) - 1)
        choice = _FACTION_ENCOUNTER_CHOICES[idx]

        faction_id = _REGION_TO_FACTION.get(state.region, "local-faction")

        result: Dict[str, Any] = {
            "attribute_deltas": choice.get("attribute_deltas", {}),
            "skills": dict(choice.get("skills", {})),
            "resources": choice.get("resources", {}),
            "heat": {faction_id: choice.get("heat_self", 0)},
            "faction_standing": {faction_id: choice.get("faction_standing", 0)},
        }

        # Add faction-specific skill bonus for "accept" choice
        if idx == 0:
            skill = _FACTION_SKILL_BONUS.get(faction_id, "streetwise")
            result["skills"][skill] = result["skills"].get(skill, 0) + 1

        if choice.get("narrative_tag"):
            result["narrative_tag"] = choice["narrative_tag"]

        result["history"] = [{
            "timestamp": "T+0.5y",
            "description": f"Faction encounter: {choice['display']} ({faction_id})",
            "type": "session_zero",
        }]

        return factory.apply_scene_result(self.scene_id, result, state, rng)


# ---------------------------------------------------------------------------
# Scene 8 — Critical Incident
# ---------------------------------------------------------------------------

def _pick_incident_type(state: CreationState) -> str:
    """Pick incident type: A (Hungry Thing), B (Reckoning), C (Loss)."""
    if state.corruption >= 1 or state.power_category_primary == "eldritch_corruptive":
        return "A"
    if any(abs(v) >= 2 for v in state.heat_deltas.values()):
        return "B"
    # Check if scene 7 choice was "played them" (index 3)
    sz7 = state.scene_choices.get("sz_7", {})
    if sz7.get("narrative_tag") == "played faction":
        return "B"
    return "C"


_INCIDENT_A_CHOICES = [
    {
        "display": "Faced it directly. Won at cost.",
        "corruption": 1,
        "harm": [{"tier": 2, "description": "marked by the encounter", "source": "eldritch_proximity"}],
        "attribute_deltas": {"will": 1},
    },
    {
        "display": "Hid. Stayed hidden. Survived without being seen.",
        "skills": {"stealth": 2, "perception": 1},
        "statuses": [{"type": "shaken", "duration_days": 30}],
        "resources": {"information": 1},
    },
    {
        "display": "Bargained.",
        "corruption": 2,
        "powers": [{"power_id": "pow_eldritch_utility", "name": "Eldritch Utility", "category": "eldritch_corruptive", "tier": 1, "slot": "supplemental"}],
        "generate_entity": True,
    },
    {
        "display": "Lost someone to it.",
        "attribute_deltas": {"will": 2},
        "harm": [{"tier": 2, "description": "the night they were taken", "source": "loss"}],
    },
]

_INCIDENT_B_CHOICES = [
    {
        "display": "Fought through it.",
        "heat_boost": 2,
        "harm": [{"tier": 2, "description": "wound from the reckoning", "source": "faction_combat"}],
        "skills": {"melee": 1, "firearms": 1},
    },
    {
        "display": "Ran. Lost everything you couldn't carry.",
        "resource_loss": 0.75,
        "skills": {"urban_movement": 2, "stealth": 1},
    },
    {
        "display": "Surrendered. Took the terms.",
        "resource_loss": 0.50,
        "statuses": [{"type": "marked", "duration_days": -1}],
    },
    {
        "display": "Talked through it. Owed someone for it.",
        "generate_creditor": True,
        "goals": [{"id": "settle_the_debt", "description": "Settle The Debt", "progress": 0, "pressure": 3}],
    },
]

_INCIDENT_C_CHOICES = [
    {
        "display": "You were there. You couldn't stop it.",
        "harm": [{"tier": 2, "description": "the day they died", "source": "loss"}],
        "skills": {"first_aid": 1},
    },
    {
        "display": "You weren't. You found out later.",
        "attribute_deltas": {"will": 1},
    },
    {
        "display": "You found them transformed.",
        "corruption": 1,
    },
    {
        "display": "You held on to them. They lived.",
        "skills": {"first_aid": 1},
        "attribute_deltas": {"will": 1},
        "resources": {"dependents": 1},
    },
]


class CriticalIncidentScene(Scene):
    scene_id = "sz_8"

    def get_framing(self, state: CreationState) -> str:
        itype = _pick_incident_type(state)
        if itype == "A":
            return (
                "Something in your part of the world started to notice you. "
                "What it was, you could not have said. It came once, and you "
                "were ready for it the second time."
            )
        elif itype == "B":
            return (
                "The faction you crossed had a long memory. They came for you. "
                "You were ready, or you weren't."
            )
        else:
            return (
                "The first year took the people you loved at a rate no one "
                "alive had been ready for. Yours came in the spring, or the "
                "winter, or one ordinary Tuesday afternoon."
            )

    def get_choices(self, state: CreationState) -> List[str]:
        itype = _pick_incident_type(state)
        self._incident_type = itype
        if itype == "A":
            return [c["display"] for c in _INCIDENT_A_CHOICES]
        elif itype == "B":
            return [c["display"] for c in _INCIDENT_B_CHOICES]
        else:
            return [c["display"] for c in _INCIDENT_C_CHOICES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        itype = getattr(self, "_incident_type", _pick_incident_type(state))

        if itype == "A":
            choices = _INCIDENT_A_CHOICES
        elif itype == "B":
            choices = _INCIDENT_B_CHOICES
        else:
            choices = _INCIDENT_C_CHOICES

        idx = min(choice_index, len(choices) - 1)
        choice = choices[idx]

        result: Dict[str, Any] = {
            "attribute_deltas": choice.get("attribute_deltas", {}),
            "skills": choice.get("skills", {}),
            "resources": choice.get("resources", {}),
            "corruption": choice.get("corruption", 0),
            "harm": choice.get("harm", []),
            "statuses": choice.get("statuses", []),
            "goals": choice.get("goals", []),
            "powers": choice.get("powers", []),
        }

        # Heat boost for reckoning
        if choice.get("heat_boost"):
            # Find the most heated faction
            if state.heat_deltas:
                max_faction = max(state.heat_deltas, key=lambda k: abs(state.heat_deltas[k]))
                result["heat"] = {max_faction: choice["heat_boost"]}

        # Generate entity NPC (Hungry Thing bargain)
        if choice.get("generate_entity"):
            npc = generate_npc(archetype="entity", rng=rng)
            result["relationship"] = {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": 0,
                "current_state": "patron_or_predator",
                "archetype": "entity",
            }

        # Generate creditor NPC (Reckoning talked through)
        if choice.get("generate_creditor"):
            npc = generate_npc(archetype="creditor", rng=rng)
            result["relationship"] = {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": 1,
                "current_state": "owed_to",
                "archetype": "creditor",
            }

        result["history"] = [{
            "timestamp": "T+0.8y",
            "description": f"Critical incident ({itype}): {choice['display']}",
            "type": "session_zero",
        }]

        return factory.apply_scene_result(self.scene_id, result, state, rng)


# ---------------------------------------------------------------------------
# Scene 9 — Settling Into a Place
# ---------------------------------------------------------------------------

_SETTLING_CHOICES = [
    {
        "display": "In a town. Working.",
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "weight": 1, "value": 2},
            {"id": "tool_kit", "name": "Basic Tool Kit", "weight": 2, "value": 10},
        ],
        "resources": {"cu": 15, "lodging_paid": 1},
        "goals": [{"id": "build_a_life_here", "description": "Build A Life Here", "progress": 0, "pressure": 2}],
    },
    {
        "display": "On a road. Moving between places.",
        "inventory": [
            {"id": "travel_kit", "name": "Travel Kit", "weight": 2, "value": 5},
            {"id": "weapon_road", "name": "Road Weapon", "weight": 1, "value": 8},
            {"id": "bedroll", "name": "Bedroll", "weight": 1, "value": 3},
        ],
        "resources": {"cu": 25, "contacts_thin": 1},
        "skills": {"urban_movement": 1, "weather_read": 1},
        "goals": [{"id": "see_whats_left", "description": "See What's Left", "progress": 0, "pressure": 1}],
    },
    {
        "display": "In a faction's service. Quartered.",
        "inventory": [
            {"id": "faction_kit", "name": "Faction Kit", "weight": 2, "value": 12},
            {"id": "weapon_faction", "name": "Faction Weapon", "weight": 1, "value": 10},
        ],
        "resources": {"cu": 20},
        "goals": [{"id": "advance_within_faction", "description": "Advance Within Faction", "progress": 0, "pressure": 2}],
        "faction_bonus": True,
    },
    {
        "display": "Hidden. Off the map.",
        "inventory": [
            {"id": "cache_food", "name": "Food Cache (14 days)", "weight": 3, "value": 15},
            {"id": "weapon_hidden", "name": "Hidden Weapon", "weight": 1, "value": 5},
        ],
        "resources": {"cu": 5},
        "skills": {"stealth": 2, "scavenging": 1},
        "goals": [{"id": "stay_invisible", "description": "Stay Invisible", "progress": 0, "pressure": 3}],
        "heat_all": -2,
    },
    {
        "display": "Among your people.",
        "inventory": [
            {"id": "kin_token", "name": "Kin Recognition Token", "weight": 0, "value": 5},
            {"id": "clothes_kin", "name": "Kin Clothes", "weight": 1, "value": 3},
        ],
        "resources": {"cu": 10, "kin_network": 1},
        "goals": [{"id": "serve_the_kin", "description": "Serve The Kin", "progress": 0, "pressure": 2}],
        "species_only": True,
    },
]


class SettlingScene(Scene):
    scene_id = "sz_9"

    def get_framing(self, state: CreationState) -> str:
        return (
            "A year after the Onset, you were somewhere. Not where you "
            "had been. Not yet anywhere you would call home. But somewhere.\n\n"
            "Where did the year leave you?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        choices = []
        for sc in _SETTLING_CHOICES:
            if sc.get("species_only") and state.species == "human":
                continue
            choices.append(sc["display"])
        return choices

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        eligible = []
        for sc in _SETTLING_CHOICES:
            if sc.get("species_only") and state.species == "human":
                continue
            eligible.append(sc)

        idx = min(choice_index, len(eligible) - 1)
        choice = eligible[idx]

        result: Dict[str, Any] = {
            "skills": choice.get("skills", {}),
            "resources": choice.get("resources", {}),
            "inventory": choice.get("inventory", []),
            "goals": choice.get("goals", []),
        }

        # Faction bonus for "in service"
        if choice.get("faction_bonus"):
            # Use the faction from scene 7
            from emergence.engine.character_creation.year_one import _REGION_TO_FACTION
            faction_id = _REGION_TO_FACTION.get(state.region, "local-faction")
            result["heat"] = {faction_id: -1}
            result["faction_standing"] = {faction_id: 1}

        # Heat reduction for hiding
        if choice.get("heat_all"):
            heat_reduction = choice["heat_all"]
            result["heat"] = {fid: heat_reduction for fid in state.heat_deltas}

        result["history"] = [{
            "timestamp": "T+1y",
            "description": f"Settled: {choice['display']}",
            "type": "session_zero",
        }]

        return factory.apply_scene_result(self.scene_id, result, state, rng)
