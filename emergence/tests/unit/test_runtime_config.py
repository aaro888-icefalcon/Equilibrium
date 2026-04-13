"""Unit tests for runtime configuration and error handling."""

import os
import tempfile
import unittest

from emergence.engine.runtime.configuration import (
    GameConfig,
    load_config,
    save_config,
)
from emergence.engine.runtime.error_handling import (
    EmergenceError,
    EngineInternalError,
    FatalError,
    NarratorProtocolError,
    RecoverableError,
    SaveIntegrityError,
    classify_error,
    crash_shutdown,
)


class TestGameConfig(unittest.TestCase):

    def test_defaults(self):
        config = GameConfig()
        self.assertEqual(config.save_root, "saves/default")
        self.assertEqual(config.log_level, "info")
        self.assertEqual(config.seed, 0)
        self.assertTrue(config.color_output)
        self.assertFalse(config.debug_mode)

    def test_load_from_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("save_root = saves/my_game\n")
            f.write("seed = 42\n")
            f.write("debug_mode = true\n")
            f.write("narrator_temperature = 0.9\n")
            path = f.name

        try:
            config = load_config(path)
            self.assertEqual(config.save_root, "saves/my_game")
            self.assertEqual(config.seed, 42)
            self.assertTrue(config.debug_mode)
            self.assertAlmostEqual(config.narrator_temperature, 0.9)
        finally:
            os.unlink(path)

    def test_load_missing_file_returns_defaults(self):
        config = load_config("/nonexistent/path/config.cfg")
        self.assertEqual(config.save_root, "saves/default")

    def test_comments_and_blank_lines_ignored(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("seed = 99\n")
            f.write("# Another comment\n")
            path = f.name

        try:
            config = load_config(path)
            self.assertEqual(config.seed, 99)
        finally:
            os.unlink(path)

    def test_quoted_values(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write('save_root = "saves/my game"\n')
            path = f.name

        try:
            config = load_config(path)
            self.assertEqual(config.save_root, "saves/my game")
        finally:
            os.unlink(path)

    def test_invalid_values_keep_defaults(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("seed = not_a_number\n")
            path = f.name

        try:
            config = load_config(path)
            self.assertEqual(config.seed, 0)  # Default
        finally:
            os.unlink(path)

    def test_unknown_keys_ignored(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            f.write("unknown_key = some_value\n")
            f.write("seed = 7\n")
            path = f.name

        try:
            config = load_config(path)
            self.assertEqual(config.seed, 7)
        finally:
            os.unlink(path)

    def test_save_and_reload(self):
        config = GameConfig(save_root="saves/test", seed=123, debug_mode=True)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg", delete=False) as f:
            path = f.name

        try:
            save_config(config, path)
            loaded = load_config(path)
            self.assertEqual(loaded.save_root, "saves/test")
            self.assertEqual(loaded.seed, 123)
            self.assertTrue(loaded.debug_mode)
        finally:
            os.unlink(path)


class TestErrorHierarchy(unittest.TestCase):

    def test_all_inherit_from_emergence_error(self):
        for cls in [RecoverableError, FatalError, SaveIntegrityError,
                    NarratorProtocolError, EngineInternalError]:
            self.assertTrue(issubclass(cls, EmergenceError))

    def test_exit_codes(self):
        self.assertEqual(RecoverableError.exit_code, 1)
        self.assertEqual(FatalError.exit_code, 2)
        self.assertEqual(SaveIntegrityError.exit_code, 3)
        self.assertEqual(NarratorProtocolError.exit_code, 4)
        self.assertEqual(EngineInternalError.exit_code, 5)


class TestClassifyError(unittest.TestCase):

    def test_classify_recoverable(self):
        self.assertEqual(classify_error(RecoverableError("test")), "recoverable")

    def test_classify_fatal(self):
        self.assertEqual(classify_error(FatalError("test")), "fatal")

    def test_classify_save(self):
        self.assertEqual(classify_error(SaveIntegrityError("test")), "save_corrupt")

    def test_classify_narrator(self):
        self.assertEqual(classify_error(NarratorProtocolError("test")), "narrator_failure")

    def test_classify_internal(self):
        self.assertEqual(classify_error(EngineInternalError("test")), "internal")

    def test_classify_unknown(self):
        self.assertEqual(classify_error(ValueError("test")), "unknown")


class TestCrashShutdown(unittest.TestCase):

    def test_returns_exit_code(self):
        code = crash_shutdown(FatalError("test"))
        self.assertEqual(code, 2)

    def test_returns_1_for_generic_error(self):
        code = crash_shutdown(ValueError("test"))
        self.assertEqual(code, 1)

    def test_emergency_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            crash_shutdown(FatalError("test"), state="some_state", save_root=tmpdir)
            crash_path = os.path.join(tmpdir, "crash_state.json")
            self.assertTrue(os.path.exists(crash_path))


if __name__ == "__main__":
    unittest.main()
