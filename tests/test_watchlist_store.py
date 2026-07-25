from pushward.watchlist_store import add_entry, build_pattern, load_entries, remove_entry


def test_add_y_load(tmp_path):
    p = tmp_path / "watchlist.txt"
    add_entry("AcmeCorp", path=p)
    add_entry("ExampleVendor", path=p)
    assert load_entries(p) == ["AcmeCorp", "ExampleVendor"]


def test_add_no_duplica(tmp_path):
    p = tmp_path / "watchlist.txt"
    add_entry("AcmeCorp", path=p)
    add_entry("AcmeCorp", path=p)
    assert load_entries(p) == ["AcmeCorp"]


def test_remove(tmp_path):
    p = tmp_path / "watchlist.txt"
    add_entry("AcmeCorp", path=p)
    add_entry("ExampleVendor", path=p)
    assert remove_entry("AcmeCorp", path=p) is True
    assert load_entries(p) == ["ExampleVendor"]


def test_remove_inexistente_devuelve_false(tmp_path):
    p = tmp_path / "watchlist.txt"
    assert remove_entry("NoExiste", path=p) is False


def test_load_ignora_comentarios_y_lineas_vacias(tmp_path):
    p = tmp_path / "watchlist.txt"
    p.write_text("# comentario\n\nAcmeCorp\n\n# otro\nExampleVendor\n", encoding="utf-8")
    assert load_entries(p) == ["AcmeCorp", "ExampleVendor"]


def test_load_fichero_inexistente_devuelve_vacio(tmp_path):
    assert load_entries(tmp_path / "no-existe.txt") == []


def test_build_pattern_casa_variantes_de_separador():
    pattern = build_pattern("Ruben.Blanco")
    assert pattern.search("ruben_blanco")
    assert pattern.search("Ruben Blanco")
    assert pattern.search("RubenBlanco")
    assert pattern.search("path/to/ruben-blanco/file.txt")


def test_build_pattern_no_casa_nombre_distinto():
    pattern = build_pattern("Ruben Blanco")
    assert not pattern.search("Pedro Garcia")


def test_build_pattern_entrada_de_un_solo_token():
    pattern = build_pattern("AcmeCorp")
    assert pattern.search("cliente: ACMECORP")
    assert not pattern.search("acmecorporate solutions")  # limite de palabra evita el falso positivo


def test_build_pattern_concatenado_sin_separador_sigue_casando():
    pattern = build_pattern("Ruben Blanco")
    assert pattern.search("carpeta/RubenBlanco/archivo.txt")
