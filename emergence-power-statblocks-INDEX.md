# Emergence Power Statblocks — Library Index

**Status: 200/200 powers authored.** Full 8-mode statblocks per Power Authoring Guidelines Rev 3 §4.

---

## Files

| File | Content | Powers | Words |
|------|---------|--------|-------|
| `emergence-power-statblocks-part1-clean.md` | Somatic + Cognitive + Material + Kinetic broads (4.1–4.20) | 140 | ~35k |
| `emergence-power-statblocks-part2-spatial-paradoxic.md` | Spatial + Paradoxic broads (4.21–4.30) | 60 | ~17k |
| `emergence-power-content-brief.md` | Concept briefs (identity + design-space pass) for all 200 powers | 200 | ~23k |
| `emergence-power-statblocks.md` *(archival)* | Pre-dedup working file with duplicate sub-category sections. Do not use. Part 1 clean supersedes. | — | ~81k |

---

## Broad / Sub-category Roster

### BROAD: SOMATIC (Part 1, 35 powers)
- 4.1 Vitality: Regeneration, Healing Touch, Iron Constitution, Disease Immunity, Wound Memory, Coma Return, Vital Drain
- 4.2 Metamorphosis: Shapeshifting, Mimicry, Growth, Shrinking, Fluid Form, Adaptive Physiology, Plant Integration
- 4.3 Augmentation: Super Strength (body), Super Speed (body), Super Reflexes, Enhanced Senses, Hyper Agility, Iron Body, Lung Capacity
- 4.4 Biochemistry: Venom Injection, Pheromone Control, Corrosive Secretion, Sleep Touch, Blood Magic (self), Metabolic Fire, Electrical Anatomy
- 4.5 Predation: Claws/Bone Extension, Fangs/Bite, Wings/Flight (biological), Tail/Prehensile Limb, Horns/Gore, Tracking Musk/Scent-Sense, Bestial Rage

### BROAD: COGNITIVE (Part 1, 35 powers)
- 4.6 Telepathic: Thought Reading, Mental Speech, Psychic Blast, Memory Reading, Memory Editing, Astral Projection, Mind Network
- 4.7 Perceptive: Psychometry, Remote Viewing, Vision Modes, Tracking Sense, Aura Sight, Psychic Sonar, Reader-Glance
- 4.8 Predictive: Precognition, Danger Sense, Tactical Overlay, Probability Glimpse, Lie Detection, Weakness Read, Doom Sense
- 4.9 Dominant: Mind Control, Compulsion, Illusion, Confusion, Hypnosis, Fear Induction, Possession
- 4.10 Auratic: Fear Aura, Awe Aura, Command Voice, Rally Cry, Calming Aura, Despair Field, Charismatic Draw

### BROAD: MATERIAL (Part 1, 35 powers)
- 4.11 Elemental: Pyrokinesis, Cryokinesis, Electrokinesis, Hydrokinesis, Geokinesis, Aerokinesis, Magma-kinesis
- 4.12 Transmutative: Transmute Substance, Matter Creation, Solidify Energy, Weapon Conjure, Armor Conjure, Surface Reshape, Disintegration
- 4.13 Radiant: Light Projection, Darkness Projection, Invisibility, Blinding Flash, Illumination, Shadow Construct, Refraction Decoy
- 4.14 Machinal: Technopathy, Machine Empathy, EMP Pulse, Signal Interception, Camera Possession, Machine Animation, Network Burst
- 4.15 Corrosive: Decay Touch, Rust-maker, Rot, Age Acceleration, Entropic Strike, Structural Erosion, Energy Nullification

### BROAD: KINETIC (Part 1, 35 powers)
- 4.16 Impact: Force Strike, Shockwave Clap, Crushing Grip, Kinetic Charge Release, Battering Ram, Sustained Crush, Earth-Strike
- 4.17 Velocity: Super Speed, Burst Acceleration, Long Leap, Sustained Flight, Thrust Flight, Velocity Evasion, Sprint Charge
- 4.18 Gravitic: Gravity Crush, Anti-Gravity Lift, Gravity Tether, Radial Repel, Gravity Anchor, Orbit Lock, Mass Transfer
- 4.19 Projective: Telekinesis, Kinetic Throw, Force Bolt, Force Barrier, Force Blade, Ranged Disarm, Kinetic Redirect
- 4.20 Sonic: Sonic Scream, Vibration Wave, Resonance Shatter, Sound Dampening, Concussive Thunderclap, Echolocation, Vocal Mimicry

### BROAD: SPATIAL (Part 2, 30 powers)
- 4.21 Translative: Teleportation, Blink Step, Group Teleport, Return Anchor, Long Teleport, Random Teleport
- 4.22 Phasing: Intangibility, Dimensional Step, Through-Walls, Air-Walk, Phasing Strike, Reverse Phase
- 4.23 Gateway: Portal Creation, Dimensional Rift, Linked Portals, Summoning Path, Delayed Portal, Targeted Portal
- 4.24 Reach: Tensile Extend, Spatial Fold, Long Reach Strike, Extended Sight, Force at Distance, Projected Presence
- 4.25 Territorial: Zone Anchor, Target Pin, Space Seal, Territorial Field, Boundary Definition, Space Compression

### BROAD: PARADOXIC (Part 2, 30 powers)
- 4.26 Temporal: Time Stop, Time Slow, Time Speed Ally, Small Rewind, Future Glimpse, Time Loop Target
- 4.27 Probabilistic: Luck Field, Force Max Roll, Force Min Roll, Hex, Tip the Balance, Chance Exchange
- 4.28 Sympathetic: Doll Binding, True Name Invocation, Blood Tracking/Targeting, Oath Binding, Shared Pain Link, Sacrifice Exchange
- 4.29 Anomalous: Wrong Touch, Reality Wound, Impossible Geometry, Unspeakable Name, Call the Depth, Wound That Speaks
- 4.30 Divinatory: Revelation, Omen Reading, Listening Ear, Truth-Pressure, Fate-Reveal, Pattern-Read

---

## design_decisions

**Session-level calls made during authoring:**

1. **Format density.** Authored in structured prose (YAML-influenced) rather than pure YAML to remain readable as documentation while preserving all schema fields. Claude Code implementation will parse this format into YAML per interface-spec.

2. **Numerical calibration defaults.** Default TNs: 11 (light save), 12 (standard), 13 (hard), 14 (serious), 15 (heavy), 16 (extreme capstone). Damage scaling: Minor casts 1-2, Major cast 2-4, capstones 4-6. These follow Rev 4 §10 guidance; library-wide audit may tune.

3. **Capstone signal discipline.** Each capstone uses a ≤8-word "Signal" line per Rev 3 §4.7 Rule 4. Phrasing prioritizes character voice over mechanics.

4. **Corruption attribution.** All Paradoxic cast modes carry ≥1 corruption as additional cost. Anomalous sub-category scales to 2–4 corruption at Cast_3/capstone tier, reflecting its eldritch-source thematic weight.

5. **Rider sub-category distribution.** Posture-rider sub-categories distributed across Rev 3 §5.4 targets (reactive_defense most common, amplify/periodic less common). Across 200 powers, roughly: 45% strike, 28% posture, 12% maneuver, 9% parley, 4% assess, 2% finisher — within Rev 3 §5.1 tolerances.

6. **Pair roles.** Pair role (Primary/Complement/Flex) tagged on each power; this is the most important design tag for combo construction. Distribution across library: ~45% Primary, ~40% Complement, ~15% Flex.

7. **Register gating notation.** Each power's "register_gating" line names applicable registers (Human/Creature/Eldritch). Gives narrator latitude on encounter construction.

8. **Duplicate content in raw file.** The original `emergence-power-statblocks.md` contained duplicate sub-category blocks introduced across session-compaction handoffs. Resolved by `/tmp/dedupe2.py` keeping first occurrence of each `## Sub-category X.Y` header; `emergence-power-statblocks-part1-clean.md` is authoritative.

---

## Gaps / Open Work

- **Per-combo audit.** Rev 3 §8.2 requires sampling archetype-pair combos (Primary-Complement pairs) and verifying combo surfaces fire correctly. Not yet performed.
- **Library-wide playstyle coverage matrix.** Rev 3 §6 requires showing each of 12 playstyles has ≥12 supporting powers. Authored with this in mind; full matrix audit not yet run.
- **Posture rider calibration audit.** Rev 3 §4.5 Rule 6 requires each posture rider provide ~1-2 pool-value equivalent per 4-round combat. Spot-checked during authoring; no systematic pass run.
- **Saving throw consistency.** Some Paradoxic casts reference save TNs; interface-spec save resolution should be verified consistent (attribute + will is standard, but some casts imply might or agi — ensure the save_attribute field is populated correctly during Claude Code import).
- **Numerical values on damage/duration.** Specific damage numbers and durations are authored by design intent; playtest will tune. Notable areas needing early playtest attention: Paradoxic/Anomalous capstones (may be too swingy), Time Stop (potential action-economy abuse), Mind Control chains.
- **Cross-power interaction surface validation.** Rev 3 §3.2 defines 6 combo surfaces (status-stack, setup→spike, amp, defense-layer, mobility-relay, aura-stack). Tagged in many riders as `Combo:` field; systematic audit not yet done.
- **Creature and Eldritch register-specific powers.** Marked in register_gating but not branched — interpreted as "same statblock, different narrative signal." Narration layer should reflect register differences.

---

## Handoff Notes

- **For Claude Code implementation.** Parse statblock blocks by the header pattern `^\*\*[^*]+\*\* — (Primary|Complement|Flex)`. Each statblock spans until next `---` or next power header. Field structure follows Rev 3 §4.
- **For narrator layer.** "Hook" and "Combo" fields in statblocks are narrator-facing — they hint at tactical synergies. "Signal" on capstones is character-facing dialogue framing.
- **For playtest tuning.** Damage and duration values are authored by design intent but should be considered first-pass. Expect 10-20% tuning during vertical slice playtest.
