"""Character factory — applies session zero scene results to build a CharacterSheet.

CreationState holds the in-progress sheet and scene metadata.
CharacterFactory applies deltas from each scene's chosen option.
"""

from __future__ import annotations

import dataclasses
import random as _random
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.schemas.character import (
    Attributes,
    CharacterSheet,
    Goal,
    Harm,
    HistoryEvent,
    InventoryItem,
    RelationshipState,
    StatusEffect,
)


@dataclasses.dataclass
class CreationState:
    """In-progress character state during session zero."""

    # Core identity
    name: str = ""
    age_at_onset: int = 25
    species: str = "human"
    seed: int = 0

    # Attribute deltas (applied to base d6=6 for all)
    attribute_deltas: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Condition track overrides
    condition_track_maxes: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Skills accumulated
    skills: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Resources accumulated
    resources: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Heat deltas per faction
    heat_deltas: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Faction standing deltas
    faction_standing_deltas: Dict[str, int] = dataclasses.field(default_factory=dict)

    # Relationships built during session zero
    relationships: Dict[str, Dict[str, Any]] = dataclasses.field(default_factory=dict)

    # Goals accumulated
    goals: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # Powers
    powers: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    power_category_primary: str = ""
    power_category_secondary: Optional[str] = None
    tier: int = 1
    tier_ceiling: int = 3

    # Breakthroughs
    breakthroughs: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # Harm / status accumulated
    harm_entries: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    statuses: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # Corruption
    corruption: int = 0

    # Location
    location: str = ""
    region: str = ""

    # Inventory
    inventory: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # History events
    history: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # Scene tracking
    beat_index: int = 0
    scene_choices: Dict[str, Any] = dataclasses.field(default_factory=dict)

    # Narrative tags
    narrative_tags: List[str] = dataclasses.field(default_factory=list)


class CharacterFactory:
    """Applies scene results and finalizes the character sheet."""

    BASE_ATTRIBUTE = 6  # d6 default
    MAX_SESSION_ZERO_ATTRIBUTE = 10  # d10 cap during session zero

    def apply_scene_result(
        self,
        scene_id: str,
        choice_data: Dict[str, Any],
        state: CreationState,
        rng: _random.Random,
    ) -> CreationState:
        """Apply a scene choice's consequences to the creation state.

        choice_data is a dict with keys like:
          attribute_deltas, skills, resources, heat, goals,
          relationship, narrative_tag, etc.
        """
        # Store the choice
        state.scene_choices[scene_id] = choice_data

        # Attribute deltas
        for attr, delta in choice_data.get("attribute_deltas", {}).items():
            state.attribute_deltas[attr] = state.attribute_deltas.get(attr, 0) + delta

        # Skills
        for skill, level in choice_data.get("skills", {}).items():
            state.skills[skill] = max(state.skills.get(skill, 0), level)

        # Resources
        for resource, amount in choice_data.get("resources", {}).items():
            state.resources[resource] = state.resources.get(resource, 0) + amount

        # Heat deltas
        for faction, delta in choice_data.get("heat", {}).items():
            state.heat_deltas[faction] = state.heat_deltas.get(faction, 0) + delta

        # Faction standing
        for faction, delta in choice_data.get("faction_standing", {}).items():
            state.faction_standing_deltas[faction] = (
                state.faction_standing_deltas.get(faction, 0) + delta
            )

        # Goals
        for goal in choice_data.get("goals", []):
            state.goals.append(goal)

        # Relationship
        rel = choice_data.get("relationship")
        if rel and isinstance(rel, dict):
            npc_id = rel.get("npc_id", f"npc-gen-{len(state.relationships)}")
            state.relationships[npc_id] = rel

        # Powers
        for power in choice_data.get("powers", []):
            state.powers.append(power)

        # Power category
        if "power_category_primary" in choice_data:
            state.power_category_primary = choice_data["power_category_primary"]
        if "power_category_secondary" in choice_data:
            state.power_category_secondary = choice_data["power_category_secondary"]

        # Tier
        if "tier" in choice_data:
            state.tier = choice_data["tier"]
        if "tier_ceiling" in choice_data:
            state.tier_ceiling = choice_data["tier_ceiling"]

        # Breakthroughs
        for bt in choice_data.get("breakthroughs", []):
            state.breakthroughs.append(bt)

        # Harm
        for harm in choice_data.get("harm", []):
            state.harm_entries.append(harm)

        # Statuses
        for status in choice_data.get("statuses", []):
            state.statuses.append(status)

        # Corruption
        state.corruption += choice_data.get("corruption", 0)

        # Location
        if "location" in choice_data:
            state.location = choice_data["location"]
        if "region" in choice_data:
            state.region = choice_data["region"]

        # Condition track maxes
        for track, max_val in choice_data.get("condition_track_maxes", {}).items():
            state.condition_track_maxes[track] = max_val

        # Inventory
        for item in choice_data.get("inventory", []):
            state.inventory.append(item)

        # Narrative tags
        if "narrative_tag" in choice_data:
            state.narrative_tags.append(choice_data["narrative_tag"])

        # History events
        for event in choice_data.get("history", []):
            state.history.append(event)

        # Species
        if "species" in choice_data:
            state.species = choice_data["species"]

        # Name/age
        if "name" in choice_data:
            state.name = choice_data["name"]
        if "age_at_onset" in choice_data:
            state.age_at_onset = choice_data["age_at_onset"]

        state.beat_index += 1
        return state

    def finalize(self, state: CreationState) -> CharacterSheet:
        """Convert the accumulated CreationState into a validated CharacterSheet."""
        # Compute attributes: base + deltas, capped at d10
        attrs = Attributes(
            strength=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("strength", 0)),
            agility=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("agility", 0)),
            perception=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("perception", 0)),
            will=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("will", 0)),
            insight=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("insight", 0)),
            might=self._clamp_attr(self.BASE_ATTRIBUTE + state.attribute_deltas.get("might", 0)),
        )

        # Condition tracks with species overrides (Dict[str, int])
        tracks = {
            "physical": state.condition_track_maxes.get("physical", 5),
            "mental": state.condition_track_maxes.get("mental", 5),
            "social": state.condition_track_maxes.get("social", 5),
        }

        # Build relationships
        relationships = {}
        for npc_id, rel_data in state.relationships.items():
            relationships[npc_id] = RelationshipState(
                standing=rel_data.get("standing", 0),
                current_state=rel_data.get("current_state", "neutral"),
                trust=rel_data.get("trust", 0),
            )

        # Build goals
        goals = []
        for i, g in enumerate(state.goals):
            goals.append(Goal(
                id=g.get("id", f"goal_{i}"),
                description=g.get("description", ""),
                progress=g.get("progress", 0),
                pressure=g.get("pressure", 1),
            ))

        # Build inventory
        inventory = []
        for item in state.inventory:
            inventory.append(InventoryItem(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
            ))

        # Build history
        history = []
        for event in state.history:
            history.append(HistoryEvent(
                date=event.get("timestamp", event.get("date", "T+0")),
                category=event.get("type", event.get("category", "session_zero")),
                description=event.get("description", ""),
            ))

        # Heat object
        base_heat = sum(state.heat_deltas.values())
        heat = {
            "current": max(0, base_heat),
            "faction_modifiers": dict(state.heat_deltas),
        }

        sheet = CharacterSheet(
            name=state.name,
            species=state.species,
            age_at_onset=state.age_at_onset,
            current_age=state.age_at_onset + 1,
            attributes=attrs,
            condition_tracks=tracks,
            powers=state.powers,
            power_category_primary=state.power_category_primary,
            power_category_secondary=state.power_category_secondary,
            tier=state.tier,
            tier_ceiling=state.tier_ceiling,
            breakthroughs=state.breakthroughs,
            heat=heat,
            corruption=state.corruption,
            relationships=relationships,
            inventory=inventory,
            location=state.location,
            history=history,
            skills=dict(state.skills),
            resources=dict(state.resources),
            goals=goals,
            session_zero_choices=dict(state.scene_choices),
        )

        return sheet

    # Valid die sizes for attributes
    _VALID_DICE = [4, 6, 8, 10, 12]

    def _clamp_attr(self, value: int) -> int:
        """Snap attribute to nearest valid die size (d4/d6/d8/d10), capped at d10."""
        clamped = max(4, min(self.MAX_SESSION_ZERO_ATTRIBUTE, value))
        # Snap to nearest valid die size
        valid = [d for d in self._VALID_DICE if d <= self.MAX_SESSION_ZERO_ATTRIBUTE]
        return min(valid, key=lambda d: abs(d - clamped))
