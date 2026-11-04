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


def test_add_sin_salto_final_no_pega_lineas(tmp_path):
    path = tmp_path / "wl.txt"
    path.write_text("Ana")
    add_entry("Luis", path)
    assert load_entries(path) == ["Ana", "Luis"]


def test_remove_conserva_comentarios(tmp_path):
    path = tmp_path / "wl.txt"
    path.write_text("# nombres reales\nAna\nLuis\n")
    remove_entry("Ana", path)
    assert path.read_text() == "# nombres reales\nLuis\n"


def test_fichero_solo_legible_por_el_dueno(tmp_path):
    import os

    old = os.umask(0o022)
    try:
        path = tmp_path / "cfg" / "wl.txt"
        add_entry("Ana", path)
    finally:
        os.umask(old)
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700


def test_build_pattern_entradas_con_simbolos_en_los_bordes():
    assert build_pattern("+34 600 111 222").search("tel +34 600111222")
    assert build_pattern("c/ Mayor 3,").search("vive en c/ Mayor 3, Madrid")
    assert not build_pattern("Ana").search("Mariana")
