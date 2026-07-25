from conftest import commit_all, write

from pushward.runner import discover_checks, run_checks


def test_discover_checks_incluye_los_builtin():
    checks = discover_checks()
    expected = {"secrets", "private_ips", "watchlist", "dni_pattern", "sensitive_filenames"}
    assert expected <= set(checks)


def test_run_checks_devuelve_un_resultado_por_check(git_repo):
    write(git_repo, "a.py", "x = 1\n")
    commit_all(git_repo)
    results = run_checks(git_repo, only={"secrets", "private_ips"})
    names = {r.check_name for r in results}
    assert names == {"secrets", "private_ips"}


def test_run_checks_skip_excluye(git_repo):
    write(git_repo, "a.py", "x = 1\n")
    commit_all(git_repo)
    results = run_checks(git_repo, only={"secrets", "private_ips"}, skip={"private_ips"})
    names = {r.check_name for r in results}
    assert "private_ips" not in names
    assert "secrets" in names


def test_run_checks_captura_excepcion_de_un_check_roto(git_repo, monkeypatch):
    import pushward.runner as runner_module

    class BrokenCheck:
        name = "broken"

        def run(self, files, repo_path):
            raise RuntimeError("boom")

    monkeypatch.setattr(runner_module, "discover_checks", lambda: {"broken": BrokenCheck})
    write(git_repo, "a.py", "x = 1\n")
    commit_all(git_repo)
    results = run_checks(git_repo)
    assert len(results) == 1
    assert results[0].error is not None
    assert "boom" in results[0].summary
