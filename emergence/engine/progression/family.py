"""Family engine — partnerships, children, descendants.

Manages family events including child birth, child aging with
manifestation potential, and descendant creation for character continuation.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional


class FamilyEvent:
    """A family-related event."""

    def __init__(self, event_type: str, description: str, data: Dict[str, Any] | None = None) -> None:
        self.event_type = event_type
        self.description = description
        self.data = data or {}


class FamilyEngine:
    """Manages family events and descendant creation."""

    # Fertility by age (approximate annual probability of child)
    FERTILITY_BY_AGE = {
        (16, 25): 0.08,
        (25, 35): 0.06,
        (35, 45): 0.03,
        (45, 55): 0.01,
        (55, 100): 0.0,
    }

    def check_family_events(
        self,
        character: Dict[str, Any],
        world: Dict[str, Any],
        rng: _random.Random | None = None,
    ) -> List[FamilyEvent]:
        """Check for annual family events. Returns list of events."""
        if rng is None:
            rng = _random.Random()

        events = []
        age = character.get("age", 25)
        partner = character.get("partner")

        # Check for child birth if partnered
        if partner:
            fertility = self._get_fertility(age)
            if fertility > 0 and rng.random() < fertility:
                child = self._generate_child(character, partner, rng)
                events.append(FamilyEvent(
                    "child_born",
                    f"A child is born: {child['name']}",
                    {"child": child},
                ))

        # Age existing children
        children = character.get("children", [])
        for child in children:
            child_age = child.get("age", 0) + 1
            child["age"] = child_age

            # Check manifestation at puberty (12-18)
            if 12 <= child_age <= 18 and not child.get("manifested", False):
                if rng.random() < 0.15:  # 15% annual chance during puberty
                    child["manifested"] = True
                    child["tier"] = 1
                    events.append(FamilyEvent(
                        "child_manifests",
                        f"{child['name']} manifests at age {child_age}",
                        {"child_name": child["name"], "child_age": child_age},
                    ))

        return events

    def create_descendant(
        self,
        parent: Dict[str, Any],
        world: Dict[str, Any],
        rng: _random.Random | None = None,
    ) -> Dict[str, Any]:
        """Create a descendant character from a parent.

        Used when the parent dies and the player continues as a child.
        """
        if rng is None:
            rng = _random.Random()

        children = parent.get("children", [])
        # Pick oldest manifested child, or oldest overall
        manifested = [c for c in children if c.get("manifested")]
        if manifested:
            child = max(manifested, key=lambda c: c.get("age", 0))
        elif children:
            child = max(children, key=lambda c: c.get("age", 0))
        else:
            # Generate a new descendant if no children
            child = {
                "name": f"Child of {parent.get('name', 'Unknown')}",
                "age": 16,
                "species": parent.get("species", "human"),
            }

        descendant = {
            "name": child.get("name", "Unknown"),
            "age": max(16, child.get("age", 16)),
            "species": child.get("species", parent.get("species", "human")),
            "tier": child.get("tier", 0),
            "primary_category": child.get("primary_category", parent.get("primary_category")),
            "attributes": self._inherit_attributes(parent, rng),
            "lineage": parent.get("lineage", []) + [parent.get("name", "Unknown")],
            "inherited_resources": self._inherit_resources(parent),
            "inherited_relationships": self._inherit_relationships(parent),
        }

        return descendant

    def _get_fertility(self, age: int) -> float:
        """Get fertility probability for given age."""
        for (lo, hi), prob in self.FERTILITY_BY_AGE.items():
            if lo <= age < hi:
                return prob
        return 0.0

    def _generate_child(
        self,
        parent: Dict[str, Any],
        partner: Dict[str, Any],
        rng: _random.Random,
    ) -> Dict[str, Any]:
        """Generate a child from two parents."""
        names = ["Ada", "Kai", "Rio", "Sage", "Quinn", "Ash", "Wren", "Lark"]
        return {
            "name": rng.choice(names),
            "age": 0,
            "species": parent.get("species", "human"),
            "manifested": False,
            "tier": 0,
        }

    def _inherit_attributes(
        self,
        parent: Dict[str, Any],
        rng: _random.Random,
    ) -> Dict[str, int]:
        """Inherit attributes from parent with variation."""
        parent_attrs = parent.get("attributes", {})
        result = {}
        for attr in ["strength", "agility", "will", "insight", "perception", "might"]:
            base = parent_attrs.get(attr, 6)
            # d6 baseline with some inheritance
            if rng.random() < 0.4:
                result[attr] = base
            else:
                result[attr] = 6  # Default d6
        return result

    def _inherit_resources(self, parent: Dict[str, Any]) -> Dict[str, int]:
        """Inherit half of parent's transferable resources."""
        parent_res = parent.get("resources", {})
        inherited = {}
        for key, val in parent_res.items():
            if isinstance(val, (int, float)) and val > 0:
                inherited[key] = int(val * 0.5)
        return inherited

    def _inherit_relationships(self, parent: Dict[str, Any]) -> List[str]:
        """Inherit parent's significant relationships."""
        rels = parent.get("relationships", {})
        inherited = []
        for npc_id, rel in rels.items():
            standing = rel.get("standing", 0)
            state = rel.get("state", "neutral")
            if abs(standing) >= 2 and state != "dead":
                inherited.append(npc_id)
        return inherited
