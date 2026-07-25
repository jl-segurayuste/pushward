from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


def _run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _run("git", "init", "-q", cwd=repo)
    _run("git", "config", "user.email", "test@example.com", cwd=repo)
    _run("git", "config", "user.name", "Test", cwd=repo)
    return repo


def write(repo: Path, relpath: str, content: str) -> Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def commit_all(repo: Path, message: str = "commit") -> None:
    _run("git", "add", "-A", cwd=repo)
    _run("git", "commit", "-q", "-m", message, cwd=repo)


def stage_all(repo: Path) -> None:
    _run("git", "add", "-A", cwd=repo)
