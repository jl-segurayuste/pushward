from conftest import write

from pushward.ignorefile import is_ignored, load_patterns


def test_load_patterns_sin_fichero_devuelve_vacio(tmp_path):
    assert load_patterns(tmp_path) == []


def test_load_patterns_ignora_comentarios_y_vacias(git_repo):
    write(git_repo, ".pushwardignore", "# comentario\n\ntests/test_secrets.py\n\n# otro\n")
    assert load_patterns(git_repo) == ["tests/test_secrets.py"]


def test_is_ignored_coincidencia_exacta():
    assert is_ignored("tests/test_secrets.py", ["tests/test_secrets.py"])


def test_is_ignored_no_coincide():
    assert not is_ignored("src/main.py", ["tests/test_secrets.py"])


def test_is_ignored_con_wildcard():
    assert is_ignored("tests/test_dni_pattern.py", ["tests/test_*.py"])
