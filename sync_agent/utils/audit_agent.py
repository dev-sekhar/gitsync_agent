"""
audit_agent.py — Central Audit Agent (replaces logger.py)

Responsibility: Be the single, authoritative source of truth for all lifecycle
events across every agent. Writes both a machine-readable NDJSON log and
printf-style human-readable console output. Exposes a read API so the server
can surface the full audit trail to the frontend.

This is an *agent*, not just a logger:
  - It timestamps and structures every event.
  - It enforces a schema (AuditEntry) on every write.
  - It can summarise its own log on demand.
  - It logs its own initialisation and any write failures.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Log file location (project root / sync-agent / audit /)
# ---------------------------------------------------------------------------
LOG_FILE: Path = Path(__file__).parents[2] / "sync-agent" / "audit" / "sync_agent_audit.log"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@dataclass
class AuditEntry:
    action: str
    result: str                          # "Success" | "Failure" | "Warning"
    agent: str = "unknown"               # which agent emitted this entry
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def to_human(self) -> str:
        ts = self.timestamp[11:19]       # HH:MM:SS of the ISO string
        icon = "✓" if self.result == "Success" else ("!" if self.result == "Warning" else "✗")
        return f"[{ts}] {icon} [{self.agent}] {self.action}: {self.result}"


# ---------------------------------------------------------------------------
# Core audit operations
# ---------------------------------------------------------------------------

def log_action(
    action: str,
    result: str,
    details: Any = None,
    agent: str = "system",
) -> AuditEntry:
    """
    Write one structured audit entry.
    Returns the AuditEntry so callers can chain or inspect it.
    """
    entry = AuditEntry(
        action=action,
        result=result,
        agent=agent,
        details=details if isinstance(details, dict) else ({"info": details} if details is not None else {}),
    )

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    except OSError as exc:
        # Never crash the caller because the log failed — just warn to stderr
        print(f"[AuditAgent] WARNING: could not write log: {exc}", file=sys.stderr)

    print(entry.to_human())
    return entry


def get_logs(limit: int | None = None) -> list[dict]:
    """
    Return all audit entries (newest-first). Optionally cap at *limit* entries.
    """
    if not LOG_FILE.exists():
        return []

    entries: list[dict] = []
    with LOG_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    entries.reverse()
    return entries[:limit] if limit else entries


def summarise(n: int = 10) -> str:
    """
    Return a compact human-readable summary of the last *n* audit entries.
    Useful for agent self-reporting.
    """
    entries = get_logs(limit=n)
    if not entries:
        return "No audit entries found."
    lines = []
    for e in entries:
        ts = e.get("timestamp", "")[ 11:19]
        icon = "✓" if e.get("result") == "Success" else "✗"
        lines.append(f"  {ts} {icon} [{e.get('agent','?')}] {e.get('action','?')}")
    return "Recent audit trail:\n" + "\n".join(lines)
