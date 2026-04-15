"""Unit tests for the step CLI dispatch layer.

Exercises dispatch_step through the full session zero flow and save operations.
Each test uses a fresh temp directory as save_root so tests are isolated.
"""

import argparse
import os
import tempfile
import unittest

from emergence.engine.runtime.step_cli import dispatch_step


def _ns(**kwargs):
    """Build an argparse.Namespace with the given attributes."""
    return argparse.Namespace(**kwargs)


class TestStepStatus(unittest.TestCase):
    """step_status on various save states."""

    def test_fresh_save_returns_fresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch_step(_ns(step_action="status"), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["classification"], "FRESH")
            self.assertIsNone(result["mode"])


class TestStepInit(unittest.TestCase):
    """step_init creates a valid world."""

    def test_init_creates_world(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertGreater(result["faction_count"], 0)
            self.assertGreater(result["npc_count"], 0)
            self.assertGreater(result["location_count"], 0)
            self.assertEqual(result["mode"], "SESSION_ZERO")

    def test_init_is_idempotent_without_force(self):
        """Calling init twice without --force should error."""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            second = dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            self.assertEqual(second["status"], "error")
            self.assertIn("already exists", second["message"])


class TestStepStatusAfterInit(unittest.TestCase):
    """step_status after init should reflect SESSION_ZERO mode."""

    def test_status_shows_session_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(_ns(step_action="status"), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["mode"], "SESSION_ZERO")
            self.assertIn("session_zero_scene", result)
            self.assertEqual(result["session_zero_scene"], 0)


class TestStepScene(unittest.TestCase):
    """step_scene returns framing and text prompt metadata."""

    def test_scene_index_0_returns_framing(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(_ns(step_action="scene", index=0), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["scene_index"], 0)
            self.assertTrue(len(result["framing_text"]) > 0)
            self.assertTrue(result["needs_text_input"])

    def test_scene_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(_ns(step_action="scene", index=99), tmp)
            self.assertEqual(result["status"], "error")
            self.assertIn("out of range", result["message"])


class TestStepSceneApply(unittest.TestCase):
    """step_scene_apply accepts text inputs and choice selections."""

    def test_apply_text_inputs_scene_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(
                _ns(
                    step_action="scene-apply",
                    index=0,
                    input_choice=None,
                    input_text=["name=Test Runner", "age=30"],
                    seed=42,
                ),
                tmp,
            )
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["applied"])
            self.assertEqual(result["creation_summary"]["name"], "Test Runner")
            self.assertEqual(result["creation_summary"]["age"], 30)
            self.assertEqual(result["next_scene"], 1)

    def test_apply_choice_scene_1(self):
        """Apply a choice on scene 1 (Occupation) after completing scene 0."""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            # Scene 0: text input
            dispatch_step(
                _ns(
                    step_action="scene-apply",
                    index=0,
                    input_choice=None,
                    input_text=["name=Test Runner", "age=25"],
                    seed=42,
                ),
                tmp,
            )
            # Scene 1: choice input (occupation)
            result = dispatch_step(
                _ns(
                    step_action="scene-apply",
                    index=1,
                    input_choice=0,
                    input_text=None,
                    seed=42,
                ),
                tmp,
            )
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["applied"])
            self.assertEqual(result["next_scene"], 2)


class TestStepSceneFinalize(unittest.TestCase):
    """step_scene_finalize produces a character with name and tier."""

    def test_finalize_produces_character(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            # Walk through all 8 scenes
            _apply_all_scenes(tmp)
            # Finalize
            result = dispatch_step(_ns(step_action="scene-finalize"), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["mode"], "SIM")
            player = result["player"]
            self.assertTrue(len(player["name"]) > 0)
            self.assertGreaterEqual(player["tier"], 1)


class TestFullSessionZeroWalkthrough(unittest.TestCase):
    """Full init -> 8 scenes -> finalize integration test."""

    def test_walkthrough(self):
        with tempfile.TemporaryDirectory() as tmp:
            # 1. Init
            init_result = dispatch_step(
                _ns(step_action="init", force=False, seed=42), tmp
            )
            self.assertEqual(init_result["status"], "ok")

            # 2. Walk all 8 scenes
            _apply_all_scenes(tmp)

            # 3. Finalize
            final = dispatch_step(_ns(step_action="scene-finalize"), tmp)
            self.assertEqual(final["status"], "ok")
            self.assertEqual(final["mode"], "SIM")
            self.assertTrue(len(final["player"]["name"]) > 0)
            self.assertGreaterEqual(final["player"]["tier"], 1)

            # 4. Verify status is now SIM (session_zero_state.json removed)
            status = dispatch_step(_ns(step_action="status"), tmp)
            self.assertEqual(status["mode"], "SIM")
            self.assertNotIn("session_zero_scene", status)

            # 5. Verify the character sheet was persisted
            self.assertIn("character_sheet", final)
            sheet = final["character_sheet"]
            self.assertIn("attributes", sheet)
            self.assertIn("name", sheet)


class TestStepSave(unittest.TestCase):
    """step_save works after a character exists."""

    def test_save_after_finalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            _apply_all_scenes(tmp)
            dispatch_step(_ns(step_action="scene-finalize"), tmp)
            result = dispatch_step(_ns(step_action="save"), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertIn("saved", result["message"].lower())
            self.assertEqual(result["mode"], "SIM")

    def test_save_on_fresh_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch_step(_ns(step_action="save"), tmp)
            self.assertEqual(result["status"], "error")


class TestStepPreamble(unittest.TestCase):
    """step preamble generates opening narration payload."""

    def test_preamble_after_finalize(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            _apply_all_scenes(tmp)
            dispatch_step(_ns(step_action="scene-finalize"), tmp)
            result = dispatch_step(_ns(step_action="preamble"), tmp)
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["mode"], "SIM")
            payload = result["narrator_payload"]
            self.assertEqual(payload["scene_type"], "scene_framing")
            self.assertTrue(payload["preamble"])
            self.assertIn("character_identity", payload)
            self.assertTrue(len(payload["character_identity"]["name"]) > 0)

    def test_preamble_without_character_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch_step(_ns(step_action="preamble"), tmp)
            self.assertEqual(result["status"], "error")


class TestDispatchUnknownAction(unittest.TestCase):
    """dispatch_step handles unknown step actions gracefully."""

    def test_unknown_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = dispatch_step(_ns(step_action="nonexistent"), tmp)
            self.assertEqual(result["status"], "error")
            self.assertIn("Unknown", result["message"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_all_scenes(save_root: str) -> None:
    """Walk through all 8 v2 session zero scenes with deterministic inputs."""
    # Scene 0: text input (name + age)
    dispatch_step(
        _ns(
            step_action="scene-apply",
            index=0,
            input_choice=None,
            input_text=["name=Marisol Reyes", "age=30"],
            seed=42,
        ),
        save_root,
    )
    # Scenes 1-7: choice-based, always pick index 0
    for i in range(1, 8):
        dispatch_step(
            _ns(
                step_action="scene-apply",
                index=i,
                input_choice=0,
                input_text=None,
                seed=42,
            ),
            save_root,
        )


if __name__ == "__main__":
    unittest.main()
