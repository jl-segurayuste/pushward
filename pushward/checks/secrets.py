from __future__ import annotations

import re
from pathlib import Path

from pushward.plugin import CheckResult, Finding
from pushward.scanner import read_text

_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("Clave privada (PEM)", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "high"),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "high"),
    ("Token de GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "high"),
    ("Token de Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "high"),
    ("Clave de API de OpenAI", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "high"),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "medium"),
]

_ASSIGNMENT = re.compile(
    r"""(?im)^\s*[\w.]*(password|passwd|secret|api_key|apikey|token)\s*[:=]\s*['"]?([^\s'"]{6,})['"]?"""
)
_PLACEHOLDER_VALUES = {
    "changeme", "change_me", "your_password", "your-password", "xxxxx",
    "placeholder", "example", "todo", "fixme", "<password>", "<secret>",
    "your_token_here", "insert_here",
}


class SecretsCheck:
    """Claves privadas, tokens de alta confianza (AWS/GitHub/Slack/OpenAI/JWT) y asignaciones de credenciales en claro."""

    name = "secrets"

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
                for title, pattern, severity in _PATTERNS:
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                severity=severity,
                                title=f"Posible secreto: {title}",
                                detail="Revisar y revocar si es real antes de publicar.",
                                path=rel,
                                line=line_no,
                            )
                        )

                m = _ASSIGNMENT.search(line)
                if m:
                    value = m.group(2).strip("'\"")
                    if value.lower() not in _PLACEHOLDER_VALUES and not value.startswith("{{"):
                        findings.append(
                            Finding(
                                severity="medium",
                                title=f"Asignación de credencial en claro ({m.group(1)})",
                                detail="Heurística -- puede ser un valor de ejemplo/placeholder real.",
                                path=rel,
                                line=line_no,
                            )
                        )

        return CheckResult(
            check_name=self.name,
            summary=f"{scanned} fichero(s) analizados, {len(findings)} hallazgo(s).",
            findings=findings,
        )
