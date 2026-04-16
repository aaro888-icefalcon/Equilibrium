"""Scenario pool and tag-weighted power selection for session zero.

Two cinematic danger vignettes (slots 1 and 2) frame each of the power-
selection scenes.  The player responds freeform; the engine extracts tags
from their response, scores V2 powers against those tags, and returns the
top-4 weighted candidates plus 2 random fillers as the 6 choices.

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
    """Tag extraction for scene-0 self-description — uses both tables so
    keywords that only appear in the reaction table (e.g. 'run', 'fight')
    still contribute when they show up in a self-description."""
    tags = extract_tags(text, SELF_DESCRIPTION_KEYWORDS)
    for tag in extract_tags(text, REACTION_KEYWORDS):
        if tag not in tags:
            tags.append(tag)
    return tags


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
