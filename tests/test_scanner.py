import subprocess

from conftest import commit_all, stage_all, write

from pushward.scanner import EMPTY_TREE_SHA, diff_files, list_files, read_text


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


def test_list_files_respeta_pushwardignore(git_repo):
    write(git_repo, ".pushwardignore", "fixtures/fake_secrets.py\n")
    write(git_repo, "fixtures/fake_secrets.py", "AWS_KEY = 'AKIA...'\n")
    write(git_repo, "kept.py", "x = 1\n")
    commit_all(git_repo)
    files = list_files(git_repo)
    names = {f.name for f in files}
    assert names == {".pushwardignore", "kept.py"}


def test_read_text_fichero_inexistente_devuelve_none(tmp_path):
    assert read_text(tmp_path / "no-existe.txt") is None


def test_read_text_binario_devuelve_none(tmp_path):
    p = tmp_path / "bin.dat"
    p.write_bytes(b"\xff\xfe\x00\x01binary")
    assert read_text(p) is None


def _rev_parse(repo, ref):
    return subprocess.run(
        ["git", "rev-parse", ref], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def test_diff_files_entre_dos_commits(git_repo):
    write(git_repo, "a.py", "x = 1\n")
    commit_all(git_repo, "primero")
    old = _rev_parse(git_repo, "HEAD")
    write(git_repo, "b.py", "y = 2\n")
    commit_all(git_repo, "segundo")
    new = _rev_parse(git_repo, "HEAD")

    files = diff_files(git_repo, f"{old}..{new}")
    assert {f.name for f in files} == {"b.py"}


def test_diff_files_contra_empty_tree_ve_todo(git_repo):
    write(git_repo, "a.py", "x = 1\n")
    write(git_repo, "b.py", "y = 2\n")
    commit_all(git_repo, "primero")
    new = _rev_parse(git_repo, "HEAD")

    files = diff_files(git_repo, f"{EMPTY_TREE_SHA}..{new}")
    assert {f.name for f in files} == {"a.py", "b.py"}
