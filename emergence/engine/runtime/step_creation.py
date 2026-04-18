"""Step handlers for the redesigned six-scene character creation flow.

Named verbs (registered in __main__.py's argparse and dispatched from
step_cli.dispatch_step):

    step pre-emergence    — text elicitation + classifier apply
    step pick-power       — subcategories then powers; auto cast/rider
    step pick-location    — post-Onset settlement pick
    step pick-job         — narrator generates 5 cards; player picks 1
    step pick-quest       — narrator generates 8; picks 4 backstory; player picks 1 urgent
    step bridge           — 1500-word bridge + opening scene; exits session zero

Each verb is effectively a state machine. The scene determines the current
phase from CreationState / QuestState; the caller passes a --mode flag or
the handler infers what to do from which fields are populated.

All writes to CreationState/QuestState go through creation_store.
"""

from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.bridge_scene import BridgeScene
from emergence.engine.character_creation.character_factory import CharacterFactory
from emergence.engine.character_creation.job_bundle_scene import JobBundleScene
from emergence.engine.character_creation.location_scene import LocationScene
from emergence.engine.character_creation.power_pick_scene import PowerPickScene
from emergence.engine.character_creation.pre_emergence_scene import PreEmergenceScene
from emergence.engine.character_creation.quest_pick_scene import QuestPickScene
from emergence.engine.quests import tick as quest_tick, check_success as quest_check_success
from emergence.engine.runtime.creation_store import (
    load_creation_state,
    load_quest_state,
    save_creation_state,
    save_quest_state,
)
from emergence.engine.runtime.quest_world_adapter import StepWorldAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rng(args: Any) -> random.Random:
    seed = getattr(args, "seed", None)
    if seed is not None:
        return random.Random(seed)
    return random.Random()


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _parse_kv_list(items: Optional[List[str]]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for entry in items or []:
        if "=" not in entry:
            continue
        k, v = entry.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _parse_int_list(raw: Optional[str]) -> List[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


# ---------------------------------------------------------------------------
# Tick helper — called from step_tick / step_scene_close / step_resolve_action
# ---------------------------------------------------------------------------


def tick_all_quests(
    save_root: str,
    event_type: str,
    magnitude: float = 1.0,
    state_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Tick every live quest whose tick_triggers include event_type.

    Returns a list of TickReport dicts. Auto-resolves any quest whose
    bright line fires. Persists QuestState after ticking.

    If state_dict is provided, uses it as the WorldView backing. Otherwise
    the caller's world-state mutations will not reach the quest predicates.
    """
    quest_state = load_quest_state(save_root)
    if not quest_state.quests:
        return []

    world = StepWorldAdapter(state_dict) if state_dict is not None else None
    reports = quest_tick(quest_state, event_type, magnitude, world=world)

    # After ticking, also run check_success so that positive predicates that
    # became true during the tick resolve cleanly.
    if world is not None:
        quest_check_success(quest_state, world)

    save_quest_state(save_root, quest_state)
    return [r.to_dict() for r in reports]


# ---------------------------------------------------------------------------
# step pre-emergence
# ---------------------------------------------------------------------------


def step_pre_emergence(args: Any, save_root: str) -> Dict[str, Any]:
    """Pre-emergence scene with three modes:

        --mode prompt           → return the text prompts
        --mode apply-text       → accept --input-text "key=value" … to capture bio
        --mode apply-classifier → accept --input-json path to Claude's classifier JSON
    """
    mode = getattr(args, "mode", None)
    scene = PreEmergenceScene()
    state = load_creation_state(save_root)
    rng = _rng(args)
    factory = CharacterFactory()

    if mode == "prompt" or mode is None:
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "framing": scene.get_framing(state),
            "text_prompts": scene.text_prompts(state),
        }

    if mode == "apply-text":
        text_inputs = _parse_kv_list(getattr(args, "input_text", None))
        state = scene.apply_text(text_inputs, state, factory, rng)
        save_creation_state(save_root, state)
        narrator_payload = scene.build_narrator_payload(state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "narrator_payload": narrator_payload,
        }

    if mode == "apply-classifier":
        path = getattr(args, "input_json", None)
        if not path or not os.path.exists(path):
            return {"status": "error", "message": "apply-classifier requires --input-json PATH"}
        payload = _read_json(path)
        state = scene.apply_classifier(payload, state, factory, rng)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "message": "Pre-emergence classifier applied. Next: step pick-power.",
        }

    return {"status": "error", "message": f"unknown mode {mode!r}"}


# ---------------------------------------------------------------------------
# step pick-power
# ---------------------------------------------------------------------------


def step_pick_power(args: Any, save_root: str) -> Dict[str, Any]:
    """Power pick with phase-inferred modes:

        phase = subcategories_pending → offer 6 subcats; accept --picks "0,3"
        phase = powers_pending        → offer 3x2 powers; accept --picks "1,4"
        phase = complete              → return summary
    """
    scene = PowerPickScene()
    state = load_creation_state(save_root)
    rng = _rng(args)
    factory = CharacterFactory()

    current_phase = scene.phase(state)

    picks = _parse_int_list(getattr(args, "picks", None))

    if current_phase == "subcategories_pending":
        if not picks:
            offer = scene.prepare_subcategory_offer(state, rng)
            save_creation_state(save_root, state)
            return {
                "status": "ok",
                "phase": "subcategories_pending",
                "subcategory_offer": offer,
                "message": "Re-run with --picks i,j to pick two of six subcategories.",
            }
        state = scene.apply_subcategory_picks(picks, state, factory, rng)
        offer = scene.prepare_power_offer(state, rng)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "subcategories_picked": state.scene_choices["subcategories_picked"],
            "power_offer": offer,
            "message": "Re-run with --picks i,j to pick one power per subcategory.",
        }

    if current_phase == "powers_pending":
        if not picks:
            return {
                "status": "ok",
                "phase": "powers_pending",
                "power_offer": state.scene_choices.get("power_offer", []),
                "message": "Re-run with --picks i,j to pick one power per subcategory.",
            }
        state = scene.apply_power_picks(picks, state, factory, rng)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "powers_final": state.scene_choices["powers_final"],
            "message": "Powers picked. Cast + rider auto-rolled. Next: step pick-location.",
        }

    return {"status": "ok", "phase": current_phase, "powers_final": state.powers}


# ---------------------------------------------------------------------------
# step pick-location
# ---------------------------------------------------------------------------


def step_pick_location(args: Any, save_root: str) -> Dict[str, Any]:
    """Post-Onset settlement pick. Accept --index N or return the menu."""
    scene = LocationScene()
    state = load_creation_state(save_root)
    rng = _rng(args)
    factory = CharacterFactory()

    idx = getattr(args, "index", None)
    if idx is None:
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "framing": scene.get_framing(state),
            "choices": scene.get_choices(state),
            "message": "Re-run with --index N to pick a settlement.",
        }
    state = scene.apply(int(idx), state, factory, rng)
    save_creation_state(save_root, state)
    return {
        "status": "ok",
        "phase": scene.phase(state),
        "location": state.scene_choices.get("post_emergence_location"),
        "message": "Settlement locked. Next: step pick-job.",
    }


# ---------------------------------------------------------------------------
# step pick-job
# ---------------------------------------------------------------------------


def step_pick_job(args: Any, save_root: str) -> Dict[str, Any]:
    """Job bundle with three modes:

        --mode prompt      → return narrator_payload (5 cards requested)
        --mode apply       → accept --input-json with Claude's bundle_output
        --mode pick        → accept --index N to pick one of 5 cards
    """
    mode = getattr(args, "mode", None)
    scene = JobBundleScene()
    state = load_creation_state(save_root)
    rng = _rng(args)
    factory = CharacterFactory()

    if mode == "prompt" or mode is None:
        payload = scene.build_narrator_payload(state)
        return {"status": "ok", "phase": scene.phase(state), "narrator_payload": payload}

    if mode == "apply":
        path = getattr(args, "input_json", None)
        if not path or not os.path.exists(path):
            return {"status": "error", "message": "apply requires --input-json PATH"}
        payload = _read_json(path)
        state = scene.store_bundle_output(payload, state)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "cards": state.scene_choices.get("job_bundle_cards", []),
            "message": "Re-run with --mode pick --index N to pick one of five.",
        }

    if mode == "pick":
        idx = getattr(args, "index", None)
        if idx is None:
            return {"status": "error", "message": "pick requires --index N"}
        state = scene.apply_pick(int(idx), state, factory, rng)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "job_pick": state.scene_choices.get("job_pick"),
            "message": "Job picked. Next: step pick-quest.",
        }

    return {"status": "error", "message": f"unknown mode {mode!r}"}


# ---------------------------------------------------------------------------
# step pick-quest
# ---------------------------------------------------------------------------


def step_pick_quest(args: Any, save_root: str) -> Dict[str, Any]:
    """Quest pick with three modes:

        --mode prompt → return narrator_payload (8 quests + 4 backstory ids requested)
        --mode apply  → accept --input-json with Claude's quest pool
        --mode pick   → accept --index N into the remaining 4 for urgent quest
    """
    mode = getattr(args, "mode", None)
    scene = QuestPickScene()
    state = load_creation_state(save_root)
    quest_state = load_quest_state(save_root)
    rng = _rng(args)
    factory = CharacterFactory()

    if mode == "prompt" or mode is None:
        payload = scene.build_narrator_payload(state)
        return {"status": "ok", "phase": scene.phase(state), "narrator_payload": payload}

    if mode == "apply":
        path = getattr(args, "input_json", None)
        if not path or not os.path.exists(path):
            return {"status": "error", "message": "apply requires --input-json PATH"}
        payload = _read_json(path)
        state = scene.store_quest_output(payload, state)
        save_creation_state(save_root, state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "urgent_offer": state.scene_choices.get("quest_urgent_offer", []),
            "message": "Re-run with --mode pick --index N for the urgent quest.",
        }

    if mode == "pick":
        idx = getattr(args, "index", None)
        if idx is None:
            return {"status": "error", "message": "pick requires --index N"}
        quest_state = scene.apply_urgent_pick(int(idx), state, factory, rng, quest_state)
        save_creation_state(save_root, state)
        save_quest_state(save_root, quest_state)
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "urgent_id": state.scene_choices.get("quest_urgent_id"),
            "quests_registered": [q.id for q in quest_state.quests],
            "message": "Five quests registered (4 background + 1 urgent). Next: step bridge.",
        }

    return {"status": "error", "message": f"unknown mode {mode!r}"}


# ---------------------------------------------------------------------------
# step bridge
# ---------------------------------------------------------------------------


def step_bridge(args: Any, save_root: str) -> Dict[str, Any]:
    """Bridge scene — 1500w bridge + opening scene.

        --mode prompt → return narrator_payload
        --mode apply  → accept --input-json with Claude's bridge output; finalize session zero
    """
    mode = getattr(args, "mode", None)
    scene = BridgeScene()
    state = load_creation_state(save_root)
    quest_state = load_quest_state(save_root)

    if mode == "prompt" or mode is None:
        payload = scene.build_narrator_payload(state, quest_state)
        return {"status": "ok", "phase": scene.phase(state), "narrator_payload": payload}

    if mode == "apply":
        path = getattr(args, "input_json", None)
        if not path or not os.path.exists(path):
            return {"status": "error", "message": "apply requires --input-json PATH"}
        payload = _read_json(path)
        state = scene.apply_bridge_output(payload, state, quest_state)
        save_creation_state(save_root, state)
        save_quest_state(save_root, quest_state)
        hooked = state.scene_choices.get("hooked_npcs") or []
        # Build a roster block from structured emissions. The engine renders
        # this after the opening scene prose so the player has a clear list
        # of who they know, without parsing the prose.
        npc_by_id = {npc.get("npc_id"): npc for npc in state.generated_npcs}
        roster_lines: List[str] = []
        for h in hooked:
            nid = h.get("npc_id", "")
            npc = npc_by_id.get(nid, {})
            name = npc.get("display_name") or nid
            rel = h.get("relation", "")
            roster_lines.append(f"- {name} ({rel})" if rel else f"- {name}")
        roster_block = (
            "People you know here:\n" + "\n".join(roster_lines)
            if roster_lines else ""
        )
        return {
            "status": "ok",
            "phase": scene.phase(state),
            "bridge_prose": state.scene_choices.get("bridge_prose"),
            "opening_scene": state.scene_choices.get("opening_scene"),
            "opening_scene_meta": state.scene_choices.get("opening_scene_meta"),
            "hooked_npcs": hooked,
            "mentioned_factions": state.scene_choices.get("mentioned_factions") or [],
            "roster_block": roster_block,
            "message": "Session zero complete. Run step scene-finalize to mint the CharacterSheet, then step preamble.",
        }

    return {"status": "error", "message": f"unknown mode {mode!r}"}
