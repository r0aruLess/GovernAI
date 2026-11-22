import hashlib
import json
import os
from datetime import datetime, timezone

LOG_PATH = "outputs/audit_log.jsonl"
GENESIS = "0" * 64
_prev = None


def _digest(entry: dict) -> str:
    return hashlib.sha256(
        json.dumps(entry, sort_keys=True, default=str).encode()
    ).hexdigest()


def _load_prev() -> str:
    if not os.path.exists(LOG_PATH):
        return GENESIS
    with open(LOG_PATH, encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
    return json.loads(lines[-1])["hash"] if lines else GENESIS


def log_event(event: str, severity: str, details: dict):
    global _prev
    os.makedirs("outputs", exist_ok=True)
    if _prev is None:
        _prev = _load_prev()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "severity": severity,
        "details": details,
        "prev_hash": _prev,
    }
    entry["hash"] = _digest(entry)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    _prev = entry["hash"]


def verify_log() -> bool:
    """True if no log entry has been altered or removed."""
    prev = GENESIS
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            stored = entry.pop("hash")
            if entry["prev_hash"] != prev or _digest(entry) != stored:
                return False
            prev = stored
    return True