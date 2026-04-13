"""Abstract (off-screen) combat resolution for faction/NPC conflicts.

Used when factions or NPCs fight each other without player involvement.
Resolution is simpler than full encounter combat: tier comparison + random.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Abstract combat
# ---------------------------------------------------------------------------

def resolve_abstract_combat(
    attacker: Dict[str, Any],
    defender: Dict[str, Any],
    context: Dict[str, Any],
    rng: random.Random,
) -> Dict[str, Any]:
    """Resolve an off-screen combat between two entities.

    Args:
        attacker: dict with at least 'id', 'tier', 'military_capacity'
        defender: dict with at least 'id', 'tier', 'military_capacity', 'defensive_capacity'
        context: dict with 'terrain_advantage' (-2..+2), 'surprise' bool, etc.
        rng: seeded random instance

    Returns:
        dict with: winner, loser, margin, casualties_attacker, casualties_defender,
                   consequences
    """
    # Calculate effective power
    atk_tier = attacker.get("tier", 3)
    atk_military = attacker.get("military_capacity", 50)
    def_tier = defender.get("tier", 3)
    def_military = defender.get("military_capacity", 50)
    def_defensive = defender.get("defensive_capacity", 0)

    # Base power: tier * 10 + military / 10
    atk_power = atk_tier * 10 + atk_military / 10
    def_power = def_tier * 10 + def_military / 10 + def_defensive * 2

    # Context modifiers
    terrain = context.get("terrain_advantage", 0)
    atk_power += terrain * 5

    if context.get("surprise", False):
        atk_power *= 1.3

    # Randomness: each side rolls 2d6
    atk_roll = rng.randint(1, 6) + rng.randint(1, 6)
    def_roll = rng.randint(1, 6) + rng.randint(1, 6)

    atk_total = atk_power + atk_roll
    def_total = def_power + def_roll

    # Determine winner
    margin = atk_total - def_total
    if margin > 0:
        winner_id = attacker["id"]
        loser_id = defender["id"]
    elif margin < 0:
        winner_id = defender["id"]
        loser_id = attacker["id"]
        margin = abs(margin)
    else:
        # Draw — defender holds
        winner_id = defender["id"]
        loser_id = attacker["id"]
        margin = 0

    # Casualties based on margin
    if margin > 15:
        casualty_scale = "devastating"
        loser_casualties = rng.randint(30, 50)
        winner_casualties = rng.randint(5, 15)
    elif margin > 8:
        casualty_scale = "heavy"
        loser_casualties = rng.randint(15, 30)
        winner_casualties = rng.randint(5, 15)
    elif margin > 3:
        casualty_scale = "moderate"
        loser_casualties = rng.randint(5, 15)
        winner_casualties = rng.randint(2, 10)
    else:
        casualty_scale = "light"
        loser_casualties = rng.randint(1, 5)
        winner_casualties = rng.randint(0, 3)

    # Consequences
    consequences: List[Dict[str, Any]] = []
    if casualty_scale in ("devastating", "heavy"):
        consequences.append({
            "type": "territory_change",
            "from": loser_id,
            "to": winner_id,
        })
    if casualty_scale == "devastating":
        consequences.append({
            "type": "faction_weakened",
            "faction": loser_id,
            "severity": "severe",
        })

    return {
        "winner": winner_id,
        "loser": loser_id,
        "margin": round(margin, 1),
        "casualty_scale": casualty_scale,
        "casualties_attacker": winner_casualties if winner_id == attacker["id"] else loser_casualties,
        "casualties_defender": loser_casualties if winner_id == attacker["id"] else winner_casualties,
        "consequences": consequences,
    }
