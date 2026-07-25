from conftest import commit_all, write

from pushward.checks.sensitive_filenames import SensitiveFilenamesCheck
from pushward.scanner import list_files


def _run(git_repo):
    files = list_files(git_repo)
    return SensitiveFilenamesCheck().run(files, git_repo)


def test_pdf_con_palabra_sensible_se_marca(git_repo):
    write(git_repo, "docs/nomina_julio.pdf", "%PDF-1.4 fake")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1


def test_pdf_sin_palabra_sensible_no_se_marca(git_repo):
    write(git_repo, "docs/manual.pdf", "%PDF-1.4 fake")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_extension_no_sensible_se_ignora_aunque_tenga_palabra_clave(git_repo):
    write(git_repo, "contrato.py", "x = 1\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_nunca_lee_contenido_del_fichero(git_repo, monkeypatch):
    write(git_repo, "docs/random.pdf", "sin nada raro")
    commit_all(git_repo)
    files = list_files(git_repo)

    def _boom(*a, **k):
        raise AssertionError("no debería leerse el contenido")

    from pathlib import Path
    monkeypatch.setattr(Path, "read_text", _boom)
    SensitiveFilenamesCheck().run(files, git_repo)
