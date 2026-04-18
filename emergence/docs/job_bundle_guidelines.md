# Job Bundle Guidelines

For the narrator generating the five job-bundle cards the player picks from
after selecting a post-emergence location.

A **job bundle** is the character's role in the post-emergence world plus the
human and institutional entanglements that come with it. Picking a bundle
binds factions, NPCs, threats, and starting location — everything the first
quests will draw from.

---

## Inputs you receive

- `character_sheet` — finalized pre-emergence attributes, skills, NPCs
- `powers` — the two powers the PC picked, with cast + rider already rolled
- `pre_emergence_location` — where the PC lived before the Onset
- `post_emergence_location` — the settlement the player picked
- `job_archetypes_for_location` — 8-12 archetype skeletons from the
  `job_archetypes.json` data file, keyed to the chosen location

---

## Your task

Generate **5 distinct job bundle cards**. Each card is the same bundle
shape (below). The 5 should cover different plausible lives for this
character in this settlement — not five versions of the same job.

### Distinct means distinct

The five cards should feel like five different futures. If the character is a
surgeon arriving in Philadelphia:

- A Bourse-affiliated clinic keeping merchant scions alive (institutional, comfortable)
- A Crabclaw dockworker infirmary in a South Philly holding (rough, blue-collar)
- A Yonkers-refugee field clinic in a fragile township (austere, meaningful)
- An Iron Crown medical officer contracted out to patrol districts (morally complicated)
- An underground surgeon for the Listening cult (dangerous, secretive)

Not:

- Five variations of "Bourse clinic." That's one card.

Pull archetypes from the location's pool. If the archetypes don't span enough,
synthesize new ones within the location's logic — the Bourse has dozens of
clinics; the Iron Crown has medical officers; the Listening has underground
specialists. Use the setting primer as a ground truth.

---

## Card shape

```json
{
  "job_id": "bourse_heart_clinic_resident",
  "title": "Resident at Weiss-Hallam Heart Clinic, Rittenhouse",
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
    {"npc_id": "npc_dr_hallam", "role": "ally", "relation": "mentor",
     "bond": {"trust": 2, "loyalty": 2, "tension": 1},
     "hook": "Co-founder of the clinic; old surgical lineage; knows your name by reputation."},
    {"npc_id": "npc_nurse_petra", "role": "ally", "relation": "coworker",
     "bond": {"trust": 2, "loyalty": 2, "tension": 0},
     "hook": "Senior circulating nurse; has run this OR longer than the clinic's been open."},
    {"npc_id": "npc_weiss_jr", "role": "rival", "relation": "colleague",
     "bond": {"trust": 0, "loyalty": 0, "tension": 3},
     "hook": "The founder's son; passed over for attending; quietly furious."},
    {"npc_id": "npc_bourse_notary_vann", "role": "contact", "relation": "faction_contact",
     "bond": {"trust": 1, "loyalty": 0, "tension": 0},
     "hook": "Clinic's liaison to the Bourse; your paperwork goes through her."}
  ],
  "threats": [
    {"archetype": "debt_holder",
     "hook": "A Tower Lord captain owes Hallam a favor you'll be asked to discharge."},
    {"archetype": "named_rival_human",
     "hook": "Weiss Jr. is not going to age out of his resentment."}
  ],
  "starting_location": "rittenhouse_square_philadelphia",
  "opening_vignette_seed": "You are finishing the second surgical case of a long Tuesday when the bell at the front desk rings three times — an Iron Crown summons."
}
```

---

## Rules

### Draw entities from the bundle, don't invent separately

NPCs, factions, and threats in each card should be local to the settlement
and its ecosystem. The Bourse's rival is South Philly Holding; not the
Delmarva Harvest Lords. Use the setting primer's faction-relationship map.

### Respect the character's skills

The job should make meaningful use of the PC's top 3–4 skills. A surgeon
card that doesn't use surgery is a waste of a card. A soldier card that
doesn't use firearms or tactics is a waste of a card. Tune the job so at
least 2 of the PC's high-rank skills are daily-use.

### Respect the character's powers

If the PC has a somatic healing power, one card should make explicit use of
it (e.g. "the clinic knows what you can do and expects it"). If the PC has
a kinetic impact power, at least one card should have violence on the menu.

### Skill tilts

The `skill_tilts` object lists skills the job will raise over the first
months of play. +1 is standard; rare skills might get +2. These are applied
silently at finalization.

### NPC count

Each card should include **4–6 NPCs** — enough to make the job feel peopled,
not so many that the initial roster becomes unmanageable. Mix roles: at
least 1 ally (strong bond), 1 contact (utility), 1 rival (low-grade
antagonist). Include a boss / patron if the job has one.

### NPC archetype

If the card invents a new NPC (not drawn from the pre-emergence roster),
use the NPC generator's archetype logic — name, species, tier, and a
one-line hook. Keep the details minimal; the engine fleshes them out.

### Threats

Each card should seed **1–2 threats** — named obstacles that will surface
during play. Pull from the canonical threat_archetypes list:

`knife_scavenger_survivor`, `iron_crown_notice`,
`warped_predator_personal`, `eldritch_persistent`, `named_rival_human`,
`faction_assassin_contract`, `biokinetic_error_infection`, `debt_holder`,
`ruined_former_ally`, `family_complication`

### Factions

Each card should have **1–2 positive** factions (employer, patron, allied
guild) and **1–2 negative** factions (rivals, enforcers, creditors).
Starting standings: +1 on the positive side, -1 on the negative side, per
entry. Exceptions allowed if justified in `reason`.

### Starting location

The `starting_location` is a fine-grained place within the settlement — the
specific clinic, the specific holding, the specific warehouse. Reference
the location by id from the world state's location registry where possible;
invent a new location only if needed, and name it plausibly.

### Opening vignette seed

One sentence that could plausibly open the PC's first scene in this role.
The Quest generator reads this as context when proposing the five starting
quests.

---

## Tone

The five cards should be offered to the player as short, vivid descriptions
— a title, a one-paragraph daily loop, and a small tag list of factions /
NPCs / threats. Keep each card's pitch under 150 words when presented in
prose. The full JSON carries the mechanics; the prose carries the choice.

---

## What to avoid

- **Heroic framing.** These are jobs, not adventures. The adventure comes
  from the quests you'll generate after the pick.
- **Invented factions.** Use only the 22 canonical Mid-Atlantic factions.
- **Invented settlements.** Use the named settlements from the primer.
- **Implausibly friendly starts.** Even the "safe" cards should carry 1+
  negative faction and 1+ threat. The post-Onset world is not safe.
