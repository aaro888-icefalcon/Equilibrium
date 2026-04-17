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
            # Scene 0 is the intro — prose-only, no text input required.
            self.assertFalse(result["needs_text_input"])

    def test_scene_1_life_needs_text_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(_ns(step_action="scene", index=1), tmp)
            self.assertTrue(result["needs_text_input"])
            prompt_keys = {p["key"] for p in result["text_prompts"]}
            self.assertIn("name", prompt_keys)
            self.assertIn("description", prompt_keys)
            self.assertIn("npc_seeds", prompt_keys)

    def test_scene_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(_ns(step_action="scene", index=99), tmp)
            self.assertEqual(result["status"], "error")
            self.assertIn("out of range", result["message"])


class TestStepSceneApply(unittest.TestCase):
    """step_scene_apply accepts text inputs and choice selections."""

    def test_apply_intro_with_choice(self):
        """Scene 0 (intro) advances on --input-choice 0."""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            result = dispatch_step(
                _ns(
                    step_action="scene-apply",
                    index=0,
                    input_choice=0,
                    input_text=None,
                    seed=42,
                ),
                tmp,
            )
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["applied"])
            self.assertEqual(result["next_scene"], 1)

    def test_apply_life_scene_text(self):
        """Scene 1 (life) advances on text alone (no choice menu)."""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            dispatch_step(
                _ns(step_action="scene-apply", index=0,
                    input_choice=0, input_text=None, seed=42),
                tmp,
            )
            result = dispatch_step(
                _ns(
                    step_action="scene-apply",
                    index=1,
                    input_choice=None,
                    input_text=[
                        "name=Test Runner",
                        "age=30",
                        "description=blunt surgeon curious and analytical",
                    ],
                    seed=42,
                ),
                tmp,
            )
            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["applied"])
            self.assertEqual(result["creation_summary"]["name"], "Test Runner")
            self.assertEqual(result["creation_summary"]["age"], 30)
            self.assertEqual(result["next_scene"], 2)

    def test_slate_scene_two_phase(self):
        """Scene 3 (power slate) needs a choice to advance; text-only call
        persists pending_slate without advancing."""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch_step(_ns(step_action="init", force=False, seed=42), tmp)
            # 0: intro
            dispatch_step(_ns(step_action="scene-apply", index=0,
                              input_choice=0, input_text=None, seed=42), tmp)
            # 1: life
            dispatch_step(_ns(
                step_action="scene-apply", index=1,
                input_choice=None,
                input_text=[
                    "name=Runner", "age=30",
                    "description=surgeon curious and analytical",
                ],
                seed=42,
            ), tmp)
            # 2: action
            dispatch_step(_ns(
                step_action="scene-apply", index=2,
                input_choice=None,
                input_text=["reaction=I reach and study what I can see"],
                seed=42,
            ), tmp)
            # 3: slate — text only, should NOT advance
            phase_1 = dispatch_step(_ns(
                step_action="scene-apply", index=3,
                input_choice=None,
                input_text=["reaction=I watch and think"],
                seed=42,
            ), tmp)
            self.assertFalse(phase_1["applied"])
            self.assertEqual(phase_1["awaiting"], "choice")
            self.assertEqual(len(phase_1["pending_slate"]), 10)

            # 3: slate — choice step, advances
            phase_2 = dispatch_step(_ns(
                step_action="scene-apply", index=3,
                input_choice="0,1",
                input_text=None,
                seed=42,
            ), tmp)
            self.assertTrue(phase_2["applied"])
            self.assertEqual(phase_2["next_scene"], 4)
            self.assertEqual(
                len(phase_2["creation_summary"]["powers"]), 2,
            )


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
    """Walk through all 13 v2 session zero scenes with deterministic inputs.

    Per-scene inputs:
      0 intro       — choice 0 (Continue)
      1 life        — name / age / description / empty npc_seeds
      2 action      — reaction text
      3 slate       — reaction + two-pick choice '0,1'
      4-7 cast/rider — narrative text + choice 0
      8-12 rest     — choice 0
    """
    # 0 intro
    dispatch_step(_ns(
        step_action="scene-apply", index=0,
        input_choice=0, input_text=None, seed=42,
    ), save_root)

    # 1 life
    dispatch_step(_ns(
        step_action="scene-apply", index=1,
        input_choice=None,
        input_text=[
            "name=Marisol Reyes",
            "age=30",
            "description=blunt surgeon curious and analytical",
            "npc_seeds=[]",
        ],
        seed=42,
    ), save_root)

    # 2 action
    dispatch_step(_ns(
        step_action="scene-apply", index=2,
        input_choice=None,
        input_text=["reaction=I reach in and work with my hands"],
        seed=42,
    ), save_root)

    # 3 slate — single call with both text and choice exercises the
    # orchestrator's combined path.
    dispatch_step(_ns(
        step_action="scene-apply", index=3,
        input_choice="0,1",
        input_text=["reaction=I stay still and study"],
        seed=42,
    ), save_root)

    # 4-7 cast / rider — narrative text + choice 0
    for i in range(4, 8):
        dispatch_step(_ns(
            step_action="scene-apply", index=i,
            input_choice=0,
            input_text=["narrative=Jason saw me do it first."],
            seed=42,
        ), save_root)

    # 8-12 remainder — choice 0
    for i in range(8, 13):
        dispatch_step(_ns(
            step_action="scene-apply", index=i,
            input_choice=0, input_text=None, seed=42,
        ), save_root)


if __name__ == "__main__":
    unittest.main()
