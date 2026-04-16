"""Social interaction logic: seeding blocks, disposition bounds, patience.

Implements hard mechanical limits on NPC social interactions:
- Seed SocialBlock from existing NPC fields (lazy: only when scene starts)
- Disposition bounds cap outcomes regardless of roll result
- Patience decrements per social action; hits 0 → interaction_ended
- Disposition shifts on CRITICAL (+1) or FUMBLE (-1), capped per scene
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from emergence.engine.combat.resolution import SuccessTier
from emergence.engine.schemas.world import (
    NPC,
    SocialBlock,
    DISPOSITION_OUTCOME_BOUNDS,
)


# ---------------------------------------------------------------------------
# Outcome tier ranks for disposition bound enforcement
# ---------------------------------------------------------------------------

# Maps each outcome bound to a rank (higher = better cooperation)
_BOUND_RANKS = {
    "doesnt_attack": 0,
    "grudging_tolerance": 1,
    "non_interference": 2,
    "transactional": 3,
    "willing_cooperation": 4,
    "proactive_help": 5,
    "sacrifice_loyalty": 6,
}

# Maps each SuccessTier to the minimum disposition rank required to achieve it
# This translates roll success into real-world cooperation levels
_TIER_REQUIRED_RANK = {
    SuccessTier.FUMBLE.value: 0,          # Can happen at any disposition
    SuccessTier.FAILURE.value: 0,
    SuccessTier.PARTIAL_FAILURE.value: 1,  # Requires at least grudging tolerance
    SuccessTier.MARGINAL.value: 3,         # Requires transactional (quid pro quo)
    SuccessTier.FULL.value: 4,             # Requires willing cooperation
    SuccessTier.CRITICAL.value: 5,         # Requires proactive help
}


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------

def _infer_mood(personality_traits: list) -> str:
    """Infer NPC mood from personality traits."""
    traits = [str(t).lower() for t in personality_traits]
    if any(t in traits for t in ("angry", "hostile", "furious")):
        return "angry"
    if any(t in traits for t in ("wary", "cautious", "suspicious")):
        return "wary"
    if any(t in traits for t in ("amused", "cheerful", "playful")):
        return "amused"
    if any(t in traits for t in ("fearful", "anxious", "nervous")):
        return "fearful"
    if any(t in traits for t in ("grieving", "mournful", "sad")):
        return "grieving"
    return "neutral"


def _patience_from_disposition(disposition: int) -> int:
    """Hostile NPCs have less patience, friendly NPCs more."""
    return max(1, 3 + disposition)


def seed_social_block(npc: NPC) -> SocialBlock:
    """Create a SocialBlock from existing NPC fields.

    Called lazily during scene generation when npc.social_block is None.
    """
    disposition = getattr(npc, "standing_with_player_default", 0)
    motivation = getattr(npc, "what_they_want_from_player", "") or "unknown"

    concerns = getattr(npc, "current_concerns", [])
    source_of_conflict = concerns[0] if concerns else "busy with own affairs"

    traits = getattr(npc, "personality_traits", [])
    mood = _infer_mood(traits)

    patience_max = _patience_from_disposition(disposition)

    return SocialBlock(
        disposition=disposition,
        patience=patience_max,
        patience_max=patience_max,
        motivation=motivation,
        source_of_conflict=source_of_conflict,
        mood=mood,
        disposition_shift_cap=1,
        disposition_shifted=0,
    )


def ensure_social_block(npc: NPC) -> SocialBlock:
    """Return the NPC's social block, seeding it if needed."""
    if npc.social_block is None:
        npc.social_block = seed_social_block(npc)
    return npc.social_block


# ---------------------------------------------------------------------------
# Disposition bounds enforcement
# ---------------------------------------------------------------------------

def enforce_disposition_bounds(
    disposition: int, outcome_tier: str
) -> Tuple[str, bool, Optional[str]]:
    """Cap the outcome tier based on NPC disposition.

    Returns:
        (effective_tier, was_capped, cap_reason)

    Example: CRITICAL roll against disposition -2 NPC → capped at PARTIAL_FAILURE
    (best case is "grudging_tolerance" which maps to tier rank 1).
    """
    disp_clamped = max(-3, min(3, disposition))
    max_bound = DISPOSITION_OUTCOME_BOUNDS[disp_clamped]
    max_rank = _BOUND_RANKS[max_bound]

    required_rank = _TIER_REQUIRED_RANK.get(outcome_tier, 0)
    if required_rank <= max_rank:
        return (outcome_tier, False, None)

    # Downgrade to highest tier allowed by disposition
    # Find the highest tier whose required rank <= max_rank
    allowed_tier = SuccessTier.FAILURE.value
    for tier_val, req in sorted(
        _TIER_REQUIRED_RANK.items(), key=lambda x: x[1], reverse=True
    ):
        if req <= max_rank:
            allowed_tier = tier_val
            break

    return (
        allowed_tier,
        True,
        f"NPC disposition {disposition} caps outcome at '{max_bound}'",
    )


# ---------------------------------------------------------------------------
# Patience and disposition shifts
# ---------------------------------------------------------------------------

def decrement_patience(
    block: SocialBlock, outcome_tier: str
) -> Dict[str, Any]:
    """Decrement patience based on outcome, return state dict."""
    decrement = 2 if outcome_tier == SuccessTier.FUMBLE.value else 1
    block.patience = max(0, block.patience - decrement)
    return {
        "patience_before": block.patience + decrement,
        "patience_after": block.patience,
        "patience_max": block.patience_max,
        "interaction_ended": block.patience == 0,
    }


def apply_disposition_shift(
    block: SocialBlock, outcome_tier: str
) -> Dict[str, Any]:
    """Shift disposition on CRITICAL (+1) or FUMBLE (-1), within cap."""
    shift = 0
    if outcome_tier == SuccessTier.CRITICAL.value:
        shift = 1
    elif outcome_tier == SuccessTier.FUMBLE.value:
        shift = -1

    # Check against cap
    if shift != 0:
        if abs(block.disposition_shifted + shift) > block.disposition_shift_cap:
            shift = 0  # Cap reached

    if shift != 0:
        block.disposition += shift
        block.disposition_shifted += shift
        # Clamp
        block.disposition = max(-3, min(3, block.disposition))

    return {
        "shift": shift,
        "disposition": block.disposition,
        "disposition_shifted": block.disposition_shifted,
    }


def reset_scene_state(block: SocialBlock) -> None:
    """Reset per-scene state at scene boundary."""
    block.patience = block.patience_max
    block.disposition_shifted = 0
