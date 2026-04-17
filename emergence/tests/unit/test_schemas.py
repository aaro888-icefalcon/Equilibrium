"""Round-trip serialization tests for all Emergence schemas."""
import unittest
import json
import tempfile
import os

from emergence.engine.schemas.character import (
    CharacterSheet, Attributes, Harm, Breakthrough, RelationshipState,
    InventoryItem, Goal, StatusEffect, HistoryEvent,
)
from emergence.engine.schemas.combatant import Combatant
from emergence.engine.schemas.encounter import (
    EncounterSpec, CombatOutcome, Action, TerrainZone, WinLossCondition,
    WorldContext, EnemyState, PlayerStateDelta, NarrativeLogEntry,
    WorldConsequence,
)
from emergence.engine.schemas.narrator import (
    NarratorPayload, OutputTarget, ContextContinuity, NarratorConstraints,
)
from emergence.engine.schemas.world import (
    WorldState, Faction, NPC, Location, Clock, TickEvent, Situation,
    SessionMetadata, ActiveScene, FactionTerritory, FactionPopulation,
    FactionPowerProfile, FactionGoal, FactionRelationship,
    LocationConnection, AmbientConditions, NpcManifest, NpcMemory,
    NpcKnowledge, SituationChoice,
)
from emergence.engine.schemas.content import Power, EnemyTemplate, PowerCost, PowerEffect
from emergence.engine.schemas.serialization import to_json, from_json, save_to_file, load_from_file


class TestCharacterSheetRoundTrip(unittest.TestCase):
    def test_default_character(self):
        c = CharacterSheet(name="Ana", species="human")
        d = c.to_dict()
        c2 = CharacterSheet.from_dict(d)
        self.assertEqual(c.name, c2.name)
        self.assertEqual(c.species, c2.species)
        self.assertEqual(c.id, c2.id)
        self.assertEqual(c.schema_version, c2.schema_version)

    def test_full_character(self):
        c = CharacterSheet(
            name="Teo", species="human", age_at_onset=30, current_age=31,
            attributes=Attributes(strength=8, agility=10, perception=6, will=8, insight=6, might=8),
            condition_tracks={"physical": 2, "mental": 1, "social": 0},
            harm=[Harm(tier=2, description="deep cut", persistent=True, source="combat", date_acquired="T+1y")],
            powers=["kin_push", "hard_skin"],
            power_category_primary="kinetic",
            power_category_secondary="somatic",
            tier=3, tier_ceiling=5,
            breakthroughs=[Breakthrough(date="T+1y", from_tier=2, to_tier=3, cost="scar", trigger="near_death")],
            heat={"iron_crown": 2, "bourse": -1},
            corruption=1,
            relationships={"npc_001": RelationshipState(standing=2, trust=3, current_state="warm")},
            inventory=[InventoryItem(id="knife_1", name="steel knife", description="sharp", quantity=1)],
            location="yonkers_market",
            history=[HistoryEvent(date="T+1y", category="combat", description="fought raiders")],
            statuses=[StatusEffect(name="bleeding", duration=2, source="combat")],
            skills={"melee": 3, "first_aid": 2},
            resources={"cu": 25},
            goals=[Goal(id="g1", description="find partner", progress=3, pressure=4)],
        )
        d = c.to_dict()
        json_str = json.dumps(d, indent=2)
        d2 = json.loads(json_str)
        c2 = CharacterSheet.from_dict(d2)
        self.assertEqual(c.name, c2.name)
        self.assertEqual(c.tier, c2.tier)
        self.assertEqual(len(c.harm), len(c2.harm))
        self.assertEqual(c.harm[0].tier, c2.harm[0].tier)
        self.assertEqual(c.harm[0].description, c2.harm[0].description)
        self.assertEqual(c.powers, c2.powers)
        self.assertEqual(c.corruption, c2.corruption)
        self.assertEqual(c.heat, c2.heat)
        self.assertEqual(c.attributes.strength, c2.attributes.strength)
        self.assertEqual(c.attributes.agility, c2.attributes.agility)
        self.assertEqual(c.goals[0].pressure, c2.goals[0].pressure)
        self.assertEqual(c.relationships["npc_001"].standing, c2.relationships["npc_001"].standing)
        self.assertEqual(c.inventory[0].name, c2.inventory[0].name)

    def test_json_roundtrip_no_info_loss(self):
        c = CharacterSheet(name="Test", tier=4, tier_ceiling=6, corruption=3)
        j = to_json(c)
        d = from_json(j)
        c2 = CharacterSheet.from_dict(d)
        self.assertEqual(c.tier, c2.tier)
        self.assertEqual(c.corruption, c2.corruption)


class TestCombatantRoundTrip(unittest.TestCase):
    def test_combatant(self):
        comb = Combatant(
            id="raider_1", name="Raider", species="human",
            attributes=Attributes(strength=8, agility=6, perception=6, will=6, insight=4, might=8),
            condition_tracks={"physical": 0, "mental": 0, "social": 0},
            harm=[], powers=["kin_push"], tier=2, corruption=0, statuses=[],
            side="enemy", ai_profile="aggressive",
            exposure_track=0, exposure_max=3,
            affinity_table={"kinetic": "neutral", "paradoxic": "vulnerable"},
            abilities=["melee_crude", "rifle_shot"],
            template_id="human_scavenger_raider",
            retreat_conditions=["phy >= 3/5"],
            parley_conditions=["food_offered"],
            motive="survival",
        )
        d = comb.to_dict()
        j = json.dumps(d)
        d2 = json.loads(j)
        comb2 = Combatant.from_dict(d2)
        self.assertEqual(comb.id, comb2.id)
        self.assertEqual(comb.side, comb2.side)
        self.assertEqual(comb.ai_profile, comb2.ai_profile)
        self.assertEqual(comb.exposure_max, comb2.exposure_max)
        self.assertEqual(comb.affinity_table, comb2.affinity_table)

    def test_from_character_sheet(self):
        sheet = CharacterSheet(name="Ana", species="human", tier=3)
        comb = Combatant.from_character_sheet(sheet, side="ally", ai_profile="tactical")
        self.assertEqual(comb.name, "Ana")
        self.assertEqual(comb.side, "ally")
        self.assertEqual(comb.ai_profile, "tactical")
        self.assertEqual(comb.tier, 3)


class TestEncounterSpecRoundTrip(unittest.TestCase):
    def test_encounter_spec(self):
        spec = EncounterSpec(
            generated_at="T+1y 3m",
            location="cross_bronx",
            enemies=[{"id": "r1", "name": "Raider"}],
            terrain_zones=[TerrainZone(id="z1", name="plaza", properties=["exposed"], description="open")],
            stakes="survival",
            win_conditions=[WinLossCondition(type="defeat_all")],
            loss_conditions=[WinLossCondition(type="defeat_specific", parameters={"target": "player"})],
            escape_conditions=[WinLossCondition(type="break_contact")],
            parley_available=True,
            world_context=WorldContext(faction_situation="tense", heat_levels={"iron_crown": 2}),
            combat_register="human",
            opening_situation="Two figures on the road.",
        )
        d = spec.to_dict()
        j = json.dumps(d)
        d2 = json.loads(j)
        spec2 = EncounterSpec.from_dict(d2)
        self.assertEqual(spec.location, spec2.location)
        self.assertEqual(spec.combat_register, spec2.combat_register)
        self.assertEqual(spec.stakes, spec2.stakes)
        self.assertEqual(len(spec.terrain_zones), len(spec2.terrain_zones))
        self.assertEqual(spec.terrain_zones[0].name, spec2.terrain_zones[0].name)

    def test_combat_outcome(self):
        outcome = CombatOutcome(
            encounter_id="enc_1",
            resolution="victory",
            rounds_elapsed=4,
            player_state_delta=PlayerStateDelta(
                condition_changes={"physical": 2},
                corruption_gained=0,
                powers_used={"kin_push": 3},
            ),
            enemy_states=[EnemyState(enemy_id="r1", final_state="dead")],
            narrative_log=[NarrativeLogEntry(turn=1, actor_id="player", action={"verb": "Attack"}, payload={})],
            world_consequences=[WorldConsequence(type="faction_standing_change", parameters={"delta": -1})],
        )
        d = outcome.to_dict()
        j = json.dumps(d)
        d2 = json.loads(j)
        outcome2 = CombatOutcome.from_dict(d2)
        self.assertEqual(outcome.resolution, outcome2.resolution)
        self.assertEqual(outcome.rounds_elapsed, outcome2.rounds_elapsed)
        self.assertEqual(outcome.enemy_states[0].final_state, outcome2.enemy_states[0].final_state)

    def test_action(self):
        a = Action(actor_id="player", verb="Attack", target_id="r1", declared_at_round=2)
        d = a.to_dict()
        a2 = Action.from_dict(d)
        self.assertEqual(a.verb, a2.verb)
        self.assertEqual(a.target_id, a2.target_id)
        self.assertEqual(a.declared_at_round, a2.declared_at_round)


class TestNarratorPayloadRoundTrip(unittest.TestCase):
    def test_payload(self):
        p = NarratorPayload(
            scene_type="combat_turn",
            state_snapshot={"actor": "player", "verb": "Attack"},
            register_directive="action",
            output_target=OutputTarget(desired_length={"min_words": 30, "max_words": 80}, format="prose"),
            constraints=NarratorConstraints(forbidden=["invent damage"]),
            context_continuity=ContextContinuity(
                last_narration_summary="The raider stepped forward.",
                key_callbacks=["rain", "steel knife"],
            ),
        )
        d = p.to_dict()
        j = json.dumps(d)
        d2 = json.loads(j)
        p2 = NarratorPayload.from_dict(d2)
        self.assertEqual(p.scene_type, p2.scene_type)
        self.assertEqual(p.register_directive, p2.register_directive)
        self.assertEqual(p.output_target.format, p2.output_target.format)
        self.assertEqual(p.constraints.forbidden, p2.constraints.forbidden)
        self.assertEqual(p.context_continuity.key_callbacks, p2.context_continuity.key_callbacks)


class TestWorldSchemaRoundTrips(unittest.TestCase):
    def test_world_state(self):
        ws = WorldState(
            current_time={"in_world_date": "T+1y 3m 14d", "onset_date_real": "2025-01-01", "year": 1},
            active_scene=ActiveScene(type="sim_mode", scene_id="s1"),
            session_metadata=SessionMetadata(session_count=5, total_playtime_real_seconds=3600),
            active_player_character="char_001",
            past_characters=["char_000"],
        )
        d = ws.to_dict()
        j = json.dumps(d)
        ws2 = WorldState.from_dict(json.loads(j))
        self.assertEqual(ws.current_time["year"], ws2.current_time["year"])
        self.assertEqual(ws.active_player_character, ws2.active_player_character)
        self.assertEqual(ws.past_characters, ws2.past_characters)

    def test_faction(self):
        f = Faction(
            id="iron_crown", display_name="Iron Crown", type="warlord_holding",
            territory=FactionTerritory(primary_region="northern_nj"),
            population=FactionPopulation(total=50000, military_capacity=5000, powered_fraction=0.15),
            goals=[FactionGoal(id="g1", description="expand territory", weight=0.8)],
            external_relationships={"bourse": FactionRelationship(disposition=-1)},
            standing_with_player_default=-1,
        )
        d = f.to_dict()
        j = json.dumps(d)
        f2 = Faction.from_dict(json.loads(j))
        self.assertEqual(f.id, f2.id)
        self.assertEqual(f.display_name, f2.display_name)
        self.assertEqual(f.type, f2.type)
        self.assertEqual(f.population.total, f2.population.total)

    def test_npc(self):
        n = NPC(
            id="npc_chen", display_name="Chen", role="mechanic",
            faction_affiliation={"primary": "bourse", "secondary": []},
            location="yonkers_market", species="silver_hand", age=35,
            manifestation=NpcManifest(category="material", tier=2),
            personality_traits=["quiet", "precise"],
            knowledge=[NpcKnowledge(topic="repairs", detail="pre-onset vehicles")],
            memory=[NpcMemory(date="T+1y", event="met player", emotional_weight=3)],
            status="alive",
        )
        d = n.to_dict()
        j = json.dumps(d)
        n2 = NPC.from_dict(json.loads(j))
        self.assertEqual(n.id, n2.id)
        self.assertEqual(n.display_name, n2.display_name)
        self.assertEqual(n.species, n2.species)
        self.assertEqual(n.manifestation.tier, n2.manifestation.tier)

    def test_location(self):
        loc = Location(
            id="yonkers_market", display_name="Yonkers Market Quarter",
            type="town", region="hudson_valley",
            controller="yonkers_compact", population=8000,
            defensive_capacity=4, economic_state="sufficient",
            connections=[LocationConnection(to_location_id="peekskill", travel_time="half a day on foot")],
            ambient=AmbientConditions(weather="overcast", season="autumn", threat_level=2),
            description="A functioning market quarter inside the Yonkers perimeter.",
        )
        d = loc.to_dict()
        j = json.dumps(d)
        loc2 = Location.from_dict(json.loads(j))
        self.assertEqual(loc.id, loc2.id)
        self.assertEqual(loc.population, loc2.population)
        self.assertEqual(loc.ambient.threat_level, loc2.ambient.threat_level)
        self.assertEqual(loc.connections[0].to_location_id, loc2.connections[0].to_location_id)

    def test_clock(self):
        c = Clock(
            id="eldritch_pressure", display_name="Eldritch Pressure",
            current_segment=3, total_segments=8,
            narrative_description="The weight of things not meant to be felt.",
        )
        d = c.to_dict()
        c2 = Clock.from_dict(d)
        self.assertEqual(c.current_segment, c2.current_segment)
        self.assertEqual(c.total_segments, c2.total_segments)

    def test_tick_event(self):
        te = TickEvent(
            tick_timestamp="T+1y 3m 14d",
            entity_type="faction", entity_id="iron_crown",
            event_type="patrol_dispatched",
            details={"region": "northern_nj"},
            visibility="regional",
        )
        d = te.to_dict()
        te2 = TickEvent.from_dict(d)
        self.assertEqual(te.entity_type, te2.entity_type)
        self.assertEqual(te.event_type, te2.event_type)

    def test_situation(self):
        s = Situation(
            location="yonkers_market", timestamp="T+1y 3m",
            present_npcs=["npc_chen"], tension="trade dispute",
            player_choices=[SituationChoice(id="c1", description="intervene", type="action")],
            encounter_probability=0.2,
        )
        d = s.to_dict()
        j = json.dumps(d)
        s2 = Situation.from_dict(json.loads(j))
        self.assertEqual(s.tension, s2.tension)
        self.assertEqual(s.encounter_probability, s2.encounter_probability)
        self.assertEqual(len(s.player_choices), len(s2.player_choices))


class TestContentSchemaRoundTrips(unittest.TestCase):
    def test_power(self):
        p = Power(
            id="kin_push", name="Kinetic Push", category="kinetic",
            tier=1, cost=PowerCost(condition={"physical": 1}),
            effect=PowerEffect(type="damage", parameters={"base": 6, "push_zones": 1}),
            damage_type="kinetic",
            description="Force push, displaces target one zone.",
        )
        d = p.to_dict()
        j = json.dumps(d)
        p2 = Power.from_dict(json.loads(j))
        self.assertEqual(p.id, p2.id)
        self.assertEqual(p.name, p2.name)
        self.assertEqual(p.tier, p2.tier)
        self.assertEqual(p.cost.condition, p2.cost.condition)

    def test_enemy_template(self):
        et = EnemyTemplate(
            id="human_scavenger_raider", display_name="Scavenger Raider",
            register="human",
            attribute_defaults={"strength": 8, "agility": 6, "perception": 6, "will": 6, "insight": 4, "might": 8},
            ai_profile="aggressive", exposure_max=3,
            abilities=["melee_crude", "rifle_shot"],
            powers=["kin_push"],
            retreat_conditions=["phy >= 3/5"],
            parley_conditions=["food_offered"],
            description="Hungry and armed.",
            tactics_note="Charges directly.",
        )
        d = et.to_dict()
        j = json.dumps(d)
        et2 = EnemyTemplate.from_dict(json.loads(j))
        self.assertEqual(et.id, et2.id)
        self.assertEqual(et.ai_profile, et2.ai_profile)
        self.assertEqual(et.exposure_max, et2.exposure_max)
        self.assertEqual(et.attribute_defaults["strength"], et2.attribute_defaults["strength"])


class TestSerializationHelpers(unittest.TestCase):
    def test_to_json_from_json(self):
        c = CharacterSheet(name="Test", tier=3)
        j = to_json(c)
        d = from_json(j)
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["tier"], 3)

    def test_save_and_load(self):
        c = CharacterSheet(name="SaveTest", tier=4, corruption=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "char.json")
            save_to_file(c, path)
            d = load_from_file(path)
            c2 = CharacterSheet.from_dict(d)
            self.assertEqual(c.name, c2.name)
            self.assertEqual(c.tier, c2.tier)
            self.assertEqual(c.corruption, c2.corruption)


class TestCompleteWorldStateRoundTrip(unittest.TestCase):
    """Integration: serialize a complete world with all entity types."""

    def test_full_world_state(self):
        ws = WorldState(
            current_time={"in_world_date": "T+1y 3m 14d", "onset_date_real": "2025-01-01", "year": 1},
            active_player_character="char_001",
        )
        faction = Faction(id="iron_crown", display_name="Iron Crown", type="warlord_holding")
        npc = NPC(id="npc_001", display_name="Chen", role="mechanic", status="alive")
        loc = Location(id="yonkers", display_name="Yonkers", type="town", economic_state="sufficient")
        clock = Clock(id="eldritch", display_name="Eldritch Pressure", current_segment=2, total_segments=8)
        char = CharacterSheet(name="Ana", species="human", tier=3, tier_ceiling=5,
                              power_category_primary="kinetic", location="yonkers")

        bundle = {
            "world": ws.to_dict(),
            "factions": [faction.to_dict()],
            "npcs": [npc.to_dict()],
            "locations": [loc.to_dict()],
            "clocks": [clock.to_dict()],
            "player": char.to_dict(),
        }
        j = json.dumps(bundle, indent=2)
        loaded = json.loads(j)

        ws2 = WorldState.from_dict(loaded["world"])
        f2 = Faction.from_dict(loaded["factions"][0])
        n2 = NPC.from_dict(loaded["npcs"][0])
        l2 = Location.from_dict(loaded["locations"][0])
        c2 = Clock.from_dict(loaded["clocks"][0])
        p2 = CharacterSheet.from_dict(loaded["player"])

        self.assertEqual(ws.current_time["year"], ws2.current_time["year"])
        self.assertEqual(faction.id, f2.id)
        self.assertEqual(npc.display_name, n2.display_name)
        self.assertEqual(loc.economic_state, l2.economic_state)
        self.assertEqual(clock.current_segment, c2.current_segment)
        self.assertEqual(char.name, p2.name)
        self.assertEqual(char.location, p2.location)


if __name__ == "__main__":
    unittest.main()
