from conftest import commit_all, write

from pushward.checks.private_ips import PrivateIpsCheck
from pushward.scanner import list_files


def _run(git_repo):
    files = list_files(git_repo)
    return PrivateIpsCheck().run(files, git_repo)


def test_detecta_ip_192_168(git_repo):
    write(git_repo, "hosts.txt", "server 192.168.1.100\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1
    assert "192.168.1.100" in result.findings[0].title


def test_detecta_ip_10(git_repo):
    write(git_repo, "hosts.txt", "10.20.30.40\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1


def test_detecta_ip_172_rango_privado(git_repo):
    write(git_repo, "hosts.txt", "172.20.0.5 y 172.99.0.5\n")
    commit_all(git_repo)
    result = _run(git_repo)
    # 172.20 esta en rango privado (16-31), 172.99 no
    assert len(result.findings) == 1
    assert "172.20.0.5" in result.findings[0].title


def test_no_duplica_misma_ip_misma_linea(git_repo):
    write(git_repo, "hosts.txt", "192.168.1.1 192.168.1.1\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert len(result.findings) == 1


def test_ip_publica_no_se_marca(git_repo):
    write(git_repo, "hosts.txt", "8.8.8.8\n")
    commit_all(git_repo)
    result = _run(git_repo)
    assert result.findings == []
