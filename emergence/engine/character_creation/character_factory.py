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

    # Pre-onset context
    onset_circumstance: str = ""
    temperament: str = ""

    # Freeform self-description (scene 0) and danger-scenario reactions (scenes 1, 2).
    # Drive tag extraction for power weighting and narrative mood.
    self_description: str = ""
    scenario_reactions: Dict[str, str] = dataclasses.field(default_factory=dict)

    # Cinematic vignettes presented in scenes 1 and 2 (by slot key: "1" / "2").
    # Stored so narrator can reference them and the slot-2 vignette can avoid reuse.
    scenario_vignettes: Dict[str, str] = dataclasses.field(default_factory=dict)

    # Tags inferred from freeform text (scene 0 description + scene 1/2 reactions).
    reaction_tags: List[str] = dataclasses.field(default_factory=list)

    # NPCs generated during session zero scenes
    generated_npcs: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # Free-form occupation parsed from the life-description scene.  Stored
    # separately from narrative_tags because the occupation look-up in the
    # OCCUPATIONS table is derived from this value.
    occupation: str = ""

    # Structured NPC seeds captured during the life-description scene.
    # Each entry: {name, relation, location, descriptor, status}.  Written
    # into the world's NPC registry at finalize time.
    npc_seeds: List[Dict[str, Any]] = dataclasses.field(default_factory=list)

    # The power slate held between the reaction-text phase of the slate
    # scene (which rebuilds and stores the 10 candidates) and the choice
    # phase (which reads them back).  Empty outside the slate scene.
    pending_slate: List[Dict[str, Any]] = dataclasses.field(default_factory=list)
    pending_slate_scene: str = ""

    # Threats — named NPCs or forces that press on the character. Entries
    # accumulate across scenes (survival raid, faction play, vow enemy) and
    # are finalized into the character sheet's relationships (negative
    # standing) AND its top-level `threats` list for narrator presentation.
    threats: List[Dict[str, Any]] = dataclasses.field(default_factory=list)


class CharacterFactory:
    """Applies scene results and finalizes the character sheet."""

    BASE_ATTRIBUTE = 6  # d6 default
    MAX_SESSION_ZERO_ATTRIBUTE = 10  # d10 cap during session zero
    MAX_SESSION_ZERO_SKILL = 6  # cap per skill during session zero

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

        # Skills (additive across scenes, capped)
        for skill, level in choice_data.get("skills", {}).items():
            state.skills[skill] = min(
                self.MAX_SESSION_ZERO_SKILL,
                state.skills.get(skill, 0) + level,
            )

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

        # Generated NPCs (from specific year-one scenarios)
        for npc in choice_data.get("generated_npcs", []):
            state.generated_npcs.append(npc)

        # Onset circumstance
        if "onset_circumstance" in choice_data:
            state.onset_circumstance = choice_data["onset_circumstance"]

        # Temperament
        if "temperament" in choice_data:
            state.temperament = choice_data["temperament"]

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

        # Self-description (scene 0)
        if "self_description" in choice_data:
            state.self_description = choice_data["self_description"]

        # Scenario reactions (scenes 1, 2) keyed by slot
        for slot, reaction in choice_data.get("scenario_reactions", {}).items():
            state.scenario_reactions[str(slot)] = reaction

        # Scenario vignette IDs (scenes 1, 2) keyed by slot
        for slot, vignette_id in choice_data.get("scenario_vignettes", {}).items():
            state.scenario_vignettes[str(slot)] = vignette_id

        # Reaction tags accumulated across scenes 0-2 (dedup, preserve order)
        for tag in choice_data.get("reaction_tags", []):
            if tag not in state.reaction_tags:
                state.reaction_tags.append(tag)

        # Occupation (life-description scene)
        if "occupation" in choice_data:
            state.occupation = choice_data["occupation"]

        # NPC seeds parsed from the life-description scene
        for seed in choice_data.get("npc_seeds", []):
            state.npc_seeds.append(seed)

        # Pending slate (two-phase slate scene: written on text apply,
        # consumed on choice apply).  An empty list here is a valid reset.
        if "pending_slate" in choice_data:
            state.pending_slate = list(choice_data["pending_slate"])
        if "pending_slate_scene" in choice_data:
            state.pending_slate_scene = choice_data["pending_slate_scene"]

        # Threats — appended, never replaced.
        for threat in choice_data.get("threats", []):
            state.threats.append(threat)

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

        # Build relationships (from both explicit relationships and generated NPCs)
        relationships = {}
        for npc_id, rel_data in state.relationships.items():
            relationships[npc_id] = RelationshipState(
                standing=rel_data.get("standing", 0),
                current_state=rel_data.get("current_state", "neutral"),
                trust=rel_data.get("trust", 0),
            )

        # Merge generated NPCs into relationships
        for npc in state.generated_npcs:
            npc_id = npc.get("npc_id", f"npc-gen-{len(relationships)}")
            if npc_id not in relationships:
                relationships[npc_id] = RelationshipState(
                    standing=npc.get("standing", 0),
                    current_state=npc.get("state", "alive_present"),
                    trust=max(0, npc.get("standing", 0)),
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

        # Finalize threats: merge into relationships (if not already present
        # as negative-standing entries) and expose as a top-level list.
        threats_final = self._finalize_threats(state, relationships)

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
            threats=threats_final,
        )

        return sheet

    def _finalize_threats(
        self,
        state: CreationState,
        relationships: Dict[str, "RelationshipState"],
    ) -> List[Dict[str, Any]]:
        """Merge declared threats into relationships and return the final list.

        Each threat entry has a stable `npc_id`. If that NPC already has a
        relationship row, we keep the existing standing (the scene that
        created the row is authoritative). If not, we add a negative-standing
        row from the threat's own standing field.
        """
        finalized: List[Dict[str, Any]] = []
        seen: set = set()

        for threat in state.threats:
            npc_id = threat.get("npc_id")
            if not npc_id or npc_id in seen:
                continue
            seen.add(npc_id)

            # Ensure a relationship row exists for this threat.
            if npc_id not in relationships:
                standing = int(threat.get("standing", -2))
                relationships[npc_id] = RelationshipState(
                    standing=standing,
                    current_state=threat.get("state", "alive_present"),
                    trust=0,
                )

            finalized.append({
                "npc_id": npc_id,
                "name": threat.get("name", ""),
                "standing": relationships[npc_id].standing,
                "source": threat.get("source", ""),
                "summary": threat.get("summary", ""),
            })

        return finalized

    # Valid die sizes for attributes
    _VALID_DICE = [4, 6, 8, 10, 12]

    def _clamp_attr(self, value: int) -> int:
        """Snap attribute to nearest valid die size (d4/d6/d8/d10), capped at d10."""
        clamped = max(4, min(self.MAX_SESSION_ZERO_ATTRIBUTE, value))
        # Snap to nearest valid die size
        valid = [d for d in self._VALID_DICE if d <= self.MAX_SESSION_ZERO_ATTRIBUTE]
        return min(valid, key=lambda d: abs(d - clamped))
