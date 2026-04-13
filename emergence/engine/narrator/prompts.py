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
        "Narrate this combat moment in 40-80 words. "
        "Do not invent powers not in the payload. "
        "Do not resolve outcomes the player did not choose."
    ),

    "scene_framing": (
        "You are framing a new scene in Emergence.\n"
        "Register: {register_directive}\n"
        "Location: {location}. Time: {time_of_day}.\n"
        "NPCs present: {npcs_present}\n"
        "Recent events: {recent_events}\n"
        "Tension: {tension_level}\n\n"
        "Frame this scene in 60-120 words. "
        "Ground details in the payload. "
        "Do not introduce characters not listed."
    ),

    "situation_description": (
        "You are describing a situation in Emergence.\n"
        "Register: {register_directive}\n"
        "Location: {location}. Tension: {tension_level}.\n"
        "Description: {description}\n"
        "Choices available: {choices}\n\n"
        "Describe the situation in 80-150 words. "
        "Present the choices clearly."
    ),

    "dialogue": (
        "You are narrating dialogue in Emergence.\n"
        "Register: {register_directive}\n"
        "NPC: {npc_name}. Voice style: {npc_voice}.\n"
        "Topic: {topic}. Standing with player: {standing}.\n"
        "Player options: {player_options}\n\n"
        "Write the NPC's dialogue in 40-100 words using their voice style. "
        "Do not speak for the player."
    ),

    "character_creation_beat": (
        "You are narrating a character creation scene in Emergence.\n"
        "Register: {register_directive}\n"
        "Scene: {scene_id}\n"
        "Framing: {framing_text}\n"
        "Choices: {choices}\n\n"
        "Present this scene in 60-120 words. "
        "Do not add choices beyond those listed."
    ),

    "transition": (
        "You are narrating a travel transition in Emergence.\n"
        "Register: {register_directive}\n"
        "From: {from_location}. To: {to_location}.\n"
        "Travel time: {travel_time}.\n"
        "Hazards: {hazards}\n\n"
        "Narrate the journey in 40-80 words."
    ),

    "death_narration": (
        "You are narrating a character's death in Emergence.\n"
        "Register: {register_directive}\n"
        "Character: {character_name}, age {age}.\n"
        "Cause: {cause}. Location: {location}.\n"
        "Legacy: {legacy}\n\n"
        "Write a death narration in 80-150 words. "
        "Be respectful. Focus on what they meant, not how they ended."
    ),

    "time_skip": (
        "You are narrating a time skip in Emergence.\n"
        "Register: {register_directive}\n"
        "Duration: {duration}.\n"
        "Events: {events_summary}\n"
        "World changes: {world_changes}\n\n"
        "Summarize the passage of time in 60-120 words."
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
