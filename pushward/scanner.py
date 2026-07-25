from __future__ import annotations

import subprocess
from pathlib import Path


def list_files(repo_path: Path, *, staged: bool = False) -> list[Path]:
    """Ficheros a escanear: `git ls-files` (todo el árbol) o el diff en stage (para el hook)."""
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    else:
        cmd = ["git", "ls-files"]
    result = subprocess.run(
        cmd, cwd=repo_path, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return []
    return [repo_path / line for line in result.stdout.splitlines() if line]


def read_text(path: Path) -> str | None:
    """Lee un fichero como texto; None si no existe o no es texto (binario)."""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
