"""Narrator payload builders — construct NarratorPayload dicts for each scene type."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from emergence.engine.narrator.validation import _FORBIDDEN_PATTERNS


def _constraints() -> Dict[str, List[str]]:
    """Standard narrator constraints dict."""
    return {"forbidden": list(_FORBIDDEN_PATTERNS)}


def build_combat_turn_payload(
    round_num: int,
    actor_name: str,
    action_type: str,
    action_result: str,
    damage_dealt: int = 0,
    status_applied: str = "",
    enemies_remaining: int = 0,
    player_condition: Dict[str, Any] | None = None,
    register: str = "action",
    # Rev 4 additions
    current_postures: Dict[str, str] | None = None,
    armed_posture_riders: Dict[str, List[Dict[str, str]]] | None = None,
    hidden_combatants: List[str] | None = None,
    declared_action: Dict[str, Any] | None = None,
    passive_effects_triggered: List[Dict[str, Any]] | None = None,
    pool_state: Dict[str, Dict[str, int]] | None = None,
) -> Dict[str, Any]:
    return {
        "scene_type": "combat_turn",
        "register_directive": register,
        "round": round_num,
        "actor": actor_name,
        "action_type": action_type,
        "action_result": action_result,
        "damage_dealt": damage_dealt,
        "status_applied": status_applied,
        "enemies_remaining": enemies_remaining,
        "player_condition": player_condition or {},
        # Rev 4 fields
        "current_postures": current_postures or {},
        "armed_posture_riders": armed_posture_riders or {},
        "hidden_combatants": hidden_combatants or [],
        "declared_action": declared_action or {},
        "passive_effects_triggered": passive_effects_triggered or [],
        "pool_state": pool_state or {},
        "output_target": {"min_words": 25, "max_words": 60, "format": "prose"},
        "constraints": _constraints(),
    }


def build_scene_framing_payload(
    scene_id: str,
    location_name: str,
    time_of_day: str,
    npcs_present: List[str],
    recent_events: List[str],
    tension_level: str = "calm",
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "scene_framing",
        "register_directive": register,
        "scene_id": scene_id,
        "location": location_name,
        "time_of_day": time_of_day,
        "npcs_present": npcs_present,
        "recent_events": recent_events,
        "tension_level": tension_level,
        "output_target": {"min_words": 60, "max_words": 150, "format": "prose"},
        "constraints": _constraints(),
    }


def build_situation_payload(
    situation_id: str,
    description: str,
    choices: List[Dict[str, str]],
    tension_level: str,
    location_name: str,
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "situation_description",
        "register_directive": register,
        "situation_id": situation_id,
        "description": description,
        "choices": choices,
        "tension_level": tension_level,
        "location": location_name,
        "output_target": {"min_words": 30, "max_words": 80, "format": "mixed"},
        "constraints": _constraints(),
    }


def build_dialogue_payload(
    npc_name: str,
    npc_voice: str,
    topic: str,
    standing: int,
    player_options: List[str],
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "dialogue",
        "register_directive": register,
        "npc_name": npc_name,
        "npc_voice": npc_voice,
        "topic": topic,
        "standing": standing,
        "player_options": player_options,
        "output_target": {"min_words": 20, "max_words": 100, "format": "dialogue"},
        "constraints": _constraints(),
    }


def build_character_creation_payload(
    scene_id: str,
    framing_text: str,
    choices: List[str],
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "character_creation_beat",
        "register_directive": register,
        "scene_id": scene_id,
        "framing_text": framing_text,
        "choices": choices,
        "output_target": {"min_words": 80, "max_words": 200, "format": "mixed"},
        "constraints": _constraints(),
    }


def build_transition_payload(
    from_location: str,
    to_location: str,
    travel_time: str,
    hazards: List[str],
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "transition",
        "register_directive": register,
        "from_location": from_location,
        "to_location": to_location,
        "travel_time": travel_time,
        "hazards": hazards,
        "output_target": {"min_words": 40, "max_words": 100, "format": "prose"},
        "constraints": _constraints(),
    }


def build_death_payload(
    character_name: str,
    cause: str,
    location: str,
    age: int,
    legacy: List[str],
    register: str = "intimate",
) -> Dict[str, Any]:
    return {
        "scene_type": "death_narration",
        "register_directive": register,
        "character_name": character_name,
        "cause": cause,
        "location": location,
        "age": age,
        "legacy": legacy,
        "output_target": {"min_words": 60, "max_words": 150, "format": "prose"},
        "constraints": _constraints(),
    }


def build_time_skip_payload(
    duration: str,
    events_summary: List[str],
    world_changes: List[str],
    register: str = "standard",
) -> Dict[str, Any]:
    return {
        "scene_type": "time_skip",
        "register_directive": register,
        "duration": duration,
        "events_summary": events_summary,
        "world_changes": world_changes,
        "output_target": {"min_words": 50, "max_words": 150, "format": "prose"},
        "constraints": _constraints(),
    }
