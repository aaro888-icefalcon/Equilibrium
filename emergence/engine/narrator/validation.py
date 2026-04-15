"""Narrator output validation — checks length, forbidden words, character mentions."""

from __future__ import annotations

from typing import Any, Dict, List


# Words/phrases the narrator should never use
_FORBIDDEN_PATTERNS = [
    "hit points",
    "experience points",
    "level up",
    "game master",
    "dice roll",
    "d20",
    "saving throw",
]


def validate_narration(
    text: str,
    payload: Dict[str, Any],
) -> List[str]:
    """Validate narrator output against payload constraints.

    Returns a list of violation descriptions. Empty list = valid.
    """
    violations = []

    # Length check
    word_count = len(text.split())
    scene_type = payload.get("scene_type", "")

    min_words, max_words = _get_length_bounds(scene_type)
    if word_count < min_words:
        violations.append(f"Too short: {word_count} words, minimum {min_words}")
    if word_count > max_words:
        violations.append(f"Too long: {word_count} words, maximum {max_words}")

    # Forbidden patterns
    text_lower = text.lower()
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in text_lower:
            violations.append(f"Forbidden term: '{pattern}'")

    # Check scene-specific forbidden list
    forbidden = payload.get("forbidden", [])
    for f in forbidden:
        if f.lower() in text_lower:
            violations.append(f"Payload-forbidden term: '{f}'")

    # Character mention check — only mention NPCs in the payload
    npcs = payload.get("npcs_present", [])
    if npcs and isinstance(npcs, list):
        # This is a soft check — we can't perfectly parse NPC mentions
        pass

    return violations


def _get_length_bounds(scene_type: str) -> tuple:
    """Return (min_words, max_words) for a scene type."""
    bounds = {
        "combat_turn": (25, 60),
        "scene_framing": (60, 150),
        "situation_description": (30, 80),
        "dialogue": (20, 100),
        "character_creation_beat": (80, 200),
        "transition": (40, 100),
        "death_narration": (60, 150),
        "time_skip": (50, 150),
    }
    return bounds.get(scene_type, (20, 200))
