from conftest import commit_all, write

from pushward.checks.secrets import SecretsCheck
from pushward.scanner import list_files


def _run(git_repo):
    files = list_files(git_repo)
    return SecretsCheck().run(files, git_repo)


def test_detecta_clave_privada_pem(git_repo):
    write(git_repo, "key.pem", "-----BEGIN RSA PRIVATE KEY-----\nMIIEow==\n-----END RSA PRIVATE KEY-----\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("privada" in f.title.lower() for f in result.findings)
    assert any(f.severity == "high" for f in result.findings)


def test_detecta_aws_key(git_repo):
    write(git_repo, "config.py", "AWS_KEY = 'AKIAABCDEFGHIJKLMNOP'\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("AWS" in f.title for f in result.findings)


def test_detecta_token_github(git_repo):
    write(git_repo, "config.py", "TOKEN = 'ghp_" + "a" * 36 + "'\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("GitHub" in f.title for f in result.findings)


def test_asignacion_password_en_claro_se_marca(git_repo):
    write(git_repo, "settings.py", "password = 'sup3rSecr3tVal'\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("credencial en claro" in f.title for f in result.findings)


def test_placeholder_no_se_marca(git_repo):
    write(git_repo, "settings.py", "password = 'changeme'\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_sin_secretos_no_hay_hallazgos(git_repo):
    write(git_repo, "clean.py", "x = 1 + 2\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
