from conftest import commit_all, write

from pushward import watchlist_store
from pushward.cli import main


def test_scan_exit_0_sin_hallazgos_graves(git_repo, capsys):
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo)
    rc = main(["scan", str(git_repo), "--fail-on", "high"])
    assert rc == 0


def test_scan_exit_1_con_hallazgo_high(git_repo, capsys):
    write(git_repo, "key.pem", "-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n")
    commit_all(git_repo)
    rc = main(["scan", str(git_repo), "--fail-on", "high"])
    assert rc == 1


def test_scan_json_produce_json_valido(git_repo, capsys):
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo)
    main(["scan", str(git_repo), "--json"])
    out = capsys.readouterr().out
    assert '"check_name"' in out


def test_list_checks_incluye_watchlist(capsys):
    main(["list-checks"])
    out = capsys.readouterr().out
    assert "watchlist" in out


def test_install_hook_via_cli(git_repo, capsys):
    rc = main(["install-hook", str(git_repo)])
    assert rc == 0
    assert (git_repo / ".git" / "hooks" / "pre-push").exists()


def test_watchlist_add_list_remove_via_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", tmp_path / "watchlist.txt")
    main(["watchlist", "add", "Consum"])
    main(["watchlist", "list"])
    out = capsys.readouterr().out
    assert "Consum" in out
    main(["watchlist", "remove", "Consum"])
    main(["watchlist", "list"])
    out = capsys.readouterr().out
    assert "vacía" in out
