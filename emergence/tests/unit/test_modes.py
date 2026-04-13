"""Unit tests for mode system."""

import unittest

from emergence.engine.runtime.modes import (
    ModeManager,
    ModeError,
    StubModeHandler,
    TRANSITION_TABLE,
)


class TestModeManager(unittest.TestCase):

    def setUp(self):
        self.mgr = ModeManager()
        self.sz = StubModeHandler()
        self.framing = StubModeHandler()
        self.sim = StubModeHandler()
        self.combat = StubModeHandler()
        self.gameover = StubModeHandler()

        self.mgr.register("SESSION_ZERO", self.sz)
        self.mgr.register("FRAMING", self.framing)
        self.mgr.register("SIM", self.sim)
        self.mgr.register("COMBAT", self.combat)
        self.mgr.register("GAME_OVER", self.gameover)

    def test_start_mode(self):
        self.mgr.start("SESSION_ZERO", {})
        self.assertEqual(self.mgr.current_mode, "SESSION_ZERO")
        self.assertTrue(self.sz.entered)

    def test_start_unregistered_raises(self):
        with self.assertRaises(ModeError):
            self.mgr.start("NONEXISTENT", {})

    def test_valid_transition(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.assertEqual(self.mgr.current_mode, "FRAMING")
        self.assertTrue(self.sz.exited)
        self.assertTrue(self.framing.entered)

    def test_invalid_transition_raises(self):
        self.mgr.start("SESSION_ZERO", {})
        with self.assertRaises(ModeError):
            self.mgr.transition("COMBAT", {})

    def test_sim_to_combat(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("COMBAT", {})
        self.assertEqual(self.mgr.current_mode, "COMBAT")

    def test_combat_to_sim(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("COMBAT", {})
        self.mgr.transition("SIM", {})
        self.assertEqual(self.mgr.current_mode, "SIM")

    def test_sim_to_game_over(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("GAME_OVER", {})
        self.assertEqual(self.mgr.current_mode, "GAME_OVER")

    def test_game_over_to_session_zero(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("GAME_OVER", {})
        self.mgr.transition("SESSION_ZERO", {})
        self.assertEqual(self.mgr.current_mode, "SESSION_ZERO")

    def test_cannot_go_backwards_combat_to_framing(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("COMBAT", {})
        with self.assertRaises(ModeError):
            self.mgr.transition("FRAMING", {})

    def test_run_cycle_stays(self):
        self.mgr.start("SESSION_ZERO", {})
        self.sz._next_mode = None
        result = self.mgr.run_cycle({})
        self.assertIsNone(result)
        self.assertEqual(self.sz.cycles, 1)

    def test_run_cycle_transitions(self):
        self.mgr.start("SESSION_ZERO", {})
        self.sz._next_mode = "FRAMING"
        result = self.mgr.run_cycle({})
        self.assertEqual(result, "FRAMING")
        self.assertEqual(self.mgr.current_mode, "FRAMING")

    def test_history_tracking(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.assertEqual(self.mgr.history, ["SESSION_ZERO", "FRAMING", "SIM"])

    def test_transition_without_start_raises(self):
        with self.assertRaises(ModeError):
            self.mgr.transition("SESSION_ZERO", {})

    def test_run_cycle_without_start_raises(self):
        with self.assertRaises(ModeError):
            self.mgr.run_cycle({})

    def test_is_valid_transition(self):
        self.assertTrue(self.mgr.is_valid_transition("SESSION_ZERO", "FRAMING"))
        self.assertFalse(self.mgr.is_valid_transition("SESSION_ZERO", "COMBAT"))
        self.assertTrue(self.mgr.is_valid_transition("SIM", "COMBAT"))
        self.assertTrue(self.mgr.is_valid_transition("COMBAT", "SIM"))

    def test_sim_to_framing_allowed(self):
        self.mgr.start("SESSION_ZERO", {})
        self.mgr.transition("FRAMING", {})
        self.mgr.transition("SIM", {})
        self.mgr.transition("FRAMING", {})
        self.assertEqual(self.mgr.current_mode, "FRAMING")

    def test_all_transitions_in_table(self):
        for mode, targets in TRANSITION_TABLE.items():
            for target in targets:
                self.assertTrue(
                    self.mgr.is_valid_transition(mode, target),
                    f"{mode} -> {target} should be valid",
                )


if __name__ == "__main__":
    unittest.main()
