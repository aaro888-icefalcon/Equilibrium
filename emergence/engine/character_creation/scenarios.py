"""Session Zero v2 — 8 scenarios that each build a visible piece of the character sheet.

Scenario 0: Identity (name, age, occupation)
Scenario 1: First Power (T3, player picks category + power)
Scenario 2: Second Power (T3, different category)
Scenario 3: Survival (months 1-3, skills/resources)
Scenario 4: Location (month 2-3, region pick)
Scenario 5: Relationships (friends, family, foes)
Scenario 6: Faction (month 10, alignment)
Scenario 7: Vows (initial quests, final character sheet)
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
# T3 Power Catalog — all powers available at session zero, grouped by category
# ---------------------------------------------------------------------------

T3_POWER_CATALOG: Dict[str, List[Dict[str, Any]]] = {
    "physical_kinetic": [
        {"id": "pow_enhanced_strength", "name": "Enhanced Strength", "desc": "Raw physical force beyond human limits. Lift, crush, throw."},
        {"id": "pow_kinetic_burst", "name": "Kinetic Burst", "desc": "Project concussive force at short range. Hits like a car."},
        {"id": "pow_speed_surge", "name": "Speed Surge", "desc": "Bursts of inhuman speed. Outrun vehicles on short sprints."},
        {"id": "pow_kinetic_shield", "name": "Kinetic Shield", "desc": "Reactive force barrier. Stops bullets, deflects blows."},
        {"id": "pow_momentum_strike", "name": "Momentum Strike", "desc": "Channel accumulated momentum into a single devastating blow."},
    ],
    "perceptual_mental": [
        {"id": "pow_heightened_senses", "name": "Heightened Senses", "desc": "Sight, hearing, smell pushed far past human range."},
        {"id": "pow_empathic_read", "name": "Empathic Read", "desc": "Feel what others feel. Detect lies, fear, intent."},
        {"id": "pow_precognitive_flash", "name": "Precognitive Flash", "desc": "Brief flashes of what's about to happen. Seconds, not minutes."},
        {"id": "pow_mental_projection", "name": "Mental Projection", "desc": "Push thoughts or images into another mind. Not control — communication."},
        {"id": "pow_intent_detection", "name": "Intent Detection", "desc": "Know when someone means to act and what they mean to do."},
    ],
    "matter_energy": [
        {"id": "pow_electrical_touch", "name": "Electrical Touch", "desc": "Channel and direct current through contact. Start hearts, stop them."},
        {"id": "pow_heat_manipulation", "name": "Heat Manipulation", "desc": "Draw heat out or push it in. Freeze water, melt steel."},
        {"id": "pow_material_shaping", "name": "Material Shaping", "desc": "Reshape non-living matter by touch. Bend steel, seal concrete."},
        {"id": "pow_energy_absorption", "name": "Energy Absorption", "desc": "Absorb kinetic or thermal energy, store it, release it later."},
        {"id": "pow_disintegration_touch", "name": "Disintegration Touch", "desc": "Unmake matter at the molecular level through sustained contact."},
    ],
    "biological_vital": [
        {"id": "pow_biokinesis", "name": "Biokinesis", "desc": "Reshape living tissue. Heal wounds, mend bone, accelerate growth."},
        {"id": "pow_vital_sense", "name": "Vital Sense", "desc": "Feel pulse, inflammation, infection without touching. Diagnose by presence."},
        {"id": "pow_regeneration", "name": "Regeneration", "desc": "Your own body heals fast. Cuts close in minutes, bones set in hours."},
        {"id": "pow_life_drain", "name": "Life Drain", "desc": "Pull vitality from the living. They weaken; you strengthen."},
        {"id": "pow_toxin_resistance", "name": "Toxin Resistance", "desc": "Your body neutralizes poisons, infections, radiation. Nearly immune."},
    ],
    "auratic": [
        {"id": "pow_calming_presence", "name": "Calming Presence", "desc": "A zone around you where panic fades and voices lower."},
        {"id": "pow_fear_induction", "name": "Fear Induction", "desc": "A zone around you where courage fails. People flee or freeze."},
        {"id": "pow_aura_suppression", "name": "Aura Suppression", "desc": "Nullify other auratic effects in your radius. The quiet one."},
        {"id": "pow_mass_influence", "name": "Mass Influence", "desc": "Sway a crowd's mood. Not mind control — emotional weather."},
        {"id": "pow_charismatic_aura", "name": "Charismatic Aura", "desc": "People trust you. Not magic — just an overwhelming pull to listen."},
    ],
    "temporal_spatial": [
        {"id": "pow_phase_step", "name": "Phase Step", "desc": "Step through solid matter. Walls, doors, floors — walk through them."},
        {"id": "pow_temporal_stutter", "name": "Temporal Stutter", "desc": "Stutter time around you. A half-second where only you move."},
        {"id": "pow_spatial_fold", "name": "Spatial Fold", "desc": "Fold space to move objects or yourself across short distances."},
        {"id": "pow_reflex_acceleration", "name": "Reflex Acceleration", "desc": "Your perception of time slows. You see the bullet before it arrives."},
        {"id": "pow_spatial_awareness", "name": "Spatial Awareness", "desc": "Sense everything in a radius. Through walls, underground, in the dark."},
    ],
    "eldritch_corruptive": [
        {"id": "pow_reality_warp", "name": "Reality Warp", "desc": "Bend local physics. Gravity shifts, distances change. Costs you."},
        {"id": "pow_entropy_channel", "name": "Entropy Channel", "desc": "Accelerate decay and dissolution. Rot, rust, ruin on contact."},
        {"id": "pow_void_sight", "name": "Void Sight", "desc": "See what others can't. The hidden, the eldritch, the things between."},
        {"id": "pow_shadow_grasp", "name": "Shadow Grasp", "desc": "Darkness obeys you. Shape it, move through it, strike from it."},
        {"id": "pow_eldritch_whisper", "name": "Eldritch Whisper", "desc": "Hear what the entities say. Understand them. They understand you back."},
    ],
}

# Category display names
CATEGORY_LABELS = {
    "physical_kinetic": "Physical / Kinetic",
    "perceptual_mental": "Perceptual / Mental",
    "matter_energy": "Matter / Energy",
    "biological_vital": "Biological / Vital",
    "auratic": "Auratic",
    "temporal_spatial": "Temporal / Spatial",
    "eldritch_corruptive": "Eldritch / Corruptive",
}

# ---------------------------------------------------------------------------
# Occupation list (reused from v1 with clearer attribute/skill output)
# ---------------------------------------------------------------------------

OCCUPATIONS = [
    {
        "display": "Federal employee (DOD civilian, clerk, analyst, engineer)",
        "attribute_deltas": {"insight": 2, "perception": 1},
        "skills": {"bureaucracy": 3, "literacy": 3, "investigation": 2},
        "resources": {"scrip_sentiment": 1},
        "heat": {"fed-continuity": -2},
        "narrative_tag": "former federal",
    },
    {
        "display": "Police / first responder / EMT",
        "attribute_deltas": {"perception": 2, "agility": 1},
        "skills": {"first_aid": 3, "streetwise": 3, "intimidation": 2},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "narrative_tag": "former badge",
    },
    {
        "display": "Soldier or veteran",
        "attribute_deltas": {"strength": 2, "will": 1},
        "skills": {"combat_melee": 3, "combat_ranged": 3, "survival": 2, "first_aid": 1},
        "resources": {"military_contacts": 1},
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
        "attribute_deltas": {"strength": 1, "will": 1, "perception": 1},
        "skills": {"farming": 4, "animal_handling": 2, "survival": 2},
        "resources": {"seed_stock": 1},
        "heat": {"central-jersey-league": -1},
        "narrative_tag": "farmer",
    },
    {
        "display": "Tradesperson (electrician, plumber, mechanic, carpenter)",
        "attribute_deltas": {"agility": 2, "insight": 1},
        "skills": {"crafting": 4, "repair": 3, "streetwise": 1},
        "resources": {"tool_kit_full": 1},
        "heat": {},
        "narrative_tag": "tradesperson",
    },
    {
        "display": "Office worker (white-collar professional)",
        "attribute_deltas": {"insight": 2, "will": 1},
        "skills": {"literacy": 3, "negotiation": 2, "bureaucracy": 2},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "narrative_tag": "white collar",
    },
    {
        "display": "Service worker (retail, food service, hospitality, driver)",
        "attribute_deltas": {"agility": 1, "perception": 1, "will": 1},
        "skills": {"streetwise": 3, "negotiation": 2, "cooking": 2},
        "resources": {},
        "heat": {},
        "narrative_tag": "service worker",
    },
    {
        "display": "Educator or academic",
        "attribute_deltas": {"insight": 2, "will": 1},
        "skills": {"literacy": 4, "instruction": 3, "history": 2},
        "resources": {"contacts_thin": 1},
        "heat": {"central-jersey-league": -1},
        "narrative_tag": "academic",
    },
    {
        "display": "Criminal (thief, dealer, smuggler, fence)",
        "attribute_deltas": {"agility": 2, "perception": 1},
        "skills": {"streetwise": 4, "stealth": 3, "lockpicking": 2},
        "resources": {"black_market_contact": 1},
        "heat": {"iron-crown": -1},
        "narrative_tag": "criminal",
    },
    {
        "display": "Manual laborer / construction / dockworker",
        "attribute_deltas": {"strength": 2, "agility": 1},
        "skills": {"crafting": 2, "survival": 2, "streetwise": 2},
        "resources": {},
        "heat": {},
        "narrative_tag": "laborer",
    },
]

# ---------------------------------------------------------------------------
# Scenario 0 — Identity
# ---------------------------------------------------------------------------

class IdentityScenario(Scene):
    """Who you were before the Onset. Name, age, occupation.

    Builds: name, age, base attributes, starting skills, resources.
    """
    scene_id = "sz_v2_identity"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Before we begin, I need to know who you were.\n\n"
            "The Onset was a year ago. Most of the people you knew are dead. "
            "The ones who lived carry the habits of what they used to do — "
            "the way they think, the way they move, what their hands remember.\n\n"
            "Tell me your name.\n"
            "Tell me how old you were when everything stopped.\n"
            "Then tell me what you did for a living."
        )

    def needs_text_input(self) -> bool:
        return True

    def get_choices(self, state: CreationState) -> List[str]:
        return [occ["display"] for occ in OCCUPATIONS]

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        name = text_inputs.get("name", "").strip() or "Unknown"
        age_str = text_inputs.get("age", "25").strip()
        try:
            age = max(16, min(65, int(age_str)))
        except ValueError:
            age = 25
        return factory.apply_scene_result(self.scene_id + "_text", {
            "name": name,
            "age_at_onset": age,
        }, state, rng)

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(OCCUPATIONS) - 1)
        occ = OCCUPATIONS[idx]
        return factory.apply_scene_result(self.scene_id, {
            "attribute_deltas": dict(occ["attribute_deltas"]),
            "skills": dict(occ["skills"]),
            "resources": dict(occ.get("resources", {})),
            "heat": dict(occ.get("heat", {})),
            "narrative_tag": occ["narrative_tag"],
            "history": [{
                "timestamp": "T+0",
                "description": f"Pre-onset occupation: {occ['display']}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 1 — First Power
# ---------------------------------------------------------------------------

def _build_power_choices(exclude_category: str = "") -> List[str]:
    """Build a flat choice list: '[Category] Power Name — description'."""
    choices = []
    for cat_id, powers in T3_POWER_CATALOG.items():
        if cat_id == exclude_category:
            continue
        label = CATEGORY_LABELS[cat_id]
        for p in powers:
            choices.append(f"[{label}] {p['name']} — {p['desc']}")
    return choices


def _power_from_flat_index(index: int, exclude_category: str = "") -> tuple:
    """Given a flat index into the power list, return (category_id, power_dict)."""
    i = 0
    for cat_id, powers in T3_POWER_CATALOG.items():
        if cat_id == exclude_category:
            continue
        for p in powers:
            if i == index:
                return cat_id, p
            i += 1
    # Fallback
    first_cat = next(c for c in T3_POWER_CATALOG if c != exclude_category)
    return first_cat, T3_POWER_CATALOG[first_cat][0]


class FirstPowerScenario(Scene):
    """Your primary power manifests at T3. You choose category and power.

    Builds: primary power, power category, tier 3, tier ceiling 5.
    """
    scene_id = "sz_v2_power1"
    register = "intimate"

    def get_framing(self, state: CreationState) -> str:
        return (
            "On the day of the Onset, something inside you opened.\n\n"
            "You felt it before you understood it. A warmth, a pressure, "
            "a sense of something that had always been there becoming "
            "available. Over the next hours and days you learned what "
            "you could do. It was not subtle. It was not small.\n\n"
            "What woke up in you?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return _build_power_choices()

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        total = sum(len(v) for v in T3_POWER_CATALOG.values())
        idx = min(choice_index, total - 1)
        cat_id, power = _power_from_flat_index(idx)

        return factory.apply_scene_result(self.scene_id, {
            "power_category_primary": cat_id,
            "tier": 3,
            "tier_ceiling": 5,
            "powers": [{
                "power_id": power["id"],
                "name": power["name"],
                "category": cat_id,
                "tier": 3,
                "slot": "anchor",
            }],
            "breakthroughs": [{
                "id": "breakthrough_0",
                "type": "manifestation",
                "description": f"Initial manifestation: {cat_id} T3",
                "cost": "onset trauma",
            }],
            "history": [{
                "timestamp": "T+0",
                "description": f"Manifestation: {CATEGORY_LABELS[cat_id]} T3 — {power['name']}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 2 — Second Power
# ---------------------------------------------------------------------------

class SecondPowerScenario(Scene):
    """A secondary power manifests at T3. Different category from the first.

    Builds: secondary power, secondary power category.
    """
    scene_id = "sz_v2_power2"
    register = "intimate"

    def get_framing(self, state: CreationState) -> str:
        primary = CATEGORY_LABELS.get(state.power_category_primary, "your first")
        return (
            "In the weeks that followed, you discovered something else.\n\n"
            f"Your {primary} ability was the loud one — the one you noticed "
            "first. But underneath it, quieter, was a second capacity. "
            "Different in kind. It took longer to understand.\n\n"
            "What else can you do?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return _build_power_choices(exclude_category=state.power_category_primary)

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        exclude = state.power_category_primary
        total = sum(
            len(v) for k, v in T3_POWER_CATALOG.items() if k != exclude
        )
        idx = min(choice_index, total - 1)
        cat_id, power = _power_from_flat_index(idx, exclude_category=exclude)

        return factory.apply_scene_result(self.scene_id, {
            "power_category_secondary": cat_id,
            "powers": [{
                "power_id": power["id"],
                "name": power["name"],
                "category": cat_id,
                "tier": 3,
                "slot": "secondary",
            }],
            "history": [{
                "timestamp": "T+0.1y",
                "description": f"Secondary manifestation: {CATEGORY_LABELS[cat_id]} T3 — {power['name']}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 3 — Survival (Months 1-3)
# ---------------------------------------------------------------------------

SURVIVAL_STRATEGIES = [
    {
        "display": "Stayed and defended. Held your ground, protected what you had.",
        "attribute_deltas": {"will": 1, "strength": 1},
        "skills": {"combat_melee": 2, "survival": 2, "intimidation": 1},
        "resources": {"salvage_cache": 1},
        "heat": {},
        "narrative_tag": "defender",
    },
    {
        "display": "Moved and joined. Found people. Safety in numbers.",
        "attribute_deltas": {"agility": 1, "perception": 1},
        "skills": {"streetwise": 2, "navigation": 2, "negotiation": 1},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "narrative_tag": "joiner",
    },
    {
        "display": "Helped. Treated the wounded, brought water, dug graves.",
        "attribute_deltas": {"will": 1, "insight": 1},
        "skills": {"first_aid": 2, "instruction": 1, "survival": 1},
        "resources": {"reputation_local": 1},
        "heat": {"yonkers-compact": -1, "central-jersey-league": -1},
        "narrative_tag": "healer",
    },
    {
        "display": "Took. Used what was in you to take what others had.",
        "attribute_deltas": {"agility": 1, "strength": 1},
        "skills": {"combat_melee": 2, "streetwise": 2, "intimidation": 2},
        "resources": {"stolen_goods": 1},
        "heat": {"iron-crown": -1},
        "narrative_tag": "raider",
    },
]


class SurvivalScenario(Scene):
    """The first three months after the Onset. How you survived.

    Builds: skills, resources, narrative tags, heat.
    """
    scene_id = "sz_v2_survival"

    def get_framing(self, state: CreationState) -> str:
        return (
            "The first three months were the worst.\n\n"
            "The dead lay where they had fallen. The food in refrigerators "
            "went bad on the second day. The water stopped on the third. "
            "By the end of the first week the hospitals were dark and the "
            "roads were impassable and the question was not what had happened "
            "but what you were going to do about it.\n\n"
            "What did you do?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [s["display"] for s in SURVIVAL_STRATEGIES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(SURVIVAL_STRATEGIES) - 1)
        strat = SURVIVAL_STRATEGIES[idx]
        return factory.apply_scene_result(self.scene_id, {
            "attribute_deltas": dict(strat["attribute_deltas"]),
            "skills": dict(strat["skills"]),
            "resources": dict(strat.get("resources", {})),
            "heat": dict(strat.get("heat", {})),
            "narrative_tag": strat["narrative_tag"],
            "history": [{
                "timestamp": "T+0.1y",
                "description": f"First months: {strat['display']}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 4 — Location (Month 2-3)
# ---------------------------------------------------------------------------

REGIONS = [
    {
        "display": "Manhattan — midtown, salvage territory, tower-lord shadow",
        "region": "New York City",
        "location": "loc-manhattan-midtown",
        "local_factions": ["tower-lords", "queens-commonage"],
    },
    {
        "display": "Brooklyn — tower-lord districts, salvage trade hub",
        "region": "New York City",
        "location": "loc-brooklyn-tower-districts",
        "local_factions": ["tower-lords"],
    },
    {
        "display": "Northern New Jersey — Iron Crown territory, Port Newark",
        "region": "Northern New Jersey",
        "location": "loc-port-newark-compound",
        "local_factions": ["iron-crown", "staten-citadel"],
    },
    {
        "display": "Hudson Valley — Catskill Throne tribute lands",
        "region": "Hudson Valley",
        "location": "loc-kingston-hv",
        "local_factions": ["catskill-throne", "yonkers-compact"],
    },
    {
        "display": "Central New Jersey — League townships, Rutgers farmland",
        "region": "Central New Jersey",
        "location": "loc-rutgers-campus",
        "local_factions": ["central-jersey-league"],
    },
    {
        "display": "Philadelphia — Bourse trading floor, copper economy",
        "region": "Philadelphia",
        "location": "loc-bourse-trading-floor",
        "local_factions": ["philadelphia-bourse", "south-philly-holding"],
    },
    {
        "display": "Lehigh Valley — coal principalities, Sun-Worn farms",
        "region": "Lehigh Valley",
        "location": "loc-lehigh-coal-towns",
        "local_factions": ["lehigh-principalities"],
    },
    {
        "display": "Delmarva Peninsula — harvest demesnes, granary of the region",
        "region": "Delmarva",
        "location": "loc-delmarva-farmstead",
        "local_factions": ["delmarva-harvest-lords"],
    },
]


class LocationScenario(Scene):
    """Month 2-3: Where you landed after the worst of it.

    Builds: region, location, local faction context.
    """
    scene_id = "sz_v2_location"

    def get_framing(self, state: CreationState) -> str:
        return (
            "By the second month, the dying had mostly stopped. "
            "What was left was geography.\n\n"
            "You could not stay where you had been — or you could, but "
            "the place had changed around you. The question was where "
            "to go, and every answer came with a different set of walls.\n\n"
            "Where did you end up?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [r["display"] for r in REGIONS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(REGIONS) - 1)
        region = REGIONS[idx]
        return factory.apply_scene_result(self.scene_id, {
            "region": region["region"],
            "location": region["location"],
            "history": [{
                "timestamp": "T+0.2y",
                "description": f"Settled in: {region['display'].split(' — ')[0]}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 5 — Relationships (Friends, Family, Foes)
# ---------------------------------------------------------------------------

RELATIONSHIP_WEBS = [
    {
        "display": "Family bond — a sibling or parent survived nearby. One close friend. One person who dislikes you.",
        "npcs": [
            {"archetype": "family", "standing": 3, "state": "alive_present", "role": "ally"},
            {"archetype": "friend", "standing": 2, "state": "alive_present", "role": "ally"},
            {"archetype": "rival", "standing": -2, "state": "alive_present", "role": "foe"},
        ],
        "goals": [
            {"id": "protect_family", "description": "Protect Your Family", "progress": 0, "pressure": 3},
        ],
    },
    {
        "display": "Close crew — two friends from before or after. No family nearby. A local enemy.",
        "npcs": [
            {"archetype": "friend", "standing": 2, "state": "alive_present", "role": "ally"},
            {"archetype": "friend", "standing": 2, "state": "alive_present", "role": "ally"},
            {"archetype": "enemy", "standing": -3, "state": "alive_present", "role": "foe"},
        ],
        "goals": [
            {"id": "keep_crew_together", "description": "Keep Your Crew Together", "progress": 0, "pressure": 2},
        ],
    },
    {
        "display": "Mentor and rival — someone taught you, someone tests you. A missing person you care about.",
        "npcs": [
            {"archetype": "mentor", "standing": 2, "state": "alive_present", "role": "ally"},
            {"archetype": "rival", "standing": -1, "state": "alive_present", "role": "foe"},
            {"archetype": "missing_person", "standing": 2, "state": "missing", "role": "absent"},
        ],
        "goals": [
            {"id": "find_the_missing", "description": "Find the Missing", "progress": 0, "pressure": 3},
        ],
    },
    {
        "display": "Alone with one bond — one person matters. Everyone else is transactional. No enemies yet.",
        "npcs": [
            {"archetype": "partner", "standing": 3, "state": "alive_present", "role": "ally"},
        ],
        "goals": [
            {"id": "hold_what_you_have", "description": "Hold What You Have", "progress": 0, "pressure": 2},
        ],
    },
    {
        "display": "Wide and shallow — many acquaintances, no one close. Two people owe you. One you owe.",
        "npcs": [
            {"archetype": "debtor", "standing": 1, "state": "alive_present", "role": "ally"},
            {"archetype": "debtor", "standing": 1, "state": "alive_present", "role": "ally"},
            {"archetype": "creditor", "standing": 1, "state": "alive_present", "role": "foe"},
        ],
        "goals": [
            {"id": "settle_debts", "description": "Settle All Debts", "progress": 0, "pressure": 2},
        ],
    },
]


class RelationshipScenario(Scene):
    """Months 1-9: The people around you. Friends, family, foes.

    Builds: 1-3 NPC relationships, a goal tied to them.
    """
    scene_id = "sz_v2_relationships"

    def get_framing(self, state: CreationState) -> str:
        return (
            "You did not survive alone. Nobody did.\n\n"
            "Over the first months you found people — or they found you. "
            "Some of them you knew from before. Some you met in the wreckage. "
            "Not all of them are on your side.\n\n"
            "Who are your people?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [w["display"] for w in RELATIONSHIP_WEBS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(RELATIONSHIP_WEBS) - 1)
        web = RELATIONSHIP_WEBS[idx]

        # Generate NPCs
        relationships_data = {}
        history_entries = []
        for i, npc_spec in enumerate(web["npcs"]):
            npc = generate_npc(npc_spec["archetype"], {}, rng)
            npc_id = getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}")
            npc_name = getattr(npc, "display_name", f"NPC-{i}")
            relationships_data[npc_id] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": npc_spec["standing"],
                "current_state": npc_spec["state"],
                "trust": max(0, npc_spec["standing"]),
                "archetype": npc_spec["archetype"],
            }
            role_label = npc_spec["role"]
            history_entries.append({
                "timestamp": "T+0.5y",
                "description": f"Relationship: {npc_name} ({npc_spec['archetype']}, {role_label})",
                "type": "session_zero",
            })

        # Apply the first relationship through the standard channel
        # and store the rest directly on state
        first_npc_id = next(iter(relationships_data)) if relationships_data else None
        first_rel = relationships_data.pop(first_npc_id) if first_npc_id else None

        result = factory.apply_scene_result(self.scene_id, {
            "relationship": first_rel,
            "goals": list(web["goals"]),
            "history": history_entries,
        }, state, rng)

        # Add remaining NPCs directly to state
        for npc_id, rel_data in relationships_data.items():
            result.relationships[npc_id] = rel_data

        return result


# ---------------------------------------------------------------------------
# Scenario 6 — Faction (Month 10)
# ---------------------------------------------------------------------------

FACTION_POSTURES = [
    {
        "display": "Join them. Accept their terms and take a position.",
        "standing_delta": 2,
        "heat_delta": -1,
        "skills": {"negotiation": 1},
        "narrative_tag": "faction aligned",
    },
    {
        "display": "Negotiate. Partial deal — work with them, keep independence.",
        "standing_delta": 1,
        "heat_delta": 0,
        "skills": {"negotiation": 1},
        "narrative_tag": "negotiated with faction",
    },
    {
        "display": "Refuse. Walk away. You don't work for anyone.",
        "standing_delta": -1,
        "heat_delta": 1,
        "skills": {"streetwise": 1},
        "narrative_tag": "independent",
    },
    {
        "display": "Play them. Take the meeting and use it for your own ends.",
        "standing_delta": 0,
        "heat_delta": 2,
        "skills": {"streetwise": 1, "negotiation": 1},
        "narrative_tag": "played faction",
    },
]

# Region → primary faction mapping
REGION_FACTIONS = {
    "New York City": {"id": "tower-lords", "name": "Tower Lords of Brooklyn"},
    "Northern New Jersey": {"id": "iron-crown", "name": "Iron Crown (Volk)"},
    "Hudson Valley": {"id": "catskill-throne", "name": "Catskill Throne (Preston)"},
    "Central New Jersey": {"id": "central-jersey-league", "name": "Central Jersey League"},
    "Philadelphia": {"id": "philadelphia-bourse", "name": "Philadelphia Bourse"},
    "Lehigh Valley": {"id": "lehigh-principalities", "name": "Lehigh Principalities"},
    "Delmarva": {"id": "delmarva-harvest-lords", "name": "Delmarva Harvest Lords"},
}


class FactionScenario(Scene):
    """Month 10: The local power structure finds you. How do you respond?

    Builds: faction standing, heat, faction-specific skills.
    """
    scene_id = "sz_v2_faction"

    def get_framing(self, state: CreationState) -> str:
        faction = REGION_FACTIONS.get(state.region, {})
        fname = faction.get("name", "the local power")
        return (
            f"By the tenth month, {fname} knew who you were.\n\n"
            "In this world, nobody with your abilities stays invisible "
            "for long. They sent someone to talk. The conversation was "
            "polite. The implication was not.\n\n"
            "How did you respond?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [p["display"] for p in FACTION_POSTURES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(FACTION_POSTURES) - 1)
        posture = FACTION_POSTURES[idx]
        faction = REGION_FACTIONS.get(state.region, {"id": "unknown", "name": "Unknown"})
        fid = faction["id"]
        fname = faction["name"]

        return factory.apply_scene_result(self.scene_id, {
            "skills": dict(posture["skills"]),
            "heat": {fid: posture["heat_delta"]},
            "faction_standing": {fid: posture["standing_delta"]},
            "narrative_tag": posture["narrative_tag"],
            "history": [{
                "timestamp": "T+0.8y",
                "description": f"Faction encounter ({fname}): {posture['display'].split('.')[0]}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 7 — Vows (Month 12, final scenario)
# ---------------------------------------------------------------------------

VOW_PACKAGES = [
    {
        "display": "Protector — keep your people safe and build something that lasts",
        "goals": [
            {"id": "protect_my_people", "description": "Protect My People", "progress": 0, "pressure": 3},
            {"id": "build_something_lasting", "description": "Build Something Lasting", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 20, "lodging_paid": 1},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "tool_kit", "name": "Basic Tool Kit", "quantity": 1},
        ],
    },
    {
        "display": "Seeker — find what was lost and understand what happened",
        "goals": [
            {"id": "find_what_was_lost", "description": "Find What Was Lost", "progress": 0, "pressure": 3},
            {"id": "understand_the_onset", "description": "Understand the Onset", "progress": 0, "pressure": 1},
        ],
        "resources": {"cu": 15, "contacts_thin": 1},
        "inventory": [
            {"id": "clothes_traveling", "name": "Traveling Clothes", "quantity": 1},
            {"id": "journal", "name": "Journal and Pen", "quantity": 1},
        ],
    },
    {
        "display": "Riser — master your powers and earn a name for yourself",
        "goals": [
            {"id": "master_your_power", "description": "Master Your Power", "progress": 0, "pressure": 2},
            {"id": "earn_standing", "description": "Earn Standing", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 15, "lodging_paid": 1},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "training_gear", "name": "Training Gear", "quantity": 1},
        ],
    },
    {
        "display": "Survivor — stay free, stay fed, owe nothing to anyone",
        "goals": [
            {"id": "stay_free", "description": "Stay Free", "progress": 0, "pressure": 2},
            {"id": "secure_supply", "description": "Secure a Reliable Supply Line", "progress": 0, "pressure": 3},
        ],
        "resources": {"cu": 25},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "salvage_tools", "name": "Salvage Tools", "quantity": 1},
            {"id": "rations_3day", "name": "Three Days of Rations", "quantity": 1},
        ],
    },
    {
        "display": "Avenger — someone wronged you or yours, and you remember",
        "goals": [
            {"id": "right_the_wrong", "description": "Right the Wrong", "progress": 0, "pressure": 3},
            {"id": "become_stronger", "description": "Become Strong Enough", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 15},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "weapon_improvised", "name": "Improvised Weapon", "quantity": 1},
        ],
    },
]


class VowScenario(Scene):
    """Month 12: What you've sworn. Determines initial quests and starting gear.

    Builds: 2 vows (goals), starting inventory, starting resources.
    This is the final scenario — the character sheet is complete after this.
    """
    scene_id = "sz_v2_vows"

    def get_framing(self, state: CreationState) -> str:
        return (
            "A year has passed. You are alive. That is not nothing.\n\n"
            "You have powers that would have been impossible a year ago. "
            "You have people — some who depend on you, some you depend on, "
            "some who would rather you were gone. You have a place, or "
            "something close to one.\n\n"
            "And you have made promises. To yourself, to others, to "
            "the shape of the life you intend to build.\n\n"
            "What are you sworn to?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [v["display"] for v in VOW_PACKAGES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(VOW_PACKAGES) - 1)
        vow = VOW_PACKAGES[idx]

        return factory.apply_scene_result(self.scene_id, {
            "goals": list(vow["goals"]),
            "resources": dict(vow["resources"]),
            "inventory": list(vow["inventory"]),
            "history": [{
                "timestamp": "T+1y",
                "description": f"Vow: {vow['display'].split(' — ')[0]}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene list builder
# ---------------------------------------------------------------------------

def make_v2_scenes() -> List[Scene]:
    """Return the 8 v2 scenarios in order."""
    return [
        IdentityScenario(),      # 0: name, age, occupation
        FirstPowerScenario(),    # 1: primary power at T3
        SecondPowerScenario(),   # 2: secondary power at T3
        SurvivalScenario(),      # 3: months 1-3
        LocationScenario(),      # 4: month 2-3 location
        RelationshipScenario(),  # 5: friends, family, foes
        FactionScenario(),       # 6: month 10 faction
        VowScenario(),           # 7: vows → initial quests
    ]
