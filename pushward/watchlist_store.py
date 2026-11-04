from __future__ import annotations

import os
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


def _write(path: Path, text: str) -> None:
    # La watchlist guarda justo lo que no debe salir a ningún sitio (nombres, DNI, teléfonos):
    # solo legible por su dueño, aunque la umask del sistema sea 022.
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.chmod(path, 0o600)


def add_entry(value: str, path: Path = WATCHLIST_PATH) -> None:
    value = value.strip()
    if not value or value in load_entries(path):
        return
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current and not current.endswith("\n"):
        current += "\n"  # sin esto la entrada nueva se pegaba a la última línea
    _write(path, current + value + "\n")


def remove_entry(value: str, path: Path = WATCHLIST_PATH) -> bool:
    value = value.strip()
    if value not in load_entries(path):
        return False
    # Se quitan solo las líneas de esa entrada: los comentarios y el resto se conservan.
    lines = path.read_text(encoding="utf-8").splitlines()
    remaining = [line for line in lines if line.strip() != value]
    _write(path, "\n".join(remaining) + ("\n" if remaining else ""))
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
    # \b solo funciona junto a una letra o un dígito: una entrada que empieza por «+» (un
    # teléfono) o acaba en «,» no casaba nunca. Se exige que no haya letra ni dígito al lado.
    return re.compile(rf"(?<![^\W_]){inner}(?![^\W_])", re.IGNORECASE)
