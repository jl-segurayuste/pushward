from conftest import commit_all, write

from pushward import watchlist_store
from pushward.checks.watchlist import WatchlistCheck
from pushward.scanner import list_files


def _run(git_repo):
    files = list_files(git_repo)
    return WatchlistCheck().run(files, git_repo)


def test_watchlist_vacia_no_aplica(git_repo, tmp_path, monkeypatch):
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", tmp_path / "watchlist.txt")
    write(git_repo, "notes.md", "cliente: Consum\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
    assert "vacía" in result.summary


def test_watchlist_detecta_en_contenido(git_repo, tmp_path, monkeypatch):
    wl = tmp_path / "watchlist.txt"
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", wl)
    watchlist_store.add_entry("Consum", path=wl)
    write(git_repo, "notes.md", "cliente real: consum\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1
    assert result.findings[0].severity == "high"


def test_watchlist_detecta_en_nombre_de_fichero(git_repo, tmp_path, monkeypatch):
    wl = tmp_path / "watchlist.txt"
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", wl)
    watchlist_store.add_entry("Ruben Blanco", path=wl)
    write(git_repo, "empleados/ruben_blanco/notas.txt", "x\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("ruta" in f.title for f in result.findings)


def test_watchlist_no_marca_nombres_distintos(git_repo, tmp_path, monkeypatch):
    wl = tmp_path / "watchlist.txt"
    monkeypatch.setattr(watchlist_store, "WATCHLIST_PATH", wl)
    watchlist_store.add_entry("Consum", path=wl)
    write(git_repo, "notes.md", "esto no tiene nada que ver\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
