# Emergence Redesign — Plain Plan

## What we're building

A new character creation flow for Emergence. The player goes through six
scenes. At the end they have: a character sheet, a roster of NPCs, a job,
five quests (four in backstory, one urgent), and an opening scene that
drops them into the urgent quest.

## The six scenes

1. **Pre-emergence.** Player types name, age, species, profession, personality,
   people in their life, and where they lived before the Onset. Claude reads
   the text and outputs a JSON that assigns attributes, skills, and NPCs.
2. **Power pick.** Engine picks 6 random subcategories out of 30. Player
   picks 2. Engine offers 3 powers from each of the 2 picked subcategories.
   Player picks 1 from each. Engine rolls a random cast mode and rider per
   power.
3. **Location.** Player picks where they ended up after the Onset. One of 18
   Mid-Atlantic settlements.
4. **Job bundle.** Claude reads character + location, writes 5 job cards.
   Each card has a job title, daily loop, skill tilts, factions, NPCs,
   threats. Player picks 1.
5. **Quest pick.** Claude writes 8 starting quests from the picked job.
   Claude picks the 4 best-fitting ones and marks them background. Player
   picks 1 urgent from the remaining 4.
6. **Bridge.** Claude writes a ~1500 word bridge from Onset day through the
   past year, weaving in the 4 background quests as history. Scene lands in
   the opening moment of the urgent quest.

## The quest module

Each quest is a JSON object with:
- A goal sentence (verb the noun)
- Bright lines (named failure states with check conditions)
- A macrostructure (one variable trending toward a threshold)
- A resolution (world deltas on success and per bright-line failure)

Engine enforces the quest schema. Narrator writes quest prose. Engine runs
tick / check_success / resolve. Player cannot abandon; quests fail via
bright line fire or macrostructure expiry.

## What's done

- Quest module: schema, 18 archetypes, delta reconciler, 4 CLI functions,
  42 unit tests passing.
- Design docs: quest design, opening scene, classifier, job bundle.
- Classifier contract + pre-emergence scene + power pick scene + location
  scene.

## What's left

- Job archetypes data file (the location-keyed templates Claude uses to
  write the 5 job cards).
- Job bundle scene (the Python scene class that wraps the pick).
- Quest pick scene (narrator generates 8, picks 4 background, player picks
  1 urgent).
- Bridge scene (the 1500 word bridge + opening scene payload).
- Orchestrator update (session_zero.py).
- Legacy scene removal.
- step_cli.py named verbs + quest tick hooks.
- Integration test.
- Smoke test on fresh save.

---

# Paced Steps

Rules:
- One-line status before each step.
- Small tool calls. Visible output between them.
- No step longer than ~30 seconds of silent work.
- Sustained reasoning goes in scratch notes, not in my head.
- Update `progress.txt` after each step.

## B1 — job_archetypes.json

Goal: author ~4 archetypes per settlement, 18 settlements, ~72 entries
total. Each entry is a skeleton (~10 JSON lines). Claude personalizes at
runtime.

**B1.1** Write schema comment header + skeleton structure.
**B1.2** Fill NYC-area settlements (manhattan_fragment, brooklyn_tower_lords,
        queens_commonage, staten_citadel, flushing_edison_c_cluster). 5 locations.
**B1.3** Fill NJ settlements (iron_crown_newark, yonkers_compact,
        peekskill_bear_house, central_jersey_league, princeton_accord). 5 locations.
**B1.4** Fill PA/DE (philadelphia_bourse, south_philly_holding, lehigh_principalities). 3 locations.
**B1.5** Fill Chesapeake + DC (crabclaw_baltimore, delmarva_harvest, fed_continuity_dc). 3 locations.
**B1.6** Fill outliers (catskill_throne, pine_barrens_batsto). 2 locations.
**B1.7** Sanity check: JSON parses, all 18 location ids present.

## B2 — job_bundle_scene.py

**B2.1** Write scene class: prepare narrator payload, accept 5 card JSON, validate, pick.
**B2.2** Write validator for job bundle JSON structure.
**B2.3** Quick test: load scene, prepare payload, accept mock 5-card output, apply pick.

## B3 — quest_pick_scene.py

**B3.1** Write scene class: prepare narrator payload (character + bundle + archetypes).
**B3.2** Accept 8 quest cards. Narrator has also marked 4 as "backstory"; validate.
**B3.3** Validate each quest with `validate_quest`. Regen up to 3 times on failure.
**B3.4** Player picks 1 from the 4 non-background. Store; write to QuestState via `quest.init()`.
**B3.5** Sanity test.

## B4 — bridge_scene.py

**B4.1** Write scene class: prepare narrator payload with full state + 4 background quests + urgent quest.
**B4.2** Accept bridge prose + opening-scene payload. Validate opening scene has required fields.
**B4.3** Sanity test.

## C1 — session_zero.py orchestrator update

**C1.1** Read current orchestrator.
**C1.2** Rewrite to host: PreEmergence, PowerPick, Location, JobBundle, QuestPick, Bridge.
**C1.3** Test: full run through with mock inputs.

## C2 — legacy scene removal

**C2.1** Delete: onset_scene.py, year_one_vignette_scene.py, scenarios_v3.py, scenario_pool.py (if only used by legacy).
**C2.2** Delete legacy tests: test_onset_scene.py, test_scenarios_v2.py, test_scenarios_v3.py, test_scaffolds.py, test_apply_vignette_choice.py, test_scenario_pool.py (if they reference removed modules).
**C2.3** Run test suite; confirm no import errors.

## C3 — step_cli.py wiring

**C3.1** Read existing step_init and dispatch.
**C3.2** Add new handlers: step_pre_emergence, step_pick_power, step_pick_location, step_pick_job, step_pick_quest, step_bridge.
**C3.3** Add quest state persistence: quests.json save/load.
**C3.4** Wire quest.tick() into existing step_tick (world_pulse).
**C3.5** Wire quest.tick() into step_scene_close and step_resolve_action (scene_close, travel_segment).
**C3.6** Remove old legacy handlers: step_scene, step_scene_apply, step_scene_ack, step_scene_finalize.
**C3.7** Update `step init` success message to point at `step pre-emergence`.
**C3.8** Add argparse entries for new step verbs in main.py or argument config.

## D1 — integration test

**D1.1** Write fixture: deterministic seeds, canned classifier output, canned bundle output, canned quest output, canned bridge output.
**D1.2** Run full flow in-process: init → pre-emergence → power-pick → location → job-bundle → quest-pick → bridge.
**D1.3** Assert: CharacterSheet populated, QuestState has 5 quests (1 urgent + 4 background), opening scene payload valid.

## D2 — smoke test

**D2.1** Wipe /home/user/Equilibrium/saves/default.
**D2.2** Run step init.
**D2.3** Run step pre-emergence with Shake's existing biography.
**D2.4** Spot-check the classifier payload shape.
**D2.5** Stop — hand back to user for live Claude classifier run.

---

## Checkpoint discipline

After each completed step:
1. Print result line.
2. Append line to progress.txt.
3. Run quick validation (import check / JSON parse) when relevant.
4. Do not start next step until the prior result line has been printed.
