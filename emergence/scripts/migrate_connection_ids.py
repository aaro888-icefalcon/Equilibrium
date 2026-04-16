#!/usr/bin/env python3
"""Migrate location connection IDs from display strings to location slugs.

Reads locations.json, fuzzy-matches each to_location_id to a real loc-* key,
moves the original string to display_label, and reports unmatched entries.
"""

import json
import re
import sys
from pathlib import Path


# Manual overrides for connections that can't be fuzzy-matched
MANUAL_OVERRIDES = {
    "Catskill Throne (reluctant tributary)": "loc-mount-tremper",
    "Catskill Throne (tributary)": "loc-mount-tremper",
    "Catskill Throne tributary polities": "loc-mount-tremper",
    "Hudson passes (tribute collection routes)": "loc-rhinebeck",
    "Bear-House (neighbors)": "loc-kingston-hv",
    "Bear-House (commercial)": "loc-kingston-hv",
    "Lehigh Principalities": "loc-jim-thorpe",
    "Lehigh Principalities (treaty)": "loc-jim-thorpe",
    "Lehigh Principalities (losing)": "loc-jim-thorpe",
    "Cortlandt (protected)": "loc-peekskill-reactor",
    "Flushing-Edison Cluster (allied)": "loc-flushing-workshop",
    "Bronx; Westchester approaches": "loc-cross-bronx-raider-territory",
    "all trade routes converge": "loc-old-market-philly",
    "all 15 CJL townships": "loc-princeton-accord-hall",
    "Crabclaw Confederation; Delmarva (Finch)": "loc-rehoboth-beach-de",
    "Rutgers Ag Archive (correspondence)": "loc-rutgers-nb",
    "The Listening (deference, unclear direction)": "loc-wharton-forest-reserve",
    "adjacent to Catskill Throne tributary polities": "loc-mount-tremper",
    "other Harvest Lords; regional Catholic communities": "loc-denton-md",
    "occasional Kostas correspondence [GM]": "loc-kaaterskill-falls",
}


def build_match_index(locations: dict) -> dict:
    """Build multiple indexes for fuzzy matching."""
    # display_name -> key
    by_display = {}
    # significant words -> key
    by_word = {}
    # key fragments -> key
    by_fragment = {}

    for key, loc in locations.items():
        dn = loc.get("display_name", "")
        dn_lower = dn.lower()
        by_display[dn_lower] = key

        # Index by significant words (4+ chars)
        for word in re.sub(r"[^a-z0-9 ]", "", dn_lower).split():
            if len(word) >= 4 and word not in by_word:
                by_word[word] = key

        # Index by key fragments
        parts = key.replace("loc-", "").split("-")
        for part in parts:
            if len(part) >= 4 and part not in by_fragment:
                by_fragment[part] = key

    return {"display": by_display, "word": by_word, "fragment": by_fragment}


def match_connection(tid: str, locations: dict, index: dict) -> str | None:
    """Try to match a connection display string to a location key."""
    # Strategy 0: manual overrides
    if tid in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[tid]

    tid_lower = tid.lower()

    # Strategy 1: exact display name substring match
    for dn, key in index["display"].items():
        if dn in tid_lower or tid_lower.startswith(dn[:15]):
            return key

    # Strategy 2: key fragment overlap (2+ fragments match)
    for key in locations:
        parts = [p for p in key.replace("loc-", "").split("-") if len(p) > 2]
        if len(parts) >= 2:
            matches = sum(1 for p in parts[:3] if p in tid_lower)
            if matches >= 2:
                return key

    # Strategy 3: significant word match
    tid_words = set(re.sub(r"[^a-z0-9 ]", "", tid_lower).split())
    for word in tid_words:
        if len(word) >= 4 and word in index["word"]:
            return index["word"][word]

    return None


def migrate(locations_path: str, dry_run: bool = False) -> dict:
    """Run the migration. Returns stats."""
    with open(locations_path) as f:
        locations = json.load(f)

    index = build_match_index(locations)

    stats = {"total": 0, "matched": 0, "unmatched": 0, "already_valid": 0}
    unmatched_report = []

    for loc_id, loc in sorted(locations.items()):
        new_conns = []
        for conn in loc.get("connections", []):
            stats["total"] += 1
            tid = conn.get("to_location_id", "")

            # Already a valid loc-* key?
            if tid in locations:
                stats["already_valid"] += 1
                new_conns.append(conn)
                continue

            matched_key = match_connection(tid, locations, index)
            if matched_key:
                stats["matched"] += 1
                conn["display_label"] = tid
                conn["to_location_id"] = matched_key
            else:
                stats["unmatched"] += 1
                # Keep original but add display_label for consistency
                conn["display_label"] = tid
                unmatched_report.append(
                    f"  {loc_id}: \"{tid}\" -> NO MATCH"
                )

            new_conns.append(conn)
        loc["connections"] = new_conns

    if not dry_run:
        with open(locations_path, "w") as f:
            json.dump(locations, f, indent=2)
        print(f"Wrote {locations_path}")

    print(f"\nStats: {stats['total']} total, {stats['matched']} matched, "
          f"{stats['already_valid']} already valid, {stats['unmatched']} unmatched")

    if unmatched_report:
        print(f"\nUnmatched connections ({len(unmatched_report)}):")
        for line in unmatched_report:
            print(line)

    return stats


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "saves/default/locations.json"
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified")
    migrate(path, dry_run=dry_run)
