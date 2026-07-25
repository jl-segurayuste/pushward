from conftest import commit_all, stage_all, write

from pushward.scanner import list_files, read_text


def test_list_files_tracked(git_repo):
    write(git_repo, "a.py", "x = 1\n")
    write(git_repo, "b.py", "y = 2\n")
    commit_all(git_repo)
    files = list_files(git_repo)
    names = {f.name for f in files}
    assert names == {"a.py", "b.py"}


def test_list_files_respeta_gitignore(git_repo):
    write(git_repo, ".gitignore", "ignored.py\n")
    write(git_repo, "ignored.py", "secret = 1\n")
    write(git_repo, "kept.py", "x = 1\n")
    commit_all(git_repo)
    files = list_files(git_repo)
    names = {f.name for f in files}
    assert names == {".gitignore", "kept.py"}


def test_list_files_staged_solo_devuelve_lo_que_esta_en_stage(git_repo):
    write(git_repo, "committed.py", "x = 1\n")
    commit_all(git_repo)
    write(git_repo, "new.py", "y = 2\n")
    stage_all(git_repo)
    files = list_files(git_repo, staged=True)
    names = {f.name for f in files}
    assert names == {"new.py"}


def test_read_text_fichero_inexistente_devuelve_none(tmp_path):
    assert read_text(tmp_path / "no-existe.txt") is None


def test_read_text_binario_devuelve_none(tmp_path):
    p = tmp_path / "bin.dat"
    p.write_bytes(b"\xff\xfe\x00\x01binary")
    assert read_text(p) is None
