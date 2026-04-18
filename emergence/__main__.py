"""CLI entry point for Emergence.

Usage: python -m emergence [subcommand] [options]

Subcommands: play (default), new, list, inspect, migrate, step, help.
"""

from __future__ import annotations

import argparse
import json
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

    # step — discrete commands for Claude Code orchestration
    step = sub.add_parser("step", help="Step-mode commands for Claude Code")
    step_sub = step.add_subparsers(dest="step_action", help="Step action")

    # step init
    step_init = step_sub.add_parser("init", help="Initialize a new game world")
    step_init.add_argument("--force", action="store_true", help="Overwrite existing save")

    # step status
    step_sub.add_parser("status", help="Show current game state")

    # step pre-emergence — text elicitation + classifier apply
    step_pre = step_sub.add_parser("pre-emergence", help="Pre-Onset biography elicitation + classifier")
    step_pre.add_argument("--mode", choices=["prompt", "apply-text", "apply-classifier"], default="prompt")
    step_pre.add_argument("--input-text", action="append", default=None, dest="input_text",
                           help="Text input as key=value (repeatable)")
    step_pre.add_argument("--input-json", default=None, dest="input_json",
                           help="Path to narrator classifier JSON output")

    # step pick-power — two-phase power pick (subcats -> powers); auto cast/rider
    step_pwr = step_sub.add_parser("pick-power", help="Power pick (6/30 subcategories, then 3+3 powers)")
    step_pwr.add_argument("--picks", default=None,
                           help="Comma-separated indices of current offer (e.g. '1,4')")

    # step pick-location — post-Onset settlement pick
    step_loc = step_sub.add_parser("pick-location", help="Post-Onset settlement pick")
    step_loc.add_argument("--index", type=int, default=None, help="Location choice index")

    # step pick-job — narrator bundle generation + player pick
    step_job = step_sub.add_parser("pick-job", help="Job bundle generation + pick")
    step_job.add_argument("--mode", choices=["prompt", "apply", "pick"], default="prompt")
    step_job.add_argument("--input-json", default=None, dest="input_json",
                           help="Path to narrator bundle_output JSON")
    step_job.add_argument("--index", type=int, default=None, help="Pick index into 5 cards")

    # step pick-quest — narrator quest-pool generation + urgent pick
    step_qp = step_sub.add_parser("pick-quest", help="Quest generation + urgent pick")
    step_qp.add_argument("--mode", choices=["prompt", "apply", "pick"], default="prompt")
    step_qp.add_argument("--input-json", default=None, dest="input_json",
                          help="Path to narrator quest_pool JSON")
    step_qp.add_argument("--index", type=int, default=None, help="Pick index into 4 urgent offers")

    # step bridge — 1500-word bridge + opening scene
    step_br = step_sub.add_parser("bridge", help="Bridge narrative + opening scene")
    step_br.add_argument("--mode", choices=["prompt", "apply"], default="prompt")
    step_br.add_argument("--input-json", default=None, dest="input_json",
                          help="Path to narrator bridge_output JSON")

    # step scene-finalize
    step_sub.add_parser("scene-finalize", help="Finalize character from session zero")

    # step preamble
    step_sub.add_parser("preamble", help="Generate opening narration after character creation")

    # step tick
    step_tick = step_sub.add_parser("tick", help="Advance world simulation")
    step_tick.add_argument("--days", type=int, default=1, help="Days to advance (default: 1)")

    # step situation
    step_sub.add_parser("situation", help="Generate current player situation")

    # step resolve
    step_resolve = step_sub.add_parser("resolve", help="Resolve player choice")
    step_resolve.add_argument("--choice-id", required=True, help="ID of chosen action")

    # step scene-open (AngryGM-style scene coding — replaces step situation)
    step_sub.add_parser("scene-open", help="Open a new scene with scene coding")

    # step scene-continue (mid-scene beat after resolve-action)
    step_sub.add_parser("scene-continue", help="Continue current scene after an action")

    # step scene-close (when DQ is resolved)
    step_sub.add_parser("scene-close", help="Close the current scene")

    # step resolve-action (new dice-backed resolver)
    step_ra = step_sub.add_parser("resolve-action", help="Resolve a declared action with dice")
    step_ra.add_argument("--type", required=True, dest="action_type",
                         choices=["social", "physical", "investigate", "travel",
                                  "medical", "craft", "wait", "exposition"],
                         help="Action type")
    step_ra.add_argument("--approach", required=True, help="Approach (e.g. persuade, force, observe)")
    step_ra.add_argument("--target", default=None, help="Target NPC or object ID")
    step_ra.add_argument("--skill", default=None, help="Skill to use (e.g. negotiation, first_aid)")

    # step combat-start
    step_sub.add_parser("combat-start", help="Start a combat encounter")

    # step combat-round
    step_round = step_sub.add_parser("combat-round", help="Process one combat round")
    step_round.add_argument("--verb", required=True, help="Combat verb")
    step_round.add_argument("--target", default=None, help="Target ID")
    step_round.add_argument("--power", default=None, help="Power ID")

    # step save
    step_sub.add_parser("save", help="Manual save")

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

    if command == "step":
        return _cmd_step(args, save_root)

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


def _cmd_step(args: argparse.Namespace, save_root: str) -> int:
    """Run a step command and output JSON."""
    from emergence.engine.runtime.step_cli import dispatch_step

    if not getattr(args, "step_action", None):
        print(json.dumps({"status": "error", "message": "No step action specified. Use --help."}))
        return 1

    result = dispatch_step(args, save_root)
    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") == "ok" else 1


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
