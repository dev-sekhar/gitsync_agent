"""
git_utils.py — Python port of sync-agent/utils/git_utils.ts
Uses GitPython (git.Repo) instead of simple-git.
"""
from __future__ import annotations

import git
from git import Repo, InvalidGitRepositoryError


def get_repo(local_path: str) -> Repo:
    """Return a GitPython Repo object for the given path."""
    return Repo(local_path)


def check_is_repo(local_path: str) -> bool:
    """Return True if local_path is a valid git repository."""
    try:
        Repo(local_path)
        return True
    except InvalidGitRepositoryError:
        return False


def fetch_remote(repo: Repo, branch: str) -> None:
    """Fetch the 'origin' remote for the given branch."""
    repo.remotes.origin.fetch(branch)


def get_diff(repo: Repo, branch: str) -> str:
    """Return the unified diff between origin/<branch> and <branch>."""
    try:
        origin_ref = repo.remotes.origin.refs[branch]
        local_ref = repo.heads[branch]
        diff = repo.git.diff(origin_ref, local_ref)
        return diff
    except (IndexError, git.exc.GitCommandError):
        return repo.git.diff(f"origin/{branch}", branch)


def get_commit_count(repo: Repo, branch: str) -> dict[str, int]:
    """
    Return how many commits local is behind and ahead of origin/<branch>.
    Equivalent to: git rev-list --left-right --count origin/<branch>...<branch>
    """
    raw = repo.git.rev_list(
        "--left-right", "--count", f"origin/{branch}...{branch}"
    )
    parts = raw.strip().split("\t")
    behind = int(parts[0]) if len(parts) > 0 else 0
    ahead = int(parts[1]) if len(parts) > 1 else 0
    return {"behind": behind, "ahead": ahead}
