from __future__ import annotations

import re
from pathlib import Path

from pushward.plugin import CheckResult, Finding

_SENSITIVE_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".odt"}
_SENSITIVE_WORDS = re.compile(
    r"(nomina|payroll|dni|nie|passport|pasaporte|contrato|contract"
    r"|confidencial|confidential|salario|salary|factura|invoice"
    r"|curriculum|cv[-_.]|expediente|historial[-_.]medico)",
    re.IGNORECASE,
)


class SensitiveFilenamesCheck:
    """Solo mira nombres de fichero, nunca abre su contenido (PDF/DOCX/etc.
    pueden ser grandes o tener formatos binarios complejos de parsear con
    seguridad -- el nombre ya es una señal suficientemente buena y barata).
    """

    name = "sensitive_filenames"

    def run(self, files: list[Path], repo_path: Path) -> CheckResult:
        findings: list[Finding] = []
        for path in files:
            if path.suffix.lower() not in _SENSITIVE_EXTENSIONS:
                continue
            if _SENSITIVE_WORDS.search(path.name):
                rel = str(path.relative_to(repo_path))
                findings.append(
                    Finding(
                        severity="medium",
                        title=f"Nombre de fichero sensible: {path.name}",
                        detail="El nombre sugiere contenido personal/confidencial -- revisar antes de publicar.",
                        path=rel,
                    )
                )

        return CheckResult(
            check_name=self.name,
            summary=f"{len(files)} fichero(s) revisados, {len(findings)} hallazgo(s).",
            findings=findings,
        )
