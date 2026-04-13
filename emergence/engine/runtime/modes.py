"""Mode system — manages game mode transitions.

Modes: SESSION_ZERO, FRAMING, SIM, COMBAT, GAME_OVER.
ModeManager enforces valid transitions.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Protocol


class ModeHandler(Protocol):
    """Protocol for game mode handlers."""

    def enter(self, state: Any) -> None:
        """Called when entering this mode."""
        ...

    def run_cycle(self, state: Any) -> Optional[str]:
        """Run one cycle of this mode.

        Returns None to stay in mode, or a mode name to transition.
        """
        ...

    def exit(self, state: Any) -> None:
        """Called when leaving this mode."""
        ...


# Valid transitions: from_mode -> set of to_modes
TRANSITION_TABLE: Dict[str, set] = {
    "SESSION_ZERO": {"FRAMING"},
    "FRAMING": {"SIM"},
    "SIM": {"COMBAT", "FRAMING", "GAME_OVER"},
    "COMBAT": {"SIM", "GAME_OVER"},
    "GAME_OVER": {"SESSION_ZERO"},
}


class ModeError(Exception):
    """Invalid mode transition."""
    pass


class ModeManager:
    """Manages game mode transitions and dispatches to handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, ModeHandler] = {}
        self._current_mode: Optional[str] = None
        self._history: List[str] = []

    @property
    def current_mode(self) -> Optional[str]:
        return self._current_mode

    @property
    def history(self) -> List[str]:
        return list(self._history)

    def register(self, mode_name: str, handler: ModeHandler) -> None:
        """Register a handler for a mode."""
        self._handlers[mode_name] = handler

    def start(self, mode_name: str, state: Any) -> None:
        """Start the mode system in the given mode."""
        if mode_name not in self._handlers:
            raise ModeError(f"No handler registered for mode: {mode_name}")
        self._current_mode = mode_name
        self._history.append(mode_name)
        self._handlers[mode_name].enter(state)

    def transition(self, to_mode: str, state: Any) -> None:
        """Transition to a new mode."""
        if self._current_mode is None:
            raise ModeError("Mode system not started")

        allowed = TRANSITION_TABLE.get(self._current_mode, set())
        if to_mode not in allowed:
            raise ModeError(
                f"Invalid transition: {self._current_mode} -> {to_mode}. "
                f"Allowed: {sorted(allowed)}"
            )

        if to_mode not in self._handlers:
            raise ModeError(f"No handler registered for mode: {to_mode}")

        # Exit current, enter new
        self._handlers[self._current_mode].exit(state)
        self._current_mode = to_mode
        self._history.append(to_mode)
        self._handlers[to_mode].enter(state)

    def run_cycle(self, state: Any) -> Optional[str]:
        """Run one cycle of the current mode.

        Returns the new mode name if a transition occurred, None otherwise.
        """
        if self._current_mode is None:
            raise ModeError("Mode system not started")

        handler = self._handlers[self._current_mode]
        next_mode = handler.run_cycle(state)

        if next_mode is not None:
            self.transition(next_mode, state)
            return next_mode

        return None

    def is_valid_transition(self, from_mode: str, to_mode: str) -> bool:
        """Check if a transition is valid."""
        return to_mode in TRANSITION_TABLE.get(from_mode, set())


class StubModeHandler:
    """Stub handler for testing — records calls."""

    def __init__(self, next_mode: Optional[str] = None) -> None:
        self._next_mode = next_mode
        self.entered = False
        self.exited = False
        self.cycles = 0

    def enter(self, state: Any) -> None:
        self.entered = True

    def run_cycle(self, state: Any) -> Optional[str]:
        self.cycles += 1
        return self._next_mode

    def exit(self, state: Any) -> None:
        self.exited = True
