from __future__ import annotations

from pathlib import Path

_HOOK_MARKER = "# installed-by: pushward"
_HOOK_TEMPLATE = f"""#!/bin/sh
{_HOOK_MARKER}
pushward scan --staged --fail-on high
exit $?
"""


def hooks_dir(repo_path: Path) -> Path:
    return repo_path / ".git" / "hooks"


def install(repo_path: Path) -> Path:
    target = hooks_dir(repo_path) / "pre-push"
    if target.exists() and _HOOK_MARKER not in target.read_text(encoding="utf-8"):
        raise FileExistsError(
            f"{target} ya existe y no fue instalado por pushward -- no lo voy a sobreescribir."
        )
    target.write_text(_HOOK_TEMPLATE, encoding="utf-8")
    target.chmod(0o755)
    return target


def uninstall(repo_path: Path) -> bool:
    target = hooks_dir(repo_path) / "pre-push"
    if not target.exists() or _HOOK_MARKER not in target.read_text(encoding="utf-8"):
        return False
    target.unlink()
    return True
