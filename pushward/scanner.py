from __future__ import annotations

import subprocess
from pathlib import Path

# Árbol vacío de git -- objeto especial ya presente en cualquier repo, útil
# para diffear "todo lo que hay en <commit>" cuando no existe un punto de
# partida real (primer push de una rama nueva).
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ZERO_OID = "0" * 40


def _git_name_only(repo_path: Path, cmd: list[str]) -> list[Path]:
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [repo_path / line for line in result.stdout.splitlines() if line]


def list_files(repo_path: Path, *, staged: bool = False) -> list[Path]:
    """Ficheros a escanear: `git ls-files` (todo el árbol) o el diff en stage."""
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    else:
        cmd = ["git", "ls-files"]
    return _git_name_only(repo_path, cmd)


def diff_files(repo_path: Path, range_arg: str) -> list[Path]:
    """Ficheros tocados en un rango de commits, p.ej. "<remote_oid>..<local_oid>"
    -- lo que de verdad se necesita en un hook pre-push, donde el stage ya
    está vacío (el commit ya se hizo) y `list_files(staged=True)` no vería nada.
    """
    cmd = ["git", "diff", "--name-only", "--diff-filter=ACM", range_arg]
    return _git_name_only(repo_path, cmd)


def read_text(path: Path) -> str | None:
    """Lee un fichero como texto; None si no existe o no es texto (binario)."""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
