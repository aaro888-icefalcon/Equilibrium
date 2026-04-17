"""Scenario pool and tag-weighted power selection for session zero.

One cinematic danger vignette frames the power-selection beat.  The player
writes a freeform reaction.  The engine extracts tags from their reaction
(gut instinct) and from their earlier life description (personality), scores
every V2 power against the combined tag bag, and returns a slate of ten
candidates: top-scored first, then random fillers.

Sub-categories and playstyles on PowerV2 (see engine/schemas/content.py)
provide the match surface — no new schema fields required.
"""

from __future__ import annotations

import os as _os
import random as _random
import re as _re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Keyword → tag tables
# ---------------------------------------------------------------------------
# Tags align with V2 categories (kinetic, material, paradoxic, spatial,
# somatic, cognitive), sub_categories (30+), and playstyles (Tank, Brawler,
# Controller, Skirmisher, Investigator, Medic, ...).

REACTION_KEYWORDS: Dict[str, List[str]] = {
    # fight / aggression
    "fight": ["kinetic", "impact", "Brawler"],
    "punch": ["kinetic", "impact", "Brawler"],
    "hit": ["kinetic", "impact", "Brawler"],
    "strike": ["kinetic", "impact", "Brawler"],
    "attack": ["kinetic", "Brawler"],
    "charge": ["kinetic", "velocity", "Brawler"],
    "smash": ["kinetic", "impact", "material"],
    "break": ["material", "kinetic", "corrosive"],

    # defend / shield
    "shield": ["kinetic", "Tank"],
    "block": ["kinetic", "Tank"],
    "protect": ["kinetic", "somatic", "Tank"],
    "guard": ["kinetic", "Tank"],
    "cover": ["kinetic", "spatial", "Tank"],
    "hold": ["kinetic", "Tank"],

    # move / flee
    "run": ["kinetic", "velocity", "Skirmisher"],
    "sprint": ["kinetic", "velocity", "Skirmisher"],
    "flee": ["spatial", "velocity", "Skirmisher"],
    "escape": ["spatial", "translative", "Skirmisher"],
    "dodge": ["kinetic", "velocity", "Skirmisher"],
    "jump": ["kinetic", "velocity"],
    "climb": ["somatic", "augmentation"],

    # stealth / hide
    "hide": ["spatial", "phasing", "cognitive"],
    "sneak": ["spatial", "phasing", "Skirmisher"],
    "vanish": ["spatial", "phasing", "paradoxic"],
    "silent": ["cognitive", "Controller"],
    "quiet": ["cognitive", "Controller"],

    # perceive / investigate
    "watch": ["cognitive", "perceptive", "Investigator"],
    "observe": ["cognitive", "perceptive", "Investigator"],
    "listen": ["cognitive", "perceptive", "Investigator"],
    "study": ["cognitive", "perceptive", "Investigator"],
    "read": ["cognitive", "telepathic"],
    "sense": ["cognitive", "perceptive"],
    "find": ["cognitive", "divinatory", "Investigator"],
    "track": ["cognitive", "perceptive", "Investigator"],

    # heal / biology
    "heal": ["somatic", "vitality", "Medic"],
    "save": ["somatic", "vitality", "Medic"],
    "mend": ["somatic", "vitality", "Medic"],
    "tend": ["somatic", "Medic"],
    "doctor": ["somatic", "Medic"],
    "treat": ["somatic", "biochemistry", "Medic"],

    # social / calm / lead
    "calm": ["cognitive", "auratic", "Controller"],
    "soothe": ["cognitive", "auratic", "Controller"],
    "lead": ["cognitive", "dominant", "Controller"],
    "order": ["cognitive", "dominant", "Controller"],
    "persuade": ["cognitive", "telepathic", "Controller"],
    "lie": ["cognitive", "telepathic"],
    "deceive": ["cognitive", "telepathic"],

    # intimidate / fear
    "scare": ["cognitive", "auratic"],
    "threaten": ["cognitive", "dominant"],
    "intimidate": ["cognitive", "dominant"],

    # analytical / predictive
    "think": ["cognitive", "predictive"],
    "plan": ["cognitive", "predictive"],
    "predict": ["cognitive", "predictive", "paradoxic"],
    "wait": ["cognitive", "predictive", "Controller"],

    # environmental / matter
    "burn": ["material", "elemental"],
    "freeze": ["material", "elemental"],
    "melt": ["material", "elemental"],
    "bend": ["material", "transmutative"],
    "shape": ["material", "transmutative"],
    "build": ["material", "machinal"],

    # reality / weird
    "reach": ["spatial", "reach"],
    "pull": ["spatial", "reach", "kinetic"],
    "step": ["spatial", "translative"],
    "through": ["spatial", "phasing"],
    "slow": ["paradoxic", "temporal"],
    "stop": ["paradoxic", "temporal"],
    "change": ["paradoxic", "probabilistic"],
    "luck": ["paradoxic", "probabilistic"],
}


SELF_DESCRIPTION_KEYWORDS: Dict[str, List[str]] = {
    # temperament / reflex
    "blunt": ["cognitive", "dominant"],
    "direct": ["cognitive", "dominant", "kinetic"],
    "patient": ["cognitive", "predictive", "Controller"],
    "curious": ["cognitive", "perceptive", "Investigator"],
    "analytical": ["cognitive", "predictive", "Investigator"],
    "pragmatic": ["cognitive", "predictive"],
    "protective": ["somatic", "kinetic", "Tank"],
    "loyal": ["somatic", "kinetic", "Tank"],
    "reckless": ["kinetic", "velocity"],
    "defiant": ["kinetic", "dominant"],
    "quiet": ["cognitive", "Controller"],

    # domain
    "doctor": ["somatic", "vitality", "Medic"],
    "surgeon": ["somatic", "vitality", "biochemistry", "Medic"],
    "medical": ["somatic", "vitality", "Medic"],
    "nurse": ["somatic", "vitality", "Medic"],
    "soldier": ["kinetic", "impact", "Brawler"],
    "veteran": ["kinetic", "impact", "Tank"],
    "cop": ["kinetic", "dominant"],
    "teacher": ["cognitive", "telepathic"],
    "engineer": ["material", "machinal"],
    "mechanic": ["material", "machinal"],
    "farmer": ["somatic", "vitality", "material"],
    "trader": ["cognitive", "telepathic"],
    "thief": ["spatial", "phasing", "Skirmisher"],
    "reader": ["cognitive", "perceptive"],

    # interests / body
    "martial": ["kinetic", "impact", "Brawler"],
    "fight": ["kinetic", "impact", "Brawler"],
    "slim": ["kinetic", "velocity"],
    "fast": ["kinetic", "velocity", "Skirmisher"],
    "strong": ["kinetic", "impact", "Tank"],
}


# ---------------------------------------------------------------------------
# Domain extraction — keywords → concrete skill / attribute / occupation deltas
# ---------------------------------------------------------------------------
# The life-description scene parses the player's prose for domain signals.
# Each keyword yields a deterministic patch: small skill grants, attribute
# nudges, and (for occupation-naming words) an occupation hint that's used
# to look up the OCCUPATIONS table entry.
#
# Matches are case-insensitive exact word matches, same as the tag tables.
# A word contributes at most once per extraction call even if it recurs.

DOMAIN_EXTRACTION: Dict[str, Dict[str, Any]] = {
    # --- medical ---
    "surgeon": {
        "skills": {"surgery": 2, "first_aid": 1, "diagnosis": 1},
        "attribute_deltas": {"insight": 1, "perception": 1},
        "occupation_hint": "medical",
    },
    "surgery": {
        "skills": {"surgery": 1, "first_aid": 1},
        "attribute_deltas": {},
    },
    "resident": {
        "skills": {"first_aid": 1, "pharmacology": 1, "literacy": 1},
        "attribute_deltas": {"will": 1},
        "occupation_hint": "medical",
    },
    "doctor": {
        "skills": {"first_aid": 2, "diagnosis": 1},
        "attribute_deltas": {"insight": 1},
        "occupation_hint": "medical",
    },
    "physician": {
        "skills": {"first_aid": 2, "diagnosis": 1},
        "attribute_deltas": {"insight": 1},
        "occupation_hint": "medical",
    },
    "nurse": {
        "skills": {"first_aid": 2, "pharmacology": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "medical",
    },
    "medic": {
        "skills": {"first_aid": 2, "diagnosis": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "medical",
    },
    "paramedic": {
        "skills": {"first_aid": 2, "diagnosis": 1},
        "attribute_deltas": {"perception": 1, "agility": 1},
        "occupation_hint": "medical",
    },
    "medical": {
        "skills": {"first_aid": 1},
        "attribute_deltas": {},
        "occupation_hint": "medical",
    },
    "vascular": {
        "skills": {"surgery": 1, "diagnosis": 1},
        "attribute_deltas": {},
    },

    # --- combat / uniformed ---
    "soldier": {
        "skills": {"combat_ranged": 2, "combat_melee": 1, "tactics": 1},
        "attribute_deltas": {"strength": 1, "will": 1},
        "occupation_hint": "veteran",
    },
    "veteran": {
        "skills": {"combat_melee": 1, "combat_ranged": 1, "survival": 1},
        "attribute_deltas": {"will": 1},
        "occupation_hint": "veteran",
    },
    "marine": {
        "skills": {"combat_ranged": 2, "combat_melee": 1, "tactics": 1},
        "attribute_deltas": {"strength": 1, "will": 1},
        "occupation_hint": "veteran",
    },
    "cop": {
        "skills": {"streetwise": 1, "intimidation": 1, "combat_ranged": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "former badge",
    },
    "officer": {
        "skills": {"streetwise": 1, "intimidation": 1},
        "attribute_deltas": {"perception": 1},
    },
    "police": {
        "skills": {"streetwise": 1, "intimidation": 1, "combat_ranged": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "former badge",
    },
    "emt": {
        "skills": {"first_aid": 2, "streetwise": 1},
        "attribute_deltas": {"perception": 1, "agility": 1},
        "occupation_hint": "former badge",
    },

    # --- trades / labor ---
    "electrician": {
        "skills": {"repair": 2, "crafting": 1},
        "attribute_deltas": {"agility": 1, "insight": 1},
        "occupation_hint": "tradesperson",
    },
    "plumber": {
        "skills": {"repair": 2, "crafting": 1},
        "attribute_deltas": {"agility": 1},
        "occupation_hint": "tradesperson",
    },
    "mechanic": {
        "skills": {"repair": 2, "crafting": 1},
        "attribute_deltas": {"agility": 1, "insight": 1},
        "occupation_hint": "tradesperson",
    },
    "carpenter": {
        "skills": {"crafting": 2, "repair": 1},
        "attribute_deltas": {"strength": 1, "agility": 1},
        "occupation_hint": "tradesperson",
    },
    "engineer": {
        "skills": {"crafting": 1, "repair": 1, "literacy": 1},
        "attribute_deltas": {"insight": 1},
        "occupation_hint": "tradesperson",
    },
    "construction": {
        "skills": {"crafting": 1, "repair": 1},
        "attribute_deltas": {"strength": 1},
        "occupation_hint": "laborer",
    },
    "dockworker": {
        "skills": {"survival": 1, "streetwise": 1},
        "attribute_deltas": {"strength": 1},
        "occupation_hint": "laborer",
    },

    # --- white-collar / academic ---
    "lawyer": {
        "skills": {"literacy": 2, "negotiation": 1, "bureaucracy": 1},
        "attribute_deltas": {"insight": 1, "will": 1},
        "occupation_hint": "white collar",
    },
    "analyst": {
        "skills": {"literacy": 1, "investigation": 1, "bureaucracy": 1},
        "attribute_deltas": {"insight": 1, "perception": 1},
        "occupation_hint": "former federal",
    },
    "teacher": {
        "skills": {"instruction": 2, "literacy": 1},
        "attribute_deltas": {"insight": 1, "will": 1},
        "occupation_hint": "academic",
    },
    "professor": {
        "skills": {"instruction": 2, "literacy": 2, "history": 1},
        "attribute_deltas": {"insight": 1},
        "occupation_hint": "academic",
    },
    "academic": {
        "skills": {"literacy": 1, "instruction": 1},
        "attribute_deltas": {"insight": 1},
        "occupation_hint": "academic",
    },
    "student": {
        "skills": {"literacy": 1},
        "attribute_deltas": {},
    },
    "clerk": {
        "skills": {"bureaucracy": 1, "literacy": 1},
        "attribute_deltas": {},
        "occupation_hint": "former federal",
    },

    # --- service / streets ---
    "driver": {
        "skills": {"navigation": 1, "streetwise": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "service worker",
    },
    "cook": {
        "skills": {"cooking": 2, "streetwise": 1},
        "attribute_deltas": {},
        "occupation_hint": "service worker",
    },
    "bartender": {
        "skills": {"streetwise": 1, "negotiation": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "service worker",
    },
    "waitress": {
        "skills": {"streetwise": 1, "negotiation": 1},
        "attribute_deltas": {},
        "occupation_hint": "service worker",
    },
    "farmer": {
        "skills": {"farming": 2, "survival": 1, "animal_handling": 1},
        "attribute_deltas": {"strength": 1, "will": 1},
        "occupation_hint": "farmer",
    },

    # --- criminal ---
    "thief": {
        "skills": {"stealth": 2, "streetwise": 1, "lockpicking": 1},
        "attribute_deltas": {"agility": 1},
        "occupation_hint": "criminal",
    },
    "dealer": {
        "skills": {"streetwise": 2, "negotiation": 1},
        "attribute_deltas": {"perception": 1},
        "occupation_hint": "criminal",
    },
    "smuggler": {
        "skills": {"stealth": 1, "streetwise": 1, "navigation": 1},
        "attribute_deltas": {"agility": 1},
        "occupation_hint": "criminal",
    },

    # --- body / training ---
    "martial": {
        "skills": {"combat_melee": 2},
        "attribute_deltas": {"agility": 1, "strength": 1},
    },
    "boxer": {
        "skills": {"combat_melee": 2},
        "attribute_deltas": {"strength": 1, "agility": 1},
    },
    "boxing": {
        "skills": {"combat_melee": 1},
        "attribute_deltas": {"strength": 1},
    },
    "karate": {
        "skills": {"combat_melee": 2},
        "attribute_deltas": {"agility": 1},
    },
    "taekwondo": {
        "skills": {"combat_melee": 2},
        "attribute_deltas": {"agility": 1},
    },
    "judo": {
        "skills": {"combat_melee": 2},
        "attribute_deltas": {"strength": 1, "agility": 1},
    },
    "wrestler": {
        "skills": {"combat_melee": 1},
        "attribute_deltas": {"strength": 1},
    },
    "wrestling": {
        "skills": {"combat_melee": 1},
        "attribute_deltas": {"strength": 1},
    },
    "runner": {
        "skills": {"survival": 1},
        "attribute_deltas": {"agility": 1},
    },
    "climber": {
        "skills": {"survival": 1},
        "attribute_deltas": {"strength": 1, "agility": 1},
    },

    # --- interests / habits ---
    "reader": {
        "skills": {"literacy": 2},
        "attribute_deltas": {"insight": 1},
    },
    "historian": {
        "skills": {"literacy": 1, "history": 2},
        "attribute_deltas": {"insight": 1},
    },
    "history": {
        "skills": {"history": 1},
        "attribute_deltas": {},
    },
    "linguist": {
        "skills": {"languages": 2, "literacy": 1},
        "attribute_deltas": {"insight": 1},
    },

    # --- temperament (attributes only, no skills) ---
    "blunt": {"skills": {}, "attribute_deltas": {"will": 1}},
    "patient": {"skills": {}, "attribute_deltas": {"will": 1}},
    "curious": {"skills": {"investigation": 1}, "attribute_deltas": {"perception": 1}},
    "analytical": {"skills": {"investigation": 1}, "attribute_deltas": {"insight": 1}},
    "pragmatic": {"skills": {}, "attribute_deltas": {"insight": 1}},
    "loyal": {"skills": {}, "attribute_deltas": {"will": 1}},
    "stubborn": {"skills": {}, "attribute_deltas": {"will": 1}},
    "reckless": {"skills": {}, "attribute_deltas": {"agility": 1}},
}


# ---------------------------------------------------------------------------
# Tag extraction
# ---------------------------------------------------------------------------

_WORD_RE = _re.compile(r"[a-z]+")


def extract_tags(text: str, table: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Lowercase + tokenize *text*, match each word against *table* (or the
    reaction table by default), return the deduplicated tag list in first-
    seen order.  Missing words contribute nothing; no fuzzy matching.
    """
    if not text:
        return []
    kw_table = table if table is not None else REACTION_KEYWORDS
    seen: List[str] = []
    for word in _WORD_RE.findall(text.lower()):
        tags = kw_table.get(word)
        if not tags:
            continue
        for tag in tags:
            if tag not in seen:
                seen.append(tag)
    return seen


def extract_description_tags(text: str) -> List[str]:
    """Tag extraction for the life-description scene — uses both tables so
    keywords that only appear in the reaction table (e.g. 'run', 'fight')
    still contribute when they show up in a self-description."""
    tags = extract_tags(text, SELF_DESCRIPTION_KEYWORDS)
    for tag in extract_tags(text, REACTION_KEYWORDS):
        if tag not in tags:
            tags.append(tag)
    return tags


def extract_domain(text: str) -> Dict[str, Any]:
    """Parse *text* through DOMAIN_EXTRACTION and return concrete deltas.

    Returns a dict with:
      - skills: Dict[str, int]     (summed across unique matching keywords)
      - attribute_deltas: Dict[str, int]
      - occupation_hint: Optional[str]  (first seen wins)

    Matches are exact-word, case-insensitive.  Each keyword contributes at
    most once per call; duplicate occurrences of the same word do not stack.
    """
    result: Dict[str, Any] = {
        "skills": {},
        "attribute_deltas": {},
        "occupation_hint": None,
    }
    if not text:
        return result
    seen_words: set[str] = set()
    for word in _WORD_RE.findall(text.lower()):
        if word in seen_words:
            continue
        entry = DOMAIN_EXTRACTION.get(word)
        if not entry:
            continue
        seen_words.add(word)
        for skill, level in entry.get("skills", {}).items():
            result["skills"][skill] = result["skills"].get(skill, 0) + level
        for attr, delta in entry.get("attribute_deltas", {}).items():
            result["attribute_deltas"][attr] = (
                result["attribute_deltas"].get(attr, 0) + delta
            )
        if result["occupation_hint"] is None and entry.get("occupation_hint"):
            result["occupation_hint"] = entry["occupation_hint"]
    return result


# ---------------------------------------------------------------------------
# Cinematic vignette pool
# ---------------------------------------------------------------------------
# Each vignette is a specific, tactile danger moment.  The player writes a
# freeform reaction and the engine weights 6 candidate powers against the
# extracted tags.  Slot 1 drives primary-power selection; slot 2 drives
# secondary (with the primary's category excluded).

# Vignettes are written in present tense, specific nouns, ~200-300 words,
# ending on "What do you do?"

_SLOT_1_VIGNETTES: List[Dict[str, Any]] = [
    {
        "id": "v1_crashed_bus",
        "slot": 1,
        "framing": (
            "The city bus is on its side across Second Avenue, wheels still "
            "spinning. You were a block back when every engine in Manhattan "
            "quit at the same moment, and the bus drifted the last fifty feet "
            "on momentum alone. Now it is leaking diesel across hot asphalt.\n\n"
            "There is a child wedged against the lower windows. You can see "
            "one hand. The rest of her is under a man in a grey suit who "
            "isn't moving. A woman outside the bus is screaming in a language "
            "you don't know. The driver's seat is empty — door hanging open, "
            "one shoe on the street.\n\n"
            "Something in your chest is burning. Not panic. Something newer "
            "than panic. A pressure that wants out.\n\n"
            "The diesel has reached the curb. A car two lanes over — engine "
            "dead, but the wiring isn't — is sparking under the dash.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "heave_man",
                "label": "Heave the dead weight off her.",
                "tradeoff": "The man may not survive the angle you'll move him at. You're choosing the child.",
                "tags": ["kinetic", "impact", "Brawler", "Tank"],
            },
            {
                "id": "kill_spark",
                "label": "Kill the spark in the other car before the diesel catches.",
                "tradeoff": "Every second on the car is a second she doesn't have. But none of them have seconds if it catches.",
                "tags": ["material", "elemental", "Controller"],
            },
            {
                "id": "read_wreck",
                "label": "Read the wreck first — who else is alive in there, where the worst of it is.",
                "tradeoff": "The diesel does not wait for certainty.",
                "tags": ["cognitive", "perceptive", "Investigator"],
            },
            {
                "id": "command_woman",
                "label": "Seize the screaming woman. Make her help you lift.",
                "tradeoff": "Her panic is a liability. Your voice may break her further.",
                "tags": ["cognitive", "dominant", "Controller"],
            },
            {
                "id": "tend_man",
                "label": "Get to the man first. He may be alive. The child's airway isn't blocked.",
                "tradeoff": "The woman outside sees you choose the grown man over the child. She will remember.",
                "tags": ["somatic", "vitality", "Medic"],
            },
        ],
    },
    {
        "id": "v1_hospital_code",
        "slot": 1,
        "framing": (
            "You were scrubbed in on the fourth-floor vascular suite when "
            "the lights went. The backup generators didn't catch. The monitors "
            "died one by one — you heard them — and then the room went quiet "
            "in a way operating rooms do not go quiet.\n\n"
            "The patient on the table is sixty-one, open aneurysm, bleeding. "
            "The circulating nurse is calling for suction that won't come. "
            "The anesthesiologist has stopped talking. You cannot see the "
            "attending — he stepped out for coffee nine minutes ago and the "
            "hallway outside is pitch black.\n\n"
            "You can feel a pulse under your gloved fingers. It is slowing.\n\n"
            "Something opens behind your sternum. A heat, a pressure, a "
            "sense of a second set of hands where your own hands are.\n\n"
            "The patient's pressure drops ten more points.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "hold_pressure",
                "label": "Hold pressure by feel. Work the vessel with your hands. Treat him.",
                "tradeoff": "Without suction, without light, without the attending. You may be working on a corpse.",
                "tags": ["somatic", "vitality", "biochemistry", "Medic"],
            },
            {
                "id": "take_command",
                "label": "Take the room. Order suction by hand, retractors, clamp. Make them move.",
                "tradeoff": "The anesthesiologist has years on you. You're about to spend a relationship.",
                "tags": ["cognitive", "dominant", "Controller"],
            },
            {
                "id": "find_attending",
                "label": "Get the attending. He's in the dark somewhere close — find him, fast.",
                "tradeoff": "Every second off the table, the patient bleeds.",
                "tags": ["cognitive", "perceptive", "Investigator", "spatial"],
            },
            {
                "id": "lend_pulse",
                "label": "Lend the pulse what is opening in you.",
                "tradeoff": "You don't know what it is. You don't know what it takes.",
                "tags": ["somatic", "vitality", "paradoxic", "Medic"],
            },
            {
                "id": "call_code",
                "label": "Call it. Pull the team out. He is gone; the living matter.",
                "tradeoff": "He has a name on the whiteboard you read this morning.",
                "tags": ["cognitive", "predictive", "Controller"],
            },
        ],
    },
    {
        "id": "v1_stairwell",
        "slot": 1,
        "framing": (
            "Twelfth-floor stairwell, Bellevue. The fire door above you just "
            "slammed. The fire door below you won't open. The emergency "
            "lights came on for thirty seconds and died.\n\n"
            "There are three people on the landing with you. A tech you've "
            "nodded to in the cafeteria. A woman in street clothes holding "
            "her wrist at a wrong angle. And a man you don't recognize, "
            "sweating, eyes too wide, a knife in his hand. Kitchen knife. "
            "Serrated.\n\n"
            "The woman is saying please, please, quietly. The tech is "
            "frozen with his back against the railing. The man with the "
            "knife is looking at you. Specifically at you.\n\n"
            "Something low in your belly has woken up. It feels like the "
            "moment before a sneeze, multiplied.\n\n"
            "The man takes a step.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "close_distance",
                "label": "Close the distance. Take the knife off him.",
                "tradeoff": "A serrated blade does not forgive hands.",
                "tags": ["kinetic", "impact", "Brawler"],
            },
            {
                "id": "shield_woman",
                "label": "Put yourself between him and the woman.",
                "tradeoff": "Your body is what stops the knife.",
                "tags": ["kinetic", "somatic", "Tank"],
            },
            {
                "id": "read_him",
                "label": "Read him. Find what he's actually afraid of.",
                "tradeoff": "He may not wait for you to finish.",
                "tags": ["cognitive", "perceptive", "Investigator"],
            },
            {
                "id": "scramble_him",
                "label": "Make him not see what he thinks he sees.",
                "tradeoff": "You've never done this. You don't know what it costs.",
                "tags": ["cognitive", "dominant", "Controller"],
            },
            {
                "id": "force_door",
                "label": "Force the fire door below. Get them out past him.",
                "tradeoff": "You turn your back on a knife to do it.",
                "tags": ["kinetic", "material", "Skirmisher"],
            },
        ],
    },
    {
        "id": "v1_subway_flood",
        "slot": 1,
        "framing": (
            "The 6 train stopped between 33rd and 28th. The lights flickered, "
            "then steadied on emergency red. Then steadied. Then the water "
            "started coming up through the floor panels.\n\n"
            "It is already ankle-deep. Thirty-odd people in your car. An old "
            "woman is sitting because her legs won't take her. A teenager is "
            "kicking the door, which will not open, because the engineer two "
            "cars forward is dead at the controls and no override answers.\n\n"
            "The smell is wrong. Not sewage — iron. Blood-iron. A taste in "
            "the back of your throat that wasn't there ninety seconds ago.\n\n"
            "Behind your eyes something is opening, the way a pupil opens "
            "in a dark room.\n\n"
            "The water reaches mid-calf. The old woman has stopped crying "
            "and is watching you. Everyone in the car is watching you now.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "pry_doors",
                "label": "Pry the doors. Brute force.",
                "tradeoff": "The emergency release you throw may pin whoever's closest.",
                "tags": ["kinetic", "impact", "Brawler"],
            },
            {
                "id": "take_car",
                "label": "Take the car. Calm them. Triage who goes out first.",
                "tradeoff": "You will not save all thirty-four. You choose who goes first.",
                "tags": ["cognitive", "dominant", "Controller"],
            },
            {
                "id": "find_breach",
                "label": "Find the breach — where the water is actually coming in.",
                "tradeoff": "Understanding is not yet rescue.",
                "tags": ["cognitive", "perceptive", "Investigator"],
            },
            {
                "id": "lift_woman",
                "label": "Get the old woman onto a seat. Then the next. Then the next.",
                "tradeoff": "The teenager at the door will see who you chose.",
                "tags": ["somatic", "vitality", "Medic", "Tank"],
            },
            {
                "id": "through_wall",
                "label": "Find a way through the wall, not the door.",
                "tradeoff": "You don't know if whatever is waking in you can carry others.",
                "tags": ["spatial", "phasing", "Skirmisher"],
            },
        ],
    },
    {
        "id": "v1_apartment_invasion",
        "slot": 1,
        "framing": (
            "Your door comes in at three in the morning. You were already "
            "awake — the lights had been flickering for an hour, the radio "
            "dead, phones dead. Now the deadbolt is splinters on your floor "
            "and two men are in your apartment with a crowbar and a length "
            "of pipe.\n\n"
            "The younger one is talking fast, too fast, telling you to stay "
            "on the floor. The older one isn't talking. He is looking at "
            "your kitchen knife block with the practiced eye of a man who "
            "has taken knives off people before.\n\n"
            "You are in your pajamas. There is nothing in your hand. The "
            "lamp at your bedside is the nearest thing, plugged in, cord "
            "dangling, dead because everything electric is dead.\n\n"
            "Something under your skin is waking up, and it is not afraid. "
            "That is the wrong feeling for this moment, and you know it, "
            "and it keeps waking up anyway.\n\n"
            "The older one steps toward the block.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "go_older",
                "label": "Go at the older one. He's the real threat.",
                "tradeoff": "The younger one has a crowbar at your back.",
                "tags": ["kinetic", "impact", "Brawler"],
            },
            {
                "id": "break_younger",
                "label": "Break the younger one first — he's scared, he'll fold.",
                "tradeoff": "The older one closes distance before you finish.",
                "tags": ["cognitive", "perceptive", "kinetic", "Skirmisher"],
            },
            {
                "id": "scramble_them",
                "label": "Scramble what they think they're seeing.",
                "tradeoff": "You don't know how to aim it. You don't know where it stops.",
                "tags": ["cognitive", "dominant", "Controller"],
            },
            {
                "id": "weaponize_room",
                "label": "Turn the room against them — shelving, lamp, glass.",
                "tradeoff": "Your home goes with them.",
                "tags": ["kinetic", "material", "Controller"],
            },
            {
                "id": "talk",
                "label": "Stop. Talk. They're hungry, not killers.",
                "tradeoff": "The older man has done this before. He knows what talking means.",
                "tags": ["cognitive", "telepathic", "Controller"],
            },
        ],
    },
    {
        "id": "v1_rooftop_fall",
        "slot": 1,
        "framing": (
            "You were on the roof of the hospital housing — tar-paper, three "
            "pigeons, a view of the East River — when every motor in the "
            "city stopped at once. You felt it as a pressure change. The "
            "helicopters just fell out of the air.\n\n"
            "A news helicopter hit the building across the street, broke "
            "apart, threw a rotor blade the length of a car into your block. "
            "Your roof shuddered. The parapet on your side is leaning now, "
            "cracked concrete, maybe ten seconds from going.\n\n"
            "There is a man on that parapet. You don't know him. He was "
            "out for a smoke. He is clutching the cracked edge and the "
            "edge is clutching him back, badly.\n\n"
            "Thirty-one stories down.\n\n"
            "Something has unlocked behind your ribs. A sense of leverage "
            "that was not there a minute ago. Not strength — leverage.\n\n"
            "The concrete cracks another inch.\n\n"
            "What do you do?"
        ),
        "choices": [
            {
                "id": "drop_flat",
                "label": "Drop flat. Save yourself. The parapet is going.",
                "tradeoff": "He watches you look away.",
                "tags": ["kinetic", "velocity", "Skirmisher"],
            },
            {
                "id": "reach_him",
                "label": "Reach for him with whatever is waking in you.",
                "tradeoff": "You don't know if you can hold the weight.",
                "tags": ["kinetic", "reach", "spatial"],
            },
            {
                "id": "anchor_pull",
                "label": "Anchor yourself to the roof door. Pull him in by hand.",
                "tradeoff": "If your leverage is wrong, the parapet takes you both.",
                "tags": ["kinetic", "somatic", "Tank"],
            },
            {
                "id": "read_concrete",
                "label": "Read the concrete. Find the seam that still holds.",
                "tradeoff": "The concrete does not wait for certainty.",
                "tags": ["cognitive", "perceptive", "Investigator"],
            },
            {
                "id": "step_to_him",
                "label": "Will yourself to him.",
                "tradeoff": "If the unlock in you is not that, you both go.",
                "tags": ["spatial", "translative", "Skirmisher"],
            },
        ],
    },
]


_SLOT_2_VIGNETTES: List[Dict[str, Any]] = [
    {
        "id": "v2_winter_clinic",
        "slot": 2,
        "framing": (
            "Three weeks later. You understand your first ability now — not "
            "completely, but enough to use it without thinking. You have "
            "been using it.\n\n"
            "Tonight the clinic is a lobby on 34th with sheets for curtains "
            "and a generator you can't run because there is no fuel. "
            "Seventeen people. Four of them shouldn't live until morning. "
            "The kerosene lamp hisses and the boy in the corner with the "
            "infected wrist has stopped shivering, which is bad.\n\n"
            "Something else is stirring in you. Different from the first. "
            "Quieter. You have caught it before — in the margins, between "
            "the obvious moments. Now it is asking to be noticed.\n\n"
            "The boy's mother is holding his hand. She has not spoken in "
            "two hours. The woman in the next cot is watching you the way "
            "people watch clocks.\n\n"
            "The generator ticks as it cools.\n\n"
            "What do you reach for now?"
        ),
    },
    {
        "id": "v2_perimeter_watch",
        "slot": 2,
        "framing": (
            "Second month after the Onset. You have a roof and three people "
            "who depend on you holding it. The first ability has been the "
            "loud one — you know its weight, its cost, what it does and "
            "what it will not do.\n\n"
            "Tonight there are lights moving in the ruins a block east. "
            "Not flashlights — something steadier. Three sources, maybe "
            "four. Patient. Whoever is out there is not in a hurry.\n\n"
            "The cold has a metal taste. You can feel something else under "
            "your tongue, under your sternum — a second capacity, waking "
            "up the way ice cracks: patiently, along fault lines.\n\n"
            "Your cousin is asleep on the mattress by the window. The child "
            "two floors down is asleep. You have a crossbow you have never "
            "fired in anger and a knife that has seen use.\n\n"
            "The lights are closer.\n\n"
            "What do you reach for now?"
        ),
    },
    {
        "id": "v2_scavenger_confrontation",
        "slot": 2,
        "framing": (
            "A month out. You went down to the flooded pharmacy on 1st "
            "Avenue for insulin. Somebody else had the same idea.\n\n"
            "Four of them. They watched you wade in and waited for you to "
            "come out with your arms full. They are between you and the "
            "stairs. The tallest one is holding what used to be a fire axe. "
            "The one on his left has a dog. The dog is not fed.\n\n"
            "You have your first ability queued up — you have used it "
            "enough that the activation is a familiar weight — but you "
            "can feel the ceiling on it. Four bodies, tight quarters, one "
            "dog. The math does not close.\n\n"
            "Something else, underneath, is asking for attention. You have "
            "felt it before. You have not used it. It is not the loud one.\n\n"
            "The man with the axe takes a step into the water. The others "
            "follow. The dog's chain is slack.\n\n"
            "What do you reach for now?"
        ),
    },
    {
        "id": "v2_faction_emissary",
        "slot": 2,
        "framing": (
            "The man sitting across the barrel-fire wears Iron Crown "
            "colors and speaks softly. He is polite. He has been polite "
            "for the whole conversation. He is also, clearly, offering "
            "you a choice whose shape is dictated by what he already knows.\n\n"
            "He knows your first ability. Word travels. He has used the "
            "word 'asset' twice and 'partner' once and not once said the "
            "word 'or.' The or is implied.\n\n"
            "Something else is open in you now — smaller than the first, "
            "but precise. A second sense. You have been catching it "
            "glance off the edges of conversations for a week. You have "
            "not named it yet.\n\n"
            "The man refills your cup. The two behind him have not moved "
            "in fifteen minutes. That in itself is a kind of fact.\n\n"
            "He asks, again, whether you have considered his offer.\n\n"
            "What do you reach for now?"
        ),
    },
    {
        "id": "v2_tunnel_crossing",
        "slot": 2,
        "framing": (
            "The Holland Tunnel is dark the way the inside of a sealed "
            "jar is dark. You are two miles in. The cars you are walking "
            "past have been there for five weeks. Some still have people "
            "in them.\n\n"
            "You came in with your first ability as the reason you could "
            "do this at all. You are good with it now — you know its "
            "shape, its draw, its fatigue curve. But the tunnel is doing "
            "something to you the surface never did. There is a second "
            "pressure, not from outside, from inside. Quieter. Subtle. "
            "It has been there the whole walk.\n\n"
            "Something is moving in the dark three cars ahead. Not a "
            "rat. Too deliberate. It has stopped now that you have "
            "stopped.\n\n"
            "Your flashlight is dim. You have maybe twenty minutes of "
            "battery. The new capacity in you is not asking, it is "
            "offering — take me out, use me, see with me.\n\n"
            "What do you reach for now?"
        ),
    },
    {
        "id": "v2_settlement_trial",
        "slot": 2,
        "framing": (
            "The council of the settlement that took you in meets in what "
            "used to be a high-school gym. You are on trial. A bag of "
            "copper went missing from the commissary three nights ago and "
            "a man named Rhys is insisting — politely, precisely — that "
            "you took it.\n\n"
            "You didn't. You know who did. You also know what will happen "
            "to that person if you name them here, in front of these "
            "people, with Rhys's voice doing what Rhys's voice does.\n\n"
            "Your first ability is no use in this room. It is a loud thing "
            "and this is a quiet problem. But something else is waking in "
            "you now — a smaller sense, focused on the shape of what people "
            "mean versus what they say. You have been noticing it for "
            "days. Tonight it is insistent.\n\n"
            "Rhys finishes his accusation. The council turns to you.\n\n"
            "What do you reach for now?"
        ),
    },
]


SCENARIO_VIGNETTES: List[Dict[str, Any]] = _SLOT_1_VIGNETTES + _SLOT_2_VIGNETTES


def select_vignette(
    slot: int,
    rng: _random.Random,
    exclude_ids: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    """Pick one vignette from *slot*, avoiding any id in *exclude_ids*.

    Falls back to the full slot pool if every candidate is excluded.
    Deterministic under a seeded rng.
    """
    candidates = [v for v in SCENARIO_VIGNETTES if v["slot"] == slot]
    usable = [v for v in candidates if v["id"] not in exclude_ids]
    pool = usable or candidates
    return rng.choice(pool)


# ---------------------------------------------------------------------------
# Power scoring and 6-option selection
# ---------------------------------------------------------------------------

# Weight per match surface.  Category matches get the most weight, then
# sub_category, then playstyle.  Case-insensitive on each side.
_WEIGHT_CATEGORY = 3
_WEIGHT_SUB_CATEGORY = 2
_WEIGHT_PLAYSTYLE = 1


def score_power(power: Any, tags: List[str]) -> int:
    """Score one V2 power against the tag bag."""
    if not tags:
        return 0
    lower_tags = {t.lower() for t in tags}
    score = 0
    if power.category and power.category.lower() in lower_tags:
        score += _WEIGHT_CATEGORY
    if getattr(power, "sub_category", "") and power.sub_category.lower() in lower_tags:
        score += _WEIGHT_SUB_CATEGORY
    for play in getattr(power, "playstyles", []) or []:
        if play.lower().strip(".") in lower_tags:
            score += _WEIGHT_PLAYSTYLE
    return score


def score_powers(powers: List[Any], tags: List[str]) -> List[Tuple[Any, int]]:
    """Return (power, score) pairs sorted high-to-low (stable ties)."""
    scored = [(p, score_power(p, tags)) for p in powers]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def pick_six(
    powers: List[Any],
    tags: List[str],
    rng: _random.Random,
    exclude_category: str = "",
) -> List[Any]:
    """Return 6 V2 powers: up to 4 top-weighted + fill with random from pool.

    *powers* is the full V2 catalog.  *exclude_category* drops every power
    with that category (used at scenario 2 to exclude primary's category).
    Duplicates are never returned.  If the eligible pool has fewer than 6
    powers, returns everything eligible.
    """
    eligible = [p for p in powers if p.category != exclude_category]
    if len(eligible) <= 6:
        return list(eligible)

    scored = score_powers(eligible, tags)
    top_weighted: List[Any] = []
    leftover: List[Any] = []
    for power, score in scored:
        if score > 0 and len(top_weighted) < 4:
            top_weighted.append(power)
        else:
            leftover.append(power)

    picked_ids = {p.id for p in top_weighted}
    remaining = [p for p in leftover if p.id not in picked_ids]
    fill_count = 6 - len(top_weighted)
    fillers = rng.sample(remaining, min(fill_count, len(remaining)))

    result = top_weighted + fillers
    # If weighted+fillers still short (no tag matched, tiny pool), top up.
    if len(result) < 6:
        pad = [p for p in eligible if p.id not in {x.id for x in result}]
        rng.shuffle(pad)
        result.extend(pad[: 6 - len(result)])
    return result[:6]


def score_power_combined(
    power: Any,
    desc_tags: List[str],
    reaction_tags: List[str],
    w_desc: int = 3,
    w_reaction: int = 2,
) -> int:
    """Combined score: personality (description) and gut instinct (reaction).

    Each source is independently scored against the power via score_power(),
    then weighted.  Description signals the player's baseline identity;
    reaction signals the instinctive move they just chose under pressure.
    Default weighting biases toward description, matching the design intent
    that powers express who the player already is, shaded by how they react.
    """
    return (
        w_desc * score_power(power, desc_tags)
        + w_reaction * score_power(power, reaction_tags)
    )


def pick_ten(
    powers: List[Any],
    desc_tags: List[str],
    reaction_tags: List[str],
    rng: _random.Random,
    w_desc: int = 3,
    w_reaction: int = 2,
    top_count: int = 6,
    filler_count: int = 4,
) -> List[Any]:
    """Return a slate of ten V2 powers for the pick-two power beat.

    Top *top_count* are the highest combined-scored candidates (desc × w_desc
    plus reaction × w_reaction).  Remaining *filler_count* are random draws
    from the rest of the pool.  No category exclusion — the player may pick
    two powers from the same category.  Duplicates never appear.  If the
    catalog is smaller than top_count + filler_count, returns everything.
    """
    total = top_count + filler_count
    eligible = list(powers)
    if len(eligible) <= total:
        return eligible

    scored = [
        (p, score_power_combined(p, desc_tags, reaction_tags, w_desc, w_reaction))
        for p in eligible
    ]
    scored.sort(key=lambda pair: pair[1], reverse=True)

    top_weighted: List[Any] = []
    leftover: List[Any] = []
    for power, score in scored:
        if score > 0 and len(top_weighted) < top_count:
            top_weighted.append(power)
        else:
            leftover.append(power)

    picked_ids = {p.id for p in top_weighted}
    remaining = [p for p in leftover if p.id not in picked_ids]
    fill = rng.sample(remaining, min(filler_count, len(remaining)))

    result = top_weighted + fill
    if len(result) < total:
        # Pool was under-weighted (no tag hits); top up from remaining eligible.
        pad = [p for p in eligible if p.id not in {x.id for x in result}]
        rng.shuffle(pad)
        result.extend(pad[: total - len(result)])
    return result[:total]


# ---------------------------------------------------------------------------
# Unified action vignette selection
# ---------------------------------------------------------------------------

def select_action_vignette(
    rng: _random.Random,
    exclude_ids: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    """Pick one onset-moment vignette for the single action scenario beat.

    Draws from the slot-1 pool (first-manifestation framings), since the
    new flow compresses power selection into a single cinematic beat where
    both abilities surface together.
    """
    candidates = list(_SLOT_1_VIGNETTES)
    usable = [v for v in candidates if v["id"] not in exclude_ids]
    pool = usable or candidates
    return rng.choice(pool)
