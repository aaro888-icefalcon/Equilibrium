"""Session Zero v2 — 12 scenarios that each build a visible piece of the sheet.

Scenario  0: Identity  (name, age, occupation, freeform self-description)
Scenario  1: Scenario1 (cinematic danger vignette -> primary power at T3)
Scenario  2: Scenario2 (second vignette -> secondary power at T3)
Scenario  3: Primary Cast Mode  (+ narrative prompt: who saw, what it cost)
Scenario  4: Primary Rider      (+ narrative prompt)
Scenario  5: Secondary Cast Mode (+ narrative prompt)
Scenario  6: Secondary Rider    (+ narrative prompt)
Scenario  7: Survival (months 1-3, pooled specific scenarios with named NPCs)
Scenario  8: Location (month 2-3, region pick)
Scenario  9: Relationships (friends, family, foes)
Scenario 10: Faction (month 10, named representative with specific demands)
Scenario 11: Vows (settlement situations with named NPCs, initial quests)

Powers come exclusively from the V2 catalog (emergence/data/powers_v2/*.json)
loaded via load_powers_v2() into the PowerV2 dataclass.
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
from emergence.engine.character_creation import scenario_pool
from emergence.engine.sim.npc_generator import generate_npc


# ---------------------------------------------------------------------------
# V2 catalog access
# ---------------------------------------------------------------------------

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


V2_CATEGORY_LABELS: Dict[str, str] = {
    "kinetic":   "Kinetic",
    "material":  "Material",
    "paradoxic": "Paradoxic",
    "spatial":   "Spatial",
    "somatic":   "Somatic",
    "cognitive": "Cognitive",
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
    """Who you were before the Onset. Name, age, occupation, self-description.

    Builds: name, age, self_description, reaction_tags (from description),
    base attributes, starting skills, resources.
    """
    scene_id = "sz_v2_identity"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Before we begin, I need to know who you were.\n\n"
            "The Onset was a year ago. Most of the people you knew are dead. "
            "The ones who lived carry the habits of what they used to do — "
            "the way they think, the way they move, what their hands remember.\n\n"
            "Tell me your name.\n"
            "Tell me how old you were when everything stopped. (16-65)\n"
            "Tell me what you did for a living.\n"
            "And in your own words — a few sentences — tell me who you were. "
            "Temperament, interests, the people who shaped you, the way "
            "others described you. Whatever feels true."
        )

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        return [
            {"key": "name", "prompt": "Tell me your name."},
            {"key": "age", "prompt": "Tell me how old you were on the day everything stopped. (16-65)"},
            {"key": "description", "prompt": "In a few sentences, tell me who you were before the Onset."},
        ]

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
        description = text_inputs.get("description", "").strip()
        tags = scenario_pool.extract_description_tags(description)
        return factory.apply_scene_result(self.scene_id + "_text", {
            "name": name,
            "age_at_onset": age,
            "self_description": description,
            "reaction_tags": tags,
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
# Scenario 1 & 2 — Cinematic Danger Vignettes → Power Selection
# ---------------------------------------------------------------------------

class _ScenarioBase(Scene):
    """Shared machinery for the two vignette-driven power-selection scenes.

    Flow per scene:
      1. prepare()   — pick vignette, pre-compute the 6 weighted V2 choices.
      2. framing     — present the vignette.
      3. text input  — freeform "reaction"; apply_text() stores reaction and
                       extracts tags, then recomputes the 6 choices with the
                       expanded tag bag.
      4. choice      — player picks one of the 6 powers.
      5. apply()     — commit the chosen PowerV2 to state at Tier 3.
    """

    _slot: int = 1
    _slot_key: str = "1"
    _slot_label: str = "anchor"
    register = "intimate"

    def __init__(self) -> None:
        super().__init__()
        self._vignette: Dict[str, Any] = {}
        self._options: List[Any] = []

    # -- scene lifecycle ----------------------------------------------------

    def _exclude_category(self, state: CreationState) -> str:
        return ""

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        # Deterministic RNGs so get_framing/get_choices and apply agree.
        vignette_rng = _random.Random(state.seed + self._slot * 101)
        option_rng = _random.Random(state.seed + self._slot * 211)

        exclude_ids = tuple(
            vid for k, vid in state.scenario_vignettes.items() if k != self._slot_key
        )
        self._vignette = scenario_pool.select_vignette(
            self._slot, vignette_rng, exclude_ids=exclude_ids,
        )

        powers = list(_get_v2_powers().values())
        self._options = scenario_pool.pick_six(
            powers,
            list(state.reaction_tags),
            option_rng,
            exclude_category=self._exclude_category(state),
        )

    # -- narration ----------------------------------------------------------

    def get_framing(self, state: CreationState) -> str:
        return self._vignette.get("framing", "") if self._vignette else ""

    def get_choices(self, state: CreationState) -> List[str]:
        lines: List[str] = []
        for p in self._options:
            label = V2_CATEGORY_LABELS.get(p.category, p.category.title())
            sub = getattr(p, "sub_category", "") or ""
            identity = getattr(p, "identity", "") or getattr(p, "description", "") or ""
            if sub:
                lines.append(f"[{label} / {sub}] {p.name} — {identity}")
            else:
                lines.append(f"[{label}] {p.name} — {identity}")
        return lines

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        return [{
            "key": "reaction",
            "prompt": "In a few sentences, tell me what you do in this moment.",
        }]

    # -- state writers ------------------------------------------------------

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        reaction = text_inputs.get("reaction", "").strip()
        tags = scenario_pool.extract_tags(reaction)
        vignette_id = self._vignette.get("id", "") if self._vignette else ""

        updated = factory.apply_scene_result(self.scene_id + "_text", {
            "scenario_reactions": {self._slot_key: reaction},
            "scenario_vignettes": {self._slot_key: vignette_id},
            "reaction_tags": tags,
        }, state, rng)

        # Recompute weighted options now that the reaction has expanded tags.
        option_rng = _random.Random(state.seed + self._slot * 211)
        powers = list(_get_v2_powers().values())
        self._options = scenario_pool.pick_six(
            powers,
            list(updated.reaction_tags),
            option_rng,
            exclude_category=self._exclude_category(updated),
        )
        return updated

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        if not self._options:
            return state
        idx = min(max(0, choice_index), len(self._options) - 1)
        chosen = self._options[idx]

        choice_data: Dict[str, Any] = {
            "powers": [{
                "power_id": chosen.id,
                "name": chosen.name,
                "category": chosen.category,
                "sub_category": getattr(chosen, "sub_category", ""),
                "tier": 3,
                "slot": self._slot_label,
                "playstyles": list(getattr(chosen, "playstyles", []) or []),
            }],
            "history": self._history_entries(chosen),
        }
        self._augment_scene_data(chosen, choice_data, state)
        return factory.apply_scene_result(self.scene_id, choice_data, state, rng)

    # -- subclass hooks -----------------------------------------------------

    def _history_entries(self, chosen: Any) -> List[Dict[str, Any]]:
        label = V2_CATEGORY_LABELS.get(chosen.category, chosen.category.title())
        return [{
            "timestamp": "T+0",
            "description": f"Manifestation ({self._slot_label}): {label} — {chosen.name}",
            "type": "session_zero",
        }]

    def _augment_scene_data(
        self,
        chosen: Any,
        choice_data: Dict[str, Any],
        state: CreationState,
    ) -> None:
        """Override to attach per-slot extras (tier ceiling, breakthroughs, etc)."""


class Scenario1Scenario(_ScenarioBase):
    """First cinematic danger vignette → primary power selection."""
    scene_id = "sz_v2_scenario1"
    _slot = 1
    _slot_key = "1"
    _slot_label = "anchor"

    def _augment_scene_data(
        self,
        chosen: Any,
        choice_data: Dict[str, Any],
        state: CreationState,
    ) -> None:
        choice_data["power_category_primary"] = chosen.category
        choice_data["tier"] = 3
        choice_data["tier_ceiling"] = 5
        choice_data["breakthroughs"] = [{
            "id": "breakthrough_0",
            "type": "manifestation",
            "description": f"Initial manifestation: {chosen.category} T3",
            "cost": "onset trauma",
        }]


class Scenario2Scenario(_ScenarioBase):
    """Second vignette → secondary power selection, primary category excluded."""
    scene_id = "sz_v2_scenario2"
    _slot = 2
    _slot_key = "2"
    _slot_label = "secondary"

    def _exclude_category(self, state: CreationState) -> str:
        return state.power_category_primary or ""

    def _history_entries(self, chosen: Any) -> List[Dict[str, Any]]:
        label = V2_CATEGORY_LABELS.get(chosen.category, chosen.category.title())
        return [{
            "timestamp": "T+0.1y",
            "description": f"Secondary manifestation: {label} — {chosen.name}",
            "type": "session_zero",
        }]

    def _augment_scene_data(
        self,
        chosen: Any,
        choice_data: Dict[str, Any],
        state: CreationState,
    ) -> None:
        choice_data["power_category_secondary"] = chosen.category


# ---------------------------------------------------------------------------
# Power Configuration — Cast Modes & Riders
# ---------------------------------------------------------------------------

class _PowerConfigBase(Scene):
    """Base for cast-mode and rider selection scenes.

    Each instance also asks a freeform narrative question whose answer
    seeds tags, small skill deltas, and (when the engine can infer one)
    a lightweight seeded NPC entry.  Overriders set _narrative_prompt
    and _narrative_skill on the subclass.
    """

    _slot: str = "anchor"  # "anchor" or "secondary"
    _config_type: str = "cast_mode"  # "cast_mode" or "rider"
    _narrative_prompt: str = ""
    _narrative_skill: str = "streetwise"

    def __init__(self) -> None:
        super().__init__()
        self._options: List[Dict[str, Any]] = []
        self._power_name: str = ""

    # -- power lookup -------------------------------------------------------

    def _find_power_entry(self, state: CreationState) -> Optional[Dict[str, Any]]:
        for p in state.powers:
            if p.get("slot") == self._slot:
                return p
        return None

    def _resolve_v2_power(self, state: CreationState) -> Optional[Any]:
        entry = self._find_power_entry(state)
        if not entry:
            return None
        pid = entry.get("power_id", "")
        return _get_v2_powers().get(pid)

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._options = []
        self._power_name = ""
        entry = self._find_power_entry(state)
        if not entry:
            return
        self._power_name = entry.get("name", "your power")
        v2_power = self._resolve_v2_power(state)
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

    # -- presentation -------------------------------------------------------

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

    # -- narrative prompt ---------------------------------------------------

    def needs_text_input(self) -> bool:
        return bool(self._narrative_prompt)

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        if not self._narrative_prompt:
            return []
        return [{"key": "narrative", "prompt": self._narrative_prompt}]

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        answer = text_inputs.get("narrative", "").strip()
        if not answer:
            return state
        tags = scenario_pool.extract_tags(answer)
        skill_grant = {self._narrative_skill: 1} if self._narrative_skill else {}
        return factory.apply_scene_result(self.scene_id + "_text", {
            "scenario_reactions": {self.scene_id: answer},
            "reaction_tags": tags,
            "skills": skill_grant,
            "history": [{
                "timestamp": "T+0",
                "description": f"{self._power_name} ({self._config_type}) — lore seed captured",
                "type": "session_zero",
            }],
        }, state, rng)

    # -- choice commit ------------------------------------------------------

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
    _narrative_prompt = (
        "Who was the first person to see you use it? "
        "What did they say, or not say?"
    )
    _narrative_skill = "streetwise"

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
    _narrative_prompt = (
        "What did using it the first time cost you? "
        "Pain, a wound, a sleepless week, a relationship — something."
    )
    _narrative_skill = "survival"

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
    _narrative_prompt = (
        "Who taught you — or who did you watch — to recognize this second "
        "capacity in yourself?"
    )
    _narrative_skill = "instruction"

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
    _narrative_prompt = (
        "What does this second ability refuse to do, no matter how hard "
        "you push? The thing it will not touch."
    )
    _narrative_skill = "investigation"

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
    """Return the 12 v2 scenarios in order."""
    return [
        IdentityScenario(),              #  0: name, age, occupation, self-description
        Scenario1Scenario(),             #  1: cinematic vignette → primary power
        Scenario2Scenario(),             #  2: second vignette → secondary power
        PrimaryCastModeScenario(),       #  3: primary cast mode (+ narrative)
        PrimaryRiderScenario(),          #  4: primary rider (+ narrative)
        SecondaryCastModeScenario(),     #  5: secondary cast mode (+ narrative)
        SecondaryRiderScenario(),        #  6: secondary rider (+ narrative)
        SurvivalScenario(),              #  7: months 1-3 (pooled, specific)
        LocationScenario(),              #  8: region
        RelationshipScenario(),          #  9: friends, family, foes
        FactionScenario(),               # 10: named faction representative
        VowScenario(),                   # 11: vows + settlement NPCs
    ]
