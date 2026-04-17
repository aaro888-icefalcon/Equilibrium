"""Session Zero orchestrator — runs the 10-scene character creation flow.

Uses InputSource + NarratorSink protocols for testability.
FixedInputSource provides deterministic test inputs.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Protocol, Tuple

from emergence.engine.schemas.character import CharacterSheet
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

class InputSource(Protocol):
    """Provides player input for session zero."""

    def get_text(self, prompt: str) -> str:
        """Get free-text input."""
        ...

    def get_choice(self, prompt: str, options: List[str]) -> int:
        """Get a numbered choice (0-indexed)."""
        ...


class NarratorSink(Protocol):
    """Receives narration payloads during session zero."""

    def narrate(self, scene_type: str, text: str, **kwargs: Any) -> str:
        """Display narration and return any response."""
        ...


# ---------------------------------------------------------------------------
# Test implementations
# ---------------------------------------------------------------------------

class FixedInputSource:
    """Deterministic input source for testing.

    Provides pre-set text answers and choice indices.
    """

    def __init__(
        self,
        texts: Dict[str, str] | None = None,
        choices: Dict[str, int] | None = None,
        default_choice: int = 0,
    ) -> None:
        self.texts = texts or {}
        self.choices = choices or {}
        self.default_choice = default_choice
        self._text_calls: List[str] = []
        self._choice_calls: List[str] = []

    def get_text(self, prompt: str) -> str:
        self._text_calls.append(prompt)
        # Match by substring in prompt
        for key, val in self.texts.items():
            if key.lower() in prompt.lower():
                return val
        return "Test Character"

    def get_choice(self, prompt: str, options: List[str]) -> int:
        self._choice_calls.append(prompt)
        for key, val in self.choices.items():
            if key.lower() in prompt.lower():
                return min(val, len(options) - 1)
        return min(self.default_choice, len(options) - 1)


class MockNarratorSink:
    """Test narrator that records payloads."""

    def __init__(self) -> None:
        self.payloads: List[Dict[str, Any]] = []

    def narrate(self, scene_type: str, text: str, **kwargs: Any) -> str:
        self.payloads.append({"scene_type": scene_type, "text": text, **kwargs})
        return f"[NARRATION: {scene_type}]"


# ---------------------------------------------------------------------------
# Scene base
# ---------------------------------------------------------------------------

class Scene:
    """Base class for a session zero scene."""

    scene_id: str = ""
    register: str = "standard"

    def prepare(self, state: CreationState, rng: _random.Random) -> None:
        """Pre-compute scene data (NPC generation, template filling).

        Called before get_framing() and get_choices() so that generated
        names can appear in framing text and choice descriptions.
        """

    def get_framing(self, state: CreationState) -> str:
        """Return the narrator framing text."""
        return ""

    def get_choices(self, state: CreationState) -> List[str]:
        """Return the list of choice descriptions."""
        return []

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Apply the chosen option and return updated state."""
        return state

    def needs_text_input(self) -> bool:
        """Whether this scene needs free-text input before choices."""
        return False

    def text_prompts(self, state: CreationState) -> List[Dict[str, str]]:
        """Return prompts for freeform text input. Each item: {"key": str, "prompt": str}."""
        return []

    def apply_text(
        self,
        text_inputs: Dict[str, str],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Apply free-text inputs to state."""
        return state


# ---------------------------------------------------------------------------
# SessionZero
# ---------------------------------------------------------------------------

class SessionZero:
    """Orchestrates the 10-scene session zero flow."""

    def __init__(self, scenes: List[Scene] | None = None) -> None:
        self.scenes = scenes or []
        self.factory = CharacterFactory()

    def run(
        self,
        input_source: InputSource,
        narrator: NarratorSink,
        rng: _random.Random,
        world: Any = None,
    ) -> CharacterSheet:
        """Run all scenes and return a finalized CharacterSheet."""
        state = CreationState(seed=rng.getrandbits(64))

        for scene in self.scenes:
            # Pre-compute scene data (NPC generation, template filling)
            scene.prepare(state, rng)

            # Narrate framing
            framing = scene.get_framing(state)
            if framing:
                narrator.narrate(
                    scene_type="character_creation_beat",
                    text=framing,
                    scene_id=scene.scene_id,
                    register=scene.register,
                )

            # Handle text input if needed
            if scene.needs_text_input():
                text_inputs: Dict[str, str] = {}
                for prompt_spec in scene.text_prompts(state):
                    key = prompt_spec.get("key", "")
                    prompt = prompt_spec.get("prompt", key)
                    if not key:
                        continue
                    text_inputs[key] = input_source.get_text(prompt)
                state = scene.apply_text(text_inputs, state, self.factory, rng)

            # Present choices and get selection
            choices = scene.get_choices(state)
            if choices:
                choice_idx = input_source.get_choice(
                    f"Scene {scene.scene_id}",
                    choices,
                )
                state = scene.apply(choice_idx, state, self.factory, rng)

        return self.factory.finalize(state)
