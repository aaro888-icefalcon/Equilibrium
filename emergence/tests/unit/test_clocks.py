"""Unit tests for emergence.engine.sim.clocks — macro clock advancement engine."""

import random
import unittest

from emergence.engine.schemas.world import Clock, TickEvent
from emergence.engine.sim.clocks import ClockEngine, _evaluate_condition


def _make_clock(**overrides) -> Clock:
    """Build a test clock with sensible defaults."""
    defaults = dict(
        id="water_crisis",
        display_name="Water Crisis",
        current_segment=2,
        total_segments=8,
        advance_conditions=[{"type": "always"}],
        advance_rate={"probability": 1.0},
        completion_consequences=[{"type": "event", "description": "Crisis hits"}],
    )
    defaults.update(overrides)
    return Clock(**defaults)


class TestEvaluateCondition(unittest.TestCase):

    def test_always_condition(self):
        self.assertTrue(_evaluate_condition({"type": "always"}, {}))

    def test_flag_present(self):
        world = {"flags": {"drought_active"}}
        self.assertTrue(_evaluate_condition(
            {"type": "flag", "flag": "drought_active"}, world
        ))

    def test_flag_absent(self):
        world = {"flags": set()}
        self.assertFalse(_evaluate_condition(
            {"type": "flag", "flag": "drought_active"}, world
        ))

    def test_resource_below(self):
        world = {"resources": {"water": 10}}
        self.assertTrue(_evaluate_condition(
            {"type": "resource_below", "resource": "water", "threshold": 20}, world
        ))

    def test_resource_above(self):
        world = {"resources": {"water": 50}}
        self.assertFalse(_evaluate_condition(
            {"type": "resource_below", "resource": "water", "threshold": 20}, world
        ))

    def test_clock_at_met(self):
        other = Clock(id="tension", current_segment=5, total_segments=8)
        world = {"clocks": {"tension": other}}
        self.assertTrue(_evaluate_condition(
            {"type": "clock_at", "clock_id": "tension", "segment": 4}, world
        ))

    def test_clock_at_not_met(self):
        other = Clock(id="tension", current_segment=2, total_segments=8)
        world = {"clocks": {"tension": other}}
        self.assertFalse(_evaluate_condition(
            {"type": "clock_at", "clock_id": "tension", "segment": 4}, world
        ))

    def test_unknown_condition_returns_false(self):
        self.assertFalse(_evaluate_condition({"type": "bogus"}, {}))


class TestClockEngineAdvance(unittest.TestCase):

    def test_advance_increments_segment(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=3)
        self.assertTrue(engine.evaluate_advance(clock, {}, random.Random(42)))
        engine.advance(clock, {}, "T+1y 0m 1d")
        self.assertEqual(clock.current_segment, 4)

    def test_no_advance_when_complete(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=8, total_segments=8)
        self.assertFalse(engine.evaluate_advance(clock, {}, random.Random(42)))

    def test_no_advance_when_no_conditions(self):
        engine = ClockEngine()
        clock = _make_clock(advance_conditions=[])
        self.assertFalse(engine.evaluate_advance(clock, {}, random.Random(42)))

    def test_no_advance_when_conditions_unmet(self):
        engine = ClockEngine()
        clock = _make_clock(advance_conditions=[
            {"type": "flag", "flag": "nonexistent"}
        ])
        self.assertFalse(engine.evaluate_advance(clock, {"flags": set()}, random.Random(42)))

    def test_probability_gate(self):
        engine = ClockEngine()
        # Probability 0 should never advance
        clock = _make_clock(advance_rate={"probability": 0.0})
        advanced = False
        for seed in range(100):
            if engine.evaluate_advance(clock, {}, random.Random(seed)):
                advanced = True
                break
        self.assertFalse(advanced)

    def test_advance_returns_tick_event(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=3)
        event = engine.advance(clock, {}, "T+1y 0m 5d")
        self.assertIsInstance(event, TickEvent)
        self.assertEqual(event.entity_type, "clock")
        self.assertEqual(event.entity_id, "water_crisis")
        self.assertEqual(event.event_type, "clock_advance")
        self.assertEqual(event.details["segment"], 4)

    def test_advance_caps_at_total(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=8, total_segments=8)
        engine.advance(clock, {}, "T+1y 0m 1d")
        self.assertEqual(clock.current_segment, 8)


class TestClockCompletion(unittest.TestCase):

    def test_completion_detected(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=8, total_segments=8)
        self.assertTrue(engine.check_completion(clock))

    def test_not_complete(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=5, total_segments=8)
        self.assertFalse(engine.check_completion(clock))

    def test_apply_completion_fires_events(self):
        engine = ClockEngine()
        clock = _make_clock(
            current_segment=8,
            total_segments=8,
            completion_consequences=[
                {"type": "crisis", "description": "Water runs out"},
                {"type": "migration", "description": "Exodus begins"},
            ],
        )
        events = engine.apply_completion(clock, {}, "T+1y 0m 10d")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "clock_completion")
        self.assertEqual(events[1].event_type, "clock_completion")

    def test_apply_completion_when_not_complete(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=3)
        events = engine.apply_completion(clock, {}, "T+1y 0m 10d")
        self.assertEqual(events, [])


class TestClockReset(unittest.TestCase):

    def test_reset_to_zero(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=8, total_segments=8)
        event = engine.reset(clock, "T+1y 0m 20d")
        self.assertEqual(clock.current_segment, 0)
        self.assertEqual(event.event_type, "clock_reset")
        self.assertEqual(event.details["from_segment"], 8)

    def test_reset_to_custom_value(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=6)
        engine.reset(clock, "T+1y 0m 20d", reset_to=3)
        self.assertEqual(clock.current_segment, 3)

    def test_check_reset_with_condition_met(self):
        engine = ClockEngine()
        clock = _make_clock(
            reset_conditions=[{"type": "flag", "flag": "crisis_resolved"}]
        )
        world = {"flags": {"crisis_resolved"}}
        self.assertTrue(engine.check_reset(clock, world))

    def test_check_reset_no_conditions(self):
        engine = ClockEngine()
        clock = _make_clock(reset_conditions=[])
        self.assertFalse(engine.check_reset(clock, {}))


class TestClockInteractions(unittest.TestCase):

    def test_interaction_triggered(self):
        engine = ClockEngine()
        clock = _make_clock(
            current_segment=4,
            interactions=[{
                "target_clock_id": "tension",
                "trigger_at_segment": 4,
                "effect_type": "accelerate",
                "probability": 1.0,
            }],
        )
        other = Clock(id="tension", current_segment=2, total_segments=8)
        all_clocks = {"water_crisis": clock, "tension": other}
        triggered = engine.check_interactions(clock, all_clocks, {})
        self.assertEqual(len(triggered), 1)
        self.assertEqual(triggered[0]["target_clock_id"], "tension")

    def test_interaction_not_triggered_below_segment(self):
        engine = ClockEngine()
        clock = _make_clock(
            current_segment=2,
            interactions=[{
                "target_clock_id": "tension",
                "trigger_at_segment": 4,
                "effect_type": "accelerate",
            }],
        )
        other = Clock(id="tension", current_segment=2, total_segments=8)
        all_clocks = {"water_crisis": clock, "tension": other}
        triggered = engine.check_interactions(clock, all_clocks, {})
        self.assertEqual(len(triggered), 0)


class TestTickClocks(unittest.TestCase):

    def test_full_tick_advances_clock(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=3)
        clocks = {"water_crisis": clock}
        events = engine.tick_clocks(clocks, {}, random.Random(42), "T+1y 0m 1d")
        self.assertEqual(clock.current_segment, 4)
        advance_events = [e for e in events if e.event_type == "clock_advance"]
        self.assertEqual(len(advance_events), 1)

    def test_full_tick_triggers_completion(self):
        engine = ClockEngine()
        clock = _make_clock(current_segment=7, total_segments=8)
        clocks = {"water_crisis": clock}
        events = engine.tick_clocks(clocks, {}, random.Random(42), "T+1y 0m 1d")
        self.assertEqual(clock.current_segment, 8)
        completion_events = [e for e in events if e.event_type == "clock_completion"]
        self.assertEqual(len(completion_events), 1)

    def test_full_tick_resets_complete_clock(self):
        engine = ClockEngine()
        clock = _make_clock(
            current_segment=8,
            total_segments=8,
            reset_conditions=[{"type": "always"}],
        )
        clocks = {"water_crisis": clock}
        events = engine.tick_clocks(clocks, {}, random.Random(42), "T+1y 0m 1d")
        self.assertEqual(clock.current_segment, 0)
        reset_events = [e for e in events if e.event_type == "clock_reset"]
        self.assertEqual(len(reset_events), 1)

    def test_cross_clock_acceleration(self):
        engine = ClockEngine()
        clock_a = _make_clock(
            id="clock_a",
            current_segment=4,
            total_segments=8,
            advance_conditions=[],  # won't advance on its own
            interactions=[{
                "target_clock_id": "clock_b",
                "trigger_at_segment": 4,
                "effect_type": "accelerate",
                "probability": 1.0,
            }],
        )
        clock_b = _make_clock(
            id="clock_b",
            current_segment=2,
            total_segments=8,
            advance_conditions=[],  # won't advance on its own
        )
        clocks = {"clock_a": clock_a, "clock_b": clock_b}
        events = engine.tick_clocks(clocks, {}, random.Random(42), "T+1y 0m 1d")
        # clock_b should have been accelerated by clock_a's interaction
        self.assertEqual(clock_b.current_segment, 3)

    def test_multiple_clocks_independent(self):
        engine = ClockEngine()
        c1 = _make_clock(id="c1", current_segment=2)
        c2 = _make_clock(id="c2", current_segment=5)
        clocks = {"c1": c1, "c2": c2}
        engine.tick_clocks(clocks, {}, random.Random(42), "T+1y 0m 1d")
        self.assertEqual(c1.current_segment, 3)
        self.assertEqual(c2.current_segment, 6)


if __name__ == "__main__":
    unittest.main()
