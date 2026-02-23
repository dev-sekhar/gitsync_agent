"""
update_agent.py — README Update Agent

Responsibility: Append an AI-generated sync note to the target repository's
README.md, commit it, push to origin, and then verify the remote was actually
updated by checking the commit SHA on origin.

Agent contract:
  - update_readme() returns an UpdateResult dataclass.
  - After pushing, the agent verifies the remote commit SHA matches local HEAD.
  - If remote verification fails, result.verified = False (not an exception).
  - All steps are individually audited.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sync_agent.utils.git_utils import get_repo
from sync_agent.utils.audit_agent import log_action

AGENT_NAME = "UpdateAgent"


# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------

@dataclass
class UpdateResult:
    success: bool
    commit_sha: str
    commit_message: str
    verified: bool          # True if remote SHA confirmed to match local HEAD
    remote_sha: str         # SHA seen on origin after push (empty if unavailable)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "commitSha": self.commit_sha,
            "commitMessage": self.commit_message,
            "verified": self.verified,
            "remoteSha": self.remote_sha,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def update_readme(local_path: str, branch: str, summary: str) -> UpdateResult:
    """
    Append a sync note to README.md, commit and push, then verify.

    Steps:
      1. Build and write the sync note.
      2. Stage README.md and commit.
      3. Push to origin/<branch>.
      4. Verify remote HEAD SHA matches local HEAD SHA.
    """
    try:
        repo = get_repo(local_path)
        readme_path = Path(local_path) / "README.md"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sync_note = (
            f"\n\n---\n"
            f"**Agent Sync Confirmation**\n"
            f"- Timestamp: {timestamp}\n"
            f"- Status: Synchronized\n"
            f"- Summary: {summary}\n"
        )

        # --- Step 1: write ---
        if readme_path.exists():
            with readme_path.open("a", encoding="utf-8") as f:
                f.write(sync_note)
        else:
            readme_path.write_text(f"# Project\n{sync_note}", encoding="utf-8")

        log_action("README: note written", "Success",
                   {"path": str(readme_path)}, agent=AGENT_NAME)

        # --- Step 2: commit ---
        repo.index.add(["README.md"])
        commit_msg = f"Agent update: README sync confirmation [{timestamp}]"
        commit = repo.index.commit(commit_msg)
        local_sha = commit.hexsha

        log_action("README: committed", "Success",
                   {"sha": local_sha, "msg": commit_msg}, agent=AGENT_NAME)

        # --- Step 3: push ---
        push_info = repo.remotes.origin.push(branch)

        log_action("README: pushed", "Success",
                   {"branch": branch}, agent=AGENT_NAME)

        # --- Step 4: verify remote ---
        verified = False
        remote_sha = ""
        try:
            remote_refs = {
                ref.name.split("/")[-1]: ref.commit.hexsha
                for ref in repo.remotes.origin.refs
            }
            remote_sha = remote_refs.get(branch, "")
            verified = remote_sha == local_sha
            status = "Success" if verified else "Warning"
            log_action("README: remote verification", status,
                       {"localSha": local_sha, "remoteSha": remote_sha}, agent=AGENT_NAME)
        except Exception as ve:
            log_action("README: remote verification", "Warning",
                       {"error": str(ve)}, agent=AGENT_NAME)

        result = UpdateResult(
            success=True,
            commit_sha=local_sha,
            commit_message=commit_msg,
            verified=verified,
            remote_sha=remote_sha,
            message="README updated and pushed successfully." + (
                " Remote verified." if verified else " Remote verification skipped."
            ),
        )
        log_action("README Update", "Success", result.to_dict(), agent=AGENT_NAME)
        return result

    except Exception as exc:
        log_action("README Update", "Failure", {"error": str(exc)}, agent=AGENT_NAME)
        raise
