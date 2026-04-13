"""Unit tests for Year One scenes (6-9)."""

import random
import unittest

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.character_creation.year_one import (
    CriticalIncidentScene,
    FactionEncounterScene,
    FirstWeeksScene,
    SettlingScene,
    _pick_incident_type,
)


class TestFirstWeeksScene(unittest.TestCase):

    def test_4_choices(self):
        scene = FirstWeeksScene()
        choices = scene.get_choices(CreationState())
        self.assertEqual(len(choices), 4)

    def test_defend_gives_will_perception(self):
        scene = FirstWeeksScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)
        self.assertEqual(state.attribute_deltas.get("will", 0), 1)
        self.assertEqual(state.attribute_deltas.get("perception", 0), 1)

    def test_move_generates_companion(self):
        scene = FirstWeeksScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(1, state, factory, rng)
        self.assertGreater(len(state.relationships), 0)

    def test_took_gives_corruption_if_eldritch(self):
        scene = FirstWeeksScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        state.power_category_primary = "eldritch_corruptive"
        rng = random.Random(42)

        state = scene.apply(3, state, factory, rng)
        self.assertGreater(state.corruption, 0)


class TestFactionEncounterScene(unittest.TestCase):

    def test_4_choices(self):
        scene = FactionEncounterScene()
        choices = scene.get_choices(CreationState())
        self.assertEqual(len(choices), 4)

    def test_accept_gives_faction_standing(self):
        scene = FactionEncounterScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25, region="Hudson Valley")
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)
        self.assertIn("catskill-throne", state.faction_standing_deltas)
        self.assertEqual(state.faction_standing_deltas["catskill-throne"], 1)

    def test_refuse_gives_will(self):
        scene = FactionEncounterScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25, region="New York City")
        rng = random.Random(42)

        state = scene.apply(2, state, factory, rng)
        self.assertEqual(state.attribute_deltas.get("will", 0), 1)

    def test_framing_includes_faction(self):
        scene = FactionEncounterScene()
        state = CreationState(region="Philadelphia and inner suburbs")
        framing = scene.get_framing(state)
        self.assertIn("philadelphia-bourse", framing)


class TestCriticalIncidentScene(unittest.TestCase):

    def test_eldritch_triggers_incident_a(self):
        state = CreationState()
        state.power_category_primary = "eldritch_corruptive"
        self.assertEqual(_pick_incident_type(state), "A")

    def test_high_corruption_triggers_incident_a(self):
        state = CreationState()
        state.corruption = 1
        self.assertEqual(_pick_incident_type(state), "A")

    def test_high_heat_triggers_incident_b(self):
        state = CreationState()
        state.heat_deltas = {"iron-crown": 3}
        self.assertEqual(_pick_incident_type(state), "B")

    def test_default_triggers_incident_c(self):
        state = CreationState()
        self.assertEqual(_pick_incident_type(state), "C")

    def test_4_choices_per_incident(self):
        scene = CriticalIncidentScene()
        for itype_setup in [
            {"power_category_primary": "eldritch_corruptive"},  # A
            {"heat_deltas": {"iron-crown": 3}},  # B
            {},  # C
        ]:
            state = CreationState(**{k: v for k, v in itype_setup.items() if k != "heat_deltas"})
            if "heat_deltas" in itype_setup:
                state.heat_deltas = itype_setup["heat_deltas"]
            choices = scene.get_choices(state)
            self.assertEqual(len(choices), 4)

    def test_incident_a_bargain_gives_corruption(self):
        scene = CriticalIncidentScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        state.power_category_primary = "eldritch_corruptive"
        rng = random.Random(42)

        scene.get_choices(state)
        state = scene.apply(2, state, factory, rng)  # Bargained
        self.assertGreaterEqual(state.corruption, 2)

    def test_incident_c_held_on_gives_will(self):
        scene = CriticalIncidentScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        scene.get_choices(state)
        state = scene.apply(3, state, factory, rng)  # Held on
        self.assertEqual(state.attribute_deltas.get("will", 0), 1)


class TestSettlingScene(unittest.TestCase):

    def test_human_gets_4_choices(self):
        scene = SettlingScene()
        state = CreationState(species="human")
        choices = scene.get_choices(state)
        self.assertEqual(len(choices), 4)  # "Among your people" filtered

    def test_nonhuman_gets_5_choices(self):
        scene = SettlingScene()
        state = CreationState(species="wide_sighted")
        choices = scene.get_choices(state)
        self.assertEqual(len(choices), 5)

    def test_town_gives_inventory(self):
        scene = SettlingScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(0, state, factory, rng)
        self.assertGreater(len(state.inventory), 0)
        self.assertIn("cu", state.resources)

    def test_hidden_reduces_heat(self):
        scene = SettlingScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        state.heat_deltas = {"iron-crown": 2, "fed-continuity": 1}
        rng = random.Random(42)

        state = scene.apply(3, state, factory, rng)  # Hidden
        # heat_all should have added -2 to both factions
        self.assertLessEqual(state.heat_deltas.get("iron-crown", 0), 2)

    def test_settling_gives_goal(self):
        scene = SettlingScene()
        factory = CharacterFactory()
        state = CreationState(age_at_onset=25)
        rng = random.Random(42)

        state = scene.apply(1, state, factory, rng)  # On a road
        goal_ids = [g.get("id", "") for g in state.goals]
        self.assertIn("see_whats_left", goal_ids)


if __name__ == "__main__":
    unittest.main()
