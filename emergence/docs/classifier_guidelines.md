# Pre-Emergence Classifier Guidelines

For the narrator reading the player's free-text pre-emergence biography and
returning a structured JSON payload the engine validates.

You have four tasks:

1. **Attributes** — assign die sizes to six attributes based on who the PC is
2. **Skills** — assign ranks to named skills based on what the PC has done
3. **NPCs** — extract family, friends, coworkers as structured bond records
4. **History seeds + inventory seeds** — minor flavor carried into the world

Be broad, use judgment. There is no point budget surfaced to you — use your
read of the character. The engine applies clamps silently if something is
out of range.

---

## Attributes

Six attributes, each expressed as a die size. Baseline is d6 across the board.

| Attribute | Die | Rough meaning |
|-----------|-----|---------------|
| **Strength** | 4/6/8/10 | lifting, muscular work, raw force |
| **Agility** | 4/6/8/10 | reflexes, fine motor, coordination |
| **Perception** | 4/6/8/10 | sensory acuity, noticing things |
| **Will** | 4/6/8/10 | discipline, command presence, fortitude |
| **Insight** | 4/6/8/10 | pattern recognition, diagnostic thinking |
| **Might** | 4/6/8/10 | endurance, stamina, long-shift grit |

### How to think about it

- A person whose work is primarily of the body — laborer, soldier, athlete,
  surgeon-under-load — raises Strength or Might, usually not both.
- A person whose work is primarily of the mind — analyst, scholar, diagnostician
  — raises Insight.
- A person whose work demands *noticing* — medic, investigator, hunter,
  long-haul driver — raises Perception.
- A person who has commanded others — teacher, chief, officer, parent of many
  — raises Will.
- A person whose training is specifically fine-motor — surgeon, musician, smith,
  martial artist — raises Agility.
- Athletes of endurance (marathoners, field workers, cyclists) raise Might.

### The spiky principle

Skilled people are spiky. A surgeon is probably Agility-d8 or d10 and Insight-d8
— the rest baseline. A soldier is Strength-d8 and Perception-d8 — the rest
baseline. Don't distribute evenly; lift what the profession and personality
directly require.

### When to drop to d4

Only if the bio explicitly supports a weakness. "Frail" / "bookish" / "never
worked a day outdoors" / "clumsy" — these are invitations to drop one attribute
to d4. Without an explicit signal, don't.

### When to raise to d10

Rare. Requires the bio to describe genuine excellence — not just
professionalism. A competition athlete. A published scholar. A combat veteran.
One d10 at most unless the bio is exceptional.

### Always include a rationale

```json
"attributes": {
  "strength": 6, "agility": 8, "perception": 8,
  "will": 8, "insight": 10, "might": 6,
  "rationale": "PGY-4 vascular surgeon: Agility (fine motor surgery), Perception (diagnostic), Will (chief-of-residents command), Insight (system-builder, analytical by temperament). Not athletic, not physically large."
}
```

---

## Skills

Emergence has 32 canonical skills in 7 clusters. Ranks are 0–5 at creation
(engine clamps to 5). Full list:

**Combat:** firearms, melee, brawling, thrown, tactics
**Physical/Survival:** stealth, urban_movement, wilderness, weather_read, animal_handling, swimming
**Craft/Technical:** craft, basic_repair, scavenging, agriculture, cooking
**Medical:** first_aid, surgery, pharmacology, field_medicine
**Social:** negotiation, intimidation, command, instruction, streetwise
**Knowledge:** literacy, languages, history, regional_geography, bureaucracy
**Other:** perception_check, faction_etiquette

### How to rank

- **5** — the thing this person does every working day at full professional
  level. For a surgeon: `surgery`. For a journalist: `negotiation`. For a
  soldier: `firearms` or `melee`.
- **3-4** — secondary professional skills, things used often but not daily.
  For a surgeon: `first_aid`, `pharmacology`, `literacy`.
- **1-2** — adjacent knowledge, hobbies, past training. For a surgeon who reads
  military history and did TKD in college: `history`-2, `brawling`-2.
- **0** (omit) — no meaningful exposure.

### Cluster logic

A professional almost always has 3–5 skills at rank 3+ from their primary
cluster plus 1–2 adjacent skills from neighboring clusters. A surgeon: Medical
cluster heavy, plus `literacy` and `bureaucracy` (Knowledge) from years of
charting and publication.

### Hobbies and training

Mine the personality and biography text for training and hobbies:
- "heavy reader" → `literacy`, `history`, `languages` (moderate ranks)
- "action RPGs" → `tactics` (small rank)
- "martial arts" → `brawling`, sometimes `melee`
- "amateur musician" → no direct skill (not in the list)
- "grew up hunting" → `firearms`, `wilderness`, `perception_check`

### Always include a rationale

```json
"skills": {
  "surgery": 5, "first_aid": 5, "pharmacology": 4, "field_medicine": 3,
  "literacy": 4, "bureaucracy": 3, "brawling": 2, "history": 3, "tactics": 2,
  "rationale": "Core vascular surgery cluster at pro level. First aid/pharm/field as daily-use in residency. Literacy + bureaucracy from academic chief role. Brawling from past TKD. History + tactics from stated reading interests."
}
```

---

## NPCs

Extract every named or role-described person from the bio as a structured NPC
record. The engine materializes these as real NPC entries; they become the
PC's pre-emergence roster.

### Record shape

```json
{
  "name": "Akhil Rao",
  "relation": "sibling",
  "role": "bond",            // "bond" | "contact" | "rival" | "distant"
  "bond": {
    "trust": 3,              // -3 to +3
    "loyalty": 3,
    "tension": 0
  },
  "distance": "near",        // "with_player" | "near" | "regional" | "distant" | "unknown"
  "notes": "Mount Sinai med student; Shake's younger brother"
}
```

### Relations — canonical set

- `parent` / `child` / `sibling` / `partner` / `extended_family`
- `friend` / `mentor` / `student`
- `coworker` / `boss` / `subordinate` / `colleague`
- `rival` / `enemy`
- `patient` / `client` / `contact`

If the bio describes a relationship not in this list, pick the nearest match
and note the specifics in `notes`.

### Roles

- **bond** — someone the PC will carry through play; high trust/loyalty
- **contact** — useful connection, modest trust
- **rival** — opposition, negative tension
- **distant** — in the PC's history but unlikely to recur

### Bond values — how to set them

| Trust | Loyalty | Typical relation |
|------|---------|------------------|
| +3 | +3 | immediate family, oldest friends |
| +2 | +2 | close friends, trusted mentor |
| +1 | +1 | friendly coworker, warm acquaintance |
| 0 | 0 | neutral — professional only |
| -1 | -1 | cool / strained |
| -2 or -3 | — | rival / enemy (use `role: "rival"`) |

**Tension** (0-3) is separate from trust/loyalty. A sibling can be trusted +3,
loyal +3, and tension +2 because they fight about Dad. Tension doesn't make
someone worse — it makes them more volatile in scene.

### Distance

- `with_player` — lives in the same household
- `near` — same city / district
- `regional` — same state / region (weekend visit possible)
- `distant` — different region / country
- `unknown` — lost contact, status unclear

### Don't invent

If the bio doesn't name or role-describe someone, don't make them up. It's
fine to return a small NPC list if the bio is thin. The world will generate
more NPCs during play.

---

## History seeds

Optional. Two or three short events from the PC's pre-emergence life that
might be referenced during play. Each:

```json
{
  "date": "2024-07-12",
  "category": "personal",   // combat | political | personal | discovery
  "description": "Completed first solo vascular case; Akhil in the gallery."
}
```

Seed events are flavor, not mechanics. Skip this field entirely if the bio
doesn't supply strong moments.

---

## Inventory seeds

Optional. Two or three items the PC plausibly carries into the post-Onset
world. Each:

```json
{
  "id": "inv_shakes_wedding_band",
  "name": "Father's wristwatch",
  "description": "Quartz, pre-Onset, hasn't been wound since.",
  "quantity": 1
}
```

Skip if the bio doesn't hint at specific objects.

---

## Final output shape

```json
{
  "attributes": { ... , "rationale": "..." },
  "skills":     { ... , "rationale": "..." },
  "npcs":       [ ... ],
  "history_seeds":   [ ... ],  // optional
  "inventory_seeds": [ ... ]   // optional
}
```

Return only valid JSON. No commentary, no markdown code fence.
