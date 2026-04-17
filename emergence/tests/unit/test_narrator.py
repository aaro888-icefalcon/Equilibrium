"""Unit tests for narrator queue, payloads, prompts, and validation."""

import json
import os
import tempfile
import unittest

from emergence.engine.narrator.queue import (
    FileNarrationQueue,
    MockNarrationQueue,
)
from emergence.engine.narrator.payloads import (
    build_combat_turn_payload,
    build_character_creation_payload,
    build_death_payload,
    build_dialogue_payload,
    build_preamble_payload,
    build_scene_framing_payload,
    build_situation_payload,
    build_time_skip_payload,
    build_transition_payload,
)
from emergence.engine.narrator.prompts import (
    PROMPT_TEMPLATES,
    format_prompt,
    get_prompt,
)
from emergence.engine.narrator.validation import validate_narration


class TestMockNarrationQueue(unittest.TestCase):

    def test_returns_immediately(self):
        queue = MockNarrationQueue()
        result = queue.emit({"scene_type": "combat_turn"})
        self.assertIn("combat_turn", result)

    def test_records_history(self):
        queue = MockNarrationQueue()
        queue.emit({"scene_type": "scene_framing"})
        queue.emit({"scene_type": "dialogue"})
        self.assertEqual(len(queue.history), 2)


class TestFileNarrationQueue(unittest.TestCase):

    def test_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = FileNarrationQueue(tmpdir)
            queue.emit({"scene_type": "test", "data": "hello"})

            queue_path = os.path.join(tmpdir, "narration_queue.jsonl")
            self.assertTrue(os.path.exists(queue_path))

            with open(queue_path) as f:
                line = json.loads(f.readline())
                self.assertEqual(line["scene_type"], "test")
                self.assertEqual(line["_seq"], 1)

    def test_increments_seq(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue = FileNarrationQueue(tmpdir)
            queue.emit({"scene_type": "a"})
            queue.emit({"scene_type": "b"})
            self.assertEqual(queue.seq, 2)

    def test_persists_seq(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            queue1 = FileNarrationQueue(tmpdir)
            queue1.emit({"scene_type": "x"})
            queue1.emit({"scene_type": "y"})

            # New queue instance should resume from persisted seq
            queue2 = FileNarrationQueue(tmpdir)
            self.assertEqual(queue2.seq, 2)


class TestPayloadBuilders(unittest.TestCase):

    def test_combat_turn_payload(self):
        p = build_combat_turn_payload(
            round_num=3, actor_name="Player", action_type="Attack",
            action_result="hit", damage_dealt=5,
        )
        self.assertEqual(p["scene_type"], "combat_turn")
        self.assertEqual(p["round"], 3)

    def test_scene_framing_payload(self):
        p = build_scene_framing_payload(
            scene_id="scene_1", location_name="Mount Tremper",
            time_of_day="dawn", npcs_present=["Preston"],
            recent_events=["raid last night"],
        )
        self.assertEqual(p["scene_type"], "scene_framing")
        self.assertIn("Preston", p["npcs_present"])

    def test_situation_payload(self):
        p = build_situation_payload(
            situation_id="sit_1", description="A stranger approaches",
            choices=[{"id": "a", "text": "Talk"}], tension_level="tense",
            location_name="Market",
        )
        self.assertEqual(p["scene_type"], "situation_description")

    def test_dialogue_payload(self):
        p = build_dialogue_payload(
            npc_name="Kostas", npc_voice="Formal and measured",
            topic="reactor parts", standing=1,
            player_options=["Agree", "Refuse"],
        )
        self.assertEqual(p["scene_type"], "dialogue")

    def test_character_creation_payload(self):
        p = build_character_creation_payload(
            scene_id="sz_0", framing_text="Tell me your name.",
            choices=["Enter name"],
        )
        self.assertEqual(p["scene_type"], "character_creation_beat")

    def test_transition_payload(self):
        p = build_transition_payload(
            from_location="Mount Tremper", to_location="Peekskill",
            travel_time="2 days", hazards=["bandits"],
        )
        self.assertEqual(p["scene_type"], "transition")

    def test_death_payload(self):
        p = build_death_payload(
            character_name="Elena", cause="age", location="Home",
            age=72, legacy=["Founded a clinic"],
        )
        self.assertEqual(p["scene_type"], "death_narration")

    def test_time_skip_payload(self):
        p = build_time_skip_payload(
            duration="3 months", events_summary=["Trade route opened"],
            world_changes=["Bourse expanded"],
        )
        self.assertEqual(p["scene_type"], "time_skip")

    def test_preamble_payload(self):
        player = {
            "name": "Marisol Reyes", "age": 30, "species": "human",
            "tier": 2, "powers": [{"id": "kinetic_push"}],
            "skills": {"first_aid": 3}, "relationships": [],
            "goals": ["Find my brother"],
        }
        p = build_preamble_payload(
            player=player,
            location_name="Yonkers",
            location_details={"type": "settlement"},
            npcs_present=["Obi"],
            faction_standings={"yonkers_compact": 1},
            recent_events=["Wretch sighting"],
        )
        self.assertEqual(p["scene_type"], "scene_framing")
        self.assertTrue(p["preamble"])
        self.assertEqual(p["character_identity"]["name"], "Marisol Reyes")
        self.assertIn("output_target", p)
        self.assertIn("constraints", p)
        self.assertIn("format_instructions", p)
        # v3 preamble targets longer narration.
        self.assertEqual(p["output_target"]["min_words"], 250)
        # v3 preamble exposes biography_roster / top_vows / top_threats /
        # opening_scenario_code (empty by default when not supplied).
        self.assertIn("biography_roster", p)
        self.assertIn("top_vows", p)
        self.assertIn("top_threats", p)
        self.assertIn("opening_scenario_code", p)

    def test_all_payloads_have_output_target(self):
        """Every payload builder should include output_target and constraints."""
        payloads = [
            build_combat_turn_payload(1, "A", "Attack", "hit"),
            build_scene_framing_payload("s1", "Loc", "dawn", [], []),
            build_situation_payload("sit1", "desc", [], "calm", "Loc"),
            build_dialogue_payload("NPC", "voice", "topic", 0, []),
            build_character_creation_payload("sz0", "text", []),
            build_transition_payload("A", "B", "1 day", []),
            build_death_payload("X", "age", "Home", 70, []),
            build_time_skip_payload("1 month", [], []),
        ]
        for p in payloads:
            self.assertIn("output_target", p, f"Missing output_target in {p['scene_type']}")
            self.assertIn("constraints", p, f"Missing constraints in {p['scene_type']}")


class TestPrompts(unittest.TestCase):

    def test_all_scene_types_have_templates(self):
        expected = [
            "combat_turn", "scene_framing", "situation_description",
            "dialogue", "character_creation_beat", "transition",
            "death_narration", "time_skip",
        ]
        for st in expected:
            template = get_prompt(st)
            self.assertGreater(len(template), 50, f"Template for {st} too short")

    def test_format_prompt_populates(self):
        template = get_prompt("combat_turn")
        payload = build_combat_turn_payload(
            round_num=1, actor_name="Player", action_type="Attack",
            action_result="hit", damage_dealt=3,
        )
        result = format_prompt(template, payload)
        self.assertIn("Player", result)
        self.assertIn("Attack", result)
        self.assertNotIn("{actor}", result)

    def test_format_handles_missing_keys(self):
        template = "Hello {name}, your score is {score}."
        result = format_prompt(template, {"name": "Test"})
        self.assertIn("Test", result)


class TestValidation(unittest.TestCase):

    def test_valid_narration_passes(self):
        text = "The blade sang as it arced. " * 5  # ~30 words
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertEqual(len(violations), 0)

    def test_too_short_flagged(self):
        text = "A hit."
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(any("short" in v.lower() for v in violations))

    def test_too_long_flagged(self):
        text = "word " * 250
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(any("long" in v.lower() for v in violations))

    def test_forbidden_term_flagged(self):
        text = "You rolled a d20 and got a saving throw. " * 3
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(any("d20" in v for v in violations))

    def test_payload_forbidden_checked(self):
        text = "You levitate with telekinesis, your powers awakening. " * 3
        violations = validate_narration(text, {
            "scene_type": "scene_framing",
            "forbidden": ["telekinesis"],
        })
        self.assertTrue(any("telekinesis" in v for v in violations))


if __name__ == "__main__":
    unittest.main()
