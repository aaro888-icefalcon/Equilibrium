"""Unit tests for relationship progression."""

import random
import unittest

from emergence.engine.progression.relationships import RelationshipProgression


class TestRelationshipProgression(unittest.TestCase):

    def _make_char(self):
        return {}

    def test_initial_state(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        self.assertEqual(rp.get_standing("npc1"), 0)
        self.assertEqual(rp.get_trust("npc1"), 0)
        self.assertEqual(rp.get_state("npc1"), "neutral")

    def test_update_standing_positive(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 1, "helped them")
        self.assertEqual(rp.get_standing("npc1"), 1)

    def test_update_standing_capped_at_3(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 5)
        self.assertEqual(rp.get_standing("npc1"), 3)

    def test_update_standing_floor_at_neg3(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", -5)
        self.assertEqual(rp.get_standing("npc1"), -3)

    def test_trust_update(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_trust("npc1", 3)
        self.assertEqual(rp.get_trust("npc1"), 3)

    def test_trust_capped_at_5(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_trust("npc1", 7)
        self.assertEqual(rp.get_trust("npc1"), 5)

    def test_state_cordial(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 1)
        rp.update_trust("npc1", 2)
        self.assertEqual(rp.get_state("npc1"), "cordial")

    def test_state_warm(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 2)
        rp.update_trust("npc1", 3)
        self.assertEqual(rp.get_state("npc1"), "warm")

    def test_state_loyal(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 3)
        rp.update_trust("npc1", 4)
        self.assertEqual(rp.get_state("npc1"), "loyal")

    def test_state_cold(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", -1)
        self.assertEqual(rp.get_state("npc1"), "cold")

    def test_state_antagonist(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", -2)
        self.assertEqual(rp.get_state("npc1"), "antagonist")

    def test_state_blood_feud(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", -3)
        self.assertEqual(rp.get_state("npc1"), "blood_feud")

    def test_betrayal(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 2)
        rp.apply_betrayal("npc1", current_day=100)
        self.assertEqual(rp.get_standing("npc1"), -3)
        self.assertEqual(rp.get_state("npc1"), "betrayed")

    def test_betrayal_locked(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.apply_betrayal("npc1", current_day=100)
        # Try to update standing during lock
        rp.update_standing("npc1", 3, current_day=110)
        self.assertEqual(rp.get_standing("npc1"), -3)  # Still locked

    def test_betrayal_unlocks_after_60_days(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.apply_betrayal("npc1", current_day=100)
        rp.update_standing("npc1", 1, current_day=161)
        self.assertEqual(rp.get_standing("npc1"), -2)

    def test_absence_decay_positive(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 3)
        rng = random.Random(42)
        # Apply many months, standing should eventually decay
        for _ in range(20):
            rp.apply_absence_decay("npc1", months=1, rng=rng)
        self.assertLess(rp.get_standing("npc1"), 3)

    def test_absence_decay_negative_drifts_to_zero(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", -3)
        rng = random.Random(42)
        for _ in range(30):
            rp.apply_absence_decay("npc1", months=1, rng=rng)
        self.assertGreater(rp.get_standing("npc1"), -3)

    def test_npc_death(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 2)
        result = rp.handle_npc_death("npc1", current_day=200)
        self.assertEqual(rp.get_state("npc1"), "dead")
        self.assertEqual(result["mental_damage"], 1)

    def test_npc_death_high_standing(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 3)
        rp.update_trust("npc1", 4)
        result = rp.handle_npc_death("npc1", current_day=200)
        self.assertEqual(result["mental_damage"], 2)

    def test_events_recorded(self):
        char = self._make_char()
        rp = RelationshipProgression(char)
        rp.update_standing("npc1", 1, "traded goods", current_day=50)
        rp.update_standing("npc1", 1, "saved them", current_day=100)
        events = char["relationships"]["npc1"]["events"]
        self.assertEqual(len(events), 2)


if __name__ == "__main__":
    unittest.main()
