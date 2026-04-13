"""Unit tests for emergence.engine.sim.yaml_parser — minimal YAML subset parser."""

import unittest

from emergence.engine.sim.yaml_parser import parse_yaml


class TestBasicMapping(unittest.TestCase):

    def test_simple_key_value(self):
        text = "name: Emergence\nversion: 1"
        result = parse_yaml(text)
        self.assertEqual(result, {"name": "Emergence", "version": 1})

    def test_empty_input(self):
        self.assertEqual(parse_yaml(""), {})

    def test_whitespace_only(self):
        self.assertEqual(parse_yaml("   \n  \n"), {})

    def test_key_no_value(self):
        text = "empty_key:"
        result = parse_yaml(text)
        self.assertEqual(result, {"empty_key": None})


class TestNestedMapping(unittest.TestCase):

    def test_one_level_nesting(self):
        text = "parent:\n  child: value"
        result = parse_yaml(text)
        self.assertEqual(result, {"parent": {"child": "value"}})

    def test_two_level_nesting(self):
        text = "a:\n  b:\n    c: deep"
        result = parse_yaml(text)
        self.assertEqual(result, {"a": {"b": {"c": "deep"}}})

    def test_sibling_keys_at_same_level(self):
        text = "parent:\n  x: 1\n  y: 2\nother: 3"
        result = parse_yaml(text)
        self.assertEqual(result, {"parent": {"x": 1, "y": 2}, "other": 3})


class TestLists(unittest.TestCase):

    def test_simple_list(self):
        text = "items:\n  - alpha\n  - beta\n  - gamma"
        result = parse_yaml(text)
        self.assertEqual(result, {"items": ["alpha", "beta", "gamma"]})

    def test_list_of_numbers(self):
        text = "nums:\n  - 1\n  - 2\n  - 3"
        result = parse_yaml(text)
        self.assertEqual(result, {"nums": [1, 2, 3]})

    def test_list_of_mappings(self):
        text = "people:\n  - name: Alice\n    age: 30\n  - name: Bob\n    age: 25"
        result = parse_yaml(text)
        self.assertEqual(result, {
            "people": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25},
            ]
        })

    def test_top_level_list(self):
        text = "- one\n- two\n- three"
        result = parse_yaml(text)
        self.assertEqual(result, ["one", "two", "three"])


class TestInlineLists(unittest.TestCase):

    def test_inline_list(self):
        text = "tags: [fire, ice, wind]"
        result = parse_yaml(text)
        self.assertEqual(result, {"tags": ["fire", "ice", "wind"]})

    def test_inline_list_with_numbers(self):
        text = "coords: [10, 20, 30]"
        result = parse_yaml(text)
        self.assertEqual(result, {"coords": [10, 20, 30]})


class TestComments(unittest.TestCase):

    def test_inline_comment(self):
        text = "name: test  # this is a comment"
        result = parse_yaml(text)
        self.assertEqual(result, {"name": "test"})

    def test_full_line_comment(self):
        text = "# full line comment\nname: test"
        result = parse_yaml(text)
        self.assertEqual(result, {"name": "test"})

    def test_comment_not_in_quotes(self):
        text = 'motto: "we # are united"'
        result = parse_yaml(text)
        self.assertEqual(result, {"motto": "we # are united"})

    def test_comment_after_quoted_string(self):
        text = "motto: 'hello world'  # a greeting"
        result = parse_yaml(text)
        self.assertEqual(result, {"motto": "hello world"})


class TestScalarTypes(unittest.TestCase):

    def test_integer(self):
        text = "count: 42"
        result = parse_yaml(text)
        self.assertEqual(result["count"], 42)
        self.assertIsInstance(result["count"], int)

    def test_negative_integer(self):
        text = "offset: -5"
        result = parse_yaml(text)
        self.assertEqual(result["offset"], -5)

    def test_float(self):
        text = "ratio: 3.14"
        result = parse_yaml(text)
        self.assertAlmostEqual(result["ratio"], 3.14)
        self.assertIsInstance(result["ratio"], float)

    def test_scientific_notation(self):
        text = "big: 1e6"
        result = parse_yaml(text)
        self.assertAlmostEqual(result["big"], 1e6)

    def test_underscore_separated(self):
        text = "population: 1_900_000"
        result = parse_yaml(text)
        self.assertEqual(result["population"], 1900000)

    def test_boolean_true(self):
        text = "active: true"
        result = parse_yaml(text)
        self.assertIs(result["active"], True)

    def test_boolean_false(self):
        text = "hidden: false"
        result = parse_yaml(text)
        self.assertIs(result["hidden"], False)

    def test_null_keyword(self):
        text = "data: null"
        result = parse_yaml(text)
        self.assertIsNone(result["data"])

    def test_null_tilde(self):
        text = "data: ~"
        result = parse_yaml(text)
        self.assertIsNone(result["data"])

    def test_approximate_value(self):
        text = "population: ~400"
        result = parse_yaml(text)
        self.assertEqual(result["population"], 400)

    def test_approximate_large_value(self):
        text = "people: ~1_900_000"
        result = parse_yaml(text)
        self.assertEqual(result["people"], 1900000)


class TestQuotedStrings(unittest.TestCase):

    def test_double_quoted(self):
        text = 'name: "hello world"'
        result = parse_yaml(text)
        self.assertEqual(result["name"], "hello world")

    def test_single_quoted(self):
        text = "name: 'hello world'"
        result = parse_yaml(text)
        self.assertEqual(result["name"], "hello world")

    def test_quoted_number_stays_string(self):
        text = 'code: "42"'
        result = parse_yaml(text)
        self.assertEqual(result["code"], "42")
        self.assertIsInstance(result["code"], str)

    def test_quoted_with_colon(self):
        text = 'label: "key: value"'
        result = parse_yaml(text)
        self.assertEqual(result["label"], "key: value")


class TestFoldedStrings(unittest.TestCase):

    def test_folded_string(self):
        text = "description: >\n  This is a long\n  description that\n  spans multiple lines."
        result = parse_yaml(text)
        self.assertEqual(
            result["description"],
            "This is a long description that spans multiple lines."
        )

    def test_folded_string_with_sibling(self):
        text = "desc: >\n  Line one\n  Line two\nname: test"
        result = parse_yaml(text)
        self.assertEqual(result["desc"], "Line one Line two")
        self.assertEqual(result["name"], "test")


class TestSettingBibleStyle(unittest.TestCase):
    """Test parsing patterns found in the Emergence setting bible YAML files."""

    def test_faction_entry(self):
        text = """\
faction:
  id: reformed_council
  name: Reformed Council of New York
  type: governmental
  tier: 8
  territory: [Manhattan, Brooklyn]
  population: ~1_900_000
  stance: neutral
  description: >
    The legitimate governing body
    of the New York metropolitan area."""
        result = parse_yaml(text)
        f = result["faction"]
        self.assertEqual(f["id"], "reformed_council")
        self.assertEqual(f["tier"], 8)
        self.assertEqual(f["territory"], ["Manhattan", "Brooklyn"])
        self.assertEqual(f["population"], 1900000)
        self.assertEqual(f["description"],
                         "The legitimate governing body of the New York metropolitan area.")

    def test_npc_entry(self):
        text = """\
npcs:
  - id: director_chen
    name: Director Chen
    faction: reformed_council
    tier: 5
    manifestation: null
    traits: [cautious, diplomatic, shrewd]
  - id: ghost_runner
    name: Ghost Runner
    faction: null
    tier: 3
    manifestation: kinetic
    traits: [reckless, loyal]"""
        result = parse_yaml(text)
        self.assertEqual(len(result["npcs"]), 2)
        self.assertEqual(result["npcs"][0]["id"], "director_chen")
        self.assertIsNone(result["npcs"][0]["manifestation"])
        self.assertEqual(result["npcs"][1]["manifestation"], "kinetic")
        self.assertEqual(result["npcs"][1]["traits"], ["reckless", "loyal"])

    def test_clock_entry(self):
        text = """\
clocks:
  - id: manhattan_water_crisis
    name: Manhattan Water Crisis
    segments: 8
    current: 2
    advance_conditions:
      - faction_conflict_manhattan
      - infrastructure_degradation
    completion_effect: >
      Water shortage becomes critical,
      forcing mass migration."""
        result = parse_yaml(text)
        clock = result["clocks"][0]
        self.assertEqual(clock["id"], "manhattan_water_crisis")
        self.assertEqual(clock["segments"], 8)
        self.assertEqual(clock["current"], 2)
        self.assertEqual(len(clock["advance_conditions"]), 2)
        self.assertIn("Water shortage", clock["completion_effect"])


class TestEdgeCases(unittest.TestCase):

    def test_colon_in_value(self):
        text = "time: 12:30"
        result = parse_yaml(text)
        self.assertEqual(result["time"], "12:30")

    def test_empty_list_item_with_nested_block(self):
        text = "items:\n  -\n    key: val"
        result = parse_yaml(text)
        self.assertEqual(result, {"items": [{"key": "val"}]})

    def test_multiple_blank_lines(self):
        text = "a: 1\n\n\n\nb: 2"
        result = parse_yaml(text)
        self.assertEqual(result, {"a": 1, "b": 2})

    def test_string_that_looks_numeric_but_isnt(self):
        text = "version: v1.2.3"
        result = parse_yaml(text)
        self.assertEqual(result["version"], "v1.2.3")
        self.assertIsInstance(result["version"], str)


if __name__ == "__main__":
    unittest.main()
