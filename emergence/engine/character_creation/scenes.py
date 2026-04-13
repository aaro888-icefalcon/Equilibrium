"""Pre-onset scenes (0-4) for session zero character creation.

Scene 0: Opening Framing (name + age)
Scene 1: Pre-Onset Occupation (12 options)
Scene 2: Pre-Onset Relationships (6 archetypes)
Scene 3: Pre-Onset Location & Circumstance (8 regions × 8 circumstances)
Scene 4: Pre-Onset Immediate Concern (8 options)
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.session_zero import Scene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.sim.npc_generator import generate_npc


# ---------------------------------------------------------------------------
# Scene 0 — Opening Framing
# ---------------------------------------------------------------------------

class OpeningScene(Scene):
    """Scene 0: Opening Framing — establish name and age at the Onset."""
    scene_id = "sz_0"

    def get_framing(self, state: CreationState) -> str:
        return (
            "The Onset was a year ago this season. Most of the people you "
            "knew are dead. The ones who lived live differently. You are a "
            "person in a smaller, harder world. You can do things now that "
            "no one could do before. So can almost everyone left alive.\n\n"
            "Tell me your name.\n"
            "Tell me how old you were on the day everything stopped."
        )

    def needs_text_input(self) -> bool:
        return True

    def get_choices(self, state: CreationState) -> List[str]:
        return []

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        name = text_inputs.get("name", "").strip()
        if not name:
            name = rng.choice([
                "Marisol Reyes", "Theo Blackwell", "Anya Sokolova",
                "Marcus Chen", "Elena Torres", "David Okonkwo",
            ])

        age_str = text_inputs.get("age", "25").strip()
        try:
            age = int(age_str)
            age = max(16, min(65, age))
        except ValueError:
            age = 25

        return factory.apply_scene_result(self.scene_id, {
            "name": name,
            "age_at_onset": age,
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene 1 — Occupation
# ---------------------------------------------------------------------------

OCCUPATIONS = [
    {
        "display": "Federal employee (DOD civilian, clerk, analyst, engineer)",
        "attribute_deltas": {"perception": 2, "insight": 2},
        "skills": {"bureaucracy": 3, "firearms": 1, "regional_geography": 2, "literacy": 4},
        "resources": {"scrip_sentiment": 1},
        "heat": {"fed-continuity": -1},
        "narrative_tag": "former federal",
    },
    {
        "display": "Police / first responder / EMT",
        "attribute_deltas": {"strength": 2, "will": 2},
        "skills": {"firearms": 3, "melee": 2, "first_aid": 3, "intimidation": 2, "urban_movement": 2},
        "resources": {"side_arm_pre_onset": 1},
        "heat": {"iron-crown": 1},
        "narrative_tag": "former badge",
    },
    {
        "display": "Soldier or veteran",
        "attribute_deltas": {"strength": 2, "will": 2, "perception": 1},
        "skills": {"firearms": 4, "melee": 2, "tactics": 2, "command": 1, "field_medicine": 2},
        "heat": {"catskill-throne": -1},
        "narrative_tag": "veteran",
    },
    {
        "display": "Doctor, nurse, or paramedic",
        "attribute_deltas": {"insight": 2, "perception": 1},
        "skills": {"first_aid": 4, "surgery": 2, "pharmacology": 3, "literacy": 4},
        "resources": {"medical_kit_partial": 1},
        "heat": {"yonkers-compact": -2},
        "narrative_tag": "medical",
    },
    {
        "display": "Farmer or agricultural worker",
        "attribute_deltas": {"strength": 2, "will": 1},
        "skills": {"agriculture": 4, "animal_handling": 3, "weather_read": 2, "basic_repair": 2},
        "heat": {"delmarva-harvest-lords": -1, "central-jersey-league": -1},
        "narrative_tag": "of the land",
    },
    {
        "display": "Tradesperson (electrician, plumber, mechanic, carpenter)",
        "attribute_deltas": {"agility": 2, "insight": 1},
        "skills": {"craft": 3, "basic_repair": 4, "scavenging": 2},
        "resources": {"tools_pre_onset": 1},
        "heat": {"flushing-edison-cluster": -1},
        "narrative_tag": "skilled hands",
    },
    {
        "display": "Office worker (white-collar professional)",
        "attribute_deltas": {"insight": 2},
        "skills": {"bureaucracy": 2, "literacy": 4, "negotiation": 2},
        "resources": {"contacts_thin": 1},
        "narrative_tag": "former office",
    },
    {
        "display": "Service worker (retail, food service, hospitality, driver)",
        "attribute_deltas": {"agility": 1, "perception": 2},
        "skills": {"streetwise": 3, "negotiation": 2, "urban_movement": 2, "languages": 1},
        "narrative_tag": "service",
    },
    {
        "display": "Educator or academic",
        "attribute_deltas": {"insight": 2, "will": 1},
        "skills": {"literacy": 4, "history": 3, "languages": 2, "instruction": 3},
        "heat": {"central-jersey-league": -1},
        "narrative_tag": "educator",
    },
    {
        "display": "Criminal (thief, dealer, smuggler, fence)",
        "attribute_deltas": {"agility": 2, "perception": 1},
        "skills": {"streetwise": 4, "stealth": 3, "melee": 2, "intimidation": 2, "scavenging": 2},
        "heat": {"iron-crown": -1, "philadelphia-bourse": 1},
        "narrative_tag": "underside",
    },
    {
        "display": "Student (college or graduate program)",
        "attribute_deltas": {"insight": 1, "perception": 1},
        "skills": {"literacy": 4, "languages": 1, "instruction": 1},
        "resources": {"youth": 1},
        "narrative_tag": "student",
        "max_age": 28,
    },
    {
        "display": "Manual laborer / construction / dockworker",
        "attribute_deltas": {"strength": 2, "will": 1},
        "skills": {"melee": 2, "basic_repair": 2, "scavenging": 3, "urban_movement": 2},
        "heat": {"south-philly-holding": -1},
        "narrative_tag": "muscle",
    },
]


class OccupationScene(Scene):
    """Scene 1: Pre-Onset Occupation — 12 options with attribute/skill/resource deltas."""
    scene_id = "sz_1"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Before the Onset you had a life and a job. The job is gone "
            "now in any form that matters, but the habits of it are still "
            "in your hands and in how you think.\n\n"
            "What did you do?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        choices = []
        for occ in OCCUPATIONS:
            # Filter by eligibility
            max_age = occ.get("max_age")
            if max_age and state.age_at_onset > max_age:
                continue
            choices.append(occ["display"])
        return choices

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        # Build eligible list
        eligible = []
        for occ in OCCUPATIONS:
            max_age = occ.get("max_age")
            if max_age and state.age_at_onset > max_age:
                continue
            eligible.append(occ)

        idx = min(choice_index, len(eligible) - 1)
        occ = eligible[idx]

        return factory.apply_scene_result(self.scene_id, {
            "attribute_deltas": occ.get("attribute_deltas", {}),
            "skills": occ.get("skills", {}),
            "resources": occ.get("resources", {}),
            "heat": occ.get("heat", {}),
            "narrative_tag": occ.get("narrative_tag", ""),
            "history": [{"timestamp": "T+0", "description": f"Pre-onset occupation: {occ['display']}", "type": "session_zero"}],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene 2 — Relationships
# ---------------------------------------------------------------------------

_RELATIONSHIP_ARCHETYPES = [
    {"display": "Spouse / partner / lover", "min_age": 18, "standing": 3, "archetype": "spouse"},
    {"display": "Parent (mother or father)", "min_age": 16, "max_age": 55, "standing": 2, "archetype": "parent"},
    {"display": "Child (one or more)", "min_age": 22, "standing": 3, "archetype": "child"},
    {"display": "Sibling", "standing": 2, "archetype": "sibling"},
    {"display": "Closest friend", "standing": 2, "archetype": "friend"},
    {"display": "Mentor or boss", "standing": 1, "archetype": "mentor"},
]

_STATUS_OPTIONS = ["alive_present", "alive_separated", "dead", "transformed", "missing"]

_GOAL_BY_STATUS = {
    "alive_present": ("rebuild_with_them", 3),
    "alive_separated": ("reach_them", 3),
    "dead": ("honor_their_memory", 3),
    "transformed": ("release_them", 3),
    "missing": ("find_them", 3),
}


class RelationshipScene(Scene):
    """Scene 2: Pre-Onset Relationships — 6 archetypes with NPC generation."""
    scene_id = "sz_2"

    def get_framing(self, state: CreationState) -> str:
        return (
            "You did not live alone before, even if you lived alone. "
            "People had a claim on you. You had a claim on them.\n\n"
            "Tell me about the one person who mattered most."
        )

    def get_choices(self, state: CreationState) -> List[str]:
        choices = []
        for arch in _RELATIONSHIP_ARCHETYPES:
            min_age = arch.get("min_age", 0)
            max_age = arch.get("max_age", 999)
            if state.age_at_onset < min_age or state.age_at_onset > max_age:
                continue
            choices.append(arch["display"])
        return choices

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        eligible = []
        for arch in _RELATIONSHIP_ARCHETYPES:
            min_age = arch.get("min_age", 0)
            max_age = arch.get("max_age", 999)
            if state.age_at_onset < min_age or state.age_at_onset > max_age:
                continue
            eligible.append(arch)

        idx = min(choice_index, len(eligible) - 1)
        arch = eligible[idx]

        # Generate NPC for this relationship
        npc_age = self._npc_age(arch["archetype"], state.age_at_onset, rng)
        npc = generate_npc(
            archetype=arch["archetype"],
            constraints={"age": npc_age},
            rng=rng,
        )

        # Pick status (default: alive_present for test simplicity)
        status = rng.choice(["alive_present", "alive_separated", "missing"])

        goal_id, pressure = _GOAL_BY_STATUS.get(status, ("find_them", 3))

        # Attribute bonus per archetype
        attr_deltas = {}
        if arch["archetype"] in ("spouse",) and status in ("dead", "missing", "transformed"):
            attr_deltas["will"] = 1
        elif arch["archetype"] == "parent":
            attr_deltas["insight"] = 1
        elif arch["archetype"] == "child":
            attr_deltas["will"] = 1
            attr_deltas["perception"] = 1
        elif arch["archetype"] == "mentor":
            attr_deltas["insight"] = 1

        # Skill bonus per archetype
        skills = {}
        if arch["archetype"] == "sibling":
            skills["streetwise"] = 1
        elif arch["archetype"] == "friend":
            skills[rng.choice(["negotiation", "streetwise", "instruction"])] = 1
        elif arch["archetype"] == "mentor":
            pass  # Resource only

        resources = {}
        if arch["archetype"] == "mentor":
            resources["contacts_thin"] = 1
        if arch["archetype"] == "child":
            resources["dependents"] = 1

        return factory.apply_scene_result(self.scene_id, {
            "attribute_deltas": attr_deltas,
            "skills": skills,
            "resources": resources,
            "relationship": {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": arch["standing"],
                "current_state": status,
                "archetype": arch["archetype"],
            },
            "goals": [{
                "id": goal_id,
                "description": goal_id.replace("_", " ").title(),
                "progress": 0,
                "pressure": pressure,
            }],
            "history": [{
                "timestamp": "T+0",
                "description": f"Key relationship: {arch['display']} ({npc.display_name}, {status})",
                "type": "session_zero",
            }],
        }, state, rng)

    def _npc_age(self, archetype: str, player_age: int, rng: _random.Random) -> int:
        if archetype == "spouse":
            return max(18, player_age + rng.randint(-10, 10))
        elif archetype == "parent":
            return player_age + rng.randint(18, 40)
        elif archetype == "child":
            return max(0, min(25, player_age - rng.randint(18, 30)))
        elif archetype == "sibling":
            return max(16, player_age + rng.randint(-5, 5))
        elif archetype == "friend":
            return max(16, player_age + rng.randint(-8, 8))
        elif archetype == "mentor":
            return player_age + rng.randint(5, 25)
        return player_age


# ---------------------------------------------------------------------------
# Scene 3 — Location & Circumstance
# ---------------------------------------------------------------------------

REGIONS = [
    "New York City",
    "Northern New Jersey",
    "Hudson Valley",
    "Central New Jersey",
    "Philadelphia and inner suburbs",
    "Lehigh Valley / Bucks County",
    "Baltimore / DC corridor",
    "Delmarva Peninsula / Chesapeake shore",
]

_REGION_TO_LOCATION = {
    "New York City": "loc-manhattan-midtown",
    "Northern New Jersey": "loc-port-newark-compound",
    "Hudson Valley": "loc-mount-tremper",
    "Central New Jersey": "loc-princeton-accord-hall",
    "Philadelphia and inner suburbs": "loc-old-market-philly",
    "Lehigh Valley / Bucks County": "loc-lehigh-bridge-bethlehem",
    "Baltimore / DC corridor": "loc-pentagon",
    "Delmarva Peninsula / Chesapeake shore": "loc-easton-marsden-estate",
}

CIRCUMSTANCES = [
    "At work, indoors, alone or near-alone",
    "At work, outdoors, with people",
    "Commuting (car, bus, subway, bicycle, on foot)",
    "At home with family",
    "At a public place (store, restaurant, park, gym)",
    "Asleep",
    "In motion: exercising, athletic activity, fighting, fleeing",
    "In a crisis: medical, emotional, witnessing violence",
]

_CIRCUMSTANCE_IDS = ["A", "B", "C", "D", "E", "F", "G", "H"]


class LocationScene(Scene):
    """Scene 3: Location and Circumstance — 8 regions x 8 circumstances."""
    scene_id = "sz_3"

    def get_framing(self, state: CreationState) -> str:
        return (
            "When the Onset hit, you were somewhere specific. Doing "
            "something specific. The where and the what of that hour "
            "shaped what happened next.\n\n"
            "Where were you? What were you doing?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        # Combined: 8 regions presented first, then circumstances
        # For simplicity, present regions as the primary choice
        return list(REGIONS)

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        region_idx = min(choice_index, len(REGIONS) - 1)
        region = REGIONS[region_idx]
        location = _REGION_TO_LOCATION.get(region, "")

        # Pick circumstance randomly (in full game, this is a second choice)
        circ_idx = rng.randint(0, len(CIRCUMSTANCES) - 1)
        circumstance = CIRCUMSTANCES[circ_idx]
        circ_id = _CIRCUMSTANCE_IDS[circ_idx]

        return factory.apply_scene_result(self.scene_id, {
            "region": region,
            "location": location,
            "onset_circumstance": circ_id,
            "history": [{
                "timestamp": "T+0",
                "description": f"Onset location: {region}. Circumstance: {circumstance}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene 4 — Immediate Concern
# ---------------------------------------------------------------------------

CONCERNS = [
    {
        "display": "Money trouble (debt, loss of job, eviction)",
        "attribute_deltas": {"will": 1},
        "goals": [{"id": "rebuild_what_was_lost", "description": "Rebuild What Was Lost", "progress": 0, "pressure": 2}],
        "narrative_tag": "from hard times",
    },
    {
        "display": "A sick or dying family member",
        "skills": {"first_aid": 1},
        "goals": [{"id": "honor_them", "description": "Honor Them", "progress": 0, "pressure": 3}],
        "generate_npc": True,
    },
    {
        "display": "A romantic crisis (breakup, affair, custody fight)",
        "attribute_deltas": {"insight": 1},
        "goals": [{"id": "settle_the_account", "description": "Settle The Account", "progress": 0, "pressure": 2}],
    },
    {
        "display": "A legal problem (case pending, recently arrested)",
        "skills": {"streetwise": 1},
        "heat": {"fed-continuity": 1},
        "goals": [{"id": "stay_free", "description": "Stay Free", "progress": 0, "pressure": 2}],
    },
    {
        "display": "A new job, move, or major life change about to happen",
        "attribute_deltas": {"insight": 1},
        "resources": {"contacts_thin": 1},
        "goals": [{"id": "become_who_i_was_going_to_be", "description": "Become Who I Was Going To Be", "progress": 0, "pressure": 1}],
    },
    {
        "display": "A child on the way",
        "attribute_deltas": {"will": 1},
        "resources": {"dependents": 1},
        "goals": [{"id": "keep_them_alive", "description": "Keep Them Alive", "progress": 0, "pressure": 5}],
    },
    {
        "display": "A grudge or open enemy",
        "skills": {"intimidation": 1},
        "goals": [{"id": "settle_with_them", "description": "Settle With Them", "progress": 0, "pressure": 2}],
        "generate_enemy": True,
    },
    {
        "display": "Nothing in particular — life was steady",
        "attribute_deltas": {"will": 1, "insight": 1},
        "resources": {"stability": 1},
        "narrative_tag": "from a quiet life",
    },
]


class ConcernScene(Scene):
    """Scene 4: Immediate Concern — 8 pre-onset worries with goals and NPCs."""
    scene_id = "sz_4"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Everyone carried something into that day that did not "
            "survive it. A worry. A debt. A diagnosis. A fight you "
            "hadn't finished.\n\n"
            "What was yours?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [c["display"] for c in CONCERNS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(CONCERNS) - 1)
        concern = CONCERNS[idx]

        result: Dict[str, Any] = {
            "attribute_deltas": concern.get("attribute_deltas", {}),
            "skills": concern.get("skills", {}),
            "resources": concern.get("resources", {}),
            "heat": concern.get("heat", {}),
            "goals": concern.get("goals", []),
        }

        if concern.get("narrative_tag"):
            result["narrative_tag"] = concern["narrative_tag"]

        # Generate NPC if needed
        if concern.get("generate_npc"):
            npc = generate_npc(archetype="family", rng=rng)
            result["relationship"] = {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": 2,
                "current_state": "dying_or_dead",
                "archetype": "family",
            }

        if concern.get("generate_enemy"):
            npc = generate_npc(archetype="enemy", rng=rng)
            result["relationship"] = {
                "npc_id": npc.id,
                "display_name": npc.display_name,
                "standing": -2,
                "current_state": "enemy",
                "archetype": "enemy",
            }

        result["history"] = [{
            "timestamp": "T+0",
            "description": f"Pre-onset concern: {concern['display']}",
            "type": "session_zero",
        }]

        return factory.apply_scene_result(self.scene_id, result, state, rng)
