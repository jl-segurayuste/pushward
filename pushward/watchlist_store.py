from __future__ import annotations

import re
from pathlib import Path

WATCHLIST_PATH = Path.home() / ".config" / "pushward" / "watchlist.txt"

_SEPARATOR_RE = re.compile(r"[\s._-]+")


def load_entries(path: Path = WATCHLIST_PATH) -> list[str]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    return entries


def add_entry(value: str, path: Path = WATCHLIST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_entries(path)
    if value in existing:
        return
    with path.open("a", encoding="utf-8") as f:
        f.write(value + "\n")


def remove_entry(value: str, path: Path = WATCHLIST_PATH) -> bool:
    existing = load_entries(path)
    if value not in existing:
        return False
    remaining = [e for e in existing if e != value]
    path.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")
    return True


def build_pattern(entry: str) -> re.Pattern[str]:
    """Casa variantes de separador (punto/guion/guion_bajo/espacio/sin separador),
    insensible a mayúsculas -- la misma clase de miss que dejó pasar
    "Ruben.Blanco" en una primera pasada case-sensitive de sustitución real.
    """
    tokens = [t for t in _SEPARATOR_RE.split(entry.strip()) if t]
    if not tokens:
        return re.compile(r"(?!x)x")  # nunca casa
    inner = r"[\s._-]*".join(re.escape(t) for t in tokens)
    return re.compile(rf"\b{inner}\b", re.IGNORECASE)
