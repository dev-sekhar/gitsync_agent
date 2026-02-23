"""
logger.py — Python port of sync-agent/utils/logger.ts
Writes NDJSON audit entries to sync-agent/audit/sync_agent_audit.log.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_FILE = Path(__file__).parents[2] / "sync-agent" / "audit" / "sync_agent_audit.log"


def log_action(action: str, result: str, details: Any = None) -> None:
    """Append an audit entry to the log file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "result": result,
    }
    if details is not None:
        entry["details"] = details

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[AUDIT] {action}: {result}")


def get_logs() -> list[dict]:
    """Read and parse all audit log entries (newest first)."""
    if not LOG_FILE.exists():
        return []

    entries = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Return newest first (mirror of .reverse() in TS)
    return list(reversed(entries))
