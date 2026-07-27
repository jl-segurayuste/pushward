from conftest import commit_all, write

from pushward.checks.dni_pattern import DniPatternCheck
from pushward.scanner import list_files


def _run(git_repo):
    files = list_files(git_repo)
    return DniPatternCheck().run(files, git_repo)


def test_dni_con_letra_de_control_valida_se_marca(git_repo):
    # 12345678 mod 23 == 14 -> 'Z' es la letra de control real
    write(git_repo, "notes.md", "usuario ejemplo: 12345678Z\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1
    assert result.findings[0].severity == "high"


def test_dni_placeholder_con_letra_invalida_no_se_marca(git_repo):
    # 12345678A no es un DNI valido (la letra real seria Z) -- placeholder tipico
    write(git_repo, "notes.md", "usuario ejemplo: 12345678A\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_nie_con_letra_de_control_valida_se_marca(git_repo):
    # X1234567 -> 01234567 mod 23 == 19 -> 'L'
    write(git_repo, "notes.md", "nie: X1234567L\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1
    assert "NIE" in result.findings[0].title


def test_timestamp_iso8601_con_fraccion_no_se_marca(git_repo):
    # "73846735" pasa el digito de control por pura casualidad -- viene de
    # la fraccion de segundo de un timestamp real, no es un DNI.
    write(git_repo, "app.log", '{"time":"2023-11-23T16:01:45.73846735Z"}\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_dni_normal_no_precedido_de_punto_sigue_marcandose(git_repo):
    write(git_repo, "notes.md", "DNI: 12345678Z\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1


def test_texto_sin_patron_dni_no_se_marca(git_repo):
    write(git_repo, "notes.md", "no hay nada aqui\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
