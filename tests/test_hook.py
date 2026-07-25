import pytest

from pushward import hook


def test_install_crea_pre_push(git_repo):
    target = hook.install(git_repo)
    assert target.exists()
    assert "pushward" in target.read_text(encoding="utf-8")
    assert target.stat().st_mode & 0o111  # ejecutable


def test_install_no_sobreescribe_hook_ajeno(git_repo):
    existing = hook.hooks_dir(git_repo) / "pre-push"
    existing.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        hook.install(git_repo)
    assert "custom" in existing.read_text(encoding="utf-8")


def test_install_es_idempotente_si_ya_es_de_pushward(git_repo):
    hook.install(git_repo)
    target = hook.install(git_repo)  # no debe lanzar
    assert "pushward" in target.read_text(encoding="utf-8")


def test_uninstall_quita_el_hook(git_repo):
    hook.install(git_repo)
    assert hook.uninstall(git_repo) is True
    assert not (hook.hooks_dir(git_repo) / "pre-push").exists()


def test_uninstall_sin_hook_devuelve_false(git_repo):
    assert hook.uninstall(git_repo) is False


def test_uninstall_no_toca_hook_ajeno(git_repo):
    existing = hook.hooks_dir(git_repo) / "pre-push"
    existing.write_text("#!/bin/sh\necho custom\n", encoding="utf-8")
    assert hook.uninstall(git_repo) is False
    assert existing.exists()
