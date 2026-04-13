"""Scene 5 — Manifestation Moment.

Circumstance-conditioned weighted draw + tier roll + power selection.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.session_zero import Scene
from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)

# Population baseline fractions
_BASE_FRACTIONS = {
    "physical_kinetic": 0.28,
    "perceptual_mental": 0.15,
    "matter_energy": 0.14,
    "biological_vital": 0.14,
    "auratic": 0.12,
    "temporal_spatial": 0.09,
    "eldritch_corruptive": 0.015,
}

# Per-circumstance multiplicative tilts
_CIRCUMSTANCE_TILTS = {
    "A": {"physical_kinetic": 1.0, "perceptual_mental": 1.4, "matter_energy": 1.2, "biological_vital": 0.9, "auratic": 1.0, "temporal_spatial": 1.1, "eldritch_corruptive": 1.0},
    "B": {"physical_kinetic": 1.3, "perceptual_mental": 0.9, "matter_energy": 1.1, "biological_vital": 1.2, "auratic": 1.0, "temporal_spatial": 0.8, "eldritch_corruptive": 0.9},
    "C": {"physical_kinetic": 1.4, "perceptual_mental": 1.0, "matter_energy": 0.9, "biological_vital": 0.8, "auratic": 0.8, "temporal_spatial": 1.4, "eldritch_corruptive": 0.9},
    "D": {"physical_kinetic": 0.9, "perceptual_mental": 1.2, "matter_energy": 0.9, "biological_vital": 1.4, "auratic": 1.4, "temporal_spatial": 0.8, "eldritch_corruptive": 0.9},
    "E": {"physical_kinetic": 1.0, "perceptual_mental": 1.3, "matter_energy": 0.9, "biological_vital": 1.0, "auratic": 1.3, "temporal_spatial": 0.9, "eldritch_corruptive": 1.0},
    "F": {"physical_kinetic": 0.7, "perceptual_mental": 1.6, "matter_energy": 0.8, "biological_vital": 1.1, "auratic": 1.1, "temporal_spatial": 1.4, "eldritch_corruptive": 1.2},
    "G": {"physical_kinetic": 1.8, "perceptual_mental": 0.9, "matter_energy": 1.0, "biological_vital": 1.0, "auratic": 0.9, "temporal_spatial": 1.0, "eldritch_corruptive": 0.7},
    "H": {"physical_kinetic": 1.4, "perceptual_mental": 1.2, "matter_energy": 1.0, "biological_vital": 1.2, "auratic": 1.0, "temporal_spatial": 0.8, "eldritch_corruptive": 1.2},
}

# Session-zero tier pyramid (T1-T4 only)
_SZ_TIER_PYRAMID = {1: 0.50, 2: 0.30, 3: 0.15, 4: 0.05}

# Starting power templates per category
_STARTER_POWERS = {
    "physical_kinetic": [
        {"id": "pow_enhanced_strength", "name": "Enhanced Strength", "tier_min": 1},
        {"id": "pow_kinetic_burst", "name": "Kinetic Burst", "tier_min": 1},
        {"id": "pow_speed_surge", "name": "Speed Surge", "tier_min": 1},
        {"id": "pow_impact_redirect", "name": "Impact Redirect", "tier_min": 2},
        {"id": "pow_momentum_strike", "name": "Momentum Strike", "tier_min": 3},
        {"id": "pow_kinetic_shield", "name": "Kinetic Shield", "tier_min": 3},
    ],
    "perceptual_mental": [
        {"id": "pow_heightened_senses", "name": "Heightened Senses", "tier_min": 1},
        {"id": "pow_danger_sense", "name": "Danger Sense", "tier_min": 1},
        {"id": "pow_empathic_read", "name": "Empathic Read", "tier_min": 1},
        {"id": "pow_intent_detection", "name": "Intent Detection", "tier_min": 2},
        {"id": "pow_precognitive_flash", "name": "Precognitive Flash", "tier_min": 3},
        {"id": "pow_mental_projection", "name": "Mental Projection", "tier_min": 3},
    ],
    "matter_energy": [
        {"id": "pow_heat_manipulation", "name": "Heat Manipulation", "tier_min": 1},
        {"id": "pow_material_shaping", "name": "Material Shaping", "tier_min": 1},
        {"id": "pow_electrical_touch", "name": "Electrical Touch", "tier_min": 1},
        {"id": "pow_density_shift", "name": "Density Shift", "tier_min": 2},
        {"id": "pow_disintegration_touch", "name": "Disintegration Touch", "tier_min": 3},
        {"id": "pow_energy_absorption", "name": "Energy Absorption", "tier_min": 3},
    ],
    "biological_vital": [
        {"id": "pow_accelerated_healing", "name": "Accelerated Healing", "tier_min": 1},
        {"id": "pow_toxin_resistance", "name": "Toxin Resistance", "tier_min": 1},
        {"id": "pow_vital_sense", "name": "Vital Sense", "tier_min": 1},
        {"id": "pow_regeneration", "name": "Regeneration", "tier_min": 2},
        {"id": "pow_biokinesis", "name": "Biokinesis", "tier_min": 3},
        {"id": "pow_life_drain", "name": "Life Drain", "tier_min": 3},
    ],
    "auratic": [
        {"id": "pow_calming_presence", "name": "Calming Presence", "tier_min": 1},
        {"id": "pow_emotional_projection", "name": "Emotional Projection", "tier_min": 1},
        {"id": "pow_charismatic_aura", "name": "Charismatic Aura", "tier_min": 1},
        {"id": "pow_fear_induction", "name": "Fear Induction", "tier_min": 2},
        {"id": "pow_aura_suppression", "name": "Aura Suppression", "tier_min": 3},
        {"id": "pow_mass_influence", "name": "Mass Influence", "tier_min": 3},
    ],
    "temporal_spatial": [
        {"id": "pow_spatial_awareness", "name": "Spatial Awareness", "tier_min": 1},
        {"id": "pow_short_blink", "name": "Short Blink", "tier_min": 1},
        {"id": "pow_reflex_acceleration", "name": "Reflex Acceleration", "tier_min": 2},
        {"id": "pow_phase_step", "name": "Phase Step", "tier_min": 2},
        {"id": "pow_temporal_stutter", "name": "Temporal Stutter", "tier_min": 3},
        {"id": "pow_spatial_fold", "name": "Spatial Fold", "tier_min": 3},
    ],
    "eldritch_corruptive": [
        {"id": "pow_eldritch_whisper", "name": "Eldritch Whisper", "tier_min": 1},
        {"id": "pow_shadow_grasp", "name": "Shadow Grasp", "tier_min": 1},
        {"id": "pow_corruption_touch", "name": "Corruption Touch", "tier_min": 2},
        {"id": "pow_void_sight", "name": "Void Sight", "tier_min": 2},
        {"id": "pow_reality_warp", "name": "Reality Warp", "tier_min": 3},
        {"id": "pow_entropy_channel", "name": "Entropy Channel", "tier_min": 3},
    ],
}


def _roll_category(circumstance: str, rng: _random.Random) -> str:
    """Roll a power category from circumstance-weighted distribution."""
    tilts = _CIRCUMSTANCE_TILTS.get(circumstance, {})
    weights = {}
    for cat, base in _BASE_FRACTIONS.items():
        weights[cat] = base * tilts.get(cat, 1.0)

    # Normalize
    total = sum(weights.values())
    cats = list(weights.keys())
    probs = [weights[c] / total for c in cats]
    return rng.choices(cats, weights=probs, k=1)[0]


def _roll_tier(circumstance: str, tags: List[str], rng: _random.Random) -> int:
    """Roll tier from session-zero pyramid with modifiers."""
    probs = dict(_SZ_TIER_PYRAMID)

    # Circumstance modifiers
    if circumstance == "H":
        probs[3] = probs.get(3, 0) + 0.10
        probs[4] = probs.get(4, 0) + 0.05
        probs[1] = probs.get(1, 0) - 0.15
    elif circumstance == "F":
        probs[3] = max(0, probs.get(3, 0) - 0.03)
        probs[4] = max(0, probs.get(4, 0) - 0.02)
        probs[1] = probs.get(1, 0) + 0.05

    # Background modifiers
    if "veteran" in tags or "former badge" in tags:
        probs[3] = probs.get(3, 0) + 0.05
        probs[1] = max(0, probs.get(1, 0) - 0.05)

    # Clamp and normalize
    total = sum(max(0, v) for v in probs.values())
    tiers = list(probs.keys())
    weights = [max(0, probs[t]) / total for t in tiers]
    return rng.choices(tiers, weights=weights, k=1)[0]


def _select_powers(category: str, tier: int, rng: _random.Random) -> List[Dict[str, Any]]:
    """Select 4 power options from a category, return the pool."""
    powers = _STARTER_POWERS.get(category, [])
    eligible = [p for p in powers if p["tier_min"] <= tier]
    if len(eligible) <= 4:
        return eligible
    return rng.sample(eligible, 4)


class ManifestationScene(Scene):
    """Scene 5: Manifestation — circumstance-weighted power category and tier rolls."""
    scene_id = "sz_5"
    register = "intimate"

    def get_framing(self, state: CreationState) -> str:
        return (
            "Something inside you opened, or closed, or turned. The word "
            "for it would come later, and the word would not be right. "
            "What you felt was that you had been carrying something all "
            "your life without knowing it, and now you knew."
        )

    def get_choices(self, state: CreationState) -> List[str]:
        # Choices are generated dynamically based on rolled category
        # For the session zero flow, present power options
        circ = state.scene_choices.get("sz_3", {}).get("onset_circumstance", "A")
        rng = _random.Random(state.seed + 5)  # Deterministic from seed
        category = _roll_category(circ, rng)
        tier = _roll_tier(circ, state.narrative_tags, rng)
        options = _select_powers(category, tier, rng)

        # Store pre-computed values for apply()
        self._category = category
        self._tier = tier
        self._options = options

        return [f"{p['name']} (T{p['tier_min']}+)" for p in options]

    def apply(
        self,
        choice_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        category = getattr(self, "_category", "physical_kinetic")
        tier = getattr(self, "_tier", 1)
        options = getattr(self, "_options", [])

        idx = min(choice_index, max(0, len(options) - 1))
        chosen_power = options[idx] if options else {
            "id": "pow_generic", "name": "Generic Power", "tier_min": 1,
        }

        # Secondary category roll (55% chance)
        secondary_cat = None
        secondary_power = None
        if rng.random() < 0.55:
            # Secondary is second-highest weight after primary
            circ = state.scene_choices.get("sz_3", {}).get("onset_circumstance", "A")
            tilts = _CIRCUMSTANCE_TILTS.get(circ, {})
            weights = {c: _BASE_FRACTIONS[c] * tilts.get(c, 1.0) for c in _BASE_FRACTIONS}
            # Remove primary
            weights.pop(category, None)
            # Boost biological and auratic as natural co-occurrences
            if "biological_vital" in weights:
                weights["biological_vital"] += 0.1
            if "auratic" in weights:
                weights["auratic"] += 0.1
            total = sum(weights.values())
            cats = list(weights.keys())
            probs = [weights[c] / total for c in cats]
            secondary_cat = rng.choices(cats, weights=probs, k=1)[0]

            # Pick secondary power at lower tier
            sec_tier = max(1, tier - 2)
            sec_options = [p for p in _STARTER_POWERS.get(secondary_cat, []) if p["tier_min"] <= sec_tier]
            if sec_options:
                secondary_power = rng.choice(sec_options)

        powers = [{
            "power_id": chosen_power["id"],
            "name": chosen_power["name"],
            "category": category,
            "tier": tier,
            "slot": "anchor",
        }]
        if secondary_power:
            powers.append({
                "power_id": secondary_power["id"],
                "name": secondary_power["name"],
                "category": secondary_cat,
                "tier": max(1, tier - 2),
                "slot": "secondary",
            })

        tier_ceiling = tier + 2

        return factory.apply_scene_result(self.scene_id, {
            "power_category_primary": category,
            "power_category_secondary": secondary_cat,
            "tier": tier,
            "tier_ceiling": tier_ceiling,
            "powers": powers,
            "breakthroughs": [{
                "id": "breakthrough_0",
                "type": "manifestation",
                "description": f"Initial manifestation: {category} T{tier}",
                "cost": "onset trauma",
            }],
            "history": [{
                "timestamp": "T+0",
                "description": f"Manifestation: {category} T{tier} — {chosen_power['name']}",
                "type": "session_zero",
            }],
        }, state, rng)
