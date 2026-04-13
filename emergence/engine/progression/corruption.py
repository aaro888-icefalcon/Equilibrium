"""Corruption engine — 0-6 scale with progressive effects.

0: baseline, 1-2: touched (cosmetic), 3-4: changed (visible),
5: transforming (severe), 6: transformed (irreversible, becomes NPC).
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional


# Effects at each corruption segment
CORRUPTION_EFFECTS = {
    0: [],
    1: [
        "Eyes shift color faintly",
        "Skin shows faint pattern",
        "Voice carries subtle resonance",
        "Sleep shortens; vivid dreams",
    ],
    2: [
        "Auratic minor effect; NPCs feel uneasy",
        "One sense enhanced",
        "Hands cold/warm to others",
    ],
    3: [
        "Visible physical alteration; commerce +1 difficulty",
        "Behavioral compulsion",
        "eldritch_corruptive cost -1",
    ],
    4: [
        "Persistent harm tier 2",
        "Relationship trust ceiling -1 with non-corrupted NPCs",
        "New tier-1 eldritch power offered",
    ],
    5: [
        "Visible transformation (not fully human)",
        "Persistent harm tier 2 (unhealable ordinary means)",
        "Aging halts",
        "Monthly will check vs DC 12 or corruption +1",
        "Faction standings cap at 1 except eldritch-aligned",
    ],
    6: [
        "Transformation complete — character becomes NPC",
        "Character Sheet locked",
        "All faction standings -2 minimum",
        "Inheritance triggered",
    ],
}


class CorruptionEffect:
    """An effect of corruption gain/change."""

    def __init__(self, description: str, mechanical: Dict[str, Any] | None = None) -> None:
        self.description = description
        self.mechanical = mechanical or {}


class CorruptionEngine:
    """Manages corruption accumulation and consequences."""

    def apply_corruption(
        self,
        character: Dict[str, Any],
        amount: float,
        source: str = "",
    ) -> List[CorruptionEffect]:
        """Apply corruption to a character. Returns list of new effects."""
        old_corruption = character.get("corruption", 0)
        new_corruption = min(6, old_corruption + amount)
        character["corruption"] = new_corruption

        # Track source
        sources = character.get("corruption_sources", [])
        sources.append({"amount": amount, "source": source})
        character["corruption_sources"] = sources

        effects = []

        # Check for threshold crossings
        old_segment = int(old_corruption)
        new_segment = int(new_corruption)

        for seg in range(old_segment + 1, new_segment + 1):
            segment_effects = self._apply_segment_effects(character, seg)
            effects.extend(segment_effects)

        return effects

    def check_corruption_consequences(
        self,
        character: Dict[str, Any],
        rng: _random.Random | None = None,
    ) -> List[CorruptionEffect]:
        """Check ongoing corruption consequences (monthly tick)."""
        if rng is None:
            rng = _random.Random()

        corruption = character.get("corruption", 0)
        effects = []

        # Segment 5: monthly will check vs DC 12
        if corruption >= 5 and corruption < 6:
            will = character.get("attributes", {}).get("will", 6)
            roll = rng.randint(1, will)
            if roll < 12:
                character["corruption"] = min(6, corruption + 1)
                effects.append(CorruptionEffect(
                    "Failed will check — corruption advances",
                    {"corruption_gained": 1},
                ))

                # Check if hit 6
                if character["corruption"] >= 6:
                    effects.extend(self._apply_segment_effects(character, 6))

        return effects

    def get_corruption_level(self, character: Dict[str, Any]) -> int:
        """Get current corruption segment (0-6)."""
        return int(character.get("corruption", 0))

    def get_corruption_label(self, character: Dict[str, Any]) -> str:
        """Get descriptive label for corruption level."""
        seg = self.get_corruption_level(character)
        labels = {
            0: "baseline",
            1: "touched_cosmetic",
            2: "touched_perceptible",
            3: "changed_visible",
            4: "changed_significant",
            5: "transforming",
            6: "transformed",
        }
        return labels.get(seg, "baseline")

    def is_reversible(self, character: Dict[str, Any]) -> bool:
        """Check if current corruption is reversible."""
        seg = self.get_corruption_level(character)
        return seg <= 4

    def attempt_reversal(
        self,
        character: Dict[str, Any],
        method: str,
        rng: _random.Random | None = None,
    ) -> Optional[CorruptionEffect]:
        """Attempt to reduce corruption.

        Methods: absence (2yr), biokinetic, sacrifice.
        Returns effect if successful.
        """
        seg = self.get_corruption_level(character)

        if seg == 0:
            return None

        # Segments 1-2: full reversal possible
        if seg <= 2:
            character["corruption"] = max(0, character["corruption"] - 1)
            return CorruptionEffect(
                f"Corruption reduced via {method}",
                {"corruption_reduced": 1},
            )

        # Segments 3-4: partial reversal (max -1 per 5 years)
        if seg <= 4:
            last_reversal = character.get("last_corruption_reversal_year", -10)
            current_year = character.get("age", 25)
            if current_year - last_reversal >= 5:
                character["corruption"] = max(0, character["corruption"] - 1)
                character["last_corruption_reversal_year"] = current_year
                return CorruptionEffect(
                    f"Corruption partially reversed via {method}",
                    {"corruption_reduced": 1},
                )

        # Segment 5: near-irreversible
        if seg == 5 and method in ("patron_release", "counter_bargain"):
            character["corruption"] = max(4, character["corruption"] - 1)
            return CorruptionEffect(
                f"Corruption reversed from transforming via {method}",
                {"corruption_reduced": 1},
            )

        # Segment 6: irreversible
        return None

    def _apply_segment_effects(
        self,
        character: Dict[str, Any],
        segment: int,
    ) -> List[CorruptionEffect]:
        """Apply effects for reaching a corruption segment."""
        effects = []
        descriptions = CORRUPTION_EFFECTS.get(segment, [])

        if segment == 5:
            # All effects apply at segment 5
            for desc in descriptions:
                effects.append(CorruptionEffect(desc))
            character["aging_halted"] = True
            character["faction_standing_cap"] = 1

        elif segment == 6:
            # Transformation
            for desc in descriptions:
                effects.append(CorruptionEffect(desc))
            character["status"] = "transformed"
            character["sheet_locked"] = True

        else:
            # Pick one effect for segments 1-4
            if descriptions:
                effects.append(CorruptionEffect(descriptions[0]))

        return effects
