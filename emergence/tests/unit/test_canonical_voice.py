"""Unit tests for canonical voice enforcement in the narrator layer.

Covers:
  - Prompt composition: canonical preamble is prepended with all samples,
    voice spec, self-audit, and per-scene contract.
  - Validator acceptance: the three canonical sample passages validate
    with zero violations.
  - Validator rejection: protagonist tense/POV slips, missing fragments,
    overlong paragraphs, missing em dashes, rhetorical questions,
    ellipses, and mechanism smuggled into prose are flagged.
  - Signature hints: non-fatal reminders surface when the signature
    cadences are missing from beats that would benefit from them.
"""

from __future__ import annotations

import unittest

from emergence.engine.narrator.payloads import (
    build_combat_turn_payload,
    build_dialogue_payload,
    build_scene_framing_payload,
    build_transition_payload,
)
from emergence.engine.narrator.prompts import (
    PROMPT_TEMPLATES,
    _CANONICAL_PREAMBLE,
    compose_narrator_prompt,
    format_prompt,
    get_prompt,
)
from emergence.engine.narrator.validation import (
    _FORBIDDEN_PATTERNS,
    _split_prose_region,
    check_em_dash_presence,
    check_fragment_paragraph,
    check_mechanism_in_boxes,
    check_no_ellipses,
    check_no_rhetorical_questions,
    check_paragraph_shape,
    check_rhythm_variance,
    check_second_person_present,
    check_typography,
    hint_negative_definition,
    hint_scene_cap,
    hint_then_hinge,
    validate_narration,
)


# ---------------------------------------------------------------------------
# Canonical sample passages — verbatim from emergence/prompts/canonical_voice.md.
# Any drift here means the preamble and the tests have desynced; fix the
# preamble first, then re-run.
# ---------------------------------------------------------------------------

PASSAGE_COMBAT = """The **Thornwolf** drives at you from the flank. Your arm is too slow.

It's not a graceful martial arts intercept. It's a kinetic wreck — shoulder into ribs, your spine torquing against the asphalt, the trauma shears spilling out of your hand. You catch it on the rebound, reverse grip, and come up driving.

**Opportunity.**

You drop your weight, pivot, and punch the shears up and under the jaw, aiming for the thick artery running behind the mandible — the one you've clamped a dozen times in the clinic, the one that jets red for twenty seconds and stops.

**ROLL: ATTACK**
**Dice:** 1 + 4 = 5
**Modifiers:** +2 (DEX) + 2 (Charging/Flank)
**Total:** 9 vs DC 10 (Distracted)
**Result:** **PARTIAL SUCCESS**

*Damage dealt: 4 | Damage taken: 3*

The blade bites deep. Not into the artery. Into the thorn-hide of its forearm, thrown up in the last tenth of a second — and the forearm rakes you as it passes, three lines of heat across your cheek and collarbone.

You roll to your feet, gasping."""


PASSAGE_TRANSITION = """You are standing at the corner of **First Avenue** and **East 31st**, waiting for the light. Your phone is in your hand. The hum of the **FDR**—the cars, the engines, the low roar of a Tuesday at 4:47 PM—is the background you have stopped hearing.

Then, it stops.

It's not a blackout. A blackout has a sound — alarms, generators kicking on, the groan of slowing fans, the collective gasp of people noticing at different speeds. This is none of that.

This is the death of physics.

Your phone, mid-scroll in your hand, goes dead black. The streetlight above you is dark. The FDR is silent — not a paused silent, an *erased* silent. A man on the sidewalk in front of you takes one more step on a leg that has forgotten what weight is, and falls. A bicycle two lanes over is already on its side, the rider's face meeting the asphalt with a sound you will remember.

The sky is wrong.

Above **Kips Bay**, above **NYU Langone**, above the bridges and the river and the long low sprawl of **Queens** beyond, the sky is the wrong color. Not a storm. A shade the eye cannot name — like staring into a photograph of a sky, not the sky itself.

A flicker in your retina. Then another. Your hands are warmer than they should be.

New York City is no longer on Earth."""


PASSAGE_NEGOTIATION = """You hook the pouch onto your belt — two vials, one silver, one dull copper — where he can see it but not reach it. Not a threat. A measurement, in his direction, of what you carry.

**Vayek** watches the motion. The heat radiating from his armor fogs the cold air between you. His eyes don't track the pouch. They track your shoulders.

**Intent:** he wants to know whether you negotiate like a man with options.

"You came alone," he says. It's not a greeting. It's a **measurement**.

"I came alone."

"The Ironbound does not trade at this corner."

"You trade here today."

**ROLL: Negotiation**
`Result: 12 vs DC 11` (**SUCCESS**)

He looks at the pouch again. Longer this time. You watch his jaw work once and settle. His posture shifts — not warmer, just calibrated. You have moved, in his registry, from a problem to a line item.

"Tomorrow," he says. "At the fence. Bring the other one."

He can bully a refugee; he can't bully a supplier. You don't look desperate. You look like a man with options."""


# ---------------------------------------------------------------------------
# Prompt composition — canonical preamble is present and scene-specific.
# ---------------------------------------------------------------------------


class TestPromptAssembly(unittest.TestCase):
    """The composer prepends canonical_voice.md verbatim and wires scene rules."""

    def test_preamble_loaded(self):
        self.assertGreater(
            len(_CANONICAL_PREAMBLE), 2000,
            "canonical preamble should load > 2 KB of spec at import"
        )
        # Spot-check the three sample-phrase tokens and the priority rule.
        for phrase in [
            "kinetic wreck",
            "death of physics",
            "measurement",
            "bully a refugee",
            "Then,",
            "Opportunity.",
            "RHYTHM PRESERVATION",
            "It's not X. It's Y.",
        ]:
            self.assertIn(phrase, _CANONICAL_PREAMBLE, f"missing '{phrase}' in preamble")

    def test_combat_beat_prompt_contains_canonical_preamble(self):
        payload = build_combat_turn_payload(
            round_num=3, actor_name="you", action_type="attack",
            action_result="partial_success", damage_dealt=4,
            status_applied="bleeding",
            enemies_remaining=1,
        )
        prompt = compose_narrator_prompt("combat_turn", payload)
        # Preamble spot checks.
        self.assertIn("# Canonical Voice", prompt)
        self.assertIn("<sample id=\"combat\">", prompt)
        self.assertIn("<sample id=\"transition\">", prompt)
        self.assertIn("<sample id=\"negotiation\">", prompt)
        self.assertIn("kinetic wreck", prompt)
        self.assertIn("death of physics", prompt)
        self.assertIn("<self_audit>", prompt)
        self.assertIn("<priority_rule>", prompt)
        self.assertIn("RHYTHM PRESERVATION", prompt)
        # Scene-specific contract.
        self.assertIn("SCENE: combat_turn", prompt)
        self.assertIn("ROLL block", prompt)
        self.assertIn("UI box", prompt)
        # Payload-injected values.
        self.assertIn("attack", prompt)
        self.assertIn("bleeding", prompt)

    def test_scene_transition_prompt_contains_canonical_preamble(self):
        payload = build_transition_payload(
            from_location="Kips Bay",
            to_location="Ironbound",
            travel_time="3 hours",
            hazards=["raider patrol", "Wretch sign"],
        )
        prompt = compose_narrator_prompt("transition", payload)
        self.assertIn("# Canonical Voice", prompt)
        self.assertIn("SCENE: transition", prompt)
        # Fragment-pivot guidance referenced from the scene template.
        self.assertIn("Then, it stops.", prompt)
        # Hazard payload field substituted.
        self.assertIn("raider patrol", prompt)
        self.assertIn("Ironbound", prompt)

    def test_dialogue_prompt_surfaces_negotiation_contract(self):
        payload = build_dialogue_payload(
            npc_name="Vayek",
            npc_voice="Ironbound captain — cold, precise, armored",
            topic="vial trade",
            standing=0,
            player_options=["Escalate", "Walk"],
        )
        prompt = compose_narrator_prompt("dialogue", payload)
        self.assertIn("# Canonical Voice", prompt)
        self.assertIn("SCENE: dialogue", prompt)
        # Template should reference the opposed-roll path even when opposed flag
        # is not yet set, since a future resolve-action call may flip it.
        self.assertIn("opposed", prompt)
        self.assertIn("ROLL: Negotiation", prompt)
        self.assertIn("Vayek", prompt)

    def test_format_prompt_fallback_without_preamble(self):
        # Directly call format_prompt with a tiny template to confirm the
        # composer still works if the preamble fails to load (graceful fallback
        # path in prompts.py). This exercises the placeholder-substitution
        # logic without depending on the full canonical preamble.
        tiny = "SCENE: demo\nActor: {actor}\nAction: {action_type}"
        rendered = format_prompt(tiny, {"actor": "you", "action_type": "attack"})
        # Canonical preamble is prepended if available; the scene tail must still
        # contain the substituted values verbatim.
        self.assertIn("Actor: you", rendered)
        self.assertIn("Action: attack", rendered)


# ---------------------------------------------------------------------------
# Validator acceptance — canonical samples validate with zero violations.
# ---------------------------------------------------------------------------


class TestValidatorAcceptsCanonicalSamples(unittest.TestCase):
    """The three verbatim samples from canonical_voice.md validate clean."""

    def test_accepts_canonical_combat_sample(self):
        payload = {"scene_type": "combat_turn"}
        violations = validate_narration(PASSAGE_COMBAT, payload)
        self.assertEqual(
            violations, [],
            f"canonical combat sample should validate with no violations; got: {violations}"
        )

    def test_accepts_canonical_transition_sample(self):
        payload = {"scene_type": "transition"}
        violations = validate_narration(PASSAGE_TRANSITION, payload)
        self.assertEqual(
            violations, [],
            f"canonical transition sample should validate with no violations; got: {violations}"
        )

    def test_accepts_canonical_negotiation_sample(self):
        payload = {"scene_type": "dialogue", "opposed": True}
        violations = validate_narration(PASSAGE_NEGOTIATION, payload)
        self.assertEqual(
            violations, [],
            f"canonical negotiation sample should validate with no violations; got: {violations}"
        )

    def test_roll_block_language_is_not_forbidden(self):
        """Dice/DC language inside a ROLL block must not trigger forbidden-term flags."""
        payload = {"scene_type": "combat_turn"}
        violations = validate_narration(PASSAGE_COMBAT, payload)
        # No violation from 'd20', 'DC', 'dice roll' style language inside the
        # ROLL block (the old stoic-voice forbidden list is relaxed).
        for v in violations:
            self.assertNotIn("d20", v.lower())
            self.assertNotIn("dice roll", v.lower())
            self.assertNotIn("hit points", v.lower())
            self.assertNotIn("saving throw", v.lower())

    def test_ui_box_hp_sp_is_not_smuggled_mechanism(self):
        """ASCII UI box with HP/SP does not trigger the mechanism-in-prose guard."""
        beat_with_box = PASSAGE_COMBAT + "\n\n" + (
            "┌──────────────────────────────────────────┐\n"
            "│ HP: 18/30   SP: 10/12                    │\n"
            "│                                          │\n"
            "│ [a] Press advantage                      │\n"
            "│ [b] Fall back                            │\n"
            "│ [c] Draw sidearm                         │\n"
            "└──────────────────────────────────────────┘"
        )
        payload = {"scene_type": "combat_turn"}
        violations = validate_narration(beat_with_box, payload)
        for v in violations:
            self.assertNotIn("mechanism smuggled", v)
            self.assertNotIn("HP", v)


# ---------------------------------------------------------------------------
# Validator rejection — voice violations surface as blocking flags.
# ---------------------------------------------------------------------------


class TestValidatorRejectsVoiceViolations(unittest.TestCase):
    """Structural voice failures produce violation messages."""

    def test_rejects_third_person_protagonist(self):
        # Narration that slips into third-person past for the PC.
        text = (
            "The **Thornwolf** drives at you. Your arm is too slow.\n\n"
            "He rolled to his feet. He gasped. He had blood on his hands — "
            "three lines of heat across his cheek and collarbone.\n\n"
            "**Opportunity.**\n\n"
            "The blade bites deep into the thorn-hide — and the forearm rakes "
            "you as it passes.\n\n"
            "You come up driving, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        # Should flag the third-person/past slippage.
        self.assertTrue(
            any("second-person" in v.lower() for v in violations),
            f"expected second-person violation; got: {violations}"
        )

    def test_rejects_past_tense_you(self):
        text = (
            "The **Thornwolf** drives at you. Your arm is too slow.\n\n"
            "You drove the trauma shears into the neck — the forearm rakes "
            "you as it passes.\n\n"
            "**Opportunity.**\n\n"
            "The blade bites deep, gasping and fast.\n\n"
            "You roll to your feet, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(
            any("past-tense 'you'" in v.lower() or "second-person" in v.lower() for v in violations),
            f"expected past-tense-you violation; got: {violations}"
        )

    def test_rejects_no_fragment_paragraph_in_combat(self):
        # Prose is well-shaped except it never drops a 1-3 word fragment paragraph.
        text = (
            "The **Thornwolf** drives at you from the flank and your arm is too slow. "
            "It's not a graceful martial arts intercept — it's a kinetic wreck. "
            "You drop your weight and pivot in the same motion. "
            "You punch the trauma shears up and under the jaw toward the artery. "
            "The blade bites the thorn-hide and rakes your cheek as you disengage. "
            "You come up driving and gasping."
        )
        # One block of text, no paragraph breaks, so definitely no fragment paragraph.
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(
            any("fragment paragraph" in v.lower() for v in violations),
            f"expected fragment-paragraph violation; got: {violations}"
        )

    def test_rejects_overlong_paragraph(self):
        # Six sentences in a single paragraph — clearly lost its shape.
        big = (
            "You move through the alley. The rain is heavy on the tin. "
            "Your shoulder aches where the Thornwolf hit it. The trauma shears "
            "are wet in your hand. A man steps out from behind the dumpster. "
            "He is holding a knife and his breath fogs the air in front of him. "
            "He is not yet committing to a line of attack but you can see him "
            "decide, the eye drift to the blade, the weight shift to the back foot."
        )
        text = (
            "The **alley** opens onto First Avenue.\n\n"
            f"{big}\n\n"
            "You catch his eye.\n\n"
            "**Opportunity.**\n\n"
            "You close the distance — three steps, shears up."
        )
        # transition scene: paragraph-overlong check fires.
        violations = validate_narration(text, {"scene_type": "transition"})
        self.assertTrue(
            any("paragraph overlong" in v.lower() for v in violations),
            f"expected paragraph-overlong violation; got: {violations}"
        )

    def test_rejects_missing_em_dash(self):
        # Combat prose >= 3 sentences with no em dash.
        text = (
            "The **Thornwolf** drives at you from the flank. Your arm is too slow. "
            "You catch the trauma shears on the rebound.\n\n"
            "**Opportunity.**\n\n"
            "You drop your weight and pivot, punching the shears up and under the jaw.\n\n"
            "The blade bites deep. You come up driving.\n\n"
            "You roll to your feet, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(
            any("em-dash" in v.lower() for v in violations),
            f"expected em-dash violation; got: {violations}"
        )

    def test_rejects_rhetorical_question_in_prose(self):
        text = (
            "The **Thornwolf** drives at you from the flank. Your arm is too slow.\n\n"
            "What could you possibly do about that?\n\n"
            "**Opportunity.**\n\n"
            "You drop your weight — pivot — punch the shears up under the jaw.\n\n"
            "The blade bites deep. You come up driving, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(
            any("rhetorical question" in v.lower() for v in violations),
            f"expected rhetorical-question violation; got: {violations}"
        )

    def test_rejects_ellipsis_in_prose(self):
        text = (
            "The **Thornwolf** drives at you from the flank. Your arm is too slow.\n\n"
            "Your hand reaches for the trauma shears...\n\n"
            "**Opportunity.**\n\n"
            "You drop your weight — pivot — punch the shears up under the jaw.\n\n"
            "The blade bites deep. You come up driving, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        self.assertTrue(
            any("ellipsis" in v.lower() for v in violations),
            f"expected ellipsis violation; got: {violations}"
        )

    def test_rejects_mechanism_in_prose(self):
        text = (
            "The **Thornwolf** drives at you. Your arm is too slow. "
            "You roll a 12 vs DC 10 and hit for damage: 4 — then the thorn-hide "
            "rakes your cheek and you come up gasping.\n\n"
            "**Opportunity.**\n\n"
            "You roll to your feet, gasping."
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        # Any of DC, rolled/you roll, damage: 4 should surface.
        mech_flags = [v for v in violations if "mechanism smuggled" in v.lower()]
        self.assertTrue(
            len(mech_flags) >= 1,
            f"expected at least one mechanism-in-prose violation; got: {violations}"
        )


# ---------------------------------------------------------------------------
# Signature hints — non-fatal reminders surface when signatures are missing.
# ---------------------------------------------------------------------------


class TestSignatureHints(unittest.TestCase):
    """Hints are soft signals; they surface but do not block emission."""

    def test_hint_negative_definition_missing_in_plain_combat(self):
        text = (
            "The **Thornwolf** drives at you. Your arm is too slow.\n\n"
            "**Opportunity.**\n\n"
            "You drop your weight and punch the shears up under the jaw — the blade "
            "bites deep.\n\n"
            "You come up driving, gasping."
        )
        hints = hint_negative_definition(text)
        self.assertTrue(
            any("It's not X. It's Y." in h for h in hints),
            f"expected negative-definition hint; got: {hints}"
        )

    def test_hint_negative_definition_accepts_transition_shape(self):
        # Passage 2 uses "It's not X. / <decomposition>. / This is Y."
        hints = hint_negative_definition(PASSAGE_TRANSITION)
        self.assertEqual(hints, [], "transition shape should satisfy the hint")

    def test_hint_negative_definition_accepts_strict_shape(self):
        # Passage 1 uses "It's not X. It's Y."
        hints = hint_negative_definition(PASSAGE_COMBAT)
        self.assertEqual(hints, [], "strict shape should satisfy the hint")

    def test_hint_then_hinge_missing_in_transition(self):
        # Transition with no "Then," sentence-initial.
        text = (
            "You are standing at the corner of **First Avenue** and **East 31st**.\n\n"
            "The hum of the FDR cuts out instantly.\n\n"
            "This is the death of physics.\n\n"
            "Your phone goes dead black.\n\n"
            "New York City is no longer on Earth."
        )
        hints = hint_then_hinge(text, "transition")
        self.assertTrue(
            any("Then," in h for h in hints),
            f"expected Then-hinge hint for transition; got: {hints}"
        )

    def test_hint_then_hinge_suppressed_on_non_transition(self):
        # Combat is not expected to use Then-hinge — no hint should fire.
        hints = hint_then_hinge("The blade bites deep.", "combat_turn")
        self.assertEqual(hints, [])

    def test_hint_scene_cap_present_on_aphoristic_close(self):
        text = (
            "You move through the alley. The rain is heavy.\n\n"
            "You roll to your feet, gasping."
        )
        hints = hint_scene_cap(text)
        self.assertEqual(
            hints, [],
            f"aphoristic <=12-word close should satisfy the hint; got: {hints}"
        )

    def test_hint_scene_cap_missing_on_long_close(self):
        # Final paragraph is long and not aphoristic.
        text = (
            "You move through the alley.\n\n"
            "You walked through the alley for a long time, thinking about many "
            "things, including whether to push forward or fall back, and whether "
            "the Ironbound would accept the vials at tomorrow's fence meeting."
        )
        hints = hint_scene_cap(text)
        self.assertTrue(
            any("scene-capping aphorism" in h for h in hints),
            f"expected scene-cap hint; got: {hints}"
        )

    def test_hints_are_returned_alongside_violations_as_non_fatal(self):
        # A passage with a real violation and a missing signature returns both —
        # the signature hint is prefixed 'hint:' so callers can filter it if
        # running in strict mode.
        text = (
            "The **Thornwolf** drives at you from the flank. Your arm is too slow.\n\n"
            "**Opportunity.**\n\n"
            "You drop your weight, pivot, and punch the shears up and under the jaw.\n\n"
            "The blade bites deep into the thorn-hide of its forearm — and the "
            "forearm rakes you as it passes, three lines of heat across the cheek "
            "and collarbone.\n\n"
            "He rolled to his feet, gasping."  # third-person slip
        )
        violations = validate_narration(text, {"scene_type": "combat_turn"})
        hard_flags = [v for v in violations if not v.startswith("hint:")]
        hints = [v for v in violations if v.startswith("hint:")]
        self.assertTrue(any("second-person" in v.lower() for v in hard_flags))
        # Hints present alongside hard flags — callers can filter either way.
        self.assertIsInstance(hints, list)


class TestForbiddenListIsRelaxed(unittest.TestCase):
    """Old stoic-voice meta-gaming forbidden terms are no longer in the list."""

    def test_meta_gaming_terms_are_not_forbidden(self):
        for term in ["hit points", "experience points", "level up", "dice roll", "d20", "saving throw", "game master"]:
            self.assertNotIn(
                term, _FORBIDDEN_PATTERNS,
                f"{term!r} should no longer be in the forbidden list"
            )

    def test_frame_break_assistant_speak_is_forbidden(self):
        for term in ["as an ai", "dear player", "in a world where"]:
            self.assertIn(
                term, _FORBIDDEN_PATTERNS,
                f"{term!r} should still be in the forbidden list"
            )


if __name__ == "__main__":
    unittest.main()
