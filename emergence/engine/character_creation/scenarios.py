"""Session Zero v2 — 14 scenarios that each build a visible piece of the character sheet.

Scenario  0: Identity (name, age, occupation)
Scenario  1: Temperament (personality reflex)
Scenario  2: Onset Circumstance (where you were when it hit)
Scenario  3: First Power (T3, player picks category + power)
Scenario  4: Primary Cast Mode (how the power expresses itself)
Scenario  5: Primary Rider (signature secondary effect)
Scenario  6: Second Power (T3, different category)
Scenario  7: Secondary Cast Mode
Scenario  8: Secondary Rider
Scenario  9: Survival (months 1-3, pooled specific scenarios with named NPCs)
Scenario 10: Location (month 2-3, region pick)
Scenario 11: Relationships (friends, family, foes)
Scenario 12: Faction (month 10, named representative with specific demands)
Scenario 13: Vows (settlement situations with named NPCs, initial quests)
"""

from __future__ import annotations

import os as _os
import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.session_zero import Scene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.sim.npc_generator import generate_npc


# ---------------------------------------------------------------------------
# V1→V2 category mapping and power loader
# ---------------------------------------------------------------------------

_V1_TO_V2_CATEGORY = {
    "physical_kinetic": "kinetic",
    "perceptual_mental": "cognitive",
    "matter_energy": "material",
    "biological_vital": "somatic",
    "auratic": "cognitive",
    "temporal_spatial": "spatial",
    "eldritch_corruptive": "paradoxic",
}

_V2_DATA_DIR = _os.path.join(
    _os.path.dirname(__file__), "..", "..", "data", "powers_v2",
)

_v2_cache: Optional[Dict[str, Any]] = None


def _get_v2_powers() -> Dict[str, Any]:
    """Load and cache all V2 powers from data files."""
    global _v2_cache
    if _v2_cache is not None:
        return _v2_cache
    from emergence.engine.combat.data_loader import load_powers_v2
    _v2_cache = load_powers_v2(_V2_DATA_DIR)
    return _v2_cache


def _find_v2_power(power_name: str, v1_category: str) -> Optional[Any]:
    """Find the best-matching V2 power for a session-zero power.

    Tries exact name match first, then fuzzy keyword match within the
    mapped V2 category.  Returns the PowerV2 object or None.
    """
    v2_powers = _get_v2_powers()
    v2_cat = _V1_TO_V2_CATEGORY.get(v1_category, "")

    # Normalize for matching
    name_lower = power_name.lower().replace("_", " ").replace("-", " ")
    keywords = set(name_lower.split()) - {"pow", "enhanced", "the", "a"}

    best = None
    best_score = 0
    for pid, pv2 in v2_powers.items():
        if pv2.category != v2_cat:
            continue
        pv2_name = pv2.name.lower().replace("-", " ")
        pv2_words = set(pv2_name.split())
        overlap = len(keywords & pv2_words)
        if overlap > best_score:
            best_score = overlap
            best = pv2
        # Exact name match wins immediately
        if pv2_name == name_lower:
            return pv2

    # If no keyword match, return first power in category
    if best is None:
        for pid, pv2 in v2_powers.items():
            if pv2.category == v2_cat:
                return pv2
    return best


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
        "skills": {"bureaucracy": 3, "literacy": 2, "investigation": 2, "regional_geography": 1},
        "resources": {"scrip_sentiment": 1},
        "heat": {"fed-continuity": -2},
        "narrative_tag": "former federal",
    },
    {
        "display": "Police / first responder / EMT",
        "attribute_deltas": {"perception": 2, "agility": 1},
        "skills": {"first_aid": 2, "streetwise": 2, "intimidation": 2, "combat_ranged": 1, "investigation": 1},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "narrative_tag": "former badge",
    },
    {
        "display": "Soldier or veteran",
        "attribute_deltas": {"strength": 2, "will": 1},
        "skills": {"combat_melee": 2, "combat_ranged": 3, "survival": 2, "first_aid": 1, "tactics": 1},
        "resources": {"military_contacts": 1},
        "heat": {"catskill-throne": -1},
        "narrative_tag": "veteran",
    },
    {
        "display": "Doctor, nurse, or paramedic",
        "attribute_deltas": {"insight": 2, "perception": 1},
        "skills": {"first_aid": 3, "surgery": 2, "pharmacology": 2, "literacy": 2, "diagnosis": 1},
        "resources": {"medical_kit_partial": 1},
        "heat": {"yonkers-compact": -2},
        "narrative_tag": "medical",
    },
    {
        "display": "Farmer or agricultural worker",
        "attribute_deltas": {"strength": 1, "will": 1, "perception": 1},
        "skills": {"farming": 3, "animal_handling": 2, "survival": 2, "weather_read": 1},
        "resources": {"seed_stock": 1},
        "heat": {"central-jersey-league": -1},
        "narrative_tag": "farmer",
    },
    {
        "display": "Tradesperson (electrician, plumber, mechanic, carpenter)",
        "attribute_deltas": {"agility": 2, "insight": 1},
        "skills": {"crafting": 3, "repair": 3, "streetwise": 1, "scavenging": 1},
        "resources": {"tool_kit_full": 1},
        "heat": {},
        "narrative_tag": "tradesperson",
    },
    {
        "display": "Office worker (white-collar professional)",
        "attribute_deltas": {"insight": 2, "will": 1},
        "skills": {"literacy": 3, "negotiation": 2, "bureaucracy": 2, "instruction": 1},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "narrative_tag": "white collar",
    },
    {
        "display": "Service worker (retail, food service, hospitality, driver)",
        "attribute_deltas": {"agility": 1, "perception": 1, "will": 1},
        "skills": {"streetwise": 2, "negotiation": 2, "cooking": 2, "navigation": 1, "languages": 1},
        "resources": {},
        "heat": {},
        "narrative_tag": "service worker",
    },
    {
        "display": "Educator or academic",
        "attribute_deltas": {"insight": 2, "will": 1},
        "skills": {"literacy": 3, "instruction": 3, "history": 2, "languages": 1},
        "resources": {"contacts_thin": 1},
        "heat": {"central-jersey-league": -1},
        "narrative_tag": "academic",
    },
    {
        "display": "Criminal (thief, dealer, smuggler, fence)",
        "attribute_deltas": {"agility": 2, "perception": 1},
        "skills": {"streetwise": 3, "stealth": 3, "lockpicking": 2, "intimidation": 1},
        "resources": {"black_market_contact": 1},
        "heat": {"iron-crown": -1},
        "narrative_tag": "criminal",
    },
    {
        "display": "Manual laborer / construction / dockworker",
        "attribute_deltas": {"strength": 2, "agility": 1},
        "skills": {"crafting": 2, "survival": 2, "streetwise": 2, "repair": 1, "scavenging": 1},
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
# Scenario 1 — Temperament
# ---------------------------------------------------------------------------

TEMPERAMENTS = [
    {
        "display": "Pragmatic — you do what works. Sentiment is a luxury.",
        "id": "pragmatic",
        "attribute_deltas": {"insight": 1},
        "skills": {"negotiation": 1, "streetwise": 1},
        "narrative_tag": "pragmatic",
    },
    {
        "display": "Protective — your people come first. Always.",
        "id": "protective",
        "attribute_deltas": {"will": 1},
        "skills": {"first_aid": 1, "intimidation": 1},
        "narrative_tag": "protective",
    },
    {
        "display": "Curious — you need to understand. The questions keep you moving.",
        "id": "curious",
        "attribute_deltas": {"perception": 1},
        "skills": {"investigation": 1, "literacy": 1},
        "narrative_tag": "curious",
    },
    {
        "display": "Defiant — you don't bend. Not for anyone. Not anymore.",
        "id": "defiant",
        "attribute_deltas": {"strength": 1},
        "skills": {"intimidation": 1, "survival": 1},
        "narrative_tag": "defiant",
    },
    {
        "display": "Patient — you watch, you wait, you choose your moment.",
        "id": "patient",
        "attribute_deltas": {"perception": 1},
        "skills": {"stealth": 1, "negotiation": 1},
        "narrative_tag": "patient",
    },
    {
        "display": "Reckless — you move first and figure it out after.",
        "id": "reckless",
        "attribute_deltas": {"agility": 1},
        "skills": {"combat_melee": 1, "streetwise": 1},
        "narrative_tag": "reckless",
    },
]


class TemperamentScenario(Scene):
    """Who you are underneath. The reflex before the thought.

    Builds: +1 attribute, +1 to two skills, narrative tag.
    """
    scene_id = "sz_v2_temperament"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Before the Onset you had a life. After it, you had instincts.\n\n"
            "People around you fell apart or found their feet. You did "
            "whatever you did — and how you did it said something about "
            "what was underneath the job title and the address.\n\n"
            "When everything broke, what was your reflex?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [t["display"] for t in TEMPERAMENTS]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(TEMPERAMENTS) - 1)
        temp = TEMPERAMENTS[idx]
        return factory.apply_scene_result(self.scene_id, {
            "temperament": temp["id"],
            "attribute_deltas": dict(temp["attribute_deltas"]),
            "skills": dict(temp["skills"]),
            "narrative_tag": temp["narrative_tag"],
            "history": [{
                "timestamp": "T+0",
                "description": f"Temperament: {temp['display'].split(' — ')[0]}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 2 — Onset Circumstance
# ---------------------------------------------------------------------------

CIRCUMSTANCES = [
    {
        "display": "At work, indoors, alone or nearly alone",
        "id": "A",
        "attribute_deltas": {"perception": 1},
        "skills": {"literacy": 1},
    },
    {
        "display": "At work, outdoors, with people around you",
        "id": "B",
        "attribute_deltas": {"strength": 1},
        "skills": {"survival": 1},
    },
    {
        "display": "Commuting — car, bus, subway, bicycle, on foot",
        "id": "C",
        "attribute_deltas": {"agility": 1},
        "skills": {"navigation": 1},
    },
    {
        "display": "At home with family",
        "id": "D",
        "attribute_deltas": {"will": 1},
        "skills": {"first_aid": 1},
    },
    {
        "display": "At a public place — store, restaurant, park",
        "id": "E",
        "attribute_deltas": {"perception": 1},
        "skills": {"streetwise": 1},
    },
    {
        "display": "Asleep",
        "id": "F",
        "attribute_deltas": {"insight": 1},
        "skills": {"investigation": 1},
    },
    {
        "display": "In motion — exercising, running, fighting",
        "id": "G",
        "attribute_deltas": {"agility": 1},
        "skills": {"combat_melee": 1},
    },
    {
        "display": "In crisis — medical emergency, witnessing violence, breaking down",
        "id": "H",
        "attribute_deltas": {"will": 1},
        "skills": {"first_aid": 1},
    },
]


class CircumstanceScenario(Scene):
    """Where you were when the Onset hit. Shapes how your powers manifested.

    Builds: +1 attribute, +1 skill, onset_circumstance (affects power tilts).
    """
    scene_id = "sz_v2_circumstance"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Thursday afternoon. 14:23 UTC. Late May.\n\n"
            "Every device stopped. Every engine quit. The lights went out "
            "and something inside you opened. What you were doing at that "
            "exact moment shaped how the change took hold.\n\n"
            "Where were you when it happened?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [c["display"] for c in CIRCUMSTANCES]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(CIRCUMSTANCES) - 1)
        circ = CIRCUMSTANCES[idx]
        return factory.apply_scene_result(self.scene_id, {
            "onset_circumstance": circ["id"],
            "attribute_deltas": dict(circ["attribute_deltas"]),
            "skills": dict(circ["skills"]),
            "history": [{
                "timestamp": "T+0",
                "description": f"Onset circumstance: {circ['display']}",
                "type": "session_zero",
            }],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scenario 3 — First Power
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
# Power Configuration — Cast Modes & Riders
# ---------------------------------------------------------------------------

class _PowerConfigBase(Scene):
    """Base for cast-mode and rider selection scenes."""

    _slot: str = "anchor"  # "anchor" or "secondary"
    _config_type: str = "cast_mode"  # "cast_mode" or "rider"

    def __init__(self) -> None:
        super().__init__()
        self._options: List[Dict[str, Any]] = []
        self._power_name: str = ""

    def _find_power_entry(self, state: CreationState) -> Optional[Dict[str, Any]]:
        """Find the power dict in state matching our slot."""
        for p in state.powers:
            if p.get("slot") == self._slot:
                return p
        return None

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._options = []
        self._power_name = ""
        power = self._find_power_entry(state)
        if not power:
            return
        self._power_name = power.get("name", "your power")
        v1_cat = power.get("category", "")
        v2_power = _find_v2_power(power.get("name", ""), v1_cat)
        if v2_power is None:
            return
        if self._config_type == "cast_mode":
            self._options = [
                {
                    "slot_id": cm.slot_id,
                    "action_cost": cm.action_cost,
                    "range_band": cm.range_band,
                    "duration": cm.duration,
                    "effect_description": cm.effect_description,
                    "effect_parameters": cm.effect_parameters,
                    "targeting_scope": cm.targeting_scope,
                    "pool_cost": cm.pool_cost,
                }
                for cm in v2_power.cast_modes
            ]
        else:
            self._options = [
                {
                    "slot_id": rs.slot_id,
                    "rider_type": rs.rider_type,
                    "effect_description": rs.effect_description,
                    "effect_parameters": rs.effect_parameters,
                    "pool_cost": rs.pool_cost,
                    "combo_note": rs.combo_note,
                }
                for rs in v2_power.rider_slots
            ]

    def get_choices(self, state: CreationState) -> List[str]:
        if not self._options:
            return ["No options available — use default configuration"]
        result = []
        for opt in self._options:
            if self._config_type == "cast_mode":
                desc = opt.get("effect_description", "")
                cost = f"pool {opt.get('pool_cost', '?')}, {opt.get('action_cost', '?')} action"
                rng_band = opt.get("range_band", "?")
                result.append(f"{desc} ({cost}, range: {rng_band})")
            else:
                desc = opt.get("effect_description", "")
                rtype = opt.get("rider_type", "")
                cost = f"pool {opt.get('pool_cost', 0)}" if opt.get("pool_cost") else "passive"
                result.append(f"[{rtype}] {desc} ({cost})")
        return result

    def _apply_config(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
        config_key: str,
    ) -> CreationState:
        power = self._find_power_entry(state)
        if power and self._options:
            idx = min(choice_index, len(self._options) - 1)
            power[config_key] = self._options[idx]
        return factory.apply_scene_result(self.scene_id, {
            "history": [{
                "timestamp": "T+0",
                "description": f"{self._power_name} {self._config_type}: option {choice_index + 1}",
                "type": "session_zero",
            }],
        }, state, rng)


class PrimaryCastModeScenario(_PowerConfigBase):
    """Choose how your primary power manifests in use — its cast mode."""
    scene_id = "sz_v2_cast1"
    register = "intimate"
    _slot = "anchor"
    _config_type = "cast_mode"

    def get_framing(self, state: CreationState) -> str:
        return (
            f"Your {self._power_name or 'primary power'} can express itself "
            "in different ways.\n\n"
            "Some people with abilities like yours focus them tight — "
            "precise, concentrated, close. Others spread them wide. "
            "Others learn to sustain them, a slow pressure instead of "
            "a quick strike.\n\n"
            "How does yours work?"
        )

    def apply(self, choice_index, state, factory, rng):
        return self._apply_config(choice_index, state, factory, rng, "selected_cast_mode")


class PrimaryRiderScenario(_PowerConfigBase):
    """Choose a rider effect for your primary power."""
    scene_id = "sz_v2_rider1"
    register = "intimate"
    _slot = "anchor"
    _config_type = "rider"

    def get_framing(self, state: CreationState) -> str:
        return (
            f"There is something else about your {self._power_name or 'power'}. "
            "A secondary effect. A signature.\n\n"
            "When you use it, something extra happens — "
            "something that is yours alone. A reflex built into the ability.\n\n"
            "What is your signature?"
        )

    def apply(self, choice_index, state, factory, rng):
        return self._apply_config(choice_index, state, factory, rng, "selected_rider")


class SecondaryCastModeScenario(_PowerConfigBase):
    """Choose how your secondary power manifests in use."""
    scene_id = "sz_v2_cast2"
    register = "intimate"
    _slot = "secondary"
    _config_type = "cast_mode"

    def get_framing(self, state: CreationState) -> str:
        return (
            f"Your second ability — {self._power_name or 'the quieter one'} — "
            "also has its own shape.\n\n"
            "How do you use it?"
        )

    def apply(self, choice_index, state, factory, rng):
        return self._apply_config(choice_index, state, factory, rng, "selected_cast_mode")


class SecondaryRiderScenario(_PowerConfigBase):
    """Choose a rider effect for your secondary power."""
    scene_id = "sz_v2_rider2"
    register = "intimate"
    _slot = "secondary"
    _config_type = "rider"

    def get_framing(self, state: CreationState) -> str:
        return (
            f"And {self._power_name or 'this ability'} has its own signature too.\n\n"
            "What marks it as yours?"
        )

    def apply(self, choice_index, state, factory, rng):
        return self._apply_config(choice_index, state, factory, rng, "selected_rider")


# ---------------------------------------------------------------------------
# Survival (Months 1-3) — pooled scenarios with named NPCs
# ---------------------------------------------------------------------------

SURVIVAL_POOL = [
    # --- Region-specific scenarios ---
    {
        "id": "burning_building",
        "display": "Help {npc_name} — thirty people trapped in a burning tenement. You lose your supplies.",
        "framing_hint": "A building is on fire on the second night.",
        "npc_archetype": "grateful_survivor",
        "npc_standing": 2,
        "attribute_deltas": {"will": 1, "strength": 1},
        "skills": {"first_aid": 2, "survival": 1},
        "resources": {"reputation_local": 2},
        "heat": {},
        "goal": {"id": "promise_to_{npc_id}", "description": "Keep Your Promise to {npc_name}", "pressure": 2},
        "narrative_tag": "rescuer",
        "filters": {"regions": ["New York City", "Philadelphia"]},
    },
    {
        "id": "cache_raid",
        "display": "Take from the {npc_name} family — they have medicine and food. They are weak.",
        "framing_hint": "A family's supply cache.",
        "npc_archetype": "victim",
        "npc_standing": -2,
        "attribute_deltas": {"agility": 1, "strength": 1},
        "skills": {"intimidation": 2, "streetwise": 1},
        "resources": {"stolen_goods": 2},
        "heat": {"iron-crown": -1},
        "goal": {"id": "{npc_id}_remembers", "description": "{npc_name} Remembers What You Did", "pressure": 3},
        "narrative_tag": "raider",
        "filters": {},
    },
    {
        "id": "clinic_defense",
        "display": "Guard {npc_name}'s clinic — protect the wounded, fight off looters. You earn trust and scars.",
        "framing_hint": "A makeshift clinic under siege.",
        "npc_archetype": "mentor",
        "npc_standing": 2,
        "attribute_deltas": {"will": 1, "perception": 1},
        "skills": {"combat_melee": 1, "first_aid": 2, "intimidation": 1},
        "resources": {"reputation_local": 1},
        "heat": {"yonkers-compact": -1},
        "goal": {"id": "clinic_debt_to_{npc_id}", "description": "{npc_name} Needs You Again", "pressure": 2},
        "narrative_tag": "healer",
        "filters": {},
    },
    {
        "id": "convoy_join",
        "display": "Join {npc_name}'s convoy south — safety in numbers, but {npc_name} decides the route.",
        "framing_hint": "A trade convoy forming in the first week.",
        "npc_archetype": "leader",
        "npc_standing": 1,
        "attribute_deltas": {"agility": 1, "perception": 1},
        "skills": {"navigation": 2, "negotiation": 1, "streetwise": 1},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "goal": {"id": "settle_with_{npc_id}", "description": "{npc_name} Owes You a Share", "pressure": 2},
        "narrative_tag": "traveler",
        "filters": {},
    },
    {
        "id": "rooftop_stand",
        "display": "Hold the rooftop with {npc_name} — two weeks, no food drops, three attacks.",
        "framing_hint": "A defensible building, barely.",
        "npc_archetype": "companion",
        "npc_standing": 2,
        "attribute_deltas": {"will": 2},
        "skills": {"combat_ranged": 1, "survival": 2, "repair": 1},
        "resources": {"salvage_cache": 1},
        "heat": {},
        "goal": {"id": "keep_{npc_id}_alive", "description": "Keep {npc_name} Alive", "pressure": 3},
        "narrative_tag": "defender",
        "filters": {"regions": ["New York City", "Northern New Jersey"]},
    },
    {
        "id": "bourse_courier",
        "display": "Run messages for {npc_name} at the early Bourse — copper for speed, enemies for free.",
        "framing_hint": "The trading houses needed couriers.",
        "npc_archetype": "employer",
        "npc_standing": 1,
        "attribute_deltas": {"agility": 2},
        "skills": {"navigation": 2, "streetwise": 1, "negotiation": 1},
        "resources": {"cu": 10},
        "heat": {"philadelphia-bourse": -1},
        "goal": {"id": "debt_to_{npc_id}", "description": "{npc_name}'s Courier Debt", "pressure": 2},
        "narrative_tag": "courier",
        "filters": {"regions": ["Philadelphia", "Central New Jersey"]},
    },
    {
        "id": "grave_detail",
        "display": "Dig graves with {npc_name}'s crew — someone has to. Three months of the dead.",
        "framing_hint": "Bodies. Hundreds.",
        "npc_archetype": "companion",
        "npc_standing": 2,
        "attribute_deltas": {"will": 1, "insight": 1},
        "skills": {"survival": 1, "first_aid": 1, "instruction": 1},
        "resources": {"reputation_local": 2},
        "heat": {"central-jersey-league": -1},
        "goal": {"id": "honor_the_dead_with_{npc_id}", "description": "The Dead Deserve Better", "pressure": 1},
        "narrative_tag": "gravedigger",
        "filters": {},
    },
    {
        "id": "power_enforcer",
        "display": "Use your abilities for {npc_name} — they pay well, but people start to fear you.",
        "framing_hint": "A local boss needed muscle with abilities.",
        "npc_archetype": "employer",
        "npc_standing": 1,
        "attribute_deltas": {"strength": 1, "will": 1},
        "skills": {"intimidation": 2, "combat_melee": 2},
        "resources": {"cu": 15},
        "heat": {"iron-crown": -1},
        "goal": {"id": "break_from_{npc_id}", "description": "Get Free of {npc_name}", "pressure": 3},
        "narrative_tag": "enforcer",
        "filters": {},
    },
    {
        "id": "water_run",
        "display": "Lead water runs with {npc_name} — clean water from the reservoir, past raider territory.",
        "framing_hint": "Water was worth killing for.",
        "npc_archetype": "companion",
        "npc_standing": 2,
        "attribute_deltas": {"agility": 1, "perception": 1},
        "skills": {"navigation": 2, "stealth": 1, "survival": 1},
        "resources": {"contacts_thin": 1},
        "heat": {},
        "goal": {"id": "water_route_with_{npc_id}", "description": "Secure the Water Route", "pressure": 2},
        "narrative_tag": "runner",
        "filters": {"regions": ["New York City", "Northern New Jersey", "Hudson Valley"]},
    },
    {
        "id": "farm_defense",
        "display": "Defend {npc_name}'s farm — the biokinetic fields feed fifty families. Raiders know it.",
        "framing_hint": "A farm worth protecting.",
        "npc_archetype": "farmer",
        "npc_standing": 2,
        "attribute_deltas": {"strength": 1, "will": 1},
        "skills": {"combat_melee": 1, "farming": 1, "survival": 2},
        "resources": {"seed_stock": 1},
        "heat": {"delmarva-harvest-lords": -1},
        "goal": {"id": "protect_{npc_id}_farm", "description": "The Farm Must Stand", "pressure": 3},
        "narrative_tag": "farm defender",
        "filters": {"regions": ["Delmarva", "Central New Jersey", "Lehigh Valley"]},
    },
    {
        "id": "salvage_team",
        "display": "Salvage Lower Manhattan with {npc_name}'s crew — good pay, bad territory, the deep floors eat memory.",
        "framing_hint": "The vaults still had value.",
        "npc_archetype": "leader",
        "npc_standing": 1,
        "attribute_deltas": {"agility": 1, "perception": 1},
        "skills": {"scavenging": 3, "stealth": 1},
        "resources": {"salvage_cache": 2},
        "heat": {"tower-lords": -1},
        "goal": {"id": "unfinished_job_with_{npc_id}", "description": "One More Run — {npc_name}'s Unfinished Job", "pressure": 2},
        "narrative_tag": "salvager",
        "filters": {"regions": ["New York City"]},
    },
    {
        "id": "militia_recruit",
        "display": "Join {npc_name}'s militia — patrol the perimeter, earn meals, lose sleep.",
        "framing_hint": "Someone organized a defense.",
        "npc_archetype": "commander",
        "npc_standing": 1,
        "attribute_deltas": {"strength": 1, "perception": 1},
        "skills": {"combat_ranged": 2, "tactics": 1, "survival": 1},
        "resources": {"military_contacts": 1},
        "heat": {},
        "goal": {"id": "rank_under_{npc_id}", "description": "Prove Yourself to {npc_name}", "pressure": 2},
        "narrative_tag": "militia",
        "filters": {},
    },
    {
        "id": "refugee_guide",
        "display": "Guide refugees south with {npc_name} — seventy people, twelve days, raiders on the third.",
        "framing_hint": "A column of survivors needed a guide.",
        "npc_archetype": "companion",
        "npc_standing": 2,
        "attribute_deltas": {"will": 1, "insight": 1},
        "skills": {"navigation": 2, "instruction": 1, "first_aid": 1},
        "resources": {"reputation_local": 1},
        "heat": {},
        "goal": {"id": "{npc_id}_still_out_there", "description": "{npc_name} Went Back for the Stragglers", "pressure": 3},
        "narrative_tag": "guide",
        "filters": {},
    },
    {
        "id": "hideout_builder",
        "display": "Build a hidden shelter with {npc_name} — underground, off every map. Safe, but isolated.",
        "framing_hint": "Nowhere was safe. You made somewhere.",
        "npc_archetype": "partner",
        "npc_standing": 2,
        "attribute_deltas": {"insight": 1, "will": 1},
        "skills": {"crafting": 2, "stealth": 2},
        "resources": {"salvage_cache": 1},
        "heat": {},
        "goal": {"id": "keep_hideout_with_{npc_id}", "description": "Protect the Hideout", "pressure": 2},
        "narrative_tag": "hider",
        "filters": {},
    },
    {
        "id": "wretch_patrol",
        "display": "Hunt Wretches with {npc_name}'s team — the twisted things in the ruins had to be cleared.",
        "framing_hint": "Wretches in the corridors.",
        "npc_archetype": "hunter",
        "npc_standing": 1,
        "attribute_deltas": {"strength": 1, "agility": 1},
        "skills": {"combat_melee": 2, "survival": 1, "stealth": 1},
        "resources": {"salvage_cache": 1},
        "heat": {},
        "goal": {"id": "hunting_debt_to_{npc_id}", "description": "{npc_name} Lost Someone on the Last Hunt", "pressure": 3},
        "narrative_tag": "wretch hunter",
        "filters": {},
    },
    {
        "id": "radio_network",
        "display": "Build a signal network with {npc_name} — scavenged radios, rooftop relays. Information is power.",
        "framing_hint": "Communication was worth more than food.",
        "npc_archetype": "technician",
        "npc_standing": 1,
        "attribute_deltas": {"insight": 2},
        "skills": {"repair": 2, "crafting": 1, "investigation": 1},
        "resources": {"contacts_thin": 2},
        "heat": {},
        "goal": {"id": "network_with_{npc_id}", "description": "Expand the Signal Network", "pressure": 1},
        "narrative_tag": "signal builder",
        "filters": {"occupations": ["former federal", "tradesperson"]},
    },
    {
        "id": "medic_rounds",
        "display": "Make rounds with {npc_name} — the sick, the wounded, the dying. Never enough hands.",
        "framing_hint": "A doctor needed help.",
        "npc_archetype": "mentor",
        "npc_standing": 2,
        "attribute_deltas": {"insight": 1, "will": 1},
        "skills": {"first_aid": 2, "pharmacology": 1, "diagnosis": 1},
        "resources": {"medical_kit_partial": 1},
        "heat": {"yonkers-compact": -1},
        "goal": {"id": "apprentice_to_{npc_id}", "description": "{npc_name} Has More to Teach You", "pressure": 2},
        "narrative_tag": "field medic",
        "filters": {"occupations": ["medical", "former badge"]},
    },
    {
        "id": "black_market",
        "display": "Run the early black market with {npc_name} — pills, ammunition, pre-Onset luxuries. Dangerous trade.",
        "framing_hint": "Supply and demand.",
        "npc_archetype": "partner",
        "npc_standing": 1,
        "attribute_deltas": {"agility": 1, "perception": 1},
        "skills": {"streetwise": 2, "negotiation": 2},
        "resources": {"cu": 20, "black_market_contact": 1},
        "heat": {"iron-crown": -1, "philadelphia-bourse": 1},
        "goal": {"id": "deal_with_{npc_id}", "description": "{npc_name} Wants a Bigger Cut", "pressure": 3},
        "narrative_tag": "trader",
        "filters": {"occupations": ["criminal", "service worker"]},
    },
    {
        "id": "lone_walker",
        "display": "Walk alone. Avoid people. Scavenge what you need. Trust nobody.",
        "framing_hint": "Nobody was reliable.",
        "npc_archetype": None,
        "npc_standing": 0,
        "attribute_deltas": {"perception": 1, "will": 1},
        "skills": {"stealth": 2, "scavenging": 2, "survival": 1},
        "resources": {"salvage_cache": 1},
        "heat": {},
        "goal": None,
        "narrative_tag": "loner",
        "filters": {},
    },
    {
        "id": "teaching_camp",
        "display": "Teach at {npc_name}'s survivor camp — forty kids, no school, you're what they've got.",
        "framing_hint": "Someone had to keep the children learning.",
        "npc_archetype": "community_leader",
        "npc_standing": 2,
        "attribute_deltas": {"insight": 1, "will": 1},
        "skills": {"instruction": 2, "literacy": 1, "negotiation": 1},
        "resources": {"reputation_local": 1},
        "heat": {"central-jersey-league": -1},
        "goal": {"id": "camp_with_{npc_id}", "description": "{npc_name}'s Camp Needs Supplies", "pressure": 2},
        "narrative_tag": "teacher",
        "filters": {"occupations": ["academic", "white collar"]},
    },
]

# Number of choices presented from the pool each playthrough
_SURVIVAL_CHOICE_COUNT = 5


def _filter_survival_pool(
    pool: List[Dict[str, Any]],
    state: CreationState,
) -> List[Dict[str, Any]]:
    """Filter survival pool by region and occupation tags."""
    eligible = []
    for s in pool:
        filters = s.get("filters", {})
        # Region filter
        regions = filters.get("regions")
        if regions and state.region and state.region not in regions:
            continue
        # Occupation filter
        occupations = filters.get("occupations")
        if occupations:
            if not any(tag in state.narrative_tags for tag in occupations):
                continue
        eligible.append(s)
    return eligible


class SurvivalScenario(Scene):
    """The first three months after the Onset. Specific scenarios with named NPCs.

    Builds: skills, resources, narrative tags, heat, relationships, goals.
    """
    scene_id = "sz_v2_survival"

    def __init__(self) -> None:
        super().__init__()
        self._selected: List[Dict[str, Any]] = []
        self._npc_names: Dict[str, str] = {}
        self._npc_ids: Dict[str, str] = {}

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        eligible = _filter_survival_pool(SURVIVAL_POOL, state)
        if len(eligible) <= _SURVIVAL_CHOICE_COUNT:
            self._selected = list(eligible)
        else:
            self._selected = rng.sample(eligible, _SURVIVAL_CHOICE_COUNT)

        # Generate NPCs for scenarios that need them
        self._npc_names = {}
        self._npc_ids = {}
        for s in self._selected:
            sid = s["id"]
            if s.get("npc_archetype"):
                npc = generate_npc(s["npc_archetype"], {}, rng)
                npc_name = getattr(npc, "display_name", f"NPC-{sid}")
                npc_id = getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}")
                self._npc_names[sid] = npc_name
                self._npc_ids[sid] = npc_id

    def _fill_template(self, template: str, scenario_id: str) -> str:
        npc_name = self._npc_names.get(scenario_id, "someone")
        npc_id = self._npc_ids.get(scenario_id, "unknown")
        return template.replace("{npc_name}", npc_name).replace("{npc_id}", npc_id)

    def get_framing(self, state: CreationState) -> str:
        return (
            "The first three months were the worst.\n\n"
            "The dead lay where they had fallen. The food went bad on the "
            "second day. The water stopped on the third. By the end of the "
            "first week the roads were impassable and the question was not "
            "what had happened but what you were going to do about it.\n\n"
            "What did you do?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [self._fill_template(s["display"], s["id"]) for s in self._selected]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        if not self._selected:
            return state
        idx = min(choice_index, len(self._selected) - 1)
        s = self._selected[idx]
        sid = s["id"]

        choice_data: Dict[str, Any] = {
            "attribute_deltas": dict(s["attribute_deltas"]),
            "skills": dict(s["skills"]),
            "resources": dict(s.get("resources", {})),
            "heat": dict(s.get("heat", {})),
            "narrative_tag": s["narrative_tag"],
            "history": [{
                "timestamp": "T+0.1y",
                "description": f"First months: {self._fill_template(s['display'], sid)}",
                "type": "session_zero",
            }],
        }

        # Generate NPC relationship + goal
        if s.get("npc_archetype") and sid in self._npc_names:
            npc_name = self._npc_names[sid]
            npc_id = self._npc_ids[sid]
            choice_data["relationship"] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": s["npc_standing"],
                "current_state": "alive_present",
                "trust": max(0, s["npc_standing"]),
                "archetype": s["npc_archetype"],
            }
            choice_data["generated_npcs"] = [{
                "npc_id": npc_id,
                "display_name": npc_name,
                "scene_id": self.scene_id,
                "role": s["npc_archetype"],
                "standing": s["npc_standing"],
                "hooks": [self._fill_template(s["goal"]["description"], sid)] if s.get("goal") else [],
            }]
        if s.get("goal"):
            goal = dict(s["goal"])
            goal["id"] = self._fill_template(goal["id"], sid)
            goal["description"] = self._fill_template(goal["description"], sid)
            goal.setdefault("progress", 0)
            choice_data["goals"] = [goal]

        return factory.apply_scene_result(self.scene_id, choice_data, state, rng)


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
# Faction (Month 10) — named representatives with specific demands
# ---------------------------------------------------------------------------

REGION_FACTIONS = {
    "New York City": {"id": "tower-lords", "name": "Tower Lords of Brooklyn"},
    "Northern New Jersey": {"id": "iron-crown", "name": "Iron Crown (Volk)"},
    "Hudson Valley": {"id": "catskill-throne", "name": "Catskill Throne (Preston)"},
    "Central New Jersey": {"id": "central-jersey-league", "name": "Central Jersey League"},
    "Philadelphia": {"id": "philadelphia-bourse", "name": "Philadelphia Bourse"},
    "Lehigh Valley": {"id": "lehigh-principalities", "name": "Lehigh Principalities"},
    "Delmarva": {"id": "delmarva-harvest-lords", "name": "Delmarva Harvest Lords"},
}

FACTION_DEMANDS = {
    "tower-lords": {
        "demand": "tribute — 40% of everything you produce or salvage, monthly",
        "counter": "20% and you scout two ruins a month for their crews",
        "rep_archetype": "enforcer",
        "faction_skill": "intimidation",
    },
    "iron-crown": {
        "demand": "service — join the militia, enforce the borders, answer when called",
        "counter": "report what you see on the roads. No uniform, no oath",
        "rep_archetype": "recruiter",
        "faction_skill": "combat_melee",
    },
    "catskill-throne": {
        "demand": "fealty — kneel to Preston's chain of command. Your powers serve the Throne",
        "counter": "contract work only. Specific jobs, specific pay, no oath",
        "rep_archetype": "officer",
        "faction_skill": "tactics",
    },
    "central-jersey-league": {
        "demand": "contribution — work the fields, teach at Rutgers, join the civic rotation",
        "counter": "seasonal work only. You keep your winters free",
        "rep_archetype": "administrator",
        "faction_skill": "farming",
    },
    "philadelphia-bourse": {
        "demand": "exclusivity — trade only through Bourse channels. They take a cut of everything",
        "counter": "preferred vendor status. You trade through them first, but not only",
        "rep_archetype": "merchant",
        "faction_skill": "negotiation",
    },
    "lehigh-principalities": {
        "demand": "labor — the mines need workers. Your powers make the work safer and faster",
        "counter": "craft commissions only. You build what they need, on your schedule",
        "rep_archetype": "foreman",
        "faction_skill": "crafting",
    },
    "delmarva-harvest-lords": {
        "demand": "tenure — work a demesne plot. The Harvest Lord takes first yield",
        "counter": "apprentice to the biokinetics. Learn their methods, share yours",
        "rep_archetype": "steward",
        "faction_skill": "farming",
    },
}


class FactionScenario(Scene):
    """Month 10: A named faction representative makes a specific demand.

    Builds: faction standing, heat, faction-specific skills, named NPC relationship.
    """
    scene_id = "sz_v2_faction"

    def __init__(self) -> None:
        super().__init__()
        self._rep_name: str = ""
        self._rep_id: str = ""
        self._faction: Dict[str, str] = {}
        self._demand_data: Dict[str, Any] = {}

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._faction = REGION_FACTIONS.get(
            state.region, {"id": "unknown", "name": "the local power"},
        )
        fid = self._faction["id"]
        self._demand_data = FACTION_DEMANDS.get(fid, {
            "demand": "loyalty",
            "counter": "partial cooperation",
            "rep_archetype": "officer",
            "faction_skill": "negotiation",
        })
        npc = generate_npc(self._demand_data["rep_archetype"], {}, rng)
        self._rep_name = getattr(npc, "display_name", "the representative")
        self._rep_id = getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}")

    def get_framing(self, state: CreationState) -> str:
        fname = self._faction.get("name", "the local power")
        demand = self._demand_data.get("demand", "loyalty")
        return (
            f"By the tenth month, {fname} knew who you were.\n\n"
            f"{self._rep_name} came to see you. The conversation was polite. "
            f"The demand was not: {demand}.\n\n"
            f"{self._rep_name} waited for your answer."
        )

    def get_choices(self, state: CreationState) -> List[str]:
        counter = self._demand_data.get("counter", "partial cooperation")
        return [
            f"Accept {self._rep_name}'s terms. Take a position within {self._faction.get('name', 'the faction')}.",
            f"Counter-offer: {counter}. Keep some independence.",
            f"Refuse {self._rep_name}. Walk away. You don't serve anyone.",
            f"Play {self._rep_name}. Take the meeting, use it for your own ends, give nothing real.",
        ]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        fid = self._faction.get("id", "unknown")
        fname = self._faction.get("name", "Unknown")
        faction_skill = self._demand_data.get("faction_skill", "negotiation")

        # Choice-specific consequences
        postures = [
            {  # Accept
                "standing_delta": 2, "heat_delta": -1,
                "skills": {faction_skill: 2},
                "rep_standing": 1,
                "narrative_tag": "faction aligned",
                "goal": {"id": f"serve_{fid}", "description": f"Prove Your Worth to {fname}", "pressure": 2},
            },
            {  # Counter-offer
                "standing_delta": 1, "heat_delta": 0,
                "skills": {"negotiation": 1, faction_skill: 1},
                "rep_standing": 1,
                "narrative_tag": "negotiated with faction",
                "goal": {"id": f"renegotiate_{fid}", "description": f"Renegotiate With {self._rep_name}", "pressure": 2},
            },
            {  # Refuse
                "standing_delta": -1, "heat_delta": 1,
                "skills": {"streetwise": 1},
                "rep_standing": -1,
                "narrative_tag": "independent",
                "goal": {"id": f"avoid_{fid}", "description": f"Stay Clear of {fname}", "pressure": 2},
            },
            {  # Play
                "standing_delta": 0, "heat_delta": 2,
                "skills": {"streetwise": 1, "negotiation": 1},
                "rep_standing": -2,
                "narrative_tag": "played faction",
                "goal": {"id": f"{self._rep_id}_grudge", "description": f"{self._rep_name} Is Looking for You", "pressure": 3},
            },
        ]
        idx = min(choice_index, len(postures) - 1)
        p = postures[idx]

        choice_data: Dict[str, Any] = {
            "skills": dict(p["skills"]),
            "heat": {fid: p["heat_delta"]},
            "faction_standing": {fid: p["standing_delta"]},
            "narrative_tag": p["narrative_tag"],
            "relationship": {
                "npc_id": self._rep_id,
                "display_name": self._rep_name,
                "standing": p["rep_standing"],
                "current_state": "alive_present",
                "trust": max(0, p["rep_standing"]),
                "archetype": self._demand_data.get("rep_archetype", "officer"),
            },
            "generated_npcs": [{
                "npc_id": self._rep_id,
                "display_name": self._rep_name,
                "scene_id": self.scene_id,
                "role": f"{fid}_representative",
                "standing": p["rep_standing"],
                "hooks": [p["goal"]["description"]],
            }],
            "goals": [dict(p["goal"], progress=0)],
            "history": [{
                "timestamp": "T+0.8y",
                "description": f"Faction encounter: {self._rep_name} ({fname})",
                "type": "session_zero",
            }],
        }
        return factory.apply_scene_result(self.scene_id, choice_data, state, rng)


# ---------------------------------------------------------------------------
# Vows & Settlement (Month 12, final scenario) — specific situations
# ---------------------------------------------------------------------------

VOW_PACKAGES = [
    {
        "display": "Protector — {npc_name} and the others depend on you. The settlement's east wall is failing.",
        "npc_archetype": "dependent",
        "npc_standing": 2,
        "goals": [
            {"id": "protect_{npc_id}", "description": "Protect {npc_name} and the Settlement", "progress": 0, "pressure": 3},
            {"id": "fix_the_wall", "description": "Fix the East Wall Before Winter", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 20, "lodging_paid": 1},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "tool_kit", "name": "Basic Tool Kit", "quantity": 1},
        ],
    },
    {
        "display": "Seeker — {npc_name} saw something in the ruins that shouldn't exist. You need to find it.",
        "npc_archetype": "informant",
        "npc_standing": 1,
        "goals": [
            {"id": "investigate_{npc_id}_lead", "description": "Follow {npc_name}'s Lead Into the Ruins", "progress": 0, "pressure": 3},
            {"id": "understand_the_onset", "description": "Understand the Onset", "progress": 0, "pressure": 1},
        ],
        "resources": {"cu": 15, "contacts_thin": 1},
        "inventory": [
            {"id": "clothes_traveling", "name": "Traveling Clothes", "quantity": 1},
            {"id": "journal", "name": "Journal and Pen", "quantity": 1},
        ],
    },
    {
        "display": "Riser — {npc_name} says you have potential. Prove it or be forgotten.",
        "npc_archetype": "mentor",
        "npc_standing": 1,
        "goals": [
            {"id": "train_with_{npc_id}", "description": "Earn {npc_name}'s Respect", "progress": 0, "pressure": 2},
            {"id": "earn_standing", "description": "Make a Name in the Region", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 15, "lodging_paid": 1},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "training_gear", "name": "Training Gear", "quantity": 1},
        ],
    },
    {
        "display": "Survivor — {npc_name} wants in on your supply route. Sharing means safety. Maybe.",
        "npc_archetype": "rival",
        "npc_standing": 0,
        "goals": [
            {"id": "deal_with_{npc_id}", "description": "Settle the Supply Route With {npc_name}", "progress": 0, "pressure": 3},
            {"id": "stay_free", "description": "Stay Free, Stay Fed", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 25},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "salvage_tools", "name": "Salvage Tools", "quantity": 1},
            {"id": "rations_3day", "name": "Three Days of Rations", "quantity": 1},
        ],
    },
    {
        "display": "Avenger — {npc_name} took something from you. You know where they sleep.",
        "npc_archetype": "enemy",
        "npc_standing": -3,
        "goals": [
            {"id": "find_{npc_id}", "description": "Find {npc_name} and Take Back What's Yours", "progress": 0, "pressure": 3},
            {"id": "become_stronger", "description": "Get Strong Enough for What Comes Next", "progress": 0, "pressure": 2},
        ],
        "resources": {"cu": 15},
        "inventory": [
            {"id": "clothes_working", "name": "Working Clothes", "quantity": 1},
            {"id": "weapon_improvised", "name": "Improvised Weapon", "quantity": 1},
        ],
    },
]


class VowScenario(Scene):
    """Month 12: Specific settlement situations with named NPCs and tensions.

    Builds: 2 vows (goals), starting inventory, starting resources, NPC relationship.
    This is the final scenario — the character sheet is complete after this.
    """
    scene_id = "sz_v2_vows"

    def __init__(self) -> None:
        super().__init__()
        self._npc_names: Dict[str, str] = {}
        self._npc_ids: Dict[str, str] = {}

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._npc_names = {}
        self._npc_ids = {}
        for i, vow in enumerate(VOW_PACKAGES):
            archetype = vow.get("npc_archetype")
            if archetype:
                npc = generate_npc(archetype, {}, rng)
                npc_name = getattr(npc, "display_name", f"NPC-vow-{i}")
                npc_id = getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}")
                self._npc_names[i] = npc_name
                self._npc_ids[i] = npc_id

    def _fill(self, text: str, idx: int) -> str:
        npc_name = self._npc_names.get(idx, "someone")
        npc_id = self._npc_ids.get(idx, "unknown")
        return text.replace("{npc_name}", npc_name).replace("{npc_id}", npc_id)

    def get_framing(self, state: CreationState) -> str:
        return (
            "A year has passed. You are alive. That is not nothing.\n\n"
            "You have powers that would have been impossible a year ago. "
            "You have people — some who depend on you, some you depend on, "
            "some who would rather you were gone. You have a place, or "
            "something close to one.\n\n"
            "And there is unfinished business. There always is.\n\n"
            "What drives you now?"
        )

    def get_choices(self, state: CreationState) -> List[str]:
        return [self._fill(v["display"], i) for i, v in enumerate(VOW_PACKAGES)]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(choice_index, len(VOW_PACKAGES) - 1)
        vow = VOW_PACKAGES[idx]

        # Fill templates
        goals = []
        for g in vow["goals"]:
            filled = dict(g)
            filled["id"] = self._fill(filled["id"], idx)
            filled["description"] = self._fill(filled["description"], idx)
            goals.append(filled)

        choice_data: Dict[str, Any] = {
            "goals": goals,
            "resources": dict(vow["resources"]),
            "inventory": list(vow["inventory"]),
            "history": [{
                "timestamp": "T+1y",
                "description": f"Vow: {self._fill(vow['display'].split(' — ')[0], idx)}",
                "type": "session_zero",
            }],
        }

        # Add vow NPC
        archetype = vow.get("npc_archetype")
        npc_standing = vow.get("npc_standing", 0)
        if archetype and idx in self._npc_names:
            npc_name = self._npc_names[idx]
            npc_id = self._npc_ids[idx]
            choice_data["relationship"] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": npc_standing,
                "current_state": "alive_present",
                "trust": max(0, npc_standing),
                "archetype": archetype,
            }
            choice_data["generated_npcs"] = [{
                "npc_id": npc_id,
                "display_name": npc_name,
                "scene_id": self.scene_id,
                "role": archetype,
                "standing": npc_standing,
                "hooks": [goals[0]["description"]] if goals else [],
            }]

        return factory.apply_scene_result(self.scene_id, choice_data, state, rng)


# ---------------------------------------------------------------------------
# Scene list builder
# ---------------------------------------------------------------------------

def make_v2_scenes() -> List[Scene]:
    """Return the 14 v2 scenarios in order."""
    return [
        IdentityScenario(),              #  0: name, age, occupation
        TemperamentScenario(),           #  1: personality / reflex
        CircumstanceScenario(),          #  2: onset circumstance
        FirstPowerScenario(),            #  3: primary power at T3
        PrimaryCastModeScenario(),       #  4: primary cast mode
        PrimaryRiderScenario(),          #  5: primary rider
        SecondPowerScenario(),           #  6: secondary power at T3
        SecondaryCastModeScenario(),     #  7: secondary cast mode
        SecondaryRiderScenario(),        #  8: secondary rider
        SurvivalScenario(),              #  9: months 1-3 (pooled, specific)
        LocationScenario(),              # 10: region
        RelationshipScenario(),          # 11: friends, family, foes
        FactionScenario(),               # 12: named faction representative
        VowScenario(),                   # 13: vows + settlement NPCs
    ]
