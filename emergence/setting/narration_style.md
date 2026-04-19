# Narration Style Guide

> **Authoritative spec:** `emergence/prompts/canonical_voice.md`. That file is prepended to every narrator prompt automatically. Read it first.

This file is a short orientation. The load-bearing rules live in the canonical voice preamble.

## Summary

The narrator writes in **pulp-cinematic second-person present** with paratactic right-branching syntax. Mechanism (dice values, DCs, damage numbers, HP/SP, tier labels) surfaces in `**ROLL:**` blocks and ASCII UI boxes. Voice lives in prose. These sit flush; they never collapse into each other.

## Signature cadences (see `canonical_voice.md` for the full spec)

- **`"It's not X. It's Y."`** — negative-definition pivot at reveals, judgments, negotiation moments.
- **`"Then,"`** as beat hinge — advances the moment without analytical connective tissue.
- **Fragment paragraphs** — single noun or onomatopoeic, on their own line. `"Opportunity."` / `"Time."` / `"Thud. Thud."`
- **Em-dash appositives** — specify mid-sentence without breaking rhythm. `"the hum of the FDR—the cars, the engines—cuts out instantly."`
- **Scene-capping aphorism** — compressed epigrammatic single-line paragraph at section end. `"New York City is no longer on Earth."`
- **Typography load** — `**bold**` for tactical entities, named NPCs, landmarks, powers. `ALL CAPS` for system labels (`**ROLL: ATTACK**`, `**PARTIAL SUCCESS**`). `*italics*` for interior emphasis and damage line.
- **Precise-technical noun + pulp verb adjacency** — `"the blade bites deep, bypassing the thick hide"`, `"driving toward the pulsing target in its neck"`.

## Recognizability test

The voice is recognizable in two sentences by: (a) second-person present tense; (b) a short declarative followed by a negative-definition pivot; (c) a precise-technical noun sitting next to a pulp verb. If a draft fails this three-part test, revise.

## Length discipline

Managed by `emergence/engine/narrator/validation.py::_get_length_bounds`. Envelopes are widened beyond the earlier stoic-voice bounds to accommodate ROLL block + UI box overhead in combat / dialogue / transition beats.

## Diction inputs

The faction voices, sensory palette, description templates by location type, and anti-patterns in `emergence/setting/narration.md` remain useful as **diction inputs**. They supply the nouns, smells, sounds, and faction register that the canonical voice then composes into prose. They do not describe the voice itself.

## Self-audit

Before emitting, run the ten checks in the preamble's `<self_audit>` block, then the `<recognizability_test>`. Cap total revisions at 2 — emit on the second pass regardless.
