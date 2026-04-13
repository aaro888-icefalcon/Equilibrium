"""Combatant schema for the Emergence game engine.

Extends the Character Sheet concept with combat-specific fields such as
exposure tracks, affinity tables, AI profiles, and retreat/parley conditions.
Uses only the Python standard library.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from enum import Enum

from emergence.engine.schemas.character import (
    Attributes,
    Harm,
    StatusEffect,
    CharacterSheet,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AiProfile(str, Enum):
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    TACTICAL = "tactical"
    OPPORTUNIST = "opportunist"
    PACK = "pack"


class CombatantSide(str, Enum):
    ENEMY = "enemy"
    ALLY = "ally"
    NEUTRAL = "neutral"


class AffinityState(str, Enum):
    VULNERABLE = "vulnerable"
    NEUTRAL = "neutral"
    RESISTANT = "resistant"
    IMMUNE = "immune"
    ABSORB = "absorb"


# ---------------------------------------------------------------------------
# Combatant dataclass
# ---------------------------------------------------------------------------

@dataclass
class Combatant:
    """A character prepared for combat encounters.

    Carries the subset of CharacterSheet data relevant to combat, plus
    combatant-specific fields like AI profile, exposure tracking, and
    affinity tables.
    """

    # Fields mirrored from CharacterSheet
    id: str
    name: str
    species: str
    attributes: Attributes
    condition_tracks: Dict[str, int]
    harm: List[Harm]
    powers: List[str]
    tier: int
    corruption: int
    statuses: List[StatusEffect]

    # Combatant-specific fields
    side: str  # enemy, ally, neutral
    ai_profile: str  # aggressive, defensive, tactical, opportunist, pack
    exposure_track: int = 0
    exposure_max: int = 6
    affinity_table: Dict[str, str] = field(default_factory=dict)  # damage_type -> AffinityState value
    abilities: List[str] = field(default_factory=list)
    template_id: str = ""
    retreat_conditions: List[str] = field(default_factory=list)
    parley_conditions: List[str] = field(default_factory=list)
    motive: str = ""
    threat_assessment: Dict[str, int] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "species": self.species,
            "attributes": self.attributes.to_dict(),
            "condition_tracks": dict(self.condition_tracks),
            "harm": [h.to_dict() for h in self.harm],
            "powers": list(self.powers),
            "tier": self.tier,
            "corruption": self.corruption,
            "statuses": [s.to_dict() for s in self.statuses],
            "side": self.side,
            "ai_profile": self.ai_profile,
            "exposure_track": self.exposure_track,
            "exposure_max": self.exposure_max,
            "affinity_table": dict(self.affinity_table),
            "abilities": list(self.abilities),
            "template_id": self.template_id,
            "retreat_conditions": list(self.retreat_conditions),
            "parley_conditions": list(self.parley_conditions),
            "motive": self.motive,
            "threat_assessment": dict(self.threat_assessment),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Combatant":
        return cls(
            id=data["id"],
            name=data["name"],
            species=data.get("species", "human"),
            attributes=Attributes.from_dict(data["attributes"])
            if "attributes" in data
            else Attributes(),
            condition_tracks=data.get(
                "condition_tracks",
                {"physical": 0, "mental": 0, "social": 0},
            ),
            harm=[Harm.from_dict(h) for h in data.get("harm", [])],
            powers=data.get("powers", []),
            tier=data.get("tier", 1),
            corruption=data.get("corruption", 0),
            statuses=[
                StatusEffect.from_dict(s) for s in data.get("statuses", [])
            ],
            side=data["side"],
            ai_profile=data["ai_profile"],
            exposure_track=data.get("exposure_track", 0),
            exposure_max=data.get("exposure_max", 6),
            affinity_table=data.get("affinity_table", {}),
            abilities=data.get("abilities", []),
            template_id=data.get("template_id", ""),
            retreat_conditions=data.get("retreat_conditions", []),
            parley_conditions=data.get("parley_conditions", []),
            motive=data.get("motive", ""),
            threat_assessment=data.get("threat_assessment", {}),
        )

    @classmethod
    def from_character_sheet(
        cls,
        sheet: CharacterSheet,
        side: str,
        ai_profile: str,
    ) -> "Combatant":
        """Create a Combatant from an existing CharacterSheet.

        Args:
            sheet: The source character sheet.
            side: One of "enemy", "ally", or "neutral".
            ai_profile: One of "aggressive", "defensive", "tactical",
                        "opportunist", or "pack".

        Returns:
            A new Combatant instance populated from the character sheet.
        """
        return cls(
            id=sheet.id,
            name=sheet.name,
            species=sheet.species,
            attributes=Attributes.from_dict(sheet.attributes.to_dict()),
            condition_tracks=dict(sheet.condition_tracks),
            harm=[Harm.from_dict(h.to_dict()) for h in sheet.harm],
            powers=list(sheet.powers),
            tier=sheet.tier,
            corruption=sheet.corruption,
            statuses=[
                StatusEffect.from_dict(s.to_dict()) for s in sheet.statuses
            ],
            side=side,
            ai_profile=ai_profile,
        )
