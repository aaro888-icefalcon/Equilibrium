"""Power pick scene — two-phase: subcategories → powers → auto-roll cast/rider.

Phase 1: engine offers 12 random sub-categories (of 30) → player picks 2
Phase 2: engine offers ALL powers in each picked sub-category (typically
         6-8 per category) → player picks 1 from each (= 2 powers) →
         engine auto-rolls 1 cast_mode + 1 rider_slot per power,
         deterministically from state.seed.

The scene phase is inferred from CreationState:
  - pending_subcategory_offer absent                    → offer subcategories
  - subcategories picked, pending_power_offer absent    → offer powers
  - powers picked, tier set                             → complete
"""

from __future__ import annotations

import json
import os
import random as _random
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)


POWERS_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "powers_v2",
)

# Number of options at each phase.
SUBCATEGORY_OFFER_COUNT = 12
SUBCATEGORY_PICK_COUNT = 2
POWER_PICK_PER_SUBCATEGORY = 1

DEFAULT_TIER = 3
DEFAULT_TIER_CEILING = 5


class PowerPickScene:
    scene_id: str = "power_pick"
    register: str = "standard"

    def __init__(self) -> None:
        self._power_cache: Optional[List[Dict[str, Any]]] = None

    # ------------------------------------------------------------------
    # Power loading
    # ------------------------------------------------------------------

    def _load_all_powers(self) -> List[Dict[str, Any]]:
        """Load all powers from powers_v2 JSON files (cached)."""
        if self._power_cache is not None:
            return self._power_cache
        powers: List[Dict[str, Any]] = []
        if os.path.isdir(POWERS_DATA_DIR):
            for fname in sorted(os.listdir(POWERS_DATA_DIR)):
                if not fname.endswith(".json"):
                    continue
                path = os.path.join(POWERS_DATA_DIR, fname)
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries = data if isinstance(data, list) else data.get("powers", [])
                powers.extend(entries)
        self._power_cache = powers
        return powers

    def _list_subcategories(self) -> List[str]:
        subs = sorted({p["sub_category"] for p in self._load_all_powers() if p.get("sub_category")})
        return subs

    # ------------------------------------------------------------------
    # Phase detection
    # ------------------------------------------------------------------

    def phase(self, state: CreationState) -> str:
        if not state.scene_choices.get("subcategory_offer"):
            return "subcategories_pending"
        if not state.scene_choices.get("power_offer"):
            return "powers_pending"
        if not state.powers:
            return "powers_pending"
        return "complete"

    # ------------------------------------------------------------------
    # Phase 1: offer subcategories
    # ------------------------------------------------------------------

    def prepare_subcategory_offer(
        self, state: CreationState, rng: _random.Random,
    ) -> List[str]:
        """Sample N subcategories weighted by classifier tags (if any)."""
        all_subs = self._list_subcategories()
        if not all_subs:
            return []
        count = min(SUBCATEGORY_OFFER_COUNT, len(all_subs))
        offer = _weighted_sample(all_subs, count, state, rng)
        state.scene_choices["subcategory_offer"] = offer
        return offer

    def apply_subcategory_picks(
        self,
        picks: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Apply the player's subcategory picks (indices into the offer)."""
        offer = state.scene_choices.get("subcategory_offer") or []
        if not offer:
            raise RuntimeError("no subcategory offer prepared; call prepare_subcategory_offer first")
        uniq = sorted(set(picks))
        if len(uniq) != SUBCATEGORY_PICK_COUNT:
            raise ValueError(f"must pick exactly {SUBCATEGORY_PICK_COUNT} distinct subcategories")
        if any(i < 0 or i >= len(offer) for i in uniq):
            raise ValueError("pick index out of range")
        chosen = [offer[i] for i in uniq]
        state.scene_choices["subcategories_picked"] = chosen
        return state

    # ------------------------------------------------------------------
    # Phase 2: offer powers per picked subcategory
    # ------------------------------------------------------------------

    def prepare_power_offer(
        self, state: CreationState, rng: _random.Random,
    ) -> List[Dict[str, Any]]:
        """Offer every power in each picked subcategory.

        Returns a flat list of offered power dicts, grouped by subcategory
        (first subcategory's powers, then the second's). Each entry carries
        a `sub_category` field for UI grouping. Within each subcategory the
        powers are sorted by id for stable ordering across calls.
        """
        picked_subs = state.scene_choices.get("subcategories_picked") or []
        if not picked_subs:
            raise RuntimeError("subcategories not picked; cannot offer powers")
        all_powers = self._load_all_powers()
        offer: List[Dict[str, Any]] = []
        for sub in picked_subs:
            in_sub = sorted(
                (p for p in all_powers if p.get("sub_category") == sub),
                key=lambda p: p.get("id", ""),
            )
            offer.extend({
                "id": p["id"],
                "name": p["name"],
                "category": p["category"],
                "sub_category": p["sub_category"],
                "description": p.get("description", ""),
                "playstyles": list(p.get("playstyles", [])),
                "tier": p.get("tier", 1),
            } for p in in_sub)
        state.scene_choices["power_offer"] = offer
        return offer

    def apply_power_picks(
        self,
        picks: List[int],
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
    ) -> CreationState:
        """Apply the player's power picks (indices into the power offer).

        Expected shape: 1 pick per picked subcategory (i.e. len(picks) ==
        len(subcategories_picked)). Auto-rolls cast_mode + rider per power.
        """
        offer = state.scene_choices.get("power_offer") or []
        picked_subs = state.scene_choices.get("subcategories_picked") or []
        if not offer:
            raise RuntimeError("no power offer prepared")
        if len(picks) != len(picked_subs):
            raise ValueError(
                f"must pick {len(picked_subs)} powers (one per subcategory)"
            )
        if len(set(picks)) != len(picks):
            raise ValueError("power picks must be distinct")
        if any(i < 0 or i >= len(offer) for i in picks):
            raise ValueError("power pick index out of range")

        # Each offered power belongs to a specific subcategory band; verify
        # that the picks cover each picked subcategory exactly once.
        picked_powers: List[Dict[str, Any]] = [offer[i] for i in picks]
        covered = {p["sub_category"] for p in picked_powers}
        if covered != set(picked_subs):
            raise ValueError("picks must cover each picked subcategory exactly once")

        # Roll cast + rider per power, deterministically off state.seed.
        all_powers = {p["id"]: p for p in self._load_all_powers()}
        final_powers: List[Dict[str, Any]] = []
        categories: List[str] = []
        for idx, summary in enumerate(picked_powers):
            power = all_powers.get(summary["id"])
            if power is None:
                raise RuntimeError(f"power id missing from data: {summary['id']!r}")
            roll_rng = _random.Random(state.seed + hash(power["id"]) + idx)
            cast_mode = _roll_one(power.get("cast_modes") or [], roll_rng)
            rider = _roll_one(power.get("rider_slots") or [], roll_rng)
            final_powers.append({
                "power_id": power["id"],
                "name": power["name"],
                "category": power["category"],
                "sub_category": power["sub_category"],
                "slot": "primary" if idx == 0 else "secondary",
                "cast_mode": cast_mode,
                "rider_slot": rider,
                "tier": power.get("tier", 1),
            })
            categories.append(power["category"])

        scene_result = {
            "powers": final_powers,
            "power_category_primary": categories[0] if categories else "",
            "power_category_secondary": (
                categories[1] if len(categories) > 1 and categories[1] != categories[0] else None
            ),
            "tier": DEFAULT_TIER,
            "tier_ceiling": DEFAULT_TIER_CEILING,
        }
        state = factory.apply_scene_result(self.scene_id, scene_result, state, rng)
        state.scene_choices["powers_final"] = final_powers
        return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _roll_one(options: List[Any], rng: _random.Random) -> Optional[Any]:
    if not options:
        return None
    return rng.choice(options)


def _weighted_sample(
    subs: List[str],
    count: int,
    state: CreationState,
    rng: _random.Random,
) -> List[str]:
    """Sample `count` distinct subcategories, weighted by classifier tags.

    If state has reaction_tags or self_description text, subcategories that
    keyword-match them get +1 weight (small nudge — the sample is still
    mostly random). Without tags, falls back to uniform random.
    """
    weights = {s: 1.0 for s in subs}
    haystack = " ".join([
        state.self_description or "",
        " ".join(state.reaction_tags or []),
    ]).lower()

    if haystack.strip():
        for sub in subs:
            if sub.lower() in haystack:
                weights[sub] += 2.0
            # Common mappings for professions/personality
            for nudge_sub, keywords in _SUB_KEYWORD_NUDGES.items():
                if nudge_sub == sub and any(k in haystack for k in keywords):
                    weights[sub] += 1.0

    # Weighted sampling without replacement.
    picks: List[str] = []
    remaining = list(subs)
    for _ in range(min(count, len(subs))):
        pool = [(s, weights[s]) for s in remaining]
        total = sum(w for _, w in pool)
        r = rng.uniform(0, total)
        acc = 0.0
        chosen = pool[-1][0]
        for s, w in pool:
            acc += w
            if r <= acc:
                chosen = s
                break
        picks.append(chosen)
        remaining.remove(chosen)
    return picks


# Small keyword nudges — profession/personality → subcategory affinity.
_SUB_KEYWORD_NUDGES: Dict[str, List[str]] = {
    "vitality":      ["surgeon", "doctor", "medic", "healer", "nurse"],
    "biochemistry":  ["pharmac", "chemist", "drug", "poison"],
    "impact":        ["soldier", "fighter", "martial", "boxing", "brawl"],
    "velocity":      ["runner", "driver", "cyclist", "athlete"],
    "perceptive":    ["detective", "investigator", "scout", "hunter"],
    "telepathic":    ["therapist", "psychologist", "counselor"],
    "projective":    ["musician", "performer", "speaker", "singer"],
    "augmentation":  ["engineer", "builder", "mechanic"],
    "machinal":      ["engineer", "mechanic", "machinist", "tinker"],
    "transmutative": ["smith", "metallurg", "crafts"],
    "elemental":     ["firefighter", "chemist", "metallurg"],
    "predictive":    ["actuary", "analyst", "strateg"],
    "probabilistic": ["gambler", "trader", "actuary"],
    "temporal":      ["scholar", "archivist", "historian"],
    "auratic":       ["commander", "officer", "leader", "chief"],
}
