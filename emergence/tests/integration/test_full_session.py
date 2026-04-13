"""Integration tests for full session lifecycle."""

import json
import os
import tempfile
import unittest

from emergence.engine.runtime.main import (
    GameState,
    LaunchLock,
    launch,
    main_session_loop,
    _populate_state,
)
from emergence.engine.persistence.save import SaveManager
from emergence.engine.persistence.load import LoadManager


class FakeArgs:
    """Fake argparse namespace for testing."""

    def __init__(self, **kwargs):
        self.save_root = kwargs.get("save_root", "/tmp/test")
        self.config = kwargs.get("config", None)
        self.log_level = kwargs.get("log_level", "info")
        self.log_file = kwargs.get("log_file", None)
        self.no_color = kwargs.get("no_color", False)
        self.seed = kwargs.get("seed", 42)
        self.dry_run = kwargs.get("dry_run", False)
        self.character = kwargs.get("character", None)
        self.resume = kwargs.get("resume", False)
        self.skip_session_zero = kwargs.get("skip_session_zero", False)


class TestLaunchLock(unittest.TestCase):

    def test_acquire_and_release(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = LaunchLock(tmpdir)
            self.assertTrue(lock.acquire())
            self.assertTrue(os.path.exists(lock.lock_path))
            lock.release()
            self.assertFalse(os.path.exists(lock.lock_path))

    def test_double_acquire_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock1 = LaunchLock(tmpdir)
            lock2 = LaunchLock(tmpdir)
            self.assertTrue(lock1.acquire())
            self.assertFalse(lock2.acquire())
            lock1.release()

    def test_release_missing_lock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lock = LaunchLock(tmpdir)
            lock.release()  # Should not raise


class TestGameState(unittest.TestCase):

    def test_default_state(self):
        state = GameState()
        self.assertEqual(state.world, {})
        self.assertEqual(state.player, {})
        self.assertFalse(state.session_should_end)
        self.assertEqual(state.narrator_mode, "mock")

    def test_populate_state(self):
        state = GameState()

        class FakeResult:
            world = {"schema_version": "1.0", "day": 42}
            player = {"name": "Elena"}
            factions = {"f1": {}}
            npcs = {"n1": {}}
            locations = {"l1": {}}
            clocks = {"c1": {}}
            metadata = {"session_count": 3}

        _populate_state(state, FakeResult())
        self.assertEqual(state.world["day"], 42)
        self.assertEqual(state.player["name"], "Elena")
        self.assertEqual(state.current_mode, "SIM")

    def test_populate_empty_player_sets_session_zero(self):
        state = GameState()

        class FakeResult:
            world = {}
            player = {}
            factions = {}
            npcs = {}
            locations = {}
            clocks = {}
            metadata = {}

        _populate_state(state, FakeResult())
        self.assertEqual(state.current_mode, "SESSION_ZERO")


class TestDryRun(unittest.TestCase):

    def test_dry_run_fresh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save_root = os.path.join(tmpdir, "save")
            args = FakeArgs(save_root=save_root, seed=42, dry_run=True)
            exit_code = launch(args, save_root)
            self.assertEqual(exit_code, 0)

    def test_dry_run_with_existing_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid save first
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            args = FakeArgs(save_root=tmpdir, seed=42, dry_run=True)
            exit_code = launch(args, tmpdir)
            self.assertEqual(exit_code, 0)


class TestSaveLoadRoundTrip(unittest.TestCase):

    def test_session_creates_save(self):
        """A mock session creates save files on clean shutdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            save_root = os.path.join(tmpdir, "save")
            args = FakeArgs(save_root=save_root, seed=42)

            # Launch will run session zero in mock mode, then shutdown
            exit_code = launch(args, save_root)
            self.assertEqual(exit_code, 0)

            # Check that save files were created on shutdown
            self.assertTrue(os.path.exists(os.path.join(save_root, "world.json")))

    def test_resume_loads_save(self):
        """Resume from an existing save populates state correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid save
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0", "day": 100},
                player={"name": "Elena", "tier": 3},
                factions={"f1": {"id": "f1"}},
                npcs={},
                locations={},
                clocks={},
            )
            args = FakeArgs(save_root=tmpdir, seed=42, dry_run=True)
            exit_code = launch(args, tmpdir)
            self.assertEqual(exit_code, 0)


class TestCorruptSave(unittest.TestCase):

    def test_corrupt_save_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create corrupt save
            with open(os.path.join(tmpdir, "world.json"), "w") as f:
                f.write("not json {{{")

            args = FakeArgs(save_root=tmpdir, seed=42)
            exit_code = launch(args, tmpdir)
            self.assertEqual(exit_code, 3)

    def test_version_mismatch_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "9.9"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            args = FakeArgs(save_root=tmpdir, seed=42)
            exit_code = launch(args, tmpdir)
            self.assertEqual(exit_code, 3)


class TestCLICommands(unittest.TestCase):

    def test_list_fresh_save(self):
        from emergence.__main__ import _cmd_list
        with tempfile.TemporaryDirectory() as tmpdir:
            save_root = os.path.join(tmpdir, "empty_save")
            exit_code = _cmd_list(save_root)
            self.assertEqual(exit_code, 0)

    def test_list_with_character(self):
        from emergence.__main__ import _cmd_list
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            exit_code = _cmd_list(tmpdir)
            self.assertEqual(exit_code, 0)

    def test_inspect_fresh(self):
        from emergence.__main__ import _cmd_inspect
        with tempfile.TemporaryDirectory() as tmpdir:
            save_root = os.path.join(tmpdir, "empty_save")
            exit_code = _cmd_inspect(save_root)
            self.assertEqual(exit_code, 0)

    def test_inspect_valid_save(self):
        from emergence.__main__ import _cmd_inspect
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            exit_code = _cmd_inspect(tmpdir)
            self.assertEqual(exit_code, 0)

    def test_migrate_no_migration_needed(self):
        from emergence.__main__ import _cmd_migrate
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            exit_code = _cmd_migrate(tmpdir)
            self.assertEqual(exit_code, 0)

    def test_main_help(self):
        from emergence.__main__ import main
        exit_code = main(["help"])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
