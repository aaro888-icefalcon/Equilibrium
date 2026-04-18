"""The Seventh Avenue Onset vignette (OnsetScene data).

A single hand-authored vignette plays for every character.  Three
beats: attention (Beat 1), engagement (Beat 2), slate (pick 2 of 10).
Attention and engagement each offer three options; the player's picks
feed reaction_tags that bias the slate.  The slate phase reuses the
existing reaction-dominant weighting from AwakeningScene.
"""

from __future__ import annotations

from typing import Any, Dict, List


SEVENTH_AVENUE_FRAMING = (
    "Seventh Avenue, Manhattan. Three minutes past noon on a Tuesday "
    "that had not intended to be anything.\n\n"
    "Every engine on the block has stopped.  Not died — stopped, at "
    "the same instant, like a held breath.  The M20 bus is still "
    "rolling the last of its momentum toward 23rd.  The cabs are "
    "dark.  A pigeon three feet from your shoe keeps eating.  Down "
    "the block a woman in a red coat drops her phone; it does not "
    "shatter, it just lies there, no glow.\n\n"
    "Above the rooftops a news helicopter comes in wrong.  You hear "
    "the shape of it before you see it — the sound of a thing that "
    "is no longer held up.  Then you see it: the east side of the "
    "block across from the Fashion Institute, a rotor through a "
    "cornice, glass.  Someone screams the word *run* in a way that "
    "sounds like permission.\n\n"
    "Inside your chest something you have never felt turns on.  Not "
    "panic.  Under panic.  A pressure behind the sternum that was "
    "not there one second ago, and now is, and does not intend to "
    "go away.\n\n"
    "You have half a block of decisions.  The first is where to put "
    "your attention."
)


# Beat 1 — attention: where the character looks first.  Tags steer
# reaction_tags for the slate phase (cognitive/perceptive vs kinetic,
# etc).  Each option is one sentence diegetic + one-line tradeoff.
ATTENTION_OPTIONS: List[Dict[str, Any]] = [
    {
        "id": "attention_helicopter",
        "label": "The helicopter across the street — who's inside, who's under.",
        "tradeoff": "You miss the person in the bus.  You see the fall coming.",
        "tags": ["cognitive", "perceptive", "Investigator"],
    },
    {
        "id": "attention_bus",
        "label": "The M20 rolling dead — who's in it, what it's about to hit.",
        "tradeoff": "You lose the helicopter's trajectory.  Twenty meters, thirty people.",
        "tags": ["kinetic", "impact", "Brawler"],
    },
    {
        "id": "attention_self",
        "label": "The pressure under your sternum — what it is, what it wants.",
        "tradeoff": "People are dying while you look inward.  You will not be caught flat-footed.",
        "tags": ["cognitive", "perceptive", "paradoxic"],
    },
]


# Beat 2 — engagement: after attention, first motion.
ENGAGEMENT_OPTIONS: List[Dict[str, Any]] = [
    {
        "id": "engage_move",
        "label": "Close the distance.  Get hands on whoever you can reach.",
        "tradeoff": "Your body commits before your mind finishes.  You will touch something that cuts you.",
        "tags": ["kinetic", "velocity", "somatic", "Skirmisher"],
    },
    {
        "id": "engage_command",
        "label": "Take the block.  Voice first — tell people what to do.",
        "tradeoff": "You don't know these people.  They don't know you.  You find out if your voice carries.",
        "tags": ["cognitive", "dominant", "Controller"],
    },
    {
        "id": "engage_observe",
        "label": "Hold still.  Watch.  Learn the shape of what's happening before moving.",
        "tradeoff": "Someone dies in the seconds you spent reading the scene.  You see the next wave coming.",
        "tags": ["cognitive", "perceptive", "predictive", "Investigator"],
    },
]


ONSET_VIGNETTE = {
    "id": "onset_seventh_avenue",
    "framing": SEVENTH_AVENUE_FRAMING,
    "attention_options": ATTENTION_OPTIONS,
    "engagement_options": ENGAGEMENT_OPTIONS,
    "closing_summary": (
        "The next year measures itself.  Power is not a gift.  It is "
        "a weight that arrived when the engines stopped, and did not "
        "leave.  You begin it at tier 3 — three fingers' worth of it "
        "on a hand that was never ready to hold anything like it — "
        "and will grow to tier 5 if you live."
    ),
}
