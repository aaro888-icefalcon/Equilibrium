"""Unit tests for input handler."""

import unittest

from emergence.engine.runtime.input_handler import InputHandler, Intent, META_COMMANDS


class TestInputHandler(unittest.TestCase):

    def setUp(self):
        self.handler = InputHandler()

    def test_save_command(self):
        intent = self.handler.parse_input("/save")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "save")

    def test_quit_command(self):
        intent = self.handler.parse_input("/quit")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "quit")

    def test_exit_alias(self):
        intent = self.handler.parse_input("/exit")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "quit")

    def test_help_command(self):
        intent = self.handler.parse_input("/help")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "help")

    def test_status_command(self):
        intent = self.handler.parse_input("/status")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "status")

    def test_inventory_command(self):
        intent = self.handler.parse_input("/inventory")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "inventory")

    def test_inv_alias(self):
        intent = self.handler.parse_input("/inv")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "inventory")

    def test_map_command(self):
        intent = self.handler.parse_input("/map")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "map")

    def test_character_command(self):
        intent = self.handler.parse_input("/character")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "character")

    def test_char_alias(self):
        intent = self.handler.parse_input("/char")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "character")

    def test_meta_command_with_args(self):
        intent = self.handler.parse_input("/save slot1")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "save")
        self.assertEqual(intent.meta_args, ["slot1"])

    def test_unknown_slash_is_freeform(self):
        intent = self.handler.parse_input("/dance")
        self.assertFalse(intent.is_meta_command)
        self.assertEqual(intent.freeform_text, "/dance")

    def test_case_insensitive_commands(self):
        intent = self.handler.parse_input("/SAVE")
        self.assertTrue(intent.is_meta_command)
        self.assertEqual(intent.meta_command, "save")

    def test_numeric_choice(self):
        intent = self.handler.parse_input("2", num_choices=4)
        self.assertFalse(intent.is_meta_command)
        self.assertEqual(intent.target_choice, 2)

    def test_numeric_choice_out_of_range(self):
        intent = self.handler.parse_input("5", num_choices=4)
        self.assertIsNone(intent.target_choice)
        self.assertEqual(intent.freeform_text, "5")

    def test_letter_choice(self):
        intent = self.handler.parse_input("b", num_choices=4)
        self.assertEqual(intent.target_choice, 2)

    def test_letter_choice_out_of_range(self):
        intent = self.handler.parse_input("z", num_choices=4)
        self.assertIsNone(intent.target_choice)

    def test_freeform_text(self):
        intent = self.handler.parse_input("I want to talk to the merchant")
        self.assertFalse(intent.is_meta_command)
        self.assertIsNone(intent.target_choice)
        self.assertEqual(intent.freeform_text, "I want to talk to the merchant")

    def test_empty_input(self):
        intent = self.handler.parse_input("")
        self.assertEqual(intent.freeform_text, "")

    def test_whitespace_only(self):
        intent = self.handler.parse_input("   ")
        self.assertEqual(intent.freeform_text, "")

    def test_stripped_input(self):
        intent = self.handler.parse_input("  /save  ")
        self.assertTrue(intent.is_meta_command)

    def test_format_choices(self):
        result = self.handler.format_choices(
            ["Attack", "Defend", "Flee"],
            prompt="What do you do?",
        )
        self.assertIn("1. Attack", result)
        self.assertIn("2. Defend", result)
        self.assertIn("3. Flee", result)
        self.assertIn("What do you do?", result)

    def test_intent_repr(self):
        meta = Intent(is_meta_command=True, meta_command="save")
        self.assertIn("save", repr(meta))

        choice = Intent(target_choice=3)
        self.assertIn("3", repr(choice))

        text = Intent(freeform_text="hello")
        self.assertIn("hello", repr(text))

    def test_numeric_without_choices(self):
        intent = self.handler.parse_input("3", num_choices=0)
        self.assertEqual(intent.freeform_text, "3")
        self.assertIsNone(intent.target_choice)


if __name__ == "__main__":
    unittest.main()
