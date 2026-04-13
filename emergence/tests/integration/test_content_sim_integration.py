"""Integration: full bible → initial state → tick 30 days → character enters combat."""

import random
import unittest

from emergence.engine.sim.initial_state import build_initial_world
from emergence.engine.sim.tick_engine import TickEngine
from emergence.engine.character_creation.session_zero import (
    FixedInputSource,
    MockNarratorSink,
    SessionZero,
)
from emergence.engine.character_creation.scenes import (
    ConcernScene,
    LocationScene,
    OccupationScene,
    OpeningScene,
    RelationshipScene,
)
from emergence.engine.character_creation.manifestation import ManifestationScene
from emergence.engine.character_creation.year_one import (
    CriticalIncidentScene,
    FactionEncounterScene,
    FirstWeeksScene,
    SettlingScene,
)
from emergence.engine.schemas.character import CharacterSheet
from emergence.engine.combat.data_loader import load_encounters
from emergence.engine.combat.encounter_runner import EncounterRunner
from emergence.engine.combat.verbs import CombatantRecord
from emergence.engine.schemas.encounter import CombatOutcome


def _create_character(seed: int) -> CharacterSheet:
    scenes = [
        OpeningScene(), OccupationScene(), RelationshipScene(),
        LocationScene(), ConcernScene(), ManifestationScene(),
        FirstWeeksScene(), FactionEncounterScene(),
        CriticalIncidentScene(), SettlingScene(),
    ]
    sz = SessionZero(scenes=scenes)
    narrator = MockNarratorSink()
    inp = FixedInputSource(
        texts={"name": "Integration Test Character", "age": "30"},
    )
    return sz.run(inp, narrator, random.Random(seed))


def _snap_to_die(val: int) -> int:
    """Snap an attribute value to the nearest valid die size."""
    valid = [4, 6, 8, 10, 12]
    return min(valid, key=lambda d: abs(d - val))


def _sheet_to_combatant(sheet: CharacterSheet) -> CombatantRecord:
    return CombatantRecord(
        id="player", side="player", tier=sheet.tier,
        strength=_snap_to_die(sheet.attributes.strength),
        agility=_snap_to_die(sheet.attributes.agility),
        perception=_snap_to_die(sheet.attributes.perception),
        will=_snap_to_die(sheet.attributes.will),
        insight=_snap_to_die(sheet.attributes.insight),
        might=_snap_to_die(sheet.attributes.might),
        phy_max=sheet.condition_tracks.get("physical", 5),
        men_max=sheet.condition_tracks.get("mental", 5),
        soc_max=sheet.condition_tracks.get("social", 5),
        exposure_max=4,
    )


class TestContentSimIntegration(unittest.TestCase):

    def test_full_bible_ticks_30_days(self):
        """Load full bible → build initial state → tick 30 days → no errors."""
        world, factions, npcs, locations, clocks = build_initial_world()
        engine = TickEngine()
        rng = random.Random(42)
        player = {"id": "player", "heat": 0, "location": "loc-mount-tremper"}

        events = []
        for _ in range(30):
            day_events = engine.run_daily_tick(
                world, factions, npcs, locations, clocks, player, rng,
            )
            events.extend(day_events)

        self.assertGreater(len(events), 0)

    def test_generated_character_enters_combat(self):
        """Session zero character → combatant → runs in combat engine."""
        sheet = _create_character(42)
        combatant = _sheet_to_combatant(sheet)

        encounters = load_encounters("emergence/data/encounters/sample_encounters.json")
        spec = next(e for e in encounters if e.id == "raider_ambush_cross_bronx")

        runner = EncounterRunner()
        outcome = runner.run(spec, combatant, random.Random(42))

        self.assertIsInstance(outcome, CombatOutcome)
        self.assertGreater(outcome.rounds_elapsed, 0)

    def test_character_attributes_work_in_combat(self):
        """Verify combat uses sheet attributes correctly."""
        sheet = _create_character(99)
        combatant = _sheet_to_combatant(sheet)

        # Combatant should have attributes from character creation
        self.assertEqual(combatant.strength, sheet.attributes.strength)
        self.assertEqual(combatant.tier, sheet.tier)


if __name__ == "__main__":
    unittest.main()
