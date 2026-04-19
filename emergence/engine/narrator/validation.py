"""Narrator output validation — checks length, forbidden words, voice structure, mechanism channel."""

from __future__ import annotations

import re
import statistics
from typing import Any, Dict, List, Tuple


# Words/phrases the narrator should never use. Meta-gaming terms (HP, DC, dice)
# now appear legitimately inside ROLL blocks and UI boxes; only frame-breaking
# assistant-speak remains forbidden here.
_FORBIDDEN_PATTERNS = [
    "as an ai",
    "as a language model",
    "in this scene we",
    "dear player",
    "dear reader",
    "let me narrate",
    "i'll narrate",
    "i will narrate",
    "in a world where",
]


# ---------------------------------------------------------------------------
# Scene types that require voice-structural checks (fragment paragraph, em dash).
# ---------------------------------------------------------------------------
_VOICE_STRUCTURED_SCENES = {
    "combat_turn",
    "scene_framing",
    "situation_description",
    "transition",
    "death_narration",
}

_FRAGMENT_REQUIRED_SCENES = {
    "combat_turn",
    "transition",
    "situation_description",
    "death_narration",
}

_EM_DASH_REQUIRED_SCENES = {
    "combat_turn",
    "transition",
    "scene_framing",
}

_BOLD_REQUIRED_SCENES = {
    "combat_turn",
    "transition",
}


# ---------------------------------------------------------------------------
# Prose-region extraction
# ---------------------------------------------------------------------------

# ASCII UI box: a block of lines whose first non-whitespace character is one
# of the box-drawing characters the narrator uses (┌└│├─). Also support the
# plain-ASCII fallback using + - | characters for broader compatibility.
_UI_BOX_LINE = re.compile(
    r"^\s*[┌└├│─┤┐┘]"              # unicode box drawing
    r"|^\s*[+\-|]{2,}"              # ascii fallback: lines like +-- or ||
    r"|^\s*\|.*\|\s*$"              # any line bracketed by pipes
)

# ROLL block lines: the header `**ROLL: ...**` and the indented Dice/Modifiers/
# Total/Result/damage-italic lines that follow. We keep these out of the prose
# region so their `**Dice:**`, `DC`, etc. do not trigger mechanism-smuggling
# or forbidden-language checks.
_ROLL_HEADER = re.compile(r"^\s*\*\*ROLL:\s*.*\*\*\s*$", re.IGNORECASE)
_ROLL_FIELD = re.compile(
    r"^\s*(\*\*)?(Dice|Modifiers|Total|Result|Damage dealt|Damage taken)"
    r"(\*\*)?[:\s]",
    re.IGNORECASE,
)
_ITALIC_DAMAGE_LINE = re.compile(
    r"^\s*\*Damage\s+(dealt|taken).*\*\s*$", re.IGNORECASE
)
_CODE_FENCE = re.compile(r"^\s*```")


# Inline backtick code span (e.g. `Result: 12 vs DC 11`) — used for inline
# dialogue ROLL lines. Strip the backticked portion from prose since its
# contents are mechanism, not narration.
_INLINE_CODE_SPAN = re.compile(r"`[^`\n]*`")

# An inline-ROLL line (inside backticks) that follows a **ROLL:** header.
_INLINE_ROLL_LINE = re.compile(
    r"^\s*`[^`]*(Result|Dice|Modifiers|Total)\s*:[^`]*`",
    re.IGNORECASE,
)


def _split_prose_region(text: str) -> str:
    """Return text with ROLL blocks, UI boxes, code fences, and damage lines removed.

    Used to isolate narrator prose for voice-structural checks so that
    mechanism language inside boxes does not confuse the analysis.
    """
    lines = text.splitlines()
    prose_lines: List[str] = []
    in_code_fence = False
    in_roll_block = False
    for raw in lines:
        if _CODE_FENCE.match(raw):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if _ROLL_HEADER.match(raw):
            in_roll_block = True
            continue
        if _ITALIC_DAMAGE_LINE.match(raw):
            # terminates a ROLL block sequence in the canonical shape
            in_roll_block = False
            continue
        if in_roll_block:
            if _ROLL_FIELD.match(raw) or _INLINE_ROLL_LINE.match(raw) or not raw.strip():
                continue
            # first prose line after a ROLL block closes it
            in_roll_block = False
        if _UI_BOX_LINE.match(raw):
            continue
        # Strip inline code spans (`...`) from the line — they carry mechanism.
        prose_lines.append(_INLINE_CODE_SPAN.sub("", raw))
    return "\n".join(prose_lines)


def _paragraphs(prose: str) -> List[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", prose.strip()) if p.strip()]


def _sentences(paragraph: str) -> List[str]:
    # Keep sentence terminators. Light-touch stdlib split; good enough for
    # variance / paragraph-shape heuristics.
    parts = re.split(r"(?<=[.!?])\s+", paragraph.strip())
    return [s.strip() for s in parts if s.strip()]


def _normalize_em_dashes(s: str) -> str:
    # Auto-normalize "--" to em dash for the em-dash-presence check, so
    # ASCII-friendly drafting is not penalized.
    return s.replace("--", "—")


# ---------------------------------------------------------------------------
# Positive voice checks
# ---------------------------------------------------------------------------

def check_second_person_present(prose: str) -> List[str]:
    """Flag past-tense protagonist slippage.

    Heuristic: a sentence that contains "he"/"she"/"they" immediately followed
    by a past-tense verb (-ed ending, or the common irregulars) is suspect when
    the scene's protagonist is addressed in second-person. Intentionally
    conservative to avoid false positives on NPC third-person narration.
    """
    violations: List[str] = []
    past_pronoun_verb = re.compile(
        r"\b(he|she|they)\s+"
        r"(was|were|had|did|went|came|saw|said|took|gave|rolled|drove|struck|bled)\b",
        re.IGNORECASE,
    )
    # "You <past-tense-verb>" is also a tense slip for the protagonist.
    you_past = re.compile(
        r"\byou\s+"
        r"(drove|struck|rolled|gasped|turned|caught|fell|came|went|saw|said|had|was|were)\b",
        re.IGNORECASE,
    )
    for sent in _sentences(prose.replace("\n", " ")):
        if you_past.search(sent):
            violations.append(
                f"second-person present violation (past-tense 'you'): '{sent[:80]}'"
            )
        # Skip NPC-third-person sentences that clearly have a named subject.
        if past_pronoun_verb.search(sent) and not re.search(
            r"\b[A-Z][a-z]{2,}\s+(he|she|they)\b", sent
        ):
            # Accept past-tense narration for named NPCs but flag raw pronouns.
            if not re.search(r"\b[A-Z][a-z]+\b", sent):
                violations.append(
                    f"second-person present violation (third-person pronoun + past): '{sent[:80]}'"
                )
    return violations


def check_fragment_paragraph(prose: str, scene_type: str) -> List[str]:
    """Require at least one 1-3 word paragraph for emphasis in qualifying scenes."""
    if scene_type not in _FRAGMENT_REQUIRED_SCENES:
        return []
    for para in _paragraphs(prose):
        # Strip formatting markers for the word count.
        clean = re.sub(r"[*_`\"'.,;:!?—-]", "", para).strip()
        if 1 <= len(clean.split()) <= 3:
            return []
    return [
        f"fragment paragraph missing — {scene_type} needs at least one 1-3 word "
        "paragraph for emphasis (e.g. 'Opportunity.', 'Then, it stops.')"
    ]


def check_rhythm_variance(prose: str) -> List[str]:
    """Sentence-length stdev >= 3.0 when >= 4 sentences present."""
    all_sentences: List[str] = []
    for para in _paragraphs(prose):
        all_sentences.extend(_sentences(para))
    if len(all_sentences) < 4:
        return []
    lengths = [len(s.split()) for s in all_sentences]
    try:
        stdev = statistics.pstdev(lengths)
    except statistics.StatisticsError:
        return []
    if stdev < 3.0:
        shortest = min(all_sentences, key=lambda s: len(s.split()))
        longest = max(all_sentences, key=lambda s: len(s.split()))
        return [
            f"rhythm variance collapsed (stdev {stdev:.2f} < 3.0) — shortest: "
            f"'{shortest[:60]}'; longest: '{longest[:60]}'"
        ]
    return []


def check_paragraph_shape(prose: str) -> List[str]:
    """Each paragraph should be 1-4 sentences. 6+-sentence paragraphs flagged.

    Canonical voice permits 4-5 sentence paragraphs for decomposition bursts
    (the "A blackout has a sound — alarms, generators, fans..." pattern).
    The check only flags paragraphs that have truly lost their shape.
    """
    violations: List[str] = []
    for idx, para in enumerate(_paragraphs(prose), start=1):
        sent_count = len(_sentences(para))
        if sent_count >= 6:
            violations.append(
                f"paragraph overlong — paragraph {idx} has {sent_count} sentences; break into shorter beats"
            )
    return violations


def check_em_dash_presence(prose: str, scene_type: str) -> List[str]:
    """In structured scenes >= 3 sentences, require at least one em dash."""
    if scene_type not in _EM_DASH_REQUIRED_SCENES:
        return []
    sentence_count = sum(len(_sentences(p)) for p in _paragraphs(prose))
    if sentence_count < 3:
        return []
    normalized = _normalize_em_dashes(prose)
    if "—" in normalized:
        return []
    return [
        f"em-dash missing — {scene_type} prose >= 3 sentences requires at least "
        "one em-dash appositive or pivot"
    ]


def check_typography(text: str, scene_type: str) -> List[str]:
    """Combat/transition prose requires at least one **bold** entity/landmark."""
    if scene_type not in _BOLD_REQUIRED_SCENES:
        return []
    prose = _split_prose_region(text)
    if re.search(r"\*\*[^*]+\*\*", prose):
        return []
    return [
        f"typography — {scene_type} requires at least one **bold** tactical entity, "
        "named NPC, landmark, or power in the prose region"
    ]


def check_no_rhetorical_questions(prose: str) -> List[str]:
    """Prose sentences ending in '?' outside quoted dialogue are flagged."""
    violations: List[str] = []
    quote_tracker = 0
    current = ""
    in_quote = False
    # Very light parser: split text into segments outside quotes.
    for ch in prose:
        if ch == '"':
            if not in_quote and current.rstrip().endswith("?"):
                violations.append(
                    f"rhetorical question in narrator prose: '{current.strip()[-60:]}'"
                )
            current = ""
            in_quote = not in_quote
            continue
        current += ch
        quote_tracker += 0
    if not in_quote and current.strip().endswith("?"):
        violations.append(
            f"rhetorical question in narrator prose: '{current.strip()[-60:]}'"
        )
    return violations


def check_no_ellipses(prose: str) -> List[str]:
    """Flag '...' or '…' in the prose region outside quoted dialogue."""
    # Strip quoted runs first.
    without_quotes = re.sub(r'"[^"]*"', "", prose)
    if re.search(r"\.{3,}|…", without_quotes):
        return ["ellipsis in narrator prose — canonical voice uses periods, not ellipses"]
    return []


def check_mechanism_in_boxes(text: str) -> List[str]:
    """Flag mechanism language (DC N, HP, damage: N, rolled) in the prose region."""
    prose = _split_prose_region(text)
    violations: List[str] = []
    if re.search(r"\bDC\s?\d+\b", prose):
        violations.append(
            "mechanism smuggled into prose — 'DC N' belongs in the ROLL block"
        )
    if re.search(
        r"\brolled\b|\brolling\s+(?:dice|a\s+\d|the\s+dice|against)"
        r"|\byou\s+roll\s+(?:a\s+)?\d"
        r"|\byou\s+roll\s+(?:a\s+)?d\d",
        prose,
        re.IGNORECASE,
    ):
        violations.append(
            "mechanism smuggled into prose — dice language belongs in the ROLL block"
        )
    if re.search(r"\bdamage:\s*\d+\b", prose, re.IGNORECASE):
        violations.append(
            "mechanism smuggled into prose — 'damage: N' belongs in the italic damage line"
        )
    if re.search(r"\b(HP|SP)\b\s*[:=]\s*\d", prose):
        violations.append(
            "mechanism smuggled into prose — HP/SP numbers belong in the UI box"
        )
    return violations


# ---------------------------------------------------------------------------
# Signature hints (non-fatal)
# ---------------------------------------------------------------------------

def hint_negative_definition(prose: str) -> List[str]:
    """Return a non-fatal hint if no negative-definition pivot is present.

    Accepts three canonical shapes:
      - "It's not X. It's Y."                       (strict)
      - "It's not X. <decomposition>. This is Y."   (Passage 2 transition shape)
      - "Not a X. A Y."                             (compressed shape)
    """
    # Strict It's not X. It's Y.
    if re.search(r"[Ii]t'?s\s+not\b[^.!?]*[.!?]\s*[Ii]t'?s\b", prose):
        return []
    # Transition shape: any "It's not X." followed (within the passage) by a
    # "This is Y." declarative.
    if re.search(r"[Ii]t'?s\s+not\b", prose) and re.search(r"\bThis is\s+\w+", prose):
        return []
    # Compressed "Not a X. A Y." shape.
    if re.search(r"(?:^|[.!?]\s+)Not a\b[^.!?]*[.!?]\s*A\b", prose):
        return []
    return [
        "hint: signature-missing — no 'It's not X. It's Y.' negative-definition pivot; "
        "consider adding one at a reveal, judgment, or negotiation moment"
    ]


def hint_then_hinge(prose: str, scene_type: str) -> List[str]:
    """For transitions, report whether 'Then,' appears sentence-initially."""
    if scene_type != "transition":
        return []
    if re.search(r"(^|\n)\s*(\*\*)?Then,", prose):
        return []
    return [
        "hint: signature-missing — no 'Then,' beat-hinge; consider using it to "
        "advance without analytical connective tissue"
    ]


def hint_scene_cap(prose: str) -> List[str]:
    """Report whether the last paragraph is an aphoristic single-line sentence <= 12 words."""
    paras = _paragraphs(prose)
    if not paras:
        return ["hint: signature-missing — no closing paragraph present"]
    last = paras[-1]
    sentences = _sentences(last)
    if len(sentences) == 1 and len(sentences[0].split()) <= 12:
        return []
    return [
        "hint: signature-missing — final paragraph is not a compressed aphoristic "
        "single-line close (<=12 words); consider a scene-capping aphorism"
    ]


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def validate_narration(
    text: str,
    payload: Dict[str, Any],
) -> List[str]:
    """Validate narrator output against payload constraints and canonical voice.

    Returns a list of violation descriptions. Entries prefixed with ``hint:``
    are non-fatal signature reminders; callers running strict mode may ignore
    or filter them. An empty list means valid with no hints.
    """
    violations: List[str] = []

    scene_type = payload.get("scene_type", "")

    # Length check on the full text (ROLL block + UI box count against the envelope).
    word_count = len(text.split())
    min_words, max_words = _get_length_bounds(scene_type)
    if word_count < min_words:
        violations.append(f"Too short: {word_count} words, minimum {min_words}")
    if word_count > max_words:
        violations.append(f"Too long: {word_count} words, maximum {max_words}")

    # Forbidden-term scan on the full text (UI boxes and ROLL blocks are not
    # exempt from frame-break assistant-speak).
    text_lower = text.lower()
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in text_lower:
            violations.append(f"Forbidden term: '{pattern}'")

    # Payload-scoped forbidden list.
    forbidden = payload.get("forbidden", []) or payload.get("constraints", {}).get("forbidden", [])
    for f in forbidden:
        if isinstance(f, str) and f.lower() in text_lower:
            violations.append(f"Payload-forbidden term: '{f}'")

    # Voice-structural checks on the prose region only.
    prose = _split_prose_region(text)

    if scene_type in _VOICE_STRUCTURED_SCENES:
        violations.extend(check_second_person_present(prose))
        violations.extend(check_fragment_paragraph(prose, scene_type))
        violations.extend(check_rhythm_variance(prose))
        violations.extend(check_paragraph_shape(prose))
        violations.extend(check_em_dash_presence(prose, scene_type))
        violations.extend(check_typography(text, scene_type))
        violations.extend(check_no_rhetorical_questions(prose))
        violations.extend(check_no_ellipses(prose))

    violations.extend(check_mechanism_in_boxes(text))

    # Signature hints (non-fatal).
    if scene_type in _VOICE_STRUCTURED_SCENES:
        if scene_type in {"combat_turn", "dialogue", "transition", "situation_description"}:
            violations.extend(hint_negative_definition(prose))
        violations.extend(hint_then_hinge(prose, scene_type))
        if scene_type in _FRAGMENT_REQUIRED_SCENES:
            violations.extend(hint_scene_cap(prose))

    return violations


def _get_length_bounds(scene_type: str) -> Tuple[int, int]:
    """Return (min_words, max_words) for a scene type."""
    bounds = {
        # Widened for ROLL block + UI box overhead. Upper bound sized to admit
        # signature-rich reference beats (canonical Passage 1 = 176 words).
        "combat_turn": (40, 200),
        "scene_framing": (60, 150),
        "situation_description": (30, 100),
        # Widened to accommodate optional negotiation ROLL block and Intent
        # label (canonical Passage 3 = 167 words).
        "dialogue": (30, 200),
        "character_creation_beat": (80, 200),
        # Widened to accommodate canonical Passage 2 transition shape.
        "transition": (40, 240),
        "death_narration": (60, 150),
        "time_skip": (50, 150),
    }
    return bounds.get(scene_type, (20, 200))
