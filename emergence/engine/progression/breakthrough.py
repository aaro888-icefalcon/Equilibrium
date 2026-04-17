"""Breakthrough mechanics — triggers, resolution, marks, and recovery.

8 breakthrough conditions per progression spec. Each trigger has unique
requirements and DCs. Resolution yields tier +1, a mark, and recovery period.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 24 breakthrough marks (P1-P4, M1-M4, E1-E4, B1-B4, A1-A4, T1-T4, X1-X4, U1-U3)
# ---------------------------------------------------------------------------

BREAKTHROUGH_MARKS = {
    # Physical
    "P1": {"name": "Densification", "effects": {"strength": 1, "agility": -1}},
    "P2": {"name": "Weight gain", "effects": {"physical_max": 1, "agility_difficulty": 1}},
    "P3": {"name": "Hand callus", "effects": {"unarmed_as_weapon": True}},
    "P4": {"name": "Eye scarring", "effects": {"perception": 1, "social_difficulty": 1}},
    # Perceptual/Mental
    "M1": {"name": "Thought-bleed", "effects": {"perception": 1, "will": -1}},
    "M2": {"name": "Sleep loss", "effects": {"perception": 1, "mental_max": -1}},
    "M3": {"name": "False memory", "effects": {"insight": 1, "false_memory": True}},
    "M4": {"name": "Affect flatness", "effects": {"will": 1, "trust_ceiling_penalty": True}},
    # Matter/Energy
    "E1": {"name": "Mineralization", "effects": {"strength": 1, "physical_max": 1, "corruption": 1}},
    "E2": {"name": "Heat tolerance", "effects": {"burning_resist": 1, "cold_sensitivity": True}},
    "E3": {"name": "EM sensitivity", "effects": {"perception": 1, "stun_risk": True}},
    "E4": {"name": "Discoloration", "effects": {"commerce_difficulty": 1}},
    # Biological/Vital
    "B1": {"name": "Plant resonance", "effects": {"agriculture": 2, "biokinetic": -1}},
    "B2": {"name": "Self-drain", "effects": {"bio_self": -1, "bio_heal_others": 2}},
    "B3": {"name": "Sense overload", "effects": {"perception": 1, "mental_max": -1}},
    "B4": {"name": "Body-shift", "effects": {"choice_strength_or_agility": 1}},
    # Auratic
    "A1": {"name": "Field fixation", "effects": {"aura_radius_bonus": 0.5, "will_difficulty_opposite": 1}},
    "A2": {"name": "Lonely zone", "effects": {"trust_ceiling": -1}},
    "A3": {"name": "Aural mark", "effects": {"stealth": -2, "intimidation": 1}},
    "A4": {"name": "Permanent presence", "effects": {"residual_duration_weeks": 1}},
    # Temporal/Spatial
    "T1": {"name": "Time-slip", "effects": {"temporal": -1}},
    "T2": {"name": "Folded inventory", "effects": {"hidden_storage_cubic_ft": 1}},
    "T3": {"name": "Position uncertainty", "effects": {"perception": 1, "navigation_difficulty": 1}},
    "T4": {"name": "Echo", "effects": {"intimidation": 1, "stealth": -1}},
    # Eldritch/Corruptive (all include corruption +1)
    "X1": {"name": "Marked tongue", "effects": {"corruption": 1, "eldritch": -2, "conversation_difficulty": 1}},
    "X2": {"name": "Patron-bond", "effects": {"corruption": 1, "patron_generated": True}},
    "X3": {"name": "Visible transformation", "effects": {"corruption": 1, "cosmetic_change": True}},
    "X4": {"name": "Dream-bleed", "effects": {"corruption": 1, "shared_dreams": True}},
    # Universal
    "U1": {"name": "Lost fear", "effects": {"will": 2, "mental_max": 1, "intimidation": 2, "loyalty_cap": 1}},
    "U2": {"name": "Aging acceleration", "effects": {"effective_age": 5}},
    "U3": {"name": "Limp/scar/chronic", "effects": {"persistent_harm_upgrade": True, "attribute_penalty": -1}},
}

# V2 broad → mark pool mapping.  Perceptual/mental + auratic V1 marks
# both map into the cognitive broad, so that pool carries 8 entries.
MARK_POOLS = {
    "kinetic":   ["P1", "P2", "P3", "P4"],
    "cognitive": ["M1", "M2", "M3", "M4", "A1", "A2", "A3", "A4"],
    "material":  ["E1", "E2", "E3", "E4"],
    "somatic":   ["B1", "B2", "B3", "B4"],
    "spatial":   ["T1", "T2", "T3", "T4"],
    "paradoxic": ["X1", "X2", "X3", "X4"],
}


class BreakthroughTrigger:
    """Represents a breakthrough trigger event."""

    def __init__(
        self,
        condition_id: int,
        condition_name: str,
        source: str = "",
    ) -> None:
        self.condition_id = condition_id
        self.condition_name = condition_name
        self.source = source


class BreakthroughResult:
    """Result of resolving a breakthrough."""

    def __init__(
        self,
        success: bool,
        new_tier: int = 0,
        mark_id: str = "",
        mark_name: str = "",
        bt_type: str = "",
        recovery_days: int = 7,
        corruption_gained: int = 0,
        side_effects: List[str] | None = None,
    ) -> None:
        self.success = success
        self.new_tier = new_tier
        self.mark_id = mark_id
        self.mark_name = mark_name
        self.bt_type = bt_type  # "depth", "breadth", "integration"
        self.recovery_days = recovery_days
        self.corruption_gained = corruption_gained
        self.side_effects = side_effects or []


class BreakthroughEngine:
    """Checks breakthrough triggers and resolves breakthroughs."""

    def check_triggers(
        self,
        character: Dict[str, Any],
        world: Dict[str, Any],
        event: Dict[str, Any],
        combat_outcome: Dict[str, Any] | None = None,
        rng: _random.Random | None = None,
    ) -> Optional[BreakthroughTrigger]:
        """Check if any breakthrough condition is met.

        Returns BreakthroughTrigger if triggered, None otherwise.
        """
        if rng is None:
            rng = _random.Random()

        # Check recovery cooldown
        recovery_remaining = character.get("breakthrough_recovery_days", 0)
        if recovery_remaining > 0:
            return None

        event_type = event.get("type", "")

        # Condition 1: Near-Death
        if event_type == "near_death":
            tier = character.get("tier", 1)
            tier_ceiling = character.get("tier_ceiling", 10)
            if tier < tier_ceiling:
                return BreakthroughTrigger(1, "near_death", "combat near-death")

        # Condition 2: Mentorship (90 days)
        if event_type == "mentorship_complete":
            days = event.get("training_days", 0)
            mentor_tier = event.get("mentor_tier", 0)
            char_tier = character.get("tier", 1)
            mentor_cat = event.get("mentor_category", "")
            char_cat = character.get("primary_category", "")
            if (days >= 90 and mentor_tier >= char_tier + 2
                    and mentor_cat == char_cat):
                return BreakthroughTrigger(2, "mentorship", f"mentor: {event.get('mentor_name', '?')}")

        # Condition 3: Eldritch Exposure (3 days in zone or entity contact)
        if event_type == "eldritch_exposure":
            cumulative_days = event.get("cumulative_days", 0)
            entity_contact = event.get("entity_contact", False)
            if cumulative_days >= 3 or entity_contact:
                return BreakthroughTrigger(3, "eldritch_exposure", "eldritch zone/entity")

        # Condition 4: Substance
        if event_type == "substance_ingestion":
            substance_used = character.get("substances_used", [])
            substance_id = event.get("substance_id", "")
            if substance_id not in substance_used:
                return BreakthroughTrigger(4, "substance", f"substance: {substance_id}")

        # Condition 5: Ritual (3+ manifesters, 1+ higher tier, 1+ day)
        if event_type == "ritual_complete":
            participants = event.get("participant_count", 0)
            highest_tier = event.get("highest_tier", 0)
            duration_days = event.get("duration_days", 0)
            char_tier = character.get("tier", 1)
            if participants >= 3 and highest_tier >= char_tier + 1 and duration_days >= 1:
                return BreakthroughTrigger(5, "ritual", "ritual completion")

        # Condition 6: Traumatic Loss (standing >= 2 NPC dies within 30 days)
        if event_type == "npc_death":
            standing = event.get("standing_with_player", 0)
            if standing >= 2:
                return BreakthroughTrigger(6, "traumatic_loss", f"loss: {event.get('npc_name', '?')}")

        # Condition 7: Sustained Crisis (condition track >= 3 for >= 14 days)
        if event_type == "sustained_crisis":
            track_value = event.get("track_value", 0)
            duration_days = event.get("duration_days", 0)
            if track_value >= 3 and duration_days >= 14:
                return BreakthroughTrigger(7, "sustained_crisis", "sustained crisis")

        # Condition 8: Sacrifice
        if event_type == "sacrifice_complete":
            last_sacrifice_day = character.get("last_sacrifice_day", -9999)
            current_day = world.get("current_time", {}).get("day_count", 0)
            if current_day - last_sacrifice_day >= 5 * 365:
                return BreakthroughTrigger(8, "sacrifice", event.get("sacrifice_type", "sacrifice"))

        return None

    def resolve_breakthrough(
        self,
        character: Dict[str, Any],
        trigger: BreakthroughTrigger,
        rng: _random.Random | None = None,
    ) -> BreakthroughResult:
        """Resolve a breakthrough trigger into a result."""
        if rng is None:
            rng = _random.Random()

        tier = character.get("tier", 1)
        will = character.get("attributes", {}).get("will", 6)
        might = character.get("attributes", {}).get("might", 6)
        insight = character.get("attributes", {}).get("insight", 6)
        primary_cat = character.get("primary_category", "kinetic")

        # Determine if roll succeeds
        success = True
        corruption = 0
        side_effects = []
        bt_type = "depth"

        cond = trigger.condition_id

        if cond == 1:  # Near-death: 1d10 + tier vs DC 12 + current_tier
            roll = rng.randint(1, 10) + tier
            dc = 12 + tier
            success = roll >= dc
            bt_type = "depth"
            # Check if 3+ powers active for integration
            active_powers = len(character.get("powers", []))
            if active_powers >= 3:
                bt_type = "integration"
            if success:
                side_effects.append("persistent harm tier 2")

        elif cond == 2:  # Mentorship: Will check vs DC 7 + (tier - 1)
            roll = rng.randint(1, will)
            dc = 7 + max(0, tier - 1)
            success = roll >= dc
            bt_type = "integration"

        elif cond == 3:  # Eldritch Exposure: automatic
            success = True
            bt_type = "breadth"
            corruption = 1
            if bt_type == "breadth":
                corruption += 1
            side_effects.append("biased to paradoxic")

        elif cond == 4:  # Substance: Will check vs DC 10
            roll = rng.randint(1, will)
            dc = 10
            success = roll >= dc
            if not success:
                corruption = 1
                side_effects.append("harm tier 2")
            else:
                bt_type = rng.choice(["breadth", "integration"])

        elif cond == 5:  # Ritual: Insight check vs DC 9 + (tier - 1)
            roll = rng.randint(1, insight)
            dc = 9 + max(0, tier - 1)
            success = roll >= dc
            bt_type = "integration"
            side_effects.append("relationship debt to participants")

        elif cond == 6:  # Traumatic Loss: Will check vs DC 8 + tier
            roll = rng.randint(1, will)
            dc = 8 + tier
            success = roll >= dc
            bt_type = "depth"
            if not success:
                side_effects.append("mental track +1")

        elif cond == 7:  # Sustained Crisis: Will + Might vs DC 11
            roll = rng.randint(1, will) + rng.randint(1, might)
            dc = 11
            success = roll >= dc
            bt_type = "depth"
            if not success:
                side_effects.append("track elevated; harm tier 2")
            side_effects.append("aging acceleration +1 category")

        elif cond == 8:  # Sacrifice: automatic
            success = True
            bt_type = rng.choice(["depth", "breadth"])

        if not success:
            return BreakthroughResult(
                success=False,
                corruption_gained=corruption,
                side_effects=side_effects,
            )

        # Tier increment
        new_tier = min(tier + 1, 10)

        # Select mark from appropriate pool
        mark_id, mark_name = self._select_mark(character, primary_cat, bt_type, rng)

        # Check for additional corruption from mark
        mark_data = BREAKTHROUGH_MARKS.get(mark_id, {})
        mark_corruption = mark_data.get("effects", {}).get("corruption", 0)
        corruption += mark_corruption

        return BreakthroughResult(
            success=True,
            new_tier=new_tier,
            mark_id=mark_id,
            mark_name=mark_name,
            bt_type=bt_type,
            recovery_days=7,
            corruption_gained=corruption,
            side_effects=side_effects,
        )

    def apply_breakthrough(
        self,
        character: Dict[str, Any],
        result: BreakthroughResult,
    ) -> None:
        """Apply a breakthrough result to a character."""
        if not result.success:
            # Apply failure side effects only
            character["corruption"] = character.get("corruption", 0) + result.corruption_gained
            return

        # Tier up
        character["tier"] = result.new_tier
        character["tier_ceiling"] = max(
            character.get("tier_ceiling", 1), result.new_tier
        )

        # Add mark
        marks = character.get("breakthrough_marks", [])
        marks.append(result.mark_id)
        character["breakthrough_marks"] = marks

        # Recovery period
        character["breakthrough_recovery_days"] = result.recovery_days

        # Corruption
        character["corruption"] = character.get("corruption", 0) + result.corruption_gained

        # Record in history
        history = character.get("breakthrough_history", [])
        history.append({
            "tier_reached": result.new_tier,
            "mark": result.mark_id,
            "type": result.bt_type,
        })
        character["breakthrough_history"] = history

    def _select_mark(
        self,
        character: Dict[str, Any],
        primary_cat: str,
        bt_type: str,
        rng: _random.Random,
    ) -> Tuple[str, str]:
        """Select a breakthrough mark from the appropriate pool."""
        existing_marks = set(character.get("breakthrough_marks", []))

        # Determine pool
        if bt_type == "breadth":
            # New domain — pick from different category
            all_pools = list(MARK_POOLS.items())
            rng.shuffle(all_pools)
            for cat, pool in all_pools:
                if cat != primary_cat:
                    available = [m for m in pool if m not in existing_marks]
                    if available:
                        mark_id = rng.choice(available)
                        return mark_id, BREAKTHROUGH_MARKS[mark_id]["name"]
        elif bt_type == "integration":
            # Integration — universal marks preferred
            universal = ["U1", "U2", "U3"]
            available = [m for m in universal if m not in existing_marks]
            if available:
                mark_id = rng.choice(available)
                return mark_id, BREAKTHROUGH_MARKS[mark_id]["name"]

        # Default: depth — pick from primary category
        pool = MARK_POOLS.get(primary_cat, [])
        available = [m for m in pool if m not in existing_marks]
        if available:
            mark_id = rng.choice(available)
            return mark_id, BREAKTHROUGH_MARKS[mark_id]["name"]

        # Fallback: any available mark
        all_marks = list(BREAKTHROUGH_MARKS.keys())
        available = [m for m in all_marks if m not in existing_marks]
        if available:
            mark_id = rng.choice(available)
            return mark_id, BREAKTHROUGH_MARKS[mark_id]["name"]

        return "U3", "Limp/scar/chronic"
