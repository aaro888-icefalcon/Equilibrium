"""Error handling — exception hierarchy and crash shutdown.

Exit codes per spec:
  0 = clean exit
  1 = recoverable error (save preserved)
  2 = fatal error (save may be corrupt)
  3 = save integrity error
  4 = narrator protocol error
  5 = engine internal error
"""

from __future__ import annotations

import os
import traceback
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------

class EmergenceError(Exception):
    """Base exception for all Emergence errors."""
    exit_code: int = 1


class RecoverableError(EmergenceError):
    """Error that can be recovered from. Save is intact."""
    exit_code = 1


class FatalError(EmergenceError):
    """Fatal error. Save may be corrupt."""
    exit_code = 2


class SaveIntegrityError(EmergenceError):
    """Save file corruption or version mismatch."""
    exit_code = 3


class NarratorProtocolError(EmergenceError):
    """Narrator communication failure."""
    exit_code = 4


class EngineInternalError(EmergenceError):
    """Internal engine bug. Should not happen in production."""
    exit_code = 5


# ---------------------------------------------------------------------------
# Crash shutdown
# ---------------------------------------------------------------------------

def crash_shutdown(error: Exception, state: Any = None, save_root: str = "") -> int:
    """Emergency shutdown — attempt to save state and return exit code.

    Returns the appropriate exit code for the error type.
    """
    exit_code = 1

    if isinstance(error, EmergenceError):
        exit_code = error.exit_code

    # Attempt emergency save if we have state and a save path
    if state is not None and save_root:
        try:
            _emergency_save(state, save_root)
        except Exception:
            # Emergency save failed — don't mask the original error
            exit_code = max(exit_code, 2)

    # Log the crash
    _log_crash(error, save_root)

    return exit_code


def _emergency_save(state: Any, save_root: str) -> None:
    """Attempt to write whatever state we have to a crash file."""
    crash_path = os.path.join(save_root, "crash_state.json")
    os.makedirs(save_root, exist_ok=True)

    try:
        from emergence.engine.schemas.serialization import to_json
        data = to_json(state) if hasattr(state, 'to_dict') else str(state)
        with open(crash_path, "w", encoding="utf-8") as f:
            f.write(data)
    except Exception:
        # If serialization fails, write a minimal crash marker
        with open(crash_path, "w", encoding="utf-8") as f:
            f.write(f'{{"crash": true, "error": "{type(state).__name__}"}}\n')


def _log_crash(error: Exception, save_root: str) -> None:
    """Write crash details to a log file."""
    log_dir = save_root or "."
    log_path = os.path.join(log_dir, "crash.log")

    try:
        os.makedirs(log_dir, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Error type: {type(error).__name__}\n")
            f.write(f"Message: {error}\n")
            f.write(traceback.format_exc())
            f.write(f"{'='*60}\n")
    except Exception:
        pass  # Logging failure is not critical


def classify_error(error: Exception) -> str:
    """Classify an error for user-facing messaging."""
    if isinstance(error, RecoverableError):
        return "recoverable"
    elif isinstance(error, SaveIntegrityError):
        return "save_corrupt"
    elif isinstance(error, NarratorProtocolError):
        return "narrator_failure"
    elif isinstance(error, FatalError):
        return "fatal"
    elif isinstance(error, EngineInternalError):
        return "internal"
    else:
        return "unknown"
