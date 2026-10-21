from __future__ import annotations

from pathlib import Path

from pushward import watchlist_store
from pushward.plugin import CheckResult, Finding
from pushward.scanner import read_text
from pushward.watchlist_store import build_pattern


class WatchlistCheck:
    """El diferenciador real frente a un escáner de secretos normal: una
    lista global (fuera del repo, en ~/.config/pushward/watchlist.txt) de
    nombres/empresas/dominios reales que no deben aparecer en NINGÚN repo.
    Los escáneres por regex no distinguen una IP/nombre real de un ejemplo
    inventado -- esto sí, porque el usuario ya le dijo qué es real.
    """

    name = "watchlist"

    def run(self, files: list[Path], repo_path: Path) -> CheckResult:
        entries = watchlist_store.load_entries(watchlist_store.WATCHLIST_PATH)
        if not entries:
            return CheckResult(
                check_name=self.name,
                summary="No aplica: la watchlist está vacía (pushward watchlist add <valor>).",
            )

        patterns = [(entry, build_pattern(entry)) for entry in entries]
        findings: list[Finding] = []
        scanned = 0

        for path in files:
            rel = str(path.relative_to(repo_path))
            for entry, pattern in patterns:
                if pattern.search(rel):
                    findings.append(
                        Finding(
                            severity="high",
                            title=f"Entrada de watchlist en la ruta (fichero o carpeta): {entry!r}",
                            path=rel,
                        )
                    )

            text = read_text(path)
            if text is None:
                continue
            scanned += 1
            for line_no, line in enumerate(text.splitlines(), start=1):
                for entry, pattern in patterns:
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                severity="high",
                                title=f"Entrada de watchlist encontrada: {entry!r}",
                                path=rel,
                                line=line_no,
                            )
                        )

        return CheckResult(
            check_name=self.name,
            summary=f"{len(entries)} entrada(s) en la watchlist, {scanned} fichero(s) analizados, {len(findings)} hallazgo(s).",
            findings=findings,
        )
