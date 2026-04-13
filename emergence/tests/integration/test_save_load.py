"""Integration tests for save/load persistence layer."""

import json
import os
import tempfile
import unittest

from emergence.engine.persistence.save import SaveManager
from emergence.engine.persistence.load import LoadManager, LoadResult
from emergence.engine.persistence.migration import SaveMigrator, MigrationResult
from emergence.engine.persistence.multi_character import MultiCharacterManager


class TestSaveManager(unittest.TestCase):

    def test_full_save_creates_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0", "time": 0},
                player={"name": "Test"},
                factions={"f1": {"id": "f1"}},
                npcs={"n1": {"id": "n1"}},
                locations={"l1": {"id": "l1"}},
                clocks={"c1": {"id": "c1"}},
            )

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "world.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "player/character.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "factions.json")))

    def test_full_save_is_valid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Test"},
                factions={}, npcs={}, locations={}, clocks={},
            )

            with open(os.path.join(tmpdir, "world.json")) as f:
                data = json.load(f)
                self.assertEqual(data["schema_version"], "1.0")

    def test_save_throttling(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.MIN_SAVE_INTERVAL = 10  # 10 seconds for test

            result1 = save.full_save(
                world={}, player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            result2 = save.full_save(
                world={}, player={}, factions={}, npcs={}, locations={}, clocks={},
            )

            self.assertTrue(result1)
            self.assertFalse(result2)  # Throttled

    def test_lightweight_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.lightweight_save({"round": 3, "enemies": []})

            path = os.path.join(tmpdir, "combat_state.json")
            self.assertTrue(os.path.exists(path))

    def test_save_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            self.assertFalse(save.save_exists())

            save.full_save(
                world={}, player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            self.assertTrue(save.save_exists())

    def test_list_save_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={}, player={"name": "test"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            files = save.list_save_files()
            self.assertIn("world.json", files)
            self.assertIn(os.path.join("player", "character.json"), files)


class TestLoadManager(unittest.TestCase):

    def test_fresh_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = os.path.join(tmpdir, "empty_save")
            loader = LoadManager(empty)
            self.assertEqual(loader.classify(), "FRESH")

    def test_valid_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "test"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            loader = LoadManager(tmpdir)
            self.assertEqual(loader.classify(), "VALID")

    def test_partial_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only player file, no world.json
            os.makedirs(os.path.join(tmpdir, "player"))
            with open(os.path.join(tmpdir, "player/character.json"), "w") as f:
                json.dump({"name": "test"}, f)

            loader = LoadManager(tmpdir)
            self.assertEqual(loader.classify(), "PARTIAL")

    def test_corrupt_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "world.json"), "w") as f:
                f.write("not valid json {{{")

            loader = LoadManager(tmpdir)
            self.assertEqual(loader.classify(), "CORRUPT")

    def test_version_mismatch_classification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "9.9"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            loader = LoadManager(tmpdir)
            self.assertEqual(loader.classify(), "VERSION_MISMATCH")

    def test_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0", "current_time": {"day": 42}},
                player={"name": "Elena", "tier": 3},
                factions={"f1": {"id": "f1", "name": "Test Faction"}},
                npcs={"n1": {"id": "n1"}},
                locations={"l1": {"id": "l1"}},
                clocks={"c1": {"id": "c1"}},
            )

            # Load
            loader = LoadManager(tmpdir)
            result = loader.load_save()

            self.assertEqual(result.classification, "VALID")
            self.assertEqual(result.world["current_time"]["day"], 42)
            self.assertEqual(result.player["name"], "Elena")
            self.assertEqual(result.factions["f1"]["name"], "Test Faction")

    def test_load_result_has_errors_for_partial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only create world.json
            with open(os.path.join(tmpdir, "world.json"), "w") as f:
                json.dump({"schema_version": "1.0"}, f)

            loader = LoadManager(tmpdir)
            result = loader.load_save()
            self.assertEqual(result.classification, "PARTIAL")
            self.assertGreater(len(result.errors), 0)

    def test_cleanup_stale_temps(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create stale temp files
            with open(os.path.join(tmpdir, "world.json.tmp"), "w") as f:
                f.write("stale")
            with open(os.path.join(tmpdir, "factions.json.tmp"), "w") as f:
                f.write("stale")

            loader = LoadManager(tmpdir)
            count = loader.cleanup_stale_temps()
            self.assertEqual(count, 2)
            self.assertFalse(os.path.exists(os.path.join(tmpdir, "world.json.tmp")))


class TestSaveMigrator(unittest.TestCase):

    def test_no_migration_needed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            migrator = SaveMigrator(tmpdir)
            self.assertFalse(migrator.needs_migration())

    def test_needs_migration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "world.json"), "w") as f:
                json.dump({"schema_version": "0.9"}, f)
            migrator = SaveMigrator(tmpdir)
            self.assertTrue(migrator.needs_migration())

    def test_get_save_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            migrator = SaveMigrator(tmpdir)
            self.assertEqual(migrator.get_save_version(), "1.0")

    def test_get_save_version_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            migrator = SaveMigrator(tmpdir)
            self.assertIsNone(migrator.get_save_version())

    def test_migrate_already_current(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={}, factions={}, npcs={}, locations={}, clocks={},
            )
            migrator = SaveMigrator(tmpdir)
            result = migrator.migrate()
            self.assertTrue(result.success)
            self.assertEqual(len(result.migrated_files), 0)

    def test_dry_run_no_writes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "world.json"), "w") as f:
                json.dump({"schema_version": "0.9"}, f)
            migrator = SaveMigrator(tmpdir)
            result = migrator.migrate(dry_run=True)
            # Should still report old version
            self.assertEqual(result.from_version, "0.9")

    def test_migrate_no_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            empty = os.path.join(tmpdir, "empty")
            migrator = SaveMigrator(empty)
            result = migrator.migrate()
            self.assertFalse(result.success)
            self.assertGreater(len(result.errors), 0)


class TestMultiCharacterManager(unittest.TestCase):

    def test_archive_character(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena", "tier": 3},
                factions={}, npcs={}, locations={}, clocks={},
            )
            mcm = MultiCharacterManager(tmpdir)
            self.assertTrue(mcm.has_active_character())

            archive_id = mcm.archive_character(reason="death")
            self.assertIsNotNone(archive_id)
            self.assertIn("Elena", archive_id)
            self.assertFalse(mcm.has_active_character())

    def test_list_characters_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcm = MultiCharacterManager(tmpdir)
            self.assertEqual(mcm.list_characters(), [])

    def test_list_archived_characters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena"},
                factions={}, npcs={}, locations={}, clocks={},
            )
            mcm = MultiCharacterManager(tmpdir)
            mcm.archive_character(reason="death")

            chars = mcm.list_characters()
            self.assertEqual(len(chars), 1)
            self.assertEqual(chars[0]["name"], "Elena")
            self.assertEqual(chars[0]["reason"], "death")

    def test_switch_character(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena", "tier": 3},
                factions={}, npcs={}, locations={}, clocks={},
            )
            mcm = MultiCharacterManager(tmpdir)

            # Archive Elena
            archive_id = mcm.archive_character(reason="death")

            # Create new active character
            player_dir = os.path.join(tmpdir, "player")
            os.makedirs(player_dir, exist_ok=True)
            with open(os.path.join(player_dir, "character.json"), "w") as f:
                json.dump({"name": "Marcus", "tier": 1}, f)

            # Switch back to Elena
            result = mcm.switch_character(archive_id)
            self.assertTrue(result)

            active = mcm.get_active_character()
            self.assertEqual(active["name"], "Elena")

            # Marcus should be archived
            chars = mcm.list_characters()
            names = [c["name"] for c in chars]
            self.assertIn("Marcus", names)

    def test_switch_nonexistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcm = MultiCharacterManager(tmpdir)
            self.assertFalse(mcm.switch_character("nonexistent_12345"))

    def test_get_active_character(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            save = SaveManager(tmpdir)
            save.full_save(
                world={"schema_version": "1.0"},
                player={"name": "Elena", "tier": 3},
                factions={}, npcs={}, locations={}, clocks={},
            )
            mcm = MultiCharacterManager(tmpdir)
            active = mcm.get_active_character()
            self.assertEqual(active["name"], "Elena")

    def test_archive_no_active(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mcm = MultiCharacterManager(tmpdir)
            result = mcm.archive_character()
            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
