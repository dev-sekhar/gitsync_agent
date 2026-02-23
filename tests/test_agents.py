"""
tests/test_agents.py
Automated tests for all sync-agent Python modules (post-upgrade).
Uses unittest.mock to avoid real git, filesystem, and Gemini API calls.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# audit_agent tests
# ===========================================================================

class TestAuditAgent:
    def test_log_action_writes_valid_json(self, tmp_path, monkeypatch):
        log_file = tmp_path / "audit" / "sync_agent_audit.log"
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", log_file)

        from sync_agent.utils.audit_agent import log_action
        entry = log_action("TestAction", "Success", {"key": "val"}, agent="TestAgent")

        assert log_file.exists()
        row = json.loads(log_file.read_text().strip())
        assert row["action"] == "TestAction"
        assert row["result"] == "Success"
        assert row["agent"] == "TestAgent"
        assert row["details"]["key"] == "val"

    def test_get_logs_returns_newest_first(self, tmp_path, monkeypatch):
        log_file = tmp_path / "a.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        rows = [
            json.dumps({"timestamp": "A", "action": "First", "result": "Success", "agent": "x", "details": {}}),
            json.dumps({"timestamp": "B", "action": "Second", "result": "Success", "agent": "x", "details": {}}),
        ]
        log_file.write_text("\n".join(rows) + "\n")
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", log_file)

        from sync_agent.utils.audit_agent import get_logs
        logs = get_logs()
        assert logs[0]["action"] == "Second"
        assert logs[1]["action"] == "First"

    def test_get_logs_empty_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE",
                            tmp_path / "missing.log")
        from sync_agent.utils.audit_agent import get_logs
        assert get_logs() == []

    def test_summarise_returns_string(self, tmp_path, monkeypatch):
        log_file = tmp_path / "a.log"
        log_file.write_text(
            json.dumps({"timestamp": "2024-01-01T00:00:00Z", "action": "A",
                        "result": "Success", "agent": "X", "details": {}}) + "\n"
        )
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", log_file)
        from sync_agent.utils.audit_agent import summarise
        s = summarise()
        assert "audit trail" in s.lower()


# ===========================================================================
# input_agent tests
# ===========================================================================

class TestInputAgent:
    def test_raises_when_path_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        from sync_agent.core.input_agent import validate_inputs
        with pytest.raises(ValueError, match="Path does not exist"):
            validate_inputs("/nonexistent/abc", "https://x.git", "main")

    def test_raises_when_not_repo(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        non_repo = tmp_path / "notarepo"
        non_repo.mkdir()
        from sync_agent.core.input_agent import validate_inputs
        with pytest.raises(ValueError):
            validate_inputs(str(non_repo), "https://x.git", "main")

    def test_success_returns_validation_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        with (
            patch("sync_agent.core.input_agent.check_is_repo", return_value=True),
            patch("sync_agent.core.input_agent.get_repo") as mock_repo,
        ):
            fake_repo = MagicMock()
            fake_repo.git.ls_remote.return_value = ""
            mock_repo.return_value = fake_repo

            from sync_agent.core.input_agent import validate_inputs, ValidationResult
            result = validate_inputs(str(tmp_path), "https://x.git", "main")

        assert isinstance(result, ValidationResult)
        assert result.success is True
        assert result.checks["path_exists"] is True
        assert result.checks["is_git_repo"] is True
        assert result.checks["remote_reachable"] is True

    def test_to_dict_has_correct_keys(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        with (
            patch("sync_agent.core.input_agent.check_is_repo", return_value=True),
            patch("sync_agent.core.input_agent.get_repo") as mock_repo,
        ):
            fake_repo = MagicMock()
            mock_repo.return_value = fake_repo
            from sync_agent.core.input_agent import validate_inputs
            result = validate_inputs(str(tmp_path), "https://x.git", "main")
        d = result.to_dict()
        assert "success" in d
        assert "checks" in d
        assert "localPath" in d


# ===========================================================================
# sync_agent tests
# ===========================================================================

class TestSyncAgent:
    def _patch(self, behind, ahead, diff):
        return (
            patch("sync_agent.core.sync_agent.get_repo", return_value=MagicMock()),
            patch("sync_agent.core.sync_agent.fetch_remote"),
            patch("sync_agent.core.sync_agent.get_commit_count",
                  return_value={"behind": behind, "ahead": ahead}),
            patch("sync_agent.core.sync_agent.get_diff", return_value=diff),
        )

    def test_synced_decision(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        with self._patch(0, 0, "")[0], self._patch(0, 0, "")[1], \
             self._patch(0, 0, "")[2], self._patch(0, 0, "")[3]:
            from sync_agent.core.sync_agent import verify_sync
            status = verify_sync("/p", "main")
        assert status.is_synced is True
        assert status.decision == "proceed_to_readme_update"

    def test_behind_decision(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        patches = self._patch(3, 0, "")
        with patches[0], patches[1], patches[2], patches[3]:
            from sync_agent.core.sync_agent import verify_sync
            status = verify_sync("/p", "main")
        assert status.behind == 3
        assert status.decision == "local_behind_pull_recommended"

    def test_ahead_decision(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        patches = self._patch(0, 2, "")
        with patches[0], patches[1], patches[2], patches[3]:
            from sync_agent.core.sync_agent import verify_sync
            status = verify_sync("/p", "main")
        assert status.ahead == 2
        assert status.decision == "local_ahead_push_recommended"

    def test_diff_capped_at_5000(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        patches = self._patch(0, 0, "x" * 10000)
        with patches[0], patches[1], patches[2], patches[3]:
            from sync_agent.core.sync_agent import verify_sync
            status = verify_sync("/p", "main")
        assert len(status.diff) == 5000

    def test_to_dict_camel_case(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        patches = self._patch(0, 0, "")
        with patches[0], patches[1], patches[2], patches[3]:
            from sync_agent.core.sync_agent import verify_sync
            status = verify_sync("/p", "main")
        d = status.to_dict()
        assert "isSynced" in d
        assert "hasDiff" in d
        assert "decision" in d


# ===========================================================================
# cleanup_agent tests
# ===========================================================================

class TestCleanupAgent:
    def test_raises_without_confirmation(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        from sync_agent.core.cleanup_agent import cleanup_local
        with pytest.raises(ValueError, match="not confirmed"):
            cleanup_local(str(tmp_path), confirmed=False)

    def test_deletes_when_confirmed(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "audit.log")
        target = tmp_path / "target"
        target.mkdir()
        (target / "file.txt").write_text("hello")

        from sync_agent.core.cleanup_agent import cleanup_local
        result = cleanup_local(str(target), confirmed=True)

        assert result.success is True
        assert not target.exists()

    def test_archives_before_delete(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "audit.log")
        target = tmp_path / "target"
        target.mkdir()
        (target / "data.txt").write_text("important data")

        from sync_agent.core.cleanup_agent import cleanup_local
        result = cleanup_local(str(target), confirmed=True, archive=True)

        assert result.archived is True
        assert result.archive_path.endswith(".zip")
        assert Path(result.archive_path).exists()
        assert not target.exists()


# ===========================================================================
# update_agent tests
# ===========================================================================

class TestUpdateAgent:
    def test_appends_to_existing_readme(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        readme = tmp_path / "README.md"
        readme.write_text("# Existing\n")

        fake_commit = MagicMock()
        fake_commit.hexsha = "abc123"
        fake_index = MagicMock()
        fake_index.commit.return_value = fake_commit
        fake_remote = MagicMock()
        fake_remote.refs = {}
        fake_repo = MagicMock()
        fake_repo.index = fake_index
        fake_repo.remotes.origin = fake_remote

        with patch("sync_agent.core.update_agent.get_repo", return_value=fake_repo):
            from sync_agent.core.update_agent import update_readme
            result = update_readme(str(tmp_path), "main", "Fixed a bug")

        assert result.success is True
        assert result.commit_sha == "abc123"
        assert "Agent Sync Confirmation" in readme.read_text()
        assert "Fixed a bug" in readme.read_text()

    def test_creates_readme_if_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        fake_commit = MagicMock(); fake_commit.hexsha = "def456"
        fake_repo = MagicMock()
        fake_repo.index.commit.return_value = fake_commit
        fake_repo.remotes.origin.refs = {}

        with patch("sync_agent.core.update_agent.get_repo", return_value=fake_repo):
            from sync_agent.core.update_agent import update_readme
            update_readme(str(tmp_path), "main", "Init")

        assert (tmp_path / "README.md").exists()
        assert "# Project" in (tmp_path / "README.md").read_text()


# ===========================================================================
# analysis_agent tests
# ===========================================================================

class TestAnalysisAgent:
    def test_empty_diff_returns_synced_message(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        from sync_agent.ai.analysis_agent import analyze_diff
        result = analyze_diff("")
        assert "synchronized" in result.lower()

    def test_calls_gemini_on_real_diff(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        fake_response = MagicMock()
        fake_response.text = "Added a new utility function."
        fake_model = MagicMock()
        fake_model.generate_content.return_value = fake_response

        with patch("sync_agent.ai.analysis_agent.genai.GenerativeModel",
                   return_value=fake_model):
            from sync_agent.ai import analysis_agent
            result = analysis_agent.analyze_diff("diff --git a/foo.py\n+def bar(): pass")

        assert "Added" in result

    def test_returns_error_on_exception(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sync_agent.utils.audit_agent.LOG_FILE", tmp_path / "a.log")
        fake_model = MagicMock()
        fake_model.generate_content.side_effect = Exception("quota exceeded")

        with patch("sync_agent.ai.analysis_agent.genai.GenerativeModel",
                   return_value=fake_model):
            from sync_agent.ai import analysis_agent
            result = analysis_agent.analyze_diff("some diff")

        assert "error" in result.lower()
