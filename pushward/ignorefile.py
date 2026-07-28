from __future__ import annotations

import fnmatch
from pathlib import Path

IGNORE_FILENAME = ".pushwardignore"


def load_patterns(repo_path: Path) -> list[str]:
    """Patrones estilo .gitignore para excluir del escaneo por completo --
    pensado para los propios fixtures de test de una herramienta de seguridad,
    que a propósito parecen secretos/DNI reales para poder probar los checks.
    """
    ignore_file = repo_path / IGNORE_FILENAME
    if not ignore_file.exists():
        return []
    patterns = []
    for line in ignore_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)
    return patterns


def is_ignored(relpath: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relpath, pattern) for pattern in patterns)
