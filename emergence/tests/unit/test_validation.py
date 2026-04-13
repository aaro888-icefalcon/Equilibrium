"""Tests for all validation functions in emergence.engine.schemas.validation.

Covers valid inputs, invalid inputs, and edge cases for all 13 validators.
"""

import unittest

from emergence.engine.schemas.character import (
    CharacterSheet, Attributes, Harm, Breakthrough, RelationshipState,
    InventoryItem, Goal, StatusEffect, HistoryEvent,
)
from emergence.engine.schemas.combatant import Combatant
from emergence.engine.schemas.encounter import (
    EncounterSpec, CombatOutcome, Action, TerrainZone, WinLossCondition,
    WorldContext,
)
from emergence.engine.schemas.narrator import (
    NarratorPayload, OutputTarget, ContextContinuity, NarratorConstraints,
)
from emergence.engine.schemas.world import (
    WorldState, Faction, NPC, Location, Clock,
    FactionTerritory, FactionPopulation, FactionPowerProfile,
    FactionEconomicBase, FactionGoal, SessionMetadata,
)
from emergence.engine.schemas.content import (
    Power, EnemyTemplate, PowerCost, PowerEffect,
)
from emergence.engine.schemas.validation import (
    validate_character_sheet, validate_combatant, validate_encounter_spec,
    validate_combat_outcome, validate_action, validate_narrator_payload,
    validate_faction, validate_npc, validate_location, validate_clock,
    validate_world_state, validate_power, validate_enemy_template,
    ValidationResult,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _valid_character() -> CharacterSheet:
    return CharacterSheet(
        name="Kael",
        species="human",
        attributes=Attributes(strength=8, agility=6, perception=6, will=6, insight=6, might=6),
        tier=1,
        tier_ceiling=3,
        corruption=0,
        condition_tracks={"physical": 0, "mental": 0, "social": 0},
    )


def _valid_combatant() -> Combatant:
    return Combatant(
        id="c1",
        name="Bandit",
        species="human",
        attributes=Attributes(),
        condition_tracks={"physical": 0, "mental": 0, "social": 0},
        harm=[],
        powers=[],
        tier=1,
        corruption=0,
        statuses=[],
        side="enemy",
        ai_profile="aggressive",
        exposure_track=0,
        exposure_max=6,
    )


def _valid_encounter_spec() -> EncounterSpec:
    return EncounterSpec(
        id="enc_001",
        combat_register="human",
        enemies=[{"id": "e1", "name": "Bandit"}],
        location="crossroads",
    )


def _valid_combat_outcome() -> CombatOutcome:
    return CombatOutcome(
        encounter_id="enc_001",
        resolution="victory",
        rounds_elapsed=3,
    )


def _valid_action() -> Action:
    return Action(
        actor_id="player",
        verb="Attack",
        declared_at_round=1,
    )


def _valid_narrator_payload() -> NarratorPayload:
    return NarratorPayload(
        scene_type="scene_framing",
        register_directive="standard",
        output_target=OutputTarget(
            desired_length={"min_words": 80, "max_words": 180},
            format="prose",
        ),
    )


def _valid_faction() -> Faction:
    return Faction(
        id="house_valdris",
        display_name="House Valdris",
        type="noble_house",
        standing_with_player_default=0,
        population=FactionPopulation(total=5000, military_capacity=800, powered_fraction=0.05),
    )


def _valid_npc() -> NPC:
    return NPC(
        id="npc_maren",
        display_name="Maren",
        species="human",
        status="alive",
        age=34,
    )


def _valid_location() -> Location:
    return Location(
        id="loc_haven",
        display_name="Haven",
        type="city",
        economic_state="sufficient",
        defensive_capacity=5,
        population=12000,
    )


def _valid_clock() -> Clock:
    return Clock(
        id="clock_war",
        display_name="Drums of War",
        total_segments=8,
        current_segment=2,
    )


def _valid_world_state() -> WorldState:
    return WorldState(
        schema_version="1.0",
        current_time={"in_world_date": "T+1y 0m 0d", "year": 1},
    )


def _valid_power() -> Power:
    return Power(
        id="pow_kinetic_strike",
        name="Kinetic Strike",
        category="physical_kinetic",
        tier=1,
        cost=PowerCost(corruption=0),
        effect=PowerEffect(type="damage", parameters={"base": 4}),
        usage_scope="combat",
    )


def _valid_enemy_template() -> EnemyTemplate:
    return EnemyTemplate(
        id="et_bandit",
        display_name="Bandit",
        register="human",
        ai_profile="aggressive",
        exposure_max=6,
        attribute_defaults={
            "strength": 6, "agility": 6, "perception": 6,
            "will": 6, "insight": 6, "might": 6,
        },
    )


# ── CharacterSheet validation ───────────────────────────────────────────────

class TestValidateCharacterSheet(unittest.TestCase):

    def test_valid(self):
        r = validate_character_sheet(_valid_character())
        self.assertTrue(r.is_valid)
        self.assertEqual(r.errors, [])

    def test_empty_name(self):
        c = _valid_character()
        c.name = ""
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("name" in e for e in r.errors))

    def test_whitespace_name(self):
        c = _valid_character()
        c.name = "   "
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_invalid_species(self):
        c = _valid_character()
        c.species = "elf"
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("species" in e for e in r.errors))

    def test_valid_species_from_setting(self):
        for sp in ("human", "hollow_boned", "deep_voiced", "silver_hand",
                    "pale_eyed", "slow_breath", "broad_shouldered",
                    "sun_worn", "quick_blooded", "wide_sighted",
                    "stone_silent", "corrupted"):
            c = _valid_character()
            c.species = sp
            r = validate_character_sheet(c)
            self.assertTrue(r.is_valid, f"species '{sp}' should be valid")

    def test_invalid_attribute_die_size(self):
        c = _valid_character()
        c.attributes.strength = 7
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("strength" in e for e in r.errors))

    def test_all_valid_die_sizes(self):
        for ds in (4, 6, 8, 10, 12):
            c = _valid_character()
            c.attributes.strength = ds
            r = validate_character_sheet(c)
            self.assertTrue(r.is_valid, f"die size {ds} should be valid")

    def test_tier_below_range(self):
        c = _valid_character()
        c.tier = 0
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_tier_above_range(self):
        c = _valid_character()
        c.tier = 11
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_tier_exceeds_ceiling(self):
        c = _valid_character()
        c.tier = 5
        c.tier_ceiling = 3
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("ceiling" in e for e in r.errors))

    def test_corruption_out_of_range(self):
        c = _valid_character()
        c.corruption = 7
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("corruption" in e for e in r.errors))

    def test_invalid_condition_track_name(self):
        c = _valid_character()
        c.condition_tracks["spiritual"] = 0
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("spiritual" in e for e in r.errors))

    def test_negative_condition_track_value(self):
        c = _valid_character()
        c.condition_tracks["physical"] = -1
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_invalid_status_name(self):
        c = _valid_character()
        c.statuses = [StatusEffect(name="frozen", duration=2, source="test")]
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertTrue(any("frozen" in e for e in r.errors))

    def test_valid_status_names(self):
        for name in ("bleeding", "stunned", "shaken", "burning", "exposed", "marked", "corrupted"):
            c = _valid_character()
            c.statuses = [StatusEffect(name=name, duration=1, source="test")]
            r = validate_character_sheet(c)
            self.assertTrue(r.is_valid, f"status '{name}' should be valid")

    def test_invalid_power_category(self):
        c = _valid_character()
        c.power_category_primary = "fire_magic"
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_valid_power_categories(self):
        for cat in ("physical_kinetic", "perceptual_mental", "matter_energy",
                     "biological_vital", "temporal_spatial", "eldritch_corruptive"):
            c = _valid_character()
            c.power_category_primary = cat
            r = validate_character_sheet(c)
            self.assertTrue(r.is_valid, f"category '{cat}' should be valid")

    def test_harm_invalid_tier(self):
        c = _valid_character()
        c.harm = [Harm(tier=4, description="broken", persistent=True, source="x", date_acquired="T+1")]
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_goal_out_of_range(self):
        c = _valid_character()
        c.goals = [Goal(id="g1", description="survive", progress=11, pressure=0)]
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_goal_pressure_out_of_range(self):
        c = _valid_character()
        c.goals = [Goal(id="g1", description="survive", progress=0, pressure=6)]
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_relationship_standing_out_of_range(self):
        c = _valid_character()
        c.relationships["npc_x"] = RelationshipState(standing=4, trust=0)
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_relationship_trust_out_of_range(self):
        c = _valid_character()
        c.relationships["npc_x"] = RelationshipState(standing=0, trust=6)
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)

    def test_multiple_errors_accumulated(self):
        c = _valid_character()
        c.name = ""
        c.tier = 0
        c.corruption = 7
        r = validate_character_sheet(c)
        self.assertFalse(r.is_valid)
        self.assertGreaterEqual(len(r.errors), 3)


# ── Combatant validation ────────────────────────────────────────────────────

class TestValidateCombatant(unittest.TestCase):

    def test_valid(self):
        r = validate_combatant(_valid_combatant())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        c = _valid_combatant()
        c.id = ""
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_empty_name(self):
        c = _valid_combatant()
        c.name = ""
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_invalid_side(self):
        c = _valid_combatant()
        c.side = "hostile"
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_valid_sides(self):
        for side in ("enemy", "ally", "neutral"):
            c = _valid_combatant()
            c.side = side
            r = validate_combatant(c)
            self.assertTrue(r.is_valid, f"side '{side}' should be valid")

    def test_invalid_ai_profile(self):
        c = _valid_combatant()
        c.ai_profile = "berserker"
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_valid_ai_profiles(self):
        for prof in ("aggressive", "defensive", "tactical", "opportunist", "pack"):
            c = _valid_combatant()
            c.ai_profile = prof
            r = validate_combatant(c)
            self.assertTrue(r.is_valid, f"ai_profile '{prof}' should be valid")

    def test_exposure_negative(self):
        c = _valid_combatant()
        c.exposure_track = -1
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_exposure_exceeds_max(self):
        c = _valid_combatant()
        c.exposure_track = 7
        c.exposure_max = 6
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_exposure_max_zero(self):
        c = _valid_combatant()
        c.exposure_max = 0
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_invalid_attribute(self):
        c = _valid_combatant()
        c.attributes.will = 3
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)

    def test_corruption_out_of_range(self):
        c = _valid_combatant()
        c.corruption = -1
        r = validate_combatant(c)
        self.assertFalse(r.is_valid)


# ── EncounterSpec validation ─────────────────────────────────────────────────

class TestValidateEncounterSpec(unittest.TestCase):

    def test_valid(self):
        r = validate_encounter_spec(_valid_encounter_spec())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        e = _valid_encounter_spec()
        e.id = ""
        r = validate_encounter_spec(e)
        self.assertFalse(r.is_valid)

    def test_invalid_register(self):
        e = _valid_encounter_spec()
        e.combat_register = "divine"
        r = validate_encounter_spec(e)
        self.assertFalse(r.is_valid)

    def test_valid_registers(self):
        for reg in ("human", "creature", "eldritch"):
            e = _valid_encounter_spec()
            e.combat_register = reg
            r = validate_encounter_spec(e)
            self.assertTrue(r.is_valid, f"register '{reg}' should be valid")

    def test_empty_enemies(self):
        e = _valid_encounter_spec()
        e.enemies = []
        r = validate_encounter_spec(e)
        self.assertFalse(r.is_valid)

    def test_empty_location(self):
        e = _valid_encounter_spec()
        e.location = ""
        r = validate_encounter_spec(e)
        self.assertFalse(r.is_valid)


# ── CombatOutcome validation ────────────────────────────────────────────────

class TestValidateCombatOutcome(unittest.TestCase):

    def test_valid(self):
        r = validate_combat_outcome(_valid_combat_outcome())
        self.assertTrue(r.is_valid)

    def test_empty_encounter_id(self):
        o = _valid_combat_outcome()
        o.encounter_id = ""
        r = validate_combat_outcome(o)
        self.assertFalse(r.is_valid)

    def test_invalid_resolution(self):
        o = _valid_combat_outcome()
        o.resolution = "annihilation"
        r = validate_combat_outcome(o)
        self.assertFalse(r.is_valid)

    def test_valid_resolutions(self):
        for res in ("victory", "defeat", "parley", "escape", "truce", "stalemate", "other"):
            o = _valid_combat_outcome()
            o.resolution = res
            r = validate_combat_outcome(o)
            self.assertTrue(r.is_valid, f"resolution '{res}' should be valid")

    def test_negative_rounds(self):
        o = _valid_combat_outcome()
        o.rounds_elapsed = -1
        r = validate_combat_outcome(o)
        self.assertFalse(r.is_valid)


# ── Action validation ────────────────────────────────────────────────────────

class TestValidateAction(unittest.TestCase):

    def test_valid(self):
        r = validate_action(_valid_action())
        self.assertTrue(r.is_valid)

    def test_empty_actor_id(self):
        a = _valid_action()
        a.actor_id = ""
        r = validate_action(a)
        self.assertFalse(r.is_valid)

    def test_invalid_verb(self):
        a = _valid_action()
        a.verb = "Smite"
        r = validate_action(a)
        self.assertFalse(r.is_valid)

    def test_valid_verbs(self):
        for verb in ("Attack", "Power", "Assess", "Maneuver", "Parley",
                      "Disengage", "Finisher", "Defend"):
            a = _valid_action()
            a.verb = verb
            r = validate_action(a)
            self.assertTrue(r.is_valid, f"verb '{verb}' should be valid")

    def test_negative_round(self):
        a = _valid_action()
        a.declared_at_round = -1
        r = validate_action(a)
        self.assertFalse(r.is_valid)


# ── NarratorPayload validation ───────────────────────────────────────────────

class TestValidateNarratorPayload(unittest.TestCase):

    def test_valid(self):
        r = validate_narrator_payload(_valid_narrator_payload())
        self.assertTrue(r.is_valid)

    def test_invalid_scene_type(self):
        p = _valid_narrator_payload()
        p.scene_type = "boss_fight"
        r = validate_narrator_payload(p)
        self.assertFalse(r.is_valid)

    def test_valid_scene_types(self):
        for st in ("combat_turn", "scene_framing", "situation_description",
                    "dialogue", "transition", "character_creation_beat",
                    "time_skip", "death_narration"):
            p = _valid_narrator_payload()
            p.scene_type = st
            r = validate_narrator_payload(p)
            self.assertTrue(r.is_valid, f"scene_type '{st}' should be valid")

    def test_invalid_register_directive(self):
        p = _valid_narrator_payload()
        p.register_directive = "epic"
        r = validate_narrator_payload(p)
        self.assertFalse(r.is_valid)

    def test_invalid_output_format(self):
        p = _valid_narrator_payload()
        p.output_target.format = "poem"
        r = validate_narrator_payload(p)
        self.assertFalse(r.is_valid)

    def test_min_exceeds_max_words(self):
        p = _valid_narrator_payload()
        p.output_target.desired_length = {"min_words": 200, "max_words": 50}
        r = validate_narrator_payload(p)
        self.assertFalse(r.is_valid)

    def test_negative_min_words(self):
        p = _valid_narrator_payload()
        p.output_target.desired_length = {"min_words": -5, "max_words": 100}
        r = validate_narrator_payload(p)
        self.assertFalse(r.is_valid)


# ── Faction validation ───────────────────────────────────────────────────────

class TestValidateFaction(unittest.TestCase):

    def test_valid(self):
        r = validate_faction(_valid_faction())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        f = _valid_faction()
        f.id = ""
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_empty_display_name(self):
        f = _valid_faction()
        f.display_name = ""
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_invalid_type(self):
        f = _valid_faction()
        f.type = "pirate_fleet"
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_valid_types(self):
        for ft in ("noble_house", "warlord_holding", "merchant_guild",
                    "religious_order", "metahuman_polity", "survivor_commune"):
            f = _valid_faction()
            f.type = ft
            r = validate_faction(f)
            self.assertTrue(r.is_valid, f"type '{ft}' should be valid")

    def test_standing_out_of_range(self):
        f = _valid_faction()
        f.standing_with_player_default = -4
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_negative_population(self):
        f = _valid_faction()
        f.population.total = -100
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_negative_military(self):
        f = _valid_faction()
        f.population.military_capacity = -1
        r = validate_faction(f)
        self.assertFalse(r.is_valid)

    def test_powered_fraction_out_of_range(self):
        f = _valid_faction()
        f.population.powered_fraction = 1.5
        r = validate_faction(f)
        self.assertFalse(r.is_valid)


# ── NPC validation ───────────────────────────────────────────────────────────

class TestValidateNpc(unittest.TestCase):

    def test_valid(self):
        r = validate_npc(_valid_npc())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        n = _valid_npc()
        n.id = ""
        r = validate_npc(n)
        self.assertFalse(r.is_valid)

    def test_empty_display_name(self):
        n = _valid_npc()
        n.display_name = ""
        r = validate_npc(n)
        self.assertFalse(r.is_valid)

    def test_invalid_species(self):
        n = _valid_npc()
        n.species = "dwarf"
        r = validate_npc(n)
        self.assertFalse(r.is_valid)

    def test_invalid_status(self):
        n = _valid_npc()
        n.status = "undead"
        r = validate_npc(n)
        self.assertFalse(r.is_valid)

    def test_valid_statuses(self):
        for s in ("alive", "dead", "missing", "transformed", "displaced"):
            n = _valid_npc()
            n.status = s
            r = validate_npc(n)
            self.assertTrue(r.is_valid, f"status '{s}' should be valid")

    def test_negative_age(self):
        n = _valid_npc()
        n.age = -1
        r = validate_npc(n)
        self.assertFalse(r.is_valid)


# ── Location validation ─────────────────────────────────────────────────────

class TestValidateLocation(unittest.TestCase):

    def test_valid(self):
        r = validate_location(_valid_location())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        loc = _valid_location()
        loc.id = ""
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_empty_display_name(self):
        loc = _valid_location()
        loc.display_name = ""
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_invalid_type(self):
        loc = _valid_location()
        loc.type = "dungeon"
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_valid_types(self):
        for lt in ("city", "town", "fortress", "ruin", "wilderness_zone",
                    "faction_holding", "natural_feature", "charged_zone"):
            loc = _valid_location()
            loc.type = lt
            r = validate_location(loc)
            self.assertTrue(r.is_valid, f"type '{lt}' should be valid")

    def test_invalid_economic_state(self):
        loc = _valid_location()
        loc.economic_state = "booming"
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_defensive_capacity_out_of_range(self):
        loc = _valid_location()
        loc.defensive_capacity = 11
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_defensive_capacity_negative(self):
        loc = _valid_location()
        loc.defensive_capacity = -1
        r = validate_location(loc)
        self.assertFalse(r.is_valid)

    def test_negative_population(self):
        loc = _valid_location()
        loc.population = -500
        r = validate_location(loc)
        self.assertFalse(r.is_valid)


# ── Clock validation ────────────────────────────────────────────────────────

class TestValidateClock(unittest.TestCase):

    def test_valid(self):
        r = validate_clock(_valid_clock())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        c = _valid_clock()
        c.id = ""
        r = validate_clock(c)
        self.assertFalse(r.is_valid)

    def test_empty_display_name(self):
        c = _valid_clock()
        c.display_name = ""
        r = validate_clock(c)
        self.assertFalse(r.is_valid)

    def test_zero_total_segments(self):
        c = _valid_clock()
        c.total_segments = 0
        r = validate_clock(c)
        self.assertFalse(r.is_valid)

    def test_negative_current_segment(self):
        c = _valid_clock()
        c.current_segment = -1
        r = validate_clock(c)
        self.assertFalse(r.is_valid)

    def test_segment_exceeds_total(self):
        c = _valid_clock()
        c.current_segment = 9
        c.total_segments = 8
        r = validate_clock(c)
        self.assertFalse(r.is_valid)

    def test_segment_at_total_is_valid(self):
        c = _valid_clock()
        c.current_segment = 8
        c.total_segments = 8
        r = validate_clock(c)
        self.assertTrue(r.is_valid)


# ── WorldState validation ───────────────────────────────────────────────────

class TestValidateWorldState(unittest.TestCase):

    def test_valid(self):
        r = validate_world_state(_valid_world_state())
        self.assertTrue(r.is_valid)

    def test_empty_schema_version(self):
        ws = _valid_world_state()
        ws.schema_version = ""
        r = validate_world_state(ws)
        self.assertFalse(r.is_valid)

    def test_missing_in_world_date(self):
        ws = _valid_world_state()
        ws.current_time = {"year": 1}
        r = validate_world_state(ws)
        self.assertFalse(r.is_valid)

    def test_missing_year(self):
        ws = _valid_world_state()
        ws.current_time = {"in_world_date": "T+1y 0m 0d"}
        r = validate_world_state(ws)
        self.assertFalse(r.is_valid)

    def test_negative_year(self):
        ws = _valid_world_state()
        ws.current_time = {"in_world_date": "T+1y 0m 0d", "year": -1}
        r = validate_world_state(ws)
        self.assertFalse(r.is_valid)


# ── Power validation ────────────────────────────────────────────────────────

class TestValidatePower(unittest.TestCase):

    def test_valid(self):
        r = validate_power(_valid_power())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        p = _valid_power()
        p.id = ""
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_empty_name(self):
        p = _valid_power()
        p.name = ""
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_invalid_category(self):
        p = _valid_power()
        p.category = "necromancy"
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_valid_categories(self):
        for cat in ("physical_kinetic", "perceptual_mental", "matter_energy",
                     "biological_vital", "temporal_spatial", "eldritch_corruptive"):
            p = _valid_power()
            p.category = cat
            r = validate_power(p)
            self.assertTrue(r.is_valid, f"category '{cat}' should be valid")

    def test_tier_below_range(self):
        p = _valid_power()
        p.tier = 0
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_tier_above_range(self):
        p = _valid_power()
        p.tier = 11
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_invalid_effect_type(self):
        p = _valid_power()
        p.effect.type = "heal"
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_valid_effect_types(self):
        for et in ("damage", "status", "utility", "movement", "combined"):
            p = _valid_power()
            p.effect = PowerEffect(type=et)
            r = validate_power(p)
            self.assertTrue(r.is_valid, f"effect type '{et}' should be valid")

    def test_invalid_usage_scope(self):
        p = _valid_power()
        p.usage_scope = "exploration"
        r = validate_power(p)
        self.assertFalse(r.is_valid)

    def test_negative_corruption_cost(self):
        p = _valid_power()
        p.cost.corruption = -1
        r = validate_power(p)
        self.assertFalse(r.is_valid)


# ── EnemyTemplate validation ────────────────────────────────────────────────

class TestValidateEnemyTemplate(unittest.TestCase):

    def test_valid(self):
        r = validate_enemy_template(_valid_enemy_template())
        self.assertTrue(r.is_valid)

    def test_empty_id(self):
        et = _valid_enemy_template()
        et.id = ""
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)

    def test_empty_display_name(self):
        et = _valid_enemy_template()
        et.display_name = ""
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)

    def test_invalid_register(self):
        et = _valid_enemy_template()
        et.register = "divine"
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)

    def test_invalid_ai_profile(self):
        et = _valid_enemy_template()
        et.ai_profile = "berserker"
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)

    def test_exposure_max_zero(self):
        et = _valid_enemy_template()
        et.exposure_max = 0
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)

    def test_invalid_attribute_default(self):
        et = _valid_enemy_template()
        et.attribute_defaults["strength"] = 7
        r = validate_enemy_template(et)
        self.assertFalse(r.is_valid)


# ── ValidationResult unit tests ──────────────────────────────────────────────

class TestValidationResult(unittest.TestCase):

    def test_default_is_valid(self):
        r = ValidationResult()
        self.assertTrue(r.is_valid)
        self.assertEqual(r.errors, [])

    def test_add_error_sets_invalid(self):
        r = ValidationResult()
        r.add_error("something wrong")
        self.assertFalse(r.is_valid)
        self.assertEqual(len(r.errors), 1)
        self.assertEqual(r.errors[0], "something wrong")

    def test_multiple_errors(self):
        r = ValidationResult()
        r.add_error("e1")
        r.add_error("e2")
        r.add_error("e3")
        self.assertFalse(r.is_valid)
        self.assertEqual(len(r.errors), 3)


if __name__ == "__main__":
    unittest.main()
