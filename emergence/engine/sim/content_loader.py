"""Content loader — loads setting bible YAML into schema objects.

Bridges the informal YAML data (factions, NPCs, locations, clocks,
constants) to the structured schema objects defined in engine/schemas/.

Handles informal values:
- ~N → int(N)
- "very high" → 9 on 0-10 scale
- "T9 Physical/kinetic" → NpcManifest(category, tier)
- "neutral-transactional" → standing int 0
- Population with underscores → int
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.sim.yaml_parser import parse_yaml
from emergence.engine.schemas.world import (
    AmbientConditions,
    Clock,
    Faction,
    FactionEconomicBase,
    FactionGoal,
    FactionRelationship,
    FactionScheme,
    FactionTerritory,
    Location,
    LocationConnection,
    NPC,
    NpcKnowledge,
    NpcManifest,
    NpcMemory,
    NpcRelationshipState,
)


# ---------------------------------------------------------------------------
# Value conversion helpers
# ---------------------------------------------------------------------------

_STANDING_MAP = {
    "hostile": -3,
    "antagonistic": -2,
    "cold": -1,
    "distrustful": -1,
    "distant-cautious": -1,
    "neutral": 0,
    "neutral-transactional": 0,
    "transactional": 0,
    "wary-neutral": 0,
    "cautious": 0,
    "warm": 1,
    "friendly": 1,
    "supportive": 2,
    "allied": 3,
}

_CAPACITY_MAP = {
    "very high": 9,
    "high": 7,
    "moderate": 5,
    "low": 3,
    "very low": 1,
    "minimal": 1,
    "none": 0,
}

_TIER_RE = re.compile(r"T(\d+)")


def parse_standing(val: Any) -> int:
    """Convert a standing value to int -3..+3."""
    if isinstance(val, int):
        return max(-3, min(3, val))
    if isinstance(val, str):
        lower = val.lower().strip()
        if lower in _STANDING_MAP:
            return _STANDING_MAP[lower]
        # Try parsing as int
        try:
            return max(-3, min(3, int(lower)))
        except ValueError:
            pass
    return 0


def parse_population(val: Any) -> int:
    """Parse population values: ~400, 1_900_000, '~400 (retinue + staff)'."""
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        # Strip leading ~ and trailing description
        clean = val.strip()
        if clean.startswith("~"):
            clean = clean[1:]
        # Take only the numeric prefix
        match = re.match(r"[\d_,]+", clean)
        if match:
            num_str = match.group().replace("_", "").replace(",", "")
            try:
                return int(num_str)
            except ValueError:
                pass
    return 0


def parse_defensive_capacity(val: Any) -> int:
    """Parse defensive capacity: 'very high — ...' → 9, int → int."""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        lower = val.lower().strip()
        for keyword, score in _CAPACITY_MAP.items():
            if lower.startswith(keyword):
                return score
        # Try parsing as int
        try:
            return int(val.strip())
        except ValueError:
            pass
    return 5  # default moderate


def parse_manifestation(val: Any) -> NpcManifest:
    """Parse manifestation strings like 'T9 Physical/kinetic narrow specialist'."""
    if val is None or val == "null" or val == "none":
        return NpcManifest()
    if isinstance(val, dict):
        return NpcManifest.from_dict(val)
    if not isinstance(val, str):
        return NpcManifest()

    text = val.strip()
    # Extract highest tier
    tiers = _TIER_RE.findall(text)
    tier = max(int(t) for t in tiers) if tiers else 1

    # Extract category
    categories = [
        "physical", "kinetic", "perceptual", "mental",
        "matter", "energy", "biological", "vital",
        "auratic", "temporal", "spatial", "eldritch",
    ]
    found_cat = ""
    lower = text.lower()
    for cat in categories:
        if cat in lower:
            found_cat = cat
            break

    return NpcManifest(
        category=found_cat,
        tier=tier,
        specific_abilities=[text],  # Preserve full text
    )


# ---------------------------------------------------------------------------
# ContentLoader
# ---------------------------------------------------------------------------

class ContentLoader:
    """Loads setting bible YAML files into schema objects."""

    def __init__(self, base_path: str = "emergence/setting") -> None:
        self.base_path = base_path

    def _read_yaml(self, filename: str) -> Any:
        path = os.path.join(self.base_path, filename)
        with open(path, "r", encoding="utf-8") as f:
            return parse_yaml(f.read())

    # ── Factions ──────────────────────────────────────────────────────

    def load_factions(self) -> Dict[str, Faction]:
        data = self._read_yaml("factions.yaml")
        raw_list = data.get("factions", [])
        result: Dict[str, Faction] = {}
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            fid = raw.get("id", "")
            faction = Faction(
                id=fid,
                display_name=raw.get("display_name", ""),
                type=raw.get("type", ""),
                current_leader={"id": raw.get("current_leader", "")},
                territory=FactionTerritory(
                    primary_region=raw.get("territory", "") if isinstance(raw.get("territory"), str) else "",
                ),
                population=FactionPopulation_from_raw(raw.get("population", 0)),
                economic_base=FactionEconomicBase(
                    primary_resources=_as_list(raw.get("economic_base", [])),
                ),
                goals=[
                    FactionGoal(id=f"goal_{i}", description=g, weight=1.0)
                    for i, g in enumerate(_as_list(raw.get("goals", [])))
                ],
                current_schemes=[
                    FactionScheme(id=f"scheme_{i}", description=s, target="")
                    for i, s in enumerate(_as_list(raw.get("current_schemes", [])))
                ],
                internal_tensions=[
                    {"description": t} if isinstance(t, str) else t
                    for t in _as_list(raw.get("internal_tensions", []))
                ],
                standing_with_player_default=parse_standing(
                    raw.get("standing_with_player_default", 0)
                ),
                known_information=_as_list(raw.get("known_information", [])),
                secret_information=_as_list(raw.get("secret_information", [])),
                narrative_voice=raw.get("narrative_voice", ""),
            )
            # Parse power_profile as a list of strings in known_information
            pp = _as_list(raw.get("power_profile", []))
            if pp:
                faction.known_information.extend([f"[power] {p}" for p in pp])

            result[fid] = faction
        return result

    # ── NPCs ──────────────────────────────────────────────────────────

    def load_npcs(self) -> Dict[str, NPC]:
        data = self._read_yaml("npcs.yaml")
        raw_list = data.get("npcs", [])
        result: Dict[str, NPC] = {}
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            nid = raw.get("id", "")
            npc = NPC(
                id=nid,
                display_name=raw.get("display_name", ""),
                faction_affiliation={
                    "primary": _extract_primary_faction(raw.get("faction_affiliation", None)),
                    "secondary": [],
                },
                location=raw.get("location", ""),
                species=raw.get("species", "human"),
                age=raw.get("age_at_game_start", 30) if isinstance(raw.get("age_at_game_start"), int) else 30,
                manifestation=parse_manifestation(raw.get("manifestation")),
                role=raw.get("role", ""),
                goals=[
                    {"id": f"goal_{i}", "description": g, "progress": 0}
                    for i, g in enumerate(_as_list(raw.get("goals", [])))
                ],
                personality_traits=[],
                knowledge=[
                    NpcKnowledge(topic=f"topic_{i}", detail=k)
                    for i, k in enumerate(_as_list(raw.get("what_they_know", [])))
                ],
                standing_with_player_default=parse_standing(
                    raw.get("standing_with_player_default", 0)
                ),
                what_they_want_from_player="; ".join(
                    str(x) for x in _as_list(raw.get("what_they_want_from_the_player", []))
                ),
                voice=raw.get("voice", ""),
                hooks=_as_list(raw.get("hooks", [])),
            )
            # Parse relationship strings into NpcRelationshipState
            for rel_str in _as_list(raw.get("relationships", [])):
                if isinstance(rel_str, str):
                    # Extract NPC IDs from text
                    npc_refs = re.findall(r"npc-[\w-]+", rel_str)
                    for ref in npc_refs:
                        npc.relationships[ref] = NpcRelationshipState(
                            current_state=rel_str,
                        )
            # Parse resources
            npc.resources = [
                {"description": r} if isinstance(r, str) else r
                for r in _as_list(raw.get("resources", []))
            ]
            result[nid] = npc
        return result

    # ── Locations ─────────────────────────────────────────────────────

    def load_locations(self) -> Dict[str, Location]:
        data = self._read_yaml("locations.yaml")
        raw_list = data.get("locations", [])
        result: Dict[str, Location] = {}
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            lid = raw.get("id", "")
            coords = raw.get("coordinates", [])
            coord_dict = {}
            if isinstance(coords, list) and len(coords) >= 2:
                coord_dict = {"lat": coords[0], "lon": coords[1]}

            loc = Location(
                id=lid,
                display_name=raw.get("display_name", ""),
                type=raw.get("type", ""),
                region=raw.get("region", ""),
                coordinates=coord_dict,
                controller=raw.get("controller", None),
                population=parse_population(raw.get("population", 0)),
                defensive_capacity=parse_defensive_capacity(
                    raw.get("defensive_capacity", 5)
                ),
                economic_state=raw.get("economic_state", "sufficient") if isinstance(raw.get("economic_state"), str) else "sufficient",
                notable_features=_as_list(raw.get("notable_features", [])),
                current_events=_as_list(raw.get("current_events", [])),
                dangers=_as_list(raw.get("dangers", [])),
                opportunities=_as_list(raw.get("opportunities", [])),
                description=raw.get("description", ""),
            )
            # Parse connections
            for conn_str in _as_list(raw.get("connections", [])):
                if isinstance(conn_str, str):
                    loc.connections.append(LocationConnection(
                        to_location_id=conn_str,
                    ))
                elif isinstance(conn_str, dict):
                    loc.connections.append(LocationConnection(
                        to_location_id=conn_str.get("to_location_id", conn_str.get("to", "")),
                        travel_mode=conn_str.get("travel_mode", "foot"),
                        travel_time=conn_str.get("travel_time", ""),
                        hazards=conn_str.get("hazards", []),
                    ))
            # Parse resources
            loc.resources = [
                {"description": r} if isinstance(r, str) else r
                for r in _as_list(raw.get("resources", []))
            ]
            result[lid] = loc
        return result

    # ── Clocks ────────────────────────────────────────────────────────

    def load_clocks(self) -> Dict[str, Clock]:
        data = self._read_yaml("clocks.yaml")
        raw_list = data.get("clocks", [])
        result: Dict[str, Clock] = {}
        for raw in raw_list:
            if not isinstance(raw, dict):
                continue
            cid = raw.get("id", "")
            clock = Clock(
                id=cid,
                display_name=raw.get("display_name", ""),
                current_segment=raw.get("current_segment", 0) if isinstance(raw.get("current_segment"), int) else 0,
                total_segments=raw.get("total_segments", 8) if isinstance(raw.get("total_segments"), int) else 8,
                advance_conditions=[
                    {"type": "always", "description": c} if isinstance(c, str) else c
                    for c in _as_list(raw.get("advance_conditions", []))
                ],
                advance_rate=_parse_advance_rate(raw.get("advance_rate", "")),
                completion_consequences=[
                    {"description": c} if isinstance(c, str) else c
                    for c in _as_list(raw.get("completion_consequences", []))
                ],
                reset_conditions=[
                    {"type": "flag", "description": c} if isinstance(c, str) else c
                    for c in _as_list(raw.get("reset_conditions", []))
                ],
                interactions=[
                    {"description": i} if isinstance(i, str) else i
                    for i in _as_list(raw.get("interactions", []))
                ],
                narrative_description=raw.get("narrative_description", ""),
            )
            result[cid] = clock
        return result

    # ── Constants ─────────────────────────────────────────────────────

    def load_constants(self) -> Dict[str, Any]:
        return self._read_yaml("constants.yaml")

    # ── Timeline ──────────────────────────────────────────────────────

    def load_timeline(self) -> List[Dict[str, Any]]:
        data = self._read_yaml("timeline.yaml")
        return data.get("timeline", [])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_primary_faction(val: Any) -> Optional[str]:
    """Extract primary faction ID from strings like 'fed-continuity (Prince George\\'s District)'."""
    if val is None:
        return None
    if not isinstance(val, str):
        return str(val)
    # Strip parenthetical qualifiers
    paren_idx = val.find("(")
    if paren_idx > 0:
        val = val[:paren_idx].strip()
    return val.strip() if val.strip() else None


def _as_list(val: Any) -> list:
    """Ensure a value is a list."""
    if isinstance(val, list):
        return val
    if val is None:
        return []
    return [val]


def _parse_advance_rate(val: Any) -> Dict[str, Any]:
    """Parse advance_rate from text like 'fast (estimated 1 segment per 3-6 months)'."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        lower = val.lower()
        if "fast" in lower:
            prob = 0.4
        elif "moderate" in lower:
            prob = 0.2
        elif "slow" in lower:
            prob = 0.1
        elif "very slow" in lower:
            prob = 0.05
        else:
            prob = 0.2
        return {"probability": prob, "description": val}
    return {"probability": 0.2}


def FactionPopulation_from_raw(val: Any):
    """Build FactionPopulation from raw YAML value."""
    from emergence.engine.schemas.world import FactionPopulation
    pop = parse_population(val)
    return FactionPopulation(total=pop)
