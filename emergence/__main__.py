"""CLI entry point for Emergence.

Usage: python -m emergence [subcommand] [options]

Subcommands: play (default), new, list, inspect, migrate, help.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="emergence",
        description="Emergence — a post-apocalyptic tactical RPG",
    )

    # Global options
    parser.add_argument(
        "--save-root",
        default=os.environ.get("EMERGENCE_SAVE_ROOT", "./saves/default"),
        help="Save directory (env: EMERGENCE_SAVE_ROOT)",
    )
    parser.add_argument(
        "--config",
        default=os.environ.get("EMERGENCE_CONFIG", "./config/emergence.toml"),
        help="Config file path (env: EMERGENCE_CONFIG)",
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warn", "error"],
        default="info",
        help="Logging verbosity",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Log destination (default: {save_root}/logs/runtime.log)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Suppress ANSI color in stdout",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override RNG seed for this session",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print launch plan without mutating save",
    )

    sub = parser.add_subparsers(dest="command", help="Subcommand")

    # play (default)
    play = sub.add_parser("play", help="Start or resume a session")
    play.add_argument("--character", default=None, help="Switch active character")
    play.add_argument("--resume", action="store_true", help="Force resume")
    play.add_argument(
        "--skip-session-zero",
        action="store_true",
        help="Dev/testing: spawn with fixed template",
    )

    # new
    new = sub.add_parser("new", help="Create a new character")
    new.add_argument("--world", default=None, help="World to place character in")
    new.add_argument("--template", default=None, help="Named character template")

    # list
    sub.add_parser("list", help="List saves and characters")

    # inspect
    sub.add_parser("inspect", help="Print validation report for save")

    # migrate
    sub.add_parser("migrate", help="Run migrations on save directory")

    # help
    sub.add_parser("help", help="Print usage and exit")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command or "play"

    if command == "help":
        parser.print_help()
        return 0

    # Resolve save root
    save_root = os.path.abspath(args.save_root)

    # Resolve log file
    if args.log_file is None:
        args.log_file = os.path.join(save_root, "logs", "runtime.log")

    if command == "list":
        return _cmd_list(save_root)

    if command == "inspect":
        return _cmd_inspect(save_root)

    if command == "migrate":
        return _cmd_migrate(save_root, dry_run=args.dry_run)

    if command in ("play", "new"):
        return _cmd_play(args, save_root, force_new=(command == "new"))

    parser.print_help()
    return 1


def _cmd_list(save_root: str) -> int:
    """List saves and characters."""
    from emergence.engine.persistence.load import LoadManager
    from emergence.engine.persistence.multi_character import MultiCharacterManager

    loader = LoadManager(save_root)
    classification = loader.classify()
    print(f"Save root: {save_root}")
    print(f"Classification: {classification}")

    if classification == "FRESH":
        print("No save data found.")
        return 0

    mcm = MultiCharacterManager(save_root)
    active = mcm.get_active_character()
    if active:
        print(f"Active character: {active.get('name', 'Unknown')}")

    archived = mcm.list_characters()
    if archived:
        print(f"\nArchived characters ({len(archived)}):")
        for c in archived:
            print(f"  - {c.get('name', '?')} (reason: {c.get('reason', '?')})")

    return 0


def _cmd_inspect(save_root: str) -> int:
    """Print validation report for save."""
    from emergence.engine.persistence.load import LoadManager

    loader = LoadManager(save_root)
    classification = loader.classify()
    print(f"Save root: {save_root}")
    print(f"Classification: {classification}")

    if classification == "FRESH":
        print("No save data found.")
        return 0

    result = loader.load_save()
    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for e in result.errors:
            print(f"  - {e}")
        return 3 if classification == "CORRUPT" else 0

    print("Save is valid.")
    if result.world:
        print(f"  Schema version: {result.world.get('schema_version', '?')}")
    if result.player:
        print(f"  Player: {result.player.get('name', '?')}")
    return 0


def _cmd_migrate(save_root: str, dry_run: bool = False) -> int:
    """Run migrations on save."""
    from emergence.engine.persistence.migration import SaveMigrator

    migrator = SaveMigrator(save_root)
    if not migrator.needs_migration():
        print("No migration needed.")
        return 0

    old_ver = migrator.get_save_version()
    print(f"Migrating from version {old_ver}...")

    result = migrator.migrate(dry_run=dry_run)
    if dry_run:
        print(f"Dry run: would migrate {len(result.migrated_files)} files")
        return 0

    if result.success:
        print(f"Migration complete. {len(result.migrated_files)} files updated.")
        return 0
    else:
        print(f"Migration failed:")
        for e in result.errors:
            print(f"  - {e}")
        return 3


def _cmd_play(args: argparse.Namespace, save_root: str, force_new: bool = False) -> int:
    """Launch the game."""
    from emergence.engine.runtime.main import launch

    try:
        return launch(args, save_root, force_new=force_new)
    except KeyboardInterrupt:
        print("\nSession interrupted.")
        return 0
    except Exception as e:
        # Import error handling
        try:
            from emergence.engine.runtime.error_handling import (
                FatalError,
                SaveIntegrityError,
                NarratorProtocolError,
                EngineInternalError,
            )
            if isinstance(e, SaveIntegrityError):
                print(f"Save integrity error: {e}")
                return 3
            if isinstance(e, NarratorProtocolError):
                print(f"Narrator protocol error: {e}")
                return 4
            if isinstance(e, EngineInternalError):
                print(f"Engine internal error: {e}")
                return 5
            if isinstance(e, FatalError):
                print(f"Fatal error: {e}")
                return 2
        except ImportError:
            pass
        print(f"Unexpected error: {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
