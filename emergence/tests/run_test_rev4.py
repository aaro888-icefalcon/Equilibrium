"""Rev 4 Combat Run-Test: 1 combat turn with cast + rider.

Demonstrates the full Rev 4 combat flow:
- Player (T3) with Force Strike + Regeneration
- NPC (T3, aggressive) with Pyrokinesis + Iron Body
- Both start in Parry posture
- Player arms Regeneration's periodic rider
- Full turn: Minor + Major for both combatants
"""

import random
import sys

from emergence.engine.combat.verbs import (
    CombatState, CombatantRecord, VerbResult,
    resolve_attack, resolve_brace, resolve_maneuver,
    resolve_power, resolve_posture_change,
)
from emergence.engine.combat.statuses import StatusEngine
from emergence.engine.combat.pool import init_pool
from emergence.engine.combat.posture_riders import arm_rider, apply_end_of_round_riders


def main():
    print("=" * 60)
    print("EMERGENCE REV 4 COMBAT RUN-TEST")
    print("=" * 60)

    rng = random.Random(17)

    # Build combatants
    player = CombatantRecord(
        id="player", side="player", tier=3,
        strength=8, agility=8, perception=6, will=6, insight=6, might=8,
        phy=0, men=0, soc=0, phy_max=5, men_max=5, soc_max=5,
        armor=1,
        powers=["somatic_vitality_regeneration", "kinetic_impact_force_strike"],
        current_posture="parry",
    )
    init_pool(player)

    npc = CombatantRecord(
        id="npc_1", side="enemy", tier=3,
        strength=6, agility=6, perception=6, will=8, insight=8, might=6,
        phy=0, men=0, soc=0, phy_max=5, men_max=5, soc_max=5,
        armor=0,
        ai_profile="aggressive",
        powers=["material_elemental_pyrokinesis", "somatic_augmentation_iron_body"],
        current_posture="parry",
    )
    init_pool(npc)

    # Build state
    state = CombatState()
    state.combatants["player"] = player
    state.combatants["npc_1"] = npc
    state.combat_register = "human"

    print(f"\n--- COMBAT START ---")
    print(f"Player: T{player.tier}, Posture={player.current_posture}, Pool={player.pool}/{player.pool_max}")
    print(f"NPC:    T{npc.tier}, Posture={npc.current_posture}, Pool={npc.pool}/{npc.pool_max}")

    # Player arms Regeneration's periodic rider
    regen_rider = {
        "slot_id": "rider_a",
        "rider_type": "posture",
        "sub_category": "periodic",
        "pool_cost": 0,
        "compatible_postures": ["parry", "block"],
        "effect_parameters": {"heal_physical": 1},
    }
    armed = arm_rider(player, "somatic_vitality_regeneration", regen_rider, "parry")
    print(f"\nPlayer arms Regeneration periodic rider: {'OK' if armed else 'FAILED'}")
    print(f"  Pool max after arming: {player.pool_max} (was {player.base_pool_max})")
    # Simulate some pool spend so brace has room to work
    player.pool = max(0, player.pool - 2)
    print(f"  Pool after spending 2 on earlier casts: {player.pool}/{player.pool_max}")

    # --- ROUND 1 ---
    print(f"\n{'=' * 40}")
    print(f"ROUND 1")
    print(f"{'=' * 40}")

    # Player Minor: Brace
    print(f"\n[Player Minor] Brace")
    r_brace = resolve_brace("player", state, rng)
    print(f"  Result: pool {player.pool}/{player.pool_max}, uses left: {player.brace_uses}")

    # Player Major: Attack (heavy) vs NPC
    print(f"\n[Player Major] Attack (heavy) vs NPC")
    r_atk = resolve_attack("player", "npc_1", state, rng)
    print(f"  Roll: d1={r_atk.check.d1}, d2={r_atk.check.d2}, total={r_atk.check.total} vs TN={r_atk.check.tn}")
    print(f"  Tier: {r_atk.success_tier}")
    print(f"  Damage: {r_atk.damage_dealt}")
    print(f"  NPC condition: phy={npc.phy}/{npc.phy_max}")

    # NPC Minor: Maneuver (reposition)
    print(f"\n[NPC Minor] Maneuver (reposition)")
    r_man = resolve_maneuver("npc_1", state, rng, target_id="player")
    print(f"  Roll: d1={r_man.check.d1}, d2={r_man.check.d2}, total={r_man.check.total} vs TN={r_man.check.tn}")
    print(f"  Tier: {r_man.success_tier}")

    # NPC Major: Power (Pyrokinesis) vs Player
    print(f"\n[NPC Major] Power (Pyrokinesis) vs Player")
    r_pow = resolve_power("npc_1", "player", state, rng)
    print(f"  Roll: d1={r_pow.check.d1}, d2={r_pow.check.d2}, total={r_pow.check.total} vs TN={r_pow.check.tn}")
    print(f"  Tier: {r_pow.success_tier}")
    print(f"  Damage: {r_pow.damage_dealt}")
    print(f"  Player condition: phy={player.phy}/{player.phy_max}")

    # End of round: periodic rider ticks
    print(f"\n[End of Round] Periodic rider ticks")
    effects = apply_end_of_round_riders(player)
    for e in effects:
        print(f"  Rider {e['rider']}: {e['effects']}")
    print(f"  Player phy after regen: {player.phy}/{player.phy_max}")

    # --- SUMMARY ---
    print(f"\n{'=' * 40}")
    print(f"END OF ROUND 1 SUMMARY")
    print(f"{'=' * 40}")
    print(f"Player: phy={player.phy}/{player.phy_max}, pool={player.pool}/{player.pool_max}, posture={player.current_posture}")
    print(f"  Armed riders: {len(player.armed_posture_riders)}")
    print(f"  Brace uses: {player.brace_uses}")
    print(f"NPC:    phy={npc.phy}/{npc.phy_max}, pool={npc.pool}/{npc.pool_max}, posture={npc.current_posture}")
    print(f"\n--- RUN-TEST COMPLETE ---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
