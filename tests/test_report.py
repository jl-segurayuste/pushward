from pushward.plugin import CheckResult, Finding
from pushward.report import build_report, write_json


def test_worst_severity_ninguno_si_no_hay_findings():
    report = build_report(".", [CheckResult(check_name="x", summary="ok")])
    assert report.worst_severity() is None


def test_worst_severity_toma_el_mas_grave():
    results = [
        CheckResult(
            check_name="x",
            summary="ok",
            findings=[Finding(severity="low", title="a"), Finding(severity="high", title="b")],
        )
    ]
    report = build_report(".", results)
    assert report.worst_severity() == "high"


def test_to_console_no_contiene_emojis():
    results = [
        CheckResult(
            check_name="secrets",
            summary="1 hallazgo",
            findings=[Finding(severity="high", title="Algo", path="a.py", line=3)],
        )
    ]
    report = build_report("/repo", results)
    out = report.to_console()
    assert "[HIGH  ]" in out
    assert "a.py:3" in out
    assert "🔒" not in out and "⚠" not in out


def test_to_json_es_json_valido():
    results = [CheckResult(check_name="x", summary="ok")]
    report = build_report("/repo", results)
    out = write_json(report)
    assert '"check_name": "x"' in out
