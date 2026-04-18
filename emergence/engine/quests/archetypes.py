"""Quest archetype library — 18 definitions.

Each archetype is a schematic skeleton, not a fully populated quest. Claude
reads an archetype definition plus the character's job bundle and composes a
fully-populated Quest instance, which is then validated by
`emergence.engine.quests.schema.validate_quest`.

An Archetype provides:
- goal_template          — a fill-in-the-blank verb-the-noun sentence
- macrostructure_shape   — direction + default tick_triggers + threshold semantics
- bright_line_templates  — canonical failure frames the archetype admits
- proxy_antagonist_role  — what kind of bundle entity fills the antagonist slot
- scope_default          — recommended expected_scenes and session_equivalents
- success_predicate_hint — a template shape for success_condition
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class ArchetypeBrightLineTemplate:
    id_suffix: str
    description_template: str
    check_condition_template: Dict[str, Any]
    telegraph_hint: str


@dataclass(frozen=True)
class Archetype:
    id: str
    display_name: str
    goal_template: str
    macrostructure_direction: str  # "decrement" | "increment"
    macrostructure_variable_hint: str
    default_tick_triggers: Tuple[str, ...]
    bright_line_templates: Tuple[ArchetypeBrightLineTemplate, ...]
    proxy_antagonist_role: str  # "rival" | "threat" | "faction_contact" | "environmental"
    scope_default_scenes: int = 3
    scope_default_sessions: float = 1.0
    success_predicate_hint: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "goal_template": self.goal_template,
            "macrostructure_direction": self.macrostructure_direction,
            "macrostructure_variable_hint": self.macrostructure_variable_hint,
            "default_tick_triggers": list(self.default_tick_triggers),
            "bright_line_templates": [
                {
                    "id_suffix": bl.id_suffix,
                    "description_template": bl.description_template,
                    "check_condition_template": dict(bl.check_condition_template),
                    "telegraph_hint": bl.telegraph_hint,
                }
                for bl in self.bright_line_templates
            ],
            "proxy_antagonist_role": self.proxy_antagonist_role,
            "scope_default_scenes": self.scope_default_scenes,
            "scope_default_sessions": self.scope_default_sessions,
            "success_predicate_hint": dict(self.success_predicate_hint),
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Canonical 18 archetypes
# ---------------------------------------------------------------------------

# Shared bright-line templates reused across archetypes.
_BL_PC_CAPTURED = ArchetypeBrightLineTemplate(
    id_suffix="pc_captured",
    description_template="PC is captured by {antagonist_faction}",
    check_condition_template={"type": "pc_status", "status": "captured"},
    telegraph_hint="a jurisdiction's enforcers closing routes, checkpoints visible in framing",
)

_BL_DEADLINE = ArchetypeBrightLineTemplate(
    id_suffix="deadline_elapses",
    description_template="Deadline elapses with goal unmet",
    check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
    telegraph_hint="visible time marker — bell, shift change, tide, sunset, convoy ETA",
)


ARCHETYPES: Tuple[Archetype, ...] = (
    Archetype(
        id="extraction",
        display_name="Extraction",
        goal_template="Get [target] out of [hostile zone] before [deadline]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="hours_until_sweep | minutes_until_lockdown | miles_to_perimeter",
        default_tick_triggers=("world_pulse", "travel_segment", "rest_action", "scene_close"),
        bright_line_templates=(
            _BL_DEADLINE,
            ArchetypeBrightLineTemplate(
                id_suffix="target_dies",
                description_template="{target_name} dies before extraction",
                check_condition_template={
                    "type": "npc_status",
                    "npc_id": "{target_npc_id}",
                    "status": "dead",
                },
                telegraph_hint="target's injury/condition visible in opening; worsens on failure to act",
            ),
            _BL_PC_CAPTURED,
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=3,
        success_predicate_hint={
            "type": "and",
            "predicates": [
                {"type": "npc_status", "npc_id": "{target_npc_id}", "status": "extracted"},
                {"type": "pc_location_not", "location_id": "{hostile_zone_id}"},
            ],
        },
    ),
    Archetype(
        id="protection",
        display_name="Protection",
        goal_template="Keep [asset] [operating/alive] through [duration]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="days_remaining | shifts_remaining | market_days_left",
        default_tick_triggers=("world_pulse", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="asset_destroyed",
                description_template="{asset_name} destroyed or closed",
                check_condition_template={
                    "type": "npc_status",
                    "npc_id": "{asset_npc_id}",
                    "status": "dead",
                },
                telegraph_hint="asset's fragility visible — recent damage, rival pressure, threats",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="pc_exiled",
                description_template="PC loses standing to work in {district}",
                check_condition_template={
                    "type": "faction_standing",
                    "faction_id": "{patron_faction_id}",
                    "op": "<=",
                    "value": -2,
                },
                telegraph_hint="patron's expectation stated in opening",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="investigation",
        display_name="Investigation",
        goal_template="Identify [unknown] before [deadline]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="days_until_cull | hours_to_hearing",
        default_tick_triggers=("world_pulse", "scene_close", "resolve_action_success"),
        bright_line_templates=(
            _BL_DEADLINE,
            ArchetypeBrightLineTemplate(
                id_suffix="wrong_name_given",
                description_template="Wrong name given under pressure",
                check_condition_template={"type": "pc_status", "status": "accused_false"},
                telegraph_hint="patron's demand explicit: a name, not a theory",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
        notes="progress_track fills as investigative scenes resolve; at full, the player names the target.",
    ),
    Archetype(
        id="recovery",
        display_name="Recovery",
        goal_template="Retrieve [object] from [location] before [rival/event]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="rival_progress | event_countdown",
        default_tick_triggers=("world_pulse", "travel_segment", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="rival_recovers_first",
                description_template="{rival_name} recovers the object first",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="rival's activity visible — caravan on road, crew assembling",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
        success_predicate_hint={
            "type": "and",
            "predicates": [
                {"type": "pc_status", "status": "carries_object"},
                {"type": "pc_location_not", "location_id": "{target_location_id}"},
            ],
        },
    ),
    Archetype(
        id="evacuation",
        display_name="Evacuation",
        goal_template="Move [group] from [source] to [destination] before [threat arrives]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="miles_until_threat | hours_until_overrun",
        default_tick_triggers=("world_pulse", "travel_segment", "rest_action"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="group_scatters",
                description_template="Group scatters; evacuation fails",
                check_condition_template={"type": "pc_status", "status": "group_lost"},
                telegraph_hint="group's cohesion visibly fragile — a child crying, an elder tiring",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="threat_overruns",
                description_template="Threat reaches group before destination",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="distant smoke, distant engines, distant voices — the threat's advance",
            ),
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=4,
    ),
    Archetype(
        id="sabotage",
        display_name="Sabotage",
        goal_template="Disable [target] before [deployment]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="hours_until_deployment | days_until_shipment",
        default_tick_triggers=("world_pulse", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="deployment_fires",
                description_template="Target deploys before sabotage completes",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="preparation cues — crates being loaded, crews assembling, a scheduled moment",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="discovered_mid_op",
                description_template="PC discovered mid-operation",
                check_condition_template={"type": "pc_status", "status": "exposed"},
                telegraph_hint="guards visible, patrol patterns implied, surveillance ambient",
            ),
        ),
        proxy_antagonist_role="faction_contact",
        scope_default_scenes=3,
    ),
    Archetype(
        id="witness",
        display_name="Witness",
        goal_template="Deliver [testimony] to [authority] before [silencer]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="hours_until_hearing_closes | miles_to_authority",
        default_tick_triggers=("world_pulse", "travel_segment", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="session_closes",
                description_template="Authority session closes before testimony delivered",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="the authority's schedule stated — court opens once, a council sits tomorrow",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="silencer_arrives",
                description_template="{silencer_name} reaches the witness",
                check_condition_template={
                    "type": "npc_status",
                    "npc_id": "{witness_npc_id}",
                    "status": "dead",
                },
                telegraph_hint="the silencer's proxies visible — a watcher at a gate, a name asked at an inn",
            ),
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=3,
    ),
    Archetype(
        id="verification",
        display_name="Verification",
        goal_template="Confirm [claim] before [decision deadline]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="hours_until_decision | days_until_vote",
        default_tick_triggers=("world_pulse", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="decision_made_unverified",
                description_template="Decision made on unverified claim",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="the decision venue visible — a council chamber, a muster line, a ledger page",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="hunt",
        display_name="Hunt",
        goal_template="Find [target] before they [vanish/act]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="target_progress | hours_before_target_acts",
        default_tick_triggers=("world_pulse", "travel_segment", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="target_vanishes",
                description_template="{target_name} disappears beyond PC's reach",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="trail cues — tracks fading, a contact last seen yesterday, a shop closed yesterday",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="target_acts",
                description_template="{target_name} completes their own agenda first",
                check_condition_template={"type": "npc_status", "npc_id": "{target_npc_id}", "status": "acted"},
                telegraph_hint="target's intent stated — what they'll do if found too late",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="elimination",
        display_name="Elimination",
        goal_template="Remove [target] before [escalation]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="days_until_escalation | hours_until_reinforcement",
        default_tick_triggers=("world_pulse", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="target_escalates",
                description_template="{target_name} becomes untouchable",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="target's guard schedule visible, new protection arriving, a summit soon",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="target_escapes",
                description_template="{target_name} leaves the region",
                check_condition_template={"type": "npc_status", "npc_id": "{target_npc_id}", "status": "fled"},
                telegraph_hint="movements implied — packing, bookings, farewells",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="negotiation",
        display_name="Negotiation",
        goal_template="Broker [deal] before [rival closes / parties break]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="parties_patience | rival_progress",
        default_tick_triggers=("world_pulse", "scene_close", "resolve_action_failure"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="rival_closes_first",
                description_template="Rival brokers the deal first",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="rival's agents visible at the table",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="impasse",
                description_template="Parties' patience exhausted; talks collapse",
                check_condition_template={"type": "pc_status", "status": "talks_collapsed"},
                telegraph_hint="tempers visible — a party already threatening to leave",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="ceremony",
        display_name="Ceremony",
        goal_template="Perform [ritual] at [location] by [window]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="hours_until_window | minutes_until_alignment",
        default_tick_triggers=("world_pulse", "travel_segment", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="window_passes",
                description_template="Ritual window passes",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="astronomical / seasonal / schedule cue — the moon, the festival, the bell",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="disruption",
                description_template="Ritual disrupted mid-performance",
                check_condition_template={"type": "pc_status", "status": "ritual_broken"},
                telegraph_hint="opponents visibly hostile to the ritual",
            ),
        ),
        proxy_antagonist_role="faction_contact",
        scope_default_scenes=3,
    ),
    Archetype(
        id="infiltration",
        display_name="Infiltration",
        goal_template="Enter [location] and exit with [objective] before alarm",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="alarm_budget | patrol_cycles_remaining",
        default_tick_triggers=("scene_close", "resolve_action_failure"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="alarm_tripped",
                description_template="Alarm tripped before extraction",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="guard density, sensor placement, shift changes visible",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="objective_unobtained",
                description_template="PC exits without the objective",
                check_condition_template={"type": "pc_status", "status": "empty_handed"},
                telegraph_hint="objective's location specified and its guards described",
            ),
        ),
        proxy_antagonist_role="faction_contact",
        scope_default_scenes=3,
    ),
    Archetype(
        id="deception",
        display_name="Deception",
        goal_template="Sustain [false identity] through [event]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="exposure_budget | event_scenes_remaining",
        default_tick_triggers=("scene_close", "resolve_action_failure"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="exposure",
                description_template="False identity exposed",
                check_condition_template={"type": "pc_status", "status": "exposed"},
                telegraph_hint="watchers in the scene, people who know the real name or face",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="event_fails_without_cover",
                description_template="Event concludes without the cover doing its work",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="the event's agenda visible — what the cover has to achieve within it",
            ),
        ),
        proxy_antagonist_role="rival",
        scope_default_scenes=3,
    ),
    Archetype(
        id="reinforcement",
        display_name="Reinforcement",
        goal_template="Reach [ally] at [location] before they fall",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="ally_survival_clock | miles_to_position",
        default_tick_triggers=("world_pulse", "travel_segment", "rest_action"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="ally_falls",
                description_template="{ally_name}'s position falls before arrival",
                check_condition_template={"type": "npc_status", "npc_id": "{ally_npc_id}", "status": "dead"},
                telegraph_hint="ally's messages stop arriving; smoke visible on horizon",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="arrival_too_late",
                description_template="PC arrives after position falls",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="distance stated, pace required, weather unfavorable",
            ),
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=3,
    ),
    Archetype(
        id="containment",
        display_name="Containment",
        goal_template="Stop [spread] before [threshold]",
        macrostructure_direction="increment",
        macrostructure_variable_hint="infection_count | blocks_compromised | days_of_spread",
        default_tick_triggers=("world_pulse", "scene_close"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="threshold_crossed",
                description_template="Spread exceeds threshold",
                check_condition_template={"type": "macrostructure", "op": ">=", "value": 0},
                telegraph_hint="spread rate visible — fresh cases, widening quarantine, rising tally",
            ),
        ),
        proxy_antagonist_role="environmental",
        scope_default_scenes=3,
    ),
    Archetype(
        id="counter_assault",
        display_name="Counter-Assault",
        goal_template="Repel [incursion] before [objective falls]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="defense_clock | waves_until_breach",
        default_tick_triggers=("world_pulse", "scene_close", "combat_round_over_threshold"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="objective_falls",
                description_template="Defended objective falls to incursion",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="defender numbers visible, wall integrity audible, reinforcements' ETA stated",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="defense_collapses",
                description_template="Defense line collapses and retreat is forced",
                check_condition_template={"type": "pc_status", "status": "retreated"},
                telegraph_hint="defender morale visible, commanders arguing, position marginal",
            ),
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=4,
    ),
    Archetype(
        id="pilgrimage",
        display_name="Pilgrimage",
        goal_template="Reach [destination] before [catch-up threat]",
        macrostructure_direction="decrement",
        macrostructure_variable_hint="miles_of_lead | days_ahead_of_pursuit",
        default_tick_triggers=("world_pulse", "travel_segment", "rest_action"),
        bright_line_templates=(
            ArchetypeBrightLineTemplate(
                id_suffix="pursuit_catches",
                description_template="Pursuit catches PC on the road",
                check_condition_template={"type": "macrostructure", "op": "<=", "value": 0},
                telegraph_hint="pursuit cues — horses heard, a signal fire answered behind",
            ),
            ArchetypeBrightLineTemplate(
                id_suffix="destination_closes",
                description_template="Destination closes to new arrivals",
                check_condition_template={"type": "pc_location_not", "location_id": "{destination_id}"},
                telegraph_hint="destination's gate schedule stated; a festival ending, a season turning",
            ),
        ),
        proxy_antagonist_role="threat",
        scope_default_scenes=4,
    ),
)


def get_archetype(archetype_id: str) -> Archetype:
    for a in ARCHETYPES:
        if a.id == archetype_id:
            return a
    raise KeyError(f"unknown archetype: {archetype_id!r}")


def list_archetypes() -> List[Dict[str, Any]]:
    return [a.to_dict() for a in ARCHETYPES]
