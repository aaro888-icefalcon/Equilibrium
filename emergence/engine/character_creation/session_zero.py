"""Session Zero orchestrator — hosts the six character creation scenes.

Scene order:
  1. PreEmergenceScene   — text elicitation + classifier apply
  2. PowerPickScene      — subcategories then powers; auto cast/rider
  3. LocationScene       — post-Onset settlement pick
  4. JobBundleScene      — narrator generates 5 cards; player picks 1
  5. QuestPickScene      — narrator generates 8; picks 4 backstory; player picks 1 urgent
  6. BridgeScene         — 1500-word bridge + opening scene; hands off to sim

Each scene is independently callable via step_cli; the orchestrator here
exposes a high-level `run()` helper for integration tests that wants to push
the full flow through a mock narrator.

Legacy Scene / SessionZero classes from the v4 arc have been removed with
the onset_scene and vignette scene files they supported.
"""

from __future__ import annotations

import random as _random
from typing import Any, Callable, Dict, List, Optional, Protocol

from emergence.engine.character_creation.bridge_scene import BridgeScene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.job_bundle_scene import JobBundleScene
from emergence.engine.character_creation.location_scene import LocationScene
from emergence.engine.character_creation.power_pick_scene import PowerPickScene
from emergence.engine.character_creation.pre_emergence_scene import PreEmergenceScene
from emergence.engine.character_creation.quest_pick_scene import QuestPickScene
from emergence.engine.quests.schema import QuestState
from emergence.engine.schemas.character import CharacterSheet


# ---------------------------------------------------------------------------
# Protocols for tests / CLI to supply input + narrator output
# ---------------------------------------------------------------------------


class InputSource(Protocol):
    def get_text(self, key: str, prompt: str) -> str: ...
    def get_choice(self, prompt: str, options: List[Any]) -> int: ...
    def get_choices(self, prompt: str, options: List[Any], count: int) -> List[int]: ...


class Narrator(Protocol):
    def classifier(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def job_bundle(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def quest_pool(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
    def bridge(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Test fakes
# ---------------------------------------------------------------------------


class FixedInputSource:
    """Deterministic inputs for tests.

    texts:   dict of key → value (used by get_text)
    choices: dict of key → chosen index (used by get_choice / get_choices)
    multi:   dict of key → list of indices (used by get_choices)
    """

    def __init__(
        self,
        texts: Optional[Dict[str, str]] = None,
        choices: Optional[Dict[str, int]] = None,
        multi: Optional[Dict[str, List[int]]] = None,
    ) -> None:
        self.texts = texts or {}
        self.choices = choices or {}
        self.multi = multi or {}

    def get_text(self, key: str, prompt: str) -> str:
        return self.texts.get(key, "")

    def get_choice(self, prompt: str, options: List[Any]) -> int:
        for key, idx in self.choices.items():
            if key.lower() in prompt.lower():
                return self._normalize(idx, len(options))
        return 0

    def get_choices(self, prompt: str, options: List[Any], count: int) -> List[int]:
        for key, picks in self.multi.items():
            if key.lower() in prompt.lower():
                return [self._normalize(p, len(options)) for p in picks[:count]]
        return list(range(count))

    @staticmethod
    def _normalize(idx: int, total: int) -> int:
        """Clamp and wrap an index so tests can use -1 for 'last option'."""
        if total <= 0:
            return 0
        if idx < 0:
            return max(0, total + idx)
        return min(idx, total - 1)


# ---------------------------------------------------------------------------
# SessionZero flow
# ---------------------------------------------------------------------------


class SessionZero:
    """Runs the six-scene creation flow end-to-end.

    The orchestrator holds one instance of each scene class and threads a
    CreationState + QuestState through them. CLI-mode entry points live in
    step_cli.py; this `run()` is the in-process driver for integration tests.
    """

    def __init__(self) -> None:
        self.pre_emergence = PreEmergenceScene()
        self.power_pick = PowerPickScene()
        self.location = LocationScene()
        self.job_bundle = JobBundleScene()
        self.quest_pick = QuestPickScene()
        self.bridge = BridgeScene()
        self.factory = CharacterFactory()

    def run(
        self,
        inputs: InputSource,
        narrator: Narrator,
        rng: Optional[_random.Random] = None,
    ) -> Dict[str, Any]:
        """Drive all six scenes with the given inputs + narrator.

        Returns a dict with final CharacterSheet, QuestState, and the
        bridge/opening-scene prose.
        """
        rng = rng or _random.Random(0)
        state = CreationState(seed=rng.getrandbits(64))
        quest_state = QuestState()

        # 1. Pre-emergence
        state = self._run_pre_emergence(state, inputs, narrator, rng)

        # 2. Power pick
        state = self._run_power_pick(state, inputs, rng)

        # 3. Location
        state = self._run_location(state, inputs, rng)

        # 4. Job bundle
        state = self._run_job_bundle(state, inputs, narrator, rng)

        # 5. Quest pick
        quest_state = self._run_quest_pick(state, inputs, narrator, rng, quest_state)

        # 6. Bridge
        state = self._run_bridge(state, narrator, quest_state)

        sheet = self.factory.finalize(state)
        return {
            "character_sheet": sheet,
            "quest_state": quest_state,
            "backstory_prose": state.scene_choices.get("backstory_prose", ""),
            "opening_scene": state.scene_choices.get("opening_scene", ""),
            "opening_scene_meta": state.scene_choices.get("opening_scene_meta", {}),
        }

    # ------------------------------------------------------------------
    # Scene drivers
    # ------------------------------------------------------------------

    def _run_pre_emergence(
        self,
        state: CreationState,
        inputs: InputSource,
        narrator: Narrator,
        rng: _random.Random,
    ) -> CreationState:
        scene = self.pre_emergence
        text_inputs: Dict[str, str] = {}
        for prompt_spec in scene.text_prompts(state):
            k = prompt_spec["key"]
            text_inputs[k] = inputs.get_text(k, prompt_spec["prompt"])
        state = scene.apply_text(text_inputs, state, self.factory, rng)
        payload = scene.build_narrator_payload(state)
        classifier_output = narrator.classifier(payload)
        state = scene.apply_classifier(classifier_output, state, self.factory, rng)
        return state

    def _run_power_pick(
        self,
        state: CreationState,
        inputs: InputSource,
        rng: _random.Random,
    ) -> CreationState:
        scene = self.power_pick
        scene.prepare_subcategory_offer(state, rng)
        sub_picks = inputs.get_choices(
            "subcategories",
            state.scene_choices["subcategory_offer"],
            2,
        )
        state = scene.apply_subcategory_picks(sub_picks, state, self.factory, rng)
        scene.prepare_power_offer(state, rng)
        picked_subs = state.scene_choices["subcategories_picked"]
        power_picks = inputs.get_choices(
            "powers",
            state.scene_choices["power_offer"],
            len(picked_subs),
        )
        state = scene.apply_power_picks(power_picks, state, self.factory, rng)
        return state

    def _run_location(
        self,
        state: CreationState,
        inputs: InputSource,
        rng: _random.Random,
    ) -> CreationState:
        scene = self.location
        choices = scene.get_choices(state)
        idx = inputs.get_choice("post-emergence location", choices)
        return scene.apply(idx, state, self.factory, rng)

    def _run_job_bundle(
        self,
        state: CreationState,
        inputs: InputSource,
        narrator: Narrator,
        rng: _random.Random,
    ) -> CreationState:
        scene = self.job_bundle
        payload = scene.build_narrator_payload(state)
        bundle_output = narrator.job_bundle(payload)
        state = scene.store_bundle_output(bundle_output, state)
        idx = inputs.get_choice("job bundle", state.scene_choices["job_bundle_cards"])
        state = scene.apply_pick(idx, state, self.factory, rng)
        return state

    def _run_quest_pick(
        self,
        state: CreationState,
        inputs: InputSource,
        narrator: Narrator,
        rng: _random.Random,
        quest_state: QuestState,
    ) -> QuestState:
        scene = self.quest_pick
        payload = scene.build_narrator_payload(state)
        quest_output = narrator.quest_pool(payload)
        state = scene.store_quest_output(quest_output, state)
        idx = inputs.get_choice(
            "urgent quest", state.scene_choices["quest_urgent_offer"],
        )
        quest_state = scene.apply_urgent_pick(idx, state, self.factory, rng, quest_state)
        return quest_state

    def _run_bridge(
        self,
        state: CreationState,
        narrator: Narrator,
        quest_state: QuestState,
    ) -> CreationState:
        scene = self.bridge
        payload = scene.build_narrator_payload(state, quest_state)
        bridge_output = narrator.bridge(payload)
        state = scene.apply_bridge_output(bridge_output, state, quest_state)
        return state
