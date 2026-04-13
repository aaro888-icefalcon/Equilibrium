"""Unit tests for narrative arc tracker."""

import unittest

from emergence.engine.progression.arcs import ArcTracker, ArcEvent


class TestArcTracker(unittest.TestCase):

    def test_goal_completion(self):
        char = {
            "goals": [
                {"description": "Find the lost city", "progress": 100, "status": "active"},
            ],
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        completed = [e for e in events if e.arc_type == "goal_completed"]
        self.assertEqual(len(completed), 1)
        self.assertIn("lost city", completed[0].description)
        # Goal should now be marked completed
        self.assertEqual(char["goals"][0]["status"], "completed")

    def test_goal_milestone_75(self):
        char = {
            "goals": [
                {"description": "Build clinic", "progress": 80, "status": "active"},
            ],
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        milestones = [e for e in events if e.arc_type == "goal_milestone"]
        self.assertEqual(len(milestones), 1)

    def test_no_double_milestone(self):
        char = {
            "goals": [
                {"description": "Build clinic", "progress": 80, "status": "active", "milestone_75": True},
            ],
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        milestones = [e for e in events if e.arc_type == "goal_milestone"]
        self.assertEqual(len(milestones), 0)

    def test_relationship_climax_loyal(self):
        char = {
            "relationships": {
                "npc1": {"state": "loyal", "prev_state": "warm"},
            },
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        climax = [e for e in events if e.arc_type == "relationship_climax"]
        self.assertEqual(len(climax), 1)
        self.assertIn("bond", climax[0].description)

    def test_relationship_blood_feud(self):
        char = {
            "relationships": {
                "npc1": {"state": "blood_feud", "prev_state": "antagonist"},
            },
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        climax = [e for e in events if e.arc_type == "relationship_climax"]
        self.assertEqual(len(climax), 1)

    def test_npc_death(self):
        char = {
            "relationships": {
                "npc1": {"state": "dead", "prev_state": "loyal"},
            },
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        deaths = [e for e in events if e.arc_type == "relationship_loss"]
        self.assertEqual(len(deaths), 1)

    def test_faction_sworn(self):
        char = {
            "faction_standings": {
                "f1": {"standing": 3, "prev_standing": 2},
            },
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        milestones = [e for e in events if e.arc_type == "faction_milestone"]
        self.assertEqual(len(milestones), 1)
        self.assertIn("allegiance", milestones[0].description)

    def test_faction_enemy(self):
        char = {
            "faction_standings": {
                "f1": {"standing": -3, "prev_standing": -2},
            },
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        milestones = [e for e in events if e.arc_type == "faction_milestone"]
        self.assertEqual(len(milestones), 1)
        self.assertIn("enemy", milestones[0].description)

    def test_corruption_visible(self):
        char = {"corruption": 3, "prev_corruption_segment": 2}
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        c_events = [e for e in events if e.arc_type == "corruption_milestone"]
        self.assertEqual(len(c_events), 1)
        self.assertIn("visible", c_events[0].description)

    def test_corruption_transformation(self):
        char = {"corruption": 6, "prev_corruption_segment": 5}
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        c_events = [e for e in events if e.arc_type == "corruption_transformation"]
        self.assertEqual(len(c_events), 1)

    def test_tier_milestone(self):
        char = {"tier": 4, "prev_tier": 3}
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        t_events = [e for e in events if e.arc_type == "tier_milestone"]
        self.assertEqual(len(t_events), 1)
        self.assertIn("tier 4", t_events[0].description)

    def test_no_events_when_stable(self):
        char = {
            "goals": [],
            "relationships": {},
            "faction_standings": {},
            "corruption": 0,
            "prev_corruption_segment": 0,
            "tier": 2,
            "prev_tier": 2,
        }
        tracker = ArcTracker()
        events = tracker.check_arc_progress(char, {})
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
