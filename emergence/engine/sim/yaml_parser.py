"""Minimal YAML subset parser — stdlib only.

Handles the subset of YAML used in the Emergence setting bible files:
- Key-value mappings with `:` separator
- Lists with `- ` prefix
- Nested indentation (2-space)
- Multi-line folded strings with `>` indicator
- Comments with `#`
- Numeric types (int, float, underscore-separated like 1_900_000)
- Approximate values (~400 → 400)
- Inline lists [a, b, c]
- Boolean values (true/false)
- Null values (null, ~)
- Quoted strings (single and double)

Does NOT handle: anchors, aliases, flow mappings, tags, multi-document, block scalars with `|`.
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Tuple


def parse_yaml(text: str) -> Any:
    """Parse a YAML text string into nested Python objects."""
    lines = _preprocess(text)
    if not lines:
        return {}
    result, _ = _parse_block(lines, 0, 0)
    return result


# ---------------------------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------------------------

def _preprocess(text: str) -> List[Tuple[int, str]]:
    """Strip comments and blank lines, return (indent, content) pairs."""
    result: List[Tuple[int, str]] = []
    in_folded = False
    folded_indent = 0

    for raw_line in text.split("\n"):
        # Strip inline comments (but not inside quotes)
        line = _strip_comment(raw_line)
        stripped = line.strip()

        if not stripped:
            # Blank line ends folded string
            if in_folded:
                in_folded = False
            continue

        indent = len(line) - len(line.lstrip())
        result.append((indent, stripped))

    return result


def _strip_comment(line: str) -> str:
    """Remove # comments that aren't inside quotes."""
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            return line[:i].rstrip()
    return line


# ---------------------------------------------------------------------------
# Block parsing
# ---------------------------------------------------------------------------

def _parse_block(
    lines: List[Tuple[int, str]], start: int, expected_indent: int
) -> Tuple[Any, int]:
    """Parse a block at a given indentation level. Returns (value, next_index)."""
    if start >= len(lines):
        return {}, start

    indent, content = lines[start]

    # Detect if this block is a list or a mapping
    if content.startswith("- ") or content == "-":
        return _parse_list(lines, start, indent)
    else:
        return _parse_mapping(lines, start, indent)


def _parse_mapping(
    lines: List[Tuple[int, str]], start: int, base_indent: int
) -> Tuple[dict, int]:
    """Parse a YAML mapping block."""
    result: dict = {}
    i = start

    while i < len(lines):
        indent, content = lines[i]

        if indent < base_indent:
            break
        if indent > base_indent:
            break  # shouldn't happen at this level

        # Handle list item that contains a mapping
        if content.startswith("- ") or content == "-":
            break

        # Parse key: value
        key, value_str = _split_key_value(content)
        if key is None:
            i += 1
            continue

        if value_str == ">":
            # Folded string: collect indented lines
            value, i = _parse_folded(lines, i + 1, base_indent)
            result[key] = value
        elif value_str == "":
            # Value is a nested block
            if i + 1 < len(lines) and lines[i + 1][0] > base_indent:
                child_indent = lines[i + 1][0]
                value, i = _parse_block(lines, i + 1, child_indent)
                result[key] = value
            else:
                result[key] = None
                i += 1
        else:
            result[key] = _parse_scalar(value_str)
            i += 1

    return result, i


def _parse_list(
    lines: List[Tuple[int, str]], start: int, base_indent: int
) -> Tuple[list, int]:
    """Parse a YAML list block."""
    result: list = []
    i = start

    while i < len(lines):
        indent, content = lines[i]

        if indent < base_indent:
            break
        is_list_item = content.startswith("- ") or content == "-"
        if indent > base_indent and not is_list_item:
            # Continuation of previous item's nested block — skip
            i += 1
            continue
        if not is_list_item:
            break

        item_content = content[2:].strip() if len(content) > 1 else ""

        if not item_content:
            # List item with nested block
            if i + 1 < len(lines) and lines[i + 1][0] > base_indent:
                child_indent = lines[i + 1][0]
                value, i = _parse_block(lines, i + 1, child_indent)
                result.append(value)
            else:
                result.append(None)
                i += 1
        elif ":" in item_content and not item_content.startswith("["):
            # List item is a mapping (e.g., "- id: foo")
            # Parse this item and any continuation lines as a mapping
            item_key, item_val_str = _split_key_value(item_content)
            if item_key is not None:
                item_dict: dict = {}
                if item_val_str == ">":
                    val, next_i = _parse_folded(lines, i + 1, base_indent)
                    item_dict[item_key] = val
                    i = next_i
                elif item_val_str == "":
                    if i + 1 < len(lines) and lines[i + 1][0] > base_indent:
                        child_indent = lines[i + 1][0]
                        val, next_i = _parse_block(lines, i + 1, child_indent)
                        item_dict[item_key] = val
                        i = next_i
                    else:
                        item_dict[item_key] = None
                        i += 1
                else:
                    item_dict[item_key] = _parse_scalar(item_val_str)
                    i += 1

                # Continue reading mapping keys at the deeper indent
                if i < len(lines):
                    # The continuation indent for mapping keys inside a list item
                    # is typically base_indent + 4 (for "- " + 2 more)
                    cont_indent = base_indent + 4
                    # But sometimes it's base_indent + 2
                    if i < len(lines) and lines[i][0] > base_indent:
                        cont_indent = lines[i][0]

                    while i < len(lines) and lines[i][0] >= cont_indent:
                        ci, cc = lines[i]
                        if ci < cont_indent:
                            break
                        if cc.startswith("- "):
                            # Nested list inside this mapping item
                            nk, nv = _split_key_value(cc)
                            if nk is None:
                                # It's a sub-list continuation
                                break
                        ck, cv_str = _split_key_value(cc)
                        if ck is not None:
                            if cv_str == ">":
                                val, i = _parse_folded(lines, i + 1, cont_indent)
                                item_dict[ck] = val
                            elif cv_str == "":
                                if i + 1 < len(lines) and lines[i + 1][0] > ci:
                                    child_indent = lines[i + 1][0]
                                    val, i = _parse_block(lines, i + 1, child_indent)
                                    item_dict[ck] = val
                                else:
                                    item_dict[ck] = None
                                    i += 1
                            else:
                                item_dict[ck] = _parse_scalar(cv_str)
                                i += 1
                        else:
                            i += 1

                result.append(item_dict)
            else:
                result.append(_parse_scalar(item_content))
                i += 1
        else:
            result.append(_parse_scalar(item_content))
            i += 1

    return result, i


def _parse_folded(
    lines: List[Tuple[int, str]], start: int, parent_indent: int
) -> Tuple[str, int]:
    """Parse a folded (>) multi-line string."""
    parts: List[str] = []
    i = start

    while i < len(lines):
        indent, content = lines[i]
        if indent <= parent_indent:
            break
        parts.append(content)
        i += 1

    return " ".join(parts), i


# ---------------------------------------------------------------------------
# Key-value splitting
# ---------------------------------------------------------------------------

def _split_key_value(content: str) -> Tuple[Optional[str], str]:
    """Split 'key: value' or 'key:' into (key, value_str).
    Returns (None, '') if not a key-value pair."""
    # Find first colon not inside quotes
    in_single = False
    in_double = False
    for idx, ch in enumerate(content):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            # Must be followed by space, EOL, or nothing
            if idx + 1 >= len(content) or content[idx + 1] == " ":
                key = content[:idx].strip()
                value = content[idx + 1:].strip() if idx + 1 < len(content) else ""
                return key, value

    return None, ""


# ---------------------------------------------------------------------------
# Scalar parsing
# ---------------------------------------------------------------------------

_NUMERIC_RE = re.compile(
    r"^[~]?[-+]?[0-9][0-9_]*(?:\.[0-9_]*)?(?:[eE][-+]?[0-9]+)?$"
)
_INLINE_LIST_RE = re.compile(r"^\[(.+)\]$")


def _parse_scalar(value: str) -> Any:
    """Parse a scalar YAML value."""
    if not value:
        return None

    # Quoted strings
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]

    # Inline list [a, b, c]
    m = _INLINE_LIST_RE.match(value)
    if m:
        items = [_parse_scalar(item.strip()) for item in m.group(1).split(",")]
        return items

    # Boolean
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    # Null
    if lower in ("null", "~"):
        return None

    # Approximate value (~400 → 400)
    clean = value
    if clean.startswith("~"):
        clean = clean[1:]

    # Numeric
    if _NUMERIC_RE.match("~" + clean if value.startswith("~") else clean):
        # Remove underscores for parsing
        num_str = clean.replace("_", "")
        try:
            if "." in num_str or "e" in num_str.lower():
                return float(num_str)
            return int(num_str)
        except ValueError:
            pass

    return value
