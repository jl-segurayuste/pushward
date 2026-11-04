from __future__ import annotations

import subprocess
from pathlib import Path

from pushward.ignorefile import is_ignored, load_patterns

# Árbol vacío de git -- objeto especial ya presente en cualquier repo, útil
# para diffear "todo lo que hay en <commit>" cuando no existe un punto de
# partida real (primer push de una rama nueva).
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
ZERO_OID = "0" * 40


def _git_name_only(repo_path: Path, cmd: list[str]) -> list[Path]:
    result = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    patterns = load_patterns(repo_path)
    return [
        repo_path / line
        for line in result.stdout.splitlines()
        if line and not is_ignored(line, patterns)
    ]


def list_files(repo_path: Path, *, staged: bool = False) -> list[Path]:
    """Ficheros a escanear: `git ls-files` (todo el árbol) o el diff en stage."""
    if staged:
        cmd = ["git", "-c", "core.quotePath=false", "diff", "--cached", "--name-only", "--diff-filter=ACM"]
    else:
        cmd = ["git", "-c", "core.quotePath=false", "ls-files"]
    return _git_name_only(repo_path, cmd)


def diff_files(repo_path: Path, range_arg: str) -> list[Path]:
    """Ficheros tocados en un rango de commits, p.ej. "<remote_oid>..<local_oid>"
    -- lo que de verdad se necesita en un hook pre-push, donde el stage ya
    está vacío (el commit ya se hizo) y `list_files(staged=True)` no vería nada.
    """
    cmd = ["git", "-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=ACM", range_arg]
    return _git_name_only(repo_path, cmd)


class ScanError(RuntimeError):
    """No se pudo saber qué se va a subir: el hook no debe dejar pasar el push a ciegas."""


def _git(repo_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo_path, capture_output=True, text=True, check=False)


def _object_exists(repo_path: Path, oid: str) -> bool:
    return _git(repo_path, "cat-file", "-e", f"{oid}^{{commit}}").returncode == 0


def commits_to_push(repo_path: Path, local_oid: str, remote_oid: str) -> list[str]:
    """Commits que el push va a subir.

    Con el remoto conocido, `remote..local`. En una rama nueva, o si el remoto tiene un commit que
    aquí no está (otro empujó y ahora se hace `push --force`), los que no están ya en ningún remoto
    conocido. Antes, en este último caso, `git diff` fallaba, se tomaba como «nada que revisar» y el
    push pasaba sin escanear.
    """
    if remote_oid != ZERO_OID and _object_exists(repo_path, remote_oid):
        args = ["rev-list", f"{remote_oid}..{local_oid}"]
    else:
        args = ["rev-list", local_oid, "--not", "--remotes"]
    result = _git(repo_path, *args)
    if result.returncode != 0:
        raise ScanError(f"git {' '.join(args)} falló: {result.stderr.strip()}")
    return result.stdout.split()


def _cat_blobs(repo_path: Path, oids: list[str]) -> dict[str, bytes]:
    if not oids:
        return {}
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=repo_path, input="\n".join(oids).encode() + b"\n",
        capture_output=True, check=False,
    )
    if proc.returncode != 0:
        raise ScanError(f"git cat-file falló: {proc.stderr.decode(errors='replace').strip()}")
    out, pos, blobs = proc.stdout, 0, {}
    for oid in oids:
        nl = out.index(b"\n", pos)
        header = out[pos:nl].split()
        if len(header) != 3:
            raise ScanError(f"Objeto {oid} ilegible: {out[pos:nl].decode(errors='replace')}")
        size = int(header[2])
        blobs[oid] = out[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
    return blobs


def materialize_commits(repo_path: Path, commits: list[str], dest: Path) -> list[Path]:
    """Copia en `dest/<commit>/<ruta>` cada versión de fichero añadida o modificada en `commits`.

    El hook leía los ficheros del árbol de trabajo: un secreto subido en un commit y borrado en el
    siguiente, o ya quitado del árbol sin commitear, pasaba sin verse aunque sí viajaba en el push.
    """
    patterns = load_patterns(repo_path)
    wanted: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for commit in commits:
        result = _git(repo_path, "diff-tree", "-r", "-m", "--root", "--no-commit-id",
                      "--diff-filter=AM", "-z", commit)
        if result.returncode != 0:
            raise ScanError(f"git diff-tree {commit} falló: {result.stderr.strip()}")
        parts = result.stdout.split("\0")
        for meta, path in zip(parts[0::2], parts[1::2], strict=False):
            fields = meta.split()
            if len(fields) < 5 or fields[1].startswith("160000"):  # submódulo: no es un fichero
                continue
            oid = fields[3]
            if oid in seen or is_ignored(path, patterns):
                continue
            seen.add(oid)
            wanted.append((commit, path, oid))

    blobs = _cat_blobs(repo_path, [oid for _, _, oid in wanted])
    files = []
    for commit, path, oid in wanted:
        target = dest / commit[:12] / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blobs[oid])
        files.append(target)
    return files


def read_text(path: Path) -> str | None:
    """Lee un fichero como texto; None si no existe o es binario.

    Un fichero que no es UTF-8 (un .env guardado en Latin-1) se leía como binario y se saltaba
    entero; ahora solo se descartan los que tienen bytes nulos.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", errors="replace")
