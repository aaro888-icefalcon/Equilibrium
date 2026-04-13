"""NPC generator — procedurally creates NPCs for session zero and simulation.

Uses setting bible population ratios for species, tier pyramid for
manifestation, and name pools for diverse characters.
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional, Tuple

from emergence.engine.schemas.world import (
    NPC,
    NpcKnowledge,
    NpcManifest,
    NpcRelationshipState,
)

# ---------------------------------------------------------------------------
# Name pools
# ---------------------------------------------------------------------------

_FIRST_NAMES_M = [
    "James", "Marcus", "David", "Chen", "Victor", "Diego", "Andre",
    "Samuel", "Elias", "Reza", "Tomás", "Kwame", "Nikolai", "Yusuf",
    "Liam", "Carlos", "Dmitri", "Hector", "Idris", "Kofi",
    "Mateo", "Obi", "Rashid", "Silas", "Tariq",
    "Wei", "Xavier", "Zane", "Arturo", "Basil",
]

_FIRST_NAMES_F = [
    "Elena", "Maria", "Sarah", "Li", "Priya", "Amara", "Lucia",
    "Fatima", "Ingrid", "Keiko", "Natasha", "Opal", "Rosa", "Uma",
    "Valentina", "Wren", "Yara", "Zara", "Anya", "Bianca",
    "Carmen", "Dara", "Esme", "Freya", "Gaia",
    "Hana", "Isla", "Jade", "Kira", "Luna",
]

_LAST_NAMES = [
    "Smith", "Chen", "Garcia", "Okonkwo", "Petrov", "Kim", "Santos",
    "Ali", "Johansson", "Mendez", "Nguyen", "O'Brien", "Patel", "Reyes",
    "Tanaka", "Volkov", "Walsh", "Xu", "Yilmaz", "Zhou",
    "Alvarez", "Becker", "Costa", "Delgado", "Fischer",
    "Gonzalez", "Hassan", "Ibrahim", "Jansen", "Kovacs",
]

# ---------------------------------------------------------------------------
# Species data
# ---------------------------------------------------------------------------

SPECIES_LIST = [
    "human",
    "hollow_boned",   # A
    "deep_voiced",    # B
    "silver_hand",    # C
    "pale_eyed",      # D
    "slow_breath",    # E
    "broad_shouldered",  # F
    "sun_worn",       # G
    "quick_blooded",  # H
    "wide_sighted",   # I
    "stone_silent",   # J
]

# Mid-Atlantic population ratios (~81% human, ~19% metahuman)
_SPECIES_WEIGHTS = {
    "human": 0.81,
    "hollow_boned": 0.01,
    "deep_voiced": 0.01,
    "silver_hand": 0.025,
    "pale_eyed": 0.01,
    "slow_breath": 0.01,
    "broad_shouldered": 0.01,
    "sun_worn": 0.025,
    "quick_blooded": 0.025,
    "wide_sighted": 0.04,
    "stone_silent": 0.01,
}

_SPECIES_NARRATION_TAGS = {
    "human": "",
    "hollow_boned": "lean and quick, lighter than they should be",
    "deep_voiced": "broader through the chest, voice that fills the room",
    "silver_hand": "the silver shows at the wrists when the sleeves move",
    "pale_eyed": "eyes that catch light wrong",
    "slow_breath": "still in a way other people aren't",
    "broad_shouldered": "large enough to be the largest in any room",
    "sun_worn": "weathered face, the look of someone who's worked in sun",
    "quick_blooded": "smaller than baseline, faster than baseline, warmer to the touch",
    "wide_sighted": "the eyes — large, often colored in ways baseline eyes are not",
    "stone_silent": "tall, still, the tension easing around them",
}

# ---------------------------------------------------------------------------
# Tier pyramid (human distribution)
# ---------------------------------------------------------------------------

_TIER_PYRAMID = {
    1: 0.40,
    2: 0.25,
    3: 0.15,
    4: 0.10,
    5: 0.05,
    6: 0.03,
    7: 0.015,
    8: 0.004,
    9: 0.0008,
    10: 0.00005,
}

_DOMAIN_FRACTIONS = {
    "physical": 0.28,
    "perceptual": 0.15,
    "matter_energy": 0.14,
    "biological": 0.14,
    "auratic": 0.12,
    "temporal_spatial": 0.09,
    "eldritch": 0.015,
}

# ---------------------------------------------------------------------------
# Personality traits pool
# ---------------------------------------------------------------------------

_PERSONALITY_TRAITS = [
    "pragmatic", "idealistic", "cautious", "reckless", "loyal",
    "suspicious", "generous", "greedy", "patient", "impulsive",
    "reserved", "outgoing", "cunning", "straightforward", "ambitious",
    "content", "protective", "detached", "compassionate", "ruthless",
]

# ---------------------------------------------------------------------------
# Voice templates
# ---------------------------------------------------------------------------

_VOICE_TEMPLATES = [
    "Speaks in short, measured sentences. Chooses words carefully.",
    "Talks fast, full of slang and half-finished thoughts.",
    "Formal diction with occasional dry humor. Rarely raises voice.",
    "Quiet until provoked. Then blunt and cutting.",
    "Warm, storytelling cadence. Draws people in before making a point.",
    "Clipped military precision. Every word has a purpose.",
    "Gentle tone that belies their intensity. Asks more questions than they answer.",
    "Rough-edged, working-class rhythm. Says exactly what they mean.",
    "Careful, diplomatic phrasing. Always leaves themselves an exit.",
    "Blunt, impatient, profane. Zero tolerance for pretension.",
]

# ---------------------------------------------------------------------------
# Role templates
# ---------------------------------------------------------------------------

_ROLE_TEMPLATES = [
    "trader", "scout", "guard", "healer", "messenger",
    "mechanic", "farmer", "hunter", "teacher", "leader",
    "smuggler", "diplomat", "enforcer", "scholar", "cook",
]

# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

def generate_npc(
    archetype: str = "general",
    constraints: Dict[str, Any] | None = None,
    rng: _random.Random | None = None,
) -> NPC:
    """Generate a procedural NPC.

    Args:
        archetype: Role archetype hint (e.g., "trader", "guard", "elder").
        constraints: Optional overrides for species, faction, location, tier, age, etc.
        rng: Random instance for deterministic generation.

    Returns:
        A fully-populated NPC object.
    """
    rng = rng or _random.Random()
    constraints = constraints or {}

    # Name
    gender = constraints.get("gender", rng.choice(["m", "f"]))
    first = constraints.get("first_name") or rng.choice(
        _FIRST_NAMES_M if gender == "m" else _FIRST_NAMES_F
    )
    last = constraints.get("last_name") or rng.choice(_LAST_NAMES)
    display_name = f"{first} {last}"

    # ID
    npc_id = constraints.get("id") or f"npc-gen-{first.lower()}-{last.lower()}"

    # Species
    species = constraints.get("species")
    if not species:
        species_names = list(_SPECIES_WEIGHTS.keys())
        species_probs = list(_SPECIES_WEIGHTS.values())
        species = rng.choices(species_names, weights=species_probs, k=1)[0]

    # Age
    age = constraints.get("age")
    if age is None:
        # Post-onset world: most NPCs are working age
        age = rng.randint(18, 65)

    # Manifestation
    tier = constraints.get("tier")
    if tier is None:
        tier_levels = list(_TIER_PYRAMID.keys())
        tier_probs = list(_TIER_PYRAMID.values())
        tier = rng.choices(tier_levels, weights=tier_probs, k=1)[0]

    domain = constraints.get("domain")
    if not domain:
        domain_names = list(_DOMAIN_FRACTIONS.keys())
        domain_probs = list(_DOMAIN_FRACTIONS.values())
        domain = rng.choices(domain_names, weights=domain_probs, k=1)[0]

    manifestation = NpcManifest(
        category=domain,
        tier=tier,
        specific_abilities=[f"T{tier} {domain} manifestation"],
    )

    # Faction
    faction = constraints.get("faction", None)

    # Location
    location = constraints.get("location", "")

    # Role
    role = constraints.get("role") or archetype
    if role == "general":
        role = rng.choice(_ROLE_TEMPLATES)

    # Personality
    num_traits = rng.randint(2, 4)
    traits = rng.sample(_PERSONALITY_TRAITS, min(num_traits, len(_PERSONALITY_TRAITS)))

    # Voice
    voice = constraints.get("voice") or rng.choice(_VOICE_TEMPLATES)

    # Standing
    standing = constraints.get("standing_with_player_default", 0)

    # Goals
    goals = []
    if role in ("trader", "smuggler"):
        goals.append({"id": "goal_0", "description": "Secure profitable trade routes", "progress": 0})
    elif role in ("guard", "enforcer"):
        goals.append({"id": "goal_0", "description": "Protect assigned territory", "progress": 0})
    elif role in ("healer", "teacher"):
        goals.append({"id": "goal_0", "description": "Help the community survive", "progress": 0})
    else:
        goals.append({"id": "goal_0", "description": "Survive and prosper in the new world", "progress": 0})

    npc = NPC(
        id=npc_id,
        display_name=display_name,
        faction_affiliation={
            "primary": faction,
            "secondary": [],
        },
        location=location,
        species=species,
        age=age,
        manifestation=manifestation,
        role=role,
        goals=goals,
        personality_traits=traits,
        knowledge=[],
        standing_with_player_default=standing,
        what_they_want_from_player="",
        voice=voice,
        hooks=[],
    )

    return npc


def generate_npc_batch(
    count: int,
    constraints: Dict[str, Any] | None = None,
    rng: _random.Random | None = None,
) -> List[NPC]:
    """Generate a batch of NPCs with variety enforcement."""
    rng = rng or _random.Random()
    constraints = constraints or {}

    npcs = []
    used_names = set()
    for _ in range(count):
        # Ensure unique names
        for _attempt in range(10):
            npc = generate_npc(constraints=dict(constraints), rng=rng)
            if npc.display_name not in used_names:
                used_names.add(npc.display_name)
                npcs.append(npc)
                break
        else:
            # If we can't get unique after 10 tries, accept duplicate
            npcs.append(npc)

    return npcs
