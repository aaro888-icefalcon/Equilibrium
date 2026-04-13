"""Integration tests for mode transitions across full session."""

import os
import tempfile
import unittest

from emergence.engine.runtime.modes import (
    ModeManager,
    ModeError,
    StubModeHandler,
    TRANSITION_TABLE,
)
from emergence.engine.runtime.main import GameState, launch
from emergence.engine.persistence.save import SaveManager


class FakeArgs:
    def __init__(self, **kwargs):
        self.save_root = kwargs.get("save_root", "/tmp/test")
        self.config = None
        self.log_level = "info"
        self.log_file = None
        self.no_color = False
        self.seed = kwargs.get("seed", 42)
        self.dry_run = kwargs.get("dry_run", False)
        self.character = None
        self.resume = False
        self.skip_session_zero = False


class TestFullModeTransitionPaths(unittest.TestCase):

    def _make_manager(self):
        mgr = ModeManager()
        modes = {}
        for name in TRANSITION_TABLE:
            handler = StubModeHandler()
            mgr.register(name, handler)
            modes[name] = handler
        return mgr, modes

    def test_session_zero_to_framing_to_sim(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})

        self.assertTrue(modes["SESSION_ZERO"].entered)
        self.assertTrue(modes["SESSION_ZERO"].exited)
        self.assertTrue(modes["FRAMING"].entered)
        self.assertTrue(modes["FRAMING"].exited)
        self.assertTrue(modes["SIM"].entered)

    def test_sim_combat_roundtrip(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        mgr.transition("COMBAT", {})
        mgr.transition("SIM", {})
        self.assertEqual(mgr.current_mode, "SIM")
        self.assertEqual(
            mgr.history,
            ["SESSION_ZERO", "FRAMING", "SIM", "COMBAT", "SIM"],
        )

    def test_multiple_combat_encounters(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})

        for _ in range(3):
            mgr.transition("COMBAT", {})
            mgr.transition("SIM", {})

        self.assertEqual(mgr.current_mode, "SIM")

    def test_sim_to_framing_to_sim(self):
        """SIM can go to FRAMING (location change) and back."""
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        self.assertEqual(mgr.current_mode, "SIM")

    def test_combat_death_to_game_over(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        mgr.transition("COMBAT", {})
        mgr.transition("GAME_OVER", {})
        self.assertEqual(mgr.current_mode, "GAME_OVER")

    def test_game_over_restart(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        mgr.transition("GAME_OVER", {})
        mgr.transition("SESSION_ZERO", {})
        self.assertEqual(mgr.current_mode, "SESSION_ZERO")

    def test_forbidden_session_zero_to_combat(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        with self.assertRaises(ModeError):
            mgr.transition("COMBAT", {})

    def test_forbidden_framing_to_combat(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        with self.assertRaises(ModeError):
            mgr.transition("COMBAT", {})

    def test_forbidden_combat_to_session_zero(self):
        mgr, modes = self._make_manager()
        mgr.start("SESSION_ZERO", {})
        mgr.transition("FRAMING", {})
        mgr.transition("SIM", {})
        mgr.transition("COMBAT", {})
        with self.assertRaises(ModeError):
            mgr.transition("SESSION_ZERO", {})


class TestSessionResumeFromSave(unittest.TestCase):

    def test_fresh_save_starts_session_zero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_root = os.path.join(tmpdir, "save")
            args = FakeArgs(save_root=save_root, seed=42, dry_run=True)
            exit_code = launch(args, save_root)
            self.assertEqual(exit_code, 0)

    def test_valid_save_resumes_in_sim(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena", "tier": 3},
                factions={}, npcs={}, locations={}, clocks={},
            )

            state = GameState()
            from emergence.engine.persistence.load import LoadManager
            from emergence.engine.runtime.main import _populate_state

            loader = LoadManager(tmpdir)
            result = loader.load_save()
            _populate_state(state, result)

            self.assertEqual(state.current_mode, "SIM")
            self.assertEqual(state.player["name"], "Elena")


class TestRunCycleDrivenTransitions(unittest.TestCase):

    def test_auto_transition_via_run_cycle(self):
        mgr = ModeManager()
        sz = StubModeHandler(next_mode="FRAMING")
        framing = StubModeHandler(next_mode="SIM")
        sim = StubModeHandler(next_mode=None)  # Stays in SIM
        combat = StubModeHandler()
        gameover = StubModeHandler()

        mgr.register("SESSION_ZERO", sz)
        mgr.register("FRAMING", framing)
        mgr.register("SIM", sim)
        mgr.register("COMBAT", combat)
        mgr.register("GAME_OVER", gameover)

        mgr.start("SESSION_ZERO", {})

        # First cycle: SESSION_ZERO -> FRAMING
        result = mgr.run_cycle({})
        self.assertEqual(result, "FRAMING")

        # Second cycle: FRAMING -> SIM
        result = mgr.run_cycle({})
        self.assertEqual(result, "SIM")

        # Third cycle: SIM stays
        result = mgr.run_cycle({})
        self.assertIsNone(result)
        self.assertEqual(mgr.current_mode, "SIM")


if __name__ == "__main__":
    unittest.main()
