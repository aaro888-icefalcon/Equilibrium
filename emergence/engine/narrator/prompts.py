"""Prompt library — templates for narrator per prompt-management.md.

Each template is a string with {variable} placeholders. Every composed
prompt is prefixed with the static canonical-voice preamble loaded from
``emergence/prompts/canonical_voice.md``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

# ---------------------------------------------------------------------------
# Canonical voice preamble (load-bearing — prepended to every composed prompt)
# ---------------------------------------------------------------------------

_PREAMBLE_PATH = Path(__file__).resolve().parent.parent.parent / "prompts" / "canonical_voice.md"


def _load_preamble() -> str:
    """Read canonical_voice.md from disk. Called once at module import."""
    try:
        return _PREAMBLE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Engine must not crash if the preamble is missing during tooling;
        # composer falls back to scene template only and the validator will
        # catch the missing-voice regression downstream.
        return ""


_CANONICAL_PREAMBLE: str = _load_preamble()

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES = {
    "combat_turn": (
        "SCENE: combat_turn\n"
        "Register: {register_directive}\n"
        "Round {round}: {actor} uses {action_type}.\n"
        "Result: {action_result}\n"
        "Damage dealt: {damage_dealt}. Status applied: {status_applied}.\n"
        "Enemies remaining: {enemies_remaining}.\n"
        "Player condition: {player_condition}\n\n"
        "STRUCTURE (emit in this exact order):\n"
        "1. Prose beat, 2-4 short declaratives, paratactic/right-branching, "
        "including at least one fragment paragraph (e.g. \"Opportunity.\" / "
        "\"Thud. Thud.\") and one precise-technical-noun + pulp-verb adjacency.\n"
        "2. ROLL block:\n"
        "   **ROLL: <ACTION>**\n"
        "   **Dice:** d1 + d2 = sum\n"
        "   **Modifiers:** +X (LABEL) ...\n"
        "   **Total:** T vs DC D (tag)\n"
        "   **Result:** **TIER**\n"
        "3. Italic damage line: *Damage dealt: X | Damage taken: Y*\n"
        "4. Consequence prose, 1-2 sentences, closing on a compressed aphoristic single-line paragraph.\n"
        "5. ASCII UI box with HP/SP/options flush against prose.\n\n"
        "Mechanism language (dice, DC, damage numbers, HP/SP) lives ONLY inside "
        "the ROLL block or UI box. Do not invent powers not in the payload. "
        "Do not resolve outcomes the player did not choose. Run the canonical "
        "self-audit before emitting. Cap total revisions at 2."
    ),

    "scene_framing": (
        "SCENE: scene_framing\n"
        "Register: {register_directive}\n"
        "Location: {location}. Time: {time_of_day}.\n"
        "NPCs present: {npcs_present}\n"
        "Recent events: {recent_events}\n"
        "Tension: {tension_level}\n\n"
        "STRUCTURE: Sensation -> Information -> Invitation, in canonical rhythm.\n"
        "- Open on one specific concrete noun (harbor tar, diesel, rust, ozone, the sound of wind). Claim-first.\n"
        "- Ground setting with real proper nouns before any unreal element.\n"
        "- **Bold** faction sigils, tactical landmarks, named NPCs on first mention.\n"
        "- If a reveal is present, deploy \"It's not X. It's Y.\" negative-definition pivot.\n"
        "- Close on a fragment-paragraph invitation or scene-capping aphorism.\n\n"
        "60-150 words. No ROLL block, no UI box. Ground every detail in the "
        "payload. Do not introduce characters not listed. Run the canonical "
        "self-audit before emitting."
    ),

    "situation_description": (
        "SCENE: situation_description\n"
        "Register: {register_directive}\n"
        "Location: {location}. Tension: {tension_level}.\n"
        "Description: {description}\n"
        "Choices available: {choices}\n\n"
        "STRUCTURE: scene_framing rhythm, shorter.\n"
        "- If a target NPC has declared intent, surface **Intent:** as a colon-prefaced bolded label line.\n"
        "- \"It's not X. It's Y.\" permitted at reveal moments.\n"
        "- Close on a scene-capping aphorism or fragment paragraph.\n\n"
        "30-80 words of prose, followed by the numbered choices exactly as "
        "listed in the payload. Do not editorialize the choices. Do not add "
        "choices beyond those listed. Run the canonical self-audit before emitting."
    ),

    "dialogue": (
        "SCENE: dialogue\n"
        "Register: {register_directive}\n"
        "NPC: {npc_name}. Voice style: {npc_voice}.\n"
        "Topic: {topic}. Standing with player: {standing}.\n"
        "Player options: {player_options}\n\n"
        "STRUCTURE: canonical prose wraps quoted NPC dialogue.\n"
        "- One-line physical-detail anchor for the NPC (armor heat, masked breath, heat radiating from armor) before or after the quote.\n"
        "- If payload has `opposed: true`, emit inline **ROLL: Negotiation** block: `Result: T vs DC D` (**TIER**).\n"
        "- Respect disposition cap — no cooperation beyond payload-declared bound.\n"
        "- Close on negative-definition pivot when NPC stance changes (\"It's not a greeting. It's a **measurement**.\" template).\n"
        "- UI box after NPC reply only if `options_changed: true`.\n\n"
        "30-140 words. Match the NPC's voice style exactly. Do not invent intent "
        "or information not in the payload. Do not speak for the player character. "
        "Run the canonical self-audit before emitting."
    ),

    "character_creation_beat": (
        "SCENE: character_creation_beat\n"
        "Register: {register_directive}\n"
        "Scene: {scene_id}\n"
        "Framing: {framing_text}\n"
        "Choices: {choices}\n\n"
        "STRUCTURE: canonical rhythm at the register directed by the payload.\n"
        "- ROLL block ONLY if the beat actually rolls (session-zero scenes 2/5/7).\n"
        "- UI box ONLY for choice-surface beats.\n"
        "- \"intimate\" register uses slower cadence + shorter paragraphs.\n\n"
        "80-200 words. Present the scene framing as prose, then the choices "
        "exactly as listed. Do not add choices beyond those listed. Do not "
        "editorialize or rank the choices. Run the canonical self-audit."
    ),

    "transition": (
        "SCENE: transition\n"
        "Register: {register_directive}\n"
        "From: {from_location}. To: {to_location}.\n"
        "Travel time: {travel_time}.\n"
        "Hazards: {hazards}\n\n"
        "STRUCTURE: scene-transition rhythm of Passage 2.\n"
        "- Fragment-paragraph pivot opens the beat (\"Then, it stops.\", \"The air changes.\", \"You cross West 23rd.\").\n"
        "- Deploy \"It's not X. It's Y.\" when the reveal is a category shift.\n"
        "- Decompose abstract category with >= 2 concrete referents before the pivot lands.\n"
        "- Specific real-world geography where applicable.\n"
        "- End on a one-line scene-capping aphorism.\n\n"
        "40-100 words. No UI box. Do not invent encounters not in the hazards list. "
        "Run the canonical self-audit before emitting."
    ),

    "death_narration": (
        "SCENE: death_narration\n"
        "Register: {register_directive}\n"
        "Character: {character_name}, age {age}.\n"
        "Cause: {cause}. Location: {location}.\n"
        "Legacy: {legacy}\n\n"
        "STRUCTURE: canonical rhythm in \"quiet\" register.\n"
        "- Slower cadence, shorter paragraphs.\n"
        "- No **bold** except for named killer or named power.\n"
        "- No UI box.\n"
        "- Scene-capping single-line paragraph: fact-first (\"He bleeds out at 4:12 AM.\" style), not emotional close-up.\n\n"
        "60-150 words. Focus on who they were and what they left behind, not "
        "the mechanics of dying. No heroic framing. No consolation. What "
        "happened, happened. Run the canonical self-audit before emitting."
    ),

    "time_skip": (
        "SCENE: time_skip\n"
        "Register: {register_directive}\n"
        "Duration: {duration}.\n"
        "Events: {events_summary}\n"
        "World changes: {world_changes}\n\n"
        "STRUCTURE: canonical rhythm.\n"
        "- Open on a compressed declarative fragment (\"Three days.\" / \"A week.\" / \"Two months.\").\n"
        "- One simile from medical, mechanical, or military domain maximum.\n"
        "- No UI box, no ROLL block.\n"
        "- Close on a scene-capping aphorism.\n\n"
        "50-150 words. Summarize the passage of time through concrete changes — "
        "what shifted, what remained, what the character noticed. Do not list "
        "events mechanically. Run the canonical self-audit before emitting."
    ),
}


def get_prompt(scene_type: str) -> str:
    """Return the prompt template for a scene type."""
    return PROMPT_TEMPLATES.get(scene_type, PROMPT_TEMPLATES.get("scene_framing", ""))


def format_prompt(template: str, payload: Dict[str, Any]) -> str:
    """Format a prompt template with payload values, prepended by the canonical preamble.

    The canonical voice preamble is injected verbatim ahead of the scene-specific
    template, separated by a ``---`` horizontal rule. Preamble is never truncated.
    """
    rendered = _render_template(template, payload)
    if _CANONICAL_PREAMBLE:
        return f"{_CANONICAL_PREAMBLE}\n\n---\n\n{rendered}"
    return rendered


def _render_template(template: str, payload: Dict[str, Any]) -> str:
    """Substitute ``{placeholder}`` values from the payload into the template."""
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


def compose_narrator_prompt(scene_type: str, payload: Dict[str, Any]) -> str:
    """Compose the full narrator prompt: canonical preamble + scene template, formatted with payload.

    This is the canonical entry point. Callers should prefer this over
    ``format_prompt(get_prompt(scene_type), payload)`` so the preamble injection
    is guaranteed.
    """
    template = get_prompt(scene_type)
    return format_prompt(template, payload)
