"""Encounter generator — builds EncounterSpec from a Situation + world state.

Takes the output of SituationGenerator (a Situation with encounter_probability)
and, if an encounter triggers, selects appropriate enemies, builds terrain,
sets conditions, and returns an EncounterSpec ready for EncounterRunner.
"""

from __future__ import annotations

import random
import uuid
from typing import Any, Dict, List, Optional

from emergence.engine.schemas.world import (
    Clock,
    Location,
    NPC,
    Situation,
)
from emergence.engine.schemas.encounter import (
    EncounterSpec,
    TerrainZone,
    WinLossCondition,
    WorldContext,
)


def _extract_player_heat(player: Dict[str, Any]) -> int:
    """Extract a numeric heat value from the player dict.

    Handles multiple heat dict formats:
      - int/float: returned directly
      - {"current": N, "faction_modifiers": {...}}  (character factory)
      - {"total": N}  (combat outcome)
      - {"total": N, "permanent": N, "decayable": N}  (merged)
    """
    heat_raw = player.get("heat", 0)
    if isinstance(heat_raw, dict):
        val = heat_raw.get("current", heat_raw.get("total", 0))
        return val if isinstance(val, (int, float)) else 0
    return heat_raw if isinstance(heat_raw, (int, float)) else 0


# ---------------------------------------------------------------------------
# Enemy templates by register
# ---------------------------------------------------------------------------

_ENEMY_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
    "human": [
        {"id": "raider_scout", "tier": 2, "ai_profile": "aggressive"},
        {"id": "raider_enforcer", "tier": 3, "ai_profile": "aggressive"},
        {"id": "scavenger", "tier": 1, "ai_profile": "defensive"},
        {"id": "militia_soldier", "tier": 2, "ai_profile": "methodical"},
        {"id": "bounty_hunter", "tier": 4, "ai_profile": "predatory"},
    ],
    "creature": [
        {"id": "feral_hound", "tier": 1, "ai_profile": "pack_tactics"},
        {"id": "mutant_stalker", "tier": 3, "ai_profile": "ambush"},
        {"id": "apex_predator", "tier": 5, "ai_profile": "territorial"},
        {"id": "swarm_insects", "tier": 2, "ai_profile": "swarming"},
    ],
    "eldritch": [
        {"id": "void_touched", "tier": 3, "ai_profile": "chaotic"},
        {"id": "echo_shade", "tier": 2, "ai_profile": "predatory"},
        {"id": "mind_weaver", "tier": 4, "ai_profile": "methodical"},
        {"id": "reality_fracture", "tier": 5, "ai_profile": "chaotic"},
    ],
}

# ---------------------------------------------------------------------------
# Terrain templates
# ---------------------------------------------------------------------------

_TERRAIN_TEMPLATES: Dict[str, List[List[Dict[str, Any]]]] = {
    "urban": [
        [
            {"id": "street", "name": "Open Street", "properties": ["exposed"], "description": "A wide street with no cover."},
            {"id": "rubble", "name": "Rubble Cover", "properties": ["cover"], "description": "Collapsed building providing cover."},
        ],
        [
            {"id": "alley", "name": "Narrow Alley", "properties": ["cover"], "description": "A tight alleyway."},
            {"id": "rooftop", "name": "Rooftop", "properties": ["exposed", "elevated"], "description": "High vantage point."},
        ],
    ],
    "wilderness": [
        [
            {"id": "clearing", "name": "Forest Clearing", "properties": ["exposed"], "description": "An open clearing."},
            {"id": "treeline", "name": "Dense Trees", "properties": ["cover"], "description": "Thick forest cover."},
        ],
    ],
    "underground": [
        [
            {"id": "tunnel", "name": "Tunnel", "properties": ["cover", "hazardous"], "description": "A dark, narrow tunnel."},
            {"id": "chamber", "name": "Open Chamber", "properties": ["exposed"], "description": "A wide underground chamber."},
        ],
    ],
}


# ---------------------------------------------------------------------------
# EncounterGenerator
# ---------------------------------------------------------------------------

class EncounterGenerator:
    """Generates EncounterSpec from a Situation and world state."""

    def should_trigger_encounter(
        self,
        situation: Situation,
        rng: random.Random,
    ) -> bool:
        """Roll against encounter_probability to see if combat starts."""
        return rng.random() < situation.encounter_probability

    def generate_encounter(
        self,
        situation: Situation,
        location: Location,
        player: Dict[str, Any],
        clocks: Dict[str, Clock],
        rng: random.Random,
    ) -> EncounterSpec:
        """Build an EncounterSpec from context."""
        register = self._determine_register(location, clocks, rng)
        enemies = self._select_enemies(register, situation, rng)
        terrain = self._build_terrain(location, rng)
        win_conds, loss_conds, escape_conds = self._build_conditions(register)

        # World context
        clock_states = {
            cid: c.current_segment for cid, c in clocks.items()
        }
        world_ctx = WorldContext(
            recent_events=situation.recent_events[:5],
            heat_levels={"player": _extract_player_heat(player)},
            clock_states=clock_states,
        )

        return EncounterSpec(
            id=str(uuid.uuid4()),
            location=location.id,
            player=player,
            enemies=enemies,
            terrain_zones=[TerrainZone(**z) for z in terrain],
            stakes=self._assess_stakes(situation, register),
            win_conditions=win_conds,
            loss_conditions=loss_conds,
            escape_conditions=escape_conds,
            parley_available=(register == "human"),
            world_context=world_ctx,
            combat_register=register,
            opening_situation=f"Encounter at {location.display_name}: tension is {situation.tension}",
        )

    # ── Register determination ────────────────────────────────────────

    def _determine_register(
        self,
        location: Location,
        clocks: Dict[str, Clock],
        rng: random.Random,
    ) -> str:
        """Choose combat register based on location and world state."""
        # Check for eldritch indicators
        eldritch_clocks = [
            c for c in clocks.values()
            if "eldritch" in c.id.lower() or "void" in c.id.lower()
        ]
        eldritch_high = any(
            c.current_segment >= c.total_segments * 0.6
            for c in eldritch_clocks
        ) if eldritch_clocks else False

        # Check for creature indicators
        creature_dangers = [d for d in location.dangers if d in (
            "mutant_activity", "predator_sighting", "feral_pack", "aberrant_creature"
        )]

        # Weighted selection
        weights = {"human": 5.0, "creature": 2.0, "eldritch": 1.0}

        if creature_dangers:
            weights["creature"] += 5.0
        if eldritch_high:
            weights["eldritch"] += 5.0
        if location.controller:
            weights["human"] += 2.0
        if location.type in ("wilderness", "wasteland"):
            weights["creature"] += 3.0

        total = sum(weights.values())
        roll = rng.random() * total
        cumulative = 0.0
        for register, w in weights.items():
            cumulative += w
            if roll <= cumulative:
                return register
        return "human"

    # ── Enemy selection ───────────────────────────────────────────────

    def _select_enemies(
        self,
        register: str,
        situation: Situation,
        rng: random.Random,
    ) -> List[Dict[str, Any]]:
        """Select enemies appropriate for the register and tension."""
        templates = _ENEMY_TEMPLATES.get(register, _ENEMY_TEMPLATES["human"])

        # Number of enemies based on tension
        count_map = {
            "calm": 1,
            "uneasy": rng.randint(1, 2),
            "tense": rng.randint(2, 3),
            "volatile": rng.randint(2, 4),
            "critical": rng.randint(3, 5),
        }
        count = count_map.get(situation.tension, 2)

        enemies: List[Dict[str, Any]] = []
        for i in range(count):
            template = rng.choice(templates)
            enemy = dict(template)
            enemy["id"] = f"{template['id']}_{i}"
            enemies.append(enemy)

        return enemies

    # ── Terrain ───────────────────────────────────────────────────────

    def _build_terrain(
        self,
        location: Location,
        rng: random.Random,
    ) -> List[Dict[str, Any]]:
        """Select terrain zones based on location type."""
        loc_type = location.type
        if loc_type in ("town", "urban", "settlement"):
            templates = _TERRAIN_TEMPLATES.get("urban", _TERRAIN_TEMPLATES["urban"])
        elif loc_type in ("wilderness", "wasteland", "forest"):
            templates = _TERRAIN_TEMPLATES.get("wilderness", _TERRAIN_TEMPLATES["urban"])
        else:
            templates = _TERRAIN_TEMPLATES.get("underground", _TERRAIN_TEMPLATES["urban"])
        return rng.choice(templates)

    # ── Conditions ────────────────────────────────────────────────────

    def _build_conditions(
        self,
        register: str,
    ) -> tuple:
        """Build win/loss/escape conditions based on register."""
        win = [WinLossCondition(type="defeat_all")]
        loss = [WinLossCondition(type="defeat_specific", parameters={"target": "player"})]

        if register == "human":
            escape = [WinLossCondition(type="break_contact")]
            win.append(WinLossCondition(type="convince_parley"))
        elif register == "eldritch":
            escape = [WinLossCondition(type="survive_rounds", parameters={"rounds": 5})]
        else:
            escape = [WinLossCondition(type="break_contact")]

        return win, loss, escape

    # ── Stakes ────────────────────────────────────────────────────────

    def _assess_stakes(self, situation: Situation, register: str) -> str:
        """Determine narrative stakes."""
        if register == "eldritch":
            return "sanity_and_survival"
        if situation.tension in ("volatile", "critical"):
            return "life_or_death"
        return "standard_conflict"
