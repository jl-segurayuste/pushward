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


def test_asignacion_env_style_sin_comillas_se_marca(git_repo):
    write(git_repo, ".env.example", "CH_PASSWORD=sup3rSecr3tVal\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("credencial en claro" in f.title for f in result.findings)


def test_referencia_a_atributo_no_se_marca(git_repo):
    # kwarg=atributo real de config -- no es un literal, es codigo normal
    write(git_repo, "server.py", "smtp_password=cfg.notifications.smtp_password,\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_llamada_a_funcion_no_se_marca(git_repo):
    write(git_repo, "cli.py", 'password = getpass.getpass("Contraseña: ")\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_sin_secretos_no_hay_hallazgos(git_repo):
    write(git_repo, "clean.py", "x = 1 + 2\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_asignacion_con_anotacion_de_tipo_se_marca(git_repo):
    # Bug real encontrado 2026-08-09: "nombre: Tipo = valor" (anotación de tipo de
    # Python) no coincidía porque el separador esperado justo tras la palabra clave
    # era "=", no "str".
    write(git_repo, "config.py", 'smtp_password: str = "hunter22345"\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("credencial en claro" in f.title for f in result.findings)


def test_asignacion_por_subindice_se_marca(git_repo):
    # Bug real encontrado 2026-08-09: os.environ["API_TOKEN"] = "..." no coincidía
    # porque la clave va entre corchetes y comillas, no como identificador suelto.
    write(git_repo, "config.py", 'os.environ["API_TOKEN"] = "abc123456789xyz"\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert any("credencial en claro" in f.title for f in result.findings)


def test_anotacion_de_tipo_sin_valor_no_se_marca(git_repo):
    write(git_repo, "config.py", "password: str\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_palabra_clave_como_prefijo_de_otra_palabra_no_se_marca(git_repo):
    # "secretary" empieza por "secret" pero no es una credencial.
    write(git_repo, "config.py", 'secretary_name = "Jane Doe"\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []


def test_subindice_con_clave_no_sensible_no_se_marca(git_repo):
    write(git_repo, "config.py", 'config["timeout"] = "30 seconds ok"\n')
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
