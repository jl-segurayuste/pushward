import io
import subprocess

from conftest import commit_all, write

from pushward import watchlist_store
from pushward.cli import main
from pushward.scanner import ZERO_OID


def _rev_parse(repo, ref="HEAD"):
    return subprocess.run(
        ["git", "rev-parse", ref], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


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


def test_pre_push_hook_bloquea_secreto_en_el_rango_a_subir(git_repo, monkeypatch, capsys):
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo, "primero")
    old = _rev_parse(git_repo)
    write(git_repo, "id_rsa", "-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n")
    commit_all(git_repo, "add key")
    new = _rev_parse(git_repo)

    monkeypatch.chdir(git_repo)
    stdin_line = f"refs/heads/main {new} refs/heads/main {old}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_line))
    rc = main(["pre-push-hook"])
    assert rc == 1


def test_pre_push_hook_deja_pasar_commits_limpios(git_repo, monkeypatch, capsys):
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo, "primero")
    old = _rev_parse(git_repo)
    write(git_repo, "b.py", "y = 2\n")
    commit_all(git_repo, "segundo")
    new = _rev_parse(git_repo)

    monkeypatch.chdir(git_repo)
    stdin_line = f"refs/heads/main {new} refs/heads/main {old}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_line))
    rc = main(["pre-push-hook"])
    assert rc == 0


def test_pre_push_hook_rama_nueva_escanea_todo_desde_empty_tree(git_repo, monkeypatch, capsys):
    write(git_repo, "id_rsa", "-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n")
    commit_all(git_repo, "primero")
    new = _rev_parse(git_repo)

    monkeypatch.chdir(git_repo)
    stdin_line = f"refs/heads/main {new} refs/heads/main {ZERO_OID}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_line))
    rc = main(["pre-push-hook"])
    assert rc == 1


def test_pre_push_hook_borrado_de_rama_no_hace_nada(git_repo, monkeypatch, capsys):
    monkeypatch.chdir(git_repo)
    stdin_line = f"refs/heads/old {ZERO_OID} refs/heads/old {'a' * 40}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_line))
    rc = main(["pre-push-hook"])
    assert rc == 0


def test_watchlist_add_list_remove_via_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", tmp_path / "watchlist.txt")
    main(["watchlist", "add", "AcmeCorp"])
    main(["watchlist", "list"])
    out = capsys.readouterr().out
    assert "AcmeCorp" in out
    main(["watchlist", "remove", "AcmeCorp"])
    main(["watchlist", "list"])
    out = capsys.readouterr().out
    assert "vacía" in out


def test_pre_push_hook_ve_secretos_borrados_en_un_commit_posterior(git_repo, monkeypatch):
    """El secreto viaja en el historial aunque el último commit lo quite."""
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo, "primero")
    old = _rev_parse(git_repo)
    write(git_repo, "conf.py", 'token = "ghp_' + "a" * 36 + '"\n')
    commit_all(git_repo, "con secreto")
    (git_repo / "conf.py").unlink()
    commit_all(git_repo, "lo quito")
    new = _rev_parse(git_repo)
    monkeypatch.chdir(git_repo)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"refs/heads/main {new} refs/heads/main {old}\n"))
    assert main(["pre-push-hook"]) == 1


def test_pre_push_hook_lee_el_commit_no_el_arbol_de_trabajo(git_repo, monkeypatch):
    write(git_repo, "clean.py", "x = 1\n")
    commit_all(git_repo, "primero")
    old = _rev_parse(git_repo)
    write(git_repo, "conf.py", 'token = "ghp_' + "a" * 36 + '"\n')
    commit_all(git_repo, "con secreto")
    new = _rev_parse(git_repo)
    write(git_repo, "conf.py", "limpio = 1\n")          # quitado del árbol, sin commitear
    monkeypatch.chdir(git_repo)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"refs/heads/main {new} refs/heads/main {old}\n"))
    assert main(["pre-push-hook"]) == 1


def test_pre_push_hook_remoto_desconocido_no_deja_pasar_a_ciegas(git_repo, monkeypatch):
    """push --force sobre un remoto con commits que no están aquí: antes no se escaneaba nada."""
    write(git_repo, "id_rsa", "-----BEGIN RSA PRIVATE KEY-----\nx\n")
    commit_all(git_repo, "primero")
    new = _rev_parse(git_repo)
    monkeypatch.chdir(git_repo)
    monkeypatch.setattr("sys.stdin", io.StringIO(f"refs/heads/main {new} refs/heads/main {'1' * 40}\n"))
    assert main(["pre-push-hook"]) == 1
