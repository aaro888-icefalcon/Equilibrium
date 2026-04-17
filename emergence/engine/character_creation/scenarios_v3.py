"""Session Zero v3 — 5 long-form scenes, biography-aware, threat-rich.

Scenes:
  0 OnsetAndBiographyScene   (Onset primer + life description + NPC seeds)
  1 AwakeningScene           (vignette + 10-power slate pick 2)
  2 PowersConfigScene        (cast + rider for both powers, mechanics verbatim)
  3 FirstYearScene           (region + survival + relationship web, bio-tie-aware)
  4 StandingAndVowsScene     (faction posture + 2-3 vows, threat accumulation)

Each scene exposes four optional hooks beyond the v2 Scene base:

  get_scenario_code(state) -> dict
      Structured facts the narrator weaves into framing: scene_intent,
      setting_details, archetype_pool, hidden_seeds, etc.

  get_known_npcs(state) -> List[dict]
      Biography tie-NPCs in scope for this scene (name, relation, status).
      The narrator casts them into archetype roles when appropriate.

  get_must_state_mechanics(state) -> List[str]
      Verbatim mechanic strings that MUST appear in narration (damage,
      range, action cost, pool cost).

  get_choice_groups(state) -> List[dict]
      Grouping metadata for multi-pick scenes: {label, start, count}
      slices into the flat `choices` list.

Scenes that reuse v2 pools (SURVIVAL_POOL, REGIONS, RELATIONSHIP_WEBS,
FACTION_DEMANDS, VOW_PACKAGES) import them from scenarios (v2) directly.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.session_zero import Scene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation import scenario_pool
from emergence.engine.sim.npc_generator import generate_npc
from emergence.engine.character_creation.scenarios import (
    _get_v2_powers,
    _occupation_by_hint,
    _parse_npc_seeds,
    V2_CATEGORY_LABELS,
    SURVIVAL_POOL,
    _filter_survival_pool,
    REGIONS,
    RELATIONSHIP_WEBS,
    REGION_FACTIONS,
    FACTION_DEMANDS,
    VOW_PACKAGES,
)


# ---------------------------------------------------------------------------
# Scene base with v3 hooks
# ---------------------------------------------------------------------------

class _V3Scene(Scene):
    """Scene base that adds the four payload-enrichment hooks.

    Subclasses override as needed. Defaults return empty containers.
    """

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        return {}

    def get_known_npcs(self, state: CreationState) -> List[Dict[str, Any]]:
        return []

    def get_must_state_mechanics(self, state: CreationState) -> List[str]:
        return []

    def get_choice_groups(self, state: CreationState) -> List[Dict[str, Any]]:
        return []


# ---------------------------------------------------------------------------
# Scene 1 — Onset and Biography
# ---------------------------------------------------------------------------

class OnsetAndBiographyScene(_V3Scene):
    """Merges the v2 IntroScene + LifeDescriptionScene.

    Text inputs: name, age, description, npc_seeds (JSON).
    No choices — advance after text apply.
    """

    scene_id = "sz_v3_onset_bio"
    register = "standard"

    def get_framing(self, state: CreationState) -> str:
        # Short orientation only. The narrator composes the full 400-600 word
        # framing from scenario_code; this string is a fallback for mock runs.
        return (
            "One year ago, the Onset ended most of the world. You lived. "
            "Tell me who you were."
        )

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        return {
            "scene_intent": "Establish who the character was pre-Onset and who their people were.",
            "beat_target_words": [400, 600],
            "setting_details": {
                "event": "Onset — one year ago. Engines stopped. Hospitals went dark. Food spoiled. Most people died in six weeks.",
                "survivor_condition": "Some who lived woke up carrying abilities. No agreed name. Survivors mostly still call themselves people.",
                "elapsed": "One year has passed.",
                "regions": [
                    "New York City (Tower Lords, Queens Commonage)",
                    "Northern New Jersey (Iron Crown, Staten Citadel)",
                    "Hudson Valley (Catskill Throne, Yonkers Compact)",
                    "Central New Jersey (League townships, Rutgers farmland)",
                    "Philadelphia (Bourse copper economy)",
                    "Lehigh Valley (coal principalities, Sun-Worn farms)",
                    "Delmarva (harvest demesnes, granary)",
                ],
            },
            "invitation": "Ask for their name, age at Onset (16-65), what they did, who their people were, where they lived.",
            "hidden_seeds": [
                "The description will shape which powers surface in the next scene.",
                "Named people become real NPCs in the world.",
            ],
        }

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        return [
            {"key": "name", "prompt": "Your name."},
            {"key": "age", "prompt": "Your age on the day it happened (16-65)."},
            {
                "key": "description",
                "prompt": (
                    "Who you were.  Write as much as feels true — your work, "
                    "your people, where you lived, what you did with your time."
                ),
            },
            {
                "key": "npc_seeds",
                "prompt": (
                    "Optional: JSON array of named relationships pulled from "
                    "your description.  Each entry: "
                    "{name, relation, location, descriptor, status}.  "
                    "Leave empty to skip."
                ),
            },
        ]

    def get_choices(self, state: CreationState) -> List[str]:
        return []

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
        domain = scenario_pool.extract_domain(description)
        occupation_hint = domain["occupation_hint"] or ""
        occupation_row = _occupation_by_hint(occupation_hint)

        merged_skills: Dict[str, int] = dict(occupation_row["skills"])
        for skill, level in domain["skills"].items():
            merged_skills[skill] = merged_skills.get(skill, 0) + level

        merged_attrs: Dict[str, int] = dict(occupation_row["attribute_deltas"])
        for attr, delta in domain["attribute_deltas"].items():
            merged_attrs[attr] = merged_attrs.get(attr, 0) + delta

        npc_seeds = _parse_npc_seeds(text_inputs.get("npc_seeds", ""))

        return factory.apply_scene_result(self.scene_id, {
            "name": name,
            "age_at_onset": age,
            "self_description": description,
            "reaction_tags": tags,
            "attribute_deltas": merged_attrs,
            "skills": merged_skills,
            "resources": dict(occupation_row.get("resources", {})),
            "heat": dict(occupation_row.get("heat", {})),
            "narrative_tag": occupation_row["narrative_tag"],
            "occupation": occupation_row["narrative_tag"],
            "npc_seeds": npc_seeds,
            "history": [
                {
                    "timestamp": "T-1y",
                    "description": "Onset: most of the world ended.",
                    "type": "session_zero",
                },
                {
                    "timestamp": "T-1y",
                    "description": (
                        f"Pre-onset: {occupation_row['display'].split(' — ')[0]}"
                    ),
                    "type": "session_zero",
                },
            ],
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene 2 — Awakening (vignette + 10-power slate, pick 2)
# ---------------------------------------------------------------------------

class AwakeningScene(_V3Scene):
    """Merges v2 ActionScenarioScene + PowerSlateScene.

    Text input: reaction (one vignette framing from the action pool).
    Choices: pick 2 from a 10-power slate, comma-separated via apply_multi.
    """

    scene_id = "sz_v3_awakening"
    register = "intimate"

    _SLATE_SIZE = 10

    def __init__(self) -> None:
        super().__init__()
        self._vignette: Dict[str, Any] = {}
        self._options: List[Any] = []

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        vignette_rng = _random.Random(state.seed + 101)
        self._vignette = scenario_pool.select_action_vignette(vignette_rng)
        # Compute slate from whatever tags are on state (empty pre-text).
        self._options = self._compute_slate(state)

    def _compute_slate(self, state: CreationState) -> List[Any]:
        option_rng = _random.Random(state.seed + 317)
        desc_tags = scenario_pool.extract_description_tags(
            state.self_description or "",
        )
        reaction_tags = list(state.reaction_tags)
        powers = list(_get_v2_powers().values())
        return scenario_pool.pick_ten(
            powers, desc_tags, reaction_tags, option_rng,
        )

    def get_framing(self, state: CreationState) -> str:
        # Short orientation fallback; narrator uses scenario_code for the
        # full vignette rendering.
        return self._vignette.get("framing", "") if self._vignette else ""

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        slate = self._current_slate(state)
        power_options = []
        for i, p in enumerate(slate):
            label = V2_CATEGORY_LABELS.get(p.category, p.category.title())
            identity = (
                getattr(p, "identity", "")
                or getattr(p, "description", "")
                or ""
            )
            power_options.append({
                "index": i,
                "name": p.name,
                "category": p.category,
                "category_label": label,
                "sub_category": getattr(p, "sub_category", ""),
                "identity": identity,
                "playstyles": list(getattr(p, "playstyles", []) or []),
            })
        return {
            "scene_intent": "First manifestation vignette + player picks two powers.",
            "beat_target_words": [400, 600],
            "vignette_id": self._vignette.get("id", "") if self._vignette else "",
            "vignette_framing": self._vignette.get("framing", "") if self._vignette else "",
            "power_slate": power_options,
            "invitation": (
                "After the player writes their reaction, present all 10 "
                "power options grouped by category with identity snippets. "
                "Player picks 2 indices (comma-separated)."
            ),
            "hidden_seeds": [
                "Both picks may come from the same category — no exclusion.",
                "Powers enter at tier 3 with tier ceiling 5.",
            ],
        }

    def get_choices(self, state: CreationState) -> List[str]:
        slate = self._current_slate(state)
        lines: List[str] = []
        for p in slate:
            label = V2_CATEGORY_LABELS.get(p.category, p.category.title())
            sub = getattr(p, "sub_category", "") or ""
            identity = (
                getattr(p, "identity", "")
                or getattr(p, "description", "")
                or ""
            )
            if sub:
                lines.append(f"[{label} / {sub}] {p.name} — {identity}")
            else:
                lines.append(f"[{label}] {p.name} — {identity}")
        return lines

    def _current_slate(self, state: CreationState) -> List[Any]:
        if state.pending_slate and state.pending_slate_scene == self.scene_id:
            powers = _get_v2_powers()
            resolved = [
                powers.get(entry.get("power_id"))
                for entry in state.pending_slate
            ]
            return [p for p in resolved if p is not None]
        return list(self._options)

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        return [{
            "key": "reaction",
            "prompt": (
                "Your reaction in this moment.  A few sentences — what you "
                "do in the next half-second, in your own words."
            ),
        }]

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        reaction = text_inputs.get("reaction", "").strip()
        updated = state
        vignette_id = self._vignette.get("id", "") if self._vignette else ""

        if reaction:
            tags = scenario_pool.extract_tags(reaction)
            updated = factory.apply_scene_result(self.scene_id + "_text", {
                "scenario_reactions": {"action": reaction},
                "scenario_vignettes": {"action": vignette_id},
                "reaction_tags": tags,
                "history": [{
                    "timestamp": "T+0",
                    "description": "Onset: first manifestation beat.",
                    "type": "session_zero",
                }],
            }, updated, rng)

        slate = self._compute_slate(updated)
        self._options = slate
        slate_payload = [
            {
                "power_id": p.id,
                "name": p.name,
                "category": p.category,
                "sub_category": getattr(p, "sub_category", ""),
            }
            for p in slate
        ]
        return factory.apply_scene_result(self.scene_id + "_slate", {
            "pending_slate": slate_payload,
            "pending_slate_scene": self.scene_id,
        }, updated, rng)

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        slate = self._current_slate(state)
        if not slate:
            return state
        first_idx = min(max(0, choice_index), len(slate) - 1)
        second_idx = (first_idx + 1) % len(slate)
        if second_idx == first_idx:
            second_idx = (first_idx + 2) % len(slate)
        return self.apply_multi([first_idx, second_idx], state, factory, rng)

    def apply_multi(
        self,
        choice_indices: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        slate = self._current_slate(state)
        if not slate:
            return state

        valid: List[int] = []
        for idx in choice_indices:
            try:
                i = int(idx)
            except (TypeError, ValueError):
                continue
            i = min(max(0, i), len(slate) - 1)
            if i not in valid:
                valid.append(i)
            if len(valid) == 2:
                break
        if len(valid) == 0:
            valid = [0, 1 if len(slate) > 1 else 0]
        elif len(valid) == 1:
            filler = (valid[0] + 1) % len(slate)
            if filler == valid[0]:
                filler = (valid[0] + 2) % len(slate)
            valid.append(filler)

        primary = slate[valid[0]]
        secondary = slate[valid[1]]

        power_rows = [
            {
                "power_id": primary.id,
                "name": primary.name,
                "category": primary.category,
                "sub_category": getattr(primary, "sub_category", ""),
                "tier": 3,
                "slot": "primary",
                "playstyles": list(getattr(primary, "playstyles", []) or []),
            },
            {
                "power_id": secondary.id,
                "name": secondary.name,
                "category": secondary.category,
                "sub_category": getattr(secondary, "sub_category", ""),
                "tier": 3,
                "slot": "secondary",
                "playstyles": list(getattr(secondary, "playstyles", []) or []),
            },
        ]

        p_label = V2_CATEGORY_LABELS.get(
            primary.category, primary.category.title(),
        )
        s_label = V2_CATEGORY_LABELS.get(
            secondary.category, secondary.category.title(),
        )

        return factory.apply_scene_result(self.scene_id, {
            "powers": power_rows,
            "power_category_primary": primary.category,
            "power_category_secondary": secondary.category,
            "tier": 3,
            "tier_ceiling": 5,
            "breakthroughs": [{
                "id": "breakthrough_0",
                "type": "manifestation",
                "description": (
                    f"Initial manifestation: {primary.category} + "
                    f"{secondary.category} at T3"
                ),
                "cost": "onset trauma",
            }],
            "history": [
                {
                    "timestamp": "T+0",
                    "description": (
                        f"Manifestation (primary): {p_label} — {primary.name}"
                    ),
                    "type": "session_zero",
                },
                {
                    "timestamp": "T+0",
                    "description": (
                        f"Manifestation (secondary): {s_label} — {secondary.name}"
                    ),
                    "type": "session_zero",
                },
            ],
            "pending_slate": [],
            "pending_slate_scene": "",
        }, state, rng)


# ---------------------------------------------------------------------------
# Scene 3 — Powers Take Shape (cast + rider for both, mechanics verbatim)
# ---------------------------------------------------------------------------

def _cast_mode_mechanic_string(cm: Any) -> str:
    """Build a verbatim mechanic string for a cast mode that the narrator
    MUST include in prose. Format: 'name — effect (range: X, duration: Y,
    pool N, ACT action)'. All fields from CastMode."""
    name = getattr(cm, "slot_id", "") or "mode"
    desc = (getattr(cm, "effect_description", "") or "").strip()
    rng_band = getattr(cm, "range_band", "?")
    duration = getattr(cm, "duration", "?")
    pool = getattr(cm, "pool_cost", 0)
    action = getattr(cm, "action_cost", "?")
    scope = getattr(cm, "targeting_scope", "?")
    return (
        f"{name} — {desc} "
        f"(range: {rng_band}, duration: {duration}, "
        f"targeting: {scope}, pool cost: {pool}, {action} action)"
    )


def _rider_mechanic_string(rs: Any) -> str:
    """Verbatim rider mechanic string."""
    name = getattr(rs, "slot_id", "") or "rider"
    rtype = getattr(rs, "rider_type", "")
    desc = (getattr(rs, "effect_description", "") or "").strip()
    pool = getattr(rs, "pool_cost", 0)
    cost = f"pool cost: {pool}" if pool else "passive"
    combo = getattr(rs, "combo_note", "") or ""
    base = f"{name} [{rtype}] — {desc} ({cost})"
    if combo:
        base = f"{base} — combo: {combo}"
    return base


class PowersConfigScene(_V3Scene):
    """Configures cast_mode + rider for BOTH primary and secondary powers.

    The player makes 4 picks in one step, passed as four comma-separated
    indices in positional order: [primary_cast, primary_rider,
    secondary_cast, secondary_rider].

    Each group's size comes from the resolved V2 power's cast_modes /
    rider_slots (typically 3 each, but we read what's available).

    Mechanics — damage, range, duration, pool cost, action cost — are
    surfaced verbatim in `must_state_mechanics` so the narrator includes
    them in the framing prose. This replaces the v2 flow's four separate
    scenes, each without mechanics in the prose.

    Also collects 2 narrative text inputs: one per power, free-form, to
    feed reaction tags + a small skill grant.
    """

    scene_id = "sz_v3_powers_config"
    register = "intimate"

    def __init__(self) -> None:
        super().__init__()
        self._primary_entry: Dict[str, Any] = {}
        self._secondary_entry: Dict[str, Any] = {}
        self._primary_power: Optional[Any] = None
        self._secondary_power: Optional[Any] = None
        self._primary_casts: List[Any] = []
        self._primary_riders: List[Any] = []
        self._secondary_casts: List[Any] = []
        self._secondary_riders: List[Any] = []

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _find_slot(self, state: CreationState, slot: str) -> Dict[str, Any]:
        for p in state.powers:
            if p.get("slot") == slot:
                return p
        return {}

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        self._primary_entry = self._find_slot(state, "primary")
        self._secondary_entry = self._find_slot(state, "secondary")
        powers = _get_v2_powers()
        self._primary_power = powers.get(self._primary_entry.get("power_id", ""))
        self._secondary_power = powers.get(self._secondary_entry.get("power_id", ""))

        self._primary_casts = list(self._primary_power.cast_modes) if self._primary_power else []
        self._primary_riders = list(self._primary_power.rider_slots) if self._primary_power else []
        self._secondary_casts = list(self._secondary_power.cast_modes) if self._secondary_power else []
        self._secondary_riders = list(self._secondary_power.rider_slots) if self._secondary_power else []

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    def get_framing(self, state: CreationState) -> str:
        pname = self._primary_entry.get("name", "your first ability")
        sname = self._secondary_entry.get("name", "your second")
        return (
            f"The first weeks you learned what was under your skin. "
            f"{pname} and {sname} — how they manifest, and the signature "
            f"each one leaves behind."
        )

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        def _pack_casts(casts: List[Any]) -> List[Dict[str, Any]]:
            return [
                {
                    "slot_id": getattr(cm, "slot_id", ""),
                    "effect_description": getattr(cm, "effect_description", ""),
                    "range_band": getattr(cm, "range_band", ""),
                    "duration": getattr(cm, "duration", ""),
                    "targeting_scope": getattr(cm, "targeting_scope", ""),
                    "pool_cost": getattr(cm, "pool_cost", 0),
                    "action_cost": getattr(cm, "action_cost", ""),
                    "playstyles": list(getattr(cm, "playstyles", []) or []),
                    "hook": getattr(cm, "hook", ""),
                }
                for cm in casts
            ]

        def _pack_riders(riders: List[Any]) -> List[Dict[str, Any]]:
            return [
                {
                    "slot_id": getattr(rs, "slot_id", ""),
                    "rider_type": getattr(rs, "rider_type", ""),
                    "effect_description": getattr(rs, "effect_description", ""),
                    "pool_cost": getattr(rs, "pool_cost", 0),
                    "combo_note": getattr(rs, "combo_note", ""),
                    "playstyles": list(getattr(rs, "playstyles", []) or []),
                }
                for rs in riders
            ]

        return {
            "scene_intent": (
                "Configure cast mode + rider for both powers. Mechanics MUST be "
                "stated verbatim in the narration."
            ),
            "beat_target_words": [400, 600],
            "primary": {
                "name": self._primary_entry.get("name", ""),
                "category": self._primary_entry.get("category", ""),
                "cast_modes": _pack_casts(self._primary_casts),
                "riders": _pack_riders(self._primary_riders),
            },
            "secondary": {
                "name": self._secondary_entry.get("name", ""),
                "category": self._secondary_entry.get("category", ""),
                "cast_modes": _pack_casts(self._secondary_casts),
                "riders": _pack_riders(self._secondary_riders),
            },
            "invitation": (
                "Narrate a bridge from Awakening through the first weeks of "
                "learning the powers. Present each choice group (primary cast, "
                "primary rider, secondary cast, secondary rider) with all "
                "options and their verbatim mechanics. Player passes 4 "
                "comma-separated indices: [primary_cast, primary_rider, "
                "secondary_cast, secondary_rider]."
            ),
        }

    def get_must_state_mechanics(self, state: CreationState) -> List[str]:
        strings: List[str] = []
        pname = self._primary_entry.get("name", "primary")
        sname = self._secondary_entry.get("name", "secondary")
        for cm in self._primary_casts:
            strings.append(f"{pname} cast — {_cast_mode_mechanic_string(cm)}")
        for rs in self._primary_riders:
            strings.append(f"{pname} rider — {_rider_mechanic_string(rs)}")
        for cm in self._secondary_casts:
            strings.append(f"{sname} cast — {_cast_mode_mechanic_string(cm)}")
        for rs in self._secondary_riders:
            strings.append(f"{sname} rider — {_rider_mechanic_string(rs)}")
        return strings

    def get_choice_groups(self, state: CreationState) -> List[Dict[str, Any]]:
        cursor = 0
        groups: List[Dict[str, Any]] = []
        for label, items in (
            (f"{self._primary_entry.get('name', 'primary')} — cast mode", self._primary_casts),
            (f"{self._primary_entry.get('name', 'primary')} — rider", self._primary_riders),
            (f"{self._secondary_entry.get('name', 'secondary')} — cast mode", self._secondary_casts),
            (f"{self._secondary_entry.get('name', 'secondary')} — rider", self._secondary_riders),
        ):
            groups.append({
                "label": label,
                "start": cursor,
                "count": len(items),
            })
            cursor += len(items)
        return groups

    def get_choices(self, state: CreationState) -> List[str]:
        """Flat list across all 4 groups. The choice_groups metadata tells
        the narrator which range belongs to which pick."""
        pname = self._primary_entry.get("name", "primary")
        sname = self._secondary_entry.get("name", "secondary")
        out: List[str] = []
        for cm in self._primary_casts:
            out.append(f"[{pname} cast] {_cast_mode_mechanic_string(cm)}")
        for rs in self._primary_riders:
            out.append(f"[{pname} rider] {_rider_mechanic_string(rs)}")
        for cm in self._secondary_casts:
            out.append(f"[{sname} cast] {_cast_mode_mechanic_string(cm)}")
        for rs in self._secondary_riders:
            out.append(f"[{sname} rider] {_rider_mechanic_string(rs)}")
        return out

    # ------------------------------------------------------------------
    # Text inputs (2 narrative beats, one per power)
    # ------------------------------------------------------------------

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        pname = self._primary_entry.get("name", "your primary ability")
        sname = self._secondary_entry.get("name", "your secondary ability")
        return [
            {
                "key": "primary_beat",
                "prompt": (
                    f"A short beat — who was the first person to see you use "
                    f"{pname}, and what it cost you the first time."
                ),
            },
            {
                "key": "secondary_beat",
                "prompt": (
                    f"A short beat — when {sname} first surfaced, and what "
                    f"it refused to do no matter how hard you pushed."
                ),
            },
        ]

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        primary_beat = text_inputs.get("primary_beat", "").strip()
        secondary_beat = text_inputs.get("secondary_beat", "").strip()

        tags: List[str] = []
        if primary_beat:
            tags.extend(scenario_pool.extract_tags(primary_beat))
        if secondary_beat:
            tags.extend(scenario_pool.extract_tags(secondary_beat))

        return factory.apply_scene_result(self.scene_id + "_text", {
            "scenario_reactions": {
                "primary_beat": primary_beat,
                "secondary_beat": secondary_beat,
            },
            "reaction_tags": tags,
            "skills": {"streetwise": 1, "survival": 1},
            "history": [{
                "timestamp": "T+0",
                "description": "Powers configured — narrative beats captured.",
                "type": "session_zero",
            }],
        }, state, rng)

    # ------------------------------------------------------------------
    # Multi-pick apply
    # ------------------------------------------------------------------

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        # Fallback: treat the single index as all four picks being index 0.
        return self.apply_multi([choice_index, 0, 0, 0], state, factory, rng)

    def apply_multi(
        self,
        choice_indices: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        # Pad / truncate to exactly 4 picks.
        picks = [int(i) if str(i).strip().isdigit() else 0 for i in choice_indices[:4]]
        while len(picks) < 4:
            picks.append(0)
        pc_idx, pr_idx, sc_idx, sr_idx = picks

        def _safe(lst: List[Any], idx: int) -> Optional[Any]:
            if not lst:
                return None
            return lst[min(max(0, idx), len(lst) - 1)]

        p_cast = _safe(self._primary_casts, pc_idx)
        p_rider = _safe(self._primary_riders, pr_idx)
        s_cast = _safe(self._secondary_casts, sc_idx)
        s_rider = _safe(self._secondary_riders, sr_idx)

        # Write picks onto the powers entries in-place. These dicts are the
        # SAME objects stored in state.powers (reference, not copy), so the
        # write persists.
        if self._primary_entry and p_cast is not None:
            self._primary_entry["selected_cast_mode"] = _cast_to_dict(p_cast)
        if self._primary_entry and p_rider is not None:
            self._primary_entry["selected_rider"] = _rider_to_dict(p_rider)
        if self._secondary_entry and s_cast is not None:
            self._secondary_entry["selected_cast_mode"] = _cast_to_dict(s_cast)
        if self._secondary_entry and s_rider is not None:
            self._secondary_entry["selected_rider"] = _rider_to_dict(s_rider)

        history_desc = []
        if p_cast:
            history_desc.append(
                f"{self._primary_entry.get('name','primary')} cast: {getattr(p_cast, 'slot_id', '')}"
            )
        if p_rider:
            history_desc.append(
                f"{self._primary_entry.get('name','primary')} rider: {getattr(p_rider, 'slot_id', '')}"
            )
        if s_cast:
            history_desc.append(
                f"{self._secondary_entry.get('name','secondary')} cast: {getattr(s_cast, 'slot_id', '')}"
            )
        if s_rider:
            history_desc.append(
                f"{self._secondary_entry.get('name','secondary')} rider: {getattr(s_rider, 'slot_id', '')}"
            )

        return factory.apply_scene_result(self.scene_id, {
            "history": [{
                "timestamp": "T+0.05y",
                "description": "Powers configured: " + "; ".join(history_desc),
                "type": "session_zero",
            }],
        }, state, rng)


def _cast_to_dict(cm: Any) -> Dict[str, Any]:
    """Serialize a CastMode for storage on the power entry."""
    return {
        "slot_id": getattr(cm, "slot_id", ""),
        "action_cost": getattr(cm, "action_cost", ""),
        "range_band": getattr(cm, "range_band", ""),
        "duration": getattr(cm, "duration", ""),
        "effect_description": getattr(cm, "effect_description", ""),
        "effect_parameters": dict(getattr(cm, "effect_parameters", {}) or {}),
        "targeting_scope": getattr(cm, "targeting_scope", ""),
        "pool_cost": getattr(cm, "pool_cost", 0),
    }


def _rider_to_dict(rs: Any) -> Dict[str, Any]:
    """Serialize a RiderSpec for storage on the power entry."""
    return {
        "slot_id": getattr(rs, "slot_id", ""),
        "rider_type": getattr(rs, "rider_type", ""),
        "effect_description": getattr(rs, "effect_description", ""),
        "effect_parameters": dict(getattr(rs, "effect_parameters", {}) or {}),
        "pool_cost": getattr(rs, "pool_cost", 0),
        "combo_note": getattr(rs, "combo_note", ""),
    }


# ---------------------------------------------------------------------------
# Scene 4 — The First Year (region + survival + relationships; bio-aware)
# ---------------------------------------------------------------------------

# Archetype → relation keywords. Used to filter biography tie-NPCs down to
# the ones that could plausibly fill a given pool role (mentor, partner,
# companion, etc.).
_TIE_ARCHETYPE_PREFERENCE: Dict[str, List[str]] = {
    "mentor": ["mentor", "teacher", "attending", "senior"],
    "grateful_survivor": [],
    "partner": ["partner", "spouse", "wife", "husband", "lover"],
    "companion": ["friend", "coworker", "colleague", "resident"],
    "leader": ["boss", "chief", "foreman", "captain"],
    "employer": ["boss", "manager", "owner"],
    "commander": ["officer", "captain", "sergeant"],
    "farmer": ["farmer"],
    "hunter": ["hunter", "tracker"],
    "technician": ["engineer", "technician", "electrician"],
    "community_leader": ["teacher", "principal", "pastor", "organizer"],
    "family": ["brother", "sister", "mother", "father", "son", "daughter", "cousin", "aunt", "uncle"],
}


def _tie_npc_matches_archetype(seed: Dict[str, Any], archetype: str) -> bool:
    """Loose match: a tie-seed is a candidate for archetype if the relation
    substring matches one of the archetype's preference keywords, OR the
    archetype is 'companion' (a broad default)."""
    prefs = _TIE_ARCHETYPE_PREFERENCE.get(archetype, [])
    if not prefs:
        return False
    relation = (seed.get("relation", "") or "").lower()
    return any(pref in relation for pref in prefs)


def _select_tie_or_generate(
    archetype: Optional[str],
    available_seeds: List[Dict[str, Any]],
    rng: _random.Random,
) -> Dict[str, str]:
    """Prefer a biography tie-NPC over a generated NPC when archetype fits.

    Returns {npc_id, name, from_bio}. If no tie matches, generates a fresh
    NPC and returns its id+name with from_bio=False.
    """
    if archetype:
        for seed in available_seeds:
            if seed.get("_used"):
                continue
            if _tie_npc_matches_archetype(seed, archetype):
                seed["_used"] = True
                name = seed["name"]
                import re as _re
                slug = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tie"
                npc_id = f"npc-tie-{slug}-{seed.get('seed_index', 0):02d}"
                return {"npc_id": npc_id, "name": name, "from_bio": True}
        # No tie match; fall through to generate.
    npc = generate_npc(archetype or "companion", {}, rng)
    return {
        "npc_id": getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}"),
        "name": getattr(npc, "display_name", "someone"),
        "from_bio": False,
    }


class FirstYearScene(_V3Scene):
    """Region pick + survival scenario + relationship web, all in one step.

    Player passes 3 comma-separated indices: [region, survival, relationship].

    Region is applied first so survival respects the region filter. Survival
    and relationship NPC roles prefer biography tie-NPCs when relations fit.
    """

    scene_id = "sz_v3_first_year"
    register = "standard"

    _SURVIVAL_PRESENT = 5

    def __init__(self) -> None:
        super().__init__()
        self._eligible_survival: List[Dict[str, Any]] = []
        self._presented_survival: List[Dict[str, Any]] = []
        self._presented_regions: List[Dict[str, Any]] = REGIONS
        self._presented_webs: List[Dict[str, Any]] = RELATIONSHIP_WEBS

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        # Pre-filter survival for the player's current region guess (may be
        # unset pre-apply). Since region is chosen here, default to no
        # region filter; apply_multi reruns the filter post-region.
        self._eligible_survival = list(SURVIVAL_POOL)
        if len(self._eligible_survival) <= self._SURVIVAL_PRESENT:
            self._presented_survival = list(self._eligible_survival)
        else:
            self._presented_survival = rng.sample(
                self._eligible_survival, self._SURVIVAL_PRESENT,
            )

    def get_framing(self, state: CreationState) -> str:
        return (
            "The first year. Where you landed, what you did to stay alive, "
            "and who stood beside you when the dying slowed."
        )

    def get_known_npcs(self, state: CreationState) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for seed in state.npc_seeds:
            if (seed.get("status") or "").lower() in {"dead"}:
                continue
            out.append({
                "name": seed.get("name", ""),
                "relation": seed.get("relation", ""),
                "location": seed.get("location", ""),
                "descriptor": seed.get("descriptor", ""),
                "status": seed.get("status", "alive"),
            })
        return out

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        return {
            "scene_intent": (
                "Through-line covering months 1-12: what the character did, "
                "where they ended up, who stayed close. Use biography ties "
                "when relations fit archetype roles."
            ),
            "beat_target_words": [500, 700],
            "regions_available": [
                {"index": i, "display": r["display"], "region": r["region"]}
                for i, r in enumerate(self._presented_regions)
            ],
            "survival_scenarios": [
                {
                    "index": i,
                    "id": s["id"],
                    "display": s["display"],
                    "framing_hint": s["framing_hint"],
                    "npc_archetype": s.get("npc_archetype"),
                    "narrative_tag": s["narrative_tag"],
                }
                for i, s in enumerate(self._presented_survival)
            ],
            "relationship_webs": [
                {"index": i, "display": w["display"]}
                for i, w in enumerate(self._presented_webs)
            ],
            "invitation": (
                "Present 3 choice groups (region, survival scenario, "
                "relationship web) with biography ties weaved into survival "
                "and relationship prose where archetype matches. Player "
                "passes 3 comma-separated indices: [region, survival, "
                "relationships]."
            ),
            "hidden_seeds": [
                "Taking-from-family and power-enforcer scenarios create threats.",
                "Relationship webs with rivals/enemies also create threats.",
            ],
        }

    def get_choice_groups(self, state: CreationState) -> List[Dict[str, Any]]:
        regions_count = len(self._presented_regions)
        survival_count = len(self._presented_survival)
        webs_count = len(self._presented_webs)
        return [
            {"label": "Region", "start": 0, "count": regions_count},
            {"label": "Survival", "start": regions_count, "count": survival_count},
            {
                "label": "Relationships",
                "start": regions_count + survival_count,
                "count": webs_count,
            },
        ]

    def get_choices(self, state: CreationState) -> List[str]:
        out: List[str] = []
        for r in self._presented_regions:
            out.append(f"[Region] {r['display']}")
        for s in self._presented_survival:
            out.append(f"[Survival] {s['display']}")
        for w in self._presented_webs:
            out.append(f"[Relationships] {w['display']}")
        return out

    # ------------------------------------------------------------------
    # Multi-pick apply
    # ------------------------------------------------------------------

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        return self.apply_multi([choice_index, 0, 0], state, factory, rng)

    def apply_multi(
        self,
        choice_indices: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        picks = [int(i) if str(i).strip().isdigit() else 0 for i in choice_indices[:3]]
        while len(picks) < 3:
            picks.append(0)
        r_idx, s_idx, w_idx = picks

        # 1) Region first — survival filter needs it.
        r_idx = min(max(0, r_idx), len(self._presented_regions) - 1)
        region = self._presented_regions[r_idx]
        state = factory.apply_scene_result(self.scene_id + "_region", {
            "region": region["region"],
            "location": region["location"],
            "history": [{
                "timestamp": "T+0.2y",
                "description": f"Settled in: {region['display'].split(' — ')[0]}",
                "type": "session_zero",
            }],
        }, state, rng)

        # 2) Survival — re-filter by region and map the presented index
        #    into the filtered list.
        filtered = _filter_survival_pool(SURVIVAL_POOL, state)
        if filtered:
            # Prefer the presented pick if it survived the filter; else wrap.
            chosen_scenario = self._presented_survival[
                min(max(0, s_idx), len(self._presented_survival) - 1)
            ] if self._presented_survival else filtered[0]
            if chosen_scenario not in filtered:
                chosen_scenario = filtered[min(max(0, s_idx), len(filtered) - 1)]
        else:
            chosen_scenario = (
                self._presented_survival[
                    min(max(0, s_idx), len(self._presented_survival) - 1)
                ]
                if self._presented_survival
                else None
            )

        available_seeds = [dict(s) for s in state.npc_seeds]
        state = self._apply_survival(chosen_scenario, available_seeds, state, factory, rng)

        # 3) Relationship web — prefer bio ties for matching archetypes.
        w_idx = min(max(0, w_idx), len(self._presented_webs) - 1)
        web = self._presented_webs[w_idx]
        state = self._apply_relationship_web(web, available_seeds, state, factory, rng)

        return state

    def _apply_survival(
        self,
        s: Optional[Dict[str, Any]],
        available_seeds: List[Dict[str, Any]],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        if not s:
            return state

        choice_data: Dict[str, Any] = {
            "attribute_deltas": dict(s["attribute_deltas"]),
            "skills": dict(s["skills"]),
            "resources": dict(s.get("resources", {})),
            "heat": dict(s.get("heat", {})),
            "narrative_tag": s["narrative_tag"],
            "history": [{
                "timestamp": "T+0.1y",
                "description": f"First months: {s['display']}",
                "type": "session_zero",
            }],
        }

        archetype = s.get("npc_archetype")
        if archetype:
            resolved = _select_tie_or_generate(archetype, available_seeds, rng)
            npc_id = resolved["npc_id"]
            npc_name = resolved["name"]
            standing = s["npc_standing"]
            display = s["display"].replace("{npc_name}", npc_name).replace(
                "{npc_id}", npc_id,
            )

            choice_data["relationship"] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": standing,
                "current_state": "alive_present",
                "trust": max(0, standing),
                "archetype": archetype,
            }
            # Only add a generated NPC entry if this NPC wasn't already a
            # biography tie (those get materialized by step_scene_finalize).
            if not resolved["from_bio"]:
                choice_data["generated_npcs"] = [{
                    "npc_id": npc_id,
                    "display_name": npc_name,
                    "scene_id": self.scene_id,
                    "role": archetype,
                    "standing": standing,
                    "hooks": [
                        s["goal"]["description"].replace(
                            "{npc_name}", npc_name,
                        ).replace("{npc_id}", npc_id)
                    ] if s.get("goal") else [],
                }]

            if s.get("goal"):
                goal = dict(s["goal"])
                goal["id"] = goal["id"].replace(
                    "{npc_name}", npc_name,
                ).replace("{npc_id}", npc_id)
                goal["description"] = goal["description"].replace(
                    "{npc_name}", npc_name,
                ).replace("{npc_id}", npc_id)
                goal.setdefault("progress", 0)
                choice_data["goals"] = [goal]

            # Threat accumulation: negative-standing survival scenarios push
            # a threat.
            if standing <= -2:
                choice_data["threats"] = [{
                    "npc_id": npc_id,
                    "name": npc_name,
                    "standing": standing,
                    "source": f"survival:{s['id']}",
                    "summary": display,
                }]

        return factory.apply_scene_result(
            self.scene_id + "_survival", choice_data, state, rng,
        )

    def _apply_relationship_web(
        self,
        web: Dict[str, Any],
        available_seeds: List[Dict[str, Any]],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Build the relationship web, casting biography ties into roles
        where relations fit, and emitting threats for negative-standing
        entries."""
        relationships_data: Dict[str, Dict[str, Any]] = {}
        history_entries: List[Dict[str, Any]] = []
        threats: List[Dict[str, Any]] = []
        generated: List[Dict[str, Any]] = []

        for spec in web["npcs"]:
            archetype = spec["archetype"]
            standing = spec["standing"]
            role = spec["role"]
            state_tag = spec["state"]
            resolved = _select_tie_or_generate(archetype, available_seeds, rng)
            npc_id = resolved["npc_id"]
            npc_name = resolved["name"]

            relationships_data[npc_id] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": standing,
                "current_state": state_tag,
                "trust": max(0, standing),
                "archetype": archetype,
            }
            if not resolved["from_bio"]:
                generated.append({
                    "npc_id": npc_id,
                    "display_name": npc_name,
                    "scene_id": self.scene_id,
                    "role": archetype,
                    "standing": standing,
                    "hooks": [],
                })
            history_entries.append({
                "timestamp": "T+0.5y",
                "description": f"Relationship: {npc_name} ({archetype}, {role})",
                "type": "session_zero",
            })

            if standing <= -2:
                threats.append({
                    "npc_id": npc_id,
                    "name": npc_name,
                    "standing": standing,
                    "source": f"relationship_web:{archetype}",
                    "summary": f"{npc_name} ({archetype}) — {role}",
                })

        choice_data: Dict[str, Any] = {
            "goals": list(web["goals"]),
            "history": history_entries,
            "threats": threats,
            "generated_npcs": generated,
        }
        if relationships_data:
            first_id = next(iter(relationships_data))
            choice_data["relationship"] = relationships_data.pop(first_id)

        result = factory.apply_scene_result(
            self.scene_id + "_rel", choice_data, state, rng,
        )
        for npc_id, rel_data in relationships_data.items():
            result.relationships[npc_id] = rel_data
        return result


# ---------------------------------------------------------------------------
# Scene 5 — Standing and Vows (faction posture + multi-vow)
# ---------------------------------------------------------------------------

# Posture archetypes for the faction encounter. Same deltas as v2's inline
# postures, surfaced here as a named pool.
_FACTION_POSTURES = [
    {
        "id": "accept",
        "display": "Accept terms — take a position within the faction.",
        "standing_delta": 2,
        "heat_delta": -1,
        "rep_standing": 1,
        "narrative_tag": "faction aligned",
        "goal_template": ("serve_{fid}", "Prove Your Worth to {fname}"),
        "threats_from_posture": False,
    },
    {
        "id": "counter",
        "display": "Counter-offer — keep some independence.",
        "standing_delta": 1,
        "heat_delta": 0,
        "rep_standing": 1,
        "narrative_tag": "negotiated with faction",
        "goal_template": ("renegotiate_{fid}", "Renegotiate With {rep_name}"),
        "threats_from_posture": False,
    },
    {
        "id": "refuse",
        "display": "Refuse — walk away, serve no one.",
        "standing_delta": -1,
        "heat_delta": 1,
        "rep_standing": -1,
        "narrative_tag": "independent",
        "goal_template": ("avoid_{fid}", "Stay Clear of {fname}"),
        "threats_from_posture": False,
    },
    {
        "id": "play",
        "display": "Play them — take the meeting, give nothing real.",
        "standing_delta": 0,
        "heat_delta": 2,
        "rep_standing": -2,
        "narrative_tag": "played faction",
        "goal_template": ("grudge_{rep_id}", "{rep_name} Is Looking for You"),
        "threats_from_posture": True,  # makes the rep a threat
    },
]


class StandingAndVowsScene(_V3Scene):
    """Faction encounter posture + 2-3 vow picks.

    Player passes 3-4 comma-separated indices:
        [faction_posture, vow_a, vow_b, (vow_c)]

    Accepts 2 or 3 vow indices. Duplicate vow indices are collapsed.
    If fewer than 2 threats have accumulated by this scene, engine tops
    them up from the faction choice and vow archetypes.
    """

    scene_id = "sz_v3_standing_vows"
    register = "standard"

    def __init__(self) -> None:
        super().__init__()
        self._faction: Dict[str, str] = {}
        self._demand_data: Dict[str, Any] = {}
        self._rep_name: str = ""
        self._rep_id: str = ""
        self._vow_npcs: Dict[int, Dict[str, str]] = {}

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
        # Faction rep — always generated fresh (representative of the
        # faction, not a personal tie).
        npc = generate_npc(self._demand_data["rep_archetype"], {}, rng)
        self._rep_name = getattr(npc, "display_name", "the representative")
        self._rep_id = getattr(npc, "id", f"npc-gen-{rng.getrandbits(32):08x}")

        # Vow NPCs — prefer biography ties, fall back to generated.
        available_seeds = [
            dict(s) for s in state.npc_seeds
            if (s.get("status") or "").lower() != "dead"
        ]
        self._vow_npcs = {}
        for i, vow in enumerate(VOW_PACKAGES):
            archetype = vow.get("npc_archetype")
            if archetype:
                resolved = _select_tie_or_generate(archetype, available_seeds, rng)
                self._vow_npcs[i] = resolved

    def get_framing(self, state: CreationState) -> str:
        fname = self._faction.get("name", "the local power")
        return (
            f"A year in, {fname} knows who you are. {self._rep_name} came "
            f"to see you. And standing behind that conversation: the "
            f"unfinished business that still drives you."
        )

    def get_known_npcs(self, state: CreationState) -> List[Dict[str, Any]]:
        out = []
        for seed in state.npc_seeds:
            if (seed.get("status") or "").lower() == "dead":
                continue
            out.append({
                "name": seed.get("name", ""),
                "relation": seed.get("relation", ""),
                "status": seed.get("status", "alive"),
            })
        return out

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        # Build filled-in vow previews so the narrator can name people.
        vow_previews = []
        for i, vow in enumerate(VOW_PACKAGES):
            npc = self._vow_npcs.get(i, {})
            name = npc.get("name", "someone")
            vow_previews.append({
                "index": i,
                "display": vow["display"].replace("{npc_name}", name),
                "npc_name": name,
                "npc_from_bio": npc.get("from_bio", False),
                "npc_archetype": vow.get("npc_archetype"),
                "resources": dict(vow.get("resources", {})),
            })

        accumulated_threats = [
            {
                "name": t.get("name", ""),
                "standing": t.get("standing", 0),
                "source": t.get("source", ""),
                "summary": t.get("summary", ""),
            }
            for t in state.threats
        ]

        return {
            "scene_intent": (
                "Political posture toward the regional faction, plus 2-3 "
                "vows that define what drives the character now."
            ),
            "beat_target_words": [500, 700],
            "faction": {
                "id": self._faction.get("id"),
                "name": self._faction.get("name"),
                "rep_name": self._rep_name,
                "rep_archetype": self._demand_data.get("rep_archetype"),
                "demand": self._demand_data.get("demand"),
                "counter": self._demand_data.get("counter"),
            },
            "posture_options": [
                {"index": i, "id": p["id"], "display": p["display"]}
                for i, p in enumerate(_FACTION_POSTURES)
            ],
            "vow_options": vow_previews,
            "accumulated_threats": accumulated_threats,
            "invitation": (
                "Present faction posture (1 pick from 4) and vows (2-3 "
                "picks from 5). Player passes indices: "
                "[posture, vow_a, vow_b, (vow_c)]."
            ),
        }

    def get_choice_groups(self, state: CreationState) -> List[Dict[str, Any]]:
        return [
            {"label": "Faction posture", "start": 0, "count": len(_FACTION_POSTURES)},
            {
                "label": "Vows (pick 2-3)",
                "start": len(_FACTION_POSTURES),
                "count": len(VOW_PACKAGES),
            },
        ]

    def get_choices(self, state: CreationState) -> List[str]:
        out: List[str] = []
        fname = self._faction.get("name", "the faction")
        demand = self._demand_data.get("demand", "loyalty")
        counter = self._demand_data.get("counter", "partial cooperation")
        posture_labels = [
            f"Accept {self._rep_name}'s terms ({demand}). Take a position within {fname}.",
            f"Counter-offer: {counter}. Keep some independence.",
            f"Refuse {self._rep_name}. Walk away.",
            f"Play {self._rep_name}. Take the meeting, give nothing real.",
        ]
        for label in posture_labels:
            out.append(f"[Posture] {label}")
        for i, vow in enumerate(VOW_PACKAGES):
            name = self._vow_npcs.get(i, {}).get("name", "someone")
            out.append(f"[Vow] {vow['display'].replace('{npc_name}', name)}")
        return out

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        return self.apply_multi([choice_index, 0, 1], state, factory, rng)

    def apply_multi(
        self,
        choice_indices: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Interpret indices as [posture, vow_a, vow_b, (vow_c)]."""
        cleaned = [
            int(i) if str(i).strip().lstrip("-").isdigit() else 0
            for i in choice_indices
        ]
        if not cleaned:
            cleaned = [0, 0, 1]

        posture_idx = cleaned[0]
        vow_idxs = cleaned[1:] or [0, 1]
        # Dedupe vow picks while preserving order.
        seen: set = set()
        unique_vows: List[int] = []
        for idx in vow_idxs:
            idx_norm = min(max(0, idx), len(VOW_PACKAGES) - 1)
            if idx_norm in seen:
                continue
            seen.add(idx_norm)
            unique_vows.append(idx_norm)
        # Need at least 2 vows. Fill with deterministic neighbors.
        while len(unique_vows) < 2:
            fallback = (unique_vows[-1] + 1) % len(VOW_PACKAGES) if unique_vows else 0
            while fallback in seen:
                fallback = (fallback + 1) % len(VOW_PACKAGES)
            seen.add(fallback)
            unique_vows.append(fallback)
        # Cap at 3.
        unique_vows = unique_vows[:3]

        # 1) Apply faction posture.
        state = self._apply_posture(posture_idx, state, factory, rng)

        # 2) Apply each vow.
        for vidx in unique_vows:
            state = self._apply_vow(vidx, state, factory, rng)

        # 3) Threat top-up: ensure at least 2 threats by finalize.
        state = self._top_up_threats(state, factory, rng)

        return state

    def _apply_posture(
        self,
        idx: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        idx = min(max(0, idx), len(_FACTION_POSTURES) - 1)
        posture = _FACTION_POSTURES[idx]
        fid = self._faction.get("id", "unknown")
        fname = self._faction.get("name", "Unknown")
        faction_skill = self._demand_data.get("faction_skill", "negotiation")

        skills = {faction_skill: 2} if posture["id"] == "accept" else {
            "accept": {faction_skill: 2},
            "counter": {"negotiation": 1, faction_skill: 1},
            "refuse": {"streetwise": 1},
            "play": {"streetwise": 1, "negotiation": 1},
        }[posture["id"]]

        goal_id_tpl, goal_desc_tpl = posture["goal_template"]
        goal_id = goal_id_tpl.format(
            fid=fid, rep_id=self._rep_id,
        )
        goal_desc = goal_desc_tpl.format(
            fname=fname, rep_name=self._rep_name,
        )

        choice_data: Dict[str, Any] = {
            "skills": dict(skills),
            "heat": {fid: posture["heat_delta"]},
            "faction_standing": {fid: posture["standing_delta"]},
            "narrative_tag": posture["narrative_tag"],
            "relationship": {
                "npc_id": self._rep_id,
                "display_name": self._rep_name,
                "standing": posture["rep_standing"],
                "current_state": "alive_present",
                "trust": max(0, posture["rep_standing"]),
                "archetype": self._demand_data.get("rep_archetype", "officer"),
            },
            "generated_npcs": [{
                "npc_id": self._rep_id,
                "display_name": self._rep_name,
                "scene_id": self.scene_id,
                "role": f"{fid}_representative",
                "standing": posture["rep_standing"],
                "hooks": [goal_desc],
            }],
            "goals": [{
                "id": goal_id,
                "description": goal_desc,
                "pressure": 2 if posture["id"] != "play" else 3,
                "progress": 0,
            }],
            "history": [{
                "timestamp": "T+0.8y",
                "description": f"Faction encounter: {self._rep_name} ({fname}) — {posture['id']}",
                "type": "session_zero",
            }],
        }

        if posture["threats_from_posture"]:
            choice_data["threats"] = [{
                "npc_id": self._rep_id,
                "name": self._rep_name,
                "standing": posture["rep_standing"],
                "source": f"faction_posture:{fid}",
                "summary": f"{self._rep_name} — {fname} representative, played",
            }]

        return factory.apply_scene_result(
            self.scene_id + "_faction", choice_data, state, rng,
        )

    def _apply_vow(
        self,
        vidx: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        vow = VOW_PACKAGES[vidx]
        npc_info = self._vow_npcs.get(vidx, {})
        npc_id = npc_info.get("npc_id", f"npc-gen-vow-{vidx}")
        npc_name = npc_info.get("name", "someone")
        archetype = vow.get("npc_archetype")
        standing = vow.get("npc_standing", 0)

        goals = []
        for g in vow["goals"]:
            filled = dict(g)
            filled["id"] = filled["id"].replace(
                "{npc_id}", npc_id,
            ).replace("{npc_name}", npc_name)
            filled["description"] = filled["description"].replace(
                "{npc_name}", npc_name,
            ).replace("{npc_id}", npc_id)
            filled.setdefault("progress", 0)
            goals.append(filled)

        choice_data: Dict[str, Any] = {
            "goals": goals,
            "resources": dict(vow.get("resources", {})),
            "inventory": list(vow.get("inventory", [])),
            "history": [{
                "timestamp": "T+1y",
                "description": f"Vow: {vow['display'].split(' — ')[0]} ({npc_name})",
                "type": "session_zero",
            }],
        }

        if archetype:
            choice_data["relationship"] = {
                "npc_id": npc_id,
                "display_name": npc_name,
                "standing": standing,
                "current_state": "alive_present",
                "trust": max(0, standing),
                "archetype": archetype,
            }
            if not npc_info.get("from_bio"):
                choice_data["generated_npcs"] = [{
                    "npc_id": npc_id,
                    "display_name": npc_name,
                    "scene_id": self.scene_id,
                    "role": archetype,
                    "standing": standing,
                    "hooks": [goals[0]["description"]] if goals else [],
                }]

            if standing <= -2:
                choice_data["threats"] = [{
                    "npc_id": npc_id,
                    "name": npc_name,
                    "standing": standing,
                    "source": f"vow:{vow.get('npc_archetype')}",
                    "summary": goals[0]["description"] if goals else "",
                }]

        return factory.apply_scene_result(
            self.scene_id + f"_vow_{vidx}", choice_data, state, rng,
        )

    def _top_up_threats(
        self,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Ensure at least 2 threats by finalize. Synthesize fillers from
        the faction if needed."""
        if len(state.threats) >= 2:
            return state
        deficit = 2 - len(state.threats)
        fid = self._faction.get("id", "unknown")
        fname = self._faction.get("name", "the local power")

        fillers: List[Dict[str, Any]] = []
        for i in range(deficit):
            npc = generate_npc("rival", {}, rng)
            npc_id = getattr(npc, "id", f"npc-threat-{rng.getrandbits(32):08x}")
            npc_name = getattr(npc, "display_name", "a rival")
            fillers.append({
                "threats": [{
                    "npc_id": npc_id,
                    "name": npc_name,
                    "standing": -2,
                    "source": f"region:{fid}",
                    "summary": f"{npc_name} — local rival, {fname} territory",
                }],
                "generated_npcs": [{
                    "npc_id": npc_id,
                    "display_name": npc_name,
                    "scene_id": self.scene_id,
                    "role": "rival",
                    "standing": -2,
                    "hooks": [],
                }],
                "relationship": {
                    "npc_id": npc_id,
                    "display_name": npc_name,
                    "standing": -2,
                    "current_state": "alive_present",
                    "trust": 0,
                    "archetype": "rival",
                },
            })

        for choice_data in fillers:
            state = factory.apply_scene_result(
                self.scene_id + "_filler_threat", choice_data, state, rng,
            )
        return state


# ---------------------------------------------------------------------------
# Scene list builder
# ---------------------------------------------------------------------------

def make_v3_scenes() -> List[Scene]:
    """Return the 5 v3 session zero scenes in order."""
    return [
        OnsetAndBiographyScene(),
        AwakeningScene(),
        PowersConfigScene(),
        FirstYearScene(),
        StandingAndVowsScene(),
    ]
