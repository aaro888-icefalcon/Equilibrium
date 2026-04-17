"""Narrator output contract for Year One vignettes.

The narrator (Claude Code operator) produces a JSON object matching
VignetteOutput in response to a VignetteScaffold.  The engine:
  1. parses the JSON via VignetteOutput.from_json,
  2. runs validate_vignette_output against the scaffold,
  3. applies the picked VignetteChoice via CharacterFactory.apply_scene_result.

No pydantic dependency; manual validation.  Every required field here is
enforced by the validator in 2.2.
"""

from __future__ import annotations

import dataclasses
import json
from typing import Any, Dict, List, Optional, Union


# ----------------------------------------------------------------------
# Seed-bundle leaves
# ----------------------------------------------------------------------

@dataclasses.dataclass
class NpcSeed:
    """One NPC to bind from a vignette pick."""
    name: str
    archetype: str
    standing: int = 0
    hooks: List[str] = dataclasses.field(default_factory=list)
    relation: str = ""       # "ally", "rival", "mentor", etc.
    voice: str = ""          # one-line persona note


@dataclasses.dataclass
class LocationSeed:
    """One location to mint or reference."""
    id: Optional[str] = None
    spec: Optional[Dict[str, Any]] = None
    is_starting: bool = False


@dataclasses.dataclass
class FactionDelta:
    """One faction standing / heat change."""
    faction_id: str
    standing_delta: int = 0
    heat_delta: int = 0
    note: str = ""


@dataclasses.dataclass
class ThreatSeed:
    """One threat to add to state.threats."""
    archetype: str
    name: str
    standing: int = -2
    pressure: Optional[int] = None       # if None, archetype default is used
    source: str = ""
    summary: str = ""


@dataclasses.dataclass
class VowSeed:
    """One vow commitment — resolves to one or more concrete goals."""
    vow_id: str                          # key into VOW_PACKAGES
    target_npc: str = ""                 # name of the NPC the vow attaches to
    goals: List[Dict[str, Any]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class SeedBundle:
    """All seeds that attach to one VignetteChoice."""
    npcs: List[NpcSeed] = dataclasses.field(default_factory=list)
    locations: List[LocationSeed] = dataclasses.field(default_factory=list)
    factions: List[FactionDelta] = dataclasses.field(default_factory=list)
    threats: List[ThreatSeed] = dataclasses.field(default_factory=list)
    vows: List[VowSeed] = dataclasses.field(default_factory=list)
    region_outcome: Optional[str] = None    # V2 only; required there
    history_record: str = ""                # one-liner into state.history


# ----------------------------------------------------------------------
# Choice and output
# ----------------------------------------------------------------------

@dataclasses.dataclass
class MechanicalBinding:
    """Which cast_mode or rider slot this choice binds, and which option."""
    slot: str           # "primary_cast" | "primary_rider" | "secondary_cast" | "secondary_rider"
    option_id: str      # must be in scaffold.option_pool


@dataclasses.dataclass
class VignetteChoice:
    """One of three diegetic choices in a vignette."""
    display_text: str
    mechanical_binding: MechanicalBinding
    mechanical_parenthetical: str       # non-empty, distinct from option default
    seed_bundle: SeedBundle


@dataclasses.dataclass
class VignetteOutput:
    """The narrator's structured response to a VignetteScaffold."""
    schema_version: str = "1.0"
    prose: str = ""
    choices: List[VignetteChoice] = dataclasses.field(default_factory=list)

    # ------------------------------------------------------------------
    # JSON ingress
    # ------------------------------------------------------------------

    @classmethod
    def from_json(cls, raw: Union[str, Dict[str, Any]]) -> "VignetteOutput":
        """Parse *raw* (JSON string or dict) into a VignetteOutput.

        Raises ValueError on malformed input.  Does NOT validate against
        a scaffold — that's validate_vignette_output's job.
        """
        if isinstance(raw, str):
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as e:
                raise ValueError(f"invalid JSON: {e}") from e
        elif isinstance(raw, dict):
            obj = raw
        else:
            raise ValueError(f"expected str or dict, got {type(raw).__name__}")

        if not isinstance(obj, dict):
            raise ValueError("top-level must be a JSON object")

        try:
            choices_raw = obj.get("choices", [])
            if not isinstance(choices_raw, list):
                raise ValueError("choices must be a list")
            choices = [_parse_choice(c) for c in choices_raw]
            return cls(
                schema_version=str(obj.get("schema_version", "1.0")),
                prose=str(obj.get("prose", "")),
                choices=choices,
            )
        except (KeyError, TypeError) as e:
            raise ValueError(f"malformed VignetteOutput: {e}") from e


def _parse_choice(raw: Dict[str, Any]) -> VignetteChoice:
    if not isinstance(raw, dict):
        raise ValueError(f"choice must be a dict, got {type(raw).__name__}")
    mb_raw = raw.get("mechanical_binding", {})
    if not isinstance(mb_raw, dict):
        raise ValueError("mechanical_binding must be a dict")
    mb = MechanicalBinding(
        slot=str(mb_raw.get("slot", "")),
        option_id=str(mb_raw.get("option_id", "")),
    )
    bundle = _parse_bundle(raw.get("seed_bundle", {}))
    return VignetteChoice(
        display_text=str(raw.get("display_text", "")),
        mechanical_binding=mb,
        mechanical_parenthetical=str(raw.get("mechanical_parenthetical", "")),
        seed_bundle=bundle,
    )


def _parse_bundle(raw: Dict[str, Any]) -> SeedBundle:
    if not isinstance(raw, dict):
        raise ValueError("seed_bundle must be a dict")
    return SeedBundle(
        npcs=[NpcSeed(**_safe_dict(n, NpcSeed)) for n in raw.get("npcs", [])],
        locations=[LocationSeed(**_safe_dict(l, LocationSeed)) for l in raw.get("locations", [])],
        factions=[FactionDelta(**_safe_dict(f, FactionDelta)) for f in raw.get("factions", [])],
        threats=[ThreatSeed(**_safe_dict(t, ThreatSeed)) for t in raw.get("threats", [])],
        vows=[VowSeed(**_safe_dict(v, VowSeed)) for v in raw.get("vows", [])],
        region_outcome=raw.get("region_outcome"),
        history_record=str(raw.get("history_record", "")),
    )


def _safe_dict(d: Any, cls: type) -> Dict[str, Any]:
    """Filter *d* down to fields *cls* accepts; tolerate unknown keys."""
    if not isinstance(d, dict):
        raise ValueError(f"expected dict for {cls.__name__}, got {type(d).__name__}")
    allowed = {f.name for f in dataclasses.fields(cls)}
    return {k: v for k, v in d.items() if k in allowed}


# ----------------------------------------------------------------------
# Validator
# ----------------------------------------------------------------------

_VALID_REGION_OUTCOMES = {"stay_nyc", "displaced_to", "traveled_to"}


def validate_vignette_output(
    output: VignetteOutput,
    scaffold: Any,                 # VignetteScaffold (avoid circular import)
    state: Any = None,             # CreationState (unused today; reserved)
) -> List[str]:
    """Return a list of violation strings.  Empty list = valid."""
    violations: List[str] = []

    # 1. Three choices exactly.
    if len(output.choices) != 3:
        violations.append(f"expected 3 choices, got {len(output.choices)}")

    pool_ids = set(scaffold.option_ids()) if scaffold.option_pool else set()
    base_by_id = {o.option_id: o.base_description for o in scaffold.option_pool}

    for i, choice in enumerate(output.choices):
        prefix = f"choice[{i}]"

        # 2. Mechanical binding: slot + option_id pool.
        if choice.mechanical_binding.slot != scaffold.mechanical_slot:
            violations.append(
                f"{prefix}.slot={choice.mechanical_binding.slot!r} "
                f"!= scaffold.mechanical_slot={scaffold.mechanical_slot!r}"
            )
        if pool_ids and choice.mechanical_binding.option_id not in pool_ids:
            violations.append(
                f"{prefix}.option_id={choice.mechanical_binding.option_id!r} "
                f"not in scaffold.option_pool={sorted(pool_ids)}"
            )

        # 3. Parenthetical: non-empty AND distinct from option base description.
        paren = (choice.mechanical_parenthetical or "").strip()
        if not paren:
            violations.append(f"{prefix}.mechanical_parenthetical is empty")
        else:
            base = (base_by_id.get(choice.mechanical_binding.option_id, "") or "").strip()
            if paren and paren == base:
                violations.append(
                    f"{prefix}.mechanical_parenthetical is identical to "
                    f"option base description; be specific to this character"
                )

        # 4. Seed bundle minimums (per-choice).
        req = scaffold.required_seeds
        b = choice.seed_bundle
        if len(b.npcs) < req.min_npcs:
            violations.append(f"{prefix}.seed_bundle.npcs "
                              f"{len(b.npcs)}<{req.min_npcs}")
        if len(b.locations) < req.min_locations:
            violations.append(f"{prefix}.seed_bundle.locations "
                              f"{len(b.locations)}<{req.min_locations}")
        if len(b.factions) < req.min_factions:
            violations.append(f"{prefix}.seed_bundle.factions "
                              f"{len(b.factions)}<{req.min_factions}")
        if len(b.threats) < req.min_threats:
            violations.append(f"{prefix}.seed_bundle.threats "
                              f"{len(b.threats)}<{req.min_threats}")
        if len(b.vows) < req.min_vows:
            violations.append(f"{prefix}.seed_bundle.vows "
                              f"{len(b.vows)}<{req.min_vows}")

        # 5. Archetype id resolution for threats.
        from emergence.engine.character_creation.threats import list_archetype_ids
        known_archetypes = set(list_archetype_ids())
        for t in b.threats:
            if t.archetype and t.archetype not in known_archetypes:
                violations.append(
                    f"{prefix}.seed_bundle.threats archetype "
                    f"{t.archetype!r} is not a known archetype"
                )

        # 6. Faction id resolution.
        from emergence.engine.character_creation.scenarios import REGION_FACTIONS
        known_factions = {rep["id"] for rep in REGION_FACTIONS.values()}
        for f in b.factions:
            if f.faction_id and f.faction_id not in known_factions:
                violations.append(
                    f"{prefix}.seed_bundle.factions faction_id "
                    f"{f.faction_id!r} is not a known faction"
                )

        # 7. V2: region_outcome value must be in the valid set.
        if req.require_region_outcome:
            if not b.region_outcome:
                violations.append(f"{prefix}.seed_bundle.region_outcome is required for V2")
            elif b.region_outcome not in _VALID_REGION_OUTCOMES:
                violations.append(
                    f"{prefix}.seed_bundle.region_outcome "
                    f"{b.region_outcome!r} not in {sorted(_VALID_REGION_OUTCOMES)}"
                )

    # 8. V2: aggregate region_outcome set must equal
    #    {stay_nyc, displaced_to, traveled_to} OR {stay_nyc, displaced_to, displaced_to}.
    if scaffold.required_seeds.require_region_outcome and len(output.choices) == 3:
        seen = [c.seed_bundle.region_outcome for c in output.choices]
        seen_set = sorted(seen)
        valid_a = sorted(["stay_nyc", "displaced_to", "traveled_to"])
        valid_b = sorted(["stay_nyc", "displaced_to", "displaced_to"])
        if seen_set != valid_a and seen_set != valid_b:
            violations.append(
                f"V2 region_outcome set {seen} must be "
                f"[stay_nyc, displaced_to, traveled_to] or "
                f"[stay_nyc, displaced_to, displaced_to]"
            )

    # 9. V4: exactly one choice's locations has is_starting=True
    #    AND total vow entries resolve to >= min_goals_from_vows goals.
    if scaffold.required_seeds.require_is_starting:
        starting_count = sum(
            1 for c in output.choices
            for loc in c.seed_bundle.locations
            if loc.is_starting
        )
        if starting_count != 1:
            violations.append(
                f"V4: exactly one choice must have is_starting=True "
                f"in its seed_bundle.locations; got {starting_count}"
            )

    if scaffold.required_seeds.min_goals_from_vows > 0:
        # Sum goals across all choices' vows; narrator offers 3 choices,
        # only one is picked — but the SCAFFOLD's min applies per-choice
        # (the picked choice must deliver ≥N goals).  Enforce per choice.
        min_g = scaffold.required_seeds.min_goals_from_vows
        for i, c in enumerate(output.choices):
            total_goals = sum(len(v.goals) for v in c.seed_bundle.vows)
            if total_goals < min_g:
                violations.append(
                    f"choice[{i}].seed_bundle.vows goals {total_goals}<{min_g}"
                )

    return violations
