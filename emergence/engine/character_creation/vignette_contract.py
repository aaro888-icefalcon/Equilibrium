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
