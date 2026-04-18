"""Quest pick scene — AI generates 8 quests, narrator picks 4 for backstory,
player picks 1 urgent from the remaining 4.

Flow:
  1. Engine builds a narrator_payload with character + bundle + archetype catalog.
  2. Narrator (Claude) returns a quest_output JSON containing:
       - 8 full Quest objects
       - a list of 4 ids flagged as "backstory" (narrator's pick)
  3. Engine validates each quest with `validate_quest`. Up to 3 regen attempts.
  4. Engine splits: 4 background quests into QuestState.quests with
     is_background=True; remaining 4 presented to player.
  5. Player picks 1 urgent from the 4 remaining; engine adds it with
     is_urgent=True.

Final state after the scene:
  - QuestState.quests holds exactly 5 quests (4 background + 1 urgent)
"""

from __future__ import annotations

import random as _random
from typing import Any, Dict, List, Optional

from emergence.engine.character_creation.character_factory import (
    CharacterFactory,
    CreationState,
)
from emergence.engine.quests.archetypes import list_archetypes
from emergence.engine.quests.schema import (
    Quest,
    QuestState,
    QuestValidationError,
    validate_quest,
    validate_quest_set,
)


QUEST_CARDS_TOTAL = 8
QUEST_BACKGROUND_COUNT = 4
QUEST_URGENT_COUNT = 1  # player picks exactly one
MAX_REGEN_ATTEMPTS = 3


class QuestOutputValidationError(ValueError):
    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("Quest output invalid:\n  - " + "\n  - ".join(errors))


class QuestPickScene:
    scene_id: str = "quest_pick"
    register: str = "standard"

    # ------------------------------------------------------------------
    # Phase 1: prepare payload for narrator
    # ------------------------------------------------------------------

    def build_narrator_payload(self, state: CreationState) -> Dict[str, Any]:
        job_card = state.scene_choices.get("job_pick")
        if not job_card:
            raise RuntimeError("job not yet picked; cannot generate quests")

        char_summary = {
            "name": state.name,
            "age_at_onset": state.age_at_onset,
            "species": state.species,
            "starting_location": state.starting_location,
            "self_description": state.self_description,
            "attributes": {
                name: 6 + state.attribute_deltas.get(name, 0)
                for name in ("strength", "agility", "perception", "will", "insight", "might")
            },
            "skills": dict(state.skills),
            "powers": [
                {
                    "power_id": p.get("power_id"),
                    "name": p.get("name"),
                    "category": p.get("category"),
                    "sub_category": p.get("sub_category"),
                }
                for p in state.powers
            ],
            "npcs": list(state.generated_npcs),
            "threats": list(state.threats),
        }

        return {
            "task": "quest_generate_v1",
            "guidelines_doc": "emergence/docs/quest_design_guidelines.md",
            "character": char_summary,
            "job_card": job_card,
            "archetype_catalog": list_archetypes(),
            "cards_required": QUEST_CARDS_TOTAL,
            "background_count": QUEST_BACKGROUND_COUNT,
            "urgent_offer_count": QUEST_CARDS_TOTAL - QUEST_BACKGROUND_COUNT,
            "regen_allowed": MAX_REGEN_ATTEMPTS,
            "schema_hint": {
                "quests": "list of 8 validated Quest JSON objects (see quests/schema.py)",
                "backstory_ids": "list of 4 quest ids flagged as backstory (narrator's pick)",
            },
        }

    # ------------------------------------------------------------------
    # Phase 2: validate quest output
    # ------------------------------------------------------------------

    @staticmethod
    def validate_quest_output(payload: Dict[str, Any]) -> List[str]:
        """Structural + per-quest validation."""
        errors: List[str] = []
        if not isinstance(payload, dict):
            return ["root: must be dict"]
        quests = payload.get("quests")
        if not isinstance(quests, list):
            return ["quests: required list"]
        if len(quests) != QUEST_CARDS_TOTAL:
            errors.append(f"quests: must contain exactly {QUEST_CARDS_TOTAL} (got {len(quests)})")
        backstory_ids = payload.get("backstory_ids")
        if not isinstance(backstory_ids, list) or len(backstory_ids) != QUEST_BACKGROUND_COUNT:
            errors.append(
                f"backstory_ids: must be list of {QUEST_BACKGROUND_COUNT} ids "
                f"(got {backstory_ids!r})"
            )

        # Per-quest validation + uniqueness
        seen_ids: set = set()
        for i, q_dict in enumerate(quests):
            prefix = f"quests[{i}]"
            if not isinstance(q_dict, dict):
                errors.append(f"{prefix}: must be dict")
                continue
            qid = q_dict.get("id")
            if not qid:
                errors.append(f"{prefix}.id: required")
            elif qid in seen_ids:
                errors.append(f"{prefix}.id: duplicate {qid!r}")
            else:
                seen_ids.add(qid)
            try:
                q = Quest.from_dict(q_dict)
            except Exception as exc:
                errors.append(f"{prefix}: failed to parse ({type(exc).__name__}: {exc})")
                continue
            per_errs = validate_quest(q)
            for e in per_errs:
                errors.append(f"{prefix}: {e}")

        # backstory_ids must reference valid quest ids
        if isinstance(backstory_ids, list):
            for bid in backstory_ids:
                if bid not in seen_ids:
                    errors.append(f"backstory_ids: {bid!r} not found among quests")

        # Simulate is_urgent=True on each non-backstory quest and verify it
        # passes urgent-quest validation. This catches tactical-verb and
        # physical_danger mistakes before the player picks.
        if isinstance(backstory_ids, list) and isinstance(quests, list):
            bset = set(backstory_ids)
            for i, q_dict in enumerate(quests):
                if not isinstance(q_dict, dict) or q_dict.get("id") in bset:
                    continue
                try:
                    sim = Quest.from_dict({**q_dict, "is_urgent": True, "is_background": False})
                except Exception:
                    continue
                for e in validate_quest(sim):
                    if "is_urgent=True" in e or "TACTICAL_VERBS" in e:
                        errors.append(f"quests[{i}] (urgent-offer): {e}")

        # Backstory quests must span >= 3 distinct conflict_modes. Simulate
        # is_background=True on them and run the set-level validator.
        if isinstance(backstory_ids, list) and isinstance(quests, list):
            bset = set(backstory_ids)
            bg_objs: List[Quest] = []
            for q_dict in quests:
                if isinstance(q_dict, dict) and q_dict.get("id") in bset:
                    try:
                        bg_objs.append(Quest.from_dict({**q_dict, "is_background": True, "is_urgent": False}))
                    except Exception:
                        continue
            if bg_objs:
                # Include a placeholder urgent so validate_quest_set's urgent-count
                # check doesn't spuriously fire.
                placeholder = Quest(id="__placeholder__", archetype="x", goal="Extract it now",
                                    is_urgent=True)
                set_errors = validate_quest_set(bg_objs + [placeholder])
                for e in set_errors:
                    if "conflict_modes" in e:
                        errors.append(f"backstory set: {e}")

        return errors

    # ------------------------------------------------------------------
    # Phase 3: split background vs offer
    # ------------------------------------------------------------------

    def store_quest_output(
        self,
        quest_output: Dict[str, Any],
        state: CreationState,
    ) -> CreationState:
        errors = self.validate_quest_output(quest_output)
        if errors:
            raise QuestOutputValidationError(errors)
        quests = quest_output["quests"]
        backstory_ids = set(quest_output["backstory_ids"])
        state.scene_choices["quest_pool"] = list(quests)
        state.scene_choices["quest_backstory_ids"] = list(backstory_ids)
        state.scene_choices["quest_urgent_offer"] = [
            q for q in quests if q["id"] not in backstory_ids
        ]
        return state

    # ------------------------------------------------------------------
    # Phase 4: player picks urgent; apply to QuestState
    # ------------------------------------------------------------------

    def apply_urgent_pick(
        self,
        pick_index: int,
        state: CreationState,
        factory: CharacterFactory,
        rng: _random.Random,
        quest_state: Optional[QuestState] = None,
    ) -> QuestState:
        """Apply the player's urgent pick. Returns a populated QuestState.

        All 5 quests (4 background + 1 urgent) are appended to QuestState.quests
        via validated init. The urgent quest carries is_urgent=True; background
        quests carry is_background=True.
        """
        offer = state.scene_choices.get("quest_urgent_offer") or []
        backstory = state.scene_choices.get("quest_backstory_ids") or []
        pool = state.scene_choices.get("quest_pool") or []
        if not offer or not pool:
            raise RuntimeError("quest output not stored; call store_quest_output first")
        if pick_index < 0 or pick_index >= len(offer):
            raise ValueError("urgent pick index out of range")

        urgent_id = offer[pick_index]["id"]
        quest_state = quest_state or QuestState()

        # Import here to avoid circular import at module load.
        from emergence.engine.quests.quest import init as quest_init

        for q_dict in pool:
            flagged = dict(q_dict)
            if flagged["id"] == urgent_id:
                flagged["is_urgent"] = True
                flagged["is_background"] = False
            elif flagged["id"] in backstory:
                flagged["is_urgent"] = False
                flagged["is_background"] = True
            else:
                # Discarded: not selected by narrator, not picked by player.
                continue
            try:
                quest_init(quest_state, flagged)
            except QuestValidationError as exc:
                raise QuestOutputValidationError(exc.errors) from exc

        state.scene_choices["quest_urgent_id"] = urgent_id
        return quest_state

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def phase(self, state: CreationState) -> str:
        if not state.scene_choices.get("quest_pool"):
            return "awaiting_narrator"
        if not state.scene_choices.get("quest_urgent_id"):
            return "awaiting_player_pick"
        return "complete"
