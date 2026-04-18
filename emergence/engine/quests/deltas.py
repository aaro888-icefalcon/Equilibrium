"""World-state delta reconciler for quest resolutions.

When a Quest resolves, its `resolution.world_deltas_on_success` or
`resolution.world_deltas_on_failure[bright_line_id]` is handed to
`apply_deltas`, which applies each delta to the provided WorldView and
returns a list of applied records plus warnings.

Delta operations (canonical set; extend by adding to DELTA_OPS + dispatch):

    {"op": "faction_standing_delta", "faction_id": str, "delta": int}
    {"op": "npc_status_set", "npc_id": str, "status": str}
    {"op": "npc_relationship_delta", "npc_id": str,
                                      "standing_delta": int (optional),
                                      "trust_delta": int (optional)}
    {"op": "player_condition_delta", "track": "physical"|"mental"|"social",
                                      "delta": int}
    {"op": "player_heat_delta", "faction_id": str, "delta": int}
    {"op": "player_corruption_delta", "delta": int}
    {"op": "player_inventory_add", "item": dict}
    {"op": "player_inventory_remove", "item_id": str}
    {"op": "player_location_set", "location_id": str}
    {"op": "player_status_add", "name": str, "duration": int, "source": str}
    {"op": "threat_add", "threat": dict}
    {"op": "threat_remove", "threat_id": str}
    {"op": "quest_seed", "archetype": str, "seed": dict}
    {"op": "clock_advance", "clock_id": str, "segments": int}
    {"op": "history_event_add", "event": dict}

The reconciler is tolerant: a missing npc_id or faction_id produces a warning
and the delta is skipped, rather than raising. This keeps quest resolution
from aborting mid-way if a referenced entity has been removed by other play.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


DELTA_OPS = {
    "faction_standing_delta",
    "npc_status_set",
    "npc_relationship_delta",
    "player_condition_delta",
    "player_heat_delta",
    "player_corruption_delta",
    "player_inventory_add",
    "player_inventory_remove",
    "player_location_set",
    "player_status_add",
    "threat_add",
    "threat_remove",
    "quest_seed",
    "clock_advance",
    "history_event_add",
}


class WorldView(Protocol):
    """Minimum surface a world object must expose to be mutated by deltas.

    Implementations are free to be thin wrappers or the full live world
    object. Unknown ops raise; known ops with missing entities warn + skip.
    """

    def player(self) -> Any: ...
    def get_faction(self, faction_id: str) -> Any: ...
    def get_npc(self, npc_id: str) -> Any: ...
    def get_clock(self, clock_id: str) -> Any: ...
    def add_quest_seed(self, archetype: str, seed: Dict[str, Any]) -> None: ...
    def add_history_event(self, event: Dict[str, Any]) -> None: ...


@dataclass
class AppliedDelta:
    op: str
    payload: Dict[str, Any]
    warning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"op": self.op, "payload": dict(self.payload), "warning": self.warning}


@dataclass
class DeltaResult:
    applied: List[AppliedDelta] = field(default_factory=list)
    skipped: List[AppliedDelta] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applied": [d.to_dict() for d in self.applied],
            "skipped": [d.to_dict() for d in self.skipped],
        }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_delta(delta: Any, path: str = "delta") -> List[str]:
    """Return a list of error messages. Empty list means structurally valid."""
    errors: List[str] = []
    if not isinstance(delta, dict):
        return [f"{path}: must be a dict, got {type(delta).__name__}"]
    op = delta.get("op")
    if op not in DELTA_OPS:
        return [f"{path}.op: unknown op {op!r} (allowed: {sorted(DELTA_OPS)})"]

    def _req(key: str, typ: type) -> None:
        val = delta.get(key)
        if val is None:
            errors.append(f"{path}.{key}: required")
        elif not isinstance(val, typ):
            errors.append(f"{path}.{key}: must be {typ.__name__}")

    if op == "faction_standing_delta":
        _req("faction_id", str)
        _req("delta", int)
    elif op == "npc_status_set":
        _req("npc_id", str)
        _req("status", str)
    elif op == "npc_relationship_delta":
        _req("npc_id", str)
        if "standing_delta" not in delta and "trust_delta" not in delta:
            errors.append(f"{path}: must include standing_delta and/or trust_delta")
    elif op == "player_condition_delta":
        _req("track", str)
        _req("delta", int)
        if delta.get("track") not in (None, "physical", "mental", "social"):
            errors.append(f"{path}.track: must be physical|mental|social")
    elif op == "player_heat_delta":
        _req("faction_id", str)
        _req("delta", int)
    elif op == "player_corruption_delta":
        _req("delta", int)
    elif op == "player_inventory_add":
        if not isinstance(delta.get("item"), dict):
            errors.append(f"{path}.item: must be dict")
    elif op == "player_inventory_remove":
        _req("item_id", str)
    elif op == "player_location_set":
        _req("location_id", str)
    elif op == "player_status_add":
        _req("name", str)
        _req("duration", int)
    elif op == "threat_add":
        if not isinstance(delta.get("threat"), dict):
            errors.append(f"{path}.threat: must be dict")
    elif op == "threat_remove":
        _req("threat_id", str)
    elif op == "quest_seed":
        _req("archetype", str)
        if not isinstance(delta.get("seed"), dict):
            errors.append(f"{path}.seed: must be dict")
    elif op == "clock_advance":
        _req("clock_id", str)
        _req("segments", int)
    elif op == "history_event_add":
        if not isinstance(delta.get("event"), dict):
            errors.append(f"{path}.event: must be dict")

    return errors


def validate_deltas(deltas: List[Dict[str, Any]], path: str = "deltas") -> List[str]:
    errors: List[str] = []
    if not isinstance(deltas, list):
        return [f"{path}: must be a list"]
    for i, d in enumerate(deltas):
        errors.extend(validate_delta(d, f"{path}[{i}]"))
    return errors


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


def apply_deltas(deltas: List[Dict[str, Any]], world: WorldView) -> DeltaResult:
    """Apply each delta to `world`. Unknown entities produce warnings.

    Structural validation runs first; any invalid delta is skipped.
    """
    result = DeltaResult()
    for delta in deltas:
        errs = validate_delta(delta)
        if errs:
            result.skipped.append(AppliedDelta(op=str(delta.get("op", "?")), payload=dict(delta), warning="; ".join(errs)))
            continue

        op = delta["op"]
        warning = _apply_one(op, delta, world)
        applied = AppliedDelta(op=op, payload=dict(delta), warning=warning)
        if warning:
            result.skipped.append(applied)
        else:
            result.applied.append(applied)
    return result


def _apply_one(op: str, delta: Dict[str, Any], world: WorldView) -> str:
    """Apply a single delta. Return warning string ("" = success)."""
    try:
        if op == "faction_standing_delta":
            faction = world.get_faction(delta["faction_id"])
            if faction is None:
                return f"faction not found: {delta['faction_id']}"
            _apply_attr_delta(faction, "standing", delta["delta"])
            return ""

        if op == "npc_status_set":
            npc = world.get_npc(delta["npc_id"])
            if npc is None:
                return f"npc not found: {delta['npc_id']}"
            # Handle both dataclass and dict-shaped NPCs.
            if hasattr(npc, "status"):
                try:
                    setattr(npc, "status", delta["status"])
                except Exception as exc:  # frozen / property-only
                    return f"cannot set npc.status: {exc}"
            elif isinstance(npc, dict):
                npc["status"] = delta["status"]
            else:
                return f"npc has no settable status: {type(npc).__name__}"
            return ""

        if op == "npc_relationship_delta":
            player = world.player()
            if player is None:
                return "player not found"
            rels = getattr(player, "relationships", None)
            if rels is None:
                return "player.relationships unavailable"
            rel = rels.get(delta["npc_id"])
            if rel is None:
                return f"player has no relationship with {delta['npc_id']}"
            if "standing_delta" in delta:
                _apply_attr_delta(rel, "standing", int(delta["standing_delta"]))
            if "trust_delta" in delta:
                _apply_attr_delta(rel, "trust", int(delta["trust_delta"]))
            return ""

        if op == "player_condition_delta":
            player = world.player()
            if player is None:
                return "player not found"
            tracks = getattr(player, "condition_tracks", None)
            if tracks is None or delta["track"] not in tracks:
                return f"player.condition_tracks missing {delta['track']!r}"
            tracks[delta["track"]] = max(0, tracks[delta["track"]] + int(delta["delta"]))
            return ""

        if op == "player_heat_delta":
            player = world.player()
            if player is None:
                return "player not found"
            heat = getattr(player, "heat", None)
            if heat is None:
                return "player.heat unavailable"
            heat[delta["faction_id"]] = max(0, heat.get(delta["faction_id"], 0) + int(delta["delta"]))
            return ""

        if op == "player_corruption_delta":
            player = world.player()
            if player is None:
                return "player not found"
            if not hasattr(player, "corruption"):
                return "player.corruption unavailable"
            player.corruption = max(0, player.corruption + int(delta["delta"]))
            return ""

        if op == "player_inventory_add":
            player = world.player()
            inv = getattr(player, "inventory", None)
            if inv is None:
                return "player.inventory unavailable"
            inv.append(delta["item"])
            return ""

        if op == "player_inventory_remove":
            player = world.player()
            inv = getattr(player, "inventory", None)
            if inv is None:
                return "player.inventory unavailable"
            target = delta["item_id"]
            for i, it in enumerate(inv):
                it_id = getattr(it, "id", None) or (it.get("id") if isinstance(it, dict) else None)
                if it_id == target:
                    inv.pop(i)
                    return ""
            return f"inventory item not found: {target}"

        if op == "player_location_set":
            player = world.player()
            if player is None:
                return "player not found"
            if not hasattr(player, "location"):
                return "player.location unavailable"
            player.location = delta["location_id"]
            return ""

        if op == "player_status_add":
            player = world.player()
            statuses = getattr(player, "statuses", None)
            if statuses is None:
                return "player.statuses unavailable"
            statuses.append({
                "name": delta["name"],
                "duration": int(delta["duration"]),
                "source": delta.get("source", "quest_resolution"),
            })
            return ""

        if op == "threat_add":
            player = world.player()
            threats = getattr(player, "threats", None)
            if threats is None:
                return "player.threats unavailable"
            threats.append(dict(delta["threat"]))
            return ""

        if op == "threat_remove":
            player = world.player()
            threats = getattr(player, "threats", None)
            if threats is None:
                return "player.threats unavailable"
            target = delta["threat_id"]
            for i, t in enumerate(threats):
                tid = t.get("id") or t.get("threat_id") or t.get("npc_id")
                if tid == target:
                    threats.pop(i)
                    return ""
            return f"threat not found: {target}"

        if op == "quest_seed":
            if not hasattr(world, "add_quest_seed"):
                return "world does not support quest_seed"
            world.add_quest_seed(delta["archetype"], delta["seed"])
            return ""

        if op == "clock_advance":
            clock = world.get_clock(delta["clock_id"])
            if clock is None:
                return f"clock not found: {delta['clock_id']}"
            _apply_attr_delta(clock, "current_segment", int(delta["segments"]))
            return ""

        if op == "history_event_add":
            if not hasattr(world, "add_history_event"):
                player = world.player()
                history = getattr(player, "history", None)
                if history is None:
                    return "world/player do not support history"
                history.append(dict(delta["event"]))
                return ""
            world.add_history_event(delta["event"])
            return ""

    except Exception as exc:
        return f"apply error: {type(exc).__name__}: {exc}"

    return f"unhandled op: {op}"


def _apply_attr_delta(obj: Any, attr: str, delta: int) -> None:
    """Increment obj.attr by delta for both dataclass and dict-shaped targets."""
    if isinstance(obj, dict):
        obj[attr] = obj.get(attr, 0) + int(delta)
        return
    current = getattr(obj, attr, 0) or 0
    setattr(obj, attr, int(current) + int(delta))
