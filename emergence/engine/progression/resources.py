"""Resource progression — wealth, followers, holdings, equipment.

7 resource types: territory, holdings, wealth, followers, influence,
knowledge, equipment. Some decay without maintenance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


RESOURCE_TYPES = [
    "territory", "holdings", "wealth", "followers",
    "influence", "knowledge", "equipment",
]

WEALTH_TYPES = [
    "cu", "scrip", "crown_chits", "grain_stores",
    "pre_onset_pharma", "trade_goods",
]

# Annual decay rates for wealth types
WEALTH_DECAY = {
    "cu": 0.0,
    "scrip": 0.05,
    "crown_chits": 0.10,
    "grain_stores": 0.10,  # per month if not preserved
    "pre_onset_pharma": 0.03,
    "trade_goods": 0.05,
}


class ResourceProgression:
    """Manages player resources."""

    def __init__(self, character: Dict[str, Any]) -> None:
        self.character = character
        if "resources" not in character:
            character["resources"] = {}

    def add_resource(self, resource_id: str, amount: int) -> int:
        """Add to a resource. Returns new total."""
        res = self.character["resources"]
        res[resource_id] = res.get(resource_id, 0) + amount
        return res[resource_id]

    def spend_resource(self, resource_id: str, amount: int) -> bool:
        """Spend a resource. Returns True if successful (had enough)."""
        res = self.character["resources"]
        current = res.get(resource_id, 0)
        if current < amount:
            return False
        res[resource_id] = current - amount
        return True

    def get_resource(self, resource_id: str) -> int:
        """Get current amount of a resource."""
        return self.character.get("resources", {}).get(resource_id, 0)

    def has_resource(self, resource_id: str, amount: int = 1) -> bool:
        """Check if player has at least amount of resource."""
        return self.get_resource(resource_id) >= amount

    def apply_wealth_decay(self, months: int = 12) -> List[str]:
        """Apply decay to perishable wealth types. Returns changes."""
        changes = []
        res = self.character.get("resources", {})

        for wtype, annual_rate in WEALTH_DECAY.items():
            current = res.get(wtype, 0)
            if current <= 0 or annual_rate <= 0:
                continue

            monthly_rate = annual_rate / 12.0
            for _ in range(months):
                loss = int(current * monthly_rate)
                if loss < 1 and current > 0 and monthly_rate > 0:
                    loss = 1  # Minimum 1 unit loss per period
                current = max(0, current - loss)

            if current != res.get(wtype, 0):
                changes.append(f"{wtype}: {res[wtype]} -> {current}")
                res[wtype] = current

        return changes

    def apply_follower_upkeep(self, wealth_available: int) -> Dict[str, Any]:
        """Check follower upkeep costs against available wealth.

        Returns dict with: upkeep_cost, can_afford, morale_penalty.
        """
        res = self.character.get("resources", {})
        retainers = res.get("retainers", 0)
        retinue = res.get("retinue", 0)

        cost = retainers * 150 + retinue * 300
        can_afford = wealth_available >= cost

        return {
            "upkeep_cost": cost,
            "can_afford": can_afford,
            "morale_penalty": 0 if can_afford else 1,
        }

    def apply_holding_upkeep(self) -> int:
        """Calculate monthly holding upkeep cost."""
        res = self.character.get("resources", {})
        cost = 0
        cost += res.get("holding_residence", 0) * 30
        cost += res.get("holding_workshop", 0) * 30
        cost += res.get("holding_warehouse", 0) * 30
        cost += res.get("holding_fortified_position", 0) * 80  # 30 + 50
        cost += res.get("holding_stronghold", 0) * 130  # 30 + 100
        cost += res.get("holding_estate", 0) * 30
        return cost
