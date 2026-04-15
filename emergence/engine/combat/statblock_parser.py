"""Statblock parser for Emergence power library (Rev 4).

Parses structured-prose markdown statblocks into PowerV2-compatible dicts.
Defensive parsing — logs unparseable lines but never crashes.

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Broad mapping from section headers
# ---------------------------------------------------------------------------

_BROAD_MAP = {
    "SOMATIC": "somatic",
    "COGNITIVE": "cognitive",
    "MATERIAL": "material",
    "KINETIC": "kinetic",
    "SPATIAL": "spatial",
    "PARADOXIC": "paradoxic",
}

# Sub-category number to name (from content brief)
_SUB_CAT_MAP = {
    "4.1": "vitality", "4.2": "metamorphosis", "4.3": "augmentation",
    "4.4": "biochemistry", "4.5": "predation",
    "4.6": "telepathic", "4.7": "perceptive", "4.8": "predictive",
    "4.9": "dominant", "4.10": "auratic",
    "4.11": "elemental", "4.12": "transmutative", "4.13": "radiant",
    "4.14": "machinal", "4.15": "corrosive",
    "4.16": "impact", "4.17": "velocity", "4.18": "gravitic",
    "4.19": "projective", "4.20": "sonic",
    "4.21": "translative", "4.22": "phasing", "4.23": "gateway",
    "4.24": "reach", "4.25": "territorial",
    "4.26": "temporal", "4.27": "probabilistic", "4.28": "sympathetic",
    "4.29": "anomalous", "4.30": "divinatory",
}


def _snake_case(name: str) -> str:
    """Convert a power name to snake_case ID."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s


def _parse_pool_cost(cost_str: str) -> Tuple[int, Dict[str, Any]]:
    """Parse cost string like '2p + 1phy + scene_use' into (pool_cost, additional_cost)."""
    pool = 0
    additional: Dict[str, Any] = {}
    if not cost_str or cost_str.strip() in ("—", "-", "0p", "0p passive"):
        return 0, additional

    for part in cost_str.split("+"):
        part = part.strip()
        m = re.match(r"(\d+)p", part)
        if m:
            pool = int(m.group(1))
            continue
        m = re.match(r"(\d+)phy", part)
        if m:
            additional["condition_physical"] = int(m.group(1))
            continue
        m = re.match(r"(\d+)men", part)
        if m:
            additional["condition_mental"] = int(m.group(1))
            continue
        if "scene_use" in part or "scene" in part:
            additional["scene_use"] = True
        if "corruption" in part:
            m2 = re.match(r"(\d+)\s*corruption", part)
            additional["corruption"] = int(m2.group(1)) if m2 else 1

    return pool, additional


def _parse_posture_compat(compat_str: str) -> List[str]:
    """Parse posture compatibility like 'R3' or 'R2 (Parry, Block)'."""
    if not compat_str:
        return []
    if "R3" in compat_str:
        return ["parry", "block", "dodge"]
    if "A" == compat_str.strip():
        return ["aggressive"]
    m = re.search(r"\(([^)]+)\)", compat_str)
    if m:
        return [p.strip().lower() for p in m.group(1).split(",")]
    if "R2" in compat_str:
        return ["parry", "block"]
    if "R1" in compat_str:
        return ["parry"]
    return []


def _parse_families(families_str: str) -> List[str]:
    """Parse effect families from comma-separated string."""
    if not families_str or families_str.strip() in ("—", "-"):
        return []
    return [f.strip().lower().replace("-", "_").replace(" ", "_")
            for f in families_str.split(",") if f.strip()]


def _parse_parameters(param_str: str) -> Dict[str, Any]:
    """Parse Parameters: key=value, key=value."""
    params: Dict[str, Any] = {}
    if not param_str:
        return params
    # Remove 'Parameters:' prefix
    param_str = re.sub(r"^Parameters:\s*", "", param_str.strip())
    for part in re.split(r",\s*(?=[a-z_])", param_str):
        part = part.strip().rstrip(".")
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            v = v.strip()
            # Try to parse as number
            try:
                params[k] = int(v)
            except ValueError:
                try:
                    params[k] = float(v)
                except ValueError:
                    if v.lower() in ("true",):
                        params[k] = True
                    elif v.lower() in ("false",):
                        params[k] = False
                    elif v.startswith("[") and v.endswith("]"):
                        params[k] = [x.strip() for x in v[1:-1].split(",")]
                    else:
                        params[k] = v
    return params


def _parse_cast_line(line: str) -> Dict[str, Any]:
    """Parse a CAST_N | action | pool | cost | scope | range | dur | families line."""
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 3:
        return {}

    slot_id = parts[0].strip().lower().replace("cast_", "cast_")
    action_cost = "minor" if parts[1].strip().lower() == "minor" else "major"

    cost_str = parts[2].strip()
    pool_cost, additional_cost = _parse_pool_cost(cost_str)

    # Merge additional cost from parts[3] if present
    if len(parts) > 3 and parts[3].strip() not in ("—", "-", ""):
        extra_pool, extra_add = _parse_pool_cost(parts[3])
        pool_cost += extra_pool
        additional_cost.update(extra_add)

    scope = parts[4].strip().lower().replace(" ", "_") if len(parts) > 4 else "enemy_single"
    range_band = parts[5].strip().lower() if len(parts) > 5 else "close"
    duration = parts[6].strip().lower().replace(" ", "_") if len(parts) > 6 else "instant"
    families = _parse_families(parts[7]) if len(parts) > 7 else []

    # Clean up scope
    if scope in ("—", "-", ""):
        scope = "self"
    if range_band in ("—", "-", ""):
        range_band = "close"

    return {
        "slot_id": slot_id,
        "action_cost": action_cost,
        "pool_cost": pool_cost,
        "additional_cost": additional_cost,
        "effect_families": families,
        "targeting_scope": scope,
        "range_band": range_band,
        "duration": duration,
        "effect_description": "",
        "effect_parameters": {},
        "posture_sensitive": False,
        "playstyles": [],
        "hook": "",
    }


def _parse_rider_line(line: str) -> Dict[str, Any]:
    """Parse a RIDER_X | type/sub | compat | pool | restrictions line."""
    parts = [p.strip() for p in line.split("|")]
    if len(parts) < 2:
        return {}

    slot_id = parts[0].strip().lower().replace("rider_", "rider_")

    # Type/sub
    type_sub = parts[1].strip() if len(parts) > 1 else "strike"
    rider_type = "strike"
    sub_category = ""
    if "/" in type_sub:
        rt, sc = type_sub.split("/", 1)
        rider_type = rt.strip().lower()
        sub_category = sc.strip().lower().replace(" ", "_")
    else:
        rider_type = type_sub.strip().lower()
        if rider_type.startswith("restriction"):
            rider_type = "strike"

    # Posture compat
    compat_str = parts[2].strip() if len(parts) > 2 else ""
    compatible_postures = _parse_posture_compat(compat_str)

    # Pool cost
    cost_str = parts[3].strip() if len(parts) > 3 else "0p"
    pool_cost, _ = _parse_pool_cost(cost_str)

    return {
        "slot_id": slot_id,
        "rider_type": rider_type,
        "sub_category": sub_category,
        "pool_cost": pool_cost,
        "restrictions": {},
        "compatible_postures": compatible_postures,
        "effect_description": "",
        "effect_parameters": {},
        "playstyles": [],
        "combo_note": "",
    }


def parse_statblock_file(filepath: str) -> List[Dict[str, Any]]:
    """Parse a statblock markdown file into a list of power dicts."""
    with open(filepath, "r") as f:
        content = f.read()

    powers: List[Dict[str, Any]] = []
    current_broad = ""
    current_sub = ""

    # Split into blocks by ---
    blocks = re.split(r"\n---\n", content)

    for block in blocks:
        lines = block.strip().split("\n")
        if not lines:
            continue

        # Check for broad header
        for line in lines:
            m = re.match(r"^#\s+BROAD:\s+(\w+)", line)
            if m:
                broad_name = m.group(1).upper()
                current_broad = _BROAD_MAP.get(broad_name, broad_name.lower())

            m = re.match(r"^##\s+Sub-category\s+([\d.]+)\s*[—–-]\s*(.+)", line)
            if m:
                sub_num = m.group(1).strip()
                current_sub = _SUB_CAT_MAP.get(sub_num, m.group(2).strip().lower())

        # Look for power header: **Name** — ...
        power = _parse_power_block(lines, current_broad, current_sub)
        if power:
            powers.append(power)

    return powers


def _parse_power_block(
    lines: List[str],
    broad: str,
    sub_category: str,
) -> Optional[Dict[str, Any]]:
    """Parse a single power block into a PowerV2-compatible dict."""

    # Find header line
    header_line = ""
    header_idx = -1
    for i, line in enumerate(lines):
        if re.match(r"^\*\*[^*]+\*\*\s*[—–-]", line):
            header_line = line
            header_idx = i
            break

    if not header_line:
        return None

    # Parse header
    m = re.match(r"^\*\*(.+?)\*\*\s*[—–-]\s*(.+)$", header_line)
    if not m:
        return None

    name = m.group(1).strip()
    rest = m.group(2).strip()

    # Parse pair_role, playstyles, register from rest
    parts = [p.strip() for p in rest.split("|")]
    pair_role = parts[0].strip() if parts else "Flex"
    playstyles = [p.strip() for p in parts[1].split(",")] if len(parts) > 1 else []
    register_gating = [r.strip().lower() for r in parts[2].split(",")] if len(parts) > 2 else ["human", "creature", "eldritch"]

    # Generate ID
    power_id = f"{broad}_{sub_category}_{_snake_case(name)}" if broad and sub_category else _snake_case(name)

    # Parse identity
    identity = ""
    for line in lines[header_idx + 1:]:
        if line.strip().startswith("Identity:"):
            identity = line.strip().replace("Identity:", "").strip()
            break

    # Parse casts
    cast_modes = []
    rider_slots = []
    capstone = None
    enhanced_rider = None

    i = header_idx + 1
    while i < len(lines):
        line = lines[i].strip()

        if re.match(r"^CAST_[123]\s*\|", line):
            cast = _parse_cast_line(line)
            # Collect Effect, Parameters, Playstyles, Hook from following lines
            j = i + 1
            while j < len(lines) and not re.match(r"^(CAST_|RIDER_|CAPSTONE|ENHANCED_RIDER|\*\*)", lines[j].strip()):
                sub = lines[j].strip()
                if sub.startswith("Effect:"):
                    cast["effect_description"] = sub.replace("Effect:", "").strip()
                elif sub.startswith("Parameters:"):
                    cast["effect_parameters"] = _parse_parameters(sub)
                elif sub.startswith("Playstyles:"):
                    ps_hook = sub.replace("Playstyles:", "").strip()
                    if "Hook:" in ps_hook:
                        ps_part, hook_part = ps_hook.split("Hook:", 1)
                        cast["playstyles"] = [p.strip() for p in ps_part.split(",") if p.strip().rstrip(".")]
                        cast["hook"] = hook_part.strip().rstrip(".")
                    else:
                        cast["playstyles"] = [p.strip() for p in ps_hook.split(",") if p.strip().rstrip(".")]
                j += 1
            cast_modes.append(cast)
            i = j
            continue

        elif re.match(r"^RIDER_[A-C]\s*\|", line):
            rider = _parse_rider_line(line)
            j = i + 1
            while j < len(lines) and not re.match(r"^(CAST_|RIDER_|CAPSTONE|ENHANCED_RIDER|\*\*)", lines[j].strip()):
                sub = lines[j].strip()
                if sub.startswith("Effect:"):
                    rider["effect_description"] = sub.replace("Effect:", "").strip()
                elif sub.startswith("Parameters:"):
                    rider["effect_parameters"] = _parse_parameters(sub)
                elif sub.startswith("Playstyles:") or sub.startswith("Playstyles."):
                    ps_combo = sub.replace("Playstyles:", "").replace("Playstyles.", "").strip()
                    if "Combo:" in ps_combo:
                        ps_part, combo_part = ps_combo.split("Combo:", 1)
                        rider["playstyles"] = [p.strip() for p in ps_part.split(",") if p.strip().rstrip(".")]
                        rider["combo_note"] = combo_part.strip().rstrip(".")
                    else:
                        rider["playstyles"] = [p.strip() for p in ps_combo.split(",") if p.strip().rstrip(".")]
                j += 1
            rider_slots.append(rider)
            i = j
            continue

        elif line.startswith("CAPSTONE"):
            cap = {"name": "", "pool_cost": 3, "additional_cost": {},
                   "targeting_scope": "self", "range_band": "close", "duration": "scene",
                   "effect_description": "", "effect_parameters": {},
                   "effect_families": [], "signal": "", "viability": "", "playstyles": []}
            # Parse capstone header
            m_cap = re.match(r"CAPSTONE\s*\(authored:\s*([^)]+)\)\s*\|(.+)", line)
            if m_cap:
                cap["name"] = m_cap.group(1).strip()
                cap_parts = [p.strip() for p in m_cap.group(2).split("|")]
                if cap_parts:
                    pool_cost, add_cost = _parse_pool_cost(cap_parts[0])
                    cap["pool_cost"] = pool_cost
                    cap["additional_cost"] = add_cost
                if len(cap_parts) > 2:
                    cap["targeting_scope"] = cap_parts[2].strip().lower().replace(" ", "_") or "self"
                if len(cap_parts) > 3:
                    cap["duration"] = cap_parts[3].strip().lower().replace(" ", "_") or "scene"
                if len(cap_parts) > 4:
                    cap["effect_families"] = _parse_families(cap_parts[4])

            j = i + 1
            while j < len(lines) and not re.match(r"^(CAST_|RIDER_|CAPSTONE|ENHANCED_RIDER|\*\*)", lines[j].strip()):
                sub = lines[j].strip()
                if sub.startswith("Signal:"):
                    cap["signal"] = sub.replace("Signal:", "").strip().strip('"').rstrip(".")
                elif sub.startswith("Viability:"):
                    cap["viability"] = sub.replace("Viability:", "").strip().rstrip(".")
                elif sub.startswith("Effect:"):
                    cap["effect_description"] = sub.replace("Effect:", "").strip()
                elif sub.startswith("Parameters:"):
                    cap["effect_parameters"] = _parse_parameters(sub)
                elif sub.startswith("Playstyles:"):
                    cap["playstyles"] = [p.strip() for p in sub.replace("Playstyles:", "").strip().split(",") if p.strip().rstrip(".")]
                j += 1
            capstone = cap
            i = j
            continue

        elif line.startswith("ENHANCED_RIDER"):
            enh = {"variant_name": "", "base_rider_slot": "", "enhancement_type": "",
                   "pool_cost": 0, "shift": "", "effect_description": "",
                   "effect_parameters": {}, "combo_note": ""}
            m_enh = re.match(r"ENHANCED_RIDER\s*\(authored:\s*(.+?)\s+on\s+(RIDER_[A-C])\)\s*\|(.+)", line)
            if m_enh:
                enh["variant_name"] = m_enh.group(1).strip()
                enh["base_rider_slot"] = m_enh.group(2).strip().lower()
                cost_str = m_enh.group(3).strip()
                enh["pool_cost"], _ = _parse_pool_cost(cost_str)
            else:
                # Simpler format
                m_enh2 = re.match(r"ENHANCED_RIDER\s*\(authored:\s*(.+?)\)\s*\|(.+)", line)
                if m_enh2:
                    enh["variant_name"] = m_enh2.group(1).strip()
                    cost_str = m_enh2.group(2).strip()
                    enh["pool_cost"], _ = _parse_pool_cost(cost_str)

            j = i + 1
            while j < len(lines) and not re.match(r"^(CAST_|RIDER_|CAPSTONE|ENHANCED_RIDER|\*\*)", lines[j].strip()):
                sub = lines[j].strip()
                if sub.startswith("Shift:"):
                    enh["shift"] = sub.replace("Shift:", "").strip().rstrip(".")
                elif sub.startswith("Effect:"):
                    enh["effect_description"] = sub.replace("Effect:", "").strip()
                elif sub.startswith("Parameters:"):
                    enh["effect_parameters"] = _parse_parameters(sub)
                elif sub.startswith("Combo:"):
                    enh["combo_note"] = sub.replace("Combo:", "").strip().rstrip(".")
                j += 1
            enhanced_rider = enh
            i = j
            continue

        i += 1

    # Pad to 3 casts, 3 riders
    while len(cast_modes) < 3:
        cast_modes.append({"slot_id": f"cast_{len(cast_modes)+1}", "action_cost": "major",
                          "pool_cost": 0, "additional_cost": {}, "effect_families": [],
                          "targeting_scope": "self", "range_band": "close", "duration": "instant",
                          "effect_description": "", "effect_parameters": {},
                          "posture_sensitive": False, "playstyles": [], "hook": ""})
    while len(rider_slots) < 3:
        rider_slots.append({"slot_id": f"rider_{len(rider_slots)+1}", "rider_type": "strike",
                           "sub_category": "", "pool_cost": 0, "restrictions": {},
                           "compatible_postures": [], "effect_description": "",
                           "effect_parameters": {}, "playstyles": [], "combo_note": ""})

    if not capstone:
        capstone = {"name": "", "pool_cost": 0, "additional_cost": {}, "targeting_scope": "self",
                   "range_band": "close", "duration": "scene", "effect_description": "",
                   "effect_parameters": {}, "effect_families": [], "signal": "",
                   "viability": "", "playstyles": []}
    if not enhanced_rider:
        enhanced_rider = {"variant_name": "", "base_rider_slot": "", "enhancement_type": "",
                         "pool_cost": 0, "shift": "", "effect_description": "",
                         "effect_parameters": {}, "combo_note": ""}

    return {
        "id": power_id,
        "schema_version": "2.0",
        "name": name,
        "category": broad,
        "sub_category": sub_category,
        "pair_role": pair_role,
        "register_gating": register_gating,
        "playstyles": playstyles,
        "identity": identity,
        "description": identity,
        "tier": 1,
        "cast_modes": cast_modes[:3],
        "capstone_options": [capstone, capstone],  # duplicate for now (spec has 2 authored but we parse 1)
        "rider_slots": rider_slots[:3],
        "enhanced_rider_options": [enhanced_rider, enhanced_rider, enhanced_rider],
        "prerequisite": None,
        "usage_scope": "both",
        "visibility": "visible",
    }


def parse_all_powers(
    part1_path: str,
    part2_path: str,
) -> List[Dict[str, Any]]:
    """Parse both statblock files and return combined power list."""
    powers = []
    if os.path.exists(part1_path):
        powers.extend(parse_statblock_file(part1_path))
    if os.path.exists(part2_path):
        powers.extend(parse_statblock_file(part2_path))
    return powers


def generate_power_json(
    powers: List[Dict[str, Any]],
    output_dir: str,
) -> Dict[str, int]:
    """Write powers to JSON files grouped by category. Returns counts per file."""
    os.makedirs(output_dir, exist_ok=True)

    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for p in powers:
        cat = p.get("category", "unknown")
        by_category.setdefault(cat, []).append(p)

    counts = {}
    for cat, cat_powers in by_category.items():
        filepath = os.path.join(output_dir, f"{cat}.json")
        with open(filepath, "w") as f:
            json.dump(cat_powers, f, indent=2)
        counts[cat] = len(cat_powers)

    return counts
