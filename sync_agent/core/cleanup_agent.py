"""
cleanup_agent.py — Cleanup / Archive Agent

Responsibility: Safely remove the local repository folder after the sync
workflow is complete. Never deletes without explicit confirmation.
Optionally archives the folder to a .zip before deletion.

Agent contract:
  - cleanup_local() returns a CleanupResult dataclass.
  - confirmed=False always raises — the agent never guesses about deletion.
  - If archive=True, the folder is zipped first; the archive path is in the result.
  - All decisions are logged before execution.
"""
from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sync_agent.utils.audit_agent import log_action

AGENT_NAME = "CleanupAgent"


# ---------------------------------------------------------------------------
# Structured result
# ---------------------------------------------------------------------------

@dataclass
class CleanupResult:
    success: bool
    local_path: str
    archived: bool
    archive_path: str       # path of .zip if archived, else ""
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "localPath": self.local_path,
            "archived": self.archived,
            "archivePath": self.archive_path,
            "message": self.message,
        }


# ---------------------------------------------------------------------------
# Agent entry point
# ---------------------------------------------------------------------------

def cleanup_local(local_path: str, confirmed: bool, archive: bool = False) -> CleanupResult:
    """
    Delete (or archive-then-delete) the local repository folder.

    Parameters:
        local_path  – absolute path to delete.
        confirmed   – must be True; any other value raises immediately.
        archive     – if True, zip the folder beside it before deletion.

    Returns CleanupResult with details of what happened.
    """
    # --- Safety gate: explicit confirmation required ---
    if not confirmed:
        log_action(
            "Cleanup: confirmation gate",
            "Failure",
            {"reason": "deletion not confirmed by user", "localPath": local_path},
            agent=AGENT_NAME,
        )
        raise ValueError("Deletion not confirmed. Set confirmed=True to proceed.")

    log_action("Cleanup: confirmation received", "Success",
               {"localPath": local_path, "archive": archive}, agent=AGENT_NAME)

    archive_path = ""
    archived = False

    try:
        # --- Optional: archive before delete ---
        if archive and Path(local_path).exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = Path(local_path).parent / f"{Path(local_path).name}_archive_{ts}.zip"
            with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zf:
                for file in Path(local_path).rglob("*"):
                    zf.write(file, file.relative_to(Path(local_path).parent))
            archive_path = str(zip_name)
            archived = True
            log_action("Cleanup: archived", "Success",
                       {"archivePath": archive_path}, agent=AGENT_NAME)

        # --- Delete ---
        shutil.rmtree(local_path)
        log_action("Cleanup: deleted", "Success",
                   {"localPath": local_path}, agent=AGENT_NAME)

        result = CleanupResult(
            success=True,
            local_path=local_path,
            archived=archived,
            archive_path=archive_path,
            message=f"Folder deleted.{' Archive saved to: ' + archive_path if archived else ''}",
        )
        log_action("Cleanup", "Success", result.to_dict(), agent=AGENT_NAME)
        return result

    except Exception as exc:
        log_action("Cleanup", "Failure", {"error": str(exc), "localPath": local_path},
                   agent=AGENT_NAME)
        raise
