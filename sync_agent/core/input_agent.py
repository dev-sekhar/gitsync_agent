"""
input_agent.py — Input Validation Agent

Responsibility: Gate-keep every workflow by validating all user-supplied inputs
before anything touches Git or the network. Returns a structured ValidationResult
so callers can make informed decisions without parsing exception messages.

Agent contract:
  - validate_inputs() never returns a bare bool/dict; always returns ValidationResult.
  - Every check is individually reported in ValidationResult.checks.
  - Failures raise ValueError so the server can surface a clear HTTP 400.
  - All actions are audited via audit_agent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from sync_agent.utils.git_utils import check_is_repo, get_repo
from sync_agent.utils.audit_agent import log_action

AGENT_NAME = "InputAgent"


# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    success: bool
    local_path: str
    repo_url: str
    branch: str
    checks: dict[str, bool] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "localPath": self.local_path,
            "repoUrl": self.repo_url,
            "branch": self.branch,
            "checks": self.checks,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def validate_inputs(local_path: str, repo_url: str, branch: str) -> ValidationResult:
    """
    Run all pre-flight checks and return a ValidationResult.

    Checks performed (in order):
      1. local_path exists on disk
      2. local_path is a git repository
      3. repo_url is reachable (via git ls-remote)

    Raises ValueError on the first failed check so the workflow stops early.
    """
    checks: dict[str, bool] = {
        "path_exists": False,
        "is_git_repo": False,
        "remote_reachable": False,
    }

    # --- 1. Path existence ---
    if not os.path.exists(local_path):
        result = ValidationResult(
            success=False,
            local_path=local_path,
            repo_url=repo_url,
            branch=branch,
            checks=checks,
            message=f"Path does not exist: {local_path}",
        )
        log_action("Input Validation", "Failure", result.to_dict(), agent=AGENT_NAME)
        raise ValueError(result.message)

    checks["path_exists"] = True

    # --- 2. Git repo check ---
    if not check_is_repo(local_path):
        result = ValidationResult(
            success=False,
            local_path=local_path,
            repo_url=repo_url,
            branch=branch,
            checks=checks,
            message=f"Path is not a git repository: {local_path}",
        )
        log_action("Input Validation", "Failure", result.to_dict(), agent=AGENT_NAME)
        raise ValueError(result.message)

    checks["is_git_repo"] = True

    # --- 3. Remote connectivity ---
    try:
        repo = get_repo(local_path)
        repo.git.ls_remote(repo_url)
        checks["remote_reachable"] = True
    except Exception as exc:
        result = ValidationResult(
            success=False,
            local_path=local_path,
            repo_url=repo_url,
            branch=branch,
            checks=checks,
            message=f"Remote not reachable ({repo_url}): {exc}",
        )
        log_action("Input Validation", "Failure", result.to_dict(), agent=AGENT_NAME)
        raise ValueError(result.message)

    # --- All checks passed ---
    result = ValidationResult(
        success=True,
        local_path=local_path,
        repo_url=repo_url,
        branch=branch,
        checks=checks,
        message="All validation checks passed.",
    )
    log_action("Input Validation", "Success", result.to_dict(), agent=AGENT_NAME)
    return result
