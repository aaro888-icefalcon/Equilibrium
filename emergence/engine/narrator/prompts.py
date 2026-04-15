"""Prompt library — templates for narrator per prompt-management.md.

Each template is a string with {variable} placeholders.
"""

from __future__ import annotations

from typing import Any, Dict

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES = {
    "combat_turn": (
        "You are narrating a combat scene in Emergence.\n"
        "Register: {register_directive}\n"
        "Round {round}: {actor} uses {action_type}.\n"
        "Result: {action_result}\n"
        "Damage dealt: {damage_dealt}. Status applied: {status_applied}.\n"
        "Enemies remaining: {enemies_remaining}.\n"
        "Player condition: {player_condition}\n\n"
        "FORMAT: 25-60 words. Prose only. No menu, no choices. "
        "Damage and status effects are rendered by the runtime — narrate the "
        "moment, not the mechanics. Do not invent powers not in the payload. "
        "Do not resolve outcomes the player did not choose."
    ),

    "scene_framing": (
        "You are framing a new scene in Emergence.\n"
        "Register: {register_directive}\n"
        "Location: {location}. Time: {time_of_day}.\n"
        "NPCs present: {npcs_present}\n"
        "Recent events: {recent_events}\n"
        "Tension: {tension_level}\n\n"
        "FORMAT: 60-150 words. Prose only. Ground every detail in the "
        "payload. Do not introduce characters not listed. Establish place, "
        "time, and tension through sensory detail, not exposition."
    ),

    "situation_description": (
        "You are describing a situation in Emergence.\n"
        "Register: {register_directive}\n"
        "Location: {location}. Tension: {tension_level}.\n"
        "Description: {description}\n"
        "Choices available: {choices}\n\n"
        "FORMAT: 30-80 words of prose describing the situation, followed by "
        "the numbered choices exactly as listed in the payload. Do not "
        "editorialize the choices. Do not add choices beyond those listed."
    ),

    "dialogue": (
        "You are narrating dialogue in Emergence.\n"
        "Register: {register_directive}\n"
        "NPC: {npc_name}. Voice style: {npc_voice}.\n"
        "Topic: {topic}. Standing with player: {standing}.\n"
        "Player options: {player_options}\n\n"
        "FORMAT: 20-100 words. The NPC speaks in their voice — match the "
        "voice style exactly. Do not invent intent or information not in the "
        "payload. Do not speak for the player character."
    ),

    "character_creation_beat": (
        "You are narrating a character creation scene in Emergence.\n"
        "Register: {register_directive}\n"
        "Scene: {scene_id}\n"
        "Framing: {framing_text}\n"
        "Choices: {choices}\n\n"
        "FORMAT: 80-200 words. Present the scene framing as prose, then "
        "the choices exactly as listed. Do not add choices beyond those "
        "listed. Do not editorialize or rank the choices."
    ),

    "transition": (
        "You are narrating a travel transition in Emergence.\n"
        "Register: {register_directive}\n"
        "From: {from_location}. To: {to_location}.\n"
        "Travel time: {travel_time}.\n"
        "Hazards: {hazards}\n\n"
        "FORMAT: 40-100 words. Prose only. Narrate the journey through "
        "sensory detail — terrain, weather, what the character sees and "
        "hears. Do not invent encounters not in the hazards list."
    ),

    "death_narration": (
        "You are narrating a character's death in Emergence.\n"
        "Register: {register_directive}\n"
        "Character: {character_name}, age {age}.\n"
        "Cause: {cause}. Location: {location}.\n"
        "Legacy: {legacy}\n\n"
        "FORMAT: 60-150 words. Prose only. Focus on who they were and what "
        "they left behind, not the mechanics of dying. No heroic framing. "
        "No consolation. What happened, happened."
    ),

    "time_skip": (
        "You are narrating a time skip in Emergence.\n"
        "Register: {register_directive}\n"
        "Duration: {duration}.\n"
        "Events: {events_summary}\n"
        "World changes: {world_changes}\n\n"
        "FORMAT: 50-150 words. Prose only. Summarize the passage of time "
        "through concrete changes — what shifted, what remained, what the "
        "character noticed. Do not list events mechanically."
    ),
}


def get_prompt(scene_type: str) -> str:
    """Return the prompt template for a scene type."""
    return PROMPT_TEMPLATES.get(scene_type, PROMPT_TEMPLATES.get("scene_framing", ""))


def format_prompt(template: str, payload: Dict[str, Any]) -> str:
    """Format a prompt template with payload values."""
    # Convert non-string values to strings for formatting
    safe_payload = {}
    for key, value in payload.items():
        if isinstance(value, (list, dict)):
            safe_payload[key] = str(value)
        else:
            safe_payload[key] = value

    try:
        return template.format(**safe_payload)
    except KeyError:
        # If template has variables not in payload, do partial formatting
        result = template
        for key, value in safe_payload.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result
