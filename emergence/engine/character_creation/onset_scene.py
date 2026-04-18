"""OnsetScene — scene 0 of the v4 arc.

Merges the prior OnsetAndBiographyScene + AwakeningScene into one
four-phase scene keyed off the hand-authored Seventh Avenue vignette:

  Pre-beat (text input): name, age, one-line bio.
  Phase 1 (attention):   pick 1 of 3 attention options.
  Phase 2 (engagement):  pick 1 of 3 engagement options.
  Phase 3 (slate):       pick 2 of 10 powers (reaction-dominant).

is_complete() gates scene advance until all four are done.  On the
last phase's apply, pending_ack is set; step scene-ack emits the T3
summary and clears it.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List

from emergence.engine.character_creation import scenario_pool
from emergence.engine.character_creation.character_factory import (
    CharacterFactory, CreationState,
)
from emergence.engine.character_creation.onset_vignette import (
    ONSET_VIGNETTE, ATTENTION_OPTIONS, ENGAGEMENT_OPTIONS,
)


V2_CATEGORY_LABELS = {
    "kinetic": "Kinetic", "material": "Material", "paradoxic": "Paradoxic",
    "spatial": "Spatial", "somatic": "Somatic", "cognitive": "Cognitive",
}


class OnsetScene:
    """Four-phase scene: bio text + attention + engagement + 2-of-10 slate."""

    scene_id = "sz_v4_onset"
    register = "intimate"

    _W_DESC = 1
    _W_REACTION = 4
    _SLATE_SIZE = 10

    def __init__(self) -> None:
        self._options: List[Any] = []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        if state.pending_dilemma_choice and state.pending_engagement_choice:
            self._options = self._compute_slate(state)
        else:
            self._options = []

    def _compute_slate(self, state: CreationState) -> List[Any]:
        option_rng = _random.Random(state.seed + 317)
        desc_tags = scenario_pool.extract_description_tags(
            state.self_description or "",
        )
        reaction_tags = list(state.reaction_tags)
        powers = list(_get_v2_powers().values())
        return scenario_pool.pick_ten(
            powers, desc_tags, reaction_tags, option_rng,
            w_desc=self._W_DESC, w_reaction=self._W_REACTION,
        )

    # ------------------------------------------------------------------
    # Framing + scenario_code
    # ------------------------------------------------------------------

    def get_framing(self, state: CreationState) -> str:
        return ONSET_VIGNETTE["framing"]

    def _phase(self, state: CreationState) -> str:
        if not state.name:
            return "biography"
        if not state.pending_dilemma_choice:
            return "attention"
        if not state.pending_engagement_choice:
            return "engagement"
        return "slate"

    def get_scenario_code(self, state: CreationState) -> Dict[str, Any]:
        phase = self._phase(state)

        attention = [
            {"index": i, "id": c["id"], "label": c["label"], "tradeoff": c["tradeoff"]}
            for i, c in enumerate(ATTENTION_OPTIONS)
        ]
        engagement = [
            {"index": i, "id": c["id"], "label": c["label"], "tradeoff": c["tradeoff"]}
            for i, c in enumerate(ENGAGEMENT_OPTIONS)
        ]

        power_options: List[Dict[str, Any]] = []
        if phase == "slate":
            for i, p in enumerate(self._current_slate(state)):
                label = V2_CATEGORY_LABELS.get(p.category, p.category.title())
                power_options.append({
                    "index": i, "name": p.name, "category": p.category,
                    "category_label": label,
                    "sub_category": getattr(p, "sub_category", ""),
                    "identity": getattr(p, "identity", "") or getattr(p, "description", ""),
                    "playstyles": list(getattr(p, "playstyles", []) or []),
                })

        return {
            "scene_intent": (
                "Four-phase Onset: biography text, attention pick, "
                "engagement pick, then pick 2 of 10 powers."
            ),
            "beat_target_words": [400, 600],
            "vignette_id": ONSET_VIGNETTE["id"],
            "vignette_framing": ONSET_VIGNETTE["framing"],
            "closing_summary": ONSET_VIGNETTE["closing_summary"],
            "phase": phase,
            "attention_options": attention,
            "engagement_options": engagement,
            "attention_choice": state.pending_dilemma_choice or "",
            "engagement_choice": state.pending_engagement_choice or "",
            "power_slate": power_options,
            "invitation": (
                "After the three text prompts (name, age, one-line bio), "
                "present the Seventh Avenue framing.  Player picks "
                "attention, then engagement, then two powers.  Reaction "
                "tags accumulate across picks; the slate is scored with "
                "reaction-dominant weighting."
            ),
            "hidden_seeds": [
                "Tier enters at 3 with ceiling 5.",
                "Reaction tags are reaction-dominant (w=4) vs description (w=1).",
                "pending_ack is set on the slate pick; step scene-ack emits T3 summary.",
            ],
        }

    def get_choices(self, state: CreationState) -> List[str]:
        phase = self._phase(state)
        if phase == "biography":
            return []
        if phase == "attention":
            return [f"{c['label']}  —  {c['tradeoff']}" for c in ATTENTION_OPTIONS]
        if phase == "engagement":
            return [f"{c['label']}  —  {c['tradeoff']}" for c in ENGAGEMENT_OPTIONS]
        # slate
        lines: List[str] = []
        for p in self._current_slate(state):
            label = V2_CATEGORY_LABELS.get(p.category, p.category.title())
            sub = getattr(p, "sub_category", "") or ""
            identity = getattr(p, "identity", "") or getattr(p, "description", "")
            lines.append(f"[{label} / {sub}] {p.name} — {identity}"
                         if sub else f"[{label}] {p.name} — {identity}")
        return lines

    def _current_slate(self, state: CreationState) -> List[Any]:
        if state.pending_slate and state.pending_slate_scene == self.scene_id:
            powers = _get_v2_powers()
            resolved = [powers.get(e.get("power_id")) for e in state.pending_slate]
            return [p for p in resolved if p is not None]
        return list(self._options)

    # ------------------------------------------------------------------
    # Text input (pre-beat)
    # ------------------------------------------------------------------

    def needs_text_input(self) -> bool:
        return True

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        if self._phase(state) != "biography":
            return []
        return [
            {"key": "name", "prompt": "Your name."},
            {"key": "age",  "prompt": "Your age on the day it happened (16-65)."},
            {"key": "description",
             "prompt": "One line: who you were before.  What you did, who your people were."},
        ]

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        if self._phase(state) != "biography":
            return state
        name = text_inputs.get("name", "").strip() or "Unknown"
        try:
            age = max(16, min(65, int(text_inputs.get("age", "25").strip())))
        except ValueError:
            age = 25
        desc = text_inputs.get("description", "").strip()
        desc_tags = scenario_pool.extract_description_tags(desc)
        return factory.apply_scene_result(self.scene_id + "_bio", {
            "name": name,
            "age_at_onset": age,
            "self_description": desc,
            "reaction_tags": desc_tags,
            "history": [{
                "timestamp": "T-1y",
                "description": f"Pre-Onset: {desc[:80]}" if desc else "Pre-Onset.",
                "type": "session_zero",
            }],
        }, state, rng)

    # ------------------------------------------------------------------
    # Phase 1 — attention; Phase 2 — engagement; Phase 3 — slate
    # ------------------------------------------------------------------

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        phase = self._phase(state)
        if phase == "attention":
            return self._apply_attention(choice_index, state, factory, rng)
        if phase == "engagement":
            return self._apply_engagement(choice_index, state, factory, rng)
        # Slate: single-choice delegates to a pair pick.
        slate = self._current_slate(state)
        if not slate:
            return state
        first = min(max(0, choice_index), len(slate) - 1)
        second = (first + 1) % len(slate)
        if second == first:
            second = (first + 2) % len(slate)
        return self.apply_multi([first, second], state, factory, rng)

    def _apply_attention(self, idx, state, factory, rng):
        c = ATTENTION_OPTIONS[min(max(0, idx), len(ATTENTION_OPTIONS) - 1)]
        existing = list(state.reaction_tags)
        merged = list(c["tags"]) + [t for t in existing if t not in c["tags"]]
        return factory.apply_scene_result(self.scene_id + "_attention", {
            "pending_dilemma_choice": c["id"],
            "scenario_reactions": {"attention": c["label"]},
            "reaction_tags": merged,
            "history": [{
                "timestamp": "T+0s",
                "description": f"Onset attention: {c['label']}",
                "type": "session_zero",
            }],
        }, state, rng)

    def _apply_engagement(self, idx, state, factory, rng):
        c = ENGAGEMENT_OPTIONS[min(max(0, idx), len(ENGAGEMENT_OPTIONS) - 1)]
        existing = list(state.reaction_tags)
        merged = existing + [t for t in c["tags"] if t not in existing]
        updated = factory.apply_scene_result(self.scene_id + "_engagement", {
            "pending_engagement_choice": c["id"],
            "scenario_reactions": {"engagement": c["label"]},
            "reaction_tags": merged,
            "history": [{
                "timestamp": "T+1s",
                "description": f"Onset engagement: {c['label']}",
                "type": "session_zero",
            }],
        }, state, rng)
        # Now compute the slate.
        slate = self._compute_slate(updated)
        self._options = slate
        slate_payload = [{
            "power_id": p.id, "name": p.name,
            "category": p.category, "sub_category": getattr(p, "sub_category", ""),
        } for p in slate]
        return factory.apply_scene_result(self.scene_id + "_slate_build", {
            "pending_slate": slate_payload,
            "pending_slate_scene": self.scene_id,
        }, updated, rng)

    def apply_multi(self, indices, state, factory, rng):
        slate = self._current_slate(state)
        if not slate:
            return state
        picks = [slate[min(max(0, i), len(slate) - 1)] for i in indices[:2]]
        # Primary + secondary.
        power_entries = []
        for slot, p in zip(("primary", "secondary"), picks):
            power_entries.append({
                "power_id": p.id, "name": p.name, "category": p.category,
                "sub_category": getattr(p, "sub_category", ""),
                "slot": slot,
            })
        updated = factory.apply_scene_result(self.scene_id + "_slate_pick", {
            "powers": power_entries,
            "power_category_primary": picks[0].category,
            "power_category_secondary": picks[1].category if len(picks) > 1 else None,
            "tier": 3,
            "tier_ceiling": 5,
            "pending_ack": True,
            "history": [{
                "timestamp": "T+2s",
                "description": (
                    f"Onset slate pick: {picks[0].name}"
                    + (f" + {picks[1].name}" if len(picks) > 1 else "")
                ),
                "type": "session_zero",
            }],
        }, state, rng)
        return updated

    def is_complete(self, state: CreationState) -> bool:
        return (
            bool(state.name)
            and bool(state.pending_dilemma_choice)
            and bool(state.pending_engagement_choice)
            and len(state.powers) >= 2
        )


def _get_v2_powers() -> Dict[str, Any]:
    """Lazy-load the v2 power registry (delegates to scenarios_v3 helper)."""
    from emergence.engine.character_creation.scenarios_v3 import _get_v2_powers as _inner
    return _inner()
