"""
sync_agent.py — Sync Verification Agent

Responsibility: Fetch the remote, calculate divergence, and return a rich
SyncStatus so downstream agents (analysis, update) can make informed decisions.

Agent contract:
  - verify_sync() always returns a SyncStatus dataclass.
  - SyncStatus includes a human-readable `decision` field describing what the
    agent recommends should happen next.
  - Every sub-step is individually logged so the audit trail is granular.
  - The diff is capped at 5000 chars to avoid bloating the log/UI.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

from sync_agent.utils.git_utils import get_repo, fetch_remote, get_diff, get_commit_count
from sync_agent.utils.audit_agent import log_action

AGENT_NAME = "SyncAgent"


# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------

@dataclass
class SyncStatus:
    behind: int
    ahead: int
    has_diff: bool
    diff: str
    is_synced: bool
    decision: str   # agent's recommended next action

    def to_dict(self) -> dict:
        d = asdict(self)
        # Rename keys to camelCase for frontend compatibility
        return {
            "behind": d["behind"],
            "ahead": d["ahead"],
            "hasDiff": d["has_diff"],
            "diff": d["diff"],
            "isSynced": d["is_synced"],
            "decision": d["decision"],
        }


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def verify_sync(local_path: str, branch: str) -> SyncStatus:
    """
    Fetch remote, compute divergence, and return a SyncStatus with a decision.

    Decision logic:
      - is_synced → "proceed_to_readme_update"
      - ahead > 0 → "local_ahead_push_recommended"
      - behind > 0 → "local_behind_pull_recommended"
      - has_diff only → "unstaged_changes_detected"
    """
    try:
        log_action("Sync: fetching remote", "Success",
                   {"localPath": local_path, "branch": branch}, agent=AGENT_NAME)

        repo = get_repo(local_path)
        fetch_remote(repo, branch)

        counts = get_commit_count(repo, branch)
        behind: int = counts["behind"]
        ahead: int = counts["ahead"]

        log_action("Sync: commit count", "Success",
                   {"behind": behind, "ahead": ahead}, agent=AGENT_NAME)

        diff: str = get_diff(repo, branch)
        has_diff = len(diff) > 0
        is_synced = behind == 0 and ahead == 0 and not has_diff

        # --- Decision ---
        if is_synced:
            decision = "proceed_to_readme_update"
        elif ahead > 0 and behind == 0:
            decision = "local_ahead_push_recommended"
        elif behind > 0:
            decision = "local_behind_pull_recommended"
        else:
            decision = "unstaged_changes_detected"

        status = SyncStatus(
            behind=behind,
            ahead=ahead,
            has_diff=has_diff,
            diff=diff[:5000],
            is_synced=is_synced,
            decision=decision,
        )

        log_action("Sync Verification", "Success", {
            "isSynced": is_synced,
            "behind": behind,
            "ahead": ahead,
            "hasDiff": has_diff,
            "decision": decision,
        }, agent=AGENT_NAME)

        return status

    except Exception as exc:
        log_action("Sync Verification", "Failure", {"error": str(exc)}, agent=AGENT_NAME)
        raise
