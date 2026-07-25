from __future__ import annotations

import traceback
from importlib.metadata import entry_points
from pathlib import Path

from pushward.plugin import Check, CheckResult
from pushward.scanner import list_files

ENTRY_POINT_GROUP = "pushward.checks"


def discover_checks() -> dict[str, type[Check]]:
    found: dict[str, type[Check]] = {}
    for ep in entry_points(group=ENTRY_POINT_GROUP):
        found[ep.name] = ep.load()
    return found


def run_checks(
    repo_path: Path,
    *,
    staged: bool = False,
    only: set[str] | None = None,
    skip: set[str] | None = None,
) -> list[CheckResult]:
    checks = discover_checks()
    names = set(checks) if only is None else (set(checks) & only)
    if skip:
        names -= skip

    files = list_files(repo_path, staged=staged)

    results = []
    for name in sorted(names):
        try:
            result = checks[name]().run(files, repo_path)
        except Exception as exc:  # noqa: BLE001 -- aislar un check roto del resto de la ejecución
            result = CheckResult(
                check_name=name,
                summary=f"El check falló al ejecutarse: {exc}",
                error=traceback.format_exc(),
            )
        results.append(result)
    return results
