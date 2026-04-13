"""Input handler — parses player input into intents.

Recognizes meta commands (/save, /quit, etc.), numeric choices,
and freeform text input.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class Intent:
    """Parsed player intent from raw input."""

    def __init__(
        self,
        is_meta_command: bool = False,
        meta_command: Optional[str] = None,
        meta_args: Optional[List[str]] = None,
        target_choice: Optional[int] = None,
        freeform_text: Optional[str] = None,
    ) -> None:
        self.is_meta_command = is_meta_command
        self.meta_command = meta_command
        self.meta_args = meta_args or []
        self.target_choice = target_choice
        self.freeform_text = freeform_text

    def __repr__(self) -> str:
        if self.is_meta_command:
            return f"Intent(meta={self.meta_command})"
        if self.target_choice is not None:
            return f"Intent(choice={self.target_choice})"
        return f"Intent(text={self.freeform_text!r})"


META_COMMANDS = {
    "/save": "save",
    "/quit": "quit",
    "/exit": "quit",
    "/status": "status",
    "/help": "help",
    "/inventory": "inventory",
    "/inv": "inventory",
    "/map": "map",
    "/character": "character",
    "/char": "character",
    "/history": "history",
}


class InputHandler:
    """Parses raw player input into Intent objects."""

    def parse_input(
        self,
        raw: str,
        num_choices: int = 0,
    ) -> Intent:
        """Parse raw input string into an Intent.

        Args:
            raw: Raw input string from player.
            num_choices: Number of available choices (0 = freeform mode).

        Returns:
            Intent describing the player's action.
        """
        stripped = raw.strip()

        if not stripped:
            return Intent(freeform_text="")

        # Meta commands
        if stripped.startswith("/"):
            parts = stripped.split(None, 1)
            cmd_key = parts[0].lower()
            args = parts[1].split() if len(parts) > 1 else []

            canonical = META_COMMANDS.get(cmd_key)
            if canonical:
                return Intent(
                    is_meta_command=True,
                    meta_command=canonical,
                    meta_args=args,
                )
            # Unknown slash command — treat as freeform
            return Intent(freeform_text=stripped)

        # Numeric choice
        if num_choices > 0:
            try:
                choice = int(stripped)
                if 1 <= choice <= num_choices:
                    return Intent(target_choice=choice)
            except ValueError:
                pass

            # Try matching by letter (a=1, b=2, ...)
            if len(stripped) == 1 and stripped.isalpha():
                idx = ord(stripped.lower()) - ord("a") + 1
                if 1 <= idx <= num_choices:
                    return Intent(target_choice=idx)

        # Freeform text
        return Intent(freeform_text=stripped)

    def format_choices(
        self,
        choices: List[str],
        prompt: str = "Choose:",
    ) -> str:
        """Format a list of choices for display."""
        lines = [prompt]
        for i, choice in enumerate(choices, 1):
            lines.append(f"  {i}. {choice}")
        return "\n".join(lines)
