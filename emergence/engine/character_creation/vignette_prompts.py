"""Narrator prompt template for Year One vignettes.

The operator of Claude Code is the narrator.  This module produces a
single prompt string from a VignetteScaffold that the operator reads and
responds to with a VignetteOutput JSON object.  No external LLM call is
made by the engine — the engine only formats the prompt and validates
the operator's response.

Prompt sections (in order):
  1. Register directive — scene tone, per scaffold.stakes_register.
  2. World compaction — state snapshot: character, prior beats, reaction tags.
  3. Mechanical constraint — which slot is being bound, which options are live.
  4. Seeding requirements — minimums per seed type, pools to draw from,
                              forbidden terms (no game-mechanical jargon).
  5. Output format — the VignetteOutput JSON skeleton the operator must return.
  6. Register reminders — the anti-patterns from narration.md.
"""

from __future__ import annotations

from typing import List

from emergence.engine.character_creation.scaffolds import VignetteScaffold


_SECTION_1 = """\
# Vignette {index} — register directive

Time period: {time_period}.
Register: {stakes_register}.
Target prose length: 400-600 words.
Present three choices, each averaging 30-50 words.
Each choice ends with a one-line parenthetical giving the mechanical
outcome of that pick: the cast mode or rider being bound, and any
immediate cost.
"""

_SECTION_2 = """\
# World compaction

Region (if locked): {region}
Reaction tags so far: {reaction_tags}
Prior vignette beats:
{prior_summaries}
"""

_SECTION_3 = """\
# Mechanical constraint

You are binding the character's **{mechanical_slot}** for power id
`{power_id}`.  The three options available are:

{option_pool}

Each of your three choices MUST pick one of these option_ids.  You may
reuse an option_id across choices, OR map each choice to a different
option_id — your call as narrator.
"""

_SECTION_4 = """\
# Seeding requirements (per choice)

Every one of your three choices must attach a seed_bundle carrying, at
minimum:

{requirements}

Available pools to draw from:
  NPC archetypes: {npc_archetypes}
  Factions: {factions}
  Locations: {locations}
  Threat archetypes: {threats}
  Vow packages: {vow_packages}
  {region_outcomes_line}

Forbidden terms (the validator will reject these verbatim):
{forbidden}
"""

_SECTION_5 = '''\
# Output format

Return exactly one JSON object matching this shape:

```json
{{
  "schema_version": "1.0",
  "prose": "<400-600 words of vignette narration>",
  "choices": [
    {{
      "display_text": "<what the player sees as option 1>",
      "mechanical_binding": {{"slot": "{mechanical_slot}", "option_id": "<one of the option_ids above>"}},
      "mechanical_parenthetical": "<one-line mechanical outcome, non-empty, specific to this choice, NOT identical to the option base description>",
      "seed_bundle": {{
        "npcs": [{{"name": "<NPC name>", "archetype": "<archetype>", "standing": 0, "relation": "", "voice": ""}}],
        "locations": [{{"id": "<existing id>" , "is_starting": false}}],
        "factions": [{{"faction_id": "<faction id>", "standing_delta": 0, "heat_delta": 0, "note": ""}}],
        "threats": [{{"archetype": "<threat archetype id>", "name": "<display name>", "standing": -2, "source": ""}}],
        "vows": [{{"vow_id": "<vow id>", "target_npc": "", "goals": []}}],
        "region_outcome": null,
        "history_record": "<one-line narrative record>"
      }}
    }},
    {{"... two more choices ..." : true}}
  ]
}}
```

Each choice must stand alone.  The player picks ONE of the three; the
other two are discarded.  Make all three diegetically distinct.
'''

_SECTION_6 = """\
# Register reminders

Grounded simulation.  Stoic.  Tactile.  Unsentimental.  The narrator
observes; does not interpret.  Show through action, not interpretation.
Prose is plain and load-bearing.  Dialogue is terse.  Powers are
physical facts, not spectacle.

Do NOT:
- Use meta-mechanical language (hit points, dice, level, XP, game master).
- Frame violence heroically or with spectacle.
- Speak for the player character.  Describe the world; let them choose.
- Pad with adjectives.  Pick one specific detail, maybe two.
- Dump exposition.  Seed it through action, inference, and terse speech.
"""


def render_prompt(scaffold: VignetteScaffold, reaction_tags: List[str] | None = None) -> str:
    """Render the six-section operator prompt from *scaffold*."""
    reaction_tags = reaction_tags or []

    prior = scaffold.prior_vignette_summaries
    prior_text = "\n".join(f"  - {s}" for s in prior) if prior else "  (none yet)"

    option_pool_text = "\n".join(
        f"  - option_id `{o.option_id}`: {o.display}\n"
        f"      base: {o.base_description}"
        for o in scaffold.option_pool
    ) if scaffold.option_pool else "  (empty — character has no power configured; flag error)"

    req = scaffold.required_seeds
    req_lines: List[str] = []
    if req.min_npcs:        req_lines.append(f"  - ≥{req.min_npcs} NPC(s)")
    if req.min_locations:   req_lines.append(f"  - ≥{req.min_locations} location(s)")
    if req.min_factions:    req_lines.append(f"  - ≥{req.min_factions} faction delta(s)")
    if req.min_threats:     req_lines.append(f"  - ≥{req.min_threats} threat(s)")
    if req.min_vows:        req_lines.append(f"  - ≥{req.min_vows} vow(s)")
    if req.require_region_outcome:
        req_lines.append("  - region_outcome must be set (one of stay_nyc | displaced_to | traveled_to)")
    if req.require_is_starting:
        req_lines.append("  - exactly ONE of your three choices must flag a location with is_starting=true")
    if req.min_goals_from_vows:
        req_lines.append(f"  - total goals across vow entries must be ≥{req.min_goals_from_vows}")
    requirements_text = "\n".join(req_lines) if req_lines else "  (no minimums for this index)"

    if scaffold.seed_pools.region_outcomes:
        region_outcomes_line = (
            f"Region outcomes (V2 only, valid set): "
            f"{scaffold.seed_pools.region_outcomes}"
        )
    else:
        region_outcomes_line = ""

    return "\n".join([
        _SECTION_1.format(
            index=scaffold.index,
            time_period=scaffold.time_period,
            stakes_register=scaffold.stakes_register,
        ),
        _SECTION_2.format(
            region=scaffold.region or "(not yet locked)",
            reaction_tags=list(reaction_tags) or "(none)",
            prior_summaries=prior_text,
        ),
        _SECTION_3.format(
            mechanical_slot=scaffold.mechanical_slot,
            power_id=scaffold.power_id or "(no power configured)",
            option_pool=option_pool_text,
        ),
        _SECTION_4.format(
            requirements=requirements_text,
            npc_archetypes=scaffold.seed_pools.npc_archetypes,
            factions=[f["id"] for f in scaffold.seed_pools.factions],
            locations=[l["id"] for l in scaffold.seed_pools.locations],
            threats=scaffold.seed_pools.threats,
            vow_packages=[v.get("display", v.get("npc_archetype", ""))[:60]
                          for v in scaffold.seed_pools.vow_packages],
            region_outcomes_line=region_outcomes_line,
            forbidden=", ".join(scaffold.forbidden),
        ),
        _SECTION_5.format(mechanical_slot=scaffold.mechanical_slot),
        _SECTION_6,
    ])
