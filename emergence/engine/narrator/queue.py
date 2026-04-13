"""Narrator queue — communication channel between engine and narrator.

Protocol per spec: engine writes NarratorPayload to JSONL queue,
prints ===NARRATION_PAYLOAD=== marker. MockNarrationQueue for testing.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Protocol

from emergence.engine.schemas.narrator import NarratorPayload


class NarrationChannel(Protocol):
    """Abstract narration channel. Engine emits, narrator responds."""

    def emit(self, payload: Dict[str, Any]) -> str:
        """Emit a narration payload and return the narrator's response."""
        ...


class MockNarrationQueue:
    """Test narrator — returns placeholder text immediately."""

    def __init__(self) -> None:
        self.history: list[Dict[str, Any]] = []

    def emit(self, payload: Dict[str, Any]) -> str:
        self.history.append(payload)
        scene_type = payload.get("scene_type", "unknown")
        return f"[NARRATION: {scene_type}]"


class FileNarrationQueue:
    """Writes payloads to a JSONL file and reads responses.

    For live play, a separate narrator process reads the queue.
    For testing, pair with MockNarrationQueue instead.
    """

    def __init__(self, queue_dir: str) -> None:
        self.queue_dir = queue_dir
        self.seq = 0
        os.makedirs(queue_dir, exist_ok=True)
        self._load_seq()

    def _load_seq(self) -> None:
        seq_path = os.path.join(self.queue_dir, "narration_seq.txt")
        if os.path.exists(seq_path):
            with open(seq_path, "r") as f:
                try:
                    self.seq = int(f.read().strip())
                except ValueError:
                    self.seq = 0

    def _save_seq(self) -> None:
        seq_path = os.path.join(self.queue_dir, "narration_seq.txt")
        with open(seq_path, "w") as f:
            f.write(str(self.seq))

    def emit(self, payload: Dict[str, Any]) -> str:
        self.seq += 1
        payload["_seq"] = self.seq

        # Write to JSONL queue
        queue_path = os.path.join(self.queue_dir, "narration_queue.jsonl")
        with open(queue_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

        self._save_seq()

        # In live mode, this would block waiting for narrator response.
        # For now, return a placeholder indicating the payload was queued.
        return f"[QUEUED:{self.seq}]"

    def read_response(self, seq: int) -> Optional[str]:
        """Read a narrator response for a given sequence number."""
        resp_path = os.path.join(self.queue_dir, f"response_{seq}.txt")
        if os.path.exists(resp_path):
            with open(resp_path, "r", encoding="utf-8") as f:
                return f.read()
        return None
