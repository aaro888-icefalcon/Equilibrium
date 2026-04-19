"""Bridge scene — opening scene payload anchored by the urgent quest.

Flow:
  1. Engine builds a narrator_payload carrying the full CreationState + all
     5 quests + the urgent quest flagged for the opening scene + the
     already-generated backstory_prose (from QuestPickScene) for context.
  2. Narrator (Claude) returns a bridge_output JSON containing:
       - opening_scene: the frozen-tableau scene (150-400 words) that drops
         the player into the urgent quest
       - opening_scene_meta: ids referencing the urgent quest, its hook NPC,
         antagonist, location, and telegraphed bright line
       - hooked_npcs / mentioned_factions for the roster block
  3. Engine validates opening_scene_meta against the urgent quest's state.
  4. Engine writes the opening-scene artifacts to CreationState and exits
     session zero. The backstory_prose continues to live where it was
     stored by QuestPickScene.

This scene does not mutate QuestState. The quests are already registered by
QuestPickScene.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.character_factory import CreationState
from emergence.engine.quests.schema import Quest, QuestState


OPENING_SCENE_WORD_MIN = 150
OPENING_SCENE_WORD_MAX = 400


class BridgeOutputValidationError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Bridge output invalid:\n  - " + "\n  - ".join(errors))


class BridgeScene:
    scene_id: str = "bridge"
    register: str = "intimate"

    # ------------------------------------------------------------------
    # Phase 1: prepare narrator payload
    # ------------------------------------------------------------------

    def build_narrator_payload(
        self,
        state: CreationState,
        quest_state: QuestState,
    ) -> Dict[str, Any]:
        urgent = _find_urgent(quest_state)
        background = [q for q in quest_state.quests if q.is_background]
        if urgent is None:
            raise RuntimeError("no urgent quest registered; cannot bridge")
        if len(background) != 4:
            raise RuntimeError(f"expected 4 background quests, got {len(background)}")

        char_summary = {
            "name": state.name,
            "age_at_onset": state.age_at_onset,
            "species": state.species,
            "pre_emergence_location": state.region,
            "post_emergence_location": state.starting_location,
            "self_description": state.self_description,
            "attributes": {
                name: 6 + state.attribute_deltas.get(name, 0)
                for name in ("strength", "agility", "perception", "will", "insight", "might")
            },
            "skills": dict(state.skills),
            "powers": list(state.powers),
            "npcs": list(state.generated_npcs),
            "threats": list(state.threats),
            "job_pick": state.scene_choices.get("job_pick"),
            "post_onset_goal": state.scene_choices.get("post_onset_goal", ""),
            "goal_conflicts_with_job": bool(
                state.scene_choices.get("goal_conflicts_with_job", False)
            ),
            "goal_conflict_note": state.scene_choices.get("goal_conflict_note", ""),
        }

        # Flatten the bundle's NPCs to a lookup set for hook validation.
        bundle_npc_ids = {npc.get("npc_id") for npc in state.generated_npcs if npc.get("npc_id")}

        return {
            "task": "opening_scene_v1",
            "guidelines_docs": [
                "emergence/docs/opening_scene_guidelines.md",
                "emergence/setting/narration_style.md",
                "emergence/setting/narration.md",
            ],
            "character": char_summary,
            "urgent_quest": urgent.to_dict(),
            "background_quests": [q.to_dict() for q in background],
            "backstory_prose": state.scene_choices.get("backstory_prose", ""),
            "bundle_npc_ids": sorted(bundle_npc_ids),
            "opening_target_words": [OPENING_SCENE_WORD_MIN, OPENING_SCENE_WORD_MAX],
            "schema_hint": {
                "opening_scene": "str (150-400 words; the frozen tableau opening the urgent quest)",
                "opening_scene_meta": {
                    "primary_quest_id": "urgent quest id",
                    "antagonist_id": "proxy antagonist npc id (must match quest)",
                    "hook_npc_id": "in-frame NPC whose stake anchors the PC",
                    "location_id": "scene location",
                    "telegraph_bright_line_id": "id of the bright line the scene telegraphs",
                },
                "hooked_npcs": [
                    {
                        "npc_id": "must appear in bundle_npc_ids",
                        "relation": "mentor | coworker | rival | patron | contact | other",
                        "introduced_in": "backstory_q0..q3 | urgent | bridge_present_day",
                    }
                ],
                "mentioned_factions": ["faction_id", "..."],
            },
            "three_questions_gate": (
                "After reading the opening_scene, a reader must be able to answer: "
                "(1) what am I trying to do? (2) what happens if I fail? "
                "(3) what's running out? If any answer is unclear, rewrite."
            ),
        }

    # ------------------------------------------------------------------
    # Phase 2: validate bridge output
    # ------------------------------------------------------------------

    @staticmethod
    def validate_bridge_output(
        payload: Dict[str, Any],
        urgent_quest: Quest,
        bundle_npc_ids: Optional[set] = None,
    ) -> List[str]:
        errors: List[str] = []
        if not isinstance(payload, dict):
            return ["root: must be dict"]

        scene = payload.get("opening_scene") or ""
        if not isinstance(scene, str) or not scene.strip():
            errors.append("opening_scene: required non-empty string")
        else:
            wc = len(scene.split())
            if wc < OPENING_SCENE_WORD_MIN - 30 or wc > OPENING_SCENE_WORD_MAX + 100:
                errors.append(
                    f"opening_scene: word count {wc} outside "
                    f"[{OPENING_SCENE_WORD_MIN - 30}, {OPENING_SCENE_WORD_MAX + 100}]"
                )

        meta = payload.get("opening_scene_meta")
        if not isinstance(meta, dict):
            errors.append("opening_scene_meta: required dict")
        else:
            if meta.get("primary_quest_id") != urgent_quest.id:
                errors.append(
                    f"opening_scene_meta.primary_quest_id: must match urgent quest "
                    f"{urgent_quest.id!r} (got {meta.get('primary_quest_id')!r})"
                )
            expected_antagonist = urgent_quest.central_conflict.proxy_antagonist_id
            if meta.get("antagonist_id") != expected_antagonist:
                errors.append(
                    f"opening_scene_meta.antagonist_id: must match urgent quest's "
                    f"proxy antagonist {expected_antagonist!r}"
                )
            for req in ("hook_npc_id", "location_id", "telegraph_bright_line_id"):
                if not meta.get(req):
                    errors.append(f"opening_scene_meta.{req}: required")
            bl_id = meta.get("telegraph_bright_line_id")
            if bl_id and bl_id not in {bl.id for bl in urgent_quest.bright_lines}:
                errors.append(
                    f"opening_scene_meta.telegraph_bright_line_id: {bl_id!r} "
                    f"is not a bright line of the urgent quest"
                )

        # Structured relationship emissions. These let the engine render a
        # roster block after the opening scene without parsing prose.
        hooked = payload.get("hooked_npcs")
        if not isinstance(hooked, list):
            errors.append("hooked_npcs: required list")
        else:
            seen_hooks = set()
            for i, h in enumerate(hooked):
                prefix = f"hooked_npcs[{i}]"
                if not isinstance(h, dict):
                    errors.append(f"{prefix}: must be dict")
                    continue
                nid = h.get("npc_id")
                if not nid:
                    errors.append(f"{prefix}.npc_id: required")
                elif nid in seen_hooks:
                    errors.append(f"{prefix}.npc_id: duplicate {nid!r}")
                elif bundle_npc_ids is not None and nid not in bundle_npc_ids:
                    errors.append(
                        f"{prefix}.npc_id: {nid!r} not in bundle_npc_ids; "
                        f"the bridge can only hook NPCs present in the job bundle"
                    )
                else:
                    seen_hooks.add(nid)
                if not h.get("relation"):
                    errors.append(f"{prefix}.relation: required")
                if not h.get("introduced_in"):
                    errors.append(f"{prefix}.introduced_in: required")

        factions = payload.get("mentioned_factions")
        if not isinstance(factions, list):
            errors.append("mentioned_factions: required list (may be empty)")

        return errors

    # ------------------------------------------------------------------
    # Phase 3: apply
    # ------------------------------------------------------------------

    def apply_bridge_output(
        self,
        bridge_output: Dict[str, Any],
        state: CreationState,
        quest_state: QuestState,
    ) -> CreationState:
        urgent = _find_urgent(quest_state)
        if urgent is None:
            raise RuntimeError("no urgent quest to bridge into")
        bundle_npc_ids = {npc.get("npc_id") for npc in state.generated_npcs if npc.get("npc_id")}
        errors = self.validate_bridge_output(bridge_output, urgent, bundle_npc_ids)
        if errors:
            raise BridgeOutputValidationError(errors)
        state.scene_choices["opening_scene"] = bridge_output["opening_scene"]
        state.scene_choices["opening_scene_meta"] = dict(bridge_output["opening_scene_meta"])
        state.scene_choices["hooked_npcs"] = list(bridge_output.get("hooked_npcs", []))
        state.scene_choices["mentioned_factions"] = list(bridge_output.get("mentioned_factions", []))
        return state

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def phase(self, state: CreationState) -> str:
        if not state.scene_choices.get("opening_scene"):
            return "awaiting_narrator"
        return "complete"


def _find_urgent(quest_state: QuestState) -> Optional[Quest]:
    for q in quest_state.quests:
        if q.is_urgent:
            return q
    return None
