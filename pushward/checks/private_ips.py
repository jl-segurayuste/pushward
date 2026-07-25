from __future__ import annotations

import re
from pathlib import Path

from pushward.plugin import CheckResult, Finding
from pushward.scanner import read_text

_IP_RE = re.compile(
    r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3})\b"
)


class PrivateIpsCheck:
    """IPs de rangos privados (RFC1918): 10.x, 172.16-31.x, 192.168.x."""

    name = "private_ips"

    def run(self, files: list[Path], repo_path: Path) -> CheckResult:
        findings: list[Finding] = []
        scanned = 0
        for path in files:
            text = read_text(path)
            if text is None:
                continue
            scanned += 1
            rel = str(path.relative_to(repo_path))
            seen_on_file: set[str] = set()
            for line_no, line in enumerate(text.splitlines(), start=1):
                for m in _IP_RE.finditer(line):
                    ip = m.group(0)
                    key = f"{ip}:{line_no}"
                    if key in seen_on_file:
                        continue
                    seen_on_file.add(key)
                    findings.append(
                        Finding(
                            severity="info",
                            title=f"IP privada: {ip}",
                            detail="Puede ser un ejemplo genérico o una IP real de infraestructura -- revisar.",
                            path=rel,
                            line=line_no,
                        )
                    )

        return CheckResult(
            check_name=self.name,
            summary=f"{scanned} fichero(s) analizados, {len(findings)} hallazgo(s).",
            findings=findings,
        )
