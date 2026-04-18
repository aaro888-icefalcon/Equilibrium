# Job Bundle Guidelines

For the narrator generating the five job-bundle cards the player picks from
after selecting a post-emergence location.

A **job bundle** is the character's role in the post-emergence world plus
the human and institutional entanglements that come with it. Picking a
bundle binds factions, NPCs, threats, and starting location — everything
the first quests will draw from.

---

## Inputs you receive

- `character_sheet` — finalized pre-emergence attributes, skills, NPCs
- `powers` — the two powers the PC picked, with cast + rider already rolled
- `pre_emergence_location` — where the PC lived before the Onset
- `post_emergence_location` — the settlement the player picked
- `archetype_pool` — **exactly 5 archetype skeletons** chosen by the engine
  sampler to span the theme buckets (see below). Use these; do not import
  archetypes from outside this list.
- `archetype_pool_full` — the full location pool, provided for reference
  only. Synthesize NPCs and flavor from it, but generate cards only against
  the sampled five.

---

## Your task

Generate **5 job bundle cards** — one per archetype in `archetype_pool`,
preserving the order the sampler provided. Each card corresponds to one
archetype and fills the card schema below.

### The five cards represent five different futures

The sampler has already selected archetypes across theme buckets
(`old_skills`, `power_based`, `combat_heavy`, `hybrid`, `post_apoc_generic`)
so the card set naturally spans continuity, transformation, and opportunity.
Follow the sampler's picks — your job is to personalize each archetype
into a complete bundle, not to re-select.

Label each card with the dominant theme bucket from its archetype's
`theme_tags`. This helps the player understand what they're choosing:

- **Continuity** (`old_skills`): this job leans on who you were before.
- **Transformation** (`power_based`): this job is organized around your
  new abilities; pre-Onset skills are secondary.
- **Dangerous** (`combat_heavy`): this job involves routine physical risk.
- **Hybrid** (`hybrid`): pre-Onset skills and powers are both load-bearing.
- **Wildcard** (`post_apoc_generic`): post-apocalyptic work anyone with
  initiative could pick up.

The label goes in the `theme_label` field of the card (see schema).

---

## Card schema

```json
{
  "job_id": "bourse_heart_clinic_resident",
  "title": "Resident at Weiss-Hallam Heart Clinic, Rittenhouse",
  "theme_label": "Continuity",
  "archetype_id": "pb_clinic_attending",
  "daily_loop": "Mornings on ward rounds in Rittenhouse Square; afternoons in the second-floor OR. Your quarters are on-site, above the pharmacy. You walk to Reading Terminal once a week to trade ledger chits for coffee.",
  "skill_tilts": {
    "surgery": 1,
    "pharmacology": 1,
    "faction_etiquette": 1,
    "bureaucracy": 1
  },
  "factions": {
    "positive": [
      {"faction_id": "philadelphia_bourse", "standing": 1, "role": "employer"}
    ],
    "negative": [
      {"faction_id": "south_philly_holding", "standing": -1,
       "reason": "Dreng's enforcers have had patients refused care at Weiss-Hallam."}
    ]
  },
  "npcs": [
    {"npc_id": "npc_dr_hallam", "name": "Dr. Hallam", "role": "ally",
     "relation": "mentor",
     "bond": {"trust": 2, "loyalty": 2, "tension": 1},
     "hook": "Co-founder of the clinic; old surgical lineage; knows your name by reputation."},
    {"npc_id": "npc_nurse_petra", "name": "Petra", "role": "ally",
     "relation": "coworker",
     "bond": {"trust": 2, "loyalty": 2, "tension": 0},
     "hook": "Senior circulating nurse; has run this OR longer than the clinic's been open."},
    {"npc_id": "npc_weiss_jr", "name": "Weiss Jr.", "role": "rival",
     "relation": "colleague",
     "bond": {"trust": 0, "loyalty": 0, "tension": 3},
     "hook": "The founder's son; passed over for attending; quietly furious."},
    {"npc_id": "npc_bourse_notary_vann", "name": "Notary Vann", "role": "contact",
     "relation": "faction_contact",
     "bond": {"trust": 1, "loyalty": 0, "tension": 0},
     "hook": "Clinic's liaison to the Bourse; your paperwork goes through her."}
  ],
  "threats": [
    {"archetype": "named_rival_human",
     "hook": "Weiss Jr. is not going to age out of his resentment."},
    {"archetype": "debt_holder",
     "hook": "A Tower Lord captain owes Hallam a favor you'll be asked to discharge."}
  ],
  "starting_location": "rittenhouse_square_philadelphia",
  "opening_vignette_seed": "You are finishing the second surgical case of a long Tuesday when the bell at the front desk rings three times — an Iron Crown summons."
}
```

---

## Writing rules

### Use the archetype's theme_tags and notes as ground truth

Each archetype in the sampled pool carries `theme_tags`, `skill_tilts_hint`,
`faction_candidates`, `npc_role_hints`, `threat_candidates`, and a `notes`
field. Use them. The `notes` line is the archetype's tone anchor — match it.

### Include at least one combat-capable threat per card

Each card's `threats` list must include at least one entry whose archetype
is combat-capable. Pull from:

`knife_scavenger_survivor`, `warped_predator_personal`,
`warped_predator_intelligent`, `wretch_swarm`, `named_rival_human`,
`faction_assassin_contract`, `raider_band_reaper`, `raider_band_chain_king`,
`iron_crown_notice`, `volk_informant`, `preston_notice`,
`doctor_pale_target`, `cult_listening_incursion`, `hive_tendril_breach`

The engine validator rejects cards without one. This guarantees the urgent
quest can always draw its proxy antagonist from a combat source.

Each card may include a second non-combat threat: `debt_holder`,
`biokinetic_error_infection`, `corruption_progressing_self`,
`family_complication`, `ruined_former_ally`, `species_cluster_obligation`,
`echo_memory_loss`, `shade_haunting`, `eldritch_persistent`.

### Use canonical factions only

All `faction_id` values must be canonical mid-Atlantic factions from the
setting primer. If the archetype's `factions.positive_candidates` lists a
faction, use it. Do not invent faction names.

### Keep NPC count at 4

Each card carries exactly 4 NPCs: 1 mentor/patron, 1 coworker/ally,
1 rival, 1 contact. Names use plausible mid-Atlantic demographics for the
location. Each NPC carries a one-line `hook` explaining their stake.

### Respect the character's skills and powers

- For `old_skills` cards, tune `skill_tilts` so the PC's top 3-4 pre-Onset
  skills are daily-use.
- For `power_based` cards, include `power_handling` in `skill_tilts` and
  write the `daily_loop` so the power is the organizing element. The job
  expects the power; the pay reflects it.
- For `hybrid` cards, do both.

### Starting location is specific

`starting_location` is a fine-grained place within the settlement — a
specific clinic, holding, warehouse. Use the archetype's
`starting_sublocation_hint` as the base and elaborate.

### Opening vignette seed

One sentence that could plausibly open the PC's first scene in this role.
The quest generator reads it as context when writing the urgent quest.

### Tone

Each card's pitch should be under 150 words of prose when presented to the
player. The JSON carries mechanics; the prose carries the choice. Write in
a plain, functional register — specific nouns, present tense, no
epigrammatic closers.

---

## Card count and order

Exactly 5 cards. The card at `cards[i]` corresponds to the archetype at
`archetype_pool[i]` in the narrator payload. Preserve this alignment.

---

## Validation summary

The engine validator checks:
- exactly 5 cards
- unique `job_id` per card
- `title`, `daily_loop`, `starting_location`, `opening_vignette_seed`
  present and non-empty
- `skill_tilts` is a dict
- `factions.positive` is non-empty list
- `factions.negative` is a list (may be empty)
- `npcs` is a list of >= 3 entries, each with `name` and a valid `role`
- `threats` is non-empty and includes at least one combat-capable archetype

Failing any check returns the error list for a regen attempt (up to 3).
