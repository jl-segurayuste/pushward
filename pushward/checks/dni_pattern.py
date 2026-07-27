from __future__ import annotations

import re
from pathlib import Path

from pushward.plugin import CheckResult, Finding
from pushward.scanner import read_text

_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX = {"X": "0", "Y": "1", "Z": "2"}

# El lookbehind negativo excluye timestamps ISO8601 con fracción de segundo
# (p.ej. "...45.73846735Z"): la "Z" de UTC hace que el número parezca DNI
# ("8 dígitos + letra"), y con miles de líneas de log da la casualidad de que
# algunos hasta pasan la validación del dígito de control por puro azar.
_DNI_RE = re.compile(r"(?<!\.)\b(\d{8})[-\s]?([A-Za-z])\b")
_NIE_RE = re.compile(r"(?<!\.)\b([XYZxyz])(\d{7})[-\s]?([A-Za-z])\b")


def _expected_letter(number: str) -> str:
    return _LETTERS[int(number) % 23]


class DniPatternCheck:
    """Heurística de DNI/NIE español.

    No basta con casar el patrón "8 dígitos + letra": ese formato aparece
    todo el tiempo en placeholders/ejemplos inventados (p.ej. "12345678A",
    que ni siquiera es un DNI válido -- su letra de control real es "Z").
    Por eso se valida el dígito de control (módulo 23) antes de reportar
    nada: reduce drásticamente los falsos positivos y solo marca strings
    que son, con alta probabilidad, un DNI/NIE real.
    """

    name = "dni_pattern"

    def run(self, files: list[Path], repo_path: Path) -> CheckResult:
        findings: list[Finding] = []
        scanned = 0
        for path in files:
            text = read_text(path)
            if text is None:
                continue
            scanned += 1
            rel = str(path.relative_to(repo_path))

            for line_no, line in enumerate(text.splitlines(), start=1):
                for m in _DNI_RE.finditer(line):
                    number, letter = m.group(1), m.group(2).upper()
                    if letter == _expected_letter(number):
                        findings.append(
                            Finding(
                                severity="high",
                                title="Posible DNI real",
                                detail="Dígito de control válido -- no parece un valor de ejemplo.",
                                path=rel,
                                line=line_no,
                            )
                        )
                for m in _NIE_RE.finditer(line):
                    prefix, number, letter = m.group(1).upper(), m.group(2), m.group(3).upper()
                    full_number = _NIE_PREFIX[prefix] + number
                    if letter == _expected_letter(full_number):
                        findings.append(
                            Finding(
                                severity="high",
                                title="Posible NIE real",
                                detail="Dígito de control válido -- no parece un valor de ejemplo.",
                                path=rel,
                                line=line_no,
                            )
                        )

        return CheckResult(
            check_name=self.name,
            summary=f"{scanned} fichero(s) analizados, {len(findings)} hallazgo(s).",
            findings=findings,
        )
