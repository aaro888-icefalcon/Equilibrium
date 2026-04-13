"""Synthetic world factory for integration testing.

Creates a minimal but complete world state with:
- 3 factions (council, raiders, enclave)
- 5 NPCs spread across locations
- 5 locations (connected)
- 8 macro clocks
"""

from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Faction,
    FactionEconomicBase,
    FactionGoal,
    FactionRelationship,
    FactionScheme,
    FactionTerritory,
    Location,
    LocationConnection,
    NPC,
    NpcKnowledge,
    NpcManifest,
    NpcMemory,
    NpcRelationshipState,
    WorldState,
)


def make_synthetic_world():
    """Build a complete synthetic test world.

    Returns:
        Tuple of (WorldState, Dict[str, Faction], Dict[str, NPC],
                  Dict[str, Location], Dict[str, Clock])
    """
    world = WorldState(current_time={
        "in_world_date": "T+1y 0m 0d",
        "onset_date_real": "2025-01-01",
        "year": 1,
        "day_count": 0,
    })

    factions = _make_factions()
    npcs = _make_npcs()
    locations = _make_locations()
    clocks = _make_clocks()

    return world, factions, npcs, locations, clocks


def _make_factions():
    council = Faction(
        id="council",
        display_name="Reformed Council",
        type="governmental",
        territory=FactionTerritory(
            primary_region="Manhattan",
            secondary_holdings=["Brooklyn"],
            contested_zones=["Midtown"],
        ),
        resources={"military": 120, "supplies": 200, "influence": 80},
        economic_base=FactionEconomicBase(
            primary_resources=["trade_goods", "salvage"],
        ),
        goals=[
            FactionGoal(id="stability", description="Maintain regional stability", weight=2.0),
            FactionGoal(id="expand", description="Expand territory", weight=1.5),
        ],
        current_schemes=[
            FactionScheme(id="spy_network", description="Build spy network", target="raiders", progress=3),
        ],
        internal_tensions=[{"type": "leadership_dispute", "severity": 2}],
        external_relationships={
            "raiders": FactionRelationship(disposition=-2, active_grievances=["border_raids"]),
            "enclave": FactionRelationship(disposition=1, active_agreements=["trade_pact"]),
        },
    )

    raiders = Faction(
        id="raiders",
        display_name="Cross-Bronx Raiders",
        type="warband",
        territory=FactionTerritory(
            primary_region="Bronx",
            contested_zones=["Midtown"],
        ),
        resources={"military": 80, "supplies": 60, "weapons": 40},
        economic_base=FactionEconomicBase(primary_resources=["scavenged_goods"]),
        goals=[
            FactionGoal(id="plunder", description="Raid for resources", weight=2.5),
        ],
        current_schemes=[
            FactionScheme(id="ambush_plan", description="Set up ambush", target="council", progress=5),
        ],
        external_relationships={
            "council": FactionRelationship(disposition=-2, active_grievances=["arrests"]),
            "enclave": FactionRelationship(disposition=-1),
        },
    )

    enclave = Faction(
        id="enclave",
        display_name="Manifested Enclave",
        type="commune",
        territory=FactionTerritory(primary_region="Queens"),
        resources={"supplies": 100, "powered_individuals": 30},
        economic_base=FactionEconomicBase(primary_resources=["crafted_goods"]),
        goals=[
            FactionGoal(id="sanctuary", description="Build safe haven", weight=2.0),
        ],
        external_relationships={
            "council": FactionRelationship(disposition=1, active_agreements=["trade_pact"]),
            "raiders": FactionRelationship(disposition=-1),
        },
    )

    return {"council": council, "raiders": raiders, "enclave": enclave}


def _make_npcs():
    chen = NPC(
        id="chen",
        display_name="Director Chen",
        faction_affiliation={"primary": "council", "secondary": []},
        location="manhattan_city_hall",
        schedule={"default": "manhattan_city_hall"},
        role="political_leader",
        goals=[{"id": "peace", "description": "Negotiate peace", "progress": 2}],
        personality_traits=["cautious", "diplomatic"],
        knowledge=[NpcKnowledge(topic="water_supply", detail="Reservoir at 40%")],
        memory=[NpcMemory(date="T+0y", event="The Onset", emotional_weight=9, decay_rate=0.01)],
    )

    ghost = NPC(
        id="ghost",
        display_name="Ghost Runner",
        faction_affiliation={"primary": None, "secondary": []},
        location="bronx_market",
        schedule={"patrol": ["bronx_market", "manhattan_docks", "queens_enclave"]},
        role="courier",
        manifestation=NpcManifest(category="kinetic", tier=3),
        goals=[{"id": "survive", "description": "Stay alive", "progress": 5}],
        personality_traits=["reckless", "loyal"],
        current_concerns=["being hunted"],
    )

    warlord = NPC(
        id="warlord",
        display_name="Warlord Kaz",
        faction_affiliation={"primary": "raiders", "secondary": []},
        location="bronx_fortress",
        schedule={"default": "bronx_fortress"},
        role="military_leader",
        goals=[{"id": "conquer", "description": "Take Midtown", "progress": 4}],
        personality_traits=["aggressive", "cunning"],
        relationships={
            "chen": NpcRelationshipState(standing=-2, current_state="hostile"),
        },
    )

    healer = NPC(
        id="healer",
        display_name="Dr. Amara",
        faction_affiliation={"primary": "enclave", "secondary": []},
        location="queens_enclave",
        schedule={"default": "queens_enclave"},
        role="medic",
        manifestation=NpcManifest(category="biological", tier=2),
        goals=[{"id": "help", "description": "Heal the wounded", "progress": 3}],
        personality_traits=["compassionate", "stubborn"],
        knowledge=[
            NpcKnowledge(topic="manifestation", detail="Powers emerge from trauma"),
        ],
    )

    trader = NPC(
        id="trader",
        display_name="Merchant Yuki",
        faction_affiliation={"primary": None, "secondary": []},
        location="manhattan_docks",
        schedule={"patrol": ["manhattan_docks", "bronx_market"]},
        role="merchant",
        goals=[{"id": "profit", "description": "Expand trade network", "progress": 6}],
        personality_traits=["shrewd", "friendly"],
        resources=[{"type": "trade_goods", "amount": 50}],
    )

    return {"chen": chen, "ghost": ghost, "warlord": warlord, "healer": healer, "trader": trader}


def _make_locations():
    city_hall = Location(
        id="manhattan_city_hall",
        display_name="Manhattan City Hall",
        type="urban",
        region="Manhattan",
        controller="council",
        population=2000,
        defensive_capacity=4,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1, season="spring"),
        connections=[
            LocationConnection(to_location_id="manhattan_docks", travel_time="1d"),
            LocationConnection(to_location_id="bronx_market", travel_time="2d", hazards=["raider_patrol"]),
        ],
        dangers=["political_unrest"],
        opportunities=["faction_contact"],
    )

    docks = Location(
        id="manhattan_docks",
        display_name="Manhattan Docks",
        type="urban",
        region="Manhattan",
        controller="council",
        population=800,
        economic_state="strained",
        ambient=AmbientConditions(threat_level=2, season="spring"),
        connections=[
            LocationConnection(to_location_id="manhattan_city_hall", travel_time="1d"),
            LocationConnection(to_location_id="queens_enclave", travel_time="2d"),
        ],
        opportunities=["trade_caravan"],
    )

    bronx_market = Location(
        id="bronx_market",
        display_name="Bronx Open Market",
        type="urban",
        region="Bronx",
        controller="raiders",
        population=500,
        economic_state="strained",
        ambient=AmbientConditions(threat_level=3, season="spring"),
        connections=[
            LocationConnection(to_location_id="manhattan_city_hall", travel_time="2d", hazards=["raider_patrol"]),
            LocationConnection(to_location_id="bronx_fortress", travel_time="1d"),
        ],
        dangers=["raider_activity"],
    )

    fortress = Location(
        id="bronx_fortress",
        display_name="Bronx Fortress",
        type="urban",
        region="Bronx",
        controller="raiders",
        population=300,
        defensive_capacity=6,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=4, season="spring"),
        connections=[
            LocationConnection(to_location_id="bronx_market", travel_time="1d"),
        ],
        dangers=["raider_activity", "mutant_activity"],
    )

    enclave = Location(
        id="queens_enclave",
        display_name="Queens Manifested Enclave",
        type="settlement",
        region="Queens",
        controller="enclave",
        population=600,
        defensive_capacity=3,
        economic_state="sufficient",
        ambient=AmbientConditions(threat_level=1, season="spring"),
        connections=[
            LocationConnection(to_location_id="manhattan_docks", travel_time="2d"),
        ],
        opportunities=["medical_supplies", "safe_passage"],
    )

    return {
        "manhattan_city_hall": city_hall,
        "manhattan_docks": docks,
        "bronx_market": bronx_market,
        "bronx_fortress": fortress,
        "queens_enclave": enclave,
    }


def _make_clocks():
    return {
        "water_crisis": Clock(
            id="water_crisis", display_name="Manhattan Water Crisis",
            current_segment=2, total_segments=8,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.3},
            completion_consequences=[{"type": "crisis", "description": "Water runs out"}],
        ),
        "raider_buildup": Clock(
            id="raider_buildup", display_name="Cross-Bronx Raider Buildup",
            current_segment=3, total_segments=6,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.2},
            completion_consequences=[{"type": "attack", "description": "Major raid"}],
        ),
        "eldritch_tide": Clock(
            id="eldritch_tide", display_name="Eldritch Tide",
            current_segment=1, total_segments=10,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.1},
        ),
        "council_reform": Clock(
            id="council_reform", display_name="Council Reform",
            current_segment=1, total_segments=6,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.15},
        ),
        "enclave_growth": Clock(
            id="enclave_growth", display_name="Enclave Growth",
            current_segment=2, total_segments=8,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.2},
        ),
        "trade_route": Clock(
            id="trade_route", display_name="Trade Route Establishment",
            current_segment=0, total_segments=6,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.25},
        ),
        "disease_outbreak": Clock(
            id="disease_outbreak", display_name="Disease Outbreak",
            current_segment=0, total_segments=8,
            advance_conditions=[{"type": "resource_below", "resource": "medical_supplies", "threshold": 10}],
            advance_rate={"probability": 0.3},
        ),
        "power_awakening": Clock(
            id="power_awakening", display_name="Mass Power Awakening",
            current_segment=0, total_segments=10,
            advance_conditions=[{"type": "always"}],
            advance_rate={"probability": 0.05},
        ),
    }
