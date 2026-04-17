"""Main runtime — launch sequence, GameState, session loop.

Implements the 11-step launch sequence and main session loop per
runtime-architecture.md.
"""

from __future__ import annotations

import os
import random
import time
from typing import Any, Dict, List, Optional


class GameState:
    """All mutable runtime state for a session."""

    def __init__(self) -> None:
        # Core state dicts (loaded from save or generated)
        self.world: Dict[str, Any] = {}
        self.player: Dict[str, Any] = {}
        self.factions: Dict[str, Any] = {}
        self.npcs: Dict[str, Any] = {}
        self.locations: Dict[str, Any] = {}
        self.clocks: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

        # Runtime
        self.session_id: str = ""
        self.session_start: float = 0.0
        self.rng: random.Random = random.Random()
        self.save_root: str = ""
        self.session_should_end: bool = False
        self.current_mode: str = ""

        # Config
        self.config: Any = None
        self.narrator_mode: str = "mock"
        self.autosave_interval: int = 600  # 10 minutes
        self.last_autosave: float = 0.0

        # Lock
        self.lock_path: str = ""


class LaunchLock:
    """File-based launch lock to prevent concurrent sessions."""

    def __init__(self, save_root: str) -> None:
        self.lock_path = os.path.join(save_root, ".lock")

    def acquire(self) -> bool:
        """Acquire the launch lock. Returns True if acquired."""
        if os.path.exists(self.lock_path):
            # Check if stale (older than 1 hour)
            try:
                age = time.time() - os.path.getmtime(self.lock_path)
                if age < 3600:
                    return False
            except OSError:
                pass

        try:
            os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
            with open(self.lock_path, "w") as f:
                f.write(f"pid={os.getpid()}\ntime={time.time()}\n")
            return True
        except OSError:
            return False

    def release(self) -> None:
        """Release the launch lock."""
        try:
            if os.path.exists(self.lock_path):
                os.unlink(self.lock_path)
        except OSError:
            pass


def launch(
    args: Any,
    save_root: str,
    force_new: bool = False,
) -> int:
    """11-step launch sequence.

    Returns exit code.
    """
    from emergence.engine.runtime.configuration import GameConfig, load_config
    from emergence.engine.persistence.load import LoadManager
    from emergence.engine.persistence.save import SaveManager
    from emergence.engine.runtime.error_handling import crash_shutdown

    state = GameState()
    state.save_root = save_root

    # Step 1: Args already parsed by __main__.py

    # Step 2: Python version check (we're running, so it's OK)

    # Step 3-4: Load config
    config_path = getattr(args, "config", None)
    if config_path and os.path.exists(config_path):
        state.config = load_config(config_path)
    else:
        state.config = GameConfig()

    # Apply CLI overrides
    if getattr(args, "seed", None) is not None:
        state.rng = random.Random(args.seed)
        state.config.seed = args.seed

    state.narrator_mode = state.config.narrator_mode
    state.autosave_interval = state.config.autosave_interval

    # Step 5: Ensure save root exists
    os.makedirs(save_root, exist_ok=True)

    # Step 6: Acquire launch lock
    lock = LaunchLock(save_root)
    if not lock.acquire():
        print("Another session is already running on this save.")
        print("If this is an error, delete: " + lock.lock_path)
        return 1

    state.lock_path = lock.lock_path

    try:
        # Step 7: Inspect save contents
        loader = LoadManager(save_root)
        classification = loader.classify()

        # Step 8: Dispatch by classification
        if classification == "CORRUPT":
            print("Save is corrupt. Run 'emergence migrate' or delete the save.")
            return 3

        if classification == "VERSION_MISMATCH":
            print("Save version mismatch. Run 'emergence migrate' first.")
            return 3

        if classification == "PARTIAL":
            print("Save is incomplete. Attempting recovery...")
            # Load what we can
            result = loader.load_save()
            _populate_state(state, result)

        elif classification == "VALID" and not force_new:
            # Resume existing game
            result = loader.load_save()
            _populate_state(state, result)
            print(f"Resuming session. Player: {state.player.get('name', '?')}")

        else:
            # FRESH or force_new — need session zero
            state.current_mode = "SESSION_ZERO"

        # Generate session ID
        state.session_id = f"session_{int(time.time())}_{state.rng.randint(0, 9999):04d}"
        state.session_start = time.time()
        state.last_autosave = time.time()

        # Step 9: Dry run check
        if getattr(args, "dry_run", False):
            print(f"Dry run — classification: {classification}")
            print(f"Mode: {state.current_mode or 'SIM'}")
            print(f"Session ID: {state.session_id}")
            return 0

        # Step 9 (real): Enter main session loop
        exit_code = main_session_loop(state)

        # Step 10: Clean shutdown
        _clean_shutdown(state)

        return exit_code

    except Exception as e:
        # Crash shutdown
        try:
            crash_shutdown(e, {"save_root": save_root, "state": state})
        except Exception:
            pass
        raise

    finally:
        # Step 11: Release lock
        lock.release()


def main_session_loop(state: GameState) -> int:
    """Main session loop — dispatches to mode handlers.

    Returns exit code.
    """
    from emergence.engine.runtime.modes import ModeManager, ModeError, StubModeHandler
    from emergence.engine.runtime.input_handler import InputHandler
    from emergence.engine.narrator.queue import MockNarrationQueue
    from emergence.engine.persistence.save import SaveManager

    input_handler = InputHandler()
    narrator = MockNarrationQueue()
    save_mgr = SaveManager(state.save_root)

    # Determine starting mode
    if not state.current_mode:
        if state.player and state.player.get("name"):
            state.current_mode = "SIM"
        else:
            state.current_mode = "SESSION_ZERO"

    # Run mode cycles
    while not state.session_should_end:
        mode = state.current_mode

        if mode == "SESSION_ZERO":
            next_mode = _run_session_zero(state, narrator)
        elif mode == "FRAMING":
            next_mode = _run_framing(state, narrator)
        elif mode == "SIM":
            next_mode = _run_sim_cycle(state, narrator, input_handler)
        elif mode == "COMBAT":
            next_mode = _run_combat(state, narrator)
        elif mode == "GAME_OVER":
            state.session_should_end = True
            next_mode = None
        else:
            print(f"Unknown mode: {mode}")
            state.session_should_end = True
            next_mode = None

        if next_mode:
            state.current_mode = next_mode

        # Autosave check
        _maybe_autosave(state, save_mgr)

    return 0


def _make_all_scenes() -> list:
    """Assemble the v3 session zero scenes (5 long-form scenes)."""
    from emergence.engine.character_creation.scenarios_v3 import make_v3_scenes
    return make_v3_scenes()


def _run_session_zero(state: GameState, narrator: Any) -> Optional[str]:
    """Run session zero mode. Returns next mode or None."""
    from emergence.engine.character_creation.session_zero import (
        SessionZero,
        FixedInputSource,
        MockNarratorSink,
    )

    if state.narrator_mode == "mock":
        inputs = FixedInputSource(
            texts={"name": "Elena", "age": "28"},
            default_choice=0,
        )
    else:
        # Live mode: stdin input source
        inputs = _StdinInputSource()

    sink = MockNarratorSink()

    scenes = _make_all_scenes()
    sz = SessionZero(scenes=scenes)
    try:
        character = sz.run(inputs, sink, state.rng)
        if hasattr(character, "to_dict"):
            state.player = character.to_dict()
        elif isinstance(character, dict):
            state.player = character
        else:
            state.player = {"name": "Unknown"}
        return "FRAMING"
    except Exception as e:
        print(f"Session zero error: {e}")
        state.session_should_end = True
        return None


class _StdinInputSource:
    """Live input source reading from stdin."""

    def get_text(self, prompt: str) -> str:
        print(prompt)
        return input("> ").strip()

    def get_choice(self, prompt: str, options: list) -> int:
        print(prompt)
        for i, opt in enumerate(options):
            print(f"  {i + 1}. {opt}")
        while True:
            raw = input("> ").strip()
            try:
                idx = int(raw) - 1
                if 0 <= idx < len(options):
                    return idx
            except ValueError:
                pass
            print(f"Enter a number 1-{len(options)}.")


def _run_framing(state: GameState, narrator: Any) -> Optional[str]:
    """Run framing mode. Returns next mode."""
    from emergence.engine.narrator.payloads import build_scene_framing_payload

    location_name = state.player.get("home_region", "Unknown")
    payload = build_scene_framing_payload(
        scene_id=f"framing_{state.session_id}",
        location_name=location_name,
        time_of_day="dawn",
        npcs_present=[],
        recent_events=[],
    )
    narrator.emit(payload)
    return "SIM"


def _run_sim_cycle(state: GameState, narrator: Any, input_handler: Any) -> Optional[str]:
    """Run one sim cycle. Returns next mode or None."""
    # For now, the sim cycle ends the session in mock mode
    # Full implementation will integrate with tick engine + situation generator
    if state.narrator_mode == "mock":
        state.session_should_end = True
        return None

    # Live mode would: generate situation, present choices, resolve, tick
    state.session_should_end = True
    return None


def _run_combat(state: GameState, narrator: Any) -> Optional[str]:
    """Run combat mode. Returns next mode."""
    # Combat delegates to the encounter runner
    # After combat, return to SIM
    return "SIM"


def _maybe_autosave(state: GameState, save_mgr: Any) -> None:
    """Check if autosave is due and perform it."""
    now = time.time()
    if now - state.last_autosave >= state.autosave_interval:
        save_mgr.full_save(
            world=state.world,
            player=state.player,
            factions=state.factions,
            npcs=state.npcs,
            locations=state.locations,
            clocks=state.clocks,
            metadata=state.metadata,
        )
        state.last_autosave = now


def _clean_shutdown(state: GameState) -> None:
    """Perform clean shutdown — final save."""
    from emergence.engine.persistence.save import SaveManager

    if state.save_root:
        save_mgr = SaveManager(state.save_root)
        save_mgr.full_save(
            world=state.world,
            player=state.player,
            factions=state.factions,
            npcs=state.npcs,
            locations=state.locations,
            clocks=state.clocks,
            metadata=state.metadata,
        )


def _populate_state(state: GameState, result: Any) -> None:
    """Populate GameState from a LoadResult."""
    state.world = result.world or {}
    state.player = result.player or {}
    state.factions = result.factions or {}
    state.npcs = result.npcs or {}
    state.locations = result.locations or {}
    state.clocks = result.clocks or {}
    state.metadata = result.metadata or {}

    # Set mode based on state
    if state.player and state.player.get("name"):
        state.current_mode = "SIM"
    else:
        state.current_mode = "SESSION_ZERO"
