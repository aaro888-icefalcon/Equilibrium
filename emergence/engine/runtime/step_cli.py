"""Step CLI — discrete, one-shot commands for Claude Code orchestration.

Each step function loads state from save, performs one atomic operation,
saves state back, and returns a dict that __main__.py serializes to JSON.

This enables Claude to orchestrate the game loop by calling individual
step commands via Bash, reading the JSON output, and generating narration.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional


def dispatch_step(args: Any, save_root: str) -> Dict[str, Any]:
    """Route to the appropriate step handler."""
    action = getattr(args, "step_action", None)

    from emergence.engine.runtime.step_creation import (
        step_pre_emergence,
        step_pick_power,
        step_pick_location,
        step_pick_job,
        step_pick_quest,
        step_bridge,
    )

    handlers = {
        "init": step_init,
        "status": step_status,
        # New six-scene character creation flow
        "pre-emergence": step_pre_emergence,
        "pick-power": step_pick_power,
        "pick-location": step_pick_location,
        "pick-job": step_pick_job,
        "pick-quest": step_pick_quest,
        "bridge": step_bridge,
        # Sim + combat (unchanged)
        "scene-finalize": step_scene_finalize,
        "preamble": step_preamble,
        "tick": step_tick,
        "situation": step_situation,
        "resolve": step_resolve,
        "combat-start": step_combat_start,
        "combat-round": step_combat_round,
        "resolve-action": step_resolve_action,
        "scene-open": step_scene_open,
        "scene-continue": step_scene_continue,
        "scene-close": step_scene_close,
        "save": step_save,
    }

    handler = handlers.get(action)
    if handler is None:
        return {"status": "error", "message": f"Unknown step action: {action}"}

    try:
        return handler(args, save_root)
    except Exception as e:
        return {"status": "error", "message": str(e), "error_type": type(e).__name__}


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def _load_full_state(save_root: str) -> Dict[str, Any]:
    """Load all game state from save files."""
    from emergence.engine.persistence.load import LoadManager

    loader = LoadManager(save_root)
    result = loader.load_save()
    return {
        "world": result.world or {},
        "player": result.player or {},
        "factions": result.factions or {},
        "npcs": result.npcs or {},
        "locations": result.locations or {},
        "clocks": result.clocks or {},
        "metadata": result.metadata or {},
    }


def _save_full_state(save_root: str, state: Dict[str, Any]) -> None:
    """Save all game state to save files."""
    from emergence.engine.persistence.save import SaveManager

    mgr = SaveManager(save_root)
    mgr.full_save(
        world=state["world"],
        player=state["player"],
        factions=state["factions"],
        npcs=state["npcs"],
        locations=state["locations"],
        clocks=state["clocks"],
        metadata=state.get("metadata"),
    )


def _get_rng(args: Any) -> random.Random:
    """Get RNG, optionally seeded."""
    seed = getattr(args, "seed", None)
    if seed is not None:
        return random.Random(seed)
    return random.Random()


def _read_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Read a JSON file, return None if missing."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json_file(path: str, data: Any) -> None:
    """Write data as JSON."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _detect_mode(save_root: str) -> str:
    """Detect current game mode from file presence."""
    if os.path.exists(os.path.join(save_root, "combat_state.json")):
        return "COMBAT"
    if os.path.exists(os.path.join(save_root, "session_zero_state.json")):
        return "SESSION_ZERO"
    return "SIM"


def _player_summary(player: Dict[str, Any]) -> Dict[str, Any]:
    """Build a compact player summary for output."""
    return {
        "name": player.get("name", "Unknown"),
        "age": player.get("age", "?"),
        "species": player.get("species", "human"),
        "tier": player.get("tier", 1),
        "home_region": player.get("home_region", "Unknown"),
        "corruption": player.get("corruption", 0),
        "power_category": player.get("power_category_primary", ""),
    }


# ---------------------------------------------------------------------------
# Step handlers
# ---------------------------------------------------------------------------

def step_init(args: Any, save_root: str) -> Dict[str, Any]:
    """Initialize a new game world."""
    from emergence.engine.persistence.load import LoadManager

    # Check if save already exists
    loader = LoadManager(save_root)
    classification = loader.classify()
    if classification == "VALID" and not getattr(args, "force", False):
        return {
            "status": "error",
            "message": "Save already exists. Use --force to overwrite.",
            "classification": classification,
        }

    from emergence.engine.sim.initial_state import build_initial_world
    from emergence.engine.sim.content_loader import ContentLoader

    content_loader = ContentLoader()
    world, factions, npcs, locations, clocks = build_initial_world(content_loader)

    state = {
        "world": world.to_dict(),
        "player": {},
        "factions": {k: v.to_dict() for k, v in factions.items()},
        "npcs": {k: v.to_dict() for k, v in npcs.items()},
        "locations": {k: v.to_dict() for k, v in locations.items()},
        "clocks": {k: v.to_dict() for k, v in clocks.items()},
        "metadata": {"created": time.time(), "schema_version": "1.0"},
    }

    _save_full_state(save_root, state)

    # Initialize session zero state with a real entropy seed. Without this,
    # CreationState.seed defaults to 0 and every character creation reuses
    # Random(317) for the power slate and Random(101) for the vignette —
    # making "random" fillers deterministic across players.
    sz_state = {
        "current_scene": 0,
        "creation_state": {"seed": random.Random().getrandbits(64)},
        "completed": False,
    }
    _write_json_file(os.path.join(save_root, "session_zero_state.json"), sz_state)

    return {
        "status": "ok",
        "mode": "SESSION_ZERO",
        "world_time": world.current_day if hasattr(world, "current_day") else "T+1",
        "faction_count": len(factions),
        "npc_count": len(npcs),
        "location_count": len(locations),
        "save_root": save_root,
        "message": "World initialized. Begin Session Zero with 'step pre-emergence --mode prompt'.",
    }


def step_status(args: Any, save_root: str) -> Dict[str, Any]:
    """Return current game state summary."""
    from emergence.engine.persistence.load import LoadManager

    loader = LoadManager(save_root)
    classification = loader.classify()

    if classification == "FRESH":
        return {
            "status": "ok",
            "classification": "FRESH",
            "mode": None,
            "message": "No save data. Use 'step init' to start a new game.",
        }

    if classification in ("CORRUPT", "VERSION_MISMATCH"):
        return {
            "status": "error",
            "classification": classification,
            "message": f"Save is {classification}. Run 'emergence migrate' or delete the save.",
        }

    result = loader.load_save()
    mode = _detect_mode(save_root)
    player = result.player or {}

    output = {
        "status": "ok",
        "classification": classification,
        "mode": mode,
        "player": _player_summary(player) if player.get("name") else None,
    }

    if result.world:
        output["world_time"] = result.world.get("current_day", "?")
        output["season"] = result.world.get("season", "?")

    # If in session zero, report progress
    if mode == "SESSION_ZERO":
        sz_state = _read_json_file(os.path.join(save_root, "session_zero_state.json"))
        if sz_state:
            output["session_zero_scene"] = sz_state.get("current_scene", 0)

    # If in combat, report combat state
    if mode == "COMBAT":
        combat = _read_json_file(os.path.join(save_root, "combat_state.json"))
        if combat:
            output["combat_round"] = combat.get("round", 0)

    return output


def step_scene(args: Any, save_root: str) -> Dict[str, Any]:
    """Get session zero scene setup (framing, choices, text prompts)."""
    index = getattr(args, "index", 0)

    from emergence.engine.runtime.main import _make_all_scenes
    from emergence.engine.character_creation.character_factory import CreationState

    scenes = _make_all_scenes()
    if index < 0 or index >= len(scenes):
        return {"status": "error", "message": f"Scene index {index} out of range (0-{len(scenes)-1})."}

    scene = scenes[index]

    # Load creation state
    sz_path = os.path.join(save_root, "session_zero_state.json")
    sz_data = _read_json_file(sz_path)
    if sz_data is None:
        return {"status": "error", "message": "No session zero in progress. Run 'step init' first."}

    creation_state = CreationState(**(sz_data.get("creation_state", {})))

    # v4 ack gate: if a prior scene is awaiting an ack beat, refuse to
    # advance until 'step scene-ack --index <prior>' consumes the flag.
    if creation_state.pending_ack and index > sz_data.get("current_scene", 0):
        return {
            "status": "error",
            "message": (
                f"pending ack for scene {sz_data.get('current_scene', 0)}. "
                f"Run 'step scene-ack --index {sz_data.get('current_scene', 0)}' "
                f"before advancing."
            ),
            "awaiting": "ack",
            "pending_ack_for": sz_data.get("current_scene", 0),
        }

    rng = _get_rng(args)
    scene.prepare(creation_state, rng)

    framing = scene.get_framing(creation_state)
    choices = scene.get_choices(creation_state)
    needs_text = scene.needs_text_input()

    text_prompts: List[Dict[str, str]] = []
    if needs_text:
        text_prompts = list(scene.text_prompts(creation_state))

    # Build narrator payload — enriched with v3 scene hooks if available.
    from emergence.engine.narrator.payloads import build_character_creation_payload
    scenario_code = (
        scene.get_scenario_code(creation_state)
        if hasattr(scene, "get_scenario_code")
        else {}
    )
    known_npcs = (
        scene.get_known_npcs(creation_state)
        if hasattr(scene, "get_known_npcs")
        else []
    )
    must_state = (
        scene.get_must_state_mechanics(creation_state)
        if hasattr(scene, "get_must_state_mechanics")
        else []
    )
    choice_groups = (
        scene.get_choice_groups(creation_state)
        if hasattr(scene, "get_choice_groups")
        else []
    )
    payload = build_character_creation_payload(
        scene_id=scene.scene_id,
        framing_text=framing,
        choices=[str(c) for c in choices],
        register=scene.register,
        scenario_code=scenario_code,
        known_npcs=known_npcs,
        must_state_mechanics=must_state,
        choice_groups=choice_groups,
    )

    return {
        "status": "ok",
        "mode": "SESSION_ZERO",
        "scene_index": index,
        "scene_id": scene.scene_id,
        "framing_text": framing,
        "choices": choices,
        "needs_text_input": needs_text,
        "text_prompts": text_prompts,
        "scenario_code": scenario_code,
        "known_npcs": known_npcs,
        "must_state_mechanics": must_state,
        "choice_groups": choice_groups,
        "narrator_payload": payload,
    }


def _parse_choice_indices(input_choice: Any) -> List[int]:
    """Normalize --input-choice into a list of ints.

    Accepts int (single pick), or comma-separated string (multi-pick, used by
    the power-slate scene's pick-two step).  Returns [] if input is None or
    unparseable.
    """
    if input_choice is None:
        return []
    if isinstance(input_choice, int):
        return [input_choice]
    if isinstance(input_choice, (list, tuple)):
        out: List[int] = []
        for item in input_choice:
            try:
                out.append(int(item))
            except (TypeError, ValueError):
                continue
        return out
    if isinstance(input_choice, str):
        out = []
        for part in input_choice.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                continue
        return out
    return []


def step_scene_apply(args: Any, save_root: str) -> Dict[str, Any]:
    """Apply player choice to a session zero scene.

    Two-phase apply for scenes that expose a slate computed from player
    text.  Current behavior:

      - Scene declares choices but no choice input was supplied: run
        apply_text() only and persist state WITHOUT advancing.  Returns
        the current slate in the response so the caller can pick.
      - Scene declares no choices and only text was supplied: run
        apply_text() and advance.
      - Scene declares choices and choice input was supplied: run
        apply_text() (if any text) then apply()/apply_multi() and advance.

    Multi-pick scenes (currently only the power-slate scene) dispatch
    through apply_multi() when more than one choice index is provided.
    """
    index = getattr(args, "index", 0)
    input_choice = getattr(args, "input_choice", None)
    input_texts_raw = getattr(args, "input_text", None) or []
    output_json_path = getattr(args, "output_json", None)

    from emergence.engine.runtime.main import _make_all_scenes
    from emergence.engine.character_creation.character_factory import (
        CharacterFactory,
        CreationState,
    )

    scenes = _make_all_scenes()
    if index < 0 or index >= len(scenes):
        return {"status": "error", "message": f"Scene index {index} out of range."}

    scene = scenes[index]
    rng = _get_rng(args)

    # Load creation state
    sz_path = os.path.join(save_root, "session_zero_state.json")
    sz_data = _read_json_file(sz_path)
    if sz_data is None:
        return {"status": "error", "message": "No session zero in progress."}

    creation_dict = sz_data.get("creation_state", {})
    creation_state = CreationState(**creation_dict)

    # v4 --output-json route: narrator's VignetteOutput JSON is loaded
    # here, validated against the scaffold, and the picked choice is
    # applied via apply_vignette_choice.  This bypasses the legacy
    # apply_text/apply_multi path for vignette scenes.
    if output_json_path and hasattr(scene, "apply_vignette_output"):
        try:
            if output_json_path == "-":
                raw = sys.stdin.read()
            else:
                with open(output_json_path, "r", encoding="utf-8") as f:
                    raw = f.read()
        except OSError as e:
            return {"status": "error",
                    "message": f"could not read --output-json: {e}"}
        pick_idx = 0
        if input_choice is not None:
            try:
                pick_idx = int(str(input_choice).split(",")[0])
            except (TypeError, ValueError):
                pick_idx = 0
        result = scene.apply_vignette_output(
            raw, pick_idx, creation_state, CharacterFactory(), rng,
        )
        if result.get("status") != "ok":
            return result
        creation_state = result["state"]
        sz_data["creation_state"] = creation_state.__dict__
        sz_data["current_scene"] = index  # stay here until ack clears
        _write_json_file(sz_path, sz_data)
        return {
            "status": "ok",
            "scene_index": index,
            "scene_id": scene.scene_id,
            "applied": True,
            "picked_choice": pick_idx,
            "next_step": "ack",
            "awaiting": "ack",
        }
    factory = CharacterFactory()

    scene.prepare(creation_state, rng)

    text_inputs: Dict[str, str] = {}
    if input_texts_raw:
        for item in input_texts_raw:
            if "=" in item:
                k, _, v = item.partition("=")
                text_inputs[k.strip()] = v.strip()

    applied_text = False
    if text_inputs:
        creation_state = scene.apply_text(text_inputs, creation_state, factory, rng)
        applied_text = True

    choice_indices = _parse_choice_indices(input_choice)
    # Re-prepare so the scene sees the post-apply_text state (matters for
    # the slate scene — get_choices() reads pending_slate from state).
    scene.prepare(creation_state, rng)
    available_choices = scene.get_choices(creation_state)

    applied_choice = False
    if choice_indices and available_choices:
        if len(choice_indices) > 1 and hasattr(scene, "apply_multi"):
            creation_state = scene.apply_multi(
                choice_indices, creation_state, factory, rng,
            )
        else:
            idx0 = min(max(0, choice_indices[0]), len(available_choices) - 1)
            creation_state = scene.apply(idx0, creation_state, factory, rng)
        applied_choice = True

    # Advance rule: scenes that offer choices require a choice to advance.
    # Scenes that offer none advance as soon as apply_text has been called.
    # Multi-phase scenes (e.g. AwakeningScene dilemma → power slate) can
    # veto the advance via an is_complete() hook.
    has_choices = bool(available_choices)
    should_advance = applied_choice or (applied_text and not has_choices)
    if should_advance and hasattr(scene, "is_complete"):
        should_advance = bool(scene.is_complete(creation_state))

    current_scene = sz_data.get("current_scene", index)
    next_scene = index + 1 if should_advance else current_scene

    sz_data["creation_state"] = creation_state.__dict__
    sz_data["current_scene"] = next_scene
    _write_json_file(sz_path, sz_data)

    # Build summary.  When the scene has not advanced we expose the
    # pending slate so the narrator can present the new 10-option list.
    # Multi-phase scenes may have applied one phase (dilemma) but still
    # need input for the next (power slate), so re-read choices post-apply
    # and surface them when present.
    awaiting: Optional[str] = None
    if not should_advance:
        post_choices = scene.get_choices(creation_state)
        if post_choices:
            awaiting = "choice"
        elif not applied_text and not applied_choice:
            awaiting = "input"

    # Re-read choices against the (possibly post-text) state for display.
    display_choices = scene.get_choices(creation_state) if awaiting else []

    result = {
        "status": "ok",
        "mode": "SESSION_ZERO",
        "scene_index": index,
        "scene_id": scene.scene_id,
        "applied": should_advance,
        "next_scene": next_scene if should_advance and next_scene < len(scenes) else None,
        "creation_summary": {
            "name": creation_state.name or None,
            "age": creation_state.age_at_onset,
            "region": creation_state.region or None,
            "tier": creation_state.tier,
            "power_category_primary": creation_state.power_category_primary or None,
            "power_category_secondary": creation_state.power_category_secondary,
            "powers": [p.get("name") for p in creation_state.powers],
            "skills": dict(creation_state.skills) if creation_state.skills else {},
            "goals": [g.get("description") for g in creation_state.goals],
        },
    }

    if awaiting:
        result["awaiting"] = awaiting
        result["choices"] = display_choices
        # Expose structured slate for the power-slate scene.
        if creation_state.pending_slate:
            result["pending_slate"] = list(creation_state.pending_slate)

    if should_advance and next_scene >= len(scenes):
        result["message"] = (
            "All scenes complete. Run 'step scene-finalize' to create character."
        )

    return result


def _slugify_name(name: str, suffix: str) -> str:
    """Make a stable, filesystem-safe NPC id from a display name."""
    import re as _re
    base = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "tie"
    return f"npc-tie-{base}-{suffix}"


def _materialize_npc_seeds(
    npc_seeds: List[Dict[str, Any]],
    state: Dict[str, Any],
    player_sheet: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Turn life-description NPC seeds into world NPC registry entries.

    Seeds from the LifeDescriptionScene are tie-of-origin NPCs: family,
    friends, coworkers the player knew before the Onset.  They land in
    state['npcs'] with a +2 default standing (proactive help) and are
    linked to the player sheet's relationships map.  Status is honored
    if the player marked someone as dead or missing.
    """
    if not npc_seeds:
        return []

    npcs = state.setdefault("npcs", {})
    sheet_relationships = player_sheet.setdefault("relationships", {})
    materialized: List[Dict[str, Any]] = []

    for seed in npc_seeds:
        name = seed.get("name", "").strip()
        if not name:
            continue
        seed_index = seed.get("seed_index", len(materialized))
        npc_id = _slugify_name(name, f"{seed_index:02d}")
        status = seed.get("status", "alive").strip().lower() or "alive"
        # Deceased ties still get a registry entry so the sheet can
        # reference them narratively, but with status=dead they won't
        # participate in live simulation.
        entry = {
            "id": npc_id,
            "schema_version": "1.0",
            "display_name": name,
            "faction_affiliation": {"primary": None, "secondary": []},
            "location": seed.get("location", ""),
            "schedule": {},
            "species": "human",
            "age": 30,
            "manifestation": {"tier": 0, "has_powers": False, "powers": []},
            "role": seed.get("relation", "tie"),
            "goals": [],
            "relationships": {},
            "resources": [],
            "knowledge": [],
            "personality_traits": [],
            "current_concerns": [seed.get("descriptor", "")]
            if seed.get("descriptor")
            else [],
            "memory": [],
            "standing_with_player_default": 2 if status == "alive" else 0,
            "what_they_want_from_player": "",
            "voice": seed.get("descriptor", ""),
            "hooks": [],
            "status": status,
            "social_block": None,
        }
        npcs[npc_id] = entry

        # Mirror into the character sheet so sheet.relationships surfaces
        # the tie during session zero preamble.
        if status == "alive":
            sheet_relationships[npc_id] = {
                "standing": 2,
                "current_state": "alive_present",
                "trust": 2,
            }
        else:
            sheet_relationships[npc_id] = {
                "standing": 2,
                "current_state": status if status in {"dead", "missing"} else "unknown",
                "trust": 0,
            }

        materialized.append(entry)

    return materialized


def step_scene_ack(args: Any, save_root: str) -> Dict[str, Any]:
    """Emit the post-pick acknowledgment beat for a vignette scene.

    Reads state.pending_ack.  If set, builds a summary narration payload
    describing what the just-applied choice seeded, clears the flag,
    and returns the payload.  Next `step scene --index N+1` will be
    allowed because the gate is cleared.
    """
    from emergence.engine.character_creation.character_factory import CreationState

    index = getattr(args, "index", 0)
    sz_path = os.path.join(save_root, "session_zero_state.json")
    sz_data = _read_json_file(sz_path)
    if sz_data is None:
        return {"status": "error", "message": "No session zero in progress."}

    creation_state = CreationState(**(sz_data.get("creation_state", {})))
    if not creation_state.pending_ack:
        return {
            "status": "ok",
            "message": f"no pending ack for scene {index}.",
            "skipped": True,
        }

    # Build ack summary payload.
    recent_npc = creation_state.generated_npcs[-1] if creation_state.generated_npcs else None
    recent_threat = creation_state.threats[-1] if creation_state.threats else None
    recent_goal = creation_state.goals[-1] if creation_state.goals else None
    recent_loc = creation_state.generated_locations[-1] if creation_state.generated_locations else None
    recent_history = None
    for h in reversed(creation_state.history):
        if h.get("type") == "character_creation_vignette":
            recent_history = h
            break

    ack_payload = {
        "scene_type": "post_pick_summary",
        "register_directive": "summary",
        "scene_index": index,
        "prose_target": {"min_words": 60, "max_words": 100},
        "seeds": {
            "npc": recent_npc.get("display_name") if recent_npc else None,
            "threat": recent_threat.get("name") if recent_threat else None,
            "goal": recent_goal.get("description") if recent_goal else None,
            "location": (
                (recent_loc.get("id") or (recent_loc.get("spec") or {}).get("id"))
                if recent_loc else None
            ),
            "starting_location": creation_state.starting_location,
            "history": recent_history.get("description") if recent_history else None,
        },
        "invitation": (
            "In 60-100 words, recap what the pick cost and planted.  Single "
            "paragraph of prose in the scene's register, then a bulleted "
            "list of every seeded thread (mechanical binding, NPCs, "
            "location, threats, goals).  No picks; player advances via "
            "'step scene --index N+1'."
        ),
    }

    # Clear the gate.
    creation_state.pending_ack = False
    sz_data["creation_state"] = creation_state.__dict__
    _write_json_file(sz_path, sz_data)

    return {
        "status": "ok",
        "scene_index": index,
        "ack_payload": ack_payload,
        "cleared_pending_ack": True,
    }


def step_scene_finalize(args: Any, save_root: str) -> Dict[str, Any]:
    """Finalize character from session zero state."""
    from emergence.engine.character_creation.character_factory import (
        CharacterFactory,
        CreationState,
    )

    sz_path = os.path.join(save_root, "session_zero_state.json")
    sz_data = _read_json_file(sz_path)
    if sz_data is None:
        return {"status": "error", "message": "No session zero in progress."}

    creation_dict = sz_data.get("creation_state", {})
    creation_state = CreationState(**creation_dict)
    factory = CharacterFactory()

    sheet = factory.finalize(creation_state)

    # Load current state and update player
    state = _load_full_state(save_root)

    # Convert CharacterSheet to dict, handling nested objects that may
    # already be dicts (from session zero scene data)
    try:
        state["player"] = sheet.to_dict()
    except AttributeError:
        # Some nested objects may already be dicts rather than typed objects.
        # Fall back to dataclass-based serialization.
        import dataclasses
        if dataclasses.is_dataclass(sheet):
            state["player"] = dataclasses.asdict(sheet)
        elif isinstance(sheet, dict):
            state["player"] = sheet
        else:
            state["player"] = {"name": getattr(sheet, "name", "Unknown")}

    # Materialize any tie NPCs captured during the life-description scene.
    seeded = _materialize_npc_seeds(
        list(creation_state.npc_seeds), state, state["player"],
    )

    # Ensure current_location is set (step_situation looks for this key)
    if "location" in state["player"] and "current_location" not in state["player"]:
        state["player"]["current_location"] = state["player"]["location"]
    if "region" not in state["player"] or not state["player"].get("region"):
        state["player"]["home_region"] = state["player"].get("current_location", "")

    _save_full_state(save_root, state)

    # Clean up session zero state file
    try:
        os.remove(sz_path)
    except OSError:
        pass

    return {
        "status": "ok",
        "mode": "SIM",
        "message": "Character created. Run 'step preamble' for opening narration.",
        "player": _player_summary(state["player"]),
        "character_sheet": state["player"],
        "seeded_npcs": [
            {"id": n["id"], "display_name": n["display_name"], "role": n.get("role", ""), "status": n.get("status", "alive")}
            for n in seeded
        ],
    }


def step_preamble(args: Any, save_root: str) -> Dict[str, Any]:
    """Generate the opening preamble narration after character creation."""
    from emergence.engine.narrator.payloads import build_preamble_payload
    from emergence.engine.schemas.world import Location, NPC

    state = _load_full_state(save_root)

    if not state["player"].get("name"):
        return {"status": "error", "message": "No active character. Complete session zero first."}

    # Find player location (same pattern as step_situation)
    player_location_id = state["player"].get("current_location") or state["player"].get("home_region", "")

    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}

    location = locations.get(player_location_id)
    if location is None and locations:
        player_location_id = next(iter(locations))
        location = locations[player_location_id]

    location_name = getattr(location, "display_name", player_location_id) if location else "Unknown"
    location_details = location.to_dict() if location else {}

    # NPCs at player's location
    npcs_present = [
        getattr(npc, "name", npc_id)
        for npc_id, npc in npcs.items()
        if getattr(npc, "location", None) == player_location_id
    ][:5]

    # Faction standings from player data
    faction_standings = state["player"].get("faction_standings", {})
    if not faction_standings:
        # Build from factions dict if player doesn't have standings yet
        faction_standings = {
            fid: fdata.get("player_standing", 0)
            for fid, fdata in state["factions"].items()
            if fdata.get("player_standing", 0) != 0
        }

    recent_events = []

    # Biography roster: tie-NPCs materialized from session zero (npc-tie-*).
    biography_roster: List[Dict[str, Any]] = []
    for npc_id, npc in npcs.items():
        if npc_id.startswith("npc-tie-"):
            biography_roster.append({
                "npc_id": npc_id,
                "name": getattr(npc, "display_name", npc_id),
                "relation": getattr(npc, "role", ""),
                "location": getattr(npc, "location", ""),
                "status": getattr(npc, "status", "alive"),
            })

    # Top vows: highest-pressure goals (cap at 3).
    goals = state["player"].get("goals", []) or []
    ranked_goals = sorted(
        goals,
        key=lambda g: g.get("pressure", 0) if isinstance(g, dict) else getattr(g, "pressure", 0),
        reverse=True,
    )
    top_vows = []
    for g in ranked_goals[:3]:
        if isinstance(g, dict):
            top_vows.append({
                "id": g.get("id", ""),
                "description": g.get("description", ""),
                "pressure": g.get("pressure", 0),
            })

    # Top threats: from player.threats if present, fallback to negative-
    # standing relationships.
    threats = state["player"].get("threats", []) or []
    if not threats:
        rels = state["player"].get("relationships", {}) or {}
        for npc_id, rel in rels.items():
            standing = (
                rel.get("standing", 0) if isinstance(rel, dict)
                else getattr(rel, "standing", 0)
            )
            if standing <= -2:
                name = (
                    npcs[npc_id].display_name
                    if npc_id in npcs and hasattr(npcs[npc_id], "display_name")
                    else npc_id
                )
                threats.append({
                    "npc_id": npc_id,
                    "name": name,
                    "standing": standing,
                    "source": "",
                    "summary": "",
                })
    top_threats = sorted(
        threats,
        key=lambda t: t.get("standing", 0) if isinstance(t, dict) else 0,
    )[:3]

    opening_scenario_code = {
        "where_character_is": location_name,
        "location_details": location_details,
        "who_is_present": npcs_present,
        "time_since_onset": "one year and change",
        "season": state.get("world", {}).get("season", ""),
        "current_day": state.get("world", {}).get("current_day", ""),
    }

    payload = build_preamble_payload(
        player=state["player"],
        location_name=location_name,
        location_details=location_details,
        npcs_present=npcs_present,
        faction_standings=faction_standings,
        recent_events=recent_events,
        biography_roster=biography_roster,
        top_vows=top_vows,
        top_threats=top_threats,
        opening_scenario_code=opening_scenario_code,
    )

    return {
        "status": "ok",
        "mode": "SIM",
        "biography_roster": biography_roster,
        "top_vows": top_vows,
        "top_threats": top_threats,
        "opening_scenario_code": opening_scenario_code,
        "narrator_payload": payload,
    }


def step_tick(args: Any, save_root: str) -> Dict[str, Any]:
    """Advance world simulation by N days."""
    days = getattr(args, "days", 1)
    rng = _get_rng(args)

    from emergence.engine.sim.tick_engine import TickEngine
    from emergence.engine.schemas.world import (
        WorldState, Faction, NPC, Location, Clock,
    )

    state = _load_full_state(save_root)

    # Reconstruct typed objects from dicts
    world = WorldState.from_dict(state["world"]) if state["world"] else None
    if world is None:
        return {"status": "error", "message": "No world state found."}

    factions = {k: Faction.from_dict(v) for k, v in state["factions"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}
    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    clocks = {k: Clock.from_dict(v) for k, v in state["clocks"].items()}

    engine = TickEngine()
    all_events = []

    for _ in range(days):
        events = engine.run_daily_tick(
            world=world,
            factions=factions,
            npcs=npcs,
            locations=locations,
            clocks=clocks,
            player=state["player"],
            rng=rng,
        )
        all_events.extend(events)

    # Save updated state
    state["world"] = world.to_dict()
    state["factions"] = {k: v.to_dict() for k, v in factions.items()}
    state["npcs"] = {k: v.to_dict() for k, v in npcs.items()}
    state["locations"] = {k: v.to_dict() for k, v in locations.items()}
    state["clocks"] = {k: v.to_dict() for k, v in clocks.items()}
    _save_full_state(save_root, state)

    # Build event summaries
    event_summaries = []
    for ev in all_events:
        event_summaries.append(ev.to_dict() if hasattr(ev, "to_dict") else str(ev))

    from emergence.engine.narrator.payloads import build_time_skip_payload
    payload = build_time_skip_payload(
        duration=f"{days} day{'s' if days != 1 else ''}",
        events_summary=[str(e) for e in all_events[:10]],
        world_changes=[],
    )

    # Tick all live quests whose tick_triggers include world_pulse.
    from emergence.engine.runtime.step_creation import tick_all_quests
    quest_reports = tick_all_quests(save_root, "world_pulse", magnitude=days, state_dict=state)

    return {
        "status": "ok",
        "mode": "SIM",
        "days_advanced": days,
        "new_date": world.current_day if hasattr(world, "current_day") else "?",
        "events": event_summaries[:20],
        "event_count": len(all_events),
        "narrator_payload": payload,
        "quest_ticks": quest_reports,
    }


def step_situation(args: Any, save_root: str) -> Dict[str, Any]:
    """Generate the current player-facing situation."""
    rng = _get_rng(args)

    from emergence.engine.sim.situation_generator import SituationGenerator
    from emergence.engine.schemas.world import (
        WorldState, Location, NPC, Clock, TickEvent,
    )

    state = _load_full_state(save_root)

    if not state["player"].get("name"):
        return {"status": "error", "message": "No active character. Complete session zero first."}

    # Find player location
    player_location_id = state["player"].get("current_location") or state["player"].get("home_region", "")

    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}
    clocks = {k: Clock.from_dict(v) for k, v in state["clocks"].items()}

    # Find the location object
    location = locations.get(player_location_id)
    if location is None and locations:
        # Fallback to first location
        player_location_id = next(iter(locations))
        location = locations[player_location_id]

    if location is None:
        return {"status": "error", "message": "No locations found in world state."}

    # Find NPCs at player's location
    npcs_present = [
        npc for npc in npcs.values()
        if getattr(npc, "location", None) == player_location_id
    ][:5]  # Cap at 5

    generator = SituationGenerator()
    situation = generator.generate_situation(
        world_state=state["world"],
        player=state["player"],
        location=location,
        npcs_present=npcs_present,
        recent_events=[],
        clocks=clocks,
        rng=rng,
    )

    # Save situation for later resolution
    sit_dict = situation.to_dict()
    _write_json_file(os.path.join(save_root, "current_situation.json"), sit_dict)

    # Build narrator payload
    from emergence.engine.narrator.payloads import build_situation_payload
    location_name = getattr(location, "display_name", player_location_id)
    situation_description = f"At {location_name}. Tension: {situation.tension}."
    choices_for_payload = [
        {"id": c.id, "description": c.description, "type": c.type}
        for c in situation.player_choices
    ]
    payload = build_situation_payload(
        situation_id=situation.id,
        description=situation_description,
        choices=choices_for_payload,
        tension_level=situation.tension,
        location_name=location_name,
    )

    return {
        "status": "ok",
        "mode": "SIM",
        "situation_id": situation.id,
        "location": location_name,
        "tension": situation.tension,
        "description": situation_description,
        "choices": [
            {"id": c.id, "description": c.description, "type": c.type}
            for c in situation.player_choices
        ],
        "npcs_present": [getattr(n, "display_name", n.id) for n in npcs_present],
        "narrator_payload": payload,
    }


def step_resolve(args: Any, save_root: str) -> Dict[str, Any]:
    """Resolve the player's chosen action."""
    choice_id = getattr(args, "choice_id", None)
    if not choice_id:
        return {"status": "error", "message": "No --choice-id provided."}

    rng = _get_rng(args)

    from emergence.engine.sim.player_actions import PlayerActionResolver
    from emergence.engine.schemas.world import (
        Location, NPC, Situation, SituationChoice,
    )

    # Load situation
    sit_path = os.path.join(save_root, "current_situation.json")
    sit_dict = _read_json_file(sit_path)
    if sit_dict is None:
        return {"status": "error", "message": "No active situation. Run 'step situation' first."}

    situation = Situation.from_dict(sit_dict)

    # Find the chosen choice
    chosen = None
    for c in situation.player_choices:
        if c.id == choice_id:
            chosen = c
            break

    if chosen is None:
        valid_ids = [c.id for c in situation.player_choices]
        return {"status": "error", "message": f"Choice '{choice_id}' not found. Valid: {valid_ids}"}

    state = _load_full_state(save_root)
    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}

    player_location_id = state["player"].get("current_location") or state["player"].get("home_region", "")
    location = locations.get(player_location_id)
    if location is None and locations:
        player_location_id = next(iter(locations))
        location = locations[player_location_id]

    npcs_present = [
        npc for npc in npcs.values()
        if getattr(npc, "location", None) == player_location_id
    ][:5]

    resolver = PlayerActionResolver()
    result = resolver.resolve_action(
        choice=chosen,
        situation=situation,
        location=location,
        npcs_present=npcs_present,
        player=state["player"],
        rng=rng,
    )

    # Apply state deltas to player
    if result.state_deltas:
        for key, delta in result.state_deltas.items():
            if isinstance(delta, (int, float)):
                state["player"][key] = state["player"].get(key, 0) + delta
            else:
                state["player"][key] = delta

    # Handle location change
    if result.new_location:
        state["player"]["current_location"] = result.new_location

    _save_full_state(save_root, state)

    # Clean up situation file
    try:
        os.remove(sit_path)
    except OSError:
        pass

    output = {
        "status": "ok",
        "mode": "SIM",
        "choice_id": result.choice_id,
        "choice_type": result.choice_type,
        "time_cost_days": result.time_cost_days,
        "encounter_triggered": result.encounter_triggered,
        "new_location": result.new_location,
        "narrative_hints": result.narrative_hints,
    }

    if result.npc_interaction:
        output["npc_interaction"] = result.npc_interaction

    if result.encounter_triggered:
        output["message"] = "Combat encounter triggered! Run 'step combat-start'."

    return output


def step_resolve_action(args: Any, save_root: str) -> Dict[str, Any]:
    """Resolve a declared player action using the dice-backed resolver."""
    rng = _get_rng(args)

    from emergence.engine.sim.action_resolver import (
        ActionDeclaration, resolve_action,
    )
    from emergence.engine.schemas.world import Location, NPC, Clock

    state = _load_full_state(save_root)

    if not state["player"].get("name"):
        return {"status": "error", "message": "No active character."}

    # Build declaration from CLI args
    declaration = ActionDeclaration(
        action_type=getattr(args, "action_type", ""),
        approach=getattr(args, "approach", ""),
        target_id=getattr(args, "target", None),
        skill_id=getattr(args, "skill", None),
    )

    # Load location and NPCs
    player_location_id = (
        state["player"].get("current_location")
        or state["player"].get("home_region", "")
    )
    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}
    clocks = {k: Clock.from_dict(v) for k, v in state["clocks"].items()}

    location = locations.get(player_location_id)
    if location is None and locations:
        player_location_id = next(iter(locations))
        location = locations[player_location_id]

    if location is None:
        return {"status": "error", "message": "No locations found."}

    npcs_present = [
        npc for npc in npcs.values()
        if getattr(npc, "location", None) == player_location_id
    ][:5]

    # Resolve
    resolution = resolve_action(
        declaration=declaration,
        player=state["player"],
        location=location,
        npcs_present=npcs_present,
        clocks=clocks,
        rng=rng,
    )

    # Apply state deltas
    if resolution.state_deltas:
        for key, delta in resolution.state_deltas.items():
            if isinstance(delta, (int, float)):
                state["player"][key] = state["player"].get(key, 0) + delta
            else:
                state["player"][key] = delta

    # Handle location change
    if resolution.new_location:
        state["player"]["current_location"] = resolution.new_location

    # Sync modified NPCs back to state (social blocks, patience, disposition)
    for npc in npcs_present:
        if npc.id in state["npcs"]:
            state["npcs"][npc.id] = npc.to_dict()

    # Sync modified clocks back to state (task clock advancement)
    for clock_id, clock in clocks.items():
        if clock_id in state["clocks"]:
            state["clocks"][clock_id] = clock.to_dict()

    _save_full_state(save_root, state)

    # Write last_engine_output.json for consequence validator (Phase 4)
    output_data = resolution.to_dict()
    _write_json_file(
        os.path.join(save_root, "last_engine_output.json"),
        output_data,
    )

    return {
        "status": "ok",
        "mode": "SIM",
        **output_data,
    }


def step_scene_open(args: Any, save_root: str) -> Dict[str, Any]:
    """Open a new scene using the AngryGM-style scene coder."""
    rng = _get_rng(args)

    from emergence.engine.sim.scene_coder import SceneCodeGenerator
    from emergence.engine.schemas.world import Location, NPC, Clock
    from emergence.engine.narrator.payloads import build_scene_opener_payload

    state = _load_full_state(save_root)

    if not state["player"].get("name"):
        return {"status": "error", "message": "No active character."}

    player_location_id = (
        state["player"].get("current_location")
        or state["player"].get("home_region", "")
    )
    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    npcs = {k: NPC.from_dict(v) for k, v in state["npcs"].items()}
    clocks = {k: Clock.from_dict(v) for k, v in state["clocks"].items()}

    location = locations.get(player_location_id)
    if location is None and locations:
        player_location_id = next(iter(locations))
        location = locations[player_location_id]
    if location is None:
        return {"status": "error", "message": "No locations found."}

    npcs_present = [
        npc for npc in npcs.values()
        if getattr(npc, "location", None) == player_location_id
    ][:5]

    generator = SceneCodeGenerator()
    scene = generator.generate_scene(
        world_state=state["world"],
        player=state["player"],
        location=location,
        npcs_present=npcs_present,
        recent_events=[],
        clocks=clocks,
        factions=state.get("factions", {}),
        rng=rng,
    )

    # Save scene for later continuation/close
    _write_json_file(
        os.path.join(save_root, "current_scene.json"), scene.to_dict()
    )

    # Sync modified NPCs (lazy social block seeding during scene gen)
    for npc in npcs_present:
        if npc.id in state["npcs"]:
            state["npcs"][npc.id] = npc.to_dict()
    _save_full_state(save_root, state)

    payload = build_scene_opener_payload(scene.to_dict())

    return {
        "status": "ok",
        "mode": "SIM",
        "scene": scene.to_dict(),
        "narrator_payload": payload,
    }


def step_scene_continue(args: Any, save_root: str) -> Dict[str, Any]:
    """Produce a continuation beat after a resolve-action."""
    from emergence.engine.sim.scene_coder import SceneCode, check_scene_continues
    from emergence.engine.narrator.payloads import build_scene_continuation_payload

    scene_path = os.path.join(save_root, "current_scene.json")
    scene_dict = _read_json_file(scene_path)
    if scene_dict is None:
        return {
            "status": "error",
            "message": "No active scene. Run 'step scene-open' first.",
        }
    scene = SceneCode.from_dict(scene_dict)

    # Read last engine output (from resolve-action)
    last_output_path = os.path.join(save_root, "last_engine_output.json")
    last_output = _read_json_file(last_output_path) or {}

    # Check if scene continues
    continues, reason = check_scene_continues(scene, last_output)
    scene.scene_continues = continues
    scene.scene_phase = "continuation" if continues else "close"

    # Save updated scene
    _write_json_file(scene_path, scene.to_dict())

    payload = build_scene_continuation_payload(
        scene_code=scene.to_dict(),
        resolution=last_output,
        complications=last_output.get("complications", []),
    )
    if not continues:
        payload["scene_end_reason"] = reason

    return {
        "status": "ok",
        "mode": "SIM",
        "scene_continues": continues,
        "end_reason": reason,
        "scene": scene.to_dict(),
        "last_resolution": last_output,
        "narrator_payload": payload,
    }


def step_scene_close(args: Any, save_root: str) -> Dict[str, Any]:
    """Close the current scene and generate resolution beat."""
    from emergence.engine.sim.scene_coder import SceneCode
    from emergence.engine.narrator.payloads import build_scene_close_payload

    scene_path = os.path.join(save_root, "current_scene.json")
    scene_dict = _read_json_file(scene_path)
    if scene_dict is None:
        return {"status": "error", "message": "No active scene."}
    scene = SceneCode.from_dict(scene_dict)
    scene.scene_phase = "close"
    scene.scene_continues = False

    last_output_path = os.path.join(save_root, "last_engine_output.json")
    last_output = _read_json_file(last_output_path) or {}

    payload = build_scene_close_payload(
        scene_code=scene.to_dict(),
        final_state=last_output,
        transition_hint=scene.transition_hint,
    )

    # Reset per-scene NPC state (patience, disposition_shifted) for next scene
    state = _load_full_state(save_root)
    from emergence.engine.sim.social import reset_scene_state
    from emergence.engine.schemas.world import NPC, SocialBlock
    for npc_id, npc_data in state["npcs"].items():
        sb_dict = npc_data.get("social_block")
        if sb_dict:
            sb = SocialBlock.from_dict(sb_dict)
            reset_scene_state(sb)
            npc_data["social_block"] = sb.to_dict()
    _save_full_state(save_root, state)

    # Clean up current scene file
    try:
        os.remove(scene_path)
    except OSError:
        pass

    # Tick quests whose tick_triggers include scene_close.
    from emergence.engine.runtime.step_creation import tick_all_quests
    quest_reports = tick_all_quests(save_root, "scene_close", magnitude=1.0, state_dict=state)

    return {
        "status": "ok",
        "mode": "SIM",
        "scene": scene.to_dict(),
        "narrator_payload": payload,
        "quest_ticks": quest_reports,
    }


def step_combat_start(args: Any, save_root: str) -> Dict[str, Any]:
    """Generate and start a combat encounter."""
    rng = _get_rng(args)

    from emergence.engine.sim.encounter_generator import EncounterGenerator
    from emergence.engine.schemas.world import Location, Clock, Situation
    from emergence.engine.schemas.encounter import EncounterSpec

    state = _load_full_state(save_root)

    # Load current situation if available
    sit_path = os.path.join(save_root, "current_situation.json")
    sit_dict = _read_json_file(sit_path)

    locations = {k: Location.from_dict(v) for k, v in state["locations"].items()}
    clocks = {k: Clock.from_dict(v) for k, v in state["clocks"].items()}

    player_location_id = state["player"].get("current_location") or state["player"].get("home_region", "")
    location = locations.get(player_location_id)
    if location is None and locations:
        player_location_id = next(iter(locations))
        location = locations[player_location_id]

    generator = EncounterGenerator()

    if sit_dict:
        situation = Situation.from_dict(sit_dict)
    else:
        # Create a minimal situation for encounter generation
        situation = Situation(
            id=f"encounter_{int(time.time())}",
            description="A sudden encounter",
            tension_level="tense",
            choices=[],
            location_id=player_location_id,
            encounter_probability=1.0,
        )

    encounter = generator.generate_encounter(
        situation=situation,
        location=location,
        player=state["player"],
        clocks=clocks,
        rng=rng,
    )

    # Save combat state
    combat_state = {
        "encounter": encounter.to_dict() if hasattr(encounter, "to_dict") else {},
        "round": 0,
        "started": time.time(),
        "player_location": player_location_id,
    }
    _write_json_file(os.path.join(save_root, "combat_state.json"), combat_state)

    # Build narrator payload
    from emergence.engine.narrator.payloads import build_scene_framing_payload
    payload = build_scene_framing_payload(
        scene_id=f"combat_{int(time.time())}",
        location_name=getattr(location, "name", player_location_id),
        time_of_day="",
        npcs_present=[],
        recent_events=[],
        tension_level="volatile",
        register="action",
    )

    enc_dict = encounter.to_dict() if hasattr(encounter, "to_dict") else {}

    return {
        "status": "ok",
        "mode": "COMBAT",
        "encounter": enc_dict,
        "enemies": enc_dict.get("enemies", []),
        "terrain": enc_dict.get("terrain", {}),
        "stakes": enc_dict.get("stakes", ""),
        "available_verbs": [
            "Attack", "Power", "Assess", "Maneuver",
            "Parley", "Disengage", "Finisher", "Defend",
        ],
        "narrator_payload": payload,
        "message": "Combat begins. Choose a verb and target with 'step combat-round'.",
    }


def step_combat_round(args: Any, save_root: str) -> Dict[str, Any]:
    """Process one combat round."""
    verb = getattr(args, "verb", "Attack")
    target = getattr(args, "target", None)
    power = getattr(args, "power", None)
    rng = _get_rng(args)

    from emergence.engine.combat.encounter_runner import EncounterRunner
    from emergence.engine.schemas.encounter import EncounterSpec

    # Load combat state
    combat_path = os.path.join(save_root, "combat_state.json")
    combat_data = _read_json_file(combat_path)
    if combat_data is None:
        return {"status": "error", "message": "No combat in progress. Run 'step combat-start' first."}

    state = _load_full_state(save_root)
    current_round = combat_data.get("round", 0) + 1
    combat_data["round"] = current_round

    # For now, use the encounter runner's full run for the round
    # This is a simplified approach that resolves combat in one step
    enc_dict = combat_data.get("encounter", {})

    runner = EncounterRunner()

    # Build narrator payload for the combat turn
    from emergence.engine.narrator.payloads import build_combat_turn_payload
    payload = build_combat_turn_payload(
        round_num=current_round,
        actor_name=state["player"].get("name", "Player"),
        action_type=verb,
        action_result=f"uses {verb}" + (f" on {target}" if target else ""),
        register="action",
    )

    # Determine if combat should end (simplified for step mode)
    # In a full implementation, this would track combatant health etc.
    combat_over = current_round >= 3  # Placeholder: 3-round encounters

    if combat_over:
        # Clean up combat state
        try:
            os.remove(combat_path)
        except OSError:
            pass

        return {
            "status": "ok",
            "mode": "SIM",
            "round": current_round,
            "combat_over": True,
            "resolution": "victory",
            "verb": verb,
            "target": target,
            "narrator_payload": payload,
            "message": "Combat resolved. Returning to simulation.",
        }

    # Save updated combat state
    _write_json_file(combat_path, combat_data)

    return {
        "status": "ok",
        "mode": "COMBAT",
        "round": current_round,
        "combat_over": False,
        "verb": verb,
        "target": target,
        "available_verbs": [
            "Attack", "Power", "Assess", "Maneuver",
            "Parley", "Disengage", "Finisher", "Defend",
        ],
        "narrator_payload": payload,
    }


def step_save(args: Any, save_root: str) -> Dict[str, Any]:
    """Manual save."""
    from emergence.engine.persistence.load import LoadManager

    loader = LoadManager(save_root)
    classification = loader.classify()

    if classification == "FRESH":
        return {"status": "error", "message": "Nothing to save. No game in progress."}

    state = _load_full_state(save_root)
    _save_full_state(save_root, state)

    return {
        "status": "ok",
        "message": "Game saved.",
        "save_root": save_root,
        "mode": _detect_mode(save_root),
    }
