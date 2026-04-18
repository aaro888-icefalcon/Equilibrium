"""Pre-emergence classifier contract — validator for narrator-authored JSON.

After the player provides name/age/profession/personality/NPCs/pre_location
text, the narrator (Claude) reads the text and returns a classifier payload.
This module validates that payload and converts it into CreationState deltas
via `apply_classifier_output`.

The classifier guidelines live in emergence/docs/classifier_guidelines.md.
The validator enforces *structure*, not judgment — attribute/skill/NPC choices
are Claude's call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


CANONICAL_ATTRIBUTES = ("strength", "agility", "perception", "will", "insight", "might")

# 32 canonical skills in 7 clusters. Keep in sync with classifier_guidelines.md.
CANONICAL_SKILLS = frozenset([
    # Combat
    "firearms", "melee", "brawling", "thrown", "tactics",
    # Physical / Survival
    "stealth", "urban_movement", "wilderness", "weather_read",
    "animal_handling", "swimming",
    # Craft / Technical
    "craft", "basic_repair", "scavenging", "agriculture", "cooking",
    # Medical
    "first_aid", "surgery", "pharmacology", "field_medicine",
    # Social
    "negotiation", "intimidation", "command", "instruction", "streetwise",
    # Knowledge
    "literacy", "languages", "history", "regional_geography", "bureaucracy",
    # Other
    "perception_check", "faction_etiquette",
])

VALID_DIE_SIZES = (4, 6, 8, 10)
VALID_RELATIONS = frozenset([
    "parent", "child", "sibling", "partner", "extended_family",
    "friend", "mentor", "student",
    "coworker", "boss", "subordinate", "colleague",
    "rival", "enemy",
    "patient", "client", "contact",
])
VALID_ROLES = ("bond", "contact", "rival", "distant")
VALID_DISTANCES = ("with_player", "near", "regional", "distant", "unknown")


class ClassifierValidationError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Classifier output invalid:\n  - " + "\n  - ".join(errors))


def validate_classifier_output(payload: Dict[str, Any]) -> List[str]:
    """Return a list of error messages. Empty list means valid."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return ["root: must be a dict"]

    # Attributes
    attrs = payload.get("attributes")
    if not isinstance(attrs, dict):
        errors.append("attributes: required dict")
    else:
        for name in CANONICAL_ATTRIBUTES:
            val = attrs.get(name)
            if val is None:
                errors.append(f"attributes.{name}: required")
                continue
            if not isinstance(val, int):
                errors.append(f"attributes.{name}: must be int")
                continue
            if val not in VALID_DIE_SIZES:
                errors.append(
                    f"attributes.{name}: must be one of {VALID_DIE_SIZES} (got {val})"
                )

    # Skills
    skills = payload.get("skills")
    if not isinstance(skills, dict):
        errors.append("skills: required dict")
    else:
        for key, val in skills.items():
            if key == "rationale":
                continue
            if key not in CANONICAL_SKILLS:
                errors.append(f"skills.{key}: not a canonical skill")
                continue
            if not isinstance(val, int):
                errors.append(f"skills.{key}: must be int")
                continue
            if val < 0 or val > 6:
                errors.append(f"skills.{key}: must be 0-6 (got {val})")

    # NPCs
    npcs = payload.get("npcs")
    if not isinstance(npcs, list):
        errors.append("npcs: required list")
    else:
        for i, npc in enumerate(npcs):
            prefix = f"npcs[{i}]"
            if not isinstance(npc, dict):
                errors.append(f"{prefix}: must be dict")
                continue
            if not npc.get("name"):
                errors.append(f"{prefix}.name: required")
            relation = npc.get("relation")
            if relation not in VALID_RELATIONS:
                errors.append(f"{prefix}.relation: must be one of {sorted(VALID_RELATIONS)}")
            role = npc.get("role")
            if role not in VALID_ROLES:
                errors.append(f"{prefix}.role: must be one of {VALID_ROLES}")
            distance = npc.get("distance", "unknown")
            if distance not in VALID_DISTANCES:
                errors.append(f"{prefix}.distance: must be one of {VALID_DISTANCES}")
            bond = npc.get("bond")
            if not isinstance(bond, dict):
                errors.append(f"{prefix}.bond: required dict")
            else:
                for k in ("trust", "loyalty"):
                    v = bond.get(k, 0)
                    if not isinstance(v, int) or v < -3 or v > 3:
                        errors.append(f"{prefix}.bond.{k}: must be int in [-3, 3] (got {v!r})")
                tension = bond.get("tension", 0)
                if not isinstance(tension, int) or tension < 0 or tension > 3:
                    errors.append(f"{prefix}.bond.tension: must be int in [0, 3] (got {tension!r})")

    # Optional: history_seeds, inventory_seeds
    for opt_key in ("history_seeds", "inventory_seeds"):
        if opt_key in payload and not isinstance(payload[opt_key], list):
            errors.append(f"{opt_key}: must be list if present")

    return errors


def to_scene_result(
    payload: Dict[str, Any],
    *,
    name: str,
    age_at_onset: int,
    species: str,
    self_description: str,
    pre_emergence_location: str,
) -> Dict[str, Any]:
    """Convert a validated classifier payload into CharacterFactory scene_result form.

    Caller is responsible for running `validate_classifier_output` first.
    This builds the dict that CharacterFactory.apply_scene_result consumes,
    translating attribute die-sizes into deltas off the d6 baseline.
    """
    attrs = payload.get("attributes", {})
    attribute_deltas = {
        name_: int(attrs.get(name_, 6)) - 6
        for name_ in CANONICAL_ATTRIBUTES
    }

    skills = {k: v for k, v in (payload.get("skills") or {}).items() if k != "rationale"}

    generated_npcs: List[Dict[str, Any]] = []
    npc_seeds: List[Dict[str, Any]] = []
    for npc in payload.get("npcs", []):
        npc_id = _stable_npc_id(npc.get("name", ""), npc.get("relation", ""))
        bond = npc.get("bond", {})
        standing = int(bond.get("loyalty", 0))  # loyalty proxies for standing
        trust = max(0, int(bond.get("trust", 0)))
        generated_npcs.append({
            "npc_id": npc_id,
            "display_name": npc.get("name", ""),
            "scene_id": "pre_emergence",
            "role": npc.get("role", "bond"),
            "standing": standing,
            "trust": trust,
            "relation": npc.get("relation", ""),
            "distance": npc.get("distance", "unknown"),
            "tension": int(bond.get("tension", 0)),
            "hooks": [npc.get("notes", "")] if npc.get("notes") else [],
        })
        npc_seeds.append({
            "name": npc.get("name", ""),
            "relation": npc.get("relation", ""),
            "location": npc.get("distance", "unknown"),
            "descriptor": npc.get("notes", ""),
            "status": "alive",
            "npc_id": npc_id,
        })

    history = [
        {
            "timestamp": ev.get("date", "T+0"),
            "type": ev.get("category", "personal"),
            "description": ev.get("description", ""),
        }
        for ev in payload.get("history_seeds", [])
        if isinstance(ev, dict)
    ]

    inventory = []
    for i, item in enumerate(payload.get("inventory_seeds", [])):
        if not isinstance(item, dict):
            continue
        inventory.append({
            "id": item.get("id") or f"inv_pre_{i}",
            "name": item.get("name", ""),
            "description": item.get("description", ""),
            "quantity": int(item.get("quantity", 1)),
        })

    return {
        "name": name,
        "age_at_onset": age_at_onset,
        "species": species,
        "self_description": self_description,
        "attribute_deltas": attribute_deltas,
        "skills": skills,
        "generated_npcs": generated_npcs,
        "npc_seeds": npc_seeds,
        "history": history,
        "inventory": inventory,
        "region": pre_emergence_location,
    }


def _stable_npc_id(name: str, relation: str) -> str:
    """Derive a deterministic npc_id from (name, relation)."""
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_") or "unnamed"
    rel = (relation or "other").lower().replace(" ", "_")
    return f"npc_pre_{rel}_{base}"
